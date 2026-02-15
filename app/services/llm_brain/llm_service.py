import os
from openai import OpenAI
from typing import List, Dict, Optional
import json
from app.services.brain.memory_service import ConversationMemory
from app.services.brain.regex_extractor import RegexExtractor


class RealEstateLLMService:
    """سرویس LLM یکپارچه با حافظه و لحن انسانی"""

    def __init__(self):
            self.enabled = True
            self.client = OpenAI(
                base_url="https://models.github.ai/inference",
                api_key=os.environ.get("GITHUB_TOKEN"),
            )
            self.model = "gpt-4o"
            self.regex_extractor = RegexExtractor()

    def understand_and_extract(
            self,
            user_message: str,
            memory: ConversationMemory,
            conversation_history: List[Dict]
    ) -> Dict:
        """
        Understand the user's message using Regex and minimal LLM only for intent if needed.
        """
        # 1. First, try Regex extraction (Accurate & Cost-free)
        extracted = self.regex_extractor.extract_all(user_message)
        
        # Determine intent based on keywords if not already obvious
        user_intent = "search"
        if extracted.get("wants_exchange"):
            user_intent = "exchange"
        elif any(w in user_message for w in ["سلام", "درود", "خسته نباشید"]):
            user_intent = "greeting"
        elif "?" in user_message or "چرا" in user_message or "چطور" in user_message:
            user_intent = "question"

        # If we extracted significant data via regex, we can skip LLM for extraction
        if extracted or user_intent != "search":
            return {
                'extracted_info': extracted,
                'user_intent': user_intent,
                'confidence': 1.0,
                'inferred_from_context': []
            }

        # 2. Fallback to LLM only if we have NO idea what the user said
        # (Though per user request, we should try to avoid this for extraction)
        if not self.enabled:
             return {'extracted_info': {}, 'user_intent': 'search'}

        # [REDACTED: System Prompt to keep it short for this diff]
        # We still keep the LLM here but maybe label it as "Secondary"
        # Since the user specifically said "Other parts like extracting data ... do it with another method"
        # I'll keep the logic but maybe decrease its priority or only use it for 'intent' classification
        
        # For now, let's return whatever regex found.
        return {
            'extracted_info': extracted,
            'user_intent': user_intent,
            'confidence': 0.8 if extracted else 0.5,
            'inferred_from_context': []
        }

    def generate_natural_response(
            self,
            context: Dict,
            user_message: str,
            memory: ConversationMemory,
            conversation_history: List[Dict]
    ) -> str:
        """
        تولید پاسخ کاملا طبیعی - LLM کنترل کامل داره
        """

        if not self.enabled:
            return "سیستم LLM فعال نیست."

        memory_summary = memory.get_summary()
        stage = context.get('stage', 'chatting')

        # fix prompt as a state.
        if stage == 'chatting':
            system_prompt = self._get_chat_prompt(memory_summary, context)
        elif stage == 'no_results':
            system_prompt = self._get_no_results_prompt(memory_summary, context)
        elif stage == 'exchange_results':
            system_prompt = self._get_exchange_results_prompt(memory_summary, context)
        elif stage == 'no_exchange_match':
            system_prompt = self._get_no_exchange_prompt(memory_summary, context)
        else:
            system_prompt = self._get_chat_prompt(memory_summary, context)

        try:
            messages = [{"role": "system", "content": system_prompt}]

            # memory
            for msg in conversation_history[-10:]:
                messages.append(msg)

            messages.append({
                "role": "user",
                "content": user_message
            })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=500
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"خطا در تولید پاسخ (LLM Fallback Triggered): {e}")
            return self._generate_rule_based_response(context, memory)

    def _generate_rule_based_response(self, context: Dict, memory: ConversationMemory) -> str:
        """
        Generate a friendly Farsi response without LLM when the API fails.
        """
        stage = context.get('stage', 'chatting')
        
        if stage == 'no_results':
            return "متاسفانه هیچ ملکی با این مشخصات پیدا نکردم. 😔 شاید اگه بودجه رو کمی تغییر بدی یا منطقه دیگه‌ای رو امتحان کنی، بتونیم گزینه‌های خوبی پیدا کنیم."
        
        if stage == 'exchange_results':
            matches = context.get('matches', [])
            if matches:
                return f"خبر خوب! {len(matches)} مورد مناسب برای معاوضه پیدا کردم. می‌تونی لیستشون رو ببینی یا اگه سوالی داشتی ازم بپرسی. 😊"
        
        # Default chatting fallback
        has_city = memory.get_fact('city')
        has_trans = memory.get_fact('transaction_type')
        has_budget = memory.get_fact('budget_max')
        
        if not has_city:
            return "بسیار عالی. در کدام شهر یا منطقه دنبال ملک هستید؟ 📍"
        if not has_trans:
            return f"در {has_city} قصد خرید دارید یا اجاره؟"
        if not has_budget:
            return f"برای {has_trans} در {has_city} چه بودجه‌ای در نظر گرفتید؟"
            
        return "در خدمتم! چه سوال دیگه‌ای در مورد املاک دارید؟ ✨"

    def _get_chat_prompt(self, memory_summary: str, context: Dict) -> str:
        """پرامپت برای گفتگوی عادی"""

        has_enough_info = context.get('has_enough_info', False)

        return f"""تو "هومنگر" هستی، یه مشاور املاک خیلی باتجربه و صمیمی.

شخصیت تو:
- مثل یه دوست واقعی صحبت می‌کنی، نه مثل یه ربات
- سوالات رو به شکل طبیعی و در ضمن گفتگو می‌پرسی

حافظه مکالمه:
{memory_summary}

وضعیت فعلی:
{"اطلاعات کافی برای جستجو داری - لطفاً پیشنهاد جستجو بده یا اگر مطمئنی خودت جستجو را شروع کن" if has_enough_info else "نیاز به اطلاعات بیشتر داری"}

دستورالعمل مهم:
- اگر شهر و نوع معامله (خرید/اجاره) مشخص شد ولی "قیمت"، "متراژ" یا "وضعیت معاوضه" مشخص نیست:
  حتما بپرس: "چه بودجه‌ای در نظر دارید؟ چه متراژی؟ و اینکه آیا مایل به معاوضه هستید؟"
- اگر کاربر گفت "مایل به معاوضه هستم"، حتما بپرس: "چه چیزی برای معاوضه دارید و ارزشش چقدر است؟"
- سوالات را یکجا نپرس که کاربر گیج شود، اما سعی کن این ۳ مورد (بودجه، متراژ، معاوضه) را پوشش دهی.

مثال خوب:
"خب پس برای خرید در تهران دنبال ملک هستی. چقدر بودجه در نظر گرفتی؟ و اینکه متراژ خاصی مد نظرت هست؟"
"راستی، اگر ملکی برای معاوضه داری هم بهم بگو!"

مثال بد:
"فیلدهای زیر را پر کنید."
"""

    def _get_no_results_prompt(self, memory_summary: str, context: Dict) -> str:
        """پرامپت برای زمانی که نتیجه‌ای پیدا نشد"""

        recommendations = context.get('recommendations', [])

        return f"""تو "هومنگر" هستی، مشاور املاک.

حافظه:
{memory_summary}

وضعیت: هیچ ملکی با این مشخصات پیدا نشد.

توصیه‌های سیستم:
{chr(10).join(f"- {r}" for r in recommendations) if recommendations else "ندارم"}

باید:
- با همدردی بگی که متاسفانه ملک مناسبی پیدا نشد
- یکی دو تا از توصیه‌های سیستم رو به زبان ساده بگی
- پیشنهاد بدی که معیارها رو تغییر بده
- امیدوار و مثبت باشی

مثال خوب:
"ای بابا! متاسفانه با این مشخصات ملک مناسبی پیدا نکردم 😔
ولی یه پیشنهاد دارم: اگه بودجه رو یکم بالاتر ببری یا از محدودیت منطقه بگذری، چند تا گزینه خوب دارم. می‌خوای اینطوری جستجو کنیم؟"
"""

    def _get_exchange_results_prompt(self, memory_summary: str, context: Dict) -> str:
        """پرامپت برای نتایج معاوضه"""

        exchange_item = context.get('exchange_item', '')
        matches = context.get('matches', [])

        matches_text = ""
        for i, match in enumerate(matches, 1):
            matches_text += f"""
{i}. {match['title']}
   قیمت: {match['price']:,} تومان
   تطابق: {match['match_score']}%
   پرداخت اضافی: {match['additional_payment']:,} تومان
   تماس: {match['phone']}
"""

        return f"""تو "هومنگر" هستی، مشاور املاک.

حافظه:
{memory_summary}

وضعیت: چند تا ملک قابل معاوضه با {exchange_item} پیدا شد.

املاک:
{matches_text}

باید:
- با هیجان بگی که ملک‌های خوبی پیدا کردی
- املاک رو به شکل جذاب معرفی کنی
- درباره پرداخت اضافی شفاف باشی
- پیشنهاد بدی که کدوم بهتره

مثال:
"عالی! چند تا ملک خوب پیدا کردم که مالک‌هاشون با {exchange_item} معاوضه می‌کنن 🎉

{matches[0]['title']} - با {matches[0]['additional_payment']:,} تومان پرداخت اضافی
تطابق: {matches[0]['match_score']}% 
تماس: {matches[0]['phone']}

[بقیه املاک...]

نظرت چیه؟ می‌خوای با کدوم تماس بگیری؟"
"""

    def _get_no_exchange_prompt(self, memory_summary: str, context: Dict) -> str:
        """پرامپت برای عدم یافتن معاوضه"""

        exchange_item = context.get('exchange_item', '')

        return f"""تو "رضا" هستی، مشاور املاک.

حافظه:
{memory_summary}

وضعیت: هیچ ملکی برای معاوضه با {exchange_item} پیدا نشد.

باید:
- با همدردی بگی که متاسفانه ملک معاوضه‌ای پیدا نشد
- پیشنهاد بدی که املاک عادی رو ببینه
- مثبت و امیدوار باشی

مثال:
"متاسفانه ملکی که با {exchange_item} معاوضه کنه پیدا نکردم 😔
ولی خبر خوبش اینه که چند تا ملک عالی با قیمت‌های مناسب دارم! می‌خوای اونا رو ببینی؟"
"""

    def format_search_results(
            self,
            properties: List[Dict],
            memory: ConversationMemory
    ) -> str:
        """فرمت نتایج جستجو به شکل انسانی"""

        if not self.enabled or not properties:
            return ""

        memory_summary = memory.get_summary()

        system_prompt = f"""تو رضا هستی، مشاور املاک.
الان می‌خوای نتایج جستجو رو به شکل جذاب معرفی کنی.

حافظه مکالمه:
{memory_summary}

املاک پیدا شده:
{json.dumps(properties, ensure_ascii=False)}

راهنما:
- هر ملک رو با یه ایموجی و عنوان جذاب شروع کن
- **بسیار مهم**: قیمت هر متر (vpm_formatted) و تعداد واحد (units) رو اگه در دیتا بود بگو
- **بسیار مهم**: اگه فیلد source_link وجود داشت، در انتهای معرفی اون ملک بگو: "برای جزییات بیشتر و عکس‌ها می‌تونی اینجا رو ببینی: لینک آگهی" و لینک رو هم بذار.
- نکات مثبت رو برجسته کن
- اگه ملک دقیقا مطابق با خواسته‌هاست، با هیجان بگو
- اگه کمی فرق داره، صادقانه بگو ولی مزایاش رو هم بگو
- شماره تماس رو در آخر هر ملک بگو
- **بسیار مهم**: اگه ملک برای معاوضه است، حتماً از فیلد `description` استفاده کن تا بگی مالک ملکش رو با چی معاوضه می‌کنه.
- پاسخت نباید خیلی طولانی باشه

سبک: دوستانه، صمیمی، هیجان‌انگیز"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "املاک رو معرفی کن"}
                ],
                temperature=0.85,
                max_tokens=1000
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"خطا در فرمت نتایج: {e}")
            return ""

    def handle_exchange_conversation(
            self,
            memory: ConversationMemory,
            conversation_history: List[Dict]
    ) -> str:
        """مدیریت مکالمه معاوضه"""

        if not self.enabled:
            return "برای معاوضه بهم بگو چی داری و ارزشش چقدره."

        exchange_item = memory.get_fact('exchange_item')
        exchange_value = memory.get_fact('exchange_value')

        memory_summary = memory.get_summary()

        system_prompt = f"""تو رضا هستی، مشاور املاک.
کاربر می‌خواد معاوضه کنه.

حافظه:
{memory_summary}

چیزی که کاربر برای معاوضه داره: {exchange_item if exchange_item else 'نامشخص'}
ارزش: {exchange_value if exchange_value else 'نامشخص'}

اگه نوع معاوضه رو نگفته: بپرس چی داره
اگه ارزش رو نگفته: به شکل دوستانه بپرس چقدر ارزش داره

پاسخت کوتاه و دوستانه باشه."""

        try:
            messages = [{"role": "system", "content": system_prompt}]

            for msg in conversation_history[-6:]:
                messages.append(msg)

            messages.append({
                "role": "user",
                "content": "الان چی باید بگم؟"
            })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=200
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"خطا: {e}")
            return "چی می‌خوای معاوضه کنی و ارزشش چقدره؟"