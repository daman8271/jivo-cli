# `OPDF` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 1,568 | 220 | `DocDate` | 2024-10-07 → 2026-08-17 |
| MART | 20 | 0 | `DocDate` | 2025-01-01 → 2026-03-31 |
| BEV | 200 | 20 | `DocDate` | 2025-01-07 → 2026-08-10 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | · | 100% | 1,568 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | · | 100% | 666 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 3 | |
| `Canceled` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 2 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | · | 100% | 558 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | · | 100% | 557 | |
| `CardCode` | NVARCHAR(15) | 3% | 40% | 3% | — | · | — | 34 | |
| `CardName` | NVARCHAR(200) | 3% | 40% | 3% | — | · | — | 34 | |
| `Address` | NVARCHAR(254) | 3% | 40% | 3% | — | · | — | 34 | |
| `CreditSum` | DECIMAL | 1% | — | — | — | · | — | 13 | |
| `TrsfrAcct` | NVARCHAR(15) | 99% | 90% | 100% | 100% | · | 100% | 21 | |
| `TrsfrSum` | DECIMAL | 99% | 90% | 100% | 100% | · | 100% | 833 | |
| `TrsfrSumFC` | DECIMAL | <1% | — | — | — | · | — | 2 | |
| `TrsfrDate` | TIMESTAMP | 99% | 90% | 100% | 100% | · | 100% | 552 | |
| `TrsfrRef` | NVARCHAR(27) | — | — | <1% | — | · | — | 0 | |
| `PayNoDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 2 | |
| `NoDocSum` | DECIMAL | 99% | 80% | 100% | 100% | · | 100% | 835 | |
| `NoDocSumFC` | DECIMAL | <1% | — | — | — | · | — | 2 | |
| `DocCurr` | NVARCHAR(3) | 100% | 100% | 100% | 100% | · | 100% | 2 | |
| `DiffCurr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `DocRate` | DECIMAL | <1% | — | — | — | · | — | 2 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `DocTotal` | DECIMAL | 100% | 90% | 100% | 100% | · | 100% | 841 | |
| `DocTotalFC` | DECIMAL | <1% | — | — | — | · | — | 2 | |
| `Ref2` | NVARCHAR(50) | 8% | — | 7% | 15% | · | 20% | 29 | |
| `CounterRef` | NVARCHAR(50) | 8% | — | 7% | 15% | · | 20% | 29 | |
| `Comments` | NVARCHAR(254) | 97% | 80% | 98% | 98% | · | 100% | 977 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 95% | 100% | 100% | · | 100% | 71 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | · | 100% | 539 | |
| `ShowAtCard` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 2 | |
| `SpiltTrans` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `CntctCode` | INTEGER | 3% | 35% | 2% | — | · | — | 30 | |
| `CredSumSy` | DECIMAL | 1% | — | — | — | · | — | 13 | |
| `TrsfrSumSy` | DECIMAL | 99% | 90% | 100% | 100% | · | 100% | 833 | |
| `NoDocSumSy` | DECIMAL | 99% | 80% | 100% | 100% | · | 100% | 835 | |
| `DocTotalSy` | DECIMAL | 100% | 90% | 100% | 100% | · | 100% | 841 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | · | 100% | 2 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | · | 100% | 349 | |
| `ApplyVAT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | · | 100% | 557 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | · | 100% | 24 | |
| `confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `ShowJDT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 2 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | · | 100% | 7 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | · | 100% | 23 | |
| `SpltCredLn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `Submitted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `Status` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `Proforma` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `BpAct` | NVARCHAR(15) | 3% | 25% | 3% | — | · | — | 7 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | · | 100% | 23 | |
| `PaPriority` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `PayToCode` | NVARCHAR(50) | 3% | 40% | 3% | — | · | — | 25 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `WizDunBlck` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | · | 100% | 2 | |
| `VatDate` | TIMESTAMP | 99% | 100% | 100% | 96% | · | 100% | 349 | |
| `PaymType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 4 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `ShowDocNo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `BPLId` | INTEGER | 100% | 90% | 100% | 100% | · | 100% | 2 | |
| `BPLName` | NVARCHAR(200) | 100% | 90% | 100% | 100% | · | 100% | 2 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 90% | 100% | 100% | · | 100% | 2 | |
| `BPLCentPmt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 2 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | · | 100% | 1,525 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | · | 100% | 1,531 | |
| `PmntWTCert` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `AtcEntry` | INTEGER | 13% | 15% | 2% | 10% | · | — | 207 | |
| `EnblDpmTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | · | 100% | 5 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | · | 100% | 1 | |
| `U_Pymnt_Mode` | NVARCHAR(10) | 99% | 35% | 48% | 100% | · | 45% | 3 | |
| `U_Pay_Report_Gen` | NVARCHAR(10) | 100% | — | 100% | 100% | · | 100% | 1 | |
| `U_Type_of_Advance` | NVARCHAR(20) | 81% | 20% | 26% | 50% | · | — | 2 | |
| `U_Adv_Settl_Dt` | TIMESTAMP | 3% | n/a | 3% | 3% | n/a | — | 15 | |
| `U_URGENCY` | NVARCHAR(10) | 2% | — | 3% | 16% | · | 10% | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_Adv_Settl_Dt` | OIL, BEV | **MART** |
| `U_Adv_settl_Dt` | MART | **OIL, BEV** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`DocType`** (3 values) — `A`×1,522, `S`×45, `C`×1
- **`Canceled`** (2 values) — `Y`×1,376, `N`×192
- **`Handwrtten`** (1 values) — `N`×1,568
- **`Printed`** (1 values) — `N`×1,568
- **`CreditSum`** (13 values) — `0.000000`×1,547, `529.820000`×5, `1531.640000`×3, `411.820000`×2, `5071.640000`×2, `824.820000`×2, `5592.520000`×1, `118.200000`×1, `2295.280000`×1, `588.820000`×1, `2833.180000`×1, `1037.220000`×1, `3122.280000`×1
- **`TrsfrAcct`** (22 values) — `2201101`×626, `2201102`×306, `1104104`×185, `2201105`×154, `1104106`×79, `2201202`×37, `1104107`×36, `∅`×21, `2201205`×21, `2201402`×20, `2201104`×16, `2201204`×12, `2201103`×12, `2201207`×10, `2201206`×10, `2201208`×6, `1104103`×5, `2201209`×4, `2201301`×4, `1104102`×2, `NULL`×1, `2201106`×1
- **`TrsfrSumFC`** (2 values) — `0.000000`×1,567, `577315.200000`×1
- **`PayNoDoc`** (2 values) — `Y`×1,558, `N`×10
- **`NoDocSumFC`** (2 values) — `0.000000`×1,567, `577315.200000`×1
- **`DocCurr`** (2 values) — `INR`×1,567, `USD`×1
- **`DiffCurr`** (1 values) — `N`×1,568
- **`DocRate`** (2 values) — `0.000000`×1,567, `85.800000`×1
- **`SysRate`** (1 values) — `1.000000`×1,568
- **`DocTotalFC`** (2 values) — `0.000000`×1,567, `577315.200000`×1
- **`Ref2`** (30 values) — `NULL`×1,449, `1`×12, `7`×12, `6`×11, `9`×10, `8`×10, `5`×7, `3`×7, `2`×6, `10`×5, `4`×5, `15`×4, `14`×3, `20`×3, `12`×3, `18`×2, `25`×2, `23`×2, `17`×2, `01`×2, `21`×2, `16`×1, `28`×1, `29`×1, `24`×1, `19`×1, `11`×1, `202`×1, `0`×1, `13`×1
- **`CounterRef`** (30 values) — `NULL`×1,449, `7`×12, `1`×12, `6`×11, `8`×10, `9`×10, `5`×7, `3`×7, `2`×6, `10`×5, `4`×5, `15`×4, `14`×3, `20`×3, `12`×3, `01`×2, `21`×2, `25`×2, `18`×2, `17`×2, `23`×2, `0`×1, `13`×1, `19`×1, `24`×1, `28`×1, `29`×1, `16`×1, `11`×1, `202`×1
- **`ShowAtCard`** (2 values) — `N`×1,085, `Y`×483
- **`SpiltTrans`** (1 values) — `N`×1,568
- **`CreateTran`** (1 values) — `Y`×1,568
- **`CntctCode`** (30 values) — `NULL`×1,526, `4509`×4, `2513`×3, `1895`×3, `4871`×3, `2104`×2, `4557`×2, `2343`×2, `2099`×1, `2269`×1, `2242`×1, `2767`×1, `2728`×1, `2755`×1, `2045`×1, `4794`×1, `2067`×1, `4599`×1, `2476`×1, `2263`×1, `4907`×1, `2719`×1, `2212`×1, `2621`×1, `1968`×1, `1925`×1, `2053`×1, `2652`×1, `2758`×1, `1936`×1
- **`CredSumSy`** (13 values) — `0.000000`×1,547, `529.820000`×5, `1531.640000`×3, `411.820000`×2, `824.820000`×2, `5071.640000`×2, `588.820000`×1, `2833.180000`×1, `2295.280000`×1, `3122.280000`×1, `1037.220000`×1, `5592.520000`×1, `118.200000`×1
- **`ObjType`** (2 values) — `46`×1,567, `24`×1
- **`ApplyVAT`** (1 values) — `N`×1,568
- **`Series`** (24 values) — `2215`×132, `2216`×106, `2224`×99, `2214`×92, `2225`×91, `712`×83, `2217`×81, `713`×74, `2223`×74, `2598`×67, `714`×66, `2596`×64, `2219`×64, `715`×59, `2222`×57, `2220`×56, `2221`×55, `2218`×54, `2597`×54, `711`×51, `2599`×46, `2600`×36, `710`×6, `697`×1
- **`confirmed`** (1 values) — `N`×1,568
- **`ShowJDT`** (2 values) — `N`×1,513, `Y`×55
- **`UserSign`** (7 values) — `14`×812, `10`×713, `13`×22, `39`×10, `1`×9, `20`×1, `40`×1
- **`FinncPriod`** (23 values) — `15`×131, `16`×103, `24`×101, `14`×92, `25`×91, `17`×85, `9`×82, `10`×75, `23`×72, `11`×66, `43`×66, `19`×64, `41`×62, `12`×59, `42`×57, `22`×57, `20`×56, `21`×55, `18`×54, `8`×52, `44`×46, `45`×36, `7`×6
- **`SpltCredLn`** (1 values) — `N`×1,568
- **`Submitted`** (1 values) — `N`×1,568
- **`Status`** (1 values) — `N`×1,568
- **`Proforma`** (1 values) — `N`×1,568
- **`BpAct`** (8 values) — `∅`×1,519, `2110001`×16, `2110004`×13, `NULL`×9, `2110005`×8, `2110003`×1, `1101001`×1, `2110002`×1
- **`PIndicator`** (23 values) — `MAY-25-26`×131, `JUN-25-26`×103, `FEB-25-26`×101, `APR-25-26`×92, `MAR-25-26`×91, `JUL-25-26`×85, `Dec-24-25`×82, `Jan-24-25`×75, `JAN-25-26`×72, `Feb-24-25`×66, `JUN-26-27`×66, `SEP-25-26`×64, `APR-26-27`×62, `Mar-24-25`×59, `MAY-26-27`×57, `DEC-25-26`×57, `OCT-25-26`×56, `NOV-25-26`×55, `AUG-25-26`×54, `Nov-24-25`×52, `JUL-26-27`×46, `AUG-26-27`×36, `Oct-24-25`×6
- **`PaPriority`** (1 values) — `6`×1,568
- **`PayToCode`** (26 values) — `NULL`×1,522, `GHAZIABAD`×5, `SONIPAT`×4, `VAISHNODEVI AGRO RESOURCES RADHANPUR PATAN`×4, `RAJASTHAN`×4, `KIRTI NAGAR`×4, `DEEN DAYAL AGRO INDUSTRIES JAIPUR`×3, `GANAUR`×2, `KUTCH CHEMICAL VADODARA`×2, `NEW DELHI`×2, `WILSON PLASTIC NEW DELHI`×1, `224 PHASE3 OKHLA`×1, `BILL`×1, `VAISHNODEVI OIL SEEDS GUJARAT`×1, `GURUGAON`×1, `AHMEDABAD`×1, `BIHAR`×1, `UTTAR PRADESH`×1, `SHRI JEE TRADING CO DELHI`×1, `BATHINDA`×1, `INFO EDGE NOIDA`×1, `DEEPAK KUMAR DELHI`×1, `DUBAI`×1, `CHADHA SALES SONIPAT`×1, `PANCHKULA`×1, `BILL TO`×1
- **`IsPaytoBnk`** (1 values) — `N`×1,568
- **`WizDunBlck`** (1 values) — `N`×1,568
- **`VersionNum`** (2 values) — `10.00.250.15`×998, `10.00.310.21`×570
- **`PaymType`** (1 values) — `N`×1,568
- **`WddStatus`** (4 values) — `-`×1,385, `C`×150, `Y`×21, `N`×12
- **`ResidenNum`** (1 values) — `1`×1,568
- **`ShowDocNo`** (1 values) — `Y`×1,568
- **`BPLId`** (3 values) — `1`×1,512, `2`×55, `NULL`×1
- **`BPLName`** (3 values) — `DELHI`×1,512, `FACTORY`×55, `NULL`×1
- **`VATRegNum`** (3 values) — `07AACCJ4223F1ZY`×1,512, `06AACCJ4223F1Z0`×55, `NULL`×1
- **`BPLCentPmt`** (2 values) — `N`×1,530, `Y`×38
- **`PmntWTCert`** (1 values) — `N`×1,568
- **`DPPStatus`** (1 values) — `N`×1,568
- **`EnblDpmTax`** (1 values) — `N`×1,568
- **`DataVers`** (5 values) — `1`×1,322, `2`×194, `3`×40, `4`×10, `5`×2
- **`DigPayment`** (1 values) — `N`×1,568
- **`BaseType`** (1 values) — `-1`×1,568
- **`U_Pymnt_Mode`** (4 values) — `NEFT`×1,164, `RTGS`×380, `NULL`×19, `FT`×5
- **`U_Pay_Report_Gen`** (1 values) — `N`×1,568
- **`U_Type_of_Advance`** (3 values) — `One Time Settlement`×1,266, `NULL`×293, `Adjustable in EMI`×9
- **`U_Adv_Settl_Dt`** (16 values) — `NULL`×1,528, `2024-11-20 00:00:00.0000000`×11, `2024-11-30 00:00:00.0000000`×11, `2024-12-20 00:00:00.0000000`×3, `2025-01-20 00:00:00.0000000`×2, `2026-06-30 00:00:00.0000000`×2, `2024-12-25 00:00:00.0000000`×2, `2026-07-31 00:00:00.0000000`×1, `2026-04-30 00:00:00.0000000`×1, `2025-07-30 00:00:00.0000000`×1, `2026-07-30 00:00:00.0000000`×1, `2024-12-31 00:00:00.0000000`×1, `2026-05-31 00:00:00.0000000`×1, `2026-05-30 00:00:00.0000000`×1, `2025-04-30 00:00:00.0000000`×1, `2024-12-30 00:00:00.0000000`×1
- **`U_URGENCY`** (2 values) — `NULL`×1,531, `H`×37
