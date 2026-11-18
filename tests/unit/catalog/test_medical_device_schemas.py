"""Schema tests for medical-device reference search responses."""

from datetime import date
from types import SimpleNamespace

import pytest

from src.pharmaviyum.schemas.medical_device import MedicalDeviceSearchResult

pytestmark = pytest.mark.unit


def test_medical_device_result_exposes_udi_and_regulatory_authorization():
    device = SimpleNamespace(
        id=1,
        source_name="Health Canada MDALL",
        source_record_id="MDALL:12345:9001",
        country="CA",
        name="Example Implant",
        brand_name="Example Implant",
        model=None,
        manufacturer="Teva Medical Devices",
        manufacturer_country="IL",
        device_type="Device Family",
        risk_class="3",
        intended_purpose=None,
        regulatory_status="Issued / Active",
        source_updated_at=date(2026, 10, 1),
        identifiers=[
            SimpleNamespace(
                identifier_type="MDALL_DEVICE_IDENTIFIER",
                identifier_value="UDI-CA-001",
                issuing_agency=None,
                is_primary=False,
            )
        ],
        authorizations=[
            SimpleNamespace(
                country="CA",
                authorization_id="12345",
                authorization_type="Device Family",
                status="Issued / Active",
                risk_class="3",
                effective_date=date(2024, 1, 15),
                end_date=None,
                source_updated_at=date(2026, 10, 1),
            )
        ],
    )

    result = MedicalDeviceSearchResult.model_validate(device)

    assert result.identifiers[0].identifier_value == "UDI-CA-001"
    assert result.authorizations[0].authorization_id == "12345"
    assert result.manufacturer_country == "IL"
    assert result.regulatory_status == "Issued / Active"
