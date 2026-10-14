from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select

from src.pharmaviyum.models.product import Product
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser, CurrentUser, SessionDep
from src.pharmaviyum.schemas.product_schema import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: SessionDep,
    _: CurrentSuperuser,
) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/search", response_model=list[ProductResponse])
async def search_products(
    db: SessionDep,
    _: CurrentUser,
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=100),
) -> list[Product]:
    """Search actual sellable pharmacy products; never searches reference-only drugs."""
    term = f"%{q.strip()}%"
    statement = (
        select(Product)
        .where(
            Product.is_active.is_(True),
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.inn_name.ilike(term),
                Product.manufacturer.ilike(term),
                Product.regulatory_id.ilike(term),
                Product.gtin.ilike(term),
                Product.barcode.ilike(term),
            ),
        )
        .order_by(Product.name.asc(), Product.id.asc())
        .limit(limit)
    )
    result = await db.execute(statement)
    return list(result.scalars().all())


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: SessionDep, _: CurrentUser) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    db: SessionDep,
    _: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[Product]:
    result = await db.execute(
        select(Product).where(Product.is_active).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: SessionDep,
    _: CurrentSuperuser,
) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: SessionDep,
    _: CurrentSuperuser,
) -> dict[str, str]:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    await db.commit()
    return {"message": "Product deactivated"}
