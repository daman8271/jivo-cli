---
title: KYC & Vendor Onboarding (VMS)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, platform, kyc-onboarding]
status: studied
---

# KYC & Vendor Onboarding (VMS)

The **KYC & Vendor Onboarding** section is Zepto's **VMS** (Vendor Management System) admin surface — the lead-to-vendor pipeline that takes a prospective supplier from an invited **lead** through **KYC** (GSTIN + PAN verification, bank details), **contract / VRF** (Vendor Registration Form) capture, **warehouse / vendor details**, and a **review → approve / reject / hold / modification-requested** workflow, ending in a **vendor-sync** into Zepto's master systems. It covers both the standard **trade-vendor / marketer / distributor** onboarding and the parallel **non-trade-vendor** onboarding (services / expense vendors), plus a **file / attachment** layer (templates, uploads, presigned downloads) and the VMS **config / mappings / status enums**. For JIVO this is Jivo Wellness Pvt. Ltd. (Manufacturer, STANDARD tier, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, login `ecom1@jivo.in`) — i.e. the record on the *other* side of this admin console; most of these routes are the operator/admin view of an onboarding record. All calls hit **`fcc.zepto.co.in`** under the **`vms/api/v1|v2/*`** prefix (with a handful of `brand-analytics-web/api/v1/kyc/*` consumer-analytics endpoints swept in by the `kyc` substring — see the naming note below), using the single JWT in the `authorization` header (no `Bearer` prefix) documented in [[Auth-and-Access]]. Endpoint contracts below were read out of the vendor remote (module-federation remote 635) code-split chunk `captures/js/vendor/3539.64ab07c46b8741b5.js` — the VMS API-constant maps (`GET_SUMMARY`, `GET_KYC_DETAILS`, `GET_CONTRACT_DETAILS`, `getMarketerDetailsById`, the `files/*` map, …) — plus the `GET_GSTIN_DETAILS` constant seen in `remoteEntry.js` / `root-shell-main.*`. They are not live captures (the only JWT on disk is expired; see evidence).

> **Naming note — two different "KYC".** This section merges two unrelated feature families that share the `kyc` token: (1) **identity/onboarding KYC** = `vms/api/v1/*/kyc/*` (GSTIN, PAN, bank, the real vendor-onboarding KYC), and (2) **consumer "Know Your Consumer" analytics** = `brand-analytics-web/api/v1/kyc/*` (conversion funnel, brand recall, ARPU, penetration/retention) which actually belongs to the ads **[[Brand-Analytics]]** lane. Both are documented here (no endpoint is dropped), but the `brand-analytics-web/*` rows are analytics reads, not onboarding.

## Subpages & tabs

**Leads onboarding hub** — `/leads-onboarding` (shell alias `/vendor/leads-onboarding`), with per-persona profile pages:
- **Advertiser profile** — `/leads-onboarding/advertiser-profile` → `/vendor/leads-onboarding/advertiser-profile/:userId`.
- **Marketer profile** — `/leads-onboarding/marketer-profile` → `/vendor/leads-onboarding/marketer-profile/:userId`.
- **Vendor profile** — `/leads-onboarding/vendor-profile` → `/vendor/leads-onboarding/vendor-profile/:userId`.
- Lead pipeline reads: summary tiles (`GET_SUMMARY` = `vms/api/v1/admin/lead/summary`), the full lead grid (`GET_ALL_LEADS` = `vms/api/v1/admin/lead/filter`), per-lead detail (`GET_LEAD_DETAILS` = `vms/api/v1/admin/user/lead`) and user detail (`GET_USER_DETAILS` = `vms/api/v1/admin/lead/get-user-details`), status enums (`LEADS_STATUS_CONFIG`), and lead categories (`GET_CATGORIES`). Lead **actions** (invite / approve / reject / on-hold) are writes — held out of scope.

