from fastapi import APIRouter, HTTPException

from app.models.auth_model import SendOtpSchema
from app.services.auth.send_otp import send_otp

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/send-otp")
def send_otp_route(data: SendOtpSchema):
    send_otp(data.phone_number)
    return {"message": "OTP sent successfully"}

