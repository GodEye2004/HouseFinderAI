
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.agents.state import AgentState
from typing import Dict
from app.services.advertisements.divar_property.divar_api import divar_router
from app.routers import send_otp, session, chat, properties, verify_otp
from app.services.llm_brain.persistence import load_sessions
from app.routers import profile

app = FastAPI(
    title="real state agent with memory",
    description="Real estate consulting system with integrated LLM and full memory",
    version="1.0.0",
)

app.include_router(divar_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


sessions: Dict[str, AgentState] = load_sessions()


@app.get("/")
def read_root():
    """Main page"""
    return {
        "message": "سیستم مشاور املاک هوشمند با حافظه",
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
app.include_router(verify_otp.router, tags=["auth"])
app.include_router(send_otp.router, tags=["auth"])
app.include_router(profile.router, tags=["profile"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
