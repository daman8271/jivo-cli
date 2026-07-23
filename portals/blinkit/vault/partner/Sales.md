---
title: Sales
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: studied
---

# Sales

The **Sales** section (route `/app/sales`, nav label "Sales", route enum `Jr.SALES`) is Blinkit's **secondary-sales / sell-out** view for the manufacturer: what actually sold *through* Blinkit to consumers, sliced by item × city (and, in the exported detail, by date). It is the demand-signal counterpart to [[Stock-on-Hand]] (what's sitting in Blinkit warehouses) and to [[PO-Summary]] (what Blinkit ordered from us). For JIVO (entity `1117`, internal `manufacturer_id: 176`) it reports units sold (`qty_sold`) and MRP value per SKU per city. The on-screen grid is a live, paginated aggregate; a bulk **export** button generates a per-date CSV that is queued in [[Report-Requests]] and also emailed. This is the primary feed for JIVO's e-com "Secondary" sales upload lane.

## Subpages & tabs

No sub-tabs were found in the bundle — Sales is a **single table view** with a filter bar and a bulk-export action (contrast with PO, which has PO/Invoices tabs). The section's behaviour is captured by four analytics events in the bundle, which map the whole UX:

| Event (bundle) | Meaning |
|---|---|
| `SALES_VIEWED` | page opened / grid rendered |
| `SALES_FILTER_APPLIED` | **global** filter bar changed (top-of-page date/city/etc.) |
| `SALES_TABLE_FILTER_APPLIED` | **in-table** column filter/sort changed |
| `SALES_BULK_DATA_REQUESTED` | "Export" pressed → async Sales Details report generated (lands in [[Report-Requests]]) |

## Filters & columns (what the table shows)

