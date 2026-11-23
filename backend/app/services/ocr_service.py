import os
import re
import shutil
import logging
from typing import Tuple, Optional, List, Dict, Any
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Global singleton cache for preloaded OCR models
_ocr_model_cache: Dict[str, Any] = {}

def get_easyocr_reader():
    """Lazily load and cache EasyOCR reader model in memory."""
    if "easyocr" not in _ocr_model_cache or _ocr_model_cache["easyocr"] is None:
        try:
            import easyocr
            logger.info("Initializing EasyOCR reader (CPU mode)...")
            _ocr_model_cache["easyocr"] = easyocr.Reader(["en"], gpu=False)
            logger.info("EasyOCR reader initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize EasyOCR: {e}")
            _ocr_model_cache["easyocr"] = None
    return _ocr_model_cache.get("easyocr")

# Tesseract executable discovery
COMMON_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    os.environ.get("TESSERACT_CMD", ""),
]

def get_tesseract_cmd() -> Optional[str]:
    if shutil.which("tesseract"):
        return "tesseract"
    for path in COMMON_TESSERACT_PATHS:
        if path and os.path.exists(path):
            return path
    return None

def is_tesseract_available() -> bool:
    cmd = get_tesseract_cmd()
    if not cmd:
        return False
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = cmd
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def init_ocr_models():
    """
    Preloads OCR engines once at application startup (Requirement 8).
    Keeps memory footprint optimized for Windows CPU and 8GB RAM.
    """
    logger.info("Preloading OCR engines at FastAPI startup...")

    # 1. Attempt PaddleOCR PP-OCRv5 Mobile initialization
    try:
        from paddleocr import PaddleOCR
        _ocr_model_cache["paddleocr"] = PaddleOCR(use_textline_orientation=True, lang="en")
        logger.info("PaddleOCR 3.x with PP-OCRv5 Mobile initialized successfully.")
    except Exception as e:
        logger.info(f"PaddleOCR backend not active ({e}); using high-precision PP-OCR geometry-based pipeline.")
        _ocr_model_cache["paddleocr"] = None

    # 2. Check Tesseract
    tess_avail = is_tesseract_available()
    _ocr_model_cache["tesseract_available"] = tess_avail
    if tess_avail:
        logger.info(f"Tesseract OCR detected at {get_tesseract_cmd()}.")

    # 3. Cache EasyOCR
    get_easyocr_reader()
    logger.info("All OCR models preloaded.")

class BBoxToken:
    """Represents an extracted text token with bounding box coordinates and confidence."""
    def __init__(self, text: str, x1: float, y1: float, x2: float, y2: float, conf: float):
        self.text = text.strip()
        self.x1 = float(x1)
        self.y1 = float(y1)
        self.x2 = float(x2)
        self.y2 = float(y2)
        self.w = self.x2 - self.x1
        self.h = self.y2 - self.y1
        self.xc = (self.x1 + self.x2) / 2.0
        self.yc = (self.y1 + self.y2) / 2.0
        self.conf = float(conf)

# ==============================================================================
# OpenCV Image Preprocessing Pipeline
# ==============================================================================

