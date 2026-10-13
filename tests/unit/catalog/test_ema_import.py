from pathlib import Path
from zipfile import ZipFile
from xml.sax.saxutils import escape

import pytest

from scripts.import_ema_catalog import parse_ema_xlsx


def _xlsx(path: Path, rows: list[list[str]]) -> None:
    sheet_rows = []
    for row_idx, values in enumerate(rows, start=1):
        cells = []
        for col_idx, value in enumerate(values):
            n = col_idx + 1
            letters = ""
            while n:
                n, remainder = divmod(n - 1, 26)
                letters = chr(65 + remainder) + letters
            cells.append(
                f'<c r="{letters}{row_idx}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
            )
        sheet_rows.append(f'<row r="{row_idx}">{"".join(cells)}</row>')
    sheet = (
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    )
    workbook = (
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels = (
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/></Relationships>'
    )
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def test_parse_ema_single_ingredient_and_country(tmp_path: Path) -> None:
    path = tmp_path / "ema.xlsx"
    _xlsx(path, [
        ["Product name", "Active substance", "Route of administration",
         "Country of authorisation", "Name of marketing authorisation holder"],
        ["ExampleMed", "ibuprofen", "Oral use", "Germany", "Example GmbH"],
        ["Combination", "ingredient A; ingredient B", "Oral use", "France", "Example SAS"],
    ])
    assert parse_ema_xlsx(path) == [{
        "product_name": "ExampleMed",
        "ingredient": "ibuprofen",
        "route": "Oral use",
        "country": "Germany",
        "holder": "Example GmbH",
    }]


def test_missing_required_columns_fails_clearly(tmp_path: Path) -> None:
    path = tmp_path / "bad.xlsx"
    _xlsx(path, [["Product", "Substance"], ["X", "Y"]])
    with pytest.raises(ValueError, match="Could not identify"):
        parse_ema_xlsx(path)
