# Subsystem: primary-sales

## 1. Overview

Primary sales in JIVO's DSR is the **upstream leg of distribution**: goods moving from JIVO (the company / super-stockist / SAP invoicing) **into distributors/super-stockists**, as distinct from secondary sales (distributor → retailer). This subsystem captures three related flows:

- **Distributor primary stock** entries logged in the field by a Sales Officer (SO) or Promoter — a visit-style record ("I dropped stock at this distributor today") with GPS, approval and receipt tracking (`tbl_distributorPrimary` header + `tbl_distPrimaryProducts` lines).
- **Primary sales transactions** (`tbl_primary_sales`) — bulk/dispatch sales lines, often uploaded in batch ("PALLAVI FOR DIST STOCK"), moving items between distributor stock points / retailers with bill and receive dates.
- **Order-file ingestion** from distributors: raw uploaded distributor order spreadsheets (`tbl_distorders`) plus a name→ID mapping table (`tbl_distmappings`) that resolves free-text retailer/SKU names in those files to DSR IDs.
- **SAP sales mirror** (`sap_sales_log`) — a flat pull of SAP B1 A/R invoice lines (docnum, itemcode, qty, price, channel group) used to reconcile DSR-recorded primary sales against the SAP books.

Together they let JIVO track what was actually pushed into the distribution channel, approve/reconcile it, and tie DSR field activity back to SAP invoicing.

## 2. Tables

### tbl_distributorPrimary — 222 rows — PK `distStockId`
Header for a field-logged primary stock/dispatch event at a distributor.
- `distStockId` — PK, header id (referenced by product lines and by `tbl_primary_sales.from/to_distStockId`).
- `distId`, `distName`, `distAddress` — the distributor (distId → distributor tables); name/address denormalized.
- `personId`, `personName`, `personType` — the field user who logged it; `personType` = `SO` (Sales Officer) or Promoter. `personId` → `tbl_salesperson.personId`.
- `stockDate` — when stock was recorded.
- `lotitude`/`longitude` (sic) — GPS of the capture (often null).
- `completionStatus` (int, not-null) — workflow state of the entry (e.g. 1 = complete/saved).
- `approved`/`approvedBy`/`approvedOn` — approval flags; `approved` 0 = pending.
- `received` (bit) — whether the distributor confirmed receipt.
- `dueDate` — payment/credit due date.
- `discountRate`/`discountAmount` — header-level discount.
- `remarks` — free text.
- `deleted`/`deletedby`/`deletedOn` — soft delete; `deletedOn` uses 1899-12-30 sentinel when live. Filter `deleted = 0`.

### tbl_distPrimaryProducts — 774 rows — PK (none listed; keyed by `distStockId`+`productId`)
Line items for a `tbl_distributorPrimary` header.
- `distStockId` — FK → `tbl_distributorPrimary.distStockId`.
- `productId`, `productName` — item (productId → `tbl_item.itemId`); name denormalized.
- `productQuantity` — qty per box/unit; `boxes` — number of boxes.
- `totalPieces`, `totalQuantity` — computed totals (often null in samples).
- `productMrp`, `totalMrp` — MRP value fields (often null).

### tbl_primary_sales — 12,542 rows — PK `id`
Individual primary-sales transaction lines (the main volume table).
- `id` — PK line id; `salesid` — groups lines into one document/upload batch.
- `date` — transaction date; `bill_date`, `receive_date` — invoice / goods-received dates; `bill_number` — external bill ref.
- `from_retailerid` / `to_retailerid` — source/destination party (→ `tbl_retailers.retailerId`; distributors are stored as retailer records here). Sample shows only `to_retailerid` populated (stock going *to* a party).
- `from_distStockId` / `to_distStockId` — link to `tbl_distributorPrimary` stock points (often null).
- `itemid`, `itemname` — item (itemid → `tbl_item.itemId`).
- `quantity`, `price` — line qty and rate (price often null).
- `uploaded_by` — free-text source of the row (e.g. "PALLAVI FOR DIST STOCK") indicating batch uploads.
- `deleted`/`deletedBy`/`deletedOn` — soft delete (nullable; treat null or 0 as live). Filter `deleted = 0 OR deleted IS NULL`.

