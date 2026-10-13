from fastapi import APIRouter, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from src.pharmaviyum.models.drug_catalog import (
    DrugReference,
    DrugReferenceIngredient,
    MedicinalProduct,
)
from src.pharmaviyum.modules.auth.deps import CurrentUser, SessionDep
from src.pharmaviyum.schemas.drug_catalog import DrugCatalogResult

router = APIRouter(prefix="/drug-catalog", tags=["Drug Catalog"])


@router.get("/search", response_model=list[DrugCatalogResult])
async def search_drug_catalog(
    db: SessionDep,
    _: CurrentUser,
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=100),
) -> list[DrugCatalogResult]:
    term = f"%{q.strip()}%"
    stmt = (
        select(MedicinalProduct)
        .join(MedicinalProduct.drug_reference)
        .outerjoin(
            DrugReferenceIngredient,
            DrugReferenceIngredient.drug_reference_id == DrugReference.id,
        )
        .options(
            selectinload(MedicinalProduct.drug_reference).selectinload(
                DrugReference.ingredients
            )
        )
        .where(
            or_(
                DrugReference.inn_name.ilike(term),
                DrugReference.atc_code.ilike(term),
                DrugReferenceIngredient.ingredient_name.ilike(term),
                MedicinalProduct.brand_name.ilike(term),
                MedicinalProduct.manufacturer.ilike(term),
                MedicinalProduct.dosage_form.ilike(term),
                MedicinalProduct.package_description.ilike(term),
                MedicinalProduct.gtin.ilike(term),
                MedicinalProduct.regulatory_id.ilike(term),
            )
        )
        .distinct()
        .limit(limit)
    )
    result = await db.execute(stmt)
    products = result.scalars().unique().all()

    return [
        DrugCatalogResult(
            medicinal_product_id=product.id,
            drug_reference_id=product.drug_reference.id,
            inn_name=product.drug_reference.inn_name,
            atc_code=product.drug_reference.atc_code,
            ingredient_names=[
                ingredient.ingredient_name
                for ingredient in product.drug_reference.ingredients
            ],
            brand_name=product.brand_name,
            product_type=product.product_type,
            manufacturer=product.manufacturer,
            strength=product.strength,
            dosage_form=product.dosage_form,
            route=product.route,
            package_description=product.package_description,
            gtin=product.gtin,
            regulatory_id=product.regulatory_id,
        )
        for product in products
    ]
