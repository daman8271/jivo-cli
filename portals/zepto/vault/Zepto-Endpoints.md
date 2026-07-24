---
title: Zepto Endpoints (read-only master index)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, seller, endpoints, master-index]
---

# Zepto Seller Portal — Read-Only Master Endpoint Inventory

Consolidated endpoint spec for JIVO's **Zepto** seller portal, every endpoint across all 25 section notes, grouped **vendor → ads → platform**. This is the source of truth a future **read-only** CLI is generated from: `READ` / `READ (file)` rows are safe to expose; `UNKNOWN` rows have a binding but the method / read-vs-write is not resolved from the bundle (treat as *to confirm*, do **not** wire in blind); everything in [Out of scope (writes/exports)](#out-of-scope-writesexports) mutates or side-effects and must **never** be exposed.

Atlas: [[00-Zepto-Atlas]] · Data model: [[Zepto-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]]

> WARNING: READ-ONLY study. Contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) — API-constant + `doHttpGet`/`doHttpPost` bindings — not from any new live call. Method/host/path/const/read-write are taken **verbatim** from `captures/js/sections.json`. No write was ever fired; writes & exports are documented **out of scope** only.

## Auth & base (from FACTS)

**Backends (one JWT spans all):**

| Backend host | Scope |
|---|---|
| `fcc.zepto.co.in` | Vendor reports + `/ads-bff` ads + most catalog/PO/invoice/payment data |
| `auth-backend.zepto.co.in` | Identity / access-management / subscription / KYC / brands / config |
| `financenew.zepto.co.in` | Finance / receivables / ledger |
| `scpfin.zepto.co.in` | Supply-chain finance |
| `brands-onboarding.zepto.co.in` | Onboarding / KYC |
| `ads-platform.zepto.co.in` | Ads platform |
| `partner.zepto.co.in` | Partner |
| `events.zepto.co.in` | Client telemetry / events |

**Required header (every data-API call):**

```http
authorization: <JWT>        # raw token, NO "Bearer " prefix
```

- WAF is **not** enforced. One JWT (obtained via login `ecom1@jivo.in`) is accepted across all backends above.
- **Entity:** Jivo Wellness Pvt. Ltd. — Manufacturer, tier `STANDARD`. `manufacturer_id = 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`.
- **Ads:** `brand_id = b3550d5d-fc71-47b0-af4f-f221f909b936`.

**Read/Write legend:** `READ` = pure JSON query · `READ (file)` = downloads a PDF/CSV/XLSX/ZIP binary · `UNKNOWN` = binding present but HTTP method / read-vs-write not resolved from the bundle → **to confirm** before exposing · `WRITE` = mutates business data/state · `EXPORT` = side-effecting export job (creates a report-request row, often emails a copy — not a pure read).

> **Path column** is written `host/path` so the backend is unambiguous per row. Path templating (`${e}`, `:id`) is preserved verbatim from the bundle.

---

# Vendor lane

## [[Purchase-Orders]]

Purchase Orders — 25 endpoints (24 read/to-confirm, 1 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `fcc.zepto.co.in/api/v1/grn/${e}` | get GRN Details By ID | READ |
| GET | `fcc.zepto.co.in/api/v1/grn/${e}/asn-info` | get ASN By GRN ID | READ |
| GET | `fcc.zepto.co.in/api/v1/grn/${e}/items` | get GRN Items By ID | READ |
| GET | `fcc.zepto.co.in/api/v1/grn/filter` | GET GRN Listing | READ |
| GET | `fcc.zepto.co.in/api/v1/grn/user/mh-list` | External Location Filter List | READ |
| GET | `fcc.zepto.co.in/api/v1/grn/user/vendor-list` | External Vendor Filter List | READ |
| GET | `fcc.zepto.co.in/api/v1/po/${e}` | get PO Details By ID | READ |
| GET | `fcc.zepto.co.in/api/v1/po/${e}/asn` | get ASN By PO ID | READ |
| GET | `fcc.zepto.co.in/api/v1/po/${e}/attachments` | get PO Documents By ID | READ |
| GET | `fcc.zepto.co.in/api/v1/po/${e}/checklist` | get PO Checklist By ID | READ |
| GET | `fcc.zepto.co.in/api/v1/po/${e}/grn` | get GRN By PO ID | READ |
| GET | `fcc.zepto.co.in/api/v1/po/${e}/items` | get PO Items By ID | READ |
| GET | `fcc.zepto.co.in/api/v1/po/${e}/logs` | get PO Activity Logs By ID | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/po/acknowledge` | Acknowledge PO | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/po/filter` | GET PO Listing | READ |
| GET | `fcc.zepto.co.in/api/v1/po/ib-capacity` | GET IB Capacity | READ |
| GET | `fcc.zepto.co.in/api/v1/po/listing-stat` | GET PO Summary | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/po/request-schedule` | Request PO | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/po/reschedule` | Reschedule PO | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/po/schedule` | Schedule PO | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/po/scheduled` | GET Scheduled PO Summary | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/po/unschedule` | Unschedule PO | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/po/user/mh-list` | External Location Filter List | READ |
| GET | `fcc.zepto.co.in/api/v1/po/user/vendor-list` | External Vendor Filter List | READ |

> **Out of scope:** 1 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[ASN]]

ASN (Advance Shipping Notices) — 34 endpoints (25 read/to-confirm, 9 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `fcc.zepto.co.in/api/v1/asn/${e}` | get ASN Details By ID | READ |
| GET | `fcc.zepto.co.in/api/v1/asn/${e}/attachments` | get ASN Documents | READ |
| GET | `fcc.zepto.co.in/api/v1/asn/${e}/cancel` | get Cancel ASN | READ |
| GET | `fcc.zepto.co.in/api/v1/asn/${e}/csv-details` | get Create ASN Template | READ |
| GET | `fcc.zepto.co.in/api/v1/asn/${e}/failure-csv-details` | get Mrp Cost Sheet Template | READ |
| GET | `fcc.zepto.co.in/api/v1/asn/${e}/grn-info` | get GRN By ASN ID | READ |
| GET | `fcc.zepto.co.in/api/v1/asn/${e}/items` | get ASN Items By ID | READ |
| GET | `fcc.zepto.co.in/api/v1/asn/${e}/settlement-info` | get Dn Cn Details | READ |
| GET | `fcc.zepto.co.in/api/v1/asn/filter` | GET ASN Listing | READ |
| GET | `fcc.zepto.co.in/api/v1/asn/list` | GET ASN Summary List | READ |
| GET | `fcc.zepto.co.in/api/v1/asn/user/mh-list` | External Location Filter List | READ |
| GET | `fcc.zepto.co.in/api/v1/asn/user/vendor-list` | External Vendor Filter List | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/${e}` | ASN | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/${e}/cancel` | ASN cancel | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/${e}/clone` | ASN clone | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/${e}/documents` | ASN documents | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/${e}/product-csv` | ASN product CSV | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/${e}/status` | ASN status | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/calculate` | ASN calculate | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/draft` | ASN draft | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/draft/${e}` | ASN draft | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/invoice/ocr` | ASN invoice ocr | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/listing` | ASN listing | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/product-csv` | ASN product CSV | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/asn/submit` | ASN submit | UNKNOWN |

> **Out of scope:** 9 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Release-Orders-Amendment-Requests]]

Release Orders & Amendment Requests — 16 endpoints (13 read/to-confirm, 3 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/release-order` | release order | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/release-order/${e}` | release order | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/release-order/approvers/${e}` | release order approvers | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/release-order/meta` | release order meta | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/release-order/s3/presigned-url` | release order s3 presigned URL | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/amendment-requests` | Amendment Requests | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/amendment-requests/${e}` | amendment Request By ID | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/amendment-requests/${e}/review` | amendment Request Review | READ |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/amendment-requests/${e}/state-timeline` | amendment Request State Timelines | UNKNOWN |
| GET | `fcc.zepto.co.in/contractservice/api/v1/amendment-requests/list` | Amendment Requests List | READ |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/amendment-requests/pending-on-reviewer` | Amendment Requests Pending ON Reviewer | READ |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/bulk-jobs/${e}/amendment-requests` | bulk Job Amendment Requests | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/amendment-requests` | contract Amendment Requests | UNKNOWN |

> **Out of scope:** 3 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[RTV]]

RTV (Return to Vendor) — 11 endpoints (11 read/to-confirm, 0 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `fcc.zepto.co.in/api/v1/rtv/filter` | GET RTV Listing | READ |
| GET | `fcc.zepto.co.in/api/v1/rtv/listing-stat` | GET RTV Summary | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/rtv/schedule` | Schedule RTV | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/rtv/user/mh-list` | External Location Filter List | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/rtv/${e}/list-packing-slips` | get Packing Slips By ID | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/rtv/${e}/packing-slips/${t}/job` | RTV packing slips job | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/rtv/download/${e}/attachments/${t}` | RTV download attachments | READ (file) |
| GET | `fcc.zepto.co.in/vendor/api/v2/rtv/${e}` | get RTV Details By ID | READ |
| GET | `fcc.zepto.co.in/vendor/api/v2/rtv/${e}/checklist` | get RTV Checklist By ID | READ |
| GET | `fcc.zepto.co.in/vendor/api/v2/rtv/${e}/items` | get RTV Items By ID | READ |
| GET | `fcc.zepto.co.in/vendor/api/v2/rtv/filter` | GET RTV Listing V2 | READ |

---

## [[Catalog-Health]]

Catalog & Catalog Health — 27 endpoints (24 read/to-confirm, 3 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/catalog` | catalog | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/catalog/metadata` | catalog metadata | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/catalog/validate` | catalog validate | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/media/attachments` | media attachments | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/validate_pvids` | validate pvids | UNKNOWN |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog-health-dashboard/attribute-view` | GET Attribute View | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog-health-dashboard/get-l4-values/${e}` | get All Attibutes For Pv ID | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog-health-dashboard/sku-rule-scores` | GET SKU Rule Scores | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog-health-dashboard/sku-ruleset-score/overview` | GET SKU Ruleset Score Overview | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog-health-dashboard/sku-ruleset-scores` | GET Product Scores | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog-health-dashboard/suggestions/get-attributes-by-pv-id` | GET Attributes BY PV ID | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/catalog-health-dashboard/suggestions/send-for-review` | Send FOR Review | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/catalog-health-dashboard/suggestions/send-to-vendor` | Send TO Vendor | UNKNOWN |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog/category-hierarchy/search` | Search Categories | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog/failed-download` | Failed Download | READ (file) |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog/sku-onboarding/drafts` | GET Drafts | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/catalog/sku-onboarding/export` | Export SKU Attributes | UNKNOWN |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog/sku-onboarding/list` | SKU Onboarding List | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/catalog/sku-onboarding/presigned-url` | Presigned URL | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/catalog/sku-onboarding/send-to-cm` | Send TO CM | UNKNOWN |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog/sku-onboarding/skus` | GET Skus | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/catalog/sku-onboarding/template` | GET CSV Template | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v2/product_onboarding` | p | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v2/product_onboarding/template` | product onboarding template | UNKNOWN |

> **Out of scope:** 3 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Stock-View-Inventory]]

