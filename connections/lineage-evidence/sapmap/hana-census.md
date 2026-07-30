# SAP HANA census — what SAP B1 actually holds (and does NOT hold)

**Probe:** `hana-census` · **Run:** 2026-07-30 ~02:30–03:00 UTC · **Evidence: LIVE SQL** unless noted.

**Connection that works (use this, the default env is dead off-office):**
```bash
export HANA_ENV=/Users/damanpreetsingh/jivo-cli/connections/hana-tunnel.env   # 127.0.0.1:13015
/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql "SELECT ... FROM \"JIVO_OIL_HANADB\".\"OINV\""
```
`connections/hana.env` points at `103.89.45.192:30015` **direct — that port is CLOSED from here** (query hangs
forever, no error). The SSH tunnel env is the only working path. Login is `ZIA`.

Method note: row counts come from `M_TABLES.RECORD_COUNT`. Validated against real `COUNT(*)` on OINV
(30,477 = 30,477) and OHEM (17 = 17). Treat it as accurate.

---

## PART 1 — THE NEGATIVE FINDINGS (read this first)

These are the buckets where SAP has **nothing**, so whatever app holds that data is holding
data SAP will never have. Every count below is live.

### 1.1 SAP has NO HR, NO payroll, NO attendance. At all. (confidence 99)

```sql
SELECT SCHEMA_NAME, TABLE_NAME, RECORD_COUNT FROM M_TABLES
WHERE SCHEMA_NAME LIKE 'JIVO%'
  AND (UPPER(TABLE_NAME) LIKE '%ATTEND%' OR '%PAYROL%' OR '%SALAR%'
       OR '%LEAVE%' OR '%WAGE%' OR '%PAYSLIP%')
-- → ZERO ROWS. Not one such table exists in any of the three company schemas.
```

| Table | Oil | Mart | Bev | What it is |
|---|---|---|---|---|
| `OHEM` | **17** | **1** | **15** | Employee master |
| `HEM1` / `HEM2` | 0 | 0 | 0 | Employee education / reviews |
| `OHTM` (absence) | 0 | 0 | 0 | Time-off |
| `OEDG` | 0 | 0 | 0 | Education |

And the 17 OHEM rows in Oil are **stubs** — every one has `jobTitle = NULL`, `startDate = NULL`,
`salary = 0`. They exist only so documents can carry an owner/sales-employee tag. JIVO's real
headcount is in the hundreds.

**Ruling for downstream: TankhaPay (employees, attendance, salary, payouts, leave) is unambiguously N.
There is no SAP object it could mirror or feed.** The only payroll trace in SAP is the *money* —
a salary/wage journal line in `OJDT`/`JDT1` — never a person, a day, or a shift.

### 1.2 SAP CRM is completely unused (confidence 99)

| Table | Oil | Mart | Bev |
|---|---|---|---|
| `OCLG` / `CLG1` — activities, calls, meetings | **0** | 0 | 0 |
| `OOPR` / `OPR1` — sales opportunities / pipeline | **0** | 0 | 0 |
| `OOIN` — opportunity info | 0 | 0 | 0 |
| `OCON` | 0 | 0 | 0 |

Zero activities ever logged in SAP. Any app holding visits, calls, follow-ups, tasks, pipeline
stages or lead status is **N**.

### 1.3 SAP Service module is completely unused (confidence 99)

`OSCL` (service calls) = 0 · `SCL1` = 0 · `OINS` (customer equipment cards) = 0 ·
`OCTR` (service contracts) = 0 — in **all three** companies. Any complaint / ticket / service
app is **N**.

### 1.4 The field-sales hierarchy exists as empty columns (confidence 98)

`OCRD` carries `U_UNE_RSM`, `U_UNE_ASM`, `U_UNE_SO`, `U_UNE_SR`, `U_UNE_AREA` — and they are
**100 % NULL**:

```
TOT 3390 | RSM 0 | ASM 0 | SO 0 | SR 0 | AREA 0 | U_Emp_Code 510 | U_Chain 1477 | U_Main_Group 3348
```

So SAP **does** classify customers by chain / main-group (channel), but it holds **no**
RSM→ASM→SO→SR reporting structure, no territory (`OTER` = 1 row, the default), and only 155
sales-employee records (`OSLP`). **DSR's beat plans, territory hierarchy, visits and coverage are N.**
The customer↔chain/main-group mapping, however, is duplicated in SAP → that slice is M.

### 1.5 Purchase requisition / pre-PO approval does not exist in SAP (confidence 97)

