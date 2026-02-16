import requests
import sys
import os

# Add app to path to use create_access_token
sys.path.append(os.getcwd())
from app.services.auth.access_token import create_access_token

BASE_URL = "http://localhost:8000"
USER_ID = "2052776b-3ba0-4615-bff6-abf5d1354dbe"

def test_persistent_sessions():
    # 1. Generate Token
    token = create_access_token(USER_ID)
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. First Request (Authenticated)
    print("--- Request 1 (Authenticated) ---")
    payload = {"message": "سلام"}
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    data1 = response.json()
    sid1 = data1["session_id"]
    print(f"Session ID 1: {sid1}")
    
    # 3. Second Request (Authenticated)
    print("\n--- Request 2 (Authenticated) ---")
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    data2 = response.json()
    sid2 = data2["session_id"]
    print(f"Session ID 2: {sid2}")
    
    if sid1 == sid2:
        print("\nSUCCESS: Session IDs match for the same user token!")
    else:
        print("\nFAILURE: Session IDs do not match!")
        
    # 4. Third Request (Not Authenticated, but with session_id)
    print("\n--- Request 3 (Manual Session ID, No Auth) ---")
    payload_manual = {"message": "تست", "session_id": sid1}
    response = requests.post(f"{BASE_URL}/chat", json=payload_manual)
    data3 = response.json()
    sid3 = data3["session_id"]
    print(f"Session ID 3: {sid3}")
    
    if sid3 == sid1:
         print("SUCCESS: Session persistence works without auth if session_id passed manually.")

if __name__ == "__main__":
    test_persistent_sessions()
