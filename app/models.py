from pydantic import BaseModel
from typing import List, Optional, Any

class ChatRequest(BaseModel):
    user_id: str
    message: str
    top_k: int = 3

class Source(BaseModel):
    id: int
    title: str
    snippet: str
    meta: dict

class ChatResponse(BaseModel):
    reply: str
    sources: List[Source]
    from_rag: bool
    sentiment: Optional[str] = None
    memory_len: Optional[int] = None

class UpsertDoc(BaseModel):
    text: str
    title: str = "Manual Entry"
    meta: Optional[dict] = None
