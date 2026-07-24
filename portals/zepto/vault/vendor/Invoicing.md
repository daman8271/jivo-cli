---
title: Invoicing (Self-Invoice & Off-Invoice)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, invoicing]
---

# Invoicing (Self-Invoice & Off-Invoice)

**Purpose.** The vendor **Invoicing** surface covers two money flows for Jivo Wellness Pvt. Ltd. (Manufacturer, STANDARD tier, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, login `ecom1@jivo.in`): (1) **Self-Invoice / Non-Trade Vendor (NTV)** — where the vendor raises and tracks its own non-trade invoices (create a draft → upload the PDF → OCR-verify → submit → track/cancel), and (2) **Off-Invoice rules** — the discount/margin rules applied *off* the trade invoice, configured against a vendor contract (add/remove rules, upload inclusion/exclusion lists, download a template, track application). Only the **read** halves are in scope here; every create/submit/cancel/upload/delete is documented and held out of scope.

## SPA routes

The section maps to these micro-frontend routes (vendor remote `635`, mounted under the root-shell `631`; both bare and `/vendor`-prefixed forms exist):

- `/invoice` · `/vendor/invoice` — self-invoice / NTV list landing
- `/invoice/details` · `/vendor/invoice/details` — invoice details view
- `/invoice/details/:id` · `/vendor/invoice/details/:id` — single invoice detail
- `/invoice/edit/:id` · `/vendor/invoice/edit/:id` — invoice edit (create/draft flow — mutating)
- `/payments/invoices` · `/vendor/payments/invoices` — invoices under the payments tab
- `/accounts-receivable/total-invoices` · `/vendor/accounts-receivable/total-invoices` — AR total-invoices roll-up

## Backend host

- **`fcc.zepto.co.in`** — vendor reports/finance gateway (fronted by the **bifrost** API gateway). Two service prefixes serve this section: `invoice/api/v1/self-invoice/non-trade/*` (self-invoice / NTV) and `contractservice/api/v1/off-invoice/*` (+ `contractservice/api/v1/margin-and-incentive/*`) for off-invoice rules. One JWT (`authorization` header, **no** `Bearer` prefix) authenticates across all Zepto backends; WAF headers were not enforced at last capture.

All contracts below were extracted from the vendor chunk `vendor/3539.64ab07c46b8741b5.js` (the invoicing page module) — API-constant + method bindings, not live captures unless marked PROVEN. `${e}` = a path parameter (invoice id / contract id / rules id).

