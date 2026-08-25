"""
extract_text.py
----------------
Person B (RAG + LLM) — Document Processing Layer

Extracts text from a single PDF that may contain multiple medical reports
for the same patient (different dates/doctors). Handles both:
  - Digital PDFs (text-based, e.g. exported from Word)
  - Scanned/photographed PDFs (image-based, needs OCR)

INTERFACE CONTRACT (must match exactly — extraction.py depends on this):
    extract_text(pdf_path) -> str
    On failure, returns a string starting with "[ERROR]" instead of raising
    an exception — extraction.py checks for this prefix to fail safely.
"""

import io
import pymupdf  # PyMuPDF

# Only import pytesseract/PIL if available. This prevents a crash on
# machines (e.g. a teammate's computer during integration) where Tesseract
# isn't installed yet, as long as they're only testing digital PDFs.
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


TESSERACT_CMD_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if OCR_AVAILABLE and TESSERACT_CMD_PATH:
    import os
    if os.path.exists(TESSERACT_CMD_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD_PATH

MIN_DIGITAL_TEXT_LENGTH = 20  # below this, a page is treated as scanned/image-based
OCR_DPI = 300  # higher DPI = better OCR accuracy, but slower


def _ocr_page(page):
    """Rasterize a page and run OCR on it. Returns extracted text (str)."""
    if not OCR_AVAILABLE:
        return "[OCR SKIPPED — pytesseract/Pillow not installed]"

    try:
        pix = page.get_pixmap(dpi=OCR_DPI)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img)
    except Exception as e:
        return f"[OCR FAILED on this page: {e}]"


def extract_text(pdf_path):
    """
    Extract text from a PDF, handling both digital and scanned pages.

    Args:
        pdf_path (str): path to the PDF file

    Returns:
        str: combined text from all pages, with page markers, e.g.:
             "--- Page 1 ---\\n<text>\\n--- Page 2 (OCR) ---\\n<text>..."
             Returns a string starting with "[ERROR]" (not a crash) if the
             PDF can't be opened — callers must check for this prefix.
    """
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        return f"[ERROR] Could not open PDF '{pdf_path}': {e}"

    if doc.page_count == 0:
        doc.close()
        return "[ERROR] PDF has no pages."

    full_text_parts = []

    for page_num, page in enumerate(doc, start=1):
        try:
            digital_text = page.get_text().strip()
        except Exception:
            digital_text = ""

        if len(digital_text) >= MIN_DIGITAL_TEXT_LENGTH:
            full_text_parts.append(f"--- Page {page_num} ---\n{digital_text}")
        else:
            ocr_text = _ocr_page(page)
            full_text_parts.append(f"--- Page {page_num} (OCR) ---\n{ocr_text}")

    doc.close()
    return "\n\n".join(full_text_parts)


# ---- Quick manual test ----
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_text.py <path_to_pdf>")
        sys.exit(1)

    result = extract_text(sys.argv[1])
    print(result)
    print(f"\n\n[INFO] Extracted {len(result)} characters total.")