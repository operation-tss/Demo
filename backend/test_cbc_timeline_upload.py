import requests
import json
import sys

URL = "http://127.0.0.1:8000/api/reports/analyze"
SAMPLE_CBC = "samples/sample_cbc.pdf"

print("======================================================================")
print("STEP 4 INTEGRATION TEST: CBC REPORT UPLOAD WITH PATIENT 8")
print("======================================================================")

# 1. First Upload
print("\n--- Phase 1: Uploading sample_cbc.pdf for Patient 8 ---")
with open(SAMPLE_CBC, "rb") as f:
    resp1 = requests.post(URL, files={"file": ("sample_cbc.pdf", f, "application/pdf")}, data={"patient_id": 8})

print("HTTP Status Code:", resp1.status_code)
assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}"

data1 = resp1.json()
print("Processing Status:", data1.get("processing_status"))
print("Detected Report Type:", data1.get("report_type"))
print("Extracted Report Date:", data1.get("report_date"))
print("Extracted Patient Info:", data1.get("patient_information"))
print("Total Parameters Extracted by OCR:", len(data1.get("results", [])))

sync1 = data1.get("timeline_sync")
print("\nTimeline Sync Result:")
print("  Status:", sync1.get("status"))
print("  Attempted Count:", sync1.get("attempted_count"))
print("  Synced Count:", sync1.get("synced_count"))
print("  Synced Parameters:", sync1.get("synced_parameters"))
print("  Skipped Duplicates:", sync1.get("skipped_duplicates"))
print("  Skipped for Review:", sync1.get("skipped_for_review"))
print("  Error:", sync1.get("error"))

assert sync1.get("status") == "SUCCESS", f"Expected SUCCESS, got {sync1.get('status')}"
assert sync1.get("synced_count") == 14, f"Expected 14 synced parameters, got {sync1.get('synced_count')}"
assert len(sync1.get("skipped_for_review")) == 0, f"Expected 0 skipped for review, got {len(sync1.get('skipped_for_review'))}"

print("\n>>> Phase 1 PASSED: 14 CBC parameters matched master catalog and inserted!")

# 2. Duplicate Upload (Idempotency Test)
print("\n--- Phase 2: Duplicate Upload of sample_cbc.pdf for Patient 8 ---")
with open(SAMPLE_CBC, "rb") as f:
    resp2 = requests.post(URL, files={"file": ("sample_cbc.pdf", f, "application/pdf")}, data={"patient_id": 8})

print("HTTP Status Code:", resp2.status_code)
assert resp2.status_code == 200

data2 = resp2.json()
sync2 = data2.get("timeline_sync")
print("\nDuplicate Timeline Sync Result:")
print("  Status:", sync2.get("status"))
print("  Synced Count (should be 0):", sync2.get("synced_count"))
print("  Skipped Duplicates (should be 14):", len(sync2.get("skipped_duplicates")))
print("  Skipped Duplicates List:", sync2.get("skipped_duplicates"))

assert sync2.get("status") == "SUCCESS"
assert sync2.get("synced_count") == 0, "Duplicate upload should insert 0 new records"
assert len(sync2.get("skipped_duplicates")) == 14, "All 14 parameters should be skipped as duplicates"

print("\n>>> Phase 2 PASSED: Duplicate detection completely prevented redundant readings!")
print("\n======================================================================")
print("STEP 4 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
print("======================================================================")
