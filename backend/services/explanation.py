"""
Layer 5: LLM Clinical Explanation & Synthesis

Owner: Person B (rag-llm branch)

Synthesizes:
- ML model prediction
- Longitudinal consistency metrics
- RAG retrieved evidence excerpts

into a plain-language summary for physician review
using Google Gemini.

If required ML fields are missing, the system does NOT
invent a risk score or risk level. Instead, it generates
an evidence-based clinical summary from available data.
"""

import os
from typing import Dict, Any, List


# ============================================================
# NORMAL ML EXPLANATION PROMPT
# ============================================================

PROMPT_TEMPLATE = (
    "Patient's cardiovascular risk level is {risk_level} "
    "(calibrated risk score: {risk_score}%). "
    "Top contributing factors from the ML model: {top_factors}. "
    "Factors that stayed persistently high across multiple past "
    "encounters: {consistent_high_factors}. "
    "Evidence excerpts retrieved via RAG similarity search: {evidence}. "
    "Write a concise, plain-language summary (3-4 sentences) "
    "for a cardiologist reviewing this patient. "
    "Highlight what has been persistently elevated across visits "
    "rather than only the latest reading. "
    "Do NOT state a final diagnosis. "
    "Frame everything as an indicative triage summary for physician review."
)


# ============================================================
# HELPER: LIST → TEXT
# ============================================================

def _list_to_text(
    items: List[Any],
    empty_label: str,
) -> str:

    if not items:
        return empty_label

    return ", ".join(
        str(item)
        for item in items
    )


# ============================================================
# HELPER: EXTRACT RAG EVIDENCE
# ============================================================

def _extract_evidence_strings(
    evidence: List[Any],
) -> List[str]:

    extracted = []

    for item in evidence:

        # --------------------------------------------
        # String evidence
        # --------------------------------------------

        if isinstance(item, str):

            extracted.append(item)

        # --------------------------------------------
        # Dictionary / report evidence
        # --------------------------------------------

        elif isinstance(item, dict):

            date = item.get(
                "date",
                "Encounter",
            )

            doctor = item.get(
                "doctor",
                "Physician",
            )

            snippet = item.get(
                "snippet",
                "",
            )

            extracted.append(
                f"[{date} - {doctor}]: "
                f"{snippet[:200]}"
            )

    return extracted


# ============================================================
# GEMINI GENERATION HELPER
# ============================================================

def _generate_with_gemini(
    prompt: str,
) -> str | None:

    gemini_key = os.getenv(
        "GEMINI_API_KEY"
    )

    # --------------------------------------------------------
    # No API key
    # --------------------------------------------------------

    if not gemini_key:

        print(
            "[Stage 4 Notice] "
            "GEMINI_API_KEY not configured."
        )

        return None

    if gemini_key.startswith("your_"):

        print(
            "[Stage 4 Notice] "
            "GEMINI_API_KEY appears to be a placeholder."
        )

        return None

    # --------------------------------------------------------
    # Try available Gemini models
    # --------------------------------------------------------

    model_names = [
        "gemini-3.5-flash-lite",
    ]

    for model_name in model_names:

        try:

            from google import genai

            client = genai.Client(
                api_key=gemini_key
            )

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )

            if (
                response
                and response.text
                and len(
                    response.text.strip()
                ) > 20
            ):

                print(
                    "[Stage 4: Narrative Explanation] "
                    f"Status: [LIVE GEMINI - {model_name}] "
                    f"Generated "
                    f"{len(response.text)} chars."
                )

                return response.text.strip()

        except Exception as exc:

            print(
                "[Stage 4 Notice] "
                f"Gemini model {model_name} "
                f"explanation attempt failed: {exc}"
            )

    return None


# ============================================================
# MAIN EXPLANATION FUNCTION
# ============================================================

