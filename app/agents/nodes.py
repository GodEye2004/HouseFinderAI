from app.agents.state import AgentState
from app.models.property import UserRequirements, PropertyType, TransactionType, DocumentType
from app.services.decision_engine import DecisionEngine
from app.services.matching import ExchangeMatchingService
from app.services.llm_service import RealEstateLLMService
from app.services.memory_service import ConversationMemory
from app.services.property_manager import property_manager


# ایجاد instance ها
llm_service = RealEstateLLMService()
decision_engine = DecisionEngine()
matching_service = ExchangeMatchingService()


def chat_node(state: AgentState) -> AgentState:
    """
    نود اصلی چت - همه چیز اینجا انجام میشه
    LLM کنترل کامل رو داره
    """

    # بررسی اینکه پیامی وجود داره
    if not state["messages"] or len(state["messages"]) == 0:
        state["next_message"] = "سلام! من هومنگرم ، مشاور املاک شما 👋\nچطور می‌تونم کمکتون کنم؟"
        state["needs_user_input"] = True
        state["current_stage"] = "greeting"
        return state

    last_message = state["messages"][-1]["content"]
    memory = state["memory"]
    requirements = state["requirements"]

    print(f"\n{'=' * 60}")
    print(f"📨 پیام کاربر: {last_message}")
    print(f"🧠 حافظه فعلی: {list(memory.facts.keys())}")

    # فهم کامل پیام با LLM
    if llm_service.enabled:
        try:
            understanding = llm_service.understand_and_extract(
                last_message,
                memory,
                state["messages"][:-1]
            )

            print(f"🤖 Intent: {understanding.get('user_intent')}")
            print(f"📊 Extracted: {understanding.get('extracted_info')}")

            extracted = understanding.get('extracted_info', {})
            user_intent = understanding.get('user_intent', 'chat')

            # آپدیت حافظه و requirements
            _update_memory_and_requirements(extracted, memory, requirements, state)

            print(f"✅ حافظه بعد آپدیت: {list(memory.facts.keys())}")
            print(
                f"✅ Requirements: budget={requirements.budget_max}, city={requirements.city}, type={requirements.property_type}")

            # ⭐ CRITICAL: تصمیم‌گیری درست
            should_search = _should_search(memory)
            
            # برای معاوضه همیشه اول ببینیم اطلاعات کافیه یا نه
            if extracted.get('wants_exchange') or state.get("wants_exchange"):
                 # اگر آیتم یا ارزش مشخص نیست، جستجو نکن تا اول بپرسی
                 if not (memory.get_fact('exchange_item') or extracted.get('exchange_item')) or \
                    not (memory.get_fact('exchange_value') or extracted.get('exchange_value')):
                     should_search = False

            print(f"🔍 آیا باید جستجو کنم؟ {should_search}")

            # فقط اگه واقعا اطلاعات کافی داریم جستجو کن
            if should_search and (user_intent == 'search' or len(extracted) > 0):
                print("🎯 در حال جستجو...")
                state = _perform_search(state, memory, requirements)
            elif user_intent == 'exchange' or state.get("wants_exchange"):
                print("🔄 در حال پردازش معاوضه...")
                state = _handle_exchange(state, memory)
            else:
                print("💬 ادامه گفتگو و دریافت اطلاعات...")
                state = _generate_chat_response(state, memory, last_message)

        except Exception as e:
            print(f"❌ خطا در پردازش LLM: {e}")
            # تلاش برای استخراج دستی
            _simple_extraction(last_message, memory, requirements)
            state = _generate_chat_response_fallback(state, memory, last_message)
            
    else:
        print("⚠️ LLM غیرفعال - استفاده از fallback")
        # تلاش برای استخراج دستی
        _simple_extraction(last_message, memory, requirements)
        state = _generate_chat_response_fallback(state, memory, last_message)

    state["requirements"] = requirements
    state["memory"] = memory
    state["needs_user_input"] = True

    print(f"📤 پاسخ: {state['next_message'][:100]}...")
    print(f"{'=' * 60}\n")

    return state

