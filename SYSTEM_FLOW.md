# 🏡 Real Estate Agent System - Complete Flow Documentation

## System Overview

This is an intelligent real estate conversational agent that helps users find properties through natural Persian language conversation. The system uses LLM for understanding, maintains conversation memory, and makes intelligent decisions about property matching.

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                             │
│                    (Persian Text Message)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Endpoint                            │
│                     POST /chat                                   │
│  • Creates/retrieves session                                    │
│  • Adds user message to conversation history                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                            │
│                   (create_agent_graph)                           │
│                                                                  │
│   Entry Point → chat_node → END                                 │
│                                                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CHAT NODE                                  │
│                   (Main Processing Hub)                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  1. Extract Information (LLM Service)                │      │
│  │     • understand_and_extract()                       │      │
│  │     • Extracts: city, budget, area, exchange info    │      │
│  │     • Returns: user_intent, extracted_info           │      │
│  └──────────────────┬───────────────────────────────────┘      │
│                     │                                            │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  2. Update Memory & Requirements                     │      │
│  │     • _update_memory_and_requirements()              │      │
│  │     • Updates ConversationMemory                     │      │
│  │     • Updates UserRequirements                       │      │
│  │     • Calculates total budget (cash + exchange)      │      │
│  └──────────────────┬───────────────────────────────────┘      │
│                     │                                            │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  3. Decision: Should Search?                         │      │
│  │     • _should_search()                               │      │
│  │     • Checks: city + (budget OR area)                │      │
│  └──────────────────┬───────────────────────────────────┘      │
│                     │                                            │
│         ┌───────────┴───────────┐                               │
│         │                       │                               │
│         ▼                       ▼                               │
│    [YES: Search]          [NO: Continue Chat]                  │
│         │                       │                               │
└─────────┼───────────────────────┼───────────────────────────────┘
          │                       │
          │                       ▼
          │              ┌─────────────────────────┐
          │              │ _generate_chat_response │
          │              │  • LLM generates reply  │
          │              │  • Asks for missing info│
          │              └─────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SEARCH FLOW                                   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  1. Get All Properties                               │      │
│  │     • property_manager.get_all_properties()          │      │
│  │     • Fetches from postgresSQL (APPROVED status)        │      │
│  └──────────────────┬───────────────────────────────────┘      │
│                     │                                            │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  2. Decision Engine                                  │      │
│  │     • decision_engine.make_decision()                │      │
│  │                                                       │      │
│  │     A. Check Missing Critical Info                   │      │
│  │        • Only city is mandatory                      │      │
│  │                                                       │      │
│  │     B. Apply Hard Filters                            │      │
│  │        • Transaction Type (Buy/Rent/Exchange)        │      │
│  │        • Budget (with 10% tolerance)                 │      │
│  │        • City (exact match, case-insensitive)        │      │
│  │        • Property Type (optional)                    │      │
│  │        • Area (with ±20m tolerance)                  │      │
│  │        • Document Type, Parking, etc.                │      │
│  │                                                       │      │
│  │     C. Score & Rank Properties                       │      │
│  │        • PropertyScoringSystem.rank_properties()     │      │
│  │        • Calculates match percentage                 │      │
│  │                                                       │      │
│  │     D. Generate Recommendations                      │      │
│  │        • Suggests budget adjustments                 │      │
│  │        • Suggests relaxing filters                   │      │
│  └──────────────────┬───────────────────────────────────┘      │
│                     │                                            │
│         ┌───────────┴───────────┐                               │
│         │                       │                               │
│         ▼                       ▼                               │
│   [Results Found]         [No Results]                          │
│         │                       │                               │
└─────────┼───────────────────────┼───────────────────────────────┘
          │                       │
          │                       ▼
          │              ┌─────────────────────────┐
          │              │  Smart Fallback:        │
          │              │  • Search other cities  │
          │              │  • Suggest alternatives │
          │              └─────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FORMAT & RETURN RESULTS                         │
