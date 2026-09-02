# `OWDD` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 59,787 | 59,787 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 14,925 | 14,925 | `DocDate` | 2025-01-01 → 2026-08-24 |
| BEV | 17,225 | 17,225 | `DocDate` | 2024-10-01 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `WddCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 59,787 | |
| `WtmCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 72 | |
| `OwnerID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 37 | |
| `DocEntry` | INTEGER | 92% | 92% | 89% | 92% | 92% | 89% | 34,655 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 15 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 693 | |
| `CurrStep` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `Status` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Remarks` | NVARCHAR(254) | <1% | <1% | <1% | <1% | <1% | <1% | 222 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 37 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 634 | |
| `CreateTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1,048 | |
| `IsDraft` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `MaxReqr` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `MaxRejReqr` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DraftType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DraftEntry` | INTEGER | 99% | 100% | 100% | 99% | 100% | 100% | 49,092 | |
| `BFType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ProcessID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 51,254 | |
| `ProcesStat` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `StpUpdated` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`OwnerID`** (30 values) — `33`×8,746, `36`×7,851, `22`×6,590, `17`×6,191, `18`×5,404, `15`×4,805, `24`×2,612, `16`×2,608, `30`×2,102, `31`×1,813, `20`×1,577, `32`×1,542, `35`×1,405, `44`×1,207, `26`×1,057, `21`×1,008, `10`×814, `19`×801, `14`×738, `13`×296, `49`×116, `39`×107, `53`×106, `48`×68, `40`×51, `1`×48, `2`×31, `12`×29, `52`×15, `46`×11
- **`ObjType`** (15 values) — `67`×17,683, `18`×15,302, `13`×10,607, `20`×5,265, `22`×2,359, `19`×1,802, `15`×1,655, `14`×1,552, `46`×1,494, `16`×1,244, `1250000001`×705, `21`×104, `17`×7, `59`×7, `60`×1
- **`CurrStep`** (24 values) — `13`×18,367, `6`×11,807, `5`×10,394, `9`×7,009, `8`×2,329, `15`×2,305, `23`×1,681, `16`×1,259, `3`×771, `11`×700, `10`×668, `14`×528, `25`×479, `4`×419, `24`×365, `27`×294, `18`×134, `19`×123, `17`×91, `1`×51, `28`×7, `21`×3, `22`×2, `26`×1
- **`Status`** (3 values) — `Y`×57,032, `W`×1,712, `N`×1,043
- **`UserSign`** (30 values) — `33`×8,746, `36`×7,851, `22`×6,590, `17`×6,191, `18`×5,404, `15`×4,805, `24`×2,612, `16`×2,608, `30`×2,102, `31`×1,813, `20`×1,577, `32`×1,542, `35`×1,405, `44`×1,207, `26`×1,057, `21`×1,008, `10`×814, `19`×801, `14`×738, `13`×296, `49`×116, `39`×107, `53`×106, `48`×68, `40`×51, `1`×48, `2`×31, `12`×29, `52`×15, `46`×11
- **`IsDraft`** (2 values) — `N`×55,090, `Y`×4,697
- **`MaxReqr`** (1 values) — `1`×59,787
- **`MaxRejReqr`** (1 values) — `1`×59,787
- **`DraftType`** (2 values) — `112`×58,293, `140`×1,494
- **`BFType`** (2 values) — `A`×59,724, `U`×63
- **`ProcesStat`** (6 values) — `P`×54,713, `C`×3,489, `N`×784, `A`×377, `Y`×220, `W`×204
- **`StpUpdated`** (2 values) — `N`×58,504, `Y`×1,283
