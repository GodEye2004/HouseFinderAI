from pydantic import BaseModel
from typing import Optional

class DivarProperty(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    transaction_type: Optional[str] = None
    price: Optional[float] = None
    area: Optional[int] = None
    vpm: Optional[float] = None
    city: Optional[str] = None
    district: Optional[str] = None
    bedrooms: Optional[int] = None
    year_built: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    units: Optional[int] = None
    document_type: Optional[str] = None
    has_parking: Optional[bool] = False
    has_elevator: Optional[bool] = False
    has_storage: Optional[bool] = False
    is_renovated: Optional[bool] = False
    open_to_exchange: Optional[bool] = False
    exchange_preference: Optional[str] = None
    source_link: Optional[str] = None
    image_url: Optional[str] = None

class DivarPropertyResponse(DivarProperty):
    id: int

    class Config:
        orm_mode = True
