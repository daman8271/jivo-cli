# `OWOR` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 8,333 | 1,835 | `CreateDate` | 2024-10-03 → 2026-08-24 |
| MART | 27 | 20 | `CreateDate` | 2025-08-19 → 2026-06-30 |
| BEV | 1,472 | 256 | `CreateDate` | 2024-10-07 → 2026-08-22 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 8,333 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 8,333 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `ItemCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 341 | |
| `Status` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `Type` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `PlannedQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 3,017 | |
| `CmpltQty` | DECIMAL | 99% | 96% | 91% | 100% | 100% | 99% | 3,014 | |
| `PostDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 615 | |
| `DueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 615 | |
| `OriginType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `Comments` | NVARCHAR(254) | 4% | — | <1% | 2% | — | <1% | 326 | |
| `CloseDate` | TIMESTAMP | 97% | 59% | 81% | 100% | 55% | 97% | 604 | |
| `RlsDate` | TIMESTAMP | 100% | 100% | 96% | 100% | 100% | 100% | 608 | |
| `CardCode` | NVARCHAR(15) | 31% | — | — | 100% | — | — | 1 | |
| `Warehouse` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 15 | |
| `Uom` | NVARCHAR(100) | 90% | 100% | 74% | 100% | 100% | 100% | 6 | |
| `LineDirty` | INTEGER | 100% | 100% | 96% | 100% | 100% | 100% | 22 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 337 | |
| `TransId` | INTEGER | 67% | — | 7% | 88% | — | 14% | 5,601 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 605 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `UomEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PickRmrk` | NVARCHAR(254) | 5% | — | 1% | 2% | — | — | 361 | |
| `SysCloseDt` | TIMESTAMP | 97% | 59% | 81% | 100% | 55% | 97% | 603 | |
| `SysCloseTm` | SMALLINT | 97% | 59% | 81% | 100% | 55% | 97% | 1,096 | |
| `CloseVerNm` | NVARCHAR(13) | 97% | 59% | 81% | 100% | 55% | 97% | 2 | |
| `StartDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 615 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ProdName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 343 | |
| `Priority` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `RouDatCalc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdAlloc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 7,675 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 7,629 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AtcEntry` | INTEGER | <1% | — | — | <1% | — | — | 7 | |
| `AsChild` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LinkToObj` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ProcItms` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReopOriDoc` | NVARCHAR(1) | <1% | 4% | 2% | <1% | — | <1% | 1 | |
| `U_UNE_PLQT` | DECIMAL | — | — | <1% | — | — | — | 1 | |
| `U_UNE_CHK` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_WASTAGE` | NVARCHAR(10) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (4)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BATCH_NO` | OIL, MART | **BEV** |
| `U_EXP_DATE` | OIL, MART | **BEV** |
| `U_MFG` | OIL, MART | **BEV** |
| `U_WASTAGE` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`Series`** (23 values) — `762`×609, `2695`×550, `2692`×438, `2696`×419, `2693`×402, `2694`×396, `2330`×391, `2325`×388, `2323`×372, `759`×359, `2331`×344, `2332`×341, `764`×339, `2321`×333, `2324`×327, `2329`×322, `2328`×300, `2326`×300, `2322`×295, `763`×292, `761`×285, `760`×266, `2327`×265
- **`Status`** (4 values) — `L`×8,116, `R`×163, `C`×31, `P`×23
- **`Type`** (3 values) — `S`×6,728, `P`×900, `D`×705
- **`OriginType`** (1 values) — `M`×8,333
- **`UserSign`** (12 values) — `33`×6,338, `10`×577, `1`×347, `44`×344, `15`×337, `36`×141, `32`×97, `26`×68, `35`×34, `30`×29, `40`×20, `56`×1
- **`CardCode`** (2 values) — `NULL`×5,721, `VENDA001625`×2,612
- **`Warehouse`** (15 values) — `BH-PF`×6,460, `BH-LO`×880, `BH-GJ`×334, `BH-GR`×268, `BH-BS`×113, `DL-GR`×68, `BH-WST`×65, `BH-EC`×50, `BH-PC`×34, `BH-PM`×16, `BH-JW`×11, `BH-EX`×11, `BH-FP`×10, `BH-FG`×8, `BH-OT`×5
- **`Uom`** (7 values) — `PCS`×6,266, `LTR`×1,236, `NULL`×807, `DRM`×13, `SET`×5, `∅`×3, `KGS`×3
- **`LineDirty`** (23 values) — `4`×5,816, `5`×1,146, `6`×329, `7`×262, `10`×160, `9`×111, `8`×103, `11`×100, `3`×99, `12`×61, `2`×32, `1`×29, `NULL`×22, `14`×17, `13`×17, `18`×8, `17`×8, `16`×6, `15`×3, `23`×1, `20`×1, `22`×1, `19`×1
- **`Printed`** (2 values) — `N`×8,332, `Y`×1
- **`PIndicator`** (23 values) — `Jan-24-25`×609, `JUL-26-27`×550, `APR-26-27`×438, `AUG-26-27`×419, `MAY-26-27`×402, `JUN-26-27`×396, `JAN-25-26`×391, `AUG-25-26`×388, `JUN-25-26`×372, `Oct-24-25`×359, `FEB-25-26`×344, `MAR-25-26`×341, `Mar-24-25`×339, `APR-25-26`×333, `JUL-25-26`×327, `DEC-25-26`×322, `SEP-25-26`×300, `NOV-25-26`×300, `MAY-25-26`×295, `Feb-24-25`×292, `Dec-24-25`×285, `Nov-24-25`×266, `OCT-25-26`×265
- **`UomEntry`** (2 values) — `-1`×7,104, `2`×1,229
- **`CloseVerNm`** (3 values) — `10.00.250.15`×4,755, `10.00.310.21`×3,359, `NULL`×219
- **`ObjType`** (1 values) — `202`×8,333
- **`Priority`** (3 values) — `100`×8,330, `1000`×2, `60`×1
- **`RouDatCalc`** (1 values) — `S`×8,333
- **`UpdAlloc`** (2 values) — `C`×6,540, `M`×1,793
- **`VersionNum`** (2 values) — `10.00.250.15`×4,872, `10.00.310.21`×3,461
- **`AtcEntry`** (8 values) — `NULL`×8,326, `148750`×1, `47073`×1, `44019`×1, `28301`×1, `28308`×1, `26708`×1, `44018`×1
- **`AsChild`** (2 values) — `N`×8,310, `Y`×23
- **`LinkToObj`** (1 values) — `17`×8,333
- **`ProcItms`** (1 values) — `N`×8,333
- **`ReopOriDoc`** (2 values) — `NULL`×8,300, `N`×33
- **`U_UNE_CHK`** (1 values) — `N`×8,333
- **`U_WASTAGE`** (1 values) — `Y`×8,333
