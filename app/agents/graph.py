

from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes import chat_node
from app.models.property import UserRequirements
from app.services.brain.memory_service import ConversationMemory


def create_agent_graph():
    """
    گراف خیلی ساده - فقط یه نود چت!
    LLM کنترل کامل رو داره
    """

    workflow = StateGraph(AgentState)

    workflow.add_node("chat", chat_node)

    workflow.set_entry_point("chat")
    workflow.add_edge("chat", END)

    return workflow.compile()


def initialize_state(session_id: str) -> AgentState:
    """ایجاد state با حافظه"""
    return AgentState(
        messages=[],
        memory=ConversationMemory(),
        requirements=UserRequirements(),
        current_stage="start",
        missing_fields=[],
        search_results=None,
        decision_summary=None,
        recommendations=None,
        wants_exchange=False,
        exchange_item=None,
        exchange_value=None,
        exchange_matches=None,
        needs_user_input=True,
        next_message=""
    )