# `OSLP` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 158 | 0 | `—` | — |
| MART | 51 | 0 | `—` | — |
| BEV | 99 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `SlpCode` | INTEGER | 100% | 100% | 100% | · | · | · | 158 | |
| `SlpName` | NVARCHAR(155) | 100% | 100% | 100% | · | · | · | 158 | |
| `Locked` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | · | · | · | 5 | |
| `Active` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`Locked`** (2 values) — `N`×157, `Y`×1
- **`UserSign`** (5 values) — `39`×47, `38`×46, `40`×40, `1`×18, `47`×7
- **`Active`** (1 values) — `Y`×158
- **`DPPStatus`** (1 values) — `N`×158
