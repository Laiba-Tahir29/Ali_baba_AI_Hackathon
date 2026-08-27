"""
Layer 5: LLM Clinical Explanation & Synthesis
Owner: Person B (rag-llm branch)

Synthesizes ML model prediction, longitudinal consistency metrics,
and RAG retrieved evidence excerpts into a plain-language summary for physician review
using Google Gemini (gemini-3.6-flash / gemini-flash-latest).
"""

import os
from typing import Dict, Any, List


PROMPT_TEMPLATE = (
    "Patient's cardiovascular risk level is {risk_level} (calibrated risk score: {risk_score}%). "
    "Top contributing factors from the ML model: {top_factors}. "
    "Factors that stayed persistently high across multiple past encounters: {consistent_high_factors}. "
    "Evidence excerpts retrieved via RAG similarity search: {evidence}. "
    "Write a concise, plain-language summary (3-4 sentences) for a cardiologist reviewing this patient. "
    "Highlight what has been persistently elevated across visits rather than only the latest reading. "
    "Do NOT state a final diagnosis — frame everything as an indicative triage summary for physician review."
)


def _list_to_text(items: List[Any], empty_label: str) -> str:
    if not items:
        return empty_label
    return ", ".join(str(item) for item in items)


def _extract_evidence_strings(evidence: List[Any]) -> List[str]:
    extracted = []
    for item in evidence:
        if isinstance(item, str):
            extracted.append(item)
        elif isinstance(item, dict):
            date = item.get("date", "Encounter")
            doctor = item.get("doctor", "Physician")
            snippet = item.get("snippet", "")
            extracted.append(f"[{date} - {doctor}]: {snippet[:120]}")
    return extracted


def generate_explanation(
    risk_data: Dict[str, Any],
    consistent_high_factors: List[str],
    evidence: List[Any]
) -> str:
    """
    Public Interface Function — Person B's Clinical Narrative Explanation.
    
    Generates physician triage narrative using Google Gemini with RAG grounding.
    Falls back gracefully to deterministic clinical rule-based engine if unconfigured.
    """
    risk_level = str(risk_data.get("risk_level", "high")).lower()
    risk_score = risk_data.get("risk_score", 0.0)
    top_factors = risk_data.get("top_3_factors") or risk_data.get("top_factors") or ["Blood Pressure", "Cholesterol"]
    
    evidence_strings = _extract_evidence_strings(evidence)
    prompt = PROMPT_TEMPLATE.format(
        risk_level=risk_level.upper(),
        risk_score=risk_score,
        top_factors=_list_to_text(top_factors, "general cardiovascular indicators"),
        consistent_high_factors=_list_to_text(consistent_high_factors, "none"),
        evidence=_list_to_text(evidence_strings[:3], "historical encounter notes"),
    )

    # 1. Google Gemini Generation
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and not gemini_key.startswith("your_"):
        for model_name in ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite", "gemini-flash-latest"]:
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text and len(response.text.strip()) > 20:
                    print(f"[Stage 4: Narrative Explanation] Status: [LIVE GEMINI - {model_name}] Generated {len(response.text)} chars.")
                    return response.text.strip()
            except Exception as e:
                print(f"[Stage 4 Notice] Gemini model {model_name} explanation attempt: {e}")

    # 2. Clinical Synthesis Fallback Engine
    print("[Stage 4: Narrative Explanation] Status: [FALLBACK DETERMINISTIC ENGINE]")
    num_encounters = len(evidence) if evidence else 1
    consistent_desc = _list_to_text(consistent_high_factors, "routine parameters")

    if risk_level == "high":
        return (
            f"Multi-encounter longitudinal analysis across {num_encounters} clinical records indicates persistent "
            f"elevation in {consistent_desc}. The machine-learning risk model identifies an elevated cardiovascular "
            f"risk score of {risk_score}%, with primary driver contributions from {', '.join(top_factors[:3])}. "
            f"These findings suggest sustained hemodynamic and metabolic strain warranting physician review and consideration of targeted follow-up."
        )
    elif risk_level == "medium":
        return (
            f"Review across {num_encounters} encounter reports shows borderline baseline parameters, predominantly influenced "
            f"by {', '.join(top_factors[:2])}. Longitudinal tracking reflects intermittent elevation in {consistent_desc} "
            f"with a calculated triage risk score of {risk_score}%. Routine physician follow-up and lifestyle modification reinforcement are recommended."
        )
    else:
        return (
            f"Consolidated parameters reflect optimal cardiovascular metrics across all {num_encounters} historical encounter records. "
            f"Blood pressure and fasting metabolic markers remain stable within normal target zones (calibrated score {risk_score}%). "
            f"Continued routine preventive care is supported."
        )
