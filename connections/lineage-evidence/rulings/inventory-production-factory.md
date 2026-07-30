# FINAL RULINGS — domain: inventory · production · factory

Adjudicator run 2026-07-30. Evidence: **live SAP HANA SQL** (tunnel `127.0.0.1:13015`, `-env
connections/hana-tunnel.env`) + **live Postgres** (`factory_flow`, `test_supabase`,
`order_management` via `postsql`). App REST APIs were NOT reachable — every app token in this
workspace is expired (`factory doctor` and `ecom doctor` both return `Credentials: invalid (HTTP
401)`). That matters and is stated on every ruling it touches.

---

## 0. The one-paragraph answer for Daman

**SAP owns the BALANCE and the DOCUMENT. The factory app owns the EVENT.** Every stock figure,
item master, batch, warehouse, production order, goods receipt, goods issue, inventory transfer
and BOM you can pull out of factory-cli / control-panel / oms-cli / exim / jsap is a live SAP
row with nicer field names — I proved it four documents deep, row for row. What none of those
systems can give you, and what SAP will never hold, is the 301,821 cartons, 791,851 carton
movements, 143,236 scans, 10,740 QC lab readings, 1,720 weighbridge weighments, 1,202 arrival
slips with CoA photos, and the whole gate/dispatch/MES layer. Those are not a duplicate of SAP at
a finer grain — SAP has **no object at any grain** that could hold them. And exactly **one**
thing in this entire domain flows back into SAP: the GRPO.

---

## 1. The discriminator that decided most of this domain

`OUSR.U_NAME` on the SAP document, joined via `UserSign`. SAP's integration user is **`B1i`**.

```sql
-- who creates GRPOs in SAP (Oil, since 2026-03-01)
SELECT U."U_NAME", COUNT(*) FROM JIVO_OIL_HANADB.OPDN P
LEFT JOIN JIVO_OIL_HANADB.OUSR U ON U."USERID"=P."UserSign"
WHERE P."DocDate">='2026-03-01' GROUP BY U."U_NAME" ORDER BY 2 DESC;
-- GURCHARAN 662 · VISHAL TYAGI 462 · SHAHRUKH 329 · B1i 262 · KULBIR 224 · NEETU 132 · ...
```

```sql
-- who creates production orders / goods receipts / goods issues in SAP (Oil, all time)
-- OWOR: Gautam CHanana 6003 · AVTAR SINGH 510 · manager 347 · LOVPREET 334 · PANKAJ 276 · ...
-- OIGN: Gautam CHanana 6015 · manager 541 · AVTAR 534 · LOVPREET 325 · PANKAJ 271 · ...
-- OIGE: Gautam CHanana 6024 · AVTAR 515 · manager 474 · LOVPREET 324 · PANKAJ 268 · ...
-- B1i appears ZERO times in all three.
```

**So: `B1i` posts GRPOs and nothing else in this domain.** Production orders, goods receipts and
goods issues are keyed by humans inside SAP. That single fact flips three phase-1 rulings.

---

## 2. Live proof that factory-cli's SAP endpoints are a real-time window, not a cache

The factory-cli source-mapper got **zero** live SAP rows (HANA was saturated when it ran) and
said so honestly. I closed that gap. Four documents it captured off the live API on 2026-07-13,
looked up in HANA today — all four land in **`JIVO_MART_HANADB`**, which is exactly the CLI's
default `Company-Code: JIVO_MART`:

| app payload (raw capture 2026-07-13) | HANA today |
|---|---|
| `/gate-core/sales-dispatch/documents/` → `doc_entry 36528, doc_num "707260234", card_code "CUSTA000048"` | `JIVO_MART_HANADB.OINV` DocEntry **36528**, DocNum **707260234**, CardCode **CUSTA000048**, DocDate 2026-07-13 ✅ |
| `/gate-core/bst-outs/sap-transfers/` → `doc_entry 3306, doc_num "726674571", comments "Based On Inventory Transfers 726674570."` | `JIVO_MART_HANADB.OWTR` DocEntry **3306**, DocNum **726674571**, Comments **verbatim identical** ✅ |
| `/sap/plan-dashboard/summary` → `prod_order_entry 39, prod_order_num 825926501, sku_code "FG0000326", warehouse "DL-MP"` | `JIVO_MART_HANADB.OWOR` DocEntry **39**, DocNum **825926501**, ItemCode **FG0000326**, Warehouse **DL-MP** ✅ |
| `/warehouse/wms/sales-orders/backlog/` → `doc_entry 1133, doc_num 1725021002, customer_code "CUSTA000827"` | `JIVO_MART_HANADB.ORDR` DocEntry **1133**, DocNum **1725021002**, CardCode **CUSTA000827**, DocStatus **O** ✅ |