def _simple_extraction(text: str, memory: ConversationMemory, requirements: UserRequirements):
    """استخراج ساده بر اساس کلمات کلیدی برای زمانی که LLM کار نمی‌کند"""
    text = text.lower()
    
    # نوع ملک
    if "آپارتمان" in text:
        memory.add_fact('property_type', "آپارتمان")
        requirements.property_type = PropertyType.APARTMENT
    elif "ویلا" in text:
        memory.add_fact('property_type', "ویلا")
        requirements.property_type = PropertyType.VILLA
    elif "مغازه" in text:
        memory.add_fact('property_type', "مغازه")
        requirements.property_type = PropertyType.STORE
    elif "زمین" in text:
        memory.add_fact('property_type', "زمین")
        requirements.property_type = PropertyType.LAND
        
    # شهر
    cities = ["تهران", "کرج", "شیراز", "اصفهان", "مشهد", "تبریز", "رشت"]
    for city in cities:
        if city in text:
            memory.add_fact('city', city)
            requirements.city = city
            break
            
    # نوع معامله
    if "اجاره" in text or "رهن" in text:
        memory.add_fact('transaction_type', "اجاره")
        requirements.transaction_type = TransactionType.RENT
    elif "خرید" in text or "فروش" in text:
        memory.add_fact('transaction_type', "فروش")
        requirements.transaction_type = TransactionType.SALE
    elif "معاوضه" in text:
        memory.add_fact('transaction_type', "معاوضه")
        requirements.transaction_type = TransactionType.EXCHANGE
        memory.add_fact('wants_exchange', True)


def _update_memory_and_requirements(extracted: dict, memory: ConversationMemory,
                                    requirements: UserRequirements, state: AgentState):
    """آپدیت حافظه و requirements بر اساس اطلاعات استخراج شده"""

    for key, value in extracted.items():
        if value is not None and value != "":
            memory.add_fact(key, value)

            # آپدیت requirements
            if hasattr(requirements, key):
                if key == 'property_type' and isinstance(value, str):
                    type_map = {
                        "آپارتمان": PropertyType.APARTMENT,
                        "ویلا": PropertyType.VILLA,
                        "مغازه": PropertyType.STORE,
                        "زمین": PropertyType.LAND,
                        "اداری": PropertyType.OFFICE
                    }
                    mapped_value = type_map.get(value)
                    if mapped_value:
                        setattr(requirements, key, mapped_value)
                        print(f"   ✓ property_type = {mapped_value}")

                elif key == 'transaction_type' and isinstance(value, str):
                    trans_map = {
                        "فروش": TransactionType.SALE,
                        "اجاره": TransactionType.RENT,
                        "معاوضه": TransactionType.EXCHANGE
                    }
                    mapped_value = trans_map.get(value)
                    if mapped_value:
                        setattr(requirements, key, mapped_value)
                        print(f"   ✓ transaction_type = {mapped_value}")

                elif key == 'document_type' and isinstance(value, str):
                    doc_map = {
                        "تک برگ": DocumentType.SINGLE_PAGE,
                        "مشاع": DocumentType.COOPERATIVE,
                        "وقفی": DocumentType.ENDOWMENT,
                        "اجاره‌ای": DocumentType.LEASE
                    }
                    mapped_value = doc_map.get(value)
                    if mapped_value:
                        setattr(requirements, key, mapped_value)
                        print(f"   ✓ document_type = {mapped_value}")
                else:
                    setattr(requirements, key, value)
                    print(f"   ✓ {key} = {value}")

    # بررسی معاوضه
    if extracted.get('wants_exchange'):
        state["wants_exchange"] = True
        memory.add_fact('wants_exchange', True)

        if extracted.get('exchange_item'):
            state["exchange_item"] = extracted['exchange_item']
            memory.add_entity('exchange_items', extracted['exchange_item'])

        if extracted.get('exchange_value'):
            state["exchange_value"] = extracted['exchange_value']

    # ---------------------------------------------------------
    # محاسبه قدرت خرید کل (بودجه نقد + ارزش معاوضه)
    # ---------------------------------------------------------
    # آیا معاوضه داریم؟
    is_exchanging = state.get("wants_exchange") or extracted.get("wants_exchange") or memory.get_fact("wants_exchange")
    
    if is_exchanging:
        # بودجه نقد (از اکسترکت جدید یا حافظه)
        cash_budget = extracted.get('budget_max')
        if not cash_budget:
            cash_budget = memory.get_fact('budget_max')
            
        # ارزش معاوضه (از اکسترکت جدید یا حافظه)
        exchange_val = extracted.get('exchange_value')
        if not exchange_val:
            exchange_val = memory.get_fact('exchange_value')
            
        # اگر هر دو را داریم، جمع بزن
        if cash_budget and exchange_val:
            total_budget = int(cash_budget) + int(exchange_val)
            requirements.budget_max = total_budget
            print(f"   💰 بودجه کل محاسبه شده: {cash_budget:,} (نقد) + {exchange_val:,} (معاوضه) = {total_budget:,} تومان")


