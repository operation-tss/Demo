import os
import sys
import json
import logging
from typing import Dict, Any, List

sys.path.insert(0, "backend")

from app.services.ocr_service import init_ocr_models, extract_text_from_image
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.report_classifier import classify_report
from app.services.data_extractor import extract_all_parameters, extract_patient_information
from app.services.report_analyzer import analyze_test_result, generate_findings_and_summary

logging.basicConfig(level=logging.WARNING)

def test_file_pipeline(filepath: str) -> Dict[str, Any]:
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        file_bytes = f.read()

    warnings: List[str] = []
    if filepath.lower().endswith(".pdf"):
        try:
            extracted_text, is_scanned, ocr_conf, ocr_engine, pdf_warn = extract_text_from_pdf(file_bytes)
            warnings.extend(pdf_warn)
        except Exception as e:
            return {"file": filename, "status": "failed", "error": str(e), "parameters": []}
    else:
        extracted_text, ocr_conf, ocr_engine, img_warn = extract_text_from_image(file_bytes)
        warnings.extend(img_warn)

    if not extracted_text or len(extracted_text.strip()) < 8:
        return {
            "file": filename,
            "status": "failed",
            "ocr_engine": ocr_engine,
            "ocr_confidence": 0.0,
            "report_type": "Unknown / Unclassified",
            "parameters": [],
            "warnings": warnings
        }

    report_type, class_conf, _ = classify_report(extracted_text)
    patient_info, report_date, lab_name = extract_patient_information(extracted_text)
    raw_params = extract_all_parameters(extracted_text, report_type, patient_info)

    analyzed_params = [analyze_test_result(p) for p in raw_params]

    return {
        "file": filename,
        "status": "completed",
        "ocr_engine": ocr_engine,
        "ocr_confidence": ocr_conf,
        "report_type": report_type,
        "patient_name": patient_info.name,
        "patient_id": patient_info.patient_id,
        "patient_age": patient_info.age,
        "patient_gender": patient_info.gender,
        "report_date": report_date,
        "parameters": [
            {
                "name": p.test_name,
                "value": p.value,
                "unit": p.unit,
                "range": p.reference_range,
                "status": p.status
            }
            for p in analyzed_params
        ],
        "warnings": warnings
    }

def main():
    print("\n" + "=" * 80)
    print("   MEDISCAN PRO - IMAGE OCR & FIELD-LEVEL ACCURACY EVALUATION")
    print("=" * 80 + "\n")

    init_ocr_models()

    test_images = [
        "sample_screenshot_cbc.png",
        "sample_screenshot_lft.jpg",
        "sample_tilted_kft.png",
        "sample_blurred_lipid.png",
        "sample_scanned_lft.pdf",
        "sample_unreadable.jpg"
    ]

    total_fields_expected = 0
    total_fields_extracted = 0

    for fname in test_images:
        fpath = os.path.join("samples", fname)
        if not os.path.exists(fpath):
            print(f"Skipping {fname} (not found)")
            continue

        res = test_file_pipeline(fpath)
        print(f"\n--- {fname} ---")
        print(f"Status: {res['status']} | Engine: {res.get('ocr_engine', 'N/A')} | Confidence: {res.get('ocr_confidence', 0.0):.1%}")
        print(f"Report Type: {res.get('report_type', 'N/A')}")
        print(f"Patient: {res.get('patient_name', 'N/A')} | ID: {res.get('patient_id', 'N/A')} | Date: {res.get('report_date', 'N/A')}")
        print(f"Extracted Parameters: {len(res['parameters'])}")

        for p in res["parameters"]:
            print(f"  • {p['name']:<28}: {p['value']:<8} {p['unit']:<14} (Ref: {p['range']:<14}) -> [{p['status']}]")

        if res.get("warnings"):
            print(f"Warnings: {res['warnings']}")

if __name__ == "__main__":
    main()
