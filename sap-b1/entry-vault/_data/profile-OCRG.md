# `OCRG` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 47 | 0 | `—` | — |
| MART | 45 | 0 | `—` | — |
| BEV | 45 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `GroupCode` | SMALLINT | 100% | 100% | 100% | · | · | · | 47 | |
| `GroupName` | NVARCHAR(100) | 100% | 100% | 100% | · | · | · | 47 | |
| `GroupType` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `Locked` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | · | · | · | 4 | |
| `DiscRel` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `EffecPrice` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`GroupType`** (2 values) — `C`×32, `S`×15
- **`Locked`** (1 values) — `N`×47
- **`UserSign`** (4 values) — `7`×39, `1`×5, `38`×2, `40`×1
- **`DiscRel`** (1 values) — `L`×47
- **`EffecPrice`** (1 values) — `D`×47
