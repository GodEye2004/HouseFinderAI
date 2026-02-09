import uuid
from fastapi import APIRouter
from gotrue import Dict
import app
from app.agents.graph import create_agent_graph, create_agent_graph, initialize_state
from app.agents.state import AgentState
from app.models.user import ChatRequest, ChatResponse
from app.services.advertisements.app_property import property_manager
from app.services.llm_brain.persistence import load_sessions, save_sessions

sessions: Dict[str, AgentState] = load_sessions()
agent_graph = create_agent_graph()

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    main chat , llm has full controll
    """

    # creat or recive session
    if not request.session_id or request.session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = initialize_state(session_id)
        save_sessions(sessions)
    else:
        session_id = request.session_id

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
        for score in result["search_results"][:5]:
            prop = property_manager.get_property_by_id(score.property_id)

            if prop:
                recommended.append(
                    {
                        "id": prop.id,
                        "title": prop.title,
                        "price": prop.price,
                        "area": prop.area,
                        "location": f"{prop.city}، {prop.district}",
                        "match_percentage": score.match_percentage,
                        "score": score.total_score,
                    }
                )

        response.recommended_properties = recommended

    return response
