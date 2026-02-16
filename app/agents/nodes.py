from app.agents.state import AgentState
from app.models.property import UserRequirements, PropertyType, TransactionType, DocumentType
from app.services.brain.decision_engine import DecisionEngine
from app.services.brain.matching import ExchangeMatchingService
from app.services.llm_brain.llm_service import RealEstateLLMService
from app.services.brain.memory_service import ConversationMemory
from app.services.advertisements.app_property.property_manager import property_manager

# creeat instance
llm_service = RealEstateLLMService()
decision_engine = DecisionEngine()
matching_service = ExchangeMatchingService()


def chat_node(state: AgentState) -> AgentState:
    """
   Very simple graph - just a chat node!
   LLM has full control
    """

    if not state["messages"] or len(state["messages"]) == 0:
        state["next_message"] = "سلام! من هومنگرم ، مشاور املاک شما 👋\nچطور می‌تونم کمکتون کنم؟"
        state["needs_user_input"] = True
        state["current_stage"] = "greeting"
        return state

    last_message = state["messages"][-1]["content"]
    memory = state["memory"]
    requirements = state["requirements"]

    print(f"\n{'=' * 60}")
    print(f"user message received")
    print(f"Current memory keys: {list(memory.facts.keys())}")

    # llm undrestanding
    if llm_service.enabled:
        try:
            understanding = llm_service.understand_and_extract(
                last_message,
                memory,
                state["messages"][:-1]
            )

            print(f"Intent: {understanding.get('user_intent')}")
            print(f"Extracted: {understanding.get('extracted_info')}")

            extracted = understanding.get('extracted_info', {})
            user_intent = understanding.get('user_intent', 'chat')

            _update_memory_and_requirements(extracted, memory, requirements, state)

            print(f"memory updated {list(memory.facts.keys())}")
            
            if user_intent == 'reset':
                state["requirements"] = UserRequirements()
                state["memory"] = ConversationMemory()
                state["search_results"] = []
                state["shown_properties_context"] = None
                state["next_message"] = "حافظه و فیلترها پاک شدند. از اول شروع می‌کنیم! چطور می‌تونم کمکتون کنم؟ 🔄"
                return state

            print(
                f"Requirements updated for city: {requirements.city is not None}")

            # CRITICAL: currect decision
            should_search = _should_search(memory)
            
            if extracted.get('wants_exchange') or state.get("wants_exchange"):
                 if not (memory.get_fact('exchange_item') or extracted.get('exchange_item')) or \
                    not (memory.get_fact('exchange_value') or extracted.get('exchange_value')):
                     should_search = False

            if should_search and (user_intent == 'search' or len(extracted) > 0):
                # If it's an exchange search, go here
                print("searching.....")
                state = _perform_search(state, memory, requirements)
            elif (user_intent == 'exchange' or state.get("wants_exchange")) and \
                 (memory.get_fact('exchange_item') or extracted.get('exchange_item')):
                # Only go to deal handling if we have something to exchange
                print("exchange processing....")
                state = _handle_exchange(state, memory)
            elif user_intent == 'exchange' or state.get("wants_exchange"):
                 # Force search for exchanges if no deal info provided
                 print("proactive exchange search....")
                 state = _perform_search(state, memory, requirements)
            else:
                print("continue conversation and give infornation")
                state = _generate_chat_response(state, memory, last_message)

        except Exception as e:
            print(f"Error in LLM processing: {e}")
            import traceback
            traceback.print_exc()
            
            # Ensure we fallback to rule-based extraction and response
            _simple_extraction(last_message, memory, requirements)
            state = _generate_chat_response_fallback(state, memory, last_message)
            
    else:
        print("llm disable use fallback")
        _simple_extraction(last_message, memory, requirements)
        state = _generate_chat_response_fallback(state, memory, last_message)

    state["requirements"] = requirements
    state["memory"] = memory
    state["needs_user_input"] = True

    print(f"answer sent")
    print(f"{'=' * 60}\n")

    return state

