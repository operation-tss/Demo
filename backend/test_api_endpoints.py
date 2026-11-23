import requests
import json

URL = "http://127.0.0.1:8000/api/reports/analyze"
SAMPLE_FILE = "samples/sample_cbc.pdf"

print("--- Test 1: Standalone Upload (No patient_id) ---")
with open(SAMPLE_FILE, "rb") as f:
    resp = requests.post(URL, files={"file": ("sample_cbc.pdf", f, "application/pdf")})
print("HTTP Status:", resp.status_code)
data = resp.json()
print("Processing Status:", data.get("processing_status"))
print("Report Type:", data.get("report_type"))
print("Total Parameters:", len(data.get("results", [])))
print("Timeline Sync (should be None):", data.get("timeline_sync"))
assert resp.status_code == 200
assert data.get("timeline_sync") is None
print("Test 1 Passed!\n")

print("--- Test 2: Upload with Nonexistent patient_id (999999) ---")
with open(SAMPLE_FILE, "rb") as f:
    resp = requests.post(URL, files={"file": ("sample_cbc.pdf", f, "application/pdf")}, data={"patient_id": 999999})
print("HTTP Status:", resp.status_code)
data = resp.json()
print("Processing Status:", data.get("processing_status"))
print("Timeline Sync Status:", data.get("timeline_sync", {}).get("status"))
print("Timeline Sync Error:", data.get("timeline_sync", {}).get("error"))
assert resp.status_code == 200
assert data.get("timeline_sync", {}).get("status") == "FAILED"
assert "does not exist in Mst_Patients" in data.get("timeline_sync", {}).get("error")
print("Test 2 Passed!\n")

print("--- Test 3: Upload with Authenticated patient_id (8) ---")
with open(SAMPLE_FILE, "rb") as f:
    resp = requests.post(URL, files={"file": ("sample_cbc.pdf", f, "application/pdf")}, data={"patient_id": 8})
print("HTTP Status:", resp.status_code)
data = resp.json()
print("Processing Status:", data.get("processing_status"))
print("Timeline Sync Status:", data.get("timeline_sync", {}).get("status"))
print("Attempted Count:", data.get("timeline_sync", {}).get("attempted_count"))
print("Synced Count:", data.get("timeline_sync", {}).get("synced_count"))
print("Skipped for Review:", len(data.get("timeline_sync", {}).get("skipped_for_review", [])))
assert resp.status_code == 200
assert data.get("timeline_sync") is not None
print("Test 3 Passed!\n")

print("--- Test 4: Image Upload with patient_id (sample_image.png) ---")
with open("samples/sample_image.png", "rb") as f:
    resp = requests.post(URL, files={"file": ("sample_image.png", f, "image/png")}, data={"patient_id": 8})
print("HTTP Status:", resp.status_code)
data = resp.json()
print("Processing Status:", data.get("processing_status"))
print("Report Type:", data.get("report_type"))
print("Timeline Sync Status:", data.get("timeline_sync", {}).get("status"))
assert resp.status_code == 200
print("Test 4 Passed!\n")

print("ALL API ENDPOINT TESTS PASSED SUCCESSFULLY!")