│                                                                  │
│  • LLM formats results naturally                                │
│  • llm_service.format_search_results()                          │
│  • Returns top 3 properties with details                        │
│  • Includes: price, area, location, match %, phone              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESPONSE TO USER                              │
│                                                                  │
│  • Natural Persian language response                            │
│  • Property recommendations (if found)                          │
│  • Next question or suggestions                                 │
│  • Session saved to persistence                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Core Components

### 1. **FastAPI Application** (`app/main.py`)
**Purpose**: HTTP API layer

**Key Endpoints**:
- `POST /chat` - Main conversation endpoint
- `POST /session/new` - Create new session
- `GET /session/{id}` - Get session info
- `POST /properties/submit` - Submit new property
- `GET /properties` - List all properties

**Flow**:
```python
User Request → Create/Get Session → Invoke Graph → Save State → Return Response
```

---

### 2. **LangGraph Workflow** (`app/agents/graph.py`)
**Purpose**: Orchestrates conversation flow

**Structure**:
```python
StateGraph(AgentState)
  ├── Entry Point: "chat"
  ├── Single Node: chat_node
  └── End
```

**State Management**:
- `messages`: Conversation history
- `memory`: ConversationMemory object
- `requirements`: UserRequirements object
- `search_results`: Matched properties
- `wants_exchange`: Exchange flag
- `exchange_item`, `exchange_value`: Exchange details

---

### 3. **Chat Node** (`app/agents/nodes.py`)
**Purpose**: Main processing logic

**Key Functions**:

#### `chat_node(state: AgentState)`
Main entry point for each turn

**Process**:
1. Check if first message → Send greeting
2. Extract information using LLM
3. Update memory and requirements
4. Decide: search or continue chat
5. Generate appropriate response

#### `_update_memory_and_requirements()`
Updates both memory and requirements

**Special Logic**:
- Maps Persian terms to enums (آپارتمان → PropertyType.APARTMENT)
- Calculates total budget: `cash_budget + exchange_value`
- Stores exchange preferences

#### `_should_search()`
Decides if enough info to search

**Criteria**:
```python
if has_city and has_transaction and (has_budget or has_area):
    return True
```

#### `_perform_search()`
Executes property search

**Steps**:
1. Get all properties
2. Call decision engine
3. Handle results (success/no_results/need_more_info)
4. Format with LLM

#### `_handle_exchange()`
Manages exchange-specific flow

**Checks**:
- Exchange item specified?
- Exchange value known?
- Finds matching exchange properties

---

### 4. **LLM Service** (`app/services/llm_service.py`)
**Purpose**: Natural language understanding and generation

**Key Methods**:

#### `understand_and_extract()`
Extracts structured data from Persian text

**Input**: User message + conversation history + memory
**Output**:
```json
{
  "extracted_info": {
    "budget_max": 2000000000,
    "city": "تهران",
    "transaction_type": "فروش",
    "wants_exchange": true,
    "exchange_item": "ماشین",
    "exchange_value": 2000000000
  },
  "user_intent": "search",
  "confidence": 0.9
}
```

#### `generate_natural_response()`
Generates contextual Persian responses

**Contexts**:
- `chatting`: Asking for more info
- `no_results`: No properties found
- `exchange_results`: Exchange matches found
- `no_exchange_match`: No exchange matches

#### `format_search_results()`
Formats property list naturally

**Output**: Beautiful Persian description of properties

---

### 5. **Decision Engine** (`app/services/decision_engine.py`)
**Purpose**: Property matching logic

**Main Method**: `make_decision(properties, requirements)`

**Process**:

#### A. Check Critical Info
```python
if not requirements.city:
    return 'need_more_info'
```

#### B. Apply Hard Filters
```python
# Transaction Type (exact match)
if req.transaction_type:
    filter by transaction_type

# Budget (with 10% tolerance)
if req.budget_max:
    filter by price <= budget_max * 1.1

# City (case-insensitive, whitespace-trimmed)
if req.city:
    filter by city.strip().lower() == req.city.strip().lower()

# Property Type (optional)
if req.property_type:
    filter by property_type

# Area (with ±20m tolerance)
if req.area_min:
    filter by area >= (area_min - 20)
if req.area_max:
    filter by area <= (area_max + 20)
```

