# FR8HODBNEW (ARY / FusionERP8) — verified schema notes

Every statement below was checked against the live database on **2026-08-27**
with the queries shown. Anything not checked is marked UNVERIFIED.

## What the system is

| Fact | Value | How it was checked |
|---|---|---|
| Product | **FusionERP8** (retail + distribution ERP) | `LocationMaster` rows carry `C:\FusionERP8\Export` / `Import` / `Backup` paths |
| Host | `138.252.101.118:1433`, SQL Server 2017 Enterprise 14.0.1000.169 | `ary doctor` |
| Database | `FR8HODBNEW` — 290 tables, 269 of them real (rest are `Temp*`/`Header0*` scratch) | `sys.tables` + `INFORMATION_SCHEMA.COLUMNS` dumps in `../schema/` |
| Legal entity | **Akal Rozgar Yojana A U/O Jivo Wellness Pvt Ltd**, PAN `AACCJ4223F` | `LocationMaster.CompanyName`, `.PanNo` |
| Locations | 3: Ary HO Delhi `07AACCJ4223F1ZY` · Ary Baru Sahib HP `02AACCJ4223F1Z8` · Ary Bathinda PB `03AACCJ4223F1Z6` | `ary locations` |
| Warehouses | 12 rows, 11 with stock: Ary Pos, Ary Warehouse, Ary Clothing, Ary Lite, Ary G Canteen, Girls Canteen Ts, Ary Apple A Day, Basement, Talwandi Sabo, Fruits & Vegetables | `ary warehouses` |
| Sibling DBs on the box | `ARY_BSU` (SAP B1 SQL company, journals to FY24-25) · `FR8Ilahi` (separate Ilahi unit, live) · `BusyComp*_db*` (Busy books) · `jsap`/`jsaplive3` · DSR family — 72 user DBs | `ary schema databases` |

## Document tables — the pattern

Every voucher is a `…Header` / `…Detail` pair keyed on **`SerialNumber`** (decimal,
e.g. `2264295.0015` — the fraction encodes the location). Dates are
`smalldatetime`; the empty sentinel is **1900-01-01**, so any date filter must
exclude `<= '1901-01-01'`.

| Module | Header | Detail | Rows | Last document (2026-08-27) |
|---|---|---|---|---|
| Sales | `SaleHeader` | `SaleDetail`, `SalePayment` | 1,088,607 / 2,904,146 / 1,109,913 | 2026-08-21 14:05 |
| Sale returns | `SaleReturnHeader` | `SaleReturnDetail`, `SaleReturnPayment` | 1,891 | 2026-08-21 11:03 |
| Purchases | `PurchaseHeader` | `PurchaseDetail` | 9,221 / 89,960 | 2026-08-21 14:08 |
| Purchase returns | `PurchaseReturnHeader` | `PurchaseReturnDetail` | 369 / 937 | — |
| Accounting | `TransactionMaster` | `TransactionChild` | 1,111,478 / 5,127,541 | **2026-08-27 15:51** |
| Bill-wise refs | `RefMaster` (flat) | — | 582,298 | — |
| Stock transfers | `StockTransferHeader` | `StockTransferDetail` | 22,297 / 107,988 | 2026-08-21 14:09 |
| Stock journals | `StockJournalHeader` | `StockJournalDetail` | 2,199 / 81,943 | **2026-08-26 17:45** |
| Physical counts | `PhysicalStockHeader` | `PhysicalStockDetail` | 2,835 / 41,755 | 2026-08-21 15:40 |

## Traps that will produce wrong numbers

1. **`SaleHeader` has no cancellation flag.** All 1,088,607 rows are `Status=2`,
   `IsAudited=false`, and no `SaleDetail` row has a `VoidDateTime`. The only
   reversal is a separate `SaleReturnHeader` document — so gross sales overstate
   by the return value. Use `ary sales net`.
   ```sql
   SELECT Status, IsAudited, COUNT(*) FROM SaleHeader GROUP BY Status, IsAudited;  -- 1 row
   SELECT StatusID, COUNT(*), SUM(CASE WHEN VoidDateTime>'1901-01-01' THEN 1 ELSE 0 END) FROM SaleDetail GROUP BY StatusID;  -- 0 voided
   ```