**Filters**
- **Date range** — the primary, proven filter: body `{"filters":{"created_at__gte":"YYYY-MM-DD","created_at__lte":"YYYY-MM-DD"}}`. Default window used by the official CLI = **1st-of-month → T-1 (IST)** (`defaultSalesRange`), i.e. month-to-date sell-out.
- **Global filter bar** (`SALES_FILTER_APPLIED`) — the top bar shared across sections. City / Category / Item selectors are the likely members; the exact set is *to confirm via live network capture* (the current bundle's grid columns and filter chips are server-driven, not hardcoded label strings).
- **Table filters** (`SALES_TABLE_FILTER_APPLIED`) — per-column sort/filter/search on the rendered grid.

**Columns** — the on-screen grid mirrors the `get-sales-details` JSON, so the data fields are the columns (labels are server-supplied):

| Field | Meaning |
|---|---|
| `item_id` | Blinkit item id (SKU) |
| `item_name` | product name |
| `category` | e.g. "Dry Fruits, Masala & Oil" |
| `city_id` / `city_name` | destination city (e.g. Ghaziabad) |
| `mrp` | MRP value (₹) for the slice |
| `qty_sold` | **units sold** — the core sell-out metric |

The **exported CSV** (bulk report, see below) is richer than the grid — it adds `manufacturer_id`, `manufacturer_name`, and crucially a per-row **`date`** column (true daily granularity), which the on-screen `get-sales-details` aggregate does **not** carry. CSV schema:
`item_id, item_name, manufacturer_id, manufacturer_name, city_id, city_name, category, date, qty_sold, mrp`.

## API endpoints

Base `https://www.partnersbiz.com`, prefix `/v1/`. Auth = header tokens (`token` + `access_token` = `v2::<uuid>`, `x-api-key: fe25a1da-…`, `x-entity-id: 1117`, `x-entity-type: manufacturer`, `service: partnersbiz`, `app_client: partnerbiz-web`). All four below are **proven 200** end-to-end (captures 2026-07-08, `blinkit-cli`).

| METHOD | Path | Purpose | Read / Write |
|---|---|---|---|
| POST | `/v1/get-sales-details/?offset=&limit=` | Direct paginated sell-out JSON = the on-screen grid. Body `{"filters":{created_at__gte,created_at__lte},"order_by":[]}`. Returns `{city_id,item_id,mrp,qty_sold,city_name,item_name,category}` per row (aggregate — **no `date`** col). | **READ** (pure query, no side effects) — the safe primary read for a CLI |
| POST | `/v1/report-requests/` | List the async report queue (body `{}`), newest first; shared by Sales + SOH + Invoices + Bulk-PO. Match your row by `id`, wait for `state=="success"`. | **READ** |
| GET | `/v1/report-requests/download//{id}/` | Mint a presigned S3 `download_url` for a finished report (note the literal double slash; ~15-min expiry, re-call to refresh). | **READ** |
| GET | `<presigned S3 url>` | Fetch the CSV itself — no auth (presigned). | **READ** |
| POST | `/v1/reports/sales-details-excel/` | **Export**: enqueue the async "Sales Details Excel" report for a date window (body `{"filters":{created_at__gte,created_at__lte}}`) → `{"data":{"request_id":N}}`. | **Export — side-effecting** (creates a report-request row + emails the file to `tanuj@jivo.in`). Not a business-data mutation, but it *does* create server state, so a strict read-only CLI should prefer `get-sales-details`. Treat as **OUT-OF-SCOPE for a pure read-only surface**; documented only because it is the official bulk-export path and produces the per-date CSV. |

> No portal-mutating write endpoints (create/edit/delete of POs, invoices, offers, inventory) exist for this section — Sales is inherently read/export only. The manufacturer entity is read-only in practice.

**Current-build note (honest):** the 2026-07-24 `index.js` routes data through a newer gateway `${VendorConsoleEndpoint}seller-hub/api/...` (headers `App_client: partnersbiz-web`, `service: partnersbiz`, `Token`, `x-vendor-id`), and does **not** contain the literal strings `get-sales-details` / `sales-details-excel` (they were direct on `/v1/…` in the 2026-07-08 captures). The `/v1/…` contracts above are still the proven, working endpoints; the equivalent `seller-hub/api` sales path in the newest build is *to confirm via live network capture*.

## Real data seen (evidence)

- **Bulk Sales CSV, live-verified:** report generated over `2026-07-01 → 2026-07-06` → request_id `2693589` → COMPLETE ~12s → presigned S3 → real `.csv`, `binary/octet-stream`, **248 KB, 1,838 data rows**. Example row: `10049199, Jivo Cold Pressed Canola Oil 1 ltr, 176, Jivo Wellness Pvt. Ltd., 10, Ghaziabad, "Dry Fruits, Masala & Oil", 2026-07-05, 47.0, 17625.0`.
- **Direct grid JSON:** `POST /v1/get-sales-details/?offset=0&limit=30` with `{"filters":{"created_at__gte":"2026-06-30","created_at__lte":"2026-07-07"},"order_by":[]}` returns the aggregate item×city sell-out (units + MRP), no date column — verified 200 (capture `05-get-sales-details.txt`).
- **Report queue:** live queue showed 20 rows incl. `type: "Sales Details Excel"` in state `success`, each carrying `comments.filters` (`created_at__gte/__lte`, `manufacturer_id__in:[176]`) and `file_path: sales_csv-<id>.csv`.
- **Email fallback:** every Sales export is also emailed (subject `Sales Detail Report <from> - <to>`) to `tanuj@jivo.in` → an IMAP fallback exists if the API path ever breaks.

## What a READ-ONLY CLI would expose (candidate commands)

- `blinkit sales table [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--offset N] [--limit N] [--json]` — the **pure read**: `POST /v1/get-sales-details/`, prints item×city units + MRP for the window (defaults to MTD → T-1). Zero side effects. This is the recommended read-only surface.
- `blinkit sales pull [--from --to] [--out PATH]` — the export chain (generate → poll → download) that yields the per-**date** CSV (matches `blinkit-cli sales pull`). Flag clearly: this **creates a report-request row + sends an email**, so it is an export with side effects, not a pure read; gate it behind an explicit `--export` opt-in.
- `blinkit reports [--json]` — list the report-request queue (READ), so users can find/re-download an existing Sales report without re-generating.
- `blinkit reports download <id> [--out]` — mint the presigned URL and fetch an already-finished report (READ).
- `blinkit sales verify [--from --to]` — cross-check: compare `get-sales-details` aggregate totals against a downloaded CSV as a data-freshness / integrity check.

## Connections
- Portal: [[Partner-Hub]] · [[00-Blinkit-Atlas]]
- Exports queue in / downloaded via [[Report-Requests]] (shared async report list)
- Demand vs supply: compare against [[Stock-on-Hand]] (inventory snapshot) and [[PO-Summary]] (what Blinkit ordered)
- Performance context: [[Score-Card]] (fill rate, ranks) · [[Assortment]] (which SKUs are listable)
- Money side: [[Invoices]] · [[Payments]] · brand-fund/offers spend in [[Consumer-Offers]]
