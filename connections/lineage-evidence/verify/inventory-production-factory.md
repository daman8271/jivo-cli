# ADVERSARIAL VERIFICATION — domain `inventory-production-factory`

Refuter pass. 2026-07-30. Every query below was run live by me, not inherited.

Tools that worked:
- HANA: `/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql -env /Users/damanpreetsingh/jivo-cli/connections/hana-tunnel.env "<SQL>"`
  (the plain `connections/hana.env` hangs — must use `hana-tunnel.env`, per ACCESS-CORRECTIONS)
- Postgres: `/Users/damanpreetsingh/jivo-cli/postsql/postsql -d <db> query "<SQL>"`
- EXIM CLI: `/Users/damanpreetsingh/jivo-cli/exim/exim items get-rm` — **live, works**
- ecom CLI: `doctor` → `Credentials: invalid (HTTP 401)` — **still dead**, open question unresolved
- DSR MSSQL: not attempted

---

## HEADLINE VERDICT

The domain ruling's spine is correct: SAP owns the balance and the document, the factory app
owns the event. I attacked every `N` and could not break one. But **the headline sentence is
factually wrong on its most quotable claim**, and two operational statements are wrong in a way
that would mislead someone acting on them.

| # | Claim under attack | Verdict |
|---|---|---|
| 1 | "exactly ONE thing in this domain flows back into SAP — the GRPO" | **REFUTED** |
| 2 | factory marketplace fulfilment module = `N` | **REFUTED → F** |
| 3 | GRPO feeder "live and current … latest 2026-07-28" | **REFUTED** — dead since 2026-07-15 |
| 4 | GRPO: "SAP lacks … 232 GRPO attachments" | **REFUTED** — those 232 are exactly what IS pushed to SAP |
| 5 | Batches: "Ask SAP for batches **and expiry**", confidence raised 85→95 | **REFUTED on expiry** — Mart has 0 expiry dates |
| 6 | Everything else (all 27 `N`, the `M` mirrors, the staleness figures) | **UPHELD**, several strengthened |

---

## 1. REFUTED — there is a SECOND feeder: Mart delivery notes

```sql
SELECT 'ODLN' T, COUNT(*) N FROM JIVO_MART_HANADB.ODLN P
  JOIN JIVO_MART_HANADB.OUSR U ON U."USERID"=P."UserSign" WHERE U."USER_CODE"='B1i';
-- 13
SELECT D."DocEntry", D."DocNum", D."DocDate", D."CardName", D."Comments"
  FROM JIVO_MART_HANADB.ODLN D JOIN JIVO_MART_HANADB.OUSR U ON U."USERID"=D."UserSign"
 WHERE U."USER_CODE"='B1i' ORDER BY D."DocEntry";
```

13 rows, 2026-07-18 → 2026-07-29, all `CUSTA000910 FLIPKART (B2C-MAY-JULY)`, comments literally:

```
12222 | 1507264739 | MARKETPLACE FLIPKART BULK DELIVERY NOTE · 48 ORDERS · FLIPKART B2C HARYANA · 2026-07-29
12224 | 1507264740 | MARKETPLACE FLIPKART BULK DELIVERY NOTE ·  2 ORDERS · FLIPKART B2C DELHI   · 2026-07-29
12073 | 1507264664 | MARKETPLACE FLIPKART BULK DELIVERY NOTE · 199 ORDERS · 2026-07-20
12107 | 1507264675 | LIVE CASE TEST DL - AUTO CANCEL
```

Row-for-row match on the app side:

```sql
-- factory_flow
SELECT sap_delivery_note_doc_entry, sap_delivery_note_num, count(*)
  FROM marketplace_marketplacedispatch WHERE sap_delivery_note_doc_entry IS NOT NULL GROUP BY 1,2;
-- 12222 | 1507264739 | 48      <- SAP comment says "48 ORDERS"
-- 12224 | 1507264740 |  2      <- SAP comment says " 2 ORDERS"
```

and `marketplace_marketplaceorderbilling` (50 rows) carries the same doc entry per buyer, e.g.
`invoice_number MKT-20260729-00001 / order_id OD438174840724407100 / sap_delivery_note_doc_entry 12222`.

**Conclusion:** the factory marketplace module posts real Mart delivery notes into SAP as `B1i`.
It is `F`, not `N`. The GRPO is not the only feeder. (The `LIVE CASE TEST … AUTO CANCEL` rows show
the integration was being commissioned in the last two weeks — this is new, live plumbing.)

