---
title: Stock on Hand
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: studied
---

# Stock on Hand

The **Stock-on-Hand (SOH)** section (SPA route `/app/soh`, page constant `SOH` in the bundle) is the manufacturer's **live inventory snapshot at Blinkit's backend facilities / feeder warehouses** — how many units of each SKU are sitting in Blinkit's own DCs (`backend_inv_qty`) versus fulfilment-facing / darkstore stock (`frontend_inv_qty`) at a point in time. It is the "how much of my product does Blinkit physically hold right now" view, and it pairs with [[Sales]] (sell-through) to compute days-of-cover / stock health. For JIVO this is Jivo Wellness Pvt. Ltd. (`x-entity-id=1117`, `x-entity-type=manufacturer`, internal `manufacturer_id=176`). Unlike Sales, SOH is a **live snapshot with no date window** — you get "as of now", not a time range.

**Honest scope note:** the captured main bundle `captures/partner/js/index.js` (8.4 MB) contains the SOH **route wiring and analytics events** but **not** the SOH page's data-grid component, its column definitions, or its grid-populate fetch call. Like Sales and Assortment, the SOH page is a **code-split lazy chunk that was not captured** — `backend_facility_name`, `frontend_inv_qty`, `backend_inv_qty`, `facility_id` etc. return **0 hits** in `index.js`. What is documented below as verified comes from our own live captures (`ecomcliauto/captures/blinkit/06-soh-request.txt`) and the working `blinkit-cli`, not from reverse-reading the bundle. The on-screen filter names and grid columns are marked "to confirm via live capture" where the bundle can't prove them.

## Subpages & tabs

- **`/app/soh`** — the SOH landing / inventory grid. Confirmed as a first-class route: the page-name resolver maps route segment `"soh"` → constant `Jr.SOH` (`case"soh":return Jr.SOH`), and `Jr.SOH="SOH"`.
- **No sub-routes.** SOH has no detail route (contrast [[PO-Summary]]'s `/app/po-details/:poNumber` or [[Invoices]]' `/app/invoice-details/...`). It is a single flat grid with a filter bar and a bulk-export action.
- Page-level behaviour is proven by three analytics events in the bundle, which is the strongest local evidence of what the page does:
  - `SOH_VIEWED` — page-view (fires on landing on `/app/soh`).
  - `SOH_FILTER_APPLIED` — the page has a **filter bar** (at least one global filter the user applies).
  - `SOH_BULK_DATA_REQUESTED` — the page has a **bulk-data / export action** (the "download the full SOH as a file" button → the async report-request flow below).
- Any in-grid tabs or a facility-picker are **to confirm via live capture** — that config lives in the un-captured page chunk.

## Filters & columns (what the table shows)

**Filter bar:** confirmed to exist (`SOH_FILTER_APPLIED` event) but the **field names are not in the captured bundle**. By analogy to sibling grids and to the exported CSV, the filter is plausibly by **facility / warehouse** and possibly **category or item**, but the exact controls are **to confirm via live network capture** — not invented here.

**Columns:** the on-screen grid column defs are **not in the bundle**. The most reliable evidence of the SOH data shape is the **exported CSV** (live-verified via `soh pull`), whose schema is:

| CSV column | meaning |
|---|---|
| `created_at` | snapshot date/time of the SOH reading |
| `backend_facility_name` | Blinkit backend facility / feeder-warehouse name (e.g. "Goa G2 - Feeder Warehouse") |
| `backend_facility_id` | that facility's Blinkit id (e.g. `4449`) |
| `item_id` | Blinkit item id (e.g. `10143020`) |
| `item_name` | product name (e.g. "Jivo Pomace Olive Oil(Bottle) 1 l - Rs 1049") |
| `backend_inv_qty` | units held in the backend / DC inventory |
| `frontend_inv_qty` | units in front-end / fulfilment-facing inventory |

The on-screen grid almost certainly renders a subset/superset of these same fields (facility, item, backend qty, frontend qty), but the exact rendered columns/labels are **to confirm via live capture**. Note the CSV is keyed **per item × facility** (one row per SKU per warehouse), not per city/date the way [[Sales]] is.

## API endpoints

