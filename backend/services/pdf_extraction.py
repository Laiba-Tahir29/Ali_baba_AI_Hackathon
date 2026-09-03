"""
Layer 1 & 2: Document Processing & Medical Profile Extraction

Pipeline:

PDF
  ↓
PyMuPDF text extraction
  ↓
Tesseract OCR fallback for scanned PDFs
  ↓
Gemini structured extraction
  ↓
Deterministic regex validation/recovery
  ↓
Final per-report profiles

IMPORTANT:
- Only values explicitly present in the document are extracted.
- No clinical defaults are invented.
- Missing values remain None.
- Gemini is primary.
- Regex recovers fields Gemini misses.
"""

import os
import re
import json
try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None
    Image = None

from typing import List, Dict, Any, Optional

import pymupdf


# ============================================================
# 1. PDF TEXT EXTRACTION
# ============================================================

def extract_raw_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from the actual uploaded PDF.

    Primary:
    - PyMuPDF machine-readable text extraction

    Fallback:
    - Tesseract OCR for scanned/image-only PDFs

    Existing machine-readable PDFs continue through
    the original extraction path.
    """

    if not pdf_path or not os.path.exists(pdf_path):
        return f"[ERROR] File not found: {pdf_path}"

    try:
        doc = pymupdf.open(pdf_path)
    except Exception as exc:
        return f"[ERROR] Could not open PDF: {exc}"

    if doc.page_count == 0:
        doc.close()
        return "[ERROR] PDF has no pages."

    # ========================================================
    # EXISTING PDF TEXT EXTRACTION
    # ========================================================

    pages = []

    for page_number, page in enumerate(doc, start=1):
        try:
            text = page.get_text("text").strip()
        except Exception:
            text = ""

        if text:
            pages.append(
                f"--- Page {page_number} ---\n{text}"
            )

    # ========================================================
    # NORMAL TEXT PDF
    # Keep existing behavior exactly the same.
    # ========================================================

    if pages:
        doc.close()
        return "\n\n".join(pages)

    # ========================================================
    # OCR FALLBACK
    # Only reached when NO machine-readable text was found.
    # ========================================================

    print(
        "[Stage 1: PDF Extraction] "
        "No machine-readable text found. "
        "Starting OCR fallback..."
    )

    ocr_pages = []

    try:
        # Windows default Tesseract installation path
        if os.name == "nt":
            tesseract_path = (
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            )

            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = (
                    tesseract_path
                )

        # OCR each PDF page
        for page_number, page in enumerate(doc, start=1):
            try:
                # Render PDF page as an image
                matrix = pymupdf.Matrix(2, 2)

                pix = page.get_pixmap(
                    matrix=matrix,
                    alpha=False
                )

                # Convert rendered PDF page to PIL image
                image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                # Run Tesseract OCR
                ocr_text = pytesseract.image_to_string(
                    image,
                    lang="eng"
                ).strip()

                if ocr_text:
                    ocr_pages.append(
                        f"--- Page {page_number} ---\n{ocr_text}"
                    )

            except Exception as page_exc:
                print(
                    f"[Stage 1 OCR] "
                    f"Page {page_number} failed: {page_exc}"
                )

        doc.close()

    except pytesseract.pytesseract.TesseractNotFoundError:
        doc.close()

        return (
            "[ERROR] Tesseract OCR is not installed "
            "or could not be found."
        )

    except Exception as exc:
        doc.close()

        return f"[ERROR] OCR processing failed: {exc}"

    # ========================================================
    # OCR RESULT
    # Send OCR text into the EXISTING pipeline.
    # ========================================================

    if not ocr_pages:
        return (
            "[ERROR] OCR completed but no readable text "
            "was found in the scanned PDF."
        )

    print(
        "[Stage 1 OCR] "
        "OCR completed successfully."
    )

    return "\n\n".join(ocr_pages)


# ============================================================
# 2. BASIC NORMALIZATION HELPERS
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

        if not cleaned:
            return None

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

    if isinstance(value, bool):
        return int(value)

    text = str(value).strip().lower()

    if text in {
        "yes",
        "y",
        "true",
        "1",
        "positive",
        "present",
    }:
        return 1

    if text in {
        "no",
        "n",
        "false",
        "0",
        "negative",
        "none",
        "absent",
    }:
        return 0

    return None


def _normalize_history(value: Any) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip().lower()

    if any(
        word in text
        for word in [
            "yes",
            "positive",
            "present",
        ]
    ):
        return "yes"

    if any(
        word in text
        for word in [
            "no",
            "negative",
            "none",
            "absent",
        ]
    ):
        return "no"

    return None


# ============================================================
# 3. GENDER
# ============================================================

def _standardize_gender(value: Any) -> Optional[int]:
    """
    Dataset representation:

    1 = Female
    2 = Male
    """

    if value is None:
        return None

    numeric = _normalize_int(value)

    if numeric in (1, 2):
        return numeric

    text = str(value).strip().lower()

    if text in {"female", "f", "woman"}:
        return 1

    if text in {"male", "m", "man"}:
        return 2

    return None


# ============================================================
# 4. CHOLESTEROL
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

    numeric = _normalize_int(value)

    if numeric in (1, 2, 3):
        return numeric

    text = str(value).strip().lower()

    if "well above" in text or "very high" in text:
        return 3

    if (
        "above" in text
        or "high" in text
        or "elevated" in text
    ):
        return 2

    raw_match = re.search(
        r"\d+(?:\.\d+)?",
        text
    )

    if raw_match:
        raw = _normalize_number(
            raw_match.group(0)
        )

        if raw is not None:
            if raw >= 240:
                return 3

            if raw >= 200:
                return 2

            return 1

    return None


# ============================================================
# 5. GLUCOSE
# ============================================================

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

    raw_match = re.search(
        r"\d+(?:\.\d+)?",
        text
    )

    if raw_match:
        raw = _normalize_number(
            raw_match.group(0)
        )

        if raw is not None:
            if raw >= 126:
                return 3

            if raw >= 100:
                return 2

            return 1

    return None


# ============================================================
# 6. REPORT SECTION SPLITTING
# ============================================================

def _split_reports(raw_text: str) -> List[str]:
    """
    Try to identify separate encounters.

    If no explicit report separator exists,
    treat the complete document as one report.
    """

    if not raw_text:
        return []

    separator_pattern = re.compile(
        r"""
        (?:
            \bReport\s+\d+\b
            |
            \bMedical\s+Report\b
            |
            ---\s*Page\s+\d+\s*---
        )
        """,
        flags=re.IGNORECASE | re.VERBOSE,
    )

    sections = separator_pattern.split(raw_text)

    sections = [
        section.strip()
        for section in sections
        if len(section.strip()) > 20
    ]

    if not sections:
        return [raw_text.strip()]

    return sections


# ============================================================
# 7. DETERMINISTIC REGEX EXTRACTION
# ============================================================

def parse_reports_with_regex(
    raw_text: str,
) -> List[Dict[str, Any]]:
    """
    Deterministic extraction from the actual PDF text.

    No clinical defaults are used.
    Missing values remain None.
    """

    if not raw_text or not raw_text.strip():
        return []

    sections = _split_reports(raw_text)

    reports = []

    for index, section in enumerate(
        sections,
        start=1,
    ):
        sec = section.strip()

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        date_match = re.search(
            r"\bDate\s*:?\s*(.+?)(?=\n|$)",
            sec,
            re.IGNORECASE,
        )

        date = (
            _clean_text(date_match.group(1))
            if date_match
            else None
        )

        # ----------------------------------------------------
        # DOCTOR
        # ----------------------------------------------------

        doctor_match = re.search(
            r"\bDoctor(?:\s+Name)?\s*:?\s*(.+?)(?=\n|$)",
            sec,
            re.IGNORECASE,
        )

        doctor = (
            _clean_text(doctor_match.group(1))
            if doctor_match
            else None
        )

        # ----------------------------------------------------
        # CLINIC
        # ----------------------------------------------------

        clinic_match = re.search(
            r"\bClinic\s*:?\s*(.+?)(?=\n|$)",
            sec,
            re.IGNORECASE,
        )

        clinic = (
            _clean_text(clinic_match.group(1))
            if clinic_match
            else None
        )

        # ----------------------------------------------------
        # AGE
        # ----------------------------------------------------

        age_match = re.search(
            r"\bAge\s*:?\s*(\d{1,3})\b",
            sec,
            re.IGNORECASE,
        )

        if not age_match:
            age_match = re.search(
                r"\b(\d{1,3})\s*(?:years?|yrs?)\s*(?:old)?\b",
                sec,
                re.IGNORECASE,
            )

        age = (
            _normalize_int(age_match.group(1))
            if age_match
            else None
        )

        # ----------------------------------------------------
        # GENDER
        # ----------------------------------------------------

        gender_match = re.search(
            r"\bGender\s*:?\s*([A-Za-z]+)",
            sec,
            re.IGNORECASE,
        )

        gender = (
            _standardize_gender(
                gender_match.group(1)
            )
            if gender_match
            else None
        )

        # ----------------------------------------------------
        # HEIGHT
        # ----------------------------------------------------

        height_match = re.search(
            r"\bHeight\s*:?\s*(\d+(?:\.\d+)?)\s*(?:cm|centimeters?)?\b",
            sec,
            re.IGNORECASE,
        )

        height = (
            _normalize_number(
                height_match.group(1)
            )
            if height_match
            else None
        )

        # ----------------------------------------------------
        # WEIGHT
        # ----------------------------------------------------

        weight_match = re.search(
            r"\bWeight\s*:?\s*(\d+(?:\.\d+)?)\s*(?:kg|kilograms?)?\b",
            sec,
            re.IGNORECASE,
        )

        weight = (
            _normalize_number(
                weight_match.group(1)
            )
            if weight_match
            else None
        )

        # ----------------------------------------------------
        # BLOOD PRESSURE
        # ----------------------------------------------------

        bp_match = re.search(
            r"\b(?:Blood\s+Pressure|BP)\s*:?\s*"
            r"(\d{2,3})\s*/\s*(\d{2,3})",
            sec,
            re.IGNORECASE,
        )

        ap_hi = None
        ap_lo = None

        if bp_match:
            ap_hi = _normalize_int(
                bp_match.group(1)
            )

            ap_lo = _normalize_int(
                bp_match.group(2)
            )

        # Explicit systolic
        if ap_hi is None:
            systolic_match = re.search(
                r"\bSystolic\s*:?\s*(\d{2,3})\b",
                sec,
                re.IGNORECASE,
            )

            if systolic_match:
                ap_hi = _normalize_int(
                    systolic_match.group(1)
                )

        # Explicit diastolic
        if ap_lo is None:
            diastolic_match = re.search(
                r"\bDiastolic\s*:?\s*(\d{2,3})\b",
                sec,
                re.IGNORECASE,
            )

            if diastolic_match:
                ap_lo = _normalize_int(
                    diastolic_match.group(1)
                )

        # ----------------------------------------------------
        # BMI
        # ----------------------------------------------------

        bmi_match = re.search(
            r"\bBMI\s*:?\s*(\d+(?:\.\d+)?)",
            sec,
            re.IGNORECASE,
        )

        bmi = (
            _normalize_number(
                bmi_match.group(1)
            )
            if bmi_match
            else None
        )

        # ----------------------------------------------------
        # CHOLESTEROL
        # ----------------------------------------------------

        cholesterol_match = re.search(
            r"\bCholesterol\s*:?\s*"
            r"(\d+(?:\.\d+)?)",
            sec,
            re.IGNORECASE,
        )

        cholesterol = None

        if cholesterol_match:
            cholesterol = _standardize_cholesterol(
                cholesterol_match.group(1)
            )

        # ----------------------------------------------------
        # GLUCOSE
        # ----------------------------------------------------

        glucose_match = re.search(
            r"\b(?:Fasting\s+)?Glucose\s*:?\s*"
            r"(\d+(?:\.\d+)?)",
            sec,
            re.IGNORECASE,
        )

        gluc = None

        if glucose_match:
            gluc = _standardize_glucose(
                glucose_match.group(1)
            )

        # ----------------------------------------------------
        # SMOKING
        # ----------------------------------------------------

        smoke_match = re.search(
            r"\b(?:Smoking|Smoke)\s*:?\s*"
            r"(Yes|No|Y|N|True|False|1|0)\b",
            sec,
            re.IGNORECASE,
        )

        smoke = (
            _normalize_yes_no(
                smoke_match.group(1)
            )
            if smoke_match
            else None
        )

        # ----------------------------------------------------
        # ALCOHOL
        # ----------------------------------------------------

        alcohol_match = re.search(
            r"\b(?:Alcohol\s+Intake|Alcohol)\s*:?\s*"
            r"(Yes|No|Y|N|True|False|1|0)\b",
            sec,
            re.IGNORECASE,
        )

        alco = (
            _normalize_yes_no(
                alcohol_match.group(1)
            )
            if alcohol_match
            else None
        )

        # ----------------------------------------------------
        # PHYSICAL ACTIVITY
        # ----------------------------------------------------

        active_match = re.search(
            r"\b(?:Physically\s+Active|Physical\s+Activity|Active)"
            r"\s*:?\s*"
            r"(Yes|No|Y|N|True|False|1|0)\b",
            sec,
            re.IGNORECASE,
        )

        active = (
            _normalize_yes_no(
                active_match.group(1)
            )
            if active_match
            else None
        )

        # ----------------------------------------------------
        # FAMILY HISTORY
        # ----------------------------------------------------

        history_match = re.search(
            r"\b(?:Family\s+History|Cardiovascular\s+History)"
            r"\s*:?\s*(.+?)(?=\n|$)",
            sec,
            re.IGNORECASE,
        )

        history = None

        if history_match:
            history = _normalize_history(
                history_match.group(1)
            )

        # Narrative family history
        # Narrative family history
        if history is None:
            family_pattern = re.search(
                r"\b(?:father|mother|parent|brother|sister)\b"
                r".{0,150}?"
                r"\b(?:heart\s+attack|cardiovascular|CVD|stroke|heart\s+disease|"
                r"diabetes|hypertension|high\s+blood\s+pressure|"
                r"high\s+cholesterol|cholesterol)\b",
                sec,
                re.IGNORECASE,
            )

            if family_pattern:
                history = "yes"

        # ----------------------------------------------------
        # SNIPPET
        # ----------------------------------------------------

        narrative_lines = []

        ignored_prefixes = (
            "doctor",
            "clinic",
            "date",
            "patient",
            "age",
            "gender",
            "height",
            "weight",
            "blood pressure",
            "bp",
            "systolic",
            "diastolic",
            "bmi",
            "cholesterol",
            "glucose",
            "fasting glucose",
            "smoking",
            "smoke",
            "alcohol",
            "physical activity",
            "physically active",
            "active",
            "family history",
            "cardiovascular history",
            "report",
            "clinical",
        )

        for line in sec.splitlines():
            line = line.strip()

            if not line:
                continue

            lower_line = line.lower()

            if lower_line.startswith(
                ignored_prefixes
            ):
                continue

            narrative_lines.append(line)

        if narrative_lines:
            snippet = " ".join(
                narrative_lines
            )

        else:
            bp_display = (
                f"{ap_hi}/{ap_lo}"
                if ap_hi is not None
                and ap_lo is not None
                else "N/A"
            )

            chol_display = {
                1: "Normal",
                2: "Above Normal",
                3: "Well Above Normal",
            }.get(
                cholesterol,
                "Unknown",
            )

            glucose_display = {
                1: "Normal",
                2: "Above Normal",
                3: "Well Above Normal",
            }.get(
                gluc,
                "Unknown",
            )

            snippet = (
                "Clinical encounter"
                f"{f' at {clinic}' if clinic else ''}. "
                f"Vitals evaluated: BP {bp_display} mmHg, "
                f"Cholesterol: {chol_display}, "
                f"Glucose: {glucose_display}."
            )

        snippet = snippet.strip()

        if len(snippet) > 240:
            snippet = snippet[:240] + "…"

        # ----------------------------------------------------
        # REPORT OBJECT
        # ----------------------------------------------------

        reports.append(
            {
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
                "bp": (
                    f"{ap_hi}/{ap_lo}"
                    if ap_hi is not None
                    and ap_lo is not None
                    else None
                ),
                "bmi": bmi,
                "cholesterol": cholesterol,
                "gluc": gluc,
                "glucose": (
                    str(gluc)
                    if gluc is not None
                    else None
                ),
                "smoke": smoke,
                "smoking": (
                    "yes"
                    if smoke == 1
                    else "no"
                    if smoke == 0
                    else None
                ),
                "alco": alco,
                "active": active,
                "history": history,
            }
        )

    return reports


# ============================================================
# 8. MERGE GEMINI + REGEX
# ============================================================

def _merge_missing_fields(
    gemini_reports: List[Dict[str, Any]],
    regex_reports: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Gemini remains primary.

    Regex fills only fields Gemini left missing.
    """

    merged = []

    fields = [
        "date",
        "doctor",
        "clinic",
        "snippet",
        "age",
        "gender",
        "height",
        "weight",
        "ap_hi",
        "ap_lo",
        "bp",
        "bmi",
        "cholesterol",
        "gluc",
        "glucose",
        "smoke",
        "smoking",
        "alco",
        "active",
        "history",
    ]

    for index, gemini_report in enumerate(
        gemini_reports
    ):
        report = dict(gemini_report)

        regex_report = (
            regex_reports[index]
            if index < len(regex_reports)
            else {}
        )

        for field in fields:
            gemini_value = report.get(field)
            regex_value = regex_report.get(field)

            if (
                gemini_value is None
                and regex_value is not None
            ):
                report[field] = regex_value

        # ----------------------------------------------------
        # Normalize final values
        # ----------------------------------------------------

        report["date"] = _clean_text(
            report.get("date")
        )

        report["doctor"] = _clean_text(
            report.get("doctor")
        )

        report["clinic"] = _clean_text(
            report.get("clinic")
        )

        report["snippet"] = _clean_text(
            report.get("snippet")
        )

        report["age"] = _normalize_int(
            report.get("age")
        )

        report["gender"] = _standardize_gender(
            report.get("gender")
        )

        report["height"] = _normalize_number(
            report.get("height")
        )

        report["weight"] = _normalize_number(
            report.get("weight")
        )

        report["ap_hi"] = _normalize_int(
            report.get("ap_hi")
        )

        report["ap_lo"] = _normalize_int(
            report.get("ap_lo")
        )

        report["bmi"] = _normalize_number(
            report.get("bmi")
        )

        report["cholesterol"] = (
            _standardize_cholesterol(
                report.get("cholesterol")
            )
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
        # Derived display values
        # ----------------------------------------------------

        if (
            report.get("ap_hi") is not None
            and report.get("ap_lo") is not None
        ):
            report["bp"] = (
                f"{report['ap_hi']}/"
                f"{report['ap_lo']}"
            )
        else:
            report["bp"] = None

        if report.get("smoke") == 1:
            report["smoking"] = "yes"

        elif report.get("smoke") == 0:
            report["smoking"] = "no"

        else:
            report["smoking"] = None

        if report.get("gluc") is not None:
            report["glucose"] = str(
                report["gluc"]
            )
        else:
            report["glucose"] = None

        # ----------------------------------------------------
        # Fallback snippet
        # ----------------------------------------------------

        if not report.get("snippet"):
            clinic = (
                report.get("clinic")
                or "Clinical Facility"
            )

            date = (
                report.get("date")
                or "Encounter"
            )

            ap_hi = report.get("ap_hi")
            ap_lo = report.get("ap_lo")

            bp_display = (
                f"{ap_hi}/{ap_lo}"
                if ap_hi is not None
                and ap_lo is not None
                else "N/A"
            )

            chol_display = {
                1: "Normal",
                2: "Above Normal",
                3: "Well Above Normal",
            }.get(
                report.get("cholesterol"),
                "Unknown",
            )

            glucose_display = {
                1: "Normal",
                2: "Above Normal",
                3: "Well Above Normal",
            }.get(
                report.get("gluc"),
                "Unknown",
            )

            report["snippet"] = (
                f"Clinical encounter at {clinic} "
                f"on {date}. "
                f"Evaluated vitals: "
                f"BP {bp_display} mmHg, "
                f"Cholesterol: {chol_display}, "
                f"Glucose: {glucose_display}."
            )

        merged.append(report)

    return merged


# ============================================================
# 9. GEMINI EXTRACTION
# ============================================================

def _extract_with_gemini(
    raw_text: str,
) -> Optional[List[Dict[str, Any]]]:

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if (
        not api_key
        or api_key.startswith("your_")
    ):
        print(
            "[Stage 1 Notice] "
            "GEMINI_API_KEY not configured."
        )
        return None

    # Fast, low-latency Gemini model.
    # Do not change gemini-embedding-001 elsewhere;
    # that is used for RAG embeddings, not text extraction.
    model_names = [
        "gemini-3.5-flash-lite",
    ]

    for model_name in model_names:
        try:
            from google import genai

            client = genai.Client(
                api_key=api_key
            )

            prompt = f"""
You are extracting structured information from a medical report.

STRICT RULES:

1. Use ONLY information explicitly present in the document.
2. NEVER guess missing values.
3. NEVER use typical/default patient values.
4. Missing fields MUST be null.
5. Extract EVERY separate medical encounter.
6. Preserve the actual date, doctor, and clinic.
7. Extract BMI only when explicitly present.

8. Cholesterol:
   - < 200 = 1
   - 200-239 = 2
   - >= 240 = 3

9. Glucose:
   - < 100 = 1
   - 100-125 = 2
   - >= 126 = 3

10. Do not confuse age with other numbers.

11. Extract family cardiovascular history only when explicitly stated.

12. Do not create medical information.

Gender:

1 = female
2 = male
null = not reported

Cholesterol:

1 = normal
2 = above normal
3 = well above normal
null = not reported

Glucose:

1 = normal
2 = above normal
3 = well above normal
null = not reported

Smoking:

0 = no
1 = yes
null = not reported

Alcohol:

0 = no
1 = yes
null = not reported

Physical activity:

0 = no
1 = yes
null = not reported

History:

"yes"
"no"
null

Return ONLY valid JSON.

Return a JSON array containing objects with:

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
bp
bmi
cholesterol
gluc
glucose
smoke
smoking
alco
active
history

DOCUMENT:

{raw_text}
"""

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )

            if not response:
                continue

            text = getattr(
                response,
                "text",
                None,
            )

            if not text:
                continue

            clean = text.strip()

            # Remove markdown fences
            clean = re.sub(
                r"^```(?:json)?\s*",
                "",
                clean,
                flags=re.IGNORECASE,
            )

            clean = re.sub(
                r"\s*```$",
                "",
                clean,
            )

            clean = clean.strip()

            parsed = json.loads(clean)

            if (
                isinstance(parsed, list)
                and parsed
            ):
                print(
                    "[Stage 1: PDF Extraction] "
                    f"Gemini succeeded using "
                    f"{model_name}"
                )

                return parsed

        except Exception as exc:
            print(
                "[Stage 1 Notice] "
                f"Gemini {model_name} failed: "
                f"{exc}"
            )

    return None


