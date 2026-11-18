"""Import Health Canada's official Medical Devices Active Licence Listing (MDALL).

The importer preserves active and archived licences, device identifiers, risk class,
manufacturer details and source provenance. It creates reference records only; it
never creates pharmacy SKUs, purchase orders, batches, prices or inventory.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import date, datetime
from typing import Any

import httpx

BASE_URL = "https://health-products.canada.ca/api/medical-devices/"
SOURCE_NAME = "Health Canada MDALL"
SOURCE_URL = "https://health-products.canada.ca/api/documentation/mdall-documentation-en.html"
ENDPOINTS = {
    "active_licences": "licence/?state=active&lang=en&type=json",
    "archived_licences": "licence/?state=archived&lang=en&type=json",
    "active_devices": "device/?state=active&type=json",
    "archived_devices": "device/?state=archived&type=json",
    "active_identifiers": "deviceidentifier/?state=active&type=json",
    "archived_identifiers": "deviceidentifier/?state=archived&type=json",
    "companies": "company/?type=json",
}
LICENCE_STATUS = {
    "C": "Cancelled",
    "D": "Issued / Conditional",
    "I": "Issued / Active",
    "M": "Merged",
    "O": "Discontinued at Renewal",
    "P": "Pending Signature",
    "R": "Cancelled - Renewal No Response",
    "S": "Suspended",
    "W": "Withdrawn",
    "Q": "Suspended / Invalid QS Certification",
    "X": "Cancelled",
}


def _rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        nested = value.get("result") or value.get("data")
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]
        if isinstance(nested, dict):
            return [nested]
        if "original_licence_no" in value or "device_id" in value or "company_id" in value:
            return [value]
    return []


def _date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def normalize_mdall_records(
    datasets: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Join official licence, device, company and device-identifier records."""
    licences = {
        str(row.get("original_licence_no")): row
        for name in ("active_licences", "archived_licences")
        for row in datasets.get(name, [])
        if row.get("original_licence_no") is not None
    }
    companies = {
        str(row.get("company_id")): row
        for row in datasets.get("companies", [])
        if row.get("company_id") is not None
    }
    identifiers_by_device: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for source_name in ("active_identifiers", "archived_identifiers"):
        for row in datasets.get(source_name, []):
            licence_no = str(row.get("original_licence_no") or "").strip()
            device_id = str(row.get("device_id") or "").strip()
            if licence_no and device_id:
                identifiers_by_device.setdefault((licence_no, device_id), []).append(row)

    normalized: dict[str, dict[str, Any]] = {}
    for source_name in ("active_devices", "archived_devices"):
        for device in datasets.get(source_name, []):
            device_id = str(device.get("device_id") or "").strip()
            licence_no = str(device.get("original_licence_no") or "").strip()
            trade_name = str(device.get("trade_name") or "").strip()
            if not device_id or not licence_no or not trade_name:
                continue

            licence = licences.get(licence_no, {})
            company = companies.get(str(licence.get("company_id") or ""), {})
            status_code = str(licence.get("licence_status") or "").strip().upper()
            record_id = f"MDALL:{licence_no}:{device_id}"
            identifier_rows = identifiers_by_device.get((licence_no, device_id), [])
            identifiers = [
                {
                    "identifier_type": "MDALL_DEVICE_IDENTIFIER",
                    "identifier_value": str(item.get("device_identifier") or "").strip(),
                    "issuing_agency": None,
                    "is_primary": False,
                    "raw_payload": item,
                }
                for item in identifier_rows
                if str(item.get("device_identifier") or "").strip()
            ]
            normalized[record_id] = {
                "source_record_id": record_id,
                "name": trade_name,
                "brand_name": trade_name,
                "model": None,
                "manufacturer": str(company.get("company_name") or "").strip() or None,
                "manufacturer_country": str(company.get("country_cd") or "").strip() or None,
                "country": "CA",
                "device_type": str(licence.get("licence_type_desc") or "").strip() or None,
                "risk_class": str(licence.get("appl_risk_class") or "").strip() or None,
                "regulatory_status": LICENCE_STATUS.get(status_code, status_code or "Unknown"),
                "source_updated_at": _date(licence.get("last_refresh_dt")),
                "source_url": SOURCE_URL,
                "license_terms": (
                    "Health Canada MDALL public API. Verify current Government of Canada "
                    "open-licence, attribution and redistribution terms before republication."
                ),
                "identifiers": identifiers,
                "authorizations": [
                    {
                        "country": "CA",
                        "authorization_id": licence_no,
                        "authorization_type": str(
                            licence.get("licence_type_desc") or ""
                        ).strip() or None,
                        "status": LICENCE_STATUS.get(
                            status_code, status_code or "Unknown"
                        ),
                        "risk_class": str(
                            licence.get("appl_risk_class") or ""
                        ).strip() or None,
                        "effective_date": _date(
                            licence.get("first_licence_status_dt")
                        ),
                        "end_date": _date(licence.get("end_date")),
                        "source_updated_at": _date(licence.get("last_refresh_dt")),
                        "raw_payload": licence,
                    }
                ],
                "raw_payload": {
                    "device": device,
                    "licence": licence,
                    "company": company,
                    "identifiers": identifier_rows,
                },
            }
    return list(normalized.values())


