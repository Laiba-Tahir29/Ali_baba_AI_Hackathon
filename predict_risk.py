"""
predict_risk.py
----------------
Person A (ML Model) — loads the trained model and predicts cardiovascular
risk from a patient profile.

INTERFACE CONTRACT (matches rag-llm's consolidate_profiles() output —
must stay in sync with rag-llm/consolidation.py):

    predict_risk(final_profile) -> {risk_score, risk_level, top_factors}

    final_profile is expected to have these keys (from rag-llm):
        age (YEARS, not days — converted internally below)
        gender, height, weight, ap_hi, ap_lo, cholesterol, gluc,
        smoke, alco, active
        history (present but IGNORED here — not a dataset column,
                 rag-llm only needs it for generate_explanation())
        consistent_high_factors (present but IGNORED here — this
                 function returns its OWN top_factors based on the
                 model's feature importance + this patient's values)
"""

import joblib
import numpy as np
import pandas as pd
import shap

MODEL_PATH = "cardio_risk_model.pkl"

# Must match train_model.py's FEATURE_COLUMNS exactly, same order.
FEATURE_COLUMNS = [
    "age", "gender", "height", "weight", "ap_hi", "ap_lo",
    "cholesterol", "gluc", "smoke", "alco", "active",
]

# Risk score -> risk level thresholds. Adjust based on how the trained
# model's probabilities distribute (check with test set predictions).
RISK_THRESHOLDS = {
    "Low": 0.33,
    "Medium": 0.66,
    # anything above 0.66 -> "High"
}

_model_cache = None


def _get_model():
    """Load the trained model once and reuse it (avoids reloading from
    disk on every predict_risk() call)."""
    global _model_cache
    if _model_cache is None:
        _model_cache = joblib.load(MODEL_PATH)
    return _model_cache


def _age_years_to_days(age_years):
    """The dataset stores age in DAYS; rag-llm's final_profile gives
    age in YEARS (as written in medical reports). Convert here so the
    rag-llm side doesn't need to know this detail."""
    if age_years is None:
        return None
    return round(age_years * 365.25)


def _get_shap_explanation(model, feature_vector_df, max_factors=3):
    """
    Use SHAP TreeExplainer to compute patient-level feature attributions.

    Returns a list of dicts (top `max_factors` by |shap_value|), each:
        {"feature": str, "shap_value": float, "direction": str, "value": ...}
    """
    explainer = shap.TreeExplainer(model)
    raw = explainer.shap_values(feature_vector_df)

    # Handle different SHAP output formats
    if isinstance(raw, list):
        # Binary classification: list of two arrays — use class 1
        shap_vals = np.array(raw[1])
    elif hasattr(raw, "values"):
        # shap.Explanation object
        shap_vals = np.array(raw.values)
    else:
        shap_vals = np.array(raw)

    # Collapse to 1-D (n_features,) for the single-row input.
    # Possible shapes: (1, n_features), (n_features,), or (1, n_features, n_classes).
    if shap_vals.ndim == 3:
        # (n_samples, n_features, n_classes) — take positive class
        shap_vals = shap_vals[0, :, 1]
    else:
        shap_vals = shap_vals.flatten()

    if shap_vals.shape[0] != len(FEATURE_COLUMNS):
        raise ValueError(
            f"Expected {len(FEATURE_COLUMNS)} SHAP values, got {shap_vals.shape[0]}"
        )
    shap_1d = shap_vals

    # Pair with feature names and actual values from the vector
    feature_vals = feature_vector_df.iloc[0].values
    paired = list(zip(FEATURE_COLUMNS, shap_1d, feature_vals))
    paired.sort(key=lambda t: abs(t[1]), reverse=True)

    result = []
    for name, sv, fv in paired[:max_factors]:
        result.append({
            "feature": name,
            "shap_value": round(float(sv), 4),
            "direction": "increases_risk" if sv > 0 else "decreases_risk",
            "value": fv.item() if hasattr(fv, "item") else fv,
        })
    return result


def predict_risk(final_profile):
    """
    PUBLIC INTERFACE FUNCTION — called by Person C's integration layer,
    after rag-llm's consolidate_profiles() produces final_profile.

    Args:
        final_profile: dict from consolidate_profiles(), with age in YEARS.

    Returns:
        {risk_score: float (0-1), risk_level: str, top_factors: list[str]}
    """
    model = _get_model()

    # Build the feature vector, converting age years -> days and ignoring
    # non-dataset fields (history, consistent_high_factors).
    row = {
        "age": _age_years_to_days(final_profile.get("age")),
        "gender": final_profile.get("gender"),
        "height": final_profile.get("height"),
        "weight": final_profile.get("weight"),
        "ap_hi": final_profile.get("ap_hi"),
        "ap_lo": final_profile.get("ap_lo"),
        "cholesterol": final_profile.get("cholesterol"),
        "gluc": final_profile.get("gluc"),
        "smoke": final_profile.get("smoke"),
        "alco": final_profile.get("alco"),
        "active": final_profile.get("active"),
    }

    if any(v is None for v in row.values()):
        missing = [k for k, v in row.items() if v is None]
        raise ValueError(
            f"final_profile is missing required field(s) for prediction: {missing}"
        )

    feature_vector = pd.DataFrame([row], columns=FEATURE_COLUMNS)

    risk_score = float(model.predict_proba(feature_vector)[0][1])

    if risk_score < RISK_THRESHOLDS["Low"]:
        risk_level = "Low"
    elif risk_score < RISK_THRESHOLDS["Medium"]:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # SHAP-based patient-level explanation
    try:
        shap_explanation = _get_shap_explanation(model, feature_vector)
        top_factors = [item["feature"] for item in shap_explanation]
        shap_details = shap_explanation
    except Exception as exc:
        # Fallback: top 3 features by global importance (names only)
        importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_))
        top_factors = sorted(importances, key=importances.get, reverse=True)[:3]
        shap_details = f"SHAP explanation unavailable: {exc}"

    return {
        "risk_score": round(risk_score, 4),
        "risk_level": risk_level,
        "top_factors": top_factors,
        "shap_details": shap_details,
    }


# ---- Quick manual test ----
if __name__ == "__main__":
    # Sample final_profile shaped exactly like rag-llm's consolidate_profiles() output
    sample_profile = {
        "age": 55,  # years
        "gender": 1,
        "height": 160,
        "weight": 81,
        "ap_hi": 138,
        "ap_lo": 89,
        "cholesterol": 2,
        "gluc": 1,
        "smoke": 0,
        "alco": 0,
        "active": 1,
        "history": "no",  # ignored
        "consistent_high_factors": ["cholesterol", "ap_hi"],  # ignored here
    }

    result = predict_risk(sample_profile)

    print(f"Risk Score : {result['risk_score']}")
    print(f"Risk Level : {result['risk_level']}")
    print("\nTop Contributing Factors (SHAP):")
    print("-" * 60)
    details = result["shap_details"]
    if isinstance(details, list):
        for i, d in enumerate(details, 1):
            print(
                f"  {i}. {d['feature']:<14}"
                f"value={d['value']!s:<10}  "
                f"shap={d['shap_value']:+.4f}  "
                f"({d['direction']})"
            )
    else:
        print(f"  {details}")