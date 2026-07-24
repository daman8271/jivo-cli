---
title: Vendor Contracts, Margins & Incentives
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, vendor-contracts-margins]
status: studied
---

# Vendor Contracts, Margins & Incentives

The **Vendor Contracts, Margins & Incentives** section is Zepto's **commercial-terms
surface** — the machinery that defines *what Zepto pays JIVO and what it deducts*: the
vendor contract itself (parties, category, payment terms, reviewers, lifecycle
state) plus the **margin & incentive** schedules bolted onto it — **on-invoice** and
**off-invoice** margins, **DeQ** (deal / quantity discount), **stock-correction**, and
**RTV / stock** consolidations, and the **PV (Price-Variance) base margin** used on the
Fulfilled-by-Zepto (FBZ) side. This is the upstream of the money lane: the margins agreed
here are what later show up as invoice **deductions** in [[Payments]] and as rebates /
debit notes in [[Fulfilled-by-Zepto]]. For JIVO this is Jivo Wellness Pvt. Ltd.
(Manufacturer / STANDARD tier, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`).

All calls hit **`fcc.zepto.co.in`** (the same vendor backend the proven SALES/INVENTORY
and ads pulls use), under two service prefixes: the newer **`contractservice/api/v1/*`**
(the contract + margin-and-incentive engine) and the older **`api/v1/vendor-pv-margin/*`**
(the FBZ PV-margin bulk-upload tool). One JWT (header `authorization: <jwt>`, **no**
`Bearer` prefix) authenticates both; WAF headers were not enforced at last capture.

The endpoint contracts below were extracted from the vendor micro-frontend code-split
chunk **`captures/js/vendor/3539.64ab07c46b8741b5.js`** — the API-constant maps
(`getContractDetails:e=>\`contractservice/api/v1/vendor-contract/${e}\``, the
`margin-and-incentive` download/upload template map, and the `vendor-pv-margin` FBZ map)
— **not** live captures except where a probe is noted. This is a **heavily write-shaped**
section: contract authoring, publishing, reviewer assignment, amendment submission, and
the entire margin/stock/DeQ/on-invoice/off-invoice **upload** side are all mutating and
held **out of scope**. The read surface is the contract **list / summary / detail /
activity-log / state-timeline**, the **margin-details listings**, and the
already-generated **download** (consolidated data + blank templates) endpoints.

## SPA route(s)

Vendor-lane, rendered by the vendor remote (635). Routes from `sections.json`:

- `/contract-management` and `/vendor/contract-management` — the contract-management home.
- `/contract-management/all-contracts` · `/vendor/contract-management/all-contracts` — the
  full contracts grid (`GET_FILTERED_CONTRACTS` + `GET_CONTRACTS_SUMMARY`).
- `/contract-management/contracts-approval` · `/vendor/contract-management/contracts-approval`
  — approval queue (`GET_APPROVAL_CONTRACTS` = pending-on-approver).
- `/contract-management/activity-logs` · `/vendor/contract-management/activity-logs` —
  activity feed (`GET_ALL_ACTIVITY_LOGS`).
- `/contract-management/bulk-jobs` · `/vendor/contract-management/bulk-jobs` ·
  `/vendor/contract-management/bulk-jobs/:jobId` — bulk contract jobs.
- `/contract-management/create-contract` · `/vendor/contract-management/create-contract` —
  the contract-authoring wizard (write flow; out of scope).
- `/vendor/contract-management/:contractId/details` — single-contract detail page
  (`getContractDetails`, `state-timeline`, per-contract `activity-log`, margin listings).

## Backend host(s)

- **`fcc.zepto.co.in`** — the sole host. Two service prefixes:
  - `contractservice/api/v1/*` — vendor contracts + `margin-and-incentive/*` +
    `margin-incentive/*` (the contract-terms engine).
  - `api/v1/vendor-pv-margin/*` — the FBZ **Price-Variance base-margin** bulk tool.

## API endpoints (READ)

`${e}` = a contract id (or margin-and-incentive id) path param. All rows below are pure
reads — list / summary / detail / activity feed, or **file fetches of already-generated
content** (consolidated data exports the *server* has already produced, and blank upload
**templates**). Method shown as wired in the chunk (`GET` = confirmed constant binding;
`—` = binding present, verb not directly observed).

### Contracts (list / detail / lifecycle)

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/contractservice/api/v1/vendor-contract/get-filtered-contracts` | All-contracts grid, filtered/paged — `GET_FILTERED_CONTRACTS` | READ |
| GET | `/contractservice/api/v1/vendor-contract/listing-summary` | Contracts summary tiles for the grid header — `GET_CONTRACTS_SUMMARY` | READ · probed → **401 Token expired** (documented, expired-token) |
| GET | `/contractservice/api/v1/vendor-contract/pending-on-approver` | Contracts pending on the current approver (approval queue) — `GET_APPROVAL_CONTRACTS` | READ |
| GET | `/contractservice/api/v1/vendor-contract/static-config` | Static config + roles for the contract UI — `GET_STATIC_CONFIG` / `GET_ROLES` | READ |
| GET | `/contractservice/api/v1/vendor-contract/users` | Users available for a role (reviewer/approver pickers) — `GET_USERS_FOR_ROLE` | READ |
| GET | `/contractservice/api/v1/vendor-contract/activity-log` | Global contract activity feed — `GET_ALL_ACTIVITY_LOGS` | READ |
| GET | `/contractservice/api/v1/vendor-contract/${e}` | Single contract detail (parties, category, terms, state) — `getContractDetails` | READ |
| GET | `/contractservice/api/v1/vendor-contract/${e}/activity-log` | Per-contract activity log — `getActivityLogsByContractId` | READ |
| GET | `/contractservice/api/v1/vendor-contract/${e}/state-timeline` | Contract lifecycle state timeline — `getContractStates` | READ |
| — | `/contractservice/api/v1/vendor-contract/${e}/logs` | Per-contract logs feed — `contractLogs` (method to confirm) | READ |
| — | `/contractservice/api/v1/vendor-contract/${e}/amendment-reviewers` | Reviewers assigned to a contract's amendment — `amendmentReviewers` (method to confirm) | READ |
| — | `/contractservice/api/v1/vendor-contract/${e}/payment-terms` | **GET** `getVendorPaymentTerms` — read the contract's payment terms (the same path's **POST** `submitPaymentTerms` is a write; see out-of-scope) | READ (GET only) |
| — | `/contractservice/api/v1/vendor-contract/${e}/review` | `reviewContract` — fetch a contract in its review context (verb ambiguous; **do not fire** — if a review-submit POST, it is a write) | READ (method to confirm) |
| — | `/contractservice/api/v1/cdf` | `cdf` contract-data feed (const `It`; sits beside the `vms/api/v2/vendor/*` maps; purpose/method to confirm) | READ (to confirm) |

### Margins & incentives (listings)

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/contractservice/api/v1/margin-incentive/list-item-margin-details` | Global item-level margin-detail listing — `LIST_ITEM_MARGIN_DETAILS_GLOBAL` | READ |
| GET | `/contractservice/api/v1/margin-incentive/${e}/list-item-margin-details` | Per-contract item-level margin-detail listing — `listItemMarginDetailsForContract` | READ |

### FBZ Price-Variance base margin (listings)

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| — | `/api/v1/vendor-pv-margin/status-config` | FBZ upload status config — `GET_FBZ_UPLOAD_STATUS` | READ |
| — | `/api/v1/vendor-pv-margin/upload-request-list` | List of prior FBZ PV-margin upload jobs (a queue **list**, not an upload) — `GET_FBZ_UPLOAD_LISTING` | READ |
| — | `/api/v1/vendor-pv-margin/vendor` | FBZ vendor details — `GET_FBZ_VENDOR_DETAILS` | READ |
| — | `/api/v1/vendor-pv-margin/vendor/filter` | FBZ vendor listing / filter values — `GET_FBZ_VENDOR_LISTING` | READ |
| — | `/api/v1/vendor-pv-margin/vendor/pv-list` | FBZ per-vendor SKU PV-margin listing — `GET_FBZ_VENDOR_SKU_LISTING` | READ |

### File downloads — already-generated content & blank templates (READ · file)

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/contractservice/api/v1/margin-and-incentive/${e}/download-margin-data` | Consolidated contract-margin data export (already generated) — `downloadConsolidatedContractMargins` | READ (file) |
| GET | `/contractservice/api/v1/margin-and-incentive/${e}/download-on-invoice-data` | Consolidated on-invoice data export — `downloadConsolidatedOnInvoiceData` | READ (file) |
| GET | `/contractservice/api/v1/margin-and-incentive/${e}/download-deq-data` | Consolidated DeQ (deal/qty) data export — `downloadConsolidatedDeqDetails` | READ (file) |
| GET | `/contractservice/api/v1/margin-and-incentive/${e}/download-stock-data` | Consolidated RTV/stock data export — `downloadConsolidatedRtvData` | READ (file) |
| GET | `/contractservice/api/v1/margin-and-incentive/${e}/download-stock-correction-data` | Consolidated stock-correction data export — `downloadConsolidatedStockCorrectionDetails` | READ (file) |
| GET | `/contractservice/api/v1/margin-and-incentive/${e}/item-margin-details-template` | Blank item-margin upload **template** — `downloadMarginDetailsTemplate` | READ (file) |
| GET | `/contractservice/api/v1/margin-and-incentive/${e}/on-invoice-details-template` | Blank on-invoice upload template — `downloadOnInvoiceDetailsTemplate` | READ (file) |
| GET | `/contractservice/api/v1/margin-and-incentive/${e}/deq-details-template` | Blank DeQ-details upload template — `downloadDeQDetailsTemplate` | READ (file) |
| GET | `/contractservice/api/v1/margin-and-incentive/${e}/item-stock-details-template` | Blank item-stock upload template — `downloadStockDetailsTemplate` | READ (file) |
| GET | `/contractservice/api/v1/margin-and-incentive/${e}/stock-correction-details-template` | Blank stock-correction upload template — `downloadStockCorrectionDetailsTemplate` | READ (file) |
| — | `/api/v1/vendor-pv-margin/download` | Download a previously-uploaded FBZ PV-margin file — `DOWNLOAD_FBZ_UPLOAD_FILE` | READ (file) |
| — | `/api/v1/vendor-pv-margin/upload/template` | Blank FBZ PV-margin upload **template** — `DOWNLOAD_FBZ_TEMPLATE_FILE` | READ (file) |
| — | `/api/v1/vendor-pv-margin/vendor/download` | FBZ per-vendor margin data download — `GET_FBZ_VENDOR_DOWNLOAD` | READ (file) |
| — | `/api/v1/vendor-pv-margin/vendor/pv-list/download` | FBZ per-vendor SKU PV-list download — `GET_FBZ_VENDOR_SKU_DOWNLOAD` | READ (file) |

**Note on the `download-*` rows.** These fetch data the server has **already consolidated**
for an existing margin-and-incentive record `${e}` (a GET blob), not a report-generation
job — they are the read counterparts to the `upload-*` POSTs below and are safe pure
reads. The `*-template` rows return a **blank** spreadsheet template (no state). Contrast
with the [[Vendor-Reports-Queue]] pattern, where a report must first be *requested* (a
write) before download.

## Out of scope (writes) — never expose in a read-only CLI

All DOCUMENTED-FROM-BUNDLE ONLY. A strict read-only CLI must never call these — they
create / edit / publish / delete / submit / upload contract & margin state.

### Contract authoring & lifecycle (WRITE)

| METHOD | Path | Purpose | Why held out |
|---|---|---|---|
| POST | `/contractservice/api/v1/vendor-contract/contract-details` | Submit basic contract details — `SUBMIT_BASIC_CONTRACT_DETAILS` | Creates a contract. WRITE. |
| POST | `/contractservice/api/v1/vendor-contract/${e}/margin-and-incentive` | Save margin & incentive details — `saveMarginIncentiveDetails` | Writes margin schedule. WRITE. |
| POST | `/contractservice/api/v1/vendor-contract/${e}/reviewers-and-terms` | Submit reviewers + remarks — `submitReviewersAndRemarks` | WRITE. |
| PUT | `/contractservice/api/v1/vendor-contract/${e}/reviewer` | Update the contract reviewer — `updateContractReviewer` | WRITE. |
| POST | `/contractservice/api/v1/vendor-contract/${e}/submit-amendment-requests` | Submit amendment requests for review — `submitAmendmentRequestsForReview` | WRITE. |
| POST | `/contractservice/api/v1/vendor-contract/${e}/payment-terms` | Submit payment terms — `submitPaymentTerms` (same path GET reads terms; POST is the write) | WRITE. |
| — | `/contractservice/api/v1/vendor-contract/${e}/publish` | Publish a contract — `publishContract` | Mutates lifecycle. WRITE. |
| — | `/contractservice/api/v1/vendor-contract/bulk-publish` | Bulk-publish contracts — `BULK_PUBLISH_CONTRACTS` | Mutates lifecycle. WRITE. |
| — | `/contractservice/api/v1/vendor-contract/${e}/discard` | Discard a draft contract — `discardDraftContract` | Destroys draft state. WRITE. |
| DELETE | `/contractservice/api/v1/margin-and-incentive/${e}/delete-margin-and-incentive-details` | Delete a margin-and-incentive attachment — `removeMarginAndIncentiveDetailsAttachment` | WRITE (delete). |

### Uploads / attachments (EXPORT / write — enqueue or attach a file)

| METHOD | Path | Purpose | Why held out |
|---|---|---|---|
| POST | `/contractservice/api/v1/margin-and-incentive/${e}/upload-item-margin-details` | Upload item-margin details — `uploadMarginDetails` | Writes margin data. |
| POST | `/contractservice/api/v1/margin-and-incentive/${e}/upload-on-invoice-details` | Upload on-invoice details — `uploadOnInvoiceDetails` | Writes. |
| POST | `/contractservice/api/v1/margin-and-incentive/${e}/upload-off-invoice-details` | Upload off-invoice details — `uploadOffInvoiceDetails` | Writes. |
| POST | `/contractservice/api/v1/margin-and-incentive/${e}/upload-deq-details` | Upload DeQ details — `uploadDeQDetailsAttachment` | Writes. |
| POST | `/contractservice/api/v1/margin-and-incentive/${e}/upload-item-stock-details` | Upload item-stock details — `uploadStockDetails` | Writes. |
| POST | `/contractservice/api/v1/margin-and-incentive/${e}/upload-stock-correction-details` | Upload stock-correction details — `uploadStockCorrectionDetailsAttachment` | Writes. |
| POST | `/contractservice/api/v1/vendor-contract/${e}/upload-terms-and-schedule` | Upload contract terms + schedule — `uploadTermsAndSchedules` | Writes/attaches. |
| POST | `/contractservice/api/v1/vendor-contract/${e}/upload-email-attachment` | Upload an email attachment — `uploadEmailAttachment` | Writes/attaches (may email). |
| — | `/api/v1/vendor-pv-margin/upload` | Upload FBZ PV-margin file — `POST_FBZ_UPLOAD` | Writes FBZ margins. |
| — | `/api/v1/vendor-pv-margin/vendor/base-margin` | Edit FBZ base margin — `POST_EDIT_BASE_MARGIN` | WRITE (edit). |
| — | `/api/v1/vendor-pv-margin/vendor/pv/update-fields` | Edit FBZ BFD margin fields — `POST_EDIT_BFD_MARGIN` | WRITE (update-fields). |

## Live probe (evidence)

- **1 probe fired, read-only GET, then halted** (per the guardrails, stop on first
  401/403/429). `GET https://fcc.zepto.co.in/contractservice/api/v1/vendor-contract/listing-summary`
  with the captured vendor JWT returned **`HTTP 401 {"code":401,"message":"Token expired"}`** —
  the same token (`exp 1783967399` = 2026-07-13 18:29:59 UTC) used by the sibling
  [[RTV]] and [[Release-Orders-Amendment-Requests]] probes, lapsed 11 days before this run. No
  2xx, so **nothing was upgraded to PROVEN**; all endpoints remain **documented (not
  probed)**. Transcript: `captures/vendor/vendor-contracts-margins-probes.txt`.
- **Auth/base confirmed** by the proven sibling flows on the same host: SALES/INVENTORY
  (`fcc /api/v1/reports*`) and ads (`fcc /ads-bff/api/v1`) work with the identical
  `authorization: <jwt>` header (no `Bearer`), `origin/referer https://brands.zepto.co.in`.
  Re-run these probes with a fresh token to lock down response shapes.
- **Response shapes:** to confirm via live read-only capture. Expected top-level keys
  (from grid usage): `get-filtered-contracts` → paged contract rows + total;
  `listing-summary` → status-count tiles; `getContractDetails` → contract header + parties
  + category + terms + state; `state-timeline` → ordered state events;
  `list-item-margin-details` → per-item margin rows (on-invoice / off-invoice / DeQ);
  `static-config` → enums + roles.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no create/publish/submit/upload/delete):

- `zepto contracts list [--filters … --page …]` → `GET vendor-contract/get-filtered-contracts`;
  `zepto contracts summary` → `…/listing-summary`. Pure READ.
- `zepto contracts approvals` → `…/pending-on-approver`; `zepto contracts activity` →
  `…/activity-log`. Pure READ.
- `zepto contracts get <contractId>` → `vendor-contract/<id>`; `zepto contracts timeline <id>`
  → `…/state-timeline`; `zepto contracts activity <id>` → `…/activity-log`;
  `zepto contracts payment-terms <id>` → GET `…/payment-terms`. Pure READ.
- `zepto contracts config` → `…/static-config` (roles + enums); `zepto contracts users --role …`
  → `…/users`. Pure READ.
- `zepto margins list [--contract <id>]` → `margin-incentive[/{id}]/list-item-margin-details`.
  Pure READ.
- `zepto margins download <miId> --kind margin|on-invoice|deq|stock|stock-correction [--out FILE]`
  → the `margin-and-incentive/<id>/download-*-data` blobs; `zepto margins template <miId> --kind …`
  → the `*-template` files. Pure READ (file).
- `zepto fbz-margin vendors` / `zepto fbz-margin skus` → `vendor-pv-margin/vendor{,/filter,/pv-list}`;
  `zepto fbz-margin download …` → `vendor-pv-margin[/vendor]/…/download`. Pure READ.
- **Excluded:** authoring / editing / publishing / discarding a contract, saving or
  uploading margin / on-invoice / off-invoice / DeQ / stock / stock-correction details,
  editing FBZ base/BFD margins, submitting payment terms, assigning reviewers, submitting
  amendment requests, and the delete-attachment call — all writes.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] ·
  [[Read-Only-Guardrails]]
- **Downstream money lane** — the margins & incentives defined here become invoice
  deductions and rebates: [[Payments]] · [[Fulfilled-by-Zepto]] · [[Ledger-Recon-Upload]] · [[Receivables]].
- **Vendor-lane siblings** feeding/consuming these terms: [[Purchase-Orders]] ·
  [[Invoicing]] · [[RTV]] (stock-correction/RTV consolidations reference the same
  contracts) · [[Release-Orders-Amendment-Requests]] · [[Vendor-Reports-Queue]] (the
  request-then-download pattern this section's direct `download-*` blobs deliberately
  differ from).
- Contract reviewer/approver users tie into [[Users-Access]] and [[KYC-Onboarding]] (VMS
  vendor identity the `vms/api/v2/vendor/*` maps beside `cdf` reference).
