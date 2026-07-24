---
title: Fulfilled-by-Zepto (Rebates, Debit Notes & Packaging)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, fbz-fulfillment]
status: studied
---

# Fulfilled-by-Zepto (Rebates, Debit Notes & Packaging)

The **Fulfilled-by-Zepto (FBZ)** section is the money-and-materials backend of the FBZ programme, where Zepto fulfils on JIVO's behalf (Jivo Wellness Pvt. Ltd., Manufacturer, STANDARD tier, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, login `ecom1@jivo.in`). It bundles three related surfaces: (1) **Rebates** — the FBZ rebate portal where per-vendor rebate margins are viewed, reconciled against a rebate CSV, and approved/rejected; (2) **Vendor Debit / Credit Notes (DN/CN)** — the debit-note review queue where Zepto raises DNs against the vendor, JIVO downloads the DN copy + working copy, and (single or batch) uploads working files, then Zepto approves/rejects; and (3) **Packaging Management** — the bag-barcode surface used to configure, preview, list, confirm and download packaging (bag) barcodes. From JIVO's read-only vantage this is where it **inspects** rebate margins, DN review rows and packaging-barcode records — every accept/reject/upload/confirm verb is a write held out of scope.

Endpoint contracts were read out of the vendor remote (module-federation remote 635) code-split chunk `captures/js/vendor/3539.64ab07c46b8741b5.js` — the API-constant maps (`GET_ALL_FBZ_REBATE`, `GET_DN_CN_REVIEW_LISTING`, `Se/Re/Oe/ve/me` packaging consts, …) plus the `` e=>`${n.sx}api/v1/fbz/...` `` id-templated bindings — not live captures (the only JWT on disk is expired; see evidence).

**Backends — corrected from the bundle.** The section's rebate + debit-note const map builds URLs as `` `${n.sx}api/v1/fbz/...` `` where the getter map `{…,sx:()=>b,…,Qw:()=>P,…}` resolves `b = "https://financenew.zepto.co.in/"` and `P = "https://scpfin.zepto.co.in/"`. So the **FBZ rebate + vendor-debit-note endpoints live on `financenew.zepto.co.in`** (the finance/receivables/ledger backend), **not** `fcc.zepto.co.in`. The **packaging bag-barcode** consts are bare strings on the default vendor host **`fcc.zepto.co.in`** (same host as PO/payment/reports). Both hosts were live-probe-confirmed at the route level (401 auth failure, not 404) — see the probe note below. All hosts take the single JWT in the `authorization` header (no `Bearer` prefix) from [[Auth-and-Access]].

## Subpages & tabs

**FBZ shell** — `/fbz` (+ `/vendor/fbz` alias)
- Landing hub linking the three FBZ surfaces below.

**Rebate portal** — `/fbz/rebate` (+ `/vendor/fbz/rebate`)
- Main rebate listing (`GET_ALL_FBZ_REBATE` = `api/v1/fbz/rebate/view-rebate-portal`) — per-vendor rebate rows.
- Vendor-code filter (`GET_FBZ_REBATE_VENDOR_CODES` = `api/v1/fbz/rebate/fetch-all-vendor-codes`) and rebate-margin details (`GET_REBATE_MARGIN_DETAILS` = `api/v1/fbz/rebate/fetch-rebate-margin-details`).
- Per-vendor **rebate CSV download** (`downloadRebateCsvFile` = `api/v1/fbz/rebate/{vendorCode}/download-rebate-csv`), blank **template download** (`GET_FBZ_REBATE_TEMPLATE` = `api/v1/fbz/rebate/template-download`), and a **report listing** (`DOWNLOAD_REPORT` = `api/v1/fbz/rebate/fetch-reports`).
- **Upload rebate CSV** (`UPLOAD_FBZ_REBATE`) and **approve/reject rebate** (`approveOrRejectRebate` = `.../{vendorCode}/update-rebate-status`) — mutating; out of scope.

**Upload surface** — `/fbz/upload` (+ `/vendor/fbz/upload`)
- The rebate/DN CSV upload entry point (feeds `upload-rebate-csv` / DN batch-upload — writes, out of scope).

