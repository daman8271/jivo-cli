#!/usr/bin/env python3
"""check.py - production RM sheet vs live SAP loose-oil stock.

Give it the shift-wise RM sheet (the one with Date / Shift / RM code / oil name /
quantity). It pulls the live stock for those RM codes out of SAP HANA, writes an
Excel workbook with the SAP numbers alongside each line, and prints what is
short.

The catch it exists for: one RM code can appear on several lines of the sheet
(RM0000001 is keyed three times - EL, EV, POM). Every line can look covered
while the code as a whole is short, so the shortage is decided on the CODE
TOTAL, not the line.

Read-only by construction. Everything goes through the `hana-sql` CLI, which
refuses anything but SELECT/WITH and runs inside a HANA read-only transaction,
so this honours CLAUDE.md RULE 0.

Usage:
    python3 check.py sheet.xlsx                  # -> out/rm-stock-<date>.xlsx
    python3 check.py paste.txt                   # pasted rows, any spacing
    python3 check.py -                           # rows on stdin
    python3 check.py sheet.xlsx --warehouse BH-LO --company oil
    python3 check.py sheet.xlsx --all-warehouses # every godown, not just BH-LO
    python3 check.py sheet.xlsx -o my-name.xlsx
"""
import argparse
import csv as _csv
import datetime
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "out")

SCHEMAS = {
    "oil": "JIVO_OIL_HANADB",
    "mart": "JIVO_MART_HANADB",
    "bev": "JIVO_BEVERAGES_HANADB",
}
COMPANY_NAME = {"oil": "JIVO Oil", "mart": "JIVO Mart", "bev": "JIVO Beverages"}

# Loose oil godown at Bhakharpur - where the RM the shift draws on actually sits.
DEFAULT_WHS = "BH-LO"

ITEM_RE = re.compile(r"\b(RM\d{5,9})\b", re.I)
NUM_RE = re.compile(r"^-?[\d,]*\.?\d+$")
SHIFT_RE = re.compile(r"shift\s*[-_]?\s*(\w+)", re.I)
DATE_RE = re.compile(r"^(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})$")

# ------------------------------------------------------------------ hana-sql


def hana_bin():
    for name in ("hana-sql.exe", "hana-sql"):
        p = os.path.join(REPO, "hana-sql", name)
        if os.path.exists(p):
            return p
    sys.exit("hana-sql not found under %s/hana-sql" % REPO)


def query(sql):
    """Run one read-only statement, return a list of dicts.

    -env is passed explicitly and cwd is pinned to the repo: hana-sql otherwise
    searches upward from the working directory for connections/hana.env, which
    finds nothing when this is run from somewhere else.
    """
    cmd = [hana_bin(), "-csv"]
    env_file = os.path.join(REPO, "connections", "hana.env")
    if os.path.exists(env_file):
        cmd += ["-env", env_file]
    out = subprocess.run(cmd + [sql], capture_output=True, text=True, cwd=REPO)
    if out.returncode != 0 or out.stdout.startswith("QUERY ERROR"):
        sys.stderr.write((out.stdout or "") + (out.stderr or ""))
        sys.exit("hana-sql failed - check connections/hana.env and the VPN/route")
    return list(_csv.DictReader(io.StringIO(out.stdout)))


def sql_list(codes):
    return ", ".join("'%s'" % c.replace("'", "''") for c in codes)


# ------------------------------------------------------------------ the sheet


def num(v):
    """A number out of a cell, or None. Handles '25,000', '25000.00', 25000."""
    if v is None:
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    s = str(v).strip().replace(" ", " ")
    if not s or not NUM_RE.match(s):
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def cell_date(v):
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.strftime("%Y-%m-%d")
    s = str(v or "").strip()
    m = DATE_RE.match(s)
    if not m:
        return ""
    d, mo, y = (int(x) for x in m.groups())
    if y < 100:
        y += 2000
    try:
        return datetime.date(y, mo, d).strftime("%Y-%m-%d")
    except ValueError:
        return ""


