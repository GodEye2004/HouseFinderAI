from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class PropertyType(str, Enum):
    APARTMENT = "آپارتمان"
    VILLA = "ویلا"
    OFFICE = "اداری"
    LAND = "زمین"
    STORE = "مغازه"


class TransactionType(str, Enum):
    SALE = "فروش"
    RENT = "اجاره"
    EXCHANGE = "معاوضه"


class DocumentType(str, Enum):
    SINGLE_PAGE = "تک برگ"
    COOPERATIVE = "مشاع"
    ENDOWMENT = "وقفی"
    LEASE = "اجاره‌ای"


class Property(BaseModel):
    id: str
    title: str
    property_type: PropertyType
    transaction_type: TransactionType

    # Required variables (high weight)
    price: int = Field(..., description="قیمت به تومان")
    area: int = Field(..., description="متراژ به متر مربع")
    city: str
    district: str

    # Important variables (average weight)
    bedrooms: Optional[int] = None
    year_built: Optional[int] = Field(None, description="سال ساخت (شمسی)")
    floor: Optional[int] = None
    total_floors: Optional[int] = None

    # Document type
    document_type: Optional[DocumentType] = None

    # Optional variables (low weight)
    has_parking: bool = False
    has_elevator: bool = False
    has_storage: bool = False
    is_renovated: bool = False

    # exchange details
    open_to_exchange: bool = False
    exchange_preferences: Optional[List[str]] = Field(
        default=None,
        description="چیزهایی که مایل به معاوضه است مثل ماشین، ملک دیگر"
    )

    
    owner_phone: str
    description: str

    # Add extra fields for better data integration
    vpm: Optional[int] = Field(None, description="قیمت هر متر")
    units: Optional[int] = Field(None, description="تعداد واحد")
    source_link: Optional[str] = Field(None, description="لینک آگهی اصلی")
    image_url: Optional[str] = Field(None, description="لینک تصویر آگهی")

    @property
    def age(self) -> Optional[int]:
        """calculate age of buildeing"""
        if self.year_built:
            from datetime import datetime
            current_year = 1403  # convert to shamsi
            return current_year - self.year_built
        return None


class UserRequirements(BaseModel):
    # require
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    property_type: Optional[PropertyType] = None
    transaction_type: Optional[TransactionType] = None

    # Important
    area_min: Optional[int] = None
    area_max: Optional[int] = None
    city: Optional[str] = None
    district: Optional[str] = None
    bedrooms_min: Optional[int] = None

    # year of build
    year_built_min: Optional[int] = None  

    
    document_type: Optional[DocumentType] = None

    # Optional
    max_age: Optional[int] = None
    min_floor: Optional[int] = None
    must_have_parking: bool = False
    must_have_elevator: bool = False
    must_have_storage: bool = False

    # exchange details
    has_exchange_item: bool = False
    exchange_item_type: Optional[str] = None
    exchange_item_value: Optional[int] = None
    wants_exchange: bool = False


class PropertyScore(BaseModel):
    property_id: str
    total_score: float
    score_details: dict
    match_percentage: float
    missing_requirements: List[str] = []
    decision_reasons: List[str] = []  # Reasons for the engine decision