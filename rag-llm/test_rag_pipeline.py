"""
Test script for extraction, consolidation, and explanation pipeline.

Runs the full RAG+LLM flow on synthetic multi-report medical text. The
Anthropic client is mocked so the test does not require a real API key, while
still exercising the JSON parsing, consolidation logic, and prompt formatting.

NOTE: Mock data below matches the ACTUAL TRAINING DATASET SCHEMA:
    id;age;gender;height;weight;ap_hi;ap_lo;cholesterol;gluc;smoke;alco;active;cardio
- ap_hi / ap_lo are separate fields (systolic/diastolic), not a combined string
- cholesterol / gluc are CATEGORICAL (1=normal, 2=above normal, 3=well above
  normal) — not raw mg/dL values
- gender, height, weight, alco, active are included
- age is in YEARS here (extraction/consolidation keep it in years; convert
  to days only when calling predict_risk)
- history (family history) is kept for generate_explanation() context only —
  it is NOT a dataset column and is not fed to predict_risk
"""

import json
from unittest.mock import MagicMock, patch

from extraction import extract_profile
from consolidation import consolidate_profiles
from explanation import generate_explanation


# Synthetic raw text that might come from extract_text.py. Three reports for
# the same patient across different dates, matching the dataset's fields.
SAMPLE_PDF_TEXT = """
Patient Name: Ayesha Malik

Report 1
Doctor: Dr. Ahmed
Clinic: City Heart Clinic
Date: 10 Jan 2026

Age: 55
Gender: Female
Height: 160 cm
Weight: 78 kg
Systolic BP (ap_hi): 140
Diastolic BP (ap_lo): 90
Cholesterol Level: 3 (well above normal)
Glucose Level: 1 (normal)
Smoking: No
Alcohol Intake: No
Physically Active: Yes
Family history of cardiovascular disease: Yes

---

Report 2
Doctor: Dr. Sara
Clinic: National Cardiology Center
Date: 5 March 2026

Age: 55
Gender: Female
Height: 160 cm
Weight: 80 kg
Systolic BP (ap_hi): 135
Diastolic BP (ap_lo): 88
Cholesterol Level: 3 (well above normal)
Glucose Level: 1 (normal)
Smoking: No
Alcohol Intake: No
Physically Active: Yes
Family history: Yes

---

Report 3
Doctor: Dr. Khan
Clinic: Al-Shifa Hospital
Date: 20 June 2026

Age: 55
Gender: Female
Height: 160 cm
Weight: 81 kg
Systolic BP (ap_hi): 125
Diastolic BP (ap_lo): 80
Cholesterol Level: 1 (normal)
Glucose Level: 1 (normal)
Smoking: No
Alcohol Intake: No
Physically Active: Yes
Family history: Yes
"""

# JSON the mocked LLM would return for the extraction prompt.
# Field names and categorical cholesterol/gluc values must match what
# extraction.py's SYSTEM_INSTRUCTION actually asks the LLM to return.
MOCK_EXTRACTED_PROFILES = [
    {
        "date": "10/01/2026",
        "doctor": "Dr. Ahmed",
        "age": 55,
        "gender": 2,  # female
        "height": 160,
        "weight": 78,
        "ap_hi": 140,
        "ap_lo": 90,
        "cholesterol": 3,
        "gluc": 1,
        "smoke": 0,
        "alco": 0,
        "active": 1,
        "history": "yes",
    },
    {
        "date": "05/03/2026",
        "doctor": "Dr. Sara",
        "age": 55,
        "gender": 2,
        "height": 160,
        "weight": 80,
        "ap_hi": 135,
        "ap_lo": 88,
        "cholesterol": 3,
        "gluc": 1,
        "smoke": 0,
        "alco": 0,
        "active": 1,
        "history": "yes",
    },
    {
        "date": "20/06/2026",
        "doctor": "Dr. Khan",
        "age": 55,
        "gender": 2,
        "height": 160,
        "weight": 81,
        "ap_hi": 125,
        "ap_lo": 80,
        "cholesterol": 1,
        "gluc": 1,
        "smoke": 0,
        "alco": 0,
        "active": 1,
        "history": "yes",
    },
]


def _make_mock_llm(response_text: str):
    """Build a mock Anthropic client that returns the given response text."""
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=response_text)]

    mock_messages = MagicMock()
    mock_messages.create.return_value = mock_message

    mock_client = MagicMock()
    mock_client.messages = mock_messages
    return mock_client


