---
title: Payments & Settlements
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, payments]
status: studied
---

# Payments & Settlements

The **Payments & Settlements** section is Zepto's **money / payout view** of the JIVO ↔ Zepto
vendor relationship — what Zepto has invoiced/paid against received goods, the **payment advice**
(remittance references) behind each payout, the **debit / credit notes** Zepto raises as
settlement adjustments, and the running **ledger** that reconciles it all. For JIVO this is Jivo
Wellness Pvt. Ltd. (`manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, Manufacturer /
STANDARD tier). It is the settlement counterpart of the inbound goods lane: [[Purchase-Orders]] is
"what Zepto ordered", [[Invoicing]] is "what was billed", and Payments is "what actually settles —
invoices, advice, debit/credit notes, ledger". It also surfaces the **receivable / non-trade
vendor (RV / NTV)** side — invoices JIVO is billed on (`rv-invoice`, `ntv-invoice`) and their
settlements — which overlaps the dedicated [[Receivables]] surface.

The endpoint contracts below were extracted from the vendor micro-frontend code-split chunk
**`captures/js/vendor/3539.64ab07c46b8741b5.js`** — several API-constant maps (`x={…}` for invoice,
`y={…}` for payment-advice, `P={…}` for settlement, plus the ledger consts `v`/`O` and the RV/NTV
maps `K`/`R`) — **not** live captures except where a probe is noted. All calls hit a single host,
**`fcc.zepto.co.in`** (the same vendor-reports backend the proven SALES/INVENTORY pulls use), under
the `api/v1/payment/*` prefix (plus two `vendor/api/v1/payment/*` ledger reads). One JWT (header
`authorization: <jwt>`, **no** `Bearer` prefix) authenticates all of them; WAF headers were not
enforced at last capture.

## SPA route(s)

Eight routes, the same money surface mounted under both the bare and the `/vendor`-prefixed tree:

- `/payments` · `/vendor/payments` — Payments landing (invoice / payout list).
- `/payments/advice` · `/vendor/payments/advice` — **Payment Advice** (remittance references).
- `/payments/debit-credit-notes` · `/vendor/payments/debit-credit-notes` — **Debit / Credit Notes**
  (settlement adjustments; the `settlement/*` endpoints).
- `/payments/ledger` · `/vendor/payments/ledger` — **Ledger** (Zepto-side running ledger; recon).

These are vendor-lane pages rendered by the vendor remote (635) against the `fcc.zepto.co.in`
backend. (The deeper ledger recon/upload surface is documented separately in [[Ledger-Recon-Upload]].)

## Backend host(s)

- **`fcc.zepto.co.in`** — the sole host for this section. Path families: `api/v1/payment/invoice/*`
  (self/trade invoices + payout), `api/v1/payment/ntv-invoice/*` (non-trade vendor invoices),
  `api/v1/payment/rv-invoice/*` + `rv-settlement/*` + `rv-ledger/*` (receivable-vendor side),
  `api/v1/payment/payment-advice/*` + `payment-doc/*` (remittance advice + docs),
  `api/v1/payment/settlement/*` (debit/credit notes), and `api/v1/payment/ledger/*` +
  `vendor/api/v1/payment/ledger/zepto` (ledger).

## API endpoints (READ)

`${e}` = a payment-doc / invoice id (path param). All rows below are pure reads (list / summary /
detail / file-fetch of already-generated content). Method shown as wired in the chunk: `GET` =
confirmed constant binding; `UNKNOWN` = constant present in the map but the verb was not directly
observed in this chunk (these are listing/summary/detail constants used by read views, so their
effect is a read — verb to confirm on a live capture). Several `*/filter` endpoints are the
filtered-listing reads behind each grid.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/api/v1/payment/invoice/filter` | Invoice / payout list — `GET_INVOICE_LIST` (the Payments landing grid) | READ |
| GET | `/api/v1/payment/invoice/listing-stat` | Invoice list summary / stat tiles — `GET_INVOICE_SUMMARY` | READ |
| UNKNOWN | `/api/v1/payment/ledger/filter` | Ledger listing (filtered rows) — const `v` | READ (verb to confirm) |
| UNKNOWN | `/api/v1/payment/ledger/summary` | Ledger summary / running-balance tiles — const `O` | READ (verb to confirm) |
| GET | `/api/v1/payment/ntv-invoice/filter` | Non-trade-vendor (NTV) invoice / credit-note list — `GET_INVOICE_CN_LIST` | READ |
| GET | `/api/v1/payment/ntv-invoice/listing-stat` | NTV invoice list summary / stat — `GET_INVOICE_CN_SUMMARY` | READ |
| GET | `/api/v1/payment/payment-advice/filter` | **Payment Advice** listing (remittance references) — `GET_PAYMENT_ADVICE_LISTING` | READ |
| UNKNOWN | `/api/v1/payment/payment-advice/reference` | Single payment-advice detail (by reference) — `PAYMENT_ADVICE_DETAILS` | READ (verb to confirm) |
| GET | `/api/v1/payment/payment-doc/${e}` | Fetch a payment document by id (advice / settlement doc) — `getPaymentDocById` | READ (file) |
| GET | `/api/v1/payment/rv-invoice/filter` | Receivable-vendor (RV) invoice list — `GET_TOTAL_INVOICES` | READ |
| GET | `/api/v1/payment/rv-invoice/listing-stat` | RV invoice list summary / stat — `GET_INVOICE_LISTING_STAT` | READ |
| GET | `/api/v1/payment/rv-settlement/filter` | RV debit/credit-note (settlement) list — `GET_TOTAL_DN_CN` | READ |
| GET | `/api/v1/payment/settlement/filter` | **Debit / Credit Notes** list — `GET_DEBIT_AND_CREDIT_NOTE_LIST` | READ |
| GET | `/api/v1/payment/settlement/requested-debit-note/filter` | Requested (pending) debit/credit-note list — `GET_REQUESTED_DEBIT_AND_CREDIT_NOTE_LIST` | READ |
| GET | `/api/v1/payment/settlement/sub-type-list` | Settlement sub-type filter values — `TYPE_FILTER_LIST` | READ · probed → **401 Token expired** (documented, expired-token) |
| GET | `/vendor/api/v1/payment/ledger/zepto` | Zepto-side ledger listing — `GET_ZEPTO_LEDGER_LISTING` | READ |
| GET | `/vendor/api/v1/payment/rv-ledger/filter` | RV ledger listing (filtered rows) — `GET_RV_LEDGER_FILTER` | READ |

**Sibling constants (not in this section's 18).** The same const maps reference filter-seed and
receivable endpoints owned by other surfaces: `GET_RECEIVABLE_VENDORS`
(`/vms/api/v1/receivable-vendor/filter`) and `SEARCH_VENDORS` (`api/v1/commons/search-vendors`) seed
the RV grid dropdowns — those live in [[Receivables]] / [[Platform-Common]]. `GET_VENDOR_LEDGER_LISTING`
(`vendor/api/v1/ledger-upload/vendor`) and the sign-off/signed-copy consts belong to the
recon/upload surface in [[Ledger-Recon-Upload]]. They are not counted among this section's 18.

## Out of scope (writes) — never expose in a read-only CLI

| METHOD | Path | Purpose | Why held out |
|---|---|---|---|
| UNKNOWN (write) | `/api/v1/payment/rv-invoice/${e}/acknowledge` | **Acknowledge** a receivable-vendor invoice — `acknowledgeInvoice` | Mutates invoice state (records an acknowledgement). WRITE. |

DOCUMENTED-FROM-BUNDLE ONLY. A strict read-only CLI must never call it. Adjacent write/upload/export
verbs seen in the *same* const maps but owned by other surfaces (held out of this section, noted for
trace-back): `UPDATE_VENDOR_DETAILS` / `receivable-vendor/update`, `NON_TRADE_VENDOR` update,
`UPLOAD_ATTACHMENT` (`/vms/api/v2/admin/attachment/save`), the FBZ vendor-debit-note `update` /
`DOWNLOAD_DN` (`api/v2/ips/debit-note`) / `upload-template` / `batch-upload`, `GET_PRESIGNED_URL`
(`config/get-pre-signed-url`), and the ledger `SIGN_OFF_STATEMENT` / `SAVE_SIGNED_COPY` — all
mutating or export/upload flows documented under [[Ledger-Recon-Upload]] · [[Receivables]] · [[Fulfilled-by-Zepto]].

## Live probe (evidence)

- **1 probe fired, read-only GET, then halted** (per the guardrails, stop on first 401/403/429).
  `GET https://fcc.zepto.co.in/api/v1/payment/settlement/sub-type-list` (const `TYPE_FILTER_LIST`,
  an unambiguous pure-GET filter-value read) with the captured vendor JWT returned
  **`HTTP 401 {"message":"Token expired","code":401}`** — the token (`iat 1783887610`,
  `exp 1783967399` = 2026-07-13 18:29:59 UTC) had lapsed ~11 days before this run (2026-07-24). No
  2xx, so **nothing was upgraded to PROVEN**; all endpoints remain **documented (not probed)**.
  Transcript: `captures/vendor/payments-probes.txt`.
- **Auth/base confirmed** by the proven sibling flows on the same host: SALES/INVENTORY
  (`fcc /api/v1/reports*`) and ads (`fcc /ads-bff/api/v1`) work with the identical
  `authorization: <jwt>` header (no `Bearer`), `origin/referer https://brands.zepto.co.in`. Re-run
  these Payments probes with a fresh token to lock down response shapes.
- **Response shapes:** to confirm via live read-only capture. Expected top-level keys (from grid
  usage): `*/filter` → paged rows + total; `*/listing-stat` and `ledger/summary` → status/amount
  count tiles; `payment-advice/reference` → advice header + line references; `getPaymentDocById` →
  a document / presigned reference; `settlement/sub-type-list` → a flat type-value array.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no acknowledge, no upload, no export/generate):

- `zepto payments invoices [--filters … --page …]` → `GET /api/v1/payment/invoice/filter`;
  `zepto payments invoices-stat` → `.../invoice/listing-stat`. Pure READ.
- `zepto payments advice [--filters …]` → `GET /api/v1/payment/payment-advice/filter`;
  `zepto payments advice <reference>` → `.../payment-advice/reference`;
  `zepto payments doc <id> [--out FILE]` → `.../payment-doc/<id>` (saves the document). Pure READ.
- `zepto payments dcn [--sub-type …]` → `GET /api/v1/payment/settlement/filter` (debit/credit
  notes); `zepto payments dcn-requested` → `.../settlement/requested-debit-note/filter`;
  `zepto payments dcn-types` → `.../settlement/sub-type-list`. Pure READ.
- `zepto payments ledger` → `GET /api/v1/payment/ledger/filter`; `zepto payments ledger-summary`
  → `.../ledger/summary`; `zepto payments ledger-zepto` → `/vendor/api/v1/payment/ledger/zepto`.
  Pure READ.
- `zepto payments rv-invoices` → `GET /api/v1/payment/rv-invoice/filter` (+ `.../listing-stat`);
  `zepto payments rv-settlement` → `.../rv-settlement/filter`;
  `zepto payments rv-ledger` → `/vendor/api/v1/payment/rv-ledger/filter`;
  `zepto payments ntv-invoices` → `.../ntv-invoice/filter` (+ `.../listing-stat`). Pure READ.
- **Excluded:** acknowledging an RV invoice (`/api/v1/payment/rv-invoice/<id>/acknowledge`) and any
  update / upload / debit-note-download / sign-off verb — all writes / exports.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] ·
  [[Read-Only-Guardrails]]
- **Tightest siblings** — the money lane splits across dedicated surfaces this note overlaps:
  [[Ledger-Recon-Upload]] (the recon/upload ledger surface behind the `/payments/ledger` route) and
  [[Receivables]] (the receivable / non-trade vendor side behind `rv-invoice` / `ntv-invoice`).
- Upstream billing & goods lanes that feed a payout: [[Invoicing]] (self/off-invoice billing) ·
  [[Purchase-Orders]] (inbound demand) · [[Release-Orders-Amendment-Requests]].
- Settlement debit notes trace back to recoveries in [[Fulfilled-by-Zepto]] (rebates / debit notes /
  packaging) and to returns in [[RTV]] — those adjustments settle here.
- Filter-seed & receivable-vendor lookups it references live in [[Platform-Common]] (commons
  search) and [[Receivables]].
