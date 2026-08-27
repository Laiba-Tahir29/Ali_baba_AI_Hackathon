from datetime import datetime
from fastapi import APIRouter, HTTPException
from ..models.schemas import (
    AnalyzeRequest,
    AnalysisResponse,
    ReportItem,
    FinalProfile,
    RiskAnalysis,
    PatientMeta,
)
from ..services.pdf_extraction import extract_profile
from ..services.consolidation import consolidate_profiles
from ..services.risk_model import predict_risk
from ..services.explanation import generate_explanation
from ..services.rag_pipeline import build_rag_index_for_patient, retrieve_relevant_evidence_chunks
from .upload import PATIENT_FILE_REGISTRY

router = APIRouter(tags=["Clinical Analysis Pipeline"])

# Metadata lookup for demo patients
PATIENT_METADATA_LOOKUP = {
    "PT-8821": {
        "name": "Eleanor Caldwell",
        "mrn": "MRN-78429"
    },
    "PT-1204": {
        "name": "Jameson Wright",
        "mrn": "MRN-99312"
    },
    "PT-22105": {
        "name": "Maria Sanchez",
        "mrn": "MRN-22105"
    }
}


@router.post("/analyze", response_model=AnalysisResponse, summary="Execute full multi-report risk synthesis pipeline")
async def analyze_patient(request: AnalyzeRequest):
    """
    Orchestrates the complete 5-layer pipeline:
    1. Document extraction (PDF -> list of per-report profiles from genuine file)
    2. RAG Indexing & Chunking (Vector store creation with Gemini / TF-IDF embeddings)
    3. Profile consolidation (LLM reconciliation + longitudinal consistency)
    4. ML Risk prediction (Random Forest inference + SHAP attributions)
    5. Semantic Retrieval & LLM Explanation (Grounded narrative generation)
    6. Server-side Supabase persistence (gracefully degraded if unconfigured)
    """
    patient_id = request.patient_id.strip()
    pdf_path = PATIENT_FILE_REGISTRY.get(patient_id)

    try:
        # Step 1: Extract individual encounter profiles from genuine uploaded PDF
        raw_profiles = extract_profile(pdf_path=pdf_path)
        if not raw_profiles:
            raise HTTPException(
                status_code=422,
                detail="Unable to extract clinical data from the uploaded file. Please ensure it is a valid medical report PDF containing legible encounter text."
            )

        # Step 2: Build local RAG Vector Store across patient's encounter text
        rag_store = build_rag_index_for_patient(raw_profiles)

        # Step 3: Consolidate longitudinal profile (LLM reconciliation + consistency)
        consolidated = consolidate_profiles(raw_profiles)

        # Persist extracted reports to Supabase if configured
        try:
            from ..services.supabase_client import (
                persist_reports_after_consolidation,
                persist_analysis_results,
                persist_ai_summary,
                update_patient_with_extracted_data,
            )
            update_patient_with_extracted_data(patient_id, age=consolidated.get("age"))
            persist_reports_after_consolidation(patient_id, raw_profiles)
        except Exception as e:
            print(f"[Supabase Notice] Reports/Patient sync: {e}")

        # Step 4: Run ML model inference for risk score & top drivers (Person A)
        risk_output = predict_risk(consolidated)

        # Step 5: Retrieve semantically relevant evidence chunks for grounding
        rag_evidence = retrieve_relevant_evidence_chunks(
            rag_store,
            query=f"cardiovascular risk factors {', '.join(risk_output.get('top_3_factors', []))} blood pressure cholesterol glucose",
            top_k=3
        )

        # Step 6: Generate LLM clinical narrative summary with Gemini (Person B)
        explanation_text = generate_explanation(
            risk_data=risk_output,
            consistent_high_factors=consolidated.get("consistent_high_factors", []),
            evidence=rag_evidence if rag_evidence else raw_profiles
        )

        # Persist analysis results & AI summary to Supabase if configured
        try:
            persist_analysis_results(
                patient_id=patient_id,
                pdf_path=pdf_path,
                risk_level=risk_output.get("risk_level", "low"),
                top_factors=risk_output.get("top_3_factors", []),
                consistent_high_factors=consolidated.get("consistent_high_factors", []),
                explanation=explanation_text
            )
            persist_ai_summary(
                patient_id=patient_id,
                summary_text=explanation_text,
                risk_notes=f"Calculated risk score: {risk_output.get('risk_score')}% ({risk_output.get('risk_level')})"
            )
        except Exception as e:
            print(f"[Supabase Notice] Results sync: {e}")

        # Build clean report items for evidence display
        report_items = [
            ReportItem(
                date=p.get("date", "Unknown Date"),
                doctor=p.get("doctor", "Unknown Attending"),
                clinic=p.get("clinic", "Clinic"),
                snippet=p.get("snippet", "")
            )
            for p in raw_profiles
        ]

        # Attach patient metadata
        patient_meta_info = PATIENT_METADATA_LOOKUP.get(
            patient_id,
            {
                "name": f"Patient {patient_id}",
                "mrn": f"MRN-{patient_id.replace('PT-', '')}"
            }
        )

        patient_meta = PatientMeta(
            id=patient_id,
            name=patient_meta_info["name"],
            mrn=patient_meta_info["mrn"],
            analyzedAt=datetime.now().strftime("%I:%M %p")
        )

        return AnalysisResponse(
            reports=report_items,
            final_profile=FinalProfile(**consolidated),
            risk=RiskAnalysis(**risk_output),
            explanation=explanation_text,
            patient_meta=patient_meta
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Clinical analysis pipeline error: {str(e)}"
        )
