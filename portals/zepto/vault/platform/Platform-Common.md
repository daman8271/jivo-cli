---
title: Platform-Common (Layout, Commons, Config, Files, Support)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, platform, platform-common]
status: studied
---

# Platform-Common (Layout, Commons, Config, Files, Support)

The **Platform-Common** section is the Zepto seller portal's **shared plumbing** — the
cross-cutting endpoints every other lane leans on but that belong to no single lane:
the **layout/UI config** service (server-driven form/table/page metadata that the
micro-frontends render), the **commons** master-data lookups (vendor / manufacturer /
brand / category / city filter lists), **feature-flag & status config**, the
**file/attachment/document** plumbing (pre-signed S3 URLs, template downloads, bulk-job
report downloads), the **learning-center** content, the **Sendbird-backed chat** and
**CRM ticketing / vendor-support** surface, and the analytics **event publisher**. For
JIVO this is Jivo Wellness Pvt. Ltd. (`manufacturer_id
946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, Manufacturer / STANDARD tier); the captured
session is `ecom1@jivo.in`, role **"External Super Ads Admin"**.

The endpoint contracts below were extracted from the **root-shell**, **vendor** (635)
and **ads** (632) micro-frontend chunks — principally the API-constant maps in
`captures/js/vendor/3539.64ab07c46b8741b5.js` plus the `layout/config/*` string tables
across the ads and vendor bundles — **not** live captures except where a probe is noted.
Three hosts serve this surface: **`auth-backend.zepto.co.in`** (identity provider —
`api/v1/commons/*` master data, config, learning-center, chat token), **`fcc.zepto.co.in`**
(the vendor + ads BFF — `layout/config`, `contractservice`, `crm-ticketing`, `vendor`
bulk-jobs/tickets, file jobs), and **`events.zepto.co.in`** (the analytics event sink).
One JWT (`authorization: <jwt>`, **no** `Bearer` prefix) works across all three; WAF
headers were not enforced at last capture.

**This section is mostly READ.** It is master-data and UI-config plumbing, so the large
majority of endpoints are pure lookups. The writes are the human-action verbs that ride
on top of the plumbing — submitting feedback / chat, setting an impersonation session,
accepting terms, creating a support ticket or bulk job, updating an ads user, publishing
an analytics event — and the file **uploads** (mint-an-upload-URL / save-attachment /
document-upload). All of those are DOCUMENTED-FROM-BUNDLE ONLY and held out of scope.

## SPA route(s)

This section owns the shell chrome + the cross-cutting routes rather than one feature
page. Meaningful routes (from the root-shell + vendor route maps):

- `/` · `/dashboard` · `/dashboard/fulfillment` · `/dashboard/know-your-customer` — the
  shell landing + dashboards.
- `/vendor/*` (and bare mirrors): `/vendor/dashboard`, `/manage-vendor`,
  `/vendor-master` · `/vendor-master/distributor` · `/vendor-master/trade-vendors`,
  `/cdf-management` · `/cdf-management/creation` · `/cdf-management/approvals`,
  `/dn-cn` · `/dn-cn/review` · `/dn-cn/upload/:id`, `/sku-uploads` · `/sku-uploads/:uploadId`,
  `/learning-hub`, `/zepto-reactor`.
- **Support:** `/vendor-support` · `/vendor-support/:ticketId` · `/vendor-support/bulk-jobs`.
- **Ads shell:** `/ads` · `/ads/help-center` · `/ads/change-logs` · `/ads/pricing` ·
  `/ads/jarvis-ai` · `/ads/kams-ai` · `/ads/playground`.
- **Static/legal & misc:** `/terms-and-conditions` · `/terms-of-use` ·
  `/terms-of-spotlight-use` · `/forgot-password` · `/reset-password` · `/forms` ·
  `/feedbacks` · `/notifications` · `/learning-hub`.

The remaining path entries in the section data (`/eq`, `/gt`, `/lt`, `/or`, `/in`,
`/nin`, `/where`, `/regex`, `/metacounter`, `/sdk/*`, `/message/*`, `/push/*`,
`/reactions`, `/voters`, `/mute`, `/pin`, …) are **not SPA routes** — they are the
**Sendbird chat SDK's** query-operator / channel / statistics path fragments baked into
the bundled `sendbird` client, surfaced here only because they share the chunk. They are
noted for completeness and are not portal endpoints of ours.

## Backend host(s)

- **`auth-backend.zepto.co.in`** — identity provider + commons master-data. Path families
  `api/v1/commons/*` (vendor/manufacturer/brand/category/city lookups, status-config,
  user filter lists, learning-center, pre-signed URL), `api/v1/chat/*` (Sendbird token).
- **`fcc.zepto.co.in`** — vendor + ads BFF (same host the proven SALES / INVENTORY / ads
  pulls use). Path families `api/v1/layout/*` and `ads-bff/api/v1|v2/layout/*` (server-driven
  UI config/tables/pages), `contractservice/api/v1/*` (attachments, bulk-jobs, common
  master data), `crm-ticketing/api/v1/*` + `vendor/api/v1/ticket|bulk-job` (support),
  `api/v1/file-job/*` + `client/api/v1/file/*` + `vendor/api/v1/attachment/*` (files),
  `relay/api/v1/config/*` (feature flags), `brand-analytics-web/*` reconciliation reads.
- **`events.zepto.co.in`** — analytics event publisher (`api/v2/publish-events`). Write-only
  sink; held out of scope.

## API endpoints (READ)

Method shown as wired in the chunk: `GET`/`POST` = confirmed constant binding
(POST-with-`{filters}` list/search endpoints are **pure reads**, no state change, same
idiom as the proven report-queue lists); `UNKNOWN` = constant/path present but the verb
was not directly observed in this chunk — these are lookup/list/config resources whose
effect is a read (verb to confirm on a live capture). `READ (file)` = returns / mints a
**download** artifact or pre-signed **download** URL (no mutation).

### Commons master data & config — `auth-backend.zepto.co.in`

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/api/v1/chat/sendbird/user/token` | Fetch the Sendbird chat user token for this session (`N`) | READ |
| GET | `/api/v1/commons/brand-category-mapping` | Brand → category mapping (`GET_BRANDS_AND_CATEGORY`) | READ |
| GET | `/api/v1/commons/brand-l3-category-mapping` | Brand → L3-category mapping (`GET_BRAND_L3_CATEGORY_MAPPING_BA`) | READ |
| UNKNOWN | `/api/v1/commons/brand-manufacturer-mapping` | Brand ↔ manufacturer mapping (`MANUFACTURER_BRAND_MAPPING`; verb to confirm) | READ |
| GET | `/api/v1/commons/config/get-pre-signed-url` | Mint a pre-signed S3 **download** URL (`GET_PRESIGNED_URL`) | READ (file) |
| GET | `/api/v1/commons/config/learning-center/all` | All learning-center content (`GET_ALL_LEARNING_CONTENT`) | READ |
| GET | `/api/v1/commons/config/learning-center/get-by-subModule` | Learning-center content for a sub-module (`GET_LEARNING_CONTENT_BY_SUBMODULE`) | READ |
| GET | `/api/v1/commons/manufacturer-list` | Manufacturer list (`GET_MANUFACTURER_LIST`) | READ |
| GET | `/api/v1/commons/mh-list` | Merchandising-hierarchy list (`GET_MH_LIST`) | READ |
| GET | `/api/v1/commons/search-customers-and-vendors` | Search customers + vendors (`GET_VENDORS_LIST_V3`) | READ |
| POST | `/api/v1/commons/search-customers-and-vendors` | Same, POST-body filter variant (`GET_VENDORS_LIST_V3`) | READ |
| GET | `/api/v1/commons/search-vendors` | Vendor search (`GET_VENDORS_LIST` / `SEARCH_VENDORS`) | READ |
| POST | `/api/v1/commons/search-vendors` | Vendor search, POST-body variant (`GET_VENDORS_LIST`) | READ |
| GET | `/api/v1/commons/search-vendors-v2` | Vendor search v2 (`GET_VENDORS_LIST_V2`) | READ |
| POST | `/api/v1/commons/search-vendors-v2` | Vendor search v2, POST-body variant (`GET_VENDORS_LIST_V2`) | READ |
| GET | `/api/v1/commons/status-config` | Status enum/label config (`GET_STATUS_CONFIG`) | READ |
| GET | `/api/v1/commons/user/mh-list` | User-scoped location/MH filter list (`LOCATION_FILTER_LIST` / `EXTERNAL_LOCATION_FILTER_LIST`) | READ |
| GET | `/api/v1/commons/user/vendor-list` | User-scoped vendor filter list (`VENDOR_FILTER_LIST` / `EXTERNAL_VENDOR_FILTER_LIST`) | READ |

### Layout / UI config & tables — `fcc.zepto.co.in` (ads-bff + vendor)

Server-driven UI metadata: forms, tables, pages, modal/nudge/walkthrough configs. All are
static-config reads consumed by the micro-frontends at render time.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/ads-bff/api/v1/layout/config/create_campaign_modal_subtype_image_map` | Create-campaign modal subtype→image map (`GET_CREATE_CAMPAIGN_MODAL_SUBTYPE_IMAGE_MAP`) | READ |
| GET | `/ads-bff/api/v1/layout/config/jarvis_ai_ui_config` | Jarvis-AI UI config (`GET_UI_CONFIG`) | READ |
| GET | `/ads-bff/api/v1/layout/config/kam_ai_ui_config` | KAM-AI UI config (`GET_UI_CONFIG`) | READ |
| GET | `/ads-bff/api/v1/layout/config/payment_confirmation_modal_status_config` | Payment-confirmation modal status config (`GET_PAYMENT_STATUS_CONFIG`) | READ |
| GET | `/ads-bff/api/v1/layout/config/pricing_page_metadata` | Ads pricing-page metadata (`GET_PRICING_PAGE_METADATA`) | READ |
| GET | `/ads-bff/api/v2/layout/table/user_approvals_table_meta` | User-approvals table meta (`GET_APPROVERS_TABLE_METADATA`) | READ |
| UNKNOWN | `/ads-bff/api/v2/users` | Ads users table data (`USER_TABLE_DATA`; verb to confirm) | READ |
| UNKNOWN | `/api/v1/config` | Root config blob (verb to confirm) | READ |
| UNKNOWN | `/api/v1/config/get-configdata` | Config-data fetch (verb to confirm) | READ |
| UNKNOWN | `/api/v1/layout/config/${e}` | Generic layout-config fetch by key (verb to confirm) | READ |
| UNKNOWN | `/api/v1/layout/config/AdCreativeSectionConfigXPlacementTypeMap` | Ad-creative section × placement-type map | READ |
| UNKNOWN | `/api/v1/layout/config/NewCreativeFormDetails` | New-creative form details | READ |
| UNKNOWN | `/api/v1/layout/config/nonEndemicCreativeFormDetails` | Non-endemic creative form details | READ |
| UNKNOWN | `/api/v1/layout/config/ads-banner-config` | Ads banner config | READ |
| UNKNOWN | `/api/v1/layout/config/ads-feature-metadata` | Ads feature metadata | READ |
| UNKNOWN | `/api/v1/layout/config/ads_brand_analytics_config` | Ads brand-analytics config | READ |
| UNKNOWN | `/api/v1/layout/config/campaign_forecast_review_config` | Campaign forecast-review config | READ |
| UNKNOWN | `/api/v1/layout/config/campain-review-detail-from` | Campaign review detail form | READ |
| UNKNOWN | `/api/v1/layout/config/category-popup-config` | Category-popup config | READ |
| UNKNOWN | `/api/v1/layout/config/create_campaign_walkthrough` | Create-campaign walkthrough steps | READ |
| UNKNOWN | `/api/v1/layout/config/dcm_trackers_fe_config` | DCM trackers FE config | READ |
| UNKNOWN | `/api/v1/layout/config/gamification_frequency_caps` | Gamification frequency caps | READ |
| UNKNOWN | `/api/v1/layout/config/hyperlocal_default_values` | Hyperlocal default values | READ |
| UNKNOWN | `/api/v1/layout/config/keywords-layout-config` | Keywords layout config | READ |
| UNKNOWN | `/api/v1/layout/config/pagewise-placements` | Page-wise placement config | READ |
| UNKNOWN | `/api/v1/layout/config/quick_edit_form_metadata` | Quick-edit form metadata | READ |
| UNKNOWN | `/api/v1/layout/config/quick_edit_nudge_metadata` | Quick-edit nudge metadata | READ |
| UNKNOWN | `/api/v1/layout/config/review-checklist` | Review-checklist config | READ |
| UNKNOWN | `/api/v1/layout/config/reward_creation_template_download_path` | Reward-creation template **download** path (config value) | READ (file) |
| UNKNOWN | `/api/v1/layout/config/smart_nudge_metadata` | Smart-nudge metadata | READ |
| UNKNOWN | `/api/v1/layout/config/smart_nudge_sub_headers` | Smart-nudge sub-headers | READ |
| UNKNOWN | `/api/v1/layout/config/summaryMetricsMeta` | Summary-metrics meta | READ |
| UNKNOWN | `/api/v1/layout/config/swap_strategy_metadata` | Swap-strategy metadata | READ |
| UNKNOWN | `/api/v1/layout/config/version-enforcer` | Client version-enforcer config | READ |
| UNKNOWN | `/api/v1/layout/page/${e}` | Generic layout-page fetch by key | READ |
| UNKNOWN | `/api/v1/layout/page/hyperlocal-help-center` | Hyperlocal help-center page | READ |
| UNKNOWN | `/api/v1/layout/table/campaign-review-table-meta` | Campaign-review table meta | READ |
| UNKNOWN | `/api/v1/layout/table/change-log-table-meta` | Change-log table meta | READ |
| UNKNOWN | `/api/v2/layout/table/users_table_meta` | Users table meta (v2) | READ |

### Admin, audit, filters, relay flags & analytics reconciliation — `fcc.zepto.co.in`

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `/api/v1/admin/brands/metrics/summary` | Admin brands metrics summary (verb to confirm) | READ |
| UNKNOWN | `/api/v1/admin/campaigns` | Admin campaigns list (verb to confirm) | READ |
| UNKNOWN | `/api/v1/audit-logs` | Audit-log listing (verb to confirm) | READ |
| UNKNOWN | `/api/v1/commons/search-ntv` | Search non-trade vendors (verb to confirm) | READ |
| GET | `/api/v1/filter/city-list` | City filter list (`GET_CITY`) | READ |
| UNKNOWN | `/api/v1/log-details` | Log-details lookup (verb to confirm) | READ |
| UNKNOWN | `/api/v2/ips/debit-note` | IPS debit-note lookup (verb to confirm; noun resource, read effect) | READ |
| GET | `/brand-analytics-web/api/v1/common/enhancement-config` | Analytics enhancement config (`GET_ENHANCEMENT_CONFIG`) | READ |
| UNKNOWN | `/brand-analytics-web/api/v1/reconciliation/inventory/city-level-listing` | Inventory reconciliation, city-level listing | READ |
| UNKNOWN | `/brand-analytics-web/api/v1/reconciliation/inventory/summary` | Inventory reconciliation summary | READ |
| UNKNOWN | `/brand-analytics-web/api/v1/reconciliation/inventory/vendor-level-listing` | Inventory reconciliation, vendor-level listing | READ |
| UNKNOWN | `/relay/api/v1/config` | Relay/flagship config (verb to confirm) | READ |
| GET | `/relay/api/v1/config/get-configdata` | Feature flags (`GET_FETAURE_FLAGS`) | READ |

### Files & attachments (download / pre-signed **download** URLs) — `fcc.zepto.co.in`

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `/api/v1/file-job/download-file` | Download a file-job output | READ (file) |
| UNKNOWN | `/api/v1/file-job/get-signed-url` | Mint a signed URL for a file-job artifact (verb to confirm; download context) | READ (file) |
| UNKNOWN | `/api/v1/s3/file` | Fetch an S3 file (verb to confirm) | READ (file) |
| UNKNOWN | `/client/api/v1/file/${e}/get-presigned-url` | Pre-signed **download** URL for a client file (verb to confirm) | READ (file) |
| GET | `/contractservice/api/v1/attachment` | Contract attachment content (`GET_CONTRACT_ATTACHMENT_CONTENT`) | READ (file) |
| GET | `/contractservice/api/v1/attachment/pre-signed-url` | Pre-signed **download** URL for a contract attachment (`GET_ATTACHMENT_PRE_SIGNED_URL`) | READ (file) |
| GET | `/contractservice/api/v1/bulk-jobs/download-template` | Download the contract bulk-job template (`DOWNLOAD_BULK_JOB_TEMPLATE`) | READ (file) |
| UNKNOWN | `/vendor/api/v1/attachment/get-presigned-url` | Pre-signed **download** URL for a vendor attachment (`rt`) | READ (file) |
| UNKNOWN | `/vendor/api/v1/attachment/get-template` | Download a vendor attachment template (`ot`) | READ (file) |
| UNKNOWN | `/vendor/api/v1/bulk-job/${e}/download-report` | Download a vendor bulk-job report | READ (file) |
| GET | `/vendor/api/v1/bulk-job/download-template` | Download the vendor bulk-ticket template (`DOWNLOAD_BULK_TICKET_TEMPLATE`) | READ (file) |
| GET | `/vendor/api/v2/util/document-download` | Download a document (`DOWNLOAD_DOCUMENT`) | READ (file) |

### Contract-service common master data — `fcc.zepto.co.in`

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/contractservice/api/v1/bulk-jobs/list` | List contract bulk jobs (`BULK_JOB_LIST`) | READ |
| GET | `/contractservice/api/v1/common/fbz-margins` | FBZ margins (`GET_FBZ_MARGINS`) | READ |
| GET | `/contractservice/api/v1/common/fbz-payment-terms` | FBZ payment terms (`GET_PAYMENT_TERMS`) | READ |
| GET | `/contractservice/api/v1/common/get-brands-of-manufacturer` | Brands of a manufacturer (`GET_BRANDS_OF_MANUFACTURER`) | READ |
| GET | `/contractservice/api/v1/common/get-categories-of-manufacturer` | Categories of a manufacturer (`GET_CATEGORIES`) | READ |
| GET | `/contractservice/api/v1/common/get-subcategories-of-manufacturer` | Sub-categories of a manufacturer (`GET_SUB_CATEGORIES`) | READ |
| GET | `/contractservice/api/v1/common/manufacturer-list` | Manufacturer/distributor search (`SEARCH_MANUFACTURERS_DISTRIBUTORS`) | READ |
| GET | `/contractservice/api/v1/common/vendor-details` | Vendor details by code (`GET_VENDORS_DETAILS_BY_CODE`) | READ |
| GET | `/contractservice/api/v1/common/vendor-list` | Vendor search (`SEARCH_VENDORS`) | READ |

### Support: CRM ticketing, vendor tickets, bulk jobs, meta — `fcc.zepto.co.in`

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN | `/crm-ticketing/api/v1/ticket/${e}` | Single support ticket detail (verb to confirm; GET = read) | READ |
| UNKNOWN | `/crm-ticketing/api/v1/ticket/${e}/notes` | Notes on a ticket (verb to confirm; GET lists notes) | READ |
| UNKNOWN | `/crm-ticketing/api/v1/tickets` | Support ticket listing (verb to confirm) | READ |
| UNKNOWN | `/internal/api/v1/vendor-po` | Internal vendor-PO lookup (verb to confirm) | READ |
| GET | `/vendor/api/v1/bulk-job` | List vendor bulk-ticket jobs (`GET_BULK_TICKET_JOBS`) | READ |
| GET | `/vendor/api/v1/commons/search-ntv` | Search non-trade vendors (`SEARCH_NTV`) | READ |
| POST | `/vendor/api/v1/commons/search-ntv` | Search non-trade vendors, POST-body variant (`SEARCH_NTV`) | READ |
| GET | `/vendor/api/v1/config/load` | Vendor shell meta/config (`GET_META_INFO`) | READ · probed → **401 Token expired** (documented, expired-token) |

## Out of scope (writes) — never expose in a read-only CLI

DOCUMENTED-FROM-BUNDLE ONLY. A strict read-only study must never call any of these —
every one mutates server state, records a human action, fires an event/email, or
**uploads** a file.

| METHOD | Path | Purpose | Why held out |
|---|---|---|---|
| POST | `auth-backend /api/v1/chat/feedback` | Submit chat feedback (`POST_CHAT_FEEDBACK`) | Records feedback. WRITE. |
| POST | `auth-backend /api/v1/chat/sendbird/user/token/refresh` | Refresh/mint the Sendbird chat token (`v`) | Mints a token. WRITE. |
| POST | `auth-backend /api/v1/commons/feedback` | Submit portal feedback (`POST_FEEDBACK`) | Records feedback. WRITE. |
| POST | `auth-backend /api/v1/commons/impersonation` | Set an impersonation session (`SET_IMPERSONATION`) | Changes session identity. WRITE. |
| POST | `auth-backend /api/v1/commons/tnc/user` | Record the user's terms-and-conditions acceptance (`R`/`g`) | Mutates user TnC state. WRITE. |
| POST | `events /api/v2/publish-events` | Publish analytics events (`NX_EVENT_SERVICE_ENDPOINT`) | Emits/stores events. WRITE. |
| POST | `fcc /ads-bff/api/v2/users/${e}/update` | Update an ads user | Mutates a user. WRITE. |
| POST | `fcc /ads-bff/api/v2/users/${e}/update/payload` | Update an ads user (payload variant) | Mutates a user. WRITE. |
| UNKNOWN (write) | `fcc /api/v1/domain/create-domains` | Create domain(s) | `create`. WRITE. |
| POST | `fcc /contractservice/api/v1/bulk-jobs/create` | Create a contract bulk job (`CREATE_BULK_CONTRACT_JOB`) | Creates a job. WRITE. |
| UNKNOWN (write) | `fcc /crm-ticketing/api/v1/ticket/${e}/actions/reassign` | Reassign a support ticket | Ticket action. WRITE. |
| UNKNOWN (write) | `fcc /crm-ticketing/api/v1/ticket/${e}/actions/reopen` | Reopen a support ticket | Ticket action. WRITE. |
| UNKNOWN (write) | `fcc /customer/api/v1/ticket/${e}/rating` | Submit a ticket satisfaction rating | Records a rating. WRITE. |
| POST | `fcc /vendor/api/v1/bulk-job/create` | Create a vendor bulk-ticket job (`CREATE_BULK_TICKET_JOB`) | Creates a job. WRITE. |
| POST | `fcc /vendor/api/v1/ticket/create` | Create a support ticket (`CREATE_TICKET`) | Creates a ticket. WRITE. |
| UNKNOWN (export) | `fcc /client/api/v1/file/generate-upload-url` | Mint an **upload** URL for a client file | Upload path. EXPORT/WRITE. |
| POST | `fcc /contractservice/api/v1/attachment/save` | Save/upload a rule artifact (`UPLOAD_RULE_ARTIFACT`) | Uploads a file. EXPORT/WRITE. |
| UNKNOWN (export) | `fcc /vendor/api/v1/attachment/get-upload-url` | Mint an **upload** URL for a vendor attachment (`st`) | Upload path. EXPORT/WRITE. |
| POST | `fcc /vendor/api/v2/util/document-upload` | Upload a document (`UPLOAD_DOCUMENT`) | Uploads a file. EXPORT/WRITE. |

## Live probe (evidence)

- **1 probe fired, read-only GET, then halted** (per the guardrails — stop on the first
  401/403/429). `GET https://fcc.zepto.co.in/vendor/api/v1/config/load` (const
  `GET_META_INFO`, the cleanest unambiguous pure-GET config read: matches
  `config`/`load`, no path param, no body, no download/export/upload/create/otp keyword)
  with the captured vendor JWT returned **`HTTP 401 {"code":401,"message":"Token
  expired"}`**. Same one shared token as the sibling platform-lane probe runs
  (`iat 1783887610`, `exp 1783967399` = 2026-07-13 18:29:59 UTC), lapsed ~11 days before
  this run (2026-07-24). No 2xx, so **nothing was upgraded to PROVEN**; all endpoints
  remain **documented (not probed)**. Transcript:
  `captures/platform/platform-common-probes.txt`.
- **Auth/base confirmed** by the proven sibling flows on the same host: SALES / INVENTORY
  (`fcc /api/v1/reports*`) and ads (`fcc /ads-bff/api/v1`) work with the identical
  `authorization: <jwt>` header (no `Bearer`), origin/referer `https://brands.zepto.co.in`.
  Re-run the probe queue in the transcript with a fresh token to lock response shapes.
- **Response shapes:** to confirm via live read-only capture. Expected: the
  `commons/*-list` / `search-vendors*` endpoints return arrays of `{id, name, code}`-style
  rows; `status-config` / `layout/config/*` return static JSON config blobs the FE renders;
  `relay/config/get-configdata` returns a feature-flag map; the `*-pre-signed-url` /
  `download-*` endpoints return a short-lived S3 URL or a file blob.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no feedback/chat post, no impersonation, no ticket/bulk-job
create, no upload, no event publish):

- `zepto commons vendors [--search …]` → `GET /api/v1/commons/search-vendors(-v2)` /
  `search-customers-and-vendors`; `zepto commons manufacturers` → `manufacturer-list`;
  `zepto commons cities` → `/api/v1/filter/city-list`. Master-data lookups. Pure READ.
- `zepto commons brand-category` / `brand-l3-category` / `brand-manufacturer` → the mapping
  endpoints; `zepto commons status-config` → `status-config`. Pure READ.
- `zepto config flags` → `GET /relay/api/v1/config/get-configdata` (`GET_FETAURE_FLAGS`);
  `zepto config layout <key>` → `GET /api/v1/layout/config/<key>` (any of the static UI
  configs above). Pure READ.
- `zepto learning-center [--submodule …]` → learning-center content. Pure READ.
- `zepto support tickets` / `zepto support ticket <id>` → `crm-ticketing/tickets` +
  `ticket/${id}` (+ `/notes`); `zepto support bulk-jobs` → `vendor/api/v1/bulk-job`. Pure
  READ (list/detail only — never reassign/reopen/rate/create).
- `zepto contracts common fbz-margins|fbz-payment-terms|brands|categories|subcategories` →
  the `contractservice/api/v1/common/*` reads. Pure READ.
- `zepto files download <presigned>` → consume an already-minted **download** pre-signed
  URL (`attachment/pre-signed-url`, `document-download`, bulk-job `download-report`,
  `download-template`). Pure READ (download only — never `get-upload-url` / `document-upload`
  / `attachment/save`).
- **Excluded:** feedback / chat-feedback, impersonation, tnc/user, publish-events,
  ads user update, ticket/bulk-job **create**, ticket reassign/reopen, ticket rating, and
  every upload / generate-upload-url / document-upload verb — all writes / exports. The CLI
  must **consume** config, master data and existing files, never mutate or upload.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] ·
  [[Read-Only-Guardrails]]
- **Tightest siblings** — this is the shared plumbing every lane draws on. The JWT it uses
  is minted by [[Auth-Identity]]; the user/role admin behind the same shell is
  [[Users-Access]]; the vendor/manufacturer master-data here feeds [[KYC-Onboarding]] and
  the contract lane [[Vendor-Contracts-Margins]].
- The `layout/config/*` + `ads-bff/*` UI configs drive the ads surfaces
  ([[Ads-Campaigns-Booking-Keywords]] · [[Creative-Management]] · [[Brand-Analytics]]); the
  `commons/*-list` + `filter/city-list` lookups populate filters across
  [[Purchase-Orders]] · [[ASN]] · [[Stock-View-Inventory]] · [[Payments]].
- The file/attachment/bulk-job plumbing here is the download side of the export flows in
  [[Vendor-Reports-Queue]] · [[Ledger-Recon-Upload]]; support tickets tie back to
  [[Subscription-Billing]] and every operational lane.
