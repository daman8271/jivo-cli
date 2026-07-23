---
title: Consumer Offers
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: studied
---

# Consumer Offers

The **Consumer Offers** menu item (internally called **"Brand Fund"**, route `/app/brand-fund`) is where a manufacturer like JIVO funds consumer-facing price offers on Blinkit and tracks the spend that funding generates. A "brand fund" offer is a per-product, per-city price contribution (an absolute ₹ value or a % / multiplier off MRP) that the brand pays for; Blinkit passes the discount to the shopper and bills the brand for the funded amount. The section has two faces: a **Spends Summary** (how much you are spending on offers this month, on how many unique products) and an **Offer Upload / Upload History** area where offer sheets are created (write) and their processing status + row-level detail are reviewed (read). Naming is inconsistent across the code: the sidebar/analytics label is "Consumer Offers", the page-title enum and API namespace say "Brand Fund"/`brands-fund`, and the URL slug is `brand-fund`.

Note: the captured screenshot `captures/partner/sec-07-consumer-offers.png` is only the PartnersBiz login page (session was logged out at capture time), so there is no rendered UI evidence for this section — everything below is reconstructed from the JS bundles and the existing verified CLI findings.

## Subpages & tabs

Routes (from `captures/partner/routes.js`):
- `/app/brand-fund` → default, redirects into the **daily-summary** view.
- `brand-fund/daily-summary` — the **Spends Summary** landing (summary cards + table). The page header also switches between three states: **"Spends Summary"** (`daily-summary`), **" Month End Claimable"** (`month-end-claimable`, a spend/claim view — no distinct endpoint found, treat data source as "to confirm"), and **"Offer Upload History"** (`sheet-history`).
- `brand-fund/sheet-history/:offerType` — Offer Upload History list, where `:offerType` is `single` or `bundle`.
- `brand-fund/sheet-history/single/details/:sheetId` — detail rows for one **Single** offer sheet.
- `brand-fund/sheet-history/bundle/details/:sheetId` — detail rows for one **Bundle & Combo** offer sheet.
- Nav helpers also build `/app/brand-fund/{sheetId}` and `/app/brand-fund/{sheetId}/single`.

Offer-type toggle across the history/detail tables: **"Single Offer"** (`single`) vs **"Bundles & Combos"** (`bundle`). There is also a **"Create Offer"** / **"Offer Upload"** action that opens the upload form (write — see out-of-scope note) with a downloadable sample file and an `offerType` selector.

## Filters & columns (what the table shows)

**Spends Summary — top cards** (`getDailySummaryCounts`):
- **Total Spend** — tooltip "Total spend on all of your products for current month till date".
- **Unique Products** — tooltip "Count of all unique products you are running offers on".
Analytics fires `SPENDS_SUMMARY_VISIBLE`, `..._FILTERS_APPLIED`, `..._BULK_DATA_REQUESTED`, plus `OFFER_TOTAL_SPEND_HOVERED` / `OFFER_UNIQUE_PRODUCTS_HOVERED` on the card tooltips.

**Spends Summary — filters:** date range (`date__gte` / `date__lte`), a `date_type` selector ("Date Type : …"), and it is scoped by `manufacturer_id__in`. The bulk export is delivered to an email (`to_user_email`), not shown inline.

**Offer Upload History table** (`brands-sheets/` list) columns seen: **Manufacturer** (`manufacturer_name`), **Created by** (`creator_email`), **Created at** (`install_ts`, date-formatted), **Status** (`state`, rendered as a colored Tag). History filters: date range on `install_ts__gte` / `install_ts__lte`, `state__in` (status), `upload_source=BRAND`, plus `offset` / `limit` paging and `manufacturer_id__in`.

**Offer detail rows table** (`SingleHistoryTable` / bundle equivalent) columns seen: **Item Id** (`itemId`), **Product Name** (`productName`), **Offer Type** (`offerType`), **Funding Type** (`fundingType`), **Start Date** (`startDate`), **End Date** (`endDate`), **City** (`city`) / **City Value** (`cityValue`), **Brand Fund Value** (`brandFundValue`), **Status** (`status`), **Brand Comments** (`brandComments`), plus dynamically-generated **Multiplier N** columns (`multiplier1`, `multiplier2`, … — one per pricing tier/city on the sheet).

**Status/`state` values** (`ReportState` enum): `success`, `processing`, `rejected`, `failed`.

## API endpoints

Base host is `${hostUrl.VendorConsoleEndpoint}` — the PartnersBiz Vendor-Console data host (same host family as `www.partnersbiz.com` that serves `/v1/report-requests/`). All endpoint literals below come from the code-split bundle `captures/partner/js/useFirebasePageTracking-CGSyAZ_Q.js`; methods are taken from the calling functions (`doHttpGet` = read, `doHttpPostMultipart` = write).

