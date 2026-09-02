---
type: evidence
for: [[Transport-Bill-Playbook]]
sap_tables: [OPCH, PCH1, PCH4, PCH5, OPDN, PDN1, ODRF, DRF1, OCRD, CRD4, CRD7, OCRG, NNM1, OSAC, OUSR, ATC1]
companies: [OIL, MART, BEV]
mined: 2026-08-27
tool: hana-sql (read-only, HANA 30015)
---

# Evidence — transporter A/P invoices

Every number in [[Transport-Bill-Playbook]] traces to a query here. Population is always
`OCRG.GroupName = 'TRANSPORTER'`, `OPCH.CANCELED = 'N'`, `DocDate >= '2026-04-01'`
(FY26-27 to 2026-08-27) unless stated. Run date **2026-08-27**.

Nothing here wrote to SAP.

## The population filter

```sql
FROM "<DB>"."OPCH" o
JOIN "<DB>"."OCRD" c ON c."CardCode" = o."CardCode"
JOIN "<DB>"."OCRG" g ON g."GroupCode" = c."GroupCode"
WHERE g."GroupName" = 'TRANSPORTER' AND o."CANCELED" = 'N' AND o."DocDate" >= '2026-04-01'
```

Bills: **Oil 198 · Mart 145 · Bev 90**.

## 1 · Header fill rates (Oil, 198 bills)

```sql
SELECT COUNT(*) BILLS,
 SUM(CASE WHEN o."DocType"='S' THEN 1 ELSE 0 END) SERVICE,
 SUM(CASE WHEN o."NumAtCard" IS NOT NULL AND o."NumAtCard"<>'' THEN 1 ELSE 0 END) NUMATCARD,
 SUM(CASE WHEN o."Comments" IS NOT NULL AND o."Comments"<>'' THEN 1 ELSE 0 END) COMMENTS,
 SUM(CASE WHEN o."BPLId"=2 THEN 1 ELSE 0 END) BRANCH2,
 SUM(CASE WHEN o."DocDate"=o."TaxDate" THEN 1 ELSE 0 END) SAMEDATE,
 SUM(CASE WHEN o."AtcEntry">0 THEN 1 ELSE 0 END) ATTACHED,
 SUM(CASE WHEN o."U_BilltyNumber" IS NOT NULL AND o."U_BilltyNumber"<>'' THEN 1 ELSE 0 END) U_BILTY,
 SUM(CASE WHEN o."U_TransporterName" IS NOT NULL AND o."U_TransporterName"<>'' THEN 1 ELSE 0 END) U_TRANS,
 SUM(CASE WHEN o."U_VehicleNoM" IS NOT NULL AND o."U_VehicleNoM"<>'' THEN 1 ELSE 0 END) U_VEH,
 COUNT(DISTINCT o."Series") NSERIES, COUNT(DISTINCT o."UserSign") NUSERS, COUNT(DISTINCT o."CtlAccount") NCTL
```

| BILLS | SERVICE | NUMATCARD | COMMENTS | BRANCH2 | SAMEDATE | ATTACHED | U_BILTY | U_TRANS | U_VEH | NSERIES | NUSERS | NCTL |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 198 | **198** | 198 | 197 | 197 | **151** | **198** | 9 | 9 | 7 | 11 | 6 | 1 |

`DocType='S'` and `AtcEntry>0` on **100 %**. The three transport UDFs are effectively unused.

## 2 · Line fill rates (Oil, 1,093 lines)

```sql
SELECT COUNT(*) LINES,
 SUM(CASE WHEN l."BaseType"=20 THEN 1 ELSE 0 END) FROM_GRPO,
 SUM(CASE WHEN l."BaseType"=-1 THEN 1 ELSE 0 END) KEYED,
 SUM(CASE WHEN l."ItemCode" IS NOT NULL AND l."ItemCode"<>'' THEN 1 ELSE 0 END) HASITEM,
 SUM(CASE WHEN l."WtLiable"='Y' THEN 1 ELSE 0 END) WTLIABLE,
 SUM(CASE WHEN l."OcrCode"<>'' THEN 1 ELSE 0 END) DIM1, … DIM2, DIM3, DIM4, DIM5,
 SUM(CASE WHEN l."LocCode" IS NOT NULL THEN 1 ELSE 0 END) LOC,
 SUM(CASE WHEN l."U_Recvd_Qty">0 THEN 1 ELSE 0 END) RQTY,
 SUM(CASE WHEN l."SacEntry">0 THEN 1 ELSE 0 END) SAC
FROM "JIVO_OIL_HANADB"."PCH1" l JOIN … (population)
```

| LINES | FROM_GRPO | KEYED | HASITEM | WTLIABLE | DIM1 | DIM2 | DIM3 | DIM4 | DIM5 | LOC | RQTY | SAC |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,093 | **1,073** | 20 | **0** | 834 | 1,093 | 1,093 | 1,093 | **0** | 1,085 | 1,093 | **0** | 1,077 |

