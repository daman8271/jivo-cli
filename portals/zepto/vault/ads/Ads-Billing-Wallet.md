---
title: Ads Billing & Wallet
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, ads, ads-billing-wallet]
status: studied
---

# Ads Billing & Wallet

The **Ads Billing & Wallet** section is the **money side of Zepto Ads** — the ad-account
**wallet** JIVO funds to run campaigns (balance, transactions, transfer/asset limits, recharge)
and the **billing** ledger Zepto raises against that ad spend (billing runs, per-record details,
vendor billing code, and generated ad-spend invoices). For JIVO this is Jivo Wellness Pvt. Ltd.
(`manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, Manufacturer / STANDARD tier; ads
`brand_id b3550d5d-fc71-47b0-af4f-f221f909b936`). It is the ad-lane counterpart of the vendor-lane
[[Payments]] surface: campaigns are booked in [[Ads-Campaigns-Booking-Keywords]], the wallet here
pays for them, and Zepto's billing runs invoice the consumed spend. Recharge routes wallet money in
via a Juspay payment SDK; a bulk-upload flow lets finance reconcile billing in Excel.

The endpoint contracts below were extracted from the **ads** micro-frontend (remote 632) code-split
chunks — chiefly **`captures/js/ads/1183.8940422c8268d8dc.js`** (the billing + wallet-recharge API
const maps: `n={GET_BILLING_DATA…}`, the `E={WALLET_METADATA…}` wallet map, the `JUSPAY_SDK`
payment map, and the `getBillingDetailsById`/`getPaymentStatus`/`getBulkDataList` id-templated
helpers), plus **`captures/js/ads/8046.1433017a95faec2b.js`** and
**`captures/js/ads/469.ba55b215c9a03211.js`** (the `wallet/details` + `wallet/transfer/asset-limits`
+ `wallet/transfer` service class `i`) — **not** live captures. All calls hit a single host,
**`fcc.zepto.co.in`**, under the `ads-bff/api/v1/*` prefix (the same ads-BFF backend the proven ads
2x2 products/brands pulls use). One JWT (header `authorization: <jwt>`, **no** `Bearer` prefix)
authenticates all of them; WAF headers were not enforced at last capture. Some const values are
written without the leading slash (e.g. `"ads-bff/api/v1/wallet/details"`) but resolve to the same
`/ads-bff/api/v1/...` path — normalised below.

## SPA route(s)

Three routes, all under the ads remote's `/ads/wallet` tree:

- `/ads/wallet` — Wallet landing (balance, transactions, billing grid).
- `/ads/wallet/edit/:roId` — Edit a wallet entry against a release-order id (`roId`).
- `/ads/wallet/recharge` — Recharge flow (Juspay payment SDK → initiate → poll status).

These are ads-lane pages rendered by the ads remote (632) against the `fcc.zepto.co.in` backend.
The wallet funds the campaigns booked under [[Ads-Campaigns-Booking-Keywords]].

## Backend host(s)

- **`fcc.zepto.co.in`** — the sole host for this section. Path families:
  `ads-bff/api/v1/billing*` (billing runs, details, vendor code, summary, bulk-download,
  generate-invoice), `ads-bff/api/v1/wallet/*` + `ads-bff/api/v1/wallets/metadata` (wallet
  details / transactions / metadata / transfer-limits / transfer / S3 recharge-proof / payment
  initiate + status), `ads-bff/api/v1/file-job/*` (the billing bulk upload/download jobs),
  `ads-bff/api/v1/inventory/slots*` (ad-slot pricing-CSV upload + its history — adjacent pricing
  surface bundled in the same chunk), and `ads-bff/api/v1/layout/config/*` (billing table
  metadata).

## API endpoints (READ)

All rows below are pure reads (list / summary / detail / config / status / file-fetch of
already-generated content). Method shown as wired in the chunk: `GET` = confirmed constant binding
or observed service call; `UNKNOWN` = the constant/template is present but the verb was not directly
observed in this chunk (these are listing/detail/status/metadata constants used by read views, so
their effect is a read — verb to confirm on a live capture). `${e}` = a path-param id
(billing-record id, file-job id, or payment id). None probed live (single probe → HTTP 429, token
expired; see Live probe).

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/ads-bff/api/v1/billing` | Billing runs list grid — `GET_BILLING_DATA` (the wallet/billing landing) | READ |
| GET | `/ads-bff/api/v1/billing/summary` | Billing summary / stat tiles — `GET_BILLING_SUMMARY` | READ |
| GET | `/ads-bff/api/v1/billing-details` | Billing line details — `GET_BILLING_DETAILS` | READ |
| UNKNOWN | `/ads-bff/api/v1/billing/${e}` | Single billing record by id — `getBillingDetailsById` | READ (verb to confirm) |
| GET | `/ads-bff/api/v1/billing-code` | Vendor billing code — `GET_VENDOR_CODE` | READ |
| UNKNOWN | `/ads-bff/api/v1/billing/bulk-download` | Download an already-generated billing bulk file — `BILLING_BULK_DOWNLOAD` | READ (file) |
| GET | `/ads-bff/api/v1/layout/config/billing_management_table_metadata` | Billing grid column/config metadata — `GET_TABLE_METADATA` | READ |
| GET | `/ads-bff/api/v1/layout/config/billing_bulk_upload_table_metadata` | Bulk-upload table column/config metadata (read-only config) — `GET_BILLING_BULK_UPLOAD_TABLE_METADATA` | READ (config) |
| GET | `/ads-bff/api/v1/users/details` | Booking/billing user details — `GET_BOOKING_USER_DETAILS` (`KING_USER_DETAILS`) | READ |
| GET | `/ads-bff/api/v1/wallet/details` | Ad-wallet balance / details — service `getWalletDetails` (chunks 469/8046) | READ |
| GET | `/ads-bff/api/v1/wallet/transfer/asset-limits` | Wallet transfer asset-limits (max transferable per asset) — `getWalletAssetLimits` | READ |
| UNKNOWN | `/ads-bff/api/v1/wallet/details` | Wallet details — alias const `WALLET_DETAILS` in the `E={…}` map (same path as above via a different const map) | READ (verb to confirm) |
| UNKNOWN | `/ads-bff/api/v1/wallet/transactions` | Wallet transaction ledger — `WALLET_TRANSACTIONS` | READ (verb to confirm) |
| UNKNOWN | `/ads-bff/api/v1/wallets/metadata` | Wallet metadata (asset types / config) — `WALLET_METADATA` | READ (verb to confirm) |
| UNKNOWN | `/ads-bff/api/v1/wallet/payment/status/${e}` | Recharge payment status by payment id — `getPaymentStatus` | READ (verb to confirm) |
| UNKNOWN | `/ads-bff/api/v1/file-job/view/${e}` | View a file-job (bulk upload/download job) status/rows — `getBulkDataList` | READ (verb to confirm) |
| GET | `/ads-bff/api/v1/inventory/slots/listing` | Ad-slot pricing-CSV upload history list — `GET_PRICING_UPLOAD_HISTORY_LIST` (adjacent pricing surface) | READ |

**Alias / adjacent note.** The two `/ads-bff/api/v1/wallet/details` rows are the **same endpoint**
referenced by two different const maps (the `i.getWalletDetails` service in chunks 469/8046 and the
`WALLET_DETAILS` const in the `E={…}` map in chunk 1183) — kept as separate rows because they are two
distinct bindings in the section data. The `inventory/slots/listing` read belongs to the ad-slot
**pricing** feature (its upload sibling is held out below); it is a genuine GET history list.

## Out of scope (writes) — never expose in a read-only CLI

DOCUMENTED-FROM-BUNDLE ONLY. A strict read-only CLI must never call any of these — they generate,
upload, move money, or initiate a payment.

| METHOD | Path | Purpose | Why held out |
|---|---|---|---|
| POST | `/ads-bff/api/v1/billing/generate-invoice` | **Generate** an ad-spend invoice — `GENERATE_INVOICE` | Creates/generates a billing invoice document. EXPORT/WRITE. |
| POST (upload) | `/ads-bff/api/v1/file-job/UPLOAD/BILLING_BULK_UPLOAD` | **Bulk-upload** a billing reconciliation file — `BILLING_BULK_UPLOAD` | Uploads a file / enqueues an upload job. UPLOAD/EXPORT. |
| GET (upload presign) | `/ads-bff/api/v1/file-job/get-signed-url` | Mint an **upload** presigned URL for the billing bulk-upload — `GET_UPLOAD_PRESIGNED_URL` | Exists solely to enable an S3 upload. UPLOAD/EXPORT. |
| POST | `/ads-bff/api/v1/inventory/slots` | **Upload** ad-slot pricing CSV — `UPLOAD_PRICING_CSV` | Uploads pricing data (mutates slot pricing). UPLOAD/EXPORT. |
| POST | `/ads-bff/api/v1/wallet/transfer` | **Transfer** wallet funds between assets — `transferWalletAmount` | Moves money between wallet assets. WRITE. |
| POST | `/ads-bff/api/v1/wallet/payment/initiate` | **Initiate** a wallet recharge payment — `INITIATE_PAYMENT` | Starts a real payment. WRITE / PAY. |
| UNKNOWN (payment) | `/ads-bff/api/v1/wallet/payment/initiate-sdk-payload` | Build the Juspay payment **SDK payload** for recharge — `INITIATE_JUSPAY_SDK` | Part of the recharge payment-initiation flow. WRITE / PAY. |
| GET (upload presign) | `/ads-bff/api/v1/wallet/s3/presigned-url` | Recharge-proof **S3 presigned URL** (pairs with save-upload-key) | Feeds a proof-of-payment upload; held out under the ABSOLUTE read-only law even though it is a GET. UPLOAD/EXPORT. |
| POST | `/ads-bff/api/v1/wallet/s3/save-upload-key` | **Save** the uploaded recharge-proof S3 key — `WALLET_SAVE_UPLOAD_KEY` | Records/commits an upload. WRITE / UPLOAD. |

Adjacent write/delete verbs seen in the *same* const maps but owned by other ads surfaces (held out
of this section, noted for trace-back): `deleteBooking` / `editBooking` / `submit-for-approval`
(`/ads-bff/api/v1/booking/${e}*`) belong to [[Ads-Campaigns-Booking-Keywords]];
`DOWNLOAD_ANALYTICS_METRICS` (`ads-bff/api/v1/brands/analytics/reports`) and
`release-order/s3/presigned-url` belong to [[Brand-Analytics]] / [[Release-Orders-Amendment-Requests]].

## Live probe (evidence)

- **1 probe fired, read-only GET, then halted** (per the guardrails, stop on first 401/403/429).
  `GET https://fcc.zepto.co.in/ads-bff/api/v1/wallet/details` (service `getWalletDetails`, an
  unambiguous pure-GET wallet read — name has `wallet`+`details`, none of the excluded verbs) with
  the captured `ecom1@jivo.in` JWT returned **`HTTP 429`** (empty body). The token
  (`iat 1783887610`, `exp 1783967399` = 2026-07-13 18:29:59 UTC) had lapsed ~11 days before this
  run (2026-07-24), same expiry that 429'd/401'd every other Zepto section this run. No 2xx, so
  **nothing was upgraded to PROVEN**; all 26 endpoints remain **documented (not probed)**.
  Transcript: `captures/ads/ads-billing-wallet-probes.txt`.
- **Auth/base confirmed** by the proven sibling ads flows on the same host: the ads 2x2
  products/brands × range/daily pulls (`fcc /ads-bff/api/v1`) work with the identical
  `authorization: <jwt>` header (no `Bearer`). Re-run these Billing/Wallet probes with a fresh token
  to lock down response shapes.
- **Response shapes:** to confirm via live read-only capture. Expected top-level keys (from grid /
  service usage): `billing` → paged billing rows + total; `billing/summary` → status/amount tiles;
  `billing-details` / `billing/${e}` → per-record billing breakdown; `wallet/details` → balance +
  asset ledger; `wallet/transactions` → paged transaction rows; `wallets/metadata` → asset-type
  config; `wallet/transfer/asset-limits` → per-asset max amounts; `wallet/payment/status/${e}` →
  a payment-state field; `file-job/view/${e}` → job status + rows; `inventory/slots/listing` →
  pricing-upload history rows; `layout/config/*_table_metadata` → column definitions.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no generate-invoice, no upload/presign, no transfer, no
payment-initiate):

- `zepto ads billing list [--filters … --page …]` → `GET /ads-bff/api/v1/billing`;
  `zepto ads billing summary` → `.../billing/summary`;
  `zepto ads billing details [--filters …]` → `.../billing-details`;
  `zepto ads billing get <id>` → `.../billing/<id>`;
  `zepto ads billing code` → `.../billing-code`;
  `zepto ads billing bulk-download [--out FILE]` → `.../billing/bulk-download` (saves the file).
  Pure READ.
- `zepto ads wallet details` → `GET /ads-bff/api/v1/wallet/details`;
  `zepto ads wallet transactions [--page …]` → `.../wallet/transactions`;
  `zepto ads wallet metadata` → `.../wallets/metadata`;
  `zepto ads wallet limits` → `.../wallet/transfer/asset-limits`;
  `zepto ads wallet payment-status <id>` → `.../wallet/payment/status/<id>`. Pure READ.
- `zepto ads billing job <id>` → `.../file-job/view/<id>` (bulk-job status);
  `zepto ads pricing history` → `.../inventory/slots/listing`;
  `zepto ads billing table-config` → `.../layout/config/billing_management_table_metadata`. Pure READ.
- **Excluded:** generating an invoice, any billing/pricing/recharge-proof **upload** or
  **presigned-url**, wallet **transfer**, and recharge **payment initiate / SDK payload** — all
  writes / exports / payments.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] ·
  [[Read-Only-Guardrails]]
- **Tightest sibling** — the wallet funds the ad bookings and the billing invoices the spend:
  [[Ads-Campaigns-Booking-Keywords]] (same `booking` const map; campaigns draw down this wallet).
- Money-lane counterpart on the vendor side: [[Payments]] (vendor invoices/settlement) — this note
  is the ads-spend equivalent (wallet + ad-billing).
- Adjacent ads surfaces sharing the same const maps: [[Brand-Analytics]] (analytics-report export),
  [[Release-Orders-Amendment-Requests]] (release-order presign), [[Creative-Management]] ·
  [[Brands-Audiences]].
- Filter-seed / commons lookups it references live in [[Platform-Common]].