def _should_search(memory: ConversationMemory) -> bool:
    """
    تصمیم‌گیری خودکار: آیا باید جستجو کنیم؟
    """
    # بررسی فیلدهای الزامی
    has_budget = memory.get_fact('budget_max') is not None
    has_city = memory.get_fact('city') is not None
    has_type = memory.get_fact('property_type') is not None
    has_area = memory.get_fact('area_min') is not None
    has_transaction = memory.get_fact('transaction_type') is not None

    print(f"   💰 بودجه: {has_budget}")
    print(f"   🏙 شهر: {has_city}")
    print(f"   🏠 نوع: {has_type}")
    print(f"   🔄 معامله: {has_transaction}")
    print(f"   📐 متراژ: {has_area}")

    # اگر کاربر درخواست جستجو کرده (در intent)، که در نود چک می‌شود
    # اینجا فقط تصمیم می‌گیریم آیا "بدون درخواست صریح" جستجو کنیم یا نه

    # اگر فقط شهر و نوع معامله را داریم، هنوز جستجو نکن تا بقیه سوالات را بپرسیم
    if has_city and has_transaction and not (has_budget or has_area):
        return False

    # اگر شهر، نوع معامله و (بودجه یا متراژ) را داریم، جستجو کن
    if has_city and has_transaction and (has_budget or has_area):
        return True
    
    # حالت‌های قدیمی برای پشتیبانی
    important_fields = [has_budget, has_city, has_type, has_transaction, has_area]
    count = sum(important_fields)

    print(f"   📊 تعداد فیلدهای پر شده: {count}/5")

    # اگر شهر را نداریم اما 3 مورد دیگر را داریم
    if count >= 3 and not has_city:
        return True

    return False


def _perform_search(state: AgentState, memory: ConversationMemory,
                    requirements: UserRequirements) -> AgentState:
    """انجام جستجو و نمایش نتایج"""

    all_properties = property_manager.get_all_properties()

    print(f"   📦 تعداد کل املاک: {len(all_properties)}")

    # جستجو با موتور تصمیم
    decision_result = decision_engine.make_decision(all_properties, requirements)

    state["search_results"] = decision_result.get("properties", [])
    state["decision_summary"] = decision_result.get("decision_summary", {})
    state["recommendations"] = decision_result.get("recommendations", [])

    print(f"   ✅ نتایج: {len(state['search_results'])} ملک")
    print(f"   📊 وضعیت: {decision_result['status']}")

    if decision_result["status"] == "need_more_info":
        # اگر اطلاعات کافی نبود، بپرس
        missing = decision_result.get("missing_fields", [])
        if "city" in missing:
            state["next_message"] = "لطفا شهر مورد نظر را بفرمایید."
        else:
            state["next_message"] = "اطلاعات بیشتری نیاز است."
        state["current_stage"] = "need_info"
        return state

    # تولید پاسخ با LLM
    if decision_result["status"] == "no_results":
        context = {
            'stage': 'no_results',
            'decision_summary': decision_result.get("decision_summary", {}),
            'recommendations': decision_result.get("recommendations", [])
        }

        if llm_service.enabled:
            state["next_message"] = llm_service.generate_natural_response(
                context=context,
                user_message="نتیجه‌ای پیدا نشد",
                memory=memory,
                conversation_history=state["messages"]
            )
        else:
            state["next_message"] = "متاسفانه ملک مناسبی پیدا نشد 😔"
    else:
        # موفقیت - نمایش نتایج
        results = state["search_results"][:3]
        properties_data = []

        if not results:
             state["next_message"] = "متاسفانه با معیارهای شما ملکی پیدا نشد."
             state["current_stage"] = "results_shown"
             return state

        for score in results:
            prop = property_manager.get_property_by_id(score.property_id)

            if prop:
                properties_data.append({
                    "title": prop.title,
                    "price": prop.price,
                    "price_formatted": f"{prop.price:,} تومان",
                    "area": prop.area,
                    "location": f"{prop.city}، {prop.district}",
                    "match_percentage": score.match_percentage,
                    "bedrooms": prop.bedrooms,
                    "year_built": prop.year_built,
                    "document_type": prop.document_type.value if prop.document_type else None,
                    "has_parking": prop.has_parking,
                    "has_elevator": prop.has_elevator,
                    "has_storage": prop.has_storage,
                    "phone": prop.owner_phone,
                })

        # LLM نتایج رو فرمت می‌کنه
        if llm_service.enabled:
            formatted = llm_service.format_search_results(properties_data, memory)
            if formatted:
                state["next_message"] = formatted
            else:
                state["next_message"] = _format_simple(properties_data)
        else:
            state["next_message"] = _format_simple(properties_data)

    state["current_stage"] = "results_shown"
    return state