#### C. Smart Fallback
If no results in requested city:
```python
# Search globally (ignore city)
global_results = search_without_city_filter()
if global_results:
    return "Not found in Tehran, but found in Gorgan"
```
 
#### D. Score & Rank
```python
PropertyScoringSystem.rank_properties()
# Returns sorted list with match percentages
```

**Return Structure**:
```python
{
    'status': 'success' | 'no_results' | 'need_more_info',
    'properties': [PropertyScore],
    'decision_summary': {...},
    'recommendations': [...]
}
```

---

### 6. **Conversation Memory** (`app/services/memory_service.py`)
**Purpose**: Maintains conversation context

**Data Structure**:
```python
{
    'facts': {
        'city': {'value': 'تهران', 'confidence': 1.0, 'timestamp': '...'},
        'budget_max': {'value': 4000000000, ...},
        'wants_exchange': {'value': True, ...}
    },
    'entities_mentioned': {
        'exchange_items': ['ماشین']
    },
    'timeline': [...]
}
```

**Key Methods**:
- `add_fact(key, value)`: Store extracted information
- `get_fact(key)`: Retrieve stored information
- `get_summary()`: Generate human-readable summary for LLM

---

### 7. **Property Manager** (`app/services/property_manager.py`)
**Purpose**: Property CRUD operations

**Data Source**: postgresSQL

**Key Methods**:

#### `get_all_properties()`
```python
# Fetches APPROVED properties from Supabase
# Converts to Property objects
```

#### `submit_property()`
```python
# Saves new property submission
# Sets status to APPROVED by default
```

#### `get_exchange_properties()`
```python
# Returns properties with open_to_exchange = True
```

---

### 8. **Supabase Service** (`app/services/supabase_service.py`)
**Purpose**: Database operations

**Methods**:
- `insert(table, data)`: Insert record
- `select(table, filters)`: Query records
- `update(table, id, data)`: Update record
- `delete(table, id)`: Delete record

---

## Complete User Journey Example

### Scenario: User wants to buy property in Tehran with exchange

```
┌─────────────────────────────────────────────────────────────────┐
│ USER: "سلام دنبال خونم"                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    [LLM Extraction]
                    intent: "search"
                    extracted: {}
                             │
                             ▼
                    [Memory: Empty]
                    [Requirements: Empty]
                             │
                             ▼
                    [Should Search? NO]
                    (Missing: city, budget)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGENT: "کجا دنبالش هستی؟ تهران، کرج یا یه جای دیگه؟"          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ USER: "تهران خرید میخوام"                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    [LLM Extraction]
                    extracted: {
                        city: "تهران",
                        transaction_type: "فروش"
                    }
                             │
                             ▼
                    [Memory Updated]
                    facts: {city: تهران, transaction_type: فروش}
                             │
                             ▼
                    [Should Search? NO]
                    (Has city + transaction, but missing budget/area)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGENT: "چه بودجه‌ای در نظر داری؟ و متراژ چطور؟                │
│        راستی، اگه چیزی برای معاوضه داری هم بگو!"               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ USER: "۲ میلیارد دارم و یه ماشینم دارم که ارزش اونم ۲ میلیارد"│
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    [LLM Extraction]
                    extracted: {
                        budget_max: 2000000000,
                        wants_exchange: true,
                        exchange_item: "ماشین",
                        exchange_value: 2000000000
                    }
                             │
                             ▼
                    [Calculate Total Budget]
                    total = 2B + 2B = 4B
                             │
                             ▼
                    [Memory Updated]
                    facts: {
                        city: تهران,
                        transaction_type: فروش,
                        budget_max: 2000000000,
                        wants_exchange: true,
                        exchange_item: ماشین,
                        exchange_value: 2000000000
                    }
                    [Requirements Updated]
                    budget_max: 4000000000 (total)
                             │
                             ▼
                    [Should Search? YES]
                    (Has city + transaction + budget)
                             │
                             ▼
                    [Get All Properties]
                    3 properties from Supabase
                             │
                             ▼
                    [Decision Engine]
                    Apply Filters:
                    ✓ Transaction: فروش
                    ✓ Budget: <= 4.4B (4B + 10%)
                    ✓ City: تهران
                             │
                             ▼
                    [Results Found]
                    1 property: پونک 230m, 5B
                             │
                             ▼
                    [Score & Rank]
                    Match: 85%
                             │
                             ▼
                    [LLM Format Results]
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGENT: "🌟 اپارتمان مدرن در پونک                                │
│        یه فرصت عالی! این ویلا ۲۳۰ متری توی پونک...            │
│        قیمت: ۵ میلیارد تومان                                    │
│        تطابق: ۸۵٪                                                │
│        📞 ۰۹۱۱۳۶۹۰۷۱۷"                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

##  Key Intelligence Features

### 1. **Budget Calculation with Exchange**
```python
if wants_exchange:
    total_budget = cash_budget + exchange_value
    # User can afford more expensive properties