`U_Recvd_Qty` is **zero on every transport line** — it is the fuel-bill field (C-0025),
not this one. Dim4 is never used.

## 3 · GL accounts

```sql
SELECT l."AcctCode", a."AcctName", COUNT(*) N, SUM(l."LineTotal") AMT … GROUP BY 1,2
```

| Acct | Name | Lines | ₹ |
|---|---|---:|---:|
| **5670001** | FREIGHT AND CARTAGE OUTWARD-INDIRECT EXP | **1,077** | 88,70,636 |
| 5100002 | FREIGHT INWARD CHARGES-DIRECT | 8 | 5,61,900 |
| 1212013 | BUILDINGS WIP CONSTRUCTION -NEW BUILDING | 6 | 76,282 |
| 5680028 | FREIGHT INWARD-INDIRECT | 1 | 4,814 |
| 5500001 | FREIGHT EXPENSE-IMPORT | 1 | 84,000 |

## 4 · Dimensions

Dim3 (Budget), by book:

| Book | Value | Lines |
|---|---|---:|
| Oil | `Del Bkhp` / `Factory` | 1,077 / 16 |
| Mart | `SUPPLY-C` | 530 |
| Bev | `Del Bkhp` / `Factory` | 815 / 4 |

Dim5 (Oil, top 11): PB 316 · DL 267 · HR 145 · MH 51 · UP 44 · TE 39 · KN 30 · WB 27 ·
RJ 26 · GJ 24 · UK 22. 23 distinct.

## 5 · Tax codes — `PCH4` (Oil)

```sql
SELECT t."StaCode", t."TaxRate", t."TaxAcct", a."AcctName", COUNT(*) N, SUM(t."TaxSum")
FROM "JIVO_OIL_HANADB"."PCH4" t JOIN … GROUP BY 1,2,3,4
```

| StaCode | Rate | Account | Name | Rows | ₹ |
|---|---:|---|---|---:|---:|
| `RCGS@2.5` | 2.5 | 2137102 | INPUT CGST @2.5 % RCM | 470 | 69,733 |
| `RSGS@2.5` | 2.5 | 2137101 | INPUT SGST @2.5 % RCM | 470 | 69,733 |
| `RIGST@5` | 5 | 2137109 | INPUT IGST @5 % RCM | 412 | 2,55,008 |
| `IGST@18` | 18 | 2131004 | INPUT IGST @18 % | 204 | 2,86,894 |
| `Exampt` | 0 | 2131017 | INPUT EXEMPT | 6 | 0 |
| `CGST@9`/`SGST@9` | 9 | 2131012 / 2131011 | | 1 each | 3,420 each |

`PCH1.VatGroup` is **blank** on these lines — the tax code lives in `PCH4.StaCode`, so do
not test `VatGroup` to decide RCM. Test `OPCH.VatSum = 0` while `PCH1.VatSum > 0`.

## 6 · Series actually used

```sql
SELECT SUBSTRING(TO_VARCHAR(o."DocDate",'YYYY-MM-DD'),1,7) MTH, o."Series", n."SeriesName", o."DocSubType", COUNT(*)
FROM … LEFT JOIN "<DB>"."NNM1" n ON n."Series"=o."Series" GROUP BY 1,2,3,4
```

| Book | Month | Series | Name | SubType | N |
|---|---|---:|---|---|---:|
| Oil | 2026-08 | 3684 | HR_G0826 | GA | 5 |
| Oil | 2026-08 | 3324 | HR_B0826 | -- | 1 |
| Oil | 2026-07 | 3683 / 3323 | HR_G0726 / HR_B0726 | GA / -- | 43 / 11 |
| Mart | 2026-08 | 2754 / 2766 | DL_G0826 / HR_G0826 | GA | 4 / 3 |
| Bev | 2026-08 | 2777 / 2678 | HR_G0826 / HR_B0826 | GA / -- | 4 / 1 |

Mart branch split, FY26-27: **BPLId 1 DELHI 85 · 2 HARYANA 60**. Oil: 197 of 198 on 2.

## 7 · GRPO linkage

```sql
SELECT AVG(x."NGRPO"), MAX(x."NGRPO"), AVG(x."LAGD"), MAX(x."LAGD"), MIN(x."LAGD"), COUNT(*), SUM(CASE WHEN x."LAGD"=0 THEN 1 ELSE 0 END)
FROM (SELECT o."DocEntry", COUNT(DISTINCT l."BaseEntry") "NGRPO",
             DAYS_BETWEEN(MAX(p."DocDate"), MAX(o."DocDate")) "LAGD"
      FROM "JIVO_OIL_HANADB"."OPCH" o
      JOIN "JIVO_OIL_HANADB"."PCH1" l ON l."DocEntry"=o."DocEntry"
      JOIN "JIVO_OIL_HANADB"."OPDN" p ON p."DocEntry"=l."BaseEntry"
      JOIN … WHERE … AND l."BaseType"=20 GROUP BY o."DocEntry") x
```

