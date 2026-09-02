# `OVPM` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 14,851 | 2,307 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 2,294 | 533 | `DocDate` | 2025-01-01 → 2026-08-24 |
| BEV | 1,925 | 252 | `DocDate` | 2024-10-15 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 14,851 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 14,851 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Canceled` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 638 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 870 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 1,610 | |
| `CardName` | NVARCHAR(200) | 66% | 70% | 85% | 64% | 82% | 88% | 1,277 | |
| `Address` | NVARCHAR(254) | 66% | 70% | 85% | 64% | 82% | 88% | 1,088 | |
| `CashAcct` | NVARCHAR(15) | <1% | <1% | <1% | <1% | <1% | <1% | 3 | |
| `CashSum` | DECIMAL | <1% | <1% | <1% | <1% | <1% | <1% | 12 | |
| `CreditSum` | DECIMAL | <1% | — | — | — | — | — | 54 | |
| `TrsfrAcct` | NVARCHAR(15) | 99% | 100% | 99% | 100% | 99% | 100% | 24 | |
| `TrsfrSum` | DECIMAL | 99% | 100% | 99% | 100% | 99% | 100% | 9,215 | |
| `TrsfrSumFC` | DECIMAL | <1% | — | — | <1% | — | — | 78 | |
| `TrsfrDate` | TIMESTAMP | 99% | 100% | 99% | 100% | 99% | 100% | 867 | |
| `TrsfrRef` | NVARCHAR(27) | <1% | — | <1% | — | — | — | 6 | |
| `PayNoDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `NoDocSum` | DECIMAL | 62% | 59% | 45% | 62% | 60% | 40% | 5,611 | |
| `NoDocSumFC` | DECIMAL | <1% | — | — | <1% | — | — | 78 | |
| `DocCurr` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `DiffCurr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocRate` | DECIMAL | 3% | — | — | <1% | — | — | 82 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocTotal` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 9,257 | |
| `DocTotalFC` | DECIMAL | <1% | — | — | <1% | — | — | 78 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 14,851 | |
| `Ref2` | NVARCHAR(50) | 3% | <1% | <1% | 6% | <1% | 3% | 37 | |
| `CounterRef` | NVARCHAR(50) | 6% | <1% | <1% | 6% | <1% | 3% | 462 | |
| `Comments` | NVARCHAR(254) | 97% | 75% | 98% | 99% | 42% | 98% | 7,737 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 1,611 | |
| `TransId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 14,851 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 684 | |
| `ShowAtCard` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SpiltTrans` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 50% | 60% | 75% | 48% | 70% | 83% | 1,136 | |
| `CashSumSy` | DECIMAL | <1% | <1% | <1% | <1% | <1% | <1% | 12 | |
| `CredSumSy` | DECIMAL | <1% | — | — | — | — | — | 54 | |
| `TrsfrSumSy` | DECIMAL | 99% | 100% | 99% | 100% | 99% | 100% | 9,215 | |
| `NoDocSumSy` | DECIMAL | 62% | 59% | 45% | 62% | 60% | 40% | 5,611 | |
| `DocTotalSy` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 9,257 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 571 | |
| `ApplyVAT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 870 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShowJDT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `SpltCredLn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Submitted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Status` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeNum` | INTEGER | 97% | 100% | 100% | 100% | 100% | 100% | 14,426 | |
| `Proforma` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BpAct` | NVARCHAR(15) | 66% | 71% | 85% | 64% | 82% | 88% | 19 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `PaPriority` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayToCode` | NVARCHAR(50) | 66% | 70% | 85% | 64% | 82% | 88% | 970 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PBnkCnt` | NVARCHAR(3) | <1% | <1% | <1% | <1% | <1% | — | 1 | |
| `PBnkCode` | NVARCHAR(30) | <1% | <1% | <1% | <1% | <1% | — | 3 | |
| `PBnkAccnt` | NVARCHAR(50) | <1% | <1% | <1% | <1% | <1% | — | 4 | |
| `WizDunBlck` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `VatDate` | TIMESTAMP | 97% | 100% | 100% | 100% | 100% | 100% | 570 | |
| `PaymType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CancelDate` | TIMESTAMP | 6% | 10% | 7% | 5% | 7% | 4% | 406 | |
| `OpenBal` | DECIMAL | 6% | 20% | 5% | 16% | 37% | 20% | 594 | |
| `OpenBalFc` | DECIMAL | <1% | — | — | <1% | — | — | 41 | |
| `OpenBalSc` | DECIMAL | 6% | 20% | 5% | 16% | 37% | 20% | 594 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LocCode` | INTEGER | 3% | — | — | — | — | — | 1 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShowDocNo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `BPLCentPmt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DraftKey` | INTEGER | 9% | <1% | 9% | 8% | — | 6% | 1,376 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 11,259 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 11,299 | |
| `PmntWTCert` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 57% | 44% | 74% | 63% | 56% | 87% | 8,489 | |
| `EnblDpmTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Pymnt_Mode` | NVARCHAR(10) | 97% | 98% | 99% | 100% | 100% | 100% | 3 | |
| `U_Pay_Report_Gen` | NVARCHAR(10) | 100% | — | 100% | 100% | — | 100% | 1 | |
| `U_Pay_Rep_Gen_Inf` | NVARCHAR(50) | — | <1% | — | — | — | — | 0 | |
| `U_Type_of_Advance` | NVARCHAR(20) | 89% | 56% | 92% | 83% | 49% | 88% | 2 | |
| `U_Adv_Settl_Dt` | TIMESTAMP | 27% | n/a | 30% | 29% | n/a | 29% | 106 | |
| `U_UNE_MLOC` | NVARCHAR(80) | <1% | — | — | — | — | — | 1 | |
| `U_URGENCY` | NVARCHAR(10) | 7% | 13% | 5% | 30% | 27% | 27% | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_Adv_Settl_Dt` | OIL, BEV | **MART** |
| `U_Adv_settl_Dt` | MART | **OIL, BEV** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`DocType`** (3 values) — `S`×9,705, `A`×5,061, `C`×85
- **`Canceled`** (2 values) — `N`×13,912, `Y`×939
- **`Handwrtten`** (2 values) — `N`×14,426, `Y`×425
- **`Printed`** (2 values) — `N`×14,425, `Y`×426
- **`CashAcct`** (4 values) — `NULL`×14,837, `1105003`×9, `1105001`×3, `1105002`×2
- **`CashSum`** (12 values) — `0.000000`×14,837, `0.000100`×4, `59970.000000`×1, `0.950000`×1, `0.117600`×1, `50000.000000`×1, `129.316200`×1, `0.001000`×1, `10.000000`×1, `82000.000000`×1, `0.098900`×1, `0.737700`×1
- **`TrsfrAcct`** (25 values) — `1104107`×6,157, `1104104`×2,449, `2201102`×2,200, `2201101`×2,182, `1104106`×750, `3200003`×425, `2201105`×331, `2201106`×101, `NULL`×90, `2201202`×27, `2201205`×25, `2201402`×22, `2201104`×18, `2201204`×12, `2201207`×10, `2201206`×10, `2201103`×10, `1104108`×8, `1104103`×6, `1104102`×5, `2201209`×4, `5200015`×3, `2201208`×3, `2201405`×2, `1104109`×1
- **`TrsfrRef`** (7 values) — `NULL`×14,845, `*219`×1, `∅`×1, `*`×1, `HDFC0000396`×1, `*549`×1, `CMS/001767496038/JULYFACTOR`×1
- **`PayNoDoc`** (2 values) — `Y`×9,229, `N`×5,622
- **`DocCurr`** (3 values) — `INR`×14,764, `USD`×67, `EUR`×20
- **`DiffCurr`** (1 values) — `N`×14,851
- **`SysRate`** (1 values) — `1.000000`×14,851
- **`ShowAtCard`** (2 values) — `N`×9,943, `Y`×4,908
- **`SpiltTrans`** (1 values) — `N`×14,851
- **`CreateTran`** (1 values) — `Y`×14,851
- **`CashSumSy`** (12 values) — `0.000000`×14,837, `0.000100`×4, `0.950000`×1, `59970.000000`×1, `0.098900`×1, `0.737700`×1, `10.000000`×1, `0.001000`×1, `129.316200`×1, `50000.000000`×1, `0.117600`×1, `82000.000000`×1
- **`ObjType`** (1 values) — `46`×14,851
- **`ApplyVAT`** (1 values) — `N`×14,851
- **`Series`** (24 values) — `2217`×810, `2215`×732, `710`×707, `2214`×698, `2598`×691, `2219`×679, `715`×679, `711`×643, `2223`×642, `2222`×632, `2225`×632, `2218`×614, `2216`×611, `2596`×608, `713`×607, `2220`×607, `714`×590, `2224`×588, `2597`×585, `712`×566, `2599`×562, `2221`×554, `-1`×425, `2600`×389
- **`confirmed`** (1 values) — `N`×14,851
- **`ShowJDT`** (2 values) — `Y`×9,121, `N`×5,730
- **`UserSign`** (10 values) — `14`×11,736, `10`×2,522, `1`×426, `39`×58, `13`×46, `11`×17, `48`×14, `46`×13, `15`×11, `17`×8
- **`FinncPriod`** (24 values) — `17`×810, `15`×732, `7`×707, `14`×698, `43`×691, `12`×679, `19`×679, `8`×643, `23`×642, `25`×632, `22`×632, `18`×614, `16`×611, `41`×608, `10`×607, `20`×607, `11`×590, `24`×588, `42`×585, `9`×566, `44`×562, `21`×554, `6`×425, `45`×389
- **`SpltCredLn`** (1 values) — `N`×14,851
- **`Submitted`** (1 values) — `N`×14,851
- **`Status`** (1 values) — `N`×14,851
- **`Proforma`** (1 values) — `N`×14,851
- **`BpAct`** (20 values) — `∅`×5,052, `2110003`×3,206, `2110004`×3,125, `2110005`×1,915, `2110001`×1,300, `2110002`×74, `2110008`×52, `1101001`×36, `1101005`×24, `2110007`×20, `2110006`×10, `NULL`×9, `1101009`×8, `1101008`×7, `1101007`×4, `1101012`×3, `1101004`×2, `2121003`×2, `1102002`×1, `1101015`×1
- **`PIndicator`** (24 values) — `JUL-25-26`×810, `MAY-25-26`×732, `Oct-24-25`×707, `APR-25-26`×698, `JUN-26-27`×691, `SEP-25-26`×679, `Mar-24-25`×679, `Nov-24-25`×643, `JAN-25-26`×642, `DEC-25-26`×632, `MAR-25-26`×632, `AUG-25-26`×614, `JUN-25-26`×611, `APR-26-27`×608, `OCT-25-26`×607, `Jan-24-25`×607, `Feb-24-25`×590, `FEB-25-26`×588, `MAY-26-27`×585, `Dec-24-25`×566, `JUL-26-27`×562, `NOV-25-26`×554, `Sep-24-25`×425, `AUG-26-27`×389
- **`PaPriority`** (1 values) — `6`×14,851
- **`IsPaytoBnk`** (2 values) — `N`×14,847, `Y`×4
- **`PBnkCnt`** (2 values) — `NULL`×14,847, `IN`×4
- **`PBnkCode`** (4 values) — `NULL`×14,847, `HDFC`×2, `ICICI`×1, `AXIS`×1
- **`PBnkAccnt`** (5 values) — `NULL`×14,847, `629301521609`×1, `01582320002665`×1, `924020067160142`×1, `50200039205833`×1
- **`WizDunBlck`** (1 values) — `N`×14,851
- **`VersionNum`** (2 values) — `10.00.250.15`×9,755, `10.00.310.21`×5,096
- **`PaymType`** (1 values) — `N`×14,851
- **`WddStatus`** (2 values) — `-`×13,540, `P`×1,311
- **`LocCode`** (2 values) — `NULL`×14,426, `1`×425
- **`ResidenNum`** (1 values) — `1`×14,851
- **`ShowDocNo`** (1 values) — `Y`×14,851
- **`BPLId`** (6 values) — `1`×9,062, `2`×5,550, `5`×210, `3`×12, `6`×10, `4`×7
- **`BPLName`** (6 values) — `DELHI`×9,062, `FACTORY`×5,550, `HARYANA SALES`×210, `PUNJAB`×12, `DELHI ISD`×10, `HIMACHAL PRADESH`×7
- **`VATRegNum`** (5 values) — `07AACCJ4223F1ZY`×9,062, `06AACCJ4223F1Z0`×5,760, `03AACCJ4223F1Z6`×12, `07AACCJ4223F2ZX`×10, `02AACCJ4223F1Z8`×7
- **`BPLCentPmt`** (2 values) — `Y`×7,905, `N`×6,946
- **`PmntWTCert`** (1 values) — `N`×14,851
- **`DPPStatus`** (1 values) — `N`×14,851
- **`EnblDpmTax`** (1 values) — `N`×14,851
- **`DataVers`** (5 values) — `1`×13,204, `2`×1,536, `3`×97, `4`×12, `5`×2
- **`DigPayment`** (1 values) — `N`×14,851
- **`BaseType`** (1 values) — `-1`×14,851
- **`U_Pymnt_Mode`** (4 values) — `NEFT`×9,613, `RTGS`×4,782, `NULL`×437, `FT`×19
- **`U_Pay_Report_Gen`** (1 values) — `N`×14,851
- **`U_Type_of_Advance`** (3 values) — `One Time Settlement`×13,228, `NULL`×1,564, `Adjustable in EMI`×59
- **`U_UNE_MLOC`** (2 values) — `NULL`×14,850, `.`×1
- **`U_URGENCY`** (2 values) — `NULL`×13,824, `H`×1,027
