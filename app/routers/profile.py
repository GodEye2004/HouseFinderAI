from fastapi import APIRouter, Depends
from app.services.auth.access_token import get_current_user

router = APIRouter()

@router.get("/profile")
# We pass get_current_user as a dependency. 
# FastAPI runs it ONCE and puts the result into 'current_user'.
def get_profile(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "phone_number": current_user["phone_number"],
        "is_verified": current_user["is_verified"],
    }