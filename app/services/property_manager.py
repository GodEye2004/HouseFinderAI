from typing import List, Dict, Optional
from datetime import datetime
from app.models.property_submission import PropertySubmission, PropertySubmissionWithStatus, PropertyStatus
from app.models.property import Property
from app.services.supabase_service import supabase_service
import uuid

class PropertyManager:
    """مدیریت آگهی‌های املاک با استفاده از Supabase"""

    def __init__(self):
        # این متد دیگر نیازی به دیکشنری ندارد
        pass

    def _map_status_to_db(self, status: str) -> str:
        if status == PropertyStatus.PENDING:
            return 'PENDING'
        elif status == PropertyStatus.APPROVED:
            return 'APPROVED'
        elif status == PropertyStatus.REJECTED:
            return 'REJECTED'
        return 'PENDING'

    def _map_status_from_db(self, status: str) -> str:
        if status == 'PENDING':
            return PropertyStatus.PENDING
        elif status == 'APPROVED':
            return PropertyStatus.APPROVED
        elif status == 'REJECTED':
            return PropertyStatus.REJECTED
        return PropertyStatus.PENDING

    def submit_property(
            self,
            submission: PropertySubmission,
            user_id: Optional[str] = None
    ) -> PropertySubmissionWithStatus:
        """ثبت آگهی جدید در Supabase"""

        property_id = f"p{str(uuid.uuid4())[:8]}"
        now = datetime.now().isoformat()
        
        # محاسبه سن بنا
        age = None
        if submission.year_built:
            age = 1403 - submission.year_built

        # آماده‌سازی دیتا برای ذخیره
        db_data = {
            "id": property_id,
            "user_id": user_id if user_id else None,
            "owner_phone": submission.owner_phone or "",
            "title": submission.title or "",
            "description": submission.description,
            "property_type": submission.property_type,
            "transaction_type": submission.transaction_type,
            "status": 'APPROVED',  # پیش‌فرض تایید شده طبق کد قبلی (یا PENDING طبق لاجیک) - کد قبلی APPROVED بود
            "price": submission.price,
            "area": submission.area,
            "city": submission.city,
            "district": submission.district,
            "bedrooms": submission.bedrooms,
            "age": age,
            "floor": submission.floor,
            "total_floors": submission.total_floors,
            "document_type": submission.document_type,
            "has_parking": submission.has_parking,
            "has_elevator": submission.has_elevator,
            "has_storage": submission.has_storage,
            "is_renovated": submission.is_renovated,
            "open_to_exchange": submission.open_to_exchange,
            "exchange_preferences": submission.exchange_preferences or [],
            "created_at": now,
            "updated_at": now
        }

        # ذخیره در Supabase
        supabase_service.insert("properties", db_data)

        # ایجاد آبجکت بازگشتی
        return PropertySubmissionWithStatus(
            id=property_id,
            status=PropertyStatus.APPROVED, # باید با آنچه ذخیره کردیم یکی باشد
            created_at=now,
            updated_at=now,
            **submission.dict()
        )

    def get_submission(self, property_id: str) -> Optional[PropertySubmissionWithStatus]:
        """دریافت آگهی از Supabase"""
        results = supabase_service.select("properties", filters={"id": property_id})
        if not results:
            return None
        
        data = results[0]
        return self._map_db_to_submission(data)

    def get_user_submissions(self, user_id: str) -> List[PropertySubmissionWithStatus]:
        """دریافت آگهی‌های یک کاربر"""
        results = supabase_service.select("properties", filters={"user_id": user_id})
        return [self._map_db_to_submission(item) for item in results]

    def get_all_submissions(
            self,
            status: Optional[PropertyStatus] = None
    ) -> List[PropertySubmissionWithStatus]:
        """دریافت تمام آگهی‌ها"""
        filters = {}
        if status:
            filters["status"] = self._map_status_to_db(status)
            
        results = supabase_service.select("properties", filters=filters)
        # مرتب‌سازی در پایتون چون متد select ساده است (یا باید order به سرویس اضافه کنیم)
        submissions = [self._map_db_to_submission(item) for item in results]
        submissions.sort(key=lambda x: x.created_at, reverse=True)
        return submissions

    def update_status(
            self,
            property_id: str,
            new_status: PropertyStatus,
            admin_note: Optional[str] = None
    ) -> bool:
        """تغییر وضعیت آگهی"""
        db_status = self._map_status_to_db(new_status)
        try:
            supabase_service.update("properties", property_id, {
                "status": db_status,
                "updated_at": datetime.now().isoformat()
            })
            return True
        except:
            return False

    def delete_submission(self, property_id: str) -> bool:
        """حذف آگهی"""
        return supabase_service.delete("properties", property_id)

    def _map_db_to_submission(self, data: Dict) -> PropertySubmissionWithStatus:
        """تبدیل دیتای دیتابیس به مدل پایتون"""
        # محاسبه سال ساخت از روی سن
        year_built = None
        if data.get("age") is not None:
             year_built = 1403 - data.get("age")

        return PropertySubmissionWithStatus(
            id=data["id"],
            status=self._map_status_from_db(data.get("status", "PENDING")),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            owner_phone=data.get("owner_phone"),
            title=data.get("title"),
            description=data.get("description"),
            property_type=data.get("property_type"),
            transaction_type=data.get("transaction_type"),
            price=data.get("price"),
            area=data.get("area"),
            city=data.get("city"),
            district=data.get("district"),
            bedrooms=data.get("bedrooms"),
            year_built=year_built,
            floor=data.get("floor"),
            total_floors=data.get("total_floors"),
            document_type=data.get("document_type"),
            has_parking=data.get("has_parking", False),
            has_elevator=data.get("has_elevator", False),
            has_storage=data.get("has_storage", False),
            is_renovated=data.get("is_renovated", False),
            open_to_exchange=data.get("open_to_exchange", False),
            exchange_preferences=data.get("exchange_preferences", [])
        )

    def convert_to_property(
            self,
            submission: PropertySubmissionWithStatus
    ) -> Property:
        """تبدیل آگهی به Property برای نمایش"""
        return Property(
            id=submission.id,
            title=submission.title or "",
            property_type=submission.property_type,
            transaction_type=submission.transaction_type,
            price=submission.price or 0,
            area=submission.area or 0,
            city=submission.city or "",
            district=submission.district or "",
            bedrooms=submission.bedrooms,
            year_built=submission.year_built,
            floor=submission.floor,
            total_floors=submission.total_floors,
            document_type=submission.document_type,
            has_parking=submission.has_parking,
            has_elevator=submission.has_elevator,
            has_storage=submission.has_storage,
            is_renovated=submission.is_renovated,
            open_to_exchange=submission.open_to_exchange,
            exchange_preferences=submission.exchange_preferences,
            owner_phone=submission.owner_phone or "",
            description=submission.description or "",
        )


    def get_all_properties(self) -> List[Property]:
        """دریافت تمام املاک تایید شده به صورت آبجکت Property"""
        submissions = self.get_all_submissions(status=PropertyStatus.APPROVED)
        return [self.convert_to_property(s) for s in submissions]

    def get_property_by_id(self, property_id: str) -> Optional[Property]:
        """دریافت ملک با ID"""
        submission = self.get_submission(property_id)
        if submission:
            return self.convert_to_property(submission)
        return None

    def get_exchange_properties(self) -> List[Property]:
        """دریافت املاک مناسب معاوضه"""
        all_props = self.get_all_properties()
        return [p for p in all_props if p.open_to_exchange]

    def get_statistics(self) -> Dict:
        """آمار آگهی‌ها"""
        # این متد میتونه بهینه تر بشه با کوئری کانت
        submissions = self.get_all_submissions()
        total = len(submissions)
        pending = len([s for s in submissions if s.status == PropertyStatus.PENDING])
        approved = len([s for s in submissions if s.status == PropertyStatus.APPROVED])
        rejected = len([s for s in submissions if s.status == PropertyStatus.REJECTED])

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
        }


    def update_property_details(self, property_id: str, updates: Dict) -> bool:
        """آپدیت جزییات ملک"""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            supabase_service.update("properties", property_id, updates)
            return True
        except:
            return False

# Instance سراسری
property_manager = PropertyManager()