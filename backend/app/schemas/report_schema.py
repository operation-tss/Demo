from typing import List, Optional, Any, Dict
from datetime import date, datetime
from pydantic import BaseModel, Field

class PatientInformation(BaseModel):
    name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    patient_id: Optional[str] = None
    lab_name: Optional[str] = None

class PatientMatchResult(BaseModel):
    """
    Patient identity matching metadata.
    Enforces strict clinical safety: Never matches by name alone.
    """
    matched: bool = False
    patient_id: Optional[int] = None
    health_id: Optional[str] = None
    patient_name: Optional[str] = None
    match_type: str = "UNMATCHED"  # "EXPLICIT", "HEALTH_ID", "PHONE", "AADHAAR", "COMPOSITE", "CREATED", "UNMATCHED"
    confidence: str = "LOW"        # "HIGH", "MEDIUM", "LOW"
    notes: str = ""

class TestResult(BaseModel):
    test_name: str
    value: str
    unit: Optional[str] = ""
    reference_range: Optional[str] = ""
    status: str = Field(description="LOW, HIGH, NORMAL, or NEEDS REVIEW")
    flag: Optional[str] = None
    category: Optional[str] = None

class Summary(BaseModel):
    total_parameters: int = 0
    low: int = 0
    high: int = 0
    normal: int = 0
    needs_review: int = 0

class TimelineSyncSummary(BaseModel):
    status: str = "SKIPPED"  # "SUCCESS", "PARTIAL", "FAILED", "SKIPPED"
    synced_count: int = 0
    attempted_count: int = 0
    synced_parameters: List[str] = Field(default_factory=list)
    newly_created_parameters: List[str] = Field(default_factory=list)
    skipped_duplicates: List[str] = Field(default_factory=list)
    skipped_for_review: List[Dict[str, Any]] = Field(default_factory=list)
    requires_date_verification: bool = False
    error: Optional[str] = None
    requires_retry: bool = False

class ReportAnalysisResponse(BaseModel):
    processing_status: str = "completed"  # "completed", "partial", "failed"
    report_type: str = "Unknown / Unclassified"
    report_title: Optional[str] = None
    patient_information: PatientInformation = Field(default_factory=PatientInformation)
    patient_match: Optional[PatientMatchResult] = Field(default_factory=PatientMatchResult)
    report_date: Optional[str] = None
    requires_date_verification: bool = False
    laboratory_name: Optional[str] = None
    summary: Summary = Field(default_factory=Summary)
    results: List[TestResult] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    extracted_text: str = ""
    ocr_confidence: Optional[float] = None
    ocr_engine: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    timeline_sync: Optional[TimelineSyncSummary] = None

# --- Three-Table JOIN Timeline History Schemas (Task 7) ---

class PatientDemographics(BaseModel):
    patient_id: int
    health_id: Optional[str] = None
    patient_name: str
    gender: Optional[str] = None
    dob: Optional[date] = None
    phone: Optional[str] = None

class TimelineItem(BaseModel):
    timeline_id: int
    parameter_id: int
    parameter_name: str
    test_result: str
    report_date: Optional[date] = None
    saved_on: Optional[datetime] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    status: Optional[str] = None

class PatientTimelineHistoryResponse(BaseModel):
    patient: PatientDemographics
    timeline: List[TimelineItem] = Field(default_factory=list)
    total_records: int = 0

class ParameterMasterItem(BaseModel):
    id: int
    Name: str
    Desc: Optional[str] = None
    is_active: bool = True

class DashboardMetricsResponse(BaseModel):
    total_patients: int = 0
    total_reports: int = 0
    abnormal_reports: int = 0
    processed_reports: int = 0
    patients_trend: str = "+12% this month"
    reports_trend: str = "+8%"
    abnormal_percent: str = "11.0% of total"
    processed_percent: str = "89.0%"
