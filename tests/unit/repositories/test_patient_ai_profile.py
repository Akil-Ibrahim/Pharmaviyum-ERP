"""Unit tests for minimum-necessary AI patient context."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.pharmaviyum.repositories.patient import PatientRepository
from src.pharmaviyum.schemas.patient import PatientAIProfile

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_ai_profile_returns_only_clinical_safety_context():
    repository = PatientRepository(AsyncMock())
    patient = SimpleNamespace(
        id=17,
        allergies=[SimpleNamespace(allergen_name="penicillin")],
        conditions=[SimpleNamespace(condition_name="hypertension")],
    )
    repository.get_by_id_with_relations = AsyncMock(return_value=patient)

    result = await repository.get_ai_profile(17, pharmacy_id=731)

    assert result == {
        "patient_id": 17,
        "allergies": ["penicillin"],
        "conditions": ["hypertension"],
    }
    assert PatientAIProfile.model_validate(result).patient_id == 17
    repository.get_by_id_with_relations.assert_awaited_once_with(
        17,
        pharmacy_id=731,
        include_allergies=True,
        include_conditions=True,
        include_insurances=False,
        include_consultations=False,
        include_purchases=False,
    )
