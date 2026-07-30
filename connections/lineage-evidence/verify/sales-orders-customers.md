# ADVERSARIAL VERIFICATION — domain `sales-orders-customers`

Refuter pass, 2026-07-30 ~03:15-04:10 IST. Every number below was pulled live by me.

**Stores I reached (all live):**
- SAP HANA via tunnel — `./hana-sql/hana-sql -env connections/hana-tunnel.env "<SQL>"` (the plain
  `hana.env` hangs; see ACCESS-CORRECTIONS)
- DSR SQL Server `DSR_V6` @103.89.45.75:1433 — built `dsr-cli` (`cd dsr-cli && go build -o dsr .`),
  `DSR_USER=ab DSR_PASSWORD=... ./dsr query "<T-SQL>"`
- Postgres cluster — `./postsql/postsql -d <db> query "<SQL>"`
- EXIM CLI — `cd exim && ./exim sap-sync get-open-ar --json`
- Control-panel CLI — `cd control-panel/cli/jivo && ./jivo accounts claims --json` (read-only GET)
- **NOT reachable:** ecom API (token 401, `doctor` says invalid), OMS API (token expired)

---

## HEADLINE — what changed

| # | Ruling | Was | Now | Why |
|---|---|---|---|---|
| 1 | **DSR primary sales 2026-05+** | M@97 | **N@92** | 55% of rows in that window (820 of 1,483) have a **SUPER STOCKIST as seller**, not JIVO. SAP has no such document. |
| 2 | **Customer/BP master** | M@98 | M@96 **REFUTED claim** | OMS mirror is 3,350 rows over only **1,251 distinct card_codes** — a 3-company union with no company key. `CUSTA000912` = 3 different companies. Not a "strict lossy subset". |
| 3 | **Dispatch/freight on invoice** | M@99 | M@93 **REFUTED claim** | `U_DriverName` 498/30,477 (1.6%), `U_LRNUmber` 43/30,477 (0.14%). On the *exact invoice* cited as proof (626070454) both are NULL. |
| 4 | **OMS A/R invoice module** | F@78 | **U@80** | No POSTED_TO_SAP row matches a SAP invoice created at that time. The 6 base orders were invoiced in May/June by humans, 2 months before the July log rows; 2 of 6 never invoiced at all. |
| 5 | **DSR sap_sales_log** | M@96 | M@95 **REFUTED claim** | Its DocNums *do* resolve — **1,918/1,918** — against the pre-HANA SAP B1 company DB `Jivo_All_Branches_Live`, which is **still online** on the same MSSQL box. "Ignore it entirely" is wrong. |
| 6 | **GST IRN** | M@96 | M@94 | `U_UTL_IRN` is populated on **15,623 of 17,695**, not "all 17,695". |
| 7 | **DSR primary pre-2026-05** | U@55 | U@75 **REFUTED claim** | "No key exists" is false — `from_retailerid` classifies every row. 6,784 JIVO-seller / 838 super-stockist / 3,455 unattributed. |

Everything else survived. The N block is, on my own re-testing, **stronger** than the ruling claimed.

---

## 1. THE BIG ONE — DSR `tbl_primary_sales` is NOT a SAP mirror

The ruling reversed phase-1's N to M@97 on one test: *"184 of 185 distinct bill_numbers resolve to
JIVO_OIL_HANADB.OINV DocNums."* **I reproduced that test exactly and it is true — and it is also
a 39% sample presented as the whole.**

### 1.1 The DocNum test replicates

```sql
-- DSR
SELECT DISTINCT LTRIM(RTRIM(bill_number)) FROM tbl_primary_sales
WHERE ISNUMERIC(bill_number)=1 AND LEN(LTRIM(RTRIM(bill_number)))>=8;   -- 186 distinct
-- HANA
SELECT COUNT(DISTINCT "DocNum") FROM "JIVO_OIL_HANADB"."OINV" WHERE "DocNum" IN (<those 186>);
--   OIL 184 | MART 0 | BEV 0
```
Confirmed. 184/186.

### 1.2 But those 186 values cover only 39% of the billed rows

