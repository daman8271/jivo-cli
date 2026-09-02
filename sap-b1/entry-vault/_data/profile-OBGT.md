# `OBGT` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 164 | 0 | `—` | — |
| MART | 0 | — | — | **not used in this book** |
| BEV | 175 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | BEV all | OIL 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---|
| `AbsId` | INTEGER | 100% | 100% | · | · | 164 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | · | · | 8 | |
| `BgdCode` | INTEGER | 100% | 100% | · | · | 1 | |
| `DebLTotal` | DECIMAL | 100% | 100% | · | · | 54 | |
| `DebSTotal` | DECIMAL | 100% | 100% | · | · | 54 | |
| `FinancYear` | TIMESTAMP | 100% | 100% | · | · | 3 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`AcctCode`** (8 values) — `5630001`×55, `5670001`×30, `5680016`×18, `5680011`×13, `5630005`×12, `5610001`×12, `5640002`×12, `5640001`×12
- **`BgdCode`** (1 values) — `1`×164
- **`FinancYear`** (3 values) — `2025-04-01 00:00:00.0000000`×88, `2024-04-01 00:00:00.0000000`×72, `2026-04-01 00:00:00.0000000`×4
