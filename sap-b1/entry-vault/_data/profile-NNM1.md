# `NNM1` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 2,850 | 2,806 | `CreateDate` | 2024-08-27 → 2026-08-08 |
| MART | 2,439 | 2,395 | `CreateDate` | 2024-08-27 → 2026-08-13 |
| BEV | 2,459 | 2,415 | `CreateDate` | 2024-08-27 → 2026-08-08 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `ObjectCode` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 70 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,850 | |
| `SeriesName` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 1,318 | |
| `InitialNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,663 | |
| `NextNumber` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,726 | |
| `LastNum` | INTEGER | 98% | 97% | 97% | 99% | 99% | 99% | 2,725 | |
| `BeginStr` | NVARCHAR(20) | <1% | 2% | <1% | <1% | 2% | <1% | 23 | |
| `Remark` | NVARCHAR(50) | <1% | <1% | <1% | <1% | <1% | <1% | 1 | |
| `GroupCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `Locked` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `YearTransf` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Indicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 33 | |
| `NumSize` | INTEGER | <1% | <1% | <1% | <1% | <1% | <1% | 3 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 13 | |
| `IsDigSerie` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SeriesType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `IsManual` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BPLId` | INTEGER | 75% | 73% | 72% | 77% | 74% | 74% | 7 | |
| `IsForCncl` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `IsElAuth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CoAccount` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GenPassprt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UserSign` | SMALLINT | 98% | 98% | 98% | 100% | 100% | 100% | 5 | |
| `CreateDate` | TIMESTAMP | 98% | 98% | 98% | 100% | 100% | 100% | 72 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`BeginStr`** (24 values) — `NULL`×2,825, `ISD`×3, `ZIA0426`×1, `ZIA0924`×1, `JWPL0924`×1, `EX`×1, `CF`×1, `FG`×1, `FA`×1, `FB`×1, `ISDR`×1, `ISD1`×1, `RM`×1, `SC`×1, `SL`×1, `CG`×1, `CUSTA`×1, `ORGC`×1, `VENDA`×1, `PM`×1, `ORGV`×1, `SF`×1, `ISDI`×1, `ISDRI`×1
- **`Remark`** (2 values) — `NULL`×2,849, `6`×1
- **`GroupCode`** (7 values) — `1`×692, `6`×621, `7`×556, `2`×488, `3`×488, `NULL`×4, `30`×1
- **`Locked`** (2 values) — `N`×2,772, `Y`×78
- **`YearTransf`** (1 values) — `N`×2,850
- **`Indicator`** (30 values) — `Aug-24-25`×98, `Feb-24-25`×96, `Mar-24-25`×94, `Jan-24-25`×93, `MAR-25-26`×93, `Sep-24-25`×91, `FEB-25-26`×90, `SEP-25-26`×90, `AUG-25-26`×90, `JUL-25-26`×89, `DEC-25-26`×89, `NOV-25-26`×89, `Dec-24-25`×89, `Nov-24-25`×88, `Oct-24-25`×88, `JUN-25-26`×88, `MAY-25-26`×88, `JAN-25-26`×88, `OCT-25-26`×88, `APR-25-26`×87, `MAR-26-27`×83, `APR-26-27`×83, `JUL-26-27`×83, `AUG-26-27`×83, `SEP-26-27`×83, `OCT-26-27`×83, `NOV-26-27`×83, `DEC-26-27`×83, `JAN-26-27`×83, `FEB-26-27`×83
- **`NumSize`** (4 values) — `NULL`×2,834, `7`×11, `6`×4, `4`×1
- **`DocSubType`** (13 values) — `--`×1,247, `GA`×1,132, `GD`×455, `C`×4, `S`×4, `OI`×1, `OS`×1, `ON`×1, `OG`×1, `OV`×1, `OD`×1, `IC`×1, `RV`×1
- **`IsDigSerie`** (2 values) — `N`×2,502, `Y`×348
- **`SeriesType`** (5 values) — `D`×2,822, `I`×12, `W`×8, `B`×6, `R`×2
- **`IsManual`** (2 values) — `N`×2,846, `Y`×4
- **`BPLId`** (8 values) — `NULL`×701, `2`×508, `1`×489, `3`×488, `4`×488, `5`×114, `6`×48, `7`×14
- **`IsForCncl`** (2 values) — `N`×2,129, `Y`×721
- **`IsElAuth`** (1 values) — `N`×2,850
- **`CoAccount`** (1 values) — `N`×2,850
- **`GenPassprt`** (1 values) — `N`×2,850
- **`UserSign`** (6 values) — `1`×2,712, `40`×61, `NULL`×44, `38`×28, `47`×3, `10`×2
