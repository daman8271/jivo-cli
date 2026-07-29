# Subsystem: field-sales-entry

## 1. Overview

The **field-sales-entry** subsystem is the transactional heart of JIVO's DSR (Daily Sales Report / Sales Force Automation). It captures what a field **Sales Officer (SO)** or **Promoter** does at each retailer visit during a daily "beat":

- A **visit** is one row in `tbl_SalesReport` (the header) — who (personId), where (retailerId + geo hierarchy state/zone/area/subArea), which distributor supplied, GPS start location, visit status/outcome, timings, and approval/duplicate-check flags.
- The **line items** of that visit hang off the header by `salesId`: normal products sold (`tbl_ProductsSold`), scheme/offer products (`tbl_SchemeProductsSold`), retailer's on-shelf stock counted (`tbl_retailerStock`), and shelf/display photos (`tbl_shelfImages`).
- **Gifts** (trade-scheme freebies) are defined in `tbl_Gift`, targeted per retailer in `tbl_GiftMapwithRetailer`, and issued at a visit in `tbl_saveGift`.
- Supporting/audit tables: `saleLog` (per-day sync heartbeat), `tbl_SoAppSalesJsonLog` (raw mobile-app payload as JSON, the source of truth before parsing), `tbl_SalesActionLog` (approve/reject actions), `tbl_SalesProductStockEditLog` (back-office corrections to punched quantities), `tbl_AllSalesData` (call-centre confirmation of orders).
- `tbl_CC_Orders` / `tbl_CC_OrderDetails` are a separate **call-centre order-taking** channel (telesales), lightly used.

This records **secondary sales** (distributor → retailer) — see `salesType:"secondary"` in the raw JSON.

## 2. Per table

### tbl_SalesReport — visit header (2,128,082 rows, PK `salesId`)
One row per retailer visit / sale-attempt. Core columns:
- `salesId` PK; `date` (visit date); `personId`→SO/promoter; `retailerId`→shop visited.
- Geo denormalized both as IDs and names: `stateId/state`, `zoneId/zone`, `areaId/area`, `subAreaId/subArea`; `distId/distributor` = supplying distributor.
- `personName`, `retailerName` cached for reporting.
- `status` (nvarchar) — visit outcome: `DONE`, `ALREADY STOCKED`, `OWNER NOT AVAILABLE`, `MEETING`, etc.
- `completionStatus` (bit) — beat/visit completed flag.
- `totalQuantity` (bottles), `totalPieces` (cases/units), `totalPrice` — visit totals.
- `startLatitude`/`startLongitude` — GPS at check-in; `timeDuration` (mm:ss spent); `timestamp` = device sale time; `CreatedOn` = server insert.
- `parentId/parentName/parentType` — reporting manager (e.g. `parentType='ASM'`).
- `simnumber`, `devicename` — device fingerprint (anti-fraud).
- Scheme/approval: `schemeApprovedBy`, `ApprovedBy`, `allowed` (bit — geofence pass), `dueDate`, `deliverydate`, `discountRate`, `discountAmount`.
- `SoOrderStatus` (varchar 5) — e.g. `D` (delivered/dispatched).
- Duplicate control: `duplicacyStatus` (int; 2 seen in samples), `duplicacyApprovedBy`.
- Soft delete: `deleted` (1=deleted), `deletedBy`, `deletionDate`, plus `tempDeleted`. **Filter `deleted=0`** (deleted is nullable → use `(deleted IS NULL OR deleted=0)` or `ISNULL(deleted,0)=0`).
- `imagePath` — visit photo filename (pattern `person-day-month-yy-epoch.jpg`).

