"""
vector_store.py
----------------
Person B (RAG + LLM) — Vector store module for building FAISS-based
retrieval indexes and performing similarity search over text chunks.
Uses sentence-transformers for embedding generation.

MODEL CHOICE NOTE:
    Default is 'all-MiniLM-L6-v2' — lightweight (~80MB), fast on CPU, no
    API key needed. This is the model decided on for the hackathon (good
    enough for medical-term similarity matching, doesn't eat time/storage
    budget). Only switch to a larger model like 'all-mpnet-base-v2' if
    testing shows retrieval quality is actually a problem — it's ~5x the
    size and noticeably slower to load/encode.
"""

from typing import List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


def build_vector_store(
    chunks: List[str],
    model_name: str = "all-MiniLM-L6-v2"
) -> Tuple[faiss.IndexFlatL2, SentenceTransformer]:
    """
    Build a FAISS IndexFlatL2 vector store from a list of text chunks.

    Args:
        chunks: List of text chunk strings to embed and index.
        model_name: Name of the sentence-transformers model to use
            (default: 'all-MiniLM-L6-v2').

    Returns:
        A tuple of (faiss_index, embed_model) so both can be reused for queries.

    Raises:
        ValueError: If chunks is empty.
    """
    if not chunks:
        raise ValueError("Cannot build vector store from an empty list of chunks.")

    embed_model = SentenceTransformer(model_name)

    # Encode all chunks into dense embeddings
    embeddings = embed_model.encode(chunks, show_progress_bar=False)
    embeddings = np.array(embeddings, dtype="float32")

    # Normalize embeddings for cosine similarity via L2 index
    faiss.normalize_L2(embeddings)

    # Build a flat L2 index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index, embed_model


def retrieve(
    query: str,
    index: faiss.IndexFlatL2,
    chunks: List[str],
    embed_model: SentenceTransformer,
    k: int = 5
) -> List[str]:
    """
    Retrieve the top-k most relevant chunks for a given query.

    Args:
        query: The query string to search for.
        index: The FAISS index built from the chunks.
        chunks: The original list of chunk strings (same order as indexed).
        embed_model: The sentence-transformers model used to embed the query.
        k: Number of top results to return (default: 5).

    Returns:
        A list of the top-k most relevant chunk strings.
    """
    if not query or not query.strip():
        return []

    if index.ntotal == 0:
        return []

    # Clamp k to the number of indexed vectors
    k = min(k, index.ntotal)

    # Embed and normalize the query vector
    query_embedding = embed_model.encode([query], show_progress_bar=False)
    query_embedding = np.array(query_embedding, dtype="float32")
    faiss.normalize_L2(query_embedding)

    # Search the index
    distances, indices = index.search(query_embedding, k)

    # Map returned indices back to chunk strings
    results = [chunks[idx] for idx in indices[0] if idx != -1]
    return results


# ---- Quick manual test ----
if __name__ == "__main__":
    sample_chunks = [
        "Blood Pressure: 145/95, elevated, needs monitoring.",
        "Cholesterol: 230 mg/dL, above normal range.",
        "Patient reports occasional chest discomfort during exercise.",
        "Smoking status: yes, 1 pack per day for 10 years.",
        "Family history of cardiovascular disease: yes, father had a heart attack at 55.",
    ]

    index, model = build_vector_store(sample_chunks)

    for test_query in ["blood pressure", "cholesterol", "smoking history"]:
        results = retrieve(test_query, index, sample_chunks, model, k=2)
        print(f"\nQuery: '{test_query}'")
        for r in results:
            print(f"  -> {r}")