```sql
SELECT CASE WHEN ISNUMERIC(bill_number)=1 AND LEN(LTRIM(RTRIM(bill_number)))>=8 THEN 'NUMERIC8+'
            WHEN bill_number LIKE 'SS%' THEN 'SS-series'
            WHEN bill_number LIKE 'TS%' THEN 'TS-series' ELSE 'OTHER' END kind,
       COUNT(*) rows_, COUNT(DISTINCT bill_number) distinct_
FROM tbl_primary_sales WHERE bill_number IS NOT NULL AND LTRIM(RTRIM(bill_number))<>'' GROUP BY 1;
```
| kind | rows | distinct |
|---|---|---|
| NUMERIC8+ (SAP DocNum shape) | **478** | 189 |
| OTHER | **649** | 274 |
| SS-series | 85 | 20 |
| TS-series | 6 | 5 |

The "OTHER" values are `AA/1186/26-27`, `OT/678/26-27`, `SINV-26/27-000033`, `AD-147`, `260/26-27`,
and bare 3-digit bill-book numbers `327`, `339`, `405`, `123`, `000134`. **The dsr-cli mapper's
original statement — "a 3-digit bill book, not a SAP DocNum" — is true of a large slice of the
CURRENT data, not just the old rows.** The ruling's "true of old rows and false of current ones" is
wrong.

### 1.3 The discriminator the ruling never used: `from_retailerid`

```sql
SELECT CASE WHEN ISNUMERIC(p.bill_number)=1 AND LEN(...)>=8 THEN 'SAP-DOCNUM' ELSE 'NON-SAP' END,
       f.retailerName, f.[type], COUNT(*)
FROM tbl_primary_sales p LEFT JOIN tbl_retailers f ON f.id=p.from_retailerid ... GROUP BY ...;
```
| kind | seller | rows |
|---|---|---|
| SAP-DOCNUM | **JIVO WELLNESS** (id 9771) | **471** of 478 |
| NON-SAP | GROVER AGENCY (SUPER) | 277 |
| NON-SAP | ARJAN DASS & SONS (SUPER) | 117 |
| NON-SAP | Sakshi sales / ROYAL SUPER SALES / OJAS / Aggarwal / ABNASH BROTHERS SUPER / … | 346 |

Rows where the bill_number is a SAP DocNum are almost exactly the rows where **JIVO is the seller**.
Rows with a bill-book number are **super-stockist → sub-distributor** sales.

Sample, live, dated *yesterday*:
```
GROVER AGENCY (SUPER) -> RAJEEV KUMAR RAM LAL           bill 768  2026-07-29
GROVER AGENCY (SUPER) -> DEEPAK TRADING CO. (PATIALA)   bill 765  2026-07-29  qty 200
GROVER AGENCY (SUPER) -> UNIVERSAL SALES                bill 764  2026-07-29
```

### 1.4 The killer test — does SAP invoice those buyers?

```sql
SELECT "CardCode",COUNT(*) FROM "JIVO_OIL_HANADB"."OINV"
WHERE "CardCode" IN ('CUSTA000394','CUSTA000477','CUSTA000941','CUSTA000631','CUSTA000912') GROUP BY 1;
```
- `CUSTA000394` DEEPAK TRADING COMPANY PATIALA → **0 invoices, ever**
- `CUSTA000477` RAJEEV KUMAR RAM LAL → **0**
- `CUSTA000631` GROVER AGENCIES JAGRAON → **0**
- `CUSTA000941` BALAJI TRADING CO → 1, in 2024-11
- `CUSTA000912` PARSHOTAM LAL VISHWA NATH → 21, but all SOYABEAN 13 KG tins — a different line from
  the Coldpress/Pomace/Groundnut on the DSR rows

These parties exist as OCRD cards but **JIVO does not bill them**. SAP stops at the super stockist:
`SELECT "U_Chain",COUNT(*) FROM OCRD GROUP BY 1` → `SUPER STOCKIST` **35**, `DISTRIBUTOR` 684,
`RETAILER` 33.

### 1.5 Split of the exact window the ruling declared M

```sql
SELECT CASE WHEN [date]<'2026-05-01' THEN 'pre' ELSE 'from-2026-05' END,
  SUM(CASE WHEN from_retailerid=9771 THEN 1 ELSE 0 END) jivo,
  SUM(CASE WHEN from_retailerid IS NULL OR from_retailerid=0 THEN 1 ELSE 0 END) nullz,
  SUM(CASE WHEN from_retailerid NOT IN (0,9771) THEN 1 ELSE 0 END) other_, COUNT(*) FROM tbl_primary_sales GROUP BY 1;
```
| window | JIVO seller | super-stockist/other | unattributed | total |
|---|---|---|---|---|
| **from 2026-05** | 629 | **820** | 34 | 1,483 |
| pre 2026-05 | 6,784 | 838 | 3,455 | 11,077 |

