
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

def predict_risk(
    consolidated_profile: Any,
):

    print(
        "\n" + "=" * 60
    )

    print(
        "[Risk Model] "
        "Starting risk prediction"
    )

    print(
        "=" * 60
    )

    # ========================================================
    # 1. LOAD MODEL
    # ========================================================

    model = _load_model()

    # ========================================================
    # 2. LOAD IMPUTATION VALUES
    # ========================================================

    imputation_values = (
        _load_imputation_values()
    )

    # ========================================================
    # 3. EXTRACT ACTUAL PATIENT VALUES
    # ========================================================

    original_values = _profile_to_features(
        consolidated_profile
    )

    # IMPORTANT:
    # Keep this dictionary untouched.
    #
    # It represents REAL extracted patient information.
    #
    # None means:
    # "The report did not provide this value."

    print(
        "[Risk Model] "
        "Extracted feature values:"
    )

    for feature in MODEL_FEATURES:

        print(
            f"    {feature}: "
            f"{original_values.get(feature)}"
        )

    # ========================================================
    # 4. IDENTIFY MISSING VALUES
    # ========================================================

    missing_fields = []

    for feature in MODEL_FEATURES:

        if original_values.get(feature) is None:

            missing_fields.append(
                DISPLAY_NAMES.get(
                    feature,
                    feature,
                )
            )

    # ========================================================
    # 5. CREATE SEPARATE ML VALUES
    # ========================================================
    #
    # DO NOT modify original_values.
    #
    # This is the key fix.
    #
    # original_values:
    #     Actual patient data.
    #
    # model_values:
    #     Actual patient data + training imputation.
    #
    # ========================================================

    model_values = dict(
        original_values
    )

    imputed_fields = []

    for feature in MODEL_FEATURES:

        if model_values.get(feature) is None:

            model_values[feature] = (
                imputation_values[feature]
            )

            imputed_fields.append(
                DISPLAY_NAMES.get(
                    feature,
                    feature,
                )
            )

    # ========================================================
    # 6. BUILD MODEL INPUT
    # ========================================================

    X = pd.DataFrame(
        [
            [
                model_values[feature]
                for feature in MODEL_FEATURES
            ]
        ],
        columns=MODEL_FEATURES,
    )

    print(
        "[Risk Model] "
        "Final model input:"
    )

    print(
        X.to_string(
            index=False
        )
    )

    # ========================================================
    # 7. PREDICT PROBABILITY
    # ========================================================

    probability_array = (
        model.predict_proba(X)
    )

    classes = list(
        model.classes_
    )

    if 1 in classes:

        positive_index = classes.index(1)

    else:

        positive_index = len(classes) - 1

    probability = float(
        probability_array[
            0,
            positive_index,
        ]
    )

    risk_score = round(
        probability * 100,
        1,
    )

    # ========================================================
    # 8. RISK LEVEL
    # ========================================================

    risk_level = _risk_level(
        risk_score
    )

    # ========================================================
    # 9. SHAP
    # ========================================================

    all_shap_details = _calculate_shap(
        model,
        X,
    )

    # IMPORTANT:
    #
    # SHAP was calculated using the actual model input,
    # which may contain imputed values.
    #
    # Therefore we must NOT blindly present every SHAP
    # feature as an observed clinical factor.
    #

    actual_shap_details = _filter_actual_factors(
        all_shap_details,
        original_values,
    )

    # ========================================================
    # 10. TOP FACTORS
    # ========================================================

    top_actual = actual_shap_details[:3]

    top_factors = [
        item["feature"]
        for item in top_actual
    ]

    top_3_factors = [
        item["name"]
        for item in top_actual
    ]

    # ========================================================
    # 11. FALLBACK IF SHAP IS UNAVAILABLE
    # ========================================================

    if not top_3_factors:

        # If no actual features are available,
        # do not invent risk factors.

        top_3_factors = []

        top_factors = []

    # ========================================================
    # 12. DATA SUFFICIENCY
    # ========================================================

    available_count = sum(
        value is not None
        for value in original_values.values()
    )

    required_core_features = [
        "age",
        "ap_hi",
        "ap_lo",
    ]

    core_available = all(
        original_values.get(feature) is not None
        for feature in required_core_features
    )

    insufficient_data = (
        not core_available
    )

    # ========================================================
    # 13. MESSAGE
    # ========================================================

    if imputed_fields:

        message = (
            "Risk calculated using the trained "
            "Random Forest model. Missing features "
            "were imputed internally using "
            "training-data statistics. "
            "Imputed values are not treated as "
            "observed patient measurements."
        )

    else:

        message = (
            "Risk calculated using the trained "
            "Random Forest model using extracted "
            "patient data."
        )

    # ========================================================
    # 14. FINAL RESULT
    # ========================================================

    result = {

        "risk_score":
            risk_score,

        "risk_level":
            risk_level,

        "top_3_factors":
            top_3_factors,

        "top_factors":
            top_factors,

        "shap_details":
            actual_shap_details,

        "insufficient_data":
            insufficient_data,

        "missing_fields":
            missing_fields,

        "imputed_fields":
            imputed_fields,

        "available_feature_count":
            available_count,

        "message":
            message,
    }

    # ========================================================
    # 15. DEBUG OUTPUT
    # ========================================================

    print(
        "[Risk Model] "
        f"Risk Score: {risk_score}%"
    )

    print(
        "[Risk Model] "
        f"Risk Level: {risk_level}"
    )

    print(
        "[Risk Model] "
        f"Actual Top Factors: {top_3_factors}"
    )

    print(
        "[Risk Model] "
        f"Missing Fields: {missing_fields}"
    )

    print(
        "[Risk Model] "
        f"Internally Imputed Fields: "
        f"{imputed_fields}"
    )

    print(
        "=" * 60
    )

    print(
        "[Risk Model] "
        "Prediction completed"
    )

    print(
        "=" * 60
    )

    return result

