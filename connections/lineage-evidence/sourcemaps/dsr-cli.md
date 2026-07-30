# Source map — `dsr-cli` (JIVO DSR field-sales / SFA)

Agent: dsr-cli source-mapper. Date: 2026-07-30. Repo path: `/Users/damanpreetsingh/jivo-cli/dsr-cli`.

## Headline

**dsr-cli is the most native system in the fleet.** 17 of its 18 command groups read
data that is born in the DSR Android app / web portal and never touches SAP: GPS
breadcrumbs, selfie attendance, beat routes, 127k retail outlets, secondary-sale
visits, gift issuance, targets, travel-allowance, portal ACLs, exception logs.
The 18th group (`ecom`) is an Amazon file import (external). There is **one** true
SAP mirror in the database — `sap_sales_log` — and it is (a) **frozen since
2023-08-12**, (b) **from the previous, decommissioned SAP install**, and (c) **not
exposed by any `dsr` command at all**.

## 1. Runtime & how it authenticates

- Go 1.x, cobra CLI, module `dsr`. Entry `main.go` → `internal/cli/root.go`.
- Driver: `github.com/microsoft/go-mssqldb`. DSN built in
  `internal/db/db.go:82-96` → `sqlserver://<user>:<pw>@<host>:<port>?database=…&encrypt=disable&app name=dsr-cli`.
- Creds: `DSR_USER` / `DSR_PASSWORD` from env or a gitignored `.env`
  (`internal/config/config.go:111-134`). Defaults host `103.89.45.75`, port `1433`,
  database `DSR_V6` (`config.go:36-42`). No token/OAuth anywhere.
- Read-only posture (verified in code, `internal/db/db.go:107-155`): SELECT/WITH
  first-token allowlist → always-rolled-back `READ UNCOMMITTED` tx → `QueryContext`
  only, never `ExecContext`. Login `ab` is a **sysadmin** (confirmed live by
  `dsr doctor`), so the app-layer guard is the only write block.

## 2. Datastores actually reached

| # | Datastore | How reached | Data used? |
|---|---|---|---|
| 1 | **MS SQL Server `DSR_V6`** @ 103.89.45.75:1433 (SQL Server 2017, 208 tables, ~47.5M rows) | direct TDS, every command | **YES — 100% of the CLI's data** |
| 2 | DSR web portal `http://103.89.45.75:90` | one `GET /Login/Login` in `internal/cli/doctor.go:98-102` | **NO** — reachability probe only, no rows parsed |

There is **no HTTP data path, no SAP Service Layer call, no HANA connection** in
the dsr-cli source. Verified by grep over `internal/` + `main.go`: the only
`net/http` import is `doctor.go`.

### 2b. What else is reachable through `dsr --db <name>` (scope warning)

The instance hosts **76 databases** (`SELECT name FROM sys.databases`, run live).
`--db` will point the CLI at any of them. Relevant neighbours:

- `Live_Jivo_WellnessN_Aug_2019` — **an archived SAP Business One company database**
  (MSSQL era). Live-verified: `OINV` 33,066 rows spanning **2014-11-01 → 2019-08-31**,
  `INV1` 98,761, `OJDT` 185,991, `OCRD` 7,015, `OITM` 1,119, `ORIN` 4,523, `ORDR` 17,332.
- `SBO-COMMON`, `SLDModel.SLDData` — SAP B1 system databases (same box).
- `JIVO_SAP_RECOVERED_DATA`, `Jivo_All_Branches_Live`, `JivoReports`, `jsaplive3`,
  `JSAPNew`, `ecom`, `Call_Center_CRM`, `Employee_Master`, 30+ `BusyComp*` Busy-accounting DBs.
- **Linked server `HANADB112`** (`product='HANA'`, `provider='MSDASQL'`,
  `data_source='HANA64'`) — a live ODBC bridge from this box into SAP HANA.
  It is used by `Jivo_All_Branches_Live` (SQL Agent job "Every hour" contains
  `EXEC('UPDATE JIVO_OIL_HANADB.OWHS SET "Inactive"=''Y'' …') AT HANADB112`, **currently
  disabled, enabled=0**). **No object in `DSR_V6` references `HANADB112`** (0 hits in
  `sys.sql_modules`). DSR does not use the bridge.

## 3. Command group → concrete backing table (exhaustive over groups)

All 18 groups, source-traced in `internal/cli/*.go` (`FROM`/`JOIN` grep + read).

