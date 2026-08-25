"""
extraction.py
-------------
Person B (RAG + LLM) — Medical profile extraction module.

Uses an LLM to parse raw PDF medical text into a list of per-report profile
dictionaries. Reports may span multiple dates/doctors for the same patient.

INTERFACE CONTRACT (aligned to the actual training dataset schema —
id;age;gender;height;weight;ap_hi;ap_lo;cholesterol;gluc;smoke;alco;active;cardio):

    extract_profile(pdf_path) -> List[Dict]
        Each dict has these keys:
            date, doctor          -> metadata only, NOT fed to predict_risk
            age                   -> age in YEARS as written in the report
                                      (dataset stores age in DAYS — whoever
                                      builds predict_risk must convert
                                      years -> days before calling the model,
                                      e.g. age_days = round(age_years * 365.25))
            gender                -> 1 or 2 if stated in the report, else null
                                      (report may not always state this)
            height, weight        -> raw numbers (cm, kg) if given, else null
            ap_hi, ap_lo           -> systolic / diastolic blood pressure,
                                      as separate integer fields (NOT a
                                      combined "140/90" string)
            cholesterol            -> 1 (normal), 2 (above normal), or
                                      3 (well above normal) — CATEGORICAL,
                                      matching the dataset's encoding
            gluc                   -> same 1/2/3 categorical encoding
            smoke, alco, active     -> 0 or 1
            history                -> family history, "yes"/"no" — kept for
                                      generate_explanation() context only;
                                      NOT a dataset column, do not feed to
                                      predict_risk directly

    This shape is designed so consolidate_profiles()'s output (final_profile)
    can be handed almost directly to predict_risk(), except for the
    age years->days conversion noted above.
"""

import json
from typing import Any, Dict, List, Optional

from extract_text import extract_text
from utils import clean_json_response, get_gemini_model


SYSTEM_INSTRUCTION = (
    "The text below may contain multiple medical reports from different dates/doctors "
    "for the same patient. Some of this text may have come from OCR, so tolerate minor "
    "character/spelling errors and use medical context to infer the correct value. "
    "Identify each separate report. For each report, extract these exact fields:\n"
    "- date, doctor\n"
    "- age (as a plain integer, in YEARS, exactly as stated or calculable from the report)\n"
    "- gender (1 or 2, ONLY if explicitly stated in the report; otherwise null — do not guess)\n"
    "- height (cm, if given, else null), weight (kg, if given, else null)\n"
    "- ap_hi (systolic blood pressure, integer, e.g. from '140/90' this is 140)\n"
    "- ap_lo (diastolic blood pressure, integer, e.g. from '140/90' this is 90)\n"
    "- cholesterol: map the report's wording to a category: "
    "1 = normal, 2 = above normal, 3 = well above normal. "
    "If a raw lab value with units is given, use standard medical ranges to decide the "
    "category (do not return the raw number).\n"
    "- gluc: same mapping (1 = normal, 2 = above normal, 3 = well above normal) for glucose\n"
    "- smoke (0 or 1)\n"
    "- alco: alcohol consumption (0 = no/rarely, 1 = yes/regularly) if mentioned, else 0\n"
    "- active: physical activity (0 = sedentary/inactive, 1 = physically active) if "
    "mentioned, else null\n"
    "- history: family history of cardiovascular disease ('yes' or 'no')\n\n"
    "Return only a valid JSON array, one object per report, using exactly these field "
    "names, no extra text, no markdown code fences, no commentary."
)

def _call_llm_for_extraction(text: str, strict: bool = False) -> Optional[str]:
    model = get_gemini_model()

    instruction = SYSTEM_INSTRUCTION

    if strict:
        instruction += " Return ONLY JSON, nothing else — no preamble, no explanation."

    prompt = instruction + "\n\nMEDICAL REPORT TEXT:\n" + text

    response = model.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    print("\n===== GEMINI RAW RESPONSE =====")
    print(response.text)
    print("===== END RESPONSE =====\n")

    return response.text if response.text else None



def extract_profile(pdf_path: str) -> List[Dict[str, Any]]:
    """
    PUBLIC INTERFACE FUNCTION — this is what Person C (and whoever builds
    predict_risk) calls.

    Extract a list of per-report profile dictionaries from a PDF file.
    Field names/format are documented in the module docstring above and are
    designed to match the training dataset schema as closely as possible.

    Args:
        pdf_path: Path to a PDF that may contain multiple medical reports.

    Returns:
        A list of profile dictionaries, one per identified report. Returns
        an empty list (never raises) if the PDF cannot be read or if JSON
        parsing fails after retry.
    """
    text = extract_text(pdf_path)
    print("\n===== EXTRACTED TEXT =====")
    print(text)
    print("===== END EXTRACTED TEXT =====\n")

    if text.startswith("[ERROR]"):
        return []

    if not text or not text.strip():
        return []

    raw_response = _call_llm_for_extraction(text)
    if raw_response is None:
        return []

    cleaned = clean_json_response(raw_response)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        raw_response = _call_llm_for_extraction(text, strict=True)
        if raw_response is None:
            return []
        cleaned = clean_json_response(raw_response)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return []

    if not isinstance(parsed, list):
        return []

    return [p for p in parsed if isinstance(p, dict)]


# ---- Quick manual test ----
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extraction.py <path_to_pdf>")
        sys.exit(1)

    profiles = extract_profile(sys.argv[1])
    print(json.dumps(profiles, indent=2))
    print(f"\n[INFO] Extracted {len(profiles)} report(s).")