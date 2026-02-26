from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class HistoryMessage(BaseModel):
    id: int
    user_id: str
    session_id: str
    role: str
    content: str
    created_at: datetime

class HistorySessionResponse(BaseModel):
    session_id: str
    last_message: str
    last_updated: datetime

class HistoryResponse(BaseModel):
    messages: List[HistoryMessage]