`OPRQ` / `PRQ1` (purchase requests) = **0 / 0 / 0**. `OPQT` (purchase quotations) = 0.
SAP's purchase trail starts at the **PO** (`OPOR`). Everything upstream of the PO — indent,
requisition, comparative quotes, vendor negotiation — is **N or F, never M**.

### 1.6 Other standard modules sitting empty (all three companies)

| Module | Tables checked | Verdict |
|---|---|---|
| Cheques / payment wizard | `OCHO`, `OCHH`, `ODPS`, `OPYM` | 0 — unused |
| Down payments | `ODPI`, `ODPO` | 0 — unused |
| Projects | `OPRJ` | 0 — unused |
| Dunning | `ODUN` | 0 — unused |
| Bin locations | `OBIN`, `OBBQ` | 0 — unused (warehouse-level only, `OWHS` = 58) |
| Serial numbers | `OSRI`, `OSRN`, `OSRQ` | 0 — batches only (`OBTN` 17,505) |
| Package/shipping | `OPKG`, `OSHP`, `OTPI` | 0 — unused |
| Blanket agreements | `OOAT` family / `OMGP`, `PMG1` | 0 — unused |
| MRP / forecast wizard | `OPWZ`, `OWKO`, `ORCM` | 0 — unused (`OFRC`/`FRC1` forecasts ARE used: 2,736 / 17,727) |
| Cost accounting extras | `OCPI`, `OCRP`, `OCRV`, `OHST` | 0 — unused |
| Human-resource extras | `OASG`, `OASC`, `OCLS`, `OMLS` | 0 — unused |

### 1.7 SAP HAS NO HISTORY BEFORE ~SEPT 2024 (confidence 97 — biggest scope trap here)

```
OJDT by month: 2024-08 → 2, 2024-09 → 16,764 (opening-balance batch), 2024-10 → 6,256, …
OFPR fiscal periods: 2024-04-01 → 2027-03-31 (36 periods)
Earliest DocDate on every trading table: 2024-09-30 / 2024-10-01
```

**SAP B1 went live around Sept–Oct 2024.** Any app that predates that (OMS, ecom, exim, factory,
DSR all have older histories) holds pre-go-live data that is **N by date** even where the same
*kind* of data is M today. Downstream agents must state the date window in every M ruling.
*Uncertainty:* I did not check whether a legacy system was migrated in as opening balances beyond
the Sept-2024 `OJDT` batch — the batch looks like balances only, not transactions.

### 1.8 The OMS→SAP order link is effectively DEAD since Sept 2025 (confidence 82)

`ORDR.U_OMS_Order_No` (and `OINV.U_OMS_Order_No`) is the field that stamps an OMS order onto a SAP
document. 6,253 of 14,736 Oil sales orders carry it. Monthly:

```
2025-05  817 | 2025-06  777 | 2025-07  450 | 2025-08  161 | 2025-09   22
2025-10    8 | 2025-11    9 | 2025-12    9 | 2026-01   10 | 2026-04    2   (nothing after 2026-04-28)
```

`U_OMS_REF` — the apparent replacement field — has **1** row ever (OINV, 2026-07-07) and **0** on ORDR.

*Uncertainty (why this is 82, not 95):* the collapse proves the **stamping** stopped, not necessarily
that the **integration** stopped. Orders could still be pushed without the reference. Someone needs to
match OMS order counts to SAP `ORDR` counts for e.g. June 2026 to settle it. Do not rule OMS "M" on
current data without that check.

---

## PART 2 — SCALE OF THE CENSUS

```sql
SELECT SCHEMA_NAME, COUNT(*) TBLS, SUM(CASE WHEN RECORD_COUNT>0 THEN 1 ELSE 0 END) POPULATED,
       SUM(RECORD_COUNT) TOTAL_ROWS
FROM M_TABLES WHERE SCHEMA_NAME LIKE 'JIVO%' GROUP BY SCHEMA_NAME;
```

| Schema | Tables | Populated | Empty | Total rows |
|---|---:|---:|---:|---:|
| `JIVO_OIL_HANADB` | 3,121 | **746** | 2,375 | 69,079,398 |
| `JIVO_MART_HANADB` | 3,050 | 617 | 2,433 | 7,971,577 |
| `JIVO_BEVERAGES_HANADB` | 3,092 | 659 | 2,433 | 3,385,625 |

**76 % of SAP's tables have never held a row.** The prior "~3,111 / ~746" figure is confirmed for Oil.

