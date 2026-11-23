import re
import uuid
import logging
from datetime import datetime, date
from typing import Optional, Tuple
from sqlmodel import Session
from sqlalchemy import text
from ..schemas.report_schema import PatientInformation, PatientMatchResult

logger = logging.getLogger("patient_matching")

def format_health_id(patient_id: int, branch_code: str = "GEN", registration_date: Optional[datetime] = None) -> str:
    """Standard Healthcare Connect Health ID formatter: HC-{Year}-{Branch}-{PatientID}"""
    dt = registration_date or datetime.now()
    year = dt.year
    return f"HC-{year}-{branch_code}-{patient_id}"

def calculate_age_from_dob(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def extract_phone_and_aadhar_from_text(raw_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extracts 10-digit Indian mobile number and 12-digit Aadhaar number from report text."""
    phone = None
    aadhar = None
    
    # 10-digit phone starting with 6, 7, 8, or 9
    phone_match = re.search(r"\b([6-9]\d{9})\b", raw_text)
    if phone_match:
        phone = phone_match.group(1)

    # 12-digit Aadhaar (continuous or spaced 4-4-4)
    aadhar_match = re.search(r"\b(\d{4}\s*\d{4}\s*\d{4})\b", raw_text)
    if aadhar_match:
        aadhar = re.sub(r"\s+", "", aadhar_match.group(1))

    return phone, aadhar

def identify_or_register_patient(
    session: Session,
    patient_info: PatientInformation,
    raw_text: str = "",
    explicit_patient_id: Optional[int] = None
) -> PatientMatchResult:
    """
    Safely identifies a patient in Mst_Patients using multi-tier verification.
    
    STRICT CLINICAL RULES:
    1. NEVER match by name alone.
    2. NEVER assign an ambiguous patient automatically.
    3. Require secondary unambiguous clinical anchor (Health ID, Phone, Aadhaar, or exact Name + Gender + Age).
    4. If uncertain, return matched=False for manual review.
    """
    # Tier 1: Explicit Authenticated Patient ID (e.g. from session or dropdown)
    if explicit_patient_id is not None and isinstance(explicit_patient_id, int) and explicit_patient_id > 0:
        query = text("""
            SELECT Mst_Patients_patient_id, Mst_Patients_health_id, 
                   Mst_Patients_first_name, Mst_Patients_last_name
            FROM Mst_Patients 
            WHERE Mst_Patients_patient_id = :pid AND Mst_Patients_is_active = 1
        """)
        row = session.execute(query, {"pid": explicit_patient_id}).first()
        if row:
            full_name = f"{row[2]} {row[3]}".strip()
            return PatientMatchResult(
                matched=True,
                patient_id=row[0],
                health_id=row[1],
                patient_name=full_name,
                match_type="EXPLICIT",
                confidence="HIGH",
                notes=f"Explicitly verified Patient ID {explicit_patient_id} ({full_name})"
            )
        else:
            return PatientMatchResult(
                matched=False,
                match_type="UNMATCHED",
                confidence="LOW",
                notes=f"Supplied Patient ID {explicit_patient_id} does not exist in Mst_Patients."
            )

    # Tier 2: Unique Health ID in Extracted Information or Text
    candidate_health_id = None
    if patient_info.patient_id and patient_info.patient_id.strip():
        pid_clean = patient_info.patient_id.strip()
        if pid_clean.startswith("HC-"):
            candidate_health_id = pid_clean
        elif pid_clean.isdigit():
            # Check integer ID
            row = session.execute(
                text("SELECT Mst_Patients_patient_id, Mst_Patients_health_id, Mst_Patients_first_name, Mst_Patients_last_name FROM Mst_Patients WHERE Mst_Patients_patient_id = :pid AND Mst_Patients_is_active = 1"),
                {"pid": int(pid_clean)}
            ).first()
            if row:
                full_name = f"{row[2]} {row[3]}".strip()
                return PatientMatchResult(
                    matched=True,
                    patient_id=row[0],
                    health_id=row[1],
                    patient_name=full_name,
                    match_type="HEALTH_ID",
                    confidence="HIGH",
                    notes=f"Matched by Patient ID {pid_clean} ({full_name})"
                )

    if not candidate_health_id and raw_text:
        hid_match = re.search(r"\b(HC-\d{4}-[A-Z0-9]+-\d+)\b", raw_text)
        if hid_match:
            candidate_health_id = hid_match.group(1)

    if candidate_health_id:
        row = session.execute(
            text("SELECT Mst_Patients_patient_id, Mst_Patients_health_id, Mst_Patients_first_name, Mst_Patients_last_name FROM Mst_Patients WHERE Mst_Patients_health_id = :hid AND Mst_Patients_is_active = 1"),
            {"hid": candidate_health_id}
        ).first()
        if row:
            full_name = f"{row[2]} {row[3]}".strip()
            return PatientMatchResult(
                matched=True,
                patient_id=row[0],
                health_id=row[1],
                patient_name=full_name,
                match_type="HEALTH_ID",
                confidence="HIGH",
                notes=f"Matched by Health ID {candidate_health_id} ({full_name})"
            )

    # Tier 3: Primary Phone or Aadhaar Lookup
    phone, aadhar = extract_phone_and_aadhar_from_text(raw_text)
    if phone:
        rows = session.execute(
            text("SELECT Mst_Patients_patient_id, Mst_Patients_health_id, Mst_Patients_first_name, Mst_Patients_last_name FROM Mst_Patients WHERE Mst_Patients_phone_primary = :phone AND Mst_Patients_is_active = 1"),
            {"phone": phone}
        ).fetchall()
        if len(rows) == 1:
            row = rows[0]
            full_name = f"{row[2]} {row[3]}".strip()
            return PatientMatchResult(
                matched=True,
                patient_id=row[0],
                health_id=row[1],
                patient_name=full_name,
                match_type="PHONE",
                confidence="HIGH",
                notes=f"Matched by verified phone number {phone}"
            )
        elif len(rows) > 1:
            logger.warning(f"Multiple patients share phone {phone}. Auto-assignment prohibited.")

    if aadhar:
        rows = session.execute(
            text("SELECT Mst_Patients_patient_id, Mst_Patients_health_id, Mst_Patients_first_name, Mst_Patients_last_name FROM Mst_Patients WHERE Mst_Patients_aadhar_number = :aadhar AND Mst_Patients_is_active = 1"),
            {"aadhar": aadhar}
        ).fetchall()
        if len(rows) == 1:
            row = rows[0]
            full_name = f"{row[2]} {row[3]}".strip()
            return PatientMatchResult(
                matched=True,
                patient_id=row[0],
                health_id=row[1],
                patient_name=full_name,
                match_type="AADHAAR",
                confidence="HIGH",
                notes=f"Matched by verified Aadhaar identifier"
            )

    # Tier 4: Safe Composite Demographic Matching (First Name + Last Name + Gender + Age)
    # STRICT RULE: NEVER MATCH BY NAME ALONE
    if patient_info.name and patient_info.name.strip():
        name_parts = patient_info.name.strip().split()
        if len(name_parts) >= 2:
            first_name = name_parts[0].strip()
            last_name = " ".join(name_parts[1:]).strip()

            # Require gender and age for safe composite disambiguation
            extracted_gender = (patient_info.gender or "").strip().capitalize()
            extracted_age = None
            if patient_info.age:
                age_digits = re.search(r"\b(\d{1,3})\b", patient_info.age)
                if age_digits:
                    extracted_age = int(age_digits.group(1))

            if extracted_gender in ["Male", "Female", "Other"] and extracted_age is not None:
                # Query candidate matches
                candidates = session.execute(
                    text("""
                        SELECT Mst_Patients_patient_id, Mst_Patients_health_id,
                               Mst_Patients_first_name, Mst_Patients_last_name,
                               Mst_Patients_gender, Mst_Patients_date_of_birth
                        FROM Mst_Patients
                        WHERE LOWER(Mst_Patients_first_name) = :fn
                          AND LOWER(Mst_Patients_last_name) = :ln
                          AND Mst_Patients_is_active = 1
                    """),
                    {"fn": first_name.lower(), "ln": last_name.lower()}
                ).fetchall()

                valid_composite_matches = []
                for cand in candidates:
                    cand_gender = (cand[4] or "").strip().capitalize()
                    cand_dob = cand[5]
                    if cand_gender == extracted_gender and cand_dob:
                        calculated_age = calculate_age_from_dob(cand_dob)
                        # Allow +/- 1 year tolerance for birthday boundaries
                        if abs(calculated_age - extracted_age) <= 1:
                            valid_composite_matches.append(cand)

                if len(valid_composite_matches) == 1:
                    matched_patient = valid_composite_matches[0]
                    full_name = f"{matched_patient[2]} {matched_patient[3]}".strip()
                    return PatientMatchResult(
                        matched=True,
                        patient_id=matched_patient[0],
                        health_id=matched_patient[1],
                        patient_name=full_name,
                        match_type="COMPOSITE",
                        confidence="MEDIUM",
                        notes=f"Safely matched by complete composite identity: {full_name}, {extracted_gender}, Age {extracted_age}"
                    )
                elif len(valid_composite_matches) > 1:
                    return PatientMatchResult(
                        matched=False,
                        match_type="UNMATCHED",
                        confidence="LOW",
                        notes=f"Ambiguity detected: {len(valid_composite_matches)} patients share identical name, gender, and age. Automatic assignment prohibited."
                    )
            else:
                return PatientMatchResult(
                    matched=False,
                    match_type="UNMATCHED",
                    confidence="LOW",
                    notes="Clinical safety enforcement: Matching by patient name alone without verified age and gender is strictly prohibited."
                )

    # Tier 5: Fallback when identity cannot be verified with certainty
    return PatientMatchResult(
        matched=False,
        match_type="UNMATCHED",
        confidence="LOW",
        notes="Patient could not be identified with certainty. Timeline sync held for manual patient confirmation."
    )
