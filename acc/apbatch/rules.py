"""rules — the decisions, with no I/O anywhere in them.

Everything here is a pure function of data that was already fetched. That is
what makes the batch reviewable: the same functions decide a single bill in the
ap-rm-pm skill and 50 rows in `acc batch`, and every one of them can be
pinned by a test without SAP being up.

The two that carry the most risk are documented at length where they are
defined: tds_proposal (precedent beats the master flag — C-0018, TPAC 08-22) and
pick_series (branch x month x sub-type, month-BOUNDED — C-0018).
"""

from __future__ import annotations

import collections
import datetime as dt
import re
import sys
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Iterable, Mapping, Sequence

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# --------------------------------------------------------------------------
# money, dates, text
# --------------------------------------------------------------------------

def inr(n: float) -> str:
    """₹ with Indian digit grouping. Byte-identical to the skill's original."""
    neg = n < 0
    n = abs(float(n))
    i, f = f"{n:.2f}".split(".")
    last3, rest = i[-3:], i[:-3]
    if rest:
        rest = re.sub(r"\B(?=(\d{2})+(?!\d))", ",", rest) + ","
    return ("-" if neg else "") + "₹" + rest + last3 + "." + f


def ingroup(n: float) -> str:
    """Indian grouping without the currency sign, trailing zeros dropped."""
    text = inr(n)[1:] if n >= 0 else "-" + inr(n)[2:]
    return text[:-3] if text.endswith(".00") else text


def tokens(s: str | None) -> set[str]:
    """Words of two or more characters — for loose name comparison."""
    return {t for t in re.findall(r"[a-z0-9.]+", (s or "").lower()) if len(t) > 1}


def as_date(value: Any) -> dt.date:
    """A SAP date string, an ISO string or a date -> date."""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if value is None:
        raise ValueError("no date")
    return dt.date.fromisoformat(str(value)[:10])


def iso_date(value: Any) -> str | None:
    """'2026-08-14T00:00:00Z' -> '2026-08-14'. None stays None."""
    if value in (None, ""):
        return None
    return as_date(value).isoformat()


def fy_indicator(d: dt.date | str) -> str:
    """SAP period indicator, e.g. AUG-26-27 (JIVO's year runs April-March)."""
    d = as_date(d)
    start = d.year if d.month >= 4 else d.year - 1
    return f"{d.strftime('%b').upper()}-{start % 100:02d}-{(start + 1) % 100:02d}"


def fy_start(d: dt.date | str) -> dt.date:
    """1 April of the financial year this date falls in."""
    d = as_date(d)
    return dt.date(d.year if d.month >= 4 else d.year - 1, 4, 1)


def month_bounds(docdate: dt.date | str) -> tuple[str, str]:
    """The half-open month around a posting date: ['2026-07-01', '2026-08-01').

    The UPPER bound is the point. Without it, a July GRPO scanned in August pulls
    August's documents into the series vote and takes August's series — a wrong
    number on a July posting, which SAP will happily accept.
    """
    d = as_date(docdate)
    first = d.replace(day=1)
    nxt = dt.date(first.year + 1, 1, 1) if first.month == 12 else first.replace(month=first.month + 1)
    return first.isoformat(), nxt.isoformat()


def month_label(d: dt.date | str) -> str:
    """'Aug-26' — how the source of a series choice is described to a reviewer."""
    d = as_date(d)
    return f"{d.strftime('%b')}-{d.year % 100:02d}"


_EXCEL_EPOCH = dt.date(1899, 12, 30)
_TEXT_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d-%b-%Y", "%d.%m.%Y", "%d/%m/%y")


def parse_sheet_date(value: Any) -> dt.date | None:
    """Whatever Excel handed back in a date cell -> a date.

    Excel will not be told: a column formatted as text still comes back as a
    serial number if the operator retyped the cell, and a date typed by hand
    arrives in whichever format their Windows locale prefers. Blank is None;
    anything unrecognised raises, because a silently mis-parsed vendor bill date
    lands on a real document.
    """
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _from_excel_serial(float(value))

    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T[\d:.]+Z?", text):
        text = text[:10]
    if re.fullmatch(r"\d+(\.\d+)?", text):
        return _from_excel_serial(float(text))
    for fmt in _TEXT_DATE_FORMATS:
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"cannot read {value!r} as a date — use YYYY-MM-DD or DD/MM/YYYY")


def _from_excel_serial(serial: float) -> dt.date:
    if not 20000 <= serial <= 80000:                 # 1954-01-01 .. 2119-01-01
        raise ValueError(f"{serial} is not a plausible Excel date serial")
    return _EXCEL_EPOCH + dt.timedelta(days=int(serial))


def to_excel_serial(d: dt.date | str) -> int:
    return (as_date(d) - _EXCEL_EPOCH).days


# --------------------------------------------------------------------------
# intercompany (C-0005 + C-0020)
# --------------------------------------------------------------------------

