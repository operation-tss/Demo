import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pymupdf

os.makedirs("samples", exist_ok=True)

# Select high quality system font if available
FONT_PATH = "C:/Windows/Fonts/arial.ttf"
if os.path.exists(FONT_PATH):
    font_title = ImageFont.truetype(FONT_PATH, 17)
    font_header = ImageFont.truetype(FONT_PATH, 14)
    font_bold = ImageFont.truetype(FONT_PATH, 13)
    font_body = ImageFont.truetype(FONT_PATH, 13)
    font_small = ImageFont.truetype(FONT_PATH, 11)
else:
    font_title = ImageFont.load_default()
    font_header = ImageFont.load_default()
    font_bold = ImageFont.load_default()
    font_body = ImageFont.load_default()
    font_small = ImageFont.load_default()

def create_report_image(filename, title, patient, rows, tilt_angle=0.0, add_blur=False, add_shadow=False):
    w, h = 1000, 750
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header banner
    draw.rectangle([0, 0, w, 75], fill=(30, 58, 138))
    draw.text((30, 16), "METROPOLITAN CLINICAL LABORATORY & DIAGNOSTIC CENTRE", fill=(255, 255, 255), font=font_title)
    draw.text((30, 44), "104 Healthcare Boulevard • Tel: +1 (555) 234-5678 • ISO 15189 Certified", fill=(219, 234, 254), font=font_small)

    # Patient details box
    draw.rectangle([30, 95, w - 30, 165], outline=(203, 213, 225), fill=(248, 250, 252), width=1)
    draw.text((45, 108), f"Patient Name: {patient['name']}", fill=(15, 23, 42), font=font_header)
    draw.text((400, 108), f"Patient ID: {patient['id']}", fill=(15, 23, 42), font=font_header)
    draw.text((700, 108), f"Age / Sex: {patient['age']} / {patient['gender']}", fill=(15, 23, 42), font=font_header)

    draw.text((45, 135), f"Report Date: {patient['date']}", fill=(15, 23, 42), font=font_body)
    draw.text((400, 135), f"Referred By: Dr. A. Sharma, MD", fill=(15, 23, 42), font=font_body)
    draw.text((700, 135), f"Sample: Venous Blood", fill=(15, 23, 42), font=font_body)

    # Report title
    draw.text((30, 185), f"DEPARTMENT OF CLINICAL PATHOLOGY - {title.upper()}", fill=(30, 58, 138), font=font_bold)

    # Table Header
    draw.rectangle([30, 215, w - 30, 250], fill=(37, 99, 235))
    draw.text((45, 225), "Test Parameter", fill=(255, 255, 255), font=font_bold)
    draw.text((350, 225), "Observed Value", fill=(255, 255, 255), font=font_bold)
    draw.text((550, 225), "Unit", fill=(255, 255, 255), font=font_bold)
    draw.text((680, 225), "Reference Interval", fill=(255, 255, 255), font=font_bold)
    draw.text((880, 225), "Flag", fill=(255, 255, 255), font=font_bold)

    # Table Rows
    y = 260
    for i, row in enumerate(rows):
        bg = (248, 250, 252) if i % 2 == 1 else (255, 255, 255)
        draw.rectangle([30, y, w - 30, y + 34], fill=bg)
        draw.text((45, y + 8), row[0], fill=(15, 23, 42), font=font_body)
        draw.text((350, y + 8), row[1], fill=(220, 38, 38) if row[4] in ["L", "H", "H*", "L*"] else (15, 23, 42), font=font_body)
        draw.text((550, y + 8), row[2], fill=(71, 85, 105), font=font_body)
        draw.text((680, y + 8), row[3], fill=(71, 85, 105), font=font_body)
        draw.text((880, y + 8), row[4], fill=(220, 38, 38) if row[4] else (15, 23, 42), font=font_body)
        y += 36

    # Footer note
    draw.text((30, y + 25), "Verified by Medical Biochemist & Pathologist • End of Report", fill=(100, 116, 139), font=font_small)

    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # 1. Simulate mobile camera shadow gradient if requested
    if add_shadow:
        gradient = np.linspace(0.65, 1.0, w, dtype=np.float32)
        gradient = np.tile(gradient, (h, 1))
        for c in range(3):
            cv_img[:, :, c] = np.clip(cv_img[:, :, c] * gradient, 0, 255).astype(np.uint8)

    # 2. Simulate camera out-of-focus blur if requested
    if add_blur:
        cv_img = cv2.GaussianBlur(cv_img, (3, 3), 0.8)

    # 3. Rotate image if tilt requested
    if abs(tilt_angle) > 0.1:
        center = (w // 2, h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, tilt_angle, 1.0)
        cv_img = cv2.warpAffine(cv_img, rot_mat, (w, h), borderValue=(255, 255, 255), flags=cv2.INTER_CUBIC)

    filepath = os.path.join("samples", filename)
    cv2.imwrite(filepath, cv_img)
    print(f"Generated test image: {filepath}")
    return filepath

# 1. Clear Desktop Screenshot: CBC (PNG)
create_report_image(
    "sample_screenshot_cbc.png",
    "Complete Blood Count (CBC)",
    {"name": "Sarah Connor", "id": "PID-88019", "age": "32", "gender": "Female", "date": "2026-11-18"},
    [
        ["Hemoglobin", "10.5", "g/dL", "12.0 - 15.5", "L"],
        ["Total RBC Count", "3.9", "mil/uL", "4.0 - 5.2", "L"],
        ["Packed Cell Volume (PCV)", "32.0", "%", "36.0 - 46.0", "L"],
        ["Total Leukocyte Count (WBC)", "7200", "/uL", "4000 - 11000", ""],
        ["Platelet Count", "85000", "/uL", "150000 - 450000", "L*"]
    ]
)

# 2. Camera Photograph with Lighting / Shadow: LFT (JPG)
create_report_image(
    "sample_screenshot_lft.jpg",
    "Liver Function Test (LFT)",
    {"name": "James Gordon", "id": "PID-44211", "age": "47", "gender": "Male", "date": "2026-11-17"},
    [
        ["Total Bilirubin", "2.8", "mg/dL", "0.2 - 1.2", "H*"],
        ["SGOT / AST", "75", "U/L", "5 - 40", "H"],
        ["SGPT / ALT", "88", "U/L", "7 - 56", "H"],
        ["Alkaline Phosphatase (ALP)", "130", "U/L", "44 - 147", ""],
        ["Albumin", "3.9", "g/dL", "3.5 - 5.2", ""]
    ],
    add_shadow=True
)

# 3. Tilted / Rotated Phone Capture: KFT (PNG) - 3.5 degrees rotation
create_report_image(
    "sample_tilted_kft.png",
    "Kidney Function Test (KFT)",
    {"name": "Bruce Banner", "id": "PID-33045", "age": "49", "gender": "Male", "date": "2026-11-16"},
    [
        ["Serum Creatinine", "2.1", "mg/dL", "0.7 - 1.3", "H*"],
        ["Blood Urea", "58", "mg/dL", "15 - 45", "H"],
        ["Blood Urea Nitrogen (BUN)", "26.5", "mg/dL", "7 - 20", "H"],
        ["Uric Acid", "6.2", "mg/dL", "3.5 - 7.2", ""],
        ["eGFR", "38", "mL/min/1.73m2", "> 90", "L"]
    ],
    tilt_angle=3.5
)

# 4. Low-Quality / Blurry Capture: Lipid Profile (PNG)
create_report_image(
    "sample_blurred_lipid.png",
    "Lipid Profile",
    {"name": "Diana Prince", "id": "PID-11029", "age": "38", "gender": "Female", "date": "2026-11-15"},
    [
        ["Total Cholesterol", "245", "mg/dL", "< 200", "H*"],
        ["Triglycerides", "210", "mg/dL", "< 150", "H"],
        ["HDL Cholesterol", "42", "mg/dL", "> 50", "L"],
        ["LDL Cholesterol", "161", "mg/dL", "< 100", "H*"]
    ],
    add_blur=True
)

# 5. Scanned PDF (Pure raster PDF with NO selectable text)
def create_pure_scanned_pdf():
    img_path = os.path.join("samples", "sample_screenshot_lft.jpg")
    doc = pymupdf.open()
    img_doc = pymupdf.open(img_path)
    pdf_bytes = img_doc.convert_to_pdf()
    img_doc.close()
    
    scanned_pdf_path = os.path.join("samples", "sample_scanned_lft.pdf")
    with open(scanned_pdf_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"Generated pure scanned PDF: {scanned_pdf_path}")

create_pure_scanned_pdf()

# 6. Unreadable Noise Image
def create_unreadable_image():
    noise = np.random.randint(0, 256, (400, 600, 3), dtype=np.uint8)
    blurred = cv2.GaussianBlur(noise, (51, 51), 0)
    filepath = os.path.join("samples", "sample_unreadable.jpg")
    cv2.imwrite(filepath, blurred)
    print(f"Generated unreadable image: {filepath}")

create_unreadable_image()
