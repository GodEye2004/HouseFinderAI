from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum
from app.models.property import PropertyType, TransactionType, DocumentType


class PropertySubmission(BaseModel):
    """مدل برای ثبت آگهی جدید بدون محدودیت سختگیرانه"""

    # اطلاعات اصلی
    title: Optional[str] = None
    property_type: Optional[str] = None
    transaction_type: Optional[str] = None
    price: Optional[int] = None
    area: Optional[int] = None
    city: Optional[str] = None
    district: Optional[str] = None
    description: Optional[str] = None
    owner_phone: Optional[str] = None

    # اطلاعات تکمیلی
    bedrooms: Optional[int] = None
    year_built: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None

    # نوع سند
    document_type: Optional[str] = None

    # امکانات
    has_parking: bool = False
    has_elevator: bool = False
    has_storage: bool = False
    is_renovated: bool = False

    # معاوضه
    open_to_exchange: bool = False
    exchange_preferences: Optional[List[str]] = None


class SubmissionResponse(BaseModel):
    """پاسخ ثبت آگهی"""
    success: bool
    message: str
    property_id: Optional[str] = None
    property_data: Optional[dict] = None


class PropertyStatus(str):
    PENDING = "در_انتظار_تایید"
    APPROVED = "تایید_شده"
    REJECTED = "رد_شده"


class PropertySubmissionWithStatus(PropertySubmission):
    """آگهی با وضعیت"""
    id: str
    status: str = PropertyStatus.PENDING
    created_at: str
    updated_at: str