| METHOD | path | purpose | read/write |
|---|---|---|---|
| GET | `api/attributes/v1/brands-fund-summary/view/?manufacturer_id__in={id}` | Spends Summary cards — Total Spend + Unique Products (`getDailySummaryCounts`) | read |
| GET | `api/attributes/v1/brands-fund-summary-count/view/?manufacturer_id__in={id}&to_user_email={email}&date__gte=&date__lte=` | Bulk Spends Summary export — async, delivered as a CSV to email (`downloadDailySummary`, the `SPENDS_SUMMARY_BULK_DATA_REQUESTED` action) | read (triggers email export) |
| GET | `api/attributes/v1/brands-fund/cities/?active=true&is_frontend=true` | City list for filters (`brandFundCities`) | read |
| GET | `api/attributes/v1/brands-sheets/?offset=&limit=&manufacturer_id__in=&upload_source=BRAND&install_ts__gte=&install_ts__lte=&state__in=` | Offer Upload History list (Single) | read |
| GET | `api/attributes/v1/brands-fund/get/?sheet_id=&row_number=&limit=` | Single offer sheet — row-wise detail data (`getSingleSheetDataRowWise`) | read |
| GET | `api/attributes/v1/brands-fund/get-sheet-rows/?sheet_id=` | Single offer sheet — row list (`getSingleSheetRowData`) | read |
| GET | `api/attributes/v1/brands-sheets/download-sample-file/?manufacturer_id__in=&id__in=` | Download single-offer sample/template file | read |
| GET | `api/bundlesandcombos/v1/bundles_and_combos_approval/brand-fund/?sheet_id=&row_number=&limit=` | Bundle & Combo offer sheet — row-wise detail (`getBundleSheetDataRowWise`) | read |
| GET | `api/bundlesandcombos/v1/bundles_and_combos_approval/get-sheet-rows/?sheet_id=&limit=&offset=` | Bundle & Combo offer sheet — row list (`getBundleSheetRowData`) | read |
| GET | `api/bundlesandcombos/v1/bundles_and_combos_bf/download-sample-file/?bundle_type=` | Download bundle/combo sample/template file | read |
| GET | `api/v1/bulk-upload-jobs/` | Bulk-upload job status list (`getBulkUploadRequests`) | read |
| GET | `api/bundlesandcombos/v1/bundles_and_combos_bf/?…` (Bundle Upload History list) | Bundle upload-history list — endpoint reused for GET; exact query params: to confirm via live network capture | read |
| — | `month-end-claimable` view data source | endpoint not found in bundle: to confirm via live network capture | read |

**Out of scope (writes — never call from a read-only CLI):**
- POST (multipart) `api/attributes/v1/brands-sheets/` — upload/create a **Single** offer sheet (`singleFileUpload`). OUT-OF-SCOPE.
- POST (multipart) `api/bundlesandcombos/v1/bundles_and_combos_bf/` — upload/create a **Bundle & Combo** offer sheet (`bundleComboFileUpload`). OUT-OF-SCOPE.
- The related uploader path `jivo-ecom-upload upload flow --dataset brand_fund` (in the JIVO stack) is likewise a write and OUT-OF-SCOPE here.

## Real data seen (evidence)

The Spends Summary bulk export is already **live-verified end to end** through the email channel (not the inline API):
- `blinkit-cli brandfund pull` (Flow 7) fetches the export from `tanuj@jivo.in` over IMAP. Sender `no-reply@partnersbiz.com`, subject **"PartnersBiz Portal | Spends summary file"**, attachment **"PartnersBiz Portal _ Spends summary file.csv"**.
- Verified pull: email #281511 → **1,920-row CSV**.
- CSV schema (the row-level brand-fund spend data): `date, city, product_id, item_id, multiplier, offer_type, item_mrp, brandfund_absolute_value, brandfund_absolute_input_value, brandfund_percentage_value, product_name, l0/l1/l2_category_name, brand_name, p_type, qty_sold, total_brand_fund, system_sheet_id, mrp_gmv, upload_source, user_email`.
- This CSV is the emailed materialization of the `downloadDailySummary` (`brands-fund-summary-count/view/`) request; freshness T-1, range = 1st-of-month → T-1 (IST).

No inline JSON captures of the brand-fund endpoints exist yet in `captures/partner/api/` (only `profile-user.json` and `appointment-stats.json` were captured). Endpoint paths/params above are proven from the bundle source, not from a captured response body.

## What a READ-ONLY CLI would expose (candidate commands)

- `offers summary` — GET `brands-fund-summary/view/` → Total Spend + Unique Products for the current month (per `manufacturer_id`).
- `offers export --email <addr> [--from --to]` — GET `brands-fund-summary-count/view/` to request the bulk Spends Summary CSV (arrives by email); or skip the API entirely and reuse the proven `blinkit-cli brandfund pull` IMAP path to grab the delivered CSV.
- `offers history [--type single|bundle] [--state ...] [--from --to]` — GET `brands-sheets/` (single) / `bundles_and_combos_bf/` (bundle) → Offer Upload History (sheet id, manufacturer, created by, created at, status).
- `offers sheet <sheetId> [--type single|bundle]` — GET `brands-fund/get/` + `brands-fund/get-sheet-rows/` (or the `bundles_and_combos_approval/*` pair) → row-level offer detail (item, product, offer/funding type, dates, city value, brand fund value, multipliers, status).
- `offers cities` — GET `brands-fund/cities/` → city reference list for filters.
- `offers jobs` — GET `bulk-upload-jobs/` → status of recent upload jobs.
- Sample-file download endpoints are read-only helpers for the (out-of-scope) upload flow; a read CLI can expose them as `offers sample --type single|bundle` if useful, but **create/upload is out of scope**.

## Connections

- Portal home: [[Partner-Hub]] · [[00-Blinkit-Atlas]]
- Spend here funds price offers that show up as uplift in [[Sales]]; the `manufacturer_id` / entity scoping matches the rest of the portal.
- Offer sheets reference products/items shared with [[Assortment]].
- The bulk export uses the same async-export pattern as [[Report-Requests]] (request → success → download), but for Brand Fund it is delivered by **email**, not the on-portal report queue.
- Ads-side (paid placements, separate from brand-fund price offers) lives on Blinkit Brand Central, not in this section.
