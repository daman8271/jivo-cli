#!/usr/bin/env python3
"""
sections.py — the section map for the Swiggy Instamart study.

Every endpoint in endpoints-raw.tsv is assigned to exactly ONE section by an
ordered list of path rules. First match wins; the LAST rule is a catch-all so no
endpoint can ever fall through unassigned (that is what makes the Phase-7
"100% of paths indexed" check mechanically true rather than a claim).

Each section carries the prose that makes its note a study rather than a stub:
what the surface is, what it does for JIVO, and what to watch out for.
"""

# (folder, note-name, [path-prefix rules], one-line purpose, long purpose, gotchas)
SECTIONS = [
    # ---------------- supply / vendor lane (picker.swiggy.com) --------------
    dict(folder="supply", name="Purchase-Orders",
         rules=["/api/v1/searchPurchaseOrder", "/api/v1/listPurchaseOrderLines",
                "/api/v1/purchaseMetrics", "/api/v1/suppliers/searchSuppliers",
                "/api/v1/listAllFCs"],
         short="Every PO Swiggy Instamart raises against JIVO's supplying vendors.",
         long="""The **Purchase Orders** surface (`/im-vendor/po-dashboard`) is the inbound-demand
view of the Supply Portal: every purchase order Swiggy Instamart has raised
against the distributors that supply JIVO product into its dark stores. A PO row
carries a PO number, a BU type (`MOQ`, `Multi-GRN`), the receiving facility, the
vendor name + vendor code, created/expiry dates, ordered quantity, a rank, and a
booking start date.

This is the lane JIVO's own automation has **never** touched — the daily cron
pulls a sales xlsx from the *ads* portal and nothing from the supply portal at
all. Everything documented here is new surface.""",
         gotchas="""- The dashboard status filter offers **All POs · Open · Partially Open ·
  Completed · Expired · Cancelled**, and defaults to a **`Last 30 Days`** window —
  so the first screen is never the whole PO book.
- The grid is **vendor/warehouse-scoped**: with no vendor or warehouse selected
  several sibling pages render as empty (`No data available for Selected
  Filters`) even though data exists. A count read off an unfiltered screen is
  meaningless.
- `Download Data` on this page is a **report generation** control — a WRITE under
  G2 and never clicked."""),

    dict(folder="supply", name="PO-Booking-Appointments",
         rules=["/api/v1/fc-appointment", "/api/v1/batch/list", "/api/v1/batch/submit",
                "/api/v1/document/batch/generate", "/api/v1/document/merged/generate"],
         short="Slot booking for POs into Swiggy fulfilment centres.",
         long="""**PO Booking** (`/im-vendor/po-booking`) is where a pending PO is turned into a
delivery appointment at a Swiggy facility. It is the richest page in the vendor
lane — the live walk rendered **9,486 characters** of PO rows and captured
**~83 KB** of API responses from a single visit.

The page splits into two views, `Pending POs` and `Scheduled Appointments`, and
exposes a slot recommender (`fc-appointment/recommend-slots`) plus the facility
list (`listAllFCs`) and supplier search that drive its filters.""",
         gotchas="""- **This page is the most dangerous surface in the whole study.** `Pick slot/s`,
  `Club selected POs & Book`, and the `batch-create` / `batch-reschedule` /
  `batch-cancel` appointment endpoints all mutate a real delivery booking.
  None of them was clicked and none is in the read allowlist.
- `/api/v1/batch/submit` reads like a read (its constant is
  `BULK_DOWNLOAD_PO_DATA`) but `submit` enqueues a job — treated as a WRITE.
- `document/batch/generate` and `document/merged/generate` are report generation
  → EXPORT, excluded per G2."""),

    dict(folder="supply", name="Goods-Received-GRN",
         rules=["/api/v1/searchGrns", "/api/v1/grn/searchGrnLines", "/api/v1/grn-list-data"],
         short="What Swiggy's facilities actually received against each PO.",
         long="""**Goods Received** (`/im-vendor/grn`) is the receipt side of the PO lifecycle: the
GRN (Goods Receipt Note) records what a Swiggy facility physically accepted
against a purchase order, at header level (`searchGrns`) and line level
(`grn/searchGrnLines`). Short-receipt and rejection quantities visible here are
what reconcile PO ordered-qty against invoiced qty, so this is the surface that
explains fill-rate gaps.""",
         gotchas="""- The GRN response carries `total_number_of_grn_records` at header level and
  `total_records_count` at line level — **those are the true totals**, not the
  rows drawn on screen.
- Vendor/warehouse-scoped like the rest of the lane; unfiltered = empty."""),

    dict(folder="supply", name="Returns-RTV-and-Purchase-Returns",
         rules=["/api/v1/search/rtv", "/api/v1/searchPurchaseReturn", "/api/v1/returnMetrics"],
         short="Return-to-vendor and purchase-return flows.",
         long="""Two adjacent return surfaces sit under **RETURNS** in the Supply Portal nav:

- **Return To Vendor** (`/im-vendor/rtv`) — stock Swiggy is sending back, header
  (`search/rtv`) and line (`search/rtvLines`) level.
- **Purchase Returns** (`/im-vendor/purchase-returns`) — the purchase-return
  documents, again header (`searchPurchaseReturns`) and line
  (`searchPurchaseReturnLines`) level, with `returnMetrics` for the summary
  tiles.

For an edible-oil brand these two are the direct read on damages, near-expiry
pullbacks and rejected consignments — a cost line JIVO currently has no
automated visibility into at all.""",
         gotchas="""- Both grids expose `total_records_count` and a `last_update_time`; quote those
  rather than on-screen rows.
- Nothing here is a write, but the pages sit next to PO Booking's booking
  controls — stay on the returns routes."""),

    dict(folder="supply", name="Stock-On-Hand-and-Low-Stock",
         rules=["/api/v1/inventory/"],
         short="Dark-store level inventory, days-on-hand and low-stock alerts.",
         long="""**Stock On Hand** (`/im-vendor/stock-on-hand`) and **Low Inventory**
(`/im-vendor/low-stock`) are the inventory surfaces of the Supply Portal. Stock
On Hand offers a `Real Time Summary` and a `Detailed View` with per-facility,
per-product quantity available, **DOH** (days-on-hand), open POs and open PO
quantity. The summary tiles are High Risk Items (DOH <= 1), Low Stock Items
(1 < DOH <= 5), Total Inventory Count and Total Inventory Value.

`inventory/search/lowStockFcs` is the facility-level low-stock list; this is the
closest thing Swiggy exposes to a stock-out early-warning feed, and JIVO reads
none of it today.""",
         gotchas="""- **The empty-state trap:** with no vendor/warehouse selected the tiles read
  `High Risk Items 0 · Low Stock Items 0 · Total Inventory Count 0 · Total
  Inventory Value Rs 0` and the grid says `No data available for Selected
  Filters`. Those zeros are **not** JIVO's inventory — they are an unfiltered
  query. Any number taken from this page must name its vendor + warehouse filter.
- `Bulk Download` is a report-generation control → WRITE under G2, never clicked.
- **The grid could not be driven, and the numbers were obtained anyway.** A fifth
  pass seeded `__IM_VENDOR_BRAND_ID__` (client-side, in a copy of the profile) and
  the grid still rendered empty; a DOM dump proved these pages expose **no standard
  `<select>` or combobox at all** (0 selects, 0 comboboxes, 0-1 checkboxes), which is
  also why the earlier filter-widening clicks produced byte-identical before/after
  screenshots. The real inventory data came instead from an **already-generated
  export** in [[Vendor-Downloads]] — 735 SKU x facility rows with `DaysOnHand`,
  `PotentialGmvLoss`, `OpenPos`, `OpenPoQuantity` and `WarehouseQtyAvailable`.
  See [[Swiggy-Instamart-Data-Inventory]] section 3b."""),

    dict(folder="supply", name="Availability-and-Fill-Rate",
         rules=["/api/v1/searchInventoryAvailabilityMetrics", "/api/v1/category/list",
                "/api/v1/brands/list"],
         short="City/store availability and the fill-rate view.",
         long="""**Availability** (`/im-vendor/availability`) reports how often JIVO's SKUs were
actually available to buy, sliced by city, facility and category — the
q-commerce metric that decides whether a listed SKU earns anything. It is fed by
`searchInventoryAvailabilityMetrics`, with `category/list` and `brands/list`
supplying its filter vocabularies.

`category/list` returned **94 categories** live; that list is the complete
category filter vocabulary for the vendor lane.""",
         gotchas="""- `searchInventoryAvailabilityMetrics` returned **HTTP 403
  `{"status_code":1,"message":"Invalid Request Body"}`** on the passive render —
  the page issues it before a required filter is chosen. So the endpoint is
  PROVEN to exist and PROVEN to reject an unfiltered call; its success shape is
  **not** captured. Recorded as such rather than guessed.
- Availability is inherently **city- and dark-store-scoped**. A national roll-up
  hides exactly the gaps this page exists to show."""),

    dict(folder="supply", name="Vendor-Performance-Scores",
         rules=["/api/v1/searchSupplierPerformanceMetrics"],
         short="Swiggy's scorecard on JIVO's supplying vendors.",
         long="""**PERFORMANCE** is the first block in the Supply Portal nav and has three views:
`Vendor Scores` (`/im-vendor/performance-vendor-scores`), `Facility Level`
(`/im-vendor/performance-facility-view`) and `Item Level`
(`/im-vendor/performance-item-list-view`). All three are served by
`searchSupplierPerformanceMetrics` with a different grouping.

This is Swiggy's own scorecard on how well JIVO's distributors serve it — fill
rate, appointment adherence, short supply. It is the surface most likely to be
quoted back at JIVO in a commercial conversation, and JIVO does not read it.""",
         gotchas="""- One endpoint, three groupings — the view is chosen by the request body, not
  the path, so the three routes share a single endpoint row.
- Vendor-scoped; pick the vendor before quoting a score."""),

    dict(folder="supply", name="Vendor-Downloads",
         rules=["/api/v1/vendorPortal/accessInfo"],
         short="The vendor lane's report queue and access scope.",
         long="""**Downloads** (`/im-vendor/downloads`, filed under `Finance` in the nav) is the
vendor lane's report queue: report type, requested date, the filters the report
was generated with, and the download action. `vendorPortal/accessInfo` is the
call every vendor page makes on mount to establish what the signed-in user may
see — it is the vendor lane's authorization probe.""",
         gotchas="""- The queue header reads **"Reports created in the last 7 days"** with an
  explicit date range. That 7-day window is a display default, not the retention
  limit.
- **This section turned out to be the way into the whole inventory dataset.**
  `batch/list` reports **`total_records_count` = 101** completed export jobs that
  `ecom1@jivo.in` has already generated. Downloading an already-completed row is a
  READ (AMENDMENT-02 permits it explicitly); **generating** one is a WRITE (G2) and
  was never done. Three existing exports were downloaded and aggregated — see
  [[Swiggy-Instamart-Data-Inventory]] section 3b for the numbers, including
  **Rs 2.84 Cr of `PotentialGmvLoss`** across 735 SKU x facility rows.
- Job types seen: `VENDOR_PORTAL_GENERATE_ITEM_INVENTORY_DOCUMENTS`,
  `VENDOR_PORTAL_GENERATE_GOODS_RECEIVE_NOTE_DOCUMENTS`,
  `VENDOR_PORTAL_GENERATE_PURCHASE_ORDER_DOCUMENTS`.
- Output files land on a **fifth S3 bucket**,
  `scm-procurement-mumbai.s3.ap-south-1.amazonaws.com/inventory-downloads/csv/`,
  distinct from the ads lane's `im-brand-reports-in-west` bucket.
- The first walk saw the queue as empty; a later pass saw a completed
  **Stock On Hand / 29 Jul 2026** row. So "empty" here means "nothing in the
  display window", not "no reports exist"."""),

    dict(folder="supply", name="Local-Buying",
         rules=["/api/v1/external/indent"],
         short="The local-buying indent flow — a separate login.",
         long="""**Local Buying** (`/im-vendor/local-buying/*`) is a distinct sub-application
inside the vendor remote (its own federation entry,
`__federation_expose_LocalBuyingApp`) covering city-level local purchase
indents: an indent list, indent detail, indent line items, and a PO download.

It is the only surface in the study that sits behind a **second, different
login**: the remote resolves a `LOCAL_VENDOR` user pool to an
`influencer-app-*.swig.gy` identity host rather than the ozone brand IdP, and
`/im-vendor/local-buying/login` is its own login route.""",
         gotchas="""- Walked and screenshotted, but **no data**: every local-buying route rendered
  a shell with **0 API calls** under the `ecom1@jivo.in` session. Marked
  NOT_REACHABLE — needs the separate local-vendor credential, which JIVO may not
  hold at all.
- `indent/accept`, `indent/reject` and `indent/item/update` are writes that
  would accept or reject a real purchase indent. Excluded, never clicked."""),

    dict(folder="supply", name="Vendor-FAQ-Help",
         rules=["/pdf-data"],
         short="Help content and the support contact for the vendor lane.",
         long="""**Help** (`/im-vendor/faq`) carries the Supply Portal's own FAQ content and the
escalation address. It is a documentation surface rather than a data one, but it
is worth recording because it names the channel Swiggy expects a vendor issue to
arrive on, and because the FAQ text is where Swiggy states its own definitions
of the performance metrics scored elsewhere in the lane.""",
         gotchas="""- Support contact observed on the vendor pages: **`brand.support@scootsy.com`**
  (Scootsy is Swiggy's B2B entity) — the address a supply-portal dispute goes to.
- Static content; no business data, no writes."""),

    # ---------------- ads lane (partner-api + brand-portal-service) ---------
    dict(folder="ads", name="Sales-Reports",
         rules=["/api/v1/sales/report", "/instamart/v1/report"],
         short="The sales xlsx queue — the one surface JIVO's cron already uses.",
         long="""**Sales** (`/instamart/sales`) is the only Swiggy surface JIVO's daily automation
touches. The contract is three steps: **generate** (`/api/v1/sales/report`,
enqueue), **poll/list** (`/api/v1/sales/reports`), **download** the
`downloadUrl`, which is a **presigned S3 link on
`im-brand-reports-in-west.s3.ap-south-1.amazonaws.com`** requiring no auth of its
own — the presign *is* the auth.

Live, the queue held **12 completed report rows** for Jivo Wellness, the newest
`IMSales_072926_1731` covering 2026-07-01 → 2026-07-28. The parallel
`/instamart/v1/report/*` family on `partner-api` is the newer report API with
`list-sales` and `list-bdpo` variants.""",
         gotchas="""- **Listing and downloading are reads; generating is a WRITE** (G2) — it creates
  a queue row and burns the account's report quota. The read-only CLI exposes
  list + download only.
- `reports.nextPageOffset` is an operation name, not an integer — the queue is
  paginated and 12 rows is one page, not the total.
- Report rows expire (24 h per one internal note, 7 days per a later and better
  tested one), which is why JIVO's cron must regenerate daily."""),

    dict(folder="ads", name="Sales-Insights",
         rules=["/api/v1/sales/metric", "/api/v1/sales/filters"],
         short="City / product / category sales analytics — 47 metrics, 17 dimensions.",
         long="""**Sales Insights** (`/instamart/sales-insights`) is the analytical counterpart to
the sales xlsx, and it is the single biggest unexploited surface in this study.
Two endpoints drive it: `sales/filters` returns the queryable vocabularies and
`sales/metric` returns the numbers.

Live for **Jivo Wellness**, default window 2026-07-23 → 2026-07-29:

- **132 city rows**, each with `currentValue`, `priorValue`, a percentage delta
  and lat/lng/state metadata.
- **Total sales Rs 2,35,05,424** against a prior-period Rs 2,21,00,498 = **+6.36%**.
- Top cities: Hyderabad Rs 35.7 L · Bangalore Rs 29.1 L · Delhi Rs 27.3 L ·
  Mumbai Rs 25.5 L · Chennai Rs 11.3 L.

The full vocabulary available here is **47 metric types, 17 dimension types and
25 filter types** (enumerated in [[Swiggy-Instamart-Data-Inventory]]). JIVO's
automation requests exactly **two** of the 47 (`GMV`, `UNITS_SOLD`).""",
         gotchas="""- **The default window is 7 days.** Every number on first render is a
  week-to-date figure. Any quoted total must state its window.
- The feature flag `REPORTS_NEW_UI_35_DAYS_WINDOW_ENFORCEMENT_FULL_ROLLOUT` is
  currently **false**, so the 35-day cap is not being enforced on this account —
  but it exists and can be switched on.
- `hasSalesInWindow` on each filter option tells you whether that city/product
  actually transacted in the window — the difference between "listed" and
  "selling"."""),

    dict(folder="ads", name="Ad-Campaigns",
         rules=["/api/v1/campaign", "/instamart/v1/campaign", "/api/v1/bidding-events"],
         short="Every ad campaign, its budget, pacing and state.",
         long="""**Campaigns** (`/instamart/campaign/list`, `/instamart/ads`,
`/instamart/advertisement`) is the ads-spend surface. `/api/v1/campaigns` returns
the campaign list with a **33-field** `campaign` object each: id, name, start/end
time, status and status-update reason, bidding strategy, budget (total, pacing
strategy, budget type, rollover flag), campaign criteria, ad groups with their
ads and bids, creation source and full created/updated/status-changed audit
trail with the acting email.

Live for **Jivo Wellness**: `totalCampaigns` = **27**, of which the page rendered
**10** (`paginationContext.size` = 10). Jivo Mart and the `Jivo` brand account
reported **0** campaigns each. Example row: *"Olive Oil (Early & Late)"*,
`CAMPAIGN_AD_TYPE_SPONSORED_PRODUCT`, `CAMPAIGN_STATUS_STOPPED`,
`BUDGET_TYPE_DAILY`, last touched by `ecom1@jivo.in` on 2025-12-31.""",
         gotchas="""- **27 vs 10 is the pagination trap in one line.** Read `totalCampaigns`, never
  count the rows on screen.
- Campaign create / update / pause / resume / deactivate and every bid or budget
  write are excluded — **ad campaigns spend real money**. `/api/v1/campaign`
  serves create *and* update on the same path, so the whole path is denied even
  though a GET-shaped constant (`CAMPAIGN_GET_BPS`) also points at it.
- `campaignPolicyValidationFailures` is where Swiggy reports why a campaign was
  rejected — worth reading, never writing."""),

    dict(folder="ads", name="Brand-Insights-Metrics",
         rules=["/api/v1/advertiser/metrics", "/api/v1/get-advertiser-metrics",
                "/instamart/v1/metrics"],
         short="Ad performance metrics: impressions, clicks, spend, ROAS, share-of-voice.",
         long="""**Brand Insights** is the advertiser-metrics engine behind the ads dashboards.
`advertiser/metrics` and `advertiser/metrics/batch` accept a metric list, a
dimension grouping and a filter set, and return time-series or grouped
performance. `get-advertiser-metrics` is the uptime/efficiency variant.

The metric vocabulary reachable here is far wider than sales: impressions,
clicks, CTR, CVR, conversions, spend, budget burnt (including realtime), ROAS,
ROI, CPO, eCPS, AOV, reach, sessions, new-user counts, market share, and three
share-of-voice metrics (`SOV`, `OVERALL_SHARE_OF_VOICE`,
`SPONSORED_SHARE_OF_VOICE`) plus benchmark CTR/CVR/ROI to compare against
category norms.""",
         gotchas="""- `/api/v1/3p/advertiser/metrics/batch` (the brandverse third-party variant)
  returned **HTTP 403** on passive render for this account — PROVEN to exist,
  PROVEN to be denied to `ecom1@jivo.in`. Recorded as role-denied, not guessed.
- `BENCHMARK_*` metrics are Swiggy's category benchmark, i.e. competitor-relative
  performance without naming competitors. Nothing in JIVO's stack reads them."""),

    dict(folder="ads", name="Keyword-And-Bid-Suggestions",
         rules=["/api/v1/suggest", "/api/v1/keyword", "/instamart/v1/keywords",
                "/api/v1/campaigns/suggest_bids"],
         short="Keyword suggestions, bid guidance, budget and placement recommendations.",
         long="""A cluster of recommendation endpoints supports campaign construction:
keyword suggestions (`suggest/keyword/bids`, `instamart/v1/keywords/suggestions`),
L2 category placement suggestions, catalog-targeting category paths, suggested
bids inside campaigns, budget suggestions and placement suggestions, plus
`keyword/campaign-insights` for how keywords are actually performing.

These are pure reads that reveal **what Swiggy thinks JIVO should be bidding on**
— the platform's own view of the search demand around edible oil — and none of it
is currently pulled.""",
         gotchas="""- The keyword-insight surface pairs with the `KEYWORD_SOV_FULL_ROLLOUT` and
  `SEARCH_QUERY_REPORT_FULL_ROLLOUT` flags, both **on** for this account: there
  is a search-query report available that JIVO has never generated.
- These endpoints are read-safe but sit inside campaign-editing screens; the
  surrounding Save/Launch controls are forbidden."""),

    dict(folder="ads", name="Creatives",
         rules=["/api/v1/creative", "/instamart/v1/creative"],
         short="Ad creative library and its (excluded) upload path.",
         long="""The creative surface covers the pre-approved creative library
(`creative/list`) and creative detail (`creative/details`), which together are
what a campaign's ad units draw from. Alongside them sits
`instamart/v1/creative/get-upload-info-v2`, which issues S3 upload credentials.""",
         gotchas="""- `get-upload-info-v2` is an **HTTP GET** and its constant is
  `GET_S3_UPLOAD_INFO`, so a naive verb-based rule would admit it. It is
  nevertheless **excluded**: its only purpose is to hand back credentials that
  enable a creative upload. Read-only means not standing next to the write
  either.
- `creative/list`'s constant is `PREAPPROVED_CREATIVES` — an early pass of my
  classifier flagged it WRITE because the string contains "approve". Tokenising
  the constant name (`pre` / `approved` / `creatives`) fixed it; it is a READ."""),

    dict(folder="ads", name="Requisition-Orders",
         rules=["/api/v1/release-order"],
         short="Release / requisition orders — the ads booking documents.",
         long="""**Requisition Orders** (`/instamart/requisition-orders`) covers release orders
(ROs): the commercial documents behind booked ad inventory. `release-orders/search`
lists them, `release-order` fetches one, and the surface also carries approve and
delete operations.

The `RO_UPLOAD_FULL_ROLLOUT` flag is **false** on this account, so the RO bulk
upload path is not currently active for JIVO.""",
         gotchas="""- `/api/v1/release-order` is bound to **two** constants — `RELEASE_ORDER_GET`
  *and* `RELEASE_ORDER_DELETE` — on the same path, distinguished only by HTTP
  method. Deny-by-default applies to the path, so it is excluded even though a
  read exists there. `release-orders/search` (plural, `/search`) is the safe read.
- `release-order/approve` is a commercial approval. Never called."""),

    dict(folder="ads", name="Products-And-SPINs",
         rules=["/api/v1/products", "/instamart/v1/products"],
         short="JIVO's product catalogue as the ads platform sees it.",
         long="""Product lookup for campaign targeting and reporting: `products/filter` (by
brand), `products/search` (free text), `products/batch` (bulk fetch by id) and
the sampling remote's `spins` / `spins/batch`. Swiggy's product identifier is the
**SPIN** (e.g. `L7P0RZ1JUI`), which is the join key between the ads surface, the
catalog surface and the sales report xlsx.

Live, the sales filter reported **37 products with sales in window** for Jivo
Wellness against **12** for Jivo Mart.""",
         gotchas="""- SPIN is the identifier to key on across every Swiggy surface — not EAN, not
  JIVO's item code. The sales xlsx `ITEM_CODE` column maps to it.
- "Products with sales in window" (37) is smaller than "SPINs listed" (43): the
  gap is listed-but-not-selling, which is exactly the number worth watching."""),

    dict(folder="ads", name="Ads-AI-Chat",
         rules=["/api/v1/ads-chat"],
         short="An in-portal AI assistant over JIVO's own ads data.",
         long="""The shell ships an **AI chat assistant** — chunks `AskMeAnything` and
`AiChatPanel` — backed by `ads-chat/chat` plus conversation list, history and
delete endpoints. It answers questions over the account's own ads data inside the
portal.

Nobody at JIVO appears to know it exists, and the config flag
`AI_ASSISTANT_FULL_ROLLOUT` is **false**, so it is gated off for this account
even though the client code and endpoints ship.""",
         gotchas="""- `ads-chat/chat` posts a prompt and creates a conversation record; classified
  UNKNOWN and **not** exercised (G1). Sending a prompt would write a
  conversation row.
- `conversations/{conversation_id}` on **DELETE** removes a session — excluded.
- The listing endpoints (`conversations/list`,
  `conversations/{id}/messages/list`) are reads."""),

    dict(folder="ads", name="NPI-New-Product-Introduction",
         rules=["/api/v1/suggest-placement"],
         short="New Product Introduction pipeline.",
         long="""**NPI** (`/instamart/npi`) is the New Product Introduction surface — the pipeline
by which a new SKU gets listed onto Instamart. The config flag `NPI_ENABLED` is
**true** for this account and the walk saw NPI-tagged catalog images
(`NPI-152297`, `NPI-151560`, `NPI-151565`, `NPI-151592`, `NPI-151593`,
`NPI-151561`, `NPI-151573`, all dated 2026-07-16) being loaded by the catalog
surface, which means there is live NPI activity on JIVO's account.

The route renders inside the ads remote and shares the placement-suggestion
endpoint.""",
         gotchas="""- The NPI ids seen came from **image URLs** the page loaded, not from a JSON
  response — good enough to prove activity and a date, not enough to enumerate
  the pipeline. Recorded as evidence of activity, not as a count.
- NPI submission is a write surface; only the listing view was opened."""),

    # ---------------- discounts / sampling / brandverse / catalog -----------
    dict(folder="brand", name="Discounts-BDPO",
         rules=["/api/discounting", "/im-discounts/v1", "/api/v1/discount"],
         short="Brand-funded discount campaigns (BDPO) and their reports.",
         long="""**Discounts** (`/im-discounts`) is the `imBdpoClient` remote — BDPO is
Swiggy's brand-funded discount mechanism, where JIVO funds a price cut in
exchange for visibility. The remote has its own API family under
`/api/discounting/v1/*` (campaign, campaign search, campaign config, campaigns,
metrics batch, T&C acceptance, upload status) plus an account/config family
mirroring the shell's under `/im-discounts/v1/*`.

Its reports come out through the shared report queue as
`discount/reports` (list) and `discounts/report` / `report/initiate-bdpo-report`
(generate), and the sales-report API has a matching `list-bdpo` variant.""",
         gotchas="""- **Every `/api/discounting/v1/*` endpoint is method-UNRESOLVED** from the
  minified source and therefore denied per G1. They are documented in full here
  and in [[Swiggy-Instamart-Endpoints]] but none is wired into the CLI.
- The host for `/api/discounting/v1/*` (brand-portal-service) and
  `/im-discounts/v1/*` (partner-api) is **INFERRED** from the path-prefix pattern
  the other remotes follow, not observed on the wire — the live walk never got a
  discounts data call to fire.
- `ENABLE_BDPO_MONITORING` and `BDPO_INTEGRATION_FULL_ROLLOUT` are both **true**,
  so this surface is live for JIVO."""),

    dict(folder="brand", name="Sampling-Campaigns",
         rules=["/api/v1/campaign/{0}", "/api/v1/spins"],
         short="Product-sampling campaigns to acquire new users.",
         long="""**Sampling** (`/im-sampling`) is the `imSamplingClient` remote: campaigns that
put JIVO product samples into other customers' orders to acquire new users. The
portal's own promotional copy for it was captured in the config
(`BANNER_POPUP.bannerContainerTitle` = *"Introducing Sampling"*, description
*"Acquire new users by deliv..."*), which is how a surface nobody opened
advertises itself.

`SAMPLING_INTEGRATION_FULL_ROLLOUT` is **true**. The remote exposes campaign
detail and product-SPIN batch lookups, and a reports route.""",
         gotchas="""- Campaign **create** routes exist (`/im-sampling/campaign/create`) and were
  deliberately **not navigated** — a create screen can fire a draft-create call
  on mount, which would be a write. Marked NOT_WALKED with that reason.
- No sampling campaign data was returned for this account, so "is JIVO running
  sampling?" is **not answered** by this study. The surface is mapped; the
  occupancy is unknown."""),

    dict(folder="brand", name="Brandverse",
         rules=["/api/v1/3p/"],
         short="Swiggy's cross-platform brand campaign product.",
         long="""**Brandverse** (`/brandverse/overview`, `/brandverse/campaign-metrics`) is the
`brandverseClient` remote — Swiggy's cross-surface brand-campaign product,
reaching beyond Instamart into the wider Swiggy app. It talks to
`brand-portal-service` under a **third-party** metrics path
(`/api/v1/3p/advertiser/metrics/batch`) and its client identifies itself with
`x-client-id: BRANDVERSE_CLIENT`.

Its dimension vocabulary includes `DIMENSION_TYPE_CAMPAIGN_NAME` and a
`FILTERS_CAMPAIGN_LIST` query, and the UI offers an "All Brandverse Campaigns"
selector.""",
         gotchas="""- The one Brandverse data call returned **HTTP 403** for `ecom1@jivo.in` — the
  remote loads and renders but the account is **not entitled** to its metrics.
  That is a role-denied finding, recorded as such.
- Whether JIVO has ever run a Brandverse campaign therefore cannot be answered
  from this session; it needs an account with the entitlement."""),

    dict(folder="brand", name="Catalog-SPIN-Management",
         rules=["/v1/list_spin", "/v1/get_spin", "/v1/search_", "/v1/create_spin",
                "/v1/reassign_spin", "/v1/transition_spin", "/v1/validate_spin",
                "/v1/update_spin", "/v1/generate_signed_url", "/v1/list_spins"],
         short="Product catalogue: SPIN attributes, change requests and approvals.",
         long="""**Catalog** (`/im-catalog`) is the `imCatalogClient` remote and the most
surprising find of the study: JIVO can read and (with permission) drive its own
Instamart product catalogue from here. It has three routes — my catalogue
(`/im-catalog`), **approvals** (`/im-catalog/approvals`) and **update requests**
(`/im-catalog/update-requests`) — over a SPIN-change-request workflow.

Reads: `list_spins`, `get_spin_details`, `get_spin_metrics`,
`list_spin_change_requests`, `get_spin_change_workflow_details`,
`get_spin_change_attribute_details`, `search_brands`, `search_categories`.

Live: **43 SPINs total** for Jivo Wellness (10 on the first page) and **9** for
Jivo Mart. `CATALOG_FULL_ROLLOUT` is **true**.""",
         gotchas="""- The `/im-catalog/update-requests` route was **missed in walk pass 1** because
  my own transport gate blocked the page navigation — the route string contains
  the word "update". Fixed under AMENDMENT-04 and walked in a later pass. Logged
  rather than quietly dropped.
- `create_spin_change_request`, `reassign_spin_change_request`,
  `update_spin_change_workflow` are writes against JIVO's own catalogue —
  excluded. `transition_` and `validate_` are UNKNOWN → denied.
- `generate_signed_url` is an upload enabler → EXPORT, excluded."""),

    # ---------------- platform ---------------------------------------------
    dict(folder="platform", name="Accounts-And-Entities",
         rules=["/instamart/v1/account", "/api/v1/account"],
         short="The three JIVO accounts and what each may see.",
         long="""The account surface is what makes multi-entity coverage possible.
`instamart/v1/account/list` returns the full entity graph and
`api/v1/account/permissions` returns the signed-in user's domains.

Live, `ecom1@jivo.in` (user id **345**) can select **three** accounts, and the
`/account-select` screen states it plainly: *"Welcome ecom1, You can access both
the Brand and Supply portal from below."*

| Account (selectable) | Account id | brandCompany id | brandAccount id |
|---|---|---|---|
| **Jivo Mart Pvt. Ltd** | `89bafc9c-8a56-4286-94cf-a55ab4e564d3` | `935ac57d898d4c1b3b8ec0001a87d28a44b12928` | `e4d59d18-4a2a-4ccb-a03c-2bbdb4474b79` |
| **Jivo Wellness** | `c9f24655-a984-4b65-a4da-2d5b6461b9ec` | `5ecb3c0025f73c6716097e1a1a6e62390ceb2504` | `260921c1-76e7-48ef-9771-82124ebe1fcc` |
| **Jivo** (brand under Wellness) | `260921c1-76e7-48ef-9771-82124ebe1fcc` | — | brand `1bd421f677aba0b28ef95a6ed80970824cdf83ec` |

Permissions returned `userType: USER_TYPE_BRAND`, `personas: []`, and
`accessibleDomains: ["DOMAIN_ADS", "DOMAIN_CATALOG", "DOMAIN_PARTNER"]`.""",
         gotchas="""- **A naming error in JIVO's own automation.** `~/.config/swiggy-instamart-cli/
  config.json` maps `brand_accounts.mart -> c9f24655...`, but the live
  `/account-select` tile for `c9f24655...` is **Jivo Wellness**, and Jivo Mart is
  `89bafc9c...`. VERIFIED by clicking each tile and reading back
  `__IM_ADS_CURRENT_ACCOUNT_ID__`. The consequence — whether the daily sales
  upload is labelling Mart and Wellness data correctly — is **INFERRED and worth
  a human check**; this study did not trace the upload.
- The hierarchy is `brandCompany -> account -> brandAccount -> brand`. Several
  internal notes use "brand id" for three different levels of it.
- Every account object returned `status: "ACCOUNT_STATE_INVALID"` and an empty
  `name` — a Swiggy-side data quirk, not an account problem; the display names
  come from `brandCompany.name`."""),

    dict(folder="platform", name="Config-And-Feature-Flags",
         rules=["/instamart/v1/configs", "/api/discounting/v1/campaign/config"],
         short="141 cities, 74 config keys, and the portal's whole feature surface.",
         long="""`GET partner-api.swiggy.com/instamart/v1/configs` is the single most
information-dense endpoint in the portal: **24,655 bytes / 74 keys**, fetched on
every page load. It is the portal telling you exactly what it can do.

- **`IM_ENABLED_CITIES` = 141 cities**, each with an id — the master city
  vocabulary for every city-scoped query in the study.
- **`VENDOR_WHITELISTED_ACCOUNTS` = 198** account ids;
  `BANNER_ADS_WHITELISTED_ACCOUNTS` and
  `SPECIALITY_ADS_WHITELISTED_ACCOUNTS` = **83** each.
- ~60 `*_FULL_ROLLOUT` feature flags naming every ad format and surface Swiggy
  ships: sponsored product, banner, speciality, top-slot (v1 and a gated v2),
  collection ads, pre-search ads, auto-suggest ads, FBT / SwigSmart, one-click
  campaigns, dynamic pricing, festival bid booster, user targeting, keyword SOV,
  budget rollover, ad-slot rank, granular reports, search-query report.
- `CONFIG_TEXTS` carries live commercial parameters, e.g.
  `BID_DISCOUNT_FOR_TOP_SLOT#0.25`.""",
         gotchas="""- **Flags that are OFF are as informative as those that are ON.**
  `AI_ASSISTANT_FULL_ROLLOUT`, `REPORTS_V2_FULL_ROLLOUT`,
  `RO_UPLOAD_FULL_ROLLOUT`, `TOP_SLOTV2_FULL_ROLLOUT`,
  `REPORTS_NEW_UI_35_DAYS_WINDOW_ENFORCEMENT_FULL_ROLLOUT` and
  `FEATURE_RESTRICTIONS_FULL_ROLLOUT` are all **false** for this account.
- The 141-city config list is larger than the 132 cities the sales filter
  returns — the gap is cities with no JIVO sales history, and it is a real
  distribution-whitespace signal.
- `FEATURE_CONFIG` came back as an **empty object**; recorded as empty, not
  omitted."""),

    dict(folder="platform", name="Auth-Sessions-And-Login",
         rules=["/v1/accounts", "/v2/accounts", "/v1/token", "/time"],
         short="Email-OTP login, the JWT, and the endpoints this study refuses to call.",
         long="""Authentication runs through Swiggy's **ozone** IdP at
`ozone-idp-brands-im-kba.swiggy.com` for the brand user pool, with
`partner-api.swiggy.com` serving the internal/employee pool. Login is
**passwordless email OTP**; there is no password to hold.

The endpoint family is `createAuthURI` (initiate), `sendVerificationCode` (mails
the OTP), `signInWithOTP`, `signInWithIDP` (SSO), `token/refresh` and `signOut`.
The vendor remote uses `/v2/accounts/sendVerificationCode`.

`GET partner-api.swiggy.com/time` is an unauthenticated server-clock endpoint
that exists because every brand-portal data call is **request-signed** with a
server-synced millisecond timestamp. Full mechanics in [[Auth-and-Access]].""",
         gotchas="""- **Every endpoint in this section is a WRITE and none was called.** They mint,
  rotate or destroy a session. `sendVerificationCode` would email a real OTP to a
  real mailbox; `signOut` would log out the human whose session this study
  borrowed; `token/refresh` rotates a **single-use** refresh token and would
  break both JIVO's e-com team's live session and the production keepalive cron.
- `token/refresh` was attempted **123 times by the application itself** during
  the walks and blocked every time, before the socket opened. That block is
  deliberate and was ratified by the lead.
- `/time` is the one read here, and it is the only unauthenticated endpoint in
  the entire study."""),

    dict(folder="platform", name="Telemetry-And-Third-Party",
         rules=["/message-set", "/1/", "/browser/blobs", "/events/"],
         short="New Relic and Swiggy analytics beacons — out of scope, documented.",
         long="""The portal ships two telemetry channels that are not JIVO business surfaces but
do appear in any honest network capture, so they are recorded rather than
silently filtered:

- **New Relic Browser** on `bam.nr-data.net` (`/1/<key>`, `/events/1/<key>`,
  `/browser/blobs`), configured in-app with a `NR_ENDPOINT` on
  `insights-collector.newrelic.com` for account `737486`. The shell also names an
  `appVCode` of `0.0.34`.
- **Swiggy analytics** on `analytics.swiggy.com/message-set`.

Neither carries JIVO data worth reading; both are excluded from the CLI.""",
         gotchas="""- These are **third-party hosts**, so they are listed for completeness of the
  network record and explicitly kept out of the endpoint allowlist.
- The New Relic browser key appeared in captured URLs and has been **redacted**
  per G6 by `captures/scrub.py`.
- Because they are non-GET beacons, they would otherwise clutter the
  AMENDMENT-04 audit trail; they are filtered out of
  `nonget-allowed.tsv` by host, and that filter is stated here so the omission
  is not mistaken for completeness."""),
]