Stock View & Inventory — 9 endpoints (9 read/to-confirm, 0 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/inventory/availability` | inventory availability | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/stock-view/availability/city-level-performance` | we | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/stock-view/availability/product-level-performance` | Ve | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/stock-view/availability/store-level-performance` | Fe | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/stock-view/availability/summary` | Me | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/stock-view/inventory/city-level-performance` | je | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/stock-view/inventory/product-level-performance` | He | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/stock-view/inventory/store-level-performance` | ke | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/stock-view/inventory/summary` | Be | UNKNOWN |

---

## [[Vendor-Reports-Queue]]

Vendor Reports Queue — 5 endpoints (4 read/to-confirm, 1 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `fcc.zepto.co.in/api/v1/reports` | GET Reports Listing | READ |
| GET | `fcc.zepto.co.in/api/v1/reports/${e}/download` | download Reports | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/reports/${e}/retry` | retry Reports | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/reports/request` | Request Download Report,request Report | READ (file) |

> **Out of scope:** 1 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Invoicing]]

Invoicing (Self-Invoice & Off-Invoice) — 20 endpoints (12 read/to-confirm, 8 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/off-invoice-details-template` | download Off Invoice Details Template | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/off-invoice/contracts/${e}/off-invoice-rules` | create Off Invoice Rules,get Off Invoice Rules | UNKNOWN |
| GET | `fcc.zepto.co.in/contractservice/api/v1/off-invoice/off-invoice-rules/${e}/tracking` | get Tracking | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/off-invoice/off-invoice-rules/get-config` | GET OFF Invoice Config | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/off-invoice/off-invoice-rules/template` | Download Template | READ (file) |
| GET | `fcc.zepto.co.in/invoice/api/v1/self-invoice/non-trade/${e}/details` | get Invoice Details | READ |
| GET | `fcc.zepto.co.in/invoice/api/v1/self-invoice/non-trade/${e}/documents` | get Self Invoice S3 URL | READ |
| GET | `fcc.zepto.co.in/invoice/api/v1/self-invoice/non-trade/entity-names` | GET Entity Names | READ |
| GET | `fcc.zepto.co.in/invoice/api/v1/self-invoice/non-trade/gstin-state` | GET Gstin State | READ |
| GET | `fcc.zepto.co.in/invoice/api/v1/self-invoice/non-trade/list` | GET Invoice List | READ |
| UNKNOWN | `fcc.zepto.co.in/invoice/api/v1/self-invoice/non-trade/poll-ocr` | Self Invoice OCR | UNKNOWN |
| GET | `fcc.zepto.co.in/invoice/api/v1/self-invoice/non-trade/summary` | GET Invoice Summary | READ |

> **Out of scope:** 8 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Vendor-Contracts-Margins]]

Vendor Contracts, Margins & Incentives — 55 endpoints (38 read/to-confirm, 17 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/download` | vendor pv margin download | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/status-config` | vendor pv margin status config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/vendor` | vendor pv margin | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/vendor/base-margin` | vendor pv margin base margin | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/vendor/download` | vendor pv margin download | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/vendor/filter` | vendor pv margin filter | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/vendor/pv-list` | vendor pv margin pv list | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/vendor/pv-list/download` | vendor pv margin pv list download | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/vendor/pv/update-fields` | vendor pv margin pv update fields | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/cdf` | It | UNKNOWN |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/deq-details-template` | download De QDetails Template | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/download-deq-data` | download Consolidated Deq Details | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/download-margin-data` | download Consolidated Contract Margins | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/download-on-invoice-data` | download Consolidated On Invoice Data | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/download-stock-correction-data` | download Consolidated Stock Correction Details | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/download-stock-data` | download Consolidated RTV Data | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/item-margin-details-template` | download Margin Details Template | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/item-stock-details-template` | download Stock Details Template | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/on-invoice-details-template` | download On Invoice Details Template | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/stock-correction-details-template` | download Stock Correction Details Template | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-incentive/${e}/list-item-margin-details` | list Item Margin Details For Contract | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/margin-incentive/list-item-margin-details` | List Item Margin Details Global | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}` | get Contract Details | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/activity-log` | get Activity Logs By Contract ID | READ |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/amendment-reviewers` | amendment Reviewers | READ |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/discard` | discard Draft Contract | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/logs` | contract Logs | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/payment-terms` | get Vendor Payment Terms,submit Payment Terms | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/publish` | publish Contract | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/review` | review Contract | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/state-timeline` | get Contract States | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/activity-log` | GET ALL Activity Logs | READ |
| UNKNOWN | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/bulk-publish` | Bulk Publish Contracts | UNKNOWN |
| GET | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/get-filtered-contracts` | GET Filtered Contracts | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/listing-summary` | GET Contracts Summary | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/pending-on-approver` | GET Approval Contracts | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/static-config` | GET Roles,get Static Config | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/users` | GET Users FOR Role | READ |

> **Out of scope:** 17 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Payments]]

Payments & Settlements — 18 endpoints (18 read/to-confirm, 0 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `fcc.zepto.co.in/api/v1/payment/invoice/filter` | GET Invoice List | READ |
| GET | `fcc.zepto.co.in/api/v1/payment/invoice/listing-stat` | GET Invoice Summary | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/payment/ledger/filter` | v | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/payment/ledger/summary` | O | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/payment/ntv-invoice/filter` | GET Invoice CN List | READ |
| GET | `fcc.zepto.co.in/api/v1/payment/ntv-invoice/listing-stat` | GET Invoice CN Summary | READ |
| GET | `fcc.zepto.co.in/api/v1/payment/payment-advice/filter` | GET Payment Advice Listing | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/payment/payment-advice/reference` | Payment Advice Details | READ |
| GET | `fcc.zepto.co.in/api/v1/payment/payment-doc/${e}` | get Payment Doc By ID | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/payment/rv-invoice/${e}/acknowledge` | acknowledge Invoice | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/payment/rv-invoice/filter` | GET Total Invoices | READ |
| GET | `fcc.zepto.co.in/api/v1/payment/rv-invoice/listing-stat` | GET Invoice Listing Stat | READ |
| GET | `fcc.zepto.co.in/api/v1/payment/rv-settlement/filter` | GET Total DN CN | READ |
| GET | `fcc.zepto.co.in/api/v1/payment/settlement/filter` | GET Debit AND Credit Note List | READ |
| GET | `fcc.zepto.co.in/api/v1/payment/settlement/requested-debit-note/filter` | GET Requested Debit AND Credit Note List | READ |
| GET | `fcc.zepto.co.in/api/v1/payment/settlement/sub-type-list` | Type Filter List | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/payment/ledger/zepto` | GET Zepto Ledger Listing | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/payment/rv-ledger/filter` | GET RV Ledger Filter | READ |

---

## [[Ledger-Recon-Upload]]

Ledger (Recon & Upload) — 16 endpoints (10 read/to-confirm, 6 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/reconciliation/inventory/reports` | tt | UNKNOWN |
| GET | `fcc.zepto.co.in/vendor/api/v1/ledger-recon/external-view/status` | GET External View Status | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/ledger-recon/external-view/toggle` | Toggle External View | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/ledger-recon/recon-user-data` | GET Recon User Data | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/ledger-recon/statement/details` | t | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/ledger-recon/statement/save-signed-copy` | Tt | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/ledger-recon/statement/sign-off` | dt | UNKNOWN |
| GET | `fcc.zepto.co.in/vendor/api/v1/ledger-recon/working/closing-balances` | GET Closing Balances | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/ledger-recon/working/filter` | GET Recon Workings Listing | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/ledger-upload/bulk-download` | Et | READ (file) |

> **Out of scope:** 6 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Receivables]]

Receivables & Non-Trade Vendor — 9 endpoints (4 read/to-confirm, 5 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/ntv` | OCR Invoice Check | UNKNOWN |
| GET | `fcc.zepto.co.in/vms/api/v1/non-trade-vendor/filter` | GET NON Trade Vendors | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/non-trade-vendor/kyc` | GET KYC Details | READ |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v1/receivable-vendor/filter` | GET Receivable VENDORS,path | READ |

> **Out of scope:** 5 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Fulfilled-by-Zepto]]

