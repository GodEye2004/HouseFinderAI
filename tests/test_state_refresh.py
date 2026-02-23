import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.property import Property, UserRequirements, PropertyType, TransactionType
from app.services.brain.decision_engine import DecisionEngine
from app.agents.nodes import _perform_search
from app.agents.state import AgentState
from app.services.brain.memory_service import ConversationMemory

# Mock PropertyManager
class MockPropertyManager:
    def __init__(self, props):
        self.props = props
    def get_all_properties(self):
        return self.props
    def get_property_by_id(self, pid):
        return next((p for p in self.props if p.id == pid), None)

def test_state_refresh_deduplication():
    # 6 Similar properties
    props = [
        Property(id=str(i), price=6_000_000_000, area=100, city="تهران", district="ونک", 
                 title=f"House {i}", transaction_type=TransactionType.SALE, 
                 property_type=PropertyType.APARTMENT, owner_phone="0911", description="desc")
        for i in range(1, 7)
    ]
    
    import app.agents.nodes as nodes
    nodes.property_manager = MockPropertyManager(props)
    
    memory = ConversationMemory()
    memory.add_fact('city', "تهران")
    memory.add_fact('budget_max', 10_000_000_000)
    memory.add_fact('transaction_type', "فروش")
    
    requirements = UserRequirements(city="تهران", budget_max=10_000_000_000, transaction_type=TransactionType.SALE)
    
    state: AgentState = {
        "messages": [],
        "memory": memory,
        "requirements": requirements,
        "shown_ids": [],
        "search_results": [],
        "shown_properties_context": None
    }
    
    # First search
    print("\n--- First Search ---")
    state = _perform_search(state, memory, requirements)
    print(f"Shown IDs: {state['shown_ids']}")
    assert len(state['shown_ids']) == 3
    assert set(state['shown_ids']) == {"1", "2", "3"}
    
    # Second search (simulating user changing something minor or just re-searching)
    print("\n--- Second Search (Deduplication) ---")
    state = _perform_search(state, memory, requirements)
    print(f"Shown IDs: {state['shown_ids']}")
    assert len(state['shown_ids']) == 6
    assert set(state['shown_ids']) == {"1", "2", "3", "4", "5", "6"}
    
    # Third search (should be no results)
    print("\n--- Third Search (Exhausted) ---")
    state = _perform_search(state, memory, requirements)
    assert "متاسفانه ملک جدیدی" in state["next_message"]
    
    # Reset/City change (Simulate behavior in _update_memory_and_requirements)
    print("\n--- City Change (Reset) ---")
    state["shown_ids"] = [] # This is what _update_memory_and_requirements does
    state = _perform_search(state, memory, requirements)
    assert len(state['shown_ids']) == 3
    print("✅ State refresh and deduplication test PASSED!")

if __name__ == "__main__":
    test_state_refresh_deduplication()
