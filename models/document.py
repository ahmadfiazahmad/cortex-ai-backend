from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    fileType: str
    status: str
    pageCount: int | None = None
    errorMessage: str | None = None
    uploadedAt: datetime
    updatedAt: datetime
