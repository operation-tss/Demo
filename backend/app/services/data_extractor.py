import re
from typing import Dict, Any, List, Optional, Tuple
from rapidfuzz import fuzz
from ..schemas.report_schema import PatientInformation, TestResult

def restore_medical_decimals(test_name: str, val_str: str, ref_range_str: str) -> Tuple[str, str]:
    """
    Prevents errors in decimal values and comma-separated numbers (Requirement 6).
    Restores missing periods from OCR drops based on clinical ranges.
    """
    val = re.sub(r"(\d+),(\d{1,2})(?!\d)", r"\1.\2", val_str.strip())
    ref = re.sub(r"(\d+),(\d{1,2})(?!\d)", r"\1.\2", ref_range_str.strip())

    # 1. Restore reference range decimals
    if re.search(r"\b0[2-9]\s*[-–]\s*1[0-9]\b", ref):
        ref = re.sub(r"\b0([2-9])\s*[-–]\s*1([0-9])\b", r"0.\1 - 1.\2", ref)
    elif re.search(r"\b40\s*[-–]\s*5[0-9]\b", ref):
        ref = re.sub(r"\b40\s*[-–]\s*5([0-9])\b", r"4.0 - 5.\1", ref)
    elif re.search(r"\b40\s*[-–]\s*5\.([0-9])\b", ref):
        ref = re.sub(r"\b40\s*[-–]\s*5\.([0-9])\b", r"4.0 - 5.\1", ref)
    elif re.search(r"\b35\s*[-–]\s*5[0-9]\b", ref):
        ref = re.sub(r"\b35\s*[-–]\s*5([0-9])\b", r"3.5 - 5.\1", ref)
    elif re.search(r"\b02\s*[-–]\s*12\b", ref):
        ref = "0.2 - 1.2"
    elif re.search(r"\b07\s*[-–]\s*13\b", ref):
        ref = "0.7 - 1.3"

    # 2. Restore value decimals where period was dropped in OCR
    try:
        num = float(re.sub(r"[^\d\.]", "", val))
        if "Bilirubin" in test_name and 10 <= num <= 99 and ("0." in ref or "1." in ref or not ref):
            val = str(round(num / 10.0, 2))
        elif "Creatinine" in test_name and 10 <= num <= 99 and ("0." in ref or "1." in ref or not ref):
            val = str(round(num / 10.0, 2))
        elif "Albumin" in test_name and 20 <= num <= 99:
            val = str(round(num / 10.0, 2))
        elif "RBC" in test_name and 20 <= num <= 99:
            val = str(round(num / 10.0, 2))
        elif "Uric Acid" in test_name and 20 <= num <= 99:
            val = str(round(num / 10.0, 2))
        elif "Calcium" in test_name and 60 <= num <= 150:
            val = str(round(num / 10.0, 2))
        elif "Potassium" in test_name and 25 <= num <= 99:
            val = str(round(num / 10.0, 2))
        elif "BUN" in test_name and 100 <= num <= 500:
            val = str(round(num / 10.0, 1))
    except Exception:
        pass

    return val, ref

def normalize_medical_unit(raw_u: str, default_unit: str) -> str:
    """Normalizes OCR unit typos to standard clinical notation."""
    if not raw_u:
        return default_unit
    u_clean = raw_u.strip()
    u_lower = u_clean.lower()
    if u_lower in ["g/dl", "gdl", "g.dl", "gidl", "g/l"]:
        return "g/dL"
    if u_lower in ["mg/dl", "mgdl", "mg.dl", "mg/l"]:
        return "mg/dL"
    if u_lower in ["mil/ul", "milul", "milful", "mil/cumm", "mil/mm3", "miu"]:
        return "mil/uL"
    if u_lower in ["/ul", "ful", "lul", "ul", "/cumm", "/mm3"]:
        return "/uL"
    if u_lower in ["u/l", "uil", "un", "iu/l", "ual"]:
        return "U/L"
    if "min/1.73" in u_lower or "min" in u_lower:
        return "mL/min/1.73m2"
    if u_lower in ["%", "percent"]:
        return "%"
    if u_lower in ["fl"]:
        return "fL"
    if u_lower in ["pg"]:
        return "pg"
    return u_clean

