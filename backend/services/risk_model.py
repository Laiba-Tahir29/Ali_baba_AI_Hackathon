from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "backend"
    / "models"
    / "cardio_risk_model.pkl"
)

IMPUTATION_PATH = (
    PROJECT_ROOT
    / "processed"
    / "imputation_values.csv"
)


# ============================================================
# EXACT TRAINING FEATURES
# ============================================================

MODEL_FEATURES = [
    "age",
    "gender",
    "height",
    "weight",
    "ap_hi",
    "ap_lo",
    "cholesterol",
    "gluc",
    "smoke",
    "alco",
    "active",
]


# ============================================================
# DISPLAY NAMES
# ============================================================

DISPLAY_NAMES = {
    "age": "Age",
    "gender": "Gender",
    "height": "Height",
    "weight": "Weight",
    "ap_hi": "Systolic Blood Pressure",
    "ap_lo": "Diastolic Blood Pressure",
    "cholesterol": "Cholesterol",
    "gluc": "Fasting Glucose",
    "smoke": "Smoking",
    "alco": "Alcohol Use",
    "active": "Physical Activity",
}


# ============================================================
# LOAD MODEL
# ============================================================

def _load_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Could not find trained model at: {MODEL_PATH}"
        )

    print(
        "[Risk Model] Loading model from: "
        f"{MODEL_PATH}"
    )

    return joblib.load(MODEL_PATH)


# ============================================================
# LOAD TRAINING IMPUTATION VALUES
# ============================================================

def _load_imputation_values() -> Dict[str, float]:

    if not IMPUTATION_PATH.exists():
        raise FileNotFoundError(
            "Could not find imputation file at: "
            f"{IMPUTATION_PATH}"
        )

    df = pd.read_csv(IMPUTATION_PATH)

    print(
        "[Risk Model] Loading imputation values from: "
        f"{IMPUTATION_PATH}"
    )

    result: Dict[str, float] = {}

    # --------------------------------------------------------
    # Standard format:
    #
    # feature,imputation_value
    # age,19701.0
    # gender,1.0
    # --------------------------------------------------------

    if (
        "feature" in df.columns
        and "imputation_value" in df.columns
    ):

        for _, row in df.iterrows():

            feature = str(
                row["feature"]
            ).strip()

            if feature not in MODEL_FEATURES:
                continue

            value = row["imputation_value"]

            if pd.isna(value):
                continue

            try:
                result[feature] = float(value)

            except (
                TypeError,
                ValueError,
            ):
                print(
                    "[Risk Model] Invalid imputation "
                    f"value for {feature}: {value}"
                )

    # --------------------------------------------------------
    # Backward-compatible format:
    #
    # feature,value
    # --------------------------------------------------------

    elif (
        "feature" in df.columns
        and "value" in df.columns
    ):

        for _, row in df.iterrows():

            feature = str(
                row["feature"]
            ).strip()

            if feature not in MODEL_FEATURES:
                continue

            value = row["value"]

            if pd.isna(value):
                continue

            try:
                result[feature] = float(value)

            except (
                TypeError,
                ValueError,
            ):
                pass

    # --------------------------------------------------------
    # Single-row format
    # --------------------------------------------------------

    else:

        if len(df) > 0:

            for feature in MODEL_FEATURES:

                if feature not in df.columns:
                    continue

                value = df[feature].iloc[0]

                if pd.isna(value):
                    continue

                try:
                    result[feature] = float(value)

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

    # --------------------------------------------------------
    # Verify all required imputation values
    # --------------------------------------------------------

    missing = [
        feature
        for feature in MODEL_FEATURES
        if feature not in result
    ]

    if missing:

        raise ValueError(
            "Missing training-data imputation values for: "
            + ", ".join(missing)
        )

    print(
        "[Risk Model] Loaded imputation values successfully:"
    )

    for feature in MODEL_FEATURES:

        print(
            f"    {feature}: {result[feature]}"
        )

    return result


# ============================================================
# NUMERIC NORMALIZATION
# ============================================================

def _numeric_value(
    value: Any,
) -> Optional[float]:

    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    try:

        text = str(value).strip().lower()

        if text in {
            "",
            "none",
            "null",
            "unknown",
            "n/a",
            "na",
            "not available",
            "not mentioned",
            "not provided",
            "missing",
        }:
            return None

        text = (
            text
            .replace("mg/dl", "")
            .replace("mmhg", "")
            .replace("kg/m²", "")
            .replace("kg/m2", "")
            .replace("kg", "")
            .replace("cm", "")
            .strip()
        )

        return float(text)

    except Exception:

        return None