# The 23 related-party CUSTOMER cards catalogued in C-0005. They are customer
# codes, so they never appear on a GRPO — they are here so one function answers
# "is this party ourselves" for any company, whichever side it is read from.
INTERCOMPANY_CARDS: dict[str, frozenset[str]] = {
    "JIVO_OIL_HANADB": frozenset({
        "CUSTA000001", "CUSTA000002", "CUSTA000003", "CUSTA000004", "CUSTA000606",
        "CUSTA000827", "CUSTA000906", "CUSTA001099", "CUSTA001113"}),
    "JIVO_MART_HANADB": frozenset({
        "CUSTA000001", "CUSTA000827", "CUSTA000874", "CUSTA000875", "CUSTA000876",
        "CUSTA000877", "CUSTA000878", "CUSTA000926"}),
    "JIVO_BEVERAGES_HANADB": frozenset({
        "CUSTA000001", "CUSTA000002", "CUSTA000003", "CUSTA000004", "CUSTA000606",
        "CUSTA000827"}),
}

# C-0020: on the vendor side the group cards sit in ordinary trading groups
# (Mart VENDA000001 'JIVO WELLNESS PVT LTD' is in PURCHASE), so the group is not
# a usable test. The NAME is.
INTERCOMPANY_NAME_MARKERS = ("JIVO", "AKAL")

# Anchored to a word start: a plain substring test makes PRAKALP and SAKAL
# intercompany, and an excluded vendor is a bill nobody books.
INTERCOMPANY_NAME_RE = re.compile(
    r"\b(" + "|".join(INTERCOMPANY_NAME_MARKERS) + r")", re.I)


def is_intercompany(card_code: str | None, card_name: str | None, company_db: str | None) -> bool:
    if INTERCOMPANY_NAME_RE.search(card_name or ""):
        return True
    return (card_code or "") in INTERCOMPANY_CARDS.get(company_db or "", frozenset())


# --------------------------------------------------------------------------
# GRPO lines and totals
# --------------------------------------------------------------------------

def is_service(grpo: Mapping[str, Any]) -> bool:
    return grpo.get("DocType") == "dDocument_Service"


def open_lines(grpo: Mapping[str, Any], allow_service: bool = True) -> list[dict]:
    """The lines an A/P invoice would be drawn from.

    Item lines must still be open AND carry open quantity. Service lines carry
    no quantity at all (Quantity 0, RemainingOpenQuantity 0, ItemCode null), so
    the quantity test would throw all of them away — they qualify on status.

    allow_service=False makes a service GRPO come back with no lines at all,
    which is what the single-bill skill has always done with one: it says "no
    open lines" and stops rather than building a draft shape nobody has proved.
    """
    service = is_service(grpo) and allow_service
    out = []
    for l in grpo.get("DocumentLines") or []:
        if l.get("LineStatus") != "bost_Open":
            continue
        if not service and not (l.get("RemainingOpenQuantity") or 0) > 0:
            continue
        out.append(dict(l))
    return out


@dataclass
class Totals:
    open_qty: float = 0.0
    taxable: float = 0.0
    tax: float = 0.0
    gross: float = 0.0
    per_line: dict = field(default_factory=dict)
    # LineNums that are only partly open. Their money is the OPEN part, which is
    # less than what the GRPO line says — the review sheet has to say so.
    partial_lines: list = field(default_factory=list)

    @property
    def partial(self) -> bool:
        return bool(self.partial_lines)

    def as_dict(self) -> dict:
        return {"open_qty": self.open_qty, "taxable": self.taxable, "tax": self.tax,
                "gross": self.gross, "lines": self.per_line,
                "partial_lines": list(self.partial_lines)}


def gross_of(lines: Sequence[Mapping[str, Any]]) -> Totals:
    """Money for the part that will actually be billed — not the whole GRPO line.

    build_payload sends `Quantity = RemainingOpenQuantity`, so a line that was
    half invoiced last month bills only the half that is left. Summing the
    GRPO's own LineTotal would put a number on the review sheet bigger than the
    document the batch is about to create, and an operator who ticks yes on
    "₹2,14,700" would be approving ₹2,14,700 while ₹700 of it is already booked.

    Per line, therefore:
      taxable = open qty x UnitPrice        (exactly what the payload asks SAP for)
      tax     = TaxTotal x open/total qty   (pro-rated; SAP recomputes it anyway)
    A service line carries no quantity at all (Quantity 0, RemainingOpenQuantity
    0): nothing to pro-rate, the whole line is what gets billed, so its own
    LineTotal/TaxTotal stand.

    Note on discounts: a GRPO line with a discount has LineTotal < qty x price,
    so this would read high on such a line. The payload does not send
    DiscountPercent either, so what it reads is still what the draft asks for;
    the draft SAP actually builds is the authority in that case.
    """
    t = Totals()
    for l in lines:
        openq = float(l.get("RemainingOpenQuantity") or 0)
        qty = float(l.get("Quantity") or 0)
        if qty > 0:
            taxable = openq * float(l.get("UnitPrice") or 0)
            tax = float(l.get("TaxTotal") or 0) * (openq / qty)
            if abs(openq - qty) > 1e-9:
                t.partial_lines.append(l.get("LineNum"))
        else:
            taxable = float(l.get("LineTotal") or 0)
            tax = float(l.get("TaxTotal") or 0)
        t.open_qty += openq
        t.taxable += taxable
        t.tax += tax
        t.per_line[str(l["LineNum"])] = openq
    t.open_qty = round(t.open_qty, 6)
    t.taxable = round(t.taxable, 2)
    t.tax = round(t.tax, 2)
    t.gross = round(t.taxable + t.tax, 2)
    return t


