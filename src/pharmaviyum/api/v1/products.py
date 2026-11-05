from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, not_, or_, select

from src.pharmaviyum.models.drug_catalog import MedicinalProduct
from src.pharmaviyum.models.product import Product
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser, CurrentUser, SessionDep
from src.pharmaviyum.services.catalog_exclusions import is_excluded_catalog_entry
from src.pharmaviyum.schemas.product_schema import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["Products"])


async def _validate_product_exclusion(*, db: SessionDep, name: str, manufacturer: str | None, medicinal_product_id: int | None) -> None:
    linked_product = None
    if medicinal_product_id is not None:
        linked_product = await db.get(MedicinalProduct, medicinal_product_id)
        if linked_product is None:
            raise HTTPException(status_code=404, detail="Medicinal catalog product not found")
    if is_excluded_catalog_entry(brand_name=name, manufacturer=manufacturer, authorization_country=linked_product.authorization_country if linked_product is not None else None):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Teva and Israeli medicines are excluded from Pharmaviyum")


def _visible_product_conditions():
    israel_codes = ("il", "isr", "israel", "state of israel", "израиль", "ізраїль")
    linked_to_israeli_product = select(MedicinalProduct.id).where(
        MedicinalProduct.id == Product.medicinal_product_id,
        func.lower(func.trim(MedicinalProduct.authorization_country)).in_(israel_codes),
    ).exists()
    return (
        not_(Product.name.ilike("%teva%")),
        not_(Product.manufacturer.ilike("%teva%")),
        not_(linked_to_israeli_product),
    )


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: SessionDep,
    _: CurrentSuperuser,
) -> Product:
    await _validate_product_exclusion(db=db, name=data.name, manufacturer=data.manufacturer, medicinal_product_id=data.medicinal_product_id)
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
            *_visible_product_conditions(),
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
    result = await db.execute(select(Product).where(Product.id == product_id, *_visible_product_conditions()))
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
        select(Product).where(Product.is_active, *_visible_product_conditions()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: SessionDep,
    _: CurrentSuperuser,
) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id, *_visible_product_conditions()))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    updates = data.model_dump(exclude_unset=True)
    await _validate_product_exclusion(db=db, name=updates.get('name', product.name), manufacturer=updates.get('manufacturer', product.manufacturer), medicinal_product_id=updates.get('medicinal_product_id', product.medicinal_product_id))
    for key, value in updates.items():
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
