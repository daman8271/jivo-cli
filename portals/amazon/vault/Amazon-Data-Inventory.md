---
title: Amazon Data Inventory
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: data-inventory
tags: [amazon, data-inventory, read-only]
status: studied
read_only: true
---

# Amazon — Data Inventory (what the portals actually hold for JIVO)

> This is the answer to Daman's question — *"how many campaigns, what are we doing, all the data
> that is in this portal"* — pulled **live** from JIVO Mart's Seller Central session on
> **2026-07-30**. Every number is tagged `VERIFIED` (pulled this run, with its source endpoint)
> or `PENDING_AUTH` (queryable, but the value sits behind a surface not reached this run —
> see [[Read-Only-Guardrails]]) or `NOT_REACHABLE` (Vendor Central, session expired). No number here
> is guessed. Where a figure is derived, it says so.

## 0. The entity model — read this first (AMENDMENT-03 #2)

JIVO is **two Amazon selling entities across two portals**, i.e. *four* datasets, not one. Reporting
one entity's numbers as "JIVO on Amazon" understates the business.

| Entity | Portal | Login | Merchant / Vendor id | Marketplace | This run |
|---|---|---|---|---|---|
| **Jivo Mart** | Seller Central (3P) | `ecom1@jivo.in` | merchant `A2V85Y00QGIGP9` (`amzn1.merchant.d.ADSL7LHDS7PB7HHUSL46EW4NVI2Q`), global acct `amzn1.pa.d.ADXGX6ZRG5EN7JM6YI6TGAGTEXDA` | India `A21TJRUUN4KGV` | ✅ **VERIFIED — fully walked live** |
| **Jivo Wellness** | Seller Central (3P) | *separate login (unknown / not on disk)* | — | — | ⚠️ `NOT_REACHABLE` — no session; existence of a distinct SC Wellness account is **UNCONFIRMED** (this login exposes only one global account, "Jivo Mart") |
| **Jivo Wellness** | Vendor Central (1P) | `tanuj@jivo.in` | vendorGroup `7691702`, cid `A2I4CTXZEM9HDK` | India | `NOT_REACHABLE` — session expired 2026-07-16, G9 forbids re-login |
| **Jivo Mart** | Vendor Central (1P) | `ecom4@jivo.in` | vendorGroup `8592892`, cid `A2882479L2H86F` | India | `NOT_REACHABLE` — session expired, G9 |

- The Seller Central session's account-switcher (`GET /account-switcher/global-and-regional-account/merchantMarketplace`) returns **exactly one global account — "Jivo Mart"** — and one regional account, India. So under *this* login there is no second seller entity to switch to. `VERIFIED`.
- Marketplace ids also seen in responses: `A21TJRUUN4KGV` (India, active), `ATVPDKIKX0DER` (US), `A2NH4IXZ2D0U9U` (UAE) — these appear as *global-selling reachable* marketplaces, not as places JIVO has live inventory. `VERIFIED` (present in `meld/mons-api/GetMarketplaceSwitcher`).

> 🔴 **This study covers dataset #1 (Jivo Mart · Seller Central) ONLY. Datasets #2–#4 are
> `NOT_REACHABLE`.** Every number below §0 is a *Jivo-Mart-3P* number — do not read it as "JIVO on
> Amazon." Jivo Wellness is a distinct Amazon entity with its own data that this run never touched.

### Reachability evidence for #2–#4 (why they are NOT_REACHABLE, not skipped)