def line_summary(lines: Sequence[Mapping[str, Any]], max_lines: int = 3) -> str:
    """One cell that says what is on the GRPO, for a human scanning 50 rows."""
    parts = []
    for l in lines[:max_lines]:
        what = l.get("ItemCode") or ""
        desc = (l.get("ItemDescription") or "").strip()
        head = f"{l['LineNum']}: {what} {desc}".replace("  ", " ").strip()
        openq = float(l.get("RemainingOpenQuantity") or 0)
        qty = float(l.get("Quantity") or 0)
        piece = head
        if qty and abs(openq - qty) > 1e-9:
            piece += f" open {ingroup(openq)}/{ingroup(qty)}"
        elif openq:
            piece += f" {ingroup(openq)}"
        piece += f" @{float(l.get('UnitPrice') or 0):.2f}"
        parts.append(piece)
    text = " · ".join(parts)
    if len(lines) > max_lines:
        text += f" +{len(lines) - max_lines} more"
    return text


# --------------------------------------------------------------------------
# TDS — precedent beats the master flag
# --------------------------------------------------------------------------

@dataclass
class TdsProposal:
    choice: str                      # "yes" | "no"  -> what W is PROPOSED as
    basis: str
    check: bool                      # render as "CHECK:" — W is left blank, a human answers
    master_liable: bool
    wt_code: str | None              # the first code, for the sidecar's old shape
    rate: float | None
    expected_amount: int
    precedent: list = field(default_factory=list)
    wt_codes: list = field(default_factory=list)
    # The taxable this was computed from. A field, not an attribute bolted on
    # after construction, so as_dict()/from_dict() round trips and `send` can
    # rebuild the proposal from the sidecar and still print the same evidence.
    taxable: float = 0.0

    def evidence(self) -> str:
        if self.precedent:
            marks = "/".join(_precedent_mark(p) for p in self.precedent)
            amounts = "/".join(f"{p['wtamount']:g}" for p in self.precedent)
            head = f"last {len(self.precedent)} posted: {marks} (WTAmount {amounts})"
            if any(p.get("marked") and not p["withheld"] for p in self.precedent):
                head += " [lines say WTax liable, nothing was withheld]"
        else:
            head = "no posted history for this vendor"
        codes = self.wt_codes or ([self.wt_code] if self.wt_code else [])
        if self.master_liable and codes:
            rate = f"@{self.rate}%" if self.rate is not None else "(rate unknown)"
            tail = f"master {', '.join(str(c) for c in codes)} {rate}"
            if len(codes) > 1:
                tail += f" ({len(codes)} codes on the card — which one applies?)"
            if self.rate:
                tail += f" → {inr(round(self._would_be()))} if yes"
        elif self.master_liable:
            tail = "master: liable, no WT code on the card"
        else:
            tail = "master: not TDS-liable"
        text = f"{head} · {tail}"
        return ("CHECK: " + text) if self.check else text

    def _would_be(self) -> float:
        return float(self.taxable or 0) * (self.rate or 0) / 100

    def as_dict(self) -> dict:
        return {"choice": self.choice, "basis": self.basis, "check": self.check,
                "master_liable": self.master_liable, "wt_code": self.wt_code,
                "rate": self.rate, "expected_amount": self.expected_amount,
                "precedent": self.precedent, "wt_codes": list(self.wt_codes),
                "taxable": self.taxable}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TdsProposal":
        """Rebuild from a sidecar. Unknown keys are ignored; missing ones default."""
        return cls(choice=data.get("choice", "no"), basis=data.get("basis", ""),
                   check=bool(data.get("check")), master_liable=bool(data.get("master_liable")),
                   wt_code=data.get("wt_code"), rate=data.get("rate"),
                   expected_amount=int(data.get("expected_amount") or 0),
                   precedent=list(data.get("precedent") or []),
                   wt_codes=list(data.get("wt_codes") or []),
                   taxable=float(data.get("taxable") or 0))


def _precedent_mark(p: Mapping[str, Any]) -> str:
    """How one previous invoice reads: withheld, marked-but-zero, or plain no."""
    if p.get("withheld"):
        return "yes"
    return "marked" if p.get("marked") else "no"