CATCHALL = dict(folder="platform", name="Unclassified-Endpoints",
                rules=[""],
                short="Endpoints that matched no section rule — listed so none is lost.",
                long="""This note exists so that the section map can never silently drop an endpoint.
Every path in `captures/endpoints-raw.tsv` is assigned to a section by an ordered
rule list; anything that matches no rule lands here and is visible rather than
absent. An empty table below is the healthy state and means the map is complete.""",
                gotchas="""- If this table is ever non-empty, the fix is to add a rule to
  `captures/sections.py`, not to delete the row.""")


def assign(path):
    """Longest-matching-rule wins, so section order in the list cannot starve a
    more specific section (e.g. Brandverse's `/api/v1/3p/` vs Brand-Insights'
    `/api/v1/advertiser/metrics`, or Sampling's `/api/v1/campaign/{0}` vs
    Ad-Campaigns' `/api/v1/campaign`). Ties fall back to declaration order."""
    best, best_len = None, -1
    for s in SECTIONS:
        for r in s["rules"]:
            if r and path.startswith(r) and len(r) > best_len:
                best, best_len = s, len(r)
    return best or CATCHALL


if __name__ == "__main__":
    import csv
    import os
    from collections import Counter
    here = os.path.dirname(os.path.abspath(__file__))
    c = Counter()
    with open(os.path.join(here, "endpoints-raw.tsv")) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            c[assign(row["path"])["name"]] += 1
    for s in SECTIONS + [CATCHALL]:
        print(f"{c.get(s['name'], 0):4d}  {s['folder']}/{s['name']}")
    print(f"total assigned: {sum(c.values())}")
