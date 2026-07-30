---
title: Flipkart Data Inventory
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, data-inventory, read-only]
---

# Flipkart — Data Inventory (what the portal actually holds for JIVO)

> Every number is tagged **VERIFIED** (pulled live read-only this session, with its source
> endpoint) or **UNVERIFIED** (from a JIVO seed doc / July capture, not re-pulled today) or
> **PENDING_AUTH** / **NOT_REACHABLE** (queryable but not reached this session, with the exact
> blocker). No number here is guessed. No cell is ever left blank — an unreached one carries its
> tag and reason.

**How these were captured:** a **read-only live browser walk** (headless Chrome on `HO-IT-PC10`,
navigation-only, no clicks, write-verb/auth requests aborted before the socket — Amendment-02
method) of **both** portals with the production sessions (consumed, never minted — G9). Numbers are
read off the live UI + the app's own network responses; screenshots in `captures/{vendorhub,seller}-walk/`,
gallery [[Flipkart-Live-Walk]]. **37 distinct section pages** captured (13 Vendor Hub + 24 Seller
Hub). 0 login-redirects (sessions healthy); the gate aborted 2 app-fired write requests (verbs
"edit"/"delete") before they left the process. The Amendment-04 non-GET audit
(`captures/nonget-allowed.tsv` + `-flagged.tsv` + `-telemetry.tsv`): **122 app-fired non-GET reads,
0 mutations, 15 telemetry** — all GraphQL POSTs were `query` type (verified by operationName +
response shape); no click means no mutation.

---

## 1. Entities / accounts — the biggest data-loss risk (Amendment-03 §2)

JIVO holds **9 Flipkart vendor entities** across **two** Vendor-Hub logins, plus **one** Seller-Hub
seller account. Studying only "JIVO" would drop 8 of the 9 vendor datasets.

### Vendor Hub — `gurvinder@jivo.in` (6 vendors) — VERIFIED live
Source: `GET vendorhub.flipkart.com/vendor/user-management/vendor-list` (200, this session).

| Vendor id | Name | Currently selected |
|---|---|---|
| `VEN23097` | JIVO MART PRIVATE LIMITED | ✓ (session vendor) |
| `VEN19086` | CHIRAG ENTERPRISES | |
| `VEN20606` | FAIRDEAL MARKETING | |
| `VEN19640` | M/S SHIV SHAKTI ENTERPRISES | |
| `VEN21197` | KNOWTABLE ONLINE SERVICES PRIVATE LIMITED | |
| `VEN18904` | Jivo wellness private limited | |

### Vendor Hub — `infinite@jivo.in` (3 vendors) — UNVERIFIED (token on disk expired)
Source: decoded from the `infinite` JWT + JIVO seed docs. Not re-pulled (its jar expired ~9 h ago).

| Vendor id | Name |
|---|---|
| `VEN20104` | BABA LOKENATH TRADERS |
| `VEN54675` | SUSTAINQUEST PRIVATE LIMITED |
| (id PENDING_AUTH) | Evara Enterprises |

### Seller Hub — `ecom8@jivo.in` — VERIFIED identity, data UNVERIFIED-today
sellerId `e56b4e65e27e4162`, display "JIVOMART". (One 3P seller account.)

> **Per-vendor deep data (POs, stock, sales) for the other 8 entities is PENDING_AUTH.** The live
> reads below are scoped by the session's *selected* vendor (JIVO MART). Switching vendor is a
> `POST /select-vendor`, which this study will not author (G0 / Amendment-04). To pull the other
> 8 entities, re-run the read-only CLI once per vendor after the app itself selects each — the
> exact commands are in [[Vendor-Users-and-Access]].

---

## 2. Vendor Hub — JIVO MART (VEN23097) — VERIFIED live via the browser WALK this session

Numbers below are read off the **live Vendor Hub UI** during the read-only walk (screenshots in
`captures/vendorhub-walk/`) and its captured network responses. **These CORRECT an earlier error:**
a constructed `GET /vendor/purchase-orders` returned 0 rows (wrong params/scope), but the portal's
own PO dashboard shows JIVO MART is an **active, high-volume vendor node**, not empty.

