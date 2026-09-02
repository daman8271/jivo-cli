# `CUFD` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 5,614 | 0 | `—` | — |
| MART | 5,236 | 0 | `—` | — |
| BEV | 5,106 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `TableID` | NVARCHAR(21) | 100% | 100% | 100% | · | · | · | 278 | |
| `FieldID` | SMALLINT | 96% | 96% | 96% | · | · | · | 67 | |
| `AliasID` | NVARCHAR(50) | 100% | 100% | 100% | · | · | · | 566 | |
| `Descr` | NVARCHAR(80) | 100% | 100% | 100% | · | · | · | 517 | |
| `TypeID` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 5 | |
| `EditType` | NVARCHAR(1) | 14% | 13% | 15% | · | · | · | 9 | |
| `SizeID` | SMALLINT | 100% | 100% | 100% | · | · | · | 22 | |
| `EditSize` | SMALLINT | 99% | 99% | 99% | · | · | · | 22 | |
| `Dflt` | NVARCHAR(254) | 4% | 3% | 5% | · | · | · | 3 | |
| `NotNull` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `IndexID` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `RTable` | NVARCHAR(21) | 2% | 3% | 3% | · | · | · | 3 | |
| `Sys` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `RelUDO` | NVARCHAR(20) | <1% | <1% | <1% | · | · | · | 4 | |
| `ValidRule` | NVARCHAR(254) | <1% | — | — | · | · | · | 2 | |
| `RelSO` | NVARCHAR(20) | 4% | 4% | 4% | · | · | · | 8 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TypeID`** (5 values) — `A`×4,141, `B`×740, `D`×388, `N`×230, `M`×115
- **`EditType`** (10 values) — `∅`×4,840, `P`×295, `Q`×219, `S`×130, `%`×96, `NULL`×16, `?`×8, `B`×5, `I`×3, `T`×2
- **`SizeID`** (22 values) — `100`×1,349, `16`×742, `50`×661, `8`×571, `254`×445, `20`×411, `10`×330, `1`×238, `15`×232, `11`×228, `5`×104, `12`×102, `200`×56, `30`×48, `250`×37, `80`×20, `3`×15, `6`×10, `2`×6, `25`×4, `9`×4, `235`×1
- **`EditSize`** (23 values) — `100`×1,349, `16`×742, `50`×661, `8`×456, `254`×450, `10`×437, `20`×411, `1`×238, `15`×232, `11`×145, `5`×104, `12`×102, `NULL`×74, `200`×56, `30`×48, `250`×37, `80`×20, `9`×16, `3`×15, `6`×8, `2`×8, `25`×4, `235`×1
- **`Dflt`** (4 values) — `NULL`×5,388, `N`×152, `Y`×72, `SALE`×2
- **`NotNull`** (2 values) — `N`×5,606, `Y`×8
- **`IndexID`** (1 values) — `N`×5,614
- **`RTable`** (4 values) — `NULL`×5,480, `UTL_CARES`×66, `UTL_EXRES`×34, `UTL_VURES`×34
- **`Sys`** (2 values) — `N`×5,596, `Y`×18
- **`RelUDO`** (5 values) — `NULL`×5,602, `Items SKU`×4, `ITEM VARIETY`×4, `Chain`×2, `Cust Main Group`×2
- **`ValidRule`** (3 values) — `NULL`×4,065, `∅`×1,547, `bt=[1,10]`×2
- **`RelSO`** (9 values) — `NULL`×5,376, `64`×64, `2`×64, `202`×32, `20`×32, `30`×32, `12`×6, `1`×6, `171`×2
