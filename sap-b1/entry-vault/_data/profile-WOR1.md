# `WOR1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 54,132 | 0 | `—` | — |
| MART | 36 | 0 | `—` | — |
| BEV | 7,750 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | · | · | · | 8,333 | |
| `LineNum` | INTEGER | 85% | 25% | 81% | · | · | · | 20 | |
| `ItemCode` | NVARCHAR(50) | 100% | 100% | 100% | · | · | · | 630 | |
| `BaseQty` | DECIMAL | 100% | 100% | 100% | · | · | · | 265 | |
| `PlannedQty` | DECIMAL | 100% | 100% | 100% | · | · | · | 10,655 | |
| `IssuedQty` | DECIMAL | 99% | 97% | 91% | · | · | · | 10,622 | |
| `IssueType` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `wareHouse` | NVARCHAR(8) | 100% | 100% | 100% | · | · | · | 19 | |
| `VisOrder` | INTEGER | 85% | 25% | 81% | · | · | · | 20 | |
| `WipActCode` | NVARCHAR(15) | <1% | — | — | · | · | · | 4 | |
| `CompTotal` | DECIMAL | 11% | — | <1% | · | · | · | 3,737 | |
| `OcrCode` | NVARCHAR(8) | 5% | 6% | <1% | · | · | · | 16 | |
| `OcrCode2` | NVARCHAR(8) | <1% | — | — | · | · | · | 6 | |
| `OcrCode3` | NVARCHAR(8) | <1% | — | — | · | · | · | 1 | |
| `OcrCode5` | NVARCHAR(8) | <1% | — | — | · | · | · | 1 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | · | · | · | 2 | |
| `UomEntry` | INTEGER | 89% | 100% | 100% | · | · | · | 3 | |
| `UomCode` | NVARCHAR(20) | 89% | 100% | 100% | · | · | · | 2 | |
| `ItemType` | INTEGER | 100% | 100% | 100% | · | · | · | 2 | |
| `AdditQty` | DECIMAL | <1% | — | 12% | · | · | · | 2 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `ResAlloc` | NVARCHAR(1) | 11% | — | <1% | · | · | · | 1 | |
| `StartDate` | TIMESTAMP | 100% | 100% | 100% | · | · | · | 615 | |
| `EndDate` | TIMESTAMP | 100% | 100% | 100% | · | · | · | 615 | |
| `BaseQtyNum` | DECIMAL | 100% | 100% | 100% | · | · | · | 142 | |
| `BaseQtyDen` | DECIMAL | 100% | 100% | 100% | · | · | · | 102 | |
| `RtCalcProp` | DECIMAL | 11% | — | <1% | · | · | · | 2 | |
| `Status` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `ItemName` | NVARCHAR(200) | 100% | 100% | 100% | · | · | · | 647 | |
| `AlwProcDoc` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `PoQuantity` | DECIMAL | 89% | 100% | 100% | · | · | · | 10,143 | |
| `U_WASTAGE_QUANTITY` | DECIMAL | 1% | n/a | 11% | · | n/a | · | 216 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (1)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_WASTAGE_QUANTITY` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`LineNum`** (20 values) — `0`×8,291, `1`×7,239, `2`×6,717, `3`×6,541, `4`×6,408, `5`×5,546, `6`×5,214, `7`×4,338, `8`×1,885, `9`×864, `10`×326, `11`×245, `12`×143, `13`×139, `14`×125, `15`×89, `17`×7, `18`×5, `16`×5, `19`×5
- **`IssueType`** (2 values) — `M`×54,111, `B`×21
- **`wareHouse`** (19 values) — `BH-PC`×32,690, `BH-PP`×13,454, `BH-LO`×4,385, `BH-GR`×1,862, `BH-WST`×483, `BH-SDL`×316, `BH-CRUDE`×233, `DL-GR`×194, `GP-FG`×116, `BH-GJ`×110, `BH-JW`×93, `BH-FG`×67, `BH-PF`×44, `BH-SC`×26, `BH-EC`×25, `BH-PM`×13, `BH-EX`×12, `BH-OT`×7, `GP-NM`×2
- **`VisOrder`** (20 values) — `0`×8,333, `1`×7,274, `2`×6,729, `3`×6,563, `4`×6,418, `5`×5,647, `6`×5,179, `7`×4,250, `8`×1,875, `9`×822, `10`×302, `11`×231, `12`×141, `13`×135, `14`×124, `15`×89, `18`×5, `17`×5, `16`×5, `19`×5
- **`WipActCode`** (5 values) — `NULL`×54,110, `1103009`×11, `5100003`×9, `5100013`×1, `∅`×1
- **`OcrCode`** (17 values) — `NULL`×51,546, `CANOLA`×1,477, `OLIVE`×440, `SUNFLOWR`×145, `MUSTARD`×141, `GROUNDNT`×118, `SOYABEAN`×115, `BLENDED`×88, `COTTONSD`×16, `RICEBRAN`×15, `COCONUT`×13, `GHEE`×6, `∅`×5, `SPICES`×4, `CARTON`×1, `CAP`×1, `TIN`×1
- **`OcrCode2`** (7 values) — `NULL`×54,109, `08-2025`×10, `09-2025`×6, `07-2024`×4, `06-2024`×1, `06-2025`×1, `12-2024`×1
- **`OcrCode3`** (2 values) — `NULL`×54,112, `Factory`×20
- **`OcrCode5`** (2 values) — `NULL`×54,121, `HR`×11
- **`LocCode`** (2 values) — `2`×53,938, `1`×194
- **`UomEntry`** (3 values) — `-1`×39,819, `2`×8,239, `0`×6,074
- **`UomCode`** (3 values) — `Manual`×39,819, `LTR`×8,239, `NULL`×6,074
- **`ItemType`** (2 values) — `4`×48,058, `290`×6,074
- **`AdditQty`** (2 values) — `0.000000`×54,131, `43740.000000`×1
- **`PickStatus`** (1 values) — `N`×54,132
- **`ResAlloc`** (2 values) — `NULL`×48,058, `S`×6,074
- **`RtCalcProp`** (2 values) — `0.000000`×48,052, `100.000000`×6,080
- **`Status`** (1 values) — `P`×54,132
- **`AlwProcDoc`** (2 values) — `N`×54,131, `Y`×1
