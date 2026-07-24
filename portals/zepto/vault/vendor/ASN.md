---
title: ASN (Advance Shipping Notices)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, asn]
status: studied
---

# ASN (Advance Shipping Notices)

The **ASN (Advance Shipping Notice)** section is Zepto's **inbound-dispatch surface** — the
notice JIVO (Jivo Wellness Pvt. Ltd., `manufacturer_id
946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, Manufacturer / STANDARD tier) files to tell Zepto
*"here is the stock I am shipping against your Purchase Order"*. An ASN carries the SKU ×
quantity being dispatched, the source/destination facility, an uploaded vendor invoice,
and a lifecycle (Draft → Created → In-transit → Received/GRN'd → Settled, or Cancelled).
This section lets JIVO **list** its ASNs, read a per-ASN **summary/detail**, drill into an
ASN's **items**, its **GRN info** (what Zepto actually received), its **settlement / DN-CN
info** (debit/credit note reconciliation), and its **attachments** (uploaded invoice/docs);
plus fetch the **CSV templates** used to build an ASN. All the **create / draft / submit /
upload / cancel** verbs — the reason this section exists in the portal — are **writes** and
are held out of scope under the read-only law.

All calls hit **`fcc.zepto.co.in`** (the same vendor-reports backend the proven
SALES/INVENTORY pulls use), under two families: the public REST prefix `api/v1/asn/*`, and
an internal gRPC-web prefix `/grpc/vendor/api/v1/asn/*` (a second "internal ASN" builder,
draft/calculate/submit + OCR). One JWT (header `authorization: <jwt>`, **no** `Bearer`
prefix) authenticates both; WAF headers were not enforced at last capture.

The endpoint contracts below were extracted from the vendor micro-frontend code-split chunk
**`captures/js/vendor/3539.64ab07c46b8741b5.js`** — the same const map (`m={…}` +
`RETURNS/INTERNAL` groups) that holds the RTV/PO modules — **not** live captures except the
probes noted. A live read-only probe run (below) confirmed the token is valid and the ASN
service answers, but no listing endpoint returned 2xx, so **nothing is upgraded to PROVEN**.

## SPA route(s)

- **None captured.** The section object in `sections.json` carries `routes: []`. The ASN
  route/page-title is defined in the **root-shell (631)** remote, not in the vendor (635)
  chunk that holds the ASN data module, so the exact `/…` path is not in this chunk. ASN is
  a **vendor-lane** page rendered by the vendor remote (635) against `fcc.zepto.co.in`. Live
  route to confirm via an authenticated capture (expected sibling of the PO/RTV routes).

## Backend host(s)

- **`fcc.zepto.co.in`** — the sole host. Two path families:
  - `api/v1/asn/*` — public REST (listing, by-id detail/items/grn/settlement/attachments,
    CSV templates, and the create/upload/submit writes).
  - `/grpc/vendor/api/v1/asn/*` — internal gRPC-web "ASN builder" (draft/calculate/submit,
    clone/cancel/status, product-csv, invoice OCR). Method not exposed as a literal verb in
    the chunk (gRPC-web transport); classified by const/path semantics below.
  The grid's location/vendor filter dropdowns are also seeded from `api/v1/asn/user/*`.

## API endpoints (READ)

`${e}` = an ASN id (path param). All rows below are pure reads (list / summary / detail /
file-fetch of already-generated content). Method shown as wired in the chunk; `GET` =
confirmed constant binding. Live-probe caveat on the two listing rows is called out inline.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/api/v1/asn/list` | ASN summary list for the grid — `GET_ASN_SUMMARY_LIST`. **Probed → HTTP 404** "No ASN found for asn number: list": live GET resolves to the by-id route, so the app almost certainly **POSTs a filter body** (the `GET_` prefix is a fetch-verb naming convention, not the HTTP method) — method to confirm | READ · probed → 404 (routed to by-id) |
| GET | `/api/v1/asn/filter` | ASN listing grid (filtered/paged) — `GET_ASN_LISTING`. Same probe result as `list` above (404 "…asn number: filter") → likely **POST + `{filters}`** in the app | READ · probed → 404 (routed to by-id) |
| GET | `/api/v1/asn/${e}` | Single ASN detail (header, facility, dates, status) — `getAsnDetailsById` | READ |
| GET | `/api/v1/asn/${e}/items` | Line items in an ASN (SKU × dispatched qty) — `getAsnItemsById` | READ |
| GET | `/api/v1/asn/${e}/grn-info` | GRN info for an ASN (what Zepto received against it) — `getGrnByAsnId` | READ |
| GET | `/api/v1/asn/${e}/settlement-info` | Debit-note / credit-note settlement reconciliation for an ASN — `getDnCnDetails` | READ |
| GET | `/api/v1/asn/${e}/attachments` | List / fetch an ASN's uploaded documents (invoice, etc.) — `getAsnDocuments` | READ (file) |
| GET | `/api/v1/asn/${e}/cancel` | Fetch cancel-eligibility / cancel context for an ASN — `getCancelAsn` (`get`-prefixed reader; the actual cancel mutation is the internal `/grpc/…/${e}/cancel`, held out of scope) | READ |
| GET | `/api/v1/asn/${e}/csv-details` | CSV template / row details for building this ASN — `getCreateAsnTemplate` | READ (file) |
| GET | `/api/v1/asn/${e}/failure-csv-details` | MRP-cost-sheet failure-rows CSV template for an ASN — `getMrpCostSheetTemplate` | READ (file) |
| GET | `/api/v1/asn/user/mh-list` | Mother-hub / location filter values for the ASN grid — `EXTERNAL_LOCATION_FILTER_LIST`. Probed → plain "404 page not found" (needs the app's `x-proxy-target` routing; not fuzzed) | READ · probed → 404 (proxy-target) |
| GET | `/api/v1/asn/user/vendor-list` | Vendor filter values for the ASN grid — `EXTERNAL_VENDOR_FILTER_LIST`. Same 404-page-not-found as `mh-list` above | READ · probed → 404 (proxy-target) |
| GET (gRPC) | `/grpc/vendor/api/v1/asn/${e}` | Internal ASN detail — `getInternalAsnDetails` | READ |
| GET (gRPC) | `/grpc/vendor/api/v1/asn/${e}/status` | Internal ASN status — `getInternalAsnStatus` | READ |
| GET (gRPC) | `/grpc/vendor/api/v1/asn/${e}/documents` | Internal ASN documents — `getInternalAsnDocuments` | READ |
| GET (gRPC) | `/grpc/vendor/api/v1/asn/${e}/product-csv` | Internal ASN product-CSV template — `getInternalAsnProductCsvTemplate` | READ (file) |
| GET (gRPC) | `/grpc/vendor/api/v1/asn/draft/${e}` | Internal ASN draft details (read a saved draft) — `getInternalAsnDraftDetails` | READ |
| GET (gRPC) | `/grpc/vendor/api/v1/asn/listing` | Internal ASN listing — `INTERNAL_GET_ASN_LISTING` | READ |

**Note on `${e}/cancel` (row 8).** The public `getCancelAsn` GET is a *reader* (`get`-prefixed,
fetches cancel-eligibility/context) — the state-changing cancel is the internal
`/grpc/…/asn/${e}/cancel` verb, which is held out of scope below. Treated conservatively:
because the path contains `cancel` (a deny-listed token) it was **not** probed.

## Out of scope (writes / uploads) — never expose in a read-only CLI

All DOCUMENTED-FROM-BUNDLE ONLY. A strict read-only CLI must never call these — they
create/submit/upload/cancel/OCR-process, i.e. mutate Zepto state. The already-generated
data is readable via the READ rows above (detail / items / grn / attachments) instead.

| METHOD | Path | Purpose | Why held out |
|---|---|---|---|
| POST | `/api/v1/asn/` | **Create an ASN** — `CREATE_ASN` | Creates a new ASN. WRITE. |
| POST | `/api/v1/asn/asn-automation` | **Create ASN by automation** — `CREATE_ASN_BY_AUTOMATION` | Creates ASN(s). WRITE. |
| POST | `/api/v1/asn/create-exceptional-asn` | **Save ASN draft** (exceptional) — `SAVE_ASN_DRAFT` | Persists a draft ASN. WRITE. |
| POST | `/api/v1/asn/failure-submit` | **Submit MRP cost sheet** — `SUBMIT_MRP_COST_SHEET` | Submits corrected cost rows. WRITE. |
| POST | `/api/v1/asn/failure-upload-csv` | **Upload MRP cost sheet** CSV — `UPLOAD_MRP_COST_SHEET` | File upload → server-side ingest. WRITE (upload). |
| POST | `/api/v1/asn/item-details-from-csv` | **Upload ASN qty document** CSV — `UPLOAD_ASN_QTY_DOCUMENT` | File upload → parses item qtys. WRITE (upload). |
| POST | `/api/v1/asn/upload-asn-creation-csv` | **Upload ASN-creation** CSV — `UPLOAD_ASN_CREATION_CSV` | File upload that drives ASN creation. WRITE (upload). |
| POST | `/api/v1/asn/upload-asn-fallback-csv` | **Upload ASN fallback** CSV — `UPLOAD_ASN_FALLBACK_CSV` | File upload. WRITE (upload). |
| POST | `/api/v1/asn/upload-invoice` | **Upload vendor invoice** for an ASN — `UPLOAD_INVOICE` | File upload. WRITE (upload). |
| POST/UNKNOWN (gRPC) | `/grpc/vendor/api/v1/asn/draft` | **Create/save internal ASN draft** — `INTERNAL_DRAFT_ASN` | Persists a draft. WRITE. |
| POST/UNKNOWN (gRPC) | `/grpc/vendor/api/v1/asn/submit` | **Submit internal ASN** — `INTERNAL_SUBMIT_ASN` | Commits the ASN. WRITE. |
| POST/UNKNOWN (gRPC) | `/grpc/vendor/api/v1/asn/calculate` | **Calculate/preview internal ASN** — `INTERNAL_CALCULATE_ASN` | Create-flow compute POST tied to draft building; not a proven pure read (method/side-effect unconfirmed) — excluded conservatively. |
| POST/UNKNOWN (gRPC) | `/grpc/vendor/api/v1/asn/product-csv` | **Upload internal ASN** product CSV — `INTERNAL_UPLOAD_ASN` | File upload. WRITE (upload). |
| POST/UNKNOWN (gRPC) | `/grpc/vendor/api/v1/asn/invoice/ocr` | **Invoice OCR** for internal ASN — `INTERNAL_INVOICE_OCR` | Uploads + OCR-processes an invoice. WRITE. |
| UNKNOWN (gRPC) | `/grpc/vendor/api/v1/asn/${e}/cancel` | **Cancel** an internal ASN — `getInternalAsnCancel` | State-changing cancel (despite `get`-prefixed fn name). WRITE. |
| UNKNOWN (gRPC) | `/grpc/vendor/api/v1/asn/${e}/clone` | **Clone** an internal ASN — `getInternalAsnClone` | Creates a new ASN from an existing one. WRITE. |

## Live probe (evidence)

- **4 read-only GET probes fired (~1/s), then stopped** (cap 8; halted at 4 — no further
  pure-GET reads possible without a valid ASN id, and no 401/403/429/WAF hit). Transcript:
  `captures/vendor/asn-probes.txt`.
- **Token is VALID (no 401)** — the config token (`iat 2026-07-24 …`, `exp 2026-07-24
  18:29:59 UTC`) was live at run time (2026-07-23 20:27 UTC) and the ASN service answered
  with structured JSON. This is a fresher token than the expired one the sibling
  RTV/PO/vendor-reports probes hit (`exp 2026-07-13`), so ASN is the first vendor section to
  confirm the auth actually passes.
- **Listing endpoints are not GET-by-name:** `GET /api/v1/asn/list` and `/api/v1/asn/filter`
  both returned **HTTP 404** `{"success":false,…,"error":{"message":"No ASN found for asn
  number: list|filter"}}` — the server routes `GET /api/v1/asn/{anything}` to the by-id
  handler (`getAsnDetailsById`). So `GET_ASN_SUMMARY_LIST` / `GET_ASN_LISTING` are almost
  certainly invoked as **POST with a `{filters}`/paging body** in the app (the `GET_` const
  prefix = "fetch", not the HTTP verb). Documented, method to confirm.
- **Filter-list endpoints need proxy routing:** `GET /api/v1/asn/user/mh-list` and
  `/user/vendor-list` returned plain **"404 page not found"** (not the ASN-service JSON) —
  they require the app's `x-proxy-target` header (the proven Sales flow sends
  `x-proxy-target: brand-analytics`); the ASN filter-list target was **not** guessed (no
  blind POST/target fuzzing under the read-only law).
- **2xx PROVEN: 0.** All ASN endpoints remain **documented (not proven)**. Auth/base is
  otherwise confirmed by the proven sibling flows on the same host — SALES/INVENTORY
  (`fcc /api/v1/reports*`) and ads (`fcc /ads-bff/api/v1`) with the identical
  `authorization: <jwt>` header (no `Bearer`), `origin/referer https://brands.zepto.co.in`.
- **Response shapes:** to confirm via a live read-only capture with a valid ASN id + the
  correct method/`x-proxy-target`. Expected keys (from grid/detail usage): listing → paged
  rows + total + status counts; `getAsnDetailsById` → ASN header + facility + dates + status;
  `items` → SKU rows; `grn-info` → received-qty rows; `settlement-info` → DN/CN reconciliation;
  `attachments` → document metadata array.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no create/draft/submit/upload/cancel/clone/OCR):

- `zepto asn list [--filters … --page … --page_size …]` → the ASN listing/summary
  (`GET_ASN_LISTING` / `GET_ASN_SUMMARY_LIST`; **send as POST `{filters}` per live evidence,
  method to confirm**). Pure READ.
- `zepto asn get <asnId>` → `GET /api/v1/asn/<id>` (`getAsnDetailsById`);
  `zepto asn items <asnId>` → `…/items`. Pure READ.
- `zepto asn grn <asnId>` → `…/grn-info`; `zepto asn settlement <asnId>` → `…/settlement-info`
  (DN/CN reconciliation). Pure READ.
- `zepto asn attachments <asnId> [--out DIR]` → `…/attachments` (list/fetch already-uploaded
  docs — never the `upload-*` writes). Pure READ (file).
- `zepto asn template <asnId>` → `…/csv-details` (create-template CSV, read-only). Pure READ.
- `zepto asn locations` / `zepto asn vendors` → `…/user/mh-list` / `…/user/vendor-list`
  (filter values; needs the correct `x-proxy-target`). Pure READ.
- **Excluded:** every `create*`/`asn-automation`/`create-exceptional-asn`/`failure-submit`/
  `upload-*` REST write, and the internal gRPC `draft`/`submit`/`calculate`/`product-csv`/
  `invoice/ocr`/`${e}/cancel`/`${e}/clone` verbs — all writes/uploads.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] ·
  [[Read-Only-Guardrails]]
- Vendor lane siblings: [[Purchase-Orders]] (an ASN is filed **against** a PO — the PO note's
  `getAsnByPoId` is the inbound link) · [[Release-Orders-Amendment-Requests]] · [[RTV]] (ASN is the
  forward dispatch; RTV is its reverse). The GRN an ASN is received into and the DN/CN it
  settles through surface in [[Stock-View-Inventory]] and [[Fulfilled-by-Zepto]]; ASN-linked debit
  notes settle in [[Payments]].
