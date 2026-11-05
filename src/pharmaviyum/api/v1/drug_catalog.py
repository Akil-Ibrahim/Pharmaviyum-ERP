from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import String, cast, or_, select
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
from src.pharmaviyum.services.catalog_exclusions import is_excluded_catalog_entry
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
    source_payload = payload.normalized_payload or {}
    if is_excluded_catalog_entry(
        brand_name=source_payload.get("brand_name") or source_payload.get("product_name"),
        manufacturer=source_payload.get("manufacturer") or source_payload.get("holder"),
        authorization_country=source_payload.get("authorization_country")
        or source_payload.get("country"),
        payload=source_payload,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This catalog entry is excluded from Pharmaviyum",
        )
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
    records = result.scalars().all()
    return [
        DrugCatalogSourceResult.model_validate(record)
        for record in records
        if not is_excluded_catalog_entry(
            brand_name=(record.normalized_payload or {}).get("brand_name")
            or (record.normalized_payload or {}).get("product_name"),
            manufacturer=(record.normalized_payload or {}).get("manufacturer")
            or (record.normalized_payload or {}).get("holder"),
            authorization_country=(record.normalized_payload or {}).get("authorization_country")
            or (record.normalized_payload or {}).get("country"),
            payload=record.normalized_payload or {},
        )
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
    source_payload = source_record.normalized_payload or {}
    if is_excluded_catalog_entry(
        brand_name=source_payload.get("brand_name") or source_payload.get("product_name"),
        manufacturer=source_payload.get("manufacturer") or source_payload.get("holder"),
        authorization_country=source_payload.get("authorization_country")
        or source_payload.get("country"),
        payload=source_payload,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This catalog entry is excluded from Pharmaviyum",
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
    """Approve, reject, or link a source record without creating local sellable stock."""
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
    source_payload = record.normalized_payload or {}
    if is_excluded_catalog_entry(
        brand_name=source_payload.get("brand_name") or source_payload.get("product_name"),
        manufacturer=source_payload.get("manufacturer") or source_payload.get("holder"),
        authorization_country=source_payload.get("authorization_country")
        or source_payload.get("country"),
        payload=source_payload,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This catalog entry is excluded from Pharmaviyum",
        )

    matched_reference_id = payload.matched_drug_reference_id
    matched_product_id = payload.matched_medicinal_product_id

    if matched_reference_id is not None:
        reference = await db.get(DrugReference, matched_reference_id)
        if reference is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matched drug reference not found",
            )
    if matched_product_id is not None:
        medicinal_product = await db.get(MedicinalProduct, matched_product_id)
        if medicinal_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matched medicinal product not found",
            )

    if payload.create_new:
        source = record.normalized_payload or {}
        ingredient = str(
            source.get("ingredient_name")
            or source.get("ingredient")
            or source.get("inn_name")
            or ""
        ).strip()
        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Source record has no single active ingredient to create",
            )

        reference_result = await db.execute(
            select(DrugReference)
            .where(DrugReference.inn_name.ilike(ingredient))
            .order_by(DrugReference.id.asc())
            .limit(1)
        )
        reference = reference_result.scalar_one_or_none()
        if reference is None:
            reference = DrugReference(
                inn_name=ingredient[:200],
                atc_code=source.get("atc_code"),
            )
            db.add(reference)
            await db.flush()

        ingredient_result = await db.execute(
            select(DrugReferenceIngredient).where(
                DrugReferenceIngredient.drug_reference_id == reference.id,
                DrugReferenceIngredient.ingredient_name.ilike(ingredient),
            )
        )
        if ingredient_result.scalar_one_or_none() is None:
            db.add(
                DrugReferenceIngredient(
                    drug_reference_id=reference.id,
                    ingredient_name=ingredient[:200],
                )
            )

        brand_value = source.get("brand_name")
        if not brand_value and "ema" in record.source_name.lower():
            brand_value = source.get("product_name")
        brand = str(brand_value).strip()[:200] if brand_value else None
        strength_value = source.get("strength")
        strength = str(strength_value).strip()[:100] if strength_value else None
        form_value = source.get("dosage_form")
        dosage_form = str(form_value).strip()[:100] if form_value else None
        route_value = source.get("route")
        route = str(route_value).strip()[:100] if route_value else None
        manufacturer_value = source.get("manufacturer") or source.get("holder")
        manufacturer = (
            str(manufacturer_value).strip()[:200] if manufacturer_value else None
        )
        package_value = source.get("package_description")
        package_description = (
            str(package_value).strip()[:200] if package_value else None
        )
        gtin_value = source.get("gtin")
        gtin = str(gtin_value).strip()[:14] if gtin_value else None
        regulatory_value = source.get("regulatory_id")
        regulatory_id = (
            str(regulatory_value).strip()[:100] if regulatory_value else None
        )
        country_value = source.get("country") or source.get("authorization_country")
        authorization_country = (
            str(country_value).strip()[:100] if country_value else None
        )

        product_statement = (
            select(MedicinalProduct)
            .where(
                MedicinalProduct.drug_reference_id == reference.id,
                (
                    MedicinalProduct.brand_name == brand
                    if brand is not None
                    else MedicinalProduct.brand_name.is_(None)
                ),
                (
                    MedicinalProduct.strength == strength
                    if strength is not None
                    else MedicinalProduct.strength.is_(None)
                ),
                (
                    MedicinalProduct.dosage_form == dosage_form
                    if dosage_form is not None
                    else MedicinalProduct.dosage_form.is_(None)
                ),
                (
                    MedicinalProduct.authorization_country == authorization_country
                    if authorization_country is not None
                    else MedicinalProduct.authorization_country.is_(None)
                ),
            )
            .order_by(MedicinalProduct.id.asc())
        )
        existing_product = (
            await db.execute(product_statement.limit(1))
        ).scalar_one_or_none()
        if existing_product is None:
            medicinal_product = MedicinalProduct(
                drug_reference_id=reference.id,
                brand_name=brand,
                product_type="branded" if brand else "generic",
                manufacturer=manufacturer,
                strength=strength,
                dosage_form=dosage_form,
                route=route,
                package_description=package_description,
                gtin=gtin,
                regulatory_id=regulatory_id,
                authorization_country=authorization_country,
            )
            db.add(medicinal_product)
            await db.flush()
        else:
            medicinal_product = existing_product
        matched_product_id = medicinal_product.id
        matched_reference_id = None

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
    stmt = stmt.distinct().order_by(MedicinalProduct.brand_name.asc()).limit(limit * 3)
    result = await db.execute(stmt)
    products = [
        product
        for product in result.scalars().unique().all()
        if not is_excluded_catalog_entry(
            brand_name=product.brand_name,
            manufacturer=product.manufacturer,
            authorization_country=product.authorization_country,
        )
    ]

    catalog_results = [
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
            review_status="approved",
        )
        for product in products
    ]

    # Show imported source variants before approval as reference-only records.
    # A staged regulatory record is never converted into a local sellable Product.
    staged_stmt = (
        select(DrugCatalogSourceRecord)
        .where(
            DrugCatalogSourceRecord.review_status == "pending_review",
            cast(DrugCatalogSourceRecord.normalized_payload, String).ilike(term),
        )
        .order_by(
            DrugCatalogSourceRecord.extracted_at.desc(),
            DrugCatalogSourceRecord.id.desc(),
        )
        .limit(limit * 5)
    )
    staged_rows = (await db.execute(staged_stmt)).scalars().all()
    seen_source_ids: set[tuple[str, str]] = set()
    for record in staged_rows:
        source_identity = (record.source_name, record.source_record_id)
        if source_identity in seen_source_ids:
            continue
        seen_source_ids.add(source_identity)
        payload = record.normalized_payload or {}
        if is_excluded_catalog_entry(
            brand_name=payload.get("brand_name") or payload.get("product_name"),
            manufacturer=payload.get("manufacturer") or payload.get("holder"),
            payload=payload,
        ):
            continue
        ingredient = (
            payload.get("ingredient_name")
            or payload.get("ingredient")
            or payload.get("inn_name")
        )
        if not ingredient:
            continue
        brand = payload.get("brand_name")
        if not brand and "ema" in record.source_name.lower():
            brand = payload.get("product_name")
        catalog_results.append(
            DrugCatalogResult(
                inn_name=str(ingredient),
                ingredient_names=[str(ingredient)],
                brand_name=str(brand) if brand else None,
                product_type=(
                    "branded"
                    if brand and str(payload.get("tty", "")).upper() == "SBD"
                    else "generic" if not brand else "reference"
                ),
                manufacturer=payload.get("manufacturer") or payload.get("holder"),
                strength=payload.get("strength"),
                dosage_form=payload.get("dosage_form"),
                route=payload.get("route"),
                package_description=payload.get("package_description"),
                gtin=payload.get("gtin"),
                authorization_country=(
                    payload.get("country") or payload.get("authorization_country")
                ),
                authorization_status=payload.get("authorization_status"),
                product_class=payload.get("product_class"),
                source_record_id=record.source_record_id,
                source_name=record.source_name,
                review_status=record.review_status,
            )
        )
        if len(catalog_results) >= limit:
            break

    return catalog_results[:limit]