```

### 2. **Flexible Filtering**
- Budget: ±10% tolerance
- Area: ±20m tolerance
- City: Case-insensitive, whitespace-trimmed
- Property Type: Optional (shows all if not specified)

### 3. **Smart Fallback**
```python
if no_results_in_city:
    search_globally()
    suggest_other_cities()
```

### 4. **Memory Persistence**
- Saves session state to JSON
- Restores on reconnect
- Maintains conversation context

### 5. **Natural Language**
- Persian language understanding
- Contextual responses
- Handles typos and variations

---

##  Configuration

### Environment Variables
```bash
POSTGRESS_URL=your_postgres_url
OPENAI_API_KEY=your_github_models_key  # GitHub Models API
```

### LLM Configuration
```python
model = "gpt-4o"
base_url = "https://models.github.ai/inference"
```

---

##  Data Models

### AgentState
```python
{
    messages: List[Dict],           # Conversation history
    memory: ConversationMemory,     # Persistent memory
    requirements: UserRequirements, # Search criteria
    current_stage: str,             # Conversation stage
    search_results: List,           # Found properties
    wants_exchange: bool,           # Exchange flag
    exchange_item: str,             # What to exchange
    exchange_value: int,            # Exchange value
    needs_user_input: bool,         # Waiting for user?
    next_message: str               # Response to send
}
```

### UserRequirements
```python
{
    budget_max: int,
    budget_min: int,
    property_type: PropertyType,
    transaction_type: TransactionType,
    city: str,
    district: str,
    area_min: int,
    area_max: int,
    bedrooms_min: int,
    year_built_min: int,
    document_type: DocumentType,
    must_have_parking: bool,
    must_have_elevator: bool,
    must_have_storage: bool
}
```

### Property
```python
{
    id: str,
    title: str,
    property_type: PropertyType,
    transaction_type: TransactionType,
    price: int,
    area: int,
    city: str,
    district: str,
    bedrooms: int,
    year_built: int,
    document_type: DocumentType,
    has_parking: bool,
    has_elevator: bool,
    has_storage: bool,
    open_to_exchange: bool,
    exchange_preferences: List[str],
    owner_phone: str,
    description: str
}
```

---

## 🎯 Success Criteria

The system successfully:
1. ✅ Understands Persian natural language
2. ✅ Maintains conversation memory
3. ✅ Asks relevant follow-up questions
4. ✅ Calculates total buying power (cash + exchange)
5. ✅ Applies flexible filters with tolerance
6. ✅ Suggests alternatives when no exact match
7. ✅ Formats results naturally in Persian
8. ✅ Persists sessions across restarts

---

## 🚀 Future Enhancements

1. **Image Support**: Property photos
2. **Location Maps**: Integration with mapping services
3. **Price Prediction**: ML-based price estimation
4. **User Profiles**: Saved preferences
5. **Notifications**: New property alerts
6. **Multi-language**: Support for English
7. **Voice Interface**: Speech-to-text integration

---

*Generated: 2025-12-16*
