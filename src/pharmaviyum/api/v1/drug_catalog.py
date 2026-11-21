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
    MedicinalProductIngredient,
)
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser, CurrentUser, SessionDep
from src.pharmaviyum.schemas.drug_catalog import (
    DrugCatalogIngredientResult,
    DrugCatalogResult,
)
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
    )

    result = await db.execute(stmt.limit(limit))
    records = result.scalars().all()
    return [DrugCatalogSourceResult.model_validate(record) for record in records]


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
            selectinload(DrugReference.medicinal_products).selectinload(
                MedicinalProduct.ingredients
            ),
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
    """Review a source record without creating local sellable stock."""
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
        raw_ingredients = source.get("ingredients")
        ingredient_components: list[dict[str, object]] = []
        if isinstance(raw_ingredients, list):
            for item in raw_ingredients:
                if isinstance(item, dict):
                    name = str(
                        item.get("ingredient_name") or item.get("name") or ""
                    ).strip()
                    strength_value = item.get("strength_value") or item.get("strength")
                    strength_unit = item.get("strength_unit")
                    source_identifier = item.get("source_identifier")
                else:
                    name = str(item).strip()
                    strength_value = None
                    strength_unit = None
                    source_identifier = None
                if name:
                    ingredient_components.append(
                        {
                            "ingredient_name": name[:200],
                            "strength_value": (
                                str(strength_value).strip()[:80]
                                if strength_value is not None
                                else None
                            ),
                            "strength_unit": (
                                str(strength_unit).strip()[:40]
                                if strength_unit is not None
                                else None
                            ),
                            "source_identifier": (
                                str(source_identifier).strip()[:100]
                                if source_identifier is not None
                                else None
                            ),
                        }
                    )
        if not ingredient_components:
            fallback_ingredient = str(
                source.get("ingredient_name")
                or source.get("ingredient")
                or source.get("inn_name")
                or ""
            ).strip()
            if fallback_ingredient:
                ingredient_components.append(
                    {
                        "ingredient_name": fallback_ingredient[:200],
                        "strength_value": None,
                        "strength_unit": None,
                        "source_identifier": None,
                    }
                )
        if not ingredient_components:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Source record has no active ingredient composition to create",
            )
        ingredient_names = [
            str(component["ingredient_name"]) for component in ingredient_components
        ]
        ingredient = ingredient_names[0]

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
        manufacturer_country_value = (
            source.get("manufacturer_country")
            or source.get("country_of_origin")
            or source.get("country_of_manufacture")
            or source.get("country_of_production")
        )
        manufacturer_country = (
            str(manufacturer_country_value).strip()[:100]
            if manufacturer_country_value
            else None
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
                (
                    MedicinalProduct.manufacturer_country == manufacturer_country
                    if manufacturer_country is not None
                    else MedicinalProduct.manufacturer_country.is_(None)
                ),
            )
            .order_by(MedicinalProduct.id.asc())
        )
        product_candidates = (await db.execute(product_statement)).scalars().all()
        existing_product = None
        for candidate_product in product_candidates:
            component_result = await db.execute(
                select(MedicinalProductIngredient.ingredient_name)
                .where(
                    MedicinalProductIngredient.medicinal_product_id
                    == candidate_product.id
                )
                .order_by(MedicinalProductIngredient.position.asc())
            )
            existing_component_names = list(component_result.scalars().all())
            if not existing_component_names:
                existing_component_names = [reference.inn_name]
            if sorted(name.casefold() for name in existing_component_names) == sorted(
                name.casefold() for name in ingredient_names
            ):
                existing_product = candidate_product
                break
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
                manufacturer_country=manufacturer_country,
            )
            db.add(medicinal_product)
            await db.flush()
            for position, component in enumerate(ingredient_components):
                db.add(
                    MedicinalProductIngredient(
                        medicinal_product_id=medicinal_product.id,
                        ingredient_name=str(component["ingredient_name"]),
                        strength_value=component["strength_value"],
                        strength_unit=component["strength_unit"],
                        source_identifier=component["source_identifier"],
                        position=position,
                    )
                )
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
        .outerjoin(
            MedicinalProductIngredient,
            MedicinalProductIngredient.medicinal_product_id == MedicinalProduct.id,
        )
        .options(
            selectinload(MedicinalProduct.drug_reference).selectinload(
                DrugReference.ingredients
            ),
            selectinload(MedicinalProduct.ingredients),
        )
        .where(
            or_(
                DrugReference.inn_name.ilike(term),
                DrugReference.atc_code.ilike(term),
                DrugReferenceIngredient.ingredient_name.ilike(term),
                MedicinalProductIngredient.ingredient_name.ilike(term),
                MedicinalProduct.brand_name.ilike(term),
                MedicinalProduct.manufacturer.ilike(term),
                MedicinalProduct.strength.ilike(term),
                MedicinalProduct.dosage_form.ilike(term),
                MedicinalProduct.package_description.ilike(term),
                MedicinalProduct.gtin.ilike(term),
                MedicinalProduct.regulatory_id.ilike(term),
            ),
        )
    )
    if country:
        stmt = stmt.where(MedicinalProduct.authorization_country.ilike(country.strip()))
    stmt = stmt.distinct().order_by(MedicinalProduct.brand_name.asc()).limit(limit * 3)
    result = await db.execute(stmt)
    products = result.scalars().unique().all()

    catalog_results = [
        DrugCatalogResult(
            medicinal_product_id=product.id,
            drug_reference_id=product.drug_reference.id,
            inn_name=(
                " + ".join(
                    component.ingredient_name for component in product.ingredients
                )
                if product.ingredients
                else product.drug_reference.inn_name
            ),
            atc_code=product.drug_reference.atc_code,
            ingredient_names=(
                [component.ingredient_name for component in product.ingredients]
                if product.ingredients
                else [
                    ingredient.ingredient_name
                    for ingredient in product.drug_reference.ingredients
                ]
            ),
            ingredient_components=[
                DrugCatalogIngredientResult(
                    ingredient_name=component.ingredient_name,
                    strength_value=component.strength_value,
                    strength_unit=component.strength_unit,
                    source_identifier=component.source_identifier,
                )
                for component in product.ingredients
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
            manufacturer_country=product.manufacturer_country,
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
        raw_ingredients = payload.get("ingredients")
        ingredient_names = []
        if isinstance(raw_ingredients, list):
            for item in raw_ingredients:
                name = (
                    item.get("ingredient_name") or item.get("name")
                    if isinstance(item, dict)
                    else item
                )
                if name and str(name).strip():
                    ingredient_names.append(str(name).strip())
        if not ingredient_names:
            ingredient = (
                payload.get("ingredient_name")
                or payload.get("ingredient")
                or payload.get("inn_name")
            )
            if ingredient:
                ingredient_names = [str(ingredient).strip()]
        if not ingredient_names:
            continue
        ingredient = " + ".join(ingredient_names)
        brand = payload.get("brand_name")
        if not brand and "ema" in record.source_name.lower():
            brand = payload.get("product_name")
        catalog_results.append(
            DrugCatalogResult(
                inn_name=str(ingredient),
                ingredient_names=ingredient_names,
                ingredient_components=(
                    [
                        DrugCatalogIngredientResult(
                            ingredient_name=(
                                str(item.get("ingredient_name") or item.get("name"))
                                if isinstance(item, dict)
                                else str(item)
                            ),
                            strength_value=(
                                str(item.get("strength_value") or item.get("strength"))
                                if isinstance(item, dict)
                                and (item.get("strength_value") or item.get("strength"))
                                else None
                            ),
                            strength_unit=(
                                str(item.get("strength_unit"))
                                if isinstance(item, dict) and item.get("strength_unit")
                                else None
                            ),
                            source_identifier=(
                                str(item.get("source_identifier"))
                                if isinstance(item, dict)
                                and item.get("source_identifier")
                                else None
                            ),
                        )
                        for item in raw_ingredients
                    ]
                    if isinstance(raw_ingredients, list)
                    else []
                ),
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
                manufacturer_country=(
                    payload.get("manufacturer_country")
                    or payload.get("country_of_origin")
                    or payload.get("country_of_manufacture")
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
