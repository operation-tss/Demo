import os
import sys
sys.path.insert(0, os.path.abspath("."))

# Ensure test DB mode is set BEFORE any imports
os.environ["USE_TEST_DB"] = "1"

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.timeline_db import get_engine, reset_engine, test_connection

def run_isolated_verification():
    print("================================================================")
    print("STARTING ISOLATED TEST DATABASE BACKEND & API VERIFICATION")
    print("Target DB: HealthCare_connect_test (USE_TEST_DB=1)")
    print("================================================================")

    reset_engine()
    engine = get_engine()
    print(f"Connected DB Engine URL: {engine.url}")

    # 1. Test Connection
    assert test_connection(), "Database connection test failed for HealthCare_connect_test!"
    print("✓ Test 1 PASSED: Successfully connected to HealthCare_connect_test.")

    client = TestClient(app)

    # 2. Verify Patients API
    resp = client.get("/api/v1/report-analyzer/patients")
    assert resp.status_code == 200, f"Patients API failed: {resp.status_code}"
    body = resp.json()
    patients = body.get("data", [])
    print(f"Fetched {len(patients)} patients from test database.")
    assert len(patients) >= 1, "No patients found in test database!"
    
    test_patient = next((p for p in patients if "TEST" in p.get("patient_name", "")), None)
    assert test_patient is not None, "Synthetic patient 'Rohan Sharma TEST' not returned by API!"
    print(f"  - Verified Patient Details: ID={test_patient['patient_id']}, Name={test_patient['patient_name']}, Health ID={test_patient['health_id']}, Phone={test_patient['phone']}")
    assert test_patient['patient_name'] == 'Rohan Sharma TEST'
    assert test_patient['phone'] == '9999999999'
    print("✓ Test 2 PASSED: Synthetic patient 'Rohan Sharma TEST' correctly returned by API.")

    patient_id = test_patient['patient_id']

    # 3. Verify Timeline API
    resp = client.get(f"/api/v1/report-analyzer/timeline/{patient_id}")
    assert resp.status_code == 200, f"Timeline API failed: {resp.status_code}"
    timeline_data = resp.json().get("data", {})
    records = timeline_data.get("timeline", [])
    available_dates = sorted(list(set(str(r.get("report_date")) for r in records if r.get("report_date"))))

    print(f"\nTimeline API returned {len(records)} parameter readings across {len(available_dates)} dates.")
    assert len(available_dates) == 10, f"Expected 10 dates, got {len(available_dates)}: {available_dates}"
    print(f"  - Dates: {available_dates}")

    # Check each required parameter has exactly 10 chronological readings
    required_params = ["Hemoglobin", "Total RBC Count", "Total Leukocyte Count (WBC)", "MCV", "MCH", "Platelet Count"]

    for param in required_params:
        param_records = [r for r in records if r.get("parameter_name") == param or r.get("test_name") == param]
        print(f"\n--- Parameter: {param} ---")
        print(f"  Total chronological readings: {len(param_records)}")
        assert len(param_records) == 10, f"Parameter {param} expected 10 readings, got {len(param_records)}!"
        
        # Verify chronological ordering and values
        dates = [r["report_date"] for r in param_records]
        values = [r["test_result"] for r in param_records]
        for d, v in zip(dates, values):
            print(f"    Date: {d} -> Value: {v}")
        
        # Verify dates are 10 distinct dates
        assert len(set(dates)) == 10, f"Duplicate dates in {param}!"
        print(f"  ✓ {param} verified with 10 distinct chronological readings.")

    print("\n✓ Test 3 PASSED: All 6 required parameters have exactly 10 date-wise readings.")

    # 4. Verify Metrics API
    resp = client.get("/api/v1/report-analyzer/metrics")
    assert resp.status_code == 200, f"Metrics API failed: {resp.status_code}"
    metrics = resp.json().get("data", {})
    print("\nMetrics API Response in Test Database:")
    print(f"  Total Patients: {metrics.get('total_patients')} (Expected 1)")
    print(f"  Total Reports: {metrics.get('total_reports')} (Expected 10)")
    print(f"  Processed Reports: {metrics.get('processed_reports')} (Expected 10)")
    assert metrics.get('total_patients') == 1, "Metrics total_patients mismatch!"
    assert metrics.get('total_reports') == 10, "Metrics total_reports mismatch!"
    print("✓ Test 4 PASSED: Live database metrics accurately computed from test database.")

    print("\n================================================================")
    print("ALL BACKEND & API TESTS PASSED IN ISOLATED HealthCare_connect_test!")
    print("================================================================")

if __name__ == '__main__':
    run_isolated_verification()
