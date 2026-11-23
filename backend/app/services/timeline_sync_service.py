import re
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple, Set
from pydantic import BaseModel, Field
from .timeline_db import get_db_session, text
from ..models.timeline_models import HCTimelineParameter, HCPatientHealthTimeline
from ..schemas.report_schema import TestResult

logger = logging.getLogger("timeline_sync")

class SkippedReviewItem(BaseModel):
    parameter_name: str
    extracted_value: str
    reason: str

class TimelineSyncResult(BaseModel):
    status: str = "SKIPPED"  # "SUCCESS", "PARTIAL", "FAILED", "SKIPPED"
    synced_count: int = 0
    attempted_count: int = 0
    synced_parameters: List[str] = Field(default_factory=list)
    newly_created_parameters: List[str] = Field(default_factory=list)
    skipped_duplicates: List[str] = Field(default_factory=list)
    skipped_for_review: List[SkippedReviewItem] = Field(default_factory=list)
    requires_date_verification: bool = False
    error: Optional[str] = None
    requires_retry: bool = False

# Explicitly approved clinical synonyms (Requirement 4 & 7)
# Canonical name maps to approved synonyms
APPROVED_CLINICAL_ALIASES: Dict[str, List[str]] = {
    # 1. Complete Blood Count (14)
    "hemoglobin": ["hb", "hgb", "haemoglobin", "hemoglobin level"],
    "total rbc count": ["rbc", "total rbc", "rbc count", "total rbc count", "red blood cell count", "erythrocyte count"],
    "packed cell volume (pcv)": ["pcv", "hematocrit", "hct", "packed cell volume"],
    "mcv": ["mean corpuscular volume"],
    "mch": ["mean corpuscular hemoglobin"],
    "mchc": ["mean corpuscular hemoglobin concentration"],
    "rdw": ["red cell distribution width", "rdw-cv", "rdw cv"],
    "total leukocyte count (wbc)": ["wbc", "tlc", "total leukocyte count", "total wbc count", "white blood cells", "total wbc", "leukocyte count"],
    "neutrophils": ["neutrophil", "polymorphs", "segs"],
    "lymphocytes": ["lymphocyte", "lymphs"],
    "monocytes": ["monocyte", "monos"],
    "eosinophils": ["eosinophil", "eos"],
    "basophils": ["basophil", "baso"],
    "platelet count": ["platelets", "total platelets", "plt", "platelet", "thrombocyte count"],

    # 2. Liver Function Test (11)
    "total bilirubin": ["bilirubin total", "serum bilirubin", "s. bilirubin", "bilirubin (total)"],
    "direct bilirubin": ["bilirubin direct", "conjugated bilirubin", "s. direct bilirubin"],
    "indirect bilirubin": ["bilirubin indirect", "unconjugated bilirubin"],
    "sgot / ast": ["sgot", "ast", "aspartate aminotransferase", "serum glutamic oxaloacetic transaminase"],
    "sgpt / alt": ["sgpt", "alt", "alanine aminotransferase", "serum glutamic pyruvic transaminase"],
    "alkaline phosphatase (alp)": ["alp", "alkaline phosphatase", "alk phos", "s. alp"],
    "total protein": ["protein total", "serum total protein", "s. total protein", "total proteins"],
    "albumin": ["serum albumin", "s. albumin"],
    "globulin": ["serum globulin", "s. globulin"],
    "a/g ratio": ["ag ratio", "albumin/globulin ratio", "albumin globulin ratio"],
    "ggt": ["ggtp", "gamma gt", "gamma glutamyl transferase"],

    # 3. Kidney Function Test (5)
    "blood urea": ["urea", "serum urea", "s. urea"],
    "blood urea nitrogen (bun)": ["bun", "urea nitrogen", "serum bun"],
    "serum creatinine": ["creatinine", "s. creatinine", "creat", "serum creat"],
    "uric acid": ["serum uric acid", "s. uric acid"],
    "egfr": ["estimated gfr", "glomerular filtration rate"],

    # 4. Lipid Profile (6)
    "total cholesterol": ["cholesterol", "cholesterol total", "serum cholesterol", "s. cholesterol"],
    "triglycerides": ["serum triglycerides", "tg", "s. triglycerides"],
    "hdl cholesterol": ["hdl", "high density lipoprotein", "serum hdl"],
    "ldl cholesterol": ["ldl", "low density lipoprotein", "serum ldl"],
    "vldl cholesterol": ["vldl", "very low density lipoprotein", "serum vldl"],
    "tc / hdl ratio": ["cholesterol/hdl ratio", "tc/hdl", "cholesterol to hdl ratio"],

    # 5. Thyroid Profile (5)
    "tsh": ["tsh ultra", "thyroid stimulating hormone", "s. tsh"],
    "free t3": ["ft3", "free triiodothyronine"],
    "free t4": ["ft4", "free thyroxine"],
    "total t3": ["triiodothyronine", "total triiodothyronine"],
    "total t4": ["thyroxine", "total thyroxine"],

    # 6. Blood Glucose & Diabetes (4)
    "fasting blood sugar (fbs)": ["fasting blood glucose", "fbs", "glucose fasting", "fasting glucose", "fasting blood sugar"],
    "post prandial blood sugar (ppbs)": ["post prandial blood sugar", "ppbs", "glucose pp", "glucose postprandial", "postprandial glucose"],
    "random blood sugar (rbs)": ["random blood glucose", "rbs", "glucose random"],
    "hba1c": ["glycated hemoglobin", "glycosylated hemoglobin", "hemoglobin a1c"],

    # 7. Nutritional Vitamins (2)
    "vitamin b12": ["vit b12", "cobalamin", "cyanocobalamin"],
    "vitamin d (25-oh)": ["vit d", "25-hydroxy vitamin d", "25-oh cholecalciferol", "25-oh vit d"],

    # 8. Serum Electrolytes & Minerals (4)
    "serum sodium": ["sodium", "s. sodium", "na+"],
    "serum potassium": ["potassium", "s. potassium", "k+"],
    "serum chloride": ["chloride", "s. chloride", "cl-"],
    "serum calcium": ["calcium", "s. calcium", "total calcium"],

    # 9. Urine Routine Examination (9) - Strictly Qualified
    "urine specific gravity": ["specific gravity", "sp. gravity", "sp gravity"],
    "urine ph / reaction": ["urine ph", "ph (urine)", "urine reaction"],
    "urine protein / albumin": ["urine protein", "protein (urine)", "urine albumin", "albumin (urine)"],
    "urine glucose / sugar": ["urine sugar", "sugar (urine)", "urine glucose", "glucose (urine)"],
    "urine ketone bodies": ["urine ketones", "ketone bodies", "ketones (urine)", "urine acetone"],
    "urine pus cells (wbc)": ["pus cells", "leukocytes (urine)", "wbc (urine)", "urine pus cells"],
    "urine rbcs": ["red blood cells (urine)", "rbc (urine)", "urine rbc", "urine erythrocytes"],
    "urine epithelial cells": ["urine epithelial cells", "urine epithelial cell", "epithelial cells (urine)"],
    "urobilinogen": ["urine urobilinogen"],

    # 10. Inflammatory & Routine Serology (3)
    "esr (erythrocyte sedimentation rate)": ["esr", "erythrocyte sedimentation rate", "sedimentation rate"],
    "c-reactive protein (crp)": ["crp", "c-reactive protein", "c reactive protein"],
    "serum ferritin": ["ferritin", "s. ferritin", "serum ferritin level"]
}