| Metric | Value | Source | Tag |
|---|---|---|---|
| Purchase orders — **Open to fulfil** | **1 PO · 3.3K units · ₹6,49,540 (₹6.49 L)** | PO dashboard tile (`sec-05` walk) | **VERIFIED (walk)** |
| Purchase orders — New in last 2 days | **0** | same tile | VERIFIED (walk) |
| Purchase orders — Pending Acknowledgement | **0** | same tile | VERIFIED (walk) |
| Purchase orders — Expiring in 10 days | **0** | same tile | VERIFIED (walk) |
| Purchase orders — **Completed** | **~741–750** (grid: **75 pages × 10/pg**, true total via pagination) | Completed tab pager (`sec-05`) | **VERIFIED (walk)** |
| Purchase orders — **Cancelled** | **~561–570** (grid: **57 pages × 10/pg**) | Cancelled tab pager (`sec-06`) | **VERIFIED (walk)** |
| Sample completed POs | `FDGN07597805` (28 Jan 2026), `FDGN07589834`, `FBSWN07587432` … — Category **Gourmet**, FK wh "Delhi Grocery NCR Warehouse 1", vendor wh West Delhi VS58039, Fulfilment "Merchandising" | Completed grid rows | VERIFIED (walk) |
| Users with access | **3 active, 0 suspended** (all Operations Head): abhilash kutty `<abhilashkutty0@gmail.com>`, Gurvinder Jivo `<gurvinder@jivo.in>`, Kalpana Thakur `<kalpana@jivo.in>` | `GET /vendor/user-management/users/active` + `/users/suspended` | VERIFIED (GET) |
| Warehouses / vendor sites (this vendor) | **2** — `VS58039` West Delhi 110027, `VS96323011` Bengaluru Rural 562123 | `/roles-and-warehouses` + `/profile/my` | VERIFIED (GET) |
| Payments — Payment History FY 2026-27 | **₹0.00**, **0 invoices** approved for payment ("No invoices found") | Payments page (`sec-15` walk) | **VERIFIED (walk)** |
| Sale active right now? | **No** — last sale window 2025-09-22 → 2025-10-03 | `GET /vendor/config/sale-config` | VERIFIED (GET) |
| Performance (Fill Rate / Lead Time / QC Reject / RO Approval TAT) | shown **0** for May/Jun/Jul-2026 on the dashboard tiles | Home dashboard (`sec-01` walk) | VERIFIED (walk) |
| Inventory analytics — FK warehouse dimension | **319 FK warehouses** enumerable in the filter (del_/mum_/noi_/ghz_/jai_… networks); default filter "Fast Selling & Low DOH (<10 days)"; category **Gourmet** | Inventory analytics page (`sec-09` walk) | **VERIFIED (walk)** |

**Corrected reading:** JIVO MART (VEN23097) is a **live, active** 1P grocery vendor — ~750 completed
POs, ~570 cancelled, 1 currently open (₹6.49 L). It supplies **Gourmet** (olive-oil etc.) into
Flipkart's grocery warehouse network (Delhi Grocery NCR + 319 FK darkstores). Current invoices/
payments are ₹0 (the open PO is not yet fulfilled/invoiced). Interactive GUI logins are near-dormant
(last 2019/none) — the account is API-driven, consistent with JIVO's `~/ecomcliauto` automation.

> The constructed `GET /vendor/purchase-orders?status=…&from_date=2023-01-01` returning 0 is
> retained as a documented gotcha: that endpoint's result did not reflect the account's true PO
> history, whereas the app's own dashboard calls did. **This is exactly why Amendment-02 makes the
> live walk the method and constructed probing the fallback.**

---

## 3. Seller Hub — `ecom8@jivo.in` (JIVOMART) — VERIFIED live via the browser WALK this session

Read off the live Seller Hub UI during the read-only walk (screenshots in `captures/seller-walk/`,
gallery [[Flipkart-Live-Walk]]). Session live; sellerId `e56b4e65e27e4162` confirmed.

