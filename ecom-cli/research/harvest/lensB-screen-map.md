# JIVO ecom SPA - screen map (Lens B: react-query hooks + endpoint-to-screen)

Static analysis of the 152 bundled JS chunks at `https://ecom.jivo.in`. No HTTP request was made.

## How to read this

The app is a React single-page app. Each screen is its own JS chunk, and each
data-loading screen registers its reads with TanStack Query under a **query key** -
the app's own human-readable name for the thing it is fetching. This document maps
**URL -> screen -> the API endpoints that back it**.

Two service modules hold nearly the whole API surface:

* `api-De44ElJm.js` - 51 service objects, 167 path-bearing functions (dashboard, platform, sap, reports, uploads, auth, notifications, chatbot)
* `shipmentAPI-DKVOXJWL.js` - 6 service objects, 37 path-bearing functions: the whole shipment/appointment domain

A handful of endpoints are called with a raw `fetch` outside both modules - those are
listed separately at the end, and they are the ones most likely to be missing from any
earlier scrape.

In the endpoint tables, **direct** means the screen calls `service.fn(...)` by name.
**via config/prop** means the service was handed to the screen through a lookup table
or a prop, so the call site does not name it - equally real, just not greppable.

---

## 1. URL map

Nested routes (no leading `/`) sit under `/platform/:slug/` unless the parent says otherwise;
`:shipmentId`, `new`, `plan-review`, `list`, `approvals`, `appointments`, `po-list`,
`sku-pendency`, `inventory`, `soh-doh`, `record`, `short-supply` sit under
`/platform/amazon/shipment-planning/`.

| URL | Screen chunk | Permission gate |
|---|---|---|
| `/login` | inline in index-B7YHcZB3 (posts `/api/auth/login`) | - |
| `/register` | _redirect_ -> `/login` | - |
| `/home` | Dashboard-Ci-nVmGI | - |
| `/dashboard` | _redirect_ -> `/home` | - |
| `/monthly-targets` | MonthlyTargetsDashboard-C6tDz4u1 | - |
| `/realise` | RealiseDashboard-Swjb6XJE | - |
| `/state-wise-sales` | StateSalesPage-BkPgGHdT | - |
| `/platform-primary` | PlatformSummaryDashboard-1tTM8G_m | - |
| `/platform-primary/summary` | _redirect_ -> `/platform-primary` | - |
| `/secondary` | PlatformSummaryDashboard-1tTM8G_m | - |
| `/secondary/summary` | _redirect_ -> `/secondary` | - |
| `/uploaders` | UploadHub-CFeNTXbc | - |
| `/inventory` | FolderLandingPage-Bvg4tfpe | - |
| `/inventory/:section` | FolderLandingPage-Bvg4tfpe | - |
| `/distributor` | FolderLandingPage-Bvg4tfpe | - |
| `/distributor/inventory` | DistributorInventory-BuH1TMUp | - |
| `/distributor/lead-time-report` | DistributorLeadTimeReport-j325ZCaA | - |
| `/distributor/:section` | FolderLandingPage-Bvg4tfpe | - |
| `/expense` | FolderLandingPage-Bvg4tfpe | - |
| `/expense/:section` | FolderLandingPage-Bvg4tfpe | - |
| `/ads/summary` | AdsSummaryDashboard-DeFWFp7z | - |
| `/meta/summary` | MetaDashboard-BDuhtHQG | - |
| `/ads/:slug` | AdsDashboardPage-CvWsF0-5 | - |
| `/brand-fund/:slug` | BrandFundDashboardPage-ctfVl_O5 | - |
| `/coupon/:slug` | CouponDashboardPage-DgAebL8Y | - |
| `/platform/:slug` | PlatformLayout-CyWcJFoO | - |
| `distributors` | PlatformDistributors-GraOOjYO | - |
| `landing-rate` | PlatformLandingRate-ekTWGLjV | - |
| `monthly-targets` | PlatformMonthlyTargets-KsbVedp7 | - |
| `mp-dashboard` | PlatformAmazonMpDashboard-DpC_8QRL | - |
| `sec-monthly-dashboard` | PlatformSecondaryMonthlyDashboard-BDkOtNie | - |
| `comparison-dashboard` | PlatformAmazonComparisonDashboard-CGE4ONLi | - |
| `price-dashboard` | PlatformAmazonPriceDashboard-CB0kEp_Y | - |
| `ads-dashboard` | PlatformAmazonAdsDashboard-CrRNhpXf | - |
| `coupon-dashboard` | PlatformAmazonCouponDashboard-B-fM8OBN | - |
| `swiggy-ads-dashboard` | PlatformSwiggyAdsDashboard-BFm-kjY7 | - |
| `zepto-ads-dashboard` | PlatformZeptoAdsDashboard-CzxboD8A | - |
| `bigbasket-ads-dashboard` | PlatformBigBasketAdsDashboard-BM6JTRv6 | - |
| `swiggy-ads-daily-dashboard` | PlatformSwiggyAdsDailyDashboard-CACAkuCY | - |
| `zepto-ads-daily-dashboard` | PlatformZeptoAdsDailyDashboard-kPA13_UP | - |
| `bigbasket-ads-daily-dashboard` | PlatformBigBasketAdsDailyDashboard-CWBiApPj | - |
| `blinkit-ads-dashboard` | PlatformBlinkitAdsDashboard-D_Da537r | - |
| `flipkart-ads-dashboard` | PlatformFlipkartAdsDashboard-D4pIPBx6 | - |
| `flipkart-fsn-dashboard` | PlatformFlipkartFsnDashboard-m4SGOAfl | - |
| `blinkit-brandfund-dashboard` | PlatformBlinkitBrandFundDashboard-B6HX96hG | - |
| `swiggy-brandfund-dashboard` | PlatformSwiggyBrandFundDashboard-BzwzwbVT | - |
| `zepto-brandfund-dashboard` | PlatformZeptoBrandFundDashboard-BDqDCRih | - |
| `drr-dashboard` | PlatformDrrDashboard-Cqk5cpEd | - |
| `sales-explorer` | PlatformSalesExplorer-D1Uo1eXe | - |
| `monthly-sales-explorer` | PlatformMonthlySalesExplorer-DtnEz7vb | - |
| `soh-doh-dashboard` | PlatformBlinkitSohDohDashboard-D2tLCClb | - |
| `region-doh-dashboard` | PlatformRegionDohDashboard-pJnNQ_ky | - |
| `primary-dashboard` | PlatformPrimaryDashboard-CGfMM7xY | - |
| `primary/new-po` | AmazonNewPoDashboard-BQx-Ys_W | - |
| `primary/sku-pendency` | SkuPoPendency-3UpTl4Uw | - |
| `primary/billing` | AmazonBilling-BiLIzb_- | - |
| `pendency` | PlatformPendencyDashboard-CmKVtdvh | - |
| `primary/dashboard` | PlatformPrimaryDashboard-CGfMM7xY | - |
| `primary/sheet-preview` | PlatformSheetPreview-yW3PDFNM | - |
| `primary/sheet/:table` | PlatformSheetView-Uw04Ru2T | - |
| `primary/landing-rate` | PlatformLandingRate-ekTWGLjV | - |
| `primary/monthly-targets` | PlatformPrimaryMonthlyTargets-1Am4xH-_ | - |
| `uploads` | _redirect_ -> `/uploaders/primary/amazon` | - |
| `uploads/amazon-po` | _redirect_ -> `/uploaders/primary/amazon` | - |
| `uploads/appointment` | AmazonUploadReports-6BX8qlyd | - |
| `uploads/history` | AmazonUploadHistory-nep8tTxX | - |
| `uploads/:uploadId` | AmazonUploadDetail-C3Ao7_Sr | - |
| `reports/amazon-po` | AmazonReportPage-BLx9otoW | - |
| `reports/appointment` | AmazonReportPage-BLx9otoW | - |
| `po-dashboard` | _redirect_ -> `../reports/amazon-po` | - |
| `appt-dashboard` | AmazonDashboard-DrkflwCw | - |
| `upload/inventory` | InventoryUploader-BAqj1RTL | - |
| `upload/secondary` | SecondaryUploader-CkLbJWEG | - |
| `upload/primary` | PrimaryUploader-CsWhy2Fm | - |
| `upload/fk-grocery` | FkGroceryUploader-qAJP3aLc | - |
| `upload/amazon-price-data` | AmazonPriceUploader-DpnBkbjw | - |
| `upload/brand-fund` | ZeptoBrandFundUploader-2nPpFxXZ | - |
| `/uploaders/primary/amazon` | AmazonUploadReports-6BX8qlyd | - |
| `/uploaders/primary/amazon/detail/:uploadId` | AmazonUploadDetail-C3Ao7_Sr | - |
| `/uploads` | _redirect_ -> `/uploaders/primary/amazon` | - |
| `/uploads/amazon-po` | _redirect_ -> `/uploaders/primary/amazon` | - |
| `/uploads/appointment` | _redirect_ -> `/platform/amazon/uploads/appointment` | - |
| `/uploads/history` | _redirect_ -> `/platform/amazon/uploads/history` | - |
| `/reports/amazon-po` | _redirect_ -> `/platform/amazon/reports/amazon-po` | - |
| `/reports/appointment` | _redirect_ -> `/platform/amazon/reports/appointment` | - |
| `/upload/inventory` | InventoryUploader-BAqj1RTL | - |
| `/upload/secondary` | SecondaryUploader-CkLbJWEG | - |
| `/upload/primary` | PrimaryUploader-CsWhy2Fm | - |
| `/upload/fk-grocery` | FkGroceryUploader-qAJP3aLc | - |
| `/upload/amazon-price-data` | _redirect_ -> `/platform/amazon/upload/amazon-price-data` | - |
| `/sap-data` | PlatformSapData-ByaICPCc | `jmPrimary` |
| `/sap-dashboard` | PlatformSapDashboard-bUN0KEtA | `jmPrimary` |
| `/sap-inventory` | PlatformSapInventory-DsKqShCV | `jmInventory` |
| `/sap-inventory-dashboard` | PlatformSapInventoryDashboard-CWJH5Sdz | `jmInventory` |
| `/reports` | Reports-C5n-R5Ns | - |
| `/pricing` | LiveReports-CYEa95aB | `pricing` |
| `/penetration-report` | PenetrationReport-D-5IXm27 | - |
| `/upload/master-sheet` | MasterSheetManager-CWEDZOOq | - |
| `/upload/ads-master` | MasterSheetManager-CWEDZOOq | - |
| `/upload/pincode-mapping` | MasterSheetManager-CWEDZOOq | - |
| `/notifications/inventory-doh/:id` | InventoryDohNotificationDetail-BgnS1LOZ | - |
| `/upload/amazon-price` | _redirect_ -> `/platform/amazon/upload/amazon-price-data` | - |
| `/platform/amazon/shipment-planning` | SPDashboard-B50OFi59 | `shipmentPlanning` |
| `new` | CreateShipment-jeq_xTG5 | - |
| `plan-review` | PlanReview-BcfG6YlQ | - |
| `list` | ShipmentList-G11ipdat | - |
| `approvals` | Approvals-S-KerpS0 | - |
| `appointments` | AppointmentListPage-C-tsUaqF | - |
| `po-list` | POList-CN9Y_k2W | - |
| `sku-pendency` | SkuPoPendency-3UpTl4Uw | - |
| `inventory` | InventoryView-Bw0D5ewQ | - |
| `inventory-wellness` | _redirect_ -> `/platform/amazon/shipment-planning/inventory` | - |
| `inventory-mart` | _redirect_ -> `/platform/amazon/shipment-planning/inventory` | - |
| `soh-doh` | SohDohView-IPXqP2BN | - |
| `sap-sales-analysis` | PlatformSapData-ByaICPCc | `jmPrimary` |
| `short-supply` | _redirect_ -> `/platform/amazon/shipment-planning/record` | - |
| `record` | Record-uhJVTCfL | - |
| `upload/appointment` | AppointmentUploader-DpWIppvv | - |
| `upload/appointment/history` | AmazonUploadHistory-nep8tTxX | - |
| `:shipmentId` | ShipmentDetail-CPxKwggz | - |
| `*` | _redirect_ -> `/login` | - |
| `sec-dashboard` | PlatformSecDashboard-BvjEDwtI (via an inline wrapper; `amazon_mp` redirects to `mp-dashboard`) | - |
| `upload/ads` | per-platform ads uploader, defaulting to AdsUploader-tW5wZlYK | - |

