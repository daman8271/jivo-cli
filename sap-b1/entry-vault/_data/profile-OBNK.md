# `OBNK` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 201 | 35 | `CreateDate` | 2024-12-09 → 2026-07-28 |
| MART | 7 | 1 | `CreateDate` | 2025-08-02 → 2026-06-15 |
| BEV | 51 | 4 | `CreateDate` | 2025-01-14 → 2026-06-06 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 19 | |
| `Sequence` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 30 | |
| `AcctName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 19 | |
| `DueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 67 | |
| `DebAmount` | DECIMAL | 42% | 14% | 53% | 17% | — | 25% | 85 | |
| `DebAmntCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CredAmnt` | DECIMAL | 57% | 86% | 47% | 83% | 100% | 75% | 115 | |
| `CredAmntCu` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BankMatch` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 30 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `PaymCreat` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VisOrder` | INTEGER | 60% | 71% | 78% | — | — | — | 24 | |
| `DocNumType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `autoCreate` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Cleared` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjCrtType` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PstMethod` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineOrigin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Source` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 62 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`AcctCode`** (19 values) — `1104106`×30, `1104107`×25, `2201101`×25, `2201102`×25, `1104104`×23, `2201202`×13, `2201104`×9, `2201402`×9, `2201205`×8, `2201105`×7, `2201103`×4, `2201401`×3, `2201207`×3, `2201404`×3, `2201204`×3, `2201405`×3, `2201403`×3, `2201206`×3, `1104103`×2
- **`Sequence`** (30 values) — `2`×19, `1`×19, `3`×18, `4`×11, `7`×10, `6`×10, `5`×10, `8`×9, `9`×8, `13`×6, `10`×6, `11`×6, `12`×6, `15`×5, `16`×5, `14`×5, `18`×5, `17`×5, `23`×5, `20`×5, `19`×5, `21`×5, `22`×5, `24`×4, `25`×4, `27`×1, `30`×1, `28`×1, `26`×1, `29`×1
- **`DebAmntCur`** (1 values) — `INR`×201
- **`CredAmntCu`** (1 values) — `INR`×201
- **`BankMatch`** (30 values) — `1`×18, `2`×18, `3`×17, `5`×10, `4`×10, `6`×10, `7`×10, `8`×9, `9`×8, `12`×7, `11`×7, `10`×7, `13`×7, `20`×5, `23`×5, `17`×5, `18`×5, `14`×5, `22`×5, `21`×5, `19`×5, `15`×5, `16`×5, `24`×4, `25`×4, `27`×1, `30`×1, `28`×1, `29`×1, `26`×1
- **`UserSign`** (3 values) — `14`×119, `10`×81, `39`×1
- **`PaymCreat`** (1 values) — `N`×201
- **`VisOrder`** (25 values) — `NULL`×80, `1`×12, `2`×12, `3`×9, `4`×7, `6`×6, `5`×6, `7`×6, `9`×5, `11`×5, `8`×5, `10`×5, `13`×5, `16`×5, `15`×5, `12`×5, `17`×5, `14`×5, `18`×4, `19`×4, `23`×1, `24`×1, `21`×1, `22`×1, `20`×1
- **`DocNumType`** (1 values) — `D`×201
- **`autoCreate`** (1 values) — `A`×201
- **`Cleared`** (1 values) — `N`×201
- **`ObjCrtType`** (1 values) — `24`×201
- **`PstMethod`** (1 values) — `C`×201
- **`LineOrigin`** (1 values) — `R`×201
- **`Source`** (1 values) — `I`×201
- **`DPPStatus`** (1 values) — `N`×201
