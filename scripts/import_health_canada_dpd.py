"""Stage Health Canada's Drug Product Database (DPD) as reference-only records.

The DPD is Canadian regulatory reference data. It is not a global catalogue and
its inclusion/status must not be interpreted as authorization in another market.
Only single-ingredient products with current Approved or Marketed status are
staged because the current canonical medicinal-product model is single-ingredient.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from typing import Any

import httpx

BASE_URL = "https://health-products.canada.ca/api/drug/"
SOURCE_NAME = "Health Canada DPD"
ENDPOINTS = {
    "products": "drugproduct/?lang=en&type=json",
    "ingredients": "activeingredient/?lang=en&type=json",
    "forms": "form/?lang=en&type=json",
    "routes": "route/?lang=en&type=json",
    "statuses": "status/?lang=en&type=json",
    "packaging": "packaging/?type=json",
}


def _rows(value: Any) -> list[dict[str, Any]]:
    """Normalize the DPD API's list or single-object response shape."""
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        return [value]
    raise ValueError("Health Canada DPD returned an unexpected JSON response")


def normalize_dpd_records(
    products: list[dict[str, Any]],
    ingredients: list[dict[str, Any]],
    forms: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    statuses: list[dict[str, Any]],
    packaging: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Normalize current single-ingredient Canadian drug product records."""
    ingredients_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    forms_by_code: dict[str, set[str]] = defaultdict(set)
    routes_by_code: dict[str, set[str]] = defaultdict(set)
    packaging_by_code: dict[str, set[str]] = defaultdict(set)
    status_by_code: dict[str, tuple[str, str]] = {}

    for row in ingredients:
        ingredients_by_code[str(row.get("drug_code", ""))].append(row)
    for row in forms:
        name = str(row.get("pharmaceutical_form_name") or "").strip()
        if name:
            forms_by_code[str(row.get("drug_code", ""))].add(name)
    for row in routes:
        name = str(row.get("route_of_administration_name") or "").strip()
        if name:
            routes_by_code[str(row.get("drug_code", ""))].add(name)
    for row in packaging:
        info = str(row.get("product_information") or "").strip()
        if info:
            packaging_by_code[str(row.get("drug_code", ""))].add(info)
    for row in statuses:
        code = str(row.get("drug_code", ""))
        name = str(row.get("status") or "").strip()
        history_date = str(row.get("history_date") or "")
        if code and (code not in status_by_code or history_date > status_by_code[code][0]):
            status_by_code[code] = (history_date, name)

    normalized: list[dict[str, str]] = []
    for product in products:
        code = str(product.get("drug_code", "")).strip()
        if not code:
            continue
        current_status = status_by_code.get(code, ("", ""))[1]
        if current_status not in {"Approved", "Marketed"}:
            continue
        product_ingredients = ingredients_by_code.get(code, [])
        if str(product.get("number_of_ais", "")) != "1" or len(product_ingredients) != 1:
            continue
        ingredient = product_ingredients[0]
        ingredient_name = str(ingredient.get("ingredient_name") or "").strip()
        if not ingredient_name:
            continue

        strength_value = str(ingredient.get("strength") or "").strip()
        strength_unit = str(ingredient.get("strength_unit") or "").strip()
        strength = " ".join(part for part in (strength_value, strength_unit) if part)
        din = str(product.get("drug_identification_number") or "").strip()
        brand = str(product.get("brand_name") or "").strip()
        normalized.append(
            {
                "source_record_id": f"DPD:{code}",
                "product_name": brand or str(product.get("descriptor") or ingredient_name),
                "brand_name": brand,
                "ingredient_name": ingredient_name,
                "strength": strength,
                "dosage_form": " / ".join(sorted(forms_by_code.get(code, set()))),
                "route": " / ".join(sorted(routes_by_code.get(code, set()))),
                "manufacturer": str(product.get("company_name") or "").strip(),
                "country": "CA",
                "regulatory_id": din,
                "authorization_status": current_status,
                "product_class": str(product.get("class_name") or "").strip(),
                "package_description": " / ".join(sorted(packaging_by_code.get(code, set()))),
                "last_update_date": str(product.get("last_update_date") or ""),
            }
        )
    return normalized


async def download_dpd() -> tuple[dict[str, list[dict[str, Any]]], str]:
    """Fetch the complete public DPD API resources and return a content version."""
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


async def stage_catalog(
    datasets: dict[str, list[dict[str, Any]]], version: str
) -> tuple[int, int]:
    """Persist new DPD source records without creating approved catalog or stock."""
    from sqlalchemy import select

    from src.pharmaviyum.database import AsyncSessionLocal
    from src.pharmaviyum.models.drug_catalog import DrugCatalogSourceRecord

    rows = normalize_dpd_records(
        datasets["products"],
        datasets["ingredients"],
        datasets["forms"],
        datasets["routes"],
        datasets["statuses"],
        datasets["packaging"],
    )
    async with AsyncSessionLocal() as session:
        existing_result = await session.execute(
            select(
                DrugCatalogSourceRecord.source_record_id,
                DrugCatalogSourceRecord.normalized_payload,
            ).where(DrugCatalogSourceRecord.source_name == SOURCE_NAME)
        )
        existing_payloads = {
            source_id: payload for source_id, payload in existing_result.all()
        }
        staged = 0
        for row in rows:
            source_id = row["source_record_id"]
            payload = {
                key: value for key, value in row.items() if key != "source_record_id"
            }
            if existing_payloads.get(source_id) == payload:
                continue
            session.add(
                DrugCatalogSourceRecord(
                    source_name=SOURCE_NAME,
                    source_record_id=source_id,
                    source_version=version,
                    source_url=BASE_URL,
                    license_terms=(
                        "Health Canada Drug Product Database public API; verify "
                        "applicable reuse and redistribution terms."
                    ),
                    extracted_at=datetime.utcnow(),
                    normalized_payload=payload,
                )
            )
            existing_payloads[source_id] = payload
            staged += 1
        await session.commit()
    return staged, len(rows) - staged


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download and normalize DPD without writing to the database.",
    )
    args = parser.parse_args()
    datasets, version = await download_dpd()
    rows = normalize_dpd_records(
        datasets["products"],
        datasets["ingredients"],
        datasets["forms"],
        datasets["routes"],
        datasets["statuses"],
        datasets["packaging"],
    )
    if args.dry_run:
        print(
            f"Health Canada DPD dry run: {len(rows)} current single-ingredient "
            "products normalized; database unchanged."
        )
        return
    staged, skipped = await stage_catalog(datasets, version)
    print(
        f"Health Canada DPD staging complete: {staged} new records, {skipped} "
        "already present for this source version. All new records remain "
        "pending review; no sellable Product, price, batch, or stock was created."
    )


if __name__ == "__main__":
    asyncio.run(main())