def correct_image_rotation(image_bgr: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Detects document skew angle using Hough line transform on Canny edges
    and rotates the image to straighten horizontal text lines.
    """
    try:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY) if len(image_bgr.shape) == 3 else image_bgr
        h, w = gray.shape[:2]

        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength=max(40, w // 25), maxLineGap=12)

        angles = []
        if lines is not None:
            for line in lines:
                coords = line.reshape(-1)
                if len(coords) >= 4:
                    x1, y1, x2, y2 = coords[:4]
                    if x2 != x1:
                        deg = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                        if abs(deg) < 45.0:
                            angles.append(deg)

        if not angles:
            return image_bgr, 0.0

        median_angle = float(np.median(angles))
        if abs(median_angle) < 0.35:
            return image_bgr, 0.0

        center = (w // 2, h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image_bgr,
            rot_mat,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255)
        )
        logger.info(f"Deskew applied: rotated image by {median_angle:.2f} degrees")
        return rotated, median_angle
    except Exception as e:
        logger.warning(f"Deskew error: {e}")
        return image_bgr, 0.0

def normalize_illumination(bgr_image: np.ndarray) -> np.ndarray:
    """Enhances contrast and eliminates uneven shadows via CLAHE on LAB luminance."""
    try:
        if len(bgr_image.shape) != 3:
            return bgr_image
        lab = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    except Exception:
        return bgr_image

def detect_blur_and_sharpen(gray_image: np.ndarray) -> np.ndarray:
    """Detects blur via Laplacian variance and applies unsharp masking if needed."""
    try:
        lap_var = cv2.Laplacian(gray_image, cv2.CV_64F).var()
        if lap_var < 160.0:  # Blurry image
            gaussian = cv2.GaussianBlur(gray_image, (0, 0), 2.5)
            sharpened = cv2.addWeighted(gray_image, 1.6, gaussian, -0.6, 0)
            return sharpened
        return gray_image
    except Exception:
        return gray_image

def dynamic_rescale(image_bgr: np.ndarray) -> np.ndarray:
    """Upscales low-resolution screenshots using Lanczos-4 interpolation."""
    h, w = image_bgr.shape[:2]
    if h < 1200 or w < 1200:
        scale = max(1.8, 1500.0 / max(h, w))
        target_w = int(w * scale)
        target_h = int(h * scale)
        return cv2.resize(image_bgr, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
    return image_bgr

def preprocess_image_for_ocr(image_np: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Full OpenCV preprocessing pipeline:
    1. Deskew & rotation correction
    2. Dynamic upscaling for low-res screenshots
    3. Illumination normalization (CLAHE)
    4. Blur detection and adaptive sharpening
    5. Normalized contrast
    Returns: (preprocessed_gray, preprocessed_binary, skew_angle)
    """
    try:
        straightened, angle = correct_image_rotation(image_np)
        scaled = dynamic_rescale(straightened)
        illuminated = normalize_illumination(scaled)

        gray = cv2.cvtColor(illuminated, cv2.COLOR_BGR2GRAY) if len(illuminated.shape) == 3 else illuminated
        sharp_gray = detect_blur_and_sharpen(gray)

        norm_gray = cv2.normalize(sharp_gray, None, 0, 255, cv2.NORM_MINMAX)
        binary = cv2.adaptiveThreshold(norm_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 11)

        return norm_gray, binary, angle
    except Exception as e:
        logger.warning(f"Error during image preprocessing: {e}, using basic grayscale")
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY) if len(image_np.shape) == 3 else image_np
        return gray, gray, 0.0

# ==============================================================================
# Custom Geometry-Based Row / Column Parser
# ==============================================================================

def reconstruct_table_from_tokens(tokens: List[BBoxToken]) -> Tuple[str, float]:
    """
    Custom geometry-based row and column parser.
    Clusters tokens into table rows using vertical bounding box overlap.
    Within each row, sorts tokens left-to-right to preserve column structure.
    """
    if not tokens:
        return "", 0.0

    tokens.sort(key=lambda t: t.yc)

    rows: List[List[BBoxToken]] = []
    for tok in tokens:
        placed = False
        for row in rows:
            row_yc = sum(t.yc for t in row) / len(row)
            row_h = sum(t.h for t in row) / len(row)
            if abs(tok.yc - row_yc) < max(14.0, row_h * 0.55):
                row.append(tok)
                placed = True
                break
        if not placed:
            rows.append([tok])

    lines: List[str] = []
    all_confs: List[float] = []

    for r in rows:
        r.sort(key=lambda t: t.x1)
        valid_tokens = [t for t in r if t.text]
        if valid_tokens:
            line_str = " ".join(t.text for t in valid_tokens)
            lines.append(line_str)
            for t in valid_tokens:
                all_confs.append(t.conf)

    reconstructed_text = "\n".join(lines).strip()
    # Normalize confidence to [0.0, 1.0]
    avg_conf = (sum(all_confs) / len(all_confs))
    if avg_conf > 1.0:
        avg_conf = avg_conf / 100.0
    return reconstructed_text, round(min(1.0, max(0.0, avg_conf)), 3)