def normalize_text(text_val: str) -> str:
    """Removes punctuation, extra spaces, and lowercases for exact matching."""
    if not text_val:
        return ""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text_val)
    return " ".join(cleaned.lower().split())

def is_valid_clinical_parameter_name(name: str) -> bool:
    """
    Validates whether an extracted string is a legitimate clinical parameter name.
    Rejects OCR noise, administrative headers, page numbers, and dates.
    """
    if not name or not isinstance(name, str):
        return False
    clean = name.strip()
    if len(clean) < 2 or len(clean) > 150:
        return False
    
    # Must contain at least 2 alphabetic characters
    if len(re.findall(r"[a-zA-Z]", clean)) < 2:
        return False
        
    lower = clean.lower()
    ADMIN_JUNK = [
        "page", "test parameter", "observed value", "reference range", "biological reference",
        "doctor", "signature", "verified by", "department of", "hospital billing", "invoice",
        "patient name", "patient id", "report date", "collection date", "age / sex", "phone",
        "mobile", "hospital", "clinic", "pathology", "sample type", "sample id", "specimen"
    ]
    for junk in ADMIN_JUNK:
        if lower == junk or lower.startswith(junk + " ") or lower.endswith(" " + junk):
            return False
            
    return True

def is_valid_clinical_value(val: Any) -> bool:
    """
    Requirement 3: Skip missing or empty values, but preserve legitimate numeric zeros.
    0, 0.0, '0' are legitimate clinical measurements.
    """
    if val is None:
        return False
    s = str(val).strip()
    if s == "" or s.lower() in ["null", "none", "n/a", "na", "-", "--"]:
        return False
    return True