async def download_mdall() -> tuple[dict[str, list[dict[str, Any]]], str]:
    """Download active and archived MDALL data and calculate a stable version."""
    timeout = httpx.Timeout(180.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        async def fetch(name: str, path: str) -> tuple[str, bytes]:
            response = await client.get(BASE_URL + path)
            response.raise_for_status()
            return name, response.content

        downloads = await asyncio.gather(
            *(fetch(name, path) for name, path in ENDPOINTS.items())
        )
    raw_by_name = dict(downloads)
    digest = hashlib.sha256()
    datasets: dict[str, list[dict[str, Any]]] = {}
    for name in sorted(raw_by_name):
        digest.update(name.encode("utf-8"))
        digest.update(raw_by_name[name])
        datasets[name] = _rows(json.loads(raw_by_name[name]))
    return datasets, f"sha256:{digest.hexdigest()}"


async def stage_mdall(
    datasets: dict[str, list[dict[str, Any]]], version: str
) -> tuple[int, int, int]:
    """Idempotently upsert source-specific device and authorization references."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from src.pharmaviyum.database import AsyncSessionLocal
    from src.pharmaviyum.models.medical_device import (
        MedicalDevice,
        MedicalDeviceAuthorization,
        MedicalDeviceIdentifier,
    )

    rows = normalize_mdall_records(datasets)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MedicalDevice)
            .options(
                selectinload(MedicalDevice.identifiers),
                selectinload(MedicalDevice.authorizations),
            )
            .where(MedicalDevice.source_name == SOURCE_NAME)
        )
        existing = {row.source_record_id: row for row in result.scalars().all()}
        created = updated = skipped = 0
        for row in rows:
            source_record_id = row["source_record_id"]
            identifiers = row["identifiers"]
            authorizations = row["authorizations"]
            payload = row["raw_payload"]
            device = existing.get(source_record_id)
            if device is not None and device.raw_payload == payload:
                if device.source_version != version:
                    device.source_version = version
                    device.imported_at = datetime.utcnow()
                    updated += 1
                else:
                    skipped += 1
                continue

            values = {
                key: value
                for key, value in row.items()
                if key not in {
                    "source_record_id",
                    "identifiers",
                    "authorizations",
                    "raw_payload",
                }
            }
            if device is None:
                device = MedicalDevice(
                    source_name=SOURCE_NAME,
                    source_record_id=source_record_id,
                    source_version=version,
                    raw_payload=payload,
                    **values,
                )
                session.add(device)
                await session.flush()
                created += 1
            else:
                for key, value in values.items():
                    setattr(device, key, value)
                device.source_version = version
                device.raw_payload = payload
                device.imported_at = datetime.utcnow()
                device.identifiers.clear()
                device.authorizations.clear()
                updated += 1

            device.identifiers = [
                MedicalDeviceIdentifier(
                    identifier_type=item["identifier_type"],
                    identifier_value=item["identifier_value"],
                    issuing_agency=item["issuing_agency"],
                    is_primary=item["is_primary"],
                    raw_payload=item["raw_payload"],
                )
                for item in identifiers
            ]
            device.authorizations = [
                MedicalDeviceAuthorization(**item) for item in authorizations
            ]
        await session.commit()
    return created, updated, skipped


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download and normalize MDALL without writing to the database.",
    )
    args = parser.parse_args()
    datasets, version = await download_mdall()
    rows = normalize_mdall_records(datasets)
    if args.dry_run:
        print(
            f"Health Canada MDALL dry run: {len(rows)} device/licence records, "
            f"{sum(len(row['identifiers']) for row in rows)} identifiers; "
            "database unchanged."
        )
        return
    created, updated, skipped = await stage_mdall(datasets, version)
    print(
        f"Health Canada MDALL staging complete: {created} created, "
        f"{updated} updated, {skipped} unchanged; reference data only."
    )


if __name__ == "__main__":
    asyncio.run(main())
