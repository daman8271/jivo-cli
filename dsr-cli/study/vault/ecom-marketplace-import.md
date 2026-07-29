# Subsystem: ecom-marketplace-import

## 1. Overview
This subsystem ingests **online-marketplace (Amazon / Flipkart) transaction files** into DSR_V6 and reconciles them. Unlike the rest of DSR (field SFA — Sales Officers walking retailer beats), this is a **back-office file-loader pipeline**: someone drops seller-portal export files (Amazon GST invoice CSVs `format002amz`, Amazon settlement/payment TXTs `format003amz`, Flipkart returns XLSX `format004flp`, PDFs, etc.) and a "FileLoader" job parses each file into these tables. It gives JIVO Wellness visibility into its **e-commerce channel**: what sold online (B2C invoices), what was returned, and how much the marketplace actually settled/deposited to JIVO's bank. Every row carries a `filename` + `loadingid` provenance stamp so a load can be traced or reversed.

Data is coarse-grained per-transaction (order/invoice/settlement level), **not** tied to salespersons, beats, or retailers — so its joins into the DSR SFA core are weak (mainly via SKU → item/BOM).

## 2. Tables

### tbl_ecom_sales — 13,387 rows — PK `id` (int identity)
One row per **marketplace invoice line** (Amazon "MTR"/GST report style). Wide GST-invoice schema.
- `Seller_Gstin` — JIVO's selling GSTIN (e.g. `07AACCJ4223F1ZY` = Delhi).
- `Invoice_Number`, `Invoice_Date`, `Order_Id`, `Shipment_Id`, `Shipment_Date`, `Order_Date` — marketplace document/order keys & dates.
- `Transaction_Type` — `Shipment` (sale) vs `Refund`/`Cancel` etc.
- `Quantity`, `Sku` (marketplace/FBA SKU e.g. `SUNFLOWER-OIL-5L-FBA`), `Asin` (Amazon product id), `Hsn_sac`, `Item_Description`.
- `Bill_From_*` / `Ship_From_*` / `ship_to_*` / `bill_to_*` — city/state/country/postcode of warehouse & customer (state drives IGST vs CGST+SGST).
- Money: `invoice_amount`, `tax_exclusive_gross`, `principal_amount` (item net), `shipping_amount`, `gift_wrap_amount`, plus full GST breakup — `cgst/sgst/igst/utgst/compensatory_cess` each as `_rate` and `_tax`, mirrored for shipping & gift-wrap, plus `item_promo_discount*` and `tcs_*` (Tax Collected at Source).
- `warehouse_id`, `fulfillment_channel` — `AFN` = Amazon-fulfilled (FBA), `MFN` = merchant-fulfilled.
- `payment_method_code` — `CC`, `COD`, etc.
- `credit_note_no/date`, `irn_number/date/filing_status/error_code` — e-invoice (IRN) reference for the marketplace invoice.
- `buyer_name`, `customer_bill_to_gstid`, `customer_ship_to_gstid` — B2B buyer GST identity when present.
- `filename`, `loadingdate`, `loadingid` — load provenance.

### tbl_ecom_returns — 1,224 rows — PK `id` (int; no PK listed but `id` is identity)
One row per **returned unit** from marketplace returns reports (Flipkart-style; `fsn` = Flipkart Serial Number).
- `date` — return date; `order_id`; `qty` (usually 1).
- `fsn`, `sku` (portal SKU string e.g. `MUSTARD 5LTR`), `sale_bom`/`sale_bom_descr` — the internal **BOM/combo code** (e.g. `SL000051 = Canola 5L + Extra Light 1L`) the return maps back to.
- `condition` — item condition on return (`OK`, damaged, etc.).
- `filename`, `loadingdate`, `loadingid` — provenance.

### tbl_payments_hdr — 27 rows — PK `settlement_id` (bigint)
One row per **marketplace settlement batch** (Amazon payments report header).
- `settlement_id` — marketplace settlement id.
- `sstartdate`, `senddate` (settlement period start/end), `depositdate` — when money hit JIVO's bank.
- `totalamt`, `currency` (INR) — net amount deposited for that settlement.
- `loadingid` — provenance (often null in header).

### tbl_payments_line — 113,547 rows — PK `id` (int identity)
Line detail of each settlement — every fee/charge/credit that nets to the header total. Largest table here.
- `settlement_id` → FK to `tbl_payments_hdr`.
- `transaction_type` — `Order`, `Refund`, `ServiceFee`, `Adjustment`, etc.
- `order_id`, `merchant_order_id`, `adjustment_id`, `shipment_id` — links back to the order/sale.
- `marketplace_name` — e.g. `Amazon.in`.
- `amount_type` / `amount_description` / `amount` — the charge category, its label (e.g. Principal, Commission, FBA fee, Tax), and signed value. **Many rows have these NULL** (Amazon report emits a header/grouping row per order before its amount lines) — filter `amount is not null` when summing.
- `fulfillment_id`, `posted_date`/`posted_datetime`, `sku`, `quantity_purchased`, `promotion_id`.
- `filename`, `loadingdate`, `loadingid` — provenance.

### tbl_uploadstatus — 195 rows — PK `loadingid` (int)
Load-run log — one row per file-load attempt.
- `loadingid` — the load id stamped onto every ingested row above.
- `status` — free-text outcome, e.g. `Done format001chrpart1 (2).PDF` (prefix `Done` = success + the filename processed).
- `datetime` — when processed.

### tbl_ecom_lastfile — 1 row — PK `id` (int)
High-water mark: the **last processed file/loading id** (sample `id = 620`) so the loader knows where to resume. Single-row control table.

