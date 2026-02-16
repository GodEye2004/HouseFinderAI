import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header
from gotrue import Dict
import app
from app.agents.graph import initialize_state
from app.agents.state import AgentState
from app.models.user import ChatRequest, ChatResponse
from app.services.advertisements.app_property.property_manager import property_manager
from app.services.llm_brain.persistence import load_sessions, save_sessions, sessions, agent_graph
from app.services.auth.access_token import get_current_user

# Helper to make authentication optional for chat
async def get_current_user_optional(current_user: Optional[dict] = Depends(get_current_user)):
    return current_user

# Note: Since get_current_user raises HTTPException, we might need a custom one for optional.
# Alternatively, we can check for the Authorization header manually.
# For now, let's keep it simple: if the user passes a token, we use it. 
# If they don't, they need to pass a session_id.

# Initial load of sessions at startup
shared_sessions_loaded = load_sessions()
sessions.update(shared_sessions_loaded)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, authorization: Optional[str] = Header(None)):
    """
    main chat , llm has full controll
    """
    from app.services.auth.access_token import decode_access_token, get_user_by_id

    user_session_id = None
    
    # 1. Try to get session from Auth Header
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            user = get_user_by_id(payload["sub"])
            if user:
                # Fixed session ID for this user
                user_session_id = f"user_{user['id']}"
    
    # 2. Determine which session_id to use
    session_id = user_session_id or request.session_id

    # 3. Create or receive session
    if not session_id:
        session_id = str(uuid.uuid4())
        sessions[session_id] = initialize_state(session_id)
        save_sessions(sessions)
    elif session_id not in sessions:
        # Try to reload from file
        reloaded = load_sessions()
        sessions.update(reloaded)
        
        if session_id not in sessions:
            # Still not found, create new
            sessions[session_id] = initialize_state(session_id)
            save_sessions(sessions)
    
    # Use the session_id we finalized

    current_state = sessions[session_id]

    # add user message
    current_state["messages"].append({"role": "user", "content": request.message})

    # run graph(always use chat_node)
    result = agent_graph.invoke(current_state)

    # update state
    sessions[session_id] = result
    save_sessions(sessions)

    # add response to history
    result["messages"].append({"role": "assistant", "content": result["next_message"]})

    # creat answere
    response = ChatResponse(
        response=result["next_message"],
        session_id=session_id,
        requires_input=result["needs_user_input"],
        missing_fields=result["missing_fields"],
        state=result["current_stage"],
    )

    # Suggested properties
    if result.get("search_results"):

        recommended = []
        for item in result["search_results"][:5]:
            # Handle both object and dict access (since persistence might return dicts)
            if hasattr(item, "property_id"):
                prop_id = item.property_id
                match_pct = item.match_percentage
                total_score = item.total_score
            else:
                prop_id = item.get("property_id")
                match_pct = item.get("match_percentage")
                total_score = item.get("total_score")
                
            prop = property_manager.get_property_by_id(prop_id)

            if prop:
                recommended.append(
                    {
                        "id": prop.id,
                        "title": prop.title,
                        "price": prop.price,
                        "area": prop.area,
                        "vpm": prop.vpm,
                        "units": prop.units,
                        "location": f"{prop.city}، {prop.district}",
                        "image_url": prop.image_url,
                        "source_link": prop.source_link,
                        "description": prop.description,
                        "match_percentage": match_pct,
                        "score": total_score,
                    }
                )

        response.recommended_properties = recommended

    return response
