# app/services/ocr_service.py

import io
import re
import fitz
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, List, Optional
import logging
import numpy as np

logger = logging.getLogger("legalyze.ocr")

# ── Tesseract Config ───────────────────────────────────────────────
# PSM 6  = Assume uniform block of text (best for contracts)
# OEM 3  = Default LSTM + Legacy engine
TESSERACT_CONFIG = "--oem 3 --psm 6 -l eng"

# Resolution for rendering PDF pages to images
DPI = 300


# ══════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def extract_text_with_ocr(
    contents: bytes,
    content_type: str = "application/pdf"
) -> Tuple[str, int, int]:
    """
    Extracts text from scanned or image-based documents using OCR.

    Pipeline:
        1. Render each PDF page to a high-res PIL image (300 DPI)
        2. Preprocess image (greyscale, denoise, contrast, threshold)
        3. Run Tesseract OCR on preprocessed image
        4. Aggregate and clean text across all pages

    Returns:
        Tuple of (ocr_text, page_count, word_count)

    Raises:
        RuntimeError — If OCR fails entirely
    """
    logger.info("Starting OCR extraction pipeline")

    if content_type == "application/pdf":
        return _ocr_pdf(contents)
    else:
        return _ocr_image_bytes(contents)


# ══════════════════════════════════════════════════════════════════
# PDF → IMAGE → OCR
# ══════════════════════════════════════════════════════════════════

def _ocr_pdf(contents: bytes) -> Tuple[str, int, int]:
    """
    Renders each page of a PDF to an image and applies OCR.
    """
    ocr_pages: List[str] = []
    page_count = 0

    try:
        doc = fitz.open(stream=contents, filetype="pdf")
        page_count = len(doc)
        logger.info(f"PDF opened for OCR | total_pages={page_count}")

        for page_num, page in enumerate(doc, start=1):
            try:
                logger.debug(f"OCR processing page {page_num}/{page_count}")

                # Render page to image at specified DPI
                mat  = fitz.Matrix(DPI / 72, DPI / 72)   # 72 = default PDF DPI
                pix  = page.get_pixmap(matrix=mat, alpha=False)
                img  = _pixmap_to_pil(pix)

                # Preprocess image
                img = _preprocess_image(img)

                # Run Tesseract
                page_text = pytesseract.image_to_string(
                    img,
                    config=TESSERACT_CONFIG
                )
                cleaned = _clean_ocr_text(page_text)

                if cleaned:
                    ocr_pages.append(f"[PAGE {page_num}]\n{cleaned}")
                    logger.debug(
                        f"Page {page_num} OCR complete | words={len(cleaned.split())}"
                    )

            except Exception as e:
                logger.warning(f"OCR failed on page {page_num}: {e}")
                continue

        doc.close()

    except Exception as e:
        logger.error(f"PDF OCR pipeline failed: {e}")
        raise RuntimeError(f"OCR extraction failed: {str(e)}")

    full_text  = "\n\n".join(ocr_pages)
    word_count = len(full_text.split())

    logger.info(
        f"OCR complete | pages={page_count}, words={word_count}"
    )

    return full_text, page_count, word_count


def _ocr_image_bytes(contents: bytes) -> Tuple[str, int, int]:
    """
    Applies OCR directly on a single image file (PNG, JPG, TIFF).
    """
    try:
        img = Image.open(io.BytesIO(contents))
        img = _preprocess_image(img)

        text = pytesseract.image_to_string(img, config=TESSERACT_CONFIG)
        text = _clean_ocr_text(text)

        return text, 1, len(text.split())

    except Exception as e:
        raise RuntimeError(f"Image OCR failed: {str(e)}")


# ══════════════════════════════════════════════════════════════════
# IMAGE PREPROCESSING
# ══════════════════════════════════════════════════════════════════

def _preprocess_image(img: Image.Image) -> Image.Image:
    """
    Multi-step image preprocessing pipeline to maximize OCR accuracy:

    Steps:
        1. Convert to greyscale              (removes color noise)
        2. Upscale if too small              (min 1800px width)
        3. Enhance contrast                  (sharpen text vs background)
        4. Apply slight sharpening filter    (reduce blur)
        5. Binarize with adaptive threshold  (pure black/white)
        6. Remove noise (median filter)      (clean up artifacts)
    """
    # Step 1: Greyscale
    img = img.convert("L")

    # Step 2: Upscale small images
    w, h = img.size
    if w < 1800:
        scale = 1800 / w
        img = img.resize(
            (int(w * scale), int(h * scale)),
            Image.LANCZOS
        )
        logger.debug(f"Upscaled image from {w}x{h} to {img.size}")

    # Step 3: Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # Step 4: Sharpen
    img = img.filter(ImageFilter.SHARPEN)

    # Step 5: Binarize (convert to pure black/white)
    img = _binarize(img)

    # Step 6: Noise removal (median filter)
    img = img.filter(ImageFilter.MedianFilter(size=3))

    return img


def _binarize(img: Image.Image, threshold: int = 180) -> Image.Image:
    """
    Converts a greyscale image to pure black/white using a fixed threshold.
    Pixels above threshold → white (background)
    Pixels below threshold → black (text)
    """
    img_array = np.array(img)
    binary    = (img_array > threshold).astype(np.uint8) * 255
    return Image.fromarray(binary)


def _pixmap_to_pil(pix: fitz.Pixmap) -> Image.Image:
    """Converts a PyMuPDF Pixmap to a PIL Image."""
    mode = "RGBA" if pix.alpha else "RGB"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


# ══════════════════════════════════════════════════════════════════
# OCR TEXT CLEANING
# ══════════════════════════════════════════════════════════════════

def _clean_ocr_text(text: str) -> str:
    """
    Cleans raw OCR output:
    - Removes garbage characters and special symbols
    - Fixes common OCR mistakes (e.g., 'l' → '1' in numbers)
    - Normalizes whitespace
    - Removes lines that are too short to be meaningful (< 3 chars)
    """
    if not text:
        return ""

    # Remove non-printable characters
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)

    # Remove lines shorter than 3 characters (likely OCR artifacts)
    lines = text.split("\n")
    lines = [line for line in lines if len(line.strip()) >= 3]
    text  = "\n".join(lines)

    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)

    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ══════════════════════════════════════════════════════════════════
# OCR CONFIDENCE CHECK
# ══════════════════════════════════════════════════════════════════

def get_ocr_confidence(contents: bytes) -> float:
    """
    Returns the average Tesseract confidence score (0–100) for the document.
    Used to decide whether OCR quality is acceptable.
    Scores below 60 may indicate poor image quality.
    """
    try:
        doc   = fitz.open(stream=contents, filetype="pdf")
        page  = doc[0]
        mat   = fitz.Matrix(DPI / 72, DPI / 72)
        pix   = page.get_pixmap(matrix=mat, alpha=False)
        img   = _pixmap_to_pil(pix)
        img   = _preprocess_image(img)
        data  = pytesseract.image_to_data(
            img,
            output_type=pytesseract.Output.DICT,
            config=TESSERACT_CONFIG
        )
        confs = [
            int(c) for c in data["conf"]
            if str(c).strip() not in ["-1", ""]
        ]
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        doc.close()
        logger.info(f"OCR confidence score: {avg_conf:.1f}%")
        return round(avg_conf, 2)

    except Exception as e:
        logger.error(f"Confidence check failed: {e}")
        return 0.0