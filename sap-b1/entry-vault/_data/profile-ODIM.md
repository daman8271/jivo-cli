# `ODIM` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 5 | 0 | `—` | — |
| MART | 5 | 0 | `—` | — |
| BEV | 5 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DimCode` | SMALLINT | 100% | 100% | 100% | · | · | · | 5 | |
| `DimName` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 5 | |
| `DimActive` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `DimDesc` | NVARCHAR(50) | 100% | 100% | 100% | · | · | · | 5 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`DimCode`** (5 values) — `2`×1, `3`×1, `1`×1, `4`×1, `5`×1
- **`DimName`** (5 values) — `Dimension 5`×1, `Dimension 2`×1, `Dimension 4`×1, `Dimension 1`×1, `Dimension 3`×1
- **`DimActive`** (1 values) — `Y`×5
- **`DimDesc`** (5 values) — `Budget`×1, `Variety`×1, `Sub Budget`×1, `State`×1, `Effective Month`×1
