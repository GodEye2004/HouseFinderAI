from app.models.property import Property, UserRequirements
from typing import List, Dict


class ExchangeMatchingService:
    """Real Estate Exchange Matching System"""

    def find_exchange_matches(
            self,
            user_exchange_item: str,
            user_exchange_value: int,
            properties: List[Property]
    ) -> List[Dict]:
        """
        Finding properties that match the user's exchange item

        Args:
            user_exchange_item: Something the user has in exchange (e.g. "car")
            user_exchange_value: Approximate value of the exchange item
            properties:Property List

        Returns:
            List of properties suitable for exchange
        """
        matches = []

        for prop in properties:
            if not prop.open_to_exchange or not prop.exchange_preferences:
                continue

            # بررسی تطابق نوع آیتم معاوضه
            item_match_score = self._calculate_item_match(
                user_exchange_item,
                prop.exchange_preferences
            )

            if item_match_score == 0:
                continue

            # بررسی تطابق ارزش
            value_match_score = self._calculate_value_match(
                user_exchange_value,
                prop.price
            )

            # محاسبه امتیاز کلی تطبیق
            total_match_score = (item_match_score * 0.6) + (value_match_score * 0.4)

            matches.append({
                "property": prop,
                "match_score": round(total_match_score, 2),
                "item_match": item_match_score,
                "value_match": value_match_score,
                "price_difference": abs(prop.price - user_exchange_value),
                "additional_payment_needed": max(0, prop.price - user_exchange_value),
                "exchange_preferences": prop.exchange_preferences
            })

        # مرتب‌سازی بر اساس امتیاز تطبیق
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        return matches

    def _calculate_item_match(self, user_item: str, property_preferences: List[str]) -> float:
        """
        محاسبه امتیاز تطبیق نوع آیتم

        Returns:
            امتیاز بین 0 تا 100
        """
        user_item_lower = user_item.lower().strip()

        # کلمات کلیدی برای تطبیق
        keywords_map = {
            "ماشین": ["ماشین", "خودرو", "اتومبیل", "car"],
            "خودرو": ["ماشین", "خودرو", "اتومبیل"],
            "ملک": ["ملک", "آپارتمان", "خانه", "property"],
            "زمین": ["زمین", "land"],
            "طلا": ["طلا", "gold", "جواهر"],
        }

        # پیدا کردن کلمات کلیدی مرتبط
        relevant_keywords = set([user_item_lower])
        for key, synonyms in keywords_map.items():
            if any(syn in user_item_lower for syn in synonyms):
                relevant_keywords.update(synonyms)

        # بررسی تطبیق با ترجیحات ملک
        for pref in property_preferences:
            pref_lower = pref.lower().strip()

            # تطبیق دقیق
            if user_item_lower in pref_lower or pref_lower in user_item_lower:
                return 100.0

            # تطبیق با کلمات کلیدی
            for keyword in relevant_keywords:
                if keyword in pref_lower:
                    return 80.0

        # تطبیق جزئی
        for pref in property_preferences:
            pref_words = set(pref.lower().split())
            user_words = set(user_item_lower.split())

            intersection = pref_words.intersection(user_words)
            if intersection:
                return 50.0

        return 0.0

    def _calculate_value_match(self, user_value: int, property_price: int) -> float:
        """
        محاسبه امتیاز تطابق ارزش

        Returns:
            امتیاز بین 0 تا 100
        """
        if property_price == 0:
            return 0.0

        # محاسبه نسبت ارزش
        ratio = user_value / property_price

        # بهترین حالت: ارزش‌ها نزدیک به هم باشند
        if 0.8 <= ratio <= 1.2:
            return 100.0
        elif 0.6 <= ratio <= 1.4:
            return 80.0
        elif 0.4 <= ratio <= 1.6:
            return 60.0
        elif 0.2 <= ratio <= 1.8:
            return 40.0
        else:
            return 20.0

    def create_exchange_proposal(
            self,
            user_item: str,
            user_value: int,
            property: Property
    ) -> Dict:
        """ایجاد پیشنهاد معاوضه"""

        price_diff = property.price - user_value

        proposal = {
            "property_id": property.id,
            "property_title": property.title,
            "property_price": property.price,
            "user_exchange_item": user_item,
            "user_exchange_value": user_value,
            "price_difference": abs(price_diff),
            "exchange_type": "متقابل" if abs(price_diff) < property.price * 0.1 else "با پرداخت اضافی"
        }

        if price_diff > 0:
            proposal["additional_payment"] = price_diff
            proposal["payment_by"] = "شما"
            proposal["description"] = (
                f"شما {user_item} خود به ارزش {user_value:,} تومان را معاوضه می‌کنید "
                f"و مبلغ {price_diff:,} تومان اضافی پرداخت می‌کنید."
            )
        elif price_diff < 0:
            proposal["additional_payment"] = abs(price_diff)
            proposal["payment_by"] = "مالک"
            proposal["description"] = (
                f"شما {user_item} خود به ارزش {user_value:,} تومان را معاوضه می‌کنید "
                f"و مبلغ {abs(price_diff):,} تومان از مالک دریافت می‌کنید."
            )
        else:
            proposal["additional_payment"] = 0
            proposal["payment_by"] = None
            proposal["description"] = (
                f"معاوضه برابر: {user_item} شما به ارزش {user_value:,} تومان "
                f"با این ملک به ارزش {property.price:,} تومان."
            )

        return proposal