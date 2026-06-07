# api/v1/endpoints/clients.py - FastAPI endpoints for Client
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.crud.client import ClientCRUD
from src.pharmaviyum.schemas.client_schema import ClientCreate, ClientUpdate, ClientResponse
from src.pharmaviyum.models.client import Client

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(data: ClientCreate, db: AsyncSession = Depends(get_db)):
    crud = ClientCRUD(db)
    existing = await crud.get_by_phone(data.phone)
    if existing:
        raise HTTPException(status_code=400, detail="Client with this phone already exists")
    return await crud.create(data)

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    crud = ClientCRUD(db)
    client = await crud.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    response = ClientResponse.model_validate(client)
    response.segment = crud.get_segment(client)
    return response

@router.get("/search/by-phone/{phone}", response_model=ClientResponse)
async def search_by_phone(phone: str, db: AsyncSession = Depends(get_db)):
    crud = ClientCRUD(db)
    client = await crud.get_by_phone(phone)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    response = ClientResponse.model_validate(client)
    response.segment = crud.get_segment(client)
    return response

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: int, data: ClientUpdate, db: AsyncSession = Depends(get_db)):
    crud = ClientCRUD(db)
    try:
        client = await crud.update(client_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    response = ClientResponse.model_validate(client)
    response.segment = crud.get_segment(client)
    return response

@router.delete("/{client_id}")
async def delete_client(client_id: int, db: AsyncSession = Depends(get_db)):
    crud = ClientCRUD(db)
    success = await crud.soft_delete(client_id)
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deactivated successfully"}

@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    crud = ClientCRUD(db)
    clients = await crud.list_all(skip, limit)
    result = []
    for c in clients:
        resp = ClientResponse.model_validate(c)
        resp.segment = crud.get_segment(c)
        result.append(resp)
    return result

@router.get("/{client_id}/recommendations")
async def get_client_recommendations(
    client_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get personalized product recommendations via Mortarium AI"""
    from src.pharmaviyum.config import settings
    import httpx

    crud = ClientCRUD(db)
    client = await crud.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Build a concise prompt for the RAG model using available client data
    prompt_parts = [
        f"Client: {client.full_name}",
        f"Phone: {client.phone}",
    ]
    if getattr(client, "chronic_diseases", None):
        prompt_parts.append(f"Chronic diseases: {client.chronic_diseases}")
    if getattr(client, "allergies", None):
        prompt_parts.append(f"Allergies: {client.allergies}")
    if getattr(client, "regular_medications", None):
        prompt_parts.append(f"Medications: {client.regular_medications}")
    prompt_parts.append(f"Total purchases: {getattr(client, 'total_purchases', 0)}")
    prompt_parts.append(f"Total spent: {getattr(client, 'total_spent', 0.0)}")

    prompt = "\n".join(prompt_parts) + "\n\nProvide 3 personalized product recommendations (concise). Include reasons and any safety notes."

    ai_url = settings.AI_SERVICE_URL.rstrip("/") + "/api/ask"
    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            resp = await c.post(ai_url, json={"question": prompt})
            resp.raise_for_status()
            body = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")

    return {
        "client_id": client_id,
        "client_name": client.full_name,
        "recommendations": body.get("answer"),
        "sources": body.get("sources", []),
        "prompt": prompt,
    }