| Group | Sub-cmds | Backing tables (DSR_V6) | Bucket |
|---|---|---|---|
| `retailers` | list get count | `tbl_retailers` (127,395 rows) | **N** |
| `salespersons` | list get count subordinates | `tbl_salesperson` (1,809) | **N** |
| `beats` | list shops assignments count | `tbl_beats` (4,882), `tbl_BeatShopMap` (182,151), `tbl_BeatAssign` | **N** |
| `attendance` | list summary register count | `tbl_salesPersonAttendance` (426,055), `tbl_AttendanceAudit` | **N** |
| `geo` | track last count | `tbl_geoLocation` (27,026,680) | **N** |
| `sales` | visits lines summary count | `tbl_SalesReport` (2,128,151), `tbl_ProductsSold` (685,564), `tbl_SchemeProductsSold` | **N** |
| `promoters` | visits lines count | `tbl_SalesReportPromoter` (185,696), `tbl_ProductsSoldPromoter` | **N** |
| `schemes` | list-sold issued gifts get count | `tbl_SchemeProductsSold`, `tbl_Gift` (15), `tbl_saveGift` (34,236), `tbl_GiftMapwithRetailer` | **N** |
| `targets` | person retailer category count | `tbl_salesPersonMontlhyTarget` (581), `tbl_categoryWiseTargets`, `tbl_retailerMonthlySale`, `tbl_retailerMonthlyTarget`, `retailerLastSale` | **N** |
| `stock` | retailer distributor lines monthly count | `tbl_retailerStock` (585,626), `tbl_distributorStock` (18,767), `tbl_distStockProducts`, `tbl_monthlystock` | **N** |
| `distributors` | list shops mappings count | `tbl_retailers WHERE type='Distributor'` (1,062), `tbl_distributorShopMap`, `tbl_distmappings` | **N** |
| `products` | list get count | `tbl_item` (333) + `tbl_itemType`/`tbl_UOMMaster`/`tbl_ItemGroupName` | **N** |
| `geography` | states zones areas subareas | `tbl_states` (21), `tbl_zones` (178), `tbl_areas`, `tbl_subArea` | **N** |
| `primary` | list stock orders count | `tbl_primary_sales` (12,560), `tbl_distributorPrimary` (222), `tbl_distorders` (1,315) | **N** (overlap caveat, §5) |
| `ecom` | sales returns settlements count | `tbl_ecom_sales` (13,387), `tbl_ecom_returns` (1,224), `tbl_payments_hdr` (27) | **X** |
| `travel` | rates km place reports count | `tbl_TA_PersonRate`, `tbl_TA_PersonRetailerKm`, `tbl_TA_PlaceKm`, `TAReprotSave` (24) | **N** |
| `users` | list roles permissions count | `tbl_loginUser` (87), `tbl_roles`, `tbl_pageMaster`, `tbl_pagePermission` | **N** |
| `logs` | recent errors reports count | `tbl_apiexceptions` (8,543,865), `hslog` (952,160) | **N** |
| *(generic)* | `query` `count` `peek` `schema` `doctor` | arbitrary table in `--db` | passthrough |

## 4. The SAP question — every bridge tested live

### 4a. `SAPID` — the column that looks like a SAP bridge and is empty

`internal/cli/retailers.go:90` and `internal/cli/distributors.go:41` and
`internal/cli/products.go:101` all SELECT a `SAPID` column, so the CLI *appears*
to surface a SAP key. Live:

```sql
-- via dsr query
SELECT COUNT(*) total, COUNT(SAPID) notnull FROM tbl_retailers
-- 127,395 total / 0 not-null
SELECT COUNT(*) total, COUNT(SAPID) notnull FROM tbl_item
--     333 total / 0 not-null
```

**`SAPID` is 100% NULL on 127,395 retailers and 333 items.** `dsr distributors list -n 3`
returns a blank SAPID column for every row. The bridge exists as a column and has
never been populated. (`tbl_states.SAPID`, `tbl_zones.SAPID` likewise; `tbl_StoreSale.sapId`
and `tbl_RealiseEntry` (CardCode/ItemCode) are **0-row dormant tables**.)

### 4b. `erpId` is NOT a SAP CardCode

12,095 / 127,395 retailers carry `erpId`. Sampled live: `FO_Jivo_75780549`,
`NEWDISTRI10-11-2021`, `103105`, `83286`, `106193`.
Live SAP HANA `JIVO_OIL_HANADB.OCRD` CardCodes look like `CUSTA000001…CUSTA000941`.
Cross-check run through the HANA tunnel:

```sql
SELECT "CardCode","CardName" FROM JIVO_OIL_HANADB.OCRD
WHERE "CardCode" IN ('83286','83248','106193','111350','119400')  -- 0 rows
```