### tbl_distorders — 1,315 rows — PK `id`
Raw distributor order/scheme lines ingested from uploaded Excel files (channel/scheme reimbursement data).
- `id` — PK; `distid` — distributor (→ distributor tables).
- `retailername`/`retailerid` — free-text retailer name + resolved id (id stored as varchar).
- `sku`/`itemid` — free-text SKU description + resolved item id (both varchar; itemid often null → unresolved).
- `processstatus` — e.g. `RETR` (retrieved/processed marker).
- `quantity`, `free`, `rate`, `amount` — order economics incl. free/scheme qty.
- `liters`, `litersfree` — volume equivalents.
- `datefrom`/`dateto` — scheme/display period (sample SKUs read "DISPLAY MONTH OF MAY" — trade-scheme display claims).
- `loadingdate`, `loadingid`, `orderid`, `lineid`, `filename` — batch/ingest provenance (source spreadsheet + loading run).

### tbl_distmappings — 1,050 rows — PK (none; lookup table)
Name-resolution map used when ingesting `tbl_distorders`-style files: turns free-text names into DSR IDs, scoped per distributor.
- `applyto` — what the mapping resolves, e.g. `RETR` (retailer). Likely also item/product scopes.
- `distid` — distributor this mapping belongs to (→ distributor tables).
- `inputvalue` — the free-text name from the file (e.g. "AGGARWAL DEPARTMENTAL STORE").
- `outputvalue` — the resolved DSR id (e.g. retailerId "6163").
- `status` — mapping state, e.g. `B` (bound/approved).

### sap_sales_log — 8,009 rows — PK (none; flat SAP mirror/log)
Flat mirror of SAP B1 A/R invoice lines, for reconciling DSR primary sales against the SAP books.
- `docnum`, `linenum` — SAP invoice number + line.
- `docdate`, `docduedate`, `extradays` — invoice date, due date, extra credit days.
- `cardname`, `address` — SAP business partner (customer) name/address.
- `itemcode`, `itemname` — SAP item (e.g. `FG0000065` Pomace Olive) — SAP FG codes, not DSR itemIds.
- `quantity`, `Price` — invoiced qty and unit price.
- `PymntGroup` — payment terms (e.g. "Net-30", "Advance/Cash/0 Days").
- `U_UNE_GRP1` — sales channel group: `E-COMMERCE`, `MT` (Modern Trade), `GT` (General Trade).
- `u_une_grp2` — sub-channel / customer type: `Swiggy`, `Wal-Mart`, `Distributor`.
- `U_SchemeAgst`, `U_SchemeBase` — SAP scheme UDFs (usually null).
- `comments` — line comments.

## 3. Linkages

- `tbl_distributorPrimary.personId` → `tbl_salesperson.personId` (the SO/Promoter who logged the primary stock).
- `tbl_distributorPrimary.distId`, `tbl_distorders.distid`, `tbl_distmappings.distid` → distributor tables (distributor master; note distributors also appear as retailer records elsewhere).
- `tbl_distPrimaryProducts.distStockId` → `tbl_distributorPrimary.distStockId` (header↔line).
- `tbl_distPrimaryProducts.productId`, `tbl_primary_sales.itemid` → `tbl_item.itemId`.
- `tbl_primary_sales.from_retailerid` / `to_retailerid`, `tbl_distorders.retailerid`, `tbl_distmappings.outputvalue` (when `applyto='RETR'`) → `tbl_retailers.retailerId`.
- `tbl_primary_sales.from_distStockId` / `to_distStockId` → `tbl_distributorPrimary.distStockId`.
- `sap_sales_log` joins to DSR only by **soft keys** (cardname↔distributor/retailer name, itemcode↔SAP FG code, docdate) — no numeric FK; it's a reconciliation mirror, not a live join.

## 4. Portal mapping

