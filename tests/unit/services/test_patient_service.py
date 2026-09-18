"""
Unit tests for PatientService
Best practice 2026: Comprehensive service layer testing with mocks
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.pharmaviyum.models.patients import Patient
from src.pharmaviyum.schemas.patient import PatientCreate, PatientUpdate
from src.pharmaviyum.services.patient import PatientService

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_repository():
    """Mock patient repository"""
    repo = AsyncMock()
    repo.get_by_phone = AsyncMock(return_value=None)
    repo.get_by_email = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_id_with_relations = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock(return_value=True)
    repo.soft_delete = AsyncMock(return_value=True)
    repo.search = AsyncMock(return_value=([], 0))
    repo.count = AsyncMock(return_value=0)
    repo.get_loyalty_tiers_stats = AsyncMock(return_value={})
    repo.get_country_stats = AsyncMock(return_value={})
    repo.get_total_purchase_value = AsyncMock(return_value=0.0)
    repo.get_total_loyalty_points = AsyncMock(return_value=0)
    repo.record_visit = AsyncMock()
    return repo


@pytest.fixture
def patient_service(mock_repository, mock_cache_service, mock_event_bus):
    """Patient service with mocked dependencies"""
    return PatientService(mock_repository)


@pytest.fixture
def sample_patient():
    """Sample patient instance"""
    return Patient(
        id=1,
        first_name="Ибрагим",
        last_name="Тестов",
        full_name="Ibrahim Ibrahim",
        phone="+84123456789",
        email="ibragim@example.com",
        country="VN",
        loyalty_tier="Bronze",
        loyalty_points=0,
        total_purchases=0,
        visit_count=0,
        is_active=True,
    )


class TestPatientServiceCreate:
    """Tests for create_patient method"""

    @pytest.mark.asyncio
    async def test_create_patient_success(
        self,
        patient_service,
        mock_repository,
        mock_event_bus,
    ):
        """Test successful patient creation"""
        # Arrange
        patient_data = PatientCreate(
            first_name="Ибрагим",
            last_name="Тестов",
            phone="+84123456789",
            email="ibragim@example.com",
            country="VN",
        )

        expected_patient = Patient(
            id=1,
            first_name="Ибрагим",
            last_name="Тестов",
            full_name="Ibrahim Ibrahim",
            phone="+84123456789",
        )
        mock_repository.create.return_value = expected_patient

        # Act
        result = await patient_service.create_patient(patient_data)

        # Assert
        assert result.id == 1
        assert result.full_name == "Ibrahim Ibrahim"
        mock_repository.create.assert_called_once()
        mock_event_bus.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_phone(
        self,
        patient_service,
        mock_repository,
    ):
        """Test creation fails with duplicate phone"""
        # Arrange
        patient_data = PatientCreate(
            first_name="Ибрагим",
            last_name="Тестов",
            phone="+84123456789",
        )

        existing_patient = Patient(id=1, phone="+84123456789")
        mock_repository.get_by_phone.return_value = existing_patient

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            await patient_service.create_patient(patient_data)


class TestPatientServiceGet:
    """Tests for get methods"""

    @pytest.mark.asyncio
    async def test_get_patient_with_cache(
        self,
        patient_service,
        mock_repository,
        mock_cache_service,
        sample_patient,
    ):
        """Test patient retrieval uses cache"""
        # Arrange
        mock_cache_service.get.return_value = sample_patient

        # Act
        result = await patient_service.get_patient(1)

        # Assert
        assert result.id == 1
        mock_cache_service.get.assert_called_once()
        mock_repository.get_by_id_with_relations.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_patient_cache_miss(
        self,
        patient_service,
        mock_repository,
        mock_cache_service,
        sample_patient,
    ):
        """Test patient retrieval on cache miss"""
        # Arrange
        mock_cache_service.get.return_value = None
        mock_repository.get_by_id_with_relations.return_value = sample_patient

        # Act
        result = await patient_service.get_patient(1)

        # Assert
        assert result.id == 1
        mock_cache_service.get.assert_called_once()
        mock_repository.get_by_id_with_relations.assert_called_once()
        mock_cache_service.set.assert_called_once()


class TestPatientServiceUpdate:
    """Tests for update_patient method"""

    @pytest.mark.asyncio
    async def test_update_patient_success(
        self,
        patient_service,
        mock_repository,
        mock_cache_service,
        mock_event_bus,
        sample_patient,
    ):
        """Test successful patient update"""
        # Arrange
        mock_repository.get_by_id_with_relations.return_value = sample_patient
        mock_repository.update.return_value = sample_patient

        update_data = PatientUpdate(first_name="Новое имя")

        # Act
        result = await patient_service.update_patient(1, update_data)

        # Assert
        assert result is not None
        mock_repository.update.assert_called_once()
        mock_cache_service.delete.assert_called()
        mock_event_bus.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_patient_duplicate_phone(
        self,
        patient_service,
        mock_repository,
        sample_patient,
    ):
        """Test update fails with duplicate phone"""
        # Arrange
        mock_repository.get_by_id_with_relations.return_value = sample_patient

        other_patient = Patient(id=2, phone="+84999999999")
        mock_repository.get_by_phone.return_value = other_patient

        update_data = PatientUpdate(phone="+84999999999")

        # Act & Assert
        with pytest.raises(ValueError, match="already in use"):
            await patient_service.update_patient(1, update_data)


class TestPatientServiceDelete:
    """Tests for delete_patient method"""

    @pytest.mark.asyncio
    async def test_soft_delete_success(
        self,
        patient_service,
        mock_repository,
        mock_cache_service,
        mock_event_bus,
    ):
        """Test successful soft delete"""
        # Arrange
        mock_repository.soft_delete.return_value = True

        # Act
        result = await patient_service.delete_patient(1, hard_delete=False)

        # Assert
        assert result is True
        mock_repository.soft_delete.assert_called_once_with(1)
        mock_cache_service.delete.assert_called()
        mock_event_bus.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_hard_delete_with_feature_flag_disabled(
        self,
        patient_service,
        mock_repository,
    ):
        """Test hard delete falls back to soft when feature flag disabled"""
        # Arrange
        mock_repository.soft_delete.return_value = True

        with patch(
            "src.pharmaviyum.services.patient.is_feature_enabled",
            return_value=False,
        ):
            # Act
            result = await patient_service.delete_patient(1, hard_delete=True)

        # Assert
        assert result is True
        mock_repository.soft_delete.assert_called_once()


class TestPatientServiceStatistics:
    """Tests for statistics methods"""

    @pytest.mark.asyncio
    async def test_get_statistics(
        self,
        patient_service,
        mock_repository,
    ):
        """Test statistics retrieval"""
        # Arrange
        mock_repository.count.side_effect = [100, 80]
        mock_repository.get_loyalty_tiers_stats.return_value = {
            "Bronze": 50,
            "Silver": 30,
            "Gold": 20,
        }
        mock_repository.get_country_stats.return_value = {
            "VN": 60,
            "TH": 20,
        }
        mock_repository.get_total_purchase_value.return_value = 12500.5
        mock_repository.get_total_loyalty_points.return_value = 3400

        # Act
        result = await patient_service.get_statistics()

        # Assert
        assert result["total"] == 100
        assert result["active"] == 80
        assert result["inactive"] == 20
        assert "by_loyalty_tier" in result
        assert "by_country" in result
        assert result["total_purchase_value"] == 12500.5
        assert result["total_loyalty_points"] == 3400
