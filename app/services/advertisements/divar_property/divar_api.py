from fastapi import APIRouter, HTTPException
from typing import List
from app.core.postgres_service import postgres_service
from app.models.divar_propertys import DivarProperty  # the Pydantic model for divar_data

divar_router = APIRouter(prefix="/divar", tags=["Divar Properties"])

TABLE_NAME = "divar_data"

@divar_router.get("/", response_model=List[DivarProperty])
def list_divar_properties(limit: int = 100, offset: int = 0):
    records = postgres_service.select(TABLE_NAME, limit=limit, offset=offset)
    return [DivarProperty(**r) for r in records]

@divar_router.get("/{property_id}", response_model=DivarProperty)
def get_divar_property(property_id: int):
    records = postgres_service.select(TABLE_NAME, filters={"id": property_id})
    if not records:
        raise HTTPException(status_code=404, detail="Property not found")
    return DivarProperty(**records[0])