def _handle_exchange(state: AgentState, memory: ConversationMemory) -> AgentState:
    """مدیریت معاوضه"""

    exchange_item = memory.get_fact('exchange_item')
    exchange_value = memory.get_fact('exchange_value')

    # اگر مقدار جدیدی در استیت بود، اون رو هم چک کن (برای آپدیت لحظه‌ای)
    if state.get("exchange_value"):
         exchange_value = state["exchange_value"]

    print(f"   🔄 آیتم معاوضه: {exchange_item}")
    print(f"   💵 ارزش: {exchange_value}")

    # اگر اطلاعات کامل نیست، LLM می‌پرسه
    if not exchange_item or not exchange_value:
        if llm_service.enabled:
            state["next_message"] = llm_service.handle_exchange_conversation(
                memory,
                state["messages"]
            )
        else:
            if not exchange_item:
                state["next_message"] = "چی می‌خوای معاوضه کنی؟"
            else:
                state["next_message"] = "ارزشش چقدره؟"

        state["current_stage"] = "exchange_info_needed"
        return state

    # جستجوی املاک قابل معاوضه
    exchange_properties = property_manager.get_exchange_properties()

    matches = matching_service.find_exchange_matches(
        exchange_item,
        exchange_value,
        exchange_properties
    )

    state["exchange_matches"] = matches
    print(f"   ✅ تطابق‌های پیدا شده: {len(matches)}")

    # تولید پاسخ با LLM
    if matches:
        matches_data = []
        for match in matches[:3]:
            prop = match["property"]
            matches_data.append({
                "title": prop.title,
                "price": prop.price,
                "match_score": match["match_score"],
                "additional_payment": match["additional_payment_needed"],
                "phone": prop.owner_phone
            })

        context = {
            'stage': 'exchange_results',
            'exchange_item': exchange_item,
            'exchange_value': exchange_value,
            'matches': matches_data
        }

        if llm_service.enabled:
            state["next_message"] = llm_service.generate_natural_response(
                context=context,
                user_message="املاک معاوضه",
                memory=memory,
                conversation_history=state["messages"]
            )
        else:
            state["next_message"] = _format_exchange_simple(matches_data)
    else:
        context = {
            'stage': 'no_exchange_match',
            'exchange_item': exchange_item
        }

        if llm_service.enabled:
            state["next_message"] = llm_service.generate_natural_response(
                context=context,
                user_message="معاوضه پیدا نشد",
                memory=memory,
                conversation_history=state["messages"]
            )
        else:
            state["next_message"] = f"متاسفانه ملکی برای معاوضه با {exchange_item} پیدا نشد."

    state["current_stage"] = "exchange_shown"
    return state


