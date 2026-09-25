from uuid import UUID

from pydantic import BaseModel


class ChunkInfo(BaseModel):
    id: UUID
    chunkIndex: int
    tokenCount: int
    embeddingStatus: str
