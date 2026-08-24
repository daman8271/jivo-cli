"""precheck — one open GRPO in, one decision out.

This is the batch's per-row judgement. It answers, in this order:

  is this party ourselves        -> INTERCOMPANY
  is this bill already in SAP    -> DUPLICATE
  can it even be identified      -> NEEDS-REF
  is it a shape we have proved   -> SERVICE-HOLD
  is anything actually wrong     -> CANNOT-BUILD
  otherwise                      -> READY, with a payload

The order matters. A duplicate that is also missing a reference is a duplicate:
saying "fix the reference" about a bill somebody already keyed sends an operator
to do work that must not be done.

Nothing here writes, and nothing here reads directly — every fact comes from the
ScanContext it is handed.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Mapping

from . import rules
from .context import ScanContext

READY = "READY"
DUPLICATE = "DUPLICATE"
CANNOT_BUILD = "CANNOT-BUILD"
SERVICE_HOLD = "SERVICE-HOLD"
NEEDS_REF = "NEEDS-REF"
INTERCOMPANY = "INTERCOMPANY"
# Not decided per row: two rows of the SAME batch carrying one vendor reference.
# batch_scan applies it after every row has been checked, because it takes the
# whole batch to see it.
REF_COLLISION = "REF-COLLISION"

STATUSES = (READY, DUPLICATE, REF_COLLISION, NEEDS_REF, SERVICE_HOLD, CANNOT_BUILD,
            INTERCOMPANY)


@dataclass
class PrecheckResult:
    grpo: dict
    status: str = READY
    reasons: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    lines: list = field(default_factory=list)
    totals: rules.Totals = field(default_factory=rules.Totals)
    vendor: dict = field(default_factory=dict)
    group_name: str = ""
    branch: dict = field(default_factory=dict)
    subtype: str = "bod_GSTTaxInvoice"
    series: rules.SeriesChoice | None = None
    tds: rules.TdsProposal | None = None
    po_nums: list = field(default_factory=list)
    payload: dict | None = None
    comments_base: str = ""
    attachment_entry: Any = None
    duplicates: list = field(default_factory=list)

    @property
    def reason_text(self) -> str:
        return "; ".join(self.reasons + self.notes)

    @property
    def is_ready(self) -> bool:
        return self.status == READY


def precheck_grpo(ctx: ScanContext, grpo: Mapping[str, Any], allow_service: bool = False,
                  include_intercompany: bool = False, today: dt.date | None = None) -> PrecheckResult:
    today = today or dt.date.today()
    res = PrecheckResult(grpo=dict(grpo))
    res.attachment_entry = grpo.get("AttachmentEntry")

    vendor = ctx.vendor(grpo["CardCode"])
    res.vendor = vendor
    res.group_name = ctx.group_name(vendor.get("GroupCode"))
    res.lines = rules.open_lines(grpo)
    res.totals = rules.gross_of(res.lines)
    res.branch = ctx.branches().get(grpo.get("BPL_IDAssignedToInvoice")) or {}

    # 1. ourselves? (C-0020: the name is the test, not the group)
    name = vendor.get("CardName") or grpo.get("CardName")
    if rules.is_intercompany(grpo["CardCode"], name, ctx.company_db) and not include_intercompany:
        res.status = INTERCOMPANY
        res.reasons.append(f"{grpo['CardCode']} {name} is a JIVO group company — intercompany "
                           "billing is not this batch's job (--include-intercompany to override)")
        return res

    # 2. already in SAP?
    res.duplicates = rules.find_duplicates(grpo, ctx.posted_by_ref(), ctx.drafts_by_ref(),
                                           ctx.drafts_by_base())
    if res.duplicates:
        res.status = DUPLICATE
        res.reasons.append(rules.duplicate_reason(res.duplicates))
        return res

    # 3. can it be identified at all?
    if not (grpo.get("NumAtCard") or "").strip():
        res.status = NEEDS_REF
        res.reasons.append("the GRPO carries no vendor reference — nothing to put in NumAtCard, "
                           "and no way to tell later whether this bill was already booked")
        return res

    # 4. a shape we have proved on live SAP?
    if rules.is_service(grpo) and not allow_service:
        res.status = SERVICE_HOLD
        res.reasons.append("service GRPO (no item lines) — that draft shape has not been sent "
                           "live yet; held until one is proved by hand")
        return res

    # 5. anything actually wrong
    problems = _problems(ctx, grpo, res, today)
    res.notes.extend(_notes(grpo, res, today))
    if problems:
        res.status = CANNOT_BUILD
        res.reasons.extend(problems)
        return res

    # 6. ready — build it
    res.po_nums = ctx.po_docnums(
        [l.get("BaseEntry") for l in res.lines if l.get("BaseType") == 22 and l.get("BaseEntry")])
    res.comments_base = rules.comments_base(grpo, res.po_nums)
    res.payload = rules.build_payload(grpo, res.lines, res.branch["BPLID"],
                                      res.series.series, res.subtype)
    res.status = READY
    return res


def _problems(ctx: ScanContext, grpo: Mapping[str, Any], res: PrecheckResult,
              today: dt.date) -> list[str]:
    problems: list[str] = []

    if not res.lines:
        problems.append("no open lines — the GRPO is already invoiced "
                        "(C-0019: an 'open' status here can lag reality)")
    if not res.vendor:
        problems.append(f"vendor card {grpo['CardCode']} could not be read")
    else:
        if res.vendor.get("Frozen") == "tYES":
            problems.append(f"vendor card {grpo['CardCode']} is FROZEN")
        if res.vendor.get("Valid") not in (None, "tYES"):
            problems.append(f"vendor card {grpo['CardCode']} is not valid")

    bpl_id = grpo.get("BPL_IDAssignedToInvoice")
    if not res.branch:
        problems.append(f"branch {bpl_id} is not in BusinessPlaces — no BPL_IDAssignedToInvoice "
                        "to post under (-5002)")
    elif res.branch.get("Disabled") == "tYES":
        problems.append(f"branch {bpl_id} {res.branch.get('BPLName')} is disabled")

    docdate = rules.as_date(grpo["DocDate"])
    if docdate < rules.fy_start(today):
        problems.append(f"posting date {docdate.isoformat()} is in the previous financial year, "
                        "period closed — handle it in the client")

    # TDS and series need the vendor, so they come after it is known to exist.
    if res.vendor:
        res.subtype = ctx.subtype_for(grpo["CardCode"])
        tds_code = next((w.get("WTCode") for w in
                         (res.vendor.get("BPWithholdingTaxCollection") or []) if w.get("WTCode")),
                        None)
        res.tds = rules.tds_proposal(res.vendor, ctx.last_invoices(grpo["CardCode"]),
                                     ctx.wt_rate(tds_code), res.totals.taxable)
    if res.branch:
        res.series = ctx.series_for(res.branch["BPLID"], docdate, res.subtype)
        if res.series.problem:
            problems.append(res.series.problem)
    return problems


def _notes(grpo: Mapping[str, Any], res: PrecheckResult, today: dt.date) -> list[str]:
    """Things a reviewer should see that are NOT reasons to stop."""
    notes: list[str] = []
    if not grpo.get("AttachmentEntry"):
        notes.append("no bill attached to the GRPO — the draft will have nothing to point at")
    if res.series and res.series.warning:
        notes.append(res.series.warning)
    if res.totals.partial_lines:
        # The money columns are the OPEN part (rules.gross_of), which is less
        # than the GRPO's own line totals. Say so, or the reviewer compares the
        # sheet against the paper bill and thinks a figure is wrong.
        notes.append(f"line(s) {res.totals.partial_lines} partially billed earlier — "
                     "value is the open part, not the whole GRPO line")

    docdate = rules.as_date(grpo["DocDate"])
    this_month = today.replace(day=1)
    prev_month = (this_month - dt.timedelta(days=1)).replace(day=1)
    if docdate.replace(day=1) not in (this_month, prev_month) and docdate >= rules.fy_start(today):
        notes.append(f"posting month {rules.month_label(docdate)} — confirm the period is open")

    if rules.iso_date(grpo.get("TaxDate")) == rules.iso_date(grpo.get("DocDate")):
        notes.append("bill date on the GRPO equals the gate date — it may be a default, "
                     "check the bill")
    return notes


def bill_date_source(grpo: Mapping[str, Any]) -> str:
    """What column S says: can the vendor's invoice date be trusted as it stands?"""
    if not grpo.get("TaxDate"):
        return "no TaxDate on the GRPO — read it off the bill"
    if rules.iso_date(grpo.get("TaxDate")) == rules.iso_date(grpo.get("DocDate")):
        return "= gate date (may be default) — check bill"
    return "GRPO TaxDate"