### tbl_ProductsSold — sold line items (685,525 rows, PK `Id`)
Products punched as sold at a visit. `salesId`→header; `productId`→`tbl_item.itemId`; `productName` cached; `pieces` (cases), `productQuantity` (bottles/case), `totalQuantity` (bottles = pieces×qty); `cost`/`totalCost`, `price`/`totalPrice`. `itemType` (int) = product category code. `isScheme` (bit) marks a scheme placeholder row. `isOfferAvailed` (bit). Distributor feedback loop: `DistId`, `DistFeedback`, `DistFeedbackStatus`, `DistFeedbackcreatedDate`. `UOM` unit-of-measure code. Soft delete: `deleted/deletedBy/deletionDate`.

### tbl_SchemeProductsSold — scheme line items (423,746 rows, PK `Id`)
Same shape as tbl_ProductsSold but for **scheme/offer** products (combo packs, e.g. "1LTR + 1LTR Coldpress"). `salesId`, `productId`, `productName` (sometimes literal "No Item"), `pieces`, `productQuantity`, `totalQuantity`, `cost/totalCost`, `UOM`, `itemType`. Soft delete cols present. `CreatedBy` = personId string.

### tbl_retailerStock — shelf/stock audit (585,587 rows, PK `id`)
Retailer's existing stock counted during the visit. `salesId`→header; `itemId`→`tbl_item.itemId`; `stock` (float qty); `stockType` (nvarchar) — e.g. `"Second"` (secondary/own stock vs competitor).

### tbl_shelfImages — shelf photos (2,956 rows, no PK)
Display/shelf photos captured at visit. `salesId`→header, `shopId`→retailer, `personId`→SO, `img` (filename), `createdOn`. Note many rows have `salesId=0` and null person/shop (early data).

### saleLog — daily sync heartbeat (2,407,434 rows, no PK)
High-volume log: `saleId` (int, not unique — repeats), `personId`, `createdOn`. Appears to be a per-person per-sale sync/upload marker (not the sale itself).

### tbl_SoAppSalesJsonLog — raw mobile payload (5,267 rows, PK `id`)
The **untouched JSON** the SO app posted before parsing into SalesReport/ProductsSold. `rawJson` holds the full object: personId, shopId, saleDateTime, status, lat/long, battery, GPS accuracy, salesType (`secondary`), distId, distance, deliveryDate, allowed, simnumber, devicename, `items[]` (itemId/order/stock/cost), `schemes[]`. `personId` column often null (value lives inside JSON). `imageName`, `createdOn`. Recent (2026) — this is the current ingestion audit trail; good for debugging what the device actually sent.

### tbl_SalesActionLog — approval action log (598 rows, PK `id`)
Back-office actions on a sale. `action` (`APPROVE`, likely `REJECT`), `salesId`, `retailerId`, `details` (e.g. `approvedBy=71`), `performedBy`/`performedByName`, `performedOn`.

### tbl_SalesProductStockEditLog — quantity-correction audit (129 rows, PK `LogId`)
Back-office corrections to punched quantities. `SourceTable` (`tbl_ProductsSold`), `SalesId`, `ProductSoldId`, Old/New `ProductId`/`ProductName`, Before/Changed/After `Pieces` and `Quantity`, `ChangedBy`, `ChangeReason` (free text), `ChangedOn`, `PersonId`, `DistId`. Compliance trail for edits (e.g. "had to fill 40 pieces but filled 4").

### tbl_Gift — gift/scheme catalog (15 rows, PK `giftId`)
Defines gift tiers by cumulative-sale range. `giftName` (e.g. "2 bottle Canola"), `giftRange` (text "125-249"), `giftStartRange`/`giftEndRange` (int bounds), `giftShowRange`, `giftAllow` (1=active), `createdDate`, `createBy`.

### tbl_GiftMapwithRetailer — gift eligibility per retailer (2,837 rows, PK `Id`)
Which gift a retailer qualifies for. `retailerId`→shop, `giftId`→tbl_Gift, `giftAvg` (running avg qty), `totalqty` (cumulative qty), `isActive` (bit), `createdate`.

### tbl_saveGift — gift issued at a visit (34,236 rows, PK `Id`)
Actual gift given during a sale. `salesId`→header, `retailerId`, `personId`→SO, `giftId`+`giftName`+`giftrange`, `totalQty` (cumulative), `QtyProduct` (qty given this time), `active` (1=live, soft-delete flag), `remark`, `createdDate`.

