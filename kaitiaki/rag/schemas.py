# kaitiaki/rag/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Query(BaseModel):
    text: str
    sources: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    top_k: int = 20

class Citation(BaseModel):
    doc_id: str
    page: int
    snippet: str

class Answer(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    latency_ms: int = 0
    latency_breakdown: Dict[str, int] = Field(..., alias="latencyMs")

    class Config:
        populate_by_name = True


