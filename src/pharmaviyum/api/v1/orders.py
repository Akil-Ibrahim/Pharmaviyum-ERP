from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.models.order import Order
from src.pharmaviyum.schemas.order_schema import OrderCreate, OrderResponse
from src.pharmaviyum.crud.client import ClientCRUD

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    # ensure client exists
    client_crud = ClientCRUD(db)
    client = await client_crud.get(data.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    order = Order(client_id=data.client_id, total_amount=data.total_amount)
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # update client purchase stats
    await client_crud.update_purchase_stats(data.client_id, data.total_amount)

    return order


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
