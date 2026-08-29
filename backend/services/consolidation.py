"""
Layer 3: Clinical Profile Consolidation

Purpose:
    Consolidate multiple extracted medical encounters into one
    latest-valid patient profile.

Rules:
    - Missing values ALWAYS remain None.
    - Never invent clinical defaults.
    - Latest available value is selected per field.
    - Persistent high factors are calculated only from
      actually reported values.
    - Anomalies are calculated only when both compared
      values actually exist.
    - ALWAYS return a FinalProfile Pydantic object.
"""

from typing import List, Dict, Any, Optional

from ..models.schemas import FinalProfile


# ============================================================
# HELPERS
# ============================================================

def _to_dict(profile: Any) -> Dict[str, Any]:
    """Convert Pydantic model/dict/object to dictionary."""

    if profile is None:
        return {}

    if isinstance(profile, dict):
        return dict(profile)

    if hasattr(profile, "model_dump"):
        return profile.model_dump()

    if hasattr(profile, "dict"):
        return profile.dict()

    try:
        return vars(profile)
    except Exception:
        return {}


def _is_valid(value: Any) -> bool:
    """
    A value is valid only if it is actually present.

    None and empty strings are considered missing.
    Zero is a valid value.
    """

    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return True


def _latest_valid(
    reports: List[Dict[str, Any]],
    field: str,
) -> Any:
    """
    Return the newest non-missing value.

    Reports are expected to be in chronological/document order.
    """

    for report in reversed(reports):

        value = report.get(field)

        if _is_valid(value):
            return value

    # IMPORTANT:
    # Never create a default value.
    return None


