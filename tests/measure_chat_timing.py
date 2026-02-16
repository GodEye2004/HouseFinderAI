import requests
import time

BASE_URL = "http://localhost:8000"

def test_chat_timing():
    sess_resp = requests.post(f"{BASE_URL}/session/new")
    session_id = sess_resp.json()["session_id"]
    
    message = "خونه میخوام توی گرگان آپارتمان باشه برای خرید میخوام ۵ میلیارد هم پول دارم"
    print(f"Sending: {message}")
    
    start_time = time.time()
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "session_id": session_id
        }
    )
    end_time = time.time()
    
    print(f"Status Code: {resp.status_code}")
    print(f"Time Taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    test_chat_timing()
