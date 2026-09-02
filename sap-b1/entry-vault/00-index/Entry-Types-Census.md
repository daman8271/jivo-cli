---
type: foundation
sap_tables: [ODRF, OJDT, SYS.M_TABLES]
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Entry types census — everything JIVO actually keys

> The work-list for the whole vault, taken from the books rather than from a
> module list. If a document type is not here, nobody at JIVO has ever made one.

Mined 2026-08-24 from `SYS.M_TABLES` row counts and `GROUP BY` over `ODRF."ObjType"`
and `OJDT."TransType"` in all three schemas.

## 1. Document volumes — all history, all three books

| Table | Document | Oil | Mart | Bev | Total |
|---|---|---:|---:|---:|---:|
| `OJDT` | [[Journal-Entry]] (all origins) | 136,721 | 64,640 | 23,621 | **224,982** |
| `OWDD` | [[Approval-Workflow]] requests | 59,787 | 14,925 | 17,225 | **91,937** |
| `ODRF` | [[Document-Drafts]] (any type) | 49,463 | 14,683 | 14,346 | **78,492** |
| `OINV` | [[AR-Invoice]] | 31,084 | 25,752 | 5,590 | **62,426** |
| `OITR` | [[Internal-Reconciliation]] | 30,084 | 13,403 | 6,353 | **49,840** |
| `ORCT` | [[Incoming-Payment]] | 14,149 | 11,391 | 4,166 | **29,706** |
| `ORDR` | [[Sales-Order]] | 15,133 | 7,675 | 5,578 | **28,386** |
| `OPCH` | [[AP-Invoice]] | 16,334 | 4,864 | 3,170 | **24,368** |
| `OPDN` | [[GRPO]] | 11,649 | 3,222 | 4,826 | **19,697** |
| `OVPM` | [[Outgoing-Payment]] | 14,844 | 2,294 | 1,925 | **19,063** |
| `OWTR` | [[Stock-Transfer]] | 12,204 | 1,728 | 2,200 | **16,132** |
| `ORIN` | [[AR-Credit-Memo]] | 6,434 | 4,545 | 438 | **11,417** |
| `OIGN` | [[Goods-Receipt]] | 8,548 | 75 | 1,477 | **10,100** |
| `OIGE` | [[Goods-Issue]] | 8,422 | 73 | 1,405 | **9,900** |
| `OWOR` | [[Production-Order]] | 8,333 | 27 | 1,472 | **9,832** |
| `ODLN` | [[Delivery]] | 2,842 | 6,126 | 303 | **9,271** |
| `OPOR` | [[Purchase-Order]] | 4,325 | 2,258 | 1,141 | **7,724** |
| `OBTF` | [[Journal-Voucher]] (parked) | 3,245 | 791 | 897 | **4,933** |
| `ORDN` | [[AR-Return]] | 2,031 | 1,847 | 187 | **4,065** |
| `ORPC` | [[AP-Credit-Memo]] | 1,595 | 781 | 248 | **2,624** |
| `OWTQ` | [[Inventory-Transfer-Request]] | 1,325 | 1,120 | 58 | **2,503** |
| `OQUT` | [[Sales-Quotation]] | 1,692 | 0 | 733 | **2,425** |
| `OPDF` | [[Payment-Draft]] | 1,568 | 20 | 200 | **1,788** |
| `OIPF` | [[Landed-Costs]] | 534 | 0 | 6 | **540** |
| `OBNK` | [[Bank-Statement]] | 201 | 7 | 51 | **259** |
| `ORPD` | [[Goods-Return]] | 117 | 59 | 33 | **209** |
| `OMRV` | [[Inventory-Revaluation]] | 114 | 0 | 46 | **160** |
| `ORRR` | [[Return-Request]] | 32 | 1 | 0 | **33** |

**Master and setup tables** in scope for the foundation notes: `OCRD` 8,566 ·
`NNM1` 7,748 · `OITM` 5,823 · `OACT` 3,298 · `OPRC` 566 · `OBGT` 339 · `OSLP` 308 ·
`OCST` 283 · `OUSR` 160 · `OWHS` 150 · `OCRG` 137 · `OFPR` 108 · `OWHT` 72 ·
`OBPL` 34 · `ODIM` 15 · `OACP` 9.

### Modules SAP ships that JIVO does not use at all