**Vendor master — marketer** — `/vendor-master/marketer` (alias `/vendor/vendor-master/marketer`)
- Marketer directory: list (`GET_MARKETER_LIST` = `vms/api/v1/admin/marketer/filter`), search (`SEARCH_MARKETER` = `vms/api/v1/admin/marketer/search`), single marketer (`getMarketerDetailsById` = `vms/api/v1/admin/marketer/{id}`), and the distributor list (`GET_DISTRIBUTOR_LIST` = `vms/api/v1/admin/distributor/filter`). Marketer **create / update / link** are writes — out of scope.

**Onboarding record (trade vendor)** — the KYC / contract / details tabs for a vendor being onboarded:
- **Basic / contract (VRF)** — onboarding summary (`GET_SUMMARY` = `vms/api/v1/admin/basic-details/onboarding-summary`), filtered onboarding list (`GET_FILTERED_LIST` = `.../onboarding-filter`), VRF details (`GET_VRF_DETAILS` = `.../contract-details`), contracts (`GET_CONTRACT_DETAILS` = `.../fetch-contracts`), and the `ONBOARDING_STATUS_CONFIG` / `GET_MAPPINGS` enums.
- **KYC tab** — `GET_KYC_DETAILS` = `vms/api/v1/admin/kyc/fetch`; supporting GSTIN lookup (`GET_GSTIN_DETAILS` = `vms/api/v1/kyc/gstin-details`). PAN verification + KYC save are writes.
- **Bank details** — `GET_BANK_DETAILS` = `vms/api/v1/admin/bank-details/fetch`.
- **Warehouse / vendor details** — `GET_VENDOR_DETAILS` = `vms/api/v1/admin/warehouse-details/fetch`.
- **Attachments** — content (`GET_ATTACHMENT_CONTENT` = `vms/api/v1/admin/attachment`), presigned download (`DOWNLOAD_ATTACHMENT` = `.../attachment/pre-signed-url`), and the vendor-attachments list (`GET_VENDOR_ATTACHMENTS` = `vms/api/v1/admin/common/vendor-attachments`).
- **Vendor sync status** — `GET_SYNC_STATUS_DETAILS` = `vms/api/v1/admin/vendor-sync/get-by-user-id` (held out of scope, see below).

**Onboarding record (non-trade vendor)** — the parallel `non-trade-vendor/*` family: onboarding summary / filter / status-config, VRF (`contract-details`), contracts (`fetch-contracts`), bank details, warehouse details, vendor-attachments, profile (`GET_VENDOR_PROFILE` = `.../user/non-trade-vendor/profile`), unified review (`UNIFIED_REVIEW` = `.../user/non-trade-vendor/review`), and approval data (`GET_APPROVAL_DATA` = `.../user/non-trade-vendor/approval-onboarding-data`). Its KYC/contract/warehouse **saves** and the `counterpart` create are writes.

**Files layer** — the VMS shared file service used by every tab: list (`GET_FILES_LIST` = `vms/api/v1/files/filter`), fetch-by-id (`getFile` = `vms/api/v1/files/{id}`), error file (`GET_ERROR_FILE` = `vms/api/v1/files/error`), and download **templates** (`GET_TEMPLATE_FILE` = `vms/api/v1/files/template`, plus the v2 `vms/api/v2/files/template`). Uploads (`files/upload`, `attachment/save`) are writes.

**Vendor v2 lookups** — `vms/api/v2/vendor/*`: `filter` (list), `manufacturer-ids`, `relation-type` are reads; `update` and `extend-organization` are writes.

## Naming / classification note (what the grids show)

The section is admin-CRUD-shaped: every family exposes a **list/filter + summary + per-record fetch** read triplet and a **save/approve/reject** write set. Status enums (`LEADS_STATUS_CONFIG`, `ONBOARDING_STATUS_CONFIG`) and field mappings (`GET_MAPPINGS`) drive the columns and are served as their own config reads. The exact column arrays + status label maps render client-side in `3539.…js`; a logged-in grid capture is still owed (JWT expired at capture time).

