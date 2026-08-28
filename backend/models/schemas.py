from typing import List, Optional
from pydantic import BaseModel, Field


class ReportItem(BaseModel):
    date: str = Field(
        ...,
        description="Date of the clinical encounter"
    )
    doctor: str = Field(
        ...,
        description="Attending physician name"
    )
    clinic: str = Field(
        ...,
        description="Clinic or hospital location"
    )
    snippet: str = Field(
        ...,
        description="Direct excerpt from the encounter note"
    )


class PerReportProfile(BaseModel):
    """
    Extracted parameters per individual encounter report.

    Produced by Person B's extract_profile().

    Missing clinical values MUST remain None.
    No clinical defaults are invented.
    """

    date: str
    doctor: str
    clinic: str
    snippet: str

    age: Optional[int] = None
    gender: Optional[int] = None

    height: Optional[float] = None
    weight: Optional[float] = None

    ap_hi: Optional[int] = None
    ap_lo: Optional[int] = None
    bp: Optional[str] = None

    cholesterol: Optional[str] = None

    gluc: Optional[int] = None
    glucose: Optional[str] = None

    bmi: Optional[float] = None

    smoke: Optional[int] = None
    smoking: Optional[str] = None

    alco: Optional[int] = None
    active: Optional[int] = None

    history: Optional[str] = None


class FinalProfile(BaseModel):
    """
    Consolidated clinical profile using the latest valid values.

    Produced by Person B's consolidate_profiles().

    Missing clinical values remain None instead of being
    replaced with fabricated defaults.
    """

    age: Optional[int] = None
    gender: Optional[int] = None

    height: Optional[float] = None
    weight: Optional[float] = None

    ap_hi: Optional[int] = None
    ap_lo: Optional[int] = None
    bp: Optional[str] = None

    cholesterol: Optional[str] = None

    gluc: Optional[int] = None
    glucose: Optional[str] = None

    bmi: Optional[float] = None

    smoke: Optional[int] = None
    smoking: Optional[str] = None

    alco: Optional[int] = None
    active: Optional[int] = None

    history: Optional[str] = None

    consistent_high_factors: List[str] = Field(
        default_factory=list,
        description=(
            "Fields that remained persistently elevated "
            "across multiple historical encounters"
        )
    )

    anomalies_flagged: List[str] = Field(
        default_factory=list,
        description=(
            "Sudden spikes, contradictions, or anomalies "
            "detected across encounters"
        )
    )


class RiskAnalysis(BaseModel):
    """
    ML risk prediction model output.

    Produced by Person A's predict_risk().
    """

    risk_score: float = Field(
        ...,
        description="Calculated percentage risk score, e.g. 24.5"
    )

    risk_level: str = Field(
        ...,
        description="Risk category: low, medium, or high"
    )

    top_3_factors: List[str] = Field(
        ...,
        description="Top contributing risk driver names"
    )


class PatientMeta(BaseModel):
    id: str
    name: str
    mrn: str
    analyzedAt: Optional[str] = None


class UploadResponse(BaseModel):
    patient_id: str = Field(
        ...,
        description="Assigned patient/session identifier for analysis"
    )


class AnalyzeRequest(BaseModel):
    patient_id: str = Field(
        ...,
        description="Patient ID to retrieve and analyze"
    )


class AnalysisResponse(BaseModel):
    """
    Final consolidated contract payload returned to the frontend.
    """

    reports: List[ReportItem]

    final_profile: FinalProfile

    risk: RiskAnalysis

    explanation: str

    patient_meta: Optional[PatientMeta] = None