Zero matches. Different key space entirely.

### 4c. `tbl_item.itemCode` is NOT a SAP ItemCode

91 of 333 items have a non-blank `itemCode`, and the values are small integers
(`0`, `1`, `435`, `852`, `969`). SAP item codes are `FG0000065`-style. No overlap.
SAP `OITM` holds 2,269 items vs DSR's 333 — and the naming differs
("1LTR Coldpress (20 pack)" in DSR vs "Cold Press 1 Ltr 20 Pcs" in SAP), i.e. two
independently maintained catalogues reconcilable only by eye.

### 4d. The one real mirror: `sap_sales_log` — stale AND from a dead SAP

```
rows 8,009 | docs 1,918 | items 161 | parties 213
docdate span 2023-04-01 → 2023-08-12   (nothing since)
columns: docnum, linenum, docdate, docduedate, cardname, itemcode, itemname,
         quantity, Price, PymntGroup, U_UNE_GRP1, u_une_grp2, U_SchemeAgst, U_SchemeBase
sample: 23081166 | 2023-08-12 | Hands on Trade Pvt. Ltd. | FG0000065 | Pomace Olive 1 Ltr 16 Pcs | 16 | 342.8571 | Institutional | Grofer
```

This is unmistakably a flat extract of SAP B1 `OINV`+`INV1` (SAP DocNum, SAP FG
ItemCodes, SAP UDFs `U_UNE_GRP1`/`U_SchemeAgst`). **Three things make it a trap:**

1. **It is frozen.** Last row 2023-08-12; ~3 years stale. No SQL Agent job, no
   stored procedure, and no SQL module in `DSR_V6` references it
   (`sys.sql_modules … LIKE '%sap_sales_log%'` → 0 rows). It was a one-off load.
2. **It came from the PREVIOUS SAP install.** Live HANA companies start
   `2024-09-30` (Oil), `2024-10-03` (Mart), `2024-10-04` (Bev) — verified:
   `SELECT MIN("DocDate") FROM JIVO_OIL_HANADB.OINV` → 2024-09-30. Its docnums
   (23081166/23081175/23081163) **do not exist** in any live company, and
   2023-08-12 has 0 invoices in all three.
3. **Its item codes now mean different products.** `FG0000065` in `sap_sales_log`
   = "Pomace Olive 1 Ltr 16 Pcs"; in live `JIVO_OIL_HANADB.OITM` `FG0000065`
   = "CANOLA GOLD 5 LTR 4 PCS". Same for `FG0000042` (Cold Press 5+1 → EXTRA
   VIRGIN OLIVE 1 LTR). **Anyone joining `sap_sales_log.itemcode` to today's SAP
   gets the wrong product.**
4. **No `dsr` command exposes it.** `study/vault/00-INDEX.md` proposes `dsr sap-sales`,
   but it was never built — `internal/cli/primary.go` covers only
   `tbl_primary_sales` / `tbl_distributorPrimary` / `tbl_distorders`.

### 4e. Dead legacy SAP code inside DSR_V6

`dbo.Return2Jivo` (scalar function) reads
`Live_Jivo_WellnessN.dbo.ORIN` join `Live_Jivo_WellnessN.dbo.OCRD` on
`B.U_CATGCODE = @DistributorId` — i.e. the *old* MSSQL SAP company DB carried a
UDF holding the DSR distributor id. **That database no longer exists on the
instance** (only `Live_Jivo_WellnessN_Aug_2019` remains), so the function is dead
code. And the live HANA `OCRD` has **zero `U_%` user fields**
(`SYS.TABLE_COLUMNS … TABLE_NAME='OCRD' AND COLUMN_NAME LIKE 'U[_]%'` → 0 rows),
so the DSR↔SAP party bridge that once existed is gone in the current SAP.

### 4f. No feeder path either (nothing pushes DSR into SAP)

- Column scan for `%sync%`/`%posted%`/`%export%`/`%pushed%` across all 208 tables →
  only `tbl_payments_line.posted_date/posted_datetime` (Amazon settlement file field).
- SQL Agent: 36 jobs, 14 enabled. The only jobs whose `database_name` is `DSR_V6`
  are `AutoWeeklyOff` (disabled), `AutoDuplicateShopDetector` (disabled),
  `Monthly Distributor Stock Closing Opening` (enabled) and
  `Monthly Opening Stock Insert` (enabled) — all DSR-internal rollups.
