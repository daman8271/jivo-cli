---
title: Factory endpoint × company sweep — findings
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: research
tags: [factory, sweep, endpoints, jivo-mart, jivo-oil, jivo-beverages]
---

# Endpoint × company sweep — findings (as of 2026-07-19)

Read-only GET sweep of all 210 candidate endpoints (`endpoints.txt`) × 3 `Company-Code` values, 25 auth/action paths skipped by law, `/barcode/scan/history/` probed separately (false skip). Evidence: `company-matrix.tsv` (185 rows × 3 companies). Method: `sweep_companies.py` (page_size=1, 4 workers, throttled). Feeds Phase 3 of [[FACTORY_CLI_PLAN]].

## Headlines

- **The endpoint surface is uniform across companies**: JIVO_MART **155** live · JIVO_OIL **156** · JIVO_BEVERAGES **155**. The *data* differs, not the API.
- **46 endpoints SHARED** (byte-identical across all 3 codes — campus infrastructure: gate, vehicles, drivers, accounts…), **109 company-scoped**.
- **Exactly one company-exclusive endpoint:** `/barcode/production-release-oil/` — 200 only under `JIVO_OIL` (503 for Mart/Beverages).
- **Company character** (scoped counts, as of 2026-07-19): **Oil is the heavyweight** — 247,462 barcode print-history rows, 181,401 boxes, 52,687 scans, 3,709 pallets, 2,261 intercompany transfers. **Mart**: 48,441 scans (dispatch arm). **Beverages is nascent but real** — 653 notifications, 108 scans, 23 prints, 20 boxes, 10 pallets.

## Spec gaps → add in Phase 3 (live but missing from `spec.yaml`)

1. `/barcode/dispatch/sessions/` (paginated_list; Oil 128)
2. `/barcode/dispatch/sessions/from-bill/` (paginated_list)
3. `/barcode/intercompany/transfers/` (paginated_list; Oil 2,261)
4. `/barcode/production-release-oil/` (**JIVO_OIL only**; 503 elsewhere — CLI must tolerate)

## Write surface confirmed OUT (405 on GET — POST-only routes, excluded by [[READ_ONLY_LAW]])

`/ai/assistant/chat/` · `/barcode/dispatch/bills/lookup/` · `/barcode/repack/` · `/barcode/transfers/box/` · `/dispatch/transporter-invoices/preview/` · `/production-execution/machine-checklists/bulk/` · `/quality-control/material-types/link-sap-item/` · `/warehouse/stock/check/`

## Dead paths (404 for all companies)

`/maintenance/spares/stock/` and the whole `/production-planning/*` family (7 paths) — the UI declares Production-Planning routes but the API prefix is absent (feature-flagged or renamed upstream). Production **execution** endpoints are live.

## CLI implications ([[FACTORY_CLI_PLAN]] Phase 3)

- `Company-Code` must be a runtime parameter (`--company` / `JIVO_FACTORY_COMPANY`, default `JIVO_MART`) — same 150+ commands serve all three companies.
- Add the 4 gap endpoints; keep `/production-planning/*` out until it exists; document the 46 SHARED endpoints as company-agnostic in help text.
- `/barcode/production-release-oil/` returns 503 for non-Oil companies — surface a clear error, not a retry loop.

---
Linked: [[FACTORY_CLI_PLAN]] · [[READ_ONLY_LAW]] · [[FACTORY_MAP]]
