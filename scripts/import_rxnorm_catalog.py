"""Import NLM RxNorm Current Prescribable Content into the drug reference tables.

Run after database migrations:
    uv run python scripts/import_rxnorm_catalog.py

The importer intentionally excludes multi-ingredient clinical products because the
current schema links a medicinal product to one canonical drug reference only.
It never creates sellable POS inventory, prices, batches, or expiry dates.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import httpx

RXNORM_URL = (
    "https://download.nlm.nih.gov/umls/kss/rxnorm/"
    "RxNorm_full_prescribe_current.zip"
)
PRODUCT_TERMS = {"SCD", "SBD"}
INGREDIENT_TERMS = {"IN", "PIN"}
INGREDIENT_RELATIONS = {"has_ingredient", "has_precise_ingredient"}
STRENGTH_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:MG|MCG|G|ML|%|UNIT)"
    r"(?:\s*/\s*\d+(?:\.\d+)?\s*(?:MG|MCG|G|ML|%|UNIT))?\b",
    re.I,
)
ROUTE_TERMS = {
    "oral",
    "topical",
    "intravenous",
    "intramuscular",
    "subcutaneous",
    "ophthalmic",
    "otic",
    "nasal",
    "inhalation",
    "rectal",
    "vaginal",
    "transdermal",
    "buccal",
    "sublingual",
}


def _rrf_rows(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield line.rstrip("\n").split("|")


def parse_rxnorm_archive(
    archive_path: Path,
) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Return canonical ingredient names and single-ingredient clinical products."""
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        conso_name = next(
            (name for name in names if name.endswith("RXNCONSO.RRF")), None
        )
        rel_name = next(
            (name for name in names if name.endswith("RXNREL.RRF")), None
        )
        if not conso_name or not rel_name:
            raise ValueError("RxNorm archive is missing RXNCONSO.RRF or RXNREL.RRF")

        with tempfile.TemporaryDirectory() as temp_dir:
            conso_path = Path(temp_dir) / "RXNCONSO.RRF"
            rel_path = Path(temp_dir) / "RXNREL.RRF"
            with archive.open(conso_name) as source, conso_path.open("wb") as target:
                shutil.copyfileobj(source, target)
            with archive.open(rel_name) as source, rel_path.open("wb") as target:
                shutil.copyfileobj(source, target)
            concepts: dict[str, tuple[str, str]] = {}

            for row in _rrf_rows(conso_path):
                if (
                    len(row) < 17
                    or row[11] != "RXNORM"
                    or row[16] not in {"", "N"}
                ):
                    continue
                rxcui, tty, term = row[0], row[12], row[14]
                if tty in INGREDIENT_TERMS | PRODUCT_TERMS and term:
                    # Keep the preferred English name when duplicate atoms exist.
                    if row[1] == "ENG" and (
                        rxcui not in concepts or row[6] == "Y"
                    ):
                        concepts[rxcui] = (tty, term)

            ingredients = {
                rxcui: term
                for rxcui, (tty, term) in concepts.items()
                if tty in INGREDIENT_TERMS
            }
            product_ingredients: dict[str, set[str]] = {}

            for row in _rrf_rows(rel_path):
                if len(row) < 8 or row[7] not in INGREDIENT_RELATIONS:
                    continue
                left, right = row[0], row[4]
                if (
                    left in concepts
                    and concepts[left][0] in PRODUCT_TERMS
                    and right in ingredients
                ):
                    product_ingredients.setdefault(left, set()).add(right)
                elif (
                    right in concepts
                    and concepts[right][0] in PRODUCT_TERMS
                    and left in ingredients
                ):
                    product_ingredients.setdefault(right, set()).add(left)

            products: list[dict[str, str]] = []
            for rxcui, (tty, term) in concepts.items():
                linked = product_ingredients.get(rxcui, set())
                # Do not silently misrepresent combination medicines.
                if tty not in PRODUCT_TERMS or len(linked) != 1:
                    continue

                ingredient_id = next(iter(linked))
                strength_match = STRENGTH_RE.search(term)
                words = term.split()
                route = next(
                    (word.lower() for word in words if word.lower() in ROUTE_TERMS),
                    "",
                )
                brand_name = ""
                if tty == "SBD":
                    brand_name = (
                        term[: strength_match.start()].strip()
                        if strength_match
                        else term
                    )
                dosage_form = (
                    term[strength_match.end() :].strip()
                    if strength_match
                    else term
                )
                products.append(
                    {
                        "rxcui": rxcui,
                        "term": term,
                        "brand_name": brand_name,
                        "tty": tty,
                        "ingredient_id": ingredient_id,
                        "strength": (
                            strength_match.group(0) if strength_match else ""
                        ),
                        "route": route,
                        "dosage_form": dosage_form,
                    }
                )

            return ingredients, products


def _archive_version(path: Path) -> str:
    """Use the exact source archive checksum as an immutable import version."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


async def import_catalog(path: Path) -> tuple[int, int]:
    """Stage RxNorm records for review; do not mutate the approved drug catalog."""
    from datetime import datetime
    from sqlalchemy import select

    from src.pharmaviyum.database import AsyncSessionLocal
    from src.pharmaviyum.models.drug_catalog import DrugCatalogSourceRecord

    ingredient_terms, products = parse_rxnorm_archive(path)
    version = _archive_version(path)
    records = [
        DrugCatalogSourceRecord(
            source_name="RxNorm",
            source_record_id=product["rxcui"],
            source_version=version,
            source_url=RXNORM_URL,
            license_terms=(
                "NLM RxNorm; review current UMLS/RxNorm terms before redistribution."
            ),
            extracted_at=datetime.utcnow(),
            normalized_payload={
                **product,
                "ingredient_name": ingredient_terms[product["ingredient_id"]],
            },
        )
        for product in products
    ]
    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(
                select(DrugCatalogSourceRecord.source_record_id).where(
                    DrugCatalogSourceRecord.source_name == "RxNorm",
                    DrugCatalogSourceRecord.source_version == version,
                )
            )
        ).scalars().all()
        existing_ids = set(existing)
        staged = 0
        for record in records:
            if record.source_record_id in existing_ids:
                continue
            session.add(record)
            existing_ids.add(record.source_record_id)
            staged += 1
        await session.commit()
    return staged, len(records) - staged


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download and validate the archive without writing to the database.",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / "rxnorm.zip"
        headers = {"User-Agent": "Pharmaviyum-DrugCatalog/1.0"}
        with httpx.stream(
            "GET",
            RXNORM_URL,
            headers=headers,
            timeout=120,
            follow_redirects=True,
        ) as response:
            response.raise_for_status()
            with archive_path.open("wb") as archive_file:
                for chunk in response.iter_bytes():
                    archive_file.write(chunk)

        if args.dry_run:
            references, products = parse_rxnorm_archive(archive_path)
            print(
                f"RxNorm dry run: {len(references)} ingredient concepts and "
                f"{len(products)} single-ingredient products parsed; "
                "database unchanged."
            )
            return

        references_added, products_added = await import_catalog(archive_path)

    print(
        f"RxNorm staging complete: {references_added} source records added, "
        f"{products_added} already present for this archive version. "
        "All new records remain pending review; the approved catalog is unchanged."
    )

if __name__ == "__main__":
    asyncio.run(main())
