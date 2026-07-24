---
title: Catalog & Catalog Health
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, catalog]
---

# Catalog & Catalog Health

The **Catalog & Catalog Health** section is the vendor-console surface where JIVO (Jivo Wellness Pvt. Ltd., Manufacturer, STANDARD tier, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`) sees **how complete and how correct its Zepto catalog is**, and where it drives new-SKU onboarding. It has two faces: a **Catalog Health dashboard** (a scorecard of per-SKU attribute completeness + data-quality ruleset scores, with drill-downs into which attribute values are missing/wrong for a given product) and a **SKU onboarding** workbench (draft new products, download a CSV/XLSX template, upload the filled sheet, and submit to Zepto's category managers). A third, lighter surface is the **ads product catalog** (`ads-bff/api/v1/catalog`) — the product picker the ads lane reuses to attach PVIDs to campaigns. All calls hit `fcc.zepto.co.in`, split across two path families: `ads-bff/api/v1/catalog*` (ads product lookup) and `vendor/api/v1|v2/*` (catalog-health + onboarding). Auth is the single portal JWT (`authorization` header, **no `Bearer` prefix**), the same token that works across every Zepto backend. Endpoint contracts below were extracted from the code-split chunks `1183.8940422c8268d8dc.js` (ads catalog constants), `3539.64ab07c46b8741b5.js` (the catalog-health + sku-onboarding API-constant map), and `remoteEntry.js` (v2 product-onboarding) — they are the URL-constant bindings, not live captures (see probe note below).

## SPA routes

- `/catalog-health` · `/vendor/catalog-health` — the Catalog Health dashboard landing (completeness + quality scorecards).
- `/catalog-health/completeness-details` · `/vendor/catalog-health/completeness-details` — attribute-completeness drill-down.
- `/catalog-health/quality-details` · `/vendor/catalog-health/quality-details` — data-quality ruleset drill-down.
- `/catalog-health/sku-review` · `/vendor/catalog-health/sku-review` — per-SKU attribute review (missing/wrong attribute values, suggestions).

(The `/vendor/*`-prefixed duplicates are the same pages mounted under the vendor micro-frontend base; the SKU-onboarding workbench is reached from the dashboard, not a top-level route in this section's map.)

## Backend

- **Host:** `fcc.zepto.co.in` (vendor reports + ads-bff family).
- **Path families:** `ads-bff/api/v1/catalog*` (ads product catalog/validation) and `vendor/api/v1/catalog-health-dashboard/*` + `vendor/api/v1|v2/catalog/sku-onboarding|product_onboarding/*` (catalog-health + onboarding).
- **Auth:** `authorization: <JWT>` (no `Bearer`), `accept: application/json`. WAF headers (`waf-enabled`, `x-aws-waf-token`) present in captures but not enforced as of last verified capture. Vendor paths route through a `bifrost` gateway that expects the vendor **proxy-target** header (see probe note) — without it the gateway 404s the path.

## READ endpoints

Base = `https://fcc.zepto.co.in/` + path. Method = as wired in the bundle (`GET` where the const is bound to a GET helper; `UNKNOWN` = const present, verb not directly observed). No endpoint here was upgraded to PROVEN — all probes returned gateway 404 (routing) / the JWT is past expiry (see probe note).

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `ads-bff/api/v1/catalog` | Ads product catalog list (`GET_PRODUCTS`) — the PVID product picker reused by the ads lane | READ |
| GET | `ads-bff/api/v1/catalog/metadata` | Catalog metadata/facets for the product picker (`CATALOG_METADATA`) | READ |
| POST | `ads-bff/api/v1/catalog/validate` | Validate a set of products/PVIDs (`VALIDATE_PRODUCTS`) — non-mutating check; verb to confirm | READ (validation, no state change) |
| POST | `ads-bff/api/v1/validate_pvids` | Resolve/validate PVIDs from an uploaded CSV (`GET_PRODUCTS_FROM_CSV`) — non-mutating lookup; verb to confirm | READ (validation, no state change) |
| GET | `vendor/api/v1/catalog-health-dashboard/attribute-view` | Attribute-view for the completeness dashboard (`GET_ATTRIBUTE_VIEW`) | READ |
| GET | `vendor/api/v1/catalog-health-dashboard/get-l4-values/{pvId}` | All attribute (L4) values for one PV id (`getAllAttibutesForPvId`) — SKU review drill-down | READ |
| GET | `vendor/api/v1/catalog-health-dashboard/sku-rule-scores` | Per-SKU data-quality rule scores (`GET_SKU_RULE_SCORES`) | READ |
| GET | `vendor/api/v1/catalog-health-dashboard/sku-ruleset-score/overview` | Ruleset score overview (dashboard headline tiles) (`GET_SKU_RULESET_SCORE_OVERVIEW`) | READ |
| GET | `vendor/api/v1/catalog-health-dashboard/sku-ruleset-scores` | Per-SKU ruleset score grid (`GET_PRODUCT_SCORES`) — quality-details table | READ |
| GET | `vendor/api/v1/catalog-health-dashboard/suggestions/get-attributes-by-pv-id` | Suggested attribute values for a PV id (`GET_ATTRIBUTES_BY_PV_ID`) — sku-review suggestions | READ |
| GET | `vendor/api/v1/catalog/category-hierarchy/search` | Category-hierarchy typeahead (`SEARCH_CATEGORIES`) — onboarding category picker | READ |
| GET | `vendor/api/v1/catalog/sku-onboarding/list` | SKU-onboarding submission list (`SKU_ONBOARDING_LIST`) | READ |
| GET | `vendor/api/v1/catalog/sku-onboarding/drafts` | Saved onboarding drafts (`GET_DRAFTS`) | READ |
| GET | `vendor/api/v1/catalog/sku-onboarding/skus` | SKUs within an onboarding submission (`GET_SKUS`) | READ |
| GET | `vendor/api/v1/catalog/sku-onboarding/template` | SKU-onboarding CSV template (`GET_CSV_TEMPLATE`) — static blank template | READ (file) |
| GET | `vendor/api/v2/product_onboarding/template` | v2 XLSX onboarding template (`GET_XLSX_TEMPLATE_V2`, base `p`) — static blank template | READ (file) |
| GET | `vendor/api/v1/catalog/failed-download` | Failed-rows file for a rejected upload (`FAILED_DOWNLOAD`) — retrieves the error report of a prior upload | READ (file) |
| GET | `vendor/api/v1/catalog/sku-onboarding/fetch-uploaded-file` | Fetch back a previously uploaded onboarding file (`FETCH_UPLOADED_FILE`) — read of existing content | READ (file) |
| GET | `vendor/api/v1/catalog/sku-onboarding/presigned-url` | Mint an S3 presigned URL for onboarding upload (`PRESIGNED_URL`) — returns a URL only; the subsequent PUT + register-file-upload are the writes (out of scope). Verb to confirm | READ (file) |
| GET | `vendor/api/v2/product_onboarding` | v2 product-onboarding base (`p`) — v2 equivalent of sku-onboarding list; verb/shape to confirm | READ (to confirm) |

## Out of scope (writes)

Never expose in a read-only CLI; documented from the bundle only, never called.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `vendor/api/v1/catalog-health-dashboard/suggestions/send-for-review` | Submit attribute suggestions for internal review (`SEND_FOR_REVIEW`) | WRITE |
| POST | `vendor/api/v1/catalog-health-dashboard/suggestions/send-to-vendor` | Push suggestions to the vendor (`SEND_TO_VENDOR`) | WRITE |
| POST | `vendor/api/v1/catalog/sku-onboarding/send-to-cm` | Submit onboarded SKUs to Zepto category managers (`SEND_TO_CM`) | WRITE |
| POST | `vendor/api/v1/catalog/sku-onboarding/register-file-upload` | Register a completed onboarding-sheet upload (`REGISTER_FILE_UPLOAD`) | WRITE (upload) |
| POST | `vendor/api/v2/product_onboarding/register_file_upload` | v2 register onboarding-sheet upload (`REGISTER_FILE_UPLOAD_V2`) | WRITE (upload) |
| POST | `vendor/api/v1/catalog/sku-onboarding/export` | Generate an SKU-attributes export (`EXPORT_SKU_ATTRIBUTES`) — enqueues an export job | EXPORT |
| POST | `fcc.zepto.co.in/api/v1/media/attachments` | `UPLOAD_LOGO` — media/logo attachment upload (a **gamification-service/rewards** const that co-located in this chunk grouping, not a catalog write; included for completeness) | WRITE (upload) |

## Probe note (evidence)

- **No endpoint upgraded to PROVEN.** Three read-only GET probes were fired (`sku-onboarding/list`, `catalog-health-dashboard/sku-ruleset-score/overview`, `catalog-health-dashboard/sku-ruleset-scores`); all returned **HTTP 404** from the `bifrost` gateway (`"Provided api path is not found in bifrost"`), which strips the `/vendor` prefix and cannot route the path without the vendor micro-frontend **proxy-target** header (not captured in the corpus). Auth was never reached (no 401). Independently, the captured JWT is past expiry (`exp` = Mon Jul 13 2026), matching the sibling [[RTV]] / [[Vendor-Reports-Queue]] probes which 401'd `Token expired`. Transcript: `captures/vendor/catalog-probes.txt`.
- **Source of truth:** the endpoint constants above are read out of the bundle chunks `1183.8940422c8268d8dc.js` (ads catalog), `3539.64ab07c46b8741b5.js` (catalog-health + sku-onboarding constant map `re`/`oe`/`p`), and `remoteEntry.js` (v2 `product_onboarding`), under `captures/js/vendor/`.
- **Exact request/response bodies want a live (read-only) capture** with a fresh token + correct proxy-target header to lock down filter keys and row schemas.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no upload, no send-to-cm/send-for-review/send-to-vendor, no export generation):

- `catalog health overview` → `catalog-health-dashboard/sku-ruleset-score/overview`.
- `catalog health scores [--pv-id …]` → `sku-ruleset-scores` / `sku-rule-scores`; `catalog health attributes` → `attribute-view`.
- `catalog sku review <pvId>` → `get-l4-values/{pvId}` + `suggestions/get-attributes-by-pv-id`.
- `catalog categories search <q>` → `catalog/category-hierarchy/search`.
- `catalog onboarding list` / `catalog onboarding drafts` / `catalog onboarding skus <id>` → the `sku-onboarding/{list,drafts,skus}` reads.
- `catalog onboarding template [--csv|--xlsx]` → `sku-onboarding/template` / `product_onboarding/template` (read-file); `catalog onboarding failed <id>` → `catalog/failed-download`.
- `catalog products [--search …]` / `catalog products validate <csv>` → `ads-bff/api/v1/catalog` + `validate` (validation reads).

Explicitly **excluded**: registering any file upload, sending SKUs to CM, sending suggestions for review / to vendor, and generating the SKU-attributes export — all writes / side-effecting.

## Connections

- Portal index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- Vendor-lane siblings: catalog health feeds the assortment JIVO can sell → [[Stock-View-Inventory]] (what's live/in-stock), [[Purchase-Orders]] (demand against onboarded SKUs); async exports land in [[Vendor-Reports-Queue]] (same queue pattern as the proven SALES/SOH flows).
- The ads product catalog (`ads-bff/api/v1/catalog`) is the same PVID picker reused by the ads lane campaign/creative flows.
