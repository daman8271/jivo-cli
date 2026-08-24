"""xlsx — a review workbook, written and read with nothing but the standard library.

Why not openpyxl: it is not installed on the operator boxes, and pip/winget on
those machines is unreliable enough that a missing wheel would be the reason
Accounts could not review a batch. Why not CSV: Excel mangles a vendor reference
with a leading zero, reformats a typed date into whatever the locale prefers, and
has nowhere to put "only these cells are yours to edit".

So: zipfile + a few hundred lines of OOXML. Enough of the format for two fills,
column widths, a frozen header, a yes/no dropdown, text-format cells, an Indian
number format and sheet protection with the editable cells unlocked.

The reader is the more important half. It has to accept what EXCEL writes back,
which is not what we wrote: Excel re-saves with a shared string table, turns a
date the operator retyped into a serial number, and re-orders parts. Both forms
are handled, and `rules.parse_sheet_date` finishes the job for date columns.
"""

from __future__ import annotations

import datetime as dt
import re
import zipfile
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from xml.etree import ElementTree as ET

from . import rules

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKGREL = "http://schemas.openxmlformats.org/package/2006/relationships"

# Indian grouping, as a real number format so the cells stay numeric and still
# add up in Excel: crores, lakhs, then thousands.
INR_FORMAT = "[&gt;=10000000]##\\,##\\,##\\,##0.00;[&gt;=100000]##\\,##\\,##0.00;##,##0.00"
QTY_FORMAT = "#,##0.###"

YELLOW = "FFFFF2CC"        # editable — yours to type in
GREY = "FFEDEDED"          # header
GREY_DATA = "FFF5F5F5"     # locked data: the About sheet promises grey means locked

# Style indexes into the cellXfs list built by _styles_xml(). Order matters —
# these are positions, not names, once the file is written.
S_DEFAULT, S_HEADER, S_TEXT, S_INR, S_QTY, S_EDIT, S_EDIT_LIST = range(7)
STYLE_BY_NAME = {"text": S_TEXT, "inr": S_INR, "qty": S_QTY,
                 "editable": S_EDIT, "list": S_EDIT_LIST, "header": S_HEADER}


@dataclass
class SheetSpec:
    name: str
    headers: Sequence[str]
    rows: Sequence[Sequence[Any]] = field(default_factory=list)
    widths: Sequence[int] | None = None
    freeze_header: bool = True
    protect: bool = True
    # column index -> "inr" | "qty" | "text"; anything unnamed is plain locked
    styles: Mapping[int, str] = field(default_factory=dict)
    # column indexes the operator may edit: unlocked, yellow, text-formatted
    editable: Iterable[int] = field(default_factory=frozenset)
    # column index -> the values a dropdown offers
    validations: Mapping[int, Sequence[str]] = field(default_factory=dict)
    # Which ROWS the editable columns are actually editable on, as 0-based
    # indexes into `rows`. None means all of them.
    #
    # This exists because "editable" is a property of a cell, not of a column: a
    # DUPLICATE row's Approve? cell must not be typeable at all. `send` refuses
    # such a row anyway (REFUSED-STATUS), but a yellow box on a row that can
    # never be sent invites an operator to fill fifty of them and then be told
    # no fifty times.
    editable_rows: Iterable[int] | None = None


# --------------------------------------------------------------------------
# cell addressing
# --------------------------------------------------------------------------

def column_letter(index: int) -> str:
    """0 -> A, 25 -> Z, 26 -> AA."""
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def column_index(letters: str) -> int:
    n = 0
    for ch in letters.upper():
        if not ch.isalpha():
            break
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def cell_ref(col: int, row: int) -> str:
    """Column index (0-based) + sheet row number (1-based) -> 'V2'."""
    return f"{column_letter(col)}{row}"


def split_ref(ref: str) -> tuple[int, int]:
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    if not m:
        raise ValueError(f"not a cell reference: {ref!r}")
    return column_index(m.group(1)), int(m.group(2))


_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def same_cell(a: Any, b: Any) -> bool:
    """Is what the sheet came back with the same value we put in it?

    Excel changes representation freely — 214500 becomes 214500.00, a string
    grows a space, a blank becomes None, and a date column typed as text comes
    back as the serial 46248. None of that is tampering; a different number or a
    different word is. This decides whether a row is refused as TAMPERED, so a
    false positive here is an operator told their file was meddled with when
    Excel simply saved it.

    Numbers compare as Decimals rounded to 2 dp. A date compares as a date
    whichever side arrived as a serial. Nothing in here may raise: NaN and
    Infinity are compared as the words they are.
    """
    if a is None:
        a = ""
    if b is None:
        b = ""
    dated = _same_date(a, b)
    if dated is not None:
        return dated
    da, db = _decimal(a), _decimal(b)
    if da is not None and db is not None:
        return round(da, 2) == round(db, 2)
    if (da is None) != (db is None):
        return False                       # one is a number, the other is a word
    return str(a).strip() == str(b).strip()