Four for four, on primary key *and* business fields, across four different SAP tables. Combined
with the source-mapper's decisive negative (**no OITM/OITW/OINM/OWOR/OWTR/OINV mirror table
exists anywhere in `factory_flow`'s 250+ tables**), this settles it: factory-cli's SAP-shaped
endpoints are assembled from HANA at request time. **M, live, no lag.** I am raising those
confidences from the source-mapper's 85–92 to 97–99.

`PRODUCTION_RELEASE_OIL` is also settled — it is a **SAP-side VIEW**, not an app table:

```sql
SELECT CAST(DEFINITION AS NVARCHAR(4000)) FROM SYS.VIEWS
WHERE SCHEMA_NAME='JIVO_OIL_HANADB' AND VIEW_NAME='PRODUCTION_RELEASE_OIL';
-- SELECT A."DocEntry", A."DocNum", A."PostDate", A."ItemCode", C."ItemName", C."U_IsLitre",
--   C."ManBtchNum", A."PlannedQty", A."PlannedQty"/C."SalFactor2" AS "Box",
--   A."PlannedQty"*C."SalPackUn" AS "Liter", A."U_BATCH_NO", A."U_MFG", A."U_EXP_DATE", A."Status"
-- FROM OWOR A INNER JOIN OITM C ON C."ItemCode"=A."ItemCode"
-- WHERE C."Series" IN (389,393) AND C."ManBtchNum"='Y' AND A."Status"='R'
```

Pure OWOR ⨝ OITM with computed Box/Litre columns. **M**, confidence 98 (was doc-only 88).

---

## 3. THREE PHASE-1 RULINGS I AM OVERTURNING

### 3.1 Production runs are **N**, not F (factory-cli said "F partial", conf 94)

```sql
SELECT sap_doc_entry, count(*) FROM warehouse_bomrequest WHERE sap_doc_entry IS NOT NULL GROUP BY 1;
-- 2650 → 5 rows | 3651 → 4 | 2945 → 1 | 6189 → 1 | 6175 → 1
SELECT id, item_code, sap_doc_entry, sap_receipt_doc_entry, sap_sync_status
FROM production_execution_productionrun WHERE sap_doc_entry IS NOT NULL ORDER BY id DESC;
-- 3651 appears on 3 runs; 2650 on 3 runs; sap_receipt_doc_entry NULL everywhere;
-- sap_sync_status = 'NOT_APPLICABLE' on every row
```

A feeder's document reference is **unique per row** and gets filled on success. These **repeat**.
Looked up in SAP:

```sql
SELECT "DocEntry","DocNum","ItemCode","PostDate","Status" FROM JIVO_OIL_HANADB.OWOR
WHERE "DocEntry" IN (3651,2650,2945);
-- 2650 → DocNum 225026669, FG0000085, 2025-02-21, Status R (Released)
-- 2945 → DocNum 325026566, FG0000169, 2025-03-08, R
-- 3651 → DocNum 425926633, FG0000142, 2025-04-14, R
```

They are **pre-existing Released SAP production orders that the shop floor runs against**. The
app writes nothing back. Confirmed by `B1i` having zero OWOR/OIGN/OIGE rows.

### 3.2 BOM requests and FG receipts are **N**, not F

```sql
SELECT id, sap_doc_entry, sap_issue_doc_entries::text, material_issue_status, status
FROM warehouse_bomrequest ORDER BY id DESC LIMIT 10;
-- sap_issue_doc_entries = '[]' on EVERY row; material_issue_status = 'NOT_ISSUED' on every row
SELECT id, sap_doc_entry, sap_receipt_doc_entry, item_code, produced_qty, status
FROM warehouse_finishedgoodsreceipt;
-- 3 rows: sap_doc_entry 2650 / 3651 / 6189 (again the OWOR refs), sap_receipt_doc_entry NULL on all 3
```