def read_rows(path):
    """Rows of cells out of xlsx / csv / tsv / a plain paste / stdin."""
    if path == "-":
        return [re.split(r"\t|\s{2,}", ln.rstrip("\n")) for ln in sys.stdin if ln.strip()]
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm", ".xltx"):
        import openpyxl

        wb = openpyxl.load_workbook(path, data_only=True)
        rows = []
        for ws in wb.worksheets:
            for r in ws.iter_rows(values_only=True):
                rows.append(list(r))
        return rows
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        text = fh.read()
    if ext == ".csv":
        return [r for r in _csv.reader(io.StringIO(text))]
    # tsv, or a paste where columns are separated by tabs or runs of spaces
    return [re.split(r"\t|\s{2,}", ln.rstrip("\n")) for ln in text.splitlines() if ln.strip()]


def parse_sheet(rows):
    """Pick the RM lines out of whatever shape the sheet is in.

    Positional-agnostic on purpose: the sheet gets re-cut (columns hidden, a
    serial number added, headers reworded) and the entry sheet is a dropdown
    grid, not a clean table. So per row: find the RM code, take the text after
    it as the name, and the numbers after that as the quantities, in order.
    Which of those numbers is the factory requirement is decided later
    (--req-col), because the sheet carries two: the indent (yellow) and the
    Fac Req next to it.
    """
    out = []
    for i, row in enumerate(rows, 1):
        cells = ["" if c is None else c for c in row]
        code = None
        at = None
        for j, c in enumerate(cells):
            m = ITEM_RE.search(str(c))
            if m:
                code, at = m.group(1).upper(), j
                break
        if code is None:
            continue
        date = ""
        date_raw = ""
        shift = ""
        for c in cells[:at]:
            if not date:
                date = cell_date(c)
                if date:
                    # keep it exactly as keyed (01.09.2026) - this is what goes
                    # in the transfer request's Comments, not the ISO form
                    date_raw = (
                        c.strftime("%d.%m.%Y")
                        if isinstance(c, (datetime.datetime, datetime.date))
                        else str(c).strip()
                    )
            ms = SHIFT_RE.search(str(c))
            if ms and not shift:
                shift = str(c).strip()
        name = ""
        qtys = []
        for c in cells[at + 1 :]:
            n = num(c)
            if n is not None:
                qtys.append(n)
            elif str(c).strip() and not name and not qtys:
                name = str(c).strip()
        if not qtys:
            sys.stderr.write("row %d: %s has no quantity - skipped\n" % (i, code))
            continue
        out.append(
            {
                "row": i,
                "date": date,
                "shift": shift,
                "code": code,
                "name": name,
                "date_raw": date_raw,
                "qtys": qtys,
            }
        )
    return out


def pick_req(lines, req_col):
    """Set ln['req'] (Fac Req) and ln['extra'] from the numbers on each line.

    The sheet has two number columns: the indent (yellow) and the Fac Req
    beside it. Lovepreet works off the SECOND one, so that is the default; a
    line carrying only one number falls back to it.
    """
    for ln in lines:
        qtys = ln["qtys"]
        i = min(req_col - 1, len(qtys) - 1)
        ln["req"] = qtys[i]
        ln["extra"] = [q for j, q in enumerate(qtys) if j != i]
        ln["req_col"] = i + 1
    return lines


# ------------------------------------------------------------------ SAP stock


def sap_stock(codes, schema, whs, all_whs):
    """{code: {sap_name, uom, onhand, committed, onorder, by_whs}} for `whs`."""
    if not codes:
        return {}
    where = "T1.\"ItemCode\" IN (%s)" % sql_list(codes)
    rows = query(
        'SELECT T1."ItemCode" AS CODE, T0."ItemName" AS NAME, T0."InvntryUom" AS UOM,'
        ' T1."WhsCode" AS WHS,'
        ' CAST(T1."OnHand" AS DOUBLE) AS ONHAND,'
        ' CAST(T1."IsCommited" AS DOUBLE) AS COMMITTED,'
        ' CAST(T1."OnOrder" AS DOUBLE) AS ONORDER'
        " FROM %s.OITW T1 JOIN %s.OITM T0 ON T0.\"ItemCode\" = T1.\"ItemCode\""
        " WHERE %s ORDER BY T1.\"ItemCode\", T1.\"WhsCode\"" % (schema, schema, where)
    )
    stock = {}
    for r in rows:
        code = r["CODE"]
        s = stock.setdefault(
            code,
            {
                "sap_name": r["NAME"],
                "uom": r["UOM"] or "",
                "onhand": 0.0,
                "committed": 0.0,
                "onorder": 0.0,
                "by_whs": {},
            },
        )
        oh = float(r["ONHAND"] or 0)
        cm = float(r["COMMITTED"] or 0)
        oo = float(r["ONORDER"] or 0)
        if oh:
            s["by_whs"][r["WHS"]] = oh
        if all_whs or r["WHS"] == whs:
            s["onhand"] += oh
            s["committed"] += cm
            s["onorder"] += oo
    return stock


