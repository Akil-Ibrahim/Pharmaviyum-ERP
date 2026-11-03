from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from src.pharmaviyum.models.drug_catalog import (
    DrugCatalogSourceRecord,
    DrugReference,
    DrugReferenceIngredient,
    MedicinalProduct,
)
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser, CurrentUser, SessionDep
from src.pharmaviyum.schemas.drug_catalog import DrugCatalogResult
from src.pharmaviyum.schemas.drug_catalog_matching import DrugCatalogMatchCandidate
from src.pharmaviyum.schemas.drug_catalog_source import (
    DrugCatalogSourceCreate,
    DrugCatalogSourceResult,
    DrugCatalogSourceReview,
    ReviewStatus,
)
from src.pharmaviyum.services.drug_catalog_matching import (
    rank_reference_ids,
    suggest_matches,
)

router = APIRouter(prefix="/drug-catalog", tags=["Drug Catalog"])


@router.post(
    "/sources",
    response_model=DrugCatalogSourceResult,
    status_code=status.HTTP_201_CREATED,
)
async def create_drug_catalog_source(
    payload: DrugCatalogSourceCreate,
    db: SessionDep,
    _: CurrentSuperuser,
) -> DrugCatalogSourceResult:
    """Register an external reference record without creating a sellable product."""
    record = DrugCatalogSourceRecord(**payload.model_dump())
    db.add(record)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This source record and version already exist",
        ) from exc
    await db.refresh(record)
    return DrugCatalogSourceResult.model_validate(record)


@router.get("/sources", response_model=list[DrugCatalogSourceResult])
async def list_drug_catalog_sources(
    db: SessionDep,
    _: CurrentSuperuser,
    review_status: ReviewStatus | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> list[DrugCatalogSourceResult]:
    """List imported source records for controlled review."""
    stmt = select(DrugCatalogSourceRecord)
    if review_status is not None:
        stmt = stmt.where(DrugCatalogSourceRecord.review_status == review_status)
    stmt = stmt.order_by(
        DrugCatalogSourceRecord.extracted_at.desc(),
        DrugCatalogSourceRecord.id.desc(),
    ).limit(limit)
    result = await db.execute(stmt)
    return [
        DrugCatalogSourceResult.model_validate(record)
        for record in result.scalars().all()
    ]


@router.get(
    "/sources/{record_id}/matches",
    response_model=list[DrugCatalogMatchCandidate],
)
async def suggest_drug_catalog_source_matches(
    record_id: int,
    db: SessionDep,
    _: CurrentSuperuser,
) -> list[DrugCatalogMatchCandidate]:
    """Suggest existing catalog matches; suggestions never approve or mutate records."""
    source_record = await db.get(DrugCatalogSourceRecord, record_id)
    if source_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug catalog source record not found",
        )
    if source_record.review_status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Match suggestions are only available for pending records",
        )

    reference_rows_result = await db.execute(
        select(DrugReference.id, DrugReference.inn_name)
    )
    ingredient_rows_result = await db.execute(
        select(
            DrugReferenceIngredient.drug_reference_id,
            DrugReferenceIngredient.ingredient_name,
        )
    )
    reference_ids = rank_reference_ids(
        source_record.normalized_payload,
        reference_rows_result.all(),
        ingredient_rows_result.all(),
    )
    if not reference_ids:
        return []

    references_result = await db.execute(
        select(DrugReference)
        .where(DrugReference.id.in_(reference_ids))
        .options(
            selectinload(DrugReference.ingredients),
            selectinload(DrugReference.medicinal_products),
        )
    )
    candidates = suggest_matches(
        source_record.normalized_payload,
        references_result.scalars().unique().all(),
    )
    return [
        DrugCatalogMatchCandidate.model_validate(candidate) for candidate in candidates
    ]


@router.patch(
    "/sources/{record_id}/review",
    response_model=DrugCatalogSourceResult,
)
async def review_drug_catalog_source(
    record_id: int,
    payload: DrugCatalogSourceReview,
    db: SessionDep,
    reviewer: CurrentSuperuser,
) -> DrugCatalogSourceResult:
    """Record an explicit review decision; never creates local products or stock."""
    result = await db.execute(
        select(DrugCatalogSourceRecord)
        .where(DrugCatalogSourceRecord.id == record_id)
        .with_for_update()
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug catalog source record not found",
        )
    if record.review_status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This source record has already been reviewed",
        )

    if payload.matched_drug_reference_id is not None:
        reference = await db.get(DrugReference, payload.matched_drug_reference_id)
        if reference is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matched drug reference not found",
            )
    if payload.matched_medicinal_product_id is not None:
        medicinal_product = await db.get(
            MedicinalProduct, payload.matched_medicinal_product_id
        )
        if medicinal_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matched medicinal product not found",
            )

    record.review_status = payload.review_status
    record.matched_drug_reference_id = payload.matched_drug_reference_id
    record.matched_medicinal_product_id = payload.matched_medicinal_product_id
    record.match_confidence = payload.match_confidence
    record.reviewed_by_user_id = reviewer.id
    record.reviewed_at = datetime.utcnow()
    record.review_notes = payload.review_notes
    await db.commit()
    await db.refresh(record)
    return DrugCatalogSourceResult.model_validate(record)


@router.get("/search", response_model=list[DrugCatalogResult])
async def search_drug_catalog(
    db: SessionDep,
    _: CurrentUser,
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    country: str | None = Query(None, min_length=2, max_length=100),
) -> list[DrugCatalogResult]:
    term_text = q.strip()
    if len(term_text) < 2:
        return []
    term = f"%{term_text}%"
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
                MedicinalProduct.strength.ilike(term),
                MedicinalProduct.dosage_form.ilike(term),
                MedicinalProduct.package_description.ilike(term),
                MedicinalProduct.gtin.ilike(term),
                MedicinalProduct.regulatory_id.ilike(term),
            )
        )
    )
    if country:
        stmt = stmt.where(MedicinalProduct.authorization_country.ilike(country.strip()))
    stmt = stmt.distinct().order_by(MedicinalProduct.brand_name.asc()).limit(limit)
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
            authorization_country=product.authorization_country,
        )
        for product in products
    ]
