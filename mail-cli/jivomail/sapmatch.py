"""Look a bill up in SAP by asking the sapb1 CLI — read only.

Only `sapb1 query` is ever invoked. The write verbs (draft/post/patch/delete)
are not reachable from this module, and a guard test asserts that.

Why shell out instead of talking to the Service Layer directly: sapb1 already
owns the session handling, the company-DB switch and the field quirks, and it
reads its own .env. Re-implementing that here would mean two clients to keep
correct.
"""
from __future__ import annotations

import os

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .config import repo_root

COMPANIES = {
    "oil": "JIVO_OIL_HANADB",
    "mart": "JIVO_MART_HANADB",
    "beverages": "JIVO_BEVERAGES_HANADB",
    "bev": "JIVO_BEVERAGES_HANADB",
}

FORBIDDEN_SAPB1_VERBS = frozenset({"draft", "post", "patch", "delete"})

# Where a vendor reference can legitimately turn up.
LOOKUP_TARGETS = (
    ("PurchaseInvoices", "posted A/P invoice"),
    ("Drafts", "draft"),
    ("PurchaseCreditNotes", "posted A/P credit note"),
)


class SapUnavailable(RuntimeError):
    pass


def sapb1_dir() -> Path:
    """sapb1 reads its .env from the working directory, so we always run it there.

    The two platforms keep the binary in different places, exactly as CLAUDE.md
    documents: Windows operators run sap-b1\\accounts-kit\\sapb1.exe with the .env
    beside it, Mac/Linux run sap-b1/cli/sapb1. Picking the wrong one is not a
    "not found" error — on Windows the tracked Mac binary IS present and simply
    fails to execute, which is what `jmail doctor` reported on DESKTOP-EQ55Q8H
    on 2026-08-25. Resolve by which one is actually runnable here.
    """
    root = repo_root() / "sap-b1"
    for candidate in _sapb1_candidates(root):
        if candidate.is_file():
            return candidate.parent
    return root / ("accounts-kit" if os.name == "nt" else "cli")


def _sapb1_candidates(root: Path):
    if os.name == "nt":
        yield root / "accounts-kit" / "sapb1.exe"
        yield root / "cli" / "sapb1.exe"
    else:
        yield root / "cli" / "sapb1"
        yield root / "accounts-kit" / "sapb1"


def sapb1_bin() -> Path:
    return sapb1_dir() / ("sapb1.exe" if os.name == "nt" else "sapb1")


def company_db(name: str | None) -> str | None:
    if not name:
        return None
    key = name.strip().lower()
    if key in COMPANIES:
        return COMPANIES[key]
    return name  # already a DB name


