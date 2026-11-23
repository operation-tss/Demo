import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    print(f"GET /api/health -> {res.status_code}, {res.json()}")
    assert res.status_code == 200

def test_all_reports():
    sample_files = [
        # Original PDFs
        "sample_cbc.pdf",
        "sample_lft.pdf",
        "sample_kft.pdf",
        "sample_lipid.pdf",
        "sample_thyroid.pdf",
        "sample_urine.pdf",
        "sample_sugar.pdf",
        "sample_missing_ranges.pdf",
        "sample_unknown.pdf",
        "sample_empty.pdf",
        "sample_corrupted.pdf",
        
        # New Images, Screenshots, Tilted & Scanned Reports
        "sample_screenshot_cbc.png",
        "sample_screenshot_lft.jpg",
        "sample_tilted_kft.png",
        "sample_blurred_lipid.png",
        "sample_scanned_lft.pdf",
        "sample_unreadable.jpg"
    ]
    
    samples_dir = os.path.join(os.path.dirname(__file__), "..", "samples")
    
    print("\n=======================================================")
    print("   EXECUTING MEDICAL REPORT ANALYZER TEST SUITE")
    print("=======================================================\n")

    for filename in sample_files:
        filepath = os.path.join(samples_dir, filename)
        if not os.path.exists(filepath):
            print(f"Skipping missing file: {filename}")
            continue
            
        with open(filepath, "rb") as f:
            file_bytes = f.read()
            
        if filename.endswith(".pdf"):
            mime = "application/pdf"
        elif filename.endswith(".png"):
            mime = "image/png"
        elif filename.endswith((".jpg", ".jpeg")):
            mime = "image/jpeg"
        else:
            mime = "application/octet-stream"

        response = client.post(
            "/api/reports/analyze",
            files={"file": (filename, file_bytes, mime)}
        )
        print(f"\n--- Testing: {filename} ---")
        print(f"HTTP Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('processing_status')}")
            print(f"Report Type: {data.get('report_type')}")
            if data.get('ocr_confidence') is not None:
                print(f"OCR Confidence: {data.get('ocr_confidence') * 100:.1f}% [{data.get('ocr_engine')}]")
            print(f"Patient Info: {data.get('patient_information')}")
            print(f"Summary: {data.get('summary')}")
            print(f"Parameters Extracted: {len(data.get('results', []))}")
            for r in data.get("results", [])[:4]:
                print(f"  • {r['test_name']}: {r['value']} {r['unit']} [{r['reference_range']}] -> {r['status']}")
            if len(data.get("results", [])) > 4:
                print(f"  ... (+ {len(data.get('results', [])) - 4} more)")
            if data.get("findings"):
                print(f"Findings: {data.get('findings')[:3]}")
            if data.get("warnings"):
                print(f"Warnings: {data.get('warnings')}")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    test_health()
    test_all_reports()
