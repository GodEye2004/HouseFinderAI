from pydantic import BaseModel


class VerifyOtpSchema(BaseModel):
    phone_number: str
    code: str