### tbl_currentstatus — 1 row — PK `id` (varchar)
Loader heartbeat/lock. Sample: `id = "FileLoader"`, `updatedttm = 2023-10-30`. Tracks whether the FileLoader job is running / last active.

## 3. Linkages
This subsystem is largely **self-contained** and does NOT carry personId / retailerId / beatId / distributorId — it is a marketplace channel, not field-force data. The only meaningful bridges into the DSR SFA core:
- **SKU / BOM → product master:** `tbl_ecom_sales.Sku`, `tbl_ecom_returns.sku` and especially `tbl_ecom_returns.sale_bom` (e.g. `SL000051`) map to internal item/BOM codes — join by convention `itemId/productId → tbl_item.itemId` (via the SKU↔item mapping / BOM tables). No numeric FK is present; matching is by code string.
- **Internal joins within subsystem:**
  - `tbl_payments_line.settlement_id → tbl_payments_hdr.settlement_id`
  - `tbl_ecom_sales.Order_Id = tbl_payments_line.order_id` and `= tbl_ecom_returns.order_id` (marketplace order id ties a sale to its settlement lines and returns).
  - `loadingid` on every data table → `tbl_uploadstatus.loadingid` (provenance / to reverse a bad load).
- **No `deleted`/`deletionDate` columns exist** on these tables (they are append-only load tables), so the usual `deleted=0` soft-delete filter does not apply here — use `filename`/`loadingid` + `tbl_uploadstatus` for validity instead.

## 4. Portal mapping
Used by the **E-commerce / Online Sales (Marketplace)** back-office section of the DSR portal, driven by the FileLoader importer:
- **Upload / Import page** — uploads Amazon/Flipkart export files; writes to `tbl_uploadstatus`, `tbl_ecom_lastfile`, `tbl_currentstatus`.
- **Ecom Sales report** — `tbl_ecom_sales` (online invoice/sales register, GST breakup).
- **Ecom Returns report** — `tbl_ecom_returns`.
- **Payments / Settlement Reconciliation** — `tbl_payments_hdr` + `tbl_payments_line` (marketplace payouts vs sales).
(These pages are distinct from the SO/Promoter beat-execution menus.)

## 5. Proposed dsr commands

### `dsr ecom-sales`
Online marketplace sales register with GST-net turnover.
Flags: `--from` `--to` (Invoice_Date), `--state` (ship_to_state), `--sku`, `--channel` (AFN/MFN), `--gstin`.
```sql
SELECT CAST(Invoice_Date AS date) AS inv_date, Invoice_Number, Order_Id,
       Sku, Asin, Quantity, ship_to_state, fulfillment_channel,
       principal_amount, invoice_amount, total_tax_amount, Transaction_Type
FROM tbl_ecom_sales
WHERE Invoice_Date >= @from AND Invoice_Date < @to
  AND Invoice_Date <> '1899-12-30'            -- empty-date sentinel
  AND (@state IS NULL OR ship_to_state = @state)
  AND (@sku   IS NULL OR Sku = @sku)
ORDER BY Invoice_Date;
-- Net sales = SUM(invoice_amount) for Transaction_Type='Shipment' minus 'Refund'/'Cancel'.
```

### `dsr ecom-returns`
Marketplace returns by SKU/BOM and condition.
Flags: `--from` `--to` (date), `--sku`, `--bom`, `--condition`.
```sql
SELECT date, order_id, sku, sale_bom, sale_bom_descr, qty, condition, filename
FROM tbl_ecom_returns
WHERE date >= @from AND date < @to
  AND date <> '1899-12-30'
  AND (@sku IS NULL OR sku = @sku)
  AND (@condition IS NULL OR condition = @condition)
ORDER BY date;
```

### `dsr ecom-settlements`
Settlement payouts actually deposited to JIVO's bank.
Flags: `--from` `--to` (depositdate).
```sql
SELECT settlement_id, sstartdate, senddate, depositdate, currency, totalamt
FROM tbl_payments_hdr
WHERE depositdate >= @from AND depositdate < @to
  AND depositdate <> '1899-12-30'
ORDER BY depositdate;
```

### `dsr ecom-settlement-detail`
Fee/charge breakup for one settlement, or fees by category over a period.
Flags: `--settlement <id>`, `--from` `--to` (posted_date), `--type` (amount_type), `--order`.
```sql
SELECT settlement_id, transaction_type, order_id, amount_type,
       amount_description, amount, posted_date, sku, quantity_purchased
FROM tbl_payments_line
WHERE amount IS NOT NULL                       -- skip Amazon grouping/header rows
  AND (@settlement IS NULL OR settlement_id = @settlement)
  AND (@order IS NULL OR order_id = @order)
  AND (@type  IS NULL OR amount_type = @type)
  AND (@from IS NULL OR posted_date >= @from)
  AND (@to   IS NULL OR posted_date <  @to)
ORDER BY settlement_id, posted_date;
```

### `dsr ecom-loads`
Recent file-load runs / import status (audit of what was ingested).
Flags: `--from` `--to` (datetime), `--failed` (status not starting with 'Done').
```sql
SELECT loadingid, status, datetime
FROM tbl_uploadstatus
WHERE (@from IS NULL OR datetime >= @from)
  AND (@to   IS NULL OR datetime <  @to)
  AND (@failed = 0 OR status NOT LIKE 'Done%')
ORDER BY loadingid DESC;
-- Last processed high-water mark: SELECT id FROM tbl_ecom_lastfile;
-- Loader heartbeat:               SELECT id, updatedttm FROM tbl_currentstatus;
```
