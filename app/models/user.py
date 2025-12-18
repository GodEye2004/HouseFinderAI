from pydantic import BaseModel
from typing import Optional, List

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    requires_input: bool = False
    missing_fields: List[str] = []
    recommended_properties: Optional[List[dict]] = None
    state: Optional[str] = None