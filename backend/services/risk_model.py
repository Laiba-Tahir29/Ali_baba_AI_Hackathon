from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================
# Project structure:
#
# Ali_baba_AI_Hackathon/
# ├── backend/
# │   ├── models/
# │   │   └── cardio_risk_model.pkl
# │   └── services/
# │       └── risk_model.py
# └── processed/
#     └── imputation_values.csv
#
# From:
# backend/services/risk_model.py
#
# parents[0] = services
# parents[1] = backend
# parents[2] = project root

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

    print(f"[Risk Model] Loading model from: {MODEL_PATH}")

    return joblib.load(MODEL_PATH)


# ============================================================
# LOAD TRAINING-DATA IMPUTATION VALUES
# ============================================================

def _load_imputation_values() -> Dict[str, float]:

    if not IMPUTATION_PATH.exists():
        raise FileNotFoundError(
            f"Could not find imputation file at: {IMPUTATION_PATH}"
        )

    df = pd.read_csv(IMPUTATION_PATH)

    print(
        f"[Risk Model] Loading imputation values from: "
        f"{IMPUTATION_PATH}"
    )

    print(
        f"[Risk Model] Imputation columns: "
        f"{list(df.columns)}"
    )

    result: Dict[str, float] = {}

    # --------------------------------------------------------
    # Your actual file format:
    #
    # feature,imputation_value
    # age,19701.0
    # gender,1.0
    # ...
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
            except (TypeError, ValueError):
                print(
                    f"[Risk Model] Invalid imputation "
                    f"value for {feature}: {value}"
                )

    # --------------------------------------------------------
    # Backward compatibility:
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
            except (TypeError, ValueError):
                pass

    # --------------------------------------------------------
    # Single-row fallback
    # --------------------------------------------------------

    else:

        for feature in MODEL_FEATURES:

            if feature in df.columns:

                value = df[feature].iloc[0]

                if pd.isna(value):
                    continue

                try:
                    result[feature] = float(value)
                except (TypeError, ValueError):
                    pass

    # --------------------------------------------------------
    # Verify ALL features exist
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
# GENERIC NUMERIC NORMALIZATION
# ============================================================

def _numeric_value(value: Any):

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

        # Remove common units
        text = text.replace("mg/dl", "")
        text = text.replace("mmhg", "")
        text = text.replace("kg", "")
        text = text.replace("cm", "")

        text = text.strip()

        return float(text)

    except Exception:
        return None


# ============================================================
# GENDER NORMALIZATION
# ============================================================

def _normalize_gender(value: Any):

    if value is None:
        return None

    # Numeric dataset values
    try:

        if isinstance(value, (int, float)):

            numeric = int(value)

            if numeric in (1, 2):
                return numeric

            if numeric == 0:
                return 1

    except Exception:
        pass

    text = str(value).strip().lower()

    if text in {
        "male",
        "m",
        "man",
    }:
        return 1

    if text in {
        "female",
        "f",
        "woman",
    }:
        return 2

    return None


# ============================================================
# CHOLESTEROL NORMALIZATION
# ============================================================

def _normalize_cholesterol(value: Any):

    if value is None:
        return None

    text = str(value).strip().lower()

    # Dataset-style categorical value
    try:

        numeric = float(text)

        if numeric in (1, 2, 3):
            return int(numeric)

    except Exception:
        pass

    # Actual cholesterol measurement
    try:

        numeric = float(
            text
            .replace("mg/dl", "")
            .strip()
        )

        if numeric < 200:
            return 1

        if numeric < 240:
            return 2

        return 3

    except Exception:
        pass

    # Text categories
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

    if (
        "normal" in text
        or "good" in text
    ):
        return 1

    return None


# ============================================================
# GLUCOSE NORMALIZATION
# ============================================================

def _normalize_glucose(value: Any):

    if value is None:
        return None

    text = str(value).strip().lower()

    # Dataset categorical values
    try:

        numeric = float(text)

        if numeric in (1, 2, 3):
            return int(numeric)

    except Exception:
        pass

    # Actual glucose measurement
    try:

        numeric = float(
            text
            .replace("mg/dl", "")
            .strip()
        )

        if numeric < 100:
            return 1

        if numeric < 126:
            return 2

        return 3

    except Exception:
        pass

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

    if (
        "normal" in text
        or "good" in text
    ):
        return 1

    return None


# ============================================================
# PROFILE → 11 MODEL FEATURES
# ============================================================

def _profile_to_features(profile: Any):

    # Pydantic model
    if hasattr(profile, "model_dump"):
        data = profile.model_dump()

    # Older Pydantic compatibility
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

def _risk_level(probability: float):

    if probability < 30:
        return "low"

    if probability < 60:
        return "moderate"

    return "high"


# ============================================================
# SHAP
# ============================================================