## API endpoints

Base = `https://fcc.zepto.co.in/` + path. `{id}` = a user / marketer id path parameter (the bundle wires these as `` e=>`vms/api/v1/admin/marketer/${e}` ``). Auth = `authorization: <jwt>` (no `Bearer`), `accept: application/json`; WAF headers not enforced as of last capture. All rows below are pure reads (GET, or an analytics GET); `READ (file)` = returns / links to a document blob (no state change).

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/vms/api/v1/admin/basic-details/onboarding-summary` | Trade-vendor onboarding summary tiles (`GET_SUMMARY`) — probed → 401 | READ |
| GET | `/vms/api/v1/admin/basic-details/onboarding-filter` | Filtered onboarding record list (`GET_FILTERED_LIST`) | READ |
| GET | `/vms/api/v1/admin/basic-details/contract-details` | VRF / registration-form details (`GET_VRF_DETAILS`) | READ |
| GET | `/vms/api/v1/admin/basic-details/fetch-contracts` | Contract(s) on the onboarding record (`GET_CONTRACT_DETAILS`) | READ |
| GET | `/vms/api/v1/admin/kyc/fetch` | KYC details for a vendor (`GET_KYC_DETAILS`) | READ |
| GET | `/vms/api/v1/kyc/gstin-details` | GSTIN lookup / details (`GET_GSTIN_DETAILS`) | READ |
| GET | `/api/v1/kyc/gstin-details` | GSTIN lookup — bare-path variant of the above (seen in `remoteEntry.js`) | READ |
| GET | `/vms/api/v1/admin/bank-details/fetch` | Bank details for a vendor (`GET_BANK_DETAILS`) | READ |
| GET | `/vms/api/v1/admin/warehouse-details/fetch` | Warehouse / vendor details (`GET_VENDOR_DETAILS`) | READ |
| GET | `/vms/api/v1/admin/common/vendor-attachments` | Vendor attachment list (`GET_VENDOR_ATTACHMENTS`) | READ |
| GET | `/vms/api/v1/admin/attachment` | Attachment content (`GET_ATTACHMENT_CONTENT`) | READ (file) |
| GET | `/vms/api/v1/admin/attachment/pre-signed-url` | Presigned download URL for an attachment (`DOWNLOAD_ATTACHMENT`) | READ (file) |
| GET | `/vms/api/v1/admin/common/category` | Vendor / lead categories (`GET_CATGORIES`) | READ |
| GET | `/vms/api/v1/admin/common/mappings` | Field / value mappings for the forms (`GET_MAPPINGS`) | READ |
| GET | `/vms/api/v1/admin/common/lead-status-config` | Lead-status enum config (`LEADS_STATUS_CONFIG`) | READ |
| GET | `/vms/api/v1/admin/common/onboarding-status-config` | Onboarding-status enum config (`ONBOARDING_STATUS_CONFIG`) | READ |
| GET | `/vms/api/v1/admin/config` | VMS admin config (`GET_CONFIG`) | READ |
| GET | `/vms/api/v1/admin/lead/summary` | Lead pipeline summary tiles (`GET_SUMMARY`) | READ |
| GET | `/vms/api/v1/admin/lead/filter` | Lead grid — all leads (`GET_ALL_LEADS`) | READ |
| GET | `/vms/api/v1/admin/lead/get-user-details` | User details behind a lead (`GET_USER_DETAILS`) | READ |
| GET | `/vms/api/v1/admin/user/lead` | Single lead detail (`GET_LEAD_DETAILS`) | READ |
| GET | `/vms/api/v1/admin/marketer/filter` | Marketer directory list (`GET_MARKETER_LIST`) | READ |
| GET | `/vms/api/v1/admin/marketer/search` | Marketer search (`SEARCH_MARKETER` / `SEARCH_MARKETER_BY_QUERY`) | READ |
| GET | `/vms/api/v1/admin/marketer/{id}` | Single marketer detail (`getMarketerDetailsById`) | READ |
| GET | `/vms/api/v1/admin/distributor/filter` | Distributor list (`GET_DISTRIBUTOR_LIST`) | READ |
| GET | `/vms/api/v1/admin/non-trade-vendor/onboarding-summary` | Non-trade onboarding summary (`GET_SUMMARY`) | READ |
| GET | `/vms/api/v1/admin/non-trade-vendor/onboarding-filter` | Non-trade onboarding list (`GET_FILTERED_LIST`) | READ |
| GET | `/vms/api/v1/admin/non-trade-vendor/onboarding-status-config` | Non-trade status enum config (`ONBOARDING_STATUS_CONFIG`) | READ |
| GET | `/vms/api/v1/admin/non-trade-vendor/contract-details` | Non-trade VRF details (`GET_VRF_DETAILS`) | READ |
| GET | `/vms/api/v1/admin/non-trade-vendor/fetch-contracts` | Non-trade contracts (`GET_CONTRACT_DETAILS`) | READ |
| GET | `/vms/api/v1/admin/non-trade-vendor/bank-details/fetch` | Non-trade bank details (`GET_BANK_DETAILS`) | READ |
| GET | `/vms/api/v1/admin/non-trade-vendor/warehouse-details/fetch` | Non-trade warehouse details (`GET_VENDOR_DETAILS`) | READ |
| GET | `/vms/api/v1/admin/non-trade-vendor/vendor-attachments` | Non-trade attachment list (`GET_VENDOR_ATTACHMENTS`) | READ |
| GET | `/vms/api/v1/admin/user/non-trade-vendor/profile` | Non-trade vendor profile (`GET_VENDOR_PROFILE`) | READ |
| GET | `/vms/api/v1/admin/user/non-trade-vendor/approval-onboarding-data` | Non-trade approval data (`GET_APPROVAL_DATA`) | READ |
| GET | `/vms/api/v1/admin/user/non-trade-vendor/review` | Non-trade unified review view (`UNIFIED_REVIEW`) | READ |
| GET | `/vms/api/v1/files/filter` | VMS file list (`GET_FILES_LIST`) | READ |
| GET | `/vms/api/v1/files/{id}` | Fetch a file by id (`getFile`) | READ (file) |
| GET | `/vms/api/v1/files/error` | Error file for a failed upload/job (`GET_ERROR_FILE`) | READ (file) |
| GET | `/vms/api/v1/files/template` | Download an upload template (`GET_TEMPLATE_FILE`) | READ (file) |
| GET | `/vms/api/v2/files/template` | Download an upload template, v2 (`GET_TEMPLATE_FILE_V2`) | READ (file) |
| GET | `/vms/api/v2/vendor/filter` | Vendor list, v2 (`At`) | READ |
| GET | `/vms/api/v2/vendor/manufacturer-ids` | Manufacturer-id lookup, v2 (`ut`) | READ |
| GET | `/vms/api/v2/vendor/relation-type` | Vendor relation-type lookup, v2 (`Nt`) | READ |
| GET | `/brand-analytics-web/api/v1/kyc/average-revenue-per-user` | Consumer analytics: ARPU (`KYC_GET_REVENUE_PER_USER`) — belongs to [[Brand-Analytics]] | READ |
| GET | `/brand-analytics-web/api/v1/kyc/brand-recall` | Consumer analytics: brand recall (`KYC_GET_BRANDS_RECALL`) | READ |
| GET | `/brand-analytics-web/api/v1/kyc/customer-penetration` | Consumer analytics: penetration (`KYC_GET_CUSTOMER_PENETRATION`) | READ |
| GET | `/brand-analytics-web/api/v1/kyc/customer-retention` | Consumer analytics: retention (`KYC_GET_CUSTOMER_RETENTION`) | READ |
| GET | `/brand-analytics-web/api/v1/kyc/product-view-to-action` | Consumer analytics: view→action (`KYC_GET_PRODUCT_VIEW_TO_ACTION`) | READ |
| GET | `/brand-analytics-web/api/v1/kyc/top-searched-keywords` | Consumer analytics: top keywords (`KYC_GET_TOP_SEARCHED_KEYWORDS`) | READ |
| GET | `/brand-analytics-web/api/v1/kyc/action-to-purchase` | Consumer analytics: action→purchase (`KYC_ACTION_TO_PURCHASE`; method wired as UNKNOWN, read effect) | READ |
| GET | `/brand-analytics-web/api/v1/kyc/overall-conversion` | Consumer analytics: overall conversion (`KYC_OVERALL_CONVERSION`; method UNKNOWN, read effect) | READ |
| GET | `/brand-analytics-web/api/v1/kyc/overall-conversion-funnel` | Consumer analytics: conversion funnel (`KYC_OVERALL_CONVERSION_FUNNEL`; method UNKNOWN, read effect) | READ |

> Probe status: `GET /vms/api/v1/admin/basic-details/onboarding-summary` fired once (read-only) → **HTTP 401 `{"message":"Token expired","code":401}`**; halted per guardrails. **0 PROVEN**; all 53 reads remain **documented (not probed)**. Transcript: `captures/platform/kyc-onboarding-probes.txt`.

**Out of scope (writes / uploads / side-effects) — documented from the bundle only, never called by a read-only CLI:**

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/vms/api/v1/admin/basic-details/save-contract` | Save contract on onboarding record (`SAVE_CONTRACT_DETAILS`) | WRITE |
| POST | `/vms/api/v1/admin/kyc/save` | Save KYC details (`SAVE_KYC_DETAILS`) | WRITE |
| POST* | `/vms/api/v1/admin/kyc/pan-verification` | Trigger PAN verification (`PAN_VERIFICATION`; external side-effecting call) | WRITE |
| POST | `/vms/api/v1/admin/lead` | Save / create lead (`SAVE_LEAD_DETAILS`) | WRITE |
| POST | `/vms/api/v1/admin/lead/invite` | Invite a lead — sends invite (`INVITE_LEAD`) | WRITE |
| POST | `/vms/api/v1/admin/lead/reject` | Reject a lead (`REJECT_LEAD`) | WRITE |
| PUT | `/vms/api/v1/admin/lead/on-hold` | Put a lead on hold (`PUT_LEAD_ON_HOLD`) | WRITE |
| POST | `/vms/api/v2/admin/lead/approve` | Approve a lead (`APPROVE_LEAD`) | WRITE |
| POST | `/vms/api/v1/admin/marketer/admin-creation` | Create a marketer (`CREATE_MARKETER`) | WRITE |
| PUT | `/vms/api/v1/admin/marketer/{id}/update` | Update a marketer (`updateMarketerDetailsById`) | WRITE |
| POST* | `/vms/api/v1/admin/marketer/link-marketer` | Link a marketer to a vendor (`LINK_MARKETER`) | WRITE |
| POST | `/vms/api/v1/admin/warehouse-details/save` | Save warehouse / vendor details (`SAVE_VENDOR_DETAILS`) | WRITE |
| POST | `/vms/api/v1/admin/user/approve-onboarding-data` | Approve an onboarding record (`APPROVE_ONBOARDING`) | WRITE |
| POST | `/vms/api/v1/admin/user/reject-onboarding-data` | Reject an onboarding record (`REJECT_ONBOARDING`) | WRITE |
| PUT | `/vms/api/v1/admin/user/hold-onboarding-data` | Put an onboarding record on hold (`PUT_ON_HOLD`) | WRITE |
| POST* | `/vms/api/v1/admin/user/modification-requested` | Request modification on a record (`REQUEST_MODIFICATION`) | WRITE |
| POST* | `/vms/api/v1/admin/user/send-reminder-mail` | Send a reminder email (`SEND_REMINDER_MAIL`) | WRITE |
| POST | `/vms/api/v1/admin/non-trade-vendor/kyc/save` | Save non-trade KYC (`SAVE_KYC_DETAILS`) | WRITE |
| POST | `/vms/api/v1/admin/non-trade-vendor/save-contract` | Save non-trade contract (`SAVE_CONTRACT_DETAILS`) | WRITE |
| POST | `/vms/api/v1/admin/non-trade-vendor/warehouse-details/save` | Save non-trade warehouse details (`SAVE_VENDOR_DETAILS`) | WRITE |
| POST | `/vms/api/v1/admin/non-trade-vendor/counterpart` | Create counterpart vendor (`CREATE_COUNTERPART_VENDOR`) | WRITE |
| PUT | `/vms/api/v2/vendor/update` | Update vendor via VMS (`UPDATE_VENDOR_VMS`) | WRITE |
| POST* | `/vms/api/v2/vendor/extend-organization` | Extend vendor organization (`pt`; mutating action, method UNKNOWN) | WRITE |
| POST | `/vms/api/v1/admin/attachment/save` | Upload an attachment (`UPLOAD_ATTACHMENT`) | EXPORT (upload) |
| POST | `/vms/api/v2/admin/attachment/save` | Upload an attachment, v2 (`UPLOAD_ATTACHMENT_V2`) | EXPORT (upload) |
| POST* | `/vms/api/v1/files/upload` | Upload a file (`UPLOAD_FILE`; the `GET_UPLOADED_FILE` read alias shares the path) | EXPORT (upload) |
| GET† | `/vms/api/v1/admin/vendor-sync/get-by-user-id` | Vendor-sync status by user id (`GET_SYNC_STATUS_DETAILS`) — tagged as a sync/export op | EXPORT |
| GET† | `/vms/api/v1/admin/non-trade-vendor/vendor-sync/get-by-user-id` | Non-trade vendor-sync status by user id (`GET_SYNC_STATUS_DETAILS`) | EXPORT |

