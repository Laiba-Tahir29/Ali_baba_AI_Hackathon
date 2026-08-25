"""
run_retrieval_pipeline.py
--------------------------
Person B (RAG + LLM) — quick end-to-end test of the RETRIEVAL path
(Path B) on a real PDF: extract_text -> chunk_text -> build_vector_store
-> retrieve.

This does NOT test extraction.py/consolidation.py (Path A, the LLM
extraction path) — this is only for confirming chunking + embeddings +
FAISS retrieval work well on real multi-report PDF content.

Usage:
    python run_retrieval_pipeline.py ../sample_pdfs/cardio_report.pdf
"""

import sys

from extract_text import extract_text
from chunking import chunk_text
from vector_store import build_vector_store, retrieve


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_retrieval_pipeline.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    print("=" * 60)
    print("STEP 1: extract_text()")
    print("=" * 60)
    text = extract_text(pdf_path)
    if text.startswith("[ERROR]"):
        print(text)
        sys.exit(1)
    print(f"Extracted {len(text)} characters.\n")

    print("=" * 60)
    print("STEP 2: chunk_text()")
    print("=" * 60)
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
    print(f"Created {len(chunks)} chunks.")
    for i, c in enumerate(chunks[:3], start=1):
        print(f"  Chunk {i} preview: {c[:80]}...")
    print()

    print("=" * 60)
    print("STEP 3: build_vector_store()")
    print("=" * 60)
    index, embed_model = build_vector_store(chunks)
    print(f"FAISS index built with {index.ntotal} vectors.\n")

    print("=" * 60)
    print("STEP 4: retrieve() — test queries")
    print("=" * 60)
    test_queries = ["blood pressure", "cholesterol", "smoking history", "glucose"]

    for query in test_queries:
        results = retrieve(query, index, chunks, embed_model, k=3)
        print(f"\nQuery: '{query}'")
        for i, r in enumerate(results, start=1):
            preview = r.replace("\n", " ")[:100]
            print(f"  {i}. {preview}...")

    print("\n" + "=" * 60)
    print("Done. Check above: do results for each query come from")
    print("DIFFERENT reports/doctors, not just one? That confirms")
    print("retrieval is working across the whole multi-report PDF.")
    print("=" * 60)


if __name__ == "__main__":
    main()