def _same_date(a: Any, b: Any) -> bool | None:
    """True/False when one side is an ISO date and the other a serial; else None.

    Only that mixed pair is handled here. Two ISO strings are already equal as
    text, and two serials are already equal as numbers.
    """
    for text, other in ((a, b), (b, a)):
        if isinstance(text, str) and _ISO_DATE.fullmatch(text.strip()) \
                and isinstance(other, (int, float, Decimal)) and not isinstance(other, bool):
            try:
                return rules.parse_sheet_date(text) == rules.parse_sheet_date(other)
            except ValueError:
                return False
    return None


def _decimal(v: Any) -> Decimal | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float, Decimal)):
        try:
            d = Decimal(str(v))
        except InvalidOperation:
            return None
        return d if d.is_finite() else None
    text = str(v).strip()
    if not text:
        return None
    try:
        d = Decimal(text)
    except InvalidOperation:
        return None
    # Decimal("inf") and Decimal("nan") parse happily and then blow up in
    # round(). A cell holding "inf" is a word, not a quantity — compare it as one.
    return d if d.is_finite() else None


# --------------------------------------------------------------------------
# writing
# --------------------------------------------------------------------------

def write_workbook(path: Path | str, sheets: Sequence[SheetSpec]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _content_types(len(sheets)))
        z.writestr("_rels/.rels", _root_rels())
        z.writestr("xl/workbook.xml", _workbook_xml(sheets))
        z.writestr("xl/_rels/workbook.xml.rels", _workbook_rels(len(sheets)))
        z.writestr("xl/styles.xml", _styles_xml())
        for i, spec in enumerate(sheets, start=1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", _sheet_xml(spec))
    return path


# Control characters XML 1.0 has no representation for. SAP text fields carry
# them (a vendor name pasted out of a PDF, a Comments field with a stray \x01),
# and Excel refuses to open a workbook that contains one — the whole batch is
# unreadable because of one byte in one cell.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


def clean_text(value: Any) -> Any:
    """What _esc will keep, applied before a value is ALSO written to the sidecar.

    The tamper check compares the sheet against the sidecar cell by cell, so the
    two have to be cleaned in the same place. Cleaning only on the way into the
    XML would make any row with a control character permanently TAMPERED.
    """
    return _CONTROL_CHARS.sub("", value) if isinstance(value, str) else value


def _esc(text: str) -> str:
    text = _CONTROL_CHARS.sub("", str(text))
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _content_types(n: int) -> str:
    sheets = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/'
        'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, n + 1))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            f"{sheets}</Types>")


def _root_rels() -> str:
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{PKGREL}">'
            f'<Relationship Id="rId1" Type="{REL}/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>")


def _workbook_xml(sheets: Sequence[SheetSpec]) -> str:
    tabs = "".join(f'<sheet name="{_esc(s.name)}" sheetId="{i}" r:id="rId{i}"/>'
                   for i, s in enumerate(sheets, start=1))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<workbook xmlns="{MAIN}" xmlns:r="{REL}">'
            f"<sheets>{tabs}</sheets></workbook>")


def _workbook_rels(n: int) -> str:
    rels = "".join(f'<Relationship Id="rId{i}" Type="{REL}/worksheet" '
                   f'Target="worksheets/sheet{i}.xml"/>' for i in range(1, n + 1))
    styles = f'<Relationship Id="rId{n + 1}" Type="{REL}/styles" Target="styles.xml"/>'
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{PKGREL}">{rels}{styles}</Relationships>')


