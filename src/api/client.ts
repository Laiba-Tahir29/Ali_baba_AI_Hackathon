import { API_BASE_URL, USE_MOCK, MOCK_API_SIMULATION_DELAY_MS } from "../config/constants";
import { AnalysisResponse } from "../types/clinical";

/**
 * Mock data dictionary corresponding to the exact response shape requested by the contract.
 */
const MOCK_HIGH_RISK_RESPONSE: AnalysisResponse = {
  reports: [
    {
      date: "May 12, 2023",
      doctor: "Dr. Aris",
      clinic: "St. Jude Hospital",
      snippet: "Patient presented for routine checkup. BP recorded at 148/95. Recommended continued monitoring and dietary changes. Continued mild fatigue noted."
    },
    {
      date: "Jan 15, 2023",
      doctor: "Dr. Smith",
      clinic: "Cardio Center",
      snippet: "Cholesterol levels remain high despite initial statin trial. Fasting glucose slightly elevated at 112 mg/dL. Recommending dosage adjustment."
    },
    {
      date: "Oct 04, 2022",
      doctor: "Dr. Henderson",
      clinic: "Metro Health Cardiology",
      snippet: "Follow-up consultation for borderline hypertension. Resting BP 142/90 mmHg. Patient reports history of coronary artery disease in father."
    }
  ],
  final_profile: {
    age: 58,
    bp: "145/92",
    cholesterol: "240",
    glucose: "110",
    bmi: 28.4,
    smoking: "no",
    history: "yes",
    consistent_high_factors: ["bp", "cholesterol"]
  },
  risk: {
    risk_score: 24.5,
    risk_level: "high",
    top_3_factors: ["Blood Pressure", "Cholesterol", "Family History"]
  },
  explanation: "Analysis of historical reports indicates persistent Stage 2 hypertension and hyperlipidemia. While glucose levels are stable, they remain in the pre-diabetic range. The combination of these factors, alongside age and positive family history, supports the elevated risk flag for clinical review.",
  patient_meta: {
    id: "PT-8821",
    name: "Eleanor Caldwell",
    mrn: "MRN-78429",
    analyzedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
};

const MOCK_MEDIUM_RISK_RESPONSE: AnalysisResponse = {
  reports: [
    {
      date: "Nov 20, 2023",
      doctor: "Dr. Vance",
      clinic: "Valley Medical Pavilion",
      snippet: "Patient follow-up regarding lifestyle modifications. BP 136/88 mmHg. Advised 150 mins aerobic activity weekly."
    },
    {
      date: "Jun 14, 2023",
      doctor: "Dr. Patel",
      clinic: "Integrative Heart & Wellness",
      snippet: "Lipid panel shows total cholesterol 218 mg/dL with HDL 42 mg/dL. Fasting blood glucose recorded at 104 mg/dL."
    }
  ],
  final_profile: {
    age: 52,
    bp: "136/88",
    cholesterol: "218",
    glucose: "104",
    bmi: 26.8,
    smoking: "former",
    history: "no",
    consistent_high_factors: ["cholesterol"]
  },
  risk: {
    risk_score: 14.8,
    risk_level: "medium",
    top_3_factors: ["Cholesterol", "Blood Pressure", "BMI"]
  },
  explanation: "Patient exhibits moderately elevated cholesterol and pre-hypertensive baseline across recent visits. No documented family history of early CVD. Lifestyle intervention and 6-month lipid recheck indicated.",
  patient_meta: {
    id: "PT-1204",
    name: "Jameson Wright",
    mrn: "MRN-99312",
    analyzedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
};

const MOCK_LOW_RISK_RESPONSE: AnalysisResponse = {
  reports: [
    {
      date: "Aug 09, 2023",
      doctor: "Dr. Kowalski",
      clinic: "University Health Partners",
      snippet: "Annual physical exam. Resting BP 118/76 mmHg. Heart rate regular at 64 bpm. Lab panel all within normal physiological ranges."
    },
    {
      date: "Sep 12, 2022",
      doctor: "Dr. Kowalski",
      clinic: "University Health Partners",
      snippet: "Routine screening. Total cholesterol 175 mg/dL, HDL 58 mg/dL. Glucose 88 mg/dL. Negative for cardiovascular symptoms."
    }
  ],
  final_profile: {
    age: 45,
    bp: "118/76",
    cholesterol: "175",
    glucose: "88",
    bmi: 22.5,
    smoking: "no",
    history: "no",
    consistent_high_factors: []
  },
  risk: {
    risk_score: 4.2,
    risk_level: "low",
    top_3_factors: ["Age", "Lipid Balance", "Physical Activity"]
  },
  explanation: "Parameters reflect optimal cardiovascular metrics across all historical document extractions. Blood pressure and fasting metabolic markers remain stable within normal target zones.",
  patient_meta: {
    id: "PT-22105",
    name: "Maria Sanchez",
    mrn: "MRN-22105",
    analyzedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
};

/**
 * Upload a PDF document to the clinical backend.
 * Returns a patient_id string for subsequent risk analysis.
 */
export async function uploadPdf(file: File): Promise<{ patient_id: string }> {
  if (USE_MOCK) {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 800));
    
    // Choose mock patient id based on filename if possible, or default
    const name = file.name.toLowerCase();
    if (name.includes("1204") || name.includes("medium") || name.includes("wright")) {
      return { patient_id: "PT-1204" };
    }
    if (name.includes("22105") || name.includes("low") || name.includes("sanchez")) {
      return { patient_id: "PT-22105" };
    }
    return { patient_id: "PT-8821" };
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errorText = await res.text().catch(() => "Unknown upload error");
      throw new Error(`Upload failed (${res.status}): ${errorText}`);
    }

    return await res.json();
  } catch (err: any) {
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      throw new Error(`Backend server unreachable at ${API_BASE_URL}. Please confirm FastAPI is running ('py -m uvicorn backend.main:app --port 8000') and retry.`);
    }
    console.warn("Backend API upload error:", err);
    throw err;
  }
}

/**
 * Trigger analysis of consolidated clinical reports for the given patient_id.
 * Returns the full structured risk summary and report extraction evidence.
 */
export async function analyzePatient(patientId: string): Promise<AnalysisResponse> {
  if (USE_MOCK) {
    // Simulate multi-stage analysis pipeline delay
    await new Promise((resolve) => setTimeout(resolve, MOCK_API_SIMULATION_DELAY_MS));

    if (patientId === "PT-1204") {
      return MOCK_MEDIUM_RISK_RESPONSE;
    }
    if (patientId === "PT-22105") {
      return MOCK_LOW_RISK_RESPONSE;
    }
    return MOCK_HIGH_RISK_RESPONSE;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ patient_id: patientId }),
    });

    if (!res.ok) {
      const errorText = await res.text().catch(() => "Unknown analysis error");
      throw new Error(`Analysis failed (${res.status}): ${errorText}`);
    }

    return await res.json();
  } catch (err: any) {
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      throw new Error(`Backend server unreachable at ${API_BASE_URL}. Please confirm FastAPI is running ('py -m uvicorn backend.main:app --port 8000') and retry.`);
    }
    console.error("Backend analyze error:", err);
    throw err;
  }
}
