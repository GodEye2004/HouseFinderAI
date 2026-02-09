# save session
from fastapi import APIRouter, HTTPException
from gotrue import Dict

import app
from app.agents.graph import create_agent_graph
from app.agents.state import AgentState
from app.models.property_submission import PropertySubmission
from app.services.advertisements.app_property.property_manager import property_manager
from app.services.llm_brain.persistence import load_sessions


sessions: Dict[str, AgentState] = load_sessions()

# graph
agent_graph = create_agent_graph()

manager = property_manager

router = APIRouter()



@router.get("/properties")
def get_properties():
    """get list of properties"""
    from app.models.property_submission import PropertyStatus

    properties = property_manager.get_all_properties()

    return {"count": len(properties), "properties": [p.dict() for p in properties]}


@router.post("/properties/submit")
# the user id , use when we add authentication.
async def submit_property(submission: PropertySubmission, user_id: str | None = None):
    try:
        result = manager.submit_property(submission, user_id)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/properties/{property_id}")
async def get_property(property_id: str):
    result = property_manager.get_submission(property_id)
    if not result:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"success": True, "data": result}


@router.get("/properties/user/{user_id}")
async def get_user_properties(user_id: str):
    items = property_manager.get_user_submissions(user_id)
    return {"success": True, "data": items}


@router.delete("/properties/{property_id}")
async def delete_property(property_id: str):
    ok = property_manager.delete_submission(property_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"success": True}


@router.patch("/properties/{property_id}")
async def update_property(property_id: str, updates: Dict):
    """Update property details"""
    # We only allow updates to specific fields.
    allowed_fields = [
        "exchange_preferences",
        "open_to_exchange",
        "price",
        "description",
    ]

    clean_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if not clean_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    try:
        updated = property_manager.update_property_details(property_id, clean_updates)
        if updated:
            return {"success": True, "message": "Property updated"}
        else:
            raise HTTPException(
                status_code=404, detail="Property not found or update failed"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
