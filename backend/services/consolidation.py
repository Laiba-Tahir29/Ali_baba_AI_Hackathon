"""
Layer 3: Profile Consolidation, Longitudinal Consistency & Anomaly Detection
Owner: Person B (rag-llm branch)

Performs clinical reconciliation across multi-encounter reports:
1. LLM Consolidation (Gemini) when GEMINI_API_KEY is available: Reconciles conflicting records,
   extracts latest values, detects longitudinal trends, and flags anomalies.
2. Deterministic Fallback: Sorts encounters by date, extracts latest non-null vitals,
   standardizes categories, and identifies consistently elevated factors (> 50% persistence).
"""

import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional


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


def _is_high_cholesterol(value: Any) -> bool:
    v = _coerce_int(value)
    if v in (2, 3):
        return True
    s = str(value).strip().lower()
    if "above" in s or "high" in s:
        return True
    try:
        val = float(str(value).replace("mg/dL", "").strip())
        return val >= 200.0
    except Exception:
        return False


def _is_high_gluc(value: Any) -> bool:
    v = _coerce_int(value)
    if v in (2, 3):
        return True
    s = str(value).strip().lower()
    if "above" in s or "high" in s:
        return True
    try:
        val = float(str(value).replace("mg/dL", "").strip())
        return val >= 100.0
    except Exception:
        return False


def _is_high_ap_hi(value: Any) -> bool:
    v = _coerce_int(value)
    if v is not None:
        return v >= 130
    try:
        bp_str = str(value)
        if "/" in bp_str:
            sys_val = int(bp_str.split("/")[0].strip())
            return sys_val >= 130
    except Exception:
        pass
    return False


def _format_category(value: Any, default_label: str = "Normal") -> str:
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
        val = float(s.replace("mg/dl", "").strip())
        if val >= 240:
            return "Well Above Normal"
        if val >= 200:
            return "Above Normal"
        return "Normal"
    except Exception:
        return str(value)


def _llm_consolidate(profiles_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Calls Gemini to reconcile multi-encounter profiles and detect longitudinal patterns."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key.startswith("your_"):
        return None

    for model_name in ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite", "gemini-flash-latest"]:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = (
                "You are an expert cardiologist assistant. Reconcile the following historical medical encounter reports "
                "into a single consolidated patient profile. Use the latest valid vitals, resolve conflicting measurements, "
                "and list which factors were consistently elevated across encounters.\n\n"
                f"REPORTS JSON:\n{json.dumps(profiles_list, indent=2)}\n\n"
                "Return a strictly valid JSON object with the following keys:\n"
                "- age (int)\n- gender (1=female, 2=male)\n- height (float cm)\n- weight (float kg)\n"
                "- ap_hi (int systolic BP)\n- ap_lo (int diastolic BP)\n- bp (string e.g. '138/89')\n"
                "- cholesterol (string: 'Normal', 'Above Normal', or 'Well Above Normal')\n"
                "- gluc (int: 1/2/3)\n- glucose (string: 'Normal', 'Above Normal', or 'Well Above Normal')\n"
                "- bmi (float)\n- smoke (0 or 1)\n- smoking (string: 'yes' or 'no')\n"
                "- alco (0 or 1)\n- active (0 or 1)\n- history (string: 'yes' or 'no')\n"
                "- consistent_high_factors (list of string display names matching: 'Systolic Blood Pressure', 'Cholesterol', 'Fasting Glucose', 'Body Mass Index', 'Smoking Status', 'Family CVD History')\n"
                "- anomalies_flagged (list of strings describing any sudden spikes or contradictory findings)\n"
            )
            res = client.models.generate_content(model=model_name, contents=prompt)
            if res and res.text:
                clean = res.text.strip()
                if clean.startswith("```"):
                    clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                parsed = json.loads(clean)
                if isinstance(parsed, dict) and "bp" in parsed and "consistent_high_factors" in parsed:
                    print(f"[Stage 3: LLM Consolidation] Status: [LIVE GEMINI - {model_name}] Anomalies flagged: {parsed.get('anomalies_flagged', [])}")
                    return parsed
        except Exception as e:
            print(f"[Stage 3 Notice] Gemini consolidation attempt {model_name}: {e}")

    return None


