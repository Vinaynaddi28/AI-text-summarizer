"""Extract PDF text in page order, using local OCR for image-based pages."""
import os
import time
from io import BytesIO

import fitz
import pytesseract
from PIL import Image
from pypdf import PdfReader

MAX_EXTRACTED_TEXT_CHARS = 50_000
MAX_RENDER_PIXELS = 12_000_000
OCR_DPI = 150

class PdfExtractionError(ValueError):
    pass

def _positive_setting(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default

def extract_pdf(data: bytes) -> dict:
    if not data.startswith(b"%PDF-"):
        raise PdfExtractionError("The uploaded file is not a valid PDF.")
    try:
        reader = PdfReader(BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise PdfExtractionError("Encrypted PDFs are not supported. Remove the password and try again.")
        page_count = len(reader.pages)
        if not page_count:
            raise PdfExtractionError("This PDF has no pages.")
        max_pages = _positive_setting("PDF_MAX_PAGES", 30)
        if page_count > max_pages:
            raise PdfExtractionError(f"PDF has too many pages (maximum {max_pages}).")
        document = None
        sections, warnings = [], []
        ocr_pages = direct_pages = 0
        started = time.monotonic()
        max_ocr_pages = _positive_setting("PDF_MAX_OCR_PAGES", 10)
        max_ocr_seconds = _positive_setting("PDF_OCR_TIMEOUT_SECONDS", 120)
        try:
            for index, page in enumerate(reader.pages):
                text = (page.extract_text() or "").strip()
                # Preserve short text-only pages; sparse pages with images are likely scans.
                needs_ocr = not text or (len(text) < 20 and bool(list(page.images)))
                if needs_ocr:
                    if ocr_pages >= max_ocr_pages:
                        raise PdfExtractionError(f"PDF exceeds the OCR page limit ({max_ocr_pages}).")
                    remaining = max_ocr_seconds - (time.monotonic() - started)
                    if remaining <= 0:
                        raise PdfExtractionError("PDF OCR timed out. Try a shorter PDF.")
                    if document is None:
                        document = fitz.open(stream=data, filetype="pdf")
                    render_page = document[index]
                    scale = OCR_DPI / 72
                    if render_page.rect.width * render_page.rect.height * scale * scale > MAX_RENDER_PIXELS:
                        raise PdfExtractionError(f"Page {index + 1} is too large to render safely for OCR.")
                    pix = render_page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    try:
                        if os.getenv("TESSERACT_CMD"):
                            pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
                        text = pytesseract.image_to_string(image, timeout=max(1, remaining)).strip()
                    except pytesseract.TesseractNotFoundError as exc:
                        raise PdfExtractionError("Tesseract OCR is unavailable. Install it and set TESSERACT_CMD in backend/.env.") from exc
                    except RuntimeError as exc:
                        raise PdfExtractionError(f"OCR timed out or failed on page {index + 1}. Try a shorter or clearer PDF.") from exc
                    finally:
                        image.close()
                    ocr_pages += 1
                    if not text:
                        warnings.append(f"Page {index + 1}: no text found; the page may be blank or the scan may be unclear.")
                else:
                    direct_pages += 1
                if text:
                    sections.append(text)
                    if len("\n\n".join(sections)) > MAX_EXTRACTED_TEXT_CHARS:
                        raise PdfExtractionError(f"Extracted text is too long (limit: {MAX_EXTRACTED_TEXT_CHARS:,} characters). Try a shorter PDF.")
        finally:
            if document is not None:
                document.close()
    except PdfExtractionError:
        raise
    except Exception as exc:
        raise PdfExtractionError("This PDF is corrupted or unsupported. Please try another PDF.") from exc
    extracted_text = "\n\n".join(sections)
    if not extracted_text:
        raise PdfExtractionError("No text could be extracted. The PDF may be blank or the scan may be unclear.")
    method = "mixed" if direct_pages and ocr_pages else "ocr" if ocr_pages else "direct"
    return {"extracted_text": extracted_text, "page_count": page_count,
            "word_count": len(extracted_text.split()), "extraction_method": method,
            "ocr_page_count": ocr_pages, "warnings": warnings}

def extract_pdf_text(data: bytes) -> tuple[str, int, int]:
    """Keep the existing service interface for callers and tests."""
    result = extract_pdf(data)
    return result["extracted_text"], result["page_count"], result["word_count"]
