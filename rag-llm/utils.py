"""
Shared RAG+LLM utilities.

Contains helpers used by both extraction.py and explanation.py so the
gemini creation and JSON-response cleaning logic live in one place.
"""

import os
from google import genai
from typing import Optional

def get_gemini_model():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    return genai.Client(api_key=api_key)




def clean_json_response(response_text: Optional[str]) -> str:
    """Strip markdown fences and surrounding whitespace from an LLM response."""
    if response_text is None:
        return ""
    text = response_text.strip()
    if text.startswith("```"):
        # Drop opening fence and optional language tag
        text = text.split("\n", 1)[1] if "\n" in text else ""
    if text.endswith("```"):
        text = text.rsplit("\n", 1)[0]
    return text.strip()
