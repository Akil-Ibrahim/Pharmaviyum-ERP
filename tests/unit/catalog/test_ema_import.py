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
                f'<c r="{letters}{row_idx}" t="inlineStr">'
                f'<is><t>{escape(value)}</t></is></c>'
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
        '<Relationships '
        'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    )
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def test_parse_ema_article_57_headers_and_single_ingredient(tmp_path: Path) -> None:
    path = tmp_path / "ema.xlsx"
    _xlsx(path, [
        ["Name of medicinal product", "Active substance", "Strength",
         "Pharmaceutical form", "Route of administration",
         "Country where authorised", "Name of marketing authorisation holder"],
        ["ExampleMed", "ibuprofen", "200 mg", "Tablet", "Oral use",
         "Germany", "Example GmbH"],
        ["Combination", "ingredient A; ingredient B", "200 mg + 325 mg",
         "Tablet", "Oral use", "France", "Example SAS"],
    ])
    assert parse_ema_xlsx(path) == [{
        "product_name": "ExampleMed",
        "ingredient": "ibuprofen",
        "strength": "200 mg",
        "dosage_form": "Tablet",
        "route": "Oral use",
        "country": "Germany",
        "holder": "Example GmbH",
    }]


def test_parse_common_alternate_headers(tmp_path: Path) -> None:
    path = tmp_path / "alternate.xlsx"
    _xlsx(path, [
        ["Product name", "Active substance(s)", "Country of authorisation"],
        ["ExampleMed", "ibuprofen", "Germany"],
    ])
    rows = parse_ema_xlsx(path)
    assert len(rows) == 1
    assert rows[0]["product_name"] == "ExampleMed"
    assert rows[0]["country"] == "Germany"
    assert rows[0]["strength"] == ""
    assert rows[0]["dosage_form"] == ""


def test_missing_required_columns_fails_clearly(tmp_path: Path) -> None:
    path = tmp_path / "bad.xlsx"
    _xlsx(path, [["Product", "Substance"], ["X", "Y"]])
    with pytest.raises(ValueError, match="Could not identify"):
        parse_ema_xlsx(path)
