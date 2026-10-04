"""
Integration tests for patient endpoints
Best practice 2026: Full stack testing with real database
"""

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.models.patients import PatientPurchase

pytestmark = pytest.mark.integration


class TestCreatePatient:
    """Tests for POST /api/v1/patients/"""

    @pytest.mark.asyncio
    async def test_create_patient_success(
        self,
        authenticated_client: AsyncClient,
        sample_patient_data: dict,
    ):
        """Test successful patient creation"""
        response = await authenticated_client.post(
            "/api/v1/patients/",
            json=sample_patient_data,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["first_name"] == sample_patient_data["first_name"]
        assert data["last_name"] == sample_patient_data["last_name"]
        assert data["phone"] == sample_patient_data["phone"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_phone(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        sample_patient_data: dict,
    ):
        """Test creation fails with duplicate phone"""
        # Create first patient
        await authenticated_client.post(
            "/api/v1/patients/",
            json=sample_patient_data,
        )

        # Try to create with same phone
        response = await authenticated_client.post(
            "/api/v1/patients/",
            json=sample_patient_data,
        )

        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_patient_unauthorized(
        self,
        client: AsyncClient,
        sample_patient_data: dict,
    ):
        """Test creation requires authentication"""
        response = await client.post(
            "/api/v1/patients/",
            json=sample_patient_data,
        )

        assert response.status_code == 401


class TestListPatients:
    """Tests for GET /api/v1/patients/"""

    @pytest.mark.asyncio
    async def test_list_patients_empty(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test listing patients when database is empty"""
        response = await authenticated_client.get("/api/v1/patients/")

        assert response.status_code == 200
        data = response.json()

        assert data == []

    @pytest.mark.asyncio
    async def test_list_patients_with_data(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        patient_factory,
    ):
        """Test listing patients with data"""
        # Create 5 patients
        for _ in range(5):
            await patient_factory.create()

        response = await authenticated_client.get("/api/v1/patients/")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 5

    @pytest.mark.asyncio
    async def test_list_patients_pagination(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        patient_factory,
    ):
        """Test pagination works correctly"""
        # Create 15 patients
        for _ in range(15):
            await patient_factory.create()

        # Get first page
        response = await authenticated_client.get(
            "/api/v1/patients/?page=1&page_size=10"
        )

        data = response.json()
        assert len(data) == 10

    @pytest.mark.asyncio
    async def test_list_patients_search(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        patient_factory,
    ):
        """Test search functionality"""
        # Create patients with specific names
        await patient_factory.create(first_name="Ibrahim", last_name="Ibrahim")
        await patient_factory.create(first_name="Другой", last_name="Пациент")

        # Search for Ибрагим
        response = await authenticated_client.get("/api/v1/patients/?search=Ибрагим")

        data = response.json()
        assert len(data) == 1
        assert data[0]["first_name"] == "Ибрагим"


class TestGetPatient:
    """Tests for GET /api/v1/patients/{id}"""

    @pytest.mark.asyncio
    async def test_get_patient_success(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        patient_factory,
    ):
        """Test successful patient retrieval"""
        patient = await patient_factory.create()

        response = await authenticated_client.get(f"/api/v1/patients/{patient.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == patient.id
        assert data["full_name"] == patient.full_name

    @pytest.mark.asyncio
    async def test_get_patient_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test retrieval returns 404 for non-existent patient"""
        response = await authenticated_client.get("/api/v1/patients/99999")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Patient not found"


class TestUpdatePatient:
    """Tests for PUT /api/v1/patients/{id}"""

    @pytest.mark.asyncio
    async def test_update_patient_success(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        patient_factory,
        sample_patient_update_data: dict,
    ):
        """Test successful patient update"""
        patient = await patient_factory.create()

        response = await authenticated_client.put(
            f"/api/v1/patients/{patient.id}",
            json=sample_patient_update_data,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["first_name"] == sample_patient_update_data["first_name"]
        assert data["loyalty_tier"] == sample_patient_update_data["loyalty_tier"]

    @pytest.mark.asyncio
    async def test_update_patient_not_found(
        self,
        authenticated_client: AsyncClient,
        sample_patient_update_data: dict,
    ):
        """Test update returns 404 for non-existent patient"""
        response = await authenticated_client.put(
            "/api/v1/patients/99999",
            json=sample_patient_update_data,
        )

        assert response.status_code == 404


class TestDeletePatient:
    """Tests for DELETE /api/v1/patients/{id}"""

    @pytest.mark.asyncio
    async def test_delete_patient_success(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        patient_factory,
    ):
        """Test successful patient deletion (soft delete)"""
        patient = await patient_factory.create()

        response = await authenticated_client.delete(f"/api/v1/patients/{patient.id}")

        assert response.status_code == 204

        # Verify patient is marked as inactive
        get_response = await authenticated_client.get(f"/api/v1/patients/{patient.id}")
        data = get_response.json()
        assert data["is_active"] is False


class TestPatientStatistics:
    """Tests for GET /api/v1/patients/statistics"""

    @pytest.mark.asyncio
    async def test_get_statistics(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        patient_factory,
    ):
        """Test statistics endpoint"""
        # Create patients with different tiers
        await patient_factory.create(loyalty_tier="Bronze", loyalty_points=100)
        await patient_factory.create(loyalty_tier="Bronze", loyalty_points=200)
        await patient_factory.create(loyalty_tier="Gold", loyalty_points=500)
        await patient_factory.create(
            loyalty_tier="Gold",
            loyalty_points=900,
            is_active=False,
        )

        response = await authenticated_client.get("/api/v1/patients/statistics")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert data["active"] == 3
        assert data["inactive"] == 1
        assert data["total_loyalty_points"] == 800
        assert data["by_loyalty_tier"] == {"Bronze": 2, "Gold": 1}
        assert "by_country" in data

    @pytest.mark.asyncio
    async def test_get_statistics_uses_persisted_purchase_lines(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        patient_factory,
    ):
        """Revenue statistics must be calculated from persisted purchase lines."""
        patient = await patient_factory.create(loyalty_points=0)

        test_db.add_all(
            [
                PatientPurchase(
                    patient_id=patient.id,
                    receipt_number="R-1001",
                    category="OTC",
                    quantity=2,
                    unit_price=12.50,
                    purchased_at=datetime.utcnow(),
                ),
                PatientPurchase(
                    patient_id=patient.id,
                    receipt_number="R-1002",
                    category="Rx",
                    quantity=3,
                    unit_price=7.25,
                    purchased_at=datetime.utcnow(),
                ),
            ]
        )
        await test_db.flush()

        response = await authenticated_client.get("/api/v1/patients/statistics")

        assert response.status_code == 200
        data = response.json()

        assert data["total_purchase_value"] == 46.75
