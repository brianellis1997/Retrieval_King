from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class DocumentMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: str
    file_size: int
    upload_time: datetime = Field(default_factory=datetime.utcnow)
    num_chunks: int = 0
    num_pages: Optional[int] = None


class ChunkMetadata(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    chunk_index: int
    page_number: Optional[int] = None
    text: str
    token_count: int


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    num_chunks: int
    message: str


class Citation(BaseModel):
    citation_id: int
    document_id: str
    filename: str
    chunk_id: str
    text: str
    page_number: Optional[int] = None
    confidence_score: float


class QueryRequest(BaseModel):
    query: str
    top_k: int = 10
    use_reranker: bool = True
    stream: bool = False


class QueryResponse(BaseModel):
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    response: str
    citations: List[Citation] = []
    num_contexts_retrieved: int
    num_contexts_used: int
    processing_time_ms: float


class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]
    total_count: int


class DocumentDeleteResponse(BaseModel):
    document_id: str
    deleted: bool
    message: str
