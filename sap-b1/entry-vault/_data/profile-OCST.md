# `OCST` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 98 | 0 | `—` | — |
| MART | 92 | 0 | `—` | — |
| BEV | 93 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `Code` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 92 | |
| `Country` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 5 | |
| `Name` | NVARCHAR(100) | 100% | 100% | 100% | · | · | · | 98 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | · | · | · | 4 | |
| `eCode` | SMALLINT | 37% | 39% | 39% | · | · | · | 36 | |
| `GSTCode` | NVARCHAR(2) | 37% | 39% | 39% | · | · | · | 36 | |
| `GSTIsUT` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`Country`** (5 values) — `US`×56, `IN`×36, `AU`×3, `AE`×2, `CA`×1
- **`UserSign`** (4 values) — `1`×92, `7`×2, `38`×2, `39`×2
- **`eCode`** (30 values) — `NULL`×62, `19`×1, `15`×1, `16`×1, `34`×1, `26`×1, `7`×1, `11`×1, `33`×1, `14`×1, `2`×1, `12`×1, `27`×1, `23`×1, `18`×1, `30`×1, `1`×1, `3`×1, `17`×1, `9`×1, `20`×1, `8`×1, `31`×1, `35`×1, `22`×1, `5`×1, `4`×1, `37`×1, `36`×1, `10`×1
- **`GSTCode`** (30 values) — `NULL`×62, `11`×1, `02`×1, `08`×1, `14`×1, `12`×1, `27`×1, `23`×1, `18`×1, `30`×1, `09`×1, `07`×1, `33`×1, `17`×1, `05`×1, `20`×1, `06`×1, `35`×1, `22`×1, `04`×1, `26`×1, `37`×1, `36`×1, `10`×1, `29`×1, `15`×1, `31`×1, `32`×1, `24`×1, `13`×1
- **`GSTIsUT`** (1 values) — `N`×98
