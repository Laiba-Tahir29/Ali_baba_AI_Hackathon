export interface ReportItem {
  date: string;
  doctor: string;
  clinic: string;
  snippet: string;
}

export interface FinalProfile {
  age: number;
  bp: string;
  cholesterol: string;
  glucose: string;
  bmi: number;
  smoking: string;
  history: string;
  consistent_high_factors: string[];
}

export interface RiskAnalysis {
  risk_score: number;
  risk_level: "low" | "medium" | "high";
  top_3_factors: string[];
}

export interface AnalysisResponse {
  reports: ReportItem[];
  final_profile: FinalProfile;
  risk: RiskAnalysis;
  explanation: string;
  patient_meta?: {
    id: string;
    name: string;
    mrn: string;
    analyzedAt?: string;
  };
}

export type ViewState = "upload" | "loading" | "results" | "error";

export interface ErrorDetails {
  title: string;
  message: string;
  code?: string;
  canRetry?: boolean;
}
