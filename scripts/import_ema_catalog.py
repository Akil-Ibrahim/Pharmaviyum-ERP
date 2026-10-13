"""Import EMA Article 57 European Economic Area medicine data.

The official EMA XLSX is regulatory reference data, not pharmacy stock.
This parser supports the EMA's "Name of medicinal product" and "Country where
authorised" header wording as well as common variants. Multi-ingredient rows
are skipped until the schema can represent multiple active substances.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import re
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import httpx

EMA_URL = "https://www.ema.europa.eu/en/documents/other/article-57-product-data_en.xlsx"
NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
SEPARATOR_RE = re.compile(r"\s*[;\n]\s*")


def _column_index(cell_ref: str) -> int:
    match = re.match(r"[A-Z]+", cell_ref)
    if match is None:
        raise ValueError(f"Invalid XLSX cell reference: {cell_ref}")
    value = 0
    for char in match.group(0):
        value = value * 26 + ord(char) - ord("A") + 1
    return value - 1


def _cell_value(cell: ET.Element, shared: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    value = cell.find("m:v", NS)
    if cell_type == "s" and value is not None:
        return shared[int(value.text or "0")]
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//m:t", NS))
    return (value.text or "") if value is not None else ""


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def parse_ema_xlsx(path: Path) -> list[dict[str, str]]:
    """Parse EMA Article 57 rows by header names rather than fixed column order."""
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.findall(".//m:t", NS))
                for item in root.findall("m:si", NS)
            ]

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheet = workbook.find("m:sheets/m:sheet", NS)
        if sheet is None:
            raise ValueError("EMA workbook has no worksheets")
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relationship_id = sheet.attrib[f"{{{NS['r']}}}id"]
        target = next(
            (
                item.attrib["Target"]
                for item in relationships
                if item.attrib.get("Id") == relationship_id
            ),
            None,
        )
        if not target:
            raise ValueError("EMA workbook worksheet relationship is missing")
        sheet_path = (
            target.lstrip("/")
            if target.startswith("/")
            else f"xl/{target}"
        )
        if sheet_path not in names:
            raise ValueError("EMA workbook worksheet XML is missing")

        root = ET.fromstring(archive.read(sheet_path))
        rows: list[list[str]] = []
        for row in root.findall(".//m:sheetData/m:row", NS):
            cells = {
                _column_index(cell.attrib.get("r", "A1")): _cell_value(cell, shared).strip()
                for cell in row.findall("m:c", NS)
            }
            if cells:
                rows.append([cells.get(i, "") for i in range(max(cells) + 1)])

    header_index = next(
        (
            i for i, row in enumerate(rows)
            if any(
                _normalize_header(value) in {
                    "product name",
                    "name of medicinal product",
                    "medicinal product name",
                }
                or (
                    "product" in _normalize_header(value)
                    and "name" in _normalize_header(value)
                )
                for value in row
            )
            and any("active substance" in _normalize_header(value) for value in row)
        ),
        None,
    )
    if header_index is None:
        raise ValueError(
            "Could not identify EMA medicinal-product-name and active-substance columns"
        )

    headers = [_normalize_header(value) for value in rows[header_index]]

    def find_column(*needles: str) -> int | None:
        return next(
            (
                i for i, header in enumerate(headers)
                if all(needle in header for needle in needles)
            ),
            None,
        )

    product_col = next(
        (
            i for i, header in enumerate(headers)
            if header in {"product name", "name of medicinal product", "medicinal product name"}
            or ("product" in header and "name" in header)
        ),
        None,
    )
    ingredient_col = find_column("active", "substance")
    route_col = find_column("route", "administration")
    strength_col = find_column("strength")
    form_col = find_column("pharmaceutical", "form") or find_column("dosage", "form")
    country_col = (
        find_column("country", "authorisation")
        or find_column("country", "authorization")
        or find_column("country", "where", "authorised")
        or find_column("country", "where", "authorized")
        or find_column("country")
    )
    holder_col = (
        find_column("marketing", "authorisation", "holder")
        or find_column("marketing", "authorization", "holder")
        or find_column("authorisation", "holder")
        or find_column("authorization", "holder")
    )
    if product_col is None or ingredient_col is None or country_col is None:
        raise ValueError(f"EMA workbook is missing required columns: {headers!r}")

    parsed: list[dict[str, str]] = []
    for row in rows[header_index + 1:]:
        def value(index: int | None) -> str:
            return row[index].strip() if index is not None and index < len(row) else ""

        product_name = value(product_col)
        ingredient_text = value(ingredient_col)
        country = value(country_col)
        if not product_name or not ingredient_text or not country:
            continue
        ingredients = [
            part.strip()
            for part in SEPARATOR_RE.split(ingredient_text)
            if part.strip()
        ]
        if len(ingredients) != 1:
            continue
        parsed.append({
            "product_name": product_name,
            "ingredient": ingredients[0],
            "strength": value(strength_col),
            "dosage_form": value(form_col),
            "route": value(route_col),
            "country": country,
            "holder": value(holder_col),
        })
    return parsed


def _regulatory_id(row: dict[str, str]) -> str:
    identity = "|".join(
        row[key].casefold().strip()
        for key in ("product_name", "ingredient", "country")
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    return f"EMA57:{digest}"


async def import_catalog(path: Path) -> tuple[int, int]:
    from sqlalchemy import select

    from src.pharmaviyum.database import AsyncSessionLocal
    from src.pharmaviyum.models.drug_catalog import (
        DrugReference,
        DrugReferenceIngredient,
        MedicinalProduct,
    )

    rows = parse_ema_xlsx(path)
    added_references = 0
    added_products = 0
    async with AsyncSessionLocal() as session:
        references = (await session.execute(select(DrugReference))).scalars().all()
        reference_ids = {item.inn_name.casefold(): item.id for item in references}
        codes = (await session.execute(select(MedicinalProduct.regulatory_id))).scalars().all()
        existing_codes = {code for code in codes if code}
        ingredient_rows = (
            await session.execute(
                select(
                    DrugReferenceIngredient.drug_reference_id,
                    DrugReferenceIngredient.ingredient_name,
                )
            )
        ).all()
        ingredient_pairs = {
            (reference_id, name.casefold())
            for reference_id, name in ingredient_rows
        }

        for row in rows:
            key = row["ingredient"].casefold()
            reference_id = reference_ids.get(key)
            if reference_id is None:
                reference = DrugReference(inn_name=row["ingredient"], atc_code=None)
                session.add(reference)
                await session.flush()
                reference_id = reference.id
                reference_ids[key] = reference_id
                added_references += 1
            if (reference_id, key) not in ingredient_pairs:
                session.add(DrugReferenceIngredient(
                    drug_reference_id=reference_id,
                    ingredient_name=row["ingredient"],
                ))
                ingredient_pairs.add((reference_id, key))

            code = _regulatory_id(row)
            if code in existing_codes:
                continue
            session.add(MedicinalProduct(
                drug_reference_id=reference_id,
                brand_name=row["product_name"],
                product_type="brand",
                manufacturer=row["holder"] or None,
                strength=row["strength"] or None,
                dosage_form=row["dosage_form"] or None,
                route=row["route"] or None,
                authorization_country=row["country"],
                regulatory_id=code,
            ))
            existing_codes.add(code)
            added_products += 1
        await session.commit()
    return added_references, added_products


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse the EMA file without writing to the database.",
    )
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "article-57.xlsx"
        with httpx.stream(
            "GET",
            EMA_URL,
            timeout=120,
            follow_redirects=True,
            headers={"User-Agent": "Pharmaviyum-European-DrugCatalog/1.0"},
        ) as response:
            response.raise_for_status()
            with path.open("wb") as target:
                for chunk in response.iter_bytes():
                    target.write(chunk)
        if args.dry_run:
            rows = parse_ema_xlsx(path)
            print(
                f"EMA Article 57 dry run: {len(rows)} single-ingredient "
                "country-authorisation records parsed; database unchanged."
            )
            return
        references, products = await import_catalog(path)
    print(
        f"EMA Article 57 import complete: {references} new references, "
        f"{products} new European medicinal products."
    )


if __name__ == "__main__":
    asyncio.run(main())