# ------------------------------------------------------------------ the answer


def fmt(n, dp=2):
    if n is None:
        return ""
    return "{:,.{dp}f}".format(n, dp=dp)


def build(lines, stock, args):
    """Per-line detail + per-code roll-up. Shortage is decided on the roll-up."""
    totals = {}
    for ln in lines:
        totals.setdefault(ln["code"], 0.0)
        totals[ln["code"]] += ln["req"]

    codes = []
    for code in sorted(totals):
        s = stock.get(code)
        req = totals[code]
        onhand = s["onhand"] if s else 0.0
        short = req - onhand
        codes.append(
            {
                "code": code,
                "sheet_names": sorted({ln["name"] for ln in lines if ln["code"] == code and ln["name"]}),
                "sap_name": s["sap_name"] if s else "NOT IN SAP",
                "uom": s["uom"] if s else "",
                "lines": sum(1 for ln in lines if ln["code"] == code),
                "req": req,
                "onhand": onhand,
                "committed": s["committed"] if s else 0.0,
                "onorder": s["onorder"] if s else 0.0,
                "short": short if short > 0.005 else 0.0,
                # LO req, the way the sheet reads it: stock minus requirement.
                # Negative = that much has to be arranged into the loose-oil godown.
                "lo_req": onhand - req,
                "left": onhand - req,
                "in_sap": bool(s),
                "by_whs": s["by_whs"] if s else {},
            }
        )
    return codes


# ------------------------------------------- inventory transfer request (OWTQ)
#
# What this reproduces, field for field, is what Lovepreet keys by hand: OWTQ
# DocEntry 2708 (DocNum 926656501, 02-Sep-2026, USER06) - BH-LO -> BH-PC, one
# line per RM code at the Fac Req quantity, and the sheet's own date + shift in
# Comments. DocDate is the day it is keyed; the sheet's date lives in Comments.
#
# It goes in as a DRAFT, which is how Lovepreet's own ones go in: ODRF holds 714
# of this object type, his last being DocEntry 55862 -> DocNum 926656501. Nothing
# posts until a human opens Document Drafts and presses Add.
#
# `sapb1 draft` cannot address it - its doctype table is the 15 marketing
# documents and it refuses "InventoryTransferRequests" outright. The draft path
# that does work is the one `draft` uses underneath: POST /Drafts with
# DocObjectCode, which `sapb1 post Drafts` reaches. --live swaps it for a direct
# POST /InventoryTransferRequests, which creates the request live instead.

ITR_OBJECT = "1250000001"  # OWTQ / ODRF ObjType - inventory transfer request
ITR_ENTITY = "InventoryTransferRequests"
ITR_FROM = "BH-LO"  # Bhakharpur Loose Oil
ITR_TO = "BH-PC"  # Bhakharpur Production Consumption


def itr_series(schema, doc_date):
    """The live series for that month, e.g. Sep-2026 -> 2649 (ITFR0926)."""
    want = "ITFR%s" % datetime.date.fromisoformat(doc_date).strftime("%m%y")
    rows = query(
        'SELECT "Series", "SeriesName", "NextNumber", "Locked" FROM %s.NNM1'
        " WHERE \"ObjectCode\" = '%s' ORDER BY \"Series\"" % (schema, ITR_OBJECT)
    )
    for r in rows:
        if (r["SeriesName"] or "").strip().upper() == want and (r["Locked"] or "N") == "N":
            return int(r["Series"]), r["SeriesName"], r["NextNumber"]
    have = ", ".join("%s=%s" % (r["SeriesName"], r["Series"]) for r in rows[-6:])
    sys.exit(
        "no open %s series for inventory transfer requests (%s).\n"
        "Ask whoever maintains the numbering series to define it, then re-run." % (want, have)
    )