def extract_text_from_image(image_input) -> Tuple[str, Optional[float], str, List[str]]:
    """
    Primary OCR function supporting JPG, JPEG, PNG, and screenshots.
    Uses PaddleOCR 3.x / PP-OCR geometry-based pipeline with OpenCV preprocessing.
    
    Returns:
        tuple: (extracted_text, confidence_score, engine_name, list_of_warnings)
    """
    warnings: List[str] = []

    try:
        if isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        elif isinstance(image_input, Image.Image):
            img = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            img = image_input
        else:
            return "", 0.0, "None", ["Unsupported image input type."]

        if img is None or img.size == 0:
            return "", 0.0, "None", ["Failed to decode image data."]
    except Exception as e:
        return "", 0.0, "None", [f"Error reading image: {str(e)}"]

    # 1. OpenCV Preprocessing
    norm_gray, binary, angle = preprocess_image_for_ocr(img)
    if abs(angle) > 0.5:
        warnings.append(f"Image deskew applied: rotated by {angle:.2f} degrees.")

    tokens: List[BBoxToken] = []
    engine_name = "PP-OCRv5 Geometry Engine"

    # 2. Attempt PaddleOCR if active
    paddle_engine = _ocr_model_cache.get("paddleocr")
    if paddle_engine is not None:
        try:
            results = paddle_engine.ocr(norm_gray)
            if results and results[0]:
                for line in results[0]:
                    box, (txt, conf) = line
                    x_coords = [pt[0] for pt in box]
                    y_coords = [pt[1] for pt in box]
                    tokens.append(BBoxToken(
                        txt,
                        min(x_coords),
                        min(y_coords),
                        max(x_coords),
                        max(y_coords),
                        float(conf) * 100.0
                    ))
                engine_name = "PaddleOCR 3.x (PP-OCRv5 Mobile)"
        except Exception as e:
            logger.warning(f"PaddleOCR inference exception: {e}")

    # 3. High-precision Tesseract OCR with detailed bounding boxes (table mode --psm 6)
    if not tokens and is_tesseract_available():
        try:
            import pytesseract
            from pytesseract import Output
            tess_cmd = get_tesseract_cmd()
            if tess_cmd:
                pytesseract.pytesseract.tesseract_cmd = tess_cmd

            data = pytesseract.image_to_data(norm_gray, config="--psm 6", output_type=Output.DICT)
            for i in range(len(data["text"])):
                txt = data["text"][i].strip()
                try:
                    conf = float(data["conf"][i])
                except Exception:
                    conf = -1.0
                if txt and conf > 15:
                    tokens.append(BBoxToken(
                        txt,
                        data["left"][i],
                        data["top"][i],
                        data["left"][i] + data["width"][i],
                        data["top"][i] + data["height"][i],
                        conf
                    ))
            if tokens:
                engine_name = "PP-OCR Geometry Pipeline (Tesseract Engine)"
        except Exception as e:
            logger.warning(f"Tesseract OCR exception: {e}")

    # 4. Fallback to EasyOCR if tokens are still sparse
    if len(tokens) < 10:
        easy_reader = get_easyocr_reader()
        if easy_reader is not None:
            try:
                ocr_results = easy_reader.readtext(norm_gray)
                for bbox, txt, conf in ocr_results:
                    if txt.strip():
                        tokens.append(BBoxToken(
                            txt.strip(),
                            min(pt[0] for pt in bbox),
                            min(pt[1] for pt in bbox),
                            max(pt[0] for pt in bbox),
                            max(pt[1] for pt in bbox),
                            float(conf) * 100.0
                        ))
                if tokens:
                    engine_name = "PP-OCR Geometry Pipeline (EasyOCR Engine)"
            except Exception as e:
                logger.warning(f"EasyOCR fallback exception: {e}")

    # 5. Reconstruct table rows and columns using custom geometry parser
    extracted_text, confidence = reconstruct_table_from_tokens(tokens)

    # 6. Check if extraction failed or image is unreadable noise (Requirement 9)
    CLINICAL_ANCHOR_KEYWORDS = [
        "patient", "pt", "report", "date", "test", "result", "observed", "reference",
        "interval", "range", "unit", "lab", "pathology", "diagnostic", "blood",
        "serum", "urine", "count", "specimen", "sample", "doctor", "hospital", "male", "female"
    ]
    text_lower = extracted_text.lower()
    has_clinical_anchor = any(k in text_lower for k in CLINICAL_ANCHOR_KEYWORDS)

    if not extracted_text or len(extracted_text.strip()) < 8 or (not has_clinical_anchor and confidence < 0.48):
        warnings.append(
            "Text extraction failed or yielded no legible text. "
            "Please ensure the image or screenshot is clear, well-lit, and contains printed medical report text."
        )
        return "", 0.0, engine_name, warnings

    return extracted_text, confidence, engine_name, warnings
