import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.property import Property, UserRequirements, PropertyType, TransactionType
from app.services.brain.decision_engine import DecisionEngine
from app.services.brain.scoring import PropertyScoringSystem

def test_budget_matching():
    engine = DecisionEngine()
    
    # 5 Mock properties
    properties = [
        Property(id="1", price=2_000_000_000, area=100, city="تهران", district="ونک", title="Cheap House", transaction_type=TransactionType.SALE, property_type=PropertyType.APARTMENT, owner_phone="0911", description="desc"),
        Property(id="2", price=4_800_000_000, area=100, city="تهران", district="ونک", title="Borderline Low", transaction_type=TransactionType.SALE, property_type=PropertyType.APARTMENT, owner_phone="0911", description="desc"),
        Property(id="3", price=6_000_000_000, area=100, city="تهران", district="ونک", title="Perfect Match", transaction_type=TransactionType.SALE, property_type=PropertyType.APARTMENT, owner_phone="0911", description="desc"),
        Property(id="4", price=9_500_000_000, area=100, city="تهران", district="ونک", title="Perfect Match High", transaction_type=TransactionType.SALE, property_type=PropertyType.APARTMENT, owner_phone="0911", description="desc"),
        Property(id="5", price=12_000_000_000, area=100, city="تهران", district="ونک", title="Too Expensive", transaction_type=TransactionType.SALE, property_type=PropertyType.APARTMENT, owner_phone="0911", description="desc"),
    ]
    
    # Request: 5 to 9 Billion
    requirements = UserRequirements(
        city="تهران",
        budget_min=5_000_000_000,
        budget_max=9_000_000_000,
        transaction_type=TransactionType.SALE,
        property_type=PropertyType.APARTMENT
    )
    
    print(f"\nSearching for budget range: 5,000,000,000 - 9,000,000,000")
    
    result = engine.make_decision(properties, requirements)
    
    print(f"Status: {result['status']}")
    print(f"Number of results: {len(result['properties'])}")
    
    for score in result['properties']:
        prop = next(p for p in properties if p.id == score.property_id)
        print(f"ID: {prop.id}, Title: {prop.title}, Price: {prop.price:,}, Match: {score.match_percentage}%")
        
    # Expectations:
    # 1. Cheap house (2B) should be FILTERED OUT (not in SUCCESS results)
    # 2. Borderline Low (4.8B) should be FILTERED OUT (strict min)
    # 3. Success properties should only be IDs 3 and 4 (6B and 9.5B - tolerance)
    
    success_ids = [s.property_id for s in result['properties']]
    assert "1" not in success_ids, "Error: Cheap house (2B) should have been filtered out!"
    assert "2" not in success_ids, "Error: 4.8B house should have been filtered out (strict min)!"
    assert "3" in success_ids, "Error: 6B house should be included!"
    assert "4" in success_ids, "Error: 9.5B house should be included (within 10% tolerance)!"
    assert "5" not in success_ids, "Error: 12B house should have been filtered out!"
    
    print("\n✅ Budget matching test PASSED!")

if __name__ == "__main__":
    test_budget_matching()
