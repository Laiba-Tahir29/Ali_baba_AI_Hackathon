# Medical PDF Analyzer API

A FastAPI-based REST API for uploading medical PDF documents and analyzing patient risk factors.

## Features

- **PDF Upload**: Accept and store PDF files with automatic unique naming
- **Risk Analysis**: Mock endpoint that returns structured patient risk assessments
- **Auto-generated Docs**: Interactive API documentation via Swagger UI

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

## API Endpoints

### POST /upload

Upload a PDF file to the server.

**Request**: `multipart/form-data`
- `file`: PDF file (required)

**Response**:
```json
{
  "message": "File uploaded successfully.",
  "path": "uploads/abc123_report.pdf"
}
```

### POST /analyze

Analyze a patient's medical PDF and return risk assessment.

**Request**: `application/json`
```json
{
  "patient_id": "P001",
  "pdf_path": "uploads/abc123_report.pdf"
}
```

**Response**:
```json
{
  "patient_id": "P001",
  "risk_level": "Moderate",
  "top_factors": [
    {
      "factor": "Blood Pressure",
      "value": "145/92 mmHg",
      "contribution": 0.28,
      "detail": "Systolic and diastolic readings are consistently above the normal range."
    },
    {
      "factor": "HbA1c",
      "value": "7.2%",
      "contribution": 0.24,
      "detail": "Indicates suboptimal long-term glucose control over the past 2-3 months."
    },
    {
      "factor": "LDL Cholesterol",
      "value": "160 mg/dL",
      "contribution": 0.20,
      "detail": "Elevated LDL increases the risk of atherosclerotic cardiovascular disease."
    }
  ],
  "consistent_high_factors": [
    "Blood Pressure",
    "HbA1c"
  ],
  "explanation": "The patient presents a Moderate overall risk driven primarily by persistently elevated blood pressure and HbA1c levels. LDL cholesterol adds a secondary but meaningful contribution. Lifestyle modifications (diet, exercise) combined with pharmacological intervention (antihypertensives, statins) are recommended to mitigate these risks."
}
```

## Testing with curl

### Upload a PDF
```bash
curl -X POST "http://127.0.0.1:8000/upload" -F "file=@path/to/your/file.pdf"
```

### Analyze a PDF
```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "P001", "pdf_path": "uploads/your_file.pdf"}'
```

## Interactive Documentation

Visit `http://127.0.0.1:8000/docs` for interactive Swagger UI documentation.

## Project Structure

```
backend/
├── main.py              # FastAPI application with endpoints
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── uploads/            # Directory for uploaded PDFs (auto-created)
```

## Notes

- Uploaded files are stored in the `uploads/` directory with UUID prefixes to prevent naming conflicts
- The `/analyze` endpoint currently returns mock data for demonstration purposes
- File existence is validated before analysis