def itr_existing(schema, date_raw, comments):
    """Anything already keyed for this sheet - live requests AND drafts.

    Both tables matter: a draft nobody added yet is still work already done, and
    a draft that WAS added leaves DocStatus 'C' in ODRF plus the live OWTQ row.
    """
    if not (date_raw or comments):
        return []
    like = (date_raw or comments).replace("'", "''")
    cols = (
        '"DocEntry", "DocNum", TO_VARCHAR("DocDate",\'YYYY-MM-DD\') AS DOCDATE,'
        ' "Comments", "DocStatus", "Filler" AS FROMWHS, "ToWhsCode" AS TOWHS'
    )
    found = []
    for kind, table, extra in (
        ("live", "OWTQ", ""),
        ("draft", "ODRF", " AND \"ObjType\" = '%s'" % ITR_OBJECT),
    ):
        for r in query(
            "SELECT %s FROM %s.%s WHERE \"Comments\" LIKE '%%%s%%'%s ORDER BY \"DocEntry\" DESC"
            % (cols, schema, table, like, extra)
        ):
            r["KIND"] = kind
            found.append(r)
    return found


def itr_payload(lines, codes, args, series):
    """The exact JSON body: POST /Drafts by default, /InventoryTransferRequests on --live."""
    date_raw = next((ln.get("date_raw") for ln in lines if ln.get("date_raw")), "")
    shift = next((ln["shift"] for ln in lines if ln["shift"]), "")
    comments = " ".join(x for x in (date_raw, shift) if x).strip()
    doc_date = args.doc_date or datetime.date.today().isoformat()
    # POST /Drafts is the generic `Document` type: its lines live in
    # `DocumentLines` and it has no header FromWarehouse/ToWarehouse. Sending
    # the StockTransfer names there is accepted with 201 and SILENTLY dropped -
    # DocEntry 55912 (02-Sep-2026) came out an empty header with BH-PF/BH-PF.
    # From/to therefore ride on every line. --live posts /InventoryTransferRequests,
    # which is the `StockTransfer` type and does take the header pair.
    lines_key = "StockTransferLines" if args.live else "DocumentLines"
    head = {} if args.live else {"DocObjectCode": ITR_OBJECT}
    if args.live:
        head["FromWarehouse"] = args.itr_from
        head["ToWarehouse"] = args.itr_to
    return comments, {
        **head,
        "Series": series,
        "DocDate": doc_date,
        "DocDueDate": doc_date,
        "Comments": comments,
        lines_key: [
            {
                "ItemCode": c["code"],
                "Quantity": round(c["req"], 3),
                "FromWarehouseCode": args.itr_from,
                "WarehouseCode": args.itr_to,
            }
            for c in codes
            if c["in_sap"] and c["req"] > 0
        ],
    }


def sapb1_env():
    """SAPB1_* for the sapb1 CLI, the way accounts-kit\\use.cmd sets them.

    A real environment variable beats the .env file, so a window already on
    `use lovepreet` (or a sourced connect.sh) keeps its own login and its own
    write-log path.
    """
    env = dict(os.environ)
    env_file = os.path.join(REPO, "sap-b1", "accounts-kit", "lovepreet-user06.env")
    if os.path.exists(env_file):
        with open(env_file, encoding="utf-8-sig", errors="replace") as fh:
            for raw in fh:
                if not raw.startswith("SAPB1_") or "=" not in raw:
                    continue
                k, v = raw.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    if not env.get("SAPB1_WRITE_LOG") and env.get("SAPB1_USER"):
        env["SAPB1_WRITE_LOG"] = os.path.join(REPO, "queries", env["SAPB1_USER"], "sap-writes.jsonl")
    if env.get("SAPB1_WRITE_LOG"):
        os.makedirs(os.path.dirname(env["SAPB1_WRITE_LOG"]), exist_ok=True)
    return env


def sapb1_bin():
    for rel in (("sap-b1", "accounts-kit", "sapb1.exe"), ("sap-b1", "cli", "sapb1")):
        p = os.path.join(REPO, *rel)
        if os.path.exists(p):
            return p
    sys.exit("sapb1 not found under %s/sap-b1" % REPO)


