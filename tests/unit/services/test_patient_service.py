"""Unit tests for PatientService
Best practice 2026: Comprehensive service layer testing"""

import pytest
from unittest.mock import AsyncMock, patch
from src.pharmaviyum.services.patient import PatientService
from src.pharmaviyum.schemas.patient import PatientCreate, PatientUpdate
from src.pharmaviyum.models.patients import Patient

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
    repo.record_visit = AsyncMock()
    return repo

@pytest.fixture
def patient_service(mock_repository):
    """Patient service with mocked repository"""
    return PatientService(mock_repository)

@pytest.fixture
def sample_patient_data():
    """Sample patient creation data"""
    return PatientCreate(
        first_name="Ibrahim",
        last_name="Ibrahim",
        phone="+84123456789",
        email="ibrahim@example.com",
        country="VN",
    )

@pytest.fixture
def sample_patient():
    """Sample patient instance"""
    return Patient(
        id=1,
        first_name="Ibrahim",
        last_name="Ibrahim",
        full_name="Ibrahim Ibrahim",
        phone="+84123456789",
        email="ibrahim@example.com",
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
    async def test_create_patient_success(self, patient_service, mock_repository, sample_patient_data, sample_patient):
        """Test successful patient creation"""
        mock_repository.create.return_value = sample_patient
        result = await patient_service.create_patient(sample_patient_data)
        assert result.id == 1
        assert result.full_name == "Ibrahim Ibrahim"
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_phone(self, patient_service, mock_repository, sample_patient_data, sample_patient):
        """Test creation fails with duplicate phone"""
        mock_repository.get_by_phone.return_value = sample_patient
        with pytest.raises(ValueError, match="already exists"):
            await patient_service.create_patient(sample_patient_data)

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_email(self, patient_service, mock_repository, sample_patient_data, sample_patient):
        """Test creation fails with duplicate email"""
        mock_repository.get_by_email.return_value = sample_patient
        with pytest.raises(ValueError, match="already exists"):
            await patient_service.create_patient(sample_patient_data)

class TestPatientServiceGet:
    """Tests for get methods"""

    @pytest.mark.asyncio
    async def test_get_patient_success(self, patient_service, mock_repository, sample_patient):
        mock_repository.get_by_id_with_relations.return_value = sample_patient
        result = await patient_service.get_patient(1)
        assert result.id == 1
        mock_repository.get_by_id_with_relations.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_patient_not_found(self, patient_service, mock_repository):
        mock_repository.get_by_id_with_relations.return_value = None
        result = await patient_service.get_patient(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_patient_by_phone(self, patient_service, mock_repository, sample_patient):
        mock_repository.get_by_phone.return_value = sample_patient
        result = await patient_service.get_patient_by_phone("+84123456789")
        assert result.phone == "+84123456789"

class TestPatientServiceUpdate:
    """Tests for update_patient method"""

    @pytest.mark.asyncio
    async def test_update_patient_success(self, patient_service, mock_repository, sample_patient):
        mock_repository.get_by_id_with_relations.return_value = sample_patient
        mock_repository.update.return_value = sample_patient
        update_data = PatientUpdate(first_name="Новое имя")
        result = await patient_service.update_patient(1, update_data)
        assert result is not None
        mock_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_patient_not_found(self, patient_service, mock_repository):
        mock_repository.get_by_id_with_relations.return_value = None
        update_data = PatientUpdate(first_name="Новое имя")
        result = await patient_service.update_patient(999, update_data)
        assert result is None

class TestPatientServiceDelete:
    """Tests for delete_patient method"""

    @pytest.mark.asyncio
    async def test_soft_delete_success(self, patient_service, mock_repository):
        mock_repository.soft_delete.return_value = True
        result = await patient_service.delete_patient(1, hard_delete=False)
        assert result is True
        mock_repository.soft_delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_hard_delete_with_feature_flag_disabled(self, patient_service, mock_repository):
        mock_repository.soft_delete.return_value = True
        with patch("src.pharmaviyum.services.patient.is_feature_enabled", return_value=False):
            result = await patient_service.delete_patient(1, hard_delete=True)
            assert result is True
            mock_repository.soft_delete.assert_called_once()

class TestPatientServiceStatistics:
    """Tests for statistics methods"""

    @pytest.mark.asyncio
    async def test_get_statistics(self, patient_service, mock_repository):
        mock_repository.count.side_effect = [100, 80]
        mock_repository.get_loyalty_tiers_stats.return_value = {"Bronze": 50, "Silver": 30, "Gold": 20}
        mock_repository.get_country_stats.return_value = {"VN": 60, "TH": 20, "MY": 20}
        result = await patient_service.get_statistics()
        assert result["total"] == 100
        assert result["active"] == 80
        assert result["inactive"] == 20
        assert "by_loyalty_tier" in result
        assert "by_country" in result