---

## 2. Screen by screen

### Ads dashboard router

`AdsDashboardPage-CvWsF0-5.js`  -  `/ads/:slug`

Picks the right per-platform ads dashboard for /ads/:slug. No endpoints of its own.

_No API endpoint of its own._

### Ads dashboard shell (generic)

`AdsDashboardShell-BwrGY4Hf.js`  -  _embedded, no route of its own_

The body of every per-platform ads dashboard. The parent page passes in the queryKey factory and the fetcher, so the shell itself names no endpoint. It does directly own two: the secondary dashboard (for the delivered-value comparison) and ads-total-sales.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/ads-total-sales` | direct |
| `GET` | `/api/platform/${e}/sec-dashboard` | direct |

### Ads summary

`AdsSummaryDashboard-DeFWFp7z.js`  -  `/ads/summary`

Total ad spend/sales across every platform in one number set.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/ads-summary` | direct |

### Ads uploader (generic)

`AdsUploader-tW5wZlYK.js`  -  `upload/ads (default)`

Default ads uploader when the platform has no bespoke one. Parses locally, commits via /api/upload/batch.

_No API endpoint of its own._

### Amazon billing

`AmazonBilling-BiLIzb_-.js`  -  `primary/billing`

What has been billed against Amazon POs.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/reports/amazon-po/billing` | direct |
| `GET` | `/api/reports/amazon-po/sku-pendency/filter-options` | direct |

### Amazon PO / appointment dashboard

`AmazonDashboard-DrkflwCw.js`  -  `appt-dashboard`

The two summary tiles for Amazon purchase orders and appointments.

Query keys: `amazonReports.amazonPOMatrix`, `amazonReports.appointmentSummary`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/reports/amazon-po/matrix` | direct |
| `GET` | `/api/reports/appointment/summary` | direct |

### Amazon new-PO dashboard

`AmazonNewPoDashboard-BQx-Ys_W.js`  -  `primary/new-po`

POs Amazon has raised that we have not yet acted on.

Query keys: `amazonReports.amazonNewPO`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/reports/amazon-po/new-po` | direct |

### Amazon price uploader

`AmazonPriceUploader-DpnBkbjw.js`  -  `upload/amazon-price-data`

Uploads Amazon price data; reads the table to preview it.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/dashboard/table-data/${e}` | direct |

### Amazon PO / Appointment report

`AmazonReportPage-BLx9otoW.js`  -  `reports/amazon-po`, `reports/appointment`

The big filterable grid. One component, two configurations chosen by the `type` prop: `amazonPO` (reporting."Amazon PO") and `appointment` (reporting."appointment"). Each config carries its own queryKey, queryFn, filter list and column set.

Query keys: `amazonReports.amazonPO`, `amazonReports.amazonPOFilterOptions`, `amazonReports.appointment`, `amazonReports.appointmentFilterOptions`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/reports/amazon-po` | direct |
| `GET` | `/api/reports/amazon-po/filter-options` | direct |
| `GET` | `/api/reports/appointment` | direct |
| `GET` | `/api/reports/appointment/filter-options` | direct |

### Upload detail

`AmazonUploadDetail-C3Ao7_Sr.js`  -  `uploads/:uploadId`, `/uploaders/primary/amazon/detail/:uploadId`

One upload: what was parsed, what failed, what was written.

Query keys: `amazonUploads.detail`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/uploads/${e}` | direct |

### Upload history

`AmazonUploadHistory-nep8tTxX.js`  -  `uploads/history`, `upload/appointment/history`

Every upload ever run, newest first.

Query keys: `amazonUploads.list`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/uploads` | direct |

### Upload a report

`AmazonUploadReports-6BX8qlyd.js`  -  `uploads/appointment`, `/uploaders/primary/amazon`

The generic upload form (file or pasted data) plus polling of the resulting upload record.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/uploads/${e}` | direct |
| `POST` | `/api/uploads` | direct |

### Appointment list

`AppointmentListPage-C-tsUaqF.js`  -  `appointments`

