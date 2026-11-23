import re
from typing import Tuple, Dict, Any, List

REPORT_CATEGORIES = {
    "CBC": {
        "name": "Complete Blood Count (CBC)",
        "titles": [
            r"complete\s+blood\s+(count|picture)",
            r"cbc\b",
            r"hemogram",
            r"haemogram",
            r"full\s+blood\s+count",
            r"fbc\b",
            r"routine\s+blood\s+examination"
        ],
        "keywords": [
            r"hemoglobin\b|haemoglobin\b|\bhb\b",
            r"platelet\s*count|\bplatelets?\b",
            r"total\s+leukocyte\s+count|\btlc\b|\bwbc\b|white\s+blood\s+cells?",
            r"total\s+rbc|\brbc\s*count|\brbc\b|red\s+blood\s+cells?",
            r"hematocrit|\bhct\b|packed\s+cell\s+volume|\bpcv\b",
            r"\bmcv\b|\bmch\b|\bmchc\b|\brdw\b",
            r"neutrophils?|\bpolymorphs?\b",
            r"lymphocytes?",
            r"monocytes?",
            r"eosinophils?",
            r"basophils?",
            r"differential\s+leukocyte\s+count|\bdlc\b"
        ],
        "min_score": 4
    },
    "LFT": {
        "name": "Liver Function Test (LFT)",
        "titles": [
            r"liver\s+function\s+test",
            r"\blft\b",
            r"hepatic\s+panel",
            r"liver\s+panel",
            r"hepatic\s+profile"
        ],
        "keywords": [
            r"total\s+bilirubin|\bbilirubin\b",
            r"direct\s+bilirubin|conjugated\s+bilirubin",
            r"indirect\s+bilirubin|unconjugated\s+bilirubin",
            r"\bsgot\b|\bast\b|aspartate\s+aminotransferase",
            r"\bsgpt\b|\balt\b|alanine\s+transaminase|alanine\s+aminotransferase",
            r"alkaline\s+phosphatase|\balp\b|\bsalp\b",
            r"total\s+protein",
            r"albumin\b",
            r"globulin\b",
            r"a/g\s+ratio|albumin\s*[\/\-:]\s*globulin",
            r"gamma\s+glutamyl|\bggt\b|\bggtp\b"
        ],
        "min_score": 4
    },
    "KFT": {
        "name": "Kidney Function Test (KFT)",
        "titles": [
            r"kidney\s+function\s+test",
            r"renal\s+function\s+test",
            r"\bkft\b|\brft\b",
            r"renal\s+panel",
            r"renal\s+profile"
        ],
        "keywords": [
            r"serum\s+creatinine|\bcreatinine\b",
            r"blood\s+urea|\burea\b",
            r"blood\s+urea\s+nitrogen|\bbun\b",
            r"uric\s+acid",
            r"egfr|estimated\s+gfr|glomerular\s+filtration",
            r"bun\s*[\/\-:]\s*creatinine\s*ratio"
        ],
        "min_score": 3
    },
    "Lipid Profile": {
        "name": "Lipid Profile",
        "titles": [
            r"lipid\s+profile",
            r"lipid\s+panel",
            r"coronary\s+risk\s+panel",
            r"cholesterol\s+profile"
        ],
        "keywords": [
            r"total\s+cholesterol|\bcholesterol\b",
            r"triglycerides?|\btg\b",
            r"hdl\s+cholesterol|\bhdl\b|high\s+density\s+lipoprotein",
            r"ldl\s+cholesterol|\bldl\b|low\s+density\s+lipoprotein",
            r"vldl\s+cholesterol|\bvldl\b",
            r"cholesterol\s*[\/\-:]\s*hdl\s*ratio|tc\s*[\/]\s*hdl",
            r"non\s*[\-\s]hdl\s+cholesterol"
        ],
        "min_score": 4
    },
    "Thyroid Profile": {
        "name": "Thyroid Profile",
        "titles": [
            r"thyroid\s+profile",
            r"thyroid\s+function\s+test",
            r"\btft\b",
            r"thyroid\s+panel"
        ],
        "keywords": [
            r"thyroid\s+stimulating\s+hormone|\btsh\b|\bs\.tsh\b",
            r"total\s+triiodothyronine|total\s+t3|\bt3\b\s*(total)?",
            r"total\s+thyroxine|total\s+t4|\bt4\b\s*(total)?",
            r"free\s+t3|\bft3\b|free\s+triiodothyronine",
            r"free\s+t4|\bft4\b|free\s+thyroxine"
        ],
        "min_score": 3
    },
    "Urine Routine": {
        "name": "Urine Routine Examination",
        "titles": [
            r"urine\s+routine",
            r"urine\s+complete",
            r"urinalysis",
            r"urine\s+examination",
            r"urine\s+r\/m|urine\s+re"
        ],
        "keywords": [
            r"specific\s+gravity|\bsp\.\s*gr\b",
            r"urine\s+reaction|\bph\b",
            r"urine\s+protein|albumin\s*\(urine\)",
            r"urine\s+glucose|sugar\s*\(urine\)",
            r"pus\s+cells|leukocytes?\s*\(urine\)",
            r"red\s+blood\s+cells?|rbc\s*\(urine\)",
            r"epithelial\s+cells",
            r"casts\b",
            r"crystals\b",
            r"urobilinogen",
            r"ketone\s+bodies|\bketones?\b",
            r"bile\s+salts|bile\s+pigments"
        ],
        "min_score": 4
    },
    "Blood Sugar": {
        "name": "Blood Sugar / Glucose Profile",
        "titles": [
            r"blood\s+glucose",
            r"blood\s+sugar",
            r"glycemic\s+profile",
            r"diabetic\s+profile",
            r"glucose\s+tolerance"
        ],
        "keywords": [
            r"fasting\s+blood\s+(sugar|glucose)|\bfbs\b",
            r"post\s+prandial\s+blood\s+(sugar|glucose)|\bppbs\b",
            r"random\s+blood\s+(sugar|glucose)|\brbs\b",
            r"glycated\s+hemoglobin|glycosylated\s+hemoglobin|\bhba1c\b",
            r"average\s+blood\s+glucose|\beag\b"
        ],
        "min_score": 3
    },
    "Vitamin B12": {
        "name": "Vitamin B12 Report",
        "titles": [
            r"vitamin\s+b12",
            r"vit\s+b12",
            r"cobalamin\s+assay",
            r"cyanocobalamin"
        ],
        "keywords": [
            r"vitamin\s+b12|\bvit\s*b\-?12\b",
            r"cyanocobalamin",
            r"serum\s+b12",
            r"methylmalonic\s+acid"
        ],
        "min_score": 2
    },
    "Vitamin D": {
        "name": "Vitamin D Report",
        "titles": [
            r"vitamin\s+d\b",
            r"vit\s+d\b",
            r"25[\s\-]hydroxy\s+vitamin\s+d",
            r"25[\s\-]oh\s+vitamin\s+d"
        ],
        "keywords": [
            r"25\s*[\-\s]\s*hydroxy\s*vitamin\s*d",
            r"25\s*[\-\s]\s*oh\s*vit(amin)?\s*d",
            r"cholecalciferol",
            r"calcidiol",
            r"vitamin\s+d3?"
        ],
        "min_score": 2
    },
    "Electrolytes": {
        "name": "Serum Electrolytes",
        "titles": [
            r"serum\s+electrolytes",
            r"electrolytes?\s+panel",
            r"electrolyte\s+profile"
        ],
        "keywords": [
            r"serum\s+sodium|\bsodium\b|\bna\+\b|\bna\b\s*\(sodium\)",
            r"serum\s+potassium|\bpotassium\b|\bk\+\b|\bk\b\s*\(potassium\)",
            r"serum\s+chloride|\bchloride\b|\bcl\-\b|\bcl\b\s*\(chloride\)",
            r"bicarbonate|\bhco3\b",
            r"ionic\s+calcium|calcium\b"
        ],
        "min_score": 3
    },
    "X-Ray Report": {
        "name": "X-Ray Written Report",
        "titles": [
            r"x\s*[\-\s]*ray",
            r"radiograph(y|ic)?",
            r"roentgenogram",
            r"chest\s+x[\-\s]*ray"
        ],
        "keywords": [
            r"pa\s+view|ap\s+view|lateral\s+view",
            r"costophrenic\s+angles?",
            r"cardiothoracic\s+ratio|\bctr\b",
            r"bony\s+cage|bony\s+thorax",
            r"lung\s+fields|bronchovascular\s+markings",
            r"hilar\s+shadows?",
            r"radiological\s+impression|findings\s*:\s*"
        ],
        "min_score": 3
    },
    "MRI Report": {
        "name": "MRI Written Report",
        "titles": [
            r"magnetic\s+resonance\s+imaging",
            r"\bmri\b\s+(brain|spine|knee|pelvis|abdomen|scan)?",
            r"mr\s+imaging"
        ],
        "keywords": [
            r"t1\s+weighted|t2\s+weighted|\bflair\b",
            r"axial|sagittal|coronal\s+sections",
            r"diffusion\s+weighted|\bdwi\b|\badc\b",
            r"gadolinium\s+contrast|contrast\s+enhancement",
            r"spin\s+echo|mri\s+findings"
        ],
        "min_score": 3
    },
    "CT Scan Report": {
        "name": "CT Scan Written Report",
        "titles": [
            r"computed\s+tomography",
            r"\bct\s+scan\b",
            r"\bcect\b|\bncct\b|\bhrct\b"
        ],
        "keywords": [
            r"slice\s+thickness",
            r"hounsfield\s+units?|\bhu\b",
            r"non\s*[\-\s]contrast|contrast\s+enhanced",
            r"axial\s+scans?|spiral\s+ct",
            r"parenchyma|attenuation|hypodense|hyperdense",
            r"ct\s+findings|scan\s+impression"
        ],
        "min_score": 3
    },
    "ECG Report": {
        "name": "ECG Written Report",
        "titles": [
            r"electrocardiogram",
            r"\becg\b|\bekg\b",
            r"12\s+lead\s+ecg"
        ],
        "keywords": [
            r"sinus\s+rhythm|normal\s+sinus",
            r"pr\s+interval",
            r"qrs\s+complex|qrs\s+duration",
            r"qt\s*[\/\-:]\s*qtc|qtc\s+interval",
            r"st\s+segment|t\s+wave\s+inversion",
            r"heart\s+rate|beats\s+per\s+minute|\bbpm\b",
            r"axis\s+deviation|ventricular\s+rate"
        ],
        "min_score": 3
    },
    "Other Laboratory": {
        "name": "Other Laboratory Report",
        "titles": [
            r"laboratory\s+report",
            r"pathology\s+report",
            r"clinical\s+chemistry",
            r"serology\s+report"
        ],
        "keywords": [
            r"erythrocyte\s+sedimentation\s+rate|\besr\b",
            r"c\s*[\-\s]reactive\s+protein|\bcrp\b",
            r"serum\s+ferritin|\bferritin\b",
            r"total\s+iron\s+binding\s+capacity|\btibc\b",
            r"prothrombin\s+time|\bpt\b\s*\/|\binr\b"
        ],
        "min_score": 2
    }
}

