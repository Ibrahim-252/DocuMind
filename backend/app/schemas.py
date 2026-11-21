from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    error_message: str | None = None
    created_at: datetime


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class SourceOut(BaseModel):
    document_id: int
    filename: str
    page: int
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceOut]
