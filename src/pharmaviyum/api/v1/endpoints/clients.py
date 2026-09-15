# api/v1/endpoints/clients.py - FastAPI endpoints for Client
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.crud.client import ClientCRUD
from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.models.user import User
from src.pharmaviyum.modules.auth.deps import get_current_user
from src.pharmaviyum.schemas.client_schema import ClientCreate, ClientResponse, ClientUpdate

router = APIRouter(prefix="/clients", tags=["Clients"])


def require_superuser(current_user: User) -> None:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_superuser(current_user)
    crud = ClientCRUD(db)
    existing = await crud.get_by_phone(data.phone)
    if existing:
        raise HTTPException(status_code=400, detail="Client with this phone already exists")
    return await crud.create(data)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crud = ClientCRUD(db)
    client = await crud.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    response = ClientResponse.model_validate(client)
    response.segment = crud.get_segment(client)
    return response


@router.get("/search/by-phone/{phone}", response_model=ClientResponse)
async def search_by_phone(
    phone: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crud = ClientCRUD(db)
    client = await crud.get_by_phone(phone)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    response = ClientResponse.model_validate(client)
    response.segment = crud.get_segment(client)
    return response


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_superuser(current_user)
    crud = ClientCRUD(db)
    try:
        client = await crud.update(client_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    response = ClientResponse.model_validate(client)
    response.segment = crud.get_segment(client)
    return response


@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_superuser(current_user)
    crud = ClientCRUD(db)
    success = await crud.soft_delete(client_id)
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deactivated successfully"}


@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crud = ClientCRUD(db)
    clients = await crud.list_all(skip, limit)
    result = []
    for client in clients:
        response = ClientResponse.model_validate(client)
        response.segment = crud.get_segment(client)
        result.append(response)
    return result


@router.get("/{client_id}/recommendations")
async def get_client_recommendations(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get personalized product recommendations via Mortarium AI."""
    import httpx

    from src.pharmaviyum.config import settings

    crud = ClientCRUD(db)
    client = await crud.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    prompt_parts = [f"Client: {client.full_name}", f"Phone: {client.phone}"]
    if getattr(client, "chronic_diseases", None):
        prompt_parts.append(f"Chronic diseases: {client.chronic_diseases}")
    if getattr(client, "allergies", None):
        prompt_parts.append(f"Allergies: {client.allergies}")
    if getattr(client, "regular_medications", None):
        prompt_parts.append(f"Medications: {client.regular_medications}")
    prompt_parts.append(f"Total purchases: {getattr(client, 'total_purchases', 0)}")
    prompt_parts.append(f"Total spent: {getattr(client, 'total_spent', 0.0)}")

    prompt = "\n".join(prompt_parts) + (
        "\n\nProvide 3 personalized product recommendations (concise). "
        "Include reasons and any safety notes."
    )

    ai_url = settings.AI_SERVICE_URL.rstrip("/") + "/api/ask"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client_http:
            response = await client_http.post(ai_url, json={"question": prompt})
            response.raise_for_status()
            body = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="AI service unavailable") from exc

    return {
        "client_id": client_id,
        "client_name": client.full_name,
        "recommendations": body.get("answer"),
        "sources": body.get("sources", []),
    }
