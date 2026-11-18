"""Tests for Health Canada's official MDALL medical-device normalizer."""

import pytest

from scripts.import_health_canada_mdall import normalize_mdall_records

pytestmark = pytest.mark.unit


def test_normalizer_joins_licences_devices_companies_and_identifiers():
    datasets = {
        "active_licences": [
            {
                "original_licence_no": 12345,
                "licence_status": "I",
                "appl_risk_class": 3,
                "licence_name": "Example implant",
                "first_licence_status_dt": "2024-01-15",
                "last_refresh_dt": "2026-10-01",
                "end_date": None,
                "company_id": 100,
                "licence_type_desc": "Device Family",
            }
        ],
        "archived_licences": [
            {
                "original_licence_no": 54321,
                "licence_status": "C",
                "appl_risk_class": 2,
                "company_id": 200,
                "licence_type_desc": "Device Group",
                "end_date": "2023-05-01",
            }
        ],
        "active_devices": [
            {
                "original_licence_no": 12345,
                "device_id": 9001,
                "trade_name": "Example Implant",
                "first_licence_dt": "2024-01-15",
                "end_date": None,
            }
        ],
        "archived_devices": [
            {
                "original_licence_no": 54321,
                "device_id": 9002,
                "trade_name": "Archived Device",
                "first_licence_dt": "2020-01-01",
                "end_date": "2023-05-01",
            }
        ],
        "active_identifiers": [
            {
                "original_licence_no": 12345,
                "device_id": 9001,
                "device_identifier": "UDI-CA-001",
                "end_date": None,
            }
        ],
        "archived_identifiers": [
            {
                "original_licence_no": 54321,
                "device_id": 9002,
                "device_identifier": "UDI-CA-OLD",
                "end_date": "2023-05-01",
            }
        ],
        "companies": [
            {
                "company_id": 100,
                "company_name": "Teva Medical Devices",
                "country_cd": "IL",
                "company_status": "A",
            },
            {
                "company_id": 200,
                "company_name": "Archived Manufacturer",
                "country_cd": "CA",
                "company_status": "I",
            },
        ],
    }

    rows = normalize_mdall_records(datasets)

    assert {row["source_record_id"] for row in rows} == {
        "MDALL:12345:9001",
        "MDALL:54321:9002",
    }
    active = next(row for row in rows if row["source_record_id"] == "MDALL:12345:9001")
    assert active["name"] == "Example Implant"
    assert active["manufacturer"] == "Teva Medical Devices"
    assert active["manufacturer_country"] == "IL"
    assert active["risk_class"] == "3"
    assert active["regulatory_status"] == "Issued / Active"
    assert active["authorizations"][0]["authorization_id"] == "12345"
    assert active["authorizations"][0]["effective_date"].isoformat() == "2024-01-15"
    assert active["identifiers"][0]["identifier_value"] == "UDI-CA-001"

    archived = next(
        row for row in rows if row["source_record_id"] == "MDALL:54321:9002"
    )
    assert archived["regulatory_status"] == "Cancelled"
    assert archived["authorizations"][0]["end_date"].isoformat() == "2023-05-01"
