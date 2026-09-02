---
type: foundation
sap_tables: [NNM1, OFPR, OBPL, OPCH]
objtype: all
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Numbering series — the field that blocks the draft

> Every document JIVO keys needs a `Series`. It is not a preference and SAP will not
> guess it: give the wrong one, or give none, and the document is refused with
> **-10 / -4002 "define the numbering series"**. The series also decides the
> DocNum printed on the paper, so a wrong one is a GST problem, not just a nuisance.

## The short version

1. A series is chosen by **document type × branch × month × sub-type**. Miss any one of the four and SAP refuses the document.
2. Only **four** document types are branch-scoped at JIVO: A/P invoice (18), A/R invoice (13), A/P credit memo (19), A/R credit memo (14). **Every other type has one series per month for the whole company** — no branch to think about. *(measured, all three books)*
3. The series **integer is different in every book.** Oil's Aug-26 factory A/P GST series is **3684**; the identically-named `HR_G0826` is **2766** in Mart and **2777** in Beverages. Never carry a series number across companies.
4. Names are 8 characters and read `<branch><type><MM><YY>` — `HR_G0826` = Haryana/FACTORY, GST tax invoice, Aug 2026. A name starting `CN` is a **cancellation** series: SAP picks it by itself, an operator never does.
5. You cannot read the series list from `sapb1`. There is no series entity set — only `SeriesService_*`, and every one of its 14 operations is a POST action the CLI refuses. **`hana-sql` against `NNM1` is the only read path from a terminal.** *(measured: `sap-b1/cli/internal/catalog/services.json`)*

## What identifies a series — the `NNM1` fields

Fill rates from `_data/profile-NNM1.md` (Oil 2,850 rows / Mart 2,439 / Bev 2,459 — 7,748 in the
group, matching the [[Entry-Types-Census]]). *Filled* = non-null, non-blank **and** non-zero.

