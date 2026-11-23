import io
import pymupdf as fitz
from PIL import Image
from typing import Tuple, List, Optional
import logging
from .ocr_service import extract_text_from_image

logger = logging.getLogger(__name__)

class PDFExtractionError(Exception):
    pass

def extract_layout_aware_page_text(page, y_tolerance: float = 4.0) -> str:
    """
    Extracts text from a PyMuPDF page by ordering words horizontally
    along the same vertical line coordinates. This reconstructs tabular
    reports into cohesive single-line rows for parsing.
    """
    words = page.get_text("words")
    if not words:
        return page.get_text("text")

    # Sort words by top-down y0, then left-to-right x0
    sorted_words = sorted(words, key=lambda w: (w[1], w[0]))

    lines = []
    current_line = []
    current_y = None

    for w in sorted_words:
        x0, y0, x1, y1, word_text = w[0], w[1], w[2], w[3], w[4]
        if current_y is None:
            current_y = y0
            current_line.append((x0, word_text))
        elif abs(y0 - current_y) <= y_tolerance:
            current_line.append((x0, word_text))
        else:
            current_line.sort(key=lambda item: item[0])
            lines.append(" ".join(item[1] for item in current_line))
            current_line = [(x0, word_text)]
            current_y = y0

    if current_line:
        current_line.sort(key=lambda item: item[0])
        lines.append(" ".join(item[1] for item in current_line))

    return "\n".join(lines)

def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[str, bool, Optional[float], str, List[str]]:
    """
    Extracts text from PDF bytes.
    First tries digital text extraction via PyMuPDF using layout-aware reconstruction.
    If the document has little or no selectable text, converts pages to images
    and executes Python-based OCR via EasyOCR (with Tesseract fallback).
    
    Returns:
        tuple: (extracted_text, is_scanned_flag, ocr_confidence, ocr_engine, list_of_warnings)
    """
    warnings: List[str] = []
    
    if not pdf_bytes or len(pdf_bytes) < 10:
        raise PDFExtractionError("PDF file is empty or invalid.")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise PDFExtractionError(f"Failed to open PDF document. It may be corrupted or encrypted: {str(e)}")

    if doc.page_count == 0:
        doc.close()
        raise PDFExtractionError("PDF document contains no pages.")

    full_digital_text = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text = extract_layout_aware_page_text(page)
        if text.strip():
            full_digital_text.append(text.strip())

    combined_digital_text = "\n\n".join(full_digital_text).strip()

    # Determine if PDF has sufficient digital text
    if len(combined_digital_text) > 60:
        doc.close()
        return combined_digital_text, False, 1.0, "Native Digital PDF", warnings

    # Scanned PDF: convert pages to images and execute OCR
    logger.info("PDF has minimal digital text. Converting pages to high-resolution images for OCR.")
    is_scanned = True
    ocr_texts = []
    confs = []
    engine = "EasyOCR (PyTorch Engine)"

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        page_text, page_conf, page_engine, ocr_warn = extract_text_from_image(img)
        if ocr_warn:
            warnings.extend(ocr_warn)
        if page_text.strip():
            ocr_texts.append(page_text.strip())
        if page_conf:
            confs.append(page_conf)
        if page_engine:
            engine = page_engine

    doc.close()
    combined_ocr_text = "\n\n".join(ocr_texts).strip()
    avg_conf = float(sum(confs) / len(confs)) if confs else None
    
    final_text = combined_ocr_text if len(combined_ocr_text) > len(combined_digital_text) else combined_digital_text
    return final_text, is_scanned, avg_conf, engine, warnings
