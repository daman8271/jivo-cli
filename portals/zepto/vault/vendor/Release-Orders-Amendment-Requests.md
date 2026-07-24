---
title: Release Orders & Amendment Requests
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, release-orders-amendments]
---

# Release Orders & Amendment Requests

**Purpose.** The contract-management surface where JIVO views **release orders** (the ads/booking release-order object served by `fcc /ads-bff`) and raises / reviews **amendment requests** against its vendor contracts (margin, incentive, on-invoice/off-invoice terms) via the `fcc /contractservice` API — list, drill into one request, watch its state timeline, and (for reviewers) see what is pending — all read-only here; every create/submit/upload/approve verb is held out of scope.

## SPA routes

- `/contract-management/all-amendments` — all amendment requests (list).
- `/contract-management/amendment-approvals` — reviewer queue (amendments pending on the logged-in user).
- `/vendor/contract-management/all-amendments` — vendor-scoped alias of the list.
- `/vendor/contract-management/amendment-approvals` — vendor-scoped alias of the reviewer queue.
- `/vendor/contract-management/amendment-requests/:amendmentRequestId` — single amendment-request detail (summary, review view, state timeline).

Served by the **vendor remote (635)** micro-frontend; endpoint constants read from chunks `vendor/1183.8940422c8268d8dc.js` (release-order) and `vendor/3539.64ab07c46b8741b5.js` (amendment-requests / contract service).

## Backend host

Single host: **`fcc.zepto.co.in`**, under two path prefixes —
- `fcc.zepto.co.in/ads-bff/api/v1/release-order…` — the release-order object (ads booking / release order).
- `fcc.zepto.co.in/contractservice/api/v1/amendment-requests…` (and `…/vendor-contract/…`, `…/bulk-jobs/…`) — the vendor-contract amendment service.

Auth = the single JWT in the `authorization` header (no `Bearer` prefix), shared across all Zepto backends; WAF headers not enforced at last capture. Entity: Jivo Wellness Pvt. Ltd. (Manufacturer, STANDARD), `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, login `ecom1@jivo.in`.

## API endpoints (READ)

Paths shown with their real prefix (`ads-bff/…` or `contractservice/…`); base = `https://fcc.zepto.co.in/`. `${e}` = a path id (release-order id / amendment-request id / bulk-job id / vendor-contract id). Methods are as wired in the bundle; "method to confirm" = binding present but verb not directly observed. No endpoint here was probed live to 2xx (the only allowlisted GET, `amendment-requests/list`, returned **401 "Token expired"** — capture token was stale), so none is marked PROVEN.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `ads-bff/api/v1/release-order` | List release orders (`RELEASE_ORDER` base collection) | READ (list; method to confirm — base also backs create, GET only here) |
| GET | `ads-bff/api/v1/release-order/${e}` | Single release-order detail (`getReleaseOrder`) | READ |
| GET | `ads-bff/api/v1/release-order/approvers/${e}` | Approvers list for a release order (`getApproversList`) | READ |
| GET | `ads-bff/api/v1/release-order/meta` | Release-order form/meta config (`RELEASE_ORDER_META`) | READ |
| GET | `ads-bff/api/v1/release-order/s3/presigned-url` | Presigned S3 URL for a release-order file (`PRE_SIGNED_URL`) | READ (file) — method to confirm; if it mints an **upload** URL treat as write |
| GET | `contractservice/api/v1/amendment-requests/list` | Amendment-requests list — the `/all-amendments` grid (`AMENDMENT_REQUESTS_LIST`) | READ (probed → 401 token-expired; documented, not proven) |
| GET | `contractservice/api/v1/amendment-requests/pending-on-reviewer` | Amendments pending on the logged-in reviewer — `/amendment-approvals` queue (`AMENDMENT_REQUESTS_PENDING_ON_REVIEWER`) | READ |
| GET | `contractservice/api/v1/amendment-requests/${e}` | Single amendment-request detail (`amendmentRequestById`) | READ |
| GET | `contractservice/api/v1/amendment-requests/${e}/review` | Review view / diff for one amendment request (`amendmentRequestReview`) | READ — method to confirm; if this **submits** an approve/reject decision it is a WRITE (do not POST) |
| GET | `contractservice/api/v1/amendment-requests/${e}/state-timeline` | State-transition history of one amendment request (`amendmentRequestStateTimelines`) | READ |
| GET | `contractservice/api/v1/bulk-jobs/${e}/amendment-requests` | Amendment requests created by a bulk job (`bulkJobAmendmentRequests`) | READ |
| GET | `contractservice/api/v1/vendor-contract/${e}/amendment-requests` | Amendment requests against one vendor contract (`contractAmendmentRequests`) | READ |