def tds_proposal(bp: Mapping[str, Any], last_posted: Sequence[Mapping[str, Any]],
                 wt_rate: float | None, taxable: float) -> TdsProposal:
    """What to tick for TDS, and why — decided from how JIVO actually books this vendor.

    The master flag alone is wrong often enough to matter: TPAC is
    SubjectToWithholdingTax boYES with 194Q at 0.1% (₹214 on this bill), and all
    three of its last posted invoices are tNO with WTAmount 0. Accounts does not
    withhold from it. Precedent wins; where precedent and master disagree the
    row is marked CHECK rather than decided quietly.

    "Withheld" means MONEY was withheld — WTAmount > 0 — and nothing else. A
    line flagged WTLiable tYES that produced ₹0 is not a precedent for
    withholding; it is the C-0018 shape, a document somebody marked liable and
    SAP computed nothing on. Reading it as a yes is how a vendor JIVO has never
    deducted from (VENDA000636: three posted invoices, every line tYES, WTAmount
    0 on all three) would get TDS deducted by a batch. That contradiction is
    exactly what a person has to resolve, so it lands as choice "no" WITH
    check=True — and a checked row leaves column W blank, so the sheet cannot be
    approved until a human types the answer.
    """
    codes = [w.get("WTCode") for w in (bp.get("BPWithholdingTaxCollection") or []) if w.get("WTCode")]
    master_liable = bp.get("SubjectToWithholdingTax") == "boYES" and bool(codes)

    prec = []
    for i in list(last_posted)[:3]:
        amount = float(i.get("WTAmount") or 0)
        prec.append({
            "docentry": i.get("DocEntry"),
            "ref": i.get("NumAtCard"),
            "docdate": iso_date(i.get("DocDate")),
            "wtamount": amount,
            "withheld": amount > 0,
            "marked": any(l.get("WTLiable") == "tYES"
                          for l in (i.get("DocumentLines") or [])),
        })

    n = len(prec)
    k = sum(1 for p in prec if p["withheld"])
    marked = sum(1 for p in prec if p["marked"])
    if not master_liable:
        choice, basis, check = "no", "MASTER-NOT-LIABLE", k > 0
    elif n == 0:
        choice, basis, check = "yes", "NO-HISTORY->MASTER", True
    elif k == n:
        choice, basis, check = "yes", "PRECEDENT-YES", False
    elif k == 0 and marked:
        choice, basis, check = "no", "PRECEDENT-NO-AMOUNT", True
    elif k == 0:
        choice, basis, check = "no", "PRECEDENT-NO", False
    else:
        choice, basis, check = "yes", "MIXED->MASTER", True

    if len(codes) > 1:                     # which of them applies is not ours to guess
        check = True

    expected = round(taxable * wt_rate / 100) if choice == "yes" and wt_rate else 0
    return TdsProposal(choice=choice, basis=basis, check=check, master_liable=master_liable,
                       wt_code=codes[0] if codes else None, rate=wt_rate,
                       expected_amount=int(expected), precedent=prec,
                       wt_codes=list(codes), taxable=float(taxable or 0))


# --------------------------------------------------------------------------
# Numbering series — branch x month x sub-type
# --------------------------------------------------------------------------

SUBTYPE_TO_NNM1 = {"bod_GSTTaxInvoice": "GA", "bod_None": "--", "bod_GSTDebitMemo": "GD"}
VENDOR_SERIES_NAME = re.compile(r"[A-Z]{2,4}_G\d{4}")


@dataclass
class SeriesChoice:
    series: int | None = None
    subtype: str = "bod_GSTTaxInvoice"
    source: str = ""
    nnm1: list = field(default_factory=list)
    warning: str | None = None
    problem: str | None = None
    # Every series seen this month and how often, so a narrative caller can show
    # the vote instead of just its winner.
    counts: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"series": self.series, "subtype": self.subtype, "source": self.source,
                "nnm1": self.nnm1, "warning": self.warning, "problem": self.problem,
                "counts": self.counts}


