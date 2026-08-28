"""
Layer 1 & 2: Document Processing & Medical Profile Extraction

Owner: Person B (rag-llm branch)

Pipeline:
1. Extract text from the genuine uploaded PDF using PyMuPDF.
2. Try Gemini extraction on the actual document.
3. Validate/recover missing Gemini fields using deterministic regex extraction.
4. If Gemini fails completely, use deterministic regex extraction.
5. NEVER invent clinical values.
6. Missing values remain None.
"""

import os
import re
import json
from typing import List, Dict, Any, Optional

import pymupdf


# ============================================================
# 1. PDF TEXT EXTRACTION
# ============================================================

def extract_raw_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from the actual uploaded PDF using PyMuPDF.

    Note:
    PyMuPDF extracts text from machine-readable PDFs.
    Image-only scanned PDFs require a separate OCR engine.
    """

    if not pdf_path or not os.path.exists(pdf_path):
        return f"[ERROR] File not found: {pdf_path}"

    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        return f"[ERROR] Could not open PDF: {e}"

    if doc.page_count == 0:
        doc.close()
        return "[ERROR] PDF has no pages."

    pages_text = []

    for page_num, page in enumerate(doc, start=1):
        try:
            text = page.get_text("text").strip()
        except Exception:
            text = ""

        if text:
            pages_text.append(
                f"--- Page {page_num} ---\n{text}"
            )

    doc.close()

    if not pages_text:
        return (
            "[ERROR] No machine-readable text found in PDF. "
            "The PDF may be image-only/scanned and require OCR."
        )

    return "\n\n".join(pages_text)


# ============================================================
# 2. SMALL HELPERS
# ============================================================

def _clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def _normalize_number(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        cleaned = str(value).replace(",", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _normalize_int(value: Any) -> Optional[int]:
    number = _normalize_number(value)

    if number is None:
        return None

    return int(number)


def _normalize_yes_no(value: Any) -> Optional[int]:
    if value is None:
        return None

    value = str(value).strip().lower()

    if value in {
        "yes",
        "y",
        "true",
        "1",
        "positive",
        "present"
    }:
        return 1

    if value in {
        "no",
        "n",
        "false",
        "0",
        "negative",
        "none",
        "absent"
    }:
        return 0

    return None


def _normalize_history(value: Any) -> Optional[str]:
    if value is None:
        return None

    value = str(value).strip().lower()

    if any(word in value for word in [
        "yes",
        "positive",
        "present",
        "father",
        "mother",
        "parent",
        "family"
    ]):
        return "yes"

    if any(word in value for word in [
        "no",
        "negative",
        "none",
        "absent"
    ]):
        return "no"

    return None


# ============================================================
# 3. CHOLESTEROL / GLUCOSE STANDARDIZATION
# ============================================================

def _standardize_cholesterol(value: Any) -> Optional[int]:
    """
    Training representation:

    1 = Normal
    2 = Above Normal
    3 = Well Above Normal
    """

    if value is None:
        return None

    # Already categorical
    numeric = _normalize_int(value)

    if numeric in (1, 2, 3):
        return numeric

    text = str(value).lower()

    if "well above" in text:
        return 3

    if "above" in text or "high" in text:
        return 2

    # Raw mg/dL value
    raw = _normalize_number(
        re.sub(r"mg\s*/?\s*dl", "", text)
    )

    if raw is not None:
        if raw >= 240:
            return 3

        if raw >= 200:
            return 2

        return 1

    return None


def _standardize_glucose(value: Any) -> Optional[int]:
    """
    Training representation:

    1 = Normal
    2 = Above Normal
    3 = Well Above Normal
    """

    if value is None:
        return None

    numeric = _normalize_int(value)

    if numeric in (1, 2, 3):
        return numeric

    text = str(value).lower()

    if "well above" in text:
        return 3

    if "above" in text or "high" in text or "elevated" in text:
        return 2

    raw = _normalize_number(
        re.sub(r"mg\s*/?\s*dl", "", text)
    )

    if raw is not None:

        if raw >= 126:
            return 3

        if raw >= 100:
            return 2

        return 1

    return None


# ============================================================
# 4. DETERMINISTIC REGEX PARSER
# ============================================================

def parse_reports_with_regex(
    raw_text: str
) -> List[Dict[str, Any]]:
    """
    Deterministic extraction from the actual PDF text.

    IMPORTANT:
    There are NO clinical defaults here.

    If the PDF does not contain a field,
    the field remains None.
    """

    if not raw_text or not raw_text.strip():
        return []

    # --------------------------------------------------------
    # Split separate encounters
    # --------------------------------------------------------

    sections = re.split(
        r"(?:"
        r"Report\s+\d+"
        r"|MEDICAL\s+REPORT"
        r"|---\s*Page\s+\d+\s*---"
        r")",
        raw_text,
        flags=re.IGNORECASE
    )

    sections = [
        section.strip()
        for section in sections
        if len(section.strip()) > 20
    ]

    if not sections:
        sections = [raw_text.strip()]

    reports = []

    for index, sec in enumerate(sections, start=1):

        # ====================================================
        # HEADER FIELDS
        # ====================================================

        doctor_match = re.search(
            r"Doctor(?:\s+Name)?\s*:\s*(.+?)(?="
            r"\s+(?:Clinic|Date|Patient\s+Name|Clinical\s+Measurements)\s*:?"
            r"|\n|\r|$)",
            sec,
            re.IGNORECASE
        )

        clinic_match = re.search(
            r"Clinic\s*:\s*(.+?)(?="
            r"\s+(?:Date|Doctor(?:\s+Name)?|Patient\s+Name|Clinical\s+Measurements)\s*:?"
            r"|\n|\r|$)",
            sec,
            re.IGNORECASE
        )

        date_match = re.search(
            r"Date\s*:\s*(.+?)(?="
            r"\s+(?:Doctor(?:\s+Name)?|Clinic|Patient\s+Name|Clinical\s+Measurements)\s*:?"
            r"|\n|\r|$)",
            sec,
            re.IGNORECASE
        )

        doctor = (
            _clean_text(doctor_match.group(1))
            if doctor_match
            else None
        )

        clinic = (
            _clean_text(clinic_match.group(1))
            if clinic_match
            else None
        )

        date = (
            _clean_text(date_match.group(1))
            if date_match
            else None
        )

        # ====================================================
        # AGE
        # Handles:
        #
        # Age: 52
        # Age 52
        # 52 years
        # 52 years old
        # ====================================================

        age_match = re.search(
            r"\bAge\s*:?\s*(\d{1,3})\s*(?:years?|yrs?)?\b",
            sec,
            re.IGNORECASE
        )

        if not age_match:
            age_match = re.search(
                r"\b(\d{1,3})\s*(?:years?|yrs?)\s*(?:old)?\b",
                sec,
                re.IGNORECASE
            )

        age = (
            _normalize_int(age_match.group(1))
            if age_match
            else None
        )

        # ====================================================
        # GENDER
        # ====================================================

        gender_match = re.search(
            r"\bGender\s*:?\s*([A-Za-z]+)",
            sec,
            re.IGNORECASE
        )

        gender = None

        if gender_match:
            gender_value = gender_match.group(1).lower()

            if gender_value in ("female", "f", "woman"):
                gender = 1

            elif gender_value in ("male", "m", "man"):
                gender = 2

        # ====================================================
        # HEIGHT
        # ====================================================

        height_match = re.search(
            r"\bHeight\s*:?\s*"
            r"(\d+(?:\.\d+)?)"
            r"\s*(?:cm|centimeters?)?\b",
            sec,
            re.IGNORECASE
        )

        height = (
            _normalize_number(height_match.group(1))
            if height_match
            else None
        )

        # ====================================================
        # WEIGHT
        # ====================================================

        weight_match = re.search(
            r"\bWeight\s*:?\s*"
            r"(\d+(?:\.\d+)?)"
            r"\s*(?:kg|kilograms?)?\b",
            sec,
            re.IGNORECASE
        )

        weight = (
            _normalize_number(weight_match.group(1))
            if weight_match
            else None
        )

        # ====================================================
        # BLOOD PRESSURE
        #
        # Handles:
        #
        # Blood Pressure 150/95
        # BP: 150/95
        # BP 150/95 mmHg
        # ====================================================

        bp_match = re.search(
            r"\b(?:Blood\s+Pressure|BP)\s*:?\s*"
            r"(\d{2,3})\s*/\s*(\d{2,3})",
            sec,
            re.IGNORECASE
        )

        ap_hi = None
        ap_lo = None

        if bp_match:
            ap_hi = _normalize_int(bp_match.group(1))
            ap_lo = _normalize_int(bp_match.group(2))

        # Also support explicit systolic/diastolic
        if ap_hi is None:
            systolic_match = re.search(
                r"\bSystolic\s*:?\s*(\d{2,3})",
                sec,
                re.IGNORECASE
            )

            if systolic_match:
                ap_hi = _normalize_int(
                    systolic_match.group(1)
                )

        if ap_lo is None:
            diastolic_match = re.search(
                r"\bDiastolic\s*:?\s*(\d{2,3})",
                sec,
                re.IGNORECASE
            )

            if diastolic_match:
                ap_lo = _normalize_int(
                    diastolic_match.group(1)
                )

        # ====================================================
        # BMI
        #
        # Handles:
        # BMI 29.1
        # BMI: 29.1
        # BMI 29.1 (Overweight)
        # ====================================================

        bmi_match = re.search(
            r"\bBMI\s*:?\s*"
            r"(\d+(?:\.\d+)?)",
            sec,
            re.IGNORECASE
        )

        bmi = (
            _normalize_number(bmi_match.group(1))
            if bmi_match
            else None
        )

        # ====================================================
        # CHOLESTEROL
        #
        # Handles:
        # Cholesterol 245 mg/dL
        # Cholesterol: 245 mg/dL
        # ====================================================

        cholesterol_match = re.search(
            r"\bCholesterol\s*:?\s*"
            r"(\d+(?:\.\d+)?)",
            sec,
            re.IGNORECASE
        )

        cholesterol = None

        if cholesterol_match:
            cholesterol = _standardize_cholesterol(
                cholesterol_match.group(1)
            )

        # ====================================================
        # GLUCOSE
        #
        # Handles:
        # Glucose 122 mg/dL
        # Fasting Glucose: 122 mg/dL
        # ====================================================

        glucose_match = re.search(
            r"\b(?:Fasting\s+)?Glucose\s*:?\s*"
            r"(\d+(?:\.\d+)?)",
            sec,
            re.IGNORECASE
        )

        gluc = None

        if glucose_match:
            gluc = _standardize_glucose(
                glucose_match.group(1)
            )

        # ====================================================
        # SMOKING
        #
        # Handles:
        # Smoking Yes
        # Smoking: Yes
        # Smoke: No
        # ====================================================

        smoke_match = re.search(
            r"\b(?:Smoking|Smoke)\s*:?\s*"
            r"(Yes|No|Y|N|True|False|1|0)\b",
            sec,
            re.IGNORECASE
        )

        smoke = (
            _normalize_yes_no(smoke_match.group(1))
            if smoke_match
            else None
        )

        # ====================================================
        # ALCOHOL
        # ====================================================

        alcohol_match = re.search(
            r"\b(?:Alcohol\s+Intake|Alcohol)\s*:?\s*"
            r"(Yes|No|Y|N|True|False|1|0)\b",
            sec,
            re.IGNORECASE
        )

        alco = (
            _normalize_yes_no(alcohol_match.group(1))
            if alcohol_match
            else None
        )

        # ====================================================
        # PHYSICAL ACTIVITY
        # ====================================================

        active_match = re.search(
            r"\b(?:Physically\s+Active|Physical\s+Activity|Active)"
            r"\s*:?\s*"
            r"(Yes|No|Y|N|True|False|1|0)\b",
            sec,
            re.IGNORECASE
        )

        active = (
            _normalize_yes_no(active_match.group(1))
            if active_match
            else None
        )

        # ====================================================
        # FAMILY HISTORY
        #
        # Handles:
        # Family History: Yes
        # Family History Father had...
        # Cardiovascular History: Positive
        # ====================================================

        history_match = re.search(
            r"\b(?:Family\s+History|Cardiovascular\s+History)"
            r"\s*:?\s*"
            r"(.+?)(?=\n|\r|$)",
            sec,
            re.IGNORECASE
        )

        history = None

        if history_match:
            history_text = history_match.group(1).strip()

            history = _normalize_history(history_text)

        # Also detect explicit family-history narrative
        if history is None:

            family_pattern = re.search(
                r"\b(?:father|mother|parent|brother|sister)"
                r".{0,120}"
                r"\b(?:heart attack|cardiovascular|CVD|stroke|heart disease)\b",
                sec,
                re.IGNORECASE
            )

            if family_pattern:
                history = "yes"

        # ====================================================
        # NARRATIVE / SNIPPET
        # ====================================================

        header_patterns = re.compile(
            r"^(?:"
            r"Doctor"
            r"|Clinic"
            r"|Date"
            r"|Patient"
            r"|Age"
            r"|Gender"
            r"|Height"
            r"|Weight"
            r"|Blood Pressure"
            r"|BP"
            r"|Systolic"
            r"|Diastolic"
            r"|BMI"
            r"|Cholesterol"
            r"|Glucose"
            r"|Fasting"
            r"|Smoking"
            r"|Smoke"
            r"|Alcohol"
            r"|Physically"
            r"|Physical"
            r"|Active"
            r"|Family"
            r"|Cardiovascular"
            r"|Report"
            r"|Clinical"
            r"|---"
            r"|==="
            r")",
            re.IGNORECASE
        )

        narrative_lines = []

        for line in sec.splitlines():

            cleaned_line = line.strip()

            if not cleaned_line:
                continue

            if header_patterns.match(cleaned_line):
                continue

            narrative_lines.append(cleaned_line)

        if narrative_lines:
            snippet = " ".join(narrative_lines)
        else:

            bp_display = (
                f"{ap_hi}/{ap_lo}"
                if ap_hi is not None and ap_lo is not None
                else "N/A"
            )

            chol_display = (
                "Well Above Normal"
                if cholesterol == 3
                else "Above Normal"
                if cholesterol == 2
                else "Normal"
                if cholesterol == 1
                else "Unknown"
            )

            glucose_display = (
                "Well Above Normal"
                if gluc == 3
                else "Above Normal"
                if gluc == 2
                else "Normal"
                if gluc == 1
                else "Unknown"
            )

            snippet = (
                f"Clinical encounter"
                f"{f' at {clinic}' if clinic else ''}. "
                f"Vitals evaluated: BP {bp_display} mmHg, "
                f"Cholesterol: {chol_display}, "
                f"Glucose: {glucose_display}."
            )

        snippet = snippet.strip()

        if len(snippet) > 240:
            snippet = snippet[:240] + "…"

        # ====================================================
        # FINAL REPORT OBJECT
        # ====================================================

        reports.append({
            "date": date,
            "doctor": doctor,
            "clinic": clinic,
            "snippet": snippet,

            "age": age,
            "gender": gender,
            "height": height,
            "weight": weight,

            "ap_hi": ap_hi,
            "ap_lo": ap_lo,
            "bmi": bmi,

            "cholesterol": cholesterol,
            "gluc": gluc,

            "smoke": smoke,
            "alco": alco,
            "active": active,
            "history": history
        })

    return reports


# ============================================================
# 5. MERGE GEMINI + REGEX
# ============================================================

def _merge_missing_fields(
    gemini_reports: List[Dict[str, Any]],
    regex_reports: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Gemini remains the primary extractor.

    If Gemini misses a field, recover it from the actual
    document using deterministic regex extraction.

    This prevents an LLM omission from becoming a fake/missing
    clinical value downstream.
    """

    merged = []

    for index, gemini_report in enumerate(gemini_reports):

        report = dict(gemini_report)

        if index < len(regex_reports):

            regex_report = regex_reports[index]

            fields = [
                "date",
                "doctor",
                "clinic",
                "age",
                "gender",
                "height",
                "weight",
                "ap_hi",
                "ap_lo",
                "bmi",
                "cholesterol",
                "gluc",
                "smoke",
                "alco",
                "active",
                "history"
            ]

            for field in fields:

                gemini_value = report.get(field)
                regex_value = regex_report.get(field)

                if gemini_value is None and regex_value is not None:
                    report[field] = regex_value

        # ----------------------------------------------------
        # Normalize Gemini values
        # ----------------------------------------------------

        if report.get("age") is not None:
            report["age"] = _normalize_int(report["age"])

        if report.get("gender") is not None:
            report["gender"] = _normalize_int(report["gender"])

        if report.get("height") is not None:
            report["height"] = _normalize_number(report["height"])

        if report.get("weight") is not None:
            report["weight"] = _normalize_number(report["weight"])

        if report.get("ap_hi") is not None:
            report["ap_hi"] = _normalize_int(report["ap_hi"])

        if report.get("ap_lo") is not None:
            report["ap_lo"] = _normalize_int(report["ap_lo"])

        if report.get("bmi") is not None:
            report["bmi"] = _normalize_number(report["bmi"])

        report["cholesterol"] = _standardize_cholesterol(
            report.get("cholesterol")
        )

        report["gluc"] = _standardize_glucose(
            report.get("gluc")
        )

        report["smoke"] = _normalize_yes_no(
            report.get("smoke")
        )

        report["alco"] = _normalize_yes_no(
            report.get("alco")
        )

        report["active"] = _normalize_yes_no(
            report.get("active")
        )

        report["history"] = _normalize_history(
            report.get("history")
        )

        # ----------------------------------------------------
        # Generate snippet if Gemini did not provide one
        # ----------------------------------------------------

        if not report.get("snippet"):

            clinic = report.get("clinic") or "Clinical Facility"
            date = report.get("date") or "Encounter"

            ap_hi = report.get("ap_hi")
            ap_lo = report.get("ap_lo")

            bp_display = (
                f"{ap_hi}/{ap_lo}"
                if ap_hi is not None and ap_lo is not None
                else "N/A"
            )

            chol = report.get("cholesterol")
            gluc = report.get("gluc")

            chol_display = (
                "Well Above Normal"
                if chol == 3
                else "Above Normal"
                if chol == 2
                else "Normal"
                if chol == 1
                else "Unknown"
            )

            glucose_display = (
                "Well Above Normal"
                if gluc == 3
                else "Above Normal"
                if gluc == 2
                else "Normal"
                if gluc == 1
                else "Unknown"
            )

            report["snippet"] = (
                f"Clinical encounter at {clinic} on {date}. "
                f"Evaluated vitals: BP {bp_display} mmHg, "
                f"Cholesterol: {chol_display}, "
                f"Glucose: {glucose_display}."
            )

        merged.append(report)

    return merged


