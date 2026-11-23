import os
import shutil
import tempfile
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from ..schemas.report_schema import ReportAnalysisResponse, PatientInformation, Summary, PatientMatchResult
from ..services.pdf_extractor import extract_text_from_pdf, PDFExtractionError
from ..services.ocr_service import extract_text_from_image
from ..services.report_classifier import classify_report
from ..services.data_extractor import extract_patient_information, extract_all_parameters
from ..services.report_analyzer import analyze_test_result, generate_findings_and_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

@router.post("/analyze", response_model=ReportAnalysisResponse)
async def analyze_medical_report(
    file: UploadFile = File(...),
    patient_id: Optional[int] = Form(None)
):
    filename = file.filename or "unknown_file"
    file_ext = os.path.splitext(filename)[1].lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: PDF, PNG, JPG, JPEG."
        )

    # Read uploaded bytes with size validation
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")

    if len(content) == 0:
        return ReportAnalysisResponse(
            processing_status="failed",
            report_type="Unknown / Unclassified",
            extracted_text="",
            warnings=["Uploaded file is completely empty (0 bytes)."]
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE // (1024 * 1024)} MB."
        )

    extracted_text = ""
    ocr_confidence = None
    ocr_engine = None
    warnings = []

    # Temporary in-memory processing to avoid permanent database storage
    try:
        if file_ext == ".pdf":
            try:
                extracted_text, is_scanned, ocr_conf, engine, pdf_warnings = extract_text_from_pdf(content)
                ocr_confidence = ocr_conf
                ocr_engine = engine
                warnings.extend(pdf_warnings)
                if is_scanned:
                    warnings.append(f"Document was identified as a scanned PDF and processed with {ocr_engine}.")
            except PDFExtractionError as pe:
                return ReportAnalysisResponse(
                    processing_status="failed",
                    report_type="Unknown / Unclassified",
                    extracted_text="",
                    warnings=[str(pe)]
                )
        else:
            # JPG, JPEG, PNG image or screenshot processing
            extracted_text, ocr_conf, engine, ocr_warnings = extract_text_from_image(content)
            ocr_confidence = ocr_conf
            ocr_engine = engine
            warnings.extend(ocr_warnings)

    except Exception as e:
        logger.error(f"Error during document processing: {e}")
        return ReportAnalysisResponse(
            processing_status="failed",
            report_type="Unknown / Unclassified",
            extracted_text="",
            warnings=[f"Unexpected processing error: {str(e)}"]
        )

    # Requirement 9: If text extraction fails, show a clear error instead of displaying fake results
    if not extracted_text or len(extracted_text.strip()) < 10:
        error_msg = (
            "Text extraction failed. No readable text could be recognized in the uploaded document. "
            "Please ensure the image or screenshot is clear, properly oriented, and has sufficient resolution."
        )
        if error_msg not in warnings:
            warnings.append(error_msg)
            
        return ReportAnalysisResponse(
            processing_status="failed",
            report_type="Unknown / Unclassified",
            report_title="Text Extraction Failed",
            extracted_text="",
            ocr_confidence=ocr_confidence,
            ocr_engine=ocr_engine,
            warnings=warnings
        )

    # Step 3: Classify Report Type
    report_type, report_title, confidence = classify_report(extracted_text)

    # Step 4: Extract Patient Demographics
    patient_info, report_date, lab_name = extract_patient_information(extracted_text)

    # Step 5: Extract Medical Test Parameters
    raw_parameters = extract_all_parameters(extracted_text, report_type, patient_info)

    # Step 6: Rule-Based Analysis (LOW / HIGH / NORMAL / NEEDS REVIEW)
    analyzed_results = [analyze_test_result(param) for param in raw_parameters]

    # Step 7: Findings & Summary aggregation
    findings, summary = generate_findings_and_summary(analyzed_results)

    status = "completed"
    if report_type == "Unknown / Unclassified":
        warnings.append("Report type could not be matched with high confidence to a known profile. Displaying all identifiable data.")

    # Step 8: Safe Patient Identification & Timeline Synchronization
    patient_match = PatientMatchResult()
    try:
        from ..services.timeline_db import get_db_session
        from ..services.patient_matching_service import identify_or_register_patient
        with get_db_session() as db_session:
            if db_session is not None:
                patient_match = identify_or_register_patient(
                    session=db_session,
                    patient_info=patient_info,
                    raw_text=extracted_text,
                    explicit_patient_id=patient_id
                )
    except Exception as p_err:
        logger.warning(f"Patient identification check notice: {p_err}")

    timeline_sync = None
    target_patient_id = patient_match.patient_id if (patient_match.matched and patient_match.patient_id) else patient_id
    if target_patient_id is not None:
        try:
            from ..services.timeline_sync_service import sync_report_to_patient_timeline
            sync_res = sync_report_to_patient_timeline(
                patient_id=target_patient_id,
                analyzed_results=analyzed_results,
                report_date_str=report_date
            )
            timeline_sync = sync_res.model_dump()
            if sync_res.status == "FAILED":
                warnings.append(f"Timeline synchronization notice: {sync_res.error}")
        except Exception as sync_exc:
            logger.error(f"Timeline sync unexpected failure: {sync_exc}", exc_info=True)
            timeline_sync = {
                "status": "FAILED",
                "synced_count": 0,
                "attempted_count": len(analyzed_results),
                "synced_parameters": [],
                "newly_created_parameters": [],
                "skipped_duplicates": [],
                "skipped_for_review": [],
                "error": f"Database synchronization error: {str(sync_exc)}",
                "requires_retry": True
            }
            warnings.append("Report analyzed successfully, but saving to patient timeline encountered an error. Extracted results preserved.")
    elif patient_match.notes:
        timeline_sync = {
            "status": "SKIPPED",
            "synced_count": 0,
            "attempted_count": len(analyzed_results),
            "synced_parameters": [],
            "newly_created_parameters": [],
            "skipped_duplicates": [],
            "skipped_for_review": [],
            "error": patient_match.notes,
            "requires_retry": False
        }

    return ReportAnalysisResponse(
        processing_status=status,
        report_type=report_type,
        report_title=report_title,
        patient_information=patient_info,
        patient_match=patient_match,
        report_date=report_date,
        laboratory_name=lab_name or patient_info.lab_name,
        summary=summary,
        results=analyzed_results,
        findings=findings,
        extracted_text=extracted_text,
        ocr_confidence=ocr_confidence,
        ocr_engine=ocr_engine,
        warnings=warnings,
        timeline_sync=timeline_sync
    )