\* method not literally bound to `doHttpGet`/`doHttpPost` in the bundle (constant is a bare path string); verb inferred from the mutating action name and held as WRITE regardless.
† `vendor-sync/get-by-user-id` is wired as a GET and reads like a status fetch, but is classified **EXPORT** in the source extraction (it can trigger / reflect a downstream sync into Zepto's master systems). Held out of the read-only surface conservatively per [[Read-Only-Guardrails]]; if a fresh capture confirms it is a pure status read, it can be promoted to the read table.

## Real data seen (evidence)

- **Endpoint set** extracted from the vendor remote (module-federation remote 635) chunk `captures/js/vendor/3539.64ab07c46b8741b5.js` — the VMS constant maps (`GET_SUMMARY`, `GET_FILTERED_LIST`, `GET_VRF_DETAILS`, `GET_CONTRACT_DETAILS`, `GET_KYC_DETAILS`, `GET_BANK_DETAILS`, `GET_VENDOR_DETAILS`, `GET_VENDOR_ATTACHMENTS`, `GET_MAPPINGS`, `GET_CATGORIES`, `LEADS_STATUS_CONFIG`, `ONBOARDING_STATUS_CONFIG`, the `non-trade-vendor/*` mirror set, the `files/*` map, and the id-templated `getMarketerDetailsById` / `getFile` bindings) — plus `GET_GSTIN_DETAILS` seen in `remoteEntry.js` and `root-shell-main.8a3af4e6aebe630f.js`.
- **Backend confirmed** = `fcc.zepto.co.in` (same host as the already-proven SALES + INVENTORY `api/v1/reports*` pulls in `zepto-cli`), so the auth model and host are live; only the token is stale. The VMS service lives under the `vms/` path prefix on that host.
- **Live probe (read-only, 2026-07-24):** `GET /vms/api/v1/admin/basic-details/onboarding-summary` → **401 `Token expired`** (JWT `exp` 2026-07-13 18:29:59 UTC). Same expired-token state as the vendor-lane probes ([[Purchase-Orders]], [[RTV]], [[Release-Orders-Amendment-Requests]], [[Vendor-Reports-Queue]]). Nothing upgraded to PROVEN; a fresh JWT is needed to capture response shapes for the onboarding/lead/marketer grids + KYC/contract detail bodies.
- **No `captures/platform/*.json` response body** exists for any VMS endpoint yet — exact filter keys, status enums, column arrays and the lead/onboarding record schemas want a live (read-only) capture once a valid token is available.
- **Naming collision noted:** the 10 `brand-analytics-web/api/v1/kyc/*` rows are "Know Your Consumer" analytics (funnel / recall / ARPU / penetration), not identity onboarding KYC; they are surfaced here because they share the `kyc` token, and belong to the ads [[Brand-Analytics]] lane.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no save/approve/reject/invite/upload/sync writes):
- `zepto vms leads [--status …]` → `vms/api/v1/admin/lead/filter`; `zepto vms leads summary` → `.../lead/summary`; `zepto vms lead <userId>` → `.../user/lead` + `.../lead/get-user-details`.
- `zepto vms onboarding summary` → `.../basic-details/onboarding-summary`; `zepto vms onboarding list` → `.../onboarding-filter`.
- `zepto vms kyc <userId>` → `.../admin/kyc/fetch`; `zepto vms gstin <gstin>` → `vms/api/v1/kyc/gstin-details`; `zepto vms bank <userId>` → `.../bank-details/fetch`.
- `zepto vms contract <userId>` → `.../basic-details/contract-details` + `.../fetch-contracts`; `zepto vms warehouse <userId>` → `.../warehouse-details/fetch`.
- `zepto vms marketers [--search …]` → `.../marketer/filter` + `.../marketer/search`; `zepto vms marketer <id>` → `.../marketer/{id}`; `zepto vms distributors` → `.../distributor/filter`.
- `zepto vms non-trade summary|list|profile|review <userId>` → the `non-trade-vendor/*` read mirror.
- `zepto vms config|mappings|categories|status-config` → the config/enum reads.
- `zepto vms files [--filter …]` / `zepto vms file <id>` / `zepto vms template` → the `files/*` reads (templates + presigned attachment downloads are `READ (file)`).

