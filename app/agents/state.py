

from typing import TypedDict, List, Optional, Annotated, Dict
from app.models.property import UserRequirements, PropertyScore
from app.services.brain.memory_service import ConversationMemory
import operator


class AgentState(TypedDict):
    """State برای مدیریت گفتگو با کاربر"""

    # پیام‌های گفتگو
    messages: Annotated[List[dict], operator.add]

    # حافظه مکالمه (جدید!)
    memory: ConversationMemory

    # نیازهای کاربر
    requirements: UserRequirements

    # مرحله فعلی گفتگو
    current_stage: str

    # فیلدهای ناقص
    missing_fields: List[str]

    # نتایج جستجو
    search_results: Optional[List[PropertyScore]]

    # خلاصه تصمیم موتور
    decision_summary: Optional[Dict]

    # توصیه‌های موتور
    recommendations: Optional[List[str]]

    # آیا کاربر مایل به معاوضه است؟
    wants_exchange: bool

    # اطلاعات معاوضه
    exchange_item: Optional[str]
    exchange_value: Optional[int]

    # املاک پیشنهادی معاوضه
    exchange_matches: Optional[List[dict]]

    # آیا نیاز به ورودی کاربر داریم؟
    needs_user_input: bool

    # پیام بعدی سیستم
    next_message: str


# فیلدهای الزامی که باید حتما از کاربر پرسیده شوند
REQUIRED_FIELDS = {
    "budget_max": "بودجه حداکثر",
    "property_type": "نوع ملک",
    "city": "شهر",
}

# فیلدهای مهم که ترجیحا باید پرسیده شوند
IMPORTANT_FIELDS = {
    "area_min": "حداقل متراژ",
    "district": "منطقه",
    "bedrooms_min": "تعداد اتاق خواب",
}

# فیلدهای اختیاری
OPTIONAL_FIELDS = {
    "max_age": "حداکثر سن بنا",
    "min_floor": "حداقل طبقه",
    "must_have_parking": "پارکینگ الزامی",
    "must_have_elevator": "آسانسور الزامی",
}