# ============================================================
# 6. GEMINI EXTRACTION
# ============================================================

def _extract_with_gemini(
    raw_text: str
) -> Optional[List[Dict[str, Any]]]:
    """
    Extract structured encounter data using Gemini.

    Returns None if Gemini is unavailable or fails.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key.startswith("your_"):
        return None

    model_names = [
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-3.1-flash-lite",
        "gemini-flash-latest"
    ]

    for model_name in model_names:

        try:

            from google import genai

            client = genai.Client(
                api_key=api_key
            )

            prompt = f"""
You are extracting structured information from a medical report.

IMPORTANT RULES:

1. Use ONLY information explicitly present in the document.
2. NEVER guess missing values.
3. NEVER use typical/default patient values.
4. If a field is missing, return null.
5. Extract EVERY separate medical encounter/report.
6. Preserve the actual encounter date, doctor and clinic.
7. If BMI is explicitly present, extract it directly.
8. If cholesterol is a raw mg/dL value, convert it:
   - < 200 = 1
   - 200-239 = 2
   - >= 240 = 3
9. If glucose is a raw mg/dL value, convert it:
   - < 100 = 1
   - 100-125 = 2
   - >= 126 = 3
10. Do not confuse the patient age with other numbers.
11. Extract family cardiovascular history if explicitly stated.