def odata_str(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def query(entity: str, *, filt: str, select: str, company: str | None = None,
          top: int = 10, timeout: int = 120) -> list[dict]:
    binary = sapb1_bin()
    if not binary.is_file():
        raise SapUnavailable(f"sapb1 not found at {binary}")
    cmd = [str(binary), "query", entity, "--filter", filt, "--select", select,
           "--top", str(top), "--json"]
    db = company_db(company)
    if db:
        cmd += ["--company", db]
    res = subprocess.run(cmd, cwd=str(sapb1_dir()), capture_output=True,
                         text=True, timeout=timeout)
    if res.returncode != 0:
        raise SapUnavailable((res.stderr or res.stdout).strip()[:300])
    body = (res.stdout or "").strip()
    if not body:
        return []
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else [data]


@dataclass
class Hit:
    entity: str
    kind: str
    ref: str
    doc_entry: int | None
    doc_num: int | None
    card_code: str
    card_name: str
    doc_date: str
    doc_total: float | None
    vat_sum: float | None
    wt_amount: float | None
    cancelled: str

    @property
    def gross_of_tds(self) -> float | None:
        """SAP's DocTotal is net of withholding; a vendor's paper is not."""
        if self.doc_total is None:
            return None
        return self.doc_total + (self.wt_amount or 0.0)


@dataclass
class MatchResult:
    verdict: str                      # IN_SAP_POSTED | IN_SAP_DRAFT | NOT_IN_SAP | SAP_ERROR
    matched_ref: str | None = None
    hits: list[Hit] = field(default_factory=list)
    amount_note: str = ""
    error: str = ""
    tried: int = 0


SELECT_FIELDS = ("DocEntry,DocNum,CardCode,CardName,NumAtCard,DocDate,TaxDate,"
                 "DocTotal,VatSum,WTAmount,Cancelled")


def _to_hit(entity: str, kind: str, row: dict) -> Hit:
    return Hit(
        entity=entity, kind=kind, ref=str(row.get("NumAtCard") or ""),
        doc_entry=row.get("DocEntry"), doc_num=row.get("DocNum"),
        card_code=str(row.get("CardCode") or ""), card_name=str(row.get("CardName") or ""),
        doc_date=str(row.get("DocDate") or "")[:10],
        doc_total=row.get("DocTotal"), vat_sum=row.get("VatSum"),
        wt_amount=row.get("WTAmount"), cancelled=str(row.get("Cancelled") or ""),
    )


def lookup_ref(ref: str, company: str | None = None) -> list[Hit]:
    """Exact NumAtCard match across posted A/P, drafts and credit notes."""
    hits: list[Hit] = []
    for entity, kind in LOOKUP_TARGETS:
        try:
            rows = query(entity, filt=f"NumAtCard eq {odata_str(ref)}",
                         select=SELECT_FIELDS, company=company, top=10)
        except SapUnavailable:
            continue
        hits.extend(_to_hit(entity, kind, r) for r in rows)
    return hits


def amount_reconciles(paper_total: float | None, hit: Hit, tol: float = 1.0) -> bool:
    """True if the paper agrees with SAP, before or after adding TDS back."""
    if paper_total is None or hit.doc_total is None:
        return False
    if abs(hit.doc_total - paper_total) <= tol:
        return True
    gross = hit.gross_of_tds
    return gross is not None and abs(gross - paper_total) <= tol


def match_bill(refs: list[str], grand_total: float | None, company: str | None = None,
               max_candidates: int = 12) -> MatchResult:
    """Try every candidate reference and PREFER the one whose amount reconciles.

    Stopping at the first ref SAP happens to recognise is wrong: a bill carries
    many number-like tokens, and one of them can collide with an unrelated
    document's NumAtCard. Amount agreement is what turns a coincidence into a
    match, so a ref-only hit is reported as REF_MATCH_AMOUNT_DIFFERS, never as
    "this bill is in SAP".
    """
    weak: list[tuple[str, list[Hit]]] = []
    tried = 0
    for ref in refs[:max_candidates]:
        tried += 1
        try:
            hits = lookup_ref(ref, company=company)
        except SapUnavailable as exc:
            return MatchResult(verdict="SAP_ERROR", error=str(exc), tried=tried)
        if not hits:
            continue
        live = [h for h in hits if h.cancelled != "tYES"] or hits
        if grand_total is None or any(amount_reconciles(grand_total, h) for h in live):
            good = [h for h in live if amount_reconciles(grand_total, h)] or live
            posted = [h for h in good if h.entity != "Drafts"]
            return MatchResult(
                verdict="IN_SAP_POSTED" if posted else "IN_SAP_DRAFT",
                matched_ref=ref, hits=good,
                amount_note=compare_amounts(grand_total, good), tried=tried)
        weak.append((ref, live))

    if weak:
        ref, live = weak[0]
        return MatchResult(verdict="REF_MATCH_AMOUNT_DIFFERS", matched_ref=ref, hits=live,
                           amount_note=compare_amounts(grand_total, live), tried=tried)
    return MatchResult(verdict="NOT_IN_SAP", tried=tried)


def compare_amounts(paper_total: float | None, hits: list[Hit]) -> str:
    if paper_total is None or not hits:
        return ""
    h = hits[0]
    if h.doc_total is None:
        return ""
    if abs(h.doc_total - paper_total) < 1.0:
        return f"amount matches ({paper_total:,.2f})"
    gross = h.gross_of_tds
    if gross is not None and abs(gross - paper_total) < 1.0:
        return (f"amount matches once TDS is added back "
                f"(SAP {h.doc_total:,.2f} + TDS {h.wt_amount or 0:,.2f} = {gross:,.2f})")
    delta = (h.doc_total or 0) - paper_total
    return (f"AMOUNT DIFFERS: paper {paper_total:,.2f} vs SAP {h.doc_total:,.2f} "
            f"(delta {delta:,.2f}) — likely a coincidental reference collision, not this bill")