Fulfilled-by-Zepto (Rebates, Debit Notes & Packaging) — 31 endpoints (21 read/to-confirm, 10 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/rebate/${e}/download-rebate-csv` | FBZ rebate download rebate CSV | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/rebate/${e}/update-rebate-status` | FBZ rebate update rebate status | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/rebate/fetch-all-vendor-codes` | FBZ rebate fetch all vendor codes | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/rebate/fetch-rebate-margin-details` | FBZ rebate fetch rebate margin details | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/rebate/fetch-reports` | FBZ rebate fetch reports | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/rebate/template-download` | FBZ rebate template download | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/rebate/view-rebate-portal` | FBZ rebate view rebate portal | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/${e}` | FBZ vendor debit note | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/${e}/dn-copy/download` | vendor debit note dn copy download | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/${e}/working-dn-copy/download` | vendor debit note working dn copy download | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/approve` | FBZ vendor debit note approve | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/asn/${e}` | FBZ vendor debit note ASN | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/filter` | FBZ vendor debit note filter | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/reject` | FBZ vendor debit note reject | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/status-config` | FBZ vendor debit note status config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/update` | FBZ vendor debit note update | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/packaging/bag-barcode/config` | Se | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/packaging/bag-barcode/confirm` | Re | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/packaging/bag-barcode/download` | Oe | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/packaging/bag-barcode/list` | ve | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/packaging/bag-barcode/preview` | me | UNKNOWN |

> **Out of scope:** 10 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

# Ads lane

## [[Brands-Audiences]]

Brands & Audiences — 29 endpoints (29 read/to-confirm, 0 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `fcc.zepto.co.in/ads-bff/api/v1/brands` | GET Brands List Data | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/brands/subcategory` | GET Subcategoeies List | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/brands/targeting-options` | GET Brand Categories | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/parent-brand` | GET Parent Brands List | READ |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/parent-brand/${e}` | parent brand | UNKNOWN |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/parent-brand/${e}/users` | parent brand users | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brand-insight/metadata` | brand insight metadata | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brand-insight/onboarding` | brand insight onboarding | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brand-insight/section/${e}/data` | brand insight section data | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brand/${e}/smart-nudges` | brand smart nudges | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands` | brands | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/${e}` | brands | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/${e}/audience-reach` | brands audience reach | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/${e}/audience/attributes` | brands audience attributes | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/${e}/audience/estimate` | brands audience estimate | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/${e}/audiences` | brands audiences | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/${e}/saved-audiences` | brands saved audiences | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/brands/analytics/metadata` | GET Headers Data | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/analytics/metrics` | brands analytics metrics | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/analytics/metrics/tabular` | analytics metrics tabular | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/analytics/reports` | brands analytics reports | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/analytics/summary` | Details TAB Summary | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/approvers/${e}` | brands approvers | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/campaigns/analytics/metadata` | get Brand Metrics Data | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/campaigns/analytics/metrics` | campaigns analytics metrics | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/campaigns/analytics/metrics/tabular` | analytics metrics tabular | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/reports` | brands reports | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/subcategory` | get Campaign Headers Meta | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/brands/targeting-options` | brands targeting options | UNKNOWN |

---

## [[Creative-Management]]

Creative Management — 9 endpoints (7 read/to-confirm, 2 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/creative-management/banner` | creative management banner | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/creative-management/banners` | creative management banners | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/creative-management/bundle-config` | creative management bundle config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/creative-management/bundles` | creative management bundles | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/creative-management/inventory/details` | creative management inventory details | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/creative-management/metadata` | creative management metadata | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v2/creative-management/bundles` | creative management bundles | UNKNOWN |

> **Out of scope:** 2 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Ads-Campaigns-Booking-Keywords]]

Ads Campaigns, Booking & Keywords — 47 endpoints (41 read/to-confirm, 6 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `fcc.zepto.co.in/ads-bff/api/v1/agents/jarvis-agent/sessions` | GET Sessions | READ |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/agents/jarvis-agent/sessions/${e}/messages` | jarvis agent sessions messages | UNKNOWN |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/agents/kam-agent/sessions` | GET Sessions | READ |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/agents/kam-agent/sessions/${e}/messages` | kam agent sessions messages | UNKNOWN |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/booking` | Create Booking/list Bookings | READ |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/booking/${e}` | booking | UNKNOWN |
| POST | `fcc.zepto.co.in/ads-bff/api/v1/booking/${e}/media-mix/closure` | booking media mix closure | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/booking/${e}/resend-create-booking-notification` | booking resend create booking notification | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/booking/${e}/submit-for-approval` | booking submit for approval | UNKNOWN |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/booking/download` | List Bookings FOR Download | READ (file) |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/booking/expense-metrics` | GET Summary Metric | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/booking/metadata` | GET Metadata | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/booking/owner` | GET Owners List | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/campaigns` | GET Table Data | READ |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/campaigns/${e}/review` | campaigns review | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/campaigns/reviews` | campaigns reviews | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaign-categories` | campaign categories | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaign-categories/${e}/metadata/${a}` | get Brand Metrics Data/get Campaign Headers Meta | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaign/recommendations/targeting` | campaign recommendations targeting | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaigns` | campaigns | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaigns/${e}` | campaign Status Update | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaigns/${e}/${a}` | campaign Status Update | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/campaigns/debug/${a}` | campaigns debug | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaigns/forecast` | campaigns forecast | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaigns/metadata` | campaigns metadata | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaigns/pla` | campaigns pla | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaigns/pla/${e}` | campaigns pla | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaigns/recommendations/${e}` | campaigns recommendations | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaigns/reviews` | campaigns reviews | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaigns/utp` | campaigns utp | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/campaigns/utp/${e}` | campaigns utp | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/keyword/config` | keyword config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/booking_approval_terms_and_conditions` | layout config booking approval terms and conditions | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/playground/search` | playground search | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/playground/stores` | playground stores | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/playground/update-keyword-metadata` | playground update keyword metadata | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/pricing/promo/ads-utp/tabular` | promo ads utp tabular | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/suggestions/bid` | suggestions bid | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/suggestions/keyword` | suggestions keyword | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/suggestions/subcategory` | suggestions subcategory | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/validate-keywords` | validate keywords | UNKNOWN |

> **Out of scope:** 6 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Ads-Billing-Wallet]]

Ads Billing & Wallet — 26 endpoints (19 read/to-confirm, 7 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `fcc.zepto.co.in/ads-bff/api/v1/billing` | GET Billing Data | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/billing-code` | GET Vendor Code | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/billing-details` | GET Billing Details | READ |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/billing/${e}` | billing | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/billing/bulk-download` | Billing Bulk Download | READ (file) |
| POST | `fcc.zepto.co.in/ads-bff/api/v1/billing/generate-invoice` | Generate Invoice | UNKNOWN |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/billing/summary` | GET Billing Summary | READ |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/file-job/view/${e}` | file job view | UNKNOWN |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/layout/config/billing_management_table_metadata` | GET Table Metadata | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/users/details` | GET Booking User Details | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/wallet/details` | path | READ |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/wallet/payment/status/${e}` | wallet payment status | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/wallet/transfer` | path | UNKNOWN |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/wallet/transfer/asset-limits` | path | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/wallet/details` | wallet details | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/wallet/payment/initiate-sdk-payload` | wallet payment initiate sdk payload | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/wallet/s3/presigned-url` | wallet s3 presigned URL | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/wallet/transactions` | wallet transactions | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/wallets/metadata` | wallets metadata | UNKNOWN |

> **Out of scope:** 7 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Brand-Analytics]]