def pick_series(docs: Sequence[Mapping[str, Any]], nnm1_rows: Sequence[Sequence] | None,
                subtype: str, bpl: int | None = None,
                docdate: dt.date | str | None = None) -> SeriesChoice:
    """Which numbering series this posting belongs to.

    First source is what the branch actually used this month for this sub-type
    (`docs` must already be month-BOUNDED — see month_bounds). Falling back to
    NNM1 matters only for the first document of a month, and there the sub-type
    is what disambiguates: branch 2 has both HR_G0826 (vendor invoices) and
    CNHR0826 (credit notes) filed as GA, and only the `xx_Gmmyy` one is right.
    """
    choice = SeriesChoice(subtype=subtype, nnm1=[list(r) for r in (nnm1_rows or [])])
    want = SUBTYPE_TO_NNM1.get(subtype)
    candidates = [r for r in (nnm1_rows or []) if len(r) > 2 and r[2] == want]
    candidate_ids = {int(r[0]) for r in candidates}

    counted = collections.Counter(d["Series"] for d in docs if d.get("Series"))
    choice.counts = dict(counted)
    if counted:
        choice.series = int(counted.most_common(1)[0][0])
        where = f" branch {bpl}" if bpl is not None else ""
        when = f" {month_label(docdate)}" if docdate else ""
        choice.source = f"{sum(counted.values())} docs{when}{where}"
        if candidates and choice.series not in candidate_ids:
            choice.warning = (f"this month's documents use series {choice.series}, which NNM1 does "
                              f"not list as {want} for branch {bpl} — double-check")
        return choice

    if len(candidates) == 1:
        choice.series = int(candidates[0][0])
        choice.source = "NNM1 (first document of the month)"
        return choice
    if len(candidates) > 1:
        named = [r for r in candidates if VENDOR_SERIES_NAME.fullmatch(str(r[1] or ""))]
        if len(named) == 1:
            choice.series = int(named[0][0])
            choice.source = f"NNM1 {named[0][1]} — the xx_G series among {len(candidates)} {want}"
            # A NAME decided this, not a document and not a single candidate.
            # The pattern is a house convention, not a rule SAP enforces: branch
            # 6's real vendor series is DISD0826, which does not match it. So say
            # out loud that a guess was made, and show what it chose between.
            choice.warning = (
                f"series {choice.series} chosen by name pattern ({named[0][1]}) from "
                f"{sorted(candidate_ids)} — no {want} document exists this month for branch "
                f"{bpl} to confirm it; verify before approving")
            return choice
        choice.problem = (f"several {want} series in NNM1 for branch {bpl} "
                          f"{sorted(candidate_ids)} — pick by hand")
        return choice

    if nnm1_rows is None:
        # None means "could not look" (hana-sql absent or unreachable), which is
        # NOT the same as "the branch has no series". Saying "first document of
        # the month" there sends the operator hunting for a fact that was never
        # checked.
        choice.problem = (f"no {want} document this month for branch {bpl} and could not check "
                          "NNM1 (hana-sql unreachable) — series unknown")
        return choice
    choice.problem = (f"first document of the month for branch {bpl} — series unknown "
                      "(see .claude/skills/ap-rm-pm/reference/series-and-errors.md)")
    return choice


# --------------------------------------------------------------------------
# Duplicates
# --------------------------------------------------------------------------

_REF_LEADING = ".-/#0 \t"


def normalize_ref(ref: Any) -> str:
    """A vendor reference reduced to what makes two of them the SAME bill.

    Accounts types these off paper, and the same invoice number arrives as
    `.2633100542`, `2633100542`, `2633100542 ` and `002633100542` on different
    days. Live proof from the 2026-08-24 Oil scan: GRPOs 25710 and 25911, both
    BR Agrotech, both the same money, refs `.2633100542` and `2633100542` — one
    bill, two open goods receipts, and an exact-string check calls neither a
    duplicate.

    So: trim, collapse inner runs of whitespace, casefold, and drop leading
    punctuation and leading zeros. Nothing is removed from the middle or the
    end — `26-27/1450` and `26271450` are NOT the same reference, and pretending
    they are would hide real bills behind each other.
    """
    text = re.sub(r"\s+", " ", str(ref or "").strip()).casefold()
    if not text:
        return ""
    stripped = text.lstrip(_REF_LEADING)
    if stripped:
        return stripped
    # Nothing survived. `000` is a reference (of zeros) and keeps them; `.` or
    # `---` is punctuation somebody typed into an empty box, and is no reference
    # at all — two GRPOs marked `.` are not the same bill.
    return text if any(c.isalnum() for c in text) else ""


def ref_variants(ref: Any) -> list[str]:
    """The spellings of one reference worth asking SAP about, case preserved.

    normalize_ref casefolds, which a `NumAtCard eq '...'` filter would not match
    on a case-sensitive column, so the query needs the real strings: the
    reference as the GRPO carries it, and the same thing without the leading
    punctuation/zeros that Accounts sometimes types and sometimes does not.
    """
    text = re.sub(r"\s+", " ", str(ref or "").strip())
    out: list[str] = []
    for v in (text, text.lstrip(_REF_LEADING)):
        if v and v not in out:
            out.append(v)
    return out