### tbl_CC_Orders — call-centre order header (5 rows, PK `id`)
Telesales channel (barely used / test data). `salePersonId`→SO, `custId`/`custName`/`custAddress`/`custContactNo1-2`, `createdBy`/`callerName`, `status` (`Open`, `Fake`), `cancelled` (0/1), `isSeen`, `createdOn`/`updatedOn`, `comment`/`remarks`.

### tbl_CC_OrderDetails — call-centre order lines (5 rows, PK `id`)
`orderId`→tbl_CC_Orders.id, `productId`→item, `productName`, `pieces`, `productQuantity`, `totalQuantity`, `cost`/`totalCost`, `itemType`.

### tbl_AllSalesData — call-centre order confirmation (12,185 rows, PK `SalesId`)
Tele-verification of field orders. `SalesId`→tbl_SalesReport.salesId, `Sales_PId` (products-sold ref), `Selection` (`Delivered`, `UnConfirmed`), `Comment` (call notes), `lastCalledDate`, `userid`/`userName` (caller). Confirms whether a punched order was really placed/delivered.

## 3. Linkages

- `personId` / `salePersonId` / `performedBy` / `ChangedBy` / `createBy` → **tbl_salesperson.personId** (SO/promoter/back-office user).
- `retailerId` / `shopId` / `custId` → **tbl_retailers.retailerId** (shop visited).
- `distId` / `DistId` → **distributor tables** (supplying distributor / super-stockist).
- `productId` / `itemId` → **tbl_item.itemId**; `productName` is a cached copy.
- Geo: `stateId/zoneId/areaId/subAreaId` → the location-hierarchy tables (beat geography). No explicit `beatId` column here — beat is resolved via person+geo; `beatId`→**tbl_beats.beatId** where present in sibling tables.
- Header→lines fan-out on **`salesId`**: `tbl_SalesReport.salesId` = `tbl_ProductsSold.salesId` = `tbl_SchemeProductsSold.salesId` = `tbl_retailerStock.salesId` = `tbl_shelfImages.salesId` = `tbl_saveGift.salesId` = `tbl_SalesActionLog.salesId` = `tbl_SalesProductStockEditLog.SalesId` = `tbl_AllSalesData.SalesId`.
- Gift chain: `tbl_saveGift.giftId` / `tbl_GiftMapwithRetailer.giftId` → `tbl_Gift.giftId`; `tbl_GiftMapwithRetailer.retailerId` → tbl_retailers.
- Promoter variants (`tbl_SalesReportPromoter`, `tbl_ProductsSoldPromoter`) and staging (`*Temp`) mirror the SO tables with identical join keys.
- Monthly targets join elsewhere on **personId + month/year** (not in this subsystem).

## 4. Portal mapping

Back-office DSR admin portal menu pages that read these tables:
- **Sales Report / Daily Sales** page → `tbl_SalesReport` (+ drill-down to `tbl_ProductsSold`, `tbl_SchemeProductsSold`, `tbl_retailerStock`, `tbl_shelfImages`). Primary field-sales grid, filtered by SO/date/geo/distributor.
- **Sales Approval / Duplicate-check** page → `tbl_SalesReport` (duplicacyStatus/allowed/ApprovedBy) writing audit to `tbl_SalesActionLog`.
- **Stock-edit / Quantity-correction** admin page → `tbl_SalesProductStockEditLog` (over `tbl_ProductsSold`).
- **Gift / Scheme management** page → `tbl_Gift`, `tbl_GiftMapwithRetailer`; issued gifts appear under a visit via `tbl_saveGift`.
- **Call-Centre / Order-confirmation** page → `tbl_AllSalesData` (order verification) and `tbl_CC_Orders`/`tbl_CC_OrderDetails` (telesales entry).
- **App-sync / Debug** (internal) → `tbl_SoAppSalesJsonLog`, `saleLog`.