def generate_explanation(
    risk_data: Dict[str, Any],
    consistent_high_factors: List[str],
    evidence: List[Any],
) -> str:

    print(
        "[DEBUG Layer 5] risk_data received:",
        risk_data,
    )

    # ========================================================
    # EXTRACT BASIC DATA
    # ========================================================

    status = risk_data.get(
        "status",
        "ok",
    )

    evidence_strings = (
        _extract_evidence_strings(
            evidence
        )
    )

    # ========================================================
    # CASE 1:
    # INSUFFICIENT DATA
    # ========================================================

    if status == "insufficient_data":

        missing_fields = risk_data.get(
            "missing_fields",
            [],
        )

        missing_text = _list_to_text(
            missing_fields,
            "required clinical information",
        )

        evidence_text = _list_to_text(
            evidence_strings[:5],
            "No historical encounter evidence was available.",
        )

        consistent_text = _list_to_text(
            consistent_high_factors,
            "none identified",
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # No risk score / risk level is passed to LLM here.
        # ----------------------------------------------------

        prompt = (
            "You are assisting a physician with cardiovascular "
            "clinical triage.\n\n"

            "The machine-learning cardiovascular risk model "
            "could NOT calculate a risk score because essential "
            f"clinical data is missing: {missing_text}.\n\n"

            "Available longitudinal clinical evidence:\n"
            f"{evidence_text}\n\n"

            "Persistently elevated factors, if any:\n"
            f"{consistent_text}\n\n"

            "Write a concise 3-4 sentence physician-facing "
            "clinical summary.\n\n"

            "Requirements:\n"
            "1. Summarize only the information actually documented "
            "in the available encounter evidence.\n"
            "2. Mention any observable trend across encounters.\n"
            "3. Clearly state that a model-based cardiovascular "
            "risk score could not be calculated because required "
            "data is missing.\n"
            "4. Do NOT invent or estimate missing values.\n"
            "5. Do NOT assign Low, Medium, or High risk.\n"
            "6. Do NOT provide a diagnosis.\n"
            "7. Frame the result as an indicative triage summary "
            "for physician review."
        )

        # ----------------------------------------------------
        # Try Gemini
        # ----------------------------------------------------

        gemini_result = _generate_with_gemini(
            prompt
        )

        if gemini_result:

            return gemini_result

        # ----------------------------------------------------
        # Deterministic fallback
        # ----------------------------------------------------

        print(
            "[Stage 4: Narrative Explanation] "
            "Status: "
            "[FALLBACK DETERMINISTIC ENGINE - INSUFFICIENT DATA]"
        )

        num_encounters = (
            len(evidence)
            if evidence
            else 0
        )

        # ----------------------------------------------------
        # Evidence exists
        # ----------------------------------------------------

        if evidence_strings:

            if consistent_high_factors:

                consistent_text = _list_to_text(
                    consistent_high_factors,
                    "available parameters",
                )

                return (
                    f"Longitudinal review across "
                    f"{num_encounters} clinical encounter "
                    f"record(s) shows documented evidence involving "
                    f"{consistent_text}. "
                    f"A cardiovascular risk score could not be "
                    f"calculated because required clinical data is "
                    f"missing: {missing_text}. "
                    f"The available historical evidence should be "
                    f"reviewed by the physician before completing "
                    f"model-based cardiovascular triage."
                )

            return (
                f"Longitudinal review across "
                f"{num_encounters} clinical encounter record(s) "
                f"shows the available documented clinical "
                f"measurements and encounter history. "
                f"A cardiovascular risk score could not be "
                f"calculated because required clinical data is "
                f"missing: {missing_text}. "
                f"No persistently elevated factors were identified "
                f"from the available documented measurements. "
                f"Additional clinical information is required "
                f"before model-based risk assessment can be completed."
            )

        # ----------------------------------------------------
        # No evidence available
        # ----------------------------------------------------

        return (
            "The available clinical information is insufficient "
            "for a model-based cardiovascular risk assessment. "
            f"The required field(s) missing from the uploaded "
            f"report(s) are: {missing_text}. "
            "No additional historical evidence was available "
            "for longitudinal synthesis. "
            "Further clinical information is required before "
            "risk assessment can be completed."
        )

    # ========================================================
    # CASE 2:
    # NORMAL ML PREDICTION
    # ========================================================

    risk_level = str(
        risk_data.get(
            "risk_level",
            "high",
        )
    ).lower()

    risk_score = risk_data.get(
        "risk_score",
        0.0,
    )

    top_factors = (
        risk_data.get(
            "top_3_factors"
        )
        or risk_data.get(
            "top_factors"
        )
        or []
    )

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    evidence_text = _list_to_text(
        evidence_strings[:3],
        "historical encounter notes",
    )

    top_factors_text = _list_to_text(
        top_factors,
        "general cardiovascular indicators",
    )

    consistent_text = _list_to_text(
        consistent_high_factors,
        "none",
    )

    # --------------------------------------------------------
    # Percentage formatting
    #
    # risk_score from predict_risk() is already percentage
    # in your current implementation, e.g. 17.1349.
    # --------------------------------------------------------

    try:

        formatted_score = (
            f"{float(risk_score):.1f}%"
        )

    except (
        TypeError,
        ValueError,
    ):

        formatted_score = "0%"

    # --------------------------------------------------------
    # Build prompt
    # --------------------------------------------------------

    prompt = PROMPT_TEMPLATE.format(
        risk_level=risk_level.upper(),

        risk_score=formatted_score,

        top_factors=top_factors_text,

        consistent_high_factors=consistent_text,

        evidence=evidence_text,
    )

    # --------------------------------------------------------
    # Try Gemini
    # --------------------------------------------------------

    gemini_result = _generate_with_gemini(
        prompt
    )

    if gemini_result:

        return gemini_result

    # ========================================================
    # NORMAL DETERMINISTIC FALLBACK
    # ========================================================

    print(
        "[Stage 4: Narrative Explanation] "
        "Status: [FALLBACK DETERMINISTIC ENGINE]"
    )

    num_encounters = (
        len(evidence)
        if evidence
        else 1
    )

    consistent_desc = _list_to_text(
        consistent_high_factors,
        "routine parameters",
    )

    # --------------------------------------------------------
    # HIGH
    # --------------------------------------------------------

    if risk_level == "high":

        if top_factors:

            factor_text = ", ".join(
                top_factors[:3]
            )

        else:

            factor_text = (
                "no elevated factors identified"
            )

        return (
            f"Multi-encounter longitudinal analysis across "
            f"{num_encounters} clinical record(s) indicates "
            f"persistent elevation in {consistent_desc}. "
            f"The machine-learning risk model identifies an "
            f"elevated cardiovascular risk score of "
            f"{formatted_score}, with primary driver contributions "
            f"from {factor_text}. "
            f"These findings warrant physician review and "
            f"consideration of targeted follow-up."
        )

    # --------------------------------------------------------
    # MEDIUM
    # --------------------------------------------------------

    elif risk_level == "medium":

        if top_factors:

            factor_text = ", ".join(
                top_factors[:2]
            )

        else:

            factor_text = (
                "general cardiovascular indicators"
            )

        return (
            f"Review across {num_encounters} encounter "
            f"record(s) shows borderline clinical parameters, "
            f"predominantly influenced by {factor_text}. "
            f"Longitudinal tracking reflects intermittent "
            f"elevation in {consistent_desc}, with a calculated "
            f"triage risk score of {formatted_score}. "
            f"Routine physician follow-up is recommended."
        )

    # --------------------------------------------------------
    # LOW
    # --------------------------------------------------------

    else:

        return (
            f"Consolidated parameters reflect stable "
            f"cardiovascular measurements across "
            f"{num_encounters} historical encounter record(s). "
            f"No major persistently elevated factors were "
            f"identified from the available documented data. "
            f"The calculated cardiovascular risk score is "
            f"{formatted_score}. "
            f"Continued routine preventive care and physician "
            f"review are supported."
        )