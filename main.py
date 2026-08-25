import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Load environment variables and set up Supabase client
# ---------------------------------------------------------------------------

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Medical PDF Analyzer API")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class AnalyzeRequest(BaseModel):
    patient_id: str
    pdf_path: str


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    return JSONResponse(
        status_code=200,
        content={"message": "File uploaded successfully.", "path": file_path},
    )


@app.post("/analyze")
async def analyze_pdf(request: AnalyzeRequest):
    if not os.path.isfile(request.pdf_path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.pdf_path}")

    mock_response = {
        "patient_id": request.patient_id,
        "risk_level": "Moderate",
        "top_factors": [
            {"factor": "Blood Pressure", "value": "145/92 mmHg", "contribution": 0.28,
             "detail": "Systolic and diastolic readings are consistently above the normal range."},
            {"factor": "HbA1c", "value": "7.2%", "contribution": 0.24,
             "detail": "Indicates suboptimal long-term glucose control over the past 2-3 months."},
            {"factor": "LDL Cholesterol", "value": "160 mg/dL", "contribution": 0.20,
             "detail": "Elevated LDL increases the risk of atherosclerotic cardiovascular disease."},
        ],
        "consistent_high_factors": ["Blood Pressure", "HbA1c"],
        "explanation": (
            "The patient presents a Moderate overall risk driven primarily by "
            "persistently elevated blood pressure and HbA1c levels. LDL cholesterol "
            "adds a secondary but meaningful contribution. Lifestyle modifications "
            "(diet, exercise) combined with pharmacological intervention "
            "(antihypertensives, statins) are recommended to mitigate these risks."
        ),
    }

    try:
        supabase.table("analysis_results").insert({
            "patient_id": mock_response["patient_id"],
            "pdf_path": request.pdf_path,
            "risk_level": mock_response["risk_level"],
            "top_factors": mock_response["top_factors"],
            "consistent_high_factors": mock_response["consistent_high_factors"],
            "explanation": mock_response["explanation"],
        }).execute()
    except Exception as e:
        print(f"Warning: failed to save to Supabase: {e}")

    return JSONResponse(status_code=200, content=mock_response)