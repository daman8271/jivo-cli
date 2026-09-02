# `OATC` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 78,342 | 0 | `—` | — |
| MART | 32,118 | 0 | `—` | — |
| BEV | 19,965 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `AbsEntry` | INTEGER | 100% | 100% | 100% | · | · | · | 78,342 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._