def classify_report(text: str) -> Tuple[str, str, float]:
    """
    Classify medical report text using multi-criteria weighted regex pattern matching.
    
    Returns:
        tuple: (short_type, full_display_name, confidence_score)
        e.g. ("CBC", "Complete Blood Count (CBC)", 0.85)
    """
    if not text or len(text.strip()) < 15:
        return "Unknown / Unclassified", "Unknown or Unclassified Report", 0.0

    lower_text = text.lower()
    best_category = "Unknown / Unclassified"
    best_display_name = "Unknown or Unclassified Report"
    highest_score = 0
    max_possible_score = 10

    for cat_key, cat_data in REPORT_CATEGORIES.items():
        score = 0
        
        # 1. Title matches (highest weight: 5 points)
        for title_pattern in cat_data["titles"]:
            if re.search(title_pattern, lower_text, re.IGNORECASE):
                score += 5
                break  # Don't double count multiple titles for same category

        # 2. Key test parameter matches (2 points per matched keyword pattern)
        matched_keywords = 0
        for kw_pattern in cat_data["keywords"]:
            if re.search(kw_pattern, lower_text, re.IGNORECASE):
                score += 2
                matched_keywords += 1

        # Check if exceeds threshold and requires at least title or multiple keywords
        min_score = cat_data.get("min_score", 3)
        if score >= min_score and score > highest_score:
            highest_score = score
            best_category = cat_key
            best_display_name = cat_data["name"]

    confidence = min(round(highest_score / max_possible_score, 2), 1.0) if highest_score > 0 else 0.0
    return best_category, best_display_name, confidence
