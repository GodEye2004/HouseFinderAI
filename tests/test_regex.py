from app.services.brain.regex_extractor import RegexExtractor

def test_extraction():
    extractor = RegexExtractor()
    
    test_cases = [
        (
            "دنبال یه خونه تو تهران هستم حدود ۳ میلیارد",
            {"city": "تهران", "budget_max": 3000000000}
        ),
        (
            "اجاره آپارتمان ۷۰ متری در کرج",
            {"transaction_type": "اجاره", "property_type": "آپارتمان", "area_min": 70, "city": "کرج"}
        ),
        (
            "معاوضه ماشین با زمین",
            {"transaction_type": "معاوضه", "property_type": "زمین", "wants_exchange": True}
        ),
        (
            "یک ویلا میخوام بخرم",
            {"property_type": "ویلا", "transaction_type": "فروش"}
        )
    ]
    
    print("Running RegexExtractor Tests...\n")
    for text, expected in test_cases:
        print(f"Input: {text}")
        result = extractor.extract_all(text)
        print(f"Extracted: {result}")
        
        # Simple check
        for key, val in expected.items():
            if result.get(key) != val:
                print(f"❌ Mismatch on {key}: Expected {val}, got {result.get(key)}")
            else:
                print(f"✅ {key} match")
        print("-" * 30)

if __name__ == "__main__":
    test_extraction()