Brand Analytics (Sales, Live & Landing) — 25 endpoints (25 read/to-confirm, 0 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/landing-page/aov` | te | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/landing-page/bill-penetration` | ae | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/landing-page/header-metrics` | J | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/landing-page/header-metrics-lite` | ee | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/landing-page/product-performance` | ne | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/landing-page/subcategory-heatmap` | se | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/landing-page/top-searched-keywords` | ie | UNKNOWN |
| GET | `fcc.zepto.co.in/brand-analytics-mobile/api/v1/access-management/user` | GET Entity Data FOR Mobile APP | READ |
| GET | `fcc.zepto.co.in/brand-analytics-mobile/api/v1/subscription/pricing-details` | GET Pricing Details Mobile | READ |
| GET | `fcc.zepto.co.in/brand-analytics-mobile/api/v1/subscription/user-details` | GET Subscription Details Mobile | READ |
| GET | `fcc.zepto.co.in/brand-analytics-mobile/api/v1/subscription/visibility-details` | GET Plan Visibility Details Mobile | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/fulfilment/available-in-service-hours` | GET Fulfilment Availble IN Service Hours | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/fulfilment/fill-rate` | GET Fulfilment Fill Rate | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/fulfilment/on-time-in-full` | GET Fulfiment ON Time IN Full | READ |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/live-analytics/conversion-metrics` | q | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/live-analytics/impression-metrics` | Z | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/live-analytics/metric-headers` | W | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/live-analytics/order-metrics` | z | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/live-analytics/product-list` | Q,qe | UNKNOWN |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/resource-last-updated` | GET Resource Last Updated | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/sales-analytics/average-order-value` | SA GET Average Order Value | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/sales-analytics/average-selling-price` | SA GET Average Selling Price PER Unit | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/sales-analytics/offers` | SA GET Offers | READ |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/sales-analytics/product-performance` | brand analytics web sales analytics product performance | UNKNOWN |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/sales-analytics/sales-overview` | SA GET Sales Overview | READ |

---

## [[Market-Geo-Consumer-Insights]]

Market, Geo & Consumer Insights — 39 endpoints (39 read/to-confirm, 0 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/coordinates/decode` | coordinates decode | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/geo-analytics/city-level-performance` | GI GET Hyperlocal City Performance | READ |
| GET | `fcc.zepto.co.in/api/v1/geo-analytics/fulfillment-scorecard` | GI GET GEO Analytics Fulfillment Scorecard | READ |
| GET | `fcc.zepto.co.in/api/v1/geo-analytics/hyperlocal-insights-card` | GI GET Hyperlocal Insights Card | READ |
| GET | `fcc.zepto.co.in/api/v1/geo-analytics/product-level-performance` | GI GET Hyperlocal Product Performance | READ |
| GET | `fcc.zepto.co.in/api/v1/geo-analytics/sales-scorecard` | GI GET GEO Analytics Sales Scorecard | READ |
| GET | `fcc.zepto.co.in/api/v1/geo-analytics/slider-data` | GI GET Slider Data | READ |
| GET | `fcc.zepto.co.in/api/v1/geo-analytics/store-geofence` | GI GET GEO Analytics Store Geofence | READ |
| GET | `fcc.zepto.co.in/api/v1/geo-analytics/store-level-performance` | GI GET Hyperlocal Store Performance | READ |
| GET | `fcc.zepto.co.in/api/v1/geo-analytics/store-locations` | GI GET GEO Analytics Store Locations | READ |
| GET | `fcc.zepto.co.in/api/v1/geo-analytics/store-metrics` | GI GET Hyperlocal Store Metrics | READ |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/elasticity/discount-roi` | Ke | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/elasticity/inventory-pulse` | $e | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/elasticity/pack-size-over-time` | We | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/elasticity/price-volume` | Ye | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/elasticity/shopper-clock` | ze | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/elasticity/trial-to-loyalty` | Xe | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/geo-analytics/city-level-performance` | Te | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/geo-analytics/fulfillment-scorecard` | Ee | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/geo-analytics/hyperlocal-insights-card` | ce | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/geo-analytics/product-level-performance` | Ne | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/geo-analytics/sales-scorecard` | le | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/geo-analytics/slider-data` | e | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/geo-analytics/store-geofence` | Ie | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/geo-analytics/store-level-performance` | Ae | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/geo-analytics/store-locations` | pe | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/geo-analytics/store-metrics` | ue | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/market-share/calculate-bill-penetration` | Market Share Calculate Bill Penetration | UNKNOWN |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/market-share/get-new-users-percentage` | Market Share GET NEW Users Percentage | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/market-share/gmv-and-units` | Market Share GET Market Share GMV AND Units | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/market-share/share-of-voice` | Market Share GET Share OF Voice | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/market-share/top-of-search` | Market Share GET TOP OF Search | READ |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/persona/city-data` | De | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/persona/graph-configs` | Le | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/persona/graph-data` | ge | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/persona/heat-map` | he | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/persona/heat-map-basket-l3-category` | be | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/persona/list` | fe | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/persona/overview` | Ce | UNKNOWN |

---

## [[Engagement]]

Engagement (Survey, Rewards & Zepto Square) — 27 endpoints (23 read/to-confirm, 4 write/export). Hosts: `auth-backend.zepto.co.in`, `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `auth-backend.zepto.co.in/api/v1/zepto-square/city-leaderboard` | GET City Ranking | READ |
| GET | `auth-backend.zepto.co.in/api/v1/zepto-square/city-level-stats` | GET City Level Orders | READ |
| GET | `auth-backend.zepto.co.in/api/v1/zepto-square/india-level-stats` | GET Order Counts | READ |
| GET | `auth-backend.zepto.co.in/api/v1/zepto-square/product-level-stats` | GET Product Level Stats | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/rewards` | rewards | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/rewards/${e}` | rewards | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/rewards/brand/${e}` | rewards brand | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/smart-nudges/${e}` | smart nudges | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/smart-nudges/campaign` | smart nudges campaign | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/survey/events` | survey events | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v2/survey/question-responses` | survey question responses | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v2/survey/questions` | survey questions | UNKNOWN |
| GET | `fcc.zepto.co.in/survey/api/v1/approvals/list` | GET Created Surveys | READ |
| UNKNOWN | `fcc.zepto.co.in/survey/api/v1/approvals/review` | Review Approval | READ |
| GET | `fcc.zepto.co.in/survey/api/v1/survey-analytics/download-responses` | Download Survey Responses | READ (file) |
| GET | `fcc.zepto.co.in/survey/api/v1/survey-analytics/graph-data` | GET Dashboard Graph Data | READ |
| GET | `fcc.zepto.co.in/survey/api/v1/survey-analytics/graph-details` | GET Dashboard Graph Config | READ |
| GET | `fcc.zepto.co.in/survey/api/v1/survey-analytics/metrics` | GET Dashboard Summary | READ |
| GET | `fcc.zepto.co.in/survey/api/v1/survey-creation/${e}/checklist` | get Survey Checklist | READ |
| GET | `fcc.zepto.co.in/survey/api/v1/survey-creation/config` | GET Survey Config | READ |
| GET | `fcc.zepto.co.in/survey/api/v1/survey/${e}` | get Survey Details | READ |
| GET | `fcc.zepto.co.in/survey/api/v1/survey/list` | GET Surveys FOR Brand | READ |
| UNKNOWN | `fcc.zepto.co.in/survey/api/v1/survey/view-all` | View ALL Surveys | READ |

> **Out of scope:** 4 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

# Platform lane

## [[KYC-Onboarding]]

KYC & Vendor Onboarding (VMS) — 81 endpoints (59 read/to-confirm, 22 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/kyc/gstin-details` | KYC gstin details | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/kyc/action-to-purchase` | KYC Action TO Purchase | UNKNOWN |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/kyc/average-revenue-per-user` | KYC GET Revenue PER User | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/kyc/brand-recall` | KYC GET Brands Recall | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/kyc/customer-penetration` | KYC GET Customer Penetration | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/kyc/customer-retention` | KYC GET Customer Retention | READ |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/kyc/overall-conversion` | KYC Overall Conversion | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/kyc/overall-conversion-funnel` | KYC Overall Conversion Funnel | UNKNOWN |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/kyc/product-view-to-action` | KYC GET Product View TO Action | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/kyc/top-searched-keywords` | KYC GET TOP Searched Keywords | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/attachment` | GET Attachment Content | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/attachment/pre-signed-url` | Download Attachment | READ (file) |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/bank-details/fetch` | GET Bank Details | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/basic-details/contract-details` | GET VRF Details | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/basic-details/fetch-contracts` | GET Contract Details | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/basic-details/onboarding-filter` | GET Filtered List | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/basic-details/onboarding-summary` | GET Summary | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/common/category` | GET Catgories | READ |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v1/admin/common/lead-status-config` | Leads Status Config | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/common/mappings` | GET Mappings | READ |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v1/admin/common/onboarding-status-config` | Onboarding Status Config | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/common/vendor-attachments` | GET Vendor Attachments | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/config` | GET Config | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/distributor/filter` | GET Distributor List | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/kyc/fetch` | GET KYC Details | READ |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v1/admin/kyc/pan-verification` | PAN Verification | UNKNOWN |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/lead/filter` | GET ALL Leads | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/lead/get-user-details` | GET User Details | READ |
| POST | `fcc.zepto.co.in/vms/api/v1/admin/lead/invite` | Invite Lead | UNKNOWN |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/lead/summary` | GET Summary | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/marketer/${e}` | get Marketer Details By ID | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/marketer/filter` | GET Marketer List | READ |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v1/admin/marketer/link-marketer` | Link Marketer | UNKNOWN |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/marketer/search` | Search Marketer,search Marketer BY Query | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/bank-details/fetch` | GET Bank Details | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/contract-details` | GET VRF Details | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/fetch-contracts` | GET Contract Details | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/onboarding-filter` | GET Filtered List | READ |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/onboarding-status-config` | Onboarding Status Config | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/onboarding-summary` | GET Summary | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/vendor-attachments` | GET Vendor Attachments | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/warehouse-details/fetch` | GET Vendor Details | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/user/lead` | GET Lead Details | READ |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v1/admin/user/modification-requested` | Request Modification | UNKNOWN |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/user/non-trade-vendor/approval-onboarding-data` | GET Approval Data | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/user/non-trade-vendor/profile` | GET Vendor Profile | READ |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v1/admin/user/non-trade-vendor/review` | Unified Review | READ |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v1/admin/user/send-reminder-mail` | Send Reminder Mail | UNKNOWN |
| GET | `fcc.zepto.co.in/vms/api/v1/admin/warehouse-details/fetch` | GET Vendor Details | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/files/${e}` | get File | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/files/error` | GET Error File | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/files/filter` | GET Files List | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/files/template` | GET Template File | READ |
| GET | `fcc.zepto.co.in/vms/api/v1/kyc/gstin-details` | GET Gstin Details | READ |
| GET | `fcc.zepto.co.in/vms/api/v2/files/template` | GET Template File V2 | READ |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v2/vendor/extend-organization` | pt | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v2/vendor/filter` | At | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v2/vendor/manufacturer-ids` | ut | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vms/api/v2/vendor/relation-type` | Nt | UNKNOWN |

> **Out of scope:** 22 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Users-Access]]

Users & Access Management — 33 endpoints (21 read/to-confirm, 12 write/export). Hosts: `auth-backend.zepto.co.in`, `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `auth-backend.zepto.co.in/api/v1/access-management/activate-vendor` | Activate User | UNKNOWN |
| GET | `auth-backend.zepto.co.in/api/v1/access-management/roles` | GET Roles List | READ |
| GET | `auth-backend.zepto.co.in/api/v1/access-management/users` | GET Users List | READ |
| GET | `auth-backend.zepto.co.in/api/v1/access-management/vendors` | GET Manage Vendors List | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/access-management/user` | access management user | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/authorize/fetch-all-modules-for-an-application-and-role` | authorize fetch all modules for an application and role | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/authorize/get-roles` | authorize get roles | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/authorize/modify-access-for-modules-and-actions` | authorize modify access for modules and actions | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/users` | users | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/users/${e}/access` | users access | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/users/access` | users access | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/users/child-roles` | GET User Roles | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/users/permissions` | users permissions | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v2/authorize/fetch-all-modules-for-an-application` | authorize fetch all modules for an application | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v2/user-approvals` | user approvals | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v2/user-approvals/${e}/details` | user approvals details | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v2/users/access` | users access | UNKNOWN |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/access-management/user` | GET Entity Data | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/authorize/fetch-all-modules-for-an-application-and-role` | GET ALL Modules Based ON Role | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/authorize/get-roles` | GET ALL Roles | READ |
| GET | `fcc.zepto.co.in/vendor/api/v2/authorize/fetch-all-modules-for-an-application` | GET Role Config | READ |

> **Out of scope:** 12 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Subscription-Billing]]

