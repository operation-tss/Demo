import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont

os.makedirs("samples", exist_ok=True)
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "ReportTitle",
    parent=styles["Heading1"],
    fontSize=14,
    leading=18,
    alignment=1, # Center
    textColor=colors.HexColor("#1e3a8a")
)

header_style = ParagraphStyle(
    "LabHeader",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    alignment=1,
    textColor=colors.HexColor("#475569")
)

def create_lab_pdf(filename, report_title, patient_info, test_data, notes=None):
    filepath = os.path.join("samples", filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    # Lab Header
    story.append(Paragraph("<b>METROPOLITAN CLINICAL LABORATORY & DIAGNOSTIC CENTRE</b>", title_style))
    story.append(Paragraph("104 Healthcare Boulevard, Medical District • Tel: +1 (555) 234-5678 • ISO 15189 Certified", header_style))
    story.append(Spacer(1, 15))

    # Patient Demographics Table
    demo_data = [
        [f"Patient Name: {patient_info['name']}", f"Patient ID: {patient_info['id']}"],
        [f"Age / Sex: {patient_info['age']} / {patient_info['gender']}", f"Report Date: {patient_info['date']}"],
        [f"Referred By: Dr. A. Sharma, MD", f"Sample Type: {patient_info.get('sample', 'Venous Blood')}"]
    ]
    t_demo = Table(demo_data, colWidths=[270, 270])
    t_demo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_demo)
    story.append(Spacer(1, 15))

    # Report Heading
    story.append(Paragraph(f"<b>DEPARTMENT OF CLINICAL PATHOLOGY - {report_title.upper()}</b>", ParagraphStyle(
        "SubTitle", parent=styles["Heading2"], fontSize=11, leading=14, textColor=colors.HexColor("#0f172a")
    )))
    story.append(Spacer(1, 8))

    # Table of tests
    table_rows = [["Test Parameter", "Observed Value", "Unit", "Biological Reference Interval", "Flag"]]
    for row in test_data:
        table_rows.append(row)

    t_tests = Table(table_rows, colWidths=[180, 90, 80, 140, 50])
    t_tests.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2563eb")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f1f5f9")]),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_tests)
    story.append(Spacer(1, 15))

    if notes:
        story.append(Paragraph(f"<b>Clinical Notes / Impression:</b> {notes}", ParagraphStyle(
            "Notes", parent=styles["Normal"], fontSize=8.5, leading=11, textColor=colors.HexColor("#334155")
        )))
        story.append(Spacer(1, 10))

    story.append(Spacer(1, 20))
    story.append(Paragraph("--- End of Report • Verified by Medical Biochemist & Pathologist ---", header_style))

    doc.build(story)
    print(f"Generated {filepath}")

# 1. CBC Report
create_lab_pdf(
    "sample_cbc.pdf",
    "Complete Blood Count (CBC)",
    {"name": "John Doe", "id": "PID-98214", "age": "34 Yrs", "gender": "Male", "date": "2026-11-18", "sample": "EDTA Whole Blood"},
    [
        ["Hemoglobin", "11.2", "g/dL", "13.0 - 17.0", "L"],
        ["Total RBC Count", "4.1", "mil/uL", "4.5 - 5.9", "L"],
        ["Packed Cell Volume (PCV)", "34.5", "%", "40.0 - 50.0", "L"],
        ["MCV", "84.0", "fL", "80.0 - 100.0", ""],
        ["MCH", "27.3", "pg", "27.0 - 33.0", ""],
        ["MCHC", "32.5", "g/dL", "32.0 - 36.0", ""],
        ["RDW", "13.2", "%", "11.5 - 14.5", ""],
        ["Total Leukocyte Count (WBC)", "6500", "/uL", "4000 - 11000", ""],
        ["Neutrophils", "62", "%", "40 - 75", ""],
        ["Lymphocytes", "28", "%", "20 - 45", ""],
        ["Monocytes", "6", "%", "2 - 10", ""],
        ["Eosinophils", "3", "%", "1 - 6", ""],
        ["Basophils", "1", "%", "0 - 1", ""],
        ["Platelet Count", "90000", "/uL", "150000 - 450000", "L*"]
    ],
    notes="Mild normocytic normochromic anemia with moderate thrombocytopenia. Clinical correlation advised."
)