def find_duplicates(grpo: Mapping[str, Any],
                    posted_by_ref: Mapping[str, Sequence[Mapping]],
                    drafts_by_ref: Mapping[str, Sequence[Mapping]],
                    drafts_by_base: Mapping[int, Sequence[Mapping]]) -> list[dict]:
    """Is this bill already in SAP?

    Three ways it can be, and the GRPO-keyed one is the one that catches what a
    ref match cannot: Accounts keys these in the client the same afternoon the
    paper arrives, sometimes with a typo'd or blank vendor reference. A second
    draft on the same GRPO is a duplicate whatever it is called.

    The ref indexes are keyed by normalize_ref, not by the raw string.

    Only a LIVE document blocks. `Cancelled` has three states on the Service
    Layer, not two: 'tNO' live, 'tYES' cancelled, and — on the cancellation
    mirror SAP creates, which HANA stores as 'C' — the key is simply ABSENT from
    the JSON. `!= "tYES"` therefore reads a cancellation mirror as a live
    duplicate and holds a bill nobody has booked. Live has to be said
    positively: Cancelled == 'tNO'.
    """
    ref = normalize_ref(grpo.get("NumAtCard"))
    entry = grpo.get("DocEntry")
    card = (grpo.get("CardCode") or "").strip().upper()
    found: dict[tuple, dict] = {}

    def add(kind, doc):
        key = (("draft" if kind.startswith("draft") else "posted"), doc.get("DocEntry"))
        if key in found:
            return
        other = (doc.get("CardCode") or "").strip().upper()
        found[key] = {"kind": kind, "docentry": doc.get("DocEntry"), "docnum": doc.get("DocNum"),
                      "cardcode": doc.get("CardCode"), "ref": doc.get("NumAtCard"),
                      "docdate": iso_date(doc.get("DocDate")),
                      "total": float(doc.get("DocTotal") or 0), "owner": doc.get("UserSign"),
                      "approval": doc.get("AuthorizationStatus"),
                      "docstatus": doc.get("DocumentStatus"),
                      "cross_vendor": bool(card and other and other != card)}

    if ref:
        for doc in posted_by_ref.get(ref, ()):
            if doc.get("Cancelled") == "tNO":
                add("posted", doc)
        for doc in drafts_by_ref.get(ref, ()):
            if doc.get("Cancelled", "tNO") == "tNO":
                add("draft-ref", doc)
    for doc in drafts_by_base.get(entry, ()):
        if doc.get("Cancelled", "tNO") == "tNO":
            add("draft-grpo", doc)
    return list(found.values())


def ref_collisions(rows: Sequence[Mapping[str, Any]]) -> dict[Any, list[dict]]:
    """Rows inside ONE batch whose vendor references are the same bill.

    find_duplicates looks at SAP. This looks at the batch itself, which SAP
    cannot help with: two open GRPOs carrying one vendor reference are one bill
    received twice, and approving both drafts two A/P invoices for it. It is on
    live data (the BR Agrotech pair above), and neither row is obviously the
    right one — so both are held and a person decides.

    `rows` are dicts with row / docentry / docnum / ref. Returns
    {docentry: the other rows it collides with}, empty when nothing collides.
    """
    buckets: dict[str, list[dict]] = {}
    for r in rows:
        ref = normalize_ref(r.get("ref"))
        if ref:
            buckets.setdefault(ref, []).append(dict(r))
    out: dict[Any, list[dict]] = {}
    for group in buckets.values():
        if len(group) < 2:
            continue
        for r in group:
            out[r["docentry"]] = [o for o in group if o["docentry"] != r["docentry"]]
    return out


def collision_reason(ref: Any, others: Sequence[Mapping[str, Any]]) -> str:
    where = "; ".join(f"row {o.get('row')} (GRPO {o.get('docnum')}, DocEntry {o.get('docentry')})"
                      for o in others)
    return (f"vendor ref {str(ref).strip()!r} is on another row of this batch — {where}. "
            "One bill cannot become two A/P invoices: check which goods receipt it belongs to, "
            "then re-scan or draft the right one by hand")


def draft_targets_grpo(draft: Mapping[str, Any], grpo_docentry: int) -> bool:
    """Does this draft already draw from that GRPO? (BaseType 20 = goods receipt PO)"""
    return any(l.get("BaseType") == 20 and l.get("BaseEntry") == grpo_docentry
               for l in (draft.get("DocumentLines") or []))


def same_ref(a: Any, b: Any) -> bool:
    """Are these two vendor references the same bill?

    The comparison the OData filter cannot make. `NumAtCard eq '2633100542'`
    matches that string and nothing else, so a document spelled `.2633100542`
    is invisible to it — in ONE direction only, which is worse than not looking,
    because it looks like a check.
    """
    left, right = normalize_ref(a), normalize_ref(b)
    return bool(left) and left == right


def adoption_evidence(draft: Mapping[str, Any], batch_id: str | None = None,
                      login_key: Any = None, grpo_docentry: Any = None) -> str | None:
    """Why this draft can be believed to be the one OUR lost write created.

    `--resume` exists to find the draft an unanswered write left behind. Matching
    on the vendor reference or the goods receipt finds that draft — and finds
    equally well the one Accounts keyed by hand in the client while the batch was
    halted. Adopting theirs means this batch reports a draft it did not make,
    stops watching for its own, and (with --yes) PATCHES somebody else's document.

    So a match is not evidence. Evidence is one of exactly two things:
      * the batch id is in the draft's Remarks — nothing but this batch puts it
        there; or
      * the draft belongs to this login AND draws from this goods receipt.

    Returns the sentence to show the operator, or None for "this is not ours".
    """
    comments = str(draft.get("Comments") or "")
    if batch_id and batch_id in comments:
        return f"its Remarks carry this batch id ({batch_id})"
    if login_key is not None and grpo_docentry is not None:
        try:
            same_user = int(draft.get("UserSign")) == int(login_key)
        except (TypeError, ValueError):
            same_user = False
        if same_user and draft_targets_grpo(draft, int(grpo_docentry)):
            return (f"it was made by this login (UserSign {login_key}) and draws from "
                    f"GRPO DocEntry {grpo_docentry}")
    return None


