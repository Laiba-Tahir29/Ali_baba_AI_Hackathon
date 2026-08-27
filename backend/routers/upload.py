import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..models.schemas import UploadResponse

router = APIRouter(tags=["Document Ingestion"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory mapping from patient_id to stored file path
PATIENT_FILE_REGISTRY = {}


@router.post("/upload", response_model=UploadResponse, summary="Upload patient multi-report PDF")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Accepts a multi-report clinical PDF, saves it to the local storage,
    and returns a patient_id for subsequent pipeline analysis.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    filename = file.filename.lower()
    if not filename.endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF documents are supported for clinical ingestion.")

    # Match preset patient IDs if filename contains specific demo keywords
    if "1204" in filename or "medium" in filename or "wright" in filename:
        patient_id = "PT-1204"
    elif "22105" in filename or "low" in filename or "sanchez" in filename:
        patient_id = "PT-22105"
    elif "8821" in filename or "caldwell" in filename:
        patient_id = "PT-8821"
    else:
        # Generate unique patient ID for arbitrary uploads
        patient_id = f"PT-{uuid.uuid4().hex[:6].upper()}"

    # Save uploaded file safely
    base_name = os.path.basename(file.filename)
    safe_filename = f"{patient_id}_{base_name}"
    saved_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        PATIENT_FILE_REGISTRY[patient_id] = saved_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save document: {str(e)}")

    # Persist patient row to Supabase if configured
    try:
        from ..services.supabase_client import persist_patient_on_upload
        persist_patient_on_upload(patient_id=patient_id, name=f"Patient {patient_id}")
    except Exception as e:
        print(f"[Supabase Notice] Background patient sync: {e}")

    return UploadResponse(patient_id=patient_id)