**Vendor DN/CN review** — `/fbz/vendor` (+ `/vendor/fbz/vendor`, and per-vendor `/vendor/fbz/vendor/:vendorCode`)
- DN/CN review listing (`GET_DN_CN_REVIEW_LISTING` = `api/v1/fbz/vendor-debit-note/filter`) with a status config (`GET_DN_CN_REVIEW_STATUS` = `.../status-config`).
- Per-DN detail (`getDNCNReviewDetails` = `api/v1/fbz/vendor-debit-note/{id}`), the DN-by-ASN lookup (`getRequstedDebitNote` = `.../asn/{id}`).
- **DN copy** + **working DN copy** downloads (`downloadDNCopy` = `.../{id}/dn-copy/download`, `downloadDNWorkingFile` = `.../{id}/working-dn-copy/download`) and the blank upload **template** (`DOWNLOAD_TEMPLATE_FILE` = `.../upload-template`).
- **Batch-upload** views: listing (`GET_DN_BATCH_UPLOAD_LISTING` = `.../batch-upload/list`), a batch row (`getDNUploadDetails` = `.../batch-upload/{id}`), its items (`getAllDNListing` = `.../batch-upload/{id}/items`), and the batch file download (`DOWNLOAD_DN_BATCH_FILE` = `.../batch-upload/file`).
- **Upload / approve / reject / update / batch-upload / cancel** DN verbs — mutating; out of scope.

**Packaging Management** — `/packaging-management` (+ `/vendor/packaging-management`)
- Bag-barcode **config** (`Se` = `api/v1/packaging/bag-barcode/config`), **list** (`ve` = `.../list`), **preview** (`me` = `.../preview`), and **download** (`Oe` = `.../download`).
- Bag-barcode **confirm** (`Re` = `.../confirm`) — commits a barcode; mutating, out of scope.

## Filters & columns (what the grids show)

The rebate grid is keyed by **vendor code** (dropdown from `fetch-all-vendor-codes`) with per-vendor rebate-margin rows (`fetch-rebate-margin-details`). The DN/CN review grid is a filtered listing (`vendor-debit-note/filter`) whose status set is served by `status-config`; each row exposes a DN copy, a working DN copy and (for batch loads) a batch-upload detail + items drill-down. The packaging grid lists bag-barcode records (`bag-barcode/list`) with a `config` lookup for options and a `preview` render before `confirm`. Exact column arrays and status enums render client-side in `3539.…js`; a logged-in grid capture is still owed (JWT expired at capture time).

## API endpoints

