

from typing import TypedDict, List, Optional, Annotated, Dict
from app.models.property import UserRequirements, PropertyScore
from app.services.brain.memory_service import ConversationMemory
import operator


class AgentState(TypedDict):
    """State برای مدیریت گفتگو با کاربر"""

    # conversation message
    messages: Annotated[List[dict], operator.add]

    # memmory of conversation (new)
    memory: ConversationMemory

    # user requirements
    requirements: UserRequirements

    # current conversation
    current_stage: str

    # missing fields
    missing_fields: List[str]

    # search resulrt
    search_results: Optional[List[PropertyScore]]

    # summart of decision engin
    decision_summary: Optional[Dict]

    # engin recommendation
    recommendations: Optional[List[str]]

    #  if user want's to exchange
    wants_exchange: bool

    # exchange information
    exchange_item: Optional[str]
    exchange_value: Optional[int]

    # exchange property matches , ready for exchange
    exchange_matches: Optional[List[dict]]

    # user input for recive new information
    needs_user_input: bool

    # next system message
    next_message: str

    # Context for LLM analysis of shown properties
    shown_properties_context: Optional[List[dict]]

    # Last identified intent
    last_intent: Optional[str]

    # IDs of properties already shown to user in this session (to avoid repetition)
    shown_ids: List[str]


# Required fields that must be asked from the user
REQUIRED_FIELDS = {
    "budget_max": "بودجه حداکثر",
    "property_type": "نوع ملک",
    "city": "شهر",
}

# Important fields that should be asked preferably
IMPORTANT_FIELDS = {
    "area_min": "حداقل متراژ",
    "district": "منطقه",
    "bedrooms_min": "تعداد اتاق خواب",
}

# Optional fields
OPTIONAL_FIELDS = {
    "max_age": "حداکثر سن بنا",
    "min_floor": "حداقل طبقه",
    "must_have_parking": "پارکینگ الزامی",
    "must_have_elevator": "آسانسور الزامی",
}