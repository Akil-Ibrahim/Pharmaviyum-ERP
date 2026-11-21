"""Tests for Health Canada's official MDALL response parsing."""

import pytest

from scripts.import_health_canada_mdall import _rows, normalize_mdall_records

pytestmark = pytest.mark.unit


def test_rows_accepts_list_singleton_and_wrapped_singleton_payloads():
    row = {"original_licence_no": 123, "licence_status": "I"}

    assert _rows([row]) == [row]
    assert _rows({"original_licence_no": 123, "licence_status": "I"}) == [row]
    assert _rows({"result": row}) == [row]
    assert _rows({"result": [row]}) == [row]


def test_rows_accepts_singleton_company_payload():
    company = {"company_id": 42, "company_name": "Example", "country_cd": "IL"}

    assert _rows({"result": company}) == [company]


def test_normalizer_keeps_device_when_company_is_not_present():
    datasets = {
        "active_licences": [
            {
                "original_licence_no": 123,
                "licence_status": "I",
                "company_id": 999,
                "appl_risk_class": 2,
            }
        ],
        "active_devices": [
            {
                "original_licence_no": 123,
                "device_id": 456,
                "trade_name": "Device without company response",
            }
        ],
    }

    rows = normalize_mdall_records(datasets)

    assert len(rows) == 1
    assert rows[0]["manufacturer"] is None
    assert rows[0]["regulatory_status"] == "Issued / Active"
