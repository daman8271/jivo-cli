"""ScanContext — everything a run needs to know about SAP, fetched once.

A scan of 50 GRPOs done naively is ~8 queries a row, ~400 process spawns over a
bridge that costs 1-3 s each. The same scan asking set-shaped questions is about
five bulk queries plus one per distinct vendor, branch-month and PO — call it
40-60. That is the whole reason this class exists: it is a cache with a query
plan, not an abstraction.

Every read is a GET. Nothing here can write; the SapCli it is handed is built
with allow_writes=False.
"""

from __future__ import annotations

import collections
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from . import rules
from .sap import SapCli, chunked, odata_str, or_filter

# How many values go into one `X eq 'a' or X eq 'b' …` filter. The Service Layer
# takes long filters, but a URL that grows without limit is how a scan starts
# failing on one company and not another.
CHUNK = 20

# Open A/P drafts have to be fetched with their lines (the Service Layer will not
# $select a sub-field of a collection), which makes this the heaviest read of a
# scan: measured 2026-08-24 on Oil, 1,053 drafts, 40 MB, 90 s at page-size 100.
DRAFT_PAGE_SIZE = 100
GRPO_PAGE_SIZE = 50

AP_DRAFT_FILTER = "DocObjectCode eq 'oPurchaseInvoices' and DocumentStatus eq 'bost_Open'"

VENDOR_SELECT = ("CardCode,CardName,GroupCode,SubjectToWithholdingTax,"
                 "BPWithholdingTaxCollection,Valid,Frozen,CurrentAccountBalance")
POSTED_SELECT = "DocEntry,DocNum,CardCode,DocDate,DocTotal,Cancelled,NumAtCard"


