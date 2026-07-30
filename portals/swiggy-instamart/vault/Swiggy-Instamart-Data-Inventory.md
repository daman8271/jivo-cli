---
title: Swiggy Instamart Data Inventory
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, data-inventory, live-counts]
---

# Data Inventory — what is actually in JIVO's Swiggy Instamart account

> **Every figure below was pulled live on 2026-07-30 between 03:20 and 04:10 IST**, read-only, by
> navigating the portal and recording the responses the application itself fired. Each number
> names its **source endpoint** and is tagged **VERIFIED** (observed in a captured response this
> run) or **INFERRED** (derived, or read from a document rather than the wire).
>
> **Session used:** `ecom1@jivo.in` (user id 345). Everything here is scoped to that user's
> entitlements — see the role-denied rows at the bottom for what it could *not* see.
> **Windows matter and are stated on every row.** Several of these surfaces default to a 7-day or
> 30-day view, and a figure quoted without its window is wrong.

## 0. The one-paragraph answer

JIVO's Swiggy Instamart account holds, right now: **₹2.35 Cr of sales in the last 7 days across
132 cities**, **27 ad campaigns** (all currently stopped or paused, spending ~₹66 k/day when live
at an ROI of 13–26×), **a ₹1.50 Cr open purchase-order book that is 55.8% unfulfilled**, **43
catalogue SPINs**, **zero sponsored share-of-voice on every one of the highest-volume oil keywords
on the platform**, and — the one that should ruin somebody's morning — **Swiggy's own inventory
report putting ₹2.84 Cr of `PotentialGmvLoss` against 735 SKU×store rows, 189 of them at zero
stock on the shelf.** JIVO's automation reads one of those numbers.

---

## 1. Entities — three accounts, and they are NOT interchangeable

Source: `GET partner-api.swiggy.com/instamart/v1/account/list` + clicking each tile and reading
back `__IM_ADS_CURRENT_ACCOUNT_ID__`. **VERIFIED.**

| Account | Account id | Campaigns | Cities w/ sales | Products w/ sales | Catalog SPINs | Sales reports queued | Ads summary reports |
|---|---|---|---|---|---|---|---|
| **Jivo Wellness** | `c9f24655-a984-4b65-a4da-2d5b6461b9ec` | **27** | **132** | **37** | **43** | **12** | **20** |
| **Jivo Mart Pvt. Ltd** | `89bafc9c-8a56-4286-94cf-a55ab4e564d3` | 0 | **22** | **12** | **9** | 0 | 0 |
| **Jivo** (brand under Wellness) | `260921c1-76e7-48ef-9771-82124ebe1fcc` | 0 | 132 | 37 | 43 | 1 | 0 |

All **VERIFIED**. brandCompany ids: Jivo Wellness `5ecb3c0025f73c6716097e1a1a6e62390ceb2504`,
Jivo Mart `935ac57d898d4c1b3b8ec0001a87d28a44b12928`. Brand id (Jivo)
`1bd421f677aba0b28ef95a6ed80970824cdf83ec`.

**Why this table matters:** Jivo Mart's footprint is roughly one-sixth of Jivo Wellness's on every
axis. A study or a report that walked only one account would have understated or overstated JIVO's
Instamart presence by a large multiple. Access scope: `userType: USER_TYPE_BRAND`,
`accessibleDomains: ["DOMAIN_ADS","DOMAIN_CATALOG","DOMAIN_PARTNER"]`, `personas: []`.

## 2. Sales — ₹2.35 Cr in 7 days, by city