TEST_DICTIONARY = {
    # CBC Parameters
    "Hemoglobin": {
        "aliases": [r"hemoglobin\b", r"haemoglobin\b", r"\bhb\b"],
        "default_unit": "g/dL",
        "default_range_male": "13.0 - 17.0",
        "default_range_female": "12.0 - 15.5",
        "default_range": "12.0 - 17.0"
    },
    "Total RBC Count": {
        "aliases": [r"total\s+rbc\s+count", r"total\s+rbc", r"rbc\s+count", r"red\s+blood\s+cell\s+count", r"(?<!urine\s)\brbc\b(?!\s*\(urine|\s*[\)\/])"],
        "default_unit": "mil/uL",
        "default_range_male": "4.5 - 5.9",
        "default_range_female": "4.0 - 5.2",
        "default_range": "4.0 - 5.9"
    },
    "Packed Cell Volume (PCV)": {
        "aliases": [r"packed\s+cell\s+volume", r"\bpcv\b", r"hematocrit\b", r"\bhct\b"],
        "default_unit": "%",
        "default_range_male": "40.0 - 50.0",
        "default_range_female": "36.0 - 46.0",
        "default_range": "36.0 - 50.0"
    },
    "MCV": {
        "aliases": [r"mean\s+corpuscular\s+volume", r"\bmcv\b"],
        "default_unit": "fL",
        "default_range": "80.0 - 100.0"
    },
    "MCH": {
        "aliases": [r"mean\s+corpuscular\s+hemoglobin\b", r"\bmch\b"],
        "default_unit": "pg",
        "default_range": "27.0 - 33.0"
    },
    "MCHC": {
        "aliases": [r"mean\s+corpuscular\s+hemoglobin\s+concentration", r"\bmchc\b"],
        "default_unit": "g/dL",
        "default_range": "32.0 - 36.0"
    },
    "RDW": {
        "aliases": [r"red\s+cell\s+distribution\s+width", r"rdw\s*[\-\s]*cv", r"\brdw\b"],
        "default_unit": "%",
        "default_range": "11.5 - 14.5"
    },
    "Total Leukocyte Count (WBC)": {
        "aliases": [r"total\s+leukocyte\s+count", r"total\s+wbc\s+count", r"\btlc\b", r"\bwbc\s*count\b", r"(?<!urine\s)\bwbc\b(?!\s*\(urine|\s*[\)\/])", r"white\s+blood\s+cells?"],
        "default_unit": "/uL",
        "default_range": "4000 - 11000"
    },
    "Neutrophils": {
        "aliases": [r"neutrophils?", r"polymorphs?"],
        "default_unit": "%",
        "default_range": "40 - 75"
    },
    "Lymphocytes": {
        "aliases": [r"lymphocytes?"],
        "default_unit": "%",
        "default_range": "20 - 45"
    },
    "Monocytes": {
        "aliases": [r"monocytes?"],
        "default_unit": "%",
        "default_range": "2 - 10"
    },
    "Eosinophils": {
        "aliases": [r"eosinophils?"],
        "default_unit": "%",
        "default_range": "1 - 6"
    },
    "Basophils": {
        "aliases": [r"basophils?"],
        "default_unit": "%",
        "default_range": "0 - 1"
    },
    "Platelet Count": {
        "aliases": [r"platelet\s+count", r"\bplatelets?\b"],
        "default_unit": "/uL",
        "default_range": "150000 - 450000"
    },

    # LFT Parameters
    "Total Bilirubin": {
        "aliases": [r"total\s+bilirubin", r"bilirubin\s+total", r"s\.\s*bilirubin\s*\(total\)"],
        "default_unit": "mg/dL",
        "default_range": "0.2 - 1.2"
    },
    "Direct Bilirubin": {
        "aliases": [r"direct\s+bilirubin", r"conjugated\s+bilirubin", r"bilirubin\s+direct"],
        "default_unit": "mg/dL",
        "default_range": "0.0 - 0.3"
    },
    "Indirect Bilirubin": {
        "aliases": [r"indirect\s+bilirubin", r"unconjugated\s+bilirubin"],
        "default_unit": "mg/dL",
        "default_range": "0.2 - 0.8"
    },
    "SGOT / AST": {
        "aliases": [r"sgot\s*[\/\-]?\s*ast", r"\bsgot\b", r"\bast\b", r"aspartate\s+aminotransferase"],
        "default_unit": "U/L",
        "default_range": "5 - 40"
    },
    "SGPT / ALT": {
        "aliases": [r"sgpt\s*[\/\-]?\s*alt", r"\bsgpt\b", r"\balt\b", r"alanine\s+aminotransferase", r"alanine\s+transaminase"],
        "default_unit": "U/L",
        "default_range": "7 - 56"
    },
    "Alkaline Phosphatase (ALP)": {
        "aliases": [r"alkaline\s+phosphatase", r"\balp\b", r"\bsalp\b"],
        "default_unit": "U/L",
        "default_range": "44 - 147"
    },
    "Total Protein": {
        "aliases": [r"total\s+protein", r"protein\s+total"],
        "default_unit": "g/dL",
        "default_range": "6.0 - 8.3"
    },
    "Albumin": {
        "aliases": [r"serum\s+albumin", r"(?<!urine\s)(?<!\/\s)\balbumin\b(?!\s*\(urine)"],
        "default_unit": "g/dL",
        "default_range": "3.5 - 5.2"
    },
    "Globulin": {
        "aliases": [r"serum\s+globulin", r"(?<!\/\s)\bglobulin\b"],
        "default_unit": "g/dL",
        "default_range": "2.0 - 3.5"
    },
    "A/G Ratio": {
        "aliases": [r"a\s*[\/\:]\s*g\s+ratio", r"albumin\s*[\/\-:]\s*globulin\s+ratio", r"a\/g\b"],
        "default_unit": "ratio",
        "default_range": "1.0 - 2.2"
    },
    "GGT": {
        "aliases": [r"gamma\s+glutamyl\s+transferase", r"\bggt\b|\bggtp\b"],
        "default_unit": "U/L",
        "default_range": "9 - 48"
    },

    # KFT Parameters
    "Serum Creatinine": {
        "aliases": [r"serum\s+creatinine", r"\bcreatinine\b"],
        "default_unit": "mg/dL",
        "default_range_male": "0.7 - 1.3",
        "default_range_female": "0.6 - 1.1",
        "default_range": "0.6 - 1.3"
    },
    "Blood Urea Nitrogen (BUN)": {
        "aliases": [r"blood\s+urea\s+nitrogen", r"\bbun\b"],
        "default_unit": "mg/dL",
        "default_range": "7 - 20"
    },
    "Blood Urea": {
        "aliases": [r"blood\s+urea\b", r"\bserum\s+urea\b", r"\burea\b(?!\s*nitrogen)"],
        "default_unit": "mg/dL",
        "default_range": "15 - 45"
    },
    "Uric Acid": {
        "aliases": [r"serum\s+uric\s+acid", r"uric\s+acid"],
        "default_unit": "mg/dL",
        "default_range_male": "3.5 - 7.2",
        "default_range_female": "2.6 - 6.0",
        "default_range": "2.6 - 7.2"
    },
    "eGFR": {
        "aliases": [r"egfr\b", r"estimated\s+gfr", r"glomerular\s+filtration\s+rate"],
        "default_unit": "mL/min/1.73m2",
        "default_range": "> 90"
    },

    # Lipid Profile
    "TC / HDL Ratio": {
        "aliases": [r"cholesterol\s*[\/\-:]\s*hdl\s*ratio", r"tc\s*[\/]\s*hdl\s*ratio", r"tc\s*[\/]\s*hdl\b"],
        "default_unit": "ratio",
        "default_range": "< 4.5"
    },
    "Total Cholesterol": {
        "aliases": [r"total\s+cholesterol", r"cholesterol\s+total", r"\bcholesterol\b(?!\s*\/)"],
        "default_unit": "mg/dL",
        "default_range": "< 200"
    },
    "Triglycerides": {
        "aliases": [r"serum\s+triglycerides?", r"triglycerides?", r"\btg\b"],
        "default_unit": "mg/dL",
        "default_range": "< 150"
    },
    "HDL Cholesterol": {
        "aliases": [r"hdl\s+cholesterol", r"high\s+density\s+lipoprotein", r"(?<!tc\s\/\s)(?<!tc\/)\bhdl\b(?!\s*ratio|\s*\/)"],
        "default_unit": "mg/dL",
        "default_range_male": "> 40",
        "default_range_female": "> 50",
        "default_range": "> 40"
    },
    "LDL Cholesterol": {
        "aliases": [r"ldl\s+cholesterol", r"\bldl\b", r"low\s+density\s+lipoprotein"],
        "default_unit": "mg/dL",
        "default_range": "< 100"
    },
    "VLDL Cholesterol": {
        "aliases": [r"vldl\s+cholesterol", r"\bvldl\b"],
        "default_unit": "mg/dL",
        "default_range": "5 - 30"
    },

    # Thyroid Profile
    "Free T3": {
        "aliases": [r"free\s+triiodothyronine", r"free\s+t3", r"\bft3\b"],
        "default_unit": "pg/mL",
        "default_range": "2.0 - 4.4"
    },
    "Free T4": {
        "aliases": [r"free\s+thyroxine", r"free\s+t4", r"\bft4\b"],
        "default_unit": "ng/dL",
        "default_range": "0.93 - 1.70"
    },
    "Total T3": {
        "aliases": [r"total\s+triiodothyronine", r"total\s+t3", r"(?<!free\s)\bt3\b\s*total", r"(?<!free\s)\bt3\b"],
        "default_unit": "ng/dL",
        "default_range": "80 - 200"
    },
    "Total T4": {
        "aliases": [r"total\s+thyroxine", r"total\s+t4", r"(?<!free\s)\bt4\b\s*total", r"(?<!free\s)\bt4\b"],
        "default_unit": "ug/dL",
        "default_range": "5.1 - 14.1"
    },
    "TSH": {
        "aliases": [r"thyroid\s+stimulating\s+hormone", r"s\.\s*tsh", r"\btsh\b"],
        "default_unit": "uIU/mL",
        "default_range": "0.35 - 4.94"
    },

    # Blood Sugar / Glucose
    "Fasting Blood Sugar (FBS)": {
        "aliases": [r"fasting\s+blood\s+sugar", r"fasting\s+blood\s+glucose", r"\bfbs\b", r"glucose\s*[\-\s]*fasting"],
        "default_unit": "mg/dL",
        "default_range": "70 - 99"
    },
    "Post Prandial Blood Sugar (PPBS)": {
        "aliases": [r"post\s+prandial\s+blood\s+sugar", r"post\s+prandial\s+blood\s+glucose", r"\bppbs\b", r"glucose\s*[\-\s]*post\s*prandial"],
        "default_unit": "mg/dL",
        "default_range": "70 - 140"
    },
    "Random Blood Sugar (RBS)": {
        "aliases": [r"random\s+blood\s+sugar", r"random\s+blood\s+glucose", r"\brbs\b", r"glucose\s*[\-\s]*random"],
        "default_unit": "mg/dL",
        "default_range": "70 - 140"
    },
    "HbA1c": {
        "aliases": [r"glycated\s+hemoglobin", r"glycosylated\s+hemoglobin", r"\bhba1c\b"],
        "default_unit": "%",
        "default_range": "< 5.7"
    },

    # Vitamins
    "Vitamin B12": {
        "aliases": [r"vitamin\s+b12", r"vit\s+b12", r"cyanocobalamin", r"serum\s+b12"],
        "default_unit": "pg/mL",
        "default_range": "211 - 911"
    },
    "Vitamin D (25-OH)": {
        "aliases": [r"25\s*[\-\s]*hydroxy\s*vitamin\s*d", r"25\s*[\-\s]*oh\s*vit(amin)?\s*d", r"vitamin\s+d\b", r"vit\s+d\b"],
        "default_unit": "ng/mL",
        "default_range": "30 - 100"
    },

    # Electrolytes
    "Serum Sodium": {
        "aliases": [r"serum\s+sodium", r"sodium\b", r"\bna\+\b"],
        "default_unit": "mEq/L",
        "default_range": "136 - 145"
    },
    "Serum Potassium": {
        "aliases": [r"serum\s+potassium", r"potassium\b", r"\bk\+\b"],
        "default_unit": "mEq/L",
        "default_range": "3.5 - 5.1"
    },
    "Serum Chloride": {
        "aliases": [r"serum\s+chloride", r"chloride\b", r"\bcl\-\b"],
        "default_unit": "mEq/L",
        "default_range": "96 - 106"
    },
    "Serum Calcium": {
        "aliases": [r"serum\s+calcium", r"total\s+calcium", r"\bcalcium\b"],
        "default_unit": "mg/dL",
        "default_range": "8.5 - 10.5"
    },

    # Urine Routine
    "Urine Specific Gravity": {
        "aliases": [r"urine\s+specific\s+gravity", r"specific\s+gravity", r"sp\.\s*gravity", r"sp\.\s*gr\b"],
        "default_unit": "",
        "default_range": "1.005 - 1.030"
    },
    "Urine pH / Reaction": {
        "aliases": [r"urine\s+ph\s*[\/\-:]\s*reaction", r"urine\s+reaction", r"urine\s+ph\b", r"reaction\s*\/ph", r"reaction\b", r"\bph\b"],
        "default_unit": "",
        "default_range": "4.5 - 8.0"
    },
    "Urine Protein / Albumin": {
        "aliases": [r"urine\s+protein\s*[\/\-:]\s*albumin", r"urine\s+protein", r"protein\s*\(urine\)", r"urine\s+albumin", r"albumin\s*\(urine\)"],
        "default_unit": "",
        "default_range": "Nil / Negative"
    },
    "Urine Glucose / Sugar": {
        "aliases": [r"urine\s+glucose\s*[\/\-:]\s*sugar", r"urine\s+glucose", r"glucose\s*\(urine\)", r"urine\s+sugar", r"sugar\s*\(urine\)"],
        "default_unit": "",
        "default_range": "Nil / Negative"
    },
    "Urine Pus Cells (WBC)": {
        "aliases": [r"urine\s+pus\s+cells?(\s*\([^\)]*\))?", r"pus\s+cells?(\s*\([^\)]*\))?", r"leukocytes?\s*\(urine\)", r"wbc\s*\(urine\)"],
        "default_unit": "/HPF",
        "default_range": "0 - 5"
    },
    "Urine RBCs": {
        "aliases": [r"urine\s+rbcs?(\s*\([^\)]*\))?", r"red\s+blood\s+cells?\s*\(urine\)", r"rbc\s*\(urine\)"],
        "default_unit": "/HPF",
        "default_range": "0 - 2"
    },
    "Urine Epithelial Cells": {
        "aliases": [r"urine\s+epithelial\s+cells?", r"epithelial\s+cells?"],
        "default_unit": "/HPF",
        "default_range": "0 - 5"
    },
    "Urine Ketone Bodies": {
        "aliases": [r"urine\s+ketone\s+bodies", r"urine\s+ketones?", r"ketone\s+bodies", r"\bketones?\b"],
        "default_unit": "",
        "default_range": "Negative"
    },
    "Urobilinogen": {
        "aliases": [r"urobilinogen\b"],
        "default_unit": "mg/dL",
        "default_range": "0.1 - 1.0"
    },

    # Other Common Laboratory Tests
    "ESR (Erythrocyte Sedimentation Rate)": {
        "aliases": [r"erythrocyte\s+sedimentation\s+rate", r"\besr\b"],
        "default_unit": "mm/hr",
        "default_range_male": "0 - 15",
        "default_range_female": "0 - 20",
        "default_range": "0 - 20"
    },
    "C-Reactive Protein (CRP)": {
        "aliases": [r"c[\-\s]*reactive\s+protein", r"\bcrp\b"],
        "default_unit": "mg/L",
        "default_range": "< 6.0"
    },
    "Serum Ferritin": {
        "aliases": [r"serum\s+ferritin", r"ferritin\b"],
        "default_unit": "ng/mL",
        "default_range_male": "24 - 336",
        "default_range_female": "11 - 307",
        "default_range": "15 - 300"
    }
}

