import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_property_analysis():
    # 1. Start a new session and perform a search
    print("--- Step 1: Performing Search ---")
    payload_search = {
        "message": "خونه میخوام توی گرگان آپارتمان باشه برای خرید میخوام ۵ میلیارد هم پول دارم",
        "session_id": None
    }
    response = requests.post(f"{BASE_URL}/chat", json=payload_search)
    data = response.json()
    session_id = data["session_id"]
    
    print(f"Session ID: {session_id}")
    print(f"Search Response: {data['response'][:100]}...")
    
    # 2. Ask for analysis of the results
    print("\n--- Step 2: Asking for Analysis ---")
    payload_analysis = {
        "message": "نظرت درباره این ملک‌هایی که نشون دادی چیه؟ کدومشون برای سرمایه‌گذاری بهتره؟",
        "session_id": session_id
    }
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/chat", json=payload_analysis)
    end_time = time.time()
    
    data = response.json()
    print(f"Analysis Response Time: {end_time - start_time:.2f}s")
    print("\nAI Analysis:")
    print(data["response"])

if __name__ == "__main__":
    test_property_analysis()