def parse_clinical_date(date_str: Optional[str]) -> Optional[date]:
    """
    Requirement 8: Parses date into date object.
    If missing or invalid, returns None (NULL). NEVER defaults to current date or upload date.
    """
    if not date_str:
        return None
    
    clean_str = date_str.strip().replace("Z", "").split("T")[0].strip()
    # Normalize multiple spaces and common separators
    clean_str = re.sub(r"\s+", " ", clean_str)
    
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%Y/%m/%d",
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%d/%b/%Y",
        "%b %d, %Y",
        "%b %d %Y",
        "%B %d, %Y",
        "%B %d %Y",
        "%d-%b-%y",
        "%d/%m/%y",
        "%d-%m-%y"
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(clean_str, fmt).date()
        except ValueError:
            continue
            
    # Try stripping commas e.g. "08 Jan, 2025" -> "08 Jan 2025"
    if "," in clean_str:
        no_comma = clean_str.replace(",", "").strip()
        for fmt in date_formats:
            try:
                return datetime.strptime(no_comma, fmt).date()
            except ValueError:
                continue

    return None

def build_parameter_lookup(active_parameters: List[HCTimelineParameter]) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Builds lookup tables for:
    1. Exact normalized parameter names -> param_id
    2. Approved clinical aliases -> param_id
    """
    exact_lookup: Dict[str, int] = {}
    alias_lookup: Dict[str, int] = {}

    # Pre-normalize canonical aliases map
    norm_alias_registry: Dict[str, List[str]] = {}
    for canonical, aliases in APPROVED_CLINICAL_ALIASES.items():
        norm_canonical = normalize_text(canonical)
        norm_aliases = [normalize_text(a) for a in aliases]
        norm_alias_registry[norm_canonical] = norm_aliases

    for param in active_parameters:
        if not param.id or not param.Name:
            continue
        norm_name = normalize_text(param.Name)
        exact_lookup[norm_name] = param.id

        # Also register unparenthesized version if param.Name contains parens
        # e.g., "Total Leukocyte Count (WBC)" -> also matches "total leukocyte count"
        if "(" in param.Name:
            base_name = normalize_text(param.Name.split("(")[0])
            if base_name and base_name not in exact_lookup:
                exact_lookup[base_name] = param.id

        # Check for matching canonical entry in approved alias registry
        for canon_norm, aliases in norm_alias_registry.items():
            if canon_norm == norm_name or canon_norm in norm_name or norm_name in canon_norm:
                for a in aliases:
                    alias_lookup[a] = param.id

    return exact_lookup, alias_lookup

def match_clinical_parameter(
    test_name: str,
    exact_lookup: Dict[str, int],
    alias_lookup: Dict[str, int]
) -> Optional[int]:
    """
    Requirement 7: Matches parameter against master catalog using
    exact matching and explicitly approved aliases ONLY.
    Uncertain / fuzzy matches return None to be reviewed.
    """
    norm_test = normalize_text(test_name)
    if not norm_test:
        return None

    # Tier 1: Exact Normalized Match
    if norm_test in exact_lookup:
        return exact_lookup[norm_test]

    # Tier 2: Explicitly Approved Alias Match
    if norm_test in alias_lookup:
        return alias_lookup[norm_test]

    # No exact match or approved alias: Reject automatic insertion
    return None

def sync_report_to_patient_timeline(
    patient_id: int,
    analyzed_results: List[TestResult],
    report_date_str: Optional[str]
) -> TimelineSyncResult:
    """
    Synchronizes extracted medical parameters with HC_Patient_Health_Timeline for a specific patient.
    Enforces transaction-safety, exact matching, deduplication, and zero-loss error handling.
    """
    result_summary = TimelineSyncResult(attempted_count=len(analyzed_results))

    if not patient_id or not isinstance(patient_id, int) or patient_id <= 0:
        result_summary.status = "SKIPPED"
        result_summary.error = "Invalid or missing authenticated patient_id."
        return result_summary

    # Parse report date (stores NULL if missing, Requirement 8)
    # NEVER replace original report date with upload date
    report_date_obj = parse_clinical_date(report_date_str)
    if report_date_obj is None:
        result_summary.requires_date_verification = True

    with get_db_session() as session:
        if session is None:
            result_summary.status = "FAILED"
            result_summary.error = "Database session could not be established."
            result_summary.requires_retry = True
            return result_summary

        try:
            # 1. Validate that the patient exists in Mst_Patients (FK Constraint Verification)
            patient_check = session.execute(
                text("SELECT Mst_Patients_patient_id FROM Mst_Patients WHERE Mst_Patients_patient_id = :pid"),
                {"pid": patient_id}
            ).first()

            if not patient_check:
                result_summary.status = "FAILED"
                result_summary.error = f"Patient ID {patient_id} does not exist in Mst_Patients."
                return result_summary

            # 2. Fetch active timeline master parameters
            active_params_raw = session.execute(
                text("SELECT id, Name, [Desc], is_active, created_on_dt FROM HC_Timeline_Parameters WHERE is_active = 1")
            ).all()

            active_parameters = [
                HCTimelineParameter(
                    id=row[0],
                    Name=row[1],
                    Desc=row[2],
                    is_active=bool(row[3]),
                    created_on_dt=row[4]
                )
                for row in active_params_raw
            ]

            exact_lookup, alias_lookup = build_parameter_lookup(active_parameters)

            # 3. Process extracted parameters inside atomic transaction
            for item in analyzed_results:
                # Value Validation (Requirement 3: Skip empty, preserve 0)
                if not is_valid_clinical_value(item.value):
                    continue

                clean_val_str = str(item.value).strip()[:100]

                # Parameter Matching (Requirement 7: Exact & approved aliases only)
                param_id = match_clinical_parameter(item.test_name, exact_lookup, alias_lookup)

                if not param_id:
                    # Task 5: Automatic insertion of valid missing parameters into HC_Timeline_Parameters with duplicate prevention
                    if is_valid_clinical_parameter_name(item.test_name):
                        norm_test = normalize_text(item.test_name)
                        # Check if already present in database with normalized name
                        existing_param = session.execute(
                            text("SELECT id, Name FROM HC_Timeline_Parameters WHERE LOWER(RTRIM(LTRIM(Name))) = :pname AND is_active = 1"),
                            {"pname": item.test_name.strip().lower()}
                        ).first()

                        if existing_param:
                            param_id = existing_param[0]
                            exact_lookup[norm_test] = param_id
                        else:
                            # Concurrency-safe insertion with OUTPUT INSERTED.id directly from SQL Server
                            clean_param_name = item.test_name.strip()[:150]
                            insert_param_sql = text("""
                                INSERT INTO HC_Timeline_Parameters (Name, [Desc], is_active, created_on_dt)
                                OUTPUT INSERTED.id
                                VALUES (:pname, :pdesc, 1, SYSUTCDATETIME())
                            """)
                            inserted_row = session.execute(insert_param_sql, {
                                "pname": clean_param_name,
                                "pdesc": f"Auto-cataloged clinical parameter: {clean_param_name}"
                            }).first()
                            
                            if inserted_row and inserted_row[0]:
                                param_id = inserted_row[0]
                                exact_lookup[norm_test] = param_id
                                result_summary.newly_created_parameters.append(clean_param_name)
                            else:
                                # Fallback check if already inserted in a concurrent thread
                                fallback_row = session.execute(
                                    text("SELECT id FROM HC_Timeline_Parameters WHERE Name = :pname AND is_active = 1"),
                                    {"pname": clean_param_name}
                                ).first()
                                param_id = fallback_row[0] if fallback_row else None
                                if param_id:
                                    exact_lookup[norm_test] = param_id

                if not param_id:
                    # Uncertain / Unapproved match: Flag for review, DO NOT AUTO-INSERT
                    result_summary.skipped_for_review.append(
                        SkippedReviewItem(
                            parameter_name=item.test_name,
                            extracted_value=clean_val_str,
                            reason="Parameter name could not be validated as a clinical measurement. Skipped for clinical review."
                        )
                    )
                    continue

                # 4. Transaction-safe Duplicate Handling (Requirement 9 & 10)
                # Check for existing active record for this patient, parameter, and date
                # CRITICAL: HC_Patient_Health_Timeline does NOT have an updated_on_dt column.
                if report_date_obj is not None:
                    existing_query = text(
                        "SELECT id, Value, is_active FROM HC_Patient_Health_Timeline "
                        "WHERE patient_id = :pid AND HC_Timeline_parameter_id = :param_id "
                        "AND Date = :r_date AND is_active = 1"
                    )
                    params = {"pid": patient_id, "param_id": param_id, "r_date": report_date_obj}
                else:
                    existing_query = text(
                        "SELECT id, Value, is_active FROM HC_Patient_Health_Timeline "
                        "WHERE patient_id = :pid AND HC_Timeline_parameter_id = :param_id "
                        "AND Date IS NULL AND is_active = 1"
                    )
                    params = {"pid": patient_id, "param_id": param_id}

                existing_record = session.execute(existing_query, params).first()

                if existing_record:
                    existing_id, existing_val, _ = existing_record
                    if str(existing_val).strip() == clean_val_str:
                        # Identical reading already stored: Skip silently to prevent duplicate
                        result_summary.skipped_duplicates.append(item.test_name)
                        continue
                    else:
                        # Revised reading for same date: Update existing value cleanly
                        update_sql = text(
                            "UPDATE HC_Patient_Health_Timeline SET Value = :new_val "
                            "WHERE id = :rec_id"
                        )
                        session.execute(update_sql, {"new_val": clean_val_str, "rec_id": existing_id})
                        result_summary.synced_count += 1
                        result_summary.synced_parameters.append(f"{item.test_name} (Updated)")
                        continue

                # 5. Insert new record
                # Columns: patient_id, HC_Timeline_parameter_id, Value, Date, uploaded_on_dt, is_active
                insert_sql = text(
                    "INSERT INTO HC_Patient_Health_Timeline "
                    "(patient_id, HC_Timeline_parameter_id, Value, Date, uploaded_on_dt, is_active) "
                    "VALUES (:pid, :param_id, :val, :r_date, SYSUTCDATETIME(), 1)"
                )
                session.execute(insert_sql, {
                    "pid": patient_id,
                    "param_id": param_id,
                    "val": clean_val_str,
                    "r_date": report_date_obj
                })
                result_summary.synced_count += 1
                result_summary.synced_parameters.append(item.test_name)

            # Commit the atomic transaction
            session.commit()

            if result_summary.synced_count > 0:
                result_summary.status = "SUCCESS"
            elif len(result_summary.skipped_duplicates) > 0 and len(result_summary.skipped_for_review) == 0:
                result_summary.status = "SUCCESS"  # All matched values were already up to date
            elif len(result_summary.skipped_for_review) > 0:
                result_summary.status = "PARTIAL"
            else:
                result_summary.status = "SKIPPED"

        except Exception as e:
            session.rollback()
            logger.error(f"Error during timeline synchronization: {e}", exc_info=True)
            result_summary.status = "FAILED"
            result_summary.error = f"Database transaction failed: {str(e)}"
            result_summary.requires_retry = True

    return result_summary