Subscription & Billing — 12 endpoints (10 read/to-confirm, 2 write/export). Hosts: `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `fcc.zepto.co.in/api/v1/subscribe/free-tier` | subscribe free tier | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/subscribe/on-credit` | subscribe on credit | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/subscription/pricing-details` | subscription pricing details | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/subscription/user-details` | subscription user details | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/subscription/visibility-details` | subscription visibility details | UNKNOWN |
| POST | `fcc.zepto.co.in/brand-analytics-mobile/api/v1/subscribe/free-tier` | Subscribe Free Tier Mobile | READ |
| POST | `fcc.zepto.co.in/brand-analytics-web/api/v1/subscribe/free-tier` | Subscribe Free Tier WEB | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/subscription/pricing-details` | GET Pricing Details WEB | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/subscription/user-details` | GET Subscription Details WEB | READ |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/subscription/visibility-details` | GET Plan Visibility Details WEB | READ |

> **Out of scope:** 2 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Auth-Identity]]

Auth & Identity — 19 endpoints (10 read/to-confirm, 9 write/export). Hosts: `auth-backend.zepto.co.in`, `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `auth-backend.zepto.co.in/api/v1/auth/get-user-by-code` | c,d | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/auth/get-user-by-token` | auth get user by token | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/auth/resend-mfa-otp/` | auth resend mfa otp | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/auth/sign-out` | auth sign out | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/auth/validate-mfa-otp/` | auth validate mfa otp | UNKNOWN |
| GET | `fcc.zepto.co.in/vendor/api/v1/auth/get-user-by-token` | GET User Profile | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/auth/remove-user-application-access` | Disable User | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/auth/resend-mfa-otp/` | h | UNKNOWN |
| POST | `fcc.zepto.co.in/vendor/api/v1/auth/validate-mfa-otp` | auth validate mfa otp | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/auth/validate-mfa-otp/` | p | UNKNOWN |

> **Out of scope:** 9 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

## [[Platform-Common]]