2. **`PurchaseHeader`, `PurchaseDetail`, `TransactionMaster`, `RefMaster`, and
   `SalePayment` DO have `IsDeleted`** even though `SaleHeader` does not. Filter it.
3. **`ProductMaster.QuantityOnHand` is dead** — non-zero on exactly ONE SKU of
   21,466. Never use it for stock.
4. **`Stock.Quantity` IS the system's own on-hand**, and the identity below held
   on **104,221 of 104,221 rows**. The challan buckets (`PurCh/PRCh/SalCh/SRCh`)
   are all zero.
   ```
   Quantity = OP + Pur - PR - Sal + SR + Prod - Cons + TrIn - TrOut + Exc - Sho - Was
   ```
   So a **negative** `Quantity` is real data, not a query artefact.
5. **`TempStockTable` is a stale report cache, not the truth.** Its `CurrClo`
   agrees with `Stock.Quantity`, but its `Sho`/`Exc` are whatever the last report
   run computed (Ary Pos `Sho` = 200 there vs **173,550** in `Stock`). Read
   variance from `Stock`.
6. **The warehouse is a LINE attribute** (`SaleDetail.WarehouseID`), not a header
   one. The header carries `LocationID` (which of the three registrations).
7. **`PurchaseDetail` column names differ from the sales side**: `PurchaseCost`
   (not `PurchaseRate`), `SellingRate` (not `MRP`), **`ItemValue`** (not
   `FinalPurchaseAmount`). Sales lines use `FinalSaleAmount`.
8. **`ProductCodeSAP` exists on all 21,466 SKUs and is EMPTY in every row.**
   There is no ARY↔SAP item bridge; cross-system work has to match on name today.
9. **Busiest ledgers are enormous** — `Sales A/C` 1,088,340 lines, `Cash` 561,552,
   `Paytm` 528,483. An unwindowed running balance over `TransactionChild` cannot
   finish inside a query timeout; `ary ledger statement` is windowed by design
   (opening balance + the window's lines).
10. **Indexes that exist** (so a query can be written to be fast):
    `TransactionChild` → `AccountID`, `(SerialNumber, AccountID)`, `CostCenterID`;
    `TransactionMaster` → `VoucherDate`, `SerialNumber` (PK).

## Accounting shape

- `TransactionChild.DebitAmount` / `.CreditAmount` carry the figures; balance is
  `SUM(Debit) - SUM(Credit)` → **positive = DEBIT** (same convention as SAP's
  `CurrentAccountBalance` at JIVO).
- `AccountMaster.DebitAmount` / `.CreditAmount` are the **opening** balances.
- `RefMaster` is the bill-wise reference ledger (one row per document reference
  per account, with `DueDate`) — the basis for outstanding and ageing.
- `GroupMaster` is the chart-of-accounts tree (`ParentGroupID`), 59 groups.

## Decode tables

`ModeOfPayment` (11) · `SalesPersonMaster` (16) · `UnitMaster` (12) ·
`TaxMaster` (39) · `VoucherMaster` (84) + `VoucherTypeMaster` (32) ·
`BrandMaster` (1,195) → `PrincipalCompanyMaster` (5: J.L Enterprises, Vanesa Care
Denver & Envy, Honasa/Mamaearth, Unicorn Infosolutions/Apple) ·
`ProductGroupMaster` (93) + `SubGroupMaster` (846) · `HSNSACMaster` (1,184) ·
`StateMaster` (24) · `CustomerTypeMaster` (7) · `CostCenterMaster` (2) ·
`UserMaster` (76) · `WarehouseMaster` (12) · `LocationMaster` (3).

## The 2026-08 audit (context for a stale sales feed)

The sale/purchase/transfer feeds stop at **2026-08-21 14:05** while accounting
runs to today. That is an **internal physical stock audit in progress**, confirmed
by the owner and visible in the data: `PhysicalStockHeader` shows counts on
2026-08-21 keyed by users `Taran`, `Raunak` and **`Audit-01`**, and stock journals
posted as recently as 2026-08-26. A stale sales date here is not automatically a
broken feed — check `ary audit counts` before calling it a fault.
