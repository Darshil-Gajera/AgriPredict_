from pydantic import BaseModel, Field
from typing import Optional, Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    language: Literal["en", "gu"] = "en"
    history: list[ChatMessage] = Field(default_factory=list, max_length=10)
    # Optional context from Django merit calculator
    user_merit: Optional[float] = None
    user_category: Optional[str] = None      # "1", "2", "3"
    student_category: Optional[str] = None   # OPEN, SC, ST, SEBC, EWS


class SourceDocument(BaseModel):
    source: str
    page: Optional[int] = None
    content_preview: str


class ChatResponse(BaseModel):
    answer: str
    language: str = "en"
    sources: list[SourceDocument] = []
    intent: Optional[str] = None  # merit | college | scholarship | admission | general


class IngestRequest(BaseModel):
    secret: str  # must match INGEST_SECRET env var


class HealthResponse(BaseModel):
    status: str
    vector_store_loaded: bool
    doc_count: int