Populated-table rows by domain (Oil), with the caveats that matter:

| Domain | Tables | Rows | Caveat |
|---|---:|---:|---|
| approval/system | 37 | 57,023,266 | 95 % is `ALR3` alone (54.4 M) = alert-result rows, system noise |
| other/system | 428 | 4,435,805 | `CGEV` 3.34 M = security/change event log; `CPRF` 464 k = UI form prefs |
| inventory | 40 | 2,337,014 | real business data |
| sales | 59 | 2,181,827 | real business data |
| finance | 29 | 1,880,086 | real business data |
| "hr" | 11 | 485,027 | **fake** — `USR5` 469 k is *user UI settings*. Real HR ≈ 17 rows |
| purchase | 45 | 341,611 | real business data |
| production | 16 | 235,554 | real business data |
| business partners | 15 | 114,136 | real business data |
| UDTs (`@…`) | 66 | 45,072 | add-on config, see Part 4 |

---

## PART 3 — WHAT SAP *DOES* HOLD (headline row counts, all three companies)

Anything here with real volume is a candidate **M** for an app that surfaces it.
`MIN/MAX DocDate` for Oil in the last column where checked; latest data is **2026-07-29** across the
board, so SAP is live and current.

### Sales — LIVE, heavily used
| Table | Oil | Mart | Bev | Oil date span |
|---|---:|---:|---:|---|
| `OINV` / `INV1` A/R invoices | **30,477** / 96,900 | 25,063 / 186,581 | 5,246 / 12,592 | 2024-09-30 → 2026-07-29 |
| `ORDR` / `RDR1` sales orders | **14,736** / 74,230 | 7,374 / 37,054 | 5,275 / 15,554 | 2024-10-01 → 2026-07-29 |
| `ODLN` / `DLN1` deliveries | 2,830 / 24,241 | 6,084 / 59,145 | 303 / 807 | 2024-10-04 → 2026-07-19 |
| `ORIN` / `RIN1` credit notes | 6,377 / 15,331 | 4,439 / 28,456 | 427 / 777 | 2024-09-30 → 2026-07-29 |
| `ORDN` / `RDN1` returns | 1,990 / 8,081 | 1,820 / 13,047 | 184 / 302 | 2024-10-08 → 2026-07-28 |
| `OQUT` / `QUT1` quotations | 1,691 / 6,631 | **0** | 733 / 1,297 | 2025-02-25 → 2026-07-25 |

### Purchase — LIVE
| Table | Oil | Mart | Bev | Oil date span |
|---|---:|---:|---:|---|
| `OPOR` / `POR1` purchase orders | 4,191 / 11,363 | 2,131 / 16,788 | 1,113 / 3,087 | 2024-10-01 → 2026-07-29 |
| `OPDN` / `PDN1` GRPO | 11,248 / 24,410 | 3,023 / 15,067 | 4,533 / 6,878 | 2024-09-30 → 2026-07-29 |
| `OPCH` / `PCH1` A/P invoices | 15,934 / 39,088 | 4,569 / 21,242 | 3,068 / 10,167 | 2024-09-30 → 2026-07-25 |
| `ORPC` A/P credit | 1,530 | 759 | 231 | 2024-09-30 → 2026-07-24 |
| `OIPF` / `IPF1` **landed costs** | **525 / 534** | 0 / 0 | 6 / 15 | — imports costing IS in SAP, Oil only |

### Inventory — LIVE
| Table | Oil | Mart | Bev |
|---|---:|---:|---:|
| `OITM` items | 2,269 | 1,349 | 2,192 |
| `OITW` item-warehouse | 127,211 | 47,908 | 95,351 |
| `OITL` / `ITL1` inventory transaction log | 196,793 / 163,953 | 163,112 / 142,138 | 36,948 / 24,848 |
| `OIVL` inventory valuation | 265,963 | 142,754 | 39,118 |
| `OWTR` / `WTR1` stock transfers | 11,800 / 51,439 | 1,683 / 12,214 | 2,095 / 6,790 |
| `OIGN`+`OIGE` goods receipt/issue | 8,065 + 7,939 | 74 + 72 | 1,436 + 1,364 |
| `OBTN` / `OBTQ` batches | 17,505 / 32,967 | 10,076 / 15,759 | 2,113 / 4,224 |
| `OWHS` warehouses | 58 | 36 | 44 |
| `OPKL` pick lists | 3,598 | 702 | 1,310 |