def _generate_chat_response_fallback(state: AgentState, memory: ConversationMemory,
                                     user_message: str) -> AgentState:
    """fallback هوشمند بدون LLM - گفتگوی ساده ولی کاربردی"""

    user_lower = user_message.lower()

    # سلام و خوشامد
    if any(word in user_lower for word in ['سلام', 'hi', 'hello']):
        state["next_message"] = "سلام! خوش اومدید 👋\nدنبال چه نوع ملکی می‌گردید؟ (آپارتمان، ویلا، مغازه)"
        state["current_stage"] = "chatting"
        return state

    # بررسی اطلاعات موجود
    has_type = memory.get_fact('property_type')
    has_city = memory.get_fact('city')
    has_budget = memory.get_fact('budget_max')
    has_trans = memory.get_fact('transaction_type')

    # اگر نوع معامله یا نوع ملک مشخص نیست
    if not has_type and not has_trans:
        state["next_message"] = "دنبال خرید هستید یا اجاره؟ و چه نوع ملکی؟ (آپارتمان، ویلا...)"
    
    elif not has_city:
        state["next_message"] = "در کدام شهر و محله دنبال ملک هستید؟"

    elif not has_budget:
        if has_trans == TransactionType.RENT or has_trans == "اجاره":
             state["next_message"] = "چقدر برای رهن و اجاره در نظر دارید؟ متراژ چطور؟"
        else:
             state["next_message"] = "سقف بودجه شما چقدر است؟ و چه متراژی مد نظرتونه؟"
             
    elif not has_area:
        state["next_message"] = "چه متراژی مد نظرتونه؟ و آیا مایل به معاوضه هستید؟"

    elif not has_type:
        state["next_message"] = "چه نوع ملکی مد نظرتونه؟ (آپارتمان، ویلا، مغازه)"
        
    else:
        # اطلاعات کافی داریم
        state["next_message"] = "اطلاعات خوبی دارم. می‌تونم برات جستجو کنم؟"

    state["current_stage"] = "chatting"
    return state

def _generate_chat_response(state: AgentState, memory: ConversationMemory,
                            user_message: str) -> AgentState:
    """تولید پاسخ گفتگوی طبیعی"""

    # LLM کنترل کامل رو داره
    context = {
        'stage': 'chatting',
        'has_enough_info': _should_search(memory),
    }

    if llm_service.enabled:
        state["next_message"] = llm_service.generate_natural_response(
            context=context,
            user_message=user_message,
            memory=memory,
            conversation_history=state["messages"]
        )
    else:
        # fallback ساده
        if not memory.get_fact('budget_max'):
            state["next_message"] = "بودجه‌ت چقدره؟"
        elif not memory.get_fact('city'):
            state["next_message"] = "کدوم شهر دنبال می‌گردی؟"
        elif not memory.get_fact('property_type'):
            state["next_message"] = "چه نوع ملکی می‌خوای؟"
        else:
            state["next_message"] = "بذار برات جستجو کنم!"

    state["current_stage"] = "chatting"
    return state

def _simple_chat_fallback(state: AgentState, user_message: str) -> AgentState:
    """fallback خیلی ساده"""
    state["next_message"] = "سلام! چطور می‌تونم کمکت کنم؟ دنبال چه نوع ملکی می‌گردی؟"
    state["current_stage"] = "chatting"
    return state


def _format_simple(properties: list) -> str:
    """فرمت ساده نتایج"""
    if not properties:
        return "متاسفانه ملکی پیدا نشد."

    message = f"🎉 {len(properties)} ملک عالی پیدا کردم!\n\n"

    for i, prop in enumerate(properties, 1):
        message += f"{'=' * 50}\n"
        message += f"🏠 {i}. {prop['title']}\n"
        message += f"💰 قیمت: {prop['price_formatted']}\n"
        message += f"📐 متراژ: {prop['area']} متر\n"
        message += f"📍 {prop['location']}\n"
        message += f"📊 تطابق: {prop['match_percentage']}%\n"
        message += f"📞 {prop['phone']}\n\n"

    return message


def _format_exchange_simple(matches: list) -> str:
    """فرمت ساده معاوضه"""
    if not matches:
        return "متاسفانه ملکی برای معاوضه پیدا نشد."

    message = f"🔄 {len(matches)} ملک قابل معاوضه:\n\n"

    for i, match in enumerate(matches, 1):
        message += f"{i}. {match['title']}\n"
        message += f"   قیمت: {match['price']:,} تومان\n"
        message += f"   تطابق: {match['match_score']}%\n"
        if match['additional_payment'] > 0:
            message += f"   پرداخت اضافی: {match['additional_payment']:,} تومان\n"
        message += f"   📞 {match['phone']}\n\n"

    return message