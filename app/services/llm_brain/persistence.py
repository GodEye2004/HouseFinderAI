import json
import os
from typing import Dict, List
from app.agents.graph import create_agent_graph
from app.agents.state import AgentState
from app.services.brain.memory_service import ConversationMemory
from app.models.property import UserRequirements, PropertyScore

SESSION_FILE = "data/sessions.json"

# Shared session store and graph instance
sessions: Dict[str, AgentState] = {}
agent_graph = create_agent_graph()

def save_sessions_to_file():
    """Save the current shared sessions to file"""
    save_sessions(sessions)

def save_sessions(sessions_to_save: Dict[str, AgentState]):
    """Save sessions to file"""
    data = {}
    for sid, state in sessions_to_save.items():
        state_copy = state.copy()
        
        # Serialize Memory
        if isinstance(state_copy.get('memory'), ConversationMemory):
            state_copy['memory'] = state_copy['memory'].to_dict()
        
        # Serialize Requirements
        if isinstance(state_copy.get('requirements'), UserRequirements):
            # Use jsonable_encoder or just dict() with mode='json' if pydantic v2
            # Assuming basic dict() works for simple types, but for Enums json dump handles str
            state_copy['requirements'] = state_copy['requirements'].model_dump() if hasattr(state_copy['requirements'], 'model_dump') else state_copy['requirements'].dict()
            
        # Serialize Search Results
        if state_copy.get('search_results'):
            serialized_results = []
            for item in state_copy['search_results']:
                if hasattr(item, 'dict'):
                    serialized_results.append(item.dict())
                elif hasattr(item, 'model_dump'):
                    serialized_results.append(item.model_dump())
                else:
                    serialized_results.append(item)
            state_copy['search_results'] = serialized_results
            
        # No special serialization needed for shown_properties_context (list of dicts)
        
        data[sid] = state_copy
        
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def load_sessions() -> Dict[str, AgentState]:
    """Load sessions from file"""
    if not os.path.exists(SESSION_FILE):
        return {}
        
    try:
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        sessions = {}
        for sid, raw_state in data.items():
            # Restore Memory
            if raw_state.get('memory'):
                 raw_state['memory'] = ConversationMemory.from_dict(raw_state['memory'])
            else:
                 raw_state['memory'] = ConversationMemory()
                 
            # Restore Requirements
            if raw_state.get('requirements'):
                # Handle Enum conversion if necessary, Pydantic does this well
                raw_state['requirements'] = UserRequirements(**raw_state['requirements'])
            else:
                 raw_state['requirements'] = UserRequirements()

            # Restore Search Results
            if raw_state.get('search_results'):
                restored_results = []
                for item in raw_state['search_results']:
                    try:
                        restored_results.append(PropertyScore(**item))
                    except:
                        restored_results.append(item)
                raw_state['search_results'] = restored_results

            sessions[sid] = raw_state
            
        return sessions
    except Exception as e:
        print(f"Error loading sessions: {e}")
        return {}
