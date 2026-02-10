from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "super-secret"
ALGORITHM = "HS256"

def create_access_token(user_id: str):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)