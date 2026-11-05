"""Tests for parsing the official RxNorm reference archive."""

from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.import_rxnorm_catalog import parse_rxnorm_archive

pytestmark = pytest.mark.unit


def _conso_row(rxcui: str, tty: str, term: str) -> str:
    row = [""] * 18
    row[0] = rxcui
    row[1] = "ENG"
    row[6] = "Y"
    row[11] = "RXNORM"
    row[12] = tty
    row[14] = term
    row[16] = "N"
    return "|".join(row) + "|\n"


def _rel_row(product_id: str, ingredient_id: str) -> str:
    row = [""] * 16
    row[0] = product_id
    row[3] = "RO"
    row[4] = ingredient_id
    row[7] = "has_ingredient"
    return "|".join(row) + "|\n"


def test_parser_keeps_single_ingredient_products_and_skips_combinations(tmp_path: Path):
    archive_path = tmp_path / "rxnorm.zip"
    conso = "".join(
        [
            _conso_row("100", "IN", "ibuprofen"),
            _conso_row("200", "SCD", "ibuprofen 200 MG Oral Tablet"),
            _conso_row("201", "SBD", "Advil 200 MG Oral Tablet"),
            _conso_row("202", "SBD", "Teva 200 MG Oral Tablet"),
            _conso_row("300", "IN", "acetaminophen"),
            _conso_row("301", "SCD", "acetaminophen 160 MG/5 ML Oral Suspension"),
            _conso_row(
                "400",
                "SCD",
                "ibuprofen 200 MG / acetaminophen 325 MG Oral Tablet",
            ),
        ]
    )
    rel = "".join(
        [
            _rel_row("200", "100"),
            _rel_row("201", "100"),
            _rel_row("202", "100"),
            _rel_row("301", "300"),
            _rel_row("400", "100"),
            _rel_row("400", "300"),
        ]
    )
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("rrf/RXNCONSO.RRF", conso)
        archive.writestr("rrf/RXNREL.RRF", rel)

    ingredients, products = parse_rxnorm_archive(archive_path)

    assert ingredients == {"100": "ibuprofen", "300": "acetaminophen"}
    assert {product["rxcui"] for product in products} == {"200", "201", "202", "301"}
    generic = next(product for product in products if product["rxcui"] == "200")
    brand = next(product for product in products if product["rxcui"] == "201")
    teva_brand = next(product for product in products if product["rxcui"] == "202")
    assert generic["strength"] == "200 MG"
    assert generic["dosage_form"] == "Oral Tablet"
    assert generic["ingredient_id"] == "100"
    assert brand["tty"] == "SBD"
    assert brand["brand_name"] == "Advil"
    assert teva_brand["brand_name"] == "Teva"
    liquid = next(product for product in products if product["rxcui"] == "301")
    assert liquid["strength"] == "160 MG/5 ML"
    assert liquid["dosage_form"] == "Oral Suspension"