### Production — LIVE, and Oil-only in practice
| Table | Oil | Mart | Bev |
|---|---:|---:|---:|
| `OWOR` / `WOR1` production orders | **7,858 / 51,104** | **27 / 36** | 1,431 / 7,521 |
| `OITT` / `ITT1` bills of material | 622 / 3,006 | 467 / 1,745 | 543 / 2,520 |
| `ORSC` resources | 7 | 2 | 1 |
| `OFRC` / `FRC1` forecasts | 2,736 / 17,727 | 1,788 / 9,338 | 1,364 / 5,111 |

Oil `OWOR` status: 7,636 Closed(L) · 163 Released(R) · 31 Cancelled(C) · 28 Planned(P);
span 2024-10-01 → **2026-07-29**. Custom fields on `OWOR`: `U_BATCH_NO, U_MFG, U_EXP_DATE,
U_SFGPRODEntry, U_ProductionDate, U_WASTAGE`.

**So factory production orders DO land in SAP.** Factory-cli is therefore **F, not N**, for the
production-order layer. Whatever the factory app holds *around* the order (line-level shift data,
QC, downtime, operator, wastage detail beyond `U_WASTAGE`) is the N part — verify separately.

### Finance — LIVE
| Table | Oil | Mart | Bev |
|---|---:|---:|---:|
| `OJDT` / `JDT1` journals | 132,621 / **513,596** | 62,817 / 336,771 | 22,531 / 82,709 |
| `ORCT` / `RCT2` incoming payments | 13,861 / 19,180 | 11,122 / 19,122 | 3,872 / 3,754 |
| `OVPM` / `VPM2` outgoing payments | 14,356 / 11,469 | 2,170 / 2,204 | 1,861 / 1,827 |
| `OACT` chart of accounts | 1,424 | 1,104 | 764 |
| `OBNK` banks · `OBTF` bank transfers | 201 · 3,158 | 7 · 764 | 51 · 880 |
| `OFPR` fiscal periods | 36 | 36 | 36 |

### Business partners
`OCRD` 3,390 / 2,183 / 2,930 · `CRD1` addresses 12,861 / 11,426 / 11,414 ·
`OCPR` contacts 3,131 / 1,989 / 2,723 · `OSLP` sales employees 155 / 51 / 99 · `OTER` territories **1 / 1 / 1**.

### Documents & approvals (SAP-native)
`OWDD` / `WDD1` approval requests **57,741 / 57,752** (Oil) — SAP's own draft-approval engine IS heavily
used. `ODRF` drafts 47,609. `ADOC`/`ADO1` document history 43,054 / 188,592. `OATC`/`ATC1` attachments
**76,062 / 128,739** — SAP does hold attachment records (files themselves live on the Windows share).

### E-commerce / q-commerce presence in SAP
Marketplace parties **do** exist as business partners:

| Party | Oil | Mart | Bev | Invoices found |
|---|---|---|---|---|
| JioMart (`CUSTA000251`, `…000574`, `…001022`) | ✔ | ✔ | ✔ | Oil: 3,096 + 1,502 + 1,187, → 2026-07-16 |
| Amazon (`CUSTA000873`, `…001075`) | ✔ | ✔ | ✔ | Oil: 3,061 (all dated 2024-09-30 = migration batch) + 4 |
| Flipkart (`CUSTA000355`) | ✔ | ✔ | ✔ | Oil: 3 only |
| Zepto / Kiranakart (`CUSTA000722`) | ✔ (BP) | ✔ | ✔ (BP) | **Oil 0 · Mart 237 (2024-12-31→2026-06-18) · Bev 0** |
| Blinkit / Blink Commerce (`VENDA000849`) | vendor | vendor | vendor + `CUSTA001135` "BLINK" | — |
| Swiggy Instamart | vendor | vendor | vendor | — |

Read this carefully: **q-commerce revenue reaches SAP only as a lump customer invoice, in the Mart
company, and Blinkit/Swiggy appear mostly as *vendors* (i.e. their commission/charges), not as sales
customers.** SKU-level, city-level, order-level marketplace data has no SAP home. Portal/e-com CLIs
are **X for the raw feed and at best F for the settled invoice.**

---

## PART 4 — CUSTOM EXTENSIONS: where the non-standard data hides

### 4a. Non-SAP tables living INSIDE the HANA company schema
These are **not** SAP B1 business objects. They are app tables that somebody created in SAP's own
database. They are reachable by `hana-sql` but invisible to the Service Layer / `sapb1` CLI.
Downstream agents: **"in HANA" ≠ "in SAP".** Data here is app-native even though it shares the DB.

