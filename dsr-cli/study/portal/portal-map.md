# DSR portal — route & endpoint map (Phase 3)

Live-crawled 2026-07-30 as `daman` on `http://103.89.45.75:90`. IIS 10 / ASP.NET
MVC 5. **This tool is GET-only against the portal (RULE 0);** write-capable pages
are listed for completeness but are never POSTed to.

## Auth
- Login: **GET** `/Login/CheckLogin?user=<u>&password=<p>` → returns literal
  `window.location = '../'` on success (else `'Oops.. Wrong Credentials!!'`).
  Sets an HttpOnly forms-auth cookie; every other page 302s to `/Login/Login`
  without it. Logout: `/Login/LOGOUT`. (`dsr portal check` does this.)

## Read report pages (GET → rendered view; backing tables cross-ref the vault)
| Route | Shows | Backing tables |
|---|---|---|
| `/Home/Index` (`/`) | Dashboard: month litres, top/bottom SOs, item & location split | tbl_SalesReport, tbl_ProductsSold |
| `/SalesReport/SOAttendance`, `/AttendanceReport` | SO attendance | tbl_salesPersonAttendance |
| `/SalesReport/PromoterAttendance` | promoter attendance | tbl_SalesReportPromoter |
| `/SalesReport/AllSales`, `/SaleOverView`, `/SalesReportByState` | secondary sales | tbl_SalesReport, tbl_ProductsSold |
| `/SalesReport/RetailerReport`, `/RetailerStockDetails` | retailer sale/stock | tbl_retailers, tbl_retailerStock |
| `/SalesReport/UnassignedShopReport`, `/UncoveredShops` | coverage gaps | tbl_BeatShopMap, tbl_SalesReport |
| `/salesReport/ComparisonReport`, `/NegativeReport`, `/RetailerWithLocation`, `/approvalduplicacy` | analytics | tbl_SalesReport, tbl_geoLocation |
| `/ThirdSaleReport/*` (DailyPersonSalesReport, PromoterStoreWiseSale, PromoterStateWiseStore, NewPromoters, Selfie) | promoter reports | tbl_SalesReportPromoter, tbl_ProductsSoldPromoter |
| `/Distributor/StockReport`, `/DistributorStockReport`, `/DetailedStockReport` | distributor stock | tbl_distStockProducts, tbl_distributorStock |
| `/Beats/Index`, `/GetBeatsAssign`, `/beatReport/*` | beats & assignments | tbl_beats, tbl_BeatAssign, tbl_BeatShopMap |
| `/geoLocation/Index`, `/LocationReport`, `/uncovered` | GPS tracking | tbl_geoLocation |
| `/SalesPerson/Index` | salesperson master | tbl_salesperson |
| `/Item/Index`, `/ItemType`, `/UOM` | item master | tbl_item, tbl_itemType, tbl_UOMMaster |
| `/Retailer/index`, `/PromoterShop`, `/SoPromoterMap`, `/getAssignedShopsDetail` | retailer & promoter maps | tbl_retailers, tbl_promoterShopMap, tbl_soPromoterMap |
| `/Home/DeviceTraker` | device tracker | deviceTracker, tbl_userGcmMap |
| `/Home/TACalculateNew` | travel allowance | tbl_TA_* |
| `/Login/GiftRecord` | gift records | tbl_Gift, tbl_saveGift |
| `/SOApproval/Index`, `/MISApproval/Index` | approval queues (GET lists) | tbl_SalesReport (approvedStatus) |

## Read data endpoints (AJAX, GET/JSON — wrapped by `dsr portal`)
- `/Home/MonthlySale` `?fromdate&todate` → per-month `totalQuantity` (litres). **⚠ portal bug:** returns a garbage March value (~1.0e13).
- `/Home/GetItemWiseSale` `?month=July,2026` → item-wise pieces/quantity.
- `/Home/GetTopSos`, `/Home/GetBottomSos`, `/Home/GetLocationWiseSale` → dashboard splits.
- `/geolocation/getUnapprovedSalesCount` (GET) → count of unapproved sales.
- `/home/searchMessagesFromAndroid` → android message search.

## Write-capable pages (⚠ NEVER invoked — GET renders the form, POST would mutate)
`/Sales/Create2` (sales entry) · `/Beats/Create` · `/Home/AddZone` · `/Item/*` create ·
`/Permission/AddPage`, `/Permission/Permission`, `/LocationPermission/Index` ·
`/PrimarySalesUpload/Index` (file upload) · `/SOApproval` & `/MISApproval` approve actions ·
`/UpdateLocation/Index`. The tool only ever GETs these to read; it issues no POST.