def _styles_xml() -> str:
    """Seven cell formats, in the order S_DEFAULT..S_EDIT_LIST.

    Everything is locked by default and the sheet is protected, so "locked" only
    bites on the cells we deliberately leave unlocked — the yellow ones.
    """
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<styleSheet xmlns="{MAIN}">'
        '<numFmts count="2">'
        f'<numFmt numFmtId="164" formatCode="{INR_FORMAT}"/>'
        f'<numFmt numFmtId="165" formatCode="{QTY_FORMAT}"/>'
        "</numFmts>"
        '<fonts count="2">'
        '<font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><name val="Calibri"/></font>'
        "</fonts>"
        '<fills count="5">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        f'<fill><patternFill patternType="solid"><fgColor rgb="{GREY}"/>'
        '<bgColor indexed="64"/></patternFill></fill>'
        f'<fill><patternFill patternType="solid"><fgColor rgb="{YELLOW}"/>'
        '<bgColor indexed="64"/></patternFill></fill>'
        f'<fill><patternFill patternType="solid"><fgColor rgb="{GREY_DATA}"/>'
        '<bgColor indexed="64"/></patternFill></fill>'
        "</fills>"
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="7">'
        # 0 default — locked, and GREY, because the About sheet tells the operator
        #   "everything grey is checked against SAP again"; a white locked cell
        #   invites the edit that makes the row refuse to send.
        '<xf numFmtId="0" fontId="0" fillId="4" borderId="0" xfId="0" applyFill="1" '
        'applyProtection="1"><protection locked="1"/></xf>'
        # 1 header
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" '
        'applyFill="1" applyAlignment="1" applyProtection="1">'
        '<alignment vertical="center" wrapText="1"/><protection locked="1"/></xf>'
        # 2 locked text
        '<xf numFmtId="49" fontId="0" fillId="4" borderId="0" xfId="0" applyNumberFormat="1" '
        'applyFill="1" applyProtection="1"><protection locked="1"/></xf>'
        # 3 locked money
        '<xf numFmtId="164" fontId="0" fillId="4" borderId="0" xfId="0" applyNumberFormat="1" '
        'applyFill="1" applyProtection="1"><protection locked="1"/></xf>'
        # 4 locked quantity
        '<xf numFmtId="165" fontId="0" fillId="4" borderId="0" xfId="0" applyNumberFormat="1" '
        'applyFill="1" applyProtection="1"><protection locked="1"/></xf>'
        # 5 editable text
        '<xf numFmtId="49" fontId="0" fillId="3" borderId="0" xfId="0" applyNumberFormat="1" '
        'applyFill="1" applyProtection="1"><protection locked="0"/></xf>'
        # 6 editable with a dropdown
        '<xf numFmtId="49" fontId="0" fillId="3" borderId="0" xfId="0" applyNumberFormat="1" '
        'applyFill="1" applyProtection="1"><protection locked="0"/></xf>'
        "</cellXfs>"
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        "</styleSheet>")


def _sheet_xml(spec: SheetSpec) -> str:
    editable = set(spec.editable or ())
    width = max([len(spec.headers)] + [len(r) for r in spec.rows] or [1])
    last = cell_ref(max(width - 1, 0), len(spec.rows) + 1)

    parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             f'<worksheet xmlns="{MAIN}">',
             f'<dimension ref="A1:{last}"/>']

    pane = ('<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
            if spec.freeze_header else "")
    parts.append(f'<sheetViews><sheetView workbookViewId="0">{pane}</sheetView></sheetViews>')
    parts.append('<sheetFormatPr defaultRowHeight="15"/>')

    if spec.widths:
        cols = "".join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>'
                       for i, w in enumerate(spec.widths, start=1))
        parts.append(f"<cols>{cols}</cols>")

    parts.append("<sheetData>")
    parts.append(_row_xml(1, spec.headers, lambda _c: S_HEADER))

    editable_rows = None if spec.editable_rows is None else set(spec.editable_rows)

    def style_for(index: int, col: int) -> int:
        if col in editable and (editable_rows is None or index in editable_rows):
            return S_EDIT_LIST if col in (spec.validations or {}) else S_EDIT
        if col in editable:
            return S_TEXT                  # locked, grey, still text-formatted
        return STYLE_BY_NAME.get((spec.styles or {}).get(col, ""), S_DEFAULT)

    for index, row in enumerate(spec.rows):
        parts.append(_row_xml(index + 2, row,
                              lambda col, _i=index: style_for(_i, col)))
    parts.append("</sheetData>")

    if spec.protect:
        # sheet="1" turns protection on; sort/autoFilter="0" leave those allowed,
        # because a reviewer sorting 50 rows is normal and harmless — the sidecar
        # is keyed by GRPO DocEntry, not by row order.
        parts.append('<sheetProtection sheet="1" objects="1" scenarios="1" '
                     'sort="0" autoFilter="0" selectLockedCells="0" selectUnlockedCells="0"/>')

    if spec.validations and spec.rows:
        items = []
        for col, values in spec.validations.items():
            first = cell_ref(col, 2)
            final = cell_ref(col, len(spec.rows) + 1)
            allowed = ",".join(str(v) for v in values)
            items.append(f'<dataValidation type="list" allowBlank="1" showInputMessage="1" '
                         f'showErrorMessage="1" sqref="{first}:{final}">'
                         f'<formula1>"{_esc(allowed)}"</formula1></dataValidation>')
        parts.append(f'<dataValidations count="{len(items)}">' + "".join(items) +
                     "</dataValidations>")

    parts.append("</worksheet>")
    return "".join(parts)