def _numeric(value: Any) -> Optional[float]:
    """Safely convert a value to float."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# CONSISTENT HIGH FACTORS
# ============================================================

def _high_factor_names(
    reports: List[Dict[str, Any]]
) -> List[str]:
    """
    Detect factors that are high in every encounter where
    that factor was actually reported.

    Missing values are completely ignored.

    Example:

        Report 1 cholesterol = None
        Report 2 cholesterol = 225
        Report 3 cholesterol = 252

    Cholesterol is NOT marked consistently high because
    there are not at least two valid cholesterol observations.
    """

    if len(reports) < 2:
        return []

    high_counts = {
        "ap_hi": 0,
        "ap_lo": 0,
        "cholesterol": 0,
        "gluc": 0,
    }

    valid_counts = {
        "ap_hi": 0,
        "ap_lo": 0,
        "cholesterol": 0,
        "gluc": 0,
    }

    for report in reports:

        # ----------------------------------------------------
        # SYSTOLIC
        # ----------------------------------------------------

        ap_hi = _numeric(report.get("ap_hi"))

        if ap_hi is not None:

            valid_counts["ap_hi"] += 1

            if ap_hi >= 140:
                high_counts["ap_hi"] += 1

        # ----------------------------------------------------
        # DIASTOLIC
        # ----------------------------------------------------

        ap_lo = _numeric(report.get("ap_lo"))

        if ap_lo is not None:

            valid_counts["ap_lo"] += 1

            if ap_lo >= 90:
                high_counts["ap_lo"] += 1

        # ----------------------------------------------------
        # CHOLESTEROL
        #
        # 1 = Normal
        # 2 = Above Normal
        # 3 = Well Above Normal
        # ----------------------------------------------------

        cholesterol = _numeric(
            report.get("cholesterol")
        )

        if cholesterol is not None:

            valid_counts["cholesterol"] += 1

            if cholesterol >= 2:
                high_counts["cholesterol"] += 1

        # ----------------------------------------------------
        # GLUCOSE
        #
        # 1 = Normal
        # 2 = Above Normal
        # 3 = Well Above Normal
        # ----------------------------------------------------

        gluc = _numeric(
            report.get("gluc")
        )

        if gluc is not None:

            valid_counts["gluc"] += 1

            if gluc >= 2:
                high_counts["gluc"] += 1

    # --------------------------------------------------------
    # Persistent high factor
    #
    # Require:
    #   - at least 2 actual observations
    #   - every available observation is high
    #
    # Missing observations are NOT treated as normal.
    # --------------------------------------------------------

    display_names = {
        "ap_hi": "Systolic Blood Pressure",
        "ap_lo": "Diastolic Blood Pressure",
        "cholesterol": "Cholesterol",
        "gluc": "Fasting Glucose",
    }

    factors = []

    for field in display_names:

        valid = valid_counts[field]
        high = high_counts[field]

        if valid >= 2 and high == valid:

            factors.append(
                display_names[field]
            )

    return factors


# ============================================================
# ANOMALY DETECTION
# ============================================================

def _detect_anomalies(
    reports: List[Dict[str, Any]]
) -> List[str]:
    """
    Detect sudden changes between consecutive encounters.

    Missing values are ignored.
    """

    if len(reports) < 2:
        return []

    anomalies = []

    def add_once(message: str):

        if message not in anomalies:
            anomalies.append(message)

    for previous, current in zip(
        reports,
        reports[1:]
    ):

        # ----------------------------------------------------
        # SYSTOLIC BP
        # ----------------------------------------------------

        old_value = _numeric(
            previous.get("ap_hi")
        )

        new_value = _numeric(
            current.get("ap_hi")
        )

        if (
            old_value is not None
            and new_value is not None
        ):

            if abs(new_value - old_value) >= 30:

                add_once(
                    "Sudden change in "
                    "Systolic Blood Pressure"
                )

        # ----------------------------------------------------
        # DIASTOLIC BP
        # ----------------------------------------------------

        old_value = _numeric(
            previous.get("ap_lo")
        )

        new_value = _numeric(
            current.get("ap_lo")
        )

        if (
            old_value is not None
            and new_value is not None
        ):

            if abs(new_value - old_value) >= 20:

                add_once(
                    "Sudden change in "
                    "Diastolic Blood Pressure"
                )

        # ----------------------------------------------------
        # CHOLESTEROL CATEGORY
        # ----------------------------------------------------

        old_value = _numeric(
            previous.get("cholesterol")
        )

        new_value = _numeric(
            current.get("cholesterol")
        )

        if (
            old_value is not None
            and new_value is not None
        ):

            if old_value != new_value:

                add_once(
                    "Change in Cholesterol category"
                )

        # ----------------------------------------------------
        # GLUCOSE CATEGORY
        # ----------------------------------------------------

        old_value = _numeric(
            previous.get("gluc")
        )

        new_value = _numeric(
            current.get("gluc")
        )

        if (
            old_value is not None
            and new_value is not None
        ):

            if old_value != new_value:

                add_once(
                    "Change in Glucose category"
                )

    return anomalies


# ============================================================
# MAIN CONSOLIDATION
# ============================================================

def consolidate_profiles(
    profiles: List[Any]
) -> FinalProfile:
    """
    Consolidate extracted medical encounters.

    ALWAYS returns FinalProfile.

    Missing values remain None.
    """

    print(
        "\n============================================================"
    )

    print(
        "[Consolidation] Starting profile consolidation"
    )

    print(
        "============================================================"
    )

    # --------------------------------------------------------
    # Empty input
    # --------------------------------------------------------

    if not profiles:

        print(
            "[Consolidation] No profiles supplied."
        )

        return FinalProfile()

    # --------------------------------------------------------
    # Convert input to dictionaries
    # --------------------------------------------------------

    reports: List[Dict[str, Any]] = []

    for profile in profiles:

        data = _to_dict(profile)

        if data:
            reports.append(data)

    if not reports:

        print(
            "[Consolidation] No valid report objects found."
        )

        return FinalProfile()

    print(
        f"[Consolidation] Processing "
        f"{len(reports)} encounter(s)."
    )

    # ========================================================
    # LATEST VALID VALUES
    # ========================================================

    age = _latest_valid(
        reports,
        "age"
    )

    gender = _latest_valid(
        reports,
        "gender"
    )

    height = _latest_valid(
        reports,
        "height"
    )

    weight = _latest_valid(
        reports,
        "weight"
    )

    ap_hi = _latest_valid(
        reports,
        "ap_hi"
    )

    ap_lo = _latest_valid(
        reports,
        "ap_lo"
    )

    bmi = _latest_valid(
        reports,
        "bmi"
    )

    cholesterol = _latest_valid(
        reports,
        "cholesterol"
    )

    gluc = _latest_valid(
        reports,
        "gluc"
    )

    smoke = _latest_valid(
        reports,
        "smoke"
    )

    alco = _latest_valid(
        reports,
        "alco"
    )

    active = _latest_valid(
        reports,
        "active"
    )

    history = _latest_valid(
        reports,
        "history"
    )

    # ========================================================
    # DISPLAY FIELDS
    # ========================================================

    # --------------------------------------------------------
    # Blood pressure display
    # --------------------------------------------------------

    bp = None

    if (
        ap_hi is not None
        and ap_lo is not None
    ):
        bp = f"{ap_hi}/{ap_lo}"

    # --------------------------------------------------------
    # Glucose display
    # --------------------------------------------------------

    glucose = None

    gluc_num = _numeric(gluc)

    if gluc_num is not None:

        glucose_map = {
            1: "Normal",
            2: "Above Normal",
            3: "Well Above Normal",
        }

        glucose = glucose_map.get(
            int(gluc_num)
        )

    # --------------------------------------------------------
    # Smoking display
    # --------------------------------------------------------

    smoking = None

    smoke_num = _numeric(smoke)

    if smoke_num is not None:

        if smoke_num == 1:
            smoking = "Yes"

        elif smoke_num == 0:
            smoking = "No"

    # ========================================================
    # MULTI-ENCOUNTER ANALYSIS
    # ========================================================

    consistent_high_factors = (
        _high_factor_names(
            reports
        )
    )

    anomalies_flagged = (
        _detect_anomalies(
            reports
        )
    )

    # ========================================================
    # FINAL PROFILE
    # ========================================================

    consolidated = FinalProfile(

        age=age,

        gender=gender,

        height=height,

        weight=weight,

        ap_hi=ap_hi,

        ap_lo=ap_lo,

        bp=bp,

        cholesterol=cholesterol,

        gluc=gluc,

        glucose=glucose,

        bmi=bmi,

        smoke=smoke,

        smoking=smoking,

        alco=alco,

        active=active,

        history=history,

        consistent_high_factors=(
            consistent_high_factors
        ),

        anomalies_flagged=(
            anomalies_flagged
        ),
    )

    # ========================================================
    # DEBUG
    # ========================================================

    print(
        "\n[Consolidation] FINAL PROFILE:"
    )

    print(
        consolidated.model_dump()
    )

    print(
        "\n[Consolidation] Consistent high factors:",
        consolidated.consistent_high_factors
    )

    print(
        "[Consolidation] Anomalies:",
        consolidated.anomalies_flagged
    )

    print(
        "\n[Consolidation] Completed successfully."
    )

    print(
        "============================================================\n"
    )

    # ========================================================
    # CRITICAL
    # ========================================================
    #
    # Return the OBJECT, NOT a dictionary.
    #
    # analyze.py does:
    #
    # consolidated.consistent_high_factors
    #
    # Therefore this MUST remain:
    #
    return consolidated