# 2. LFT Report
create_lab_pdf(
    "sample_lft.pdf",
    "Liver Function Test (LFT)",
    {"name": "Emily Clark", "id": "PID-55102", "age": "42 Yrs", "gender": "Female", "date": "2026-11-17", "sample": "Serum"},
    [
        ["Total Bilirubin", "2.1", "mg/dL", "0.2 - 1.2", "H*"],
        ["Direct Bilirubin", "0.8", "mg/dL", "0.0 - 0.3", "H*"],
        ["Indirect Bilirubin", "1.3", "mg/dL", "0.2 - 0.8", "H*"],
        ["SGOT / AST", "58", "U/L", "5 - 40", "H"],
        ["SGPT / ALT", "65", "U/L", "7 - 56", "H"],
        ["Alkaline Phosphatase (ALP)", "115", "U/L", "44 - 147", ""],
        ["Total Protein", "7.1", "g/dL", "6.0 - 8.3", ""],
        ["Albumin", "4.1", "g/dL", "3.5 - 5.2", ""],
        ["Globulin", "3.0", "g/dL", "2.0 - 3.5", ""],
        ["A/G Ratio", "1.36", "ratio", "1.0 - 2.2", ""]
    ],
    notes="Elevated transaminases and conjugated hyperbilirubinemia noted."
)

# 3. KFT Report
create_lab_pdf(
    "sample_kft.pdf",
    "Kidney Function Test (KFT)",
    {"name": "Robert Brown", "id": "PID-77341", "age": "58 Yrs", "gender": "Male", "date": "2026-11-16", "sample": "Serum"},
    [
        ["Serum Creatinine", "1.8", "mg/dL", "0.7 - 1.3", "H*"],
        ["Blood Urea", "52", "mg/dL", "15 - 45", "H"],
        ["Blood Urea Nitrogen (BUN)", "24.3", "mg/dL", "7 - 20", "H"],
        ["Uric Acid", "5.5", "mg/dL", "3.5 - 7.2", ""],
        ["eGFR", "42", "mL/min/1.73m2", "> 90", "L"]
    ],
    notes="Impaired renal function indicated by elevated creatinine and reduced eGFR."
)

# 4. Lipid Profile
create_lab_pdf(
    "sample_lipid.pdf",
    "Lipid Profile",
    {"name": "David Smith", "id": "PID-44190", "age": "48 Yrs", "gender": "Male", "date": "2026-11-15", "sample": "Serum (12h Fasting)"},
    [
        ["Total Cholesterol", "245", "mg/dL", "< 200", "H"],
        ["Triglycerides", "195", "mg/dL", "< 150", "H"],
        ["HDL Cholesterol", "38", "mg/dL", "> 40", "L"],
        ["LDL Cholesterol", "168", "mg/dL", "< 100", "H*"],
        ["VLDL Cholesterol", "39", "mg/dL", "5 - 30", "H"],
        ["TC / HDL Ratio", "6.4", "ratio", "< 4.5", "H"]
    ],
    notes="Dyslipidemia pattern with borderline hypertriglyceridemia and elevated LDL."
)

# 5. Thyroid Profile
create_lab_pdf(
    "sample_thyroid.pdf",
    "Thyroid Profile",
    {"name": "Sarah Jenkins", "id": "PID-66231", "age": "29 Yrs", "gender": "Female", "date": "2026-11-14", "sample": "Serum"},
    [
        ["TSH", "7.45", "uIU/mL", "0.35 - 4.94", "H*"],
        ["Total T3", "110", "ng/dL", "80 - 200", ""],
        ["Total T4", "8.2", "ug/dL", "5.1 - 14.1", ""],
        ["Free T3", "2.8", "pg/mL", "2.0 - 4.4", ""],
        ["Free T4", "1.15", "ng/dL", "0.93 - 1.70", ""]
    ],
    notes="Subclinical hypothyroidism pattern (elevated TSH with normal free and total thyroid hormones)."
)

# 6. Urine Routine
create_lab_pdf(
    "sample_urine.pdf",
    "Urine Routine Examination",
    {"name": "Michael Davis", "id": "PID-33019", "age": "31 Yrs", "gender": "Male", "date": "2026-11-13", "sample": "Fresh Clean Catch Urine"},
    [
        ["Urine Specific Gravity", "1.020", "", "1.005 - 1.030", ""],
        ["Urine pH / Reaction", "6.0", "", "4.5 - 8.0", ""],
        ["Urine Protein / Albumin", "Trace", "", "Nil / Negative", "H*"],
        ["Urine Glucose / Sugar", "Nil", "", "Nil / Negative", ""],
        ["Urine Pus Cells (WBC)", "10-12", "/HPF", "0 - 5", "H*"],
        ["Urine RBCs", "1-2", "/HPF", "0 - 2", ""],
        ["Urine Epithelial Cells", "2-3", "/HPF", "0 - 5", ""],
        ["Urine Ketone Bodies", "Negative", "", "Negative", ""]
    ],
    notes="Pyuria with trace proteinuria. Correlate with clinical urinary symptoms."
)

