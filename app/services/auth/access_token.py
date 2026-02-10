from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.params import Depends
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional

from app.core.postgres_service import postgres_service

# Pro-tip: Move these to your .env file soon!
SECRET_KEY = "super-secret"
ALGORITHM = "HS256"

# This is the "callable" object that Depends needs
security_scheme = HTTPBearer()


def create_access_token(user_id: str):
    payload = {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(days=7)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None


def get_user_by_id(user_id: str):
    # Ensure filters matches your UUID column in the 'users' table we created
    users = postgres_service.select("users", filters={"id": user_id}, limit=1)
    return users[0] if users else None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """
    Validates the Bearer token and returns the user object.
    Used as a dependency in your profile and card design routes.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user
