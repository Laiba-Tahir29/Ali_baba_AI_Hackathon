/**
 * Clinical Configuration & Constants for Cardiovascular Risk Summarizer
 * 
 * FastAPI backend integration placeholder:
 * Set USE_MOCK to false once the backend server is running at API_BASE_URL.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Toggle between mock simulation and actual FastAPI server
export const USE_MOCK = false;

// Timing constants
export const LOADING_STATUS_INTERVAL_MS = 2000;
export const MOCK_API_SIMULATION_DELAY_MS = 3200;

// Rotating loading states during report extraction & assessment
export const LOADING_STEPS = [
  "Extracting reports…",
  "Consolidating profile…",
  "Assessing risk…",
  "Preparing summary…"
];

// Clinical Triage Disclaimers & Labels
export const CLINICAL_DISCLAIMER = "This is a triage aid, not a diagnosis. Clinical judgment required.";
export const CLINICAL_HEADER_SUBTITLE = "Doctor-facing cardiovascular triage & multi-report synthesis";

// Risk categories and visual token configurations
export const RISK_LEVELS = {
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high"
} as const;

export type RiskLevel = typeof RISK_LEVELS[keyof typeof RISK_LEVELS];

export const RISK_CONFIG = {
  low: {
    label: "Low Risk Flag — for review",
    shortLabel: "LOW RISK",
    color: "#00685f",
    bgColor: "bg-[#00685f]/10",
    textColor: "text-[#00685f]",
    borderColor: "border-[#00685f]/20",
    badgeBg: "bg-emerald-50 text-emerald-800 border-emerald-200",
    dotColor: "bg-emerald-500",
    gaugeColor: "#00685f"
  },
  medium: {
    label: "Moderate Risk Flag — for review",
    shortLabel: "MODERATE RISK",
    color: "#b05e3d",
    bgColor: "bg-[#b05e3d]/10",
    textColor: "text-[#b05e3d]",
    borderColor: "border-[#b05e3d]/20",
    badgeBg: "bg-amber-50 text-amber-900 border-amber-200",
    dotColor: "bg-amber-500",
    gaugeColor: "#b05e3d"
  },
  high: {
    label: "High Risk Flag — for review",
    shortLabel: "HIGH RISK",
    color: "#ba1a1a",
    bgColor: "bg-[#ba1a1a]/10",
    textColor: "text-[#ba1a1a]",
    borderColor: "border-[#ba1a1a]/20",
    badgeBg: "bg-rose-50 text-rose-900 border-rose-200",
    dotColor: "bg-rose-600",
    gaugeColor: "#ba1a1a"
  }
} as const;

// Sample presets for quick physician demoing
export const SAMPLE_PATIENT_PRESETS = [
  {
    id: "PT-8821",
    name: "Eleanor Caldwell",
    age: 68,
    gender: "Female",
    mrn: "MRN-78429",
    filename: "Patient_8821_Historical_Cardio_Reports.pdf",
    description: "Multi-year cardiology notes with persistent hypertension and elevated LDL",
    expectedRisk: "high"
  },
  {
    id: "PT-1204",
    name: "Jameson Wright",
    age: 52,
    gender: "Male",
    mrn: "MRN-99312",
    filename: "Jameson_Wright_FollowUp_Labs_2023.pdf",
    description: "Moderate risk profile, former smoker with borderline glucose",
    expectedRisk: "medium"
  },
  {
    id: "PT-22105",
    name: "Maria Sanchez",
    age: 45,
    gender: "Female",
    mrn: "MRN-22105",
    filename: "Sanchez_M_Routine_Cardiology_Summary.pdf",
    description: "Controlled lipid profile, normal BP, low overall cardiovascular risk",
    expectedRisk: "low"
  }
];