# 7. Blood Sugar
create_lab_pdf(
    "sample_sugar.pdf",
    "Blood Glucose & Diabetic Profile",
    {"name": "Alice Walker", "id": "PID-11208", "age": "52 Yrs", "gender": "Female", "date": "2026-11-12", "sample": "Plasma & Whole Blood"},
    [
        ["Fasting Blood Sugar (FBS)", "142", "mg/dL", "70 - 99", "H*"],
        ["Post Prandial Blood Sugar (PPBS)", "195", "mg/dL", "70 - 140", "H*"],
        ["HbA1c", "7.4", "%", "< 5.7", "H*"]
    ],
    notes="Elevated glycemic indices consistent with inadequate diabetic control."
)

# 8. Missing Ranges
create_lab_pdf(
    "sample_missing_ranges.pdf",
    "General Clinical Chemistry (No Range Column)",
    {"name": "Karen Wilson", "id": "PID-99012", "age": "45 Yrs", "gender": "Female", "date": "2026-11-11", "sample": "Serum"},
    [
        ["Serum Sodium", "140", "mEq/L", "", ""],
        ["Serum Potassium", "4.2", "mEq/L", "", ""],
        ["Serum Chloride", "101", "mEq/L", "", ""]
    ],
    notes="Electrolytes run as part of routine pre-operative screening."
)

# 9. Unknown Document (Non-lab medical invoice / clearance letter)
def create_unknown_pdf():
    filepath = os.path.join("samples", "sample_unknown.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = [
        Paragraph("<b>HOSPITAL BILLING INVOICE & DISCHARGE RECEIPT</b>", title_style),
        Spacer(1, 15),
        Paragraph("Patient Name: Mark Spencer | Patient ID: ACC-50291 | Date: 2026-11-10", styles["Normal"]),
        Spacer(1, 10),
        Paragraph("Room Charges (3 Days Deluxe Wing): $1,500.00", styles["Normal"]),
        Paragraph("Surgical Consultation Fee: $450.00", styles["Normal"]),
        Paragraph("Pharmacy & Consumables: $320.00", styles["Normal"]),
        Paragraph("Total Paid: $2,270.00 by Insurance Claim", styles["Normal"]),
        Spacer(1, 15),
        Paragraph("The patient has settled all outstanding financial liabilities and is cleared for administrative discharge.", styles["Normal"])
    ]
    doc.build(story)
    print(f"Generated {filepath}")

create_unknown_pdf()

# 10. Empty PDF (0 bytes)
with open(os.path.join("samples", "sample_empty.pdf"), "wb") as f:
    pass
print("Generated sample_empty.pdf")

# 11. Corrupted PDF
with open(os.path.join("samples", "sample_corrupted.pdf"), "wb") as f:
    f.write(b"%PDF-1.4 THIS_IS_A_CORRUPTED_FILE_WITH_BROKEN_CROSS_REFERENCE_TABLES_XXXXX")
print("Generated sample_corrupted.pdf")

# 12. Sample Image (PNG) with test parameters
def create_sample_image():
    img = Image.new("RGB", (800, 500), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw header
    draw.rectangle([0, 0, 800, 60], fill=(37, 99, 235))
    draw.text((20, 15), "ST. JUDE DIAGNOSTIC LAB - LFT REPORT", fill=(255, 255, 255))
    
    # Patient info
    draw.text((30, 80), "Patient Name: Arthur Dent", fill=(0, 0, 0))
    draw.text((350, 80), "Age: 42 Yrs", fill=(0, 0, 0))
    draw.text((550, 80), "Sex: Male", fill=(0, 0, 0))
    draw.text((30, 110), "Date: 2026-11-18", fill=(0, 0, 0))
    draw.text((350, 110), "Patient ID: LAB-9092", fill=(0, 0, 0))
    
    # Divider line
    draw.line([(30, 140), (770, 140)], fill=(200, 200, 200), width=2)
    
    # Column headers
    draw.text((30, 160), "Test Name", fill=(100, 100, 100))
    draw.text((250, 160), "Value", fill=(100, 100, 100))
    draw.text((370, 160), "Unit", fill=(100, 100, 100))
    draw.text((500, 160), "Reference Range", fill=(100, 100, 100))
    
    # Rows
    rows = [
        ("Total Bilirubin", "2.4", "mg/dL", "0.2 - 1.2"),
        ("SGOT / AST", "65", "U/L", "5 - 40"),
        ("SGPT / ALT", "72", "U/L", "7 - 56"),
        ("Alkaline Phosphatase", "98", "U/L", "44 - 147"),
        ("Albumin", "3.8", "g/dL", "3.5 - 5.2"),
    ]
    
    y = 200
    for name, val, unit, ref in rows:
        draw.text((30, y), name, fill=(0, 0, 0))
        draw.text((250, y), val, fill=(0, 0, 0))
        draw.text((370, y), unit, fill=(0, 0, 0))
        draw.text((500, y), ref, fill=(0, 0, 0))
        y += 40
        
    img_path = os.path.join("samples", "sample_image.png")
    img.save(img_path)
    print(f"Generated {img_path}")

create_sample_image()
