"""
consolidation.py
-----------------
Person B (RAG + LLM) — Profile consolidation module.

Combines multiple per-report profiles (from extraction.py's extract_profile)
into a single final_profile dict shaped to match the training dataset schema:

    id;age;gender;height;weight;ap_hi;ap_lo;cholesterol;gluc;smoke;alco;active;cardio

INTERFACE CONTRACT:
    consolidate_profiles(profiles_list) -> final_profile
        {age, gender, height, weight, ap_hi, ap_lo, cholesterol, gluc,
         smoke, alco, active, history, consistent_high_factors: [...]}

IMPORTANT — AGE UNIT NOTE:
    'age' here is in YEARS (as extracted from the report text). The dataset
    stores age in DAYS. Whoever builds predict_risk(final_profile) must
    convert before calling the model:
        age_days = round(final_profile["age"] * 365.25)
    This is intentionally NOT converted here, so final_profile stays in
    human-readable units for consolidation logic and for generate_explanation().

IMPORTANT — 'history' NOTE:
    'history' (family history) is included in final_profile for
    generate_explanation()'s context, but it is NOT a column in the training
    dataset. Do not feed it into predict_risk() — drop it (or ignore it)
    when building the model input.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


def _parse_date(value: Any) -> Optional[datetime]:
    """Best-effort parse a date string into a datetime object."""
    if value is None:
        return None
    date_str = str(value).strip()
    if not date_str:
        return None

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",   # DD/MM/YYYY tried FIRST — matches Pakistan/international
                       # date convention used in these medical reports.
        "%m/%d/%Y",   # US format, fallback only (ambiguous for day<=12)
        "%d %B %Y",   # "10 January 2026" — common in report headers
        "%d %b %Y",   # "10 Jan 2026" — common in report headers
        "%B %d, %Y",  # "January 10, 2026"
        "%b %d, %Y",  # "Jan 10, 2026"
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _coerce_int(value: Any) -> Optional[int]:
    """Safely coerce a value to int; return None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _coerce_float(value: Any) -> Optional[float]:
    """Safely coerce a value to float; return None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _yes_no_to_int(value: Any) -> Optional[int]:
    """Convert yes/no style values to 1/0; return None if not parseable."""
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in ("yes", "y", "1", "true"):
        return 1
    if s in ("no", "n", "0", "false"):
        return 0
    return None


def _is_high_cholesterol(value: Any) -> bool:
    """Cholesterol is categorical (1/2/3) — 'high' means above normal (2 or 3)."""
    return _coerce_int(value) in (2, 3)


def _is_high_gluc(value: Any) -> bool:
    """Glucose is categorical (1/2/3) — 'high' means above normal (2 or 3)."""
    return _coerce_int(value) in (2, 3)


def _is_high_ap_hi(value: Any) -> bool:
    """Systolic BP (ap_hi) above 130 is considered high."""
    v = _coerce_int(value)
    return v is not None and v > 130


def consolidate_profiles(profiles_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Consolidate a list of per-report profiles into one final_profile dict,
    shaped to match the training dataset's columns as closely as possible.

    The latest report (by date) supplies each field's value. Fields missing
    in some reports are skipped for that field (falls through to an older
    report, or None if never present). consistent_high_factors lists fields
    that were high in more than half of the reports, even if the latest
    value is normal.

    Args:
        profiles_list: List of profile dicts returned by extract_profile().

    Returns:
        A dict with keys:
            age (years), gender, height, weight, ap_hi, ap_lo, cholesterol,
            gluc, smoke, alco, active, history, consistent_high_factors.
    """
    empty_profile = {
        "age": None,
        "gender": None,
        "height": None,
        "weight": None,
        "ap_hi": None,
        "ap_lo": None,
        "cholesterol": None,
        "gluc": None,
        "smoke": None,
        "alco": None,
        "active": None,
        "history": None,
        "consistent_high_factors": [],
    }

    if not profiles_list:
        return empty_profile

    # Sort reports by date, most recent first. Reports without a parseable
    # date fall back to the end of the sorted list.
    dated_profiles = [(p, _parse_date(p.get("date"))) for p in profiles_list]
    dated_profiles.sort(key=lambda item: item[1] if item[1] is not None else datetime.min, reverse=True)
    sorted_profiles = [p for p, _ in dated_profiles]

    def latest_value(field: str, transform=None):
        """Return the first non-None transformed value from the sorted reports."""
        for profile in sorted_profiles:
            if field in profile and profile[field] is not None:
                value = profile[field]
                if transform is not None:
                    value = transform(value)
                if value is not None:
                    return value
        return None

    final_profile = {
        "age": latest_value("age", _coerce_int),  # years — convert to days before predict_risk
        "gender": latest_value("gender", _coerce_int),
        "height": latest_value("height", _coerce_float),
        "weight": latest_value("weight", _coerce_float),
        "ap_hi": latest_value("ap_hi", _coerce_int),
        "ap_lo": latest_value("ap_lo", _coerce_int),
        "cholesterol": latest_value("cholesterol", _coerce_int),
        "gluc": latest_value("gluc", _coerce_int),
        "smoke": latest_value("smoke", _yes_no_to_int) or latest_value("smoke", _coerce_int),
        "alco": latest_value("alco", _yes_no_to_int) or latest_value("alco", _coerce_int),
        "active": latest_value("active", _yes_no_to_int) or latest_value("active", _coerce_int),
        "history": latest_value("history", _yes_no_to_int),  # NOT a dataset column — context only
        "consistent_high_factors": [],
    }

    n = len(profiles_list)
    threshold = n / 2  # strictly more than half

    high_cholesterol_count = sum(1 for p in profiles_list if _is_high_cholesterol(p.get("cholesterol")))
    high_gluc_count = sum(1 for p in profiles_list if _is_high_gluc(p.get("gluc")))
    high_ap_hi_count = sum(1 for p in profiles_list if _is_high_ap_hi(p.get("ap_hi")))

    consistent_high_factors = []
    if high_cholesterol_count > threshold:
        consistent_high_factors.append("cholesterol")
    if high_gluc_count > threshold:
        consistent_high_factors.append("gluc")
    if high_ap_hi_count > threshold:
        consistent_high_factors.append("ap_hi")

    final_profile["consistent_high_factors"] = consistent_high_factors
    return final_profile


# ---- Quick manual test ----
if __name__ == "__main__":
    sample_profiles = [
        {
            "date": "12/03/2024", "doctor": "Dr. Ahmed Khan", "age": 55, "gender": 1,
            "height": 165, "weight": 78, "ap_hi": 145, "ap_lo": 95,
            "cholesterol": 2, "gluc": 1, "smoke": 1, "alco": 0, "active": 1,
            "history": "yes",
        },
        {
            "date": "20/06/2024", "doctor": "Dr. Sara Ali", "age": 55, "gender": 1,
            "height": 165, "weight": 79, "ap_hi": 138, "ap_lo": 88,
            "cholesterol": 3, "gluc": 1, "smoke": 1, "alco": 0, "active": 1,
            "history": "yes",
        },
    ]
    result = consolidate_profiles(sample_profiles)
    import json
    print(json.dumps(result, indent=2))