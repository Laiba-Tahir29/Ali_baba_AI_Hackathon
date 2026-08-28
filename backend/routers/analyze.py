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

from ..services.pdf_extraction import (
    extract_profile,
)

from ..services.consolidation import (
    consolidate_profiles,
)

from ..services.risk_model import (
    predict_risk,
)

from ..services.explanation import (
    generate_explanation,
)

from ..services.rag_pipeline import (
    build_rag_index_for_patient,
    retrieve_relevant_evidence_chunks,
)

from .upload import (
    PATIENT_FILE_REGISTRY,
)


router = APIRouter(
    tags=["Clinical Analysis Pipeline"]
)


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


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Execute clinical risk analysis pipeline",
)
async def analyze_patient(
    request: AnalyzeRequest,
):

    patient_id = (
        request.patient_id.strip()
    )

    # ========================================================
    # CHECK UPLOAD
    # ========================================================

    pdf_path = PATIENT_FILE_REGISTRY.get(
        patient_id
    )

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

        # ====================================================
        # STEP 2
        # RAG
        # ====================================================

        rag_store = (
            build_rag_index_for_patient(
                raw_profiles
            )
        )

        # ====================================================
        # STEP 3
        # CONSOLIDATION
        # ====================================================

        consolidated = (
            consolidate_profiles(
                raw_profiles
            )
        )

        # ====================================================
        # STEP 4
        # RANDOM FOREST
        # ====================================================

        risk_output = predict_risk(
            consolidated
        )

        # ====================================================
        # STEP 5
        # RAG EVIDENCE
        # ====================================================

        top_factors = risk_output.get(
            "top_3_factors",
            [],
        )

        query = (
            "cardiovascular risk factors "
            + ", ".join(top_factors)
            + " blood pressure cholesterol glucose"
        )

        rag_evidence = (
            retrieve_relevant_evidence_chunks(
                rag_store,
                query=query,
                top_k=3,
            )
        )

        # ====================================================
        # STEP 6
        # LLM EXPLANATION
        # ====================================================

        explanation_text = (
            generate_explanation(
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
        )

        # ====================================================
        # REPORT ITEMS
        # ====================================================

        report_items = []

        for profile in raw_profiles:

            if hasattr(
                profile,
                "model_dump",
            ):

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
        # PATIENT META
        # ====================================================

        patient_info = (
            PATIENT_METADATA_LOOKUP.get(
                patient_id,
                {
                    "name":
                        f"Patient {patient_id}",

                    "mrn":
                        f"MRN-{patient_id.replace('PT-', '')}",
                },
            )
        )

        patient_meta = PatientMeta(

            id=patient_id,

            name=patient_info[
                "name"
            ],

            mrn=patient_info[
                "mrn"
            ],

            analyzedAt=(
                datetime.now()
                .strftime(
                    "%I:%M %p"
                )
            ),
        )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return AnalysisResponse(

            reports=report_items,

            final_profile=consolidated,

            risk=RiskAnalysis(
                **risk_output
            ),

            explanation=explanation_text,

            patient_meta=patient_meta,
        )

    except HTTPException:

        raise

    except Exception as exc:

        print(
            "\n[Clinical Pipeline ERROR]"
        )

        print(
            repr(exc)
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "Clinical analysis pipeline error: "
                f"{str(exc)}"
            ),
        )