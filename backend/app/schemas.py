from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class DocumentOut(BaseModel):
    id:UUID
    filename: str
    status: str
    error: str | None
    total_chunks: int
    embedded_chunks: int
    created_at: datetime

class ChatRequest(BaseModel):
    document_id: UUID
    question: str = Field(min_length=1, max_length=2000)
    