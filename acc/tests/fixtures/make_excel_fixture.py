#!/usr/bin/env python3
"""Build excel_resaved.xlsx — the review workbook AFTER Excel has re-saved it.

Excel does not hand back the file we wrote. It moves every string into a shared
string table (`t="s"` + an index), turns a date the operator retyped into a
serial number, and leaves the ones they did not touch as text. That is the file
`acc batch send` is actually given, so the reader is tested against this shape
rather than against our own writer's output.

Hand-built rather than produced by Excel because no box in this fleet can be
scripted to drive Excel; the XML below is the shape Excel 365 emits (checked
against a real re-save). Rebuild with:

    python3 acc/tests/fixtures/make_excel_fixture.py
"""

from __future__ import annotations

import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKGREL = "http://schemas.openxmlformats.org/package/2006/relationships"

# Every string in the book, in the order Excel would have interned them.
STRINGS = [
    "Row", "GRPO DocEntry", "Approve? (yes/no)", "TDS (yes/no)",
    "Vendor bill date (TaxDate)", "Vendor ref (NumAtCard)",
    "yes", "no", "2606000806", "2026-08-13", "0042/26-27",
    "batch_id", "B240824-OIL-7F3A", "company", "JIVO_OIL_HANADB",
]
IDX = {s: i for i, s in enumerate(STRINGS)}


def s(text):      # a shared-string cell
    return ("s", IDX[text])


def n(value):     # a numeric cell
    return ("n", value)


REVIEW = [
    [s("Row"), s("GRPO DocEntry"), s("Approve? (yes/no)"), s("TDS (yes/no)"),
     s("Vendor bill date (TaxDate)"), s("Vendor ref (NumAtCard)")],
    # row 2: the operator ticked it and retyped the date, so Excel made it a serial
    [n(1), n(25714), s("yes"), s("no"), n(46247), s("2606000806")],
    # row 3: untouched — the date is still the text we wrote
    [n(2), n(25936), s("no"), s("no"), s("2026-08-13"), s("0042/26-27")],
]

ABOUT = [
    [s("batch_id"), s("B240824-OIL-7F3A")],
    [s("company"), s("JIVO_OIL_HANADB")],
]


def col_letter(i):
    letters = ""
    i += 1
    while i:
        i, rem = divmod(i - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def sheet_xml(rows):
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           f'<worksheet xmlns="{MAIN}" xmlns:r="{REL}">',
           '<sheetViews><sheetView tabSelected="1" workbookViewId="0">'
           '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
           "</sheetView></sheetViews>",
           '<sheetFormatPr defaultRowHeight="15"/>', "<sheetData>"]
    for r, row in enumerate(rows, start=1):
        out.append(f'<row r="{r}" spans="1:{len(row)}">')
        for c, (kind, value) in enumerate(row):
            ref = f"{col_letter(c)}{r}"
            if kind == "s":
                out.append(f'<c r="{ref}" s="1" t="s"><v>{value}</v></c>')
            else:
                out.append(f'<c r="{ref}" s="2"><v>{value}</v></c>')
        out.append("</row>")
    out.append("</sheetData>")
    out.append('<sheetProtection sheet="1" objects="1" scenarios="1" sort="0" autoFilter="0"/>')
    out.append("</worksheet>")
    return "".join(out)


def build(path: Path) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/'
                   'vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/'
                   'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/'
                   'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '<Override PartName="/xl/sharedStrings.xml" ContentType="application/'
                   'vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/'
                   'vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   "</Types>")
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   f'<Relationships xmlns="{PKGREL}">'
                   f'<Relationship Id="rId1" Type="{REL}/officeDocument" Target="xl/workbook.xml"/>'
                   "</Relationships>")
        # Excel emits the sheets in workbook order but numbers the relationship
        # ids in its own way, and the sheet parts do NOT have to line up with the
        # sheet order — sheet1.xml here is Review, sheet2.xml is About, but the
        # reader must follow the relationship, not the file name.
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   f'<workbook xmlns="{MAIN}" xmlns:r="{REL}"><sheets>'
                   '<sheet name="Review" sheetId="1" r:id="rId1"/>'
                   '<sheet name="About" sheetId="2" r:id="rId2"/>'
                   "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   f'<Relationships xmlns="{PKGREL}">'
                   f'<Relationship Id="rId1" Type="{REL}/worksheet" Target="worksheets/sheet1.xml"/>'
                   f'<Relationship Id="rId2" Type="{REL}/worksheet" Target="worksheets/sheet2.xml"/>'
                   f'<Relationship Id="rId3" Type="{REL}/styles" Target="styles.xml"/>'
                   f'<Relationship Id="rId4" Type="{REL}/sharedStrings" Target="sharedStrings.xml"/>'
                   "</Relationships>")
        items = "".join(f"<si><t>{t.replace('&', '&amp;').replace('<', '&lt;')}</t></si>"
                        for t in STRINGS)
        z.writestr("xl/sharedStrings.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   f'<sst xmlns="{MAIN}" count="{len(STRINGS)}" uniqueCount="{len(STRINGS)}">'
                   f"{items}</sst>")
        z.writestr("xl/styles.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   f'<styleSheet xmlns="{MAIN}">'
                   '<numFmts count="1"><numFmt numFmtId="164" formatCode="dd\\-mm\\-yyyy"/></numFmts>'
                   '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
                   '<fills count="2"><fill><patternFill patternType="none"/></fill>'
                   '<fill><patternFill patternType="gray125"/></fill></fills>'
                   '<borders count="1"><border/></borders>'
                   '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
                   '<cellXfs count="3">'
                   '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
                   '<xf numFmtId="49" fontId="0" fillId="0" borderId="0" xfId="0"/>'
                   '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0"/>'
                   "</cellXfs></styleSheet>")
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml(REVIEW))
        z.writestr("xl/worksheets/sheet2.xml", sheet_xml(ABOUT))
    return path


if __name__ == "__main__":
    print("wrote", build(HERE / "excel_resaved.xlsx"))
