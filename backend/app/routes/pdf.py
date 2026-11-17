"""PDF upload route for the existing summarizer text area."""

import os

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.pdf_extraction import PdfExtractionError, extract_pdf as extract_pdf_data

router = APIRouter()
DEFAULT_MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class ExtractPdfResponse(BaseModel):
    extracted_text: str
    page_count: int
    word_count: int
    extraction_method: str
    ocr_page_count: int
    warnings: list[str]


def max_upload_bytes() -> int:
    """Read a local setting, falling back to 5 MB when it is absent or invalid."""
    try:
        configured = int(os.getenv("PDF_MAX_UPLOAD_BYTES", str(DEFAULT_MAX_UPLOAD_BYTES)))
        return configured if configured > 0 else DEFAULT_MAX_UPLOAD_BYTES
    except ValueError:
        return DEFAULT_MAX_UPLOAD_BYTES


@router.post("/api/extract-pdf", response_model=ExtractPdfResponse)
async def extract_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Please choose a .pdf file.")
    if file.content_type not in ("application/pdf", "application/x-pdf", "application/octet-stream"):
        raise HTTPException(status_code=415, detail="Please choose a PDF file.")

    limit = max_upload_bytes()
    try:
        data = await file.read(limit + 1)
    finally:
        await file.close()
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"PDF is too large. Maximum upload size is {limit / (1024 * 1024):g} MB.")
    if not data:
        raise HTTPException(status_code=400, detail="The PDF file is empty.")

    try:
        result = extract_pdf_data(data)
    except PdfExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ExtractPdfResponse(**result)