By month, 2026-07: **94 JIVO / 244 non-JIVO (72% non-SAP).**

**Verdict.** The entity is mixed. The ruling's operator advice — *"Never use DSR primary for sales
numbers … ask SAP"* — would throw away the **only record JIVO has of the super-stockist leg**.
Final bucket **N**, because the table cannot be replaced by SAP. The M subset is real and precisely
identifiable: `from_retailerid = 9771` AND numeric bill_number.

---

## 2. OMS → SAP quotation feed (F) — UPHELD, verified independently

```sql
SELECT "UserSign", COUNT(*), MIN("CreateDate"), MAX("CreateDate") FROM "JIVO_OIL_HANADB"."OQUT" GROUP BY 1;
--  2 (=B1i)  1351  2026-02-11 → 2026-07-25     |  1 (manager) 330  |  22 SUMIT 6 | 40 2 | 38 1 | 15 1
SELECT "UserSign", COUNT(*) FROM "JIVO_OIL_HANADB"."ORDR" GROUP BY 1;   -- B1i: exactly 1, ever
SELECT TABLE_NAME,RECORD_COUNT FROM M_TABLES WHERE TABLE_NAME='OQUT';   -- Oil 1691 | Mart 0 | Bev 733
```
`OUSR` lookup confirms `USERID 2 = B1i`. Monthly `RDR1.BaseType=23` conversion reproduces the
ruling's figures **exactly**: Feb 63/584, Mar 98/477, Apr 79/487, May 375/533, Jun 301/454, Jul 201/418.

**End-to-end join I ran that the ruling did not.** All 221 distinct `sap_doc_num` values with
`status='SUCCESS'` in `order_management.sales_quotation_logs`:
```
OIL_OQUT 221/221   (214 of them UserSign=2)   BEV 137 (numbering collision)   MART 0
```
**100% of OMS's successful pushes land in JIVO_OIL_HANADB.OQUT.** F confirmed.

### 2.1 The feed really is dark — confirmed
```sql
SELECT "CreateDate",COUNT(*) FROM OQUT WHERE "UserSign"=2 AND "CreateDate">='2026-07-10' GROUP BY 1;
Oil: 07-22:30  07-23:18  07-25:1   then NOTHING
Bev: 07-22:16  07-23:14  07-24:2   then NOTHING
SELECT "CreateDate",COUNT(*) FROM ORDR WHERE "CreateDate">='2026-07-20' GROUP BY 1;
     07-25:19  07-27:32  07-28:46  07-29:42     <- SAP orders kept flowing
```
Three working days of silence (07-27/28/29) against 8-30/day. **Still the most urgent item in the report.**

### 2.2 Two corrections to the F ruling
- **`sales_quotation_logs.sap_doc_entry` is WRONG.** OMS says DocEntry 14584 for DocNum 232607000;
  SAP says DocEntry **15280** (DocEntry 14584 is a different June quotation). Only `sap_doc_num`
  joins. The claim "matched 400/400 on (DocEntry, CardCode, DocNum)" cannot be true of this table.
- **The reachable OMS Postgres is not a full record.** `orders` holds **85 rows, ids 22-107,
  2026-07-06→07-28**, while `sales_quotation_logs` references order_ids up to 561 — **310 of 395
  logs are orphaned**. The DB looks re-seeded ~2026-07-06. Phase-1's own sourcemap already warned
  *"Production oms.jivo.in's DB is not on this Postgres cluster"*; the ruling dropped that caveat
  while promising OMS holds the rich pre-SAP detail.

---

## 3. OMS A/R invoice module — F@78 does not survive

