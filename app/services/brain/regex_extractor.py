import re
from typing import Dict, Any, Optional

class RegexExtractor:
    """
    Extracts structured data from Persian text using regex patterns.
    Optimized for Real Estate domain: City, Budget, Area, Transaction Type.
    """

    def __init__(self):
        # Common Iranian cities for validation (expandable)
        self.cities = [
            "تهران", "کرج", "مشهد", "اصفهان", "تبریز", "شیراز", "اهواز", "قم", "رشت", 
            "ساری", "گرگان", "همدان", "ارومیه", "کرمانشاه", "یزد", "کرمان", "قزوین",
            "بوشهر", "بندرعباس", "زنجان", "سنندج", "خرم‌آباد", "اراک", "اردبیل"
        ]
        
        # Mapping for Persian numbers
        self.persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        self.english_digits = "0123456789"
        self.translation_table = str.maketrans(self.persian_digits, self.english_digits)

    def _normalize_text(self, text: str) -> str:
        """Convert Persian digits to English and normalize spaces."""
        if not text:
            return ""
        text = text.translate(self.translation_table)
        text = re.sub(r'\s+', ' ', text).strip()
        return text.lower() # Normalize to lower for easier matching

    def extract_all(self, text: str) -> Dict[str, Any]:
        """Run all extractors and return a dictionary of found fields."""
        normalized_text = self._normalize_text(text)
        
        result = {
            "city": self.extract_city(normalized_text),
            "budget_max": self.extract_budget(normalized_text),
            "area_min": self.extract_area(normalized_text),
            "transaction_type": self.extract_transaction_type(normalized_text),
            "property_type": self.extract_property_type(normalized_text),
            "district": self.extract_district(normalized_text),
            "wants_exchange": self.extract_exchange_intent(normalized_text)
        }
        
        # Filter None values
        return {k: v for k, v in result.items() if v is not None}

    def extract_city(self, text: str) -> Optional[str]:
        """Find mentioned city."""
        for city in self.cities:
            # Check for city name with word boundaries or prepositions
            # "dar tehran", "too tehran", "tehran"
            if re.search(rf'(?:\b|در |تو |شهر ){city}(?:\b|ی | )', text):
                return city
        return None

    def extract_budget(self, text: str) -> Optional[int]:
        """
        Extract budget info. 
        Handles: "2 miliard", "2.5 miliard", "500 million", "200 toman" (interpreted as million if too small?)
        """
        # Patterns for Billion (Miliard)
        # 2.5 miliard, 2 miliard, 2B
        miliard_pattern = re.search(r'(\d+(?:\.\d+)?)\s*(میلیارد|ملیارد|بیلیون)', text)
        if miliard_pattern:
            num = float(miliard_pattern.group(1))
            return int(num * 1_000_000_000)

        # Patterns for Million
        # 500 million, 500M
        million_pattern = re.search(r'(\d+(?:\.\d+)?)\s*(میلیون|ملیون)', text)
        if million_pattern:
            num = float(million_pattern.group(1))
            return int(num * 1_000_000)

        # Plain numbers with "Toman" implies context. 
        # Often people say "100 toman" meaning "100 million" in real estate, 
        # BUT strictly it means 100. Let's look for explicit large numbers or assume context if needed.
        # For now, let's stick to explicit units or explicit large numbers.
        
        # Explicit large number > 10,000,000
        # 2000000000
        large_num_pattern = re.search(r'\b(\d{8,15})\b', text)
        if large_num_pattern:
            return int(large_num_pattern.group(1))

        return None

    def extract_area(self, text: str) -> Optional[int]:
        """Values followed by 'metr'."""
        # "120 metr", "120 metri"
        pattern = re.search(r'(\d+)\s*(متر|متری)', text)
        if pattern:
            return int(pattern.group(1))
        return None

    def extract_transaction_type(self, text: str) -> Optional[str]:
        """Buy/Sell/Rent/Mortgage."""
        if any(w in text for w in ['خرید', 'فروش', 'میخرم', 'بخرم', 'دنبال']):
            return 'فروش' # User wants to buy, so we look for "Sale" (فروش) ads
        if any(w in text for w in ['اجاره', 'راهن', 'رهن']):
            return 'اجاره'
        if any(w in text for w in ['معاوضه', 'طاق', 'تعویض']):
            return 'معاوضه'
        return None

    def extract_property_type(self, text: str) -> Optional[str]:
        """Apartment, Villa, etc."""
        if 'آپارتمان' in text:
            return 'آپارتمان'
        if 'ویلا' in text or 'ویلایی' in text:
            return 'ویلا'
        if 'مغازه' in text or 'تجاری' in text:
            return 'مغازه'
        if 'زمین' in text or 'کلنگی' in text:
            return 'زمین'
        if 'اداری' in text or 'دفتر' in text:
            return 'اداری'
        return None

    def extract_district(self, text: str) -> Optional[str]:
        """Find mentioned district or neighborhood."""
        # Common districts in Tehran and Gorgan (examples)
        districts = [
            "نیاوران", "زعفرانیه", "سعادت آباد", "پاسداران", "ونک", "تجریش", # Tehran
            "ناهارخوران", "صیاد شیرازی", "گلشهر", "نهضت", "عدالت", "گرگانپارس" # Gorgan
        ]
        for district in districts:
            if re.search(rf'(?:\b|در |تو |محله ){district}(?:\b|ی | )', text):
                return district
                
        # Regex for "District X" or "Neighborhood Y"
        neighborhood_pattern = re.search(r'(?:محله|منطقه|خیابان)\s*([آ-یa-z]+)', text)
        if neighborhood_pattern:
            return neighborhood_pattern.group(1)
            
        return None

    def extract_exchange_intent(self, text: str) -> Optional[bool]:
        """Detect if user explicitly wants to check for exchange (Find all exchanges command)."""
        keywords = ['معاوضه', 'طاق', 'تعویض', 'تاخت']
        if any(w in text for w in keywords):
            # Special check for "find all exchanges" command
            if any(cmd in text for cmd in ['پیدا کن', 'بگرد', 'نشون بده', 'بیار']):
                return True
            return True
        return None
