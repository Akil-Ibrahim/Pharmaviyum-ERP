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
review_router = APIRouter(prefix="/api/v1/drug-catalog", tags=["Drug Catalog Review"])


@review_router.post(
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


@review_router.get("/sources", response_model=list[DrugCatalogSourceResult])
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


@review_router.get(
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
        reference_rows_result.tuples().all(),
        ingredient_rows_result.tuples().all(),
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
        list(references_result.scalars().unique().all()),
    )
    return [
        DrugCatalogMatchCandidate.model_validate(candidate) for candidate in candidates
    ]


@review_router.patch(
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

    matched_reference_id = payload.matched_drug_reference_id
    matched_product_id = payload.matched_medicinal_product_id
    if payload.create_catalog_entry:
        source_payload = record.normalized_payload or {}
        inn_name = (
            source_payload.get("ingredient_name")
            or source_payload.get("ingredient")
            or source_payload.get("inn_name")
            or source_payload.get("inn")
        )
        product_name = (
            source_payload.get("product_name")
            or source_payload.get("term")
            or source_payload.get("brand_name")
        )
        if not isinstance(inn_name, str) or not inn_name.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Source payload has no usable active ingredient/INN",
            )
        if not isinstance(product_name, str) or not product_name.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Source payload has no usable medicinal product name",
            )

        source_regulatory_id = (
            f"{record.source_name}:{record.source_record_id}"
        )[:100]
        existing_product_result = await db.execute(
            select(MedicinalProduct).where(
                MedicinalProduct.regulatory_id == source_regulatory_id
            ).limit(1)
        )
        existing_product = existing_product_result.scalar_one_or_none()
        if existing_product is not None:
            matched_reference_id = existing_product.drug_reference_id
            matched_product_id = existing_product.id
        else:
            reference_result = await db.execute(
                select(DrugReference)
                .where(DrugReference.inn_name.ilike(inn_name.strip()))
                .limit(1)
            )
            reference = reference_result.scalar_one_or_none()
            if reference is None:
                reference = DrugReference(
                    inn_name=inn_name.strip(),
                    atc_code=source_payload.get("atc_code") or None,
                )
                db.add(reference)
                await db.flush()

            ingredient_result = await db.execute(
                select(DrugReferenceIngredient.id)
                .where(
                    DrugReferenceIngredient.drug_reference_id == reference.id,
                    DrugReferenceIngredient.ingredient_name.ilike(inn_name.strip()),
                )
                .limit(1)
            )
            if ingredient_result.scalar_one_or_none() is None:
                db.add(
                    DrugReferenceIngredient(
                        drug_reference_id=reference.id,
                        ingredient_name=inn_name.strip(),
                    )
                )
                await db.flush()

            brand_name = (
                source_payload.get("brand_name")
                or source_payload.get("product_name")
                or source_payload.get("term")
            )
            manufacturer = (
                source_payload.get("manufacturer")
                or source_payload.get("holder")
                or None
            )
            medicinal_product = MedicinalProduct(
                drug_reference_id=reference.id,
                brand_name=str(brand_name).strip() if brand_name else None,
                product_type=(
                    "brand"
                    if source_payload.get("brand_name")
                    else "generic"
                ),
                manufacturer=str(manufacturer).strip() if manufacturer else None,
                strength=source_payload.get("strength") or None,
                dosage_form=source_payload.get("dosage_form") or None,
                route=source_payload.get("route") or None,
                package_description=source_payload.get("package_description") or None,
                gtin=source_payload.get("gtin") or None,
                regulatory_id=source_regulatory_id,
                authorization_country=(
                    source_payload.get("authorization_country")
                    or source_payload.get("country")
                    or None
                ),
            )
            db.add(medicinal_product)
            await db.flush()
            matched_reference_id = reference.id
            matched_product_id = medicinal_product.id

    record.review_status = payload.review_status
    record.matched_drug_reference_id = matched_reference_id
    record.matched_medicinal_product_id = matched_product_id
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