## READ endpoints

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/invoice/api/v1/self-invoice/non-trade/summary` | Self-invoice (NTV) summary tiles — `GET_INVOICE_SUMMARY` | READ (probed 2026-07-24 → HTTP 404 at bifrost, path not resolved; token later 401 → not PROVEN) |
| GET | `/invoice/api/v1/self-invoice/non-trade/list` | Self-invoice (NTV) list grid — `GET_INVOICE_LIST` | READ (probed → HTTP 404 at bifrost; not PROVEN) |
| GET | `/invoice/api/v1/self-invoice/non-trade/${e}/details` | Single self-invoice detail (`:id`) — `getInvoiceDetails` | READ |
| GET | `/invoice/api/v1/self-invoice/non-trade/${e}/documents` | Presigned S3 URL(s) for a self-invoice's uploaded documents — `getSelfInvoiceS3Url` | READ |
| GET | `/invoice/api/v1/self-invoice/non-trade/entity-names` | Entity-name lookup (buyer/seller legal entities) — `GET_ENTITY_NAMES` | READ |
| GET | `/invoice/api/v1/self-invoice/non-trade/gstin-state` | GSTIN → state resolver for invoice header — `GET_GSTIN_STATE` | READ |
| GET | `/contractservice/api/v1/off-invoice/off-invoice-rules/get-config` | Off-invoice rules config (allowed types, limits) — `GET_OFF_INVOICE_CONFIG` | READ (probed 2026-07-24 → **HTTP 401 Token expired**; not PROVEN) |
| GET | `/contractservice/api/v1/off-invoice/off-invoice-rules/${e}/tracking` | Application/rollout tracking for a rules set (`:id`) — `getTracking` | READ |
| GET | `/contractservice/api/v1/off-invoice/contracts/${e}/off-invoice-rules` | Fetch off-invoice rules for a contract — `getOffInvoiceRules` (GET). **Same path also carries `createOffInvoiceRules` POST — write, see below.** | READ (GET binding only) |
| GET | `/contractservice/api/v1/off-invoice/off-invoice-rules/template` | Blank off-invoice-rules upload template — `DOWNLOAD_TEMPLATE` | READ (file) |
| GET | `/contractservice/api/v1/margin-and-incentive/${e}/off-invoice-details-template` | Off-invoice details template for a margin/incentive contract (`:id`) — `downloadOffInvoiceDetailsTemplate` | READ (file) |

**Adjacent reads seen in the same chunk (referenced as consts, not emitted as distinct route objects in the section data, so listed here for completeness — the NTV credit-note listing pair):** `GET_INVOICE_CN_LIST` → `/api/v1/payment/ntv-invoice/filter`, `GET_INVOICE_CN_SUMMARY` → `/api/v1/payment/ntv-invoice/listing-stat`. Both are pure reads (list + listing-stat) for the NTV credit-note view and would probe under the same allowlist with a fresh token.

## Out of scope (writes)

Never expose in a read-only CLI; documented from the bundle only, never called.

| METHOD | Path | Const | Effect |
|---|---|---|---|
| POST | `/invoice/api/v1/self-invoice/non-trade/draft` | `SAVE_DRAFT` | Save a self-invoice draft — WRITE |
| POST | `/invoice/api/v1/self-invoice/non-trade/upload` | `UPLOAD_SELF_INVOICE` | Upload the self-invoice PDF/document — EXPORT/upload (side-effect) |
| POST/UNKNOWN | `/invoice/api/v1/self-invoice/non-trade/poll-ocr` | `SELF_INVOICE_OCR` | Trigger/poll OCR extraction on the uploaded invoice (part of the create pipeline) — side-effect, method unconfirmed |
| POST | `/invoice/api/v1/self-invoice/non-trade/submit` | `SUBMIT_INVOICE` | Submit the self-invoice for processing — WRITE |
| POST | `/invoice/api/v1/self-invoice/non-trade/cancel` | `CANCEL_INVOICE` | Cancel a self-invoice — WRITE |
| POST | `/contractservice/api/v1/off-invoice/contracts/${e}/off-invoice-rules` | `createOffInvoiceRules` | Create off-invoice rules on a contract (same path as the GET read above) — WRITE |
| POST | `/contractservice/api/v1/off-invoice/off-invoice-rules/${e}/create-rule` | `addRule` | Add a single off-invoice rule — WRITE |
| POST | `/contractservice/api/v1/off-invoice/off-invoice-rules/${e}/file-upload` | `uploadInclusionExclusion` | Upload inclusion/exclusion applicability file — EXPORT/upload (side-effect) |
| DELETE | `/contractservice/api/v1/off-invoice/off-invoice-rules/${e}/remove-rule` | `removeRule` | Delete an off-invoice rule — WRITE |
| DELETE | `/contractservice/api/v1/off-invoice/off-invoice-rules/${e}/remove-applicability-file` | `removeUploadedFile` | Delete an uploaded applicability file — WRITE |

## Evidence / probe status

- **Source of truth:** vendor chunk `captures/js/vendor/3539.64ab07c46b8741b5.js` (invoicing page module) — API-constant + method bindings for both the `invoice/…/self-invoice/non-trade/*` and `contractservice/…/off-invoice/*` service prefixes.
- **Live probe (read-only, 2026-07-24):** transcript at `captures/vendor/invoicing-probes.txt`. JWT read from `captures/vendor/23-sales-list.txt` (exp epoch `1783967399` = 2026-07-13 IST → **expired**). 3 GET probes fired, then halted on a 401:
  - `…/self-invoice/non-trade/summary` → **404** (`Api path not found in bifrost`) — gateway routed the `invoice/` service but the upstream path did not resolve.
  - `…/self-invoice/non-trade/list` → **404** (same bifrost message).
  - `…/off-invoice/off-invoice-rules/get-config` → **401 Token expired** → STOP per guardrails.
  - **0 endpoints promoted to PROVEN.** Re-run with a fresh token to upgrade `summary` / `list` / `get-config` / `entity-names` / `gstin-state` and the NTV credit-note reads.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- Tightest siblings: [[Payments]] (invoices surface under the payments tab; `/payments/invoices`), [[Receivables]] (AR total-invoices roll-up; `/accounts-receivable/total-invoices`), [[Vendor-Contracts-Margins]] (off-invoice rules hang off vendor contracts + margin/incentive templates), [[Ledger-Recon-Upload]] (invoice → recon), and the [[Vendor-Reports-Queue]] queue for any async export of the above.
