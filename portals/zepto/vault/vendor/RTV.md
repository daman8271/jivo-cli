---
title: RTV (Return to Vendor)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, rtv]
status: studied
---

# RTV (Return to Vendor)

The **RTV (Return to Vendor)** section is Zepto's **reverse-logistics surface** — the
goods Zepto sends **back** to JIVO (Jivo Wellness Pvt. Ltd., `manufacturer_id
946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, Manufacturer / STANDARD tier). When a Zepto
fulfilment centre / mother-hub holds vendor stock that is near-expiry, damaged, excess,
or otherwise unsaleable, it raises an **RTV** so the vendor collects it. This section
lets JIVO **list** the RTVs raised against it, read a per-RTV **summary/stat**, drill
into a single RTV's **details / checklist / items**, list and download the associated
**packing slips** and **attachments**, and hand an RTV into the **scheduling** flow
(pickup/dispatch — a write, held out of scope). All calls hit
**`fcc.zepto.co.in`** (the same vendor-reports backend the proven SALES/INVENTORY pulls
use), under two path prefixes: the older `api/v1/rtv/*` and the newer
`vendor/api/v2/rtv/*`. One JWT (header `authorization: <jwt>`, **no** `Bearer` prefix)
authenticates all of them; WAF headers were not enforced at last capture.

The endpoint contracts below were extracted from the vendor micro-frontend code-split
chunk **`captures/js/vendor/3539.64ab07c46b8741b5.js`** — an API-constant map (`S={…}`)
regrouped under a `RETURNS:{…}` object — **not** live captures except where a probe is
noted. The V2 endpoints supersede the V1 listing (`GET_RTV_LISTING_V2` →
`vendor/api/v2/rtv/filter`), while detail/checklist/items are V2-only and packing-slip
/ attachment reads remain on V1.

## SPA route(s)

- **None captured.** The section object in `sections.json` carries `routes: []` — the
  RTV route/page-title is defined in the **root-shell (631)** remote, not in the vendor
  (635) chunk that holds the RTV data module, so the exact `/…` path is not in this
  chunk. RTV is a **vendor-lane** page rendered by the vendor remote (635) against the
  `fcc.zepto.co.in` backend. Live route to confirm via an authenticated capture.

## Backend host(s)

- **`fcc.zepto.co.in`** — the sole host for this section. `api/v1/rtv/*` (legacy) and
  `vendor/api/v2/rtv/*` (current) paths; also serves the `api/v1/grn/user/*` filter
  lists that seed the RTV grid's location/vendor dropdowns.

## API endpoints (READ)

`${e}` = an RTV id (path param), `${t}` = a packing-slip / attachment id. All rows below
are pure reads (list / summary / detail / file-fetch of already-generated content).
Method shown as wired in the chunk; `GET` = confirmed constant binding.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/api/v1/rtv/filter` | RTV listing grid (legacy) — `GET_RTV_LISTING`; superseded by V2 below | READ · probed → **401 Token expired** (documented, expired-token) |
| GET | `/vendor/api/v2/rtv/filter` | RTV listing grid (current) — `GET_RTV_LISTING_V2`, filtered/paged | READ |
| GET | `/api/v1/rtv/listing-stat` | RTV summary / stat tiles for the listing header — `GET_RTV_SUMMARY` | READ |
| GET | `/api/v1/rtv/user/mh-list` | Mother-hub / location filter values for the RTV grid — `EXTERNAL_LOCATION_FILTER_LIST` | READ |
| GET | `/vendor/api/v2/rtv/${e}` | Single RTV detail (header, facility, dates, status) — `getRtvDetailsById` | READ |
| GET | `/vendor/api/v2/rtv/${e}/checklist` | RTV checklist (per-RTV pickup/verification checklist) — `getRtvChecklistById` | READ |
| GET | `/vendor/api/v2/rtv/${e}/items` | Line items in an RTV (SKU × qty × reason) — `getRtvItemsById` | READ |
| GET | `/vendor/api/v1/rtv/${e}/list-packing-slips` | List packing slips generated for an RTV — `getPackingSlipsById` | READ |
| GET | `/vendor/api/v1/rtv/download/${e}/attachments/${t}` | Download an existing RTV attachment file (pre-uploaded) — `downloadRtvAttachment` | READ (file) |

**Notes on filter dropdowns.** The grid's location/vendor filters are seeded by sibling
GRN endpoints referenced in the same const block — `api/v1/grn/user/mh-list`
(`NAL_LOCATION_FILTER_LIST`) and `api/v1/grn/user/vendor-list`
(`EXTERNAL_VENDOR_FILTER_LIST`) — those live in the [[Stock-View-Inventory]] / GRN surface,
not counted among this section's 11 endpoints. The RTV-owned location filter is
`api/v1/rtv/user/mh-list` (row 4 above).

## Out of scope (writes) — never expose in a read-only CLI

| METHOD | Path | Purpose | Why held out |
|---|---|---|---|
| UNKNOWN (write) | `/api/v1/rtv/schedule` | **Schedule an RTV** pickup/dispatch — `SCHEDULE_RTV` | Mutates RTV state (books/commits a pickup). WRITE. |
| UNKNOWN (export/job) | `/vendor/api/v1/rtv/${e}/packing-slips/${t}/job` | Kick off an async **packing-slip file-job** — `getPackingSlipJob`; paired with `downloadPickingSlip:"vendor/file-job/download…"` | Method not confirmed; name + the `file-job` pairing mark it a generation/export job that enqueues work. EXPORT — excluded. |

Both are DOCUMENTED-FROM-BUNDLE ONLY. A strict read-only CLI must never call them; the
already-generated packing slips are readable via `list-packing-slips` +
`download/${e}/attachments/${t}` (READ rows above) instead of triggering the job.

## Live probe (evidence)

- **1 probe fired, read-only GET, then halted** (per the guardrails, stop on first
  401/403). `GET https://fcc.zepto.co.in/api/v1/rtv/filter` with the captured vendor JWT
  returned **`HTTP 401 {"message":"Token expired","code":401}`** — the token
  (`iat 2026-07-12`, `exp 2026-07-13 18:29:59 UTC`) had lapsed 11 days before this run
  (2026-07-23). No 2xx, so **nothing was upgraded to PROVEN**; all endpoints remain
  **documented (not probed)**. Transcript:
  `captures/vendor/rtv-probes.txt`.
- **Auth/base confirmed** by the proven sibling flows on the same host: SALES/INVENTORY
  (`fcc /api/v1/reports*`) and ads (`fcc /ads-bff/api/v1`) work with the identical
  `authorization: <jwt>` header (no `Bearer`), `origin/referer https://brands.zepto.co.in`.
  Re-run the RTV probes with a fresh token to lock down response shapes.
- **Response shapes:** to confirm via live read-only capture. Expected top-level keys
  (from the grid usage): listing → paged rows + total; `listing-stat` → status-count
  tiles; `getRtvDetailsById` → RTV header + facility + dates + status; `items` → SKU
  rows; `list-packing-slips` → slip metadata array.

## What a READ-ONLY CLI would expose (candidate commands)

- `zepto rtv list [--filters … --page … --page_size …]` → `GET /vendor/api/v2/rtv/filter`
  (fall back to `api/v1/rtv/filter`). Pure READ.
- `zepto rtv stats` → `GET /api/v1/rtv/listing-stat`. Pure READ.
- `zepto rtv locations` → `GET /api/v1/rtv/user/mh-list` (filter values). Pure READ.
- `zepto rtv get <rtvId>` → `GET /vendor/api/v2/rtv/<id>`; `zepto rtv items <rtvId>` →
  `…/items`; `zepto rtv checklist <rtvId>` → `…/checklist`. Pure READ.
- `zepto rtv slips <rtvId>` → `GET /vendor/api/v1/rtv/<id>/list-packing-slips`;
  `zepto rtv attachment <rtvId> <attachmentId> [--out FILE]` →
  `GET /vendor/api/v1/rtv/download/<id>/attachments/<t>` (saves the file). Pure READ.
- **Excluded:** scheduling an RTV (`/api/v1/rtv/schedule`) and firing the packing-slip
  `…/job` generation — both writes/exports.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] ·
  [[Read-Only-Guardrails]]
- Upstream / adjacent vendor lane: [[Purchase-Orders]] (inbound demand) ·
  [[ASN]] (advance shipping) · [[Release-Orders-Amendment-Requests]] — RTV is the reverse of the
  inbound goods flow those raise.
- Filter dropdowns and the goods-receipt (GRN) context RTV returns against live in
  [[Stock-View-Inventory]]; RTV-driven debit notes / recoveries surface in
  [[Fulfilled-by-Zepto]] and settle through [[Payments]].