The material issue has **never** been executed. The FG receipt has **never** posted. Both fields
labelled `sap_doc_entry` are OWOR references, not created documents. The phase-1 agent read the
column name and inferred a feeder; the values say otherwise.

### 3.3 The `hana-census` probe's inference is wrong

It wrote: *"OWOR is NOT empty… factory production orders reach SAP, so factory-cli is F for the
production-order layer."* That is a non-sequitur — OWOR being populated says nothing about
**who** populated it. The `UserSign` join says humans in SAP did. Direction is **SAP → app**,
not app → SAP. Corrected to **M** (read) + **N** (the app's release/approval and MES wrapper).

---

## 4. THE ONE REAL FEEDER — and it is live-verified in both directions

`grpo_grpoposting` / `grpo_servicegrpoposting` → SAP `OPDN`, posted by `B1i`:

| factory_flow row | SAP HANA today |
|---|---|
| `sap_doc_entry 24783, sap_doc_num 2026076623, sap_doc_total 151436.00, POSTED 2026-07-15` | `JIVO_OIL_HANADB.OPDN` DocEntry 24783, DocNum 2026076623, VENDA000933, **DocTotal 151436.000000**, creator **B1i** ✅ |
| `24780 / 2026076622 / 99545.00` | Oil OPDN 24780, VENDA000945, **99545.000000**, **B1i** ✅ |
| `24754 / 2026076611 / 308369.00` | Oil OPDN 24754, VENDA001180, **308369.000000**, **B1i** ✅ |
| `9145 / 2026078015 / 1299140.00` | **Beverages** OPDN 9145, VENDA000878, **1299140.000000**, **B1i** ✅ |
| service GRPO `8672 / 2026068060` | Beverages OPDN 8672, VENDA001259, 5200.00, **B1i** ✅ |
| service GRPO `8670 / 2026068059` | Beverages OPDN 8670, VENDA001259, 5200.00, **B1i** ✅ |

Six for six, exact to the paisa, across two companies, all stamped with the integration user.
Fill rates and windows (live):

| feeder | rows | with SAP doc | window |
|---|--:|--:|---|
| material GRPO | 265 | **232** | 2026-03-11 → **2026-07-28** (live) |
| service GRPO | 158 | 158 | 2026-05-20 → **2026-06-15** (dormant 6 weeks) |

**What SAP does NOT receive in that push:** the QC inspection that authorised it (chemist +
QA-manager two-signature decision, remarks, 10,740 parameter readings), the arrival-slip CoA/CoQ
photos, the gate entry and truck/driver identity, the weighbridge tare, the **rejected quantity
and its reason**, and 232 GRPO attachments. That is why the app is not redundant even here.

---

## 5. The N-check I am obliged to perform, performed

Before ruling anything N I enumerated **every populated non-archive user-defined table in all
three SAP schemas**:

```sql
SELECT SCHEMA_NAME, TABLE_NAME, RECORD_COUNT FROM M_TABLES
WHERE SCHEMA_NAME LIKE 'JIVO%' AND TABLE_NAME LIKE '@%'
  AND TABLE_NAME NOT LIKE '@A%' AND RECORD_COUNT > 0;
```

The complete result set is: product taxonomy (`@BRAND`, `@CHAIN`, `@ITEM_SKU`, `@ITEM_SUBGRP`,
`@ITEM_UNIT`, `@ITEM_VARIETY`, `@MAIN_GROUP`), budget (`@BUDGET`, `@BUDGET1`), a 25-row QC stub
(`@QC_I` 19 / `@QC_O` 6, Oil only), the ZIA add-on (`@OZIA`, `@OZIAR`, `@ZIA_DL_LIMIT`,
`@ZIA_DL_OLIMIT`, `@SERVER`) and the Uneecops e-invoice / e-way-bill add-on (`@UNE_*`, `@UTL_*`).

**Nothing for tanks, cartons, barcodes, scans, pallets, weighbridge, gate entries, lab
parameters, production runs, OEE, downtime, physical stock counts, import lots or dark-store
inventory.**

I sampled the one candidate that could have been the factory QC system:

```sql
SELECT * FROM JIVO_OIL_HANADB."@QC_O";
-- 6 rows, Object='Quality Check', created 2025-10-13/14 by manager & USER31,
-- U_DocType ∈ {A/R Invoice, Stock Transfer, Delivery}, two already Cancelled.
```

That is an abandoned **dispatch-document** QC stub from October 2025. It is not the raw-material
lab. `QC_SYNC_DATA` in Oil has 0 rows.

And the standard-table census (live `M_TABLES`, Oil / Mart / Bev):

```
OINC   0 / 0 / 0   ← inventory counting: SAP has NEVER recorded a physical stock count
INC1   0 / 0 / 0
OIQR   0 / 0 / 0   ← counting results
ODPS   0 / 0 / 0
OSRN   0 / 0 / 0   ← serial numbers UNUSED → cartons cannot be SAP serials
OSRI   0 / 0 / 0
OSRQ   0 / 0 / 0
OBIN   0 / 0 / 0   ← bin locations UNUSED → SAP stops at warehouse, not bin
OBBQ   0 / 0 / 0
OPKG   0 / 0 / 0   ← packaging
OSHP   0 / 0 / 0   ← shipping
OWKO   0 / 0 / 0   ← production wizard
OPWZ   0 / 0 / 0   ← MRP wizard
ORCM   0 / 0 / 0
```

Plus a name sweep for `%BARCODE% %CARTON% %SCAN% %PALLET% %BOX% %WEIGH% %GATE% %TANK% %QC%
%QUALIT% %INSPECT% %PRODUCTION% %DISPATCH% %OEE% %DOWNTIME% %BLOW%` across all JIVO schemas
returned only: `BOX1–4`/`OBOX`/`OEEV` (all **0 rows**), `OQCN` (which is SAP's *Query Category*
table — columns `CategoryId, CatName, PermMask`, nothing to do with quality), the `@QC_*` stub,
and the app-owned `PRODUCTIONORDERSYNC` / `QC_SYNC_DATA`.

**Every N ruling below rests on this check.**

Populated, for contrast (Oil / Mart / Bev): `OITW` 127,211 / 47,908 / 95,351 · `OINM`-family
`OITL` 196,793 · `OIVL` 265,963 · `OBTN` **17,505** / 10,076 / 2,113 · `OBTQ` 32,967 · `OWOR`
7,858 / 27 / 1,431 · `OIGN` 8,065 · `OIGE` 7,939 · `OWTR` 11,800 · `OPDN` 11,248 / 3,023 / 4,533
· `OITT` 622 · `OWHS` 58 / 36 / 44. All current to **2026-07-29**; all start **2024-09/10**
(SAP go-live — nothing before that exists in any module).

---

## 6. THE GRAIN ARGUMENT — this is the part Daman actually needs

SAP tracks **batch**, the factory tracks **carton within batch**. These are not duplicates.

| question | who can answer it | why |
|---|---|---|
| How much FG is in GP-FG right now? | **SAP** (`OITW`) | it is the book of record; factory-cli just re-serves it |
| Which batches expire in 30 days? | **SAP** (`OBTN` 17,505 rows) | batch management is ON in SAP |
| Which *carton* is on which pallet in which bin? | **only factory-cli** | `OSRN`=0 and `OBIN`=0 — SAP has no serial and no bin |
| Which cartons went on truck HR67C1036 against invoice 707260234? | **only factory-cli** | 127,100 `gate_core_salesdispatchboxscan` rows; SAP holds the invoice, not the scan |
| What did the chemist measure on this consignment? | **only factory-cli** | 10,740 `inspectionparameterresult` rows; `@QC_I`/`@QC_O` hold 25 abandoned rows |
| What was the OEE / downtime / waste on run 63? | **only factory-cli** | SAP `OWOR` holds PlannedQty and CmpltQty and nothing else |
| Did the physical count match the system? | **only jsap-cli** | `OINC`/`INC1`/`OIQR` = 0 in all three companies |

### The intercompany case — the cleanest illustration

`barcode_intercompanytransfer`: **3,075 transfers, `count(NULLIF(sap_doc_num,'')) = 0`**, window
2026-06-05 → 2026-07-29. Zero SAP documents. But in that *identical* window SAP recorded:

```sql
SELECT COUNT(*), SUM("DocTotal") FROM JIVO_OIL_HANADB.OINV
WHERE "CardName" LIKE '%JIVO MART%' AND "DocDate">='2026-06-05';   -- 130 invoices, ₹43.90 cr
SELECT COUNT(*), SUM("DocTotal") FROM JIVO_MART_HANADB.OPCH
WHERE "CardName" LIKE '%JIVO WELLNESS%' AND "DocDate">='2026-06-05'; -- 137 invoices, ₹43.99 cr
```

So the **value and the quantity DO move in SAP**, as a normal intercompany sale/purchase. What
does not move is the **carton-level chain of custody** (which specific 48,664 barcodes crossed,
scanned by whom, on which device). Ruling: the *money/qty* leg is **M**; the *carton lineage* is
**N**. Do not let anyone tell you Oil→Mart transfers are "missing from SAP" — the accounting is
there; the traceability is not.

---

## 7. STALENESS — the most dangerous thing in this domain

Three caches will answer a question with a confident wrong number instead of an error:

| cache | measured live | age today | risk |
|---|---|---|---|
| `test_supabase.oitm_master` (ecom `sap items`?) | `min(created_at)=2026-01-07 12:19:40.738793`, `max=…:42.357158`, 2,014 rows | **204 days**, one 1.6-second insert batch, never refreshed | carries an `onhand` column frozen at January stock |
| `test_supabase.warehouse_inventory` (ecom `sap stock-by-warehouse`?) | `min(last_synced_at)=2026-05-17 00:22`, `max=2026-05-18 23:52`, 110 rows | **73 days**, sync visibly dead | `distributor_inventory` and `in_transit_inventory` are **0 rows** |
| `factory_flow.sales_planning_requirement_*` | last refresh run `2026-06-16 15:15:52`, `source_schema JIVO_OIL_HANADB`, `triggered_by manual` | **44 days**; Beverages 2026-06-04; **never runs for Mart** | the only materialised SAP copy in the whole factory DB |

Plus `order_management.sap_products` (OMS's item mirror, incl. `on_hand`): 4,155 rows, last
`synced_at` **2026-07-28 13:08** — only ~2 days stale but manual-triggered (`sap_sync_schedules`
is empty), so it can silently drift.

And EXIM's `items get-rm` quantities **do not reconcile to SAP at all** — verified live today:

```sql
SELECT "ItemCode", SUM("OnHand") FROM JIVO_OIL_HANADB.OITW
WHERE "ItemCode" IN ('RM0000003','RM0000025','RM0000011','RM0000013') GROUP BY "ItemCode";
-- RM0000003 177,808.85  (EXIM says 132,814.19)
-- RM0000025 200,593.29  (EXIM says  85,247.00)
-- RM0000011   4,138.08  (EXIM says  20,001.98)
-- RM0000013  47,221.93  (EXIM says  16,200.00)
```

Four for four wrong, in both directions, by up to 2.4×. **Never quote EXIM RM quantities as SAP
stock.** (EXIM's `sap-sync get-inventory` *does* reconcile — BH-CRUDE/CANOLA 84,265.0 vs SAP
84,265.479 — so the SAP-sync family is fine and the cached `items` family is not.)

---

## 8. RESOLVED DISAGREEMENTS

1. **ecom-cli ruled `product_batches` U at confidence 45** ("could be a hand-keyed subset of SAP
   OBTN — I did not check"). **Resolved: N, confidence 96.**
   ```sql
   SELECT batch_number, count(*), count(manufacture_date) FROM product_batches GROUP BY 1;
   -- 'LIVE' | 78 | 0
   ```
   `batch_number` is the literal string `'LIVE'` on all 78 rows and `manufacture_date` is NULL on
   all 78. This is a listing-lifecycle flag, not a manufacturing batch. It has no relationship to
   SAP `OBTN`.

2. **factory-cli "F partial" on production runs / BOM requests / FG receipts** → overturned to
   **N** (§3.1, §3.2).

3. **hana-census "OWOR populated ⇒ factory is F"** → overturned to **M + N** (§3.3).

4. **factory-cli's own BST reclassification (F → reference)** → **upheld**, and I now have the
   mechanism: `B1i` never touches `OWTR`, and `warehouse_bsttransfer` is 134/134 born with a doc
   number (reference pattern) versus `grpo_grpoposting` 232/265 filled on success (feeder
   pattern).

5. **oms-cli left `dispatch_locations` at U (55)** — the 4 rows `WH-DEL/WH-GGN/WH-NOI/FAC-BGH`
   looked like non-SAP seed data. Partially resolved: the warehouse code actually used in
   production push payloads is `GP-FG`, which **is** a real SAP warehouse — `JIVO_OIL_HANADB.OWHS`
   `GP-FG = "GUPTA GODOWN BASEMENT FINISHED GODOWN"`. So OMS transacts on SAP warehouse codes; the
   4-row table is dev seed data in a non-production deployment. Ruling **M** at 80.

6. **factory-cli rated batches M at 85** ("only 300 batches, every expiry blank") → **upheld and
   raised to 95**: `OBTN` holds 17,505 rows in Oil, so the endpoint is a paged/filtered read of a
   genuinely populated SAP table, not a stub.

### Unresolved — stated plainly

- **Does ecom `sap items` / `sap stock-by-warehouse` proxy SAP live, or serve the frozen
  `oitm_master` / `warehouse_inventory` tables?** I could not settle it. The ecom API token is
  expired (`doctor` → `Credentials: invalid (HTTP 401)`) and the backend source is on the app
  server, not in this repo. Both stale tables exist and both are exactly the shape those
  endpoints would return. **Two cheap tests:** (a) get a fresh ecom token and compare
  `sap items --json` against `oitm_master`'s frozen `onhand` — an exact match means the stale
  copy; (b) read the `/api/sap` router on the app server.
- **The GRPO posting transport.** I proved the app creates OPDN rows as `B1i`; I did not
  establish whether that goes via Service Layer, DI API or a HANA procedure. Does not change any
  bucket.
- **What filter EXIM applies to produce its non-reconciling RM quantities.** I proved they are
  wrong against both `OITW` and a reconstruction from `OINM`; I could not reproduce the rule.

---

## 9. Two traps for anyone reading this domain off field names

**Trap 1 — bilty / transporter / vehicle / driver is TWO different things.**
In **factory-cli** (`dispatch_plans_dispatchplan`, 1,774 rows) it is native app data: driver
licence number, ID-proof type, kanta weight, bilty scan, a 10-stage pipeline. **N.**
In **control-panel** (`sales dispatch`, `accounts aging-oil`) the identically-named fields are
**SAP user fields on OINV** — `U_BilltyNumber, U_BiltyDate, U_Dipatch_Date, U_TransporterName,
U_VehicleNoM, U_DriverName, U_Mob_No, U_LRNUmber` — and the control-panel mapper matched all
eight values live for invoice 626070454. **M.** Same words, opposite bucket.

**Trap 2 — a SAP key on a row does not make the row SAP-sourced.**
`quality_control_materialtypesapitem` (135 rows) is an explicit link table joining a native QC
taxonomy to a SAP `item_code`. `production_execution_productionrun.sap_doc_entry` is an OWOR
*pointer* that repeats across rows. `jsap inventory report` returns `itemCode FG0000004` and
`warehouse DL-EC` — both real SAP codes — on a **physical count that SAP has never seen**
(`OINC`=0). Joined ≠ sourced-from.

---

## 10. Ruling table (condensed)

M = SAP mirror · F = feeder · N = native · X = external · U = unknown

| # | entity | systems | bucket | conf |
|---|---|---|---|---|
| 1 | Item / SKU master (OITM incl. U_TYPE/U_Sub_Group/U_Variety/U_SKU/U_Brand) | factory, ecom, oms, control-panel, jsap, exim | M | 98 |
| 2 | Warehouse master (OWHS) + item groups (OITB) | factory, jsap, control-panel | M | 98 |
| 3 | Stock on hand by item × warehouse (OITW) | factory, control-panel, ecom, exim, oms | M | 97 |
| 4 | Inventory movement ledger (OINM/OITL/OIVL) | factory | M | 96 |
| 5 | Inventory ageing / non-moving / DOH cuts | factory, control-panel | M (new maths) | 95 |
| 6 | Batch master + expiry (OBTN/OBTQ) | factory, oms | M | 95 |
| 7 | Production orders + component shortfall (OWOR/WOR1) | factory, control-panel | M | 98 |
| 8 | Production release (`PRODUCTION_RELEASE_OIL` view) | factory | M | 98 |
| 9 | Bill of materials (OITT/ITT1) | factory, control-panel | M | 93 |
| 10 | Inventory transfers (OWTR/WTR1) | factory, control-panel | M | 98 |
| 11 | Posted GRPO read-back + PO being received (OPDN/OPOR) | factory, jsap | M | 96 |
| 12 | Received-vs-billed (OPDN vs OPCH) | factory | M | 92 |
| 13 | Wellness↔Mart reconciliation chains | control-panel | M (new maths) | 97 |
| 14 | Sales-planning-vs-requirement | factory | M — **44d STALE** | 97 |
| 15 | ecom `oitm_master` | ecom/postsql | M — **204d STALE** | 97 |
| 16 | ecom `warehouse_inventory` | ecom/postsql | M — **73d STALE** | 95 |
| 17 | OMS `sap_products.on_hand` | oms/postsql | M — 2d, manual | 94 |
| 18 | EXIM `items get-rm` quantities | exim | **U** — does not reconcile | 55 |
| 19 | **Material + service GRPO posting** | factory | **F** | 98 |
| 20 | Barcode carton master + movements + audit | factory | **N** | 98 |
| 21 | Scan events (all families) | factory | **N** | 98 |
| 22 | Label print events | factory | **N** | 97 |
| 23 | Pallets / loose stock | factory | **N** | 96 |
| 24 | Scan-to-ship dispatch session | factory | **N** (refs M invoice) | 97 |
| 25 | Intercompany carton transfer | factory | **N** at carton grain; value+qty is M | 97 |
| 26 | Native bin/zone/cell WMS layer | factory | **N** | 93 |
| 27 | Production-run MES detail (segments, OEE, waste, costing, manpower) | factory | **N** | 96 |
| 28 | Production release/approval gate (`PRODUCTIONORDERSYNC`) | factory | **N**-inside-HANA | 95 |
| 29 | BOM request / material issue | factory | **N** | 95 |
| 30 | FG receipt | factory | **N** | 93 |
| 31 | Line clearance + checklists | factory | **N** | 94 |
| 32 | QC raw-material inspection + parameter results | factory | **N** | 98 |
| 33 | Material arrival slips + CoA/CoQ photos | factory | **N** | 96 |
| 34 | Online/production QC (torque, fill) | factory | **N** | 94 |
| 35 | QC form template + parameter masters | jsap, factory | **N** | 93 |
| 36 | Gate arrivals + weighbridge weighments | factory | **N** | 97 |
| 37 | FG gate-out / docking / gatepass + truck photos | factory | **N** | 96 |
| 38 | Docking scan exceptions (partial-scan / skip approvals) | factory | **N** | 96 |
| 39 | Dispatch plan / bilty / freight / driver (factory) | factory | **N** | 94 |
| 40 | Vehicle / driver / transporter master | factory | **N** | 96 |
| 41 | PET bottle blowing + make-vs-buy | factory | **N** | 90 |
| 42 | Physical stock count + variance | jsap | **N** | 97 |
| 43 | EXIM tanks (master / level / logs / item namespace) | exim | **N** | 98 |
| 44 | EXIM import stock lots + 9-stage lifecycle + audit trail | exim | **N** | 96 |
| 45 | Retailer / distributor channel stock declarations | dsr | **N** | 93 |
| 46 | ecom `product_batches` | ecom | **N** (was U/45) | 96 |
| 47 | Marketplace / platform dark-store inventory (SOH/DOH) | ecom, blinkit, zepto | **X** | 96 |
| 48 | Marketplace fulfilment dispatch (factory module) | factory | **N** (F for 50/2,116) | 88 |

---

## 11. What I did not do

- **No live app API call succeeded.** Every token in this workspace is expired. App-side evidence
  is live Postgres (`factory_flow` **is** the production DB — proved by the source-mapper and
  re-confirmed by me: `barcode_box` max `created_at` 2026-07-29) plus code plus the 2026-07-13
  raw captures. SAP-side evidence is live HANA throughout.
- I did **not** query DSR's SQL Server myself; the DSR channel-stock ruling leans on the dsr-cli
  mapper's live counts plus my own live proof that SAP has no channel-stock object. Caveat worth
  knowing: SAP *does* carry a handful of C&F/consignment warehouses at named agents
  (`PB-JP Punjab Grover Agency Jagraon C & F`, `PB-ST Punjab Sai Trading C & F`,
  `PB-SG`, `PB-SP`), so a *few* channel points are visible in SAP — the 127,395-outlet retailer
  base is not.
- I did **not** call Blinkit/Zepto portals (fresh OTP required); the X ruling rests on code plus
  the live fact that SAP holds only the counterparty BP cards.
- I did **not** open the `blowing_*` module beyond its schema (8 runs, no CLI endpoint).
