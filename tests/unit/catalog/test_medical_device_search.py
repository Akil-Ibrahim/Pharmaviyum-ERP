"""Regression tests for medical-device reference search."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.pharmaviyum.api.v1.medical_devices import search_medical_devices


@pytest.mark.asyncio
async def test_search_includes_device_identifier_and_authorization_number():
    device = SimpleNamespace(
        id=1,
        source_name="Health Canada MDALL",
        source_record_id="MDALL:12345:9001",
        country="CA",
        name="Example Implant",
        brand_name="Example Implant",
        model=None,
        manufacturer="Example Devices",
        manufacturer_country="CA",
        device_type="Device Family",
        risk_class="3",
        intended_purpose=None,
        regulatory_status="Issued / Active",
        source_updated_at=date(2026, 10, 1),
        identifiers=[],
        authorizations=[],
    )
    scalars = MagicMock()
    scalars.unique.return_value.all.return_value = [device]
    result = MagicMock()
    result.scalars.return_value = scalars
    db = SimpleNamespace(execute=AsyncMock(return_value=result))

    rows = await search_medical_devices(
        db=db,
        _=SimpleNamespace(id=1),
        q="UDI-CA-001",
        limit=20,
        country="CA",
        status=None,
    )

    assert len(rows) == 1
    assert rows[0].source_record_id == "MDALL:12345:9001"
    statement = db.execute.await_args.args[0]
    sql = str(statement.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "medical_device_identifiers.identifier_value" in sql
    assert "medical_device_authorizations.authorization_id" in sql
    assert "medical_devices.source_record_id" in sql