# ============================================================
# 10. PUBLIC EXTRACTION PIPELINE
# ============================================================

def extract_profile(
    pdf_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Main extraction pipeline.

    PDF
      ↓
    PyMuPDF
      ↓
    OCR fallback if scanned
      ↓
    Regex validation
      ↓
    Gemini
      ↓
    Gemini + Regex merge

    If Gemini fails:

    PDF
      ↓
    PyMuPDF / OCR
      ↓
    Regex

    No clinical defaults are created.
    """

    if (
        not pdf_path
        or not os.path.exists(pdf_path)
    ):
        print(
            "[Stage 1 Error] "
            "Uploaded PDF path is missing."
        )
        return []

    # --------------------------------------------------------
    # Extract actual PDF text
    # --------------------------------------------------------

    raw_text = extract_raw_text_from_pdf(
        pdf_path
    )

    if raw_text.startswith("[ERROR]"):
        print(
            f"[Stage 1 Error] {raw_text}"
        )
        return []

    if len(raw_text.strip()) < 20:
        print(
            "[Stage 1 Error] "
            "Extracted PDF text is too short."
        )
        return []

    print(
        "\n========== RAW PDF TEXT =========="
    )

    print(raw_text[:5000])

    print(
        "==================================\n"
    )

    # --------------------------------------------------------
    # Regex validation/recovery
    # --------------------------------------------------------

    regex_reports = parse_reports_with_regex(
        raw_text
    )

    print(
        "\n========== REGEX EXTRACTION =========="
    )

    print(
        json.dumps(
            regex_reports,
            indent=2,
            default=str,
        )
    )

    print(
        "======================================\n"
    )

    # --------------------------------------------------------
    # Gemini
    # --------------------------------------------------------

    gemini_reports = _extract_with_gemini(
        raw_text
    )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    if gemini_reports:
        final_reports = _merge_missing_fields(
            gemini_reports,
            regex_reports,
        )

        print(
            "[Stage 1: PDF Extraction] "
            "Status: [GEMINI + REGEX VALIDATION] "
            f"Extracted {len(final_reports)} encounters."
        )

    else:
        final_reports = regex_reports

        print(
            "[Stage 1: PDF Extraction] "
            "Status: [DETERMINISTIC REGEX FALLBACK] "
            f"Extracted {len(final_reports)} encounters."
        )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print(
        "\n========== FINAL EXTRACTION =========="
    )

    print(
        json.dumps(
            final_reports,
            indent=2,
            default=str,
        )
    )

    print(
        "======================================\n"
    )

    return final_reports or []
