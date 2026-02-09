import uuid
from fastapi import APIRouter, HTTPException
from gotrue import Dict
import app
from app.agents.graph import create_agent_graph, initialize_state
from app.agents.state import AgentState
from app.services.llm_brain.persistence import load_sessions

sessions: Dict[str, AgentState] = load_sessions()
agent_graph = create_agent_graph()

router = APIRouter()


@router.post("/session/new")
def create_new_session():
    """create new session"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = initialize_state(session_id)

    return {"session_id": session_id, "message": "create session with new history"}


@router.get("/session/{session_id}")
def get_session(session_id: str):
    """get session information"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[session_id]
    memory = state["memory"]

    return {
        "session_id": session_id,
        "current_stage": state["current_stage"],
        "messages_count": len(state["messages"]),
        "memory_summary": memory.get_summary(),
        "memory_facts": list(memory.facts.keys()),
        "requirements": state["requirements"].dict(),
        "wants_exchange": state["wants_exchange"],
    }


@router.get("/session/{session_id}/memory")
def get_session_memory(session_id: str):
    """get full memory"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    memory = sessions[session_id]["memory"]

    return {
        "session_id": session_id,
        "memory": memory.to_dict(),
        "summary": memory.get_summary(),
    }


@router.delete("/session/{session_id}")
def delete_session(session_id: str):
    """delete session"""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")
