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

def test_city_fallback():
    # Properties in GORGAN
    props = [
        Property(id="g1", price=6_000_000_000, area=100, city="گرگان", district="گلشهر", 
                 title="Gorgan House", transaction_type=TransactionType.SALE, 
                 property_type=PropertyType.APARTMENT, owner_phone="0911", description="desc")
    ]
    
    import app.agents.nodes as nodes
    import app.services.brain.decision_engine as de
    mock_pm = MockPropertyManager(props)
    nodes.property_manager = mock_pm
    de.property_manager = mock_pm
    
    memory = ConversationMemory()
    memory.add_fact('city', "تهران") # Searching in TEHRAN
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
    
    # Perform Search
    print("\n--- Testing City Fallback (Tehran -> Gorgan) ---")
    state = _perform_search(state, memory, requirements)
    
    print(f"Next Message: {state['next_message']}")
    
    # Assertions
    assert "توی تهران موردی با مشخصات شما پیدا نکردم" in state["next_message"]
    assert "توی گرگان این 1 مورد" in state["next_message"]
    assert "Gorgan House" in state["next_message"]
    
    print("✅ City fallback test PASSED!")

if __name__ == "__main__":
    test_city_fallback()
