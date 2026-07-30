---
title: Swiggy Instamart Endpoints (read-only master index)
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, endpoints, master-index]
status: studied
---


# Swiggy Instamart — Read-Only Master Endpoint Inventory

Consolidated inventory of **all 134 distinct endpoint contracts** extracted from the harvested SPA corpus (the `brand-portal-client` shell + its 6 module-federation remotes), grouped by section. This is the source of truth the read-only CLI is generated from.

`READ` / `READ_FILE` rows are safe to expose. `WRITE` / `EXPORT` rows mutate or side-effect and are **never** exposed. `UNKNOWN` rows have a binding but the method/posture was not proven from the minified source — per **G1 they are denied by default** and listed in full so nothing is hidden.

Atlas: [[00-Swiggy-Instamart-Atlas]] · Data model: [[Swiggy-Instamart-Data-Model]] · Inventory: [[Swiggy-Instamart-Data-Inventory]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Routes: [[Swiggy-Instamart-Pages-and-Routes]]

## Hosts (production)

| Host | Role | Endpoints |
|---|---|---|
| `brand-portal-service-http.swiggy.com` | brand-portal data API (`brandPortalServiceBasePath`) — ads, sales, catalog, brandverse | 65 |
| `picker.swiggy.com` | **SCM / movement-planning gateway** (`scmAPIGatewayBasePath`) — the whole vendor/supply lane. Never touched by JIVO's existing automation. | 37 |
| `partner-api.swiggy.com` | partner service (`partnerServiceBasePath`) — accounts, configs, campaign, reports v2, server clock | 25 |
| `ozone-idp-brands-im-kba.swiggy.com` | ozone IdP, BRAND user pool — login/OTP/refresh/signout (all WRITE) | 7 |

## Classification roll-up

| Class | Count | Exposed in the CLI? |
|---|---|---|
| READ | 75 | yes |
| READ_FILE | 1 | yes |
| WRITE | 32 | **no** |
| EXPORT | 8 | **no** (creates a queue row — G2) |
| UNKNOWN | 18 | **no** (G1 denies unproven) |
| **TOTAL** | **134** | |


---

## [[Purchase-Orders]]

Every PO Swiggy Instamart raises against JIVO's supplying vendors. — 5 endpoint(s). Folder `vault/supply/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | READ | `picker.swiggy.com/api/v1/listAllFCs` | `—` |
| POST | READ | `picker.swiggy.com/api/v1/listPurchaseOrderLines` | `GET_ITEM_LIST_DATA` |
| POST | READ | `picker.swiggy.com/api/v1/purchaseMetrics` | `—` |
| POST | READ | `picker.swiggy.com/api/v1/searchPurchaseOrder` | `GET_PO_DETAILS` |
| UNKNOWN | UNKNOWN | `picker.swiggy.com/api/v1/suppliers/searchSuppliers` | `—` |

---

## [[PO-Booking-Appointments]]

Slot booking for POs into Swiggy fulfilment centres. — 9 endpoint(s). Folder `vault/supply/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| GET | READ | `picker.swiggy.com/api/v1/batch/list` | `BATCH_LIST` |
| POST | WRITE | `picker.swiggy.com/api/v1/batch/submit` | `BULK_DOWNLOAD_PO_DATA` |
| POST | EXPORT | `picker.swiggy.com/api/v1/document/batch/generate` | `DOWNLOAD_SINGLE_PO_DATA` |
| POST | EXPORT | `picker.swiggy.com/api/v1/document/merged/generate` | `DOWNLOAD_MULTIPLE_PO_DATA` |
| UNKNOWN | WRITE | `picker.swiggy.com/api/v1/fc-appointment/batch-cancel` | `—` |
| UNKNOWN | WRITE | `picker.swiggy.com/api/v1/fc-appointment/batch-create` | `—` |
| UNKNOWN | WRITE | `picker.swiggy.com/api/v1/fc-appointment/batch-reschedule` | `—` |
| UNKNOWN | UNKNOWN | `picker.swiggy.com/api/v1/fc-appointment/recommend-slots` | `—` |
| UNKNOWN | UNKNOWN | `picker.swiggy.com/api/v1/fc-appointment/search` | `—` |

---

## [[Goods-Received-GRN]]

What Swiggy's facilities actually received against each PO. — 3 endpoint(s). Folder `vault/supply/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| UNKNOWN | UNKNOWN | `picker.swiggy.com/api/v1/grn-list-data` | `GET_GRN_DATA` |
| POST | READ | `picker.swiggy.com/api/v1/grn/searchGrnLines` | `—` |
| POST | READ | `picker.swiggy.com/api/v1/searchGrns` | `—` |

---

## [[Returns-RTV-and-Purchase-Returns]]

Return-to-vendor and purchase-return flows. — 5 endpoint(s). Folder `vault/supply/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | READ | `picker.swiggy.com/api/v1/returnMetrics` | `—` |
| POST | READ | `picker.swiggy.com/api/v1/search/rtv` | `—` |
| POST | READ | `picker.swiggy.com/api/v1/search/rtvLines` | `—` |
| POST | READ | `picker.swiggy.com/api/v1/searchPurchaseReturnLines` | `—` |
| POST | READ | `picker.swiggy.com/api/v1/searchPurchaseReturns` | `—` |

---

## [[Stock-On-Hand-and-Low-Stock]]

Dark-store level inventory, days-on-hand and low-stock alerts. — 3 endpoint(s). Folder `vault/supply/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | READ | `picker.swiggy.com/api/v1/inventory/metrics` | `—` |
| POST | READ | `picker.swiggy.com/api/v1/inventory/search/itemInventories` | `—` |
| POST | READ | `picker.swiggy.com/api/v1/inventory/search/lowStockFcs` | `—` |

---

## [[Availability-and-Fill-Rate]]

City/store availability and the fill-rate view. — 3 endpoint(s). Folder `vault/supply/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| GET | READ | `picker.swiggy.com/api/v1/brands/list` | `—` |
| GET | READ | `picker.swiggy.com/api/v1/category/list` | `—` |
| POST | READ | `picker.swiggy.com/api/v1/searchInventoryAvailabilityMetrics` | `—` |

---

## [[Vendor-Performance-Scores]]

Swiggy's scorecard on JIVO's supplying vendors. — 1 endpoint(s). Folder `vault/supply/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | READ | `picker.swiggy.com/api/v1/searchSupplierPerformanceMetrics` | `—` |

---

## [[Vendor-Downloads]]

The vendor lane's report queue and access scope. — 1 endpoint(s). Folder `vault/supply/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| GET | READ | `picker.swiggy.com/api/v1/vendorPortal/accessInfo` | `—` |

---

## [[Local-Buying]]

The local-buying indent flow — a separate login. — 7 endpoint(s). Folder `vault/supply/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | WRITE | `picker.swiggy.com/api/v1/external/indent/accept` | `ACCEPT_INDENT` |
| POST | READ | `picker.swiggy.com/api/v1/external/indent/get` | `GET_INDENT` |
| POST | WRITE | `picker.swiggy.com/api/v1/external/indent/item/update` | `UPDATE_INDENT,UPDATE_INDENT_ITEM` |
| POST | READ | `picker.swiggy.com/api/v1/external/indent/list_indent_items` | `GET_INDENT_ITEM_LIST` |
| POST | READ | `picker.swiggy.com/api/v1/external/indent/list_indents` | `GET_INDENT_LIST` |
| POST | READ_FILE | `picker.swiggy.com/api/v1/external/indent/po/download` | `PO_DOWNLOAD` |
| POST | WRITE | `picker.swiggy.com/api/v1/external/indent/reject` | `REJECT_INDENT` |

---

## [[Vendor-FAQ-Help]]

Help content and the support contact for the vendor lane. — 0 endpoint(s). Folder `vault/supply/`.

_Route/UI surface with no endpoint of its own._

---

## [[Sales-Reports]]

The sales xlsx queue — the one surface JIVO's cron already uses. — 7 endpoint(s). Folder `vault/ads/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | EXPORT | `brand-portal-service-http.swiggy.com/api/v1/sales/report` | `INITIATE_SALES_METRIC_REPORT` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/sales/reports` | `LIST_SALES_REPORTS` |
| POST | READ | `partner-api.swiggy.com/instamart/v1/report` | `GET_REPORT` |
| POST | EXPORT | `partner-api.swiggy.com/instamart/v1/report/initiate-bdpo-report` | `INITIATE_BDPO_METRIC_REPORT` |
| UNKNOWN | EXPORT | `partner-api.swiggy.com/instamart/v1/report/initiate-sales-report` | `—` |
| POST | READ | `partner-api.swiggy.com/instamart/v1/report/list-bdpo` | `GET_BDPO_REPORT` |
| POST | READ | `partner-api.swiggy.com/instamart/v1/report/list-sales` | `GET_SALES_REPORT` |

---

## [[Sales-Insights]]

City / product / category sales analytics — 47 metrics, 17 dimensions. — 2 endpoint(s). Folder `vault/ads/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/sales/filters` | `GET_SALES_INSIGHTS_FILTER_OPTIONS` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/sales/metric` | `GET_SALES_INSIGHTS_METRICS` |

---

## [[Ad-Campaigns]]

Every ad campaign, its budget, pacing and state. — 14 endpoint(s). Folder `vault/ads/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | WRITE | `brand-portal-service-http.swiggy.com/api/v1/bidding-events` | `FESTIVAL_BID_BOOSTER` |
| POST | WRITE | `brand-portal-service-http.swiggy.com/api/v1/campaign` | `CAMPAIGN_CREATE,CAMPAIGN_UPDATE,UPDATE_CAMPAIGN,CAMPAIGN_GET_BPS` |
| POST | WRITE | `brand-portal-service-http.swiggy.com/api/v1/campaign/batch` | `UPDATE_BIDS_KEY_UPDATE,UPDATE_KEYWORD_BIDS,BATCH_CAMPAIGN_UPDATE` |
| UNKNOWN | UNKNOWN | `brand-portal-service-http.swiggy.com/api/v1/campaign/estimate-metric` | `GET_CAMPAIGN_IMPRESSIONS` |
| PUT | WRITE | `brand-portal-service-http.swiggy.com/api/v1/campaign/pause` | `CAMPAIGN_PAUSE` |
| POST | WRITE | `brand-portal-service-http.swiggy.com/api/v1/campaign/resume` | `CAMPAIGN_RESUME` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/campaign/suggest-budget` | `SUGGEST_BUDGET` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/campaigns` | `BRAND_INSIGHTS_CAMPAIGNS` |
| UNKNOWN | UNKNOWN | `partner-api.swiggy.com/instamart/v1/campaign` | `CAMPAIGN_GET` |
| GET | READ | `partner-api.swiggy.com/instamart/v1/campaign/bpo` | `CAMPAIGN_GET_BPO` |
| UNKNOWN | WRITE | `partner-api.swiggy.com/instamart/v1/campaign/create` | `—` |
| POST | WRITE | `partner-api.swiggy.com/instamart/v1/campaign/deactivate` | `CAMPAIGN_DEACTIVATE` |
| UNKNOWN | UNKNOWN | `partner-api.swiggy.com/instamart/v1/campaign/list` | `CAMPAIGN_LIST` |
| UNKNOWN | WRITE | `partner-api.swiggy.com/instamart/v1/campaign/update` | `—` |

---

## [[Brand-Insights-Metrics]]

Ad performance metrics: impressions, clicks, spend, ROAS, share-of-voice. — 6 endpoint(s). Folder `vault/ads/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/advertiser/metrics` | `BRAND_INSIGHTS_METRICS` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/advertiser/metrics/batch` | `BRAND_INSIGHTS_GET_BATCH_ADVERTISER_METRICS` |
| POST | EXPORT | `brand-portal-service-http.swiggy.com/api/v1/advertiser/metrics/report` | `INITIATE_CUSTOM_METRICS_REPORT` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/advertiser/metrics/report/list` | `LIST_CUSTOM_REPORTS` |
| UNKNOWN | UNKNOWN | `brand-portal-service-http.swiggy.com/api/v1/get-advertiser-metrics` | `UPTIME_METRICS` |
| POST | READ | `partner-api.swiggy.com/instamart/v1/metrics` | `METRICS` |

---

## [[Keyword-And-Bid-Suggestions]]

Keyword suggestions, bid guidance, budget and placement recommendations. — 6 endpoint(s). Folder `vault/ads/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | WRITE | `brand-portal-service-http.swiggy.com/api/v1/campaigns/suggest_bids` | `SUGGEST_BID_IN_CAMPAIGNS,GET_SUGGEST_BIDS` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/keyword/campaign-insights` | `LIST_KEYWORD_CAMPAIGN_INSIGHTS` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/suggest/category-paths` | `SUGGEST_CATALOG_TARGETING` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/suggest/keyword/bids` | `KEYWORD_SUGGESTIONS` |
| UNKNOWN | UNKNOWN | `partner-api.swiggy.com/instamart/v1/keywords/l2-placement-suggestions` | `L2_CATEGORY_SUGGESTIONS` |
| UNKNOWN | UNKNOWN | `partner-api.swiggy.com/instamart/v1/keywords/suggestions` | `—` |

---

## [[Creatives]]

Ad creative library and its (excluded) upload path. — 3 endpoint(s). Folder `vault/ads/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/creative/details` | `CREATIVE_DETAILS` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/creative/list` | `PREAPPROVED_CREATIVES` |
| GET | WRITE | `partner-api.swiggy.com/instamart/v1/creative/get-upload-info-v2` | `GET_S3_UPLOAD_INFO` |

---

## [[Requisition-Orders]]

Release / requisition orders — the ads booking documents. — 3 endpoint(s). Folder `vault/ads/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| UNKNOWN | WRITE | `brand-portal-service-http.swiggy.com/api/v1/release-order` | `RELEASE_ORDER_GET,RELEASE_ORDER_DELETE` |
| POST | WRITE | `brand-portal-service-http.swiggy.com/api/v1/release-order/approve` | `RELEASE_ORDER_APPROVE` |
| POST | WRITE | `brand-portal-service-http.swiggy.com/api/v1/release-orders/search` | `RELEASE_ORDER_SEARCH` |

---

## [[Products-And-SPINs]]

JIVO's product catalogue as the ads platform sees it. — 4 endpoint(s). Folder `vault/ads/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/products/batch` | `GET_PRODUCTS_BATCH` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/products/filter` | `LIST_PRODUCTS_BY_BRAND` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/products/search` | `SEARCH_PRODUCTS` |
| POST | READ | `partner-api.swiggy.com/instamart/v1/products/filter` | `PRODUCTS_FILTER` |

---

## [[Ads-AI-Chat]]

An in-portal AI assistant over JIVO's own ads data. — 4 endpoint(s). Folder `vault/ads/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | UNKNOWN | `brand-portal-service-http.swiggy.com/api/v1/ads-chat/chat` | `ADS_CHAT` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/ads-chat/conversations/list` | `ADS_CHAT_LIST_SESSIONS` |
| DELETE | WRITE | `brand-portal-service-http.swiggy.com/api/v1/ads-chat/conversations/{conversation_id}` | `ADS_CHAT_DELETE_SESSION` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/ads-chat/conversations/{conversation_id}/messages/list` | `ADS_CHAT_GET_SESSION` |

---

## [[NPI-New-Product-Introduction]]

New Product Introduction pipeline. — 1 endpoint(s). Folder `vault/ads/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/suggest-placement` | `SUGGEST_PLACEMENT` |

---

## [[Discounts-BDPO]]

Brand-funded discount campaigns (BDPO) and their reports. — 15 endpoint(s). Folder `vault/brand/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | UNKNOWN | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign` | `—` |
| PUT | WRITE | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/disable` | `—` |
| GET | READ | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/file` | `—` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/search` | `—` |
| GET | READ | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/spins` | `—` |
| GET | WRITE | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/upload-status` | `—` |
| POST | UNKNOWN | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaigns` | `—` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/discounting/v1/metrics/batch` | `—` |
| POST | UNKNOWN | `brand-portal-service-http.swiggy.com/api/discounting/v1/tnc/acceptance` | `—` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/discount/reports` | `LIST_DISCOUNTS_REPORTS` |
| POST | EXPORT | `brand-portal-service-http.swiggy.com/api/v1/discounts/report` | `INITIATE_DISCOUNTS_METRIC_REPORT` |
| GET | READ | `partner-api.swiggy.com/im-discounts/v1/account/get` | `—` |
| GET | READ | `partner-api.swiggy.com/im-discounts/v1/account/list` | `—` |
| GET | READ | `partner-api.swiggy.com/im-discounts/v1/account/permissions` | `—` |
| GET | READ | `partner-api.swiggy.com/im-discounts/v1/configs` | `—` |

---

## [[Sampling-Campaigns]]

Product-sampling campaigns to acquire new users. — 3 endpoint(s). Folder `vault/brand/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/campaign/{0}` | `GET_CAMPAIGN_DETAILS` |
| UNKNOWN | UNKNOWN | `brand-portal-service-http.swiggy.com/api/v1/spins` | `GET_SPINS` |
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/spins/batch` | `GET_PRODUCT_SPINS_BATCH` |

---

## [[Brandverse]]

Swiggy's cross-platform brand campaign product. — 1 endpoint(s). Folder `vault/brand/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | READ | `brand-portal-service-http.swiggy.com/api/v1/3p/advertiser/metrics/batch` | `BATCH_METRICS` |

---

## [[Catalog-SPIN-Management]]

Product catalogue: SPIN attributes, change requests and approvals. — 14 endpoint(s). Folder `vault/brand/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | WRITE | `brand-portal-service-http.swiggy.com/v1/create_spin_change_request` | `CREATE_SPIN_CHANGE_REQUEST` |
| POST | EXPORT | `brand-portal-service-http.swiggy.com/v1/generate_signed_url` | `GENERATE_SIGNED_URL` |
| POST | READ | `brand-portal-service-http.swiggy.com/v1/get_spin_change_attribute_details` | `GET_SPIN_CHANGE_ATTRIBUTE_DETAILS` |
| POST | READ | `brand-portal-service-http.swiggy.com/v1/get_spin_change_workflow_details` | `GET_SPIN_CHANGE_WORKFLOW_DETAILS` |
| POST | READ | `brand-portal-service-http.swiggy.com/v1/get_spin_details` | `GET_SPIN_DETAILS` |
| POST | READ | `brand-portal-service-http.swiggy.com/v1/get_spin_metrics` | `GET_SPIN_METRICS` |
| POST | READ | `brand-portal-service-http.swiggy.com/v1/list_spin_change_requests` | `LIST_SPIN_CHANGE_REQUESTS` |
| POST | READ | `brand-portal-service-http.swiggy.com/v1/list_spins` | `LIST_SPINS` |
| POST | UNKNOWN | `brand-portal-service-http.swiggy.com/v1/reassign_spin_change_request` | `REASSIGN_SPIN_CHANGE_REQUEST` |
| POST | READ | `brand-portal-service-http.swiggy.com/v1/search_brands` | `SEARCH_BRANDS` |
| POST | READ | `brand-portal-service-http.swiggy.com/v1/search_categories` | `SEARCH_CATEGORIES` |
| POST | UNKNOWN | `brand-portal-service-http.swiggy.com/v1/transition_spin_change_request` | `TRANSITION_SPIN_CHANGE_REQUEST` |
| PUT | WRITE | `brand-portal-service-http.swiggy.com/v1/update_spin_change_workflow` | `UPDATE_SPIN_CHANGE_WORKFLOW` |
| POST | UNKNOWN | `brand-portal-service-http.swiggy.com/v1/validate_spin_change_request` | `VALIDATE_SPIN_CHANGE_REQUEST` |

---

## [[Accounts-And-Entities]]

The three JIVO accounts and what each may see. — 4 endpoint(s). Folder `vault/platform/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| GET | READ | `brand-portal-service-http.swiggy.com/api/v1/account/permissions` | `ACCOUNT_PERMISSIONS` |
| GET | READ | `partner-api.swiggy.com/instamart/v1/account/get` | `ACCOUNT_GET` |
| GET | READ | `partner-api.swiggy.com/instamart/v1/account/list` | `ACCOUNT_LIST` |
| GET | READ | `partner-api.swiggy.com/instamart/v1/account/permissions` | `ACCOUNT_PERMISSIONS` |

---

## [[Config-And-Feature-Flags]]

141 cities, 74 config keys, and the portal's whole feature surface. — 2 endpoint(s). Folder `vault/platform/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| GET | READ | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/config` | `—` |
| GET | READ | `partner-api.swiggy.com/instamart/v1/configs` | `FETCH_CONFIGS` |

---

## [[Auth-Sessions-And-Login]]

Email-OTP login, the JWT, and the endpoints this study refuses to call. — 8 endpoint(s). Folder `vault/platform/`.

| METHOD | Class | Host · Path | Const |
|---|---|---|---|
| POST | WRITE | `ozone-idp-brands-im-kba.swiggy.com/v1/accounts/createAuthURI` | `initiateLogin` |
| POST | WRITE | `ozone-idp-brands-im-kba.swiggy.com/v1/accounts/sendVerificationCode` | `sendVerificationCode` |
| POST | WRITE | `ozone-idp-brands-im-kba.swiggy.com/v1/accounts/signInWithIDP` | `signInWithIDP` |
| POST | WRITE | `ozone-idp-brands-im-kba.swiggy.com/v1/accounts/signInWithOTP` | `signInWithOTP` |
| POST | WRITE | `ozone-idp-brands-im-kba.swiggy.com/v1/accounts/signOut` | `signOut` |
| POST | WRITE | `ozone-idp-brands-im-kba.swiggy.com/v1/token/refresh` | `refreshToken,vendorRefreshToken` |
| POST | WRITE | `ozone-idp-brands-im-kba.swiggy.com/v2/accounts/sendVerificationCode` | `sendVerificationCode` |
| GET | READ | `partner-api.swiggy.com/time` | `TIME` |

---

## [[Telemetry-And-Third-Party]]

New Relic and Swiggy analytics beacons — out of scope, documented. — 0 endpoint(s). Folder `vault/platform/`.

_Route/UI surface with no endpoint of its own._

---

## Connections

- [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]] · [[Vendor-Performance-Scores]] · [[Vendor-Downloads]] · [[Local-Buying]] · [[Vendor-FAQ-Help]] · [[Sales-Reports]] · [[Sales-Insights]] · [[Ad-Campaigns]] · [[Brand-Insights-Metrics]] · [[Keyword-And-Bid-Suggestions]] · [[Creatives]] · [[Requisition-Orders]] · [[Products-And-SPINs]] · [[Ads-AI-Chat]] · [[NPI-New-Product-Introduction]] · [[Discounts-BDPO]] · [[Sampling-Campaigns]] · [[Brandverse]] · [[Catalog-SPIN-Management]] · [[Accounts-And-Entities]] · [[Config-And-Feature-Flags]] · [[Auth-Sessions-And-Login]] · [[Telemetry-And-Third-Party]]
