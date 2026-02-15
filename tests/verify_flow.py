from app.agents.nodes import chat_node
from app.agents.state import AgentState
from app.services.brain.memory_service import ConversationMemory
from app.models.property import UserRequirements
from app.services.advertisements.app_property.property_manager import property_manager

def verify_full_flow():
    # Setup state
    memory = ConversationMemory()
    requirements = UserRequirements()
    
    state: AgentState = {
        "messages": [{"role": "user", "content": "دنبال یه آپارتمان ۱۰۰ متری در تهران هستم با ۵ میلیارد"}],
        "memory": memory,
        "requirements": requirements,
        "current_stage": "start",
        "search_results": [],
        "needs_user_input": False,
        "next_message": ""
    }
    
    print("Simulating user request: 'دنبال یه آپارتمان ۱۰۰ متری در تهران هستم با ۵ میلیارد'")
    
    # Run node
    result_state = chat_node(state)
    
    print("\n--- Verification Results ---")
    print(f"Extracted Memory Facts: {result_state['memory'].facts.keys()}")
    print(f"Extracted City: {result_state['memory'].get_fact('city')}")
    print(f"Extracted Budget: {result_state['memory'].get_fact('budget_max')}")
    print(f"Extracted Area: {result_state['memory'].get_fact('area_min')}")
    
    print(f"\nSearch Results Count: {len(result_state.get('search_results', []))}")
    if result_state.get('search_results'):
        prop_id = result_state['search_results'][0].property_id
        prop = property_manager.get_property_by_id(prop_id)
        print(f"First result source check: {prop_id}")
        if prop:
            print(f"Source Link: {prop.source_link}")
            print(f"Image URL: {prop.image_url}")
            print(f"VPM: {prop.vpm}")
    
    print(f"\nAgent Response: {result_state['next_message'][:200]}...")

if __name__ == "__main__":
    verify_full_flow()
