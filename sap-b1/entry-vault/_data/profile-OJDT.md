# `OJDT` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 136,729 | 18,712 | `RefDate` | 2024-08-01 → 2026-08-24 |
| MART | 64,640 | 10,554 | `RefDate` | 2024-10-03 → 2026-08-24 |
| BEV | 23,621 | 5,059 | `RefDate` | 2024-09-30 → 2026-12-31 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `BatchNum` | INTEGER | 2% | 1% | 4% | 2% | <1% | 2% | 3,080 | |
| `TransId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 136,729 | |
| `BtfStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TransType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 19 | |
| `BaseRef` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 133,995 | |
| `RefDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 694 | |
| `Memo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 22,738 | |
| `Ref1` | NVARCHAR(200) | 96% | 97% | 93% | 97% | 98% | 97% | 128,516 | |
| `Ref2` | NVARCHAR(200) | 32% | 30% | 20% | 23% | 31% | 15% | 36,351 | |
| `CreatedBy` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 57,507 | |
| `LocTotal` | DECIMAL | 80% | 97% | 88% | 68% | 98% | 89% | 57,396 | |
| `FcTotal` | DECIMAL | <1% | <1% | <1% | <1% | — | — | 191 | |
| `SysTotal` | DECIMAL | 80% | 97% | 88% | 68% | 98% | 89% | 57,396 | |
| `TransCurr` | NVARCHAR(3) | <1% | <1% | <1% | <1% | — | — | 4 | |
| `DueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 1,481 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 1,471 | |
| `PCAddition` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 25 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 649 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 40 | |
| `RefndRprt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AdjTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StornoToTr` | INTEGER | 1% | <1% | 1% | <1% | <1% | <1% | 1,478 | |
| `AutoStorno` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Corisptivi` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StampTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 50 | |
| `Number` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 136,729 | |
| `AutoVAT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSeries` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 899 | |
| `CreateTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1,210 | |
| `BlockDunn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReportEU` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Report347` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `GenRegNo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Location` | INTEGER | 3% | 1% | 4% | 2% | 1% | 2% | 5 | |
| `AutoWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Ref3` | NVARCHAR(200) | 10% | — | — | 9% | — | — | 11,232 | |
| `DeferedTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AgrNo` | INTEGER | <1% | — | — | — | — | — | 2 | |
| `ECDPosTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PrlLinked` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExclTaxRep` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsCoEntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | <1% | <1% | <1% | <1% | <1% | <1% | 407 | |
| `EBookable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `SAFTType` | NVARCHAR(1) | 73% | 75% | 66% | 75% | 73% | 67% | 1 | |
| `SAFTTypeEx` | NVARCHAR(10) | 73% | 75% | 66% | 75% | 73% | 67% | 1 | |
| `U_ATTACHEMENT` | NVARCHAR(200) | <1% | <1% | 2% | <1% | <1% | <1% | 8 | |
| `U_ATTACH_LINK` | NCLOB | 1% | <1% | n/a | <1% | <1% | n/a | 0 | |
| `U_REMARKS` | NVARCHAR(250) | 57% | 84% | 19% | 52% | 84% | 31% | 54,292 | |
| `U_TDS_LINK` | NVARCHAR(20) | — | <1% | n/a | — | <1% | n/a | 0 | |
| `U_TDS_ROLE` | NVARCHAR(10) | — | <1% | n/a | — | <1% | n/a | 0 | |

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

- **`BtfStatus`** (1 values) — `O`×136,729
- **`TransType`** (19 values) — `13`×31,078, `18`×16,334, `46`×15,790, `24`×14,645, `67`×12,089, `59`×8,431, `60`×8,364, `14`×6,434, `202`×5,601, `30`×5,235, `20`×5,176, `15`×2,804, `16`×1,925, `19`×1,595, `69`×534, `-3`×436, `21`×120, `162`×114, `321`×24
- **`TransCurr`** (5 values) — `∅`×108,709, `NULL`×27,724, `USD`×220, `EUR`×74, `AUD`×2
- **`PCAddition`** (1 values) — `N`×136,729
- **`FinncPriod`** (25 values) — `6`×16,764, `9`×6,945, `10`×6,910, `8`×6,333, `7`×6,256, `12`×5,858, `23`×5,527, `17`×5,477, `18`×5,355, `25`×5,254, `44`×5,119, `20`×5,041, `19`×5,006, `15`×4,992, `16`×4,965, `22`×4,943, `42`×4,861, `24`×4,842, `43`×4,791, `14`×4,780, `41`×4,664, `11`×4,613, `21`×4,363, `45`×3,068, `5`×2
- **`RefndRprt`** (1 values) — `N`×136,729
- **`ObjType`** (1 values) — `30`×136,729
- **`AdjTran`** (1 values) — `N`×136,729
- **`RevSource`** (1 values) — `N`×136,729
- **`AutoStorno`** (1 values) — `N`×136,729
- **`Corisptivi`** (1 values) — `N`×136,729
- **`StampTax`** (1 values) — `N`×136,729
- **`AutoVAT`** (1 values) — `N`×136,729
- **`BlockDunn`** (1 values) — `N`×136,729
- **`ReportEU`** (1 values) — `N`×136,729
- **`Report347`** (1 values) — `N`×136,729
- **`Printed`** (2 values) — `N`×136,723, `Y`×6
- **`GenRegNo`** (1 values) — `N`×136,729
- **`Location`** (6 values) — `NULL`×133,096, `1`×1,987, `2`×1,514, `3`×68, `5`×44, `4`×20
- **`AutoWT`** (1 values) — `N`×136,729
- **`VersionNum`** (2 values) — `10.00.250.15`×94,573, `10.00.310.21`×42,156
- **`ResidenNum`** (1 values) — `1`×136,729
- **`DeferedTax`** (1 values) — `N`×136,729
- **`AgrNo`** (3 values) — `NULL`×136,726, `0`×2, `10`×1
- **`ECDPosTyp`** (2 values) — `N`×136,511, `E`×218
- **`PrlLinked`** (1 values) — `N`×136,729
- **`ExclTaxRep`** (1 values) — `N`×136,729
- **`IsCoEntry`** (1 values) — `N`×136,729
- **`EBookable`** (1 values) — `N`×136,729
- **`DataVers`** (12 values) — `1`×107,356, `2`×29,322, `3`×28, `4`×11, `6`×3, `7`×3, `8`×1, `17`×1, `9`×1, `5`×1, `18`×1, `12`×1
- **`SAFTType`** (2 values) — `-`×99,847, `NULL`×36,882
- **`SAFTTypeEx`** (2 values) — `-`×99,847, `NULL`×36,882