def test_extraction():
    print("=" * 60)
    print("TEST 1: extract_profile")
    print("=" * 60)

    response_text = json.dumps(MOCK_EXTRACTED_PROFILES)
    mock_client = _make_mock_llm(response_text)

    with patch("extraction.extract_text", return_value=SAMPLE_PDF_TEXT), \
         patch("extraction.get_anthropic_client", return_value=mock_client):
        profiles = extract_profile("dummy_report.pdf")

    print(f"Extracted {len(profiles)} report(s):")
    for idx, profile in enumerate(profiles, start=1):
        print(f"  Report {idx}: {profile}")

    assert isinstance(profiles, list)
    assert len(profiles) == 3
    assert all(isinstance(p, dict) for p in profiles)
    # Confirm the LLM output used the correct field names (ap_hi/ap_lo,
    # cholesterol, gluc, history) matching the dataset schema
    assert all("ap_hi" in p and "ap_lo" in p and "history" in p for p in profiles)
    return profiles


def test_consolidation(profiles):
    print("\n" + "=" * 60)
    print("TEST 2: consolidate_profiles")
    print("=" * 60)

    final_profile = consolidate_profiles(profiles)
    print("Final profile (years — convert age to days before predict_risk):")
    for key, value in final_profile.items():
        print(f"  {key}: {value} ({type(value).__name__})")

    expected_keys = {
        "age", "gender", "height", "weight", "ap_hi", "ap_lo",
        "cholesterol", "gluc", "smoke", "alco", "active", "history",
        "consistent_high_factors",
    }
    assert set(final_profile.keys()) == expected_keys

    # Latest report is 20 June 2026, so these should reflect that report —
    # cholesterol dropped back to normal (1) in the latest report.
    assert final_profile["age"] == 55
    assert final_profile["gender"] == 2
    assert final_profile["weight"] == 81
    assert final_profile["ap_hi"] == 125
    assert final_profile["ap_lo"] == 80
    assert final_profile["cholesterol"] == 1
    assert final_profile["gluc"] == 1
    assert final_profile["smoke"] == 0
    assert final_profile["active"] == 1
    assert final_profile["history"] == 1

    # cholesterol was high (2 or 3) in reports 1 and 2 (2/3, more than half),
    # even though the latest report is normal.
    # ap_hi was >130 in reports 1 (140) and 2 (135) (2/3), even though the
    # latest report (125) is normal.
    # gluc was never high (always 1) so it should NOT be flagged.
    assert set(final_profile["consistent_high_factors"]) == {"cholesterol", "ap_hi"}

    return final_profile


def test_explanation(consistent_high_factors):
    print("\n" + "=" * 60)
    print("TEST 3: generate_explanation")
    print("=" * 60)

    risk_data = {
        "risk_score": 0.72,
        "risk_level": "High",
        "top_factors": ["age", "cholesterol", "ap_hi"],
    }
    evidence = [
        "Cholesterol Level: 3 (well above normal) — 10 Jan 2026",
        "Cholesterol Level: 3 (well above normal) — 5 March 2026",
        "Systolic BP (ap_hi): 140 — 10 Jan 2026",
    ]

    mock_summary = (
        "The patient shows a high risk score driven by age, cholesterol, and blood pressure. "
        "Notably, cholesterol and systolic blood pressure have remained elevated across multiple "
        "past visits, even though the most recent readings have improved. This persistent pattern "
        "warrants closer clinical review and ongoing monitoring."
    )
    mock_client = _make_mock_llm(mock_summary)

    with patch("explanation.get_anthropic_client", return_value=mock_client):
        explanation = generate_explanation(risk_data, consistent_high_factors, evidence)

    print("Generated explanation:")
    print(f"  {explanation}")

    assert isinstance(explanation, str)
    assert len(explanation) > 0


def main():
    profiles = test_extraction()
    final_profile = test_consolidation(profiles)
    test_explanation(final_profile["consistent_high_factors"])
    print("\n" + "=" * 60)
    print("All pipeline tests passed.")
    print("=" * 60)
    print("\nReminder: convert age (years) to days before calling predict_risk:")
    print("  age_days = round(final_profile['age'] * 365.25)")
    print("Also drop 'history' from the dict before calling predict_risk —")
    print("it's not a column in the training dataset.")


if __name__ == "__main__":
    main()