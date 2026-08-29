from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..models.schemas import (
    AnalyzeRequest,
    AnalysisResponse,
    ReportItem,
    RiskAnalysis,
    PatientMeta,
)

from ..services.pdf_extraction import extract_profile
from ..services.consolidation import consolidate_profiles
from ..services.risk_model import predict_risk
from ..services.explanation import generate_explanation

from ..services.rag_pipeline import (
    build_rag_index_for_patient,
    retrieve_relevant_evidence_chunks,
)

from ..services.supabase_client import persist_analysis_results

from .upload import PATIENT_FILE_REGISTRY


router = APIRouter(
    tags=["Clinical Analysis Pipeline"]
)


# ============================================================
# DEMO PATIENT METADATA
# ============================================================

PATIENT_METADATA_LOOKUP = {

    "PT-8821": {
        "name": "Eleanor Caldwell",
        "mrn": "MRN-78429",
    },

    "PT-1204": {
        "name": "Jameson Wright",
        "mrn": "MRN-99312",
    },

    "PT-22105": {
        "name": "Maria Sanchez",
        "mrn": "MRN-22105",
    },
}


# ============================================================
# ANALYZE ENDPOINT
# ============================================================

@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Execute clinical risk analysis pipeline",
)
async def analyze_patient(
    request: AnalyzeRequest,
):

    patient_id = request.patient_id.strip()

    # ========================================================
    # CHECK UPLOAD
    # ========================================================

    pdf_path = PATIENT_FILE_REGISTRY.get(patient_id)

    if not pdf_path:
        raise HTTPException(
            status_code=404,
            detail=(
                "No uploaded medical report "
                f"found for patient {patient_id}."
            ),
        )

    try:

        # ====================================================
        # STEP 1
        # PDF → PER REPORT PROFILES
        # ====================================================

        print("\n============================================")
        print("[Stage 1: PDF Extraction] Starting...")
        print("============================================")

        raw_profiles = extract_profile(
            pdf_path=pdf_path
        )

        if not raw_profiles:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Unable to extract clinical "
                    "data from the uploaded PDF."
                ),
            )

        print(
            f"[Stage 1: PDF Extraction] "
            f"Extracted {len(raw_profiles)} encounter(s)."
        )

        # ====================================================
        # STEP 2
        # RAG
        # ====================================================

        print("\n============================================")
        print("[Stage 2: RAG Pipeline] Starting...")
        print("============================================")

        rag_store = build_rag_index_for_patient(
            raw_profiles
        )

        # ====================================================
        # STEP 3
        # CONSOLIDATION
        # ====================================================

        print("\n============================================")
        print("[Stage 3: Profile Consolidation] Starting...")
        print("============================================")

        consolidated = consolidate_profiles(
            raw_profiles
        )

        # ====================================================
        # STEP 4
        # RANDOM FOREST RISK PREDICTION
        # ====================================================

        print("\n============================================")
        print("[Stage 4: Risk Prediction] Starting...")
        print("============================================")

        print("[DEBUG] Calling predict_risk()...")

        risk_output = predict_risk(
            consolidated
        )

        print("[DEBUG] predict_risk() returned:")
        print(risk_output)

        print(
            "[DEBUG] risk_score =",
            risk_output.get("risk_score")
        )

        print(
            "[DEBUG] risk_level =",
            risk_output.get("risk_level")
        )

        print(
            "[DEBUG] top_3_factors =",
            risk_output.get("top_3_factors")
        )

        # ====================================================
        # STEP 5
        # RAG EVIDENCE + LLM EXPLANATION
        # ====================================================

        print("\n============================================")
        print("[Stage 5: Clinical Explanation] Starting...")
        print("============================================")

        if risk_output.get("status") == "insufficient_data":

            query = (
                "cardiovascular health factors "
                "blood pressure cholesterol glucose"
            )

        else:

            top_factors = (
                risk_output.get("top_factors")
                or risk_output.get("top_3_factors")
                or []
            )

            query = (
                "cardiovascular risk factors "
                + ", ".join(top_factors)
                + " blood pressure cholesterol glucose"
            )

        rag_evidence = retrieve_relevant_evidence_chunks(
            rag_store,
            query=query,
            top_k=3,
        )

        explanation_text = generate_explanation(
            risk_data=risk_output,

            consistent_high_factors=(
                consolidated.consistent_high_factors
            ),

            evidence=(
                rag_evidence
                if rag_evidence
                else raw_profiles
            ),
        )

        print(
            "[Stage 5: Clinical Explanation] "
            "Explanation generated successfully."
        )

        # ====================================================
        # STEP 6
        # REPORT ITEMS
        # ====================================================

        report_items = []

        for profile in raw_profiles:

            if hasattr(profile, "model_dump"):
                data = profile.model_dump()
            else:
                data = profile

            report_items.append(
                ReportItem(
                    date=data.get(
                        "date",
                        "Unknown Date",
                    ),

                    doctor=data.get(
                        "doctor",
                        "Unknown Attending",
                    ),

                    clinic=data.get(
                        "clinic",
                        "Clinic",
                    ),

                    snippet=data.get(
                        "snippet",
                        "",
                    ),
                )
            )

        # ====================================================
        # STEP 7
        # PATIENT META
        # ====================================================

        patient_info = PATIENT_METADATA_LOOKUP.get(
            patient_id,
            {
                "name": f"Patient {patient_id}",
                "mrn": (
                    f"MRN-"
                    f"{patient_id.replace('PT-', '')}"
                ),
            },
        )

        patient_meta = PatientMeta(

            id=patient_id,

            name=patient_info["name"],

            mrn=patient_info["mrn"],

            analyzedAt=datetime.now().strftime(
                "%I:%M %p"
            ),
        )

        # ====================================================
        # STEP 8
        # FINAL REPORT DATA
        # ====================================================

        status_value = risk_output.get(
            "status"
        )

        # ====================================================
        # STEP 9
        # SAVE FINAL REPORT TO SUPABASE
        # ====================================================

        try:

            persist_analysis_results(

                patient_id=patient_id,

                pdf_path=pdf_path,

                risk_level=(
                    risk_output.get(
                        "risk_level",
                        "Unknown",
                    )
                ),

                top_factors=(
                    risk_output.get(
                        "top_3_factors"
                    )
                    or risk_output.get(
                        "top_factors"
                    )
                    or []
                ),

                consistent_high_factors=(
                    consolidated.consistent_high_factors
                ),

                explanation=explanation_text,
            )

            print(
                "[Stage 6: Supabase Persistence] "
                "Final analysis report saved."
            )

        except Exception as supabase_error:

            # Supabase failure should NOT break the analysis.
            print(
                "[Supabase Notice] "
                f"Final report storage failed: "
                f"{supabase_error}"
            )

        # ====================================================
        # STEP 10
        # RETURN FINAL RESPONSE TO FRONTEND
        # ====================================================

        print("\n============================================")
        print("[Clinical Pipeline] Completed Successfully")
        print("============================================")

        return AnalysisResponse(

            status=status_value,

            reports=report_items,

            final_profile=consolidated,

            risk=RiskAnalysis(
                **risk_output
            ),

            explanation=explanation_text,

            patient_meta=patient_meta,

            missing_fields=(
                risk_output.get(
                    "missing_fields",
                    []
                )
            ),

            imputed_fields=(
                risk_output.get(
                    "imputed_fields",
                    []
                )
            ),

            message=risk_output.get(
                "message"
            ),
        )

    # ========================================================
    # HTTP ERRORS
    # ========================================================

    except HTTPException:
        raise

    # ========================================================
    # UNEXPECTED ERRORS
    # ========================================================

    except Exception as exc:

        print(
            "\n============================================"
        )

        print(
            "[Clinical Pipeline ERROR]"
        )

        print(
            repr(exc)
        )

        print(
            "============================================"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Clinical analysis pipeline error"
            ),
        )