| Table (Oil) | Rows | Columns that reveal the flow |
|---|---:|---|
| `JS_SYNC_BUDGET_APPROVAL_WORKFLOW` | **29,212** | budgetId, docEntry, stageName, approvalId, rejectid, currentStageApprovers, nextStageUsers, SYNC_TIMESTAMP |
| `M_TIME_DIMENSION` / `TimeData` | 18,263 | HANA date dimension (system) |
| `JIVO_WA_MESSAGE_LOG` | **5,941** | WddCode, Phone, MessageType, Status, MetaMessageId, AttemptCount, LastError — **WhatsApp approval notifications** |
| `JIVO_WA_SENT` | 641 | WddCode, ApprovedBy, Source, ActionAt, SendStatus |
| `PRODUCTIONORDERSYNC` | **2,499** | DOCENTRY→OWOR, STATUS, CURRENTSTAGE/TOTALSTAGE, ITEMCODE, WAREHOUSE, **SAPSTATUS='PENDING'**, SYNCEDAT — newest row **2026-07-29 19:26 UTC, live** |
| `tbl_Draft_Approvals` | 1,440 | Budget_Owner, Approver_Name, ACOMMENT, VCOMMENT, VerifiedStatus, ApprovedStatus |
| `GetTurnover` | 1,392 | materialised turnover |
| `SALES_ANALYSIS` | 1,299 | flattened sales cube w/ U_Main_Group, U_Chain, Variety, Brand, SKU, COGS, SchemeQty/Amt |
| `jsDocEntries` / `jsDocumentAttachments` | 535 / 36 | workflow stage pointers |
| `ZVENDOR_PORTAL` | **49** | full vendor-onboarding form: GSTIN, PAN, TAN, TDS category/rate/LDC, MSME, FSSAI, BANK_ACCOUNTS, ATTACHMENTS, VERIFIED_BY/AT, APPROVED_BY/AT, **REJECTED_BY/AT**, `SAP_CARD_CODE` |
| `ZCUST_PORTAL` | **17** | same shape for customers, 75 columns, `SAP_CARD_CODE`, `SAP_ATT_ENTRY` |
| `ZCUST_USERS` | 13 | portal logins (not inspected — credentials) |
| `ZBOM_REQUESTS` | **12** | BOM change request: COMPONENTS, ORIGINAL_DATA, APPROVAL_LOG, REJECTED_BY/AT, **SAP_PUSHED_AT / SAP_PUSHED_BY / SAP_RESULT** |
| `tbl_customerLimit` | 35 | CardCode, CurrentLimit, NewLimit, ValidTill, expired |
| `OMS_IRN_LOG` | **4** | e-invoice IRN log with U_UTL_IRN / U_UTL_AckNo — OMS writing back into HANA |
| `ES_*`, `ZAPR_*`, `ANALYTICS_METADATA`, `PAL_*` | small | add-on/reporting config |

**Direct lineage read from those column names:** the vendor/customer/BOM portals collect a rich form,
run verify → approve → reject, and only then write a `SAP_CARD_CODE`. That is the textbook **F** shape,
with the rejected/pending/attachment/bank/TDS detail being the N residue that never reaches SAP.
`PRODUCTIONORDERSYNC` with `SAPSTATUS='PENDING'` is an approval gate sitting *in front of* `OWOR`.

Beverages additionally has `BZSTDOC`/`BZSTIDXP`/`XCLTRINQ`/`XCLTRLOG` (~9.4 k / 9.4 k / 2.8 k / 1 k) —
a different add-on stack; not investigated.

### 4b. SAP user-defined tables (`@…`)
Oil 101 UDTs / 66 populated · Mart 82 / 46 · Bev 91 / 54. Dominated by the **UTL / UNE localisation
add-on** (e-way bill, e-invoice, GST): `@UTL_MDEXTH` 17,695 · `@UNE_USERSEL` 2,449 ·
`@UTL_ST_EWAYDT` 1,333 · `@UTL_ST_INTREWBILL` 117 · `@UTL_UP_USRLIC1` 1,331.
JIVO's own master data lives in: `@ITEM_VARIETY` 196 · `@ITEM_SUBGRP` 51 · `@ITEM_SKU` 50 ·
`@CHAIN` 46 · `@MAIN_GROUP` 60 · `@BRAND` 3 · `@ZIA_DL_LIMIT` 62 · `@BUDGET`/`@BUDGET1` 1/1 ·
`@QC_I` 19 / `@QC_O` 6 (a QC stub — nearly empty, so QC data is N).
`A…`-prefixed twins (`@AITEM_VARIETY` etc.) are the audit-log copies.

