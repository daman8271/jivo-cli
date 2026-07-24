---
title: Receivables & Non-Trade Vendor
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, receivables]
---

# Receivables & Non-Trade Vendor

**Purpose.** The vendor **Receivables & Non-Trade Vendor (NTV)** surface is the accounts-receivable (AR) side of the Jivo Wellness Pvt. Ltd. ↔ Zepto relationship (Manufacturer, STANDARD tier, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, login `ecom1@jivo.in`). It covers two linked things: (1) **Receivable Vendors** — the AR ledger view of what Zepto owes / has raised debit & credit notes against (total DN/CN, per-vendor receivable detail), and (2) **Non-Trade Vendors** — onboarding, KYC and profile management for non-trade (services/expense) vendors who raise self-invoices and credit notes rather than trading goods. Only the **read** halves (list, filter, KYC/details lookup) are in scope here; every approve / reject / update / OCR-check / attachment-upload is documented and held out of scope.

## SPA routes

The section maps to these micro-frontend routes (vendor remote `635`, mounted under root-shell `631`; both bare and `/vendor`-prefixed forms exist):

- `/accounts-receivable` · `/vendor/accounts-receivable` — AR / receivable-vendor list landing
- `/accounts-receivable/total-dn-cn` · `/vendor/accounts-receivable/total-dn-cn` — total Debit-Note / Credit-Note roll-up
- `/accounts-receivable/vendor-details` · `/vendor/accounts-receivable/vendor-details` — per receivable-vendor detail
- `/non-trade-vendors` · `/vendor/non-trade-vendors` — non-trade vendor list landing
- `/non-trade-vendors/vendor-details` · `/vendor/non-trade-vendors/vendor-details` — per non-trade-vendor detail
- `/leads-onboarding/non-trade-vendor-profile` · `/vendor/leads-onboarding/non-trade-vendor-profile` — NTV onboarding profile
- `/vendor/leads-onboarding/non-trade-vendor-profile/:userId` — NTV onboarding profile for a user
- `/leads-onboarding/receivables-vendor/:code` — receivables-vendor onboarding by vendor code

## Backend host

- **`fcc.zepto.co.in`** — vendor reports/finance gateway (fronted by the **bifrost** API gateway). This section is served by the **VMS** (vendor-management-service) prefix `vms/api/v1/receivable-vendor/*` and `vms/api/v1/non-trade-vendor/*`, which sits behind the internal **brand-analytics** proxy target (client sends `x-proxy-target: brand-analytics`). The NTV self-invoice / credit-note pieces reuse the `invoice/api/v1/self-invoice/non-trade/*` and `api/v1/payment/*` prefixes documented in [[Invoicing]]. One JWT (`authorization` header, **no** `Bearer` prefix) authenticates across all Zepto backends; WAF headers were not enforced at last capture.

All contracts below were extracted from the vendor chunks `vendor/3539.64ab07c46b8741b5.js` (NTV / receivable page module) and `vendor/2348.f65d84ed5e769418.js` + `5227…` / `7430…` / `7922…` (the receivable-vendor service class) — API-constant + method bindings, not live captures unless marked PROVEN. `${e}` / `:code` / `:userId` = a path parameter (vendor code / user id).

## READ endpoints

The two list surfaces (`receivable-vendor/filter`, `non-trade-vendor/filter`) are wired in the client as **POST-with-`{filters}` bodies but are pure reads** (no state change) — the same idiom as the `report-requests` list in [[Vendor-Reports-Queue]] and the POST-filter lists in Blinkit's partner study. The client class literally calls `l.Kp.post({path:"/vms/api/v1/receivable-vendor/filter"…})` inside `getReceivablesVendorsList`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/vms/api/v1/receivable-vendor/filter` | Receivable-vendor AR list grid — `GET_RECEIVABLE_VENDORS` / `getReceivablesVendorsList` (POST `{filters}` body; drives `/accounts-receivable` + total DN/CN roll-up) | READ (documented; not probed — POST-body list, expired token) |
| POST | `/vms/api/v1/non-trade-vendor/filter` | Non-trade-vendor list grid — `GET_NON_TRADE_VENDORS` (POST `{filters}` body; drives `/non-trade-vendors`) | READ (probed 2026-07-24 as GET → **HTTP 404** `Api path not found in bifrost` — GET route absent, endpoint is POST-only; not PROVEN) |
| GET | `/vms/api/v1/non-trade-vendor/kyc` | Non-trade-vendor KYC / vendor-details lookup — `GET_KYC_DETAILS` (drives `/non-trade-vendors/vendor-details`; needs vendor code + valid token) | READ (probed 2026-07-24 → **HTTP 401** token-signature-invalid → STOP; not PROVEN) |