def consolidate_profiles(profiles_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Consolidates per-report profiles into a single final profile.
    Tries LLM consolidation with Gemini first, with seamless fallback to deterministic date-sorting.
    """
    if not profiles_list:
        return {
            "age": 50,
            "gender": 1,
            "height": 165.0,
            "weight": 70.0,
            "bp": "120/80",
            "ap_hi": 120,
            "ap_lo": 80,
            "cholesterol": "Normal",
            "gluc": 1,
            "glucose": "Normal",
            "bmi": 25.7,
            "smoking": "no",
            "smoke": 0,
            "alco": 0,
            "active": 1,
            "history": "no",
            "consistent_high_factors": []
        }

    # 1. Try LLM-based reconciliation if available
    llm_result = _llm_consolidate(profiles_list)
    if llm_result:
        return llm_result

    # 2. Deterministic Fallback Engine
    print("[Stage 3: LLM Consolidation] Status: [FALLBACK DETERMINISTIC ENGINE]")
    dated_profiles = [(p, _parse_date(p.get("date"))) for p in profiles_list]
    dated_profiles.sort(key=lambda item: item[1] if item[1] is not None else datetime.min, reverse=True)
    sorted_profiles = [p for p, _ in dated_profiles]

    def latest_value(field: str, transform=None):
        for profile in sorted_profiles:
            if field in profile and profile[field] is not None:
                val = profile[field]
                if transform is not None:
                    val = transform(val)
                if val is not None:
                    return val
        return None

    age = latest_value("age", _coerce_int) or 55
    gender = latest_value("gender", _coerce_int) or 1
    height = latest_value("height", _coerce_float) or 160.0
    weight = latest_value("weight", _coerce_float) or 78.0
    ap_hi = latest_value("ap_hi", _coerce_int) or 138
    ap_lo = latest_value("ap_lo", _coerce_int) or 89
    cholesterol = latest_value("cholesterol")
    gluc = latest_value("gluc") or latest_value("glucose")
    smoke = latest_value("smoke", _yes_no_to_int) or 0
    alco = latest_value("alco", _yes_no_to_int) or 0
    active = latest_value("active", _yes_no_to_int) if latest_value("active") is not None else 1
    history_val = latest_value("history", _yes_no_to_int) or 0

    bmi = round(weight / ((height / 100.0) ** 2), 1) if height and weight else 26.5

    n = len(profiles_list)
    threshold = n / 2.0

    high_cholesterol_count = sum(1 for p in profiles_list if _is_high_cholesterol(p.get("cholesterol")))
    high_gluc_count = sum(1 for p in profiles_list if _is_high_gluc(p.get("gluc") or p.get("glucose")))
    high_bp_count = sum(1 for p in profiles_list if _is_high_ap_hi(p.get("ap_hi") or p.get("bp")))

    consistent_high_factors = []
    if high_bp_count > threshold:
        consistent_high_factors.append("Systolic Blood Pressure")
    if high_cholesterol_count > threshold:
        consistent_high_factors.append("Cholesterol")
    if high_gluc_count > threshold:
        consistent_high_factors.append("Fasting Glucose")
    if bmi >= 30.0:
        consistent_high_factors.append("Body Mass Index")
    if smoke == 1:
        consistent_high_factors.append("Smoking Status")
    if history_val == 1:
        consistent_high_factors.append("Family CVD History")

    bp_formatted = f"{ap_hi}/{ap_lo}"
    chol_formatted = _format_category(cholesterol, "Normal")
    glucose_formatted = _format_category(gluc, "Normal")
    smoking_formatted = "yes" if smoke == 1 else "no"
    history_formatted = "yes" if history_val == 1 else "no"

    return {
        "age": age,
        "gender": gender,
        "height": height,
        "weight": weight,
        "ap_hi": ap_hi,
        "ap_lo": ap_lo,
        "bp": bp_formatted,
        "cholesterol": chol_formatted,
        "gluc": gluc or 1,
        "glucose": glucose_formatted,
        "bmi": bmi,
        "smoke": smoke,
        "smoking": smoking_formatted,
        "alco": alco,
        "active": active,
        "history": history_formatted,
        "consistent_high_factors": consistent_high_factors
    }