def itr_send(payload_path, company_db, live):
    """POST it - to /Drafts (nothing posts until a human Adds it), or live on --live."""
    entity = ITR_ENTITY if live else "Drafts"
    cmd = [
        sapb1_bin(),
        "post",
        entity,
        "--data-file",
        payload_path,
        "--company",
        company_db,
        "--yes",
    ]
    print("Sending: sapb1 post %s --data-file %s --yes" % (entity, payload_path))
    out = subprocess.run(cmd, cwd=REPO, env=sapb1_env())
    if out.returncode == 7:
        # documented meaning: the request reached SAP, the answer did not come back
        sys.exit(
            "\nEXIT 7 - the request reached SAP but the answer did not come back.\n"
            "DO NOT re-run this. Open SAP B1 -> Inventory -> Inventory Transfer Request\n"
            "and check whether the document exists before doing anything else."
        )
    if out.returncode != 0:
        sys.exit("\nsapb1 post failed (exit %d) - nothing else was sent." % out.returncode)
    return True


def write_xlsx(path, lines, codes, args, when):
    """The workbook in the shape Lovepreet keys it by hand.

    Sheet 1 is his layout exactly: every item with Stock in hand / Fac Req /
    LO req, then the short ones repeated underneath so the arrange-for list is
    the last thing on the page. The other two sheets are the working behind it.
    """
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    head = Font(bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="1F4E79")
    short_fill = PatternFill("solid", fgColor="FFC7CE")
    ok_fill = PatternFill("solid", fgColor="C6EFCE")
    warn_fill = PatternFill("solid", fgColor="FFEB9C")
    yellow = PatternFill("solid", fgColor="FFFF00")
    thin = Border(bottom=Side(style="thin", color="BFBFBF"))
    # negatives red and in brackets-free minus, the way the sheet reads today
    money = "#,##0.00;[Red]-#,##0.00"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "STOCK vs REQ"

    ws["A1"] = "RM stock in hand vs factory requirement"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = "%s  |  %s  |  godown %s  |  SAP read %s" % (
        COMPANY_NAME[args.company],
        next((ln["date"] for ln in lines if ln["date"]), ""),
        "ALL" if args.all_warehouses else args.warehouse,
        when,
    )
    ws["A2"].font = Font(italic=True, color="666666")

    def block(title, rows, start_row):
        r = start_row
        if title:
            ws.cell(row=r, column=1, value=title).font = Font(bold=True, size=12, color="C00000")
            r += 1
        hdr = ["Item No.", "Description", "Cumulative Qty", "Fac Req", "LO req"]
        if title:  # the short block names the stock column the way he reads it
            hdr[2] = "Stock in hand"
        for c, v in enumerate(hdr, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = head
            cell.fill = head_fill
        r += 1
        for item in rows:
            ws.cell(row=r, column=1, value=item["code"])
            ws.cell(row=r, column=2, value=item["sap_name"])
            ws.cell(row=r, column=3, value=item["onhand"] if item["in_sap"] else None)
            ws.cell(row=r, column=4, value=item["req"])
            ws.cell(row=r, column=5, value=item["lo_req"] if item["in_sap"] else None)
            for c in (3, 4, 5):
                ws.cell(row=r, column=c).number_format = money
            for c in range(1, 6):
                ws.cell(row=r, column=c).border = thin
            if not item["in_sap"]:
                ws.cell(row=r, column=2).fill = warn_fill
                ws.cell(row=r, column=5, value="NOT IN SAP")
            elif item["short"]:
                ws.cell(row=r, column=5).fill = short_fill
                ws.cell(row=r, column=5).font = Font(bold=True)
            r += 1
        return r

    row = block(None, codes, 4)

    shorts = [c for c in codes if c["short"] > 0 or not c["in_sap"]]
    row += 2
    if shorts:
        row = block("Ye arrange karna hai (LO req)", shorts, row)
        ws.cell(row=row, column=2, value="Total short")
        ws.cell(row=row, column=2).font = Font(bold=True)
        ws.cell(row=row, column=5, value=-sum(c["short"] for c in shorts))
        ws.cell(row=row, column=5).number_format = money
        ws.cell(row=row, column=5).font = Font(bold=True)
        ws.cell(row=row, column=5).fill = short_fill
    else:
        ws.cell(row=row, column=1, value="Kuch kam nahi - poori sheet stock ke andar hai.").fill = ok_fill

    # ---- sheet 2: SHEET - his rows, line by line, with SAP alongside
    ws3 = wb.create_sheet("SHEET")
    extra_n = max([len(ln["extra"]) for ln in lines] or [0])
    cols3 = ["Date", "Shift", "RM code", "Item name (as keyed)", "Fac Req"]
    cols3 += ["Other qty %d (as given)" % (i + 1) for i in range(extra_n)]
    cols3 += ["SAP item", "Stock in hand (code)", "Fac Req (code total)", "LO req (code)", "UOM"]
    ws3.append(cols3)
    for c in range(1, len(cols3) + 1):
        ws3.cell(row=1, column=c).font = head
        ws3.cell(row=1, column=c).fill = head_fill
    by_code = {c["code"]: c for c in codes}
    req_col = 5
    for ln in lines:
        c = by_code[ln["code"]]
        row3 = [ln["date"], ln["shift"], ln["code"], ln["name"], ln["req"]]
        row3 += list(ln["extra"]) + [None] * (extra_n - len(ln["extra"]))
        row3 += [c["sap_name"], c["onhand"], c["req"], c["lo_req"], c["uom"]]
        ws3.append(row3)
        r = ws3.max_row
        ws3.cell(row=r, column=req_col).fill = yellow
        for col in range(req_col, req_col + extra_n + 1):
            ws3.cell(row=r, column=col).number_format = money
        for col in range(req_col + extra_n + 2, req_col + extra_n + 5):
            ws3.cell(row=r, column=col).number_format = money
        if c["short"]:
            ws3.cell(row=r, column=req_col + extra_n + 4).fill = short_fill

    # ---- sheet 3: BY GODOWN - where the stock actually sits
    ws4 = wb.create_sheet("BY GODOWN")
    ws4.append(["RM code", "SAP item", "Godown", "Stock", "Committed", "On order", "UOM"])
    for c in range(1, 8):
        ws4.cell(row=1, column=c).font = head
        ws4.cell(row=1, column=c).fill = head_fill
    for c in codes:
        for whs, qty in sorted(c["by_whs"].items(), key=lambda kv: -kv[1]):
            here = whs == args.warehouse and not args.all_warehouses
            ws4.append(
                [
                    c["code"],
                    c["sap_name"],
                    whs,
                    qty,
                    c["committed"] if here else None,
                    c["onorder"] if here else None,
                    c["uom"],
                ]
            )
            r = ws4.max_row
            for col in (4, 5, 6):
                ws4.cell(row=r, column=col).number_format = money
            if here:
                ws4.cell(row=r, column=3).font = Font(bold=True)

    ws.freeze_panes = "A5"
    ws3.freeze_panes = "A2"
    ws4.freeze_panes = "A2"
    for sheet in (ws, ws3, ws4):
        for col in range(1, sheet.max_column + 1):
            width = 12
            for r in range(1, sheet.max_row + 1):
                v = sheet.cell(row=r, column=col).value
                if v is not None:
                    width = max(width, min(42, len(str(v)) + 2))
            sheet.column_dimensions[get_column_letter(col)].width = width
        for r in sheet.iter_rows():
            for cell in r:
                if isinstance(cell.value, str) and len(cell.value) > 30:
                    cell.alignment = Alignment(vertical="center")

    wb.save(path)



def main():
    ap = argparse.ArgumentParser(
        description="Production RM sheet vs live SAP loose-oil stock. Read-only."
    )
    ap.add_argument("sheet", help="xlsx / csv / tsv / pasted rows, or - for stdin")
    ap.add_argument("-o", "--out", help="output xlsx (default out/rm-stock-<date>.xlsx)")
    ap.add_argument(
        "-w", "--warehouse", default=DEFAULT_WHS, help="godown to check (default %s, loose oil)" % DEFAULT_WHS
    )
    ap.add_argument(
        "--all-warehouses", action="store_true", help="stock across every godown, not just one"
    )
    ap.add_argument("--company", default="oil", choices=sorted(SCHEMAS), help="SAP company (default oil)")
    ap.add_argument(
        "--req-col",
        type=int,
        default=2,
        metavar="N",
        help="which number column on the sheet is Fac Req (default 2 - the column"
        " beside the yellow indent; 1 = the yellow one itself)",
    )
    itr = ap.add_argument_group("inventory transfer request (OWTQ)")
    itr.add_argument(
        "--itr",
        action="store_true",
        help="also build the transfer request payload from the sheet (%s -> %s),"
        " sheet date + shift in Comments. Prints it, sends nothing." % (ITR_FROM, ITR_TO),
    )
    itr.add_argument(
        "--send",
        action="store_true",
        help="with --itr: actually send it. Goes in as a DRAFT - nothing posts"
        " until a human opens Document Drafts in SAP B1 and presses Add",
    )
    itr.add_argument(
        "--live",
        action="store_true",
        help="send it as a LIVE inventory transfer request instead of a draft",
    )
    itr.add_argument("--itr-from", default=ITR_FROM, help="issuing godown (default %s)" % ITR_FROM)
    itr.add_argument("--itr-to", default=ITR_TO, help="receiving godown (default %s)" % ITR_TO)
    itr.add_argument(
        "--doc-date", help="document date, YYYY-MM-DD (default today - the sheet date goes in Comments)"
    )
    itr.add_argument(
        "--force-duplicate",
        action="store_true",
        help="send even though a request already carries this sheet's date in Comments",
    )
    args = ap.parse_args()
    if args.send and not args.itr:
        sys.exit("--send only makes sense with --itr")

    rows = read_rows(args.sheet)
    lines = pick_req(parse_sheet(rows), args.req_col)
    if not lines:
        sys.exit(
            "no RM lines found in %s - expected an RM code (RM0000001) and a quantity on each row"
            % args.sheet
        )

    codes = sorted({ln["code"] for ln in lines})
    stock = sap_stock(codes, SCHEMAS[args.company], args.warehouse, args.all_warehouses)
    when = datetime.datetime.now().strftime("%d-%b-%Y %H:%M")
    result = build(lines, stock, args)

    os.makedirs(OUT, exist_ok=True)
    day = next((ln["date"] for ln in lines if ln["date"]), None) or datetime.date.today().isoformat()
    out_path = args.out or os.path.join(OUT, "rm-stock-%s.xlsx" % day)
    write_xlsx(out_path, lines, result, args, when)

    # ---- what to say out loud
    where = "ALL godowns" if args.all_warehouses else args.warehouse
    print(
        "%s | %s | godown %s | %d lines, %d RM codes | SAP read %s"
        % (COMPANY_NAME[args.company], day, where, len(lines), len(result), when)
    )
    print()
    hdr = "  %-11s %-34s %14s %14s %14s" % ("Item No.", "Description", "Stock in hand", "Fac Req", "LO req")
    shorts = [c for c in result if c["short"] > 0 or not c["in_sap"]]
    if shorts:
        print("YE ARRANGE KARNA HAI:")
        print(hdr)
        for c in shorts:
            if not c["in_sap"]:
                print("  %-11s %-34s %14s" % (c["code"], " + ".join(c["sheet_names"])[:34], "NOT IN SAP"))
                continue
            print(
                "  %-11s %-34s %14s %14s %14s %s"
                % (
                    c["code"],
                    c["sap_name"][:34],
                    fmt(c["onhand"]),
                    fmt(c["req"]),
                    fmt(c["lo_req"]),
                    c["uom"],
                )
            )
        print("  %-11s %-34s %14s %14s %14s" % ("", "Total short", "", "", fmt(-sum(c["short"] for c in shorts))))
    else:
        print("Kuch kam nahi - poori sheet stock ke andar hai.")
    ok = [c for c in result if c["in_sap"] and not c["short"]]
    if ok:
        print()
        print("Pura hai:")
        print(hdr)
        for c in ok:
            print(
                "  %-11s %-34s %14s %14s %14s %s"
                % (c["code"], c["sap_name"][:34], fmt(c["onhand"]), fmt(c["req"]), fmt(c["lo_req"]), c["uom"])
            )
    multi = [c for c in result if c["lines"] > 1]
    if multi:
        print()
        for c in multi:
            print(
                "note: %s is keyed on %d lines (%s) - checked on the total %s, not line by line."
                % (c["code"], c["lines"], ", ".join(c["sheet_names"]), fmt(c["req"]))
            )
    print()
    print("Excel: %s" % out_path)

    if args.itr:
        itr_step(lines, result, args, day, out_path)


def itr_step(lines, result, args, day, out_path):
    """Build (and only on --send, POST) the inventory transfer request."""
    import json

    schema = SCHEMAS[args.company]
    doc_date = args.doc_date or datetime.date.today().isoformat()
    series, series_name, next_num = itr_series(schema, doc_date)
    comments, payload = itr_payload(lines, result, args, series)

    kind = "LIVE REQUEST" if args.live else "DRAFT"
    print()
    print("=" * 78)
    print("INVENTORY TRANSFER REQUEST (%s) - %s -> %s" % (kind, args.itr_from, args.itr_to))
    print("=" * 78)
    if not comments:
        print(
            "WARNING: the sheet carried no date/shift, so Comments would go out empty.\n"
            "         Put the date and shift on the sheet, or the remark will be blank."
        )
    print("  Series      : %s (%s), next DocNum %s" % (series, series_name, next_num))
    print("  DocDate     : %s   (the sheet's date goes in the remark, not here)" % payload["DocDate"])
    print("  Comments    : %s" % (comments or "(EMPTY)"))
    itr_lines = payload.get("DocumentLines") or payload.get("StockTransferLines") or []
    print("  Lines       : %d" % len(itr_lines))
    for ln in itr_lines:
        c = next(x for x in result if x["code"] == ln["ItemCode"])
        print("    %-11s %-34s %14s %s" % (ln["ItemCode"], c["sap_name"][:34], fmt(ln["Quantity"]), c["uom"]))
    skipped = [c for c in result if not c["in_sap"]]
    for c in skipped:
        print("    %-11s NOT IN SAP - left off the request" % c["code"])

    payload_path = os.path.join(
        OUT, "itr-%s%s.json" % (day, "-" + re.sub(r"\W+", "", comments.split()[-1]) if comments else "")
    )
    with open(payload_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print()
    print("  Payload     : %s" % payload_path)

    dupes = itr_existing(schema, next((ln.get("date_raw") for ln in lines if ln.get("date_raw")), ""), comments)
    if dupes:
        print()
        print("  ALREADY IN SAP - a request for this sheet's date is keyed:")
        for d in dupes[:5]:
            print(
                "    %-5s DocEntry %-6s DocNum %-12s %s  %s -> %s  status %s  \"%s\""
                % (
                    d["KIND"],
                    d["DocEntry"],
                    d["DocNum"],
                    d["DOCDATE"],
                    d["FROMWHS"],
                    d["TOWHS"],
                    d["DocStatus"],
                    (d["Comments"] or "").replace("\r", " ").replace("\n", " ")[:40],
                )
            )

    if not args.send:
        print()
        print("Nothing sent. To %s:" % ("create it live in SAP" if args.live else "save it as a draft"))
        print(
            "  python3 acc/rm-stock/check.py %s --itr --send%s%s"
            % (args.sheet, " --live" if args.live else "", " --force-duplicate" if dupes else "")
        )
        return

    if dupes and not args.force_duplicate:
        sys.exit(
            "\nNOT SENT - a request for this sheet's date already exists (above).\n"
            "If a second one is genuinely needed, re-run with --force-duplicate."
        )
    if not (payload.get("DocumentLines") or payload.get("StockTransferLines")):
        sys.exit("\nNOT SENT - no line has a quantity.")
    print()
    if itr_send(payload_path, schema, args.live) and not args.live:
        print()
        print(
            "Draft saved. Kuch post nahi hua - SAP B1 kholo, Document Drafts me "
            "ye request dekho, aur Add dabao. Tab tak stock nahi hilta."
        )
        # POST /Drafts is the `Document` type, which has NO from-warehouse field -
        # not on the header, not on the line. It is not that the name is wrong:
        # `FromWarehouseCode` is accepted with 201/204 and dropped in silence
        # (proved on DocEntry 55914, 02-Sep-2026, by POST and again by PATCH).
        # So the draft always lands with SAP's default From (BH-PF here) and the
        # operator has to set it in the client. Only the live path
        # (/InventoryTransferRequests, the `StockTransfer` type) takes FromWarehouse.
        print(
            "\nDHYAN DO: draft me From warehouse %s NAHI jata - Drafts entity me wo"
            " field hi nahi hai, SAP apna default (BH-PF) daal deta hai."
            "\nTo (%s) theek hai. Add dabane se PEHLE client me From = %s kar lo,"
            " warna galat godown se transfer chala jayega."
            % (args.itr_from, args.itr_to, args.itr_from)
        )


if __name__ == "__main__":
    main()