```sql
SELECT id, so_number, invoice_payload->'DocumentLines'->0->>'BaseEntry' FROM invoice_log WHERE status='POSTED_TO_SAP';
--> BaseEntry 26846, 27122, 26714, 26610, 27206, 27322   (logged 2026-07-22/23)
```
All six resolve to real Oil sales orders — DocEntry/DocNum/CardCode match `so_number` exactly. The
read half is proven M. But:
```sql
SELECT h."DocNum",h."DocDate",h."CreateDate",h."UserSign" FROM INV1 l JOIN OINV h ...
WHERE l."BaseType"=17 AND l."BaseEntry" IN (26714,27122,27322);
  626050436 / 626050435  CreateDate 2026-05-21  UserSign 24 (HARPREET)
  626050684              CreateDate 2026-05-31  UserSign 22 (SUMIT)
  626060106              CreateDate 2026-06-02  UserSign 24
-- BaseEntry 26846 and 27206: NO invoice at all
SELECT "UserSign",COUNT(*) FROM OINV WHERE "CreateDate">='2026-04-01' GROUP BY 1;
  24:1272  22:390  19:215  25:142  35:142  20:69  1:20 …   -- ZERO rows for UserSign=2 (B1i)
```
The invoices exist **two months before** the OMS "POSTED_TO_SAP" entries and were keyed by named
humans. This reads as the module being exercised against already-invoiced historical orders.
**No evidence the production OMS invoice module posts to production SAP.** → **U**.

---

## 4. Customer master — bucket M survives, the safety claim does not

```sql
SELECT COUNT(*) total, COUNT(DISTINCT card_code) FROM order_management.sap_parties;
--> 3350 rows, 1251 distinct card_codes
SELECT card_code, card_name FROM sap_parties WHERE card_code='CUSTA000912';
  CUSTA000912  PARSHOTAM LAL VISHWA NATH
  CUSTA000912  SHREE KRISHNA ENTERPRISES
-- and in SAP:  Mart OCRD CUSTA000912 = "AMAZON (B2C -MAY-JULY)"
```
Customers per company: Oil **1,170** · Mart **937** · Bev **1,244** = **3,351**. So OMS mirrors the
union of all three books into one un-namespaced `card_code` column **with no company field**, giving
2,099 duplicate-key rows. Resolving a CardCode in OMS returns the wrong party roughly two times in
three. That is not a "strict, lossy subset" — it is a lossy merge that destroys the primary key.

Freshness correction: `MAX(synced_at)` on `sap_parties` and `sap_party_addresses` is **2026-07-28**,
and all five sync types ran that day (367 log rows, 313 `triggered_by='manual'`). The ruling's
"last full sync 2026-07-16" is 12 days out of date. `sap_sync_schedules` = 0 rows — the "no cron"
finding is correct. `sap_parties` has no balance column — correct.

---

## 5. Dispatch / freight fields — the "anti-trap" ruling has its own trap

```sql
SELECT COUNT(*) TOT,
 SUM(CASE WHEN LENGTH(TO_NVARCHAR("U_BilltyNumber"))>0 THEN 1 ELSE 0 END) …
FROM "JIVO_OIL_HANADB"."OINV";
```
| field | populated / 30,477 | since 2026-04 (/2,253) |
|---|---|---|
| U_Dipatch_Date | 10,034 | — |
| U_BilltyNumber | 9,018 (30%) | 1,636 (73%) |
| U_TransporterName | 8,745 | 1,536 (68%) |
| U_BiltyDate | 8,582 | — |
| U_VehicleNoM | 8,424 | — |
| U_Mob_No | 5,980 | — |
| **U_DriverName** | **498 (1.6%)** | **3** |
| **U_LRNUmber** | **43 (0.14%)** | — |

And on the very invoice the ruling cites as proof:
```
DocNum 626070454 | BIL 3698 | 2026-07-22 | Mahaveer Transport | HR67C1036 | DRV NULL | MOB 6006399745 | LR NULL
```
"Phase 1 matched all eight values on OINV DocNum 626070454" is **false** — two of the eight are NULL
on that row. Bucket M stands for bilty/date/transporter/vehicle/mobile/dispatch-date. Driver name
and LR number are effectively **not in SAP**.

