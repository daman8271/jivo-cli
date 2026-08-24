"""batch_scan — walk the open GRPOs and produce a review workbook.

Read-only by construction, not by intention: the SapCli it builds has
allow_writes=False, so draft() and patch() raise before a process is spawned.
That matters because this is the half an operator runs on their own.

What comes out is one workbook with three sheets and one sidecar. The sidecar
carries the payload for every row that could be built; the workbook carries the
same facts plus five yellow cells per row. `acc batch send` reads both and will
only send a row whose grey cells still agree with the sidecar.

If SAP goes away mid-scan, nothing is written at all. A half-scanned workbook is
worse than no workbook: it looks complete, and its missing rows look like rows
that were checked and found to need nothing.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Any, Sequence

from . import precheck as apprecheck
from . import rules, store, xlsx
from .context import GRPO_PAGE_SIZE, HanaSql, ScanContext
from .sap import (SapAuth, SapCli, SapConfig, SapError, SapUnreachable, SapUsage,
                  find_repo, odata_str)

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

COMPANIES = {
    "oil": "JIVO_OIL_HANADB",
    "mart": "JIVO_MART_HANADB",
    "bev": "JIVO_BEVERAGES_HANADB",
    "beverage": "JIVO_BEVERAGES_HANADB",
    "beverages": "JIVO_BEVERAGES_HANADB",
}

DEFAULT_SINCE_DAYS = 90

# Columns A..Z of the Review sheet. The letters are the contract: the sidecar
# records B..U as `locked` and send compares them cell by cell, so changing this
# list changes the tamper check too.
REVIEW_HEADERS = [
    "Row",                              # A
    "GRPO DocNum",                      # B
    "GRPO DocEntry",                    # C  (row key)
    "Posting date (DocDate)",           # D
    "Vendor code",                      # E
    "Vendor name",                      # F
    "Vendor group",                     # G
    "Branch",                           # H
    "Type",                             # I
    "Lines",                            # J
    "Open qty",                         # K
    "Taxable",                          # L
    "Tax",                              # M
    "Gross",                            # N
    "Series",                           # O
    "Sub-type",                         # P
    "TDS evidence",                     # Q
    "Attachment",                       # R
    "Bill date source",                 # S
    "Status",                           # T
    "Reason",                           # U
    "Approve? (yes/no)",                # V  editable
    "TDS (yes/no)",                     # W  editable
    "Vendor bill date (TaxDate)",       # X  editable
    "Vendor ref (NumAtCard)",           # Y  editable
    "Note (goes to Remarks)",           # Z  editable
]
REVIEW_WIDTHS = [5, 14, 11, 14, 13, 34, 16, 18, 8, 46, 11, 14, 12, 14, 8, 18, 52, 14,
                 34, 14, 60, 16, 12, 22, 22, 30]
COL_KEY = 2                             # C — GRPO DocEntry
LOCKED_COLUMNS = range(1, 21)           # B..U
EDITABLE_COLUMNS = {21, 22, 23, 24, 25}  # V..Z
VALIDATIONS = {21: ["yes", "no"], 22: ["yes", "no"]}
NUMBER_STYLES = {10: "qty", 11: "inr", 12: "inr", 13: "inr"}

LINES_HEADERS = ["GRPO DocEntry", "LineNum", "ItemCode", "Description", "Open qty", "Unit",
                 "UnitPrice", "LineTotal", "TaxCode", "TaxTotal", "Whs", "CostingCode",
                 "Base PO DocNum"]
LINES_WIDTHS = [13, 9, 14, 40, 12, 8, 12, 14, 12, 12, 10, 12, 15]


def resolve_company(name: str | None) -> str:
    if not name:
        return "JIVO_OIL_HANADB"
    key = name.strip().lower()
    if key in COMPANIES:
        return COMPANIES[key]
    if name.strip().upper().startswith("JIVO_") and name.strip().upper().endswith("_HANADB"):
        return name.strip().upper()
    raise ValueError(f"unknown company {name!r} — use Oil, Mart, Beverages, or the full DB name")


def run_scan(args, sap: SapCli | None = None, today: dt.date | None = None,
             now: dt.datetime | None = None, batch_id: str | None = None,
             repo: Path | str | None = None) -> int:
    today = today or dt.date.today()
    now = now or dt.datetime.now()
    repo = Path(repo) if repo else find_repo()
    quiet = bool(getattr(args, "quiet", False))

    def say(*parts):
        if not quiet:
            print(*parts)

    # -- arguments -------------------------------------------------------
    try:
        company = resolve_company(getattr(args, "company", None))
        since = _resolve_since(getattr(args, "since", None), today)
        limit = int(getattr(args, "limit", 50) or 0)
        if limit < 0:
            raise ValueError("--limit cannot be negative (0 means every matching row)")
        order = (getattr(args, "order", "oldest") or "oldest").lower()
        if order not in ("oldest", "newest"):
            raise ValueError("--order must be oldest or newest")
    except ValueError as e:
        print(f"acc batch scan: {e}", file=sys.stderr)
        return 2

    if sap is None:
        try:
            sap = SapCli(repo=repo, company=company, env_file=getattr(args, "env", None),
                         allow_writes=False)
        except SapConfig as e:
            print(f"acc batch scan: {e}", file=sys.stderr)
            return 3

    batch_id = batch_id or store.new_batch_id(company, when=now)
    out_dir = Path(getattr(args, "out", None) or store.batch_dir(repo, batch_id))

    say(f"== acc batch scan · {company} · login {sap.user} · host {sap.route} · batch {batch_id}")
    # Which env file the login came from, spelled out: "whose drafts are these"
    # is the question this answers, and an --env that resolved somewhere the
    # operator did not expect is invisible otherwise.
    say(f"   env       {sap.env_path or '(sap-b1/cli/.env)'}")
    say(f"   open GRPOs since {since}, oldest first" if order == "oldest"
        else f"   open GRPOs since {since}, newest first")

    hana = HanaSql(repo)
    ctx = ScanContext(sap, company_db=company, hana=hana if hana.available else None, log=say)

    # -- read ------------------------------------------------------------
    try:
        grpos = _fetch_grpos(ctx, since, getattr(args, "vendor", None))
        say(f"   {len(grpos)} open GRPOs in the window")
        if not grpos:
            say("   nothing to review — no workbook written")
            return 0

        ctx.prefetch_vendors({g["CardCode"] for g in grpos})
        grpos = _apply_filters(ctx, grpos, args, company)
        if not grpos:
            say("   nothing matched the filters — no workbook written")
            return 0

        grpos.sort(key=lambda g: (rules.as_date(g["DocDate"]), g["DocEntry"]),
                   reverse=(order == "newest"))
        if limit:
            grpos = grpos[:limit]
        say(f"   {len(grpos)} row(s) selected")

        ctx.branches()
        ctx.groups()
        ctx.open_ap_drafts()
        ctx.prefetch_posted_refs(g.get("NumAtCard") for g in grpos)
        ctx.prefetch_po_docnums(l.get("BaseEntry") for g in grpos
                                for l in (g.get("DocumentLines") or [])
                                if l.get("BaseType") == 22)

        results = []
        for g in grpos:
            try:
                results.append(apprecheck.precheck_grpo(
                    ctx, g,
                    allow_service=bool(getattr(args, "allow_service", False)),
                    include_intercompany=bool(getattr(args, "include_intercompany", False)),
                    today=today))
            except (SapUnreachable, SapAuth, SapConfig, SapUsage):
                raise                       # the connection is gone: abort the whole scan
            except Exception as e:          # one malformed GRPO must not eat the other 49
                results.append(_unreadable_row(g, e))
        _mark_ref_collisions(results)
    except SapUnreachable as e:
        print(f"\nacc batch scan: CANNOT REACH SAP — nothing was written.\n  {e}", file=sys.stderr)
        return 4
    except (SapAuth, SapConfig) as e:
        print(f"\nacc batch scan: SAP would not let us in — {e}", file=sys.stderr)
        return 3
    except SapUsage as e:
        print(f"\nacc batch scan: {e}", file=sys.stderr)
        return 2
    except SapError as e:
        print(f"\nacc batch scan: SAP refused a read — nothing was written.\n  {e}",
              file=sys.stderr)
        return 4

    # -- write (only once every read has succeeded) -----------------------
    sidecar = store.Sidecar.new(batch_id=batch_id, company=company, login=sap.user,
                                host=sap.route, scanned_at=now.isoformat(),
                                scan_args=_scan_args(args, since, limit, order))
    review_rows, line_rows, editable_rows = [], [], []
    for n, res in enumerate(results, start=1):
        row = _review_row(n, res)
        review_rows.append(row)
        if res.status == apprecheck.READY:
            editable_rows.append(n - 1)     # 0-based index into review_rows
        line_rows.extend(_line_rows(ctx, res))
        sidecar.add_row(
            res.grpo["DocEntry"], row=n, status=res.status, reasons=res.reasons + res.notes,
            locked={xlsx.column_letter(c): row[c] for c in LOCKED_COLUMNS},
            defaults={xlsx.column_letter(c): row[c] for c in sorted(EDITABLE_COLUMNS)},
            payload=res.payload, comments_base=res.comments_base,
            expect=res.totals.as_dict(), attachment_entry=res.attachment_entry,
            tds=res.tds.as_dict() if res.tds else None,
            series=res.series.as_dict() if res.series else None)

    out_dir.mkdir(parents=True, exist_ok=True)
    book = out_dir / store.workbook_name(batch_id)
    xlsx.write_workbook(book, [
        xlsx.SheetSpec(name="Review", headers=REVIEW_HEADERS, rows=review_rows,
                       widths=REVIEW_WIDTHS, styles=NUMBER_STYLES,
                       editable=EDITABLE_COLUMNS, validations=VALIDATIONS,
                       editable_rows=editable_rows),
        xlsx.SheetSpec(name="Lines", headers=LINES_HEADERS, rows=line_rows,
                       widths=LINES_WIDTHS, styles={4: "qty", 6: "inr", 7: "inr", 9: "inr"}),
        xlsx.SheetSpec(name="About", headers=["Field", "Value"],
                       rows=_about_rows(batch_id, company, sap, now, args, since, limit,
                                        order, results, book),
                       widths=[36, 110], protect=True),
    ])
    # Both stamped with the batch id: --out is often one folder an operator
    # scans several companies into, and a bare sidecar.json would be overwritten
    # by the next scan while its workbook stayed behind.
    sidecar.save(out_dir / store.sidecar_name(batch_id))
    store.Journal(out_dir / store.journal_name(batch_id)).append({
        "event": "scan", "batch_id": batch_id, "company": company, "login": sap.user,
        "rows": len(results), "counts": sidecar.counts(), "reads": ctx.reads,
        "workbook": str(book)})

    _report(say, results, sidecar, book, out_dir, ctx, batch_id)
    return 0


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

def _resolve_since(since: str | None, today: dt.date) -> str:
    if not since:
        return (today - dt.timedelta(days=DEFAULT_SINCE_DAYS)).isoformat()
    try:
        return dt.date.fromisoformat(since.strip()).isoformat()
    except ValueError:
        raise ValueError(f"--since {since!r} is not a date — use YYYY-MM-DD")


def _looks_like_card_code(text: str) -> bool:
    import re
    return bool(re.fullmatch(r"[A-Z]+\d{6,}", (text or "").strip().upper()))


def _fetch_grpos(ctx: ScanContext, since: str, vendor: str | None) -> list[dict]:
    flt = (f"DocumentStatus eq 'bost_Open' and Cancelled eq 'tNO' and DocDate ge '{since}'")
    if vendor and _looks_like_card_code(vendor):
        flt += f" and CardCode eq {odata_str(vendor.strip().upper())}"
    return ctx.sap.query("PurchaseDeliveryNotes", filter=flt, all=True,
                         page_size=GRPO_PAGE_SIZE, orderby="DocDate asc,DocEntry asc")


def _apply_filters(ctx: ScanContext, grpos: list[dict], args, company: str) -> list[dict]:
    """Everything that decides whether a GRPO is even this batch's business.

    Run BEFORE --limit, so the limit counts rows that reach the sheet. An
    intercompany GRPO is dropped here rather than shown as an excluded row: it
    is not work anybody is going to do, and 12 of them would otherwise eat a
    quarter of a 50-row batch.

    DUPLICATE rows are the opposite case and DO consume the limit — a bill
    already keyed is exactly what the reviewer needs to see, and hiding it would
    make the sheet disagree with SAP.
    """
    vendor = (getattr(args, "vendor", None) or "").strip()
    group = (getattr(args, "group", None) or "").strip().upper()
    include_intercompany = bool(getattr(args, "include_intercompany", False))
    out = []
    for g in grpos:
        bp = ctx.vendor(g["CardCode"])
        name = (bp.get("CardName") or g.get("CardName") or "")
        if vendor and not _looks_like_card_code(vendor):
            if vendor.lower() not in name.lower() and vendor.upper() != g["CardCode"]:
                continue
        if group and group not in (ctx.group_name(bp.get("GroupCode")) or "").upper():
            continue
        if not include_intercompany and rules.is_intercompany(g["CardCode"], name, company):
            continue
        out.append(g)
    return out


def _unreadable_row(grpo: dict, error: Exception) -> apprecheck.PrecheckResult:
    """A GRPO that threw. It becomes a row, not a traceback.

    49 checked rows and one line saying which GRPO could not be read is worth
    more than a stack trace and no workbook — the operator can still send the 49
    and hand the one to somebody.
    """
    res = apprecheck.PrecheckResult(grpo=dict(grpo), status=apprecheck.CANNOT_BUILD)
    res.reasons.append(f"could not read this GRPO: {type(error).__name__}: {error}")
    return res


def _mark_ref_collisions(results: list) -> None:
    """Two rows of this batch that are the same bill: hold BOTH.

    Only READY rows are considered — a row already held for another reason is
    already held, and adding a second reason buries the first.
    """
    candidates = [
        {"row": n, "docentry": r.grpo.get("DocEntry"), "docnum": r.grpo.get("DocNum"),
         "ref": r.grpo.get("NumAtCard")}
        for n, r in enumerate(results, start=1) if r.status == apprecheck.READY]
    collisions = rules.ref_collisions(candidates)
    if not collisions:
        return
    for res in results:
        others = collisions.get(res.grpo.get("DocEntry"))
        if res.status == apprecheck.READY and others:
            res.status = apprecheck.REF_COLLISION
            res.reasons.insert(0, rules.collision_reason(res.grpo.get("NumAtCard"), others))
            res.payload = None              # nothing sendable comes off a held row


# --------------------------------------------------------------------------
# rows
# --------------------------------------------------------------------------

def _review_row(n: int, res: apprecheck.PrecheckResult) -> list:
    g = res.grpo
    branch = res.branch
    series = res.series
    row = [
        n,                                                                      # A
        g.get("DocNum"),                                                        # B
        g["DocEntry"],                                                          # C
        rules.iso_date(g.get("DocDate")) or "",                                 # D
        g["CardCode"],                                                          # E
        res.vendor.get("CardName") or g.get("CardName") or "",                  # F
        res.group_name,                                                         # G
        f"{branch.get('BPLID')} {branch.get('BPLName')}" if branch
        else f"{g.get('BPL_IDAssignedToInvoice')} (unknown)",                    # H
        "Service" if rules.is_service(g) else "Items",                          # I
        rules.line_summary(res.lines),                                          # J
        res.totals.open_qty,                                                    # K
        res.totals.taxable,                                                     # L
        res.totals.tax,                                                         # M
        res.totals.gross,                                                       # N
        series.series if series and series.series else "",                      # O
        res.subtype,                                                            # P
        res.tds.evidence() if res.tds else "",                                  # Q
        f"yes ({g['AttachmentEntry']})" if g.get("AttachmentEntry") else "NONE",  # R
        apprecheck.bill_date_source(g),                                         # S
        res.status,                                                             # T
        res.reason_text,                                                        # U
        "",                                                                     # V
        _tds_cell(res),                                                         # W
        rules.iso_date(g.get("TaxDate")) or rules.iso_date(g.get("DocDate")) or "",  # X
        (g.get("NumAtCard") or "").strip(),                                     # Y
        "",                                                                     # Z
    ]
    return [xlsx.clean_text(v) for v in row]


def _tds_cell(res: apprecheck.PrecheckResult) -> str:
    """Column W: the proposal, or BLANK when the evidence contradicts itself.

    A prefilled answer is a decision made for the operator. When tds.check is
    set — master says liable and the last invoices withheld nothing, or the
    lines were marked liable and produced ₹0, or the card carries several WT
    codes — nobody here knows the answer, so the cell is left empty and `send`
    refuses the row as INVALID-INPUT until a person types yes or no.
    """
    if not res.tds:
        return "no"
    return "" if res.tds.check else res.tds.choice


def _line_rows(ctx: ScanContext, res: apprecheck.PrecheckResult) -> list[list]:
    out = []
    for l in res.lines:
        po = ctx.po_docnums([l.get("BaseEntry")]) if l.get("BaseType") == 22 else []
        out.append([res.grpo["DocEntry"], l.get("LineNum"), l.get("ItemCode") or "",
                    l.get("ItemDescription") or "", l.get("RemainingOpenQuantity") or 0,
                    l.get("MeasureUnit") or "", l.get("UnitPrice") or 0,
                    l.get("LineTotal") or 0, l.get("TaxCode") or "", l.get("TaxTotal") or 0,
                    l.get("WarehouseCode") or "", l.get("CostingCode") or "",
                    po[0] if po else ""])
    return out


def _scan_args(args, since: str, limit: int, order: str) -> dict:
    return {"since": since, "limit": limit, "order": order,
            "vendor": getattr(args, "vendor", None), "group": getattr(args, "group", None),
            "include_intercompany": bool(getattr(args, "include_intercompany", False)),
            "allow_service": bool(getattr(args, "allow_service", False)),
            "env": getattr(args, "env", None)}


def _about_rows(batch_id, company, sap, now, args, since, limit, order, results, book) -> list[list]:
    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    rows = [
        ["batch_id", batch_id],
        ["company", company],
        ["login (drafts land under this user)", sap.user],
        ["env file (where that login came from)", str(sap.env_path or "sap-b1/cli/.env")],
        ["host", sap.route],
        ["scanned_at", now.isoformat()],
        ["scan args", f"since={since} limit={limit or 'all'} order={order} "
                      f"vendor={getattr(args, 'vendor', None) or '-'} "
                      f"group={getattr(args, 'group', None) or '-'} "
                      f"include-intercompany={bool(getattr(args, 'include_intercompany', False))} "
                      f"allow-service={bool(getattr(args, 'allow_service', False))}"],
        ["rows", len(results)],
        ["", ""],
    ]
    for status in apprecheck.STATUSES:
        rows.append([f"count · {status}", counts.get(status, 0)])
    rows += [
        ["", ""],
        ["HOW TO REVIEW THIS", "Edit ONLY the yellow cells (V-Z). Everything grey is checked "
                               "against SAP again before anything is sent, and a changed grey "
                               "cell makes the row refuse to send."],
        ["", "Only READY rows have yellow cells. On every other row V-Z are grey and locked, "
             "because those rows cannot be sent whatever you type in them."],
        ["", "A blank TDS (yes/no) cell means the evidence contradicts itself — read the TDS "
             "evidence column and type yes or no yourself. The row will not send while it is blank."],
        ["", "Put yes in 'Approve?' on every row you want drafted. Leave it blank to skip."],
        ["", "Save the file as .xlsx (not .csv), then run:  acc batch send "
             f"\"{book.name}\"   — that PREVIEWS. Add --yes to actually send."],
        ["", ""],
        ["STATUS LEGEND", ""],
        ["READY", "a draft can be built; approve it and it will be sent"],
        ["DUPLICATE", "already in SAP (posted invoice, or an open draft on this GRPO or ref) "
                      "— never send"],
        ["REF-COLLISION", "two rows of THIS batch carry the same vendor reference — one bill on "
                          "two goods receipts. Both are held; find out which receipt it belongs "
                          "to"],
        ["NEEDS-REF", "the GRPO has no vendor reference; fix the GRPO or use the single-bill skill"],
        ["SERVICE-HOLD", "service GRPO — that draft shape has not been proved live yet"],
        ["CANNOT-BUILD", "see the Reason column; nothing here can be sent"],
        ["INTERCOMPANY", "a JIVO group company (C-0020) — not this batch's job"],
        ["", ""],
        ["Nothing posts from here", "everything this creates is a DRAFT. A person opens SAP B1 "
                                    "→ Document Drafts, reviews it and presses Add."],
    ]
    return rows


def _report(say, results, sidecar, book, out_dir, ctx, batch_id) -> None:
    counts = sidecar.counts()
    say("")
    for status in apprecheck.STATUSES:
        if counts.get(status):
            say(f"   {status:<14} {counts[status]:>4}")
    ready = counts.get("READY", 0)
    say(f"\n   {ready} row(s) can be drafted · {ctx.reads} SAP reads · nothing was written")
    say(f"   workbook  {book}")
    say(f"   sidecar   {out_dir / store.sidecar_name(batch_id)}")
    say("\n   Next: open the workbook, put 'yes' in column V on the rows you want, save,")
    say(f"   then:  acc batch send \"{book}\"        (preview — add --yes to send)")
