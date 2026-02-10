from pydantic import BaseModel

class SendOtpSchema(BaseModel):
    phone_number: str