| Metric | Value | Source (walk page) | Tag |
|---|---|---|---|
| **Listings — Active** | **152** | Listings page tabs (`sec-02`) | **VERIFIED (walk)** |
| **Listings — Blocked** | **26** | same | **VERIFIED (walk)** |
| **Listings — Inactive** | **70** | same | **VERIFIED (walk)** |
| **Listings — Archived** | **182** | same (`sec-04`) | **VERIFIED (walk)** |
| Listings — In Progress | present (own page, `sec-05`) | Listings-in-progress | VERIFIED (walk) |
| **Report Centre — Requested reports** | **73** | Report Centre page (`sec-14`) | **VERIFIED (walk)** |
| **Report Centre — Scheduled reports** | **3** | same | **VERIFIED (walk)** |
| Report categories (5) | Fulfilment · Invoices · Listings · Payment · Tax (+ Type/Sub-Type selectors) | Report Centre + `GET reportCategories` | **VERIFIED (walk + GET)** |
| **Upcoming Payment** | **₹3,90,075** (est.); other estimate cards ₹19,82,191, ₹5,33,021, **₹-8,87,863** | Payments account-summary (`sec-12`) | **VERIFIED (walk)** |
| **Payouts status** | **BLOCKED** — "postpaid payment is blocked as you have **Ads dues**… clear to unblock payouts" | Payments page banner | **VERIFIED (walk)** |
| Home — Impressions | 25 Jul **1L**, 24 Jul **1.9L** | Home dashboard (`sec-01`) | VERIFIED (walk) |
| Home — Today's Units / Sales | **0 / ₹0** (yesterday 0 / ₹0) | same | VERIFIED (walk) |
| Home — Weekly loss flags | **25 units lost / ₹13L weekly sales loss**; GMV loss due to quality **₹5,518** | same | VERIFIED (walk) |
| Compliance flag | **4/4 GSTINs not enabled for e-invoicing** | Home banner | VERIFIED (walk) |
| Ad campaigns | **NOT_REACHABLE** — Ads page threw "unexpected error, please refresh" on the live walk | Ads page (`sec-16`) | NOT_REACHABLE (app error) |
| Ad campaigns (historical) | **260** rows | `POST fed-ads/downloadV2` (JIVO, Jul-08) | UNVERIFIED-today (POST) |
| Consolidated FSN report rows (historical) | **269** product rows | `POST fed-ads/download/table` (JIVO, Jul-08) | UNVERIFIED-today (POST) |
| earn_more listings report (historical) | **1,553 rows × 16 cols** | `GET downloadReport` (JIVO, Jul-08) | UNVERIFIED-today (needs a generated report id) |

**Seller Hub reading:** JIVOMART (3P) lists **~430 FSNs** (152 active + 26 blocked + 70 inactive +
182 archived) — so **active is only ~35% of the catalogue; 182 archived + 70 inactive + 26 blocked =
278 not selling.** Sales are currently flat (0 today) with a **₹13 L weekly sales-loss** flag, and —
a material finding — **payouts are BLOCKED pending Ads dues** (a ₹-8,87,863 estimate card). All four
GSTINs lack e-invoicing. Report Centre holds **73 requested + 3 scheduled** reports across 5
categories; JIVO's automation pulls one (earn_more) — the Tax/Invoice/Payment/Fulfilment families
are untouched.

**Report categories — full descriptions (VERIFIED live today):**
- `5` **Fulfilment Reports** — reconciling Orders, Returns, Inwarding and Recall.
- `10` **Invoices** — monthly summary of all marketplace charges for the account.
- `9` **Listings reports**.
- `4` **Payment Reports** — reconciling payments.
- `11` **Tax Reports** — "access all tax related information … used to file TDS and Sales tax."

> Each category is a family of report types generated via `getReportsV2` (a POST / EXPORT — never
> fired). JIVO pulls only the earn_more listings report → the **Tax / Invoice / Payment / Fulfilment
> families are untouched.** The POST-backed *counts* require the app to fire them during a live
> browser walk (Amendment-02), not run for Flipkart this session — stated gap, see
> [[Study-Verification]] and the coverage ledger (`../COVERAGE-LEDGER.md`).

---

## 4. Date ranges — how far back the data goes (Amendment-03 §4)

| Surface | Field | Finding | Tag |
|---|---|---|---|
| Vendor Hub PO list | `from_date`/`thru_date` | accepts an arbitrary range; queried 2023-01-01→today and got a valid (empty) result — so **no server-side floor rejection observed**; true earliest with data is PENDING_AUTH (0 POs on JIVO MART) | VERIFIED (range accepted) / PENDING_AUTH (earliest-with-data) |
| Vendor Hub sale-config | window | last configured sale 2025-09-22 → 2025-10-03 | VERIFIED |
| Seller Hub earn_more | `from_date`/`to_date` | JIVO's "Last 30 days" preset = `to`=T-2, `from`=T-31; longer windows accepted per JIVO's two-date replay test | UNVERIFIED-today |
| Seller Hub FSN | `dateRange` | server keys off `dateRange`, `queryId`/`requestId` are NOT cache keys (JIVO proved via two-date replay) | UNVERIFIED-today |

---

## 5. Report catalogue vs what JIVO actually pulls (Amendment-03 §7) — a headline finding

Flipkart can produce **many** report types; JIVO's `~/ecomcliauto` automation pulls **3**.