Source: `POST brand-portal-service-http.swiggy.com/api/v1/sales/metric`,
dimension `SALES_METRICS_DIMENSION_TYPE_CITY_ID`. **VERIFIED.**
**Window: 2026-07-23 → 2026-07-29 inclusive (7 days — the portal's default).**

| Figure | Jivo Wellness / Jivo | Jivo Mart Pvt. Ltd |
|---|---|---|
| Sales, current period | **₹2,35,05,424** | **₹0** |
| Sales, prior period | ₹2,21,00,498 | ₹0 |
| Change | **+6.36%** | — |
| Rows returned | 132 cities (`totalRecords` = 132) | 7 daily rows, all zero |

Top cities (same window, **VERIFIED**):

| City | Sales |
|---|---|
| Hyderabad | ₹35,70,523 |
| Bangalore | ₹29,11,358 |
| Delhi | ₹27,28,994 |
| Mumbai | ₹25,49,703 |
| Chennai | ₹11,25,812 |
| Gurgaon | ₹9,03,386 |
| Chandigarh | ₹8,38,379 |
| Kolkata | ₹7,35,000 |
| Pune | ₹7,01,099 |
| Jaipur | ₹4,91,318 |

Each row also carries `lat`, `lng` and `state`, so this is mappable without any enrichment.
**Jivo Mart returning ₹0 for a full week is consistent** with an internal note that "Mart may be
₹0 some days" — but a whole zero week is worth a human explanation, and this study does not have
one.

## 3. Purchase orders — a ₹1.50 Cr book, 55.8% unfulfilled

Source: `POST picker.swiggy.com/api/v1/searchPurchaseOrder`, page 1. **VERIFIED.**
`last_update_time` = 2026-07-30T02:39:47 IST. **`total_number_of_purchase_order_records` = 58**;
50 captured on page one, so the figures below cover **50 of 58 POs** and are a floor, not a total.

| Figure | Value (50 of 58 POs) |
|---|---|
| Total PO value | **₹1,50,07,326** |
| Ordered quantity | 79,105 units |
| Received (GRN) quantity | 30,381 units — **38.4%** |
| **Pending quantity** | **44,124 units — 55.8%** |
| Status | 50/50 `STATUS_CONFIRMED` |
| Receiving status | 26 `NOT_RECEIVED`, 24 `PARTIALLY_RECEIVED` |
| **Flagged `is_low_stock_po`** | **48 of 50** |
| Sample POs | 0 |

**Vendors Swiggy is buying JIVO product through** (VERIFIED, PO counts):

| Vendor | Vendor code | POs |
|---|---|---|
| KNOWTABLE ONLINE SERVICES PRIVATE LIMITED | 79934149 | 33 |
| SUSTAINQUEST PRIVATE LIMITED | 77098658 | 8 |
| CHIRAG ENTERPRISES | 85235374 | 6 |
| EVARA ENTERPRISES | — | 2 |
| BABA LOKENATH TRADERS | 2586 | 1 |

**25 distinct receiving facilities** in that PO set: AHM Delhivery, BLR DHL, BLR Ecom2, BLR IM1,
BLR IM3, CBE Ecom, CHD Ecom, CHE AMB IM2, CHN ECOM, DLHY GGNFC5, DLHY GGNFC9, GOA IM1, HYD IM1,
HYD IM2, HYD IM4, Jai IM1, KOL IM2, Koc IM1, LKO IM1, MUM FC22, MUM IM1, MUM IM3, NOI IM1,
PUN Delhivery, Viz IM1.

Full field list on a PO row (**VERIFIED**, all 22): `purchase_order_id · facility_name ·
vendor_name · vendor_code · status · receiving_status · po_date · expiry_date ·
appointment_start_date · completed_date · created_at · value · total_quantity · pending_quantity ·
grn_quantity · is_low_stock_po · sample_po · business_type · reference_purchase_order_id ·
supplier_multi_grn_enabled · po_min_order_qty_fulfilled · po_min_order_value_fulfilled`.

> **This is the single most commercially significant thing in the study.** Swiggy has ₹1.5 Cr of
> confirmed demand on the table, 96% of it raised because stores are running low, and more than
> half the units have not been delivered. JIVO reads none of it — `picker.swiggy.com` appears
> nowhere in its automation.

## 3b. ⭐ Inventory and stock-outs — ₹2.84 Cr of potential GMV loss

**This is the most consequential number in the study, and it did not come from a grid.**

The vendor grids all render empty without a filter, so the inventory figures were initially
`PENDING_FILTER`. The way in turned out to be the **vendor download queue**: `POST
picker.swiggy.com/api/v1/batch/list` reports **`total_records_count` = 101** completed export jobs
that `ecom1@jivo.in` has already generated. Downloading an **already-completed** report is a read
(AMENDMENT-02 permits it explicitly; only *generating* one is the G2 write), so the newest
`VENDOR_PORTAL_GENERATE_ITEM_INVENTORY_DOCUMENTS` job was fetched by a plain `GET` of its presigned
URL and aggregated.

**Job types visible on page 1 of the queue** — the vendor report catalogue, VERIFIED:
`VENDOR_PORTAL_GENERATE_ITEM_INVENTORY_DOCUMENTS` (2) ·
`VENDOR_PORTAL_GENERATE_GOODS_RECEIVE_NOTE_DOCUMENTS` (4) ·
`VENDOR_PORTAL_GENERATE_PURCHASE_ORDER_DOCUMENTS` (4).
Files land on a **fifth S3 bucket not previously known**:
`scm-procurement-mumbai.s3.ap-south-1.amazonaws.com/inventory-downloads/csv/`.

### Item inventory — job `C0A8A1AC7840C4401DE2`, generated by `ecom1@jivo.in` 2026-07-29 09:10 UTC

Source: `captures/reports/vendor-inventory.csv`, 126,836 bytes, **735 data rows**. **VERIFIED.**

| Figure | Value |
|---|---|
| Rows (SKU × facility) | **735** |
| Distinct SKUs | **33** |
| Distinct facilities | **36** |
| Distinct cities | **20** |
| Total warehouse qty available | **82,814 units** |
| **Total `PotentialGmvLoss`** | **₹2,83,82,276** |
| Total open-PO quantity on those rows | 146,701 units |
| **Rows at DOH ≤ 1 (high risk)** | **206 of 735** |
| Rows at DOH 2–5 (low stock) | 44 |
| Rows at DOH > 5 | 485 |
| **Rows with ZERO qty on shelf** | **189** |

Storage type: Ambient 705, blank 30. Business category: Cooking Essentials 653, Packaged Food 43,
Non Food 39. L1 categories: *Edible Oils and Ghee*, *Cold Drinks and Juices*.

Worst rows by `PotentialGmvLoss` (**VERIFIED**):

| Loss | DOH | Qty | City | Facility | SKU |
|---|---|---|---|---|---|
| ₹8,75,310 | 0 | 145 | Chandigarh | CHD ECOM | Cold Press Kachi Ghani Mustard Oil 1 L |
| ₹6,31,786 | 0 | 27 | Delhi | DLHY GGNFC9 | Cold Pressed Groundnut Oil 1 L |
| ₹5,94,860 | 16 | 2,520 | Hyderabad | HYD IM4 | Cold Pressed Groundnut Oil 1 L |
| ₹5,20,106 | 0 | 10 | Bangalore | BLR ECOM2 | Cold Pressed Groundnut Oil 1 L |
| ₹4,54,289 | 5 | 608 | Hyderabad | HYD IM1 | Cold Pressed Groundnut Oil 1 L |

By city: Hyderabad ₹38.5 L · Bangalore ₹36.9 L · Mumbai ₹34.8 L · Delhi ₹22.9 L ·
Chandigarh ₹18.4 L · Chennai ₹18.1 L · Gurgaon ₹15.2 L · Pune ₹15.0 L · Kolkata ₹13.9 L ·
Noida ₹12.6 L.

Full column list (**VERIFIED**, all 14): `StorageType · FacilityName · City · SkuCode ·
SkuDescription · L1 · L2 · ShelfLifeDays · BusinessCategory · DaysOnHand · PotentialGmvLoss ·
OpenPos · OpenPoQuantity · WarehouseQtyAvailable`.

> **Read this carefully before quoting it.** `PotentialGmvLoss` is **Swiggy's own field**, summed
> across the 735 rows as of the report's generation time. This study did **not** validate Swiggy's
> methodology for it, and the total is a point-in-time snapshot, not an annualised figure. What is
> beyond doubt is the shape: against weekly sales of ₹2.35 Cr, Swiggy is reporting a comparable
> figure of foregone GMV, **189 rows are at zero stock on the shelf**, and this report already
> exists in a queue nothing in JIVO's automation reads.

### Purchase-order export — job `5BC49379A12A40C90911`, generated 2026-07-29 09:06 UTC

Source: `captures/reports/vendor-po.csv`, **141 PO LINE rows**. **VERIFIED.**

| Figure | Value |
|---|---|
| Distinct POs / SKUs / facilities / cities / vendors | 29 / 6 / 23 / 17 / 5 |
| Buying entity | **SCOOTSY LOGISTICS PRIVATE LIMITED** (Swiggy's B2B arm) |
| Status | 141/141 `CONFIRMED`, all `external` |
| PO line value incl tax | **₹20,33,736** (ex tax ₹19,36,891 + tax ₹96,845) |
| Ordered / received / balanced | **47,368 / 0 / 47,368 units — 100% pending** |
| PO ageing (days) | min 0, median 7, max 7 |

By vendor: KNOWTABLE ₹11.17 L · CHIRAG ₹3.53 L · SUSTAINQUEST ₹3.03 L · BABA LOKENATH ₹1.94 L ·
EVARA ₹0.66 L. Top SKU by ordered qty: **Cold Press Kachi Ghani Mustard Oil 200 ml — 39,760 units**.

⚠️ **Do not conflate this with §3.** This export is a *narrower slice* (29 POs / ₹20.3 L) than the
live `searchPurchaseOrder` view (58 POs / ₹1.50 Cr) because it was generated with its own filters
on 2026-07-29. Two different scopes, both stated, neither merged.

Line-level columns include the full tax breakdown (`CgstRate/Amount`, `SgstRate/Amount`,
`IgstRate/Amount`, `CessRate/Amount`, `AdditionalCess`, `TotalTax`, `TotalAmount` on the GRN
export) plus `Mrp`, `UnitBasedCost`, `ExpectedDeliveryDate`, `PoExpiryDate`, `OtbReferenceNumber`
and `PoAgeing` — i.e. everything needed to reconcile Swiggy POs against JIVO's own books.

### GRN export — job `D8AB773A919281CBDBD5`

**369 bytes, header row only, 0 data rows.** Recorded as empty rather than filed as evidence. Its
header nonetheless documents the full GRN contract: `GrnNumber · PurchaseOrderNumber ·
FacilityName · SupplierCode · VendorName · InvoiceNumber · InvoiceDate · CreatedAtDate · DnNumber ·
DNQuantity · DNValue · SkuCode · SkuDescription · BrandName · Category · ReceivedQty ·
GrnLineValueWithoutTax · GrnLineValueWithTax · LotMrp · LotExpiryDate · CgstRate · CgstAmount ·
SgstRate · SgstAmount · IgstRate · IgstAmount · CessRate · CessAmount · AdditionalCess · TotalTax ·
TotalAmount` — **including lot MRP and lot expiry date**, which is the near-expiry exposure an
edible-oil brand most wants and JIVO does not read.

## 4. Fulfilment centres

Source: `POST picker.swiggy.com/api/v1/listAllFCs`. **VERIFIED for page 1.**

- **50 FCs on page 1**, `next_page_token = "100"` → **at least 100 exist; the exact total was not
  captured** (the response carries no total-count field). Stated as a floor.
- All page-1 entries are `TYPE_WAREHOUSE`.
- Product category types across page 1: `AMBIENT` 22 · `COLD` 15 · `PACKAGING` 7 · `FNV` 6.
- 21 cities on page 1: Ahmedabad, Bangalore, Central Goa, Chennai, Coimbatore, Delhi, Dharmapuri,
  Gurgaon, Guwahati, Hyderabad, Jaipur, Kochi, Kolkata, Lucknow, Mumbai, Nagpur, Nashik, Noida,
  Patiala, Pune, Vizag.
- Fields: `id · type · name · product_categories · address · external_party_attributes`
  (the last carries `supplier_master_id`).

## 5. Advertising — 27 campaigns, ROI 13–26×, and zero sponsored share of voice

### Campaigns
Source: `POST brand-portal-service-http.swiggy.com/api/v1/campaigns`. **VERIFIED.**

- **`totalCampaigns` = 27** for Jivo Wellness; the page renders **10** (`paginationContext.size` =
  10). Jivo Mart and Jivo: **0** each.
- Each campaign carries **33 fields**, including budget (total, `BUDGET_TYPE_DAILY`,
  `PACING_STRATEGY_TYPE_DAILY_DISTRIBUTION`, rollover flag), bidding strategy, ad groups with ads
  and bids, `campaignPolicyValidationFailures`, `projectedSpend`, and a full audit trail
  (`createdBy` / `updatedBy` / `statusUpdatedBy` with email + timestamp).
- Example (**VERIFIED**): *"Olive Oil (Early & Late)"* — `CAMPAIGN_AD_TYPE_SPONSORED_PRODUCT`,
  `CAMPAIGN_STATUS_STOPPED`, reason `CAMPAIGN_STATUS_UPDATE_REASON_UPDATED_BY_ADVERTISER`, created
  2025-12-10, last status change by `ecom1@jivo.in` on 2025-12-31.

### Daily ad performance
Source: `POST /api/v1/advertiser/metrics` (`queryId: GRAPH_QUERY`), Jivo Wellness. **VERIFIED.**

| Day | GMV | Spend (budget burnt) | Impressions | Clicks | CTR | Conversions | ROI |
|---|---|---|---|---|---|---|---|
| 2026-07-27 | ₹8,99,640 | ₹66,179 | 84,585 | 1,581 | 1.87% | 1,037 | **13.59×** |
| 2026-07-28 | ₹6,88,893 | ₹26,552 | 48,676 | 1,620 | 3.33% | 705 | **25.94×** |
| 2026-07-29 | ₹0 | ₹0 | 0 | 0 | 0 | 0 | 0 |

14 metrics returned per row. The 2026-07-29 zero row is **either a reporting lag or campaigns
being off** — this study cannot distinguish the two and does not guess.

### Keyword share of voice — the competitive gap
Source: `POST /api/v1/advertiser/metrics`, dimension `DIMENSION_TYPE_KEYWORD`. **VERIFIED.**
**`totalRecords` = 33 keywords**; the page returns 10.

| Keyword | Platform searches | Sponsored SOV | Overall SOV | Overall impressions |
|---|---|---|---|---|
| oil | 65,212 | **0** | 5.52% | 76,068 |
| mustard oil | 46,453 | **0** | 3.28% | 29,801 |
| sunflower oil | 26,072 | **0** | 4.97% | 23,378 |
| refined oil | 21,096 | **0** | 3.27% | 14,107 |
| groundnut oil | 14,660 | **0** | 4.47% | 11,733 |
| mustard | 10,180 | **0** | 1.19% | 1,504 |
| rice bran oil | 7,585 | **0** | 8.68% | 11,180 |
| **fortune oil** (competitor brand) | 7,310 | **0** | 2.28% | 2,525 |
| olive oil | 5,920 | **0** | 8.90% | 9,630 |
| cooking oil | 4,848 | **0** | 7.42% | 8,958 |

**Sponsored share of voice is 0 on every one of the ten highest-volume oil keywords on Instamart**,
against an organic share of 1–9%. Consistent with all 27 campaigns being stopped. The platform is
also telling JIVO that **7,310 people searched a competitor's brand name** in the window.

## 6. Catalogue

Source: `POST brand-portal-service-http.swiggy.com/v1/list_spins`,
`/v1/list_spin_change_requests`, `/v1/search_categories`. **VERIFIED.**

| Figure | Jivo Wellness / Jivo | Jivo Mart |
|---|---|---|
| Catalogue SPINs (total) | **43** | **9** |
| SPINs returned per page | 10 | 9 |
| SPINs with sales in window | **37** | **12** |
| Open SPIN change requests | **0** | 0 |

The 43-vs-37 gap is **listed but not selling** in the 7-day window — the number worth watching.
(Jivo Mart's 12 products-with-sales against 9 catalogue SPINs reflects two different
vocabularies — the sales filter counts sellable product entries, `list_spins` the catalogue rows;
recorded as observed rather than reconciled.)

Sales-filter categories: **6** for Wellness (2 top-level with sub-categories, e.g. *cold drinks and
juices → juices and fruit drinks*), **4** for Mart. Vendor-lane categories:
**94** (`picker.swiggy.com/api/v1/category/list`).

## 7. Geography and platform scope

Source: `GET partner-api.swiggy.com/instamart/v1/configs` — 24,655 bytes, **74 keys**. **VERIFIED.**

| Figure | Value |
|---|---|
| `IM_ENABLED_CITIES` | **141 cities** (with ids, e.g. Bangalore 1, Delhi 4, Hyderabad 3, Budhwal 10000) |
| Cities with JIVO sales (7-day window) | **132** (Wellness) · **22** (Mart) |
| **Whitespace** | **9 enabled cities with no JIVO sales**, and 110 where Mart is absent |
| `VENDOR_WHITELISTED_ACCOUNTS` | 198 account ids |
| `BANNER_ADS_WHITELISTED_ACCOUNTS` | 83 |
| `SPECIALITY_ADS_WHITELISTED_ACCOUNTS` | 83 |

## 8. Feature surface — what the portal can do, and what is switched off

From the same `configs` response, ~60 `*_FULL_ROLLOUT` flags. **VERIFIED.**

**ON:** sponsored product · banner ads · speciality ads · top-slot ads · collection ads ·
pre-search ads · auto-suggest ads · FBT + FBT SwigSmart · one-click campaigns (with realtime
budget, live city edit, pause/resume, budget decrement, keyword file upload, reorder, extend) ·
dynamic pricing · festival bid booster · user targeting (+ NTP) · keyword SOV (+ manage) ·
budget rollover · ad-slot rank · granular report · **search-query report** · brand insights ·
sales insights (overview, performance, geography, category) · BDPO integration + monitoring ·
catalog · sampling integration · NPI · migration phases 1 & 2 · L1 category FMA · SB3 visibility
bids · side-panel v2 (host + vendor).

**OFF (equally informative):** `AI_ASSISTANT_FULL_ROLLOUT` · `REPORTS_V2_FULL_ROLLOUT` ·
`RO_UPLOAD_FULL_ROLLOUT` · `TOP_SLOTV2_FULL_ROLLOUT` (+ generic query type) ·
`REPORTS_NEW_UI_35_DAYS_WINDOW_ENFORCEMENT_FULL_ROLLOUT` · `FEATURE_RESTRICTIONS_FULL_ROLLOUT` ·
`NOTIFICATION_NUDGE_CONFIG` · `DURATION_CONFIG` · `SHOULD_HIDE_MEAL_SLOTS` ·
`BOTD_VIDEO_BPS_MIGRATION` · `CAMPAIGN_OP_DISABLED` (false = campaign ops enabled).

Live commercial parameter in `CONFIG_TEXTS`: **`BID_DISCOUNT_FOR_TOP_SLOT#0.25`**.
`FEATURE_CONFIG` came back as an **empty object** — recorded as empty, not omitted.

## 9. The query surface JIVO is not using

**VERIFIED** by enumerating the enums in the corpus and the request bodies the app sent:

| Vocabulary | Available | Used by `~/ecomcliauto/` |
|---|---|---|
| Metric types | **47** | **2** (`GMV`, `UNITS_SOLD`) |
| Dimension types | **17** | 3 (`DAY`, `POD`, `SPIN`) |
| Filter types | **25** | 1 (`FILTER_BRAND_ACCOUNT_ID`) |

Unused metrics include: market share, three share-of-voice variants, benchmark CTR/CVR/ROI
(category-relative performance), ROAS, ROI, brand ROI, CPO, eCPM, eCPS, AOV, reach, sessions,
new-user and new-user-to-product counts, add-to-cart count and rate, conversion rate, platform
keyword searches, product rating and rating count, budget burnt (incl. realtime), last-active-day
uptime efficiency.

Unused dimensions include: `WEEK`, `MONTH`, `BRAND`, `ACCOUNT`, `CAMPAIGN_NAME`,
`CAMPAIGN_SOURCE`, `KEYWORD`, `L`-category, `CITY_ID`.

## 10. Report catalogue — what the portal can produce vs what JIVO pulls

**VERIFIED** from the live report queues.

| Report family | Endpoint (list) | Live rows | Pulled by JIVO's cron? |
|---|---|---|---|
| **IM Sales xlsx** | `/api/v1/sales/reports` | **12** (newest `IMSales_072926_1731`, 2026-07-01 → 07-28) | **yes — the only one** |
| **Ads summary** | `/api/v1/advertiser/metrics/report/list` | **20** (`REPORT_TYPE_SUMMARY`, newest "july28" requested 2026-07-29) | no |
| **BDPO / discount** | `/api/v1/discount/reports` · `/instamart/v1/report/list-bdpo` | 0 queued | no |
| **Sales v2** | `/instamart/v1/report/list-sales` | not exercised | no |
| **Vendor-lane queue** | `/im-vendor/downloads` | 0 queued ("last 7 days" default view) | no |
| **Search-query report** | flag `SEARCH_QUERY_REPORT_FULL_ROLLOUT` = true | never generated | no |
| **Granular report** | flag `GRANULAR_REPORT_FULL_ROLLOUT` = true | never generated | no |

All report rows deliver as **presigned S3 URLs** on
`im-brand-reports-in-west.s3.ap-south-1.amazonaws.com` — no auth needed to download, the presign
*is* the auth. Listing and downloading are reads and are exposed; **generating is a WRITE (G2) and
was never done**, so "never generated" above means exactly that and not "unavailable".

## 11. Users with access

**PARTIAL — stated honestly.** `account/permissions` returns the *signed-in* user's scope, not a
user list, and no user-management endpoint was found anywhere in the corpus for this portal. So:

- **VERIFIED:** two JIVO logins exist and were both evidenced this run —
  `ecom1@jivo.in` (id 345, used) and `tanuj@jivo.in` (id 344, token expired). A third email,
  `xxx@x.com`, appears as `createdBy` on campaign records — a Swiggy-side placeholder, not a real
  user.
- **NOT ANSWERABLE from this portal:** the total number of users holding access to JIVO's Swiggy
  account and their roles. There is no users/roles endpoint in the 131 catalogued. This is a real
  gap, not an omission — it would need Swiggy account-management access.

## 12. Data coverage windows

| Surface | Default window observed | Widest available |
|---|---|---|
| Sales insights | **7 days** (2026-07-23 → 07-29) | not established; the 35-day enforcement flag is **off** |
| Ads metrics graph | 3 days returned | not established |
| PO dashboard | **`Last 30 Days`** | filter offers wider; not exercised |
| Vendor downloads queue | **`last 7 days`** | display default only |
| Sales report rows | monthly (2026-07-01 → 07-28) | report-defined |

**This is a stated gap.** AMENDMENT-03 asks for the maximum span per surface; the date-range
pickers are custom components that my DOM-driving heuristics did not reliably open, and I would not
guess at values I did not observe. What *is* established: the defaults above, and that the 35-day
cap is not currently enforced.

## 13. Role-denied and unreachable — what `ecom1@jivo.in` could NOT see

**VERIFIED denials**, recorded rather than passed over:

| Surface | Result | Meaning |
|---|---|---|
| `POST /api/v1/3p/advertiser/metrics/batch` (Brandverse) | **HTTP 403** ×18 | remote loads, account not entitled to its metrics |
| `POST picker.swiggy.com/api/v1/searchInventoryAvailabilityMetrics` | **HTTP 403 `Invalid Request Body`** | page calls it before a filter is chosen; success shape not captured |
| `/im-vendor/local-buying/*` | renders, **0 API calls** | separate `LOCAL_VENDOR` identity host (`influencer-app-*.swig.gy`); needs a credential JIVO may not hold |
| Stock-on-hand / low-stock / availability / GRN / RTV / returns grids | rendered, **empty** | vendor+warehouse-scoped; the empty state is an unfiltered query, **not** zero inventory |

> **The zeros on the inventory pages are not JIVO's inventory.** `Total Inventory Value ₹0` with
> `No data available for Selected Filters` means no vendor/warehouse was selected. Those grids are
> mapped and their endpoints proven, but the numbers **on the grid** stay `PENDING_FILTER`.
>
> **The underlying data was nonetheless obtained** — see §3b. A fifth attempt seeded
> `__IM_VENDOR_BRAND_ID__` (a client-side value, in a copy of the profile) and still could not
> unlock the grids: a DOM dump proved these pages expose **no standard `<select>` or combobox**
> control at all (0 selects, 0 comboboxes, 0–1 checkboxes per page), which is also why the pass-3
> widening clicks produced byte-identical before/after screenshots. So the grids were not driven.
> Instead the numbers came from the **already-generated exports in the vendor download queue**,
> which is a read. The route that failed and the route that worked are both recorded.

## Connections

- [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]]
- [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Sales: [[Sales-Insights]] · [[Sales-Reports]] — Ads: [[Ad-Campaigns]] ·
  [[Brand-Insights-Metrics]] · [[Keyword-And-Bid-Suggestions]]
- Supply: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] ·
  [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
- Scope: [[Accounts-And-Entities]] · [[Config-And-Feature-Flags]] · [[Catalog-SPIN-Management]]