Composite reading for the module: orders originate at Flipkart (`X`), the scan/pick/return work is
app-native (`N`), the bulk delivery note is `F`. SAP sees one aggregated document per batch; the app
holds per-buyer names, per-order billing, 2,800 fulfilment scans.

---

## 2. REFUTED — the GRPO feeder has been DOWN for 15 days

Ruling said: *"Material GRPO is live and current (265 postings, 232 with SAP doc numbers, latest 2026-07-28)."*
The 2026-07-28 is the latest **attempt**, not the latest SAP document.

```sql
-- factory_flow
SELECT max(created_at) FROM grpo_grpoposting WHERE sap_doc_num IS NOT NULL;
-- 2026-07-15 10:04:38.532182+05:30

SELECT created_at::date, count(*) n, count(sap_doc_num) posted
  FROM grpo_grpoposting WHERE created_at>='2026-07-10' GROUP BY 1 ORDER BY 1;
-- 2026-07-15 | 8 | 2
-- 2026-07-16 | 4 | 0
-- 2026-07-17 | 1 | 0   ... 2026-07-28 | 1 | 0

SELECT status, count(*) FROM grpo_grpoposting WHERE sap_doc_num IS NULL GROUP BY 1;
-- FAILED | 33
```

Corroborated SAP-side — last `B1i` GRPO in Oil is `DocDate 2026-07-14`:

```sql
SELECT COUNT(*), MIN(P."DocDate"), MAX(P."DocDate") FROM JIVO_OIL_HANADB.OPDN P
  JOIN JIVO_OIL_HANADB.OUSR U ON U."USERID"=P."UserSign" WHERE U."USER_CODE"='B1i';
-- 262 | 2026-03-11 | 2026-07-14
```

Error messages (`grpo_grpoposting.error_message`), newest first:

```
2026-07-28  Unable to connect to SAP file uploader
2026-07-27  SAP file uploader authentication failed
2026-07-22  SAP attachment metadata registration failed after uploader saved the file:
            Attachments folder not defined, or Attachments folder has been changed or removed
```

**Bucket `F` survives** (232 documents genuinely landed). The *"live and current"* characterisation
does not. Anyone told "the GRPO feeder is working" today would be misinformed — the last two weeks
of factory receipts exist only in the app.

---

## 3. REFUTED — the GRPO attachments ARE in SAP

Ruling listed among `fields_sap_lacks`: *"…232 GRPO attachments…"*. Exactly backwards.

```sql
-- factory_flow
SELECT sap_attachment_status, count(*), count(sap_absolute_entry) FROM grpo_grpoattachment GROUP BY 1;
-- LINKED  | 232 | 232
-- PENDING |   2 |   0
```

```sql
-- HANA
SELECT COUNT(*) TOT, COUNT(P."AtcEntry") WITH_ATC FROM JIVO_OIL_HANADB.OPDN P
  JOIN JIVO_OIL_HANADB.OUSR U ON U."USERID"=P."UserSign" WHERE U."USER_CODE"='B1i';
-- 262 | 262      (100% of app-posted GRPOs carry a SAP attachment)

SELECT A."AbsEntry", A."FileName", A."FileExt" FROM JIVO_OIL_HANADB.ATC1 A
 WHERE A."AbsEntry" IN (164917,164914);
-- 164914 | 657_v2  | pdf
-- 164917 | 0484_v2 | pdf
```

App side, same two rows: `original_filename '0484.pdf' → sap_absolute_entry 164917 (LINKED)`,
`'657.pdf' → 164914 (LINKED)`. `ATC1.trgtPath` decodes to `\\20.20.45.25\Attachments_Oil\JIVO_OIL\Attachments`
— the Windows share the briefing warned about. So the file is in SAP as a *document*, not as a queryable column.

**What SAP still genuinely lacks** (I re-checked and this part holds): the QC lab readings, the two-signature
decision trail, the rejected quantity, and the **arrival-slip CoA/CoQ scans** —
`quality_control_arrivalslipattachment` (1,179 rows) has **no `sap_*` column of any kind**:

```sql
SELECT table_name, column_name FROM information_schema.columns
 WHERE table_schema='public' AND table_name LIKE 'quality_control%' AND column_name ILIKE '%sap%';
-- only: quality_control_rawmaterialinspection.sap_code
```

So: **the vendor bill reaches SAP with the GRPO; the lab certificate does not.**

---

## 4. REFUTED — "ask SAP for batches and expiry" is wrong on expiry

