from fastapi import APIRouter
from app.models.verify_otp import VerifyOtpSchema
from app.services.auth.send_otp import verify_otp


router = APIRouter()
    

@router.post("/verify-otp")
def verify_otp_route(data: VerifyOtpSchema):
    token = verify_otp(data.phone_number, data.code)
    return {
        "access_token": token,
        "token_type": "bearer",
    }
