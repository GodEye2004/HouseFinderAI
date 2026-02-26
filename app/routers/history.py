from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.auth.access_token import get_current_user
from app.services.history.history_service import history_service
from app.models.history import HistoryMessage, HistorySessionResponse

router = APIRouter()

@router.get("/history", response_model=List[HistorySessionResponse])
async def get_user_history_sessions(current_user: dict = Depends(get_current_user)):
    """Get all chat sessions for the current user"""
    history = history_service.get_user_history(current_user["id"])
    return [
        HistorySessionResponse(
            session_id=item["session_id"],
            last_message=item["last_message"],
            last_updated=item["last_updated"]
        ) for item in history
    ]

@router.get("/history/{session_id}", response_model=List[HistoryMessage])
async def get_session_history(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get all messages for a specific session"""
    messages = history_service.get_session_messages(session_id)
    
    # Optional: Verify if the session belongs to the user
    # Since we filter by session_id, we should ensure the user owns this session history
    if messages and str(messages[0]["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access to this session history is denied")
        
    return messages
