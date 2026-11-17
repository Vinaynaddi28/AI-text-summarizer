from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.summarize import SummaryLength


class HistoryEntry(BaseModel):
    id: int
    original_text: str
    summary_text: str
    summary_length: SummaryLength
    provider: Literal["gemini", "ollama"]
    original_word_count: int
    summary_word_count: int
    created_at: datetime
