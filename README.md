# Cardiovascular Risk Summarizer

A doctor-facing clinical triage tool for cardiovascular risk summarization and multi-report health factor consolidation across historical patient records.

## Overview

Physicians often need to review voluminous multi-year clinical documentation across disparate encounters to evaluate a patient's cardiovascular risk profile. **Cardiovascular Risk Summarizer** streamlines this workflow by:

- Ingesting multi-encounter PDF records (clinic visit notes, discharge summaries, laboratory panels).
- Extracting and standardizing longitudinal vital metrics (Blood Pressure, Total Cholesterol, Fasting Glucose, BMI, Demographic/Family History).
- Computing an integrated cardiovascular risk score, risk level flag (Low, Moderate, High), and identifying the top contributing risk drivers.
- Displaying interactive factor contribution charts and chronological encounter snippet evidence for rapid verification.
- Providing an attending physician scratchpad and review sign-off mechanism.

> **Disclaimer:** This tool is designed strictly as a clinical triage aid for physician review and does not constitute a medical diagnosis.

---

## Tech Stack

- **Frontend Framework:** React 19 with TypeScript
- **Styling & UI:** Tailwind CSS v4, Lucide React icons
- **Data Visualization:** Recharts (Horizontal factor contribution breakdown)
- **Transitions & Animations:** Framer Motion
- **Backend API Integration:** FastAPI REST backend (`/upload`, `/analyze` endpoints)

---

## Project Structure

```
├── index.html                 # HTML shell and metadata
├── package.json               # Frontend dependencies and scripts
├── vite.config.ts             # Vite build configuration
├── tsconfig.json              # TypeScript configuration
├── backend/                   # FastAPI Backend (5-Layer Triage Architecture)
│   ├── main.py                # FastAPI app entry & CORS configuration
│   ├── requirements.txt       # Backend dependencies
│   ├── models/
│   │   └── schemas.py         # Pydantic contract models (AnalysisResponse, etc.)
│   ├── routers/
│   │   ├── upload.py          # POST /upload (PDF ingestion)
│   │   └── analyze.py         # POST /analyze (Pipeline orchestration)
│   ├── services/
│   │   ├── pdf_extraction.py  # Layer 1 & 2: extract_profile() (Person B)
│   │   ├── consolidation.py   # Layer 3: consolidate_profiles() (Person B)
│   │   ├── risk_model.py      # Layer 4: predict_risk() (Person A)
│   │   └── explanation.py     # Layer 5: generate_explanation() (Person B)
│   └── uploads/               # Uploaded PDF document storage
├── src/
│   ├── main.tsx               # Application entry point
│   ├── App.tsx                # Main view router & clinical state management
│   ├── index.css              # Global styles & Tailwind imports
│   ├── api/
│   │   └── client.ts          # API integration & mock simulation fallback
│   ├── components/
│   │   ├── ClinicalHeader.tsx     # Application navigation header & doctor profile
│   │   ├── UploadCard.tsx         # Drag-and-drop PDF ingestion & preset patient loader
│   │   ├── LoadingState.tsx       # Multi-stage synthesis loading indicator
│   │   ├── RiskBadge.tsx          # Calculated risk flag & patient summary bar
│   │   ├── FactorsGrid.tsx        # Consolidated vital parameters & alert triggers
│   │   ├── FactorsChart.tsx       # Recharts top contributing factor distribution
│   │   ├── EvidenceAccordion.tsx  # OCR encounter quotes & historical snippets
│   │   ├── ExplanationCard.tsx    # Doctor narrative summary & physician sign-off
│   │   ├── ErrorState.tsx         # Error feedback & retry interface
│   │   └── ui/                    # Reusable animation & loading primitives
│   ├── config/
│   │   └── constants.ts       # Clinical constants, risk thresholds & mock presets
│   ├── lib/
│   │   └── utils.ts           # Utility helpers
│   └── types/
│       └── clinical.ts        # TypeScript interfaces for clinical data schemas
```

---

## Getting Started

### Prerequisites

- Node.js (v18.0.0 or later)
- npm or bun

### Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   cd Hackathon-main
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   *(Optionally update `VITE_API_BASE_URL` if your FastAPI backend runs on a custom port/host).*

### Running Locally

Start the Vite development server:
```bash
npm run dev
```

The application will be accessible at `http://localhost:3000`.

### Backend Setup & Execution
1. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. Run the FastAPI development server from the project root:
   ```bash
   py -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```

3. API Documentation (Interactive Swagger UI):
   Visit `http://127.0.0.1:8000/docs`

### Available Scripts

- `npm run dev` — Start local Vite development server on `http://localhost:3000`
- `npm run build` — Build production bundle to `dist/`
- `npm run preview` — Locally preview the production build on `http://localhost:3000`