All appointments across FCs, plus the manual commit import.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/shipment/all-appointments/${t?` | direct |
| `POST` | `/api/shipment/appointment-commits/manual-import/` | direct |

### Appointment uploader

`AppointmentUploader-DpWIppvv.js`  -  `upload/appointment`

Uploads the Amazon appointment file through the same /api/uploads pipeline.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/uploads/${e}` | direct |
| `POST` | `/api/uploads` | direct |

### Shipment approvals

`Approvals-S-KerpS0.js`  -  `approvals`

The approver's queue: pending approvals, approve, reject.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/shipment/shipments/${e?` | direct |
| `GET` | `/api/shipment/shipments/pending-approvals/` | direct |
| `POST` | `/api/shipment/shipments/${e}/approve/` | direct |
| `POST` | `/api/shipment/shipments/${e}/reject/` | direct |

### Brand-fund dashboard router

`BrandFundDashboardPage-ctfVl_O5.js`  -  `/brand-fund/:slug`

Picks the right per-platform brand-fund dashboard for /brand-fund/:slug.

_No API endpoint of its own._

### Brand-fund shell (generic)

`BrandFundDashboardShell-DSuJXfX0.js`  -  _embedded, no route of its own_

Same pattern for brand-fund dashboards: everything arrives as props.

_No API endpoint of its own._

### Coupon dashboard router

`CouponDashboardPage-DgAebL8Y.js`  -  `/coupon/:slug`

Routes /coupon/:slug to the Amazon coupon dashboard.

_No API endpoint of its own._

### Create shipment

`CreateShipment-jeq_xTG5.js`  -  `new`

The planner. Pick an appointment date, load its appointments, items and families, auto-fill from DOH, run the optimiser (manual-plan), then create and submit a draft shipment. 14 endpoints, the widest single screen in the shipment domain.

| Method | Path | How |
|---|---|---|
| `?` | `/api/shipment/shipments/` | direct |
| `GET` | `/api/shipment/appointments/${e}/extra-pos/` | direct |
| `GET` | `/api/shipment/appointments/${e}/families/` | direct |
| `GET` | `/api/shipment/appointments/?date=${e}` | direct |
| `GET` | `/api/shipment/appointments/dates/` | direct |
| `GET` | `/api/shipment/fc-switch-group/?fc=${encodeURIComponent(e||` | direct |
| `GET` | `/api/shipment/po-items/?${new URLSearchParams({no_paginate:` | direct |
| `GET` | `/api/shipment/po-shipment-lookup/` | direct |
| `GET` | `/api/shipment/shipments/doh-auto-fill/${t?` | direct |
| `POST` | `/api/shipment/fc-channel/` | direct |
| `POST` | `/api/shipment/shipments/` | direct |
| `POST` | `/api/shipment/shipments/${e}/submit/` | direct |
| `POST` | `/api/shipment/shipments/manual-plan/` | direct |

### Home / company dashboard

`Dashboard-Ci-nVmGI.js`  -  `/home`

How is the whole business doing this month? One screen: category and SKU mix, top SKUs, YoY secondary growth, fulfilment health, primary vs secondary targets, an ads snapshot across all six ad platforms, SAP sales analysis, and near-expiry stock. It is by far the heaviest screen in the app - 30 endpoints, 24 react-query registrations.

Query keys: `dashboard.categoryBreakdown`, `dashboard.categoryPlatformBreakdown`, `dashboard.categorySkuBreakdown`, `dashboard.categoryTrend`, `dashboard.fulfilmentHealth`, `dashboard.platformExpiryAlerts`, `dashboard.secondaryYoyGrowth`, `dashboard.topSkus`, `masterSheet.skuLookup`, `monthlyTargets.dashboard`, `platform.amazonAdsDashboard`, `platform.bigbasketAdsDashboard`, `platform.blinkitAdsDashboard`, `platform.flipkartAdsDashboard`, `platform.mpDashboard`, `platform.primaryOverview`, `platform.primarySummary`, `platform.secDashboard`, `platform.swiggyAdsDashboard`, `platform.zeptoAdsDashboard`, `primaryMonthlyTargets.dashboard`, `sap.salesAnalysis`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/auth/me` | direct |
| `GET` | `/api/auth/permissions` | direct |
| `GET` | `/api/dashboard/category-breakdown` | direct |
| `GET` | `/api/dashboard/category-platform-breakdown` | direct |
| `GET` | `/api/dashboard/category-sku-breakdown` | direct |
| `GET` | `/api/dashboard/category-trend` | direct |
| `GET` | `/api/dashboard/fulfilment-health` | direct |
| `GET` | `/api/dashboard/platform-expiry-alerts` | direct |
| `GET` | `/api/dashboard/platform-expiry-alerts/${e}/pos` | direct |
| `GET` | `/api/dashboard/platform-expiry-alerts/${e}/pos/${encodeURIComponent(t)}/items` | direct |
| `GET` | `/api/dashboard/secondary-yoy-growth` | direct |
| `GET` | `/api/dashboard/top-skus` | direct |
| `GET` | `/api/platform/${e}/ads-dashboard` | direct |
| `GET` | `/api/platform/${e}/bigbasket-ads-dashboard` | direct |
| `GET` | `/api/platform/${e}/blinkit-ads-dashboard` | direct |
| `GET` | `/api/platform/${e}/flipkart-ads-dashboard` | direct |
| `GET` | `/api/platform/${e}/mp-dashboard` | direct |
| `GET` | `/api/platform/${e}/sec-dashboard` | direct |
| `GET` | `/api/platform/${e}/swiggy-ads-dashboard` | direct |
| `GET` | `/api/platform/${e}/zepto-ads-dashboard` | direct |
| `GET` | `/api/platform/month-targets/dashboard` | direct |
| `GET` | `/api/platform/primary-month-targets/dashboard` | direct |
| `GET` | `/api/platform/primary-overview-total` | direct |
| `GET` | `/api/platform/primary-summary` | direct |
| `GET` | `/api/sap/sales-analysis` | direct |
| `GET` | `/api/upload/master-sheet` | direct |
| `POST` | `/api/auth/change-password` | direct |

### Distributor inventory

`DistributorInventory-BuH1TMUp.js`  -  `/distributor/inventory`

What stock is sitting with a given distributor, from SAP.

Query keys: `sap.distributorInventory`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/sap/distributor-inventory` | direct |

### Distributor lead-time report

`DistributorLeadTimeReport-j325ZCaA.js`  -  `/distributor/lead-time-report`

How long between order and delivery, per distributor.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/dashboard/lead-time-report` | direct |

### Flipkart Grocery uploader

`FkGroceryUploader-qAJP3aLc.js`  -  `upload/fk-grocery`, `/upload/fk-grocery`

Parses the Flipkart Grocery sheet, commits via its own /api/upload/fk-grocery-master endpoint, and can re-enrich already-loaded rows from the master sheet and landing rates.

_No API endpoint of its own._

### Section landing pages

`FolderLandingPage-Bvg4tfpe.js`  -  `/inventory`, `/inventory/:section`, `/distributor`, `/distributor/:section`, `/expense`, `/expense/:section`

Pure navigation tiles for /inventory, /distributor and /expense. No data of its own.

_No API endpoint of its own._

### DOH alert detail

`InventoryDohNotificationDetail-BgnS1LOZ.js`  -  `/notifications/inventory-doh/:id`

Opened from a notification: the SKU-level detail behind a days-of-hand alert.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/notifications/inventory-doh/${e}` | direct |

### Inventory uploader

`InventoryUploader-BAqj1RTL.js`  -  `upload/inventory`, `/upload/inventory`

Parses an inventory sheet client-side, then commits via the shared /api/upload/batch helper.

_No API endpoint of its own._

### Warehouse inventory

`InventoryView-Bw0D5ewQ.js`  -  `inventory`

JIVO-side stock by warehouse, refreshed every 30 s. NOTE its query key says `['shipment','sap-inventory']` but the endpoint is /api/shipment/inventory/.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/shipment/inventory/${e?` | direct |

### Pricing / live reports

`LiveReports-CYEa95aB.js`  -  `/pricing`

The live report catalogue and its data. Permission-gated on `pricing`.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/reports/live/data` | direct |
| `GET` | `/api/reports/live/reports` | direct |

### Master sheet manager

`MasterSheetManager-CWEDZOOq.js`  -  `/upload/master-sheet`, `/upload/ads-master`, `/upload/pincode-mapping`

One component, three masters selected by route: Master Sheet (SKU master), ADS Master Sheet (campaign-to-SKU map) and Pincode Mapping. Full CRUD plus paste-preview-bulk-upsert on each. The three services are handed to it through a config table, which is why a naive scan sees no calls here.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/upload/ads-master` | via config/prop |
| `GET` | `/api/upload/master-sheet` | via config/prop |
| `GET` | `/api/upload/pincode-mapping` | via config/prop |
| `POST` | `/api/upload/ads-master/add` | via config/prop |
| `POST` | `/api/upload/ads-master/bulk-upsert` | via config/prop |
| `POST` | `/api/upload/ads-master/delete` | via config/prop |
| `POST` | `/api/upload/ads-master/preview` | via config/prop |
| `POST` | `/api/upload/ads-master/update` | via config/prop |
| `POST` | `/api/upload/master-sheet/add` | via config/prop |
| `POST` | `/api/upload/master-sheet/bulk-upsert` | via config/prop |
| `POST` | `/api/upload/master-sheet/delete` | via config/prop |
| `POST` | `/api/upload/master-sheet/preview` | via config/prop |
| `POST` | `/api/upload/master-sheet/update` | via config/prop |
| `POST` | `/api/upload/pincode-mapping/add` | via config/prop |
| `POST` | `/api/upload/pincode-mapping/bulk-upsert` | via config/prop |
| `POST` | `/api/upload/pincode-mapping/delete` | via config/prop |
| `POST` | `/api/upload/pincode-mapping/preview` | via config/prop |
| `POST` | `/api/upload/pincode-mapping/update` | via config/prop |

### Meta (Facebook/Instagram) ads

`MetaDashboard-BDuhtHQG.js`  -  `/meta/summary`

Meta ad performance - the only screen on /api/platform/meta.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/meta` | direct |

### Monthly targets

`MonthlyTargetsDashboard-C6tDz4u1.js`  -  `/monthly-targets`

Are we going to hit the month? Secondary and primary month targets vs actuals, per platform, with a refresh button that recomputes them server-side, plus the call-centre target editor. This is one of the few read+write screens outside the uploaders.

Query keys: `monthlyTargets.dashboard`, `platform.secDashboard`, `primaryMonthlyTargets.dashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/auth/permissions` | direct |
| `GET` | `/api/platform/${e}/sec-dashboard` | direct |
| `GET` | `/api/platform/call-center-targets` | direct |
| `GET` | `/api/platform/month-targets/dashboard` | direct |
| `GET` | `/api/platform/primary-month-targets/dashboard` | direct |
| `POST` | `/api/platform/call-center-targets` | direct |
| `POST` | `/api/platform/month-targets/refresh` | direct |
| `POST` | `/api/platform/primary-month-targets/refresh` | direct |
| `POST` | `/api/platform/primary-month-targets/set-target` | direct |

### PO list

`POList-CN9Y_k2W.js`  -  `po-list`

Open POs with their items, billing status, and a shortcut to raise a shipment draft from them.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/reports/amazon-po/billing` | direct |
| `GET` | `/api/shipment/po-items/?${new URLSearchParams({no_paginate:` | direct |
| `POST` | `/api/shipment/shipments/` | direct |
| `POST` | `/api/shipment/shipments/${e}/submit/` | direct |

### Paginated table (embedded)

`PaginatedTable-C4rt_G6C.js`  -  _embedded, no route of its own_

The reusable data grid behind every raw-table screen: columns, rows, distinct values for filters, and bulk row edit.

Query keys: `dashboard.tableColumns`, `dashboard.tableDistinctValues`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/dashboard/table-columns/${e}` | direct |
| `GET` | `/api/dashboard/table-data/${e}` | direct |
| `GET` | `/api/dashboard/table-distinct/${e}/${t}` | direct |
| `POST` | `/api/dashboard/table-rows/${e}` | direct |

### Penetration report

`PenetrationReport-D-5IXm27.js`  -  `/penetration-report`

Where are we listed and selling vs where we could be.

Query keys: `dashboard.penetrationReport`, `dashboard.penetrationReportOptions`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/dashboard/penetration-report` | direct |
| `GET` | `/api/dashboard/penetration-report/options` | direct |

### Plan review

`PlanReview-BcfG6YlQ.js`  -  `plan-review`

Review a generated plan against SOH/DOH and PO appointments before submitting it.

| Method | Path | How |
|---|---|---|
| `?` | `/api/shipment/shipments/` | direct |
| `GET` | `/api/platform/${e}/soh-doh-dashboard` | direct |
| `GET` | `/api/shipment/po-appointments/?pos=${encodeURIComponent((e||[]).join(` | direct |
| `GET` | `/api/shipment/po-items/?${new URLSearchParams({no_paginate:` | direct |
| `POST` | `/api/shipment/shipments/` | direct |
| `POST` | `/api/shipment/shipments/${e}/submit/` | direct |
| `POST` | `/api/shipment/shipments/manual-plan/` | direct |

### PlatformAmazonAdsDashboard

`PlatformAmazonAdsDashboard-CrRNhpXf.js`  -  `ads-dashboard`

Query keys: `platform.amazonAdsDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/ads-dashboard` | direct |

### Amazon comparison dashboard

`PlatformAmazonComparisonDashboard-CGE4ONLi.js`  -  `comparison-dashboard`

Period-over-period comparison for Amazon.

Query keys: `platform.comparisonDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/comparison-dashboard` | direct |

### Coupon dashboard

`PlatformAmazonCouponDashboard-B-fM8OBN.js`  -  `coupon-dashboard`

Coupon spend and redemption for one platform.

Query keys: `platform.amazonCouponDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/coupon-dashboard` | direct |

### Amazon Marketplace (MP) dashboard

`PlatformAmazonMpDashboard-DpC_8QRL.js`  -  `mp-dashboard`

Amazon MP (3P) sales. Polls a `-version` endpoint to know when to refresh.

Query keys: `platform.mpDashboard`, `platform.mpDashboardVersion`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/mp-dashboard` | direct |
| `GET` | `/api/platform/${e}/mp-dashboard-version` | direct |

### Amazon price dashboard

`PlatformAmazonPriceDashboard-CB0kEp_Y.js`  -  `price-dashboard`

Live selling price vs our landing rate on Amazon.

Query keys: `platform.priceDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/price-dashboard` | direct |

### PlatformBigBasketAdsDailyDashboard

`PlatformBigBasketAdsDailyDashboard-CWBiApPj.js`  -  `bigbasket-ads-daily-dashboard`

Query keys: `platform.bigbasketAdsDailyDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/bigbasket-ads-daily-dashboard` | direct |

### PlatformBigBasketAdsDashboard

`PlatformBigBasketAdsDashboard-BM6JTRv6.js`  -  `bigbasket-ads-dashboard`

Query keys: `platform.bigbasketAdsDailyDashboard`, `platform.bigbasketAdsDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/bigbasket-ads-daily-dashboard` | direct |
| `GET` | `/api/platform/${e}/bigbasket-ads-dashboard` | direct |

### PlatformBlinkitAdsDashboard

`PlatformBlinkitAdsDashboard-D_Da537r.js`  -  `blinkit-ads-dashboard`

Query keys: `platform.blinkitAdsDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/blinkit-ads-dashboard` | direct |

### PlatformBlinkitBrandFundDashboard

`PlatformBlinkitBrandFundDashboard-B6HX96hG.js`  -  `blinkit-brandfund-dashboard`

Query keys: `platform.blinkitBrandFundDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/blinkit-brandfund-dashboard` | direct |

### SOH / DOH dashboard

`PlatformBlinkitSohDohDashboard-D2tLCClb.js`  -  `soh-doh-dashboard`

Stock on hand and days of hand for one platform's SKUs at the platform's warehouses.

Query keys: `platform.sohDohDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/soh-doh-dashboard` | direct |

### Platform overview (embedded)

`PlatformDashboard-Df76y2uF.js`  -  _embedded, no route of its own_

The default landing tab inside /platform/:slug. It is a composite: platform stats, secondary and primary dashboards (this month and the previous month), SOH/DOH, pendency, DRR, a Blinkit-only summary report, and whichever ads / brand-fund dashboard exists for that platform. Ten react-query registrations, most of them gated on which platform you are looking at.

Query keys: `platform.drrDashboard`, `platform.stats`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/ads-dashboard` | via config/prop |
| `GET` | `/api/platform/${e}/bigbasket-ads-dashboard` | via config/prop |
| `GET` | `/api/platform/${e}/blinkit-ads-dashboard` | via config/prop |
| `GET` | `/api/platform/${e}/blinkit-brandfund-dashboard` | via config/prop |
| `GET` | `/api/platform/${e}/blinkit-summary-report` | direct |
| `GET` | `/api/platform/${e}/drr-dashboard` | direct |
| `GET` | `/api/platform/${e}/flipkart-ads-dashboard` | via config/prop |
| `GET` | `/api/platform/${e}/pendency-dashboard` | direct |
| `GET` | `/api/platform/${e}/primary-dashboard` | direct |
| `GET` | `/api/platform/${e}/sec-dashboard` | direct |
| `GET` | `/api/platform/${e}/soh-doh-dashboard` | direct |
| `GET` | `/api/platform/${e}/stats` | direct |
| `GET` | `/api/platform/${e}/swiggy-ads-dashboard` | via config/prop |
| `GET` | `/api/platform/${e}/swiggy-brandfund-dashboard` | via config/prop |
| `GET` | `/api/platform/${e}/zepto-ads-dashboard` | via config/prop |
| `GET` | `/api/platform/${e}/zepto-brandfund-dashboard` | via config/prop |

### Platform distributors

`PlatformDistributors-GraOOjYO.js`  -  `distributors`

Which distributors serve this platform, and each one's SAP orders and invoices. The deepest SAP screen in the app.

Query keys: `sap.customerSalesInvoices`, `sap.distributorInvoices`, `sap.distributorOrders`, `sap.platformDistributor`, `sap.platformDistributors`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/sap/distributor-invoices/${e}` | direct |
| `GET` | `/api/sap/distributor-orders/${e}` | direct |
| `GET` | `/api/sap/platform-distributors/${e}` | direct |
| `GET` | `/api/sap/platform-distributors/${e}/${t}` | direct |
| `GET` | `/api/sap/sales-invoices/${e}` | direct |

### DRR dashboard

`PlatformDrrDashboard-Cqk5cpEd.js`  -  `drr-dashboard`

Daily run rate for one platform.

Query keys: `platform.drrDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/drr-dashboard` | direct |

### PlatformFlipkartAdsDashboard

`PlatformFlipkartAdsDashboard-D4pIPBx6.js`  -  `flipkart-ads-dashboard`

Query keys: `platform.flipkartAdsDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/flipkart-ads-dashboard` | direct |

### Flipkart FSN dashboard

`PlatformFlipkartFsnDashboard-m4SGOAfl.js`  -  `flipkart-fsn-dashboard`

Flipkart FSN-level performance.

Query keys: `platform.flipkartFsnDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/flipkart-fsn-dashboard` | direct |

### Landing rate editor

`PlatformLandingRate-ekTWGLjV.js`  -  `landing-rate`, `primary/landing-rate`

The per-platform landing-rate master: list, add, edit, and bulk paste-upsert with a preview step. A write screen.

Query keys: `landingRate.all`, `landingRate.list`, `landingRate.skus`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/landing-rate` | direct |
| `GET` | `/api/platform/${e}/landing-rate/skus` | direct |
| `POST` | `/api/platform/${e}/landing-rate/add` | direct |
| `POST` | `/api/platform/${e}/landing-rate/bulk-upsert` | direct |
| `POST` | `/api/platform/${e}/landing-rate/preview` | direct |
| `POST` | `/api/platform/${e}/landing-rate/update` | direct |

### Platform shell

`PlatformLayout-CyWcJFoO.js`  -  `/platform/:slug`

The per-platform chrome (sidebar, platform switcher) around every /platform/:slug/* screen.

_No API endpoint of its own._

### Monthly sales explorer

`PlatformMonthlySalesExplorer-DtnEz7vb.js`  -  `monthly-sales-explorer`

Free-form slice of one platform's monthly sales.

Query keys: `platform.monthlySalesExplorer`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/monthly-sales-explorer` | direct |

### Platform monthly targets

`PlatformMonthlyTargets-KsbVedp7.js`  -  `monthly-targets`

Set and refresh secondary month targets for one platform. A write screen.

Query keys: `monthlyTargets.platformAll`, `monthlyTargets.platformList`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/month-targets` | direct |
| `POST` | `/api/platform/${e}/month-targets/${t}/update` | direct |
| `POST` | `/api/platform/${e}/month-targets/add` | direct |
| `POST` | `/api/platform/${e}/month-targets/refresh` | direct |

### Pendency dashboard

`PlatformPendencyDashboard-CmKVtdvh.js`  -  `pendency`

What has been ordered but not yet delivered, for one platform.

Query keys: `platform.pendencyDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/pendency-dashboard` | direct |

### Primary sales dashboard

`PlatformPrimaryDashboard-CGfMM7xY.js`  -  `primary-dashboard`, `primary/dashboard`

Primary (sell-in / PO) performance for one platform - ordered vs delivered vs pending, in value, litres and quantity.

Query keys: `platform.primaryDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/primary-dashboard` | direct |

### Platform primary monthly targets

`PlatformPrimaryMonthlyTargets-1Am4xH-_.js`  -  `primary/monthly-targets`

Same, for primary targets.

Query keys: `primaryMonthlyTargets.platformAll`, `primaryMonthlyTargets.platformList`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/primary-month-targets` | direct |
| `POST` | `/api/platform/${e}/primary-month-targets/${t}/update` | direct |
| `POST` | `/api/platform/${e}/primary-month-targets/add` | direct |
| `POST` | `/api/platform/${e}/primary-month-targets/refresh` | direct |

### Region DOH dashboard

`PlatformRegionDohDashboard-pJnNQ_ky.js`  -  `region-doh-dashboard`

Days of hand cut by region rather than by SKU.

Query keys: `platform.regionDohDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/region-doh-dashboard` | direct |

### Sales explorer

`PlatformSalesExplorer-D1Uo1eXe.js`  -  `sales-explorer`

Free-form sales slice. NOTE: the endpoint is hard-coded to `/api/platform/bigbasket/sales-explorer` - the platform slug is baked in, not passed.

Query keys: `platform.salesExplorer`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/bigbasket/sales-explorer` | direct |

### SAP dashboard (JM Primary)

`PlatformSapDashboard-bUN0KEtA.js`  -  `/sap-dashboard`

The charted version of the same SAP sales analysis, anchored on the latest data month.

Query keys: `dashboard.latestMonth`, `sap.salesAnalysis`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/dashboard/latest-month` | direct |
| `GET` | `/api/sap/sales-analysis` | direct |

### SAP sales analysis (JM Primary)

`PlatformSapData-ByaICPCc.js`  -  `/sap-data`, `sap-sales-analysis`

JIVO's own SAP sell-in numbers, permission-gated on `jmPrimary`.

Query keys: `sap.salesAnalysis`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/sap/sales-analysis` | direct |

### SAP inventory (JM Inventory)

`PlatformSapInventory-DsKqShCV.js`  -  `/sap-inventory`

SAP stock overview, permission-gated on `jmInventory`.

Query keys: `sap.inventoryOverview`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/sap/inventory-overview` | direct |

### SAP finished-goods inventory

`PlatformSapInventoryDashboard-CWJH5Sdz.js`  -  `/sap-inventory-dashboard`

Finished-goods stock from SAP.

Query keys: `sap.inventoryFinishedGoods`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/sap/inventory-finished-goods` | direct |

### Secondary sales dashboard

`PlatformSecDashboard-BvjEDwtI.js`  -  `sec-dashboard`

Secondary (sell-out) sales for one platform: value / litres / quantity by item head, category and SKU, against month targets, with a DRR overlay and a year picker. Redirects amazon_mp to the MP dashboard.

Query keys: `monthlyTargets.platformList`, `platform.drrDashboard`, `platform.secDashboard`, `platform.secDashboardYears`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/drr-dashboard` | direct |
| `GET` | `/api/platform/${e}/month-targets` | direct |
| `GET` | `/api/platform/${e}/sec-dashboard` | direct |
| `GET` | `/api/platform/${e}/sec-dashboard-years` | direct |

### Secondary monthly view

`PlatformSecondaryMonthlyDashboard-BDkOtNie.js`  -  `sec-monthly-dashboard`

Month-by-month secondary sales for one platform.

Query keys: `platform.secMonthlyDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/sec-monthly-dashboard` | direct |

### Sheet preview

`PlatformSheetPreview-yW3PDFNM.js`  -  `primary/sheet-preview`

Preview of a generated primary sheet. Pure UI; data arrives via platformSheets.

_No API endpoint of its own._

### Sheet view

`PlatformSheetView-Uw04Ru2T.js`  -  `primary/sheet/:table`

Renders one primary sheet table. Pure UI.

_No API endpoint of its own._

### Primary / Secondary summary

`PlatformSummaryDashboard-1tTM8G_m.js`  -  `/platform-primary`, `/secondary`

All platforms combined, in one table - the same component serves /platform-primary and /secondary. It fans out one query per platform slug and polls a cheap `-version` endpoint so it can invalidate the expensive per-platform queries only when the server data actually changed.

Query keys: `platform.primaryDashboard`, `platform.primarySummary`, `platform.secDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/primary-dashboard` | direct |
| `GET` | `/api/platform/${e}/sec-dashboard` | direct |
| `GET` | `/api/platform/primary-summary` | direct |
| `GET` | `/api/platform/primary-summary-version` | direct |
| `GET` | `/api/platform/secondary-summary-version` | direct |

### PlatformSwiggyAdsDailyDashboard

`PlatformSwiggyAdsDailyDashboard-CACAkuCY.js`  -  `swiggy-ads-daily-dashboard`

Query keys: `platform.swiggyAdsDailyDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/swiggy-ads-daily-dashboard` | direct |

### PlatformSwiggyAdsDashboard-BFm

`PlatformSwiggyAdsDashboard-BFm-kjY7.js`  -  `swiggy-ads-dashboard`

Query keys: `platform.swiggyAdsDailyDashboard`, `platform.swiggyAdsDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/swiggy-ads-daily-dashboard` | direct |
| `GET` | `/api/platform/${e}/swiggy-ads-dashboard` | direct |

### PlatformSwiggyBrandFundDashboard

`PlatformSwiggyBrandFundDashboard-BzwzwbVT.js`  -  `swiggy-brandfund-dashboard`

Query keys: `platform.swiggyBrandFundDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/swiggy-brandfund-dashboard` | direct |

### PlatformZeptoAdsDailyDashboard

`PlatformZeptoAdsDailyDashboard-kPA13_UP.js`  -  `zepto-ads-daily-dashboard`

Query keys: `platform.zeptoAdsDailyDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/zepto-ads-daily-dashboard` | direct |

### PlatformZeptoAdsDashboard

`PlatformZeptoAdsDashboard-CzxboD8A.js`  -  `zepto-ads-dashboard`

Query keys: `platform.zeptoAdsDailyDashboard`, `platform.zeptoAdsDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/zepto-ads-daily-dashboard` | direct |
| `GET` | `/api/platform/${e}/zepto-ads-dashboard` | direct |

### PlatformZeptoBrandFundDashboard

`PlatformZeptoBrandFundDashboard-BDqDCRih.js`  -  `zepto-brandfund-dashboard`

Query keys: `platform.zeptoBrandFundDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/zepto-brandfund-dashboard` | direct |

### Primary uploader

`PrimaryUploader-CsWhy2Fm.js`  -  `upload/primary`, `/upload/primary`

Primary/PO upload. Reads the target table's current rows to show a before/after.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/dashboard/table-data/${e}` | direct |

### Realisation dashboard

`RealiseDashboard-Swjb6XJE.js`  -  `/realise`

What price are we actually realising after all deductions? Overview, breakdown and trend. Note the waterfall endpoint exists but this screen never calls it.

Query keys: `realise.breakdown`, `realise.overview`, `realise.trend`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/dashboard/realise-breakdown` | direct |
| `GET` | `/api/dashboard/realise-overview` | direct |
| `GET` | `/api/dashboard/realise-trend` | direct |

### Shipment record

`Record-uhJVTCfL.js`  -  `record`

The audit trail: shipment records and the deletion log.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/shipment/record/${t?` | direct |
| `GET` | `/api/shipment/shipments/${e}/` | direct |
| `GET` | `/api/shipment/shipments/deletion-log/${e?` | direct |

### Raw report builder

`Reports-C5n-R5Ns.js`  -  `/reports`

Pick a view, pick columns, pull raw rows, export to file.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/reports/columns` | direct |
| `GET` | `/api/reports/raw` | direct |
| `POST` | `/api/reports/export` | direct |

### Shipment-planning dashboard

`SPDashboard-B50OFi59.js`  -  `/platform/amazon/shipment-planning`

The landing screen for shipment planning: shipment stats, the shipment list, PO items and short supply.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/shipment/po-short-supply/` | direct |
| `GET` | `/api/shipment/shipments/${e?` | direct |
| `GET` | `/api/shipment/shipments/${e}/` | direct |
| `GET` | `/api/shipment/shipments/stats/` | direct |

### Secondary uploader

`SecondaryUploader-CkLbJWEG.js`  -  `upload/secondary`, `/upload/secondary`

Parses a platform's secondary-sales file, then commits via /api/upload/batch.

_No API endpoint of its own._

### Shipment detail

`ShipmentDetail-CPxKwggz.js`  -  `:shipmentId`

One shipment: edit it, submit, approve, reject, dispatch, or delete the draft. Every write in the shipment domain lives here.

| Method | Path | How |
|---|---|---|
| `DELETE` | `/api/shipment/shipments/${e}/` | direct |
| `GET` | `/api/shipment/shipments/${e}/` | direct |
| `PATCH` | `/api/shipment/shipments/${e}/` | direct |
| `POST` | `/api/shipment/shipments/${e}/approve/` | direct |
| `POST` | `/api/shipment/shipments/${e}/dispatch/` | direct |
| `POST` | `/api/shipment/shipments/${e}/reject/` | direct |
| `POST` | `/api/shipment/shipments/${e}/submit/` | direct |

### Shipment list

`ShipmentList-G11ipdat.js`  -  `list`

All shipments with status counts, plus the FC-switching flow (verify, approve/reject a switch, email the request).

| Method | Path | How |
|---|---|---|
| `?` | `/api/shipment/shipments/` | direct |
| `GET` | `/api/shipment/shipments/${e?` | direct |
| `GET` | `/api/shipment/shipments/${e}/` | direct |
| `GET` | `/api/shipment/shipments/${e}/switch/verify/` | direct |
| `GET` | `/api/shipment/shipments/?switch_state=${encodeURIComponent(e)}` | direct |
| `GET` | `/api/shipment/shipments/stats/` | direct |
| `POST` | `/api/shipment/shipments/${e}/switch/verify/` | direct |

### SKU PO pendency

`SkuPoPendency-3UpTl4Uw.js`  -  `primary/sku-pendency`, `sku-pendency`

Per-SKU shortfall against open Amazon POs.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/reports/amazon-po/sku-pendency` | direct |
| `GET` | `/api/reports/amazon-po/sku-pendency/filter-options` | direct |

### SOH / DOH view

`SohDohView-IPXqP2BN.js`  -  `soh-doh`

Platform stock on hand and days of hand, joined to the ASIN catalogue.

Query keys: `platform.sohDohDashboard`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/platform/${e}/soh-doh-dashboard` | direct |
| `GET` | `/api/shipment/asin-catalog/` | direct |

### Choropleth (embedded)

`StateChoroplethMap-MsxmnSDW.js`  -  _embedded, no route of its own_

A second copy of the map component. Loads only the GeoJSON; all figures are passed in as props.

_No API endpoint of its own._

### State-wise sales map (embedded)

`StateSalesMap-ddq0BR5f.js`  -  _embedded, no route of its own_

The map and its drill-downs: state -> cities -> city SKUs, plus an export. Also loads the India GeoJSON, which is NOT an API endpoint.

Query keys: `dashboard.stateSales`, `dashboard.stateSalesDetailCities`, `dashboard.stateSalesDetailCitySkus`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/dashboard/state-sales` | direct |
| `GET` | `/api/dashboard/state-sales/detail/cities` | direct |
| `GET` | `/api/dashboard/state-sales/detail/city-skus` | direct |
| `GET` | `/api/dashboard/state-sales/export` | direct |

### State-wise sales

`StateSalesPage-BkPgGHdT.js`  -  `/state-wise-sales`

Which states/cities/SKUs are selling? A choropleth of India plus drill-downs. The page itself is a thin wrapper; StateSalesMap does the work.

_No API endpoint of its own._

### FC switching modal (embedded)

`SwitchingModal-CaoI47ZF.js`  -  _embedded, no route of its own_

Looks up which FCs are interchangeable for a given FC.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/shipment/fc-switch-group/?fc=${encodeURIComponent(e||` | direct |

### Upload hub

`UploadHub-CFeNTXbc.js`  -  `/uploaders`

The landing page for every data upload. It also owns the generic table editor (columns / data / distinct values / bulk row update) and the bespoke Flipkart-Grocery commit.

| Method | Path | How |
|---|---|---|
| `GET` | `/api/dashboard/table-columns/${e}` | direct |
| `GET` | `/api/dashboard/table-data/${e}` | direct |
| `GET` | `/api/dashboard/table-distinct/${e}/${t}` | direct |
| `POST` | `/api/dashboard/table-rows/${e}` | direct |

### Brand-fund uploader

`ZeptoBrandFundUploader-2nPpFxXZ.js`  -  `upload/brand-fund`

Brand-fund file upload. Parses locally, commits via /api/upload/batch.

_No API endpoint of its own._

### App shell

`index-B7YHcZB3.js`  -  _embedded, no route of its own_

Router, layout, auth gate, notification bell, feature flags and the chatbot drawer. Not a screen but it owns nine endpoints.

Query keys: `auth.featureFlags`, `notifications.all`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/auth/feature-flags` | direct |
| `GET` | `/api/chatbot/conversations` | direct |
| `GET` | `/api/chatbot/conversations/${e}` | direct |
| `GET` | `/api/chatbot/health` | direct |
| `GET` | `/api/notifications` | direct |
| `POST` | `/api/auth/feature-flags/update` | direct |
| `POST` | `/api/chatbot/message` | direct |
| `POST` | `/api/notifications/${e}/mark-read` | direct |
| `POST` | `/api/notifications/mark-all-read` | direct |

### Table counts + expiry alerts hook

`useDashboardData-9fTMrSwQ.js`  -  _embedded, no route of its own_

Shared hook: row counts for a set of tables and their expiry alerts, with per-table fallback when the batch endpoint misses one.

Query keys: `dashboard.expiryAlerts`, `dashboard.tableCounts`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/dashboard/expiry-alerts/${e}` | direct |
| `GET` | `/api/dashboard/table-count/${e}` | direct |
| `GET` | `/api/dashboard/table-counts` | direct |

### Latest-month hook

`useLatestMonthDefault-DiEtTS60.js`  -  _embedded, no route of its own_

Shared hook that asks the server what the newest data month is, so every screen defaults to the same period.

Query keys: `dashboard.latestMonth`

| Method | Path | How |
|---|---|---|
| `GET` | `/api/dashboard/latest-month` | direct |

---
## 3. Dead endpoints - exported by the API module, called by no screen

These 27 service functions exist in the bundled client but no page chunk references
them, directly or through a config table. They are still real server routes (the client
was written against them), but the UI no longer drives them - so live-probe evidence,
not UI evidence, is what should decide whether to publish them.

| Service fn | Method | Path | Reads as |
|---|---|---|---|
| `api.A.refresh` | `POST` | `/api/platform/${e}/month-targets/${t}/refresh` | refresh one month-target row; the UI only refreshes the whole platform |
| `api.G.getDistributor` | `GET` | `/api/sap/distributors/${e}` | single SAP distributor by code |
| `api.G.getDistributors` | `GET` | `/api/sap/distributors` | SAP distributor list (the UI uses the platform-scoped list instead) |
| `api.G.getInventoryWarehouseComparison` | `GET` | `/api/sap/inventory-warehouse-comparison` | SAP stock compared across warehouses |
| `api.G.getItems` | `GET` | `/api/sap/items` | SAP item master |
| `api.G.getPlatformSalesInvoices` | `GET` | `/api/sap/platform-sales-invoices/${e}` | SAP sales invoices for one platform |
| `api.G.getSalesInvoiceLines` | `GET` | `/api/sap/sales-invoice-lines/${e}` | line items of one SAP sales invoice |
| `api.G.getSalesInvoices` | `GET` | `/api/sap/sales-invoices` | SAP sales invoice list |
| `api.G.getStockByWarehouse` | `GET` | `/api/sap/stock-by-warehouse` | SAP stock for one item across warehouses |
| `api.I.getInventoryMatch` | `GET` | `/api/platform/${e}/inventory-match` | match a platform SKU to our inventory |
| `api.I.getPOs` | `GET` | `/api/platform/${e}/pos` | PO list for one platform |
| `api.M.getDetail` | `GET` | `/api/notifications/${e}` | one notification in full |
| `api.V.waterfall` | `GET` | `/api/dashboard/realise-waterfall` | realisation waterfall chart |
| `api.g.deleteConversation` | `?` | `/api/chatbot/conversations/${e}` | delete a chatbot conversation (DELETE) |
| `api.o.amazonPOSummary` | `GET` | `/api/reports/amazon-po/summary` | Amazon PO summary tile |
| `api.o.fcs` | `GET` | `/api/master/fcs` | fulfilment-centre master |
| `api.o.products` | `GET` | `/api/master/products` | product master |
| `api.y.getCategoryLitres` | `GET` | `/api/dashboard/category-litres` | category volume in litres |
| `api.y.getInventoryCharts` | `GET` | `/api/dashboard/inventory-charts` | inventory chart bundle |
| `api.y.getPrimaryPoLitres` | `GET` | `/api/dashboard/primary-po-litres` | primary PO volume in litres |
| `api.y.getStateSalesDetail` | `GET` | `/api/dashboard/state-sales/detail` | state sales detail (the UI calls the cities/city-skus variants instead) |
| `api.y.getStateSalesDetailOptions` | `GET` | `/api/dashboard/state-sales/detail/options` | filter options for state sales detail |
| `api.y.updateTableRow` | `POST` | `/api/dashboard/table-row/${e}` | single-row table edit (the UI uses the bulk variant) |
| `shipmentAPI.c.updateItem` | `PATCH` | `/api/shipment/shipments/${e}/items/${t}/` | edit one line of a shipment |
| `shipmentAPI.i.list` | `GET` | `/api/shipment/appointment-commits/` | list committed appointment quantities; the screen only imports the commits *import* |
| `shipmentAPI.r.importCommits` | `POST` | `/api/upload/batch` | import appointment commits via /api/upload/batch |
| `shipmentAPI.s.list` | `GET` | `/api/shipment/po-items/` | paginated PO items; every caller uses `loadAll` (`no_paginate=true`) instead |

Two of these are worth calling out. `api.o.products` and `api.o.fcs` are the **product**
and **fulfilment-centre masters** (`/api/master/products`, `/api/master/fcs`) - generically
useful endpoints that the UI simply stopped calling. And `ship:r.importCommits` is a second,
unused caller of `/api/upload/batch`; the live caller is the shared uploader helper (section 4).

---

## 4. Endpoints that live outside both service modules

These are called with a raw `fetch` from a page chunk, not through `api-De44ElJm.js` or
`shipmentAPI-DKVOXJWL.js`. **Five of the six are absent from the registry-based scrape**
(`lens1-registry.jsonl`), from `reconciled.json` and from the shipped 138-endpoint spec.
If the CLI is regenerated only from the service modules, these are the endpoints it will miss.

| Method | Path | Where | What it does |
|---|---|---|---|
| `POST` | `/api/auth/login` | AuthContext-DP7l1KMt.js | Login. Body `{email,password}`, returns `{token,refresh}`. |
| `POST` | `/api/auth/refresh` | api-De44ElJm.js (internal, not a service object) | Silent JWT refresh, fired on any 401. Body `{refresh}`. |
| `POST` | `/api/upload/batch` | uploaderUtils-D0yunz1d.js | **The generic ingest behind every platform uploader.** Body `{table, data, unique_key, upsert, expected_platform_format?, source_platform_format?}`. |
| `POST` | `/api/upload/delete-by-date` | uploaderUtils-D0yunz1d.js | Bulk row delete over a date range - `{table, date_column, from_date, to_date, end_date_column?}`. Destructive; used by the re-upload flow. |
| `POST` | `/api/upload/fk-grocery-master` | UploadHub-CFeNTXbc.js, FkGroceryUploader-qAJP3aLc.js | Flipkart Grocery master commit - `{data, upsert}`. Bypasses `/api/upload/batch`. |
| `POST` | `/api/upload/flipkart-grocery/reprocess` | FkGroceryUploader-qAJP3aLc.js | Re-enrich already-loaded Flipkart Grocery rows from master sheet + landing rates. Optional `{month,year}`. |

`/api/upload/batch` is the single most important of these operationally: it is how
every ads, brand-fund, secondary, inventory and primary uploader actually writes data.
It is read-only-hostile - it writes - so under RULE 0 it must not be published as a
CLI write command, but it must be *known about*, because it is the mechanism behind
nearly every 'the numbers changed' question.

---

## 5. Query keys with no endpoint behind them

| Query key | Screen | What it really is |
|---|---|---|
| `` [`india-geojson`] `` | StateSalesMap, StateChoroplethMap | **Not an API call.** Fetches `/geo/india_states.geojson`, and if that fails falls back to two public GitHub raw URLs (`gist.githubusercontent.com/jbrobst/...`, `raw.githubusercontent.com/Subhash9325/...`). Worth flagging: a missing static asset makes the app phone a third party. |
| `` [`ads-trend-off`] `` | AdsDashboardShell | Placeholder key used when the parent page supplies no daily/trend fetcher. Not a resource. |

No query key names a JIVO resource that has no endpoint. Every named resource in the
key factory resolves to a real path - including `masterSheet.skuLookup`, which is not a
`/sku-lookup` route but a search against `/api/upload/master-sheet?search=...`.

### Query-key vocabulary the UI defines but never uses

The key factory in `api-De44ElJm.js` declares 97 keys; 15 are referenced by no chunk.
They line up almost exactly with the dead endpoints above, which is a good cross-check
that those really are dead and not just indirection this scan missed:

`amazonReports.amazonPOSummary`, `auth.me`, `auth.permissions`, `dashboard.categoryLitres`,
`dashboard.inventoryCharts`, `dashboard.primaryPoLitres`, `dashboard.stateSalesDetail`,
`dashboard.stateSalesDetailOptions`, `dashboard.tableData`, `platform.inventoryMatch`,
`platform.pos`, `realise.waterfall`, `sap.distributor`, `sap.distributors`,
`sap.inventoryWarehouseComparison`.

(`auth.me` and `auth.permissions` are the exception: the endpoints *are* live, but the
home screen spreads the factory key into a longer ad-hoc key rather than using it as-is.)

---

## 6. Hook inventory - the shape of the data layer

134 react-query registrations across 50 chunks:

| Hook | Count |
|---|---|
| `useQuery` | 113 |
| `useMutation` | 16 |
| `useQueries` | 5 |

**Most writes are not mutations.** Only 16 of the app's 54 non-GET service functions
(49 POST, 2 PATCH, 1 DELETE, 2 unresolved verb) go through `useMutation`, and they cluster
in seven chunks:

| Chunk | Mutations |
|---|---|
| MonthlyTargetsDashboard | save call-centre target, set primary target, refresh targets dashboard |
| PlatformMonthlyTargets | create target, update target, refresh platform |
| PlatformPrimaryMonthlyTargets | create, update, refresh platform |
| index (app shell) | update feature flags, mark all notifications read, mark one read |
| PlatformLandingRate | add landing rate, update landing rate |
| AmazonUploadReports | upload a report |
| AppointmentUploader | upload an appointment file |

Everything else that writes - creating and submitting a shipment, approving / rejecting /
dispatching / deleting one, the whole master-sheet, ADS-master and pincode CRUD, every
bulk-upsert, and the `/api/upload/batch` ingest behind the platform uploaders - is a plain
`async` function called from an event handler, followed by a manual
`queryClient.invalidateQueries(...)`. So **you cannot enumerate this app's writes by looking
for mutations**; the writes are the `POST` / `PATCH` / `DELETE` rows in the tables above.

Five registrations use `useQueries` (fan-out): the home dashboard fires one query per ad
platform for its ads snapshot, one per platform for the secondary delivered-value card, and
one per year for the YoY SKU comparison; the primary/secondary summary fires one per platform slug.

### Where the query keys come from

Most keys come from a single factory object in `api-De44ElJm.js`, grouped by domain -
`auth`, `dashboard` (24 keys), `realise`, `notifications`, `masterSheet`, `platform` (33 keys),
`landingRate`, `monthlyTargets`, `primaryMonthlyTargets`, `amazonUploads`, `amazonReports`, `sap` (12 keys).
Platform keys are shaped `["platform", slug, "<dashboardName>", params]`, which is the
cleanest available statement of what each `/api/platform/{slug}/...` endpoint is *called*
by the people who built it.

A minority are written inline at the call site, usually where a screen composes something
the factory does not model: `` [`summary-ads`,slug,params] ``, `` [`summary-brandfund`,...] ``,
`` [`blinkit-summary-report`,...] ``, `` [`call-center-targets`,...] ``, `` [`meta-dashboard`,...] ``,
`` [`lead-time-report`,...] ``, `` [`penetration-drill`,...] ``, `` [`report-columns`/`report-rows`,...] ``,
`` [`shipment`,`sap-inventory`,...] ``, `` [`shipment`,`asin-catalog`] ``,
`` [`platformExpiryPoDetail`/`platformExpiryPoItems`,...] ``, `` [`notification-inventory-doh`,...] ``.

### The four screens whose endpoints are chosen at runtime

These are the ones a naive scan gets wrong, so they are worth stating plainly:

1. **Home dashboard ads snapshot** (`Dashboard-Ci-nVmGI.js`) - a table `{amazon, blinkit,
   swiggy, zepto, bigbasket, flipkart}` maps each platform to its ads endpoint
   (`/api/platform/{slug}/ads-dashboard`, `.../blinkit-ads-dashboard`, `.../swiggy-ads-dashboard`,
   `.../zepto-ads-dashboard`, `.../bigbasket-ads-dashboard`, `.../flipkart-ads-dashboard`)
   and fires all six at once.
2. **Platform overview** (`PlatformDashboard-Df76y2uF.js`) - two lookup tables, one for ads
   and one for brand fund, pick the right endpoint for whichever platform you are on;
   brand fund exists only for blinkit, swiggy and zepto.
3. **Primary/Secondary summary** (`PlatformSummaryDashboard-1tTM8G_m.js`) - one config object
   per mode. Primary uses `/api/platform/{slug}/primary-dashboard` + `/api/platform/primary-summary`
   + `/api/platform/primary-summary-version`; secondary uses `/api/platform/{slug}/sec-dashboard`
   + `/api/platform/secondary-summary-version`. The `-version` endpoints are cheap polls whose
   only job is to tell the client when to invalidate the expensive ones.
4. **Master sheet manager** (`MasterSheetManager-CWEDZOOq.js`) - one config table maps the route
   to one of three CRUD services: master sheet, ADS master, pincode mapping. All 18 of its
   endpoints are reached as `config.api.<fn>`, never as a named service call.

---

## 7. Counts

| | |
|---|---|
| Service functions with a resolvable path | 204 (167 in `api-De44ElJm.js`, 37 in `shipmentAPI-DKVOXJWL.js`) |
| Distinct normalised paths from the service modules | 195 |
| Verb split across the 204 service functions | 150 GET, 49 POST, 2 PATCH, 1 DELETE, 2 unresolved |
| Endpoints called outside both service modules | 6 (5 of them new) |
| Service functions no chunk calls | 27 |
| react-query registrations | 134 (`useQuery` 113, `useMutation` 16, `useQueries` 5) |
| Chunks that register at least one query | 50 |
| Named page chunks with at least one endpoint | 78 |
| Query-key factory entries | 97 (15 unused) |
| Routes in the router | 124 (92 to a lazy-loaded screen, the rest redirects/layouts) |

