"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class QuestionnaireRequest(BaseModel):
    """AD questionnaire - 12 clinically validated questions"""

    # === DDx Questions (7) ===
    # Q1: Pruritus Baseline
    itch_intensity: int = Field(
        ...,
        ge=0,
        le=10,
        description="On a scale of 0-10, how intense has the itching been over the last 3 days?"
    )

    # Q2: Chronicity & Pattern
    chronic_relapsing: bool = Field(
        ...,
        description="Has this rash been present for more than 6 months, coming and going in flare-ups?"
    )

    # Q3: Atopic Triad
    atopic_triad_history: bool = Field(
        ...,
        description="Do you or any immediate family members have a history of asthma, hay fever, or childhood eczema?"
    )

    # Q4: Anatomical Distribution
    primary_location: str = Field(
        ...,
        description="Where is the rash primarily located? Options: flexural, extensor, face_neck, hands_feet, trunk, widespread, scalp_hairline, webs_waistband"
    )

    # Q5: Scabies Differentiator
    household_itchy_or_nighttime_worse: bool = Field(
        ...,
        description="Is anyone else in your household currently itchy, or does the itch get significantly worse specifically at night?"
    )

    # Q6: Contact vs Endogenous
    new_exposure_trigger: bool = Field(
        ...,
        description="Did the rash appear immediately after using a new soap, jewelry, laundry detergent, or exploring outdoors?"
    )

    # Q7: Psoriasis Differentiator
    thick_silvery_scales: bool = Field(
        ...,
        description="Is the rash clearly defined with a thick, silvery-white scale on top?"
    )

    # === Clinical Data Capture (3) ===
    # Q8: Sleep Disruption
    nights_sleep_disturbed: int = Field(
        ...,
        ge=0,
        le=7,
        description="In the last week, how many nights was your sleep disturbed by the skin condition? (0-7)"
    )

    # Q9: Infection Risk
    oozing_honey_crusts: bool = Field(
        ...,
        description="Is the skin currently oozing, weeping clear fluid, or developing golden/honey-colored crusts?"
    )

    # Q10: Treatment History
    steroid_use_last_2weeks: bool = Field(
        ...,
        description="Have you used hydrocortisone or other steroid creams in the past 2 weeks?"
    )

    # === My 2 Additions ===
    # Q11: Treatment Adherence
    moisturizer_frequency: str = Field(
        ...,
        description="How often do you apply moisturizer? Options: none, once_daily, twice_daily, more"
    )

    # Q12: Stress Trigger
    recent_stress_level: int = Field(
        ...,
        ge=0,
        le=10,
        description="On a scale of 0-10, what has your stress level been recently?"
    )

    @validator('primary_location')
    def validate_primary_location(cls, v):
        allowed = ['flexural', 'extensor', 'face_neck', 'hands_feet', 'trunk', 'widespread', 'scalp_hairline', 'webs_waistband']
        if v not in allowed:
            raise ValueError(f"Must be one of: {allowed}")
        return v

    @validator('moisturizer_frequency')
    def validate_moisturizer_frequency(cls, v):
        allowed = ['none', 'once_daily', 'twice_daily', 'more']
        if v not in allowed:
            raise ValueError(f"Must be one of: {allowed}")
        return v


class UploadRequest(BaseModel):
    """Image upload request"""
    image: str = Field(..., description="Base64 encoded image")
    questionnaire: QuestionnaireRequest


class SessionResponse(BaseModel):
    """Session creation response"""
    session_id: UUID
    status: str = "processing"


class AIResultResponse(BaseModel):
    """AI analysis result"""
    severity_score: float
    affected_area_pct: float
    inflammation_score: float
    dryness_score: float
    lichenification_score: float
    excoriation_detected: bool
    flare_status: str
    body_regions: Dict[str, str]
    cnn_confidence: float


class AnalysisResponse(BaseModel):
    """Complete analysis response"""
    session_id: UUID
    status: str
    cnn_results: AIResultResponse
    saliency_map_url: str


class UserReportResponse(BaseModel):
    """User-friendly report"""
    type: str = "user"
    severity: str
    summary: str
    key_findings: List[str]
    recommendations: List[str]
    when_to_seek_help: str
    positive_note: Optional[str] = None
    visual_summary: Optional[Dict[str, Any]] = None


class HCPReportResponse(BaseModel):
    """Healthcare provider report"""
    type: str = "hcp"
    severity_assessment: Dict[str, Any]
    morphology: Dict[str, str]
    body_distribution: Dict[str, str]
    saliency_analysis: str
    symptom_burden: Dict[str, Any]
    trigger_analysis: Dict[str, Any]
    treatment_recommendations: List[str]
    prognosis: str
    differential_considerations: List[str]
    saliency_map_url: str
    next_assessment_recommended: str


class SessionSummary(BaseModel):
    """Session summary for tracking"""
    date: datetime
    severity_score: float
    inflammation_score: float
    dryness_score: float
    affected_area_pct: float
    itch_intensity: int
    flare_status: str


class AlertResponse(BaseModel):
    """Alert response"""
    type: str
    severity: str
    message: str
    recommendations: Optional[List[str]] = None
    details: Optional[str] = None
    created_at: datetime


class TrackingStatistics(BaseModel):
    """Tracking statistics"""
    total_sessions: int
    average_severity: float
    flare_frequency: str
    most_common_triggers: List[str]
    treatment_adherence_pattern: str


class TrendAnalysis(BaseModel):
    """Trend analysis"""
    direction: str  # 'improving', 'worsening', 'stable'
    change_percentage: float
    trend_period_days: int


class TrackingResponse(BaseModel):
    """Tracking dashboard response"""
    user_id: UUID
    sessions: List[SessionSummary]
    trends: TrendAnalysis
    alerts: List[AlertResponse]
    statistics: TrackingStatistics