Return ONLY valid JSON.

Return a JSON array with objects containing:

date
doctor
clinic
snippet
age
gender
height
weight
ap_hi
ap_lo
bmi
cholesterol
gluc
smoke
alco
active
history

Encoding:

gender:
1 = female
2 = male
null = not reported

cholesterol:
1 = normal
2 = above normal
3 = well above normal
null = not reported

gluc:
1 = normal
2 = above normal
3 = well above normal
null = not reported

smoke:
0 = no
1 = yes
null = not reported

alco:
0 = no
1 = yes
null = not reported

active:
0 = no
1 = yes
null = not reported

history:
"yes"
"no"
null

DOCUMENT:
{raw_text}
"""

            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            if not response or not response.text:
                continue

            clean = response.text.strip()

            # Remove markdown JSON fences
            if clean.startswith("```"):

                clean = re.sub(
                    r"^```(?:json)?\s*",
                    "",
                    clean,
                    flags=re.IGNORECASE
                )

                clean = re.sub(
                    r"\s*```$",
                    "",
                    clean
                )

                clean = clean.strip()

            parsed = json.loads(clean)

            if isinstance(parsed, list) and parsed:

                print(
                    f"[Stage 1: PDF Extraction] "
                    f"Gemini succeeded using {model_name}"
                )

                return parsed

        except Exception as e:

            print(
                f"[Stage 1 Notice] "
                f"Gemini {model_name} failed: {e}"
            )

    return None


# ============================================================
# 7. PUBLIC EXTRACTION PIPELINE
# ============================================================

def extract_profile(
    pdf_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Main document extraction pipeline.

    Flow:

    PDF
      ↓
    PyMuPDF
      ↓
    Raw text
      ↓
    Gemini extraction
      ↓
    Regex validation/recovery
      ↓
    Final encounter profiles

    If Gemini fails:
      PDF → PyMuPDF → Regex

    No hardcoded clinical values are used.
    """

    if not pdf_path or not os.path.exists(pdf_path):
        print(
            "[Stage 1 Error] Uploaded PDF path is missing."
        )
        return []

    # --------------------------------------------------------
    # Extract actual PDF text
    # --------------------------------------------------------

    raw_text = extract_raw_text_from_pdf(pdf_path)

    if raw_text.startswith("[ERROR]"):
        print(
            f"[Stage 1 Error] {raw_text}"
        )
        return []

    if len(raw_text.strip()) < 20:
        print(
            "[Stage 1 Error] Extracted PDF text is too short."
        )
        return []

    print("\n========== RAW PDF TEXT ==========")
    print(raw_text[:5000])
    print("==================================\n")

    # --------------------------------------------------------
    # ALWAYS run regex as validation
    # --------------------------------------------------------

    regex_reports = parse_reports_with_regex(
        raw_text
    )

    print("\n========== REGEX EXTRACTION ==========")
    print(
        json.dumps(
            regex_reports,
            indent=2,
            default=str
        )
    )
    print("======================================\n")

    # --------------------------------------------------------
    # Try Gemini
    # --------------------------------------------------------

    gemini_reports = _extract_with_gemini(
        raw_text
    )

    # --------------------------------------------------------
    # Gemini + Regex merge
    # --------------------------------------------------------

    if gemini_reports:

        final_reports = _merge_missing_fields(
            gemini_reports,
            regex_reports
        )

        print(
            f"[Stage 1: PDF Extraction] "
            f"Status: [GEMINI + REGEX VALIDATION] "
            f"Extracted {len(final_reports)} encounters."
        )

    else:

        final_reports = regex_reports

        print(
            f"[Stage 1: PDF Extraction] "
            f"Status: [DETERMINISTIC REGEX FALLBACK] "
            f"Extracted {len(final_reports)} encounters."
        )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print("\n========== FINAL EXTRACTION ==========")

    print(
        json.dumps(
            final_reports,
            indent=2,
            default=str
        )
    )

    print("======================================\n")

    return final_reports if final_reports else []