| Field | Oil / Mart / Bev filled | Distinct | Reads as (JIVO terms) |
|---|---|---:|---|
| `ObjectCode` | 100 / 100 / 100 | 70 | Which document type. `'18'` A/P invoice, `'13'` A/R invoice, `'19'`/`'14'` credit memos, `'20'` GRPO, `'30'` manual JE, `'2'` business partners, `'4'` items — see [[Entry-Types-Census]] |
| `Series` | 100 / 100 / 100 | 2,850 | **The value you put in the payload.** An internal key, unique inside one book only |
| `SeriesName` | 100 / 100 / 100 | 1,318 | The 8-character human name. Decoded below |
| `InitialNum` | 100 / 100 / 100 | 2,663 | First DocNum this series may issue |
| `NextNumber` | 100 / 100 / 100 | 2,726 | The DocNum the **next** document gets. Grows as documents are added |
| `LastNum` | 98 / 97 / 97 | 2,725 | Last DocNum allowed. `NextNumber > LastNum` = **exhausted** |
| `Locked` | 100 / 100 / 100 | 2 | `Y` = closed for use. At JIVO only ever used to seal the go-live months |
| `Indicator` | 100 / 100 / 100 | 33 | The **posting period** this series belongs to — joins to `OFPR."Indicator"` |
| `BPLId` | 75 / 73 / 72 | 7 | Branch. **Empty for ~25% of series, and that is correct** — those types are company-wide |
| `DocSubType` | 100 / 100 / 100 | 13 | GST sub-type. `GA` / `--` / `GD` for documents; see the table below |
| `IsForCncl` | 100 / 100 / 100 | 2 | `Y` = a cancellation series. Never hand-picked |
| `GroupCode` | 100 / 100 / 100 | 6 | Series group = **the branch's GST state code** (07 Delhi, 06 Haryana, 03 Punjab, 02 HP, 29 Karnataka); `1` for company-wide series |
| `SeriesType` | 100 / 100 / 100 | 5 | What is being numbered: `D` document (2,822), `I` item (12), `B` business partner (6), `W` (8), `R` (2) |
| `IsManual` | 100 / 100 / 100 | 2 | `Y` = the code is typed by hand, not generated. Only 4 rows per book — the shipped `Manual` series for BPs, items and one add-on |
| `BeginStr` | <1 / 2 / <1 | 23 | Code **prefix** for master data — `VENDA`, `CUSTA`, `RM`, `FG`… (see [[#Master-data-series]]) |
| `NumSize` | <1 / <1 / <1 | 3 | Digits after the prefix (6 for partners, 7 for items) |
| `UserSign` | 98 / 98 / 98 | 5 | Who created the series row — 2,712 of 2,850 by user 1 |
| `YearTransf`, `IsElAuth`, `CoAccount`, `GenPassprt` | one value, always `N` | 1 | SAP offers them, JIVO never uses them |
| `Remark` | <1 / <1 / <1 | 1 | Empty in 2,849 of 2,850 Oil rows. Dead field |

## How JIVO names them

`SeriesName` is `NVARCHAR(8)` — eight characters, which is why the convention is so compressed.

```
H R _ G 0 8 2 6
└─┬─┘ │ └──┬──┘
branch type  month + CALENDAR year
```

| Position | Meaning | Values seen |
|---|---|---|
| 1–2 | branch by state | `DL` Delhi · `HR` Haryana (Oil = the FACTORY branch) · `PB` Punjab · `HP` Himachal · `HS` Haryana Sales · `KN` Karnataka (Mart) · `DISD`/`IS_D`/`ISD_`/`DLIS`/`D_SD` Delhi ISD · `DIN_` Delhi Info |
| 3 | separator or nothing | `_` |
| 4 | document sub-type | `G` = GST tax invoice (`GA`) · `B` = non-GST (`--`) · `D` = GST debit memo (`GD`) · `E`/`F` one-off historic A/R series |
| 5–8 | `MMYY` | `0826` = Aug 2026 · **`0127` = Jan 2027** |
| prefix `CN` | cancellation series | `CNHR0826`, `CNDL0826` — SAP-only |

Company-wide types use a mnemonic instead of a branch: `GRPO0826`, `PO0826`, `IT0826`
(stock transfer), `GRE0826` (goods receipt), `GI0826` (goods issue), `OP0826` (outgoing
payment), `IP0826` (incoming payment), `ATJV0826` / `JV0826` (journals), `PRO0826`
(production), `LC0826` (landed cost), `DELG0826` (delivery), `SO_G0826` (sales order),
`RT_G0826` (A/R return), `GRT_0826` (goods return), `SQ_G0826` (quotation),
`ITFR0826` (transfer request), `IR0826` (revaluation).

### The sub-type is the half people miss

| `DocSubType` | Service Layer `DocumentSubType` | What it is | Evidence (Oil A/P, since 2025-04-01) |
|---|---|---|---|
| `GA` | `bod_GSTTaxInvoice` | normal GST vendor bill — **the common case** | 7,019 docs, 6,122 carry GST (87%), ₹412.85 Cr |
| `--` | `bod_None` | non-GST / plain | 3,604 docs, only 70 carry GST (2%), ₹214.14 Cr |
| `GD` | `bod_GSTDebitMemo` | debit memo | 11 docs |

That split is *measured*, and it is what confirms `GA` ≠ `--`: the `--` series is for
purchases with no input credit. Picking `--` for a GST bill produces a document with the
wrong invoice number on it — SAP will not stop you.

Other `DocSubType` values in `NNM1` belong to master data and add-ons, not to documents:
`C` = customer, `S` = supplier (on `ObjectCode` 2), and `OI`/`OS`/`ON`/`OG`/`OV`/`OD`/`IC`/`RV`
on add-on object types. **Unverified** what those seven mean; nothing at JIVO has ever used them.

## The period — `Indicator`

`NNM1."Indicator"` is the posting-period label, and it joins cleanly to `OFPR."Indicator"`
(**measured: 2,800 of 2,800 non-`Default` Oil rows match, zero orphans**). That join is what
turns a document date into a series.

| Oil posting periods | `Code` | `Indicator` | `PeriodStat` |
|---|---|---|---|
| Aug 2026 (current) | `FY2627-05` | `AUG-26-27` | `N` |
| Sep 2026 → Mar 2027 | `FY2627-06`…`-12` | `SEP-26-27` … `MAR-26-27` | `Y` |
| Apr 2025 → Mar 2026 | `FY2526-01`…`-12` | `APR-25-26` … `MAR-25-26` | `N` |
| Aug 2024 → Mar 2025 (go-live) | `FY2425-05`…`-12` | `Aug-24-25` … `Mar-24-25` | `N` |

Three things in there bite:

- **`JAN-26-27` means January 2027.** The suffix is the financial year, not the calendar year. The series *name* uses the calendar year (`DL_G0127`), the *indicator* uses the FY. Both are right; they just disagree on the digits.
- **Casing is inconsistent.** FY24-25 is Title case (`Aug-24-25`), FY25-26 and FY26-27 are upper (`AUG-25-26`). `WHERE "Indicator" = 'Aug-26-27'` returns nothing. Always `UPPER("Indicator")`, or join through `OFPR` on the date.
- **A 33rd indicator, `Default`,** holds 50 Oil series (52 Mart) — SAP's shipped `Primary`/`Manual` rows for object types JIVO never numbers per month. `InitialNum` 1, `NextNumber` 1, `LastNum` NULL. Exclude them from any period lookup.

## Which document types are branch-scoped

Oil, all history, by `ObjectCode` — the shape is the rule.

| Type | Object | Series defined | Periods | Sub-types | Branch on the series? |
|---|---:|---:|---:|---:|---|
| A/P invoice | 18 | 674 | 32 | `--`,`GA`,`GD` | **yes** |
| A/R invoice | 13 | 664 | 32 | `--`,`GA`,`GD` | **yes** |
| A/P credit memo | 19 | 427 | 32 | `--`,`GA` | **yes** |
| A/R credit memo | 14 | 384 | 32 | `--`,`GA` | **yes** |
| Manual journal entry | 30 | 67 | 32 | `--` | no (2 per month: `ATJV`, `JV`) |
| Sales order · stock transfer · production · revaluation · landed cost · goods issue · transfer request · goods receipt · outgoing payment · incoming payment · goods return · A/R return · delivery · GRPO · purchase order | 17, 67, 202, 162, 69, 60, 1250000001, 59, 46, 24, 21, 16, 15, 20, 22 | 32 each | 32 | `--` | **no — one per month, company-wide** |
| Sales quotation | 23 | 16 | 16 | `--` | no |
| Return request | 234000031 | 20 | 20 | `--` | no |
| ISD documents | 254000060/61/62 | 4 / 3 / 3 | ≤4 | `--` | no |
| Business partners | 2 | 6 | 2 | `C`,`S` | no |
| Items | 4 | 12 | 5 | `--` | no |
| ~40 other object codes | — | 1–8 each | 1 | — | no — untouched `Primary` rows |

**Practical read:** if you are keying anything that is *not* an invoice or a credit memo, the
series lookup takes one input — the month.

## Branches, all three books

`OBPL`, measured. Names and IDs are **not** the same across books, which is the most
expensive confusion in this area.

| `BPLId` | Oil | Mart | Beverages |
|---:|---|---|---|
| 1 | DELHI *(main)* | DELHI *(main)* | DELHI *(main)* |
| 2 | **FACTORY** (HR) | **HARYANA** (HR) | FACTORY (HR) |
| 3 | PUNJAB | PUNJAB | Punjab |
| 4 | HIMACHAL PRADESH | RAJASTHAN | Himachal Pradesh |
| 5 | HARYANA SALES | KARNATAKA | Haryana Sales |
| 6 | DELHI ISD | UTTAR PRADESH | DELHI ISD |
| 7 | DELHI INFO | DELHI ISD | — |
| 8 | HARYANA INFO | JIVO IT | — |
| 9–20 | — | BSU ×6 + TPT ×6 (see [[Mart-Branches-BSU-TPT]]) | — |

`BPLId = 2` is **FACTORY in Oil and HARYANA in Mart.** Same number, different branch, same
state. And Mart's branches 6 and 8–20 have **never had an A/P series** — you cannot key a
vendor bill against them at all:

| Mart branch | A/P series ever | Aug-26 A/P series |
|---|---:|---:|
| 1 DELHI / 2 HARYANA / 3 PUNJAB / 5 KARNATAKA / 7 DELHI ISD | 129 / 121 / 112 / 104 / 50 | 4 / 4 / 3 / 3 / 3 |
| 4 RAJASTHAN | 8 | **0** |
| 6 UTTAR PRADESH, 8 JIVO IT, 9–14 BSU, 15–20 TPT | **0** | **0** |

A branch with no series never bills — that is the mechanism behind
[[Mart-Branches-BSU-TPT]]. It is a series-master job, not something an operator can work around.

## The current month, Oil, everything (Aug-2026 / `AUG-26-27`)

83 series exist for the period. Branch-scoped types first.

### A/P invoice (18)

| Branch | `--` (non-GST) | `GA` (GST tax invoice) | `GD` (debit memo) | cancellation (do not use) |
|---|---:|---:|---:|---:|
| 1 DELHI | 3336 `DL_B0826` | 3672 `DL_G0826` | — | 3720 `CNDL0826` |
| **2 FACTORY** | 3324 `HR_B0826` | **3684 `HR_G0826`** | 3857 `HR_D0826` | 3732 `CNHR0826` |
| 3 PUNJAB | 3360 `PB_B0826` | 3696 `PB_G0826` | — | 3744 `CNPB0826` |
| 4 HIMACHAL | 3372 `HP_B0826` | 3708 `HP_G0826` | — | 3756 `CNHP0826` |
| 5 HARYANA SALES | 3384 `HS_B0826` | 3768 `HS_G0826` | 3804 `DS_D0826` | — |
| 6 DELHI ISD | 3408 `IS_D0826` | 3780 `DISD0826` | — | — |

3684 for the factory matches **[C-0018]** exactly, live today.

### Company-wide types, with the numbers left on 2026-08-24

| Document | Series | Name | Numbers left |
|---|---:|---|---:|
| Production order | 2696 | `PRO0826` | **81** ⚠ |
| Inventory revaluation | 2684 | `IR0826` | 490 |
| Landed cost | 2672 | `LC0826` | 493 |
| Goods return | 2527 | `GRT_0826` | 498 |
| Goods receipt | 2624 | `GRE0826` | 576 |
| Goods issue | 2636 | `GI0826` | 577 |
| Sales order | 2451 | `SO_G0826` | 727 |
| GRPO | 2477 | `GRPO0826` | 754 |
| Purchase order | 2465 | `PO0826` | 891 |
| Sales quotation | 2540 | `SQ_G0826` | 901 |
| Manual JE (auto) | 2576 | `ATJV0826` | 959 |
| A/R return | 2510 | `RT_G0826` | 967 |
| Manual JE (keyed) | 2588 | `JV0826` | 973 |
| Outgoing payment | 2600 | `OP0826` | 1,112 |
| Stock transfer | 2660 | `IT0826` | 1,147 |
| Transfer request | 2648 | `ITFR0826` | 1,468 |
| Delivery | 2489 | `DELG0826` | 1,489 |
| Incoming payment | 2564 | `IP0826` | 1,775 |

## The A/P series in all three books, same month

The point of this table is the middle column: **the same name is a different number.**

| Branch (per that book) | Sub-type | Oil | Mart | Beverages |
|---|---|---:|---:|---:|
| 1 DELHI | `GA` | 3672 `DL_G0826` | 2754 `DL_G0826` | 2765 `DL_G0826` |
| 1 DELHI | `--` | 3336 `DL_B0826` | 2874 `DL_B0826` | 2693 `DL_B0826` |
| 2 FACTORY / HARYANA | `GA` | **3684** `HR_G0826` | **2766** `HR_G0826` | **2777** `HR_G0826` |
| 2 FACTORY / HARYANA | `--` | 3324 `HR_B0826` | 2862 `HR_B0826` | 2678 `HR_B0826` |
| 2 | `GD` | 3857 `HR_D0826` | 3160 `HR_D0826` | — |
| 3 PUNJAB | `GA` | 3696 `PB_G0826` | 2778 `PB_G0826` | 2789 `PB_G0826` |
| 4 HIMACHAL *(Oil/Bev)* | `GA` | 3708 `HP_G0826` | n/a | 2801 `HP_G0826` |
| 5 HARYANA SALES / KARNATAKA | `GA` | 3768 `HS_G0826` | 2790 `KN_G0826` | 2898 `HS_G0826` |
| 6 / 7 DELHI ISD | `GA` | 3780 `DISD0826` | 2850 `DLIS0826` | 2862 `DISD0826` |
| 1 DELHI | `GD` | — | 3052 `DL_D0826` | 3177 `DL_D0826` |

Mart also carries `254000060`/`254000061` ISD series live this month (`ISD0826`, `ISDI0826`) —
these are the object types that show up as unidentified `TransType` 254000061/254000062 in the
census. **ISD = Input Service Distribution.** → [[Unidentified-Posting-Types]]

## The deliverable — the exact lookup

Give it a company, an `ObjectCode`, a branch (or `IS NULL`), and the document's **posting
date** and it returns the series to use. Verified: for Oil / 18 / branch 2 / 2026-08-24 it
returns exactly one row per sub-type, and the `GA` row is 3684.

```sql
-- Which series should this document use?
--   swap the schema, the ObjectCode, the BPLId and the date
SELECT n."Series",
       n."SeriesName",
       n."DocSubType",
       n."Indicator",
       n."NextNumber"                            AS NEXT_DOCNUM,
       n."LastNum",
       n."LastNum" - n."NextNumber" + 1          AS NUMBERS_LEFT
FROM   "JIVO_OIL_HANADB"."NNM1" n
JOIN   "JIVO_OIL_HANADB"."OFPR" f
       ON UPPER(f."Indicator") = UPPER(n."Indicator")
WHERE  n."ObjectCode" = '18'                     -- 18 A/P inv · 13 A/R inv · 19/14 credit memos
                                                 -- 20 GRPO · 30 journal · 22 PO · 67 transfer …
  AND  DATE'2026-08-24' BETWEEN f."F_RefDate" AND f."T_RefDate"   -- the POSTING date (C-0017)
  AND  n."BPLId" = 2                             -- or:  n."BPLId" IS NULL  for company-wide types
  AND  n."Locked"    = 'N'                       -- not sealed
  AND  n."IsForCncl" = 'N'                       -- not a cancellation series
  AND  n."NextNumber" <= n."LastNum"             -- not exhausted
ORDER BY n."DocSubType";
```

Then take the row whose `DocSubType` matches the paper: `GA` for a GST bill, `--` for a
non-GST one. **If two `GA` rows come back, take the one whose `SeriesName` matches
`__?_G` (`HR_G`, `DL_G`, `KN_G`) and never the one starting `CN`** — see the Beverages trap
below, where `IsForCncl` does not filter it out.

From the repo root:

```bash
./hana-sql/hana-sql -env connections/hana-office-bridge.env "<the SQL above, one line>"
```

For an A/P bill specifically, do not hand-run this — `jivo-ap-draft`'s
`bin/precheck.py` already does it and cross-checks against what the branch actually used
this month. → [[AP-Invoice]]

## Locked, exhausted, and running out

| | Oil | Mart | Bev |
|---|---:|---:|---:|
| Series rows | 2,850 | 2,439 | 2,459 |
| `Locked = 'Y'` | 78 | 64 | 75 |
| Exhausted (`NextNumber > LastNum`) | 3 | 4 | 2 |
| One number left | 4 | 4 | 1 |
| `IsManual = 'Y'` | 4 | 4 | 4 |

**Every locked series is a go-live month.** Oil: 38 in `Aug-24-25` + 40 in `Sep-24-25`.
Bev: 37 + 37 + one stray `Oct-24-25`. Mart: 31 + 31 + two in `Apr-25-26`. Nothing from
FY25-26 or FY26-27 is locked in any book — so `Locked` will not be the reason a current
document is refused, but leave the filter in.

Exhausted series are all old A/R series, not live ones:

| Book | Series | Name | Period | State |
|---|---:|---|---|---|
| Oil | 824 / 835 / 857 | `HR_E0125` / `HR_E0225` / `HR_F0225` | FY24-25 | full |
| Oil | 2376 / 2399 / 2403 | `HRF_0625` / `HRF_0925` / `HRF_1025` | FY25-26 | one left |
| Mart | 880, 203, 258, 1492 | `DL_G0425`, `DL_D0225`, `DL_G0325`, `DL_G0425` | FY24-25/25-26 | full |
| Bev | 129, 2409, 2410 | `HR_G1024`, `HRF_0825`, `HRF_0925` | FY24-25/25-26 | full |

**The live risk is capacity, not locking.** Oil's production-order series `PRO0826` has
**81 numbers left on day 24** with 419 used. It has happened before and someone noticed:
`PRO0726` was widened from the standard 500 to **1,500** after July needed 550.

| Oil `PRO` series | Capacity | Used |
|---|---:|---:|
| `PRO0426` Apr | 500 | 438 |
| `PRO0526` May | 500 | 402 |
| `PRO0626` Jun | 500 | 396 |
| **`PRO0726` Jul** | **1,500** | 550 |
| `PRO0826` Aug | 500 | 419 (to 08-24) |
| `PRO0926` Sep | 500 | 0 |

Sep-2026 is otherwise fully provisioned in Oil — all 83 series exist. One defect: `PRO0926`
starts at `202202500` where the pattern wants `926202500` (month-year prefix reversed). The
September production orders will number out of pattern unless someone fixes the row.

## Master-data series

`sapb1 post BusinessPartners` / `Items` also needs a `Series`, and here the series decides the
**code prefix** — `BeginStr` + `NumSize` digits.

| Object | Series | Prefix | Sub-type | Next | Cap | Produces |
|---|---:|---|---|---:|---:|---|
| 2 partners | 85 | `CUSTA` | `C` customer | 1144 | none | `CUSTA001144` |
| 2 partners | 87 | `VENDA` | `S` supplier | 1766 | none | `VENDA001766` |
| 2 partners | 86 / 88 | `ORGC` / `ORGV` | C / S | 41 / 480 | none | group-company codes |
| 2 partners | 1 / 2 | — | C / S | — | — | `Manual` — you type the code |
| 4 items | 389/390/391/392/393/394/395/820/821/2364/2396 | `FG` `FA` `PM` `RM` `SC` `SL` `CG` `EX` `CF` `SF` `FB` | — | — | — | `RM0000067` etc. (7 digits) |
| 4 items | 3 | — | — | — | — | `Manual` |

⚠ **`RM` (raw material) is the one capped series in the group:** `NextNumber` 67, `LastNum`
**80**. Thirteen raw-material item codes left in Oil before it is full. Nothing else in
`ObjectCode` 2 or 4 has a `LastNum` at all.

## How it differs across the three books

| | Oil | Mart | Beverages |
|---|---|---|---|
| Series rows | 2,850 | 2,439 | 2,459 |
| Branches | 8 | 20 | 6 |
| Branches that can take an A/P bill | 6 | 5 | 6 |
| `BPLId 2` is | FACTORY | HARYANA | FACTORY |
| `BPLId 5` is | HARYANA SALES (`HS`) | KARNATAKA (`KN`) | Haryana Sales (`HS`) |
| Delhi ISD is | `BPLId 6`, `DISD`/`IS_D` | `BPLId 7`, `DLIS`/`D_SD` | `BPLId 6`, `DISD` |
| DocNum digit order | state + YY + MM (`726083101`) | state + **MM + YY** (`708263101`), and mixed — some series use Oil's order | state + YY + MM (one credit-memo cancellation series, 3619, uses Mart's order) |
| Company-wide series live this month | 18 | 17 (2 of them the ISD add-on) | 17 |
| Company-wide types with **no series for this month** (defined in earlier periods only) | — | 23 quotation (1 series ever), 69 landed cost (8) — the census shows zero documents of either | 234000031 return request (20 series ever) |
| ISD add-on live now | no (Jul–Sep 25 only) | **yes** (`ISD0826`, `ISDI0826`) | no |

## Which documents it touches

Every one of them. The notes that have to quote a series:
[[AP-Invoice]] · [[AR-Invoice]] · [[AP-Credit-Memo]] · [[AR-Credit-Memo]] · [[GRPO]] ·
[[Purchase-Order]] · [[Sales-Order]] · [[Delivery]] · [[Stock-Transfer]] ·
[[Journal-Entry]] · [[Journal-Voucher]] · [[Incoming-Payment]] · [[Outgoing-Payment]] ·
[[Goods-Receipt]] · [[Goods-Issue]] · [[Production-Order]] · [[Landed-Costs]] ·
[[Business-Partner-Master]] · [[Item-Master]].
Foundations it leans on: [[Branches-and-BPLId]] · [[Posting-Periods]] ·
[[Document-Drafts]] · [[Opening-Balance-and-Cutover]].

## Traps

1. **The series number is per-book.** 3684 is Oil's factory A/P GST series for Aug-26. In Mart 3684 is something else entirely. Look it up in the book you are writing to, every time.
2. **`BPLId 2` is FACTORY in Oil and HARYANA in Mart.** Both in Haryana, both `HR_` in the name, different branches. Do not read the name and assume the branch.
3. **`CN…` means cancellation, not credit note.** Every one of the 71 Oil A/P invoices ever written on an `IsForCncl='Y'` series has `CANCELED='C'` — the system-generated mirror per **[C-0021]**. Zero live documents. SAP picks these itself when someone cancels; an operator picking one by hand is creating a document that looks cancelled.
4. **In Beverages, `IsForCncl` does not protect you.** Bev's Delhi A/P cancellation series 2813 `CNDL0826` is flagged `IsForCncl='N'`, so the lookup returns **two** `GA` rows for branch 1. Take the `DL_G` one. *(measured 2026-08-24)*
5. **Two Delhi ISD A/P series share the same number range.** Oil's `IS_D0826` (`--`) and `DISD0826` (`GA`) both run 726086900–726086999, and `ISD_0826` on the credit-memo object uses the identical block. It has already collided: **7 duplicate `DocNum`s in Oil `OPCH`**, most recently two live invoices both numbered `726076900` (DocEntry 47679 and 49588, July 2026).
6. **`Indicator` casing changes by financial year.** `Aug-24-25` vs `AUG-25-26`. An exact-match `WHERE` silently returns nothing, which looks like "no series exists". Use `UPPER()` or join `OFPR` on the date.
7. **`JAN-26-27` is January 2027; `DL_G0127` is the same month.** The indicator carries the FY, the name carries the calendar year.
8. **Use the *posting* date, not today and not the vendor's invoice date.** The series follows `DocDate`, and per **[C-0017]** an A/P invoice's `DocDate` is the gate-in date — usually the GRPO's, in a month that may already have closed on your calendar. **[C-0022]** warns not to run this backwards: never infer a gate-in date from an existing invoice.
9. **`Series` alone is not enough for A/P.** Per **[C-0018]** you need `DocumentSubType` too, or SAP answers `-4002 … define the numbering series` even though a valid series was supplied.
10. **A series can be filed in the wrong group.** All 36 of Beverages' FY26-27 non-GST A/P series for Delhi, Punjab and Himachal (Series 2689–2736) sit in `GroupCode` 6 — Haryana's state code — instead of 7/3/2. Mart has 8 Karnataka series still under group 2 from before Karnataka moved to 29. **Inferred** consequence: series groups gate per-user visibility in the SAP client, so a user authorised for their own state's group may not see these at all and would hit `-10`. Confirm by opening *Authorisations → Series* for that user; not testable read-only from here.
11. **~2 in 3 defined series are never used.** Oil has 674 A/P series and only 219 have ever carried a document. A series existing is no evidence it is the right one.
12. **Series `-1` means no series.** 949 Oil A/P invoices carry `Series = -1`, all dated 2024-09-30 — the go-live load. Any join from `OPCH` to `NNM1` loses exactly those rows. → [[Opening-Balance-and-Cutover]]
13. **`sapb1` cannot read the series list.** No entity set exists; all 14 `SeriesService_*` operations are POST actions and the client refuses OData actions. Terminal route is `hana-sql`, or ask someone with the SAP client open.

## Pre-flight — before you send anything

- [ ] **Which book?** Oil / Mart / Beverages. The series number is only valid in one of them.
- [ ] **Which posting date?** Not today. For an A/P bill it is the GRPO's `DocDate` (**[C-0017]**). That date, not the calendar, picks the period.
- [ ] **Is that period open?** `OFPR."PeriodStat" = 'N'`. Everything from Sep-2026 on reads `Y` today.
- [ ] **Which branch?** For an A/P or A/R invoice or credit memo only. Get it from the source document / the buyer GSTIN on the paper, not from the vendor. Everything else: no branch, `BPLId IS NULL`.
- [ ] **Which sub-type?** Does the paper show GST? → `GA` / `bod_GSTTaxInvoice`. No GST → `--`. Debit memo → `GD`.
- [ ] **Run the lookup.** One row per sub-type is the healthy answer.
- [ ] **Two `GA` rows?** Take `xx_G`, never `CNxx`.
- [ ] **`NUMBERS_LEFT` above zero,** and comfortably so if you are keying a batch.
- [ ] **A/P only:** carry `DocumentSubType` alongside `Series` (**[C-0018]**), and set the branch (`BPL_IDAssignedToInvoice`) or you get `-5002`.

## How to check you got it right, afterwards

1. **Read the draft back.** `jivo-ap-draft`'s `bin/readback.py` prints `branch … series … DocumentSubType` on one line. → [[AP-Invoice]]
2. **Compare with the branch's other documents this month.** One SQL, and a series that no one else used this month is the signal:
   ```sql
   SELECT p."Series", n."SeriesName", COUNT(*) AS DOCS
   FROM   "JIVO_OIL_HANADB"."OPCH" p
   LEFT JOIN "JIVO_OIL_HANADB"."NNM1" n
          ON n."Series" = p."Series" AND n."ObjectCode" = '18'
   WHERE  p."DocDate" >= '2026-08-01'
   GROUP BY p."Series", n."SeriesName" ORDER BY DOCS DESC;
   ```
   For July–Aug 2026 that returns 16 rows; `HR_G0726` carried 324 of them and `HR_G0826` 56. A one-off series in that list is worth a second look.
3. **Check the DocNum landed in range.** `p."DocNum" BETWEEN n."InitialNum" AND n."LastNum"` held for **15,385 of 15,385** Oil A/P invoices whose series still exists — so a failure here is real.
4. **Confirm the pairing.** In those same 15,385 rows, `OPCH."BPLId"`, `"PIndicator"` and `"DocSubType"` each equal the series' own `BPLId`, `Indicator` and `DocSubType` **100% of the time**. The document carries its series' identity; if the branch on the document is not the branch on the series, the series was wrong.

## Errors, and what each one means

| SAP error | Real cause | Fix |
|---|---|---|
| `-10 … define the numbering series` | no `Series` in the payload, and the user has no default for this type/period | supply `Series` |
| `-4002 … define the numbering series` | `Series` supplied but its `DocSubType` ≠ the document's | add `DocumentSubType` matching the series (`bod_GSTTaxInvoice` for a `_G` series) — **[C-0018]** |
| `-5002 Specify an active branch [ODRF.BPLId]` | series is branch-scoped, document has no branch | set `BPL_IDAssignedToInvoice` |
| `-10` for one user only, others fine | **inferred:** the series sits in a series group that user is not authorised for (trap 10) | check *Authorisations → Series* in the client |
| "Date deviates from permissible range" | the period is `PeriodStat = 'Y'` | a superuser opens the period; the series is not the problem |
| exit 7 | request reached SAP, reply lost — **it may have consumed a number** | do not re-run. Query `Drafts`/`PurchaseInvoices` by `NumAtCard`, per RULE 0 |

## Open questions

- **Does a draft reserve its number?** `NextNumber` advances when a document is added, but whether a *draft* holds a number until it is Added, and whether the series is re-evaluated at Add, is **not measured**. It matters for the `draft → approval → Add` path (2,857 A/P approvals in 90 days per `acc/INVENTORY.md`). Would need two drafts created minutes apart and a before/after read of `NNM1."NextNumber"` — a write, so out of scope here.
- **Who provisions next year's series, and when?** FY26-27 series were created as contiguous blocks (Bev 2689–2736) by `UserSign` 1. No schedule is recorded anywhere in the repo. `PRO0926`'s reversed prefix and Bev's mis-set `GroupCode` both look like symptoms of a hand-built batch.
- **What are `DocSubType` `OI`/`OS`/`ON`/`OG`/`OV`/`OD`/`IC`/`RV`?** They exist on add-on object codes `253000001` and `203` with `SeriesType` `W`. Never used. Would need the add-on's own documentation.
- **`SeriesType` `W` and `R`** — 8 and 2 rows in Oil. `D`/`I`/`B` are document/item/business-partner; the other two are unidentified.
- **Is trap 10 actually biting anyone?** Whether the mis-grouped Beverages series are invisible to the Delhi/Punjab/HP users is inferred from how SAP series groups work, not observed. The test is in the client.
- **Nobody has checked Mart's and Bev's DocNum-in-range consistency** the way Oil's was. Same query, other two schemas.

## Queries used

```sql
-- branch master, all three books
SELECT 'OIL',"BPLId","BPLName","MainBPL","State","DflWhs" FROM "JIVO_OIL_HANADB"."OBPL"
UNION ALL SELECT 'MART',… FROM "JIVO_MART_HANADB"."OBPL"
UNION ALL SELECT 'BEV', … FROM "JIVO_BEVERAGES_HANADB"."OBPL" ORDER BY 1,2;

-- every A/P series in Oil, all fields
SELECT "Series","SeriesName","BPLId","Indicator","DocSubType","InitialNum","NextNumber",
       "LastNum","Locked","IsDigSerie","SeriesType","IsManual","IsForCncl","GroupCode",
       "BeginStr","NumSize"
FROM "JIVO_OIL_HANADB"."NNM1" WHERE "ObjectCode"='18' ORDER BY "Indicator","BPLId","DocSubType";

-- which document types are branch-scoped
SELECT "ObjectCode", COUNT(*), SUM(CASE WHEN "Locked"='Y' THEN 1 ELSE 0 END),
       SUM(CASE WHEN "BPLId" IS NULL THEN 1 ELSE 0 END),
       COUNT(DISTINCT "Indicator"), COUNT(DISTINCT "DocSubType"), MIN("SeriesName"), MAX("SeriesName")
FROM "JIVO_OIL_HANADB"."NNM1" GROUP BY "ObjectCode" ORDER BY 2 DESC;

-- does the document agree with its series?  (15,385 / 15,385 on every column)
SELECT COUNT(*),
       SUM(CASE WHEN p."BPLId"=n."BPLId" THEN 1 ELSE 0 END),
       SUM(CASE WHEN p."PIndicator"=n."Indicator" THEN 1 ELSE 0 END),
       SUM(CASE WHEN p."DocSubType"=n."DocSubType" THEN 1 ELSE 0 END),
       SUM(CASE WHEN p."DocNum" BETWEEN n."InitialNum" AND n."LastNum" THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."OPCH" p
JOIN "JIVO_OIL_HANADB"."NNM1" n ON n."Series"=p."Series" AND n."ObjectCode"='18';

-- the 949 documents with no series
SELECT DISTINCT "Series","PIndicator","BPLId","BPLName","DocSubType" FROM "JIVO_OIL_HANADB"."OPCH" p
WHERE NOT EXISTS (SELECT 1 FROM "JIVO_OIL_HANADB"."NNM1" n
                  WHERE n."Series"=p."Series" AND n."ObjectCode"='18');   -- → Series -1

-- locked / exhausted / manual, three books
SELECT 'OIL',COUNT(*),SUM(CASE WHEN "Locked"='Y' THEN 1 ELSE 0 END),
       SUM(CASE WHEN "NextNumber">"LastNum" THEN 1 ELSE 0 END),
       SUM(CASE WHEN "NextNumber">="LastNum"-5 AND "NextNumber"<="LastNum" THEN 1 ELSE 0 END),
       SUM(CASE WHEN "IsManual"='Y' THEN 1 ELSE 0 END) FROM "JIVO_OIL_HANADB"."NNM1"
UNION ALL … MART … UNION ALL … BEV;

-- locked series are only the go-live months
SELECT "Indicator", COUNT(*), SUM(CASE WHEN "Locked"='Y' THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."NNM1" GROUP BY "Indicator" ORDER BY "Indicator";

-- posting periods and the indicator they carry
SELECT "Code","F_RefDate","T_RefDate","Indicator","PeriodStat" FROM "JIVO_OIL_HANADB"."OFPR"
ORDER BY "F_RefDate";

-- does GA really mean "carries GST"?
SELECT "DocSubType", COUNT(*), SUM(CASE WHEN "VatSum">0 THEN 1 ELSE 0 END),
       ROUND(SUM("DocTotal")/10000000,2), ROUND(SUM("VatSum")/10000000,2)
FROM "JIVO_OIL_HANADB"."OPCH" WHERE "DocDate">='2025-04-01' GROUP BY "DocSubType";

-- cancellation series carry nothing but cancellation mirrors  (71 docs, 0 live)
SELECT COUNT(*), SUM(CASE WHEN p."CANCELED"='N' THEN 1 ELSE 0 END),
       SUM(CASE WHEN p."CANCELED"='C' THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."OPCH" p JOIN "JIVO_OIL_HANADB"."NNM1" n
     ON n."Series"=p."Series" AND n."ObjectCode"='18' WHERE n."IsForCncl"='Y';

-- the overlapping-range collision
SELECT "DocNum", COUNT(*), COUNT(DISTINCT "Series") FROM "JIVO_OIL_HANADB"."OPCH"
WHERE "DocNum">0 GROUP BY "DocNum" HAVING COUNT(*)>1;   -- 7 rows, all Delhi ISD 6900-block

-- series group = GST state code
SELECT "GroupCode","BPLId",COUNT(*),COUNT(DISTINCT "ObjectCode") FROM "JIVO_OIL_HANADB"."NNM1"
GROUP BY "GroupCode","BPLId" ORDER BY 1,2;    -- and the same in MART (29 = Karnataka) and BEV

-- Mart branches that can never take a vendor bill
SELECT b."BPLId", b."BPLName", COUNT(n."Series"),
       SUM(CASE WHEN UPPER(n."Indicator")='AUG-26-27' THEN 1 ELSE 0 END)
FROM "JIVO_MART_HANADB"."OBPL" b
LEFT JOIN "JIVO_MART_HANADB"."NNM1" n ON n."BPLId"=b."BPLId" AND n."ObjectCode"='18'
GROUP BY b."BPLId", b."BPLName" ORDER BY b."BPLId";

-- master-data prefixes
SELECT "ObjectCode","Series","SeriesName","BeginStr","DocSubType","InitialNum","NextNumber",
       "LastNum","NumSize","SeriesType","IsManual","Locked"
FROM "JIVO_OIL_HANADB"."NNM1" WHERE "ObjectCode" IN ('2','4') ORDER BY "ObjectCode","Series";

-- production-order capacity by month
SELECT "SeriesName","Indicator","InitialNum","NextNumber","LastNum",
       "NextNumber"-"InitialNum" AS USED, "LastNum"-"InitialNum"+1 AS CAPACITY
FROM "JIVO_OIL_HANADB"."NNM1" WHERE "ObjectCode"='202' AND "Indicator" LIKE '%26-27';

-- how many defined A/P series were ever used
SELECT COUNT(*), SUM(CASE WHEN u."Series" IS NULL THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."NNM1" n
LEFT JOIN (SELECT DISTINCT "Series" FROM "JIVO_OIL_HANADB"."OPCH") u ON u."Series"=n."Series"
WHERE n."ObjectCode"='18';    -- 674 defined, 455 never used
```

Corpus files used: `_data/profile-NNM1.md`, `_data/profile-OPCH.md`, `_data/profile-OBPL.md`,
`_data/flow-OPCH-OIL.md`, `00-index/Entry-Types-Census.md`, `acc/INVENTORY.md`,
`.claude/skills/jivo-ap-draft/reference/series-and-errors.md`,
`sap-b1/cli/internal/catalog/services.json`.
