# `OMRV` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 114 | 30 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 0 | — | — | **not used in this book** |
| BEV | 46 | 0 | `DocDate` | 2024-09-30 → 2026-03-18 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | BEV all | OIL 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | · | 114 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | · | 114 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | · | 64 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | · | 103 | |
| `Comments` | NVARCHAR(254) | <1% | 24% | — | · | 1 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | · | 7 | |
| `TransId` | INTEGER | 100% | 100% | 100% | · | 114 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | · | 99 | |
| `RevalType` | NVARCHAR(1) | 100% | 100% | 100% | · | 2 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | · | 67 | |
| `Series` | INTEGER | 100% | 100% | 100% | · | 17 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | · | 64 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | · | 7 | |
| `StationID` | INTEGER | 100% | 100% | 100% | · | 13 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | · | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | · | 2 | |
| `InflaReval` | NVARCHAR(1) | 100% | 100% | 100% | · | 1 | |
| `CreatedBy` | NVARCHAR(1) | 100% | 100% | 100% | · | 1 | |
| `U_ATTACH` | NCLOB | <1% | 59% | — | · | 0 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`Comments`** (2 values) — `NULL`×113, `FY 2024-25 ADDITION`×1
- **`RevalType`** (2 values) — `P`×88, `M`×26
- **`Series`** (17 values) — `2680`×22, `754`×20, `2681`×13, `2684`×11, `2307`×10, `757`×7, `756`×6, `751`×6, `2683`×4, `755`×3, `752`×3, `2308`×2, `2301`×2, `2682`×2, `2297`×1, `2304`×1, `2298`×1
- **`UserSign`** (7 values) — `1`×78, `48`×8, `38`×8, `56`×7, `40`×7, `10`×5, `53`×1
- **`StationID`** (13 values) — `7`×31, `174`×23, `316`×21, `313`×10, `15`×9, `301`×8, `1`×3, `257`×2, `275`×2, `278`×2, `77`×1, `29`×1, `318`×1
- **`ObjType`** (1 values) — `162`×114
- **`VersionNum`** (2 values) — `10.00.310.21`×66, `10.00.250.15`×48
- **`InflaReval`** (1 values) — `N`×114
- **`CreatedBy`** (1 values) — `M`×114
