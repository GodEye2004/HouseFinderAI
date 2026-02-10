import os
import random
from datetime import datetime, timedelta

from fastapi import HTTPException
from dotenv import load_dotenv
from kavenegar import KavenegarAPI, APIException

from app.core import postgres_service
from app.services.auth.access_token import create_access_token
from app.core.postgres_service import postgres_service


load_dotenv()

KAVENEGAR_API_KEY = os.getenv("KAVENEGAR_API_KEY")
kavenegar_api = KavenegarAPI(KAVENEGAR_API_KEY)


def send_otp_sms(phone_number: str, code: str):
    try:
        kavenegar_api.verify_lookup(
            {
                "receptor": phone_number,
                "template": "verify",
                "token": code,
            }
        )
    except APIException as e:
        raise HTTPException(status_code=500, detail=f"SMS sending failed: {e}")


def send_otp(phone_number: str):
    code = generate_otp()
    expires_at = otp_expiry()

    # rate limit
    recent = postgres_service.execute_raw(
        (phone_number,),
    )

    if recent:
        raise HTTPException(status_code=429, detail="OTP already sent, wait 60 seconds")

    postgres_service.insert(
        table="otp_codes",
        data={
            "phone_number": phone_number,
            "code": code,
            "expires_at": expires_at,
        },
    )

    send_otp_sms(phone_number, code)


def verify_otp(phone_number: str, code: str) -> str:
    otp = postgres_service.execute_raw(
        (phone_number, code, datetime.utcnow()),
    )

    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    postgres_service.execute_raw(
        (otp[0]["id"],),
    )

    users = postgres_service.select(
        table="users",
        filters={"phone_number": phone_number},
        limit=1,
    )

    if users:
        user = users[0]
    else:
        user = postgres_service.insert(
            table="users",
            data={
                "phone_number": phone_number,
                "is_verified": True,
            },
        )[0]

    return create_access_token(user["id"])


def generate_otp():
    return str(random.randint(10000, 99999))


def otp_expiry():
    return datetime.utcnow() + timedelta(minutes=2)