## 5. Proposed dsr commands

```
# 1) visits — list field visits for a period / SO / retailer
dsr visits --from <date> --to <date> [--salesperson <personId>] [--retailer <retailerId>] [--status DONE]
#   Backing:
SELECT salesId, date, personId, personName, retailerId, retailerName,
       distributor, status, totalPieces, totalQuantity, totalPrice,
       startLatitude, startLongitude, timeDuration
FROM tbl_SalesReport
WHERE ISNULL(deleted,0)=0
  AND date >= @from AND date < @to           -- note: 'date' col; sentinel 1899-12-30 = empty
  [AND personId = @salesperson] [AND retailerId = @retailer] [AND status = @status]
ORDER BY date, personId;

# 2) visit-lines — full detail of one visit (products + schemes + stock + gifts)
dsr visit-lines --sales-id <salesId>
SELECT 'sold'   AS kind, productId, productName, pieces, totalQuantity, totalCost
FROM tbl_ProductsSold        WHERE salesId=@id AND ISNULL(deleted,0)=0
UNION ALL
SELECT 'scheme', productId, productName, pieces, totalQuantity, totalCost
FROM tbl_SchemeProductsSold  WHERE salesId=@id AND ISNULL(deleted,0)=0
UNION ALL
SELECT 'stock',  itemId, stockType, NULL, stock, NULL
FROM tbl_retailerStock       WHERE salesId=@id
UNION ALL
SELECT 'gift',   giftId, giftName, QtyProduct, totalQty, NULL
FROM tbl_saveGift            WHERE salesId=@id AND active=1;

# 3) so-productivity — per-SO daily visit + volume rollup
dsr so-productivity --from <date> --to <date> [--salesperson <personId>]
SELECT personId, personName, COUNT(*) AS visits,
       SUM(CASE WHEN status='DONE' THEN 1 ELSE 0 END) AS productive_visits,
       SUM(ISNULL(totalQuantity,0)) AS bottles, SUM(ISNULL(totalPrice,0)) AS value
FROM tbl_SalesReport
WHERE ISNULL(deleted,0)=0 AND date >= @from AND date < @to
  [AND personId = @salesperson]
GROUP BY personId, personName ORDER BY visits DESC;

# 4) gift-issued — gifts given in the field, by SO/retailer
dsr gift-issued --from <date> --to <date> [--salesperson <personId>] [--retailer <retailerId>]
SELECT g.salesId, g.personId, g.retailerId, g.giftName, g.QtyProduct, g.totalQty, g.createdDate
FROM tbl_saveGift g
WHERE g.active=1
  AND g.createdDate >= @from AND g.createdDate < @to
  [AND g.personId = @salesperson] [AND g.retailerId = @retailer]
ORDER BY g.createdDate;

# 5) order-confirm — call-centre confirmation status of punched orders
dsr order-confirm --from <date> --to <date> [--status UnConfirmed]
SELECT a.SalesId, a.Selection, a.Comment, a.lastCalledDate, a.userid,
       s.personName, s.retailerName, s.distributor
FROM tbl_AllSalesData a
JOIN tbl_SalesReport s ON s.salesId = a.SalesId AND ISNULL(s.deleted,0)=0
WHERE a.lastCalledDate >= @from AND a.lastCalledDate < @to
  [AND LTRIM(RTRIM(a.Selection)) = @status]
ORDER BY a.lastCalledDate;
```

**Caveats:** `deleted` is nullable → always `ISNULL(deleted,0)=0` (or `active=1` for gifts). Date sentinel `1899-12-30` means empty — exclude it in range filters. `pieces` = cases, `totalQuantity` = bottles (per-bottle, not per-carton). `personName`/`productName`/geo names are denormalized caches — trust IDs for joins. Promoter data lives in the parallel `tbl_SalesReportPromoter`/`tbl_ProductsSoldPromoter` tables (not covered here).