Attachment caveat (the briefing's warning applies here): `ATC1` = **128,739** rows in Oil, 111,115
PDFs + 13,495 images. A scanned bilty may carry the driver and LR even where the column is empty.
Not queryable — flag, don't rule.

---

## 6. The pre-HANA SAP is still online — and it changes `sap_sales_log`

The same SQL Server that hosts DSR (103.89.45.75:1433) also hosts a **previous SAP Business One
installation**: `SBO-COMMON`, `Jivo_All_Branches_Live`, `Live_Jivo_WellnessN_Aug_2019`,
`JIVO_SAP_RECOVERED_DATA`, `Zia_Check`.

```sql
SELECT MIN(DocDate),MAX(DocDate),COUNT(*) FROM Jivo_All_Branches_Live.dbo.OINV;
--> 2019-08-31 → 2024-10-01, 68,070 invoices
```
The ruling said DSR's `sap_sales_log` DocNums "resolve in NO live company". They resolve here:
```sql
SELECT COUNT(DISTINCT s.docnum) FROM (SELECT DISTINCT docnum FROM DSR_V6.dbo.sap_sales_log) s
JOIN (SELECT DISTINCT RIGHT(CAST(DocNum AS varchar(20)),8) d8 FROM Jivo_All_Branches_Live.dbo.OINV
      WHERE DocDate BETWEEN '2023-03-01' AND '2023-09-30') o ON o.d8 = CAST(s.docnum AS varchar(20));
--> 1918 of 1918   (legacy DocNums carry a leading branch digit: 723041001 vs DSR 23041001)
```
**100%.** So `sap_sales_log` is a fully reconcilable extract of a system that is still queryable.
The product-code-poisoning warning stands; "ignore it entirely" does not.

**Bonus for the targets ruling:** the legacy SAP *has* the Uneecops target UDTs
`@UNE_TARGETH`, `@UNE_TARGETD`, `@TARGET_MAIN`, `@TARGET_ROW` — and **all four hold 0 rows**.
Sales targets have never been in SAP, old install or new.

---

## 7. Every N — the hunt, and what I found

Sweep I ran across all three JIVO HANA schemas:
```sql
SELECT SCHEMA_NAME,TABLE_NAME,RECORD_COUNT FROM M_TABLES WHERE SCHEMA_NAME LIKE 'JIVO%'
 AND (UPPER(TABLE_NAME) LIKE '%LIMIT%' OR '%CLAIM%' OR '%TARGET%' OR '%SCHEME%' OR '%BEAT%'
      OR '%VISIT%' OR '%RETAIL%' OR '%OUTLET%' OR '%PROMOT%' OR '%SALESPER%' OR '%HIERARCH%'
      OR '%RATE%' OR '%GIFT%' OR '%REMARK%');
```
Only hits with rows: `tbl_customerLimit` (Oil 35, Bev 3), `@ZIA_DL_LIMIT`/`@ZIA_DL_OLIMIT`.
Everything else 0 or SAP-internal `TMP_`/`CRSP` artefacts. A `SYS.TABLE_COLUMNS` sweep for
`%CLAIM%/%TARGET%/%BEAT%/%RETAIL%/%OUTLET%/%PROMOT%` returned only stock B1 columns
(`TargetType`, `TargetEntry`, `ClaimRefun`).

| N ruling | my independent test | verdict |
|---|---|---|
| Approval workflow / rate approvals | `OWDD ObjType=17` = **exactly 7** in 22 months | UPHELD 96 |
| Party↔product entitlement | `OSPP` 22/0/0 — **all 22 rows have CardCode `*3`, a price-list wildcard**. SAP has **zero** party-specific special prices. OMS `basic_rate` 28.5714 (FG0000336) vs `ITM1` list 380.95; CUSTA000019 has no invoices for those items | UPHELD **97** (stronger) |
| Sales schemes / free goods | `INV1.U_SchemeAgst` populated 85,819/96,900 but **41 distinct values**, all product categories (OLIVE 23,872 · CANOLA 16,609 · MUSTARD 12,189 …). `SALES_ANALYSIS.SchemeQty` = 0 populated | UPHELD 93 |
| Retailer universe | 127,395 rows, `SAPID` populated on **0**. SAP `U_Chain`: RETAILER 33, SINGLE SHOPS 76, SUPER STOCKIST 35. `OTER`=1 in all three | UPHELD 98 |
| Salesperson master / hierarchy | `OCRD` 3,390 with `U_UNE_ASM/RSM/SO/SR/AREA` **all 0** non-blank; `ZCUST_PORTAL.MGR_RSM/ASM/SO/SR/PROMOTER/ZONE` **all 0 of 17**; `OSLP` 155/51/99 | UPHELD **97** |
| Beats / journey plans | no `%BEAT%/%ROUTE%/%JOURNEY%` object anywhere; `OTER`=1 | UPHELD 98 |
| Secondary visits | `OCLG`/`OOPR`/`OSCL` = **0 / 0 / 0** in all three, re-verified; DSR `tbl_SalesReport` 2,128,151 | UPHELD 97 |
| Promoter activity | same negative; `tbl_SalesReportPromoter` 185,696 | UPHELD 97 |
| Sales targets | no target table in HANA; **legacy SAP target UDTs all 0 rows** | UPHELD **98** |
| Trade schemes / gifts | `tbl_saveGift` 34,236, `tbl_SchemeProductsSold` **423,785** (live, grew from 423,746) | UPHELD 90 |
| Channel stock | `tbl_retailerStock` 585,626; `OITW` 127,211 = JIVO's own warehouses. I also did not enumerate the 58 warehouse codes | UPHELD 92 |
| DSR product catalogue | `tbl_item` 333, `SAPID` 100% NULL | UPHELD 94 |
| OMS `sap_sync_logs` | `sap_sync_schedules` = 0; 367 log rows, 313 `manual` | UPHELD 96 (date corrected to 07-28) |
| Factory scan-to-ship | `barcode_dispatchsession` NOT_CONFIGURED: DISPATCHED 181, OPEN 4; `barcode_dispatchsapsynclog` **0 rows**; `OSRN` 0/0/0 | UPHELD 95 |
| ecom SKU bridge / realise model | `master_sheet` 834 confirmed | UPHELD 90 |
| Control-panel claims / remarks / SP / credit lock | **live probe**: `./jivo accounts claims --json` → claim_type "NSO CLAIM", claim_hold "Yes", hold_amount 23600, reason_of_hold "APPROVAL PENDING FROM PRINCE SIR", ref_inv_no "1030003568 / 2026" — **not a DocNum in any of the three companies**. No SAP claim object | UPHELD 92 **with caveat below** |
| Control-panel rate lists | not probed | UNPROVEN 85 |

### 7.1 The one methodology hole in the N block
The claims ruling proved absence by checking **@UDTs only**. `tbl_customerLimit` is a plain custom
table **inside `JIVO_OIL_HANADB`** (35 rows Oil, 3 Bev):
```
id | CardCode        | CurrentLimit | NewLimit | ValidTill           | expired | createdBy
35 | CUSTA001015JW   | 0            | 180000   | 2025-05-09 23:07    | 0       | 17
31 | CUSTA000592JW   | 0            | 4600000  | 2024-12-29 01:14    | 0       | 17
```
That is a **per-party credit-limit override with an expiry, living in SAP's database.** It belongs
to the ZIA add-on, not the control panel, and it is stale since 2025-05 — so the bucket stays N.
But "no per-party limit freeze anywhere in SAP" is wrong as written. Also found in the same sweep:
`JivoReports` on the MSSQL box holds `tbl_claims` (10) / `tbl_claimsDetail` / `tbl_targets` (13) —
a second, non-SAP claims/targets store nobody has reconciled.

---

## 8. M and X rulings — spot checks

| Ruling | test | result |
|---|---|---|
| **A/R open items** | `./exim sap-sync get-open-ar --json` → **1,168** rows; `SELECT COUNT(*),SUM("DocTotal"-"PaidToDate") FROM JIVO_BEVERAGES_HANADB.OINV WHERE "DocStatus"='O' AND "CANCELED"='N'` → **1,168**, 177421880353/2500 = **₹70,968,752.14**. First row DocNum 626078350 exists **only** in Beverages. Oil has **12,837** open invoices EXIM never shows | UPHELD **99** |
| **Order In Hand** | `ORDR` DocNum 1726056884 `DocStatus='O'`; `RDR1` FG0000183 `OpenQty` **140** — exact | UPHELD 97 |
| **Credit notes** | `ORIN` 6,377/4,439/427 · `RIN1` 15,331/28,456/777 | UPHELD 95 |
| **Branches** | `OBPL` 8+6+8 = **22** = OMS `branches` 22 | UPHELD 97 |
| **Party addresses** | OMS 35,664 vs `CRD1` 12,861+11,426+11,414 = **35,701** — but same 3-company merge, no company key | UPHELD 90 |
| **Quotation status read-back** | `orders` has 33 columns, **no `quotation_status`** — confirmed. Endpoint not callable | UPHELD 88 |
| **GST IRN** | `@UTL_MDEXTH` Oil 17,695 rows, `U_UTL_IRN` populated on **15,623 (88%)**, `U_UTL_AckNo` 15,449, 2024-10-01→2026-07-29. `@UTL_EWAY` 0 (the wrong table), `@UTL_ST_EWAYDT` 1,333. OMS `einvoice_irn` 24 rows | UPHELD 94 (count corrected) |
| **Marketplace secondary** | `swiggySec` **634,208** · `blinkitSec` **142,038** (grew from 125,194 — live) | UPHELD 96 |
| **Marketplace POs** | `total_po` 8,848 · `total_po_zbs` 40,977 | UPHELD 94 |
| **Marketplace consumer orders** | `marketplace_marketplaceorder` **2,158** rows 2026-07-20→07-29; `amazon_mp` 8,597; SAP Mart invoice Comments literally `AMAZON HARYANA 15 TO 27 JULY Based On Deliveries 1507264731.` | UPHELD 95 |
| **sustain_dist** | 42 rows, single date 2026-06-01. Rates match SAP to 0.2-1.4% (FG0000008 1949.02 vs 1952.38; FG0000032 214.35 vs 214.29) but quantities diverge **in both directions** (FG0000008 ecom 1498 > SAP 1200; FG0000042 ecom 2353 < SAP 2912) — not a unit conversion | UPHELD U 60 |
| ecom SAP read layer / distributors | ecom token still 401. Could not upgrade past code | UNPROVEN 80 / 75 |
| OMS HANA passthrough | no backend source, token expired | UNPROVEN 70 |
| Control-panel sales analytics | aggregates still not reproducible from outside | UNPROVEN 82 |

### 8.1 Marketplace coverage in SAP — the ruling's per-channel list is incomplete
```sql
SELECT h."CardCode",c."CardName",COUNT(*),MIN("DocDate"),MAX("DocDate") FROM JIVO_MART_HANADB.OINV h
JOIN OCRD c ON … WHERE CardName LIKE '%FLIPKART%' OR '%AMAZON%' OR … GROUP BY 1,2;
```
| CardCode | name | invoices | range |
|---|---|---|---|
| CUSTA000910 | FLIPKART (B2C-MAY-JULY) | 6,883 | 2025-05-23 → 2026-07-27 |
| CUSTA000912 | AMAZON (B2C -MAY-JULY) | 2,611 | 2025-05-22 → 2026-07-29 |
| CUSTA000885 | FLIPKART B2C | **2,322** | 2025-01-31 → 2025-05-05 |
| CUSTA000879 | FLIPKART INDIA PVT LTD | **678** | 2024-12-31 → 2026-02-03 |
| CUSTA000890 | FLIPKART HARYANA FBF | **525** | 2025-01-31 → 2026-03-31 |
| CUSTA000873 | AMAZON | **511** | 2025-01-25 → 2025-04-30 |
| CUSTA000722 | KIRANAKART (Zepto) | 237 | → 2026-06-18 |
| CUSTA000907 | SUSTAINQUEST | 224 | → 2026-07-28 |
| CUSTA000891 | FLIPKART KARNATAKA FBF | **145** | |
| CUSTA000496 | **INNOVATIVE RETAIL CONCEPTS (BigBasket)** | **71** | 2024-12-31 → 2026-01-13 |

The ruling missed the four superseded Flipkart/Amazon cards and BigBasket-as-customer. There is
still **no Swiggy customer** in any company. Its warning — *never make a blanket statement about
marketplace sales in SAP* — is right, and even more right than it knew.

---

## 9. Open questions I could not close

1. **Why the OQUT feed stopped on 2026-07-25.** SQL cannot see the reason. Still the top item.
2. **Where production OMS actually lives.** The reachable `order_management` is re-seeded and
   partial; production `oms.jivo.in` is not on this Postgres cluster. Every OMS row-count in this
   domain should be treated as *schema* evidence, not production volume.
3. **What `sustain_dist` measures.** Priced from SAP, quantified from somewhere else.
4. **Whether the ecom `/api/sap/*` layer is a live proxy** — token 401, backend on the app server.
5. **Whether driver name / LR number exist as scanned bilty PDFs in ATC1.** 128,739 attachments in
   Oil; the column is empty but the document may not be.
6. **Which company the ecom SAP layer reads.** Unchanged and still dangerous.
7. **The 3,455 DSR primary rows with no seller id** (all pre-2026-05). Unattributable.
