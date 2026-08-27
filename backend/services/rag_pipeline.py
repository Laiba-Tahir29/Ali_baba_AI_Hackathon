"""
Layer 2 & 5 RAG Pipeline: Chunking, Embedding Index, & Semantic Retrieval
Owner: Person B (rag-llm branch)

Chunks multi-report medical text, generates embeddings (using Google GenAI gemini-embedding-001
with local TF-IDF cosine-similarity fallback for offline robustness), indexes chunks in a local
vector store, and retrieves the most relevant clinical excerpts to power EvidenceAccordion
and generate_explanation.
"""

import os
import re
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class MedicalChunk:
    def __init__(self, text: str, report_index: int, doctor: str, clinic: str, date: str):
        self.text = text.strip()
        self.report_index = report_index
        self.doctor = doctor
        self.clinic = clinic
        self.date = date

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "report_index": self.report_index,
            "doctor": self.doctor,
            "clinic": self.clinic,
            "date": self.date
        }


class LocalVectorStore:
    """
    Lightweight in-memory vector store supporting both Gemini embedding vectors
    and local TF-IDF vectorization with cosine similarity retrieval.
    """
    def __init__(self):
        self.chunks: List[MedicalChunk] = []
        self.embeddings: Optional[np.ndarray] = None
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.use_gemini = False
        self.active_model = "tf-idf"

    def build_index(self, chunks: List[MedicalChunk]) -> None:
        self.chunks = chunks
        if not chunks:
            return

        texts = [c.text for c in chunks]
        gemini_key = os.getenv("GEMINI_API_KEY")

        if gemini_key and not gemini_key.startswith("your_"):
            for emb_model in ["gemini-embedding-001", "gemini-embedding-2", "text-embedding-004"]:
                try:
                    from google import genai
                    client = genai.Client(api_key=gemini_key)
                    vectors = []
                    for t in texts:
                        res = client.models.embed_content(
                            model=emb_model,
                            contents=t
                        )
                        if hasattr(res, "embedding") and res.embedding:
                            vectors.append(res.embedding.values)
                        elif hasattr(res, "embeddings") and res.embeddings:
                            vectors.append(res.embeddings[0].values)
                    if len(vectors) == len(texts):
                        self.embeddings = np.array(vectors, dtype=np.float32)
                        self.use_gemini = True
                        self.active_model = emb_model
                        print(f"[Stage 2: RAG Pipeline] Status: [LIVE GEMINI EMBEDDINGS - {emb_model}] Indexed {len(chunks)} chunks (dim: {self.embeddings.shape[1]}).")
                        return
                except Exception as e:
                    print(f"[Stage 2 Notice] Gemini embedding {emb_model} attempt: {e}")

        # Local TF-IDF cosine-similarity fallback index
        print("[Stage 2: RAG Pipeline] Status: [FALLBACK LOCAL TF-IDF COSINE INDEX]")
        self.tfidf_vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
        self.use_gemini = False
        self.active_model = "local-tfidf"

    def query(self, query_text: str, top_k: int = 3) -> List[MedicalChunk]:
        if not self.chunks:
            return []

        if self.use_gemini and self.embeddings is not None:
            try:
                from google import genai
                gemini_key = os.getenv("GEMINI_API_KEY")
                client = genai.Client(api_key=gemini_key)
                res = client.models.embed_content(
                    model=self.active_model,
                    contents=query_text
                )
                q_vec = None
                if hasattr(res, "embedding") and res.embedding:
                    q_vec = np.array(res.embedding.values, dtype=np.float32)
                elif hasattr(res, "embeddings") and res.embeddings:
                    q_vec = np.array(res.embeddings[0].values, dtype=np.float32)

                if q_vec is not None:
                    norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(q_vec)
                    scores = np.dot(self.embeddings, q_vec) / np.maximum(norms, 1e-9)
                    top_indices = np.argsort(scores)[::-1][:top_k]
                    return [self.chunks[i] for i in top_indices]
            except Exception as e:
                print(f"[Stage 2 Notice] Gemini query retrieval error: {e}, using TF-IDF.")

        # TF-IDF Cosine Retrieval
        if self.tfidf_vectorizer and self.tfidf_matrix is not None:
            try:
                q_vec = self.tfidf_vectorizer.transform([query_text])
                scores = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
                top_indices = np.argsort(scores)[::-1][:top_k]
                return [self.chunks[i] for i in top_indices]
            except Exception:
                pass

        return self.chunks[:top_k]


def chunk_clinical_reports(raw_reports: List[Dict[str, Any]]) -> List[MedicalChunk]:
    """
    Chunks per-report text into focused semantic clinical passages (100-250 characters),
    retaining metadata for provenance and citation.
    """
    chunks = []
    for idx, report in enumerate(raw_reports, start=1):
        doctor = report.get("doctor", f"Physician #{idx}")
        clinic = report.get("clinic", "Cardiology Center")
        date = report.get("date", f"Encounter #{idx}")
        raw_text = report.get("snippet", "")

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw_text) if len(s.strip()) > 15]
        if not sentences:
            sentences = [raw_text.strip()] if raw_text.strip() else [f"Clinical encounter at {clinic} on {date}."]

        for i in range(0, len(sentences), 2):
            chunk_text = " ".join(sentences[i:i+2])
            chunks.append(MedicalChunk(
                text=chunk_text,
                report_index=idx,
                doctor=doctor,
                clinic=clinic,
                date=date
            ))
    return chunks


def build_rag_index_for_patient(raw_reports: List[Dict[str, Any]]) -> LocalVectorStore:
    """Chunks patient reports and returns a populated vector search store."""
    chunks = chunk_clinical_reports(raw_reports)
    store = LocalVectorStore()
    store.build_index(chunks)
    return store


def retrieve_relevant_evidence_chunks(store: LocalVectorStore, query: str = "cardiovascular risk blood pressure cholesterol glucose vitals", top_k: int = 3) -> List[str]:
    """Retrieves top relevant chunk text strings for LLM context grounding."""
    matched = store.query(query, top_k=top_k)
    return [f"[{m.date} - {m.doctor} ({m.clinic})]: {m.text}" for m in matched]
