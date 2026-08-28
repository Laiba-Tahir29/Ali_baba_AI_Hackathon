from typing import List, Optional
from pydantic import BaseModel, Field


class ReportItem(BaseModel):
    date: str = Field(..., description="Date of the clinical encounter")
    doctor: str = Field(..., description="Attending physician name")
    clinic: str = Field(..., description="Clinic or hospital location")
    snippet: str = Field(..., description="Direct quote/excerpt from the encounter note")


class PerReportProfile(BaseModel):
    """
    Extracted parameters per individual encounter report.
    Produced by Person B's extract_profile().
    """
    date: str
    doctor: str
    clinic: str
    snippet: str
    age: int
    bp: str
    cholesterol: str
    glucose: str
    bmi: float
    smoking: str
    history: str


class FinalProfile(BaseModel):
    """
    Consolidated vital & demographic profile using latest values.
    Produced by Person B's consolidate_profiles().
    """
    age: int
    bp: str
    cholesterol: str
    glucose: str
    bmi: float
    smoking: str
    history: str
    consistent_high_factors: List[str] = Field(
        default_factory=list,
        description="Fields that remained persistently elevated across multiple historical encounters"
    )


class RiskAnalysis(BaseModel):
    """
    ML risk prediction model output.
    Produced by Person A's predict_risk().
    """
    risk_score: float = Field(..., description="Calculated percentage risk score (e.g. 24.5)")
    risk_level: str = Field(..., description="Risk category: 'low', 'medium', or 'high'")
    top_3_factors: List[str] = Field(..., description="Top 3 contributing risk driver names")


class PatientMeta(BaseModel):
    id: str
    name: str
    mrn: str
    analyzedAt: Optional[str] = None



class UploadResponse(BaseModel):
    patient_id: str = Field(..., description="Assigned patient/session identifier for analysis")


class AnalyzeRequest(BaseModel):
    patient_id: str = Field(..., description="Patient ID to retrieve and analyze")


class AnalysisResponse(BaseModel):
    """
    Final consolidated contract payload returned to the frontend.
    """
    reports: List[ReportItem]
    final_profile: FinalProfile
    risk: RiskAnalysis
    explanation: str
    patient_meta: Optional[PatientMeta] = None
