# `OBTF` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 3,245 | 348 | `RefDate` | 2024-08-01 → 2026-08-21 |
| MART | 791 | 85 | `RefDate` | 2024-12-31 → 2026-08-20 |
| BEV | 897 | 97 | `RefDate` | 2024-10-01 → 2026-08-22 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `BatchNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3,223 | |
| `TransId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `BtfStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `TransType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RefDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 484 | |
| `Memo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 2,806 | |
| `Ref2` | NVARCHAR(200) | <1% | — | — | — | — | — | 5 | |
| `LocTotal` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2,274 | |
| `SysTotal` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2,274 | |
| `TransCurr` | NVARCHAR(3) | — | <1% | — | — | — | — | 0 | |
| `DueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 534 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 516 | |
| `PCAddition` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 503 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 19 | |
| `RefndRprt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AdjTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StornoDate` | TIMESTAMP | <1% | — | <1% | — | — | 1% | 1 | |
| `AutoStorno` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Corisptivi` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StampTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 41 | |
| `Number` | INTEGER | 98% | 69% | 99% | 98% | 66% | 95% | 2,817 | |
| `AutoVAT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlockDunn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReportEU` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Report347` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GenRegNo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Location` | INTEGER | 71% | 74% | 74% | 52% | 40% | 31% | 5 | |
| `AutoWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Ref3` | NVARCHAR(200) | <1% | — | — | — | — | — | 2 | |
| `DeferedTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ECDPosTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PrlLinked` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExclTaxRep` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsCoEntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EBookable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SAFTType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SAFTTypeEx` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_ATTACHEMENT` | NVARCHAR(200) | <1% | 2% | 45% | 2% | 14% | 20% | 8 | |
| `U_ATTACH_LINK` | NCLOB | 46% | 57% | n/a | 32% | 45% | n/a | 0 | |
| `U_REMARKS` | NVARCHAR(250) | <1% | 1% | — | — | — | — | 3 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (3)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_ATTACH_LINK` | OIL, MART | **BEV** |
| `U_TDS_LINK` | OIL, MART | **BEV** |
| `U_TDS_ROLE` | OIL, MART | **BEV** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TransId`** (5 values) — `1`×3,223, `2`×15, `3`×4, `4`×2, `5`×1
- **`BtfStatus`** (2 values) — `C`×3,102, `O`×143
- **`TransType`** (1 values) — `-1`×3,245
- **`Ref2`** (6 values) — `∅`×3,239, `NULL`×2, `CCAG/DN/122`×1, `CCAG/DN/164`×1, `041/25-26`×1, `TSPL/2526/RN61`×1
- **`PCAddition`** (1 values) — `N`×3,245
- **`FinncPriod`** (23 values) — `41`×315, `18`×262, `19`×226, `17`×209, `42`×201, `16`×181, `22`×177, `12`×155, `25`×148, `14`×133, `21`×115, `23`×113, `15`×113, `20`×108, `11`×105, `44`×101, `8`×99, `10`×98, `24`×91, `43`×90, `9`×89, `45`×86, `7`×30
- **`UserSign`** (19 values) — `13`×703, `39`×473, `11`×472, `10`×309, `17`×222, `15`×198, `48`×192, `16`×192, `53`×148, `14`×129, `20`×103, `18`×75, `12`×16, `1`×4, `47`×3, `24`×2, `46`×2, `22`×1, `27`×1
- **`RefndRprt`** (1 values) — `N`×3,245
- **`ObjType`** (1 values) — `30`×3,245
- **`AdjTran`** (1 values) — `N`×3,245
- **`RevSource`** (1 values) — `N`×3,245
- **`StornoDate`** (2 values) — `NULL`×3,244, `2025-10-01 00:00:00.0000000`×1
- **`AutoStorno`** (2 values) — `N`×3,244, `Y`×1
- **`Corisptivi`** (1 values) — `N`×3,245
- **`StampTax`** (1 values) — `N`×3,245
- **`AutoVAT`** (1 values) — `N`×3,245
- **`BlockDunn`** (1 values) — `N`×3,245
- **`ReportEU`** (1 values) — `N`×3,245
- **`Report347`** (1 values) — `N`×3,245
- **`Printed`** (1 values) — `N`×3,245
- **`GenRegNo`** (1 values) — `N`×3,245
- **`Location`** (6 values) — `2`×1,142, `1`×1,037, `NULL`×945, `3`×86, `5`×24, `4`×11
- **`AutoWT`** (1 values) — `N`×3,245
- **`VersionNum`** (2 values) — `10.00.250.15`×1,993, `10.00.310.21`×1,252
- **`ResidenNum`** (1 values) — `1`×3,245
- **`Ref3`** (3 values) — `∅`×3,101, `NULL`×143, `11`×1
- **`DeferedTax`** (1 values) — `N`×3,245
- **`ECDPosTyp`** (1 values) — `N`×3,245
- **`PrlLinked`** (1 values) — `N`×3,245
- **`ExclTaxRep`** (1 values) — `N`×3,245
- **`IsCoEntry`** (1 values) — `N`×3,245
- **`EBookable`** (1 values) — `N`×3,245
- **`DataVers`** (1 values) — `1`×3,245
- **`SAFTType`** (1 values) — `-`×3,245
- **`SAFTTypeEx`** (1 values) — `-`×3,245
