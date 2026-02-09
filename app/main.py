from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.property_submission import PropertySubmission
from app.models.user import ChatRequest, ChatResponse
from app.agents.graph import create_agent_graph, initialize_state
from app.agents.state import AgentState
from app.services.advertisements.app_property import property_manager
from app.services.advertisements.app_property.property_manager import PropertyManager
from app.services.brain.memory_service import ConversationMemory
from typing import Dict
import uuid
from app.services.advertisements.divar_property.divar_api import divar_router
from app.services.advertisements.app_property.property_manager import property_manager
from app.routers import session, chat, properties
from app.services.llm_brain.persistence import save_sessions, load_sessions


app = FastAPI(
    title="real state agent with memory",
    description="Real estate consulting system with integrated LLM and full memory",
    version="1.0.0",
)

app.include_router(divar_router)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# save session
sessions: Dict[str, AgentState] = load_sessions()


@app.get("/")
def read_root():
    """Main page"""
    return {
        "message": "🏡 سیستم مشاور املاک هوشمند با حافظه",
        "version": "1.0.0",
        "features": [
            "حافظه کامل مکالمه",
            "فهم طبیعی زبان فارسی",
            "موتور تصمیم‌گیری پیشرفته",
            "معاوضه هوشمند",
        ],
    }


@app.get("/health")
def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "sessions_count": len(sessions),
        "llm_enabled": True,  # check llm exist
    }


app.include_router(chat.router, tags=["chat"])
app.include_router(session.router, tags=["session"])
app.include_router(properties.router, tags=["properties"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
