"""PostgreSQL-backed integration tests for Drug Catalog source review endpoints."""

from datetime import datetime, timezone
from itertools import count

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.models.drug_catalog import (
    DrugCatalogSourceRecord,
    DrugReference,
    DrugReferenceIngredient,
    MedicinalProduct,
)

pytestmark = pytest.mark.integration
_source_ids = count(1)


async def create_source_record(
    db: AsyncSession,
    *,
    review_status: str = "pending_review",
) -> DrugCatalogSourceRecord:
    record = DrugCatalogSourceRecord(
        source_name="test-source",
        source_record_id=f"source-{next(_source_ids)}",
        source_version="2026-01",
        extracted_at=datetime.now(timezone.utc).replace(tzinfo=None),
        normalized_payload={"inn": "paracetamol"},
        review_status=review_status,
    )
    db.add(record)
    await db.flush()
    return record


class TestDrugCatalogSourceReviewAuthorization:
    async def test_sources_require_superuser(self, client: AsyncClient):
        response = await client.get("/api/v1/drug-catalog/sources")
        assert response.status_code == 401


class TestDrugCatalogSourceReviewEndpoints:
    async def test_get_matches_returns_404_for_missing_source(
        self, authenticated_client: AsyncClient
    ):
        response = await authenticated_client.get(
            "/api/v1/drug-catalog/sources/999999/matches"
        )
        assert response.status_code == 404

    async def test_get_matches_rejects_already_reviewed_source(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
    ):
        record = await create_source_record(test_db, review_status="approved")

        response = await authenticated_client.get(
            f"/api/v1/drug-catalog/sources/{record.id}/matches"
        )

        assert response.status_code == 409

    async def test_review_approves_existing_reference_and_prevents_second_review(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
    ):
        reference = DrugReference(inn_name="Paracetamol", atc_code="N02BE01")
        test_db.add(reference)
        await test_db.flush()
        record = await create_source_record(test_db)

        response = await authenticated_client.patch(
            f"/api/v1/drug-catalog/sources/{record.id}/review",
            json={
                "review_status": "approved",
                "matched_drug_reference_id": reference.id,
                "match_confidence": "0.95",
                "review_notes": "Verified against the reference record.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["review_status"] == "approved"
        assert data["matched_drug_reference_id"] == reference.id
        assert data["matched_medicinal_product_id"] is None
        assert data["reviewed_by_user_id"] == 1
        assert data["reviewed_at"] is not None

        repeated = await authenticated_client.patch(
            f"/api/v1/drug-catalog/sources/{record.id}/review",
            json={
                "review_status": "rejected",
                "review_notes": "A second decision must not overwrite the first.",
            },
        )
        assert repeated.status_code == 409

    async def test_review_rejects_nonexistent_match_target(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
    ):
        record = await create_source_record(test_db)

        response = await authenticated_client.patch(
            f"/api/v1/drug-catalog/sources/{record.id}/review",
            json={
                "review_status": "approved",
                "matched_medicinal_product_id": 999999,
            },
        )

        assert response.status_code == 404
        assert record.review_status == "pending_review"

    async def test_review_can_reject_without_a_match_target(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
    ):
        record = await create_source_record(test_db)

        response = await authenticated_client.patch(
            f"/api/v1/drug-catalog/sources/{record.id}/review",
            json={
                "review_status": "rejected",
                "review_notes": "Insufficient source provenance.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["review_status"] == "rejected"
        assert data["matched_drug_reference_id"] is None
        assert data["matched_medicinal_product_id"] is None



class TestDrugCatalogSourcePromotion:
    async def test_approved_source_can_create_searchable_medicinal_product(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
    ):
        record = await create_source_record(test_db)
        record.normalized_payload = {
            "ingredient_name": "paracetamol",
            "product_name": "Paracetamol 500 mg Oral Tablet",
            "strength": "500 mg",
            "dosage_form": "Tablet",
            "route": "Oral",
        }
        await test_db.flush()

        response = await authenticated_client.patch(
            f"/api/v1/drug-catalog/sources/{record.id}/review",
            json={
                "review_status": "approved",
                "create_catalog_entry": True,
                "review_notes": "Validated source record.",
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["review_status"] == "approved"
        assert data["matched_drug_reference_id"] is not None
        assert data["matched_medicinal_product_id"] is not None

        reference = await test_db.get(DrugReference, data["matched_drug_reference_id"])
        product = await test_db.get(
            MedicinalProduct, data["matched_medicinal_product_id"]
        )
        assert reference is not None
        assert reference.inn_name == "paracetamol"
        assert product is not None
        assert product.drug_reference_id == reference.id
        assert product.strength == "500 mg"
        assert product.regulatory_id == f"{record.source_name}:{record.source_record_id}"

        ingredient = await test_db.execute(
            select(DrugReferenceIngredient).where(
                DrugReferenceIngredient.drug_reference_id == reference.id
            )
        )
        assert ingredient.scalar_one().ingredient_name == "paracetamol"

    async def test_promotion_rejects_source_without_product_name(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
    ):
        record = await create_source_record(test_db)

        response = await authenticated_client.patch(
            f"/api/v1/drug-catalog/sources/{record.id}/review",
            json={
                "review_status": "approved",
                "create_catalog_entry": True,
            },
        )

        assert response.status_code == 422
        assert record.review_status == "pending_review"