Zero rows in every book: purchase requests (`OPRQ`), inventory counting (`OINC`),
A/R and A/P down payments (`ODPI`/`ODPO`), deposits (`ODPS`), cheque printing
(`OCHO`). Do not design a process around them, and do not go looking for the data.

## 2. What gets drafted — `ODRF` by `ObjType`

A draft is the real unit of work at JIVO: 78,492 of them, and the
[[Approval-Workflow]] expects them. Latest date shows what is still live.

| ObjType | Document | Oil | Mart | Bev | Total | Latest |
|---:|---|---:|---:|---:|---:|---|
| 18 | [[AP-Invoice]] | 15,352 | 3,834 | 3,292 | **22,478** | 2026-08-22 |
| 13 | [[AR-Invoice]] | 9,790 | 4,015 | 5,948 | **19,753** | 2026-08-24 |
| 67 | [[Stock-Transfer]] | 11,655 | 1,393 | 2,241 | **15,289** | 2026-08-24 |
| 20 | [[GRPO]] | 4,488 | 1,433 | 691 | **6,612** | 2026-08-24 |
| 15 | [[Delivery]] | 1,388 | 1,609 | 322 | **3,319** | 2026-08-12 |
| 22 | [[Purchase-Order]] | 1,631 | 245 | 1,032 | **2,908** | 2026-08-24 |
| 14 | [[AR-Credit-Memo]] | 1,488 | 1,070 | 346 | **2,904** | 2026-08-24 |
| 19 | [[AP-Credit-Memo]] | 1,696 | 554 | 263 | **2,513** | 2026-08-22 |
| 16 | [[AR-Return]] | 1,116 | 471 | 174 | **1,761** | 2026-08-24 |
| 1250000001 | [[Inventory-Transfer-Request]] | 704 | 21 | 0 | **725** | 2026-08-24 |
| 21 | [[Goods-Return]] | 102 | 24 | 21 | **147** | 2026-08-22 |
| 17 | [[Sales-Order]] | 34 | 7 | 2 | **43** | 2026-07-30 |
| 59 | [[Goods-Receipt]] | 14 | 4 | 7 | **25** | 2026-06-30 |
| 60 | [[Goods-Issue]] | 5 | 3 | 4 | **12** | 2026-08-11 |
| 23 | [[Sales-Quotation]] | 0 | 0 | 3 | **3** | 2026-05-19 |

Nothing else is ever drafted — payments, journal entries and production orders go
straight in (payments have their own draft table, `OPDF`).

## 3. Every posting source in the ledger — `OJDT` by `TransType`

Only two of these are keyed by a human as a journal: **30** (manual) and, before
it posts, the [[Journal-Voucher]]. Everything else is a document's automatic side.

| TransType | Origin | Oil | Mart | Bev | Total | Latest |
|---:|---|---:|---:|---:|---:|---|
| 13 | A/R Invoice | 31,078 | 25,730 | 5,589 | **62,397** | 2026-08-24 |
| 24 | Incoming Payment | 14,645 | 11,639 | 4,263 | **30,547** | 2026-08-24 |
| 18 | A/P Invoice | 16,334 | 4,864 | 3,170 | **24,368** | 2026-08-24 |
| 46 | Outgoing Payment | 15,782 | 2,522 | 2,064 | **20,368** | 2026-08-24 |
| 67 | Stock Transfer | 12,089 | 1,704 | 2,188 | **15,981** | 2026-08-24 |
| 14 | A/R Credit Memo | 6,434 | 4,542 | 438 | **11,414** | 2026-08-24 |
| 59 | Goods Receipt | 8,431 | 74 | 1,466 | **9,971** | 2026-08-24 |
| 60 | Goods Issue | 8,364 | 73 | 1,396 | **9,833** | 2026-08-24 |
| 15 | Delivery | 2,804 | 6,109 | 241 | **9,154** | 2026-08-24 |
| 20 | GRPO | 5,176 | 3,045 | 774 | **8,995** | 2026-08-24 |
| **30** | **Manual journal entry** | 5,235 | 1,491 | 1,364 | **8,090** | **2026-12-31** |
| 202 | Production Order | 5,601 | 0 | 97 | **5,698** | 2026-08-24 |
| 16 | A/R Return | 1,925 | 1,677 | 32 | **3,634** | 2026-08-24 |
| 19 | A/P Credit Memo | 1,595 | 781 | 248 | **2,624** | 2026-08-20 |
| **-3** | **Opening balance / cutover** | 436 | 314 | 202 | **952** | 2025-04-01 |
| 69 | Landed Costs | 534 | 0 | 6 | **540** | 2026-08-21 |
| 21 | Goods Return | 120 | 59 | 37 | **216** | 2026-08-19 |
| 162 | Inventory Revaluation | 114 | 0 | 46 | **160** | 2026-08-24 |
| 321 | *unidentified* | 24 | 0 | 0 | **24** | 2026-07-25 |
| 254000061 | *unidentified (Mart only)* | 0 | 12 | 0 | **12** | 2025-11-30 |
| 254000062 | *unidentified (Mart only)* | 0 | 4 | 0 | **4** | 2025-11-30 |