Bases: **`https://financenew.zepto.co.in/`** for `api/v1/fbz/rebate/*` and `api/v1/fbz/vendor-debit-note/*` (the bundle's `n.sx` base); **`https://fcc.zepto.co.in/`** for `api/v1/packaging/bag-barcode/*` (bare-string consts on the default vendor host). `{id}` / `{vendorCode}` = a path parameter the bundle wires as `` e=>`${n.sx}api/v1/fbz/...${e}...` ``. Auth = `authorization: <jwt>` (no `Bearer`), `accept: application/json`; WAF headers not enforced as of last capture. All rows below are reads (no state change); "READ (file)" returns a document/CSV/template blob.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `financenew · /api/v1/fbz/rebate/view-rebate-portal` | Main FBZ rebate listing (`GET_ALL_FBZ_REBATE`) | READ |
| GET | `financenew · /api/v1/fbz/rebate/fetch-all-vendor-codes` | Rebate vendor-code filter values (`GET_FBZ_REBATE_VENDOR_CODES`) — probed → 401 | READ |
| GET | `financenew · /api/v1/fbz/rebate/fetch-rebate-margin-details` | Per-vendor rebate-margin details (`GET_REBATE_MARGIN_DETAILS`) | READ |
| GET | `financenew · /api/v1/fbz/rebate/fetch-reports` | Rebate report listing (`DOWNLOAD_REPORT`) | READ |
| GET | `financenew · /api/v1/fbz/rebate/{vendorCode}/download-rebate-csv` | Per-vendor rebate CSV download (`downloadRebateCsvFile`) | READ (file) |
| GET | `financenew · /api/v1/fbz/rebate/template-download` | Blank rebate-upload template (`GET_FBZ_REBATE_TEMPLATE`) | READ (file) |
| GET | `financenew · /api/v1/fbz/vendor-debit-note/filter` | DN/CN review listing (`GET_DN_CN_REVIEW_LISTING`) | READ |
| GET | `financenew · /api/v1/fbz/vendor-debit-note/status-config` | DN/CN review status config (`GET_DN_CN_REVIEW_STATUS`) | READ |
| GET | `financenew · /api/v1/fbz/vendor-debit-note/{id}` | Single DN/CN detail (`getDNCNReviewDetails`) | READ |
| GET | `financenew · /api/v1/fbz/vendor-debit-note/asn/{id}` | DN requested against an ASN (`getRequstedDebitNote`) | READ |
| GET | `financenew · /api/v1/fbz/vendor-debit-note/{id}/dn-copy/download` | Download the DN copy (`downloadDNCopy`) | READ (file) |
| GET | `financenew · /api/v1/fbz/vendor-debit-note/{id}/working-dn-copy/download` | Download the working DN copy (`downloadDNWorkingFile`) | READ (file) |
| GET | `financenew · /api/v1/fbz/vendor-debit-note/upload-template` | Blank DN-upload template (`DOWNLOAD_TEMPLATE_FILE`) | READ (file) |
| GET | `financenew · /api/v1/fbz/vendor-debit-note/batch-upload/list` | DN batch-upload listing (`GET_DN_BATCH_UPLOAD_LISTING`) | READ |
| GET | `financenew · /api/v1/fbz/vendor-debit-note/batch-upload/{id}` | Single DN batch-upload row (`getDNUploadDetails`) | READ |
| GET | `financenew · /api/v1/fbz/vendor-debit-note/batch-upload/{id}/items` | Items in a DN batch upload (`getAllDNListing`) | READ |
| GET | `financenew · /api/v1/fbz/vendor-debit-note/batch-upload/file` | Download a DN batch file (`DOWNLOAD_DN_BATCH_FILE`) | READ (file) |
| GET | `fcc · /api/v1/packaging/bag-barcode/config` | Bag-barcode config/options (`Se`) | READ |
| GET | `fcc · /api/v1/packaging/bag-barcode/list` | Bag-barcode record listing (`ve`) — probed → 401 | READ |
| GET | `fcc · /api/v1/packaging/bag-barcode/preview` | Bag-barcode preview render before confirm (`me`; method to confirm, no commit) | READ |
| GET | `fcc · /api/v1/packaging/bag-barcode/download` | Download bag-barcode (label/file) (`Oe`) | READ (file) |

> Probe status: `GET financenew/api/v1/fbz/rebate/fetch-all-vendor-codes` → **HTTP 401 `{"code":"UNAUTHORIZED"}`** and `GET fcc/api/v1/packaging/bag-barcode/list` → **HTTP 401 `{"message":"Token expired"}`** (both route-matched; a wrong-host warm-up on fcc returned 404 `no Route matched`, which is what pinned rebate to financenew). Halted per guardrails. **0 PROVEN**; all 21 reads remain **documented (not probed)**. Transcript: `captures/vendor/fbz-fulfillment-probes.txt`.

**Out of scope (writes) — documented from the bundle only, never called by a read-only CLI:**

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST* | `financenew · /api/v1/fbz/rebate/{vendorCode}/update-rebate-status` | Approve/reject a rebate (`approveOrRejectRebate`) | WRITE |
| POST* | `financenew · /api/v1/fbz/rebate/upload-rebate-csv` | Upload the reconciled rebate CSV (`UPLOAD_FBZ_REBATE`) | WRITE (upload) |
| POST* | `financenew · /api/v1/fbz/vendor-debit-note/{id}/dn-copy/upload` | Upload a DN copy (`uploadDNFile`) | WRITE (upload) |
| POST* | `financenew · /api/v1/fbz/vendor-debit-note/{id}/working-dn-copy/upload` | Upload a working DN copy (`uploadDNWorkingCopy`) | WRITE (upload) |
| POST* | `financenew · /api/v1/fbz/vendor-debit-note/approve` | Accept a debit note (`POST_ACCEPT_DN`) | WRITE |
| POST* | `financenew · /api/v1/fbz/vendor-debit-note/reject` | Reject a debit note (`POST_REJECT_DN`) | WRITE |
| POST* | `financenew · /api/v1/fbz/vendor-debit-note/update` | Update / upload a debit note (`UPLOAD_DN`) | WRITE |
| POST* | `financenew · /api/v1/fbz/vendor-debit-note/batch-upload` | Batch-upload debit notes (`UPLOAD_DN_BATCH`) | WRITE (upload) |
| POST* | `financenew · /api/v1/fbz/vendor-debit-note/batch-upload/cancel` | Cancel a DN batch upload (`POST_CANCEL_BATCH`) | WRITE |
| POST* | `fcc · /api/v1/packaging/bag-barcode/confirm` | Confirm/commit a bag-barcode (`Re`) | WRITE |

\* method not literally observed in the bundle (constant is a bare path string or an id-template, not bound to `doHttpGet`); verb inferred from the mutating action name. Treated as WRITE and excluded regardless. Note: `download-rebate-csv`, `template-download`, `upload-template`, `dn-copy/download`, `working-dn-copy/download` and `batch-upload/file` are all file **downloads** of *existing* documents (READ (file) above); the `upload-*` verbs and `confirm` are the actual state-changers held out of scope here.

## Real data seen (evidence)

- **Endpoint set** extracted from the vendor remote (module-federation remote 635) chunk `captures/js/vendor/3539.64ab07c46b8741b5.js` — the `GET_ALL_FBZ_REBATE` / `GET_DN_CN_REVIEW_LISTING` const maps, the `` e=>`${n.sx}api/v1/fbz/...` `` id-templated bindings, and the packaging `Se/Re/Oe/ve/me` bare-string consts.
- **Backend corrected via the bundle:** the same chunk defines the getter map `{…,sx:()=>b,…,Qw:()=>P,…}` with `b = "https://financenew.zepto.co.in/"` and `P = "https://scpfin.zepto.co.in/"`. So `n.sx` (rebate + DN) = **financenew.zepto.co.in**, not the `fcc.zepto.co.in` listed in `sections.json`. Packaging bag-barcode consts carry no `n.sx` prefix → default vendor host **fcc.zepto.co.in**.
- **Live probe (read-only, 2026-07-24):** a warm-up `GET fcc/api/v1/fbz/rebate/fetch-all-vendor-codes` → **404 `no Route matched`** (Kong; wrong host), then `GET financenew/api/v1/fbz/rebate/fetch-all-vendor-codes` → **401 `UNAUTHORIZED`** (route matched, token expired) and `GET fcc/api/v1/packaging/bag-barcode/list` → **401 `Token expired`** (route matched). This pins the two hosts and confirms the auth model is live; only the JWT (`exp` 2026-07-13 18:29:59 UTC) is stale. Same expired-token state as the [[Purchase-Orders]], [[Payments]], [[Invoicing]] and [[RTV]] probes. Nothing upgraded to PROVEN.
- **No `captures/vendor/*.json` response body** exists for any FBZ/packaging endpoint yet — exact filter keys, rebate-margin columns, DN status enums and bag-barcode record shape want a live (read-only) capture once a valid token is available.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no upload/approve/reject/confirm writes):
- `zepto fbz rebate list` → `financenew /api/v1/fbz/rebate/view-rebate-portal`; `zepto fbz rebate vendors` → `.../fetch-all-vendor-codes`; `zepto fbz rebate margins` → `.../fetch-rebate-margin-details`; `zepto fbz rebate reports` → `.../fetch-reports`.
- `zepto fbz rebate csv <vendorCode>` → `.../{vendorCode}/download-rebate-csv` (saves CSV); `zepto fbz rebate template` → `.../template-download`.
- `zepto fbz dn list` → `financenew /api/v1/fbz/vendor-debit-note/filter`; `zepto fbz dn status-config` → `.../status-config`; `zepto fbz dn get <id>` → `.../{id}`; `zepto fbz dn by-asn <asnId>` → `.../asn/{id}`.
- `zepto fbz dn copy <id>` → `.../{id}/dn-copy/download`; `zepto fbz dn working-copy <id>` → `.../{id}/working-dn-copy/download`; `zepto fbz dn template` → `.../upload-template`.
- `zepto fbz dn batch list` → `.../batch-upload/list`; `zepto fbz dn batch get <id>` → `.../batch-upload/{id}`; `… items` → `.../batch-upload/{id}/items`; `zepto fbz dn batch file` → `.../batch-upload/file`.
- `zepto packaging config` → `fcc /api/v1/packaging/bag-barcode/config`; `zepto packaging list` → `.../list`; `zepto packaging preview` → `.../preview`; `zepto packaging download` → `.../download`.

Explicitly **excluded** from the read-only surface: rebate approve/reject, rebate CSV upload, DN copy/working-copy upload, DN approve/reject/update, DN batch-upload/cancel, and bag-barcode confirm — all state-changing.

## Connections

- Portal shell & index: [[00-Zepto-Atlas]] · [[00-Zepto-Atlas]] · master endpoint index [[Zepto-Endpoints]]
- Auth model & token: [[Auth-and-Access]] · scope rules: [[Read-Only-Guardrails]]
- **Tightest siblings** (same money/fulfilment lane): debit/credit notes and rebate deductions settle in [[Payments]] and post to the [[Ledger-Recon-Upload]]; DNs are raised against goods received on a [[Purchase-Orders]] / GRN and returns in [[RTV]]; non-trade DN counterparts in [[Receivables]].
- Upstream: rebate margins reconcile against the SKUs and contract terms in [[Vendor-Contracts-Margins]] and [[Catalog-Health]]; DNs link back to shipments in [[ASN]]; bulk FBZ exports surface in [[Vendor-Reports-Queue]].
