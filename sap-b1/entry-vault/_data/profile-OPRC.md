# `OPRC` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 199 | 0 | `—` | — |
| MART | 190 | 0 | `—` | — |
| BEV | 177 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `PrcCode` | NVARCHAR(8) | 100% | 100% | 100% | · | · | · | 199 | |
| `PrcName` | NVARCHAR(30) | 99% | 99% | 100% | · | · | · | 197 | |
| `Locked` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | · | · | · | 5 | |
| `DimCode` | SMALLINT | 100% | 100% | 100% | · | · | · | 5 | |
| `ValidFrom` | TIMESTAMP | 100% | 100% | 100% | · | · | · | 32 | |
| `ValidTo` | TIMESTAMP | <1% | 2% | — | · | · | · | 1 | |
| `Active` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `CCOwner` | INTEGER | 14% | <1% | 11% | · | · | · | 14 | |
| `U_Co_Owner` | INTEGER | 10% | — | 10% | · | · | · | 7 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`Locked`** (2 values) — `N`×194, `Y`×5
- **`UserSign`** (5 values) — `1`×164, `38`×12, `39`×12, `40`×8, `47`×3
- **`DimCode`** (5 values) — `1`×88, `2`×37, `4`×29, `5`×28, `3`×17
- **`ValidFrom`** (30 values) — `2024-10-01 00:00:00.0000000`×83, `2024-09-24 00:00:00.0000000`×19, `2024-09-01 00:00:00.0000000`×16, `2024-10-18 00:00:00.0000000`×13, `2026-04-04 00:00:00.0000000`×11, `2025-01-01 00:00:00.0000000`×8, `2025-12-17 00:00:00.0000000`×5, `2025-04-01 00:00:00.0000000`×4, `2026-01-01 00:00:00.0000000`×4, `1900-01-01 00:00:00.0000000`×4, `2025-08-01 00:00:00.0000000`×3, `2024-01-01 00:00:00.0000000`×3, `2025-05-01 00:00:00.0000000`×3, `2026-02-01 00:00:00.0000000`×2, `2025-02-01 00:00:00.0000000`×2, `2025-12-01 00:00:00.0000000`×2, `2024-12-01 00:00:00.0000000`×2, `2025-07-01 00:00:00.0000000`×1, `2024-08-01 00:00:00.0000000`×1, `2024-11-01 00:00:00.0000000`×1, `2025-06-01 00:00:00.0000000`×1, `2025-09-01 00:00:00.0000000`×1, `2024-07-01 00:00:00.0000000`×1, `2026-04-01 00:00:00.0000000`×1, `2024-09-30 00:00:00.0000000`×1, `2024-11-16 00:00:00.0000000`×1, `2025-11-01 00:00:00.0000000`×1, `2025-03-01 00:00:00.0000000`×1, `2024-06-01 00:00:00.0000000`×1, `2024-05-01 00:00:00.0000000`×1
- **`ValidTo`** (2 values) — `NULL`×198, `2024-09-30 00:00:00.0000000`×1
- **`Active`** (2 values) — `Y`×197, `N`×2
- **`CCOwner`** (15 values) — `NULL`×171, `18`×8, `2`×5, `9`×3, `12`×2, `19`×1, `11`×1, `14`×1, `7`×1, `15`×1, `20`×1, `13`×1, `6`×1, `4`×1, `22`×1
- **`U_Co_Owner`** (8 values) — `NULL`×179, `7`×9, `17`×6, `11`×1, `3`×1, `18`×1, `19`×1, `5`×1