## Out of scope (writes) — never expose in a read-only CLI

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `contractservice/api/v1/amendment-requests` | Create an amendment request (`AMENDMENT_REQUESTS` base; the GET list lives at `…/list`, so the bare collection is the create) | WRITE (ambiguous base — held out of scope pending method confirmation) |
| POST | `contractservice/api/v1/amendment-requests/bulk-submit` | Bulk-submit amendment requests (`AMENDMENT_REQUESTS_BULK_SUBMIT`) | WRITE |
| POST | `contractservice/api/v1/amendment-requests/file-upload` | Upload the amendment-requests file (bulk-create source, `AMENDMENT_REQUEST_FILE_UPLOAD`) | WRITE (upload) |
| POST | `contractservice/api/v1/amendment-requests/${e}/upload-artifact` | Upload a supporting artifact onto one amendment request (`amendmentRequestUploadArtifact`) | WRITE (upload) |

Also treat as write-if-POST and never fire: `…/amendment-requests/${e}/review` (see READ table caveat), and `release-order/s3/presigned-url` if it turns out to mint an upload URL.

## Real data seen (evidence)

- **Live probe (read-only):** `GET https://fcc.zepto.co.in/contractservice/api/v1/amendment-requests/list` → **HTTP 401** `{"code":401,"message":"Token expired"}`. The capture JWT (`ecom1@jivo.in`, role "External Super Ads Admin", `exp 1783967399`) had expired before probe time, so no 2xx body/response shape was captured. The 401 confirms the host+path route is live and auth-gated (no WAF challenge). Transcript: `captures/vendor/release-orders-amendments-probes.txt`.
- **Endpoint set** read out of the bundle (not invented): release-order constants from `vendor/1183.8940422c8268d8dc.js` (`RELEASE_ORDER`, `getReleaseOrder`, `getApproversList`, `RELEASE_ORDER_META`, `PRE_SIGNED_URL`); amendment-request constants from `vendor/3539.64ab07c46b8741b5.js` (`AMENDMENT_REQUESTS`, `…_LIST`, `…_PENDING_ON_REVIEWER`, `…_BULK_SUBMIT`, `…_FILE_UPLOAD`, `amendmentRequestById`, `amendmentRequestReview`, `amendmentRequestStateTimelines`, `amendmentRequestUploadArtifact`, `bulkJobAmendmentRequests`, `contractAmendmentRequests`).
- **Not in any current CLI.** The existing `zepto-cli` covers only the 6 pull flows (Sales + Inventory `fcc /api/v1/reports*`, ads 2×2 `fcc /ads-bff/api/v1`); no release-order or amendment-request endpoint is wired anywhere yet — this section is documented-but-unbuilt.
- **Response bodies uncaptured.** Because the probe token was expired, exact filter keys and row schemas for the list / detail / timeline endpoints still want a live read-only capture with a fresh JWT.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no create, submit, upload, or review-decision POST):

- `amendments list [--pending-on-reviewer] [--contract <id>] [--bulk-job <id>]` → `amendment-requests/list` / `…/pending-on-reviewer` / `vendor-contract/${id}/amendment-requests` / `bulk-jobs/${id}/amendment-requests`. Pure READ.
- `amendments get <amendmentRequestId>` → `amendment-requests/${e}`, with `--timeline` → `…/state-timeline` and `--review` → `…/review` (read-only; never submit). Pure READ.
- `release-orders list` / `release-orders get <id>` / `release-orders approvers <id>` / `release-orders meta` → the `ads-bff/api/v1/release-order…` reads. Pure READ.

Explicitly **excluded**: creating/bulk-submitting amendment requests, uploading amendment files or artifacts, minting an upload presigned URL, and firing any review approve/reject — all writes.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- Tightest siblings (same `contractservice` API / contract-management shell): [[Vendor-Contracts-Margins]] (the contracts these amendments amend; margin & incentive terms) · [[Invoicing]] (on-invoice/off-invoice terms an amendment changes).
- Upstream demand lane: [[Purchase-Orders]] · [[ASN]]; downstream money lane: [[Payments]] · [[Ledger-Recon-Upload]].
