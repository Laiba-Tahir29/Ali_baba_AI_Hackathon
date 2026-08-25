"""
Text chunking module using LangChain's RecursiveCharacterTextSplitter.
Splits text into overlapping character-based chunks for downstream RAG processing.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[str]:
    """
    Split input text into overlapping character-based chunks.

    Args:
        text: The input text to be chunked.
        chunk_size: Maximum number of characters per chunk (default: 500).
        chunk_overlap: Number of overlapping characters between consecutive chunks (default: 50).

    Returns:
        A list of chunk strings.
    """
    if not text or not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = splitter.split_text(text)
    return chunks
