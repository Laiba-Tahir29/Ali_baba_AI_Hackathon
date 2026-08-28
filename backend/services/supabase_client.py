"""
Supabase Data Persistence Layer
Initializes the supabase-py client once using SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
Provides asynchronous/synchronous helpers to persist patients, encounter reports,
risk analysis results, and AI clinical summaries according to the project schema.
"""

import os
import uuid
from typing import Dict, Any, List, Optional

_supabase_client = None
_is_configured = None


def get_supabase_client():
    """
    Initializes and returns the singleton Supabase client instance.
    Returns None if SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is not configured.
    """
    global _supabase_client, _is_configured
    if _is_configured is not None:
        return _supabase_client

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    if not url or not key or "your-project" in url:
        _is_configured = False
        _supabase_client = None
        return None

    try:
        from supabase import create_client, Client
        _supabase_client = create_client(url, key)
        _is_configured = True
        return _supabase_client
    except Exception as e:
        print(f"[Supabase Notice] Initialization failed: {e}")
        _is_configured = False
        _supabase_client = None
        return None


# Map string patient ID (e.g. PT-8821) to stable UUID for Supabase
_PATIENT_UUID_MAP: Dict[str, str] = {}


def get_or_create_patient_uuid(patient_id: str) -> str:
    if patient_id not in _PATIENT_UUID_MAP:
        try:
            val = str(uuid.UUID(patient_id))
            _PATIENT_UUID_MAP[patient_id] = val
        except ValueError:
            _PATIENT_UUID_MAP[patient_id] = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"cardio.patient.{patient_id}"))
    return _PATIENT_UUID_MAP[patient_id]


def persist_patient_on_upload(patient_id: str, name: str = "Unknown Patient", age: Optional[int] = None) -> Optional[str]:
    """Inserts or verifies patient record in the patients table."""
    client = get_supabase_client()
    if not client:
        return None

    patient_uuid = get_or_create_patient_uuid(patient_id)
    try:
        data = {
            "id": patient_uuid,
            "name": name,
            "age": age,
            "email": None
        }
        res = client.table("patients").upsert(data).execute()
        print(f"[Stage 5: Supabase Persistence] Status: [LIVE SUPABASE] Upserted patient: id={patient_uuid} ({name})")
        return patient_uuid
    except Exception as e:
        print(f"[Supabase Notice] Failed to persist patient {patient_id}: {e}")
        return None


def update_patient_with_extracted_data(patient_id: str, age: Optional[int] = None, name: Optional[str] = None) -> None:
    """Updates the patient record with the real extracted age once report extraction runs."""
    client = get_supabase_client()
    if not client or age is None:
        return

    patient_uuid = get_or_create_patient_uuid(patient_id)
    try:
        update_data = {"age": int(age)}
        if name:
            update_data["name"] = name
        client.table("patients").update(update_data).eq("id", patient_uuid).execute()
        print(f"[Stage 5: Supabase Persistence] Status: [LIVE SUPABASE] Updated patient {patient_uuid} with real extracted age={age}")
    except Exception as e:
        print(f"[Supabase Notice] Failed to update patient extracted data: {e}")


def persist_reports_after_consolidation(patient_id: str, raw_reports: List[Dict[str, Any]]) -> None:
    """Inserts parsed source reports into the reports table."""
    client = get_supabase_client()
    if not client or not raw_reports:
        return

    patient_uuid = get_or_create_patient_uuid(patient_id)
    try:
        rows = []
        for r in raw_reports:
            report_text = f"Encounter: {r.get('date', '')} | Doctor: {r.get('doctor', '')} | Clinic: {r.get('clinic', '')}\n{r.get('snippet', '')}"
            rows.append({
                "id": str(uuid.uuid4()),
                "patient_id": patient_uuid,
                "report_text": report_text,
                "report_type": "cardiology_encounter"
            })
        res = client.table("reports").insert(rows).execute()
        print(f"[Stage 5: Supabase Persistence] Status: [LIVE SUPABASE] Inserted {len(rows)} rows into reports.")
    except Exception as e:
        print(f"[Supabase Notice] Failed to persist reports: {e}")


def persist_analysis_results(
    patient_id: str,
    pdf_path: Optional[str],
    risk_level: str,
    top_factors: List[str],
    consistent_high_factors: List[str],
    explanation: str
) -> None:
    """Inserts risk prediction record into analysis_results table."""
    client = get_supabase_client()
    if not client:
        return

    try:
        row = {
            "patient_id": str(patient_id),
            "pdf_path": str(pdf_path or "direct_upload"),
            "risk_level": str(risk_level),
            "top_factors": top_factors,
            "consistent_high_factors": consistent_high_factors,
            "explanation": str(explanation)
        }
        res = client.table("analysis_results").insert(row).execute()
        print(f"[Stage 5: Supabase Persistence] Status: [LIVE SUPABASE] Inserted analysis_results for patient={patient_id}")
    except Exception as e:
        print(f"[Supabase Notice] Failed to persist analysis_results: {e}")


def persist_ai_summary(patient_id: str, summary_text: str, risk_notes: Optional[str] = None) -> None:
    """Inserts AI narrative explanation into ai_summaries table."""
    client = get_supabase_client()
    if not client:
        return

    patient_uuid = get_or_create_patient_uuid(patient_id)
    try:
        row = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_uuid,
            "summary_text": str(summary_text),
            "risk_notes": str(risk_notes or "Clinical triage synthesis for physician review")
        }
        res = client.table("ai_summaries").insert(row).execute()
        print(f"[Stage 5: Supabase Persistence] Status: [LIVE SUPABASE] Inserted ai_summaries: id={row['id']}")
    except Exception as e:
        print(f"[Supabase Notice] Failed to persist ai_summary: {e}")
