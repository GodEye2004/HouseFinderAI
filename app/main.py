from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.property_submission import PropertySubmission
from app.models.user import ChatRequest, ChatResponse
from app.agents.graph import create_agent_graph, initialize_state
from app.agents.state import AgentState
from app.services import property_manager
# from app.services import property_manager
from app.services.memory_service import ConversationMemory
from typing import Dict
import uuid
from app.services.divar_api import divar_router
from app.services.property_manager import property_manager, PropertyManager

# ما از property_manager که در ماژول اینستنس شده استفاده میکنیم
# manager = PropertyManager() رو حذف میکنیم تا دوگانگی پیش نیاد
manager = property_manager

app = FastAPI(
    title="مشاور املاک هوشمند با حافظه",
    description="سیستم مشاوره املاک با LLM یکپارچه و حافظه کامل",
    version="2.0.0"
)

app.include_router(divar_router)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.services.persistence import save_sessions, load_sessions

# ذخیره session ها
sessions: Dict[str, AgentState] = load_sessions()

# گراف
agent_graph = create_agent_graph()


@app.get("/")
def read_root():
    """صفحه اصلی"""
    return {
        "message": "🏡 سیستم مشاور املاک هوشمند با حافظه",
        "version": "2.0.0",
        "features": [
            "حافظه کامل مکالمه",
            "فهم طبیعی زبان فارسی",
            "موتور تصمیم‌گیری پیشرفته",
            "معاوضه هوشمند"
        ]
    }


@app.get("/health")
def health_check():
    """بررسی سلامت"""
    return {
        "status": "healthy",
        "sessions_count": len(sessions),
        "llm_enabled": True  # چک کردن LLM
    }


@app.post("/session/new")
def create_new_session():
    """ایجاد session جدید"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = initialize_state(session_id)

    return {
        "session_id": session_id,
        "message": "Session با حافظه جدید ایجاد شد"
    }


@app.get("/session/{session_id}")
def get_session(session_id: str):
    """دریافت اطلاعات session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session پیدا نشد")

    state = sessions[session_id]
    memory = state["memory"]

    return {
        "session_id": session_id,
        "current_stage": state["current_stage"],
        "messages_count": len(state["messages"]),
        "memory_summary": memory.get_summary(),
        "memory_facts": list(memory.facts.keys()),
        "requirements": state["requirements"].dict(),
        "wants_exchange": state["wants_exchange"]
    }


@app.get("/session/{session_id}/memory")
def get_session_memory(session_id: str):
    """دریافت حافظه کامل"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session پیدا نشد")

    memory = sessions[session_id]["memory"]

    return {
        "session_id": session_id,
        "memory": memory.to_dict(),
        "summary": memory.get_summary()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    چت اصلی - LLM کنترل کامل رو داره
    """

    # ایجاد یا دریافت session
    if not request.session_id or request.session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = initialize_state(session_id)
        save_sessions(sessions)
    else:
        session_id = request.session_id

    current_state = sessions[session_id]

    # اضافه کردن پیام کاربر
    current_state["messages"].append({
        "role": "user",
        "content": request.message
    })

    # اجرای گراف (همیشه از chat_node می‌گذره)
    result = agent_graph.invoke(current_state)

    # آپدیت state
    sessions[session_id] = result
    save_sessions(sessions)

    # اضافه کردن پاسخ به تاریخچه
    result["messages"].append({
        "role": "assistant",
        "content": result["next_message"]
    })

    # ساخت پاسخ
    response = ChatResponse(
        response=result["next_message"],
        session_id=session_id,
        requires_input=result["needs_user_input"],
        missing_fields=result["missing_fields"],
        state=result["current_stage"]
    )

    # املاک پیشنهادی
    if result.get("search_results"):

        recommended = []
        for score in result["search_results"][:5]:
            prop = property_manager.get_property_by_id(score.property_id)

            if prop:
                recommended.append({
                    "id": prop.id,
                    "title": prop.title,
                    "price": prop.price,
                    "area": prop.area,
                    "location": f"{prop.city}، {prop.district}",
                    "match_percentage": score.match_percentage,
                    "score": score.total_score
                })

        response.recommended_properties = recommended

    return response


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    """حذف session"""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session حذف شد"}
    else:
        raise HTTPException(status_code=404, detail="Session پیدا نشد")


@app.get("/properties")
def get_properties():
    """دریافت لیست املاک"""
    from app.models.property_submission import PropertyStatus
    
    properties = property_manager.get_all_properties()

    return {
        "count": len(properties),
        "properties": [p.dict() for p in properties]
    }


@app.post("/properties/submit")
async def submit_property(submission: PropertySubmission, user_id: str | None = None):
    try:
        result = manager.submit_property(submission, user_id)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/properties/{property_id}")
async def get_property(property_id: str):
    result = property_manager.get_submission(property_id)
    if not result:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"success": True, "data": result}


@app.get("/properties/user/{user_id}")
async def get_user_properties(user_id: str):
    items = property_manager.get_user_submissions(user_id)
    return {"success": True, "data": items}




@app.delete("/properties/{property_id}")
async def delete_property(property_id: str):
    ok = property_manager.delete_submission(property_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"success": True}


@app.patch("/properties/{property_id}")
async def update_property(property_id: str, updates: Dict):
    """آپدیت جزییات ملک"""
    # فقط اجازه‌ی آپدیت فیلدهای خاص رو میدیم
    allowed_fields = ["exchange_preferences", "open_to_exchange", "price", "description"]
    
    clean_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not clean_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    try:
        updated = property_manager.update_property_details(property_id, clean_updates)
        if updated:
            return {"success": True, "message": "Property updated"}
        else:
            raise HTTPException(status_code=404, detail="Property not found or update failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)