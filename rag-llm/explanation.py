"""
explanation.py
---------------
Person B (RAG + LLM) — Explanation generation module.

Generates a plain-language clinical summary for a doctor by combining the ML
model's risk output, persistently elevated factors, and retrieved evidence.

INTERFACE CONTRACT (must match exactly — Person C depends on this):
    generate_explanation(risk_data, consistent_high_factors, evidence) -> str

    risk_data: dict from Person A's predict_risk(final_profile), expected
               shape: {risk_score, risk_level, top_factors}
    consistent_high_factors: list of field names from consolidate_profiles()
    evidence: list of chunk strings (typically from retrieve(), a separate
              path — not related to extract_profile())

IMPORTANT — SAFETY CONSTRAINT (do not change):
    This is NOT a diagnostic tool. The prompt explicitly forbids stating a
    diagnosis. It only summarizes patterns and flags them for a doctor's
    review. Do not loosen this instruction.

RELIABILITY NOTE:
    This function must not crash the whole pipeline (e.g. Person C's demo)
    if the LLM API call fails — it returns a safe fallback string instead.
"""

from typing import Any, Dict, List

from utils import get_anthropic_client


PROMPT_TEMPLATE = (
    "Patient's risk level is {risk_level} (score {risk_score}). Top factors from the model: {top_factors}. "
    "Factors that stayed high across multiple past reports: {consistent_high_factors}. "
    "Evidence: {evidence}. Write a short, plain-language summary (3-4 sentences) for a doctor reviewing "
    "this patient — highlight what has been persistently elevated across visits, not just the latest reading. "
    "Do not state a diagnosis; only summarize the pattern and flag it for the doctor's review."
)


def _list_to_text(items: List[str], empty_label: str) -> str:
    """Turn a list like ['bp', 'cholesterol'] into 'bp, cholesterol' for a clean prompt."""
    if not items:
        return empty_label
    return ", ".join(str(item) for item in items)


def generate_explanation(
    risk_data: Dict[str, Any],
    consistent_high_factors: List[str],
    evidence: List[str],
) -> str:
    """
    Generate a plain-language clinical summary for a doctor.

    Args:
        risk_data: Dict from the ML model with keys risk_score, risk_level,
            and top_factors.
        consistent_high_factors: List of field names that stayed high across
            multiple past reports.
        evidence: List of text chunks retrieved from the vector store.

    Returns:
        A plain string summary. Returns a safe fallback message (never
        raises) if the LLM call fails or returns no content, so a bad API
        call doesn't break the demo/integration.
    """
    prompt = PROMPT_TEMPLATE.format(
        risk_level=risk_data.get("risk_level", "unknown"),
        risk_score=risk_data.get("risk_score", "unknown"),
        top_factors=_list_to_text(risk_data.get("top_factors", []), "none identified"),
        consistent_high_factors=_list_to_text(consistent_high_factors, "none"),
        evidence=_list_to_text(evidence, "no supporting evidence retrieved"),
    )

    try:
        client = get_anthropic_client()
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        if not message.content:
            return "[No explanation generated — empty LLM response]"
        return message.content[0].text.strip()
    except Exception as e:
        return f"[Explanation unavailable — {e}]"


# ---- Quick manual test ----
if __name__ == "__main__":
    sample_risk_data = {
        "risk_score": 0.72,
        "risk_level": "High",
        "top_factors": ["blood pressure", "cholesterol"],
    }
    sample_consistent_factors = ["bp", "cholesterol"]
    sample_evidence = [
        "BP: 145/95 (12/03/2024)",
        "BP: 138/88 (20/06/2024)",
        "Cholesterol: 230 mg/dL (12/03/2024)",
    ]

    result = generate_explanation(sample_risk_data, sample_consistent_factors, sample_evidence)
    print(result)