@router.get("/samples")
async def list_sample_reports():
    """List available sample reports for quick interactive testing."""
    samples_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "samples")
    samples_dir = os.path.abspath(samples_dir)
    if not os.path.exists(samples_dir):
        return {"samples": []}
        
    sample_files = []
    for f in os.listdir(samples_dir):
        if f.startswith("sample_"):
            sample_files.append(f)
            
    return {"samples": sorted(sample_files)}

@router.get("/samples/{filename}")
async def get_sample_report_file(filename: str):
    """Retrieve a sample file for testing."""
    samples_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "samples")
    samples_dir = os.path.abspath(samples_dir)
    
    # Path traversal protection
    if not filepath_is_safe(samples_dir, filename):
        raise HTTPException(status_code=404, detail="Sample report not found")

    filepath = os.path.abspath(os.path.join(samples_dir, filename))
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Sample report not found")
        
    if filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith((".jpg", ".jpeg")):
        media_type = "image/jpeg"
    else:
        media_type = "application/octet-stream"
        
    return FileResponse(filepath, media_type=media_type, filename=filename)

def filepath_is_safe(base_dir: str, filename: str) -> bool:
    """Helper to ensure filename does not escape base_dir."""
    target = os.path.abspath(os.path.join(base_dir, filename))
    return target.startswith(os.path.abspath(base_dir))
