from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str
    topK: int = Field(default=5, ge=1, le=50)
    documentId: UUID | None = None
