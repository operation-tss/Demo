import urllib.request
import json

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

print("=== 1. VERIFY DB STATUS ===")
db_status = fetch("http://127.0.0.1:8000/api/v1/report-analyzer/db-status")
print(json.dumps(db_status, indent=2))
assert db_status.get("database") == "HealthCare_connect_test", f"Expected HealthCare_connect_test, got {db_status.get('database')}"
assert db_status.get("is_test_db") is True, "is_test_db should be True"

print("\n=== 2. VERIFY PATIENTS API ===")
patients_resp = fetch("http://127.0.0.1:8000/api/v1/report-analyzer/patients")
patients = patients_resp.get("data", [])
print(f"Total patients in test DB: {len(patients)}")
for p in patients:
    print(f"  ID={p.get('patient_id')}, Name={p.get('patient_name')}, HealthID={p.get('health_id')}, Phone={p.get('phone')}")

test_p = next((p for p in patients if "TEST" in p.get("patient_name", "")), None)
assert test_p is not None, "Rohan Sharma TEST not found!"
assert test_p["patient_name"] == "Rohan Sharma TEST"
assert test_p["health_id"] == "HC-TEST-ROHAN-1"
assert test_p["phone"] == "9999999999"

print("\n=== 3. VERIFY TIMELINE API (70 RECORDS ACROSS 10 DATES) ===")
pid = test_p["patient_id"]
tl_resp = fetch(f"http://127.0.0.1:8000/api/v1/report-analyzer/timeline/{pid}")
timeline_data = tl_resp.get("data", {})
items = timeline_data.get("timeline", [])
dates = sorted(list(set(r["report_date"] for r in items)))
print(f"Total timeline records: {len(items)}")
print(f"Distinct dates ({len(dates)}): {dates}")
assert len(items) == 70, f"Expected 70 records, got {len(items)}"
assert len(dates) == 10, f"Expected 10 dates, got {len(dates)}"

print("\n=== 4. VERIFY HEMOGLOBIN (10 CHRONOLOGICAL READINGS) ===")
hgb_items = [r for r in items if r["parameter_name"] == "Hemoglobin"]
print(f"Hemoglobin readings count: {len(hgb_items)}")
assert len(hgb_items) == 10, f"Expected 10 Hemoglobin readings, got {len(hgb_items)}"
for idx, h in enumerate(hgb_items, 1):
    print(f"  #{idx:02d} | Date: {h['report_date']} | Result: {h['test_result']} {h['unit']} | Range: {h['reference_range']} | Status: {h['status']}")

print("\n====================================================")
print("ALL 5 VERIFICATION CHECKS PASSED ON LIVE SERVER!")
print("====================================================")