def _row_xml(number: int, values: Sequence[Any], style_for) -> str:
    cells = []
    for col, value in enumerate(values):
        ref = cell_ref(col, number)
        style = style_for(col)
        if value is None or value == "":
            # A blank cell still has to EXIST when its column is styled. Skipping
            # it leaves Excel with no style for that address, which means the
            # default — locked — and an operator who cannot type "yes" into an
            # empty Approve? cell on a protected sheet.
            if style != S_DEFAULT:
                cells.append(f'<c r="{ref}" s="{style}"/>')
            continue
        if isinstance(value, bool):
            value = str(value)
        if isinstance(value, (int, float, Decimal)):
            cells.append(f'<c r="{ref}" s="{style}"><v>{value}</v></c>')
        else:
            cells.append(f'<c r="{ref}" s="{style}" t="inlineStr">'
                         f"<is><t xml:space=\"preserve\">{_esc(value)}</t></is></c>")
    return f'<row r="{number}">' + "".join(cells) + "</row>"


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

def read_workbook(path: Path | str) -> dict[str, list[list[Any]]]:
    """{sheet name: rows}, rows padded to a rectangle, blanks as ''.

    Values come back as int, float or str. Dates are NOT converted: Excel gives
    a date back as a serial number and there is no way to tell one from a plain
    number without reading the style, so the caller decides which columns are
    dates and runs them through rules.parse_sheet_date.
    """
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared = _shared_strings(z) if "xl/sharedStrings.xml" in names else []
        targets = _sheet_targets(z)
        out: dict[str, list[list[Any]]] = {}
        for name, target in targets:
            part = target if target in names else "xl/" + target.lstrip("/")
            if part not in names:
                continue
            out[name] = _sheet_rows(z.read(part), shared)
    return out


def _shared_strings(z: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    out = []
    for si in root.findall(f"{{{MAIN}}}si"):
        out.append("".join(t.text or "" for t in si.iter(f"{{{MAIN}}}t")))
    return out


def _sheet_targets(z: zipfile.ZipFile) -> list[tuple[str, str]]:
    """Sheet names in workbook order, paired with the part each one lives in."""
    rels = {}
    if "xl/_rels/workbook.xml.rels" in z.namelist():
        root = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        for rel in root:
            rels[rel.get("Id")] = rel.get("Target")
    root = ET.fromstring(z.read("xl/workbook.xml"))
    out = []
    for i, sheet in enumerate(root.iter(f"{{{MAIN}}}sheet"), start=1):
        rid = sheet.get(f"{{{REL}}}id")
        target = rels.get(rid) or f"worksheets/sheet{i}.xml"
        if target.startswith("/"):
            target = target[1:]
        elif not target.startswith("xl/"):
            target = "xl/" + target
        out.append((sheet.get("name"), target))
    return out


def _sheet_rows(data: bytes, shared: Sequence[str]) -> list[list[Any]]:
    root = ET.fromstring(data)
    rows: dict[int, dict[int, Any]] = {}
    widest = 0
    for row in root.iter(f"{{{MAIN}}}row"):
        number = int(row.get("r") or (max(rows) + 2 if rows else 1))
        cells = rows.setdefault(number, {})
        for n, cell in enumerate(row.findall(f"{{{MAIN}}}c")):
            ref = cell.get("r")
            col = split_ref(ref)[0] if ref else n
            cells[col] = _cell_value(cell, shared)
            widest = max(widest, col + 1)
    if not rows:
        return []
    return [[rows.get(n, {}).get(c, "") for c in range(widest)]
            for n in range(1, max(rows) + 1)]


def _cell_value(cell: ET.Element, shared: Sequence[str]) -> Any:
    kind = cell.get("t")
    if kind == "inlineStr":
        node = cell.find(f"{{{MAIN}}}is")
        return "".join(t.text or "" for t in node.iter(f"{{{MAIN}}}t")) if node is not None else ""
    value = cell.find(f"{{{MAIN}}}v")
    text = value.text if value is not None else None
    if text is None:
        return ""
    if kind == "s":                                   # shared string
        idx = int(text)
        return shared[idx] if 0 <= idx < len(shared) else ""
    if kind in ("str", "e"):                          # formula result / error
        return text
    if kind == "b":
        return text == "1"
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text
