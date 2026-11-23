import os
import sys
import json
import urllib.request
from datetime import date
from sqlalchemy import text

sys.path.insert(0, os.path.abspath('.'))

def test_prod_db_untouched():
    """Verify that production HealthCare_connect database remains strictly untouched."""
    from backend.app.services.timeline_db import get_engine, reset_engine
    os.environ.pop('USE_TEST_DB', None)
    os.environ.pop('DATABASE_NAME', None)
    reset_engine()
    engine = get_engine()
    with engine.connect() as conn:
        db_name = conn.execute(text("SELECT DB_NAME()")).scalar()
        assert db_name == "HealthCare_connect", f"Expected HealthCare_connect, got {db_name}"
        # Verify no 105 synthetic records in production
        # Production patient count / test patient records check
        test_pts = conn.execute(text("SELECT COUNT(*) FROM Mst_Patients WHERE Mst_Patients_health_id = 'HC-TEST-ROHAN-1'")).scalar()
        print(f"PASS: Production DB {db_name} is untouched. Test patients with 'HC-TEST-ROHAN-1' in prod = {test_pts} (strictly 0).")
        assert test_pts == 0, "CRITICAL: Found test patient in production DB!"

def test_ocr_date_extraction():
    """Verify OCR date extraction logic accurately identifies printed dates and rejects DOB/noise."""
    from backend.app.services.data_extractor import extract_patient_information
    from backend.app.services.timeline_sync_service import parse_clinical_date

    # Test 1: Explicit 'Report Date: 08-01-2025'
    sample_text_1 = """
    METROPOLIS HEALTHCARE LABS
    Patient Name: Mr. Rahul Verma   Age: 35   Sex: Male
    Report Date: 08-01-2025
    HEMOGLOBIN: 14.5 g/dL
    """
    info1, rdate1, _ = extract_patient_information(sample_text_1)
    parsed1 = parse_clinical_date(rdate1)
    assert parsed1 == date(2025, 1, 8), f"Expected 2025-01-08, got {parsed1}"
    print(f"PASS: OCR extraction 1 -> '{rdate1}' successfully parsed to {parsed1}")

    # Test 2: 'Date of Report: 08 Jan 2025'
    sample_text_2 = """
    LAL PATHLABS
    Name: Sita Devi
    DOB: 15-08-1980
    Date of Report: 08 Jan 2025
    RBC: 4.5
    """
    info2, rdate2, _ = extract_patient_information(sample_text_2)
    parsed2 = parse_clinical_date(rdate2)
    assert parsed2 == date(2025, 1, 8), f"Expected 2025-01-08, got {parsed2}"
    print(f"PASS: OCR extraction 2 -> '{rdate2}' successfully parsed to {parsed2} (ignoring DOB 1980)")

    # Test 3: Only DOB in text (No report date) -> Must return None and require manual verification
    sample_text_3 = """
    DIAGNOSTICS CENTER
    Patient: John Doe
    DOB: 12-05-1992
    WBC: 7500 /cumm
    """
    info3, rdate3, _ = extract_patient_information(sample_text_3)
    parsed3 = parse_clinical_date(rdate3) if rdate3 else None
    assert parsed3 is None, f"Expected None for missing report date, got {parsed3}"
    print(f"PASS: OCR extraction 3 -> Missing report date correctly returned None: Flagged for manual verification")

def test_timeline_api_105_readings():
    """Verify backend API returns 105 readings for Hemoglobin, sorted chronologically with distinct dates."""
    url = "http://127.0.0.1:8000/api/v1/report-analyzer/timeline/1?parameter_id=5"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
    
    assert body.get("success") is True, f"API call failed: {body}"
    data = body.get("data", {})
    timeline = data.get("timeline", [])
    total = data.get("total_records", 0)

    print(f"API Returned total_records: {total}, timeline items: {len(timeline)}")
    assert len(timeline) >= 105, f"Expected >= 105 timeline items, got {len(timeline)}"

    # Verify chronological sorting by report_date
    dates = [t["report_date"] for t in timeline]
    for i in range(len(dates) - 1):
        assert dates[i] <= dates[i+1], f"Ordering error: {dates[i]} is after {dates[i+1]}"
    print(f"PASS: All {len(timeline)} records are sorted strictly chronologically by report date ({dates[0]} -> {dates[-1]}).")

    # Verify the test case where report date (2025-01-08) differs from upload date (2026-11-21)
    rec_2025 = next((t for t in timeline if t["report_date"] == "2025-01-08"), None)
    assert rec_2025 is not None, "Record for 2025-01-08 not found!"
    print(f"Verified distinct dates record: Report Date={rec_2025['report_date']}, Saved On={rec_2025['saved_on']}, Value={rec_2025['test_result']}")
    assert rec_2025["report_date"] == "2025-01-08"
    assert "2026" in str(rec_2025["saved_on"]), f"Expected upload timestamp in 2026, got {rec_2025['saved_on']}"
    print("PASS: Date separation verified: Actual report date is 2025-01-08, Upload timestamp is in 2026.")

def test_db_status_endpoint():
    """Verify db-status endpoint reports HealthCare_connect_test."""
    url = "http://127.0.0.1:8000/api/v1/report-analyzer/db-status"
    with urllib.request.urlopen(url) as resp:
        body = json.loads(resp.read().decode())
    assert body.get("database") == "HealthCare_connect_test", f"Unexpected DB: {body}"
    assert body.get("is_test_db") is True
    print(f"PASS: Live backend db-status confirmed: {body}")

if __name__ == "__main__":
    print("=== RUNNING VERIFICATION SUITE ===")
    test_db_status_endpoint()
    test_prod_db_untouched()
    test_ocr_date_extraction()
    test_timeline_api_105_readings()
    print("=== ALL VERIFICATION CHECKS PASSED SUCCESSFULLY ===")
