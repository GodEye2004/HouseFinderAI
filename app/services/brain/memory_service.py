from typing import Dict, List, Optional
from datetime import datetime


class ConversationMemory:
    """
    Conversation memory system
    Remembers everything the user says
    """

    def __init__(self):
        self.facts: Dict[str, any] = {}  # Extracted facts
        self.preferences: Dict[str, any] = {}  # User preferences
        self.conversation_context: List[Dict] = []  # Full conversation text
        self.entities_mentioned: Dict[str, List] = {}  # Mentioned entities
        self.timeline: List[Dict] = []  # Conversation timeline

    def add_fact(self, key: str, value: any, confidence: float = 1.0):
        """Add a fact to memory"""
        self.facts[key] = {
            'value': value,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat(),
            'updated_count': self.facts.get(key, {}).get('updated_count', 0) + 1
        }

        self.timeline.append({
            'type': 'fact_added',
            'key': key,
            'value': value,
            'timestamp': datetime.now().isoformat()
        })

    def get_fact(self, key: str) -> Optional[any]:
        """Get a fact from memory"""
        if key in self.facts:
            return self.facts[key]['value']
        return None

    def add_entity(self, entity_type: str, entity_value: str):
        """Add an entity (e.g. "gold", "car")"""
        if entity_type not in self.entities_mentioned:
            self.entities_mentioned[entity_type] = []

        if entity_value not in self.entities_mentioned[entity_type]:
            self.entities_mentioned[entity_type].append(entity_value)

    def has_mentioned(self, entity_type: str, entity_value: str = None) -> bool:
        """Has a specific entity been mentioned?"""
        if entity_value:
            return entity_value in self.entities_mentioned.get(entity_type, [])
        return entity_type in self.entities_mentioned

    def get_all_entities(self, entity_type: str) -> List[str]:
        """Get all entities of a specific type"""
        return self.entities_mentioned.get(entity_type, [])

    def update_preference(self, key: str, value: any):
        """Update preferences"""
        self.preferences[key] = value

    def get_summary(self) -> str:
        """Summary of memory for LLM"""
        summary = "Conversation summary so far:\n"

        # Important facts
        if 'budget_max' in self.facts:
            budget = self.facts['budget_max']['value'] / 1_000_000_000
            summary += f"- بودجه: {budget} میلیارد تومان\n"

        if 'area_min' in self.facts:
            summary += f"- متراژ: حداقل {self.facts['area_min']['value']} متر\n"

        if 'city' in self.facts:
            summary += f"- شهر: {self.facts['city']['value']}\n"

        if 'district' in self.facts:
            summary += f"- منطقه: {self.facts['district']['value']}\n"

        if 'property_type' in self.facts:
            summary += f"- نوع ملک: {self.facts['property_type']['value']}\n"

        if 'year_built_min' in self.facts:
            summary += f"- سال ساخت: حداقل {self.facts['year_built_min']['value']}\n"

        if 'document_type' in self.facts:
            summary += f"- نوع سند: {self.facts['document_type']['value']}\n"

        # Facilities
        facilities = []
        if self.facts.get('must_have_parking', {}).get('value'):
            facilities.append("پارکینگ")
        if self.facts.get('must_have_elevator', {}).get('value'):
            facilities.append("آسانسور")
        if self.facts.get('must_have_storage', {}).get('value'):
            facilities.append("انباری")

        if facilities:
            summary += f"- امکانات الزامی: {', '.join(facilities)}\n"

        # exchange
        if 'exchange_item' in self.facts:
            item = self.facts['exchange_item']['value']
            summary += f"- مایل به معاوضه: بله ({item})\n"

            if 'exchange_value' in self.facts:
                value = self.facts['exchange_value']['value'] / 1_000_000
                summary += f"- ارزش معاوضه: {value} میلیون تومان\n"

        return summary if len(summary) > 30 else "هنوز اطلاعات زیادی نداریم."

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'facts': self.facts,
            'preferences': self.preferences,
            'entities_mentioned': self.entities_mentioned,
            'timeline': self.timeline
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationMemory':
        """Reconstruct from dictionary"""
        memory = cls()
        memory.facts = data.get('facts', {})
        memory.preferences = data.get('preferences', {})
        memory.entities_mentioned = data.get('entities_mentioned', {})
        memory.timeline = data.get('timeline', [])
        return memory