Platform-Common (Layout, Commons, Config, Files, Support) — 118 endpoints (104 read/to-confirm, 14 write/export). Hosts: `auth-backend.zepto.co.in`, `events.zepto.co.in`, `fcc.zepto.co.in`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `auth-backend.zepto.co.in/api/v1/chat/sendbird/user/token` | N | READ |
| GET | `auth-backend.zepto.co.in/api/v1/commons/brand-category-mapping` | GET Brands AND CATEGORY,Ze | READ |
| GET | `auth-backend.zepto.co.in/api/v1/commons/brand-l3-category-mapping` | GET Brand L3 Category Mapping BA,de | READ |
| UNKNOWN | `auth-backend.zepto.co.in/api/v1/commons/brand-manufacturer-mapping` | Manufacturer Brand Mapping | UNKNOWN |
| GET | `auth-backend.zepto.co.in/api/v1/commons/config/get-pre-signed-url` | GET Presigned URL | READ (file) |
| GET | `auth-backend.zepto.co.in/api/v1/commons/config/learning-center/all` | GET ALL Learning Content | READ |
| GET | `auth-backend.zepto.co.in/api/v1/commons/config/learning-center/get-by-subModule` | GET Learning Content BY Submodule | READ |
| GET | `auth-backend.zepto.co.in/api/v1/commons/manufacturer-list` | GET Manufacturer List | READ |
| GET | `auth-backend.zepto.co.in/api/v1/commons/mh-list` | GET MH List | READ |
| GET | `auth-backend.zepto.co.in/api/v1/commons/search-customers-and-vendors` | GET Vendors List V3 | READ |
| POST | `auth-backend.zepto.co.in/api/v1/commons/search-customers-and-vendors` | GET Vendors List V3 | READ |
| GET | `auth-backend.zepto.co.in/api/v1/commons/search-vendors` | GET Vendors List,search Vendors | READ |
| POST | `auth-backend.zepto.co.in/api/v1/commons/search-vendors` | GET Vendors List | READ |
| GET | `auth-backend.zepto.co.in/api/v1/commons/search-vendors-v2` | GET Vendors List V2 | READ |
| POST | `auth-backend.zepto.co.in/api/v1/commons/search-vendors-v2` | GET Vendors List V2 | READ |
| GET | `auth-backend.zepto.co.in/api/v1/commons/status-config` | GET Status Config | READ |
| POST | `auth-backend.zepto.co.in/api/v1/commons/tnc/user` | R,g | UNKNOWN |
| GET | `auth-backend.zepto.co.in/api/v1/commons/user/mh-list` | External Location Filter List,location Filter List | READ |
| GET | `auth-backend.zepto.co.in/api/v1/commons/user/vendor-list` | External Vendor Filter List,vendor Filter List | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/layout/config/create_campaign_modal_subtype_image_map` | GET Create Campaign Modal Subtype Image MAP | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/layout/config/jarvis_ai_ui_config` | GET UI Config | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/layout/config/kam_ai_ui_config` | GET UI Config | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/layout/config/payment_confirmation_modal_status_config` | GET Payment Status Config | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v1/layout/config/pricing_page_metadata` | GET Pricing Page Metadata | READ |
| GET | `fcc.zepto.co.in/ads-bff/api/v2/layout/table/user_approvals_table_meta` | GET Approvers Table Metadata | READ |
| UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v2/users` | User Table Data | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/admin/brands/metrics/summary` | brands metrics summary | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/admin/campaigns` | admin campaigns | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/audit-logs` | audit logs | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/commons/search-ntv` | commons search ntv | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/config` | config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/config/get-configdata` | config get configdata | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/domain/create-domains` | domain create domains | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/file-job/download-file` | file job download file | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/file-job/get-signed-url` | file job get signed URL | UNKNOWN |
| GET | `fcc.zepto.co.in/api/v1/filter/city-list` | GET City | READ |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/${e}` | layout config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/AdCreativeSectionConfigXPlacementTypeMap` | layout config Ad Creative Section Config XPlacement Type Map | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/NewCreativeFormDetails` | layout config New Creative Form Details | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/ads-banner-config` | layout config ads banner config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/ads-feature-metadata` | layout config ads feature metadata | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/ads_brand_analytics_config` | layout config ads brand analytics config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/campaign_forecast_review_config` | layout config campaign forecast review config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/campain-review-detail-from` | layout config campain review detail from | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/category-popup-config` | layout config category popup config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/create_campaign_walkthrough` | layout config create campaign walkthrough | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/dcm_trackers_fe_config` | layout config dcm trackers fe config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/gamification_frequency_caps` | layout config gamification frequency caps | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/hyperlocal_default_values` | layout config hyperlocal default values | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/keywords-layout-config` | layout config keywords layout config | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/nonEndemicCreativeFormDetails` | layout config non Endemic Creative Form Details | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/pagewise-placements` | layout config pagewise placements | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/quick_edit_form_metadata` | layout config quick edit form metadata | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/quick_edit_nudge_metadata` | layout config quick edit nudge metadata | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/review-checklist` | layout config review checklist | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/reward_creation_template_download_path` | layout config reward creation template download path | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/smart_nudge_metadata` | layout config smart nudge metadata | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/smart_nudge_sub_headers` | layout config smart nudge sub headers | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/summaryMetricsMeta` | layout config summary Metrics Meta | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/swap_strategy_metadata` | layout config swap strategy metadata | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/config/version-enforcer` | layout config version enforcer | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/page/${e}` | layout page | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/page/hyperlocal-help-center` | layout page hyperlocal help center | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/table/campaign-review-table-meta` | layout table campaign review table meta | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/layout/table/change-log-table-meta` | layout table change log table meta | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/log-details` | log details | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v1/s3/file` | s3 file | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v2/ips/debit-note` | ips debit note | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/api/v2/layout/table/users_table_meta` | layout table users table meta | UNKNOWN |
| GET | `fcc.zepto.co.in/brand-analytics-web/api/v1/common/enhancement-config` | GET Enhancement Config | READ |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/reconciliation/inventory/city-level-listing` | et | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/reconciliation/inventory/summary` | Qe | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/brand-analytics-web/api/v1/reconciliation/inventory/vendor-level-listing` | Je | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/client/api/v1/file/${e}/get-presigned-url` | client file get presigned URL | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/attachment` | GET Contract Attachment Content | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/attachment/pre-signed-url` | GET Attachment PRE Signed URL | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/bulk-jobs/download-template` | Download Bulk JOB Template | READ (file) |
| GET | `fcc.zepto.co.in/contractservice/api/v1/bulk-jobs/list` | Bulk JOB List | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/common/fbz-margins` | GET FBZ Margins | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/common/fbz-payment-terms` | GET Payment Terms | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/common/get-brands-of-manufacturer` | GET Brands OF Manufacturer | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/common/get-categories-of-manufacturer` | GET Categories | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/common/get-subcategories-of-manufacturer` | GET SUB Categories | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/common/manufacturer-list` | Search Manufacturers Distributors | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/common/vendor-details` | GET Vendors Details BY Code | READ |
| GET | `fcc.zepto.co.in/contractservice/api/v1/common/vendor-list` | Search Vendors | READ |
| UNKNOWN | `fcc.zepto.co.in/crm-ticketing/api/v1/ticket/${e}` | crm ticketing ticket | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/crm-ticketing/api/v1/ticket/${e}/actions/reassign` | ticket actions reassign | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/crm-ticketing/api/v1/ticket/${e}/actions/reopen` | ticket actions reopen | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/crm-ticketing/api/v1/ticket/${e}/notes` | crm ticketing ticket notes | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/crm-ticketing/api/v1/tickets` | crm ticketing tickets | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/customer/api/v1/ticket/${e}/rating` | customer ticket rating | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/internal/api/v1/vendor-po` | internal vendor PO | UNKNOWN |
| UNKNOWN | `fcc.zepto.co.in/relay/api/v1/config` | Vite Flagship API Base URL Prod,vite Flagship API Base URL QA | UNKNOWN |
| GET | `fcc.zepto.co.in/relay/api/v1/config/get-configdata` | GET Fetaure Flags | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/attachment/get-presigned-url` | rt | READ (file) |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/attachment/get-template` | ot | UNKNOWN |
| GET | `fcc.zepto.co.in/vendor/api/v1/bulk-job` | GET Bulk Ticket Jobs | READ |
| UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/bulk-job/${e}/download-report` | bulk job download report | READ (file) |
| GET | `fcc.zepto.co.in/vendor/api/v1/bulk-job/download-template` | Download Bulk Ticket Template | READ (file) |
| GET | `fcc.zepto.co.in/vendor/api/v1/commons/search-ntv` | Search NTV | READ |
| POST | `fcc.zepto.co.in/vendor/api/v1/commons/search-ntv` | Search NTV | READ |
| GET | `fcc.zepto.co.in/vendor/api/v1/config/load` | GET Meta Info | READ |
| GET | `fcc.zepto.co.in/vendor/api/v2/util/document-download` | Download Document | READ (file) |

> **Out of scope:** 14 WRITE/EXPORT endpoint(s) in this section are held out of scope — see [Out of scope (writes/exports)](#out-of-scope-writesexports).

---

# Out of scope (writes/exports)

**Never expose these in a read-only CLI.** `WRITE` = mutates business data or state (create/edit/cancel/upload/submit/delete). `EXPORT` = side-effecting export job (enqueues a report-request and typically emails a copy — not a pure read; poll + download the *already-generated* file through the relevant reports queue instead).

| Section | METHOD | Path | Purpose | Type |
|---|---|---|---|---|
| [[ASN]] | POST | `fcc.zepto.co.in/api/v1/asn/failure-upload-csv` | Upload MRP Cost Sheet | EXPORT |
| [[ASN]] | POST | `fcc.zepto.co.in/api/v1/asn/item-details-from-csv` | Upload ASN QTY Document | EXPORT |
| [[ASN]] | POST | `fcc.zepto.co.in/api/v1/asn/upload-asn-creation-csv` | Upload ASN Creation CSV | EXPORT |
| [[ASN]] | POST | `fcc.zepto.co.in/api/v1/asn/upload-asn-fallback-csv` | Upload ASN Fallback CSV | EXPORT |
| [[ASN]] | POST | `fcc.zepto.co.in/api/v1/asn/upload-invoice` | Upload Invoice | EXPORT |
| [[ASN]] | POST | `fcc.zepto.co.in/api/v1/asn/` | Create ASN | WRITE |
| [[ASN]] | POST | `fcc.zepto.co.in/api/v1/asn/asn-automation` | Create ASN BY Automation | WRITE |
| [[ASN]] | POST | `fcc.zepto.co.in/api/v1/asn/create-exceptional-asn` | Save ASN Draft | WRITE |
| [[ASN]] | POST | `fcc.zepto.co.in/api/v1/asn/failure-submit` | Submit MRP Cost Sheet | WRITE |
| [[Ads-Billing-Wallet]] | UNKNOWN | `fcc.zepto.co.in/ads-bff/api/v1/file-job/UPLOAD/BILLING_BULK_UPLOAD` | Billing Bulk Upload | EXPORT |
| [[Ads-Billing-Wallet]] | GET | `fcc.zepto.co.in/ads-bff/api/v1/file-job/get-signed-url` | GET Upload Presigned URL | EXPORT |
| [[Ads-Billing-Wallet]] | POST | `fcc.zepto.co.in/ads-bff/api/v1/inventory/slots` | Upload Pricing CSV | EXPORT |
| [[Ads-Billing-Wallet]] | GET | `fcc.zepto.co.in/ads-bff/api/v1/inventory/slots/listing` | GET Pricing Upload History List | EXPORT |
| [[Ads-Billing-Wallet]] | GET | `fcc.zepto.co.in/ads-bff/api/v1/layout/config/billing_bulk_upload_table_metadata` | GET Billing Bulk Upload Table Metadata | EXPORT |
| [[Ads-Billing-Wallet]] | POST | `fcc.zepto.co.in/api/v1/wallet/s3/save-upload-key` | wallet s3 save upload key | EXPORT |
| [[Ads-Billing-Wallet]] | POST | `fcc.zepto.co.in/api/v1/wallet/payment/initiate` | wallet payment initiate | WRITE |
| [[Ads-Campaigns-Booking-Keywords]] | POST | `fcc.zepto.co.in/ads-bff/api/v1/agents/jarvis-agent/chat/send` | Send Chat | WRITE |
| [[Ads-Campaigns-Booking-Keywords]] | POST | `fcc.zepto.co.in/ads-bff/api/v1/agents/kam-agent/chat/send` | Send Chat | WRITE |
| [[Ads-Campaigns-Booking-Keywords]] | POST | `fcc.zepto.co.in/ads-bff/api/v1/booking/${e}/approve` | booking approve | WRITE |
| [[Ads-Campaigns-Booking-Keywords]] | POST | `fcc.zepto.co.in/ads-bff/api/v1/booking/${e}/reject` | booking reject | WRITE |
| [[Ads-Campaigns-Booking-Keywords]] | POST | `fcc.zepto.co.in/api/v1/campaigns/${e}/approve` | campaigns approve | WRITE |
| [[Ads-Campaigns-Booking-Keywords]] | POST | `fcc.zepto.co.in/api/v1/campaigns/${e}/reject` | campaigns reject | WRITE |
| [[Auth-Identity]] | POST | `auth-backend.zepto.co.in/api/v1/auth/forgot-password-invited` | o,s | WRITE |
| [[Auth-Identity]] | POST | `auth-backend.zepto.co.in/api/v1/auth/google/sign-in` | l | WRITE |
| [[Auth-Identity]] | POST | `auth-backend.zepto.co.in/api/v1/auth/reinvite-user` | Resend Invite | WRITE |
| [[Auth-Identity]] | POST | `auth-backend.zepto.co.in/api/v1/auth/resend-code` | E,u | WRITE |
| [[Auth-Identity]] | POST | `auth-backend.zepto.co.in/api/v1/auth/reset-password` | c,l | WRITE |
| [[Auth-Identity]] | POST | `auth-backend.zepto.co.in/api/v1/auth/sign-in` | i,r | WRITE |
| [[Auth-Identity]] | POST | `auth-backend.zepto.co.in/api/v1/auth/verify-invited-user` | o,s | WRITE |
| [[Auth-Identity]] | POST | `fcc.zepto.co.in/vendor/api/v1/auth/resend-mfa-otp` | auth resend mfa otp | WRITE |
| [[Auth-Identity]] | POST | `fcc.zepto.co.in/vendor/api/v1/auth/sign-out` | ,f | WRITE |
| [[Catalog-Health]] | GET | `fcc.zepto.co.in/vendor/api/v1/catalog/sku-onboarding/fetch-uploaded-file` | Fetch Uploaded File | EXPORT |
| [[Catalog-Health]] | POST | `fcc.zepto.co.in/vendor/api/v1/catalog/sku-onboarding/register-file-upload` | Register File Upload | EXPORT |
| [[Catalog-Health]] | UNKNOWN | `fcc.zepto.co.in/vendor/api/v2/product_onboarding/register_file_upload` | product onboarding register file upload | EXPORT |
| [[Creative-Management]] | UNKNOWN | `fcc.zepto.co.in/api/v1/creative-management/banner-generation` | creative management banner generation | EXPORT |
| [[Creative-Management]] | UNKNOWN | `fcc.zepto.co.in/api/v1/creative-management/banner-generation/${e}` | creative management banner generation | EXPORT |
| [[Engagement]] | PUT | `fcc.zepto.co.in/survey/api/v1/survey-creation/${e}/questions` | update Survey Questions | WRITE |
| [[Engagement]] | PUT | `fcc.zepto.co.in/survey/api/v1/survey-creation/rewards` | Update Rewards AND Reach | WRITE |
| [[Engagement]] | PUT | `fcc.zepto.co.in/survey/api/v1/survey-creation/upsert` | Update Survey | WRITE |
| [[Engagement]] | PUT | `fcc.zepto.co.in/survey/api/v1/survey/update-reward` | Update Reward | WRITE |
| [[Fulfilled-by-Zepto]] | UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/rebate/upload-rebate-csv` | FBZ rebate upload rebate CSV | EXPORT |
| [[Fulfilled-by-Zepto]] | UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/${e}/dn-copy/upload` | vendor debit note dn copy upload | EXPORT |
| [[Fulfilled-by-Zepto]] | UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/${e}/working-dn-copy/upload` | vendor debit note working dn copy upload | EXPORT |
| [[Fulfilled-by-Zepto]] | UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/batch-upload` | FBZ vendor debit note batch upload | EXPORT |
| [[Fulfilled-by-Zepto]] | UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/batch-upload/${e}` | FBZ vendor debit note batch upload | EXPORT |
| [[Fulfilled-by-Zepto]] | UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/batch-upload/${e}/items` | vendor debit note batch upload items | EXPORT |
| [[Fulfilled-by-Zepto]] | UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/batch-upload/cancel` | vendor debit note batch upload cancel | EXPORT |
| [[Fulfilled-by-Zepto]] | UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/batch-upload/file` | vendor debit note batch upload file | EXPORT |
| [[Fulfilled-by-Zepto]] | UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/batch-upload/list` | vendor debit note batch upload list | EXPORT |
| [[Fulfilled-by-Zepto]] | UNKNOWN | `fcc.zepto.co.in/api/v1/fbz/vendor-debit-note/upload-template` | FBZ vendor debit note upload template | EXPORT |
| [[Invoicing]] | POST | `fcc.zepto.co.in/contractservice/api/v1/off-invoice/off-invoice-rules/${e}/file-upload` | upload Inclusion Exclusion | EXPORT |
| [[Invoicing]] | DELETE | `fcc.zepto.co.in/contractservice/api/v1/off-invoice/off-invoice-rules/${e}/remove-applicability-file` | remove Uploaded File | EXPORT |
| [[Invoicing]] | POST | `fcc.zepto.co.in/invoice/api/v1/self-invoice/non-trade/upload` | Upload Self Invoice | EXPORT |
| [[Invoicing]] | POST | `fcc.zepto.co.in/contractservice/api/v1/off-invoice/off-invoice-rules/${e}/create-rule` | add Rule | WRITE |
| [[Invoicing]] | DELETE | `fcc.zepto.co.in/contractservice/api/v1/off-invoice/off-invoice-rules/${e}/remove-rule` | remove Rule | WRITE |
| [[Invoicing]] | POST | `fcc.zepto.co.in/invoice/api/v1/self-invoice/non-trade/cancel` | Cancel Invoice | WRITE |
| [[Invoicing]] | POST | `fcc.zepto.co.in/invoice/api/v1/self-invoice/non-trade/draft` | Save Draft | WRITE |
| [[Invoicing]] | POST | `fcc.zepto.co.in/invoice/api/v1/self-invoice/non-trade/submit` | Submit Invoice | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/attachment/save` | Upload Attachment | EXPORT |
| [[KYC-Onboarding]] | GET | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/vendor-sync/get-by-user-id` | GET Sync Status Details | EXPORT |
| [[KYC-Onboarding]] | GET | `fcc.zepto.co.in/vms/api/v1/admin/vendor-sync/get-by-user-id` | GET Sync Status Details | EXPORT |
| [[KYC-Onboarding]] | UNKNOWN | `fcc.zepto.co.in/vms/api/v1/files/upload` | GET Uploaded File,upload File | EXPORT |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v2/admin/attachment/save` | Upload Attachment,upload Attachment V2 | EXPORT |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/basic-details/save-contract` | Save Contract Details | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/kyc/save` | Save KYC Details | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/lead` | Save Lead Details | WRITE |
| [[KYC-Onboarding]] | PUT | `fcc.zepto.co.in/vms/api/v1/admin/lead/on-hold` | PUT Lead ON Hold | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/lead/reject` | Reject Lead | WRITE |
| [[KYC-Onboarding]] | PUT | `fcc.zepto.co.in/vms/api/v1/admin/marketer/${e}/update` | update Marketer Details By ID | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/marketer/admin-creation` | Create Marketer | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/counterpart` | Create Counterpart Vendor | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/kyc/save` | Save KYC Details | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/save-contract` | Save Contract Details | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/warehouse-details/save` | Save Vendor Details | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/user/approve-onboarding-data` | Approve Onboarding | WRITE |
| [[KYC-Onboarding]] | PUT | `fcc.zepto.co.in/vms/api/v1/admin/user/hold-onboarding-data` | PUT ON Hold | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/user/reject-onboarding-data` | Reject Onboarding | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v1/admin/warehouse-details/save` | Save Vendor Details | WRITE |
| [[KYC-Onboarding]] | POST | `fcc.zepto.co.in/vms/api/v2/admin/lead/approve` | Approve Lead | WRITE |
| [[KYC-Onboarding]] | PUT | `fcc.zepto.co.in/vms/api/v2/vendor/update` | Update Vendor VMS | WRITE |
| [[Ledger-Recon-Upload]] | UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/ledger-upload/count` | nt | EXPORT |
| [[Ledger-Recon-Upload]] | UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/ledger-upload/create` | lt | EXPORT |
| [[Ledger-Recon-Upload]] | UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/ledger-upload/list` | at | EXPORT |
| [[Ledger-Recon-Upload]] | UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/ledger-upload/summary` | it | EXPORT |
| [[Ledger-Recon-Upload]] | UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/ledger-upload/trigger-recon` | ct | EXPORT |
| [[Ledger-Recon-Upload]] | GET | `fcc.zepto.co.in/vendor/api/v1/ledger-upload/vendor` | GET Vendor Ledger Listing | EXPORT |
| [[Platform-Common]] | UNKNOWN | `fcc.zepto.co.in/client/api/v1/file/generate-upload-url` | client file generate upload URL | EXPORT |
| [[Platform-Common]] | POST | `fcc.zepto.co.in/contractservice/api/v1/attachment/save` | Upload Rule Artifact | EXPORT |
| [[Platform-Common]] | UNKNOWN | `fcc.zepto.co.in/vendor/api/v1/attachment/get-upload-url` | st | EXPORT |
| [[Platform-Common]] | POST | `fcc.zepto.co.in/vendor/api/v2/util/document-upload` | Upload Document | EXPORT |
| [[Platform-Common]] | POST | `auth-backend.zepto.co.in/api/v1/chat/feedback` | Post Chat Feedback | WRITE |
| [[Platform-Common]] | POST | `auth-backend.zepto.co.in/api/v1/chat/sendbird/user/token/refresh` | v | WRITE |
| [[Platform-Common]] | POST | `auth-backend.zepto.co.in/api/v1/commons/feedback` | Post Feedback | WRITE |
| [[Platform-Common]] | POST | `auth-backend.zepto.co.in/api/v1/commons/impersonation` | SET Impersonation | WRITE |
| [[Platform-Common]] | POST | `events.zepto.co.in/api/v2/publish-events` | NX Event Service ENDPOINT,w | WRITE |
| [[Platform-Common]] | POST | `fcc.zepto.co.in/ads-bff/api/v2/users/${e}/update` | users update | WRITE |
| [[Platform-Common]] | POST | `fcc.zepto.co.in/ads-bff/api/v2/users/${e}/update/payload` | users update payload | WRITE |
| [[Platform-Common]] | POST | `fcc.zepto.co.in/contractservice/api/v1/bulk-jobs/create` | Create Bulk Contract JOB | WRITE |
| [[Platform-Common]] | POST | `fcc.zepto.co.in/vendor/api/v1/bulk-job/create` | Create Bulk Ticket JOB | WRITE |
| [[Platform-Common]] | POST | `fcc.zepto.co.in/vendor/api/v1/ticket/create` | Create Ticket | WRITE |
| [[Purchase-Orders]] | POST | `fcc.zepto.co.in/api/v1/po/cancel` | Cancel Request | WRITE |
| [[Receivables]] | POST | `fcc.zepto.co.in/api/v1/ntv/attachment-upload` | Upload Invoice CN | EXPORT |
| [[Receivables]] | PUT | `fcc.zepto.co.in/vms/api/v1/non-trade-vendor/update` | Update NON Trade Vendor | WRITE |
| [[Receivables]] | POST | `fcc.zepto.co.in/vms/api/v1/receivable-vendor/approve` | path | WRITE |
| [[Receivables]] | POST | `fcc.zepto.co.in/vms/api/v1/receivable-vendor/reject` | path | WRITE |
| [[Receivables]] | PUT | `fcc.zepto.co.in/vms/api/v1/receivable-vendor/update` | Update Vendor Details | WRITE |
| [[Release-Orders-Amendment-Requests]] | POST | `fcc.zepto.co.in/contractservice/api/v1/amendment-requests/${e}/upload-artifact` | amendment Request Upload Artifact | EXPORT |
| [[Release-Orders-Amendment-Requests]] | POST | `fcc.zepto.co.in/contractservice/api/v1/amendment-requests/file-upload` | Amendment Request File Upload | EXPORT |
| [[Release-Orders-Amendment-Requests]] | POST | `fcc.zepto.co.in/contractservice/api/v1/amendment-requests/bulk-submit` | Amendment Requests Bulk Submit | WRITE |
| [[Subscription-Billing]] | POST | `fcc.zepto.co.in/brand-analytics-mobile/api/v1/subscribe/on-credit` | Subscribe TO Plan Mobile | WRITE |
| [[Subscription-Billing]] | POST | `fcc.zepto.co.in/brand-analytics-web/api/v1/subscribe/on-credit` | Subscribe TO Plan WEB | WRITE |
| [[Users-Access]] | PUT | `auth-backend.zepto.co.in/api/v1/access-management/assign-role` | Edit User | WRITE |
| [[Users-Access]] | POST | `auth-backend.zepto.co.in/api/v1/access-management/normal-user` | ADD NEW User | WRITE |
| [[Users-Access]] | POST | `auth-backend.zepto.co.in/api/v1/access-management/super-user` | Create Super User | WRITE |
| [[Users-Access]] | PUT | `auth-backend.zepto.co.in/api/v1/access-management/update-vendor` | Update Vendor | WRITE |
| [[Users-Access]] | POST | `fcc.zepto.co.in/api/v1/authorize/create/role` | authorize create role | WRITE |
| [[Users-Access]] | POST | `fcc.zepto.co.in/api/v1/users/${e}/approve` | users approve | WRITE |
| [[Users-Access]] | POST | `fcc.zepto.co.in/api/v1/users/${e}/reinvite` | users reinvite | WRITE |
| [[Users-Access]] | POST | `fcc.zepto.co.in/api/v2/user-approvals/${e}/approve` | user approvals approve | WRITE |
| [[Users-Access]] | POST | `fcc.zepto.co.in/api/v2/user-approvals/${e}/reject` | user approvals reject | WRITE |
| [[Users-Access]] | POST | `fcc.zepto.co.in/api/v2/users/${e}/sync` | users sync | WRITE |
| [[Users-Access]] | POST | `fcc.zepto.co.in/vendor/api/v1/authorize/create/role` | Create Role | WRITE |
| [[Users-Access]] | POST | `fcc.zepto.co.in/vendor/api/v1/authorize/modify-access-for-modules-and-actions` | Modify Access FOR Modules AND Actions | WRITE |
| [[Vendor-Contracts-Margins]] | UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/upload` | vendor pv margin upload | EXPORT |
| [[Vendor-Contracts-Margins]] | UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/upload-request-list` | vendor pv margin upload request list | EXPORT |
| [[Vendor-Contracts-Margins]] | UNKNOWN | `fcc.zepto.co.in/api/v1/vendor-pv-margin/upload/template` | vendor pv margin upload template | EXPORT |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/upload-deq-details` | upload De QDetails Attachment | EXPORT |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/upload-item-margin-details` | upload Margin Details | EXPORT |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/upload-item-stock-details` | upload Stock Details | EXPORT |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/upload-off-invoice-details` | upload Off Invoice Details | EXPORT |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/upload-on-invoice-details` | upload On Invoice Details | EXPORT |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/upload-stock-correction-details` | upload Stock Correction Details Attachment | EXPORT |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/upload-email-attachment` | upload Email Attachment | EXPORT |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/upload-terms-and-schedule` | upload Terms And Schedules | EXPORT |
| [[Vendor-Contracts-Margins]] | DELETE | `fcc.zepto.co.in/contractservice/api/v1/margin-and-incentive/${e}/delete-margin-and-incentive-details` | remove Margin And Incentive Details Attachment | WRITE |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/margin-and-incentive` | save Margin Incentive Details | WRITE |
| [[Vendor-Contracts-Margins]] | PUT | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/reviewer` | update Contract Reviewer | WRITE |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/reviewers-and-terms` | submit Reviewers And Remarks | WRITE |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/${e}/submit-amendment-requests` | submit Amendment Requests For Review | WRITE |
| [[Vendor-Contracts-Margins]] | POST | `fcc.zepto.co.in/contractservice/api/v1/vendor-contract/contract-details` | Submit Basic Contract Details | WRITE |
| [[Vendor-Reports-Queue]] | UNKNOWN | `fcc.zepto.co.in/api/v1/reports/uploads` | reports uploads | EXPORT |