# ============================================================
# GENDER NORMALIZATION
# ============================================================

def _normalize_gender(
    value: Any,
):

    if value is None:
        return None

    numeric = _numeric_value(value)

    if numeric is not None:

        numeric = int(numeric)

        if numeric in (1, 2):
            return numeric

    text = str(value).strip().lower()

    if text in {
        "female",
        "f",
        "woman",
    }:
        return 1

    if text in {
        "male",
        "m",
        "man",
    }:
        return 2

    return None


# ============================================================
# CHOLESTEROL NORMALIZATION
# ============================================================

def _normalize_cholesterol(
    value: Any,
):

    if value is None:
        return None

    # IMPORTANT:
    # Do not interpret None as normal.

    numeric = _numeric_value(value)

    if numeric is not None:

        numeric_int = int(numeric)

        # Dataset categories
        if numeric_int in (1, 2, 3):
            return numeric_int

    text = str(value).strip().lower()

    if (
        "well above" in text
        or "very high" in text
        or "very elevated" in text
    ):
        return 3

    if (
        "above" in text
        or "high" in text
        or "elevated" in text
    ):
        return 2

    try:

        raw = float(
            text
            .replace("mg/dl", "")
            .strip()
        )

        if raw < 200:
            return 1

        if raw < 240:
            return 2

        return 3

    except Exception:

        return None


# ============================================================
# GLUCOSE NORMALIZATION
# ============================================================

def _normalize_glucose(
    value: Any,
):

    if value is None:
        return None

    numeric = _numeric_value(value)

    if numeric is not None:

        numeric_int = int(numeric)

        if numeric_int in (1, 2, 3):
            return numeric_int

    text = str(value).strip().lower()

    if (
        "well above" in text
        or "very high" in text
    ):
        return 3

    if (
        "above" in text
        or "high" in text
        or "elevated" in text
    ):
        return 2

    try:

        raw = float(
            text
            .replace("mg/dl", "")
            .strip()
        )

        if raw < 100:
            return 1

        if raw < 126:
            return 2

        return 3

    except Exception:

        return None


# ============================================================
# PROFILE → MODEL FEATURES
# ============================================================

def _profile_to_features(
    profile: Any,
):

    # Pydantic v2
    if hasattr(profile, "model_dump"):

        data = profile.model_dump()

    # Pydantic v1
    elif hasattr(profile, "dict"):

        data = profile.dict()

    # Dictionary
    elif isinstance(profile, dict):

        data = profile

    # Generic object
    else:

        data = vars(profile)

    values = {

        "age": _numeric_value(
            data.get("age")
        ),

        "gender": _normalize_gender(
            data.get("gender")
        ),

        "height": _numeric_value(
            data.get("height")
        ),

        "weight": _numeric_value(
            data.get("weight")
        ),

        "ap_hi": _numeric_value(
            data.get("ap_hi")
        ),

        "ap_lo": _numeric_value(
            data.get("ap_lo")
        ),

        "cholesterol": _normalize_cholesterol(
            data.get("cholesterol")
        ),

        "gluc": _normalize_glucose(
            data.get(
                "gluc",
                data.get("glucose")
            )
        ),

        "smoke": _numeric_value(
            data.get("smoke")
        ),

        "alco": _numeric_value(
            data.get("alco")
        ),

        "active": _numeric_value(
            data.get("active")
        ),
    }

    return values


# ============================================================
# RISK LEVEL
# ============================================================

def _risk_level(
    probability: float,
):

    if probability < 30:
        return "low"

    if probability < 60:
        return "moderate"

    return "high"


# ============================================================
# SHAP
# ============================================================

def _calculate_shap(
    model,
    X: pd.DataFrame,
):

    try:

        import shap

        explainer = shap.TreeExplainer(model)

        shap_values = explainer.shap_values(X)

        if isinstance(shap_values, list):

            if len(shap_values) > 1:
                values = np.asarray(
                    shap_values[1]
                )[0]

            else:
                values = np.asarray(
                    shap_values[0]
                )[0]

        else:

            values = np.asarray(
                shap_values
            )

            if values.ndim == 3:

                values = values[0, :, -1]

            elif values.ndim == 2:

                values = values[0]

            else:

                values = values.flatten()

        result = []

        for feature, value in zip(
            MODEL_FEATURES,
            values,
        ):

            numeric_value = float(value)

            result.append(
                {
                    "feature": feature,

                    "name": DISPLAY_NAMES.get(
                        feature,
                        feature,
                    ),

                    "shap_value": round(
                        numeric_value,
                        6,
                    ),

                    "direction": (
                        "increases risk"
                        if numeric_value > 0
                        else
                        "decreases risk"
                    ),
                }
            )

        result.sort(
            key=lambda item: abs(
                item["shap_value"]
            ),
            reverse=True,
        )

        return result

    except Exception as exc:

        print(
            "[SHAP Notice] "
            f"{exc}"
        )

        return []


