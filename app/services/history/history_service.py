from typing import List, Dict, Any
from app.core.postgres_service import postgres_service
from app.models.history import HistoryMessage
import uuid

class HistoryService:
    @staticmethod
    def save_message(user_id: str, session_id: str, role: str, content: str):
        """Save a message to chat history"""
        data = {
            "user_id": user_id,
            "session_id": session_id,
            "role": role,
            "content": content
        }
        return postgres_service.insert("chat_history", data)

    @staticmethod
    def get_user_history(user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        query = """
            SELECT DISTINCT ON (session_id) 
                session_id, 
                content as last_message, 
                created_at as last_updated
            FROM chat_history
            WHERE user_id = %s
            ORDER BY session_id, created_at DESC
        """
        return postgres_service.execute_raw(query, (user_id,))

    @staticmethod
    def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific session"""
        return postgres_service.select(
            "chat_history", 
            filters={"session_id": session_id}, 
            order_by="created_at ASC"
        )

history_service = HistoryService()
