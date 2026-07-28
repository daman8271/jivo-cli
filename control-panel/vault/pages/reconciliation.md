---
title: Wellness–Mart Reconciliation
route: /inventory/reconciliation/
type: page
endpoints: [inventory-reconciliation-data, inventory-reconciliation-ledgers]
tags: [jivo, control-panel, inventory, reconciliation, accounts]
---
# Wellness–Mart Reconciliation

## Purpose
Reconciles the **inter-company trade between JIVO Mart (the buying/distribution arm) and JIVO Wellness (the manufacturing/selling arm)**. For every Mart purchase order it walks the full document chain **Mart PO → Wellness SO → GRPO → A/P → A/R** and flags chains whose tax-inclusive totals don't match or where documents are missing — so accounts can catch un-booked GRPOs, missing invoices, or value mismatches between the two companies' books. See [[wellness-mart-reconciliation]]. (Grouped under **Accounts** in the sidebar as "Wellness–Mart Recon".)

## What it shows
- **Company segment** — **Oil** / **Beverages** (`schema`; selects which Wellness seller company). Default Oil.
- **From / To** date window (drives both the chains and the ledgers).
- **Summary KPIs** — from `summary`: total chains, **Matched**, **Mismatch**, **Incomplete**, and **mismatch value** (₹ at risk).
- **Status filter** — **Broken** (default, = not matched) / Mismatch / Incomplete / Matched / All.
- **Node filter chips** — PO / SO / GRPO / A/P / A/R.
- **Chains table** — one row per Mart PO: Mart PO, Date, PO Total, SO, GRPO, A/P, A/R, **Status**. Each document cell drills to the underlying doc numbers/dates/amounts.
- **Free-text search** — spans **all** statuses; matches PO, vendor, status, detail, and **any** underlying SO/GRPO/A-P/A-R document number (so you can find a chain from a single invoice number).
- **Ledgers tab** — the BP ledgers behind the chains, pivoted by **ORIGIN** for JIVO Mart and JIVO Wellness, with Debit/Credit/Balance (LC). From [[inventory-reconciliation-ledgers]].
- **Export** — CSV via `/inventory/reconciliation/export/?schema=both&only=<broken|all>&…` (always `schema=both` so cross-company POs reconcile in one sheet; file download, not probed). Ledger tab exports its own CSV client-side.

## Data sources
- [[inventory-reconciliation-data]] — `GET …/api/data/?schema=[&date_from=&date_to=]`: the reconciled PO chains + summary counts.
- [[inventory-reconciliation-ledgers]] — `GET …/api/ledgers/?schema=[&date_from=&date_to=]`: Mart vs Wellness BP ledger pivot by origin.

## Key fields & columns
- **Chain nodes** — **PO** (Mart purchase order) → **SO** (Wellness sales order) → **GRPO** (Mart goods receipt PO) → **A/P** (Mart A/P invoice) → **A/R** (Wellness A/R invoice, the mirror).
- **Status** — **MATCHED** (all nodes present, totals within `tolerance`), **MISMATCH** (all present but totals differ > tolerance), **INCOMPLETE** (a node is missing; `detail` lists which).
- **tolerance** → ₹ threshold under which a total difference is ignored (default 1.0).
- **mismatch_value** → total ₹ across mismatched chains.
- **Ledger origin** → SAP document-type origin code (`PC` = A/P invoice, `PS` = goods-receipt PO, `IN` = A/R invoice…); **Balance (LC)** = Debit − Credit in local currency; cancellations excluded.

## Notes / gotchas
- Read-only. The two sides are separate SAP company DBs (Oil vs Beverages) — the `schema` toggle picks the seller company, but the **export always uses `schema=both`** because a single PO can span Oil + Beverages and would otherwise look mismatched on either toggle.
- "Broken" is the default filter (Mismatch + Incomplete) — the working queue for accounts.
- Partial documents are **summed** before comparison (multiple GRPOs/invoices against one PO reconcile in aggregate).

## Related
- [[wellness-mart-reconciliation]], [[stock-available]], [[customer-master]], [[segments-oils-beverages]], [[OIH]]
