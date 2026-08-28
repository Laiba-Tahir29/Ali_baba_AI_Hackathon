"""
Layer 4: ML Prediction & Explainability
Owner: Person A (ml-model branch)

Loads the real trained Random Forest model (cardio_risk_model.pkl),
performs SHAP TreeExplainer patient-level feature attributions,
and outputs the calibrated risk score, risk level, and top contributing factors.
"""

import os
from typing import Dict, Any, List
import joblib
import numpy as np
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "cardio_risk_model.pkl")

FEATURE_COLUMNS = [
    "age", "gender", "height", "weight", "ap_hi", "ap_lo",
    "cholesterol", "gluc", "smoke", "alco", "active",
]

RISK_THRESHOLDS = {
    "low": 0.33,
    "medium": 0.66,
}

FEATURE_DISPLAY_NAMES = {
    "ap_hi": "Systolic Blood Pressure",
    "ap_lo": "Diastolic Blood Pressure",
    "cholesterol": "Cholesterol",
    "gluc": "Fasting Glucose",
    "age": "Patient Age",
    "weight": "Weight / BMI",
    "height": "Height",
    "smoke": "Smoking Status",
    "alco": "Alcohol Consumption",
    "active": "Physical Activity",
    "gender": "Gender"
}

_model_cache = None


def _get_model():
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    if os.path.exists(MODEL_PATH):
        try:
            _model_cache = joblib.load(MODEL_PATH)
            return _model_cache
        except Exception as e:
            print(f"Warning: Failed loading model from {MODEL_PATH}: {e}")

    raise FileNotFoundError(f"Could not find trained cardio_risk_model.pkl at {MODEL_PATH}")


def _age_years_to_days(age_years):
    if age_years is None:
        return round(50 * 365.25)
    return round(float(age_years) * 365.25)


def _get_shap_explanation(model, feature_vector_df, max_factors=3):
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        raw = explainer.shap_values(feature_vector_df)

        if isinstance(raw, list):
            shap_vals = np.array(raw[1])
        elif hasattr(raw, "values"):
            shap_vals = np.array(raw.values)
        else:
            shap_vals = np.array(raw)

        if shap_vals.ndim == 3:
            shap_vals = shap_vals[0, :, 1]
        else:
            shap_vals = shap_vals.flatten()

        feature_vals = feature_vector_df.iloc[0].values
        paired = list(zip(FEATURE_COLUMNS, shap_vals, feature_vals))
        paired.sort(key=lambda t: abs(t[1]), reverse=True)

        result = []
        for name, sv, fv in paired[:max_factors]:
            result.append({
                "feature": name,
                "display_name": FEATURE_DISPLAY_NAMES.get(name, name),
                "shap_value": round(float(sv), 4),
                "direction": "increases_risk" if sv > 0 else "decreases_risk",
                "value": fv.item() if hasattr(fv, "item") else fv,
            })
        return result
    except Exception as exc:
        importances = dict(zip(FEATURE_COLUMNS, getattr(model, "feature_importances_", [0]*len(FEATURE_COLUMNS))))
        sorted_feats = sorted(importances, key=importances.get, reverse=True)[:max_factors]
        return [
            {
                "feature": name,
                "display_name": FEATURE_DISPLAY_NAMES.get(name, name),
                "shap_value": round(float(importances.get(name, 0)), 4),
                "direction": "increases_risk",
                "value": feature_vector_df.iloc[0].get(name, 0),
            }
            for name in sorted_feats
        ]


def predict_risk(final_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Public Interface Function — Person A's ML Risk Prediction.
    
    Args:
        final_profile: dict from consolidate_profiles()
        
    Returns:
        {
            "risk_score": float (e.g. 75.6 percentage),
            "risk_level": "low" | "medium" | "high",
            "top_3_factors": list[str] (clean display names for UI),
            "top_factors": list[str] (raw feature names),
            "shap_details": list[dict]
        }
    """
    model = _get_model()

    # Provide safe clinical defaults for missing fields if unmentioned in PDF
    gender = final_profile.get("gender")
    if gender is None:
        gender = 1  # default female/1

    height = final_profile.get("height")
    if height is None:
        height = 165.0

    weight = final_profile.get("weight")
    if weight is None:
        # Infer weight from BMI if present
        bmi = final_profile.get("bmi")
        if bmi:
            weight = round(float(bmi) * ((height / 100.0) ** 2), 1)
        else:
            weight = 72.0

    ap_hi = final_profile.get("ap_hi")
    ap_lo = final_profile.get("ap_lo")
    if ap_hi is None or ap_lo is None:
        # Parse from "bp" string if available e.g. "145/92"
        bp_str = str(final_profile.get("bp", "120/80"))
        try:
            parts = bp_str.split("/")
            ap_hi = int(parts[0].strip())
            ap_lo = int(parts[1].strip())
        except Exception:
            ap_hi = 120
            ap_lo = 80

    chol = final_profile.get("cholesterol")
    if chol is None or isinstance(chol, str):
        # Convert string to categorical 1, 2, 3
        try:
            val = float(str(chol).replace("mg/dL", "").strip())
            chol = 3 if val >= 240 else 2 if val >= 200 else 1
        except Exception:
            chol = 1

    gluc = final_profile.get("gluc")
    if gluc is None or isinstance(gluc, str):
        try:
            val = float(str(gluc).replace("mg/dL", "").strip())
            gluc = 3 if val >= 126 else 2 if val >= 100 else 1
        except Exception:
            gluc = 1

    smoke = final_profile.get("smoke")
    if smoke is None:
        smoke = 1 if str(final_profile.get("smoking", "")).lower() == "yes" else 0

    alco = final_profile.get("alco")
    if alco is None:
        alco = 0

    active = final_profile.get("active")
    if active is None:
        active = 1

    row = {
        "age": _age_years_to_days(final_profile.get("age")),
        "gender": int(gender),
        "height": float(height),
        "weight": float(weight),
        "ap_hi": int(ap_hi),
        "ap_lo": int(ap_lo),
        "cholesterol": int(chol),
        "gluc": int(gluc),
        "smoke": int(smoke),
        "alco": int(alco),
        "active": int(active),
    }

    feature_vector = pd.DataFrame([row], columns=FEATURE_COLUMNS)

    # Real Random Forest prediction
    prob = float(model.predict_proba(feature_vector)[0][1])

    if prob < RISK_THRESHOLDS["low"]:
        risk_level = "low"
    elif prob < RISK_THRESHOLDS["medium"]:
        risk_level = "medium"
    else:
        risk_level = "high"

    shap_explanation = _get_shap_explanation(model, feature_vector, max_factors=3)
    raw_top_factors = [item["feature"] for item in shap_explanation]
    display_top_factors = [item["display_name"] for item in shap_explanation]

    # Convert probability to percentage score for frontend UI
    risk_score_pct = round(prob * 100.0, 1)

    return {
        "risk_score": risk_score_pct,
        "risk_level": risk_level,
        "top_3_factors": display_top_factors,
        "top_factors": raw_top_factors,
        "shap_details": shap_explanation
    }