The phase-2 agent raised the batch ruling 85 → 95 arguing the factory-cli agent had only seen
"300 batches with blank expiry" while `OBTN` really holds 17,505 rows. Wrong statistic — row count,
not field fill:

```sql
SELECT 'OIL' CO, COUNT(*) TOT, COUNT("ExpDate") WITH_EXP, COUNT("InDate") WITH_MFG FROM JIVO_OIL_HANADB.OBTN
UNION ALL SELECT 'MART', COUNT(*), COUNT("ExpDate"), COUNT("InDate") FROM JIVO_MART_HANADB.OBTN
UNION ALL SELECT 'BEV',  COUNT(*), COUNT("ExpDate"), COUNT("InDate") FROM JIVO_BEVERAGES_HANADB.OBTN;
-- OIL  | 17505 | 6152 | 17322   (35% have an expiry date)
-- MART | 10076 |    0 | 10061   (ZERO)
-- BEV  |  2113 |  810 |  2027   (38%)
```

The original factory-cli doubt was correct. Bucket `M` for the batch object stands (batch number +
manufacturing date are SAP's), but **SAP cannot answer an expiry question for Mart at all**, and answers
it for barely a third of Oil. Confidence should go back down, and the operator advice must be split.

Related: `PRODUCTION_RELEASE_OIL` exposes `U_BATCH_NO / U_MFG / U_EXP_DATE` from `OWOR` — and per the
sapmap those three are 0-populated on all 7,858 orders, so those columns come back blank.

---

## 5. UPHELD AND STRENGTHENED — every `N` survived

### 5.1 My own absence sweep (I did not reuse the sapmap list)

```sql
SELECT SCHEMA_NAME, TABLE_NAME, RECORD_COUNT FROM M_TABLES
 WHERE SCHEMA_NAME LIKE 'JIVO%' AND RECORD_COUNT>0
   AND (UPPER(TABLE_NAME) LIKE '%BARCODE%' OR ... 30 keywords ...);
-- ZERO ROWS
```
Keywords swept: BARCODE, CARTON, BOX, PALLET, SCAN, TANK, GATE, WEIGH, BLOW, OEE, DRIVER, VEHICLE,
BILTY, BILLTY, LABEL, PRINT, INSPECT, DOWNTIME, WASTE, DISPATCH, DOCK, CLEARANCE, CHECKLIST, ARRIVAL,
COUNT, AUDIT, STOCKTAKE, SHIFT, MACHINE, BREAKDOWN, PREFORM, BOTTLE, KANTA, TRANSPORT. **Nothing.**

Standard objects, all three companies, one query:
```
OSRN 0/0/0 · OSRQ 0/0/0 · OBIN 0/0/0 · OBBQ 0/0/0 · OPKG 0/0/0 · OSHP 0/0/0
OWKO 0/0/0 · OPWZ 0/0/0 · OINC 0/0/0 · INC1 0/0/0 · OIQR 0/0/0 · ODPS 0/0/0
ORSC 7/2/1
```
Every zero the domain ruling depends on is real. (OPKL pick lists are **not** zero — 3,598/702/1,310 —
but pick lists are a picking document, not a truck-loading session; no ruling turns on it.)

Complete listing of every populated non-`@` custom table inside all three SAP schemas (50 rows) contains
no factory-operations object: it is entirely approval workflow (`JS_SYNC_BUDGET_APPROVAL_WORKFLOW` 29,212,
`tbl_Draft_Approvals`), the WhatsApp bot, `PRODUCTIONORDERSYNC`, the vendor/customer portals, and report caches.

### 5.2 The trap the ruling missed — and it resolves in the ruling's favour

`U_carton` and `U_cartonpc` **are defined on all 32 SAP line tables** (`INV1 PDN1 IGN1 IGE1 WTR1 DLN1 …`).
Anyone sweeping field names would call this a carton hit. They are 100% empty:

```sql
SELECT 'INV1', COUNT(*), SUM(CASE WHEN IFNULL("U_carton",'')<>'' THEN 1 ELSE 0 END) ... ;
-- INV1 96900 → 0    PDN1 24410 → 0    IGN1 16778 → 0    WTR1 51439 → 0    DLN1 24241 → 0
```
Defined, never used. The carton `N` ruling is safe *and* now has a named counter-hypothesis killed.

One real partial hit worth flagging: `WOR1.U_WASTAGE_QUANTITY` is filled on **24,893 of 51,104** lines
and non-zero on **737** (145 production orders, 2025-09-11 → 2026-06-23). So SAP *does* hold a wastage
quantity at production-order-line grain. It is not OEE/downtime/waste-log detail, but the MES ruling's
"SAP holds PlannedQty and CmpltQty and nothing else of this" overstates it slightly.

### 5.3 Direction of flow — re-proved myself

```sql
SELECT U."USER_CODE", U."U_NAME", COUNT(*) FROM JIVO_OIL_HANADB.OWOR W
  LEFT JOIN JIVO_OIL_HANADB.OUSR U ON U."USERID"=W."UserSign" GROUP BY 1,2 ORDER BY 3 DESC;
-- USER24 Gautam CHanana 6003 · USER01 AVTAR SINGH 510 · manager 347 · USER06 LOVPREET 334 · USER32 PANKAJ 276
-- B1i: ABSENT
```

`B1i` footprint by object (Oil): `OPDN 262 · OIGN 0 · OIGE 0 · OWTR 0 · OWOR 0 · ODLN 0 · OPOR 0 · OINV 2`.
Mart: `ODLN 13` (the marketplace feeder above), everything else 0. Bev: `OPDN 151 · OINV 5`.
No other service account (`Workflow`, `Support`, `AlertSvc`, `EDsUser`, `BACKUP`) created a single document.

Caveat I owe: `UserSign` identifies the *login* used, and a DI-API integration could in principle post as a
named user. The `B1i` concentration plus the app's own stored `sap_doc_entry` values make that unlikely here,
but "zero B1i rows" is evidence of absence only if every integration authenticates as B1i.

### 5.4 App-side overturns re-verified

```sql
-- production runs: pointer, not feeder
SELECT sap_doc_entry, sap_sync_status, count(*) FROM production_execution_productionrun GROUP BY 1,2;
-- (null) NOT_APPLICABLE 72 · 2650 NOT_APPLICABLE 4 · 3651 NOT_APPLICABLE 4 · 2650 FAILED 2 · 3651 FAILED 1
-- · 6189 FAILED 1 · 6175 NOT_APPLICABLE 1 · 2945 NOT_APPLICABLE 1
-- 86 rows, 14 with a doc entry, only 5 DISTINCT values, sap_receipt_doc_entry NULL on ALL 86.

SELECT material_issue_status, sap_issue_doc_entries, count(*) FROM warehouse_bomrequest GROUP BY 1,2;
-- NOT_ISSUED | [] | 72        (single group — nothing ever issued)

SELECT id, sap_doc_entry, sap_receipt_doc_entry FROM warehouse_finishedgoodsreceipt;
-- 3 rows, receipt entry NULL on all

SELECT sap_object_type, sap_update_status, count(*), min(created_at)::date, max(created_at)::date
  FROM barcode_dispatchsession GROUP BY 1,2;
-- AR_INVOICE | NOT_CONFIGURED | 185 | 2026-06-01 | 2026-06-26

SELECT count(*), count(NULLIF(sap_doc_num,'')), bool_or(sap_enabled) FROM barcode_intercompanytransfer;
-- 3075 | 0 | false
```

All four overturns hold. **One sharpening:** production runs carry `sap_sync_status='FAILED'` on 4 rows,
so a push path *exists in code* and has simply never succeeded. "Broken feeder" is a truer description than
"pure native"; the bucket stays `N` because nothing has ever landed.

`PRODUCTIONORDERSYNC` re-checked live: 2,499 Oil rows, `SAPSTATUS='PENDING'` on **all** of them,
`STATUS` A=2,496 / R=2 / P=1, `CREATEDON` 2025-10-25 → 2026-07-29, and
`LEFT JOIN OWOR ON DocEntry` matches **2,499 of 2,499**. Reference, not creation. `N` holds.

`barcode_palletmovement.sap_transfer_doc_entry`: 7,120 rows, **0** populated. Pallets `N` holds.

### 5.5 A false alarm I raised and then killed (reporting honestly)

The ruling contrasts `gate_core_salesdispatchgateout` (801/801 filled) with
`gate_core_emptyvehiclegatein` ("0 of 817"). My first count said 817/817. Wrong — the column is a
varchar and every value is the **empty string**, which `count()` counts:

```sql
SELECT count(*) total, sum(CASE WHEN sap_doc_num IS NULL OR sap_doc_num::text='' THEN 1 ELSE 0 END) blank
  FROM gate_core_emptyvehiclegatein;   -- 817 | 817
```
The ruling was right. My objection is withdrawn.

---

## 6. `M` rulings — staleness figures re-measured, all exact

| Mirror | Ruling claimed | I measured | Verdict |
|---|---|---|---|
| `test_supabase.oitm_master` | 2,014 rows, one 1.6s batch 2026-01-07, 204 d stale | `2014 · 2026-01-07 12:19:40.738793 → 12:19:42.357158` | exact |
| `test_supabase.warehouse_inventory` | 110 rows, 2026-05-17→18, 73 d stale | identical; `distributor_inventory` 0; `in_transit_inventory` 0 | exact |
| `order_management.sap_products` | 4,155 rows, on_hand on 4,154, 2026-05-13→2026-07-28, `sap_sync_schedules` 0 | identical | exact |
| `sales_planning_…refreshrun` | Oil last success 2026-06-16 15:15, Bev 2026-06-04, never Mart | `JIVO_OIL_HANADB success 2026-06-16 15:15:52.833727` (6 runs), `JIVO_BEVERAGES_HANADB success 2026-06-04 19:05:08` (2 runs), no Mart row | exact |
| `test_supabase.product_batches` | one group `'LIVE'` \| 78 \| 0 mfg | `LIVE \| 78 \| mfg 0 \| exp 78` | exact |

### 6.1 RESOLVED — the OMS mirror's fidelity (ruling's 6% uncertainty)

The ruling could not prove the OMS copy was faithful because its sync reads an MSSQL at
`103.89.45.75`, not the HANA this repo queries. Settled by value:

```sql
-- order_management
SELECT item_code, on_hand FROM sap_products WHERE item_code='RM0000052';
-- RM0000052 | 294992.524500
```
```sql
-- HANA, live now
SELECT "ItemCode", SUM("OnHand") FROM JIVO_OIL_HANADB.OITW WHERE "ItemCode"='RM0000052' GROUP BY "ItemCode";
-- RM0000052 | 589985049/2000  =  294992.5245
```
**Exact to four decimals.** Others differ only in the direction and size you would expect from a
2-day-old snapshot (`RM0000003` OMS 174,508.3078 vs SAP 177,808.8478; `RM0000011` OMS 23,166.0849 vs
SAP 4,138.0849 — a clean 19,028.0000 whole-number movement). Whatever the transport, the numbers are
SAP's `SUM(OITW.OnHand)`. Category split confirms all three companies: `OIL 1534 · BEVERAGES 1530 · MART 1091`.

### 6.2 Sampled SAP rows re-verified verbatim

```sql
SELECT "DocEntry","DocNum","Comments" FROM JIVO_MART_HANADB.OWTR WHERE "DocEntry"=3306;
-- 3306 | 726674571 | Based On Inventory Transfers 726674570.
SELECT "DocEntry","DocNum","ItemCode","Warehouse","Status","PlannedQty","CmpltQty"
  FROM JIVO_MART_HANADB.OWOR WHERE "DocEntry"=39;
-- 39 | 825926501 | FG0000326 | DL-MP | R | 160 | 160
```

### 6.3 `PRODUCTION_RELEASE_OIL` — definition read live, matches the ruling

`SELECT DEFINITION FROM SYS.VIEWS WHERE SCHEMA_NAME='JIVO_OIL_HANADB' AND VIEW_NAME='PRODUCTION_RELEASE_OIL'`
decodes to:
```sql
SELECT A."DocEntry", A."DocNum", CAST(A."PostDate" AS DATE), A."ItemCode", C."ItemName",
       C."U_IsLitre" AS "Liter Countable", C."ManBtchNum",
       CAST(A."PlannedQty" AS DECIMAL(19,0)) AS "PlannedQty",
       CAST(A."PlannedQty"/C."SalFactor2" AS DECIMAL(19,2)) AS "Box",
       CAST(A."PlannedQty"*C."SalPackUn" AS DECIMAL(19,2)) AS "Liter", ...
       A."U_BATCH_NO", CAST(A."U_MFG" AS DATE), CAST(A."U_EXP_DATE" AS DATE), A."Status"
FROM OWOR A INNER JOIN OITM C ON C."ItemCode"=A."ItemCode"
WHERE C."Series" IN (389,393) AND C."ManBtchNum"='Y' AND A."Status"='R'
```
Exists in `JIVO_OIL_HANADB` and `TEST_OIL_15122025` only — hence the raw HANA error 259 for Mart. `M` at 98 confirmed.

---

## 7. `U` — EXIM raw-material aggregates: still unknown, but narrowed

EXIM CLI is **live** (`meta.source: "live"`, 23 RM items). Two hypotheses killed:

1. **It is EXIM's own accumulator, not a SAP read.** `total_qty = total_in_qty − total_out_qty`
   holds arithmetically on all 23 rows (e.g. RM0000003: 10,303,852.0551 − 10,171,037.8683 = 132,814.1868).
2. **It is not a stale SAP snapshot.** I built the SAP running balance by month from `OINM`:
   ```sql
   SELECT "ItemCode", TO_VARCHAR("DocDate",'YYYY-MM'),
          SUM(SUM("InQty")-SUM("OutQty")) OVER (PARTITION BY "ItemCode" ORDER BY TO_VARCHAR("DocDate",'YYYY-MM'))
     FROM JIVO_OIL_HANADB.OINM WHERE "ItemCode" IN ('RM0000003','RM0000011','RM0000025') GROUP BY 1,2;
   ```
   **No month-end balance equals the EXIM figure** for RM0000011 (EXIM 20,001.9758; SAP monthly series
   9,018.71 / 52,181.18 / … / 4,138.08) or RM0000025 (EXIM 85,247.008; closest SAP month-end 84,724.4817).

3. **It is not tank stock either.** `exim tank get-item-wise-summary` returns a different namespace
   (`RM0EL`, `RM00SB`, `RM00POM`, `RM00CN`) with round quantities (14,800 / 39,000 / 51,000 / 279,000 L).

So the number is computed inside EXIM from EXIM-held accumulators that reconcile to no SAP figure at
any date I tested. Whether those accumulators are fed by a broken SAP sync (→ `M` with a bug) or by
EXIM's own lot/tank events (→ `N`) needs the EXIM backend source, which is not in this repo. **`U` is
the honest bucket and I am upholding it.** The operator warning ("do NOT quote these as SAP stock") is
correct and should be kept verbatim.

---

## 8. `X` — marketplace inventory: SAP-absence half verified myself

```sql
SELECT "WhsCode","WhsName" FROM JIVO_OIL_HANADB.OWHS ORDER BY "WhsCode";   -- 58 rows
SELECT "TableID","AliasID","Descr" FROM JIVO_OIL_HANADB.CUFD
 WHERE UPPER("AliasID") LIKE '%BLINK%' OR '%ZEPTO%' OR '%AMAZON%' OR '%FLIPKART%'
    OR '%SWIGGY%' OR '%MARKET%' OR '%CHANNEL%' OR '%DARKSTORE%' OR '%SOH%' OR '%DOH%' OR '%RETAIL%';
-- ZERO ROWS
```
No marketplace or dark-store warehouse in `OWHS`; no marketplace user field anywhere. `X` holds.

**Sharpening of the C&F caveat** (the ruling named 4; there are more): `PB-JP Punjab Grover Agency
Jagraon C & F`, `PB-ST Punjab Sai Trading C & F`, `PB-SG Punjab Sai Trading GR C & F`, `PB-SP PUNJAB
SANGRUR ONENESS`, plus `PB-RG PUNJAB SANGRUR ONENESS GR`, and three **drop-ship** warehouses
`DP-DL / DP-HR / DP-PB` that also sit at third parties. Two e-commerce warehouses `BH-EC`, `DL-EC`.
So the "SAP stock stops at JIVO-owned warehouses" line has ~8 exceptions, not 4.

---

## 9. STILL OPEN (I could not close these)

1. **ecom `/api/sap/items` live vs frozen** — `jivo-ecom-pp-cli doctor` → `Credentials: invalid (HTTP 401)`.
   Backend source is not in this repo. Unchanged. Still the highest-risk item in the domain.
2. **DSR channel stock row counts** — I did not query the MSSQL at `103.89.45.75:1433`. The SAP-side
   absence proof is mine and holds; the 585,626 / 18,767 row counts are inherited from the dsr mapper.
3. **GRPO transport mechanism** — the failure messages name a *"SAP file uploader"* service distinct from
   the document post, so at least two channels are involved. I still did not identify Service Layer vs DI API.
4. **The 23-document gap** — app-side postings (232 material + 158 service = 390) vs SAP-side `B1i` GRPOs
   (262 Oil + 151 Bev = 413). 23 unexplained `B1i` GRPOs. Small, but it means something else also posts as `B1i`.
5. **The other 11 B1i Mart delivery notes** — only 2 of the 13 (`12222`, `12224`) are referenced from
   `marketplace_marketplacedispatch`. The other 11 (199 / 305 / 181-order batches) trace to nothing I found
   in factory_flow. Either the app purged its side or a second pusher exists.