def _calculate_shap(model, X: pd.DataFrame):

    try:

        import shap

        explainer = shap.TreeExplainer(model)

        shap_values = explainer.shap_values(X)

        # ----------------------------------------------------
        # Different SHAP versions return different shapes.
        # Handle all common binary-class RF formats.
        # ----------------------------------------------------

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

                # samples, features, classes
                values = values[
                    0,
                    :,
                    -1
                ]

            elif values.ndim == 2:

                # samples, features
                values = values[0]

            else:

                values = values.flatten()

        result = []

        for feature, value in zip(
            MODEL_FEATURES,
            values
        ):

            numeric_value = float(value)

            result.append(
                {
                    "feature": feature,

                    "name": DISPLAY_NAMES.get(
                        feature,
                        feature
                    ),

                    "shap_value": round(
                        numeric_value,
                        6
                    ),

                    "direction": (
                        "increases risk"
                        if numeric_value > 0
                        else "decreases risk"
                    ),
                }
            )

        result.sort(
            key=lambda item: abs(
                item["shap_value"]
            ),
            reverse=True
        )

        return result

    except Exception as exc:

        print(
            f"[SHAP Notice] {exc}"
        )

        return []


# ============================================================
# MAIN RISK PREDICTION
# ============================================================

def predict_risk(
    consolidated_profile: Any
):

    print("\n" + "=" * 60)
    print("[Risk Model] Starting risk prediction")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Load trained Random Forest
    # --------------------------------------------------------

    model = _load_model()

    # --------------------------------------------------------
    # 2. Load training-data imputation values
    # --------------------------------------------------------

    imputation_values = (
        _load_imputation_values()
    )

    # --------------------------------------------------------
    # 3. FINAL PROFILE → 11 MODEL FEATURES
    # --------------------------------------------------------

    feature_values = (
        _profile_to_features(
            consolidated_profile
        )
    )

    print(
        "[Risk Model] Extracted feature values:"
    )

    for feature in MODEL_FEATURES:

        print(
            f"    {feature}: "
            f"{feature_values.get(feature)}"
        )

    # --------------------------------------------------------
    # 4. Detect missing values BEFORE imputation
    # --------------------------------------------------------

    missing_fields = []
    imputed_fields = []

    for feature in MODEL_FEATURES:

        if feature_values.get(feature) is None:

            missing_fields.append(
                DISPLAY_NAMES.get(
                    feature,
                    feature
                )
            )

    # --------------------------------------------------------
    # 5. TRAINING-DATA IMPUTATION
    # --------------------------------------------------------

    for feature in MODEL_FEATURES:

        value = feature_values.get(
            feature
        )

        if value is None:

            feature_values[feature] = (
                imputation_values[feature]
            )

            imputed_fields.append(
                DISPLAY_NAMES.get(
                    feature,
                    feature
                )
            )

    # --------------------------------------------------------
    # 6. Create DataFrame in EXACT training order
    # --------------------------------------------------------

    X = pd.DataFrame(
        [
            [
                feature_values[feature]
                for feature in MODEL_FEATURES
            ]
        ],
        columns=MODEL_FEATURES
    )

    print(
        "[Risk Model] Final model input:"
    )

    print(X.to_string(index=False))

    # --------------------------------------------------------
    # 7. Random Forest probability
    # --------------------------------------------------------

    probability_array = model.predict_proba(X)

    classes = list(
        model.classes_
    )

    if 1 in classes:

        positive_index = classes.index(1)

    else:

        # Fallback: last class
        positive_index = len(classes) - 1

    probability = float(
        probability_array[
            0,
            positive_index
        ]
    )

    risk_score = round(
        probability * 100,
        1
    )

    # --------------------------------------------------------
    # 8. Risk level
    # --------------------------------------------------------

    risk_level = _risk_level(
        risk_score
    )

    # --------------------------------------------------------
    # 9. SHAP explanations
    # --------------------------------------------------------

    shap_details = _calculate_shap(
        model,
        X
    )

    top_factors = [
        item["feature"]
        for item in shap_details[:3]
    ]

    top_3_factors = [
        item["name"]
        for item in shap_details[:3]
    ]

    # --------------------------------------------------------
    # 10. Final output
    # --------------------------------------------------------

    result = {

        "risk_score": risk_score,

        "risk_level": risk_level,

        "top_3_factors": top_3_factors,

        "top_factors": top_factors,

        "shap_details": shap_details,

        "insufficient_data": False,

        "missing_fields": missing_fields,

        "imputed_fields": imputed_fields,

        "message": (
            "Risk calculated using the trained "
            "Random Forest model. Missing model "
            "features were imputed using "
            "training-data statistics."
            if imputed_fields
            else
            "Risk calculated using the trained "
            "Random Forest model using extracted "
            "patient data."
        ),
    }

    print(
        f"[Risk Model] Risk Score: "
        f"{risk_score}%"
    )

    print(
        f"[Risk Model] Risk Level: "
        f"{risk_level}"
    )

    print(
        f"[Risk Model] Top Factors: "
        f"{top_3_factors}"
    )

    print("=" * 60)
    print("[Risk Model] Prediction completed")
    print("=" * 60)

    return result