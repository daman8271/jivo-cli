# `IPF1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 543 | 0 | `—` | — |
| MART | 0 | — | — | **not used in this book** |
| BEV | 15 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | BEV all | OIL 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | · | · | 534 | |
| `LineNum` | INTEGER | 2% | 60% | · | · | 3 | |
| `BaseType` | INTEGER | 100% | 100% | · | · | 2 | |
| `BaseEntry` | INTEGER | 100% | 100% | · | · | 535 | |
| `ItemCode` | NVARCHAR(50) | 100% | 100% | · | · | 34 | |
| `Dscription` | NVARCHAR(200) | 100% | 100% | · | · | 35 | |
| `Quantity` | DECIMAL | 100% | 100% | · | · | 386 | |
| `PriceFOB` | DECIMAL | 100% | 100% | · | · | 520 | |
| `Currency` | NVARCHAR(3) | 100% | 100% | · | · | 3 | |
| `Rate` | DECIMAL | 15% | — | · | · | 43 | |
| `Cost` | DECIMAL | 99% | 100% | · | · | 326 | |
| `PriceAtWH` | DECIMAL | 100% | 100% | · | · | 534 | |
| `LineTotal` | DECIMAL | 100% | 100% | · | · | 535 | |
| `UnitCode` | SMALLINT | 100% | 100% | · | · | 1 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | · | · | 49 | |
| `Reference` | NVARCHAR(16) | 100% | 100% | · | · | 531 | |
| `OrigLine` | INTEGER | 7% | 60% | · | · | 3 | |
| `FactNoCust` | DECIMAL | 99% | 100% | · | · | 230 | |
| `FacWthCust` | DECIMAL | 99% | 100% | · | · | 230 | |
| `PriceList` | SMALLINT | 12% | 67% | · | · | 2 | |
| `CostOH` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `StockEval` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `WhsCode` | NVARCHAR(8) | 100% | 100% | · | · | 6 | |
| `Locked` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `FobValue` | DECIMAL | 100% | 100% | · | · | 524 | |
| `FobValueFC` | DECIMAL | 15% | — | · | · | 69 | |
| `TtlExpndLC` | DECIMAL | 99% | 100% | · | · | 519 | |
| `TtlCostLC` | DECIMAL | 99% | 100% | · | · | 519 | |
| `TtlExpndSC` | DECIMAL | 99% | 100% | · | · | 519 | |
| `OriBAbsEnt` | INTEGER | 100% | 100% | · | · | 531 | |
| `OriBLinNum` | INTEGER | 7% | 60% | · | · | 3 | |
| `TargetDoc` | INTEGER | <1% | — | · | · | 5 | |
| `FobValCurr` | NVARCHAR(3) | 100% | 100% | · | · | 3 | |
| `FobnLaC` | DECIMAL | 100% | 100% | · | · | 524 | |
| `FobnLaCFC` | DECIMAL | 15% | — | · | · | 69 | |
| `NumPerMsr` | DECIMAL | 100% | 100% | · | · | 2 | |
| `OcrCode` | NVARCHAR(8) | 97% | 100% | · | · | 11 | |
| `OcrCode2` | NVARCHAR(8) | 58% | 100% | · | · | 21 | |
| `OcrCode3` | NVARCHAR(8) | 54% | 100% | · | · | 1 | |
| `OcrCode5` | NVARCHAR(8) | 32% | 100% | · | · | 1 | |
| `OriBDocTyp` | NVARCHAR(11) | 100% | 100% | · | · | 1 | |
| `SnbType` | NVARCHAR(20) | 100% | 100% | · | · | 1 | |
| `SnbAbsEnt` | INTEGER | 100% | 100% | · | · | 1 | |
| `ExcInStk` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `CstmInStk` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `CstmVatStk` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `InvQty` | DECIMAL | 100% | 100% | · | · | 388 | |
| `UoMNum` | DECIMAL | 100% | 100% | · | · | 2 | |
| `UoMDen` | DECIMAL | 100% | 100% | · | · | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (1)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_SchemeAgnst` | OIL | **BEV** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`LineNum`** (3 values) — `0`×534, `1`×8, `2`×1
- **`BaseType`** (2 values) — `20`×538, `69`×5
- **`Currency`** (3 values) — `INR`×464, `USD`×53, `EUR`×26
- **`UnitCode`** (1 values) — `4`×543
- **`OrigLine`** (3 values) — `0`×505, `1`×27, `2`×11
- **`PriceList`** (2 values) — `0`×478, `-1`×65
- **`CostOH`** (1 values) — `Y`×543
- **`StockEval`** (1 values) — `Y`×543
- **`UseBaseUn`** (1 values) — `N`×543
- **`WhsCode`** (6 values) — `BH-GJ`×464, `BH-CRUDE`×47, `BH-VA`×17, `BH-FA`×8, `BH-EX`×6, `BH-FG`×1
- **`Locked`** (1 values) — `N`×543
- **`OriBLinNum`** (3 values) — `0`×505, `1`×27, `2`×11
- **`TargetDoc`** (6 values) — `NULL`×538, `755`×1, `98`×1, `871`×1, `721`×1, `1805`×1
- **`FobValCurr`** (3 values) — `INR`×464, `USD`×53, `EUR`×26
- **`NumPerMsr`** (2 values) — `1098.900000`×508, `1.000000`×35
- **`OcrCode`** (12 values) — `SOYABEAN`×226, `MUSTARD`×106, `CANOLA`×78, `GROUNDNT`×37, `OLIVE`×26, `NULL`×17, `SUNFLOWR`×16, `COTTONSD`×11, `COCONUT`×11, `RICEBRAN`×8, `SlICEDOL`×6, `SESAME`×1
- **`OcrCode2`** (22 values) — `NULL`×226, `09-2025`×31, `11-2024`×29, `12-2025`×27, `08-2025`×24, `06-2025`×24, `07-2025`×23, `12-2024`×22, `10-2025`×18, `11-2025`×16, `03-2025`×16, `10-2024`×14, `05-2025`×12, `04-2026`×11, `03-2026`×10, `02-2025`×10, `01-2026`×7, `05-2026`×6, `02-2026`×6, `01-2025`×6, `04-2024`×3, `04-2025`×2
- **`OcrCode3`** (2 values) — `Factory`×292, `NULL`×251
- **`OcrCode5`** (2 values) — `NULL`×368, `HR`×175
- **`OriBDocTyp`** (1 values) — `20`×543
- **`SnbType`** (1 values) — `-1`×543
- **`SnbAbsEnt`** (1 values) — `-1`×543
- **`ExcInStk`** (1 values) — `N`×543
- **`CstmInStk`** (1 values) — `Y`×543
- **`CstmVatStk`** (1 values) — `Y`×543
- **`UoMNum`** (2 values) — `1098.900000`×508, `1.000000`×35
- **`UoMDen`** (1 values) — `1.000000`×543
