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
    from rag.context_builders.client_context import ClientContextBuilder
    crud = ClientCRUD(db)
    client = await crud.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    prompt = ClientContextBuilder.build_prompt(client)
    # TODO: Connect to Mortarium AI
    return {
        "client_id": client_id,
        "client_name": client.full_name,
        "prompt_for_rag": prompt,
        "message": "Integrate with Mortarium AI here"
    }
