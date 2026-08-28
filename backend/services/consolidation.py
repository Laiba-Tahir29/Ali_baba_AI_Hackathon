"""
Layer 3: Profile Consolidation, Longitudinal Consistency & Anomaly Detection

Owner: Person B (rag-llm branch)

Performs clinical reconciliation across multi-encounter reports:

1. LLM Consolidation (Gemini) when GEMINI_API_KEY is available:
   - Reconciles conflicting records
   - Extracts latest valid values
   - Detects longitudinal trends
   - Flags anomalies

2. Deterministic Fallback:
   - Sorts encounters by date
   - Extracts latest non-null values
   - Standardizes categories
   - Identifies consistently elevated factors

IMPORTANT:
- No fake clinical defaults.
- Missing values remain None / "Unknown".
- Missing smoking does NOT become "no".
- Missing history does NOT become "no".
- Missing BMI does NOT become a fabricated value.
"""

import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================
# DATE PARSING
# ============================================================

def _parse_date(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    date_str = str(value).strip()

    if not date_str:
        return None

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y/%m/%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


# ============================================================
# TYPE COERCION
# ============================================================

def _coerce_int(value: Any) -> Optional[int]:
    if value is None:
        return None

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _yes_no_to_int(value: Any) -> Optional[int]:
    if value is None:
        return None

    s = str(value).strip().lower()

    if s in ("yes", "y", "1", "true", "positive"):
        return 1

    if s in ("no", "n", "0", "false", "negative"):
        return 0

    return None


# ============================================================
# CLINICAL HIGH-VALUE CHECKS
# ============================================================

def _is_high_cholesterol(value: Any) -> bool:
    """
    Cholesterol:
    1 = Normal
    2 = Above Normal
    3 = Well Above Normal

    Raw values:
    >= 200 = elevated
    >= 240 = well above
    """

    if value is None:
        return False

    numeric = _coerce_int(value)

    if numeric in (2, 3):
        return True

    s = str(value).strip().lower()

    if "above" in s or "high" in s:
        return True

    try:
        val = float(
            s.replace("mg/dl", "")
             .replace("mg/dL", "")
             .strip()
        )

        return val >= 200.0

    except (ValueError, TypeError):
        return False


def _is_high_gluc(value: Any) -> bool:
    """
    Glucose:
    1 = Normal
    2 = Above Normal
    3 = Well Above Normal

    Raw fasting glucose:
    >= 100 = elevated
    >= 126 = well above
    """

    if value is None:
        return False

    numeric = _coerce_int(value)

    if numeric in (2, 3):
        return True

    s = str(value).strip().lower()

    if "above" in s or "high" in s:
        return True

    try:
        val = float(
            s.replace("mg/dl", "")
             .replace("mg/dL", "")
             .strip()
        )

        return val >= 100.0

    except (ValueError, TypeError):
        return False


def _is_high_ap_hi(value: Any) -> bool:
    """
    Systolic BP >= 130 is considered elevated
    for this application's risk-factor flagging.
    """

    if value is None:
        return False

    numeric = _coerce_int(value)

    if numeric is not None:
        return numeric >= 130

    try:
        bp_str = str(value).strip()

        if "/" in bp_str:
            systolic = int(bp_str.split("/")[0].strip())
            return systolic >= 130

    except (ValueError, TypeError):
        pass

    return False


# ============================================================
# CATEGORY FORMATTING
# ============================================================

def _format_category(
    value: Any,
    default_label: str = "Unknown"
) -> str:
    """
    Converts cholesterol/glucose values into display labels.

    Missing values remain Unknown.
    """

    if value is None:
        return default_label

    s = str(value).strip().lower()

    if "well above" in s or s == "3":
        return "Well Above Normal"

    if "above" in s or s == "2":
        return "Above Normal"

    if "normal" in s or s == "1":
        return "Normal"

    try:
        val = float(
            s.replace("mg/dl", "")
             .replace("mg/dL", "")
             .strip()
        )

        if val >= 240:
            return "Well Above Normal"

        if val >= 200:
            return "Above Normal"

        return "Normal"

    except (ValueError, TypeError):
        return str(value)


# ============================================================
# GEMINI CONSOLIDATION
# ============================================================

def _llm_consolidate(
    profiles_list: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Uses Gemini to reconcile multiple clinical encounters.

    If Gemini fails or is unavailable, caller uses deterministic
    fallback.
    """

    gemini_key = os.getenv("GEMINI_API_KEY")

    if not gemini_key or gemini_key.startswith("your_"):
        return None

    for model_name in [
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-3.1-flash-lite",
        "gemini-flash-latest",
    ]:

        try:
            from google import genai

            client = genai.Client(api_key=gemini_key)

            prompt = (
                "You are a clinical data reconciliation assistant. "
                "Reconcile the following historical medical encounter "
                "reports into ONE consolidated patient profile.\n\n"

                "RULES:\n"
                "1. Use the latest valid value when multiple encounters "
                "contain the same field.\n"
                "2. Never invent or estimate missing clinical values.\n"
                "3. If a field was never reported, return null.\n"
                "4. Missing smoking must remain null/unknown.\n"
                "5. Missing family history must remain null/unknown.\n"
                "6. Missing BMI must remain null.\n"
                "7. Detect consistently elevated factors.\n"
                "8. Detect contradictory or unusual findings.\n\n"

                f"REPORTS JSON:\n"
                f"{json.dumps(profiles_list, indent=2, default=str)}\n\n"

                "Return ONLY a valid JSON object with these keys:\n"

                "- age: int or null\n"
                "- gender: 1=female, 2=male, or null\n"
                "- height: float cm or null\n"
                "- weight: float kg or null\n"

                "- ap_hi: int systolic BP or null\n"
                "- ap_lo: int diastolic BP or null\n"
                "- bp: string such as '150/95' or null\n"

                "- cholesterol: "
                "'Normal', 'Above Normal', 'Well Above Normal', "
                "or 'Unknown'\n"

                "- gluc: 1, 2, 3, or null\n"

                "- glucose: "
                "'Normal', 'Above Normal', 'Well Above Normal', "
                "or 'Unknown'\n"

                "- bmi: float or null\n"

                "- smoke: 0, 1, or null\n"
                "- smoking: 'yes', 'no', or 'unknown'\n"

                "- alco: 0, 1, or null\n"
                "- active: 0, 1, or null\n"

                "- history: 'yes', 'no', or 'unknown'\n"

                "- consistent_high_factors: list of strings\n"

                "- anomalies_flagged: list of strings\n"
            )

            res = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            if not res or not res.text:
                continue

            clean = res.text.strip()

            # Remove markdown JSON fences if Gemini returns them.
            if clean.startswith("```"):
                lines = clean.splitlines()

                if lines and lines[0].strip().startswith("```"):
                    lines = lines[1:]

                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]

                clean = "\n".join(lines).strip()

            parsed = json.loads(clean)

            if not isinstance(parsed, dict):
                continue

            # ------------------------------------------------
            # Normalize Gemini output
            # ------------------------------------------------

            parsed["age"] = _coerce_int(parsed.get("age"))
            parsed["gender"] = _coerce_int(parsed.get("gender"))

            parsed["height"] = _coerce_float(
                parsed.get("height")
            )

            parsed["weight"] = _coerce_float(
                parsed.get("weight")
            )

            parsed["ap_hi"] = _coerce_int(
                parsed.get("ap_hi")
            )

            parsed["ap_lo"] = _coerce_int(
                parsed.get("ap_lo")
            )

            # BMI must stay None if missing.
            parsed["bmi"] = _coerce_float(
                parsed.get("bmi")
            )

            parsed["gluc"] = _coerce_int(
                parsed.get("gluc")
            )

            parsed["smoke"] = _yes_no_to_int(
                parsed.get("smoke")
            )

            parsed["alco"] = _yes_no_to_int(
                parsed.get("alco")
            )

            parsed["active"] = _yes_no_to_int(
                parsed.get("active")
            )

            history_value = parsed.get("history")

            if history_value is None:
                parsed["history"] = "unknown"
            else:
                history_int = _yes_no_to_int(history_value)

                if history_int == 1:
                    parsed["history"] = "yes"
                elif history_int == 0:
                    parsed["history"] = "no"
                else:
                    parsed["history"] = "unknown"

            # Smoking formatting
            if parsed["smoke"] == 1:
                parsed["smoking"] = "yes"
            elif parsed["smoke"] == 0:
                parsed["smoking"] = "no"
            else:
                parsed["smoking"] = "unknown"

            # BP formatting
            if (
                parsed["ap_hi"] is not None
                and parsed["ap_lo"] is not None
            ):
                parsed["bp"] = (
                    f"{parsed['ap_hi']}/{parsed['ap_lo']}"
                )
            else:
                parsed["bp"] = None

            # Cholesterol formatting
            parsed["cholesterol"] = _format_category(
                parsed.get("cholesterol"),
                "Unknown"
            )

            # Glucose formatting
            parsed["glucose"] = _format_category(
                parsed.get("glucose")
                if parsed.get("glucose") is not None
                else parsed.get("gluc"),
                "Unknown"
            )

            if not isinstance(
                parsed.get("consistent_high_factors"),
                list
            ):
                parsed["consistent_high_factors"] = []

            if not isinstance(
                parsed.get("anomalies_flagged"),
                list
            ):
                parsed["anomalies_flagged"] = []

            print(
                "[Stage 3: LLM Consolidation] "
                f"Status: [LIVE GEMINI - {model_name}]"
            )

            print(
                "[Stage 3] Anomalies:",
                parsed.get("anomalies_flagged", [])
            )

            return parsed

        except Exception as e:

            print(
                "[Stage 3 Notice] "
                f"Gemini consolidation attempt "
                f"{model_name}: {e}"
            )

    return None


# ============================================================
# MAIN CONSOLIDATION
# ============================================================

def consolidate_profiles(
    profiles_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Consolidates per-report profiles into one final profile.

    Priority:
        1. Gemini reconciliation
        2. Deterministic fallback

    IMPORTANT:
        Missing clinical values remain None.
        No fabricated clinical defaults are used.
    """

    # ========================================================
    # EMPTY INPUT
    # ========================================================

    if not profiles_list:

        return {
            "age": None,
            "gender": None,

            "height": None,
            "weight": None,

            "ap_hi": None,
            "ap_lo": None,
            "bp": None,

            "cholesterol": "Unknown",

            "gluc": None,
            "glucose": "Unknown",

            "bmi": None,

            "smoke": None,
            "smoking": "unknown",

            "alco": None,
            "active": None,

            "history": "unknown",

            "consistent_high_factors": [],
            "anomalies_flagged": [],
        }

    # ========================================================
    # 1. GEMINI CONSOLIDATION
    # ========================================================

    llm_result = _llm_consolidate(profiles_list)

    if llm_result:
        return llm_result

    # ========================================================
    # 2. DETERMINISTIC FALLBACK
    # ========================================================

    print(
        "[Stage 3: LLM Consolidation] "
        "Status: [FALLBACK DETERMINISTIC ENGINE]"
    )

    dated_profiles = [
        (
            profile,
            _parse_date(profile.get("date"))
        )
        for profile in profiles_list
    ]

    dated_profiles.sort(
        key=lambda item: (
            item[1]
            if item[1] is not None
            else datetime.min
        ),
        reverse=True
    )

    sorted_profiles = [
        profile
        for profile, _ in dated_profiles
    ]

    # ========================================================
    # LATEST NON-NULL VALUE
    # ========================================================

    def latest_value(
        field: str,
        transform=None
    ):
        for profile in sorted_profiles:

            if field not in profile:
                continue

            value = profile.get(field)

            if value is None:
                continue

            if transform is not None:
                value = transform(value)

            if value is not None:
                return value

        return None

    # ========================================================
    # DEMOGRAPHICS
    # ========================================================

    age = latest_value(
        "age",
        _coerce_int
    )

    gender = latest_value(
        "gender",
        _coerce_int
    )

    height = latest_value(
        "height",
        _coerce_float
    )

    weight = latest_value(
        "weight",
        _coerce_float
    )

    # ========================================================
    # BLOOD PRESSURE
    # ========================================================

    ap_hi = latest_value(
        "ap_hi",
        _coerce_int
    )

    ap_lo = latest_value(
        "ap_lo",
        _coerce_int
    )

    # If ap_hi/ap_lo were not separately extracted,
    # try BP string as fallback.

    if ap_hi is None or ap_lo is None:

        for profile in sorted_profiles:

            bp_value = profile.get("bp")

            if not bp_value:
                continue

            try:
                if "/" in str(bp_value):

                    parts = str(bp_value).split("/")

                    parsed_hi = _coerce_int(
                        parts[0].strip()
                    )

                    parsed_lo = _coerce_int(
                        parts[1].strip()
                    )

                    if ap_hi is None:
                        ap_hi = parsed_hi

                    if ap_lo is None:
                        ap_lo = parsed_lo

                    if (
                        ap_hi is not None
                        and ap_lo is not None
                    ):
                        break

            except Exception:
                continue

    bp_formatted = (
        f"{ap_hi}/{ap_lo}"
        if ap_hi is not None
        and ap_lo is not None
        else None
    )

    # ========================================================
    # CHOLESTEROL
    # ========================================================

    cholesterol_raw = latest_value(
        "cholesterol"
    )

    cholesterol_formatted = _format_category(
        cholesterol_raw,
        "Unknown"
    )

    # ========================================================
    # GLUCOSE
    # ========================================================

    gluc = latest_value("gluc")

    if gluc is None:
        gluc = latest_value("glucose")

    glucose_formatted = _format_category(
        gluc,
        "Unknown"
    )

    # ========================================================
    # BMI
    # ========================================================

    # First preference:
    # BMI explicitly reported in document.

    bmi = latest_value(
        "bmi",
        _coerce_float
    )

    # Only calculate BMI when BOTH height and weight
    # actually exist.

    if (
        bmi is None
        and height is not None
        and weight is not None
        and height > 0
    ):

        bmi = round(
            weight / ((height / 100.0) ** 2),
            1
        )

    # Otherwise BMI stays None.
    # NEVER use an invented default.

    # ========================================================
    # SMOKING
    # ========================================================

    smoke = latest_value(
        "smoke",
        _yes_no_to_int
    )

    # Try textual smoking field if numeric field missing.

    if smoke is None:

        smoke = latest_value(
            "smoking",
            _yes_no_to_int
        )

    if smoke == 1:
        smoking_formatted = "yes"

    elif smoke == 0:
        smoking_formatted = "no"

    else:
        smoking_formatted = "unknown"

    # ========================================================
    # ALCOHOL
    # ========================================================

    alco = latest_value(
        "alco",
        _yes_no_to_int
    )

    # Missing remains None.
    # No fake "no" default.

    # ========================================================
    # PHYSICAL ACTIVITY
    # ========================================================

    active = latest_value(
        "active",
        _yes_no_to_int
    )

    # Missing remains None.

    # ========================================================
    # FAMILY HISTORY
    # ========================================================

    history_raw = latest_value(
        "history"
    )

    history_val = _yes_no_to_int(
        history_raw
    )

    if history_val == 1:
        history_formatted = "yes"

    elif history_val == 0:
        history_formatted = "no"

    else:
        history_formatted = "unknown"

    # ========================================================
    # LONGITUDINAL CONSISTENCY
    # ========================================================

    n = len(profiles_list)

    threshold = n / 2.0

    high_cholesterol_count = sum(
        1
        for profile in profiles_list
        if _is_high_cholesterol(
            profile.get("cholesterol")
        )
    )

    high_glucose_count = sum(
        1
        for profile in profiles_list
        if _is_high_gluc(
            profile.get("gluc")
            if profile.get("gluc") is not None
            else profile.get("glucose")
        )
    )

    high_bp_count = sum(
        1
        for profile in profiles_list
        if _is_high_ap_hi(
            profile.get("ap_hi")
            if profile.get("ap_hi") is not None
            else profile.get("bp")
        )
    )

    consistent_high_factors = []

    if high_bp_count > threshold:
        consistent_high_factors.append(
            "Systolic Blood Pressure"
        )

    if high_cholesterol_count > threshold:
        consistent_high_factors.append(
            "Cholesterol"
        )

    if high_glucose_count > threshold:
        consistent_high_factors.append(
            "Fasting Glucose"
        )

    # BMI is only flagged when BMI actually exists.
    if bmi is not None and bmi >= 30.0:
        consistent_high_factors.append(
            "Body Mass Index"
        )

    # Smoking only flagged when explicitly YES.
    if smoke == 1:
        consistent_high_factors.append(
            "Smoking Status"
        )

    # Family history only flagged when explicitly YES.
    if history_val == 1:
        consistent_high_factors.append(
            "Family CVD History"
        )

    # ========================================================
    # BASIC ANOMALY DETECTION
    # ========================================================

    anomalies_flagged = []

    # Detect contradictory smoking values.
    smoking_values = []

    for profile in profiles_list:

        value = _yes_no_to_int(
            profile.get("smoke")
        )

        if value is None:
            value = _yes_no_to_int(
                profile.get("smoking")
            )

        if value is not None:
            smoking_values.append(value)

    if len(set(smoking_values)) > 1:
        anomalies_flagged.append(
            "Smoking status differs across encounters"
        )

    # Detect contradictory family history.
    history_values = []

    for profile in profiles_list:

        value = _yes_no_to_int(
            profile.get("history")
        )

        if value is not None:
            history_values.append(value)

    if len(set(history_values)) > 1:
        anomalies_flagged.append(
            "Family cardiovascular history differs across encounters"
        )

    # Detect significant BP variation.
    bp_values = []

    for profile in profiles_list:

        value = profile.get("ap_hi")

        if value is None:
            value = profile.get("bp")

        if value is not None:

            if isinstance(value, str) and "/" in value:
                value = value.split("/")[0]

            value = _coerce_int(value)

            if value is not None:
                bp_values.append(value)

    if len(bp_values) >= 2:

        bp_range = max(bp_values) - min(bp_values)

        if bp_range >= 30:
            anomalies_flagged.append(
                "Systolic blood pressure shows a substantial variation across encounters"
            )

    # ========================================================
    # FINAL PROFILE
    # ========================================================

    return {
        "age": age,
        "gender": gender,

        "height": height,
        "weight": weight,

        "ap_hi": ap_hi,
        "ap_lo": ap_lo,
        "bp": bp_formatted,

        "cholesterol": cholesterol_formatted,

        "gluc": gluc,
        "glucose": glucose_formatted,

        "bmi": bmi,

        "smoke": smoke,
        "smoking": smoking_formatted,

        "alco": alco,
        "active": active,

        "history": history_formatted,

        "consistent_high_factors": consistent_high_factors,

        "anomalies_flagged": anomalies_flagged,
    }