Explicitly **excluded** from the read-only surface: lead invite/approve/reject/hold, KYC/contract/warehouse saves, PAN verification, marketer create/update/link, onboarding approve/reject/hold/modification-request, send-reminder-mail, attachment/file uploads, counterpart create, vendor update / extend-organization, and the vendor-sync ops — all state-changing / side-effecting.

## Connections

- Portal shell & index: [[00-Zepto-Atlas]] · [[00-Zepto-Atlas]] · master endpoint index [[Zepto-Endpoints]]
- Auth model & token: [[Auth-and-Access]] · scope rules: [[Read-Only-Guardrails]]
- **Tightest siblings** (same platform lane): [[Users-Access]] (user/role management the onboarding pipeline feeds), [[Subscription-Billing]] (plan a vendor onboards onto), [[Auth-Identity]] (the identity/access-management backend), [[Platform-Common]] (shared `commons/user/mh-list` filter + config layer).
- The onboarded vendor record is the same entity the vendor lane operates on: [[Purchase-Orders]] · [[Invoicing]] · [[Vendor-Contracts-Margins]] · [[Receivables]] (non-trade vendor).
- The mis-filed `brand-analytics-web/api/v1/kyc/*` consumer-analytics reads properly belong to [[Brand-Analytics]] (ads lane).
