from typing import Literal

from pydantic import BaseModel, Field


SummaryLength = Literal["short", "medium", "long"]


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1)
    length: SummaryLength = "medium"
    provider: Literal["gemini", "ollama"] = "gemini"


class SummarizeResponse(BaseModel):
    summary: str
    original_word_count: int
    summary_word_count: int
    length: SummaryLength
