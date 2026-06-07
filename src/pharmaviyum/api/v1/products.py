from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.schemas.product_schema import (
    ProductCreate, ProductUpdate, ProductResponse,
)
from sqlalchemy import select

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/", response_model=List[ProductResponse])
async def list_products(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.is_active == True).offset(skip).limit(limit))
    return result.scalars().all()


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(product, k, v)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    await db.commit()
    return {"message": "Product deactivated"}
