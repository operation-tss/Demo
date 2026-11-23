from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field

class HCTimelineParameter(SQLModel, table=True):
    """
    Mapped directly to existing MSSQL table: HC_Timeline_Parameters
    Strictly read-only schema representation.
    """
    __tablename__ = "HC_Timeline_Parameters"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    Name: str = Field(max_length=150)
    Desc: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_on_dt: datetime = Field(default_factory=datetime.utcnow)
    updated_on_dt: Optional[datetime] = None

class HCPatientHealthTimeline(SQLModel, table=True):
    """
    Mapped directly to existing MSSQL table: HC_Patient_Health_Timeline
    CRITICAL: Does NOT have an updated_on_dt column.
    Contains ONLY: id, patient_id, HC_Timeline_parameter_id, Value, Date, uploaded_on_dt, is_active.
    """
    __tablename__ = "HC_Patient_Health_Timeline"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(index=True)
    HC_Timeline_parameter_id: int = Field(index=True)
    Value: Optional[str] = Field(default=None, max_length=100)
    Date: Optional[date] = None
    uploaded_on_dt: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