### 4c. User fields (`U_…`)
`CUFD` (field definitions): **Oil 5,572 · Mart 5,194 · Bev 5,106**. Every marketing document
(`OINV, ORDR, ODLN, ORIN, OPOR, OPCH, OPDN, ODRF, ADOC, …`) carries exactly **65** user fields.

Integration-revealing fields on `OINV`/`ORDR`:
`U_OMS_Order_No`, `U_OMS_REF`, `U_Production_Order`, `U_SFGPRODEntry`, `U_PRODUCTION_DATE`,
`U_GRPO`, `U_PONo`, `U_MartCustomer`, `U_MartCN`, `U_CreditCreated`, `U_deldocnum/date/branch`,
`U_TransporterName`, `U_VehicleNoM`, `U_DriverName`, `U_LRNUmber`, `U_BilltyNumber`, `U_AR_NO`.

On `OCRD`: `U_Main_Group`, `U_Chain`, `U_Emp_Code`, `U_MSME`, `U_MSME_Type`, `U_Fssai`,
`U_CATGCODE`, `U_ST_GRP1…11`, plus the all-NULL `U_UNE_RSM/ASM/SO/SR`.
On `OITM`: `U_Brand`, `U_Variety`, `U_SKU`, `U_Sub_Group`, `U_TYPE`, `U_PACK_TYPE`, `U_MRP`,
`U_IsLitre`, `U_Gross_Weight`, `U_Net_Weight`, `U_Qty_In_PCS`, `U_Shelflife`, `U_Mart_ItemCode`,
`U_ITEM_LOCK`, `U_Is_Plastic`, `U_Is_CSD`.

Transport/logistics detail (vehicle, driver, LR, bilty) **is** in SAP as user fields — so a logistics
app surfacing those is M, not N.

---

## PART 5 — DIRECT IMPLICATIONS FOR THE BUCKETING (my input, not the final ruling)

| App / domain | SAP holds it? | Bucket steer | Basis |
|---|---|---|---|
| TankhaPay — employees, attendance, salary, leave, payouts | **No** (OHEM 17 stubs; zero payroll tables) | **N** — high confidence | live |
| Any CRM/visit/activity/lead app | **No** (OCLG/OOPR = 0) | **N** | live |
| Any service/complaint app | **No** (OSCL/OINS/OCTR = 0) | **N** | live |
| DSR — territory hierarchy, beats, coverage | **No** (RSM/ASM/SO/SR all NULL, OTER = 1) | **N** | live |
| DSR — customer↔chain/main-group mapping | **Yes** (`U_Chain` 1,477, `U_Main_Group` 3,348) | M for that slice | live |
| Factory — production orders | **Yes, live** (OWOR 7,858, → 2026-07-29) | **F** (not N) | live |
| Factory — approval gate before the order | **No** (lives in `PRODUCTIONORDERSYNC`, SAPSTATUS=PENDING) | N residue on top of F | live |
| Purchase requisition / indent / approval | **No** (OPRQ = 0) | **N/F**, never M | live |
| Vendor & customer onboarding portals | Only the final `SAP_CARD_CODE` | **F** with large N residue (TDS, bank, MSME, FSSAI, rejections, attachments) | schema |
| Budget / draft-approval workflow apps | State is in HANA custom tables, not SAP objects; SAP has its own `OWDD` 57,741 | mixed — needs code check | live+schema |
| Exim — landed costs | **Yes** (`OIPF` 525, Oil) | F/M for costing | live |
| E-com / q-commerce SKU-level sales | **No** — only lump customer invoices, Mart only for Zepto | **X → F at settlement**, N/X for the detail | live |
| OMS — orders | Was stamped until Aug-2025, then collapsed | **F historically; verify current** | live, confidence 82 |

---

## PART 6 — WHAT I DID NOT CHECK (so nobody assumes I did)

- Whether SAP `ORDR` volume still matches OMS order volume post-Sept-2025 (the one test that settles §1.8).
- Whether a pre-Sept-2024 legacy system exists whose data was migrated as anything more than opening balances.
- The contents of `ZCUST_USERS` (portal credentials — deliberately not read).
- `BZSTDOC` / `XCLTR*` in Beverages (unidentified add-on).
- Any Postgres side, any app API. Pure HANA census only.
- SAP Service Layer (`sapb1`) — not attempted; HANA direct SQL was sufficient and faster.
