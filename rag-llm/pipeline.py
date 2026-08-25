"""
pipeline.py

Runs the complete medical document pipeline:

PDF
  ↓
Text extraction / OCR
  ↓
Gemini LLM extraction
  ↓
Multiple report profiles
  ↓
Profile consolidation
  ↓
Final patient profile
"""

import json
import sys

from extraction import extract_profile
from consolidation import consolidate_profiles


def run_pipeline(pdf_path):
    # --------------------------------------------------
    # STEP 1: EXTRACT MEDICAL REPORTS
    # --------------------------------------------------

    print("=" * 60)
    print("STEP 1: EXTRACTING MEDICAL REPORTS")
    print("=" * 60)

    profiles = extract_profile(pdf_path)

    if not profiles:
        print("\n[ERROR] No medical reports were extracted.")
        return None

    print(f"\n[INFO] Extracted {len(profiles)} report(s).")

    print("\n===== EXTRACTED PROFILES =====")
    print(json.dumps(profiles, indent=2))

    # --------------------------------------------------
    # STEP 2: CONSOLIDATE REPORTS
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("STEP 2: CONSOLIDATING REPORTS")
    print("=" * 60)

    final_profile = consolidate_profiles(profiles)

    print("\n===== FINAL PATIENT PROFILE =====")
    print(json.dumps(final_profile, indent=2))

    return final_profile


# ------------------------------------------------------
# COMMAND LINE ENTRY POINT
# ------------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("python pipeline.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    run_pipeline(pdf_path)