avg GRPOs/bill **3.19**, max **26**, bills 182; posting lag avg **19.4 d**, max 109,
min 0, same-day only **4**.

GRPO reference fill: 604 Oil transporter GRPOs FY26-27, `NumAtCard` filled on **603** —
it holds the **bilty number**.

Authors: GRPOs **GURCHARAN 551** · B1i 43 · NAVDEEP 10. Bills: SATNAM 59 · NEETU 56 ·
HARSH 40 · ISHWENDRA 34 · LOVPREET 8 · ABHIJEET 1.

### What changes between GRPO and bill

```sql
JOIN "JIVO_OIL_HANADB"."PDN1" p ON p."DocEntry"=l."BaseEntry" AND p."LineNum"=l."BaseLine"
… AND l."BaseType"=20
```

| Matched | Acct | Dim1 | Dim2 | Dim3 | Dim5 | WtLiable | of which N→Y | Amount | Desc | SAC | LocCode |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,073 | 3 | 24 | 27 | **0** | 19 | 40 | **32** | 42 | 11 | 1 | **0** |

The copy is near-perfect; the operator's real edits are **TDS liability** and the
occasional **amount**.

## 8 · TDS

Codes on transporter bills since 2026-06-01 (Oil, `PCH5` rows):
`1024` 50 · `C194` 27 · `1023` 10 · `194C` 1.

Applied vs not, FY26-27 (Oil), by vendor — the threshold test:

| Vendor | `OCRD.WTLiable` | Bills | With TDS | Avg with | Avg without | Max untaxed | Min taxed |
|---|---|---:|---:|---:|---:|---:|---:|
| PICK & SHIP | Y | 96 | 84 | 18,112 | **18,137** | 56,297 | 2,544 |
| DELHI PUNJAB | Y | 20 | 14 | 116,713 | 119,395 | 168,686 | 59,708 |
| ARNAV | **N** | 19 | 0 | — | 40,106 | 132,881 | — |
| ABHIMAN | Y | 14 | **14** | 165,468 | — | — | 25,970 |
| BOMBAY SRINAGAR | Y | 12 | 12 | 67,482 | — | — | 3,430 |
| CHOUDHARY EARTH MOVERS | Y | 4 | **0** | — | 19,071 | 26,045 | — |

Averages with and without TDS are the same → **not amount-driven**.

```sql
SELECT COUNT(*) N, SUM(o."DocTotal") VAL FROM … WHERE c."WTLiable"='Y' AND o."WTSum"=0
```
→ **27 bills, ₹14,18,796**, 2026-04-01 → 2026-08-04.

### The PAN rule (24 of 25 cards)

`CRD4.WTCode` vs the 4th character of `CRD7.TaxId0`:

| PAN 4th char | Meaning | Code | Cards |
|---|---|---|---|
| `C` `F` `A` | company / firm / AOP | **1024** (2 %) | AAQ**C**P (Pick&Ship), ACL**F**A (Abhiman), AAN**F**D (Delhi Punjab), AAX**F**B (Bombay Srinagar), AAN**F**M, ABI**F**A, AAG**C**R, AAI**C**P, AAE**C**O, AAL**C**T |
| `P` | individual | **1023** (1 %), Bev **1230** | AOU**P**J, AEN**P**S, LIA**P**S, EUY**P**K, ASI**P**V, DQF**P**K, HIG**P**S, FKJ**P**M, BRF**P**G, AGS**P**N, APP**P**B, BUI**P**K, ACB**P**Y |
| exception | | | `ANKPP8181E` — ABC TRANSPORT COMPANY **PRIVATE LIMITED** on a `P` PAN, carrying `1024` |

Master-data inconsistency: **ARNAV** (PAN `ACBPY4022H`) is `WTLiable='N'` in Oil and
Beverages, `'Y'` with code `1023` in Mart.

## 9 · SAC codes — the Mart anomaly

```sql
LEFT JOIN "<DB>"."OSAC" s ON s."AbsEntry" = l."SacEntry"
```

| Book | SacEntry | ServCode | Name | Lines |
|---|---:|---|---|---:|
| Oil | 2 | 9967 | Freight | 1,029 |
| Oil | 40 | 9965 | FREIGHT | 48 |
| Bev | 3 | 996812 | freight | 815 |
| **Mart** | **-426** | **00997136** | **Freight insurance services & Travel insurance services** | **387** |
| Mart | -485 | 00996511 | Road transport services of Goods… | 81 |
| Mart | -451 | 00996791 | Goods transport agency services for road transport | 12 |

