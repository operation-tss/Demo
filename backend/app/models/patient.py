from datetime import date, datetime
from typing import Optional
from enum import Enum
from pydantic import field_validator
from sqlmodel import Field
from sqlalchemy import Column, DateTime, text
from .base_model import SQLModel

class Genders(str, Enum):
    """Controlled values for Clinical Gender categorization."""
    Male = "Male"
    Female = "Female"
    Other = "Other"

class Patient(SQLModel, table=True):
    """
    Mst_Patients: Enterprise Master Model.
    Optimized for MS SQL Server tracking and clinical audit compliance matching Healthcare Connect.
    """
    __tablename__ = "Mst_Patients"
    __table_args__ = {"extend_existing": True}
    
    Mst_Patients_patient_id: Optional[int] = Field(default=None, primary_key=True)
    Mst_Patients_health_id: Optional[str] = Field(default=None, index=True, unique=True, description="Unique Hospital ID")
    Mst_Patients_aadhar_number: str = Field(index=True, unique=True)
    Mst_Patients_first_name: str = Field(index=True)
    Mst_Patients_last_name: str = Field(index=True)
    Mst_Patients_date_of_birth: date
    Mst_Patients_gender: Genders = Field(description="Clinical gender categorization")
    Mst_Patients_phone_primary: str = Field(index=True)
    Mst_Patients_phone_secondary: Optional[str] = None
    Mst_Patients_email: Optional[str] = None
    Mst_Patients_address_line1: str
    Mst_Patients_address_line2: Optional[str] = None
    Mst_Patients_city: str
    Mst_Patients_state: str
    Mst_Patients_pincode: str
    Mst_Patients_blood_group: Optional[str] = None
    Mst_Patients_abha_number: Optional[str] = None
    Mst_Patients_pmjay_id: Optional[str] = None
    Mst_Patients_cghs_number: Optional[str] = None
    
    # Audit Trail
    Mst_Patients_registration_date: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=text("SYSUTCDATETIME()"))
    )
    Mst_Patients_is_active: bool = Field(default=True)
    Mst_Patients_CreateonDateUTC: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=text("SYSUTCDATETIME()"))
    )
    Mst_Patients_updatedonDateUTC: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=text("SYSUTCDATETIME()"), onupdate=text("SYSUTCDATETIME()"))
    )

    @field_validator("Mst_Patients_date_of_birth")
    @classmethod
    def validate_dob(cls, v: date):
        if v > date.today():
            raise ValueError("Date of Birth cannot be in the future")
        if v.year < 1900:
            raise ValueError("Clinical record valid year must be after 1900")
        return v

    @field_validator("Mst_Patients_phone_primary")
    @classmethod
    def validate_phone(cls, v: str):
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Phone number must be exactly 10 digits")
        return v
