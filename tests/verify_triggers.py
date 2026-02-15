from app.agents.nodes import chat_node
from app.agents.state import AgentState
from app.services.brain.memory_service import ConversationMemory
from app.models.property import UserRequirements
from app.services.advertisements.app_property.property_manager import property_manager
import json

def test_trigger(message: str):
    print(f"\nTesting message: '{message}'")
    memory = ConversationMemory()
    requirements = UserRequirements()
    
    state: AgentState = {
        "messages": [{"role": "user", "content": message}],
        "memory": memory,
        "requirements": requirements,
        "current_stage": "start",
        "search_results": [],
        "needs_user_input": False,
        "next_message": ""
    }
    
    # Run node
    result_state = chat_node(state)
    
    print(f"Current Stage: {result_state['current_stage']}")
    print(f"Memory Facts: {result_state['memory'].facts}")
    print(f"Search Results Count: {len(result_state.get('search_results', []))}")
    
    if result_state.get('search_results'):
        prop = property_manager.get_property_by_id(result_state['search_results'][0].property_id)
        print(f"First Result Title: {prop.title}")
        print(f"Description: {prop.description[:100]}...")
        print(f"Source: {prop.source_link}")
    else:
        print(f"No results shown. Next Message: {result_state['next_message'][:100]}")
    
    return result_state

def run_verifications():
    print("=== TRIGGER VERIFICATION ===")
    
    # Case 2: Exchange search (global)
    test_trigger("برو معاوضه برام پیدا کن")
    
    # Case 3: District search
    test_trigger("یه آپارتمان تو نیاوران پیدا کن")
    
    # Case 4: District in Gorgan
    test_trigger("ناهارخوران بگرد")

if __name__ == "__main__":
    run_verifications()