Mart's most-used SAC on freight lines is an **insurance** code. *Measured 2026-08-27;
consequence for GST reporting inferred, not verified.*

## 10 · Attachments

```sql
JOIN "JIVO_OIL_HANADB"."ATC1" a ON a."AbsEntry" = o."AtcEntry"
```
pdf **915** · png 1 · jpeg 1 — attachment *rows* (`ATC1`) reached from the 198 bills'
`AtcEntry` groups, so a group can hold more than one file. Every one of the 198 bills has
`AtcEntry > 0`.

## 11 · Golden example — BOMBAY SRINAGAR `018`

**A/P `OPCH` DocEntry 49157** (DocNum 626074370)

| | |
|---|---|
| DocType / Series / SubType | `S` / 3683 `HR_G0726` / `GA` |
| CardCode / branch / control | `VENDA000972` / 2 FACTORY / `2110004` |
| NumAtCard / DocDate / TaxDate | `018` / 2026-07-16 / 2026-07-16 |
| Comments | `BILLTY NO. 1832 Based On Goods Receipt PO 2026076699.` |
| DocTotal / VatSum / WTSum | **57,648** / **0** / **1,177** |
| AtcEntry / UserSign | 169776 / 16 (NEETU) |

Lines — all `5670001`, `WtLiable Y`, Dim2 `07-2026`, Dim3 `Del Bkhp`, Dim5 `MH`,
`LocCode 2`, `SacEntry 2`, `BaseType 20 → 24977`:

| # | Dim1 | LineTotal | line VatSum |
|---:|---|---:|---:|
| 0 | SUNFLOWR | 14,518.62 | 725.93 |
| 1 | OLIVE | 36,024.81 | 1,801.24 |
| 2 | OLIVE | 4,140.78 | 207.04 |
| 3 | OLIVE | 4,140.78 | 207.04 |

`PCH5`: `WTCode 1024`, rate 2 %, base **58,825**, withheld **1,177**, account `2133018`.
`PCH4`: four `RIGST@5` rows → `2137109`, total 2,941.

**Source GRPO 24977** (DocNum 2026076699), 2026-07-07, `NumAtCard` = **1832** = the
bilty, Comments `BILLTY NO. 1832`, DocTotal 58,825, series 2476, branch 2, raised by
UserSign 28 (GURCHARAN), lines keyed from scratch (`BaseType -1`), now `DocStatus C`.

Arithmetic: 58,825 − 1,177 = **57,648**. GST is RCM and never enters what we owe.

## 12 · What this CLI has done

`queries/USER39/sap-writes.jsonl` and `queries/manager/sap-writes.jsonl`, 2026-08-25:

| Time | User | Payload | Result |
|---|---|---|---|
| 17:39:13 | manager | no `DocType`, 19 GRPO lines | **400** `[SAP -5002] 234103405 - Base document type and target document type do not match` |
| 17:39:35 | manager | + `"DocType": "dDocument_Service"` | 201 `DocEntry=39828` |
| 17:50:53 | USER39 | same payload | 201 `DocEntry=39829` |

```sql
SELECT "DocEntry","NumAtCard","DocTotal","WddStatus","DocStatus","CANCELED","UserSign"
FROM "JIVO_MART_HANADB"."ODRF" WHERE "NumAtCard"='DEL/260313';
-- 39829 | DEL/260313 | 737988 | '-' | O | N | 53      (39828 no longer present)
SELECT * FROM "JIVO_MART_HANADB"."OPCH" WHERE "NumAtCard"='DEL/260313';  -- 0 rows
```

Draft 39829's lines carry Dim1 `GROUNDNT`/`MUSTARD`, Dim2 `07-2026`, Dim3 `SUPPLY-C`,
Dim5 `KN`, `LocCode 2`, `SacEntry -426` — **identical to source GRPOs 13609/13621/…**,
which is the proof that a service GRPO hands over all five dimensions through the
Service Layer. `WTSum` is **0**.

## 13 · Open GRPO backlog (2026-08-27)

`OPDN` `DocStatus='O'`, `CANCELED='N'`, TRANSPORTER group. C-0019 applies — treat as
candidates, confirm per bill.

| Book | GRPOs | ₹ | Largest |
|---|---:|---:|---|
| Oil | 138 | 21,49,175 | DELHI PUNJAB 78 · ARNAV 29 · MAHAVIR 7 · PICK & SHIP 6 |
| Mart | 29 | 14,15,177 | ABHIMAN 11 (₹10.88 L) · PICK & SHIP 6 · DELHI PUNJAB 6 |
| Bev | 70 | 4,53,716 | ARNAV 56 · DELHI PUNJAB 4 |

Oil's oldest open transporter GRPO dates to **2025-02-20** (DELHI PUNJAB).
