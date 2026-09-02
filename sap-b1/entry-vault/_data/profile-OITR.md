# `OITR` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 30,085 | 30,085 | `CreateDate` | 2024-10-03 → 2026-08-24 |
| MART | 13,403 | 13,403 | `CreateDate` | 2024-10-04 → 2026-08-24 |
| BEV | 6,353 | 6,353 | `CreateDate` | 2024-10-04 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `ReconNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 30,085 | |
| `IsCard` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ReconType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 8 | |
| `ReconDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 664 | |
| `Total` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 23,172 | |
| `ReconCurr` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Canceled` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `CancelAbs` | INTEGER | 3% | 3% | 3% | 3% | 3% | 3% | 935 | |
| `IsSystem` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InitObjTyp` | NVARCHAR(20) | 85% | 88% | 76% | 85% | 88% | 76% | 11 | |
| `InitObjAbs` | INTEGER | 84% | 88% | 76% | 84% | 88% | 76% | 19,222 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 621 | |
| `CreateTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1,097 | |
| `UserSign` | SMALLINT | 65% | 66% | 57% | 65% | 66% | 57% | 33 | |
| `IsMultiBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ReconJEId` | INTEGER | <1% | — | — | <1% | — | — | 25 | |
| `BPLId` | INTEGER | <1% | 1% | <1% | <1% | 1% | <1% | 4 | |
| `IsElectr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 20,406 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 20,417 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`IsCard`** (2 values) — `C`×16,704, `A`×13,381
- **`ReconType`** (8 values) — `3`×8,759, `14`×8,076, `13`×4,970, `0`×4,217, `4`×2,388, `5`×990, `7`×467, `11`×218
- **`ReconCurr`** (1 values) — `INR`×30,085
- **`Canceled`** (3 values) — `N`×29,151, `C`×467, `Y`×467
- **`IsSystem`** (2 values) — `Y`×25,775, `N`×4,310
- **`InitObjTyp`** (12 values) — `202`×8,076, `46`×5,706, `18`×4,750, `NULL`×4,638, `24`×3,053, `30`×1,208, `14`×1,042, `19`×1,005, `13`×316, `20`×229, `-1`×46, `21`×16
- **`UserSign`** (30 values) — `0`×10,392, `14`×3,994, `33`×3,980, `20`×2,852, `16`×1,384, `37`×1,135, `15`×1,103, `22`×780, `12`×575, `38`×572, `17`×571, `18`×554, `1`×512, `40`×482, `10`×417, `11`×206, `13`×143, `39`×95, `47`×95, `26`×62, `24`×35, `23`×23, `30`×23, `21`×22, `25`×16, `46`×15, `27`×15, `48`×14, `35`×6, `44`×5
- **`IsMultiBP`** (2 values) — `N`×29,966, `Y`×119
- **`VersionNum`** (2 values) — `10.00.250.15`×19,693, `10.00.310.21`×10,392
- **`ReconJEId`** (26 values) — `0`×29,594, `NULL`×467, `166648`×1, `185006`×1, `222089`×1, `83632`×1, `165673`×1, `103127`×1, `165968`×1, `96162`×1, `165676`×1, `103128`×1, `103129`×1, `191183`×1, `185009`×1, `220510`×1, `220278`×1, `166647`×1, `202064`×1, `83629`×1, `96167`×1, `191185`×1, `185072`×1, `150217`×1, `85832`×1, `185073`×1
- **`BPLId`** (5 values) — `NULL`×29,781, `2`×129, `0`×123, `1`×44, `3`×8
- **`IsElectr`** (1 values) — `N`×30,085
- **`ObjType`** (1 values) — `321`×30,085