**Adjacent reads seen in the same chunk** (referenced as consts, not emitted as distinct route objects in the section data, so listed here for completeness — all pure reads that would probe under the same allowlist with a fresh token):
- `GET_VENDOR_ATTACHMENTS` → `vms/api/v1/admin/non-trade-vendor/vendor-attachments` — a vendor's uploaded attachments (read).
- `non-trade-vendor/contract-details` — contract details for an NTV (read).
- `GET_INVOICE_LISTING_STAT` → `/api/v1/payment/rv-invoice/listing-stat` and `ntv-invoice/listing-stat` → the receivable-vendor / non-trade-vendor credit-note listing-stat tiles (read; the NTV credit-note list/summary pair itself is documented in [[Invoicing]]).
- `GET_PRE_SIGNED_URL` → `api/v1/commons/config/get-pre-signed-url` — mint a presigned S3 URL for viewing an uploaded document (read of a document URL).

## Out of scope (writes)

Never expose in a read-only CLI; documented from the bundle only, never called.

| METHOD | Path | Const | Effect |
|---|---|---|---|
| POST (UNKNOWN verb) | `/api/v1/ntv` | `OCR_INVOICE_CHECK` | Run OCR verification on an uploaded NTV invoice (part of the create/submit pipeline) — side-effect, method unconfirmed |
| POST | `/api/v1/ntv/attachment-upload` | `UPLOAD_INVOICE_CN` | Upload an NTV invoice / credit-note attachment — EXPORT/upload (side-effect) |
| PUT | `/vms/api/v1/non-trade-vendor/update` | `UPDATE_NON_TRADE_VENDOR` | Update a non-trade vendor's record — WRITE |
| POST | `/vms/api/v1/receivable-vendor/approve` | `approveReceivablesVendor` | Approve a receivable vendor — WRITE |
| POST | `/vms/api/v1/receivable-vendor/reject` | `rejectReceivablesVendor` | Reject a receivable vendor — WRITE |
| PUT | `/vms/api/v1/receivable-vendor/update` | `UPDATE_VENDOR_DETAILS` | Update a receivable-vendor's details — WRITE |

(Also seen adjacent in the receivable service class: `CREATE_COUNTERPART_VENDOR` → `POST vms/api/v1/admin/non-trade-vendor/counterpart` — creates a counterpart vendor — WRITE; out of scope.)

## Evidence / probe status

- **Source of truth:** vendor chunk `captures/js/vendor/3539.64ab07c46b8741b5.js` (NTV / receivable page module — the `GET_NON_TRADE_VENDORS` / `GET_KYC_DETAILS` / `UPDATE_*` / `OCR_INVOICE_CHECK` / `UPLOAD_INVOICE_CN` constants) plus `2348.f65d84ed5e769418.js` (+ `5227…` / `7430…` / `7922…`) which hold the `getReceivablesVendorsList` / `approveReceivablesVendor` / `rejectReceivablesVendor` service methods (`l.Kp.post({path:"/vms/api/v1/receivable-vendor/…"}, headers {x-proxy-target:"brand-analytics"})`).
- **Live probe (read-only, 2026-07-24):** transcript at `captures/vendor/receivables-probes.txt`. JWT read from `captures/vendor/23-sales-list.txt` (exp epoch `1783967399` = 2026-07-13 IST → **expired/rotated**). 2 GET probes fired, then halted on a 401:
  - `…/non-trade-vendor/filter` (as GET) → **404** `Api path not found in bifrost` — no GET route (endpoint is POST-only).
  - `…/non-trade-vendor/kyc` → **401** `signature is invalid` → STOP per guardrails.
  - **0 endpoints promoted to PROVEN.** Re-run with a fresh token to upgrade `receivable-vendor/filter` (POST), `non-trade-vendor/filter` (POST), and `non-trade-vendor/kyc` (GET) to PROVEN.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no approve/reject, no update, no OCR-check, no upload):
- `receivables vendors [--filters …]` → `POST /vms/api/v1/receivable-vendor/filter` (AR list + total DN/CN). Pure READ.
- `receivables ntv list [--filters …]` → `POST /vms/api/v1/non-trade-vendor/filter`. Pure READ.
- `receivables ntv kyc <code>` → `GET /vms/api/v1/non-trade-vendor/kyc` (KYC / vendor-details). Pure READ.
- `receivables ntv attachments <code>` / `receivables ntv contract <code>` → the adjacent `vendor-attachments` / `contract-details` reads. Pure READ.
- (Credit-note listing-stat + NTV self-invoice reads are surfaced under [[Invoicing]].)

Explicitly **excluded** from the read-only surface: approving/rejecting a receivable vendor, updating any vendor record, the `OCR_INVOICE_CHECK` verification call, uploading an invoice/CN attachment, and creating a counterpart vendor — all writes / side-effecting.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- Tightest siblings: [[Invoicing]] (NTV self-invoice + credit-note list/summary; AR total-invoices roll-up), [[Payments]] (receivable-vendor invoice payment status), [[Vendor-Contracts-Margins]] (non-trade vendor contracts), [[Ledger-Recon-Upload]] (AR → recon), and [[Vendor-Reports-Queue]] for any async export of the above.
