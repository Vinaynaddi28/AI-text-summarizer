from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.summarize import SummarizeRequest, SummarizeResponse
from app.routes.history import router as history_router
from app.routes.pdf import router as pdf_router
from app.services.history import save_summary
from app.services.ollama import OllamaServiceError, summarize_with_ollama
from app.services.gemini import (
    MAX_INPUT_CHARACTERS,
    GeminiConfigurationError,
    GeminiServiceError,
    summarize_text,
)

app = FastAPI(title="AI Text Summarizer")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):517[0-9]+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pdf_router)
app.include_router(history_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "application": "AI Text Summarizer"}


@app.post("/api/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest):
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    if len(text) > MAX_INPUT_CHARACTERS:
        raise HTTPException(status_code=413, detail=f"Text is too long. Please keep it under {MAX_INPUT_CHARACTERS:,} characters.")
    try:
        summary = (summarize_with_ollama(text, request.length) if request.provider == "ollama"
                   else summarize_text(text, request.length))
    except OllamaServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GeminiConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except GeminiServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    response = SummarizeResponse(
        summary=summary,
        original_word_count=len(text.split()),
        summary_word_count=len(summary.split()),
        length=request.length,
    )
    save_summary(
        text=text,
        summary=summary,
        length=request.length,
        provider=request.provider,
        original_word_count=response.original_word_count,
        summary_word_count=response.summary_word_count,
    )
    return response