---

## Count
- **25 sections** documented (13 vendor · 7 ads · 5 platform).
- **600 READ / to-confirm contracts** catalogued in the section tables (`READ` + `READ (file)` + `UNKNOWN`).
- **141 WRITE / EXPORT endpoints** held **out of scope**.
- **TOTAL = 741 endpoint contracts** — matches `captures/js/endpoints-raw.json` (741) exactly.

## Connections
- Method & hubs: [[00-Zepto-Atlas]] · [[Zepto-Data-Model]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- Sections: [[Purchase-Orders]] · [[ASN]] · [[Release-Orders-Amendment-Requests]] · [[RTV]] · [[Catalog-Health]] · [[Stock-View-Inventory]] · [[Vendor-Reports-Queue]] · [[Invoicing]] · [[Vendor-Contracts-Margins]] · [[Payments]] · [[Ledger-Recon-Upload]] · [[Receivables]] · [[Fulfilled-by-Zepto]] · [[Brands-Audiences]] · [[Creative-Management]] · [[Ads-Campaigns-Booking-Keywords]] · [[Ads-Billing-Wallet]] · [[Brand-Analytics]] · [[Market-Geo-Consumer-Insights]] · [[Engagement]] · [[KYC-Onboarding]] · [[Users-Access]] · [[Subscription-Billing]] · [[Auth-Identity]] · [[Platform-Common]]