Three things in that table are worth a second look, and each has its own note:

- **`TransType -3`, all dated 2025-04-01** — the go-live cutover. Every balance
  older than that date is an opening figure, not a transaction. Any ageing or
  history question has to know this. → [[Opening-Balance-and-Cutover]]
- **Manual JEs dated 2026-12-31** — future-dated entries exist in the books *today*.
  **Now measured** ([[Journal-Entry]]): exactly **5**, all in Beverages, all created in one
  batch on 2026-07-18 — monthly amortisation of a prepaid Sidel maintenance contract, dated
  Aug–Dec 2026, ₹3,98,006 each. Oil and Mart have **none**. So: not year-end provisions as
  first guessed, and bounded at ₹19.90 lakh — but a period query should still bound
  `RefDate` at both ends, not just the lower one. → [[Journal-Entry]]
- **`321` / `254000061` / `254000062`** — unidentified object types, low volume.
  → [[Unidentified-Posting-Types]]

## 4. Add-on tables that hold real entry data

Non-standard tables with rows in Oil — an entry is not finished if the add-on row
is missing, and none of them appear in SAP's own documentation.

| Table | Rows (Oil) | Looks like |
|---|---:|---|
| `@UTL_MDEXTH` / `@AUTL_MDEXTH` | 18,346 | master-data extension, one per document |
| `@UTL_ST_EWAYDT` | 1,333 | e-way bill data |
| `@UTL_ST_INTREWBILL` | 117 | inter-state e-way bill |
| `@UTL_ST_EICO` | 1 | e-invoice |
| `OMS_IRN_LOG` | 50 | e-invoice IRN log (custom) |
| `SALES_ANALYSIS` | 1,483 | custom reporting table |
| `@QC_O` / `@AQC_O` | 6 / 17 | quality control |
| `@ZIA_DL_OLIMIT` | 3 | credit-limit add-on |
| `@BUDGET` | 1 | budget add-on |

→ [[Add-on-Tables-and-UDFs]]

## Queries used

```sql
-- non-empty tables per schema
SELECT SCHEMA_NAME, TABLE_NAME, RECORD_COUNT FROM SYS.M_TABLES
WHERE SCHEMA_NAME IN ('JIVO_OIL_HANADB','JIVO_MART_HANADB','JIVO_BEVERAGES_HANADB')
  AND RECORD_COUNT > 0 ORDER BY SCHEMA_NAME, RECORD_COUNT DESC;

-- every document header table (has a DocNum column) with rows
SELECT c.TABLE_NAME, m.RECORD_COUNT FROM SYS.TABLE_COLUMNS c
JOIN SYS.M_TABLES m ON m.SCHEMA_NAME=c.SCHEMA_NAME AND m.TABLE_NAME=c.TABLE_NAME
WHERE c.SCHEMA_NAME='JIVO_OIL_HANADB' AND c.COLUMN_NAME='DocNum' AND m.RECORD_COUNT>0
ORDER BY m.RECORD_COUNT DESC;

-- what gets drafted
SELECT "ObjType", COUNT(*), MIN("DocDate"), MAX("DocDate")
FROM "JIVO_OIL_HANADB"."ODRF" GROUP BY "ObjType";

-- every posting source
SELECT "TransType", COUNT(*), MIN("RefDate"), MAX("RefDate")
FROM "JIVO_OIL_HANADB"."OJDT" GROUP BY "TransType";
```