- Live SAP holds **101 user tables** (`@ABRAND`, `@BUDGET`, `@ITEM_SKU`, `@AUTL_ST_EWAY`, …)
  and **none** match `%BEAT%`/`%VISIT%`/`%ATTEND%`/`%GEO%`/`%PROMOTER%`/`%RETAILER%`/`%SALESPERSON%`.
  SAP's nearest people table `OSLP` has 155 sales employees vs DSR's 1,809 field staff.

## 5. The one genuinely hard call: `primary` (JIVO → distributor)

`tbl_primary_sales` (12,560 lines, live to **2026-07-29**) is the only DSR data that
describes the same commercial event SAP invoices. Facts pulled live:

- Rows are **manually keyed by named humans** — `uploaded_by` has 56 distinct values
  ("NANCY BIJJI", "PALLAVI FOR DIST STOCK").
- `bill_number` is populated on only **1,218 / 12,560** rows and holds 3-digit
  numbers (748, 769, 771) — a bill book, **not** a SAP DocNum.
- Parties are DSR retailer ids, not CardCodes.
- Source-party split: `from_retailerid` = 9771 "JIVO WELLNESS" on **7,413** lines
  (company → distributor, i.e. economically the same as a SAP A/R invoice);
  **3,471** lines have no source party; the remainder come from **super-stockists**
  (9780 GROVER AGENCY (SUPER) 336, 9814 ARJAN DASS & SONS (SUPER) 160, …), whose
  onward sales to sub-distributors **JIVO's books never see**.

Ruling: **N**, because the rows originate in DSR, carry no SAP key, are not sourced
from SAP and are not posted to SAP. But flag loudly: ~59% of the lines *duplicate*
transactions SAP also records independently, so **primary-sales volume from DSR must
never be added to SAP invoice volume** — it would double count. The truly new part is
the super-stockist leg and the field-logged `tbl_distributorPrimary` (approval /
receipt / GPS / due-date state SAP has no concept of).

## 6. `ecom` group — external, and dead

`tbl_ecom_sales` is literally Amazon's MTR B2C report schema (`Seller_Gstin`,
`Invoice_Number` = "IN-439", `Asin`, `Shipment_Item_Id`, `Product_Tax_Code`,
`Bill_From_*`/`Ship_From_*`, `fulfillment_channel` = MFN). Origin = Amazon, not JIVO,
not SAP → **X**. Latest row **2023-04-30**; `tbl_payments_hdr` has 27 settlement
rows. This importer was abandoned three years ago; the live e-com data lives in the
separate `ecom-cli`/`ecom` systems, not here.

## 7. What SAP could never give you (the value of this system)

Live sample from `dsr attendance list`:

```
457050 | 2688 | 2026-07-29T21:26:10Z | EOD | 28.4125839 | 77.0425844 | acc 25807 |
        2688-29-7-2026-21268.jpg | 124, Sector 49, Gurgaon Division, 122018
```

GPS lat/long, selfie file, reverse-geocoded address, device SIM, battery level,
accuracy/speed/altitude (`tbl_geoLocation`), visit duration, visit status
("MEETING"/"DONE"), soft-deleted and rejected records, approval trails, beat
membership history, 8.5M API exception rows. **SAP B1 holds none of this**, and
`dsr sales visits` on 2026-07-29 returns rows SAP has no analogue for at all
(distributor→retailer secondary sales into 127k outlets, of which only ~3,390
parties exist in SAP as business partners).

## 8. Gaps / bugs / things I did not do

- **`dsr schema columns <table>` is broken.** Every invocation errors with
  `mssql: The ORDER BY clause is invalid in views, inline functions, derived tables,
  subqueries … unless TOP, OFFSET or FOR XML is also specified` — the `-n/--limit`
  wrapper wraps an already-ORDER BY'd query. Reproduce:
  `dsr schema columns tbl_retailers`. I used the offline dump
  (`study/schema/columns.tsv`) instead.
- I did **not** reconcile DSR primary-sales quantities against SAP invoice
  quantities for the same distributor/period — that is the one test that would
  turn the §5 ruling from ~78% to certain.
- I did **not** log into the DSR web portal (no app credential exists yet — README
  and the memory note both say so). Everything here is DB-side.
- I did **not** enumerate every one of the 71 sub-commands; I covered all 18 groups
  and every distinct table they read.
- SAP Service Layer (`sapb1 doctor`) is **unreachable** from here
  (`cannot reach 103.89.45.192:50000`) — all SAP evidence above came from HANA
  direct SQL through the 127.0.0.1:13015 tunnel (which needed a host/port override;
  `connections/hana.env` still points at the un-tunnelled 103.89.45.192:30015).
