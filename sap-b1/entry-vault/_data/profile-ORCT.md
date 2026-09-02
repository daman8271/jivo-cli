# `ORCT` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 14,149 | 1,560 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 11,391 | 2,017 | `DocDate` | 2025-01-01 → 2026-08-24 |
| BEV | 4,166 | 1,219 | `DocDate` | 2024-09-30 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 14,149 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 14,149 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Canceled` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 682 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 1,218 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 908 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 906 | |
| `Address` | NVARCHAR(254) | 84% | 88% | 89% | 81% | 86% | 93% | 672 | |
| `CashAcct` | NVARCHAR(15) | 9% | 21% | 33% | 4% | 21% | 34% | 3 | |
| `CashSum` | DECIMAL | 9% | 21% | 33% | 4% | 21% | 34% | 539 | |
| `TrsfrAcct` | NVARCHAR(15) | 91% | 79% | 67% | 96% | 79% | 66% | 19 | |
| `TrsfrSum` | DECIMAL | 91% | 79% | 67% | 96% | 79% | 66% | 7,350 | |
| `TrsfrSumFC` | DECIMAL | <1% | — | <1% | <1% | — | — | 13 | |
| `TrsfrDate` | TIMESTAMP | 91% | 79% | 67% | 96% | 79% | 66% | 1,214 | |
| `TrsfrRef` | NVARCHAR(27) | 6% | 33% | — | — | 30% | — | 789 | |
| `PayNoDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `NoDocSum` | DECIMAL | 91% | 51% | 84% | 97% | 68% | 73% | 7,093 | |
| `NoDocSumFC` | DECIMAL | <1% | — | <1% | <1% | — | — | 13 | |
| `DocCurr` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DiffCurr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocRate` | DECIMAL | <1% | — | <1% | <1% | — | — | 14 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocTotal` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 7,584 | |
| `DocTotalFC` | DECIMAL | <1% | — | <1% | <1% | — | — | 13 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 14,149 | |
| `Ref2` | NVARCHAR(50) | <1% | <1% | <1% | 4% | <1% | 1% | 38 | |
| `CounterRef` | NVARCHAR(50) | 17% | <1% | <1% | 4% | <1% | 1% | 2,331 | |
| `Comments` | NVARCHAR(254) | 99% | 98% | 98% | 100% | 99% | 99% | 11,531 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 887 | |
| `TransId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 14,149 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 699 | |
| `ShowAtCard` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SpiltTrans` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 84% | 87% | 88% | 79% | 86% | 93% | 774 | |
| `CashSumSy` | DECIMAL | 9% | 21% | 33% | 4% | 21% | 34% | 539 | |
| `TrsfrSumSy` | DECIMAL | 91% | 79% | 67% | 96% | 79% | 66% | 7,350 | |
| `NoDocSumSy` | DECIMAL | 91% | 51% | 84% | 97% | 68% | 73% | 7,093 | |
| `DocTotalSy` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 7,584 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 579 | |
| `ApplyVAT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 1,218 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShowJDT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 19 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `SpltCredLn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Submitted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Status` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeNum` | INTEGER | 84% | 100% | 100% | 100% | 100% | 100% | 11,856 | |
| `Proforma` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BpAct` | NVARCHAR(15) | 85% | 88% | 89% | 81% | 86% | 93% | 24 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `PaPriority` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayToCode` | NVARCHAR(50) | 84% | 88% | 89% | 81% | 86% | 93% | 763 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WizDunBlck` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `VatDate` | TIMESTAMP | 84% | 100% | 100% | 100% | 100% | 100% | 579 | |
| `PaymType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CancelDate` | TIMESTAMP | 4% | 2% | 2% | 4% | 2% | 1% | 270 | |
| `OpenBal` | DECIMAL | 22% | 14% | 9% | 28% | 38% | 11% | 2,145 | |
| `OpenBalFc` | DECIMAL | <1% | — | <1% | — | — | — | 9 | |
| `OpenBalSc` | DECIMAL | 22% | 14% | 9% | 28% | 38% | 11% | 2,145 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LocCode` | INTEGER | 16% | — | — | — | — | — | 1 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShowDocNo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `BPLCentPmt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DraftKey` | INTEGER | — | <1% | — | — | — | — | 0 | |
| `AgrNo` | INTEGER | <1% | — | — | — | — | — | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 10,608 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 10,612 | |
| `PmntWTCert` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 4% | <1% | 2% | 6% | — | <1% | 608 | |
| `EnblDpmTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Pymnt_Mode` | NVARCHAR(10) | <1% | <1% | <1% | 2% | 3% | 1% | 3 | |
| `U_Pay_Report_Gen` | NVARCHAR(10) | 100% | — | 100% | 100% | — | 100% | 1 | |
| `U_Pay_Rep_Gen_Inf` | NVARCHAR(50) | <1% | — | — | — | — | — | 2 | |
| `U_Type_of_Advance` | NVARCHAR(20) | <1% | <1% | <1% | 1% | <1% | <1% | 2 | |
| `U_Adv_Settl_Dt` | TIMESTAMP | <1% | n/a | <1% | <1% | n/a | — | 3 | |
| `U_URGENCY` | NVARCHAR(10) | <1% | <1% | <1% | <1% | <1% | <1% | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_Adv_Settl_Dt` | OIL, BEV | **MART** |
| `U_Adv_settl_Dt` | MART | **OIL, BEV** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`DocType`** (3 values) — `C`×11,726, `A`×2,114, `S`×309
- **`Canceled`** (2 values) — `N`×13,653, `Y`×496
- **`Handwrtten`** (2 values) — `N`×11,856, `Y`×2,293
- **`Printed`** (2 values) — `N`×11,855, `Y`×2,294
- **`CashAcct`** (4 values) — `NULL`×12,902, `1105003`×926, `1105001`×319, `1105002`×2
- **`TrsfrAcct`** (20 values) — `2201101`×6,393, `3200003`×2,293, `1104201`×1,271, `NULL`×1,247, `2201105`×1,015, `1104104`×780, `1104107`×563, `2201102`×319, `1104202`×113, `1104106`×98, `2201103`×17, `1104102`×10, `2201202`×10, `2201206`×4, `2201205`×4, `2201207`×4, `2201402`×3, `2201104`×2, `1104103`×2, `5200015`×1
- **`TrsfrSumFC`** (13 values) — `0.000000`×14,137, `34125.000000`×1, `132176.000000`×1, `31026.000000`×1, `2450.000000`×1, `31376.000000`×1, `342375.000000`×1, `94384.350000`×1, `193163.000000`×1, `226838.000000`×1, `552759.400000`×1, `1859.000000`×1, `4953.000000`×1
- **`PayNoDoc`** (2 values) — `Y`×12,833, `N`×1,316
- **`NoDocSumFC`** (13 values) — `0.000000`×14,137, `94384.350000`×1, `4953.000000`×1, `1859.000000`×1, `226838.000000`×1, `193163.000000`×1, `552759.000000`×1, `342375.000000`×1, `31376.000000`×1, `2450.000000`×1, `31026.000000`×1, `132176.000000`×1, `34125.000000`×1
- **`DocCurr`** (2 values) — `INR`×14,137, `USD`×12
- **`DiffCurr`** (1 values) — `N`×14,149
- **`DocRate`** (14 values) — `0.000000`×14,096, `1.000000`×41, `83.050000`×1, `85.235000`×1, `86.260000`×1, `0.000100`×1, `85.570000`×1, `91.750300`×1, `85.647500`×1, `85.430000`×1, `87.050000`×1, `86.657500`×1, `76.530000`×1, `85.395000`×1
- **`SysRate`** (1 values) — `1.000000`×14,149
- **`DocTotalFC`** (13 values) — `0.000000`×14,137, `132176.000000`×1, `31376.000000`×1, `34125.000000`×1, `31026.000000`×1, `342375.000000`×1, `94384.350000`×1, `193163.000000`×1, `226838.000000`×1, `552759.400000`×1, `1859.000000`×1, `4953.000000`×1, `2450.000000`×1
- **`ShowAtCard`** (2 values) — `N`×14,120, `Y`×29
- **`SpiltTrans`** (1 values) — `N`×14,149
- **`CreateTran`** (1 values) — `Y`×14,149
- **`ObjType`** (1 values) — `24`×14,149
- **`ApplyVAT`** (1 values) — `N`×14,149
- **`Series`** (24 values) — `-1`×2,293, `698`×1,040, `697`×966, `696`×858, `699`×718, `2155`×635, `2154`×540, `2159`×509, `2156`×499, `2157`×489, `2163`×470, `2162`×456, `2561`×451, `2563`×441, `2165`×438, `700`×433, `701`×416, `2158`×405, `2164`×401, `2160`×395, `2562`×372, `2560`×349, `2161`×349, `2564`×226
- **`confirmed`** (1 values) — `N`×14,149
- **`ShowJDT`** (2 values) — `Y`×9,387, `N`×4,762
- **`UserSign`** (19 values) — `20`×6,841, `1`×2,295, `14`×2,144, `37`×1,252, `10`×1,190, `27`×107, `22`×103, `24`×91, `53`×57, `39`×24, `25`×10, `23`×9, `11`×8, `13`×8, `46`×5, `15`×2, `17`×1, `40`×1, `2`×1
- **`FinncPriod`** (24 values) — `6`×2,293, `9`×1,040, `8`×966, `7`×858, `10`×718, `15`×635, `14`×540, `19`×509, `16`×499, `17`×489, `23`×470, `22`×456, `42`×451, `44`×441, `25`×438, `11`×433, `12`×416, `18`×405, `24`×401, `20`×395, `43`×372, `21`×349, `41`×349, `45`×226
- **`SpltCredLn`** (1 values) — `N`×14,149
- **`Submitted`** (1 values) — `N`×14,149
- **`Status`** (1 values) — `N`×14,149
- **`Proforma`** (1 values) — `N`×14,149
- **`BpAct`** (25 values) — `1101001`×3,593, `1101005`×2,665, `∅`×2,113, `1101008`×1,871, `1101004`×1,282, `1101006`×842, `1101015`×429, `1101012`×284, `1101014`×212, `1101010`×169, `2110004`×148, `1101007`×146, `1101013`×116, `2110003`×73, `1101009`×68, `1101002`×44, `2110005`×39, `2110001`×36, `2110008`×6, `1102002`×4, `2110002`×4, `2110006`×2, `2121001`×1, `NULL`×1, `1102001`×1
- **`PIndicator`** (24 values) — `Sep-24-25`×2,293, `Dec-24-25`×1,040, `Nov-24-25`×966, `Oct-24-25`×858, `Jan-24-25`×718, `MAY-25-26`×635, `APR-25-26`×540, `SEP-25-26`×509, `JUN-25-26`×499, `JUL-25-26`×489, `JAN-25-26`×470, `DEC-25-26`×456, `MAY-26-27`×451, `JUL-26-27`×441, `MAR-25-26`×438, `Feb-24-25`×433, `Mar-24-25`×416, `AUG-25-26`×405, `FEB-25-26`×401, `OCT-25-26`×395, `JUN-26-27`×372, `APR-26-27`×349, `NOV-25-26`×349, `AUG-26-27`×226
- **`PaPriority`** (1 values) — `6`×14,149
- **`IsPaytoBnk`** (1 values) — `N`×14,149
- **`WizDunBlck`** (1 values) — `N`×14,149
- **`VersionNum`** (2 values) — `10.00.250.15`×10,735, `10.00.310.21`×3,414
- **`PaymType`** (1 values) — `N`×14,149
- **`OpenBalFc`** (9 values) — `0.000000`×14,141, `34125.000000`×1, `132176.000000`×1, `31026.000000`×1, `31376.000000`×1, `94384.350000`×1, `4953.000000`×1, `193163.000000`×1, `342375.000000`×1
- **`WddStatus`** (1 values) — `-`×14,149
- **`LocCode`** (2 values) — `NULL`×11,856, `1`×2,293
- **`ResidenNum`** (1 values) — `1`×14,149
- **`ShowDocNo`** (1 values) — `Y`×14,149
- **`BPLId`** (5 values) — `2`×7,177, `1`×6,418, `3`×544, `7`×9, `6`×1
- **`BPLName`** (5 values) — `FACTORY`×7,177, `DELHI`×6,418, `PUNJAB`×544, `DELHI INFO`×9, `DELHI ISD`×1
- **`VATRegNum`** (4 values) — `06AACCJ4223F1Z0`×7,177, `07AACCJ4223F1ZY`×6,427, `03AACCJ4223F1Z6`×544, `07AACCJ4223F2ZX`×1
- **`BPLCentPmt`** (2 values) — `N`×12,419, `Y`×1,730
- **`AgrNo`** (2 values) — `NULL`×14,148, `10`×1
- **`PmntWTCert`** (1 values) — `N`×14,149
- **`DPPStatus`** (1 values) — `N`×14,149
- **`EnblDpmTax`** (1 values) — `N`×14,149
- **`DataVers`** (4 values) — `1`×13,592, `2`×546, `3`×9, `4`×2
- **`DigPayment`** (1 values) — `N`×14,149
- **`BaseType`** (1 values) — `-1`×14,149
- **`U_Pymnt_Mode`** (4 values) — `NULL`×14,107, `NEFT`×33, `RTGS`×8, `FT`×1
- **`U_Pay_Report_Gen`** (1 values) — `N`×14,149
- **`U_Pay_Rep_Gen_Inf`** (3 values) — `NULL`×14,147, `31.10`×1, `30.4`×1
- **`U_Type_of_Advance`** (3 values) — `NULL`×14,114, `One Time Settlement`×34, `Adjustable in EMI`×1
- **`U_Adv_Settl_Dt`** (4 values) — `NULL`×14,140, `2026-06-30 00:00:00.0000000`×6, `2026-04-30 00:00:00.0000000`×2, `2026-03-31 00:00:00.0000000`×1
- **`U_URGENCY`** (2 values) — `NULL`×14,139, `H`×10