**What JIVO pulls daily (3):**
1. `earn_more_report` (Secondary/listings) — Seller Hub, `GET generateReport→checkReports→downloadReport`.
2. Flipkart Ads consolidated campaign CSV — `POST fed-ads/downloadV2`.
3. Consolidated FSN report — `POST fed-ads/download/table`.
Plus Vendor-Hub Sales + Inventory analytics reports (`POST vendor/analytics/sales-report` / `/report`).

**What the portal *offers* (from `reportCategories` + the report-centre bundle) — JIVO pulls none of these:**
- Category **5 Fulfilment Reports**, **10 Invoices**, **9 Listings reports**, **4 Payment Reports**,
  **11 Tax Reports** — each a family of report types behind `report-centre`.
- Every one is generated via `generateReport` / `getReportsV2` (an **EXPORT = WRITE per G2** — never fired).

> **The gap:** JIVO pulls ~3 report types; the portal exposes 5 report *categories* each containing
> multiple types (Tax/Invoice/Payment/Fulfilment reports JIVO never touches). Enumerating the full
> per-category report-type list requires firing `getReportsV2` (a POST) or a live walk — PENDING_AUTH.
> The category list itself is VERIFIED (above). This is exactly the "surface JIVO doesn't see".

---

## 6. Filter / dimension enumeration (Amendment-03 §6)

**Vendor Hub PO list** filters (from the proven query + bundle): `status` (new / …),
`from_date`, `thru_date`, `sort_column` (order_date, …), `order` (asc/desc), `page_number`,
`page_size`, plus warehouse selector (`VS58039`, `VS96323011`) and vendor selector (the 6 vendors).
**Vendor Hub analytics** filters: warehouse, category (from `browse-tree`), date range — the bare
`purchase-orders-summary` / `return-orders-summary` calls 400/500 without them (param shape NOT_REACHABLE).
**Seller Hub Ads** dimensions (from `downloadV2` body): `type` (PLA, SELLER_PCA), `marketplace`
(FLIPKART, SHOPSY), `budgetType` (DAILY_BUDGET, TOTAL_BUDGET), `timeGranularity` (DAY), 17 metric
fields (see [[Flipkart-Ads-and-FSN]]). **FSN** dimensions: `view_id=612`,
`reportId=sellerPlaConsolidatedFSNReport`, group-by campaign/adgroup/sku/listing.

---

## 7. Response field depth (Amendment-03 §10)

Full field lists of the endpoints exercised live are captured in `captures/probes/*.json`
(gitignored — real business data). Key shapes:
- **vendor-list:** `first_name, last_name, email_id, vendors[{id, name}]`
- **users/active:** `users[{first_name, last_name, email_id, phone_number, is_suspended,
  vendor_role_mapping[{roles{id,name}, vendor_nodes[{ref_id,name}]}], created_on, last_login}]`
- **profile/my:** `email_id, phone_number, vendor_name, first_name, last_name,
  vendor_sites[{ref_id, name}], roles[]`
- **roles-and-warehouses:** `roles{role_permission_mapping[{role{id,name}, permissions[{entity, actions[]}]}]}, warehouses[{ref_id, name}]`
- **config/sale-config:** `isSaleActive, startDate, endDate`

---

## Honest gaps (so nothing reads as complete when it isn't)

1. **8 of 9 vendor entities: PENDING_AUTH** — the live walk + reads were scoped to the session's
   selected vendor (JIVO MART, VEN23097). Reading the other 8 (CHIRAG, FAIRDEAL, SHIV SHAKTI,
   KNOWTABLE, Jivo Wellness; + infinite's BABA LOKENATH, SUSTAINQUEST, Evara) needs a
   `POST /select-vendor` (a write, not authored) or a walk driven after the app selects each. All 9
   are enumerated (§1); only JIVO MART's numbers are pulled.
2. **Seller Hub Ads campaign count: NOT_REACHABLE** — the Ads page threw an app error on the live
   walk. Historical (JIVO Jul) = 260 campaigns, tagged UNVERIFIED-today. Re-walk when Ads loads.
3. **PO/return summary GET params: NOT_REACHABLE** via constructed GET (400/500 bare) — but the true
   PO tallies were obtained anyway from the walk's dashboard tiles (§2), so this is closed for POs.
4. **Full per-category report-type list: PENDING_AUTH** — the 5 categories + counts (73 requested /
   3 scheduled) are VERIFIED live; enumerating every report *type* within each category needs the
   Type/Sub-Type dropdown expanded (a future click-to-open pass) or `getReportsV2` (a POST).

_The former top gap — "no browser walk was performed" — is CLOSED: both portals were walked live
this session (37 distinct section screenshots)._