The multi-entity rule (AMENDMENT-03 #2) requires studying every entity JIVO has. I hunted for a
live session for the missing three across every reachable box before writing them off:

| Where I looked | How | Result |
|---|---|---|
| This Mac — Vendor Central jars | `~/.config/amazon-vc-cli/config.toml` (mart+wellness), replayed in a real browser cookie context | both **302 → `amazon.in/ap/signin`** (`assoc_handle=amzn_vc_sm_in`); expired 2026-07-16 |
| This Mac — Seller Central | account-switcher | one global account only ("Jivo Mart"); **no SC Wellness login on disk** |
| `ssh dev` (HO-IT-PC10) | **admin VSS-copied** every Chrome + Edge cookie DB, all users (khushwinder singh incl. the live `Default` modified **today**, Administrator, Navjot Kaur), byte-searched host_keys | **zero** `amazon`/`vendorcentral`/`sellercentral` cookies on any profile |
| `ssh win2` / `victus` | admin VSS-copied every Chrome profile, all users (leela, prabh, fleet); no Edge/Brave present | **zero** Amazon cookies |

So there is **no live Amazon session for Wellness or Vendor Central on any reachable machine**, and
**G9 forbids minting one** (a fresh VC login rotates cookies out from under JIVO's 10:30 IST cron
and the e-com team). `NOT_REACHABLE` is therefore the honest, correct status — not a skip. What each
holds is documented from the Phase-0 seed (§7) so the shape is known even though the counts are not
pullable this run.

## 1. Catalogue / ASINs / Listings (Jivo Mart, 3P) — VERIFIED

> **The headline inventory picture.** Recovered from the live Manage-Inventory GraphQL panel
> (`POST /myinventory/gql`, app-fired during the walk and passed through under AMENDMENT-04). All
> `VERIFIED` — read straight off the `filterCounts` response.

| Listing state | Count | | Listing state | Count |
|---|---|---|---|---|
| **All listings** | **464** | | Out of stock | **390** |
| **Active** | **5** | | Search-suppressed | 12 |
| **Inactive** | **422** | | Detail-page removed | 22 |
| Incomplete | 10 | | Offer missing | 4 |
| Paused | 5 | | Approval required | 1 |
| Other inactive issue | 3 | | Pricing issue | 1 |
| Submitted with issues | 1 | | Blocked / Closed / At-risk | 0 |

**Read this twice: JIVO Mart has 464 SKUs listed on Amazon 3P but only 5 are Active, and 390 are
Out of Stock.** 422 of 464 are inactive. This is the single most important number in the study —
the 3P storefront is 99% dark. Source: `POST /myinventory/gql` `filterCounts`. `VERIFIED`.

| Other catalogue figures | Value | Source | Tag |
|---|---|---|---|
| Listings with a CX-health score (Voice-of-Customer) | **110** | `GET /pcrHealth/pcrListingSummary` → `totalListingsCount` | VERIFIED |
| — of which CX rating = Excellent | **110** (0 very-poor / poor / fair / good) | `GET /pcrHealth/pcrKpi` | VERIFIED |
| Program enrolment | **B2B** (Amazon Business) | `POST /business-reports/api` `amazonPrograms` | VERIFIED |
| Live JIVO ASINs seen with titles on the home dashboard | 14 (list below) | `GET /home` shell | VERIFIED |

The 14 named ASINs (VERIFIED, from the live home shell) — JIVO's edible-oil range on Amazon India:

`B07MNWTBDT` Jivo Extra Light Olive Oil 5 L TIN · `B098XPFQ28` Jivo Extra Virgin Olive Oil 2 L ·
`B0C4FFYSLV` Jivo Everyday Pomace Olive Oil 2 L · `B0CGM7THVN` Jivo Extra Virgin Olive Oil 500 ML ·
`B0GZNGK11Q` Jivo Extra Virgin Olive Oil 250 ML (pack of 2) · `B0H683KW3S` Jivo Extra Light 5 L + EVOO 200 ML ·
`B0BGQ1B36W` Jivo Kachi Ghani Mustard Oil 5 L · `B0BGPVKKD4` Jivo Cold-Pressed Sunflower Oil ·
`B08ZNM3KJK` Jivo Canola 5 L + Olive 1 L · `B0GYKDYQQL` JIVO Canola Cold-Pressed ·
`B0CFFSWMXZ` Pomace Olive Oil 5 L · `B0CSNKLSGD`, `B0CVL9WSMQ` (parent ASINs) ·
`B0GQT98GTP` Jivo Premium Tea Leaves 250 g. (Full list + provenance: `captures/js/sc-home.html`.)

## 2. Coupons & Promotions (Jivo Mart, 3P) — fully VERIFIED

| Figure | Value | Source | Tag |
|---|---|---|---|
| Total coupon promotions (all-time, this account) | **18** | `GET /coupons/api/getCouponPromotions` → `promotionTotalCount` | VERIFIED |
| — EXPIRED | **16** | same (per-row `status`) | VERIFIED |
| — CANCELLED | **2** | same | VERIFIED |
| — currently ACTIVE | **0** | derived from the 18-row status breakdown | VERIFIED (derived) |
| Coupon rights on this account | view + edit (`sellercoupons_view`, `sellercoupons_edit`, `sellercoupons_global_view`); `canCreateAndEditCoupons=true`, `canCreatePersonalizedCoupons=false` | `GET /coupons/api/merchantInfo` | VERIFIED |
| Coupon subscription type | `NONE` | `GET /coupons/api/merchantInfo` | VERIFIED |

Example rows (VERIFIED, per-promotion fields incl. `discountType`, `budget`, `couponMetrics`, `asinCount`):
"Save 10% on Jivo A2 Ghee" (10% PERCENT, 1 ASIN, 2025-12-18→2025-12-31, EXPIRED); "Save 2% on Jivo
coupon packs" (2% PERCENT, 4 ASINs, appears monthly Sep–Oct 2025, EXPIRED). **Read: JIVO Mart is
running no live coupons right now and has never had one active at capture time.**

## 3. Orders (Jivo Mart, 3P)

| Figure | Value | Source | Tag |
|---|---|---|---|
| Unshipped EasyShip MFN orders (last 7 days) | **0** | `GET /orders-api/search?date-range=last-7&orderStatus=unshipped&program=easyship` → `total` | VERIFIED |
| Order-count tiles (all 0): pending-easyship, unshipped-easyship, unshipped-selfship, business-buyer-unshipped, premium-unshipped, ship-by-today, verge-of-cancellation, verge-of-late-shipment | **0 across every tile** | `POST /orders-api/countOrders` `keyToCountMap` (app-fired, AMENDMENT-04) | VERIFIED |
| Order search field set | `orders[]`, `total`, `offset`, `appliedSearchFilters`, `featureList`, `exceptions`, `requestId`, `debugInfo` (10 top-level) | `GET /orders-api/search` | VERIFIED |

**Read: JIVO Mart has no open orders of any kind right now** — consistent with 390/464 SKUs being
out of stock. The 3P order pipeline is effectively idle.

## 4. Account Health & Performance (Jivo Mart, 3P) — VERIFIED

| Figure | Value | Source | Tag |
|---|---|---|---|
| Order Defect Rate (MFN, 2026-05-16 → 2026-07-14) | **0 defects / 0 orders → status GOOD** (target < 1%) | `GET /performance/api/summary` | VERIFIED |
| Claims / chargebacks / negative-feedback counts (same window) | **0 / 0 / 0** | `GET /performance/api/summary` | VERIFIED |
| Overall account-health metric statuses | 17 metrics `GOOD` + 6 `NONE`, 1 `BAD` (in the raw `getriskbanner`/summary set) | `GET /performance/api/summary`, `GET /performance/api/getriskbanner/` | VERIFIED |
| Priority actions open | empty array `[]` (no open account-health actions) | `GET /ahd/priorityActions` | VERIFIED |

## 5. Seller Feedback (Jivo Mart, 3P) — fully VERIFIED

Buyer star-ratings, from `GET /fbmapi/v1/aggregates?duration=30D,90D,365D,LIFETIME`:

| Window | Rating | Positive | Negative | Neutral | Total reviews |
|---|---|---|---|---|---|
| 30 days | **3.7★** | 5 | 2 | 0 | 7 |
| 90 days | **3.0★** | 8 | 7 | 0 | 15 |
| 365 days | **3.1★** | 9 | 7 | 0 | 16 |
| **Lifetime** | **3.8★** | **52** | **20** | **1** | **73** |

All `VERIFIED`. Read: JIVO Mart has 73 lifetime seller-feedback reviews, trending *down* recently
(90-day 3.0 vs lifetime 3.8) — a real, actionable signal nobody at JIVO is looking at.

## 6. The report catalogue — the headline gap (AMENDMENT-03 #7)

**Seller Central's Report Central offers 35 downloadable report types. JIVO's `~/ecomcliauto`
automation pulls ZERO of them.** (It pulls only GST MTR B2B/B2C from a *different* subsystem,
`/mytax/gstreports`.) Source: `GET /reportcentral/api/v1/getReportConfigurations` → `reportsConfig` (35 rows). `VERIFIED`.

| Category | # report types | Examples (reportType) |
|---|---|---|
| INVENTORY | 20 | `FBA_MYI_ALL_INVENTORY`, `MANAGE_INVENTORY_HEALTH`, `STRANDED_INVENTORY_UI`, `LEDGER_REPORT`, `RestockRecommendations`, `AFNInventoryReport`, `ReserveBreakdown`, `STOCKSMART`, `FBA_HAZMAT_INVENTORY`, `SnSForecasting` |
| PAYMENT | 5 | `REIMBURSEMENTS`, `LONGTERM_STORAGE_FEE_CHARGES`, `STORAGE_FEE_CHARGES`, `ESTIMATED_FBA_FEES`, `ORDER_LEVEL_REIMBURSEMENT_REPORT` |
| SALES | 4 | `FlatFileAllOrdersReport`, `SHIPMENT_SALES`, `AFNShipmentReport`, `SnSPerformance` |
| REMOVALS | 4 | `REMOVAL_ORDER_DETAIL`, `REMOVAL_SHIPMENT_DETAIL`, `RECOMMENDED_REMOVAL`, `REGIONAL_REMOVAL_RECOMMENDATIONS` |
| CUSTOMER_CONCESSIONS | 2 | `CUSTOMER_RETURNS`, `REPLACEMENT` |

Full 35-row catalogue with `reportType` · `reportTitle` · `reportCategory` · `reportDescription`
is in `captures/probes/rc-configs.json` (`VERIFIED`, 103 KB live response). **Every one of these is a
dataset JIVO can pull and currently does not.** Generating one is a WRITE (enqueue, G2) — the study
enumerates them; it never fires them.

### GST reports (the ONE surface JIVO does pull) — VERIFIED it is live

`GET /fba/gstreports/report-history` shows JIVO's own automation working: a report `reportType 61200`
covering **2026/07/01 → 2026/07/28**, requested **2026/07/29 15:02**, completed **15:04** — exactly the
MTR B2B/B2C flow (21/22) in `~/ecomcliauto/amazon-mp/FLOWS.md`. `VERIFIED`.

## 7. Vendor Central (1P) data — NOT_REACHABLE this run, documented from seed

Both VC logins' sessions are expired (see [[Auth-and-Access]]); G9 forbids minting a new one. From the
Phase-0 seed evidence (proven by terminal replay 2026-07-07/08, `captures/seed-intel.md`), the 1P data
that *is* queryable once a session exists:

| Dataset | Endpoint | Cadence | JIVO pulls it? |
|---|---|---|---|
| ARA **Sales** (ordered/shipped revenue, units, COGS, returns; 9 metrics) | `request-report-download reportId=sales` | daily T-2 + MTD | ✅ yes (flow 1) |
| ARA **Inventory** (17 of **38** metrics: OOS%, confirmation rate, net received, open PO qty, fill rate, on-hand, aged-90) | `reportId=inventory` | daily | ✅ yes (flow 2) |
| **PO line items** (32 cols) | PO Management async chain | monthly window | ✅ yes (flow 3) |
| **Coupon metrics** (per campaign) | `hz/…/download-metrics` | per campaign | ✅ yes (flow 4) |
| ARA report types **not pulled** (forecast, chargebacks, shortage claims, the other 21 of 38 inventory metrics, ~11 other ARA reports) | ARA | — | ❌ **no — the 1P gap** |

Counts (open POs, PO value, chargeback totals, forecast vs actual) are `NOT_REACHABLE` this run and
marked so honestly. The exact command that would fill each is the `sapb1`-style ARA request in
`captures/seed-intel.md`.

## 8. Access / users

| Figure | Value | Source | Tag |
|---|---|---|---|
| Seller Central global accounts on this login | **1** ("Jivo Mart") | `GET /account-switcher/…/merchantMarketplace` | VERIFIED |
| Regional accounts | **1** (India) | same | VERIFIED |
| Users with access to the account + their roles | **NOT_REACHABLE this run** — the User Permissions page (`/gp/account-manager/home.html`) returned a 302 on the walk (entitlement-gated for this role); no user-list endpoint was exercised | `/gp/account-manager/home.html` | NOT_REACHABLE |

## 9. Sales & traffic history depth (AMENDMENT-03 #4) — VERIFIED

The Business Reports sales dashboard exposes **731 days of daily-granularity sales & traffic
history: 2024-07-28 → 2026-07-28** (`POST /business-reports/api` `getReportData`, app-fired). That
is the true available span — not the default 7-day view. `VERIFIED`.

| Figure | Value | Source | Tag |
|---|---|---|---|
| Sales history available | **731 days**, daily, 2024-07-28 → 2026-07-28 | `getReportData` `size/startDate/endDate` | VERIFIED |
| Sales today (order-product-sales / units / order-items) | **0 / 0 / 0** | `getSalesDashboardData` snapshot | VERIFIED |
| Columns available per day | ~40 incl. Ordered Product Sales (+B2B), Units Ordered (+B2B), Sessions, Page Views (mobile/browser), Buy-Box %, Conversion | `getReportData` columns | VERIFIED |
| Top listing last-30-days (from home) | `B0CH13ZG5M` Jivo EVOO 2L — **₹1,65,098 GMS, 135 units** (state ACTIVE) | `POST /homepage/casino/data` `ProductPerformanceData` | VERIFIED |
| Available report definitions | Sales and Traffic · Detail Page Sales and Traffic (by parent / by child item) · Seller Performance | `getSellerMetaData` `byDateReports` | VERIFIED |

## 10. Note on how these numbers were obtained (AMENDMENT-04)

Sections 1, 3 and 9 above were initially unfilled in the first draft because the panels load over HTTP
**POST** and the read-only transport gate was blocking them. Under **AMENDMENT-04** the gate now
lets **app-fired** non-GET requests pass (the study never authors or replays a request). Navigating
to each page let the app fetch its own data, which was captured and read off. Every one of those
non-GET requests is logged in `captures/nonget-allowed.tsv` (148 rows); **zero** were
state-changing (`captures/nonget-flagged.tsv` is empty) — see [[Read-Only-Guardrails]]. No panel
number here was authored, replayed, or guessed.

## 11. Filters, dimensions & date ranges enumerated (AMENDMENT-03 #4, #6)

Every filter/dimension option JIVO *can* query, from the captured manifests — documented even
where not individually run (that list is the map of what can be asked).

**Orders — quick-filter / status dimension values** (`orders-api/manifest-v3/quick-filters`,
`countOrders`): `fulfillmentType`, `orderStatus`, `orderType`, `shipByDate`, `shippingService`,
`shippingStatus`, `dbtsStatus`; tabs/segments: unshipped-easyship, unshipped-selfship,
business-buyer-unshipped, premium-unshipped, ship-by-today, verge-of-cancellation,
verge-of-late-shipment, late-shipped, payment-on-hold, verifying-tracking-details,
waiting-for-tracking-update, shipped-order-defects, unshipped-order-defects. `VERIFIED` (present).

**Report Central — the 35 report types by category:** INVENTORY (20), PAYMENT (5), SALES (4),
REMOVALS (4), CUSTOMER_CONCESSIONS (2). Each with its own date-window + format params (see §6).
`VERIFIED`.

**Business Reports — dimensions:** by-date reports (Sales & Traffic, Detail-Page Sales & Traffic,
Seller Performance) and by-ASIN reports (Detail-Page by parent / by child item); ~40 metric
columns incl. B2B splits (§9). `VERIFIED`.

**Feedback — duration dimension:** `30D`, `90D`, `365D`, `LIFETIME` (§5). `VERIFIED`.

### Date ranges (the real available span per surface) — VERIFIED

| Surface | Available span / granularity | Source | Tag |
|---|---|---|---|
| Business Reports sales & traffic | **731 days**, daily, 2024-07-28 → 2026-07-28 | `getReportData` | VERIFIED |
| Seller feedback | 30D / 90D / 365D / LIFETIME (73 reviews lifetime) | `fbmapi/v1/aggregates` | VERIFIED |
| Account health metrics | rolling 60-day window (2026-05-16 → 2026-07-14) | `performance/api/summary` | VERIFIED |
| GST On-Demand Reports | **45-day max window** per request (portal-imposed) | `~/ecomcliauto/amazon-mp/FLOWS.md` + `fba/gstreports/report-history` | VERIFIED |
| ARA (1P, Vendor Central) | ~5-day workflow retention; daily + custom range | Phase-0 seed | INFERRED (seed) |

## Connections
- [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Model]] · [[Amazon-Pages-and-Routes]]
- [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Sections with the live numbers: [[Coupons-Promotions]] · [[Feedback-Manager]] · [[Account-Health-Performance]] · [[Business-Reports-Analytics]] · [[Orders]] · [[Inventory-FBA]]