# ============================================================
# FILTER SHAP TO ACTUAL PATIENT DATA
# ============================================================

def _filter_actual_factors(
    shap_details,
    original_values,
):
    """
    Keep only factors for which the patient actually had
    extracted clinical data.

    This prevents an imputed value from being presented as
    an actual patient-specific risk factor.
    """

    actual = []

    for item in shap_details:

        feature = item["feature"]

        if original_values.get(feature) is not None:

            actual.append(item)

    return actual


# ============================================================
# MAIN PREDICTION
# ============================================================

FEATURE_COLUMNS = MODEL_FEATURES

CORE_FIELDS = [
    "age",
    "ap_hi",
    "ap_lo",
    "cholesterol",
]

SUPPLEMENTARY_DEFAULTS = {
    "gender": 1,
    "height": 165,
    "weight": 70,
    "gluc": 1,
    "smoke": 0,
    "alco": 0,
    "active": 1,
}

RISK_THRESHOLDS = {
    "Low":33,
    "Medium":66,
}

_model_cache = None


def _get_model():
    global _model_cache
    if _model_cache is None:
        _model_cache = _load_model()
    return _model_cache


def _age_years_to_days(age_years):
    if age_years is None:
        return None
    return round(age_years * 365.25)


def _is_missing(value):
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    return False


def _is_abnormal(field, value):
    if value is None:
        return False
    if field == "ap_hi":
        return value > 130
    if field == "ap_lo":
        return value > 85
    if field in ("cholesterol", "gluc"):
        return value in (2, 3)
    if field == "smoke":
        return value == 1
    if field == "alco":
        return value == 1
    if field == "active":
        return value == 0
    if field == "age":
        return value >= 55
    return False


def _get_top_factors(model, profile, max_factors=3):
    importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_))

    candidates = [
        field for field in FEATURE_COLUMNS
        if _is_abnormal(field, profile.get(field))
    ]
    candidates.sort(key=lambda f: importances.get(f, 0), reverse=True)

    if candidates:
        return candidates[:max_factors]

    return []


def predict_risk(final_profile):
    """
    Public interface matching the requested missing-data policy.
    """
    if hasattr(final_profile, "model_dump"):
        profile = final_profile.model_dump()
    elif isinstance(final_profile, dict):
        profile = dict(final_profile)
    else:
        profile = dict(final_profile)

    core_values = {
        "age": profile.get("age"),
        "ap_hi": profile.get("ap_hi"),
        "ap_lo": profile.get("ap_lo"),
        "cholesterol": profile.get("cholesterol"),
    }

    missing_core = [
        key for key in CORE_FIELDS if _is_missing(core_values.get(key))
    ]

    if missing_core:
        return {
            "status": "insufficient_data",
            "missing_fields": missing_core,
            "message": (
                "Cannot calculate a reliable risk score — the uploaded "
                f"report(s) did not include: {', '.join(missing_core)}. "
                "These are essential values; please upload a report that "
                "includes them."
            ),
        }

    row = dict(core_values)
    imputed_fields = []

    for field, default in SUPPLEMENTARY_DEFAULTS.items():
        value = profile.get(field)
        if _is_missing(value):
            row[field] = default
            imputed_fields.append(field)
        else:
            row[field] = value

    row["age"] = _age_years_to_days(row["age"])

    model = _get_model()
    feature_vector = pd.DataFrame([row], columns=FEATURE_COLUMNS)
    risk_score = float(model.predict_proba(feature_vector)[0][1])*100

    if risk_score < RISK_THRESHOLDS["Low"]:
        risk_level = "Low"
    elif risk_score < RISK_THRESHOLDS["Medium"]:
        risk_level = "Medium"
    else:
        risk_level = "High"

    top_factors = _get_top_factors(model, profile)

    return {
        "status": "ok",
        "risk_score": round(risk_score, 4),
        "risk_level": risk_level,
        "top_factors": top_factors,
        "top_3_factors": top_factors[:3],
        "imputed_fields": imputed_fields,
    }