def _simple_extraction(text: str, memory: ConversationMemory, requirements: UserRequirements):
    """simple keyword based extraction for when llm is not working"""
    text = text.lower()
    
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
        
    # city
    cities = ["تهران", "کرج", "شیراز", "اصفهان", "مشهد", "تبریز", "رشت"]
    for city in cities:
        if city in text:
            memory.add_fact('city', city)
            requirements.city = city
            break
            
    # transaction type
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
    """update memory and requirements based on extracted information"""

    for key, value in extracted.items():
        if value is not None and value != "":
            memory.add_fact(key, value)

            # update requirements
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
            
            # Special case for wants_exchange boolean
            if key == 'wants_exchange' and isinstance(value, bool):
                requirements.wants_exchange = value
                print(f"   ✓ wants_exchange = {value}")
            
            # Handle district specifically if it wasn't handled by AttributeError check
            if key == 'district':
                requirements.district = value
                print(f"   ✓ district = {value}")

    # check transaction type
    if extracted.get('wants_exchange'):
        state["wants_exchange"] = True
        memory.add_fact('wants_exchange', True)

        if extracted.get('exchange_item'):
            state["exchange_item"] = extracted['exchange_item']
            memory.add_entity('exchange_items', extracted['exchange_item'])

        if extracted.get('exchange_value'):
            state["exchange_value"] = extracted['exchange_value']

    # ---------------------------------------------------------
    # calculate total purchasing power (cash budget + exchange value)
    # ---------------------------------------------------------
    # do we have transaction?
    is_exchanging = state.get("wants_exchange") or extracted.get("wants_exchange") or memory.get_fact("wants_exchange")
    
    if is_exchanging:
        # cash budget (from new statement or memory)
        cash_budget = extracted.get('budget_max')
        if not cash_budget:
            cash_budget = memory.get_fact('budget_max')
            
        # exchange value (from new extract memory)
        exchange_val = extracted.get('exchange_value')
        if not exchange_val:
            exchange_val = memory.get_fact('exchange_value')
            
        # iffwe have both , add the up +
        if cash_budget and exchange_val:
            total_budget = int(cash_budget) + int(exchange_val)
            requirements.budget_max = total_budget
            print(f"total calculate budget updated")


def _should_search(memory: ConversationMemory) -> bool:
    """
    we automate decision making => should i search?
    """
    
    # check require fileds
    has_budget = memory.get_fact('budget_max') is not None
    has_city = memory.get_fact('city') is not None
    has_type = memory.get_fact('property_type') is not None
    has_area = memory.get_fact('area_min') is not None
    has_transaction = memory.get_fact('transaction_type') is not None

    print(f"   budget: {has_budget}")
    print(f"   city: {has_city}")
    print(f"   type: {has_type}")
    print(f"    transaction: {has_transaction}")
    print(f"    area(pre meter): {has_area}")

    # If the user explicitly asks for exchanges, be PROACTIVE and search even with missing info
    wants_exchange = memory.get_fact('wants_exchange')
    if wants_exchange:
        return True

    # If the user specifies a district, it's a strong intent to search
    if memory.get_fact('district'):
        return True

    # if we only have city and transaction type, dont search yet until we ask the rest of the question.
    if has_city and has_transaction and not (has_budget or has_area):
        return False

    # if we have the city, type og transaction , and (budget or squar footage), start search.
    if has_city and has_transaction and (has_budget or has_area):
        return True
    
    # old school for cover
    important_fields = [has_budget, has_city, has_type, has_transaction, has_area]
    count = sum(important_fields)

    print(f"number of fields filled : {count}/5")

    # if we dont have the city but we have the order 3 things
    if count >= 3 and not has_city:
        return True

    return False


def _perform_search(state: AgentState, memory: ConversationMemory,
                    requirements: UserRequirements) -> AgentState:
    """start search and show result"""

    all_properties = property_manager.get_all_properties()

    print(f"all properties :  {len(all_properties)}")

    # search with decision engin
    decision_result = decision_engine.make_decision(all_properties, requirements)

    state["search_results"] = decision_result.get("properties", [])
    state["decision_summary"] = decision_result.get("decision_summary", {})
    state["recommendations"] = decision_result.get("recommendations", [])

    print(f"result: {len(state['search_results'])} properties")
    print(f"status: {decision_result['status']}")

    if decision_result["status"] == "need_more_info":
        # if infornation not enough, ask
        missing = decision_result.get("missing_fields", [])
        if "city" in missing:
            state["next_message"] = "لطفا شهر مورد نظر را بفرمایید."
        else:
            state["next_message"] = "اطلاعات بیشتری نیاز است."
        state["current_stage"] = "need_info"
        return state

    # create answer with llm(with llm we talk to user)
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
        # success , show result
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
                    "vpm": prop.vpm,
                    "vpm_formatted": f"{prop.vpm:,} تومان/متر" if prop.vpm else None,
                    "units": prop.units,
                    "location": f"{prop.city}، {prop.district}",
                    "match_percentage": score.match_percentage,
                    "bedrooms": prop.bedrooms,
                    "year_built": prop.year_built,
                    "document_type": prop.document_type.value if prop.document_type else None,
                    "has_parking": prop.has_parking,
                    "has_elevator": prop.has_elevator,
                    "has_storage": prop.has_storage,
                    "phone": prop.owner_phone,
                    "source_link": prop.source_link,
                    "image_url": prop.image_url,
                    "description": prop.description,
                })

        # Context for AI to analyze what user is seeing
        state["shown_properties_context"] = properties_data

        # Always use rule-based formatting for advertisements per user request.
        # This ensures consistent listing/cards in the Flutter UI.
        state["next_message"] = _format_simple(properties_data)

    state["current_stage"] = "results_shown"
    return state


def _handle_exchange(state: AgentState, memory: ConversationMemory) -> AgentState:
    """managing exchange"""

    exchange_item = memory.get_fact('exchange_item')
    exchange_value = memory.get_fact('exchange_value')

    #  if we have new thing in state , check it (for update it real time)
    if state.get("exchange_value"):
         exchange_value = state["exchange_value"]

    print(f"item for excheange: {exchange_item}")
    print(f"value: {exchange_value}")

    # when the information not enough , we ask with llm
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

    # search exchange properties
    exchange_properties = property_manager.get_exchange_properties()

    matches = matching_service.find_exchange_matches(
        exchange_item,
        exchange_value,
        exchange_properties
    )

    state["exchange_matches"] = matches
    print(f"find matches : {len(matches)}")

    # generate answere with llm
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

        # Always use rule-based formatting for exchange advertisements.
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
    """talk simple but informative to user with out llm , use it when llm not working"""

    user_lower = user_message.lower()

    if any(word in user_lower for word in ['سلام', 'hi', 'hello']):
        state["next_message"] = "سلام! خوش اومدید 👋\nدنبال چه نوع ملکی می‌گردید؟ (آپارتمان، ویلا، مغازه)"
        state["current_stage"] = "chatting"
        return state

    has_type = memory.get_fact('property_type')
    has_city = memory.get_fact('city')
    has_budget = memory.get_fact('budget_max')
    has_trans = memory.get_fact('transaction_type')
    has_area = memory.get_fact('area_min')

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
        state["next_message"] = "اطلاعات خوبی دارم. می‌تونم برات جستجو کنم؟"

    state["current_stage"] = "chatting"
    return state

def _generate_chat_response(state: AgentState, memory: ConversationMemory,
                            user_message: str) -> AgentState:
    """generatt nlp answere"""

    # llm has full controll
    context = {
        'stage': 'chatting',
        'has_enough_info': _should_search(memory),
    }

    if llm_service.enabled:
        state["next_message"] = llm_service.generate_natural_response(
            context=context,
            user_message=user_message,
            memory=memory,
            conversation_history=state["messages"],
            shown_properties=state.get("shown_properties_context")
        )
    else:
        # fallback simple
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
    state["next_message"] = "سلام! چطور می‌تونم کمکت کنم؟ دنبال چه نوع ملکی می‌گردی؟"
    state["current_stage"] = "chatting"
    return state


def _format_simple(properties: list) -> str:
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