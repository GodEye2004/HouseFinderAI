import requests
import json

BASE_URL = "http://localhost:8000"

def test_chat_search():
    # 1. Create session
    sess_resp = requests.post(f"{BASE_URL}/session/new")
    session_id = sess_resp.json()["session_id"]
    print(f"Session ID: {session_id}")
    
    # 2. Send message that triggers search
    message = "خونه میخوام توی گرگان آپارتمان باشه برای خرید میخوام ۵ میلیارد هم پول دارم"
    print(f"Sending: {message}")
    
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "session_id": session_id
        }
    )
    
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print("Response Keys:", data.keys())
        print("Response Text (first 100 chars):", data["response"][:100])
        print("Recommended Properties Count:", len(data.get("recommended_properties", [])))
        if data.get("recommended_properties"):
            print("First Property Title:", data["recommended_properties"][0].get("title"))
            # Check for any non-serializable stuff or weird fields
            print("First Property JSON:", json.dumps(data["recommended_properties"][0], ensure_ascii=False, indent=2))
    else:
        print("Error Response:", resp.text)

if __name__ == "__main__":
    test_chat_search()