class ScanContext:
    def __init__(self, sap: SapCli, company_db: str | None = None, hana: "HanaSql | None" = None,
                 log=None) -> None:
        self.sap = sap
        self.company_db = company_db or sap.company_db
        self.hana = hana
        self.log = log or (lambda *_a, **_k: None)

        self._branches: dict[int, dict] | None = None
        self._groups: dict[int, str] | None = None
        self._vendors: dict[str, dict] = {}
        self._drafts: list[dict] | None = None
        self._drafts_by_base: dict[int, list[dict]] = {}
        self._drafts_by_ref: dict[str, list[dict]] = {}
        self._posted_by_ref: dict[str, list[dict]] = {}
        self._last_invoices: dict[str, list[dict]] = {}
        self._wt_rates: dict[str, float | None] = {}
        self._series: dict[tuple, rules.SeriesChoice] = {}
        self._nnm1: dict[tuple, list | None] = {}
        self._po_docnums: dict[int, Any] = {}
        self.reads = 0

    # -- masters ---------------------------------------------------------

    def branches(self) -> dict[int, dict]:
        """Every branch, all pages.

        all=True is load-bearing, not tidiness: the Service Layer's default page
        is 20 rows and Mart has exactly 20 BusinessPlaces. Without it Mart looks
        complete and any 21st branch silently becomes "branch N is not in
        BusinessPlaces — no BPL_IDAssignedToInvoice to post under", which reads
        like a data problem at JIVO and is a bug here.
        """
        if self._branches is None:
            rows = self._query("BusinessPlaces", select="BPLID,BPLName,FederalTaxID,Disabled",
                               all=True)
            self._branches = {r["BPLID"]: r for r in rows}
        return self._branches

    def groups(self) -> dict[int, str]:
        if self._groups is None:
            try:
                # 45-47 groups per company, past the 20-row default page: without
                # --all every vendor from the 21st group onwards showed its group
                # CODE instead of its name in column G.
                rows = self._query("BusinessPartnerGroups", select="Code,Name", all=True)
            except Exception as e:                    # a nice-to-have column, never a stop
                self.log(f"  (business partner groups unavailable: {e})")
                rows = []
            self._groups = {r.get("Code"): r.get("Name") for r in rows}
        return self._groups

    def group_name(self, group_code: Any) -> str:
        return self.groups().get(group_code) or (str(group_code) if group_code is not None else "")

    # -- vendors ---------------------------------------------------------

    def prefetch_vendors(self, codes: Iterable[str]) -> None:
        missing = sorted({c for c in codes if c and c not in self._vendors})
        for batch in chunked(missing, CHUNK):
            rows = self._query("BusinessPartners", filter=or_filter("CardCode", batch),
                               select=VENDOR_SELECT, all=True)
            for r in rows:
                self._vendors[r["CardCode"]] = r
        for c in missing:                              # remember the misses too
            self._vendors.setdefault(c, {})

    def vendor(self, code: str) -> dict:
        if code not in self._vendors:
            self.prefetch_vendors([code])
        return self._vendors.get(code) or {}

    # -- the duplicate indexes -------------------------------------------

    def open_ap_drafts(self) -> list[dict]:
        """Every open A/P draft in this company, indexed both ways.

        Fetched once for the whole run. The GRPO-keyed index is the primary
        duplicate check — Accounts keys these in the client the same afternoon,
        and a typo'd vendor reference hides a duplicate from every other test.
        """
        if self._drafts is None:
            self.log("  reading open A/P drafts (the duplicate index) …")
            rows = self._query("Drafts", filter=AP_DRAFT_FILTER, all=True,
                               page_size=DRAFT_PAGE_SIZE)
            self._drafts = rows
            for r in rows:
                for l in r.get("DocumentLines") or []:
                    if l.get("BaseType") == 20 and l.get("BaseEntry") is not None:
                        bucket = self._drafts_by_base.setdefault(l["BaseEntry"], [])
                        if not any(d["DocEntry"] == r["DocEntry"] for d in bucket):
                            bucket.append(r)
                ref = rules.normalize_ref(r.get("NumAtCard"))
                if ref:
                    self._drafts_by_ref.setdefault(ref, []).append(r)
            self.log(f"  {len(rows)} open A/P drafts · {len(self._drafts_by_base)} GRPOs already drafted")
        return self._drafts

    def drafts_by_base(self) -> dict[int, list[dict]]:
        self.open_ap_drafts()
        return self._drafts_by_base

    def drafts_by_ref(self) -> dict[str, list[dict]]:
        self.open_ap_drafts()
        return self._drafts_by_ref

    def prefetch_posted_refs(self, refs: Iterable[str]) -> None:
        """Posted A/P invoices carrying these vendor references, any vendor.

        Any vendor on purpose: the same bill keyed against the wrong card is
        still that bill, and it is the reference the tax authority matches on.

        The INDEX is keyed by rules.normalize_ref, but the QUERY cannot be: the
        Service Layer matches NumAtCard exactly. So both spellings are asked for
        — what the GRPO says and its normalized form — which catches the common
        pair (`.2633100542` on one document, `2633100542` on the other) in both
        directions. It does not catch every variant a human can type (a posted
        `002633100542` is not found by asking for `2633100542`); the GRPO-keyed
        draft check and the within-batch collision check are the belts for that.

        Cancelled is filtered SERVER-side to 'tNO'. Positively: a cancellation
        mirror comes back with no Cancelled key at all, so "not tYES" keeps it.
        """
        wanted: set[str] = set()
        for raw in refs:
            key = rules.normalize_ref(raw)
            if not key or key in self._posted_by_ref:
                continue
            self._posted_by_ref.setdefault(key, [])
            wanted.update(rules.ref_variants(raw))
        seen: set[tuple] = set()
        for batch in chunked(sorted(wanted), CHUNK):
            rows = self._query(
                "PurchaseInvoices",
                filter=f"({or_filter('NumAtCard', batch)}) and Cancelled eq 'tNO'",
                select=POSTED_SELECT, all=True)
            for r in rows:
                key = rules.normalize_ref(r.get("NumAtCard"))
                if not key or (key, r.get("DocEntry")) in seen:
                    continue
                seen.add((key, r.get("DocEntry")))
                self._posted_by_ref.setdefault(key, []).append(r)

    def posted_by_ref(self) -> dict[str, list[dict]]:
        return self._posted_by_ref

    # -- vendor precedent ------------------------------------------------

    def last_invoices(self, card_code: str) -> list[dict]:
        """The vendor's last three posted A/P invoices, full rows.

        Full rows because the decision needs the lines' WTLiable, not just the
        header's WTAmount — a client-keyed invoice can be marked liable and still
        compute zero.
        """
        if card_code not in self._last_invoices:
            self._last_invoices[card_code] = self._query(
                "PurchaseInvoices",
                filter=f"CardCode eq {odata_str(card_code)} and Cancelled eq 'tNO'",
                orderby="DocEntry desc", top=3)
        return self._last_invoices[card_code]

    def subtype_for(self, card_code: str) -> str:
        """How this vendor's invoices are normally sub-typed. Defaults to GST tax invoice."""
        rows = self.last_invoices(card_code)
        kinds = collections.Counter(r["DocumentSubType"] for r in rows if r.get("DocumentSubType"))
        return kinds.most_common(1)[0][0] if kinds else "bod_GSTTaxInvoice"

    def wt_rate(self, wt_code: str | None) -> float | None:
        if not wt_code:
            return None
        if wt_code not in self._wt_rates:
            try:
                rows = self._query("WithholdingTaxCodes", filter=f"WTCode eq {odata_str(wt_code)}")
                self._wt_rates[wt_code] = rows[0].get("Rate") if rows else None
            except Exception as e:
                self.log(f"  (TDS rate for {wt_code} unavailable: {e})")
                self._wt_rates[wt_code] = None
        return self._wt_rates[wt_code]

    # -- numbering series ------------------------------------------------

    def series_for(self, bpl: int, docdate: Any, subtype: str) -> rules.SeriesChoice:
        """The series for one (branch, month, sub-type). Cached per scan.

        Both lookups are month-BOUNDED. Without the upper bound a July posting
        scanned in August votes on August's documents and takes August's series.
        """
        m0, m1 = rules.month_bounds(docdate)
        key = (bpl, m0, subtype)
        if key not in self._series:
            window = f"DocDate ge '{m0}' and DocDate lt '{m1}'"
            branch_and_type = (f"BPL_IDAssignedToInvoice eq {int(bpl)} and "
                               f"DocumentSubType eq {odata_str(subtype)}")
            docs = self._query("PurchaseInvoices", filter=f"{window} and {branch_and_type}",
                               select="DocEntry,Series", orderby="DocEntry desc", top=20)
            docs += self._query("Drafts",
                                filter=f"DocObjectCode eq 'oPurchaseInvoices' and {window} and "
                                       f"{branch_and_type}",
                                select="DocEntry,Series", orderby="DocEntry desc", top=20)
            self._series[key] = rules.pick_series(
                docs, self.nnm1(rules.fy_indicator(docdate), bpl), subtype, bpl=bpl, docdate=docdate)
        return self._series[key]

    def nnm1(self, indicator: str, bpl: int) -> list | None:
        """NNM1 through hana-sql. Optional: None means "could not look", not "empty"."""
        if not self.hana:
            return None
        key = (indicator, bpl)
        if key not in self._nnm1:
            self._nnm1[key] = self.hana.rows(
                f'SELECT "Series","SeriesName","DocSubType" FROM {self.company_db}.NNM1 '
                f"WHERE \"ObjectCode\"='18' AND \"Indicator\"='{indicator}' "
                f'AND "BPLId"={int(bpl)} AND "Locked"=\'N\'')
        return self._nnm1[key]

    # -- base POs --------------------------------------------------------

    def prefetch_po_docnums(self, entries: Iterable[int]) -> None:
        missing = sorted({int(e) for e in entries if e} - set(self._po_docnums))
        for batch in chunked(missing, CHUNK):
            rows = self._query("PurchaseOrders", filter=or_filter("DocEntry", batch, numeric=True),
                               select="DocEntry,DocNum", all=True)
            for r in rows:
                self._po_docnums[r["DocEntry"]] = r.get("DocNum")

    def po_docnums(self, entries: Iterable[int]) -> list:
        out = []
        for e in entries:
            num = self._po_docnums.get(int(e)) if e else None
            if num and num not in out:
                out.append(num)
        return out

    # -- plumbing --------------------------------------------------------

    def _query(self, entity: str, **kw: Any) -> list[dict]:
        self.reads += 1
        return self.sap.query(entity, **kw)


class HanaSql:
    """Optional read-only cross-check through hana-sql. Absent is fine."""

    def __init__(self, repo: Path, env: str | None = None, timeout: int = 25) -> None:
        self.bin = repo / "hana-sql" / "hana-sql"
        self.env = env or os.environ.get("HANA_ENV") or str(repo / "connections" / "hana.env")
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return self.bin.exists()

    def rows(self, sql: str) -> list[list[str]] | None:
        if not self.available:
            return None
        try:
            r = subprocess.run([str(self.bin), "-env", str(self.env), sql],
                               capture_output=True, text=True, timeout=self.timeout)
        except (subprocess.TimeoutExpired, OSError):
            return None
        if r.returncode != 0 or "QUERY ERROR" in r.stdout:
            return None
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        return [l.split("\t") for l in lines[1:]] if len(lines) > 1 else []