- **Distributor Primary Stock** entry/list page (field-app + admin): backed by `tbl_distributorPrimary` + `tbl_distPrimaryProducts` (log distributor stock, approve, mark received).
- **Primary Sales** upload/report page: `tbl_primary_sales` (batch dispatch/primary-sales rows, "for dist stock").
- **Distributor Order Upload / Scheme-file ingest** page: `tbl_distorders` + `tbl_distmappings` (upload distributor Excel orders; manage name→ID mappings).
- **SAP Sales reconciliation / Primary-vs-SAP report**: `sap_sales_log` (compare DSR primary sales to SAP invoices; channel-wise GT/MT/e-com views).

## Proposed dsr commands

### `dsr primary-stock`
List field-logged distributor primary-stock entries with approval/receipt status.
Flags: `--from` `--to` (stockDate range), `--salesperson <personId>`, `--distributor <distId>`, `--pending` (approved=0).
```sql
SELECT dp.distStockId, dp.distId, dp.distName, dp.personId, dp.personName,
       dp.personType, dp.stockDate, dp.approved, dp.received, dp.completionStatus
FROM tbl_distributorPrimary dp
WHERE dp.deleted = 0
  AND dp.stockDate >= @from AND dp.stockDate < @to
  -- optional: AND dp.personId=@sp  AND dp.distId=@dist  AND dp.approved=0
ORDER BY dp.stockDate DESC;
```

### `dsr primary-stock-lines`
Show product lines (with box/qty) for one primary-stock header.
Flags: `--stock-id <distStockId>` (required).
```sql
SELECT pp.productId, pp.productName, pp.boxes, pp.productQuantity,
       pp.totalPieces, pp.totalQuantity, pp.totalMrp
FROM tbl_distPrimaryProducts pp
WHERE pp.distStockId = @stockId
ORDER BY pp.productId;
```

### `dsr primary-sales`
Report primary-sales transaction lines (qty pushed into the channel) over a period.
Flags: `--from` `--to` (date), `--retailer <retailerId>` (matches from/to), `--item <itemid>`.
```sql
SELECT ps.id, ps.salesid, ps.date, ps.from_retailerid, ps.to_retailerid,
       ps.itemid, ps.itemname, ps.quantity, ps.price, ps.bill_number,
       ps.bill_date, ps.receive_date, ps.uploaded_by
FROM tbl_primary_sales ps
WHERE (ps.deleted = 0 OR ps.deleted IS NULL)
  AND ps.date >= @from AND ps.date < @to
  -- optional: AND (@retailer IN (ps.from_retailerid, ps.to_retailerid))
  -- optional: AND ps.itemid=@item
ORDER BY ps.date DESC, ps.salesid;
```

### `dsr dist-orders`
List ingested distributor order/scheme lines with resolution status.
Flags: `--from` `--to` (datefrom range), `--distributor <distid>`, `--unresolved` (itemid IS NULL).
```sql
SELECT o.id, o.distid, o.retailername, o.retailerid, o.sku, o.itemid,
       o.processstatus, o.quantity, o.free, o.rate, o.amount,
       o.datefrom, o.dateto, o.filename
FROM tbl_distorders o
WHERE o.datefrom >= @from AND o.datefrom < @to
  -- optional: AND o.distid=@dist  AND o.itemid IS NULL
ORDER BY o.loadingdate DESC, o.id;
```
(No soft-delete column on tbl_distorders / tbl_distmappings; scope by loading batch/date instead.)

### `dsr sap-sales`
Query the SAP sales mirror by channel for primary-vs-SAP reconciliation.
Flags: `--from` `--to` (docdate), `--channel <GT|MT|E-COMMERCE>` (U_UNE_GRP1), `--item <itemcode>`.
```sql
SELECT s.docnum, s.docdate, s.cardname, s.itemcode, s.itemname,
       s.quantity, s.Price, s.U_UNE_GRP1, s.u_une_grp2, s.PymntGroup
FROM sap_sales_log s
WHERE s.docdate >= @from AND s.docdate < @to
  -- optional: AND s.U_UNE_GRP1=@channel  AND s.itemcode=@item
ORDER BY s.docdate DESC, s.docnum, s.linenum;
```
