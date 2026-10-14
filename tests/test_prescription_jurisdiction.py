"""Regression tests for jurisdiction-aware prescription verification."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest


@pytest.mark.unit
class TestPrescriptionJurisdiction:
    @pytest.mark.asyncio
    async def test_missing_country_does_not_default_to_vietnam(self):
        from src.pharmaviyum.ai.mcp.tools.prescription_verification import (
            _check_expiry,
            _check_jurisdiction,
        )

        prescription = SimpleNamespace(
            date_expires=None,
            date_issued=datetime.utcnow() - timedelta(days=1),
        )

        jurisdiction = _check_jurisdiction(None)
        expiry = await _check_expiry(prescription, None)

        assert jurisdiction.passed is False
        assert "missing" in (jurisdiction.details or "")
        assert expiry.passed is False
        assert "no configured validity period" in (expiry.details or "")

    @pytest.mark.asyncio
    async def test_unsupported_country_does_not_receive_default_validity(self):
        from src.pharmaviyum.ai.mcp.tools.prescription_verification import (
            _check_expiry,
            _check_jurisdiction,
        )

        prescription = SimpleNamespace(
            date_expires=None,
            date_issued=datetime.utcnow() - timedelta(days=1),
        )

        jurisdiction = _check_jurisdiction("UA")
        expiry = await _check_expiry(prescription, "UA")

        assert jurisdiction.passed is False
        assert expiry.passed is False
        assert "UA" in (expiry.details or "")

    @pytest.mark.asyncio
    async def test_configured_market_uses_explicit_market_validity(self):
        from src.pharmaviyum.ai.mcp.tools.prescription_verification import (
            _check_expiry,
            _check_jurisdiction,
        )

        prescription = SimpleNamespace(
            date_expires=None,
            date_issued=datetime.utcnow() - timedelta(days=1),
        )

        jurisdiction = _check_jurisdiction("VN")
        expiry = await _check_expiry(prescription, "VN")

        assert jurisdiction.passed is True
        assert expiry.passed is True
        assert "Valid until" in (expiry.details or "")

    @pytest.mark.asyncio
    async def test_unknown_market_cannot_pass_quantity_check(self):
        from src.pharmaviyum.ai.mcp.tools.prescription_verification import (
            _check_quantity_limits,
        )

        item = SimpleNamespace(medication_name="Diazepam", quantity_prescribed=10)

        result = await _check_quantity_limits(item, "UA")

        assert result.passed is False
        assert "cannot verify" in result.details.lower()