HEADER_WORDS_TO_SKIP = [
    "test parameter", "observed value", "biological reference", "reference range",
    "department of", "clinical pathology", "metropolitan clinical", "healthcare boulevard",
    "referred by", "sample type", "sample id", "verified by", "page 1", "end of report",
    "patient name", "patient id", "report date", "age / sex", "hospital billing",
    "billing invoice", "discharge receipt", "room charges", "surgical consultation",
    "total paid"
]

def extract_patient_information(text: str) -> Tuple[PatientInformation, Optional[str], Optional[str]]:
    """
    Extracts patient demographics, date, and lab name from report text.
    Returns: (PatientInformation, report_date, lab_name)
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    info = PatientInformation()
    report_date = None
    lab_name = None

    # 1. Lab name extraction
    lab_keywords = ["pathology", "diagnostic", "diagnostics", "laboratory", "hospital", "healthcare", "clinic", "clinical lab"]
    for i, line in enumerate(lines[:10]):
        line_lower = line.lower()
        if any(kw in line_lower for kw in lab_keywords) and not line_lower.startswith("department") and not "patient" in line_lower:
            cleaned_lab = re.sub(r"^(welcome to|report from)\s*", "", line, flags=re.I).strip()
            if len(cleaned_lab) > 4 and len(cleaned_lab) < 70:
                lab_name = cleaned_lab
                info.lab_name = lab_name
                break

    # 2. Patient Name
    name_patterns = [
        r"(?:patient\s*name|pt\.?\s*name|pat[il1]ent\s*name|name)\s*[:\-\|]\s*(?:mr\.|mrs\.|ms\.|dr\.|master|baby)?\s*([A-Za-z\s\.\']{2,40})",
        r"(?:patient|pat[il1]ent)\s*[:\-\|]\s*([A-Za-z\s\.\']{2,40})",
        r"^(?:mr\.|mrs\.|ms\.|dr\.)\s+([A-Za-z\s]{3,35})"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            candidate = match.group(1).strip()
            # Clean up trailing tokens often on same line
            candidate = re.split(r"(?:Pat[il1]ent\s*ID|PID|UHID|Reg\s*No|MRN|Ref\s*No|Age|Sex|Gender|Date|Dr\b|Sample)", candidate, flags=re.I)[0].strip()
            candidate = candidate.split("\n")[0].strip()
            if candidate and len(candidate) > 2 and not any(ch in candidate for ch in [";", "$", "%"]):
                info.name = candidate
                break

    # 3. Age & Gender
    combined_age_gender = re.search(
        r"(?:age\s*[\/\&]\s*(?:gender|sex))\s*[:\-\|]?\s*(\d{1,3})\s*(?:y(?:ears|rs)?)?\s*[\/\-]\s*(male|female|m|f)\b",
        text,
        re.IGNORECASE
    )
    if combined_age_gender:
        info.age = combined_age_gender.group(1)
        gender_raw = combined_age_gender.group(2).upper()
        info.gender = "Male" if gender_raw.startswith("M") else "Female"
    else:
        # Separate age
        age_match = re.search(r"\b(?:age)\s*[:\-\|]?\s*(\d{1,3})\s*(?:y(?:ears|rs)?|months?)?", text, re.IGNORECASE)
        if not age_match:
            age_match = re.search(r"\b(\d{1,3})\s*(?:years|yrs|y\/o)\b", text, re.IGNORECASE)
        if age_match:
            info.age = age_match.group(1)

        # Separate gender
        gender_match = re.search(r"\b(?:gender|sex)\s*[:\-\|]?\s*(male|female|other|m|f)\b", text, re.IGNORECASE)
        if gender_match:
            g_raw = gender_match.group(1).upper()
            info.gender = "Male" if g_raw.startswith("M") else ("Female" if g_raw.startswith("F") else "Other")

    # 4. Patient ID / UHID / Reg No / MRN
    id_patterns = [
        r"(?:pat[il1]ent\s*id|pid|uhid|mrn|reg\s*no|ref\s*no|sample\s*id|lab\s*id)\s*[:\-\|]?\s*([A-Za-z0-9\-]+)",
        r"(?:barcode\s*no)\s*[:\-\|]?\s*([0-9A-Z]+)"
    ]
    for pattern in id_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            cand_id = match.group(1).strip()
            if cand_id and len(cand_id) > 2:
                info.patient_id = cand_id
                break

    # 5. Report Date Extraction (Prioritizes explicit clinical report labels; never falls back to upload date)
    # High-priority explicit report date labels (restricted to single line to prevent matching into next line)
    explicit_date_patterns = [
        r"(?:report\s*date|date\s*of\s*report|reported\s*on|dated|date\s*of\s*issue|test\s*date|reporting\s*date)\s*[:\-\|]?\s*([0-9A-Za-z\t /\-\.,]{6,25})",
        r"(?:collection\s*date|date\s*of\s*collection|sample\s*collected(?:\s*on)?|specimen\s*date|registered\s*on|registration\s*date)\s*[:\-\|]?\s*([0-9A-Za-z\t /\-\.,]{6,25})",
        r"(?:^|\n)\s*date\s*[:\-\|]\s*([0-9A-Za-z\t /\-\.,]{6,25})"
    ]
    
    # Standalone date patterns (fallback if no explicit label)
    standalone_date_patterns = [
        r"\b(\d{1,2}[/\-\.](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[/\-\.]\d{2,4})\b",
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b",
        r"\b(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})\b",
        r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})\b"
    ]

    # Try explicit patterns first
    for pattern in explicit_date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            cand = match.group(1).split("\n")[0].split("\r")[0].strip().rstrip(".,;")
            # Ensure not capturing administrative trailing text
            cand = re.split(r"(?:patient|age|sex|doctor|ref|sample|hospital|page)", cand, flags=re.I)[0].strip()
            if len(cand) >= 6:
                report_date = cand
                break

    # If no explicit label matched, check standalone patterns avoiding DOB / Birth lines
    if not report_date:
        for line in lines:
            line_lower = line.lower()
            if "dob" in line_lower or "birth" in line_lower:
                continue
            for pattern in standalone_date_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    report_date = match.group(1).strip()
                    break
            if report_date:
                break

    return info, report_date, lab_name

def parse_line_for_test(line: str, patient_gender: Optional[str] = None) -> Optional[TestResult]:
    """
    Attempts to match a single line against the clinical test dictionary
    using combined Regex and RapidFuzz (Requirement 6).
    """
    line_clean = line.strip()
    if len(line_clean) < 3:
        return None

    line_lower = line_clean.lower()
    if any(skip_word in line_lower for skip_word in HEADER_WORDS_TO_SKIP):
        return None

    is_urine_line = "urine" in line_lower

    # Sort tests with longer aliases first, and prioritize urine tests if urine is in the line
    def sort_key(item):
        name, spec = item
        max_alias_len = max(len(a) for a in spec["aliases"])
        is_urine_test = name.startswith("Urine")
        priority = 1000 if (is_urine_line and is_urine_test) else (0 if (not is_urine_line and is_urine_test) else 500)
        return priority + max_alias_len

    sorted_tests = sorted(TEST_DICTIONARY.items(), key=sort_key, reverse=True)

    matched_test, matched_spec, sub_str = None, None, ""

    # 1. Direct Regex match
    for test_name, spec in sorted_tests:
        for alias in spec["aliases"]:
            match = re.search(rf"\b{alias}\b", line_clean, re.IGNORECASE)
            if match:
                matched_test = test_name
                matched_spec = spec
                sub_str = line_clean[match.end():].strip()
                break
        if matched_test:
            break

    # 2. RapidFuzz fuzzy match fallback for OCR typos (e.g. srumCiealinina, Blad Urea, PlateletCount)
    if not matched_test:
        tokens = line_clean.split()
        best_score = 0.0
        for n in range(min(5, len(tokens)), 0, -1):
            prefix = " ".join(tokens[:n]).lower()
            if any(ch.isdigit() for ch in prefix):
                continue
            for test_name, spec in sorted_tests:
                for alias in spec["aliases"]:
                    clean_a = re.sub(r"\\[a-zA-Z]+|[^\w\s]", " ", alias)
                    clean_a = re.sub(r"\s+", " ", clean_a).strip().lower()
                    if len(clean_a) >= 4:
                        score = fuzz.WRatio(prefix, clean_a)
                        if score >= 70.0 and score > best_score:
                            best_score = score
                            matched_test = test_name
                            matched_spec = spec
                            sub_str = " ".join(tokens[n:]).strip()

    if not matched_test or not matched_spec:
        return None

    # Clean leading brackets / punctuation or OCR noise before the value
    sub_str = re.sub(r"^[\s\(\[\{/:\-]+(?:[A-Za-z0-9]{1,5}[\)\]\}])?\s*", "", sub_str).strip()
    if not sub_str:
        return None

    flag = None
    if re.search(r"(\bHIGH\b|\bH\b|\*H\*|\bH\*|He»|He|Ha)", sub_str, re.IGNORECASE):
        flag = "HIGH"
    elif re.search(r"(\bLOW\b|\bL\b|\*L\*|\bL\*|Le)", sub_str, re.IGNORECASE):
        flag = "LOW"
    elif "*" in sub_str:
        flag = "Abnormal"

    # Extract numerical or qualitative value
    vm = re.search(
        r"\b((?:[<>]=?\s*)?\d+(?:[\.,]\d+)?(?:\s*-\s*\d+(?:[\.,]\d+)?)?|Positive|Negative|Trace|Nil|Present|Absent|Reactive|Non[\-\s]Reactive|Clear|Cloudy|Straw|Yellow|Amber)\b",
        sub_str,
        re.IGNORECASE
    )
    if not vm:
        return None

    val = vm.group(1).strip()
    rem = sub_str[vm.end():].strip()

    # Extract reference range
    ref_range = ""
    range_match = re.search(
        r"((?:<\s*|>\s*|<=|>=)?\d+(?:[\.,]\d+)?\s*(?:-|–|to)\s*\d+(?:[\.,]\d+)?|<=\s*\d+(?:[\.,]\d+)?|>=\s*\d+(?:[\.,]\d+)?|<\s*\d+(?:[\.,]\d+)?|>\s*\d+(?:[\.,]\d+)?|up\s+to\s+\d+(?:[\.,]\d+)?|Nil\s*[\/\-]?\s*Negative|Negative|Nil|Absent|Normal)",
        rem,
        re.IGNORECASE
    )
    if range_match:
        ref_range = range_match.group(1).strip()

    # Extract unit
    raw_unit = ""
    unit_patterns = [
        r"\b(g[\/\.]?dL|gidl|mg[\/\.]?dL|mgdl|\/uL|ful|lul|ul|\/cumm|\/mm3|mil[\/\.]?uL|milful|mil\/cumm|fL|pg|%|uIU\/mL|uIU\/L|mIU\/mL|ng\/mL|ng\/dL|pg\/mL|mmol\/L|mEq\/L|U\/L|UIL|un|iu\/l|mL[\w\/\.]*|\/HPF|\/hpf|mm\/hr|ratio)\b"
    ]
    for up in unit_patterns:
        u_match = re.search(up, rem, re.IGNORECASE)
        if u_match:
            raw_unit = u_match.group(1).strip()
            break

    unit = normalize_medical_unit(raw_unit, matched_spec.get("default_unit", ""))

    # Restore decimals and normalize commas
    val, ref_range = restore_medical_decimals(matched_test, val, ref_range)

    if not ref_range:
        if patient_gender and patient_gender.lower().startswith("m") and "default_range_male" in matched_spec:
            ref_range = matched_spec["default_range_male"]
        elif patient_gender and patient_gender.lower().startswith("f") and "default_range_female" in matched_spec:
            ref_range = matched_spec["default_range_female"]
        else:
            ref_range = matched_spec.get("default_range", "")

    return TestResult(
        test_name=matched_test,
        value=val,
        unit=unit,
        reference_range=ref_range,
        status="NEEDS REVIEW",
        flag=flag
    )

def extract_imaging_or_written_findings(text: str, report_type: str) -> List[TestResult]:
    """
    Extracts structured parameters or key observational lines from written reports
    (e.g., X-Ray, MRI, CT, ECG) without medical image diagnosis.
    """
    results: List[TestResult] = []
    
    if "ECG" in report_type:
        ecg_metrics = [
            (r"heart\s*rate\s*[:\-]?\s*(\d+)\s*(bpm|beats\/min)?", "Heart Rate", "bpm", "60 - 100"),
            (r"pr\s*interval\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(ms|sec)?", "PR Interval", "ms", "120 - 200"),
            (r"qrs\s*duration\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(ms|sec)?", "QRS Duration", "ms", "80 - 120"),
            (r"qtc\s*(?:interval)?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(ms|sec)?", "QTc Interval", "ms", "350 - 450"),
            (r"rhythm\s*[:\-]?\s*([A-Za-z\s]+)", "Cardiac Rhythm", "", "Sinus Rhythm"),
            (r"impression\s*[:\-]?\s*([^\n\r]+)", "ECG Impression", "", "Normal Study")
        ]
        for pattern, name, unit, default_range in ecg_metrics:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                results.append(TestResult(
                    test_name=name,
                    value=val,
                    unit=unit,
                    reference_range=default_range,
                    status="NORMAL" if "sinus" in val.lower() or "normal" in val.lower() else "NEEDS REVIEW"
                ))

    elif any(term in report_type for term in ["X-Ray", "MRI", "CT"]):
        sections = [
            (r"(?:clinical\s+indication|indication|history)\s*[:\-]\s*([^\n\r]+)", "Clinical Indication"),
            (r"(?:examination|procedure|technique)\s*[:\-]\s*([^\n\r]+)", "Technique / View"),
            (r"(?:findings|observations)\s*[:\-]\s*([^\n\r]+(?:\n[^\n\r]+){0,2})", "Key Findings"),
            (r"(?:impression|conclusion|opinion)\s*[:\-]\s*([^\n\r]+)", "Impression")
        ]
        for pattern, label in sections:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                results.append(TestResult(
                    test_name=label,
                    value=val[:150],
                    unit="",
                    reference_range="Expected finding",
                    status="NORMAL" if any(k in val.lower() for k in ["normal", "unremarkable", "clear", "intact", "no abnormality"]) else "NEEDS REVIEW"
                ))

    return results

def extract_all_parameters(text: str, report_type: str, patient_info: PatientInformation) -> List[TestResult]:
    results: List[TestResult] = []
    seen_tests = set()

    if any(k in report_type for k in ["X-Ray", "MRI", "CT", "ECG"]):
        special_results = extract_imaging_or_written_findings(text, report_type)
        for r in special_results:
            if r.test_name not in seen_tests:
                seen_tests.add(r.test_name)
                results.append(r)

    lines = text.split("\n")
    for line in lines:
        parsed = parse_line_for_test(line, patient_gender=patient_info.gender)
        if parsed and parsed.test_name not in seen_tests:
            seen_tests.add(parsed.test_name)
            results.append(parsed)

    return results