def foreign_draft_reason(draft: Mapping[str, Any]) -> str:
    """A draft that matches this row but is not ours, named well enough to go and look."""
    status = draft.get("AuthorizationStatus")
    if status:
        words = APPROVAL_WORDS.get(str(status))
        where = f"AuthorizationStatus {status}" + (f" ({words})" if words else "")
    else:
        # Not every Drafts row comes back with one. Say which field is being
        # quoted rather than labelling a document status as an approval status.
        where = f"DocumentStatus {draft.get('DocumentStatus') or '?'}, no AuthorizationStatus"
    return (f"draft DocEntry {draft.get('DocEntry')} (DocNum {draft.get('DocNum')}) carries this "
            f"bill — ref {str(draft.get('NumAtCard') or '')!r}, owner UserSign "
            f"{draft.get('UserSign')}, {where}")


def cell_text(value: Any, default: Any = None) -> tuple[str, str | None]:
    """A cell that must travel to SAP as a STRING, and what went wrong with it.

    Excel re-types a box of digits as a number the moment somebody clicks in it,
    and `str()` of that is not what was printed on the bill: 2633100542.0, or
    2.6331e+09, or 26331 where the paper says 0026331. When the scan's own value
    was a string, that string is the only spelling anybody has evidence for, so
    it wins and the change is reported. When both are numbers there is nothing to
    fall back to, so it is formatted without the drift Python's str() adds.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value or "").strip(), None
    if isinstance(default, str) and default.strip():
        return default.strip(), (f"column Y came back from Excel as the number {value!r}; the "
                                 f"scan read {default.strip()!r} off the goods receipt and that "
                                 "is what was sent — check it against the bill")
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, float):
        text = repr(value)
        if "e" in text or "E" in text:
            text = f"{Decimal(str(value)):f}"
        return text, ("column Y is a number, not text — Excel may have dropped leading zeros "
                      "or rounded it; check it against the bill")
    return str(value), ("column Y is a number, not text — Excel may have dropped leading zeros; "
                        "check it against the bill")


# Drafts speak das*, posted marketing documents speak bas*. Both are here
# because the duplicate that blocks a row can be either.
#
# Checked live 2026-08-24 on Oil: of 1,053 OPEN A/P drafts, 817 are
# dasCancelled, 86 dasPending, 68 dasApproved, 57 dasRejected, 25 dasWithout.
# So most of what the GRPO-keyed duplicate check finds is somebody's abandoned
# approval, not live work — which is precisely why the state has to be in the
# reason instead of a bare "already drafted".
APPROVAL_WORDS = {
    "dasApproved": "approved", "dasPending": "PENDING APPROVAL",
    "dasRejected": "approval REJECTED", "dasCancelled": "approval CANCELLED",
    "dasWithout": "no approval needed", "dasGenerated": "not sent for approval",
    "basApproved": "approved", "basPending": "PENDING APPROVAL", "basRejected": "rejected",
    "basGenerated": "not sent for approval", "basWithout": "no approval needed",
}


def duplicate_reason(dups: Sequence[Mapping[str, Any]]) -> str:
    """Why this row is held — with enough about the blocking document to act on it.

    A draft that is PENDING APPROVAL is somebody's live work; a draft that was
    REJECTED is dead and the operator may well want to key this bill again. The
    status is the difference between "leave it alone" and "go finish it", so it
    goes in the reason rather than making them open the client to find out.
    """
    kinds = {"posted": "posted A/P invoice", "draft-ref": "open draft (same vendor ref)",
             "draft-grpo": "open draft on this GRPO"}
    bits = []
    for d in dups:
        owner = f" user {d['owner']}" if d.get("owner") is not None else ""
        ref = f" ref {d['ref']!r}" if d.get("ref") else ""
        state = ""
        approval = d.get("approval")
        if approval:
            state += f" · {APPROVAL_WORDS.get(approval, approval)}"
        if d.get("docstatus"):
            state += f" · {d['docstatus']}"
        who = ""
        if d.get("cross_vendor"):
            who = (f" — ref matches a document of a DIFFERENT vendor {d.get('cardcode')}: "
                   "verify it was not keyed against the wrong card before you dismiss this")
        bits.append(f"{kinds.get(d['kind'], d['kind'])} DocEntry {d['docentry']}{ref} "
                    f"{inr(d['total'])}{owner}{state}{who}")
    return "; ".join(bits)


# --------------------------------------------------------------------------
# The payload
# --------------------------------------------------------------------------

GATE_ENTRY = re.compile(r"GATE ENTRY NO\.?\s*(\d+)", re.I)


def comments_base(grpo: Mapping[str, Any], po_nums: Sequence[Any]) -> str:
    """`Based On Goods Receipt PO n | PO n | GATE ENTRY NO n` — how Accounts searches."""
    parts = [f"Based On Goods Receipt PO {grpo['DocNum']}"]
    if po_nums:
        parts.append("PO " + ", ".join(str(p) for p in po_nums))
    m = GATE_ENTRY.search(grpo.get("Comments") or "")
    if m:
        parts.append(f"GATE ENTRY NO {m.group(1)}")
    return " | ".join(parts)


COMMENTS_LIMIT = 254


def build_comments(base: str, note: str | None = None, tag: str | None = None,
                   limit: int = COMMENTS_LIMIT) -> str:
    """Assemble Comments, keeping the batch tag whatever else has to go.

    The tag is how a run is found afterwards — `grep <tag> queries/*/sap-writes.jsonl`
    and the same string in SAP's own search. Truncating it away would make the
    run untraceable, so it is appended after the truncation, not before.
    """
    parts = [(base or "").strip()] + ([note.strip()] if note and note.strip() else [])
    body = " | ".join(p for p in parts if p)
    if not tag:
        return body[:limit]
    if not body.strip():
        return tag[:limit]                 # never a Comments that opens with " | "
    suffix = " | " + tag
    room = limit - len(suffix)
    if room <= 0:
        return tag[:limit]
    trimmed = body[:room].rstrip(" |")
    return (trimmed + suffix) if trimmed else tag[:limit]


# --- handwriting → dimensions (C-0027) -------------------------------------
# Accounts writes the allocation on the paper itself ("Common" next to "For oil
# plant" on Ashok Diwan 1256). Those words are field values, not remarks: the
# Budget dimension (CostingCode3) they name overrides whatever the GRPO carried.
# Patterns are deliberately loose about spelling — it is handwriting.
NOTE_BUDGET: tuple[tuple[str, str], ...] = (
    (r"\bcomm?[ao]n\b", "FACT_COM"),        # Common / Comman / Comon → FACTORY COMMON
)


def budget_from_note(note: str | None) -> tuple[str, str] | None:
    """(CostingCode3, the word as written) if the note names a Budget; else None."""
    if not note:
        return None
    for pattern, code in NOTE_BUDGET:
        m = re.search(pattern, note, re.IGNORECASE)
        if m:
            return code, m.group(0)
    return None


def apply_budget(payload: dict, code: str) -> dict:
    """Set CostingCode3 on every line, in place. Returns the payload for chaining."""
    for row in payload.get("DocumentLines", []):
        row["CostingCode3"] = code
    return payload


def build_payload(grpo: Mapping[str, Any], lines: Sequence[Mapping[str, Any]],
                  bpl_id: int, series: int | None, subtype: str) -> dict:
    """The draft, minus everything that is decided at send time.

    NumAtCard, TaxDate, Comments and per-line WTLiable are deliberately absent:
    they come from the review sheet's editable cells, so the sidecar's payload is
    the part a reviewer cannot change. Add them with finalize_payload.

    DocDate is the GRPO's date (C-0017 — gate-in, not today, not the vendor's
    invoice date). DocDueDate is left out so SAP applies the vendor's terms.
    """
    payload: dict[str, Any] = {
        "CardCode": grpo["CardCode"],
        "DocDate": iso_date(grpo["DocDate"]),
        "BPL_IDAssignedToInvoice": bpl_id,
        "Series": series,
        "DocumentSubType": subtype,
        "DocumentLines": [],
    }
    service = is_service(grpo)
    for l in lines:
        row: dict[str, Any] = {
            "BaseType": 20,
            "BaseEntry": grpo["DocEntry"],
            "BaseLine": l["LineNum"],
        }
        if not service:
            row["ItemCode"] = l["ItemCode"]
            row["Quantity"] = l["RemainingOpenQuantity"]
            row["UnitPrice"] = l["UnitPrice"]
            row["TaxCode"] = l["TaxCode"]
            row["WarehouseCode"] = l["WarehouseCode"]
            if l.get("CostingCode"):
                row["CostingCode"] = l["CostingCode"]
        payload["DocumentLines"].append(row)
    return payload


def finalize_payload(payload: Mapping[str, Any], num_at_card: str, tax_date: Any,
                     wtliable: str | None, comments: str) -> dict:
    """The four send-time fields, spliced into a copy in SAP's own field order."""
    out: dict[str, Any] = {
        "CardCode": payload["CardCode"],
        "DocDate": payload["DocDate"],
        "TaxDate": iso_date(tax_date),
        "NumAtCard": num_at_card,
        "BPL_IDAssignedToInvoice": payload["BPL_IDAssignedToInvoice"],
        "Series": payload["Series"],
        "DocumentSubType": payload["DocumentSubType"],
        "Comments": comments,
        "DocumentLines": [],
    }
    for line in payload["DocumentLines"]:
        row = dict(line)
        if wtliable:
            row["WTLiable"] = wtliable
        out["DocumentLines"].append(row)
    return out