| METHOD | path | purpose | read?/write? |
|---|---|---|---|
| POST | `/v1/reports/soh-details-excel/` | body `{}` (no date filter — live snapshot). Enqueues the SOH export report; returns `{"data":{"request_id":<id>}}`. | **read-of-inventory export, but side-effecting** — a POST that creates a report-request row **and emails a copy** to the account owner. Do NOT fire in this read-only study. |
| POST | `/v1/report-requests/` | body `{}`. Lists the async report queue newest-first (shared across all report types). Match the row where `id == request_id`; wait for `state=="success"`; `type=="SOH Details Excel"`. | read |
| GET | `/v1/report-requests/download//{id}/` | (literal double slash — that's how the app builds it). Returns `{"data":{"download_url":"<presigned S3, ~15 min expiry>"}}`. | read |
| GET | `<presigned S3 url>` | plain GET, **no auth** — downloads the SOH `.csv`. | read |
| — | SOH grid-populate call (direct JSON for the on-screen table) | populate the SOH grid inline when you open `/app/soh` (the `SOH_VIEWED` render path). **Not present in the captured bundle.** | **read — endpoint: to confirm via live network capture** |
| GET | `/v1/get-entity-tabs/` | returns which sections entity 1117 may see; gates whether the SOH tab renders (401 → force-logout). | read |

Notes:
- **No `/v1/*soh*`, `/v1/*stock*` or `/v1/*inventory*` literal appears anywhere in the captured main bundle** — the SOH generate/list/download paths above are proven from our own captures + `blinkit-cli`, and the *inline grid* fetch is in the un-captured lazy chunk.
- **There is no proven direct-JSON SOH endpoint** analogous to Sales' `POST /v1/get-sales-details/`. If the grid uses one, capture it live; until then the only proven read path is the async export (generate → poll → download).
- **Out of scope (writes):** none observed. SOH is inherently read-only reporting (it reflects Blinkit-side inventory; a manufacturer cannot edit Blinkit's stock counts from this page). No mutating control was found in local material. The one caveat is that `POST /v1/reports/soh-details-excel/` is **side-effecting** (creates a queue row + sends an email) even though it exports read-data — so it must not be fired during a read-only study.

## Real data seen (evidence)

- **Route confirmed live** as a real portal section (page-name resolver `case"soh":return Jr.SOH`, constant `Jr.SOH="SOH"`, and the `SOH_VIEWED`/`SOH_FILTER_APPLIED`/`SOH_BULK_DATA_REQUESTED` analytics triple in `index.js`).
- **Full pull chain live-verified (2026-07-08)**: `soh pull` → generate report **#2693601** → poll `/v1/report-requests/` (`type="SOH Details Excel"`, `state="success"`) → `download//<id>/` → presigned S3 → a real **329-row SOH CSV**.
- **Real row example:** `2026-07-07, Goa G2 - Feeder Warehouse, 4449, 10143020, Jivo Pomace Olive Oil(Bottle) 1 l - Rs 1049, 0, 52` (backend=0, frontend=52 at that facility).
- **Report queue evidence** (live, `/v1/report-requests/`, entity 1117): among the 20 rows, `"SOH Details Excel"` is one of the four observed types (with Invoices Excel / Bulk PO Excel / Sales Details Excel) — confirming SOH exports flow through the same shared [[Report-Requests]] queue.
- **Side effect (verified):** each SOH generate also **emails** the report to the account owner (`tanuj@jivo.in`) — an IMAP fallback exists if the API ever breaks, but it also means the generate call is not truly side-effect-free.
- **Existing tooling:** `ecomcliauto/clis/blinkit-cli` implements this as Flow 6 — `client.go:GenerateSOH()` → `POST /v1/reports/soh-details-excel/` body `{}`; `main.go:cmdSOHPull` writes `blinkit-soh-<today>.csv`. Feeds the Upload Hub · Blinkit · **Inventory** dataset (upload asks for a snapshot "upload date" = today).

## What a READ-ONLY CLI would expose (candidate commands)

The pull path already exists in `blinkit-cli`; a strictly read-only surface (no report-generate side effect) would be:

- `soh queue [--json]` — list the report-request queue filtered to `type="SOH Details Excel"` (pure read of `POST /v1/report-requests/`); shows the latest already-generated SOH snapshots without creating a new one.
- `soh download --id <request_id> [--out PATH]` — resolve `download//{id}/` → presigned S3 → save the CSV of an **already-completed** SOH report (pure read).
- `soh latest [--out PATH]` — convenience: pick the newest successful `SOH Details Excel` row from the queue and download it (no generate).
- `soh grid [--facility <id>] [--json]` — dump the on-screen inventory grid **once the direct grid endpoint is captured live** (currently: endpoint to confirm).
- `soh facilities` — enumerate the `backend_facility_id/name` values seen in the latest snapshot (derived read from the CSV).
- `soh doctor` — verify `/v1/get-entity-tabs/` grants the SOH tab for entity 1117 before any call.

Explicitly **excluded / flagged:** `soh pull` (the existing generate→poll→download) is **not** in the read-only set because its first step `POST /v1/reports/soh-details-excel/` creates a queue row and emails a copy — that's a side-effecting action, out of scope for a pure read study even though the payload it returns is read-data.

## Connections

- Portal shell & nav: [[Partner-Hub]] · index: [[00-Blinkit-Atlas]]
- Pairs with [[Sales]] — SOH (stock held) ÷ Sales run-rate = days-of-cover / stock-out risk.
- Governed by [[Assortment]] — SOH ≈ *assortment ∩ has-inventory*; only listed SKUs can carry stock.
- Feeds/relates to [[PO-Summary]] — low SOH at a facility is what a replenishment PO is meant to refill.
- Shares the async export queue with [[Report-Requests]], [[Sales]], [[Invoices]] (all use `POST /v1/report-requests/` + `download//{id}/`).
