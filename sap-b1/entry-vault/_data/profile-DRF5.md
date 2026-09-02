# `DRF5` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 6,954 | 0 | `—` | — |
| MART | 3,073 | 0 | `—` | — |
| BEV | 846 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. A dash means the field is empty in every single row — SAP offers it, JIVO never uses it.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `AbsEntry` | INTEGER | 100% | 100% | 100% | · | · | · | 6,945 | |
| `WTCode` | NVARCHAR(4) | 100% | 100% | 100% | · | · | · | 18 | |
| `Rate` | DECIMAL | 100% | 99% | 100% | · | · | · | 5 | |
| `TaxbleAmnt` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `TxblAmntSC` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `TxblAmntFC` | DECIMAL | — | <1% | — | · | · | · | 1 | |
| `WTAmnt` | DECIMAL | 94% | 95% | 91% | · | · | · | 2,098 | |
| `WTAmntSC` | DECIMAL | 94% | 95% | 91% | · | · | · | 2,098 | |
| `WTAmntFC` | DECIMAL | — | <1% | — | · | · | · | 1 | |
| `Category` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `Criteria` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `Type` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `BaseType` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `BaseAbsEnt` | INTEGER | 100% | 100% | 100% | · | · | · | 314 | |
| `BaseNum` | INTEGER | 100% | 100% | 100% | · | · | · | 2 | |
| `LineNum` | INTEGER | <1% | <1% | — | · | · | · | 2 | |
| `BaseRef` | INTEGER | 5% | 4% | 7% | · | · | · | 313 | |
| `Status` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `TrgAbsEntr` | INTEGER | 100% | 100% | 99% | · | · | · | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | · | · | · | 3 | |
| `Doc1LineNo` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `WtLineType` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `TdsAcc` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 18 | |
| `SurAcc` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 18 | |
| `CessAcc` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 18 | |
| `HscAcc` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 18 | |
| `TdsRate` | DECIMAL | 100% | 100% | 100% | · | · | · | 5 | |
| `SurRate` | DECIMAL | — | — | <1% | · | · | · | 1 | |
| `TdsBAmt` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,162 | |
| `TdsBAmtSC` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,162 | |
| `TdsBAmtFC` | DECIMAL | — | <1% | — | · | · | · | 1 | |
| `SurBAmt` | DECIMAL | 94% | 96% | 91% | · | · | · | 2,097 | |
| `SurBAmtSC` | DECIMAL | 94% | 96% | 91% | · | · | · | 2,097 | |
| `SurBAmtFC` | DECIMAL | — | <1% | — | · | · | · | 1 | |
| `CessBAmt` | DECIMAL | 94% | 96% | 91% | · | · | · | 2,097 | |
| `CessBAmtSC` | DECIMAL | 94% | 96% | 91% | · | · | · | 2,097 | |
| `CessBAmtFC` | DECIMAL | — | <1% | — | · | · | · | 1 | |
| `HscBAmt` | DECIMAL | 94% | 96% | 91% | · | · | · | 2,097 | |
| `HscBAmtSC` | DECIMAL | 94% | 96% | 91% | · | · | · | 2,097 | |
| `HscBAmtFC` | DECIMAL | — | <1% | — | · | · | · | 1 | |
| `TdsAmnt` | DECIMAL | 94% | 95% | 91% | · | · | · | 2,098 | |
| `TdsAmntSC` | DECIMAL | 94% | 95% | 91% | · | · | · | 2,098 | |
| `TdsAmntFC` | DECIMAL | — | <1% | — | · | · | · | 1 | |
| `SurAmnt` | DECIMAL | — | — | <1% | · | · | · | 1 | |
| `SurAmntSC` | DECIMAL | — | — | <1% | · | · | · | 1 | |
| `TDSType` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `IgstBAmt` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `IgstBAmtSC` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `IgstBAmtFC` | DECIMAL | — | <1% | — | · | · | · | 1 | |
| `CgstBAmt` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `CgstBAmtSC` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `CgstBAmtFC` | DECIMAL | — | <1% | — | · | · | · | 1 | |
| `SgstBAmt` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `SgstBAmtSC` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `SgstBAmtFC` | DECIMAL | — | <1% | — | · | · | · | 1 | |
| `UtgstBAmt` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `UtgstBAmtS` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `UtgstBAmtF` | DECIMAL | — | <1% | — | · | · | · | 1 | |
| `CsgstBAmt` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `CsgstBAmtS` | DECIMAL | 95% | 97% | 91% | · | · | · | 5,164 | |
| `CsgstBAmtF` | DECIMAL | — | <1% | — | · | · | · | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`WTCode`** (18 values) — `TDS`×2,044, `C194`×2,044, `194C`×886, `194H`×859, `1031`×226, `94JB`×204, `94JA`×171, `1024`×165, `94IB`×145, `1006`×67, `195`×54, `1023`×44, `1027`×16, `1026`×12, `1009`×10, `94IA`×4, `1041`×2, `94I1`×1
- **`Rate`** (5 values) — `2.000000`×3,322, `0.100000`×2,270, `1.000000`×931, `10.000000`×375, `20.000000`×56
- **`Category`** (1 values) — `I`×6,954
- **`Criteria`** (2 values) — `N`×6,621, `Y`×333
- **`Type`** (1 values) — `V`×6,954
- **`BaseType`** (1 values) — `N`×6,954
- **`BaseNum`** (2 values) — `-1`×6,620, `18`×334
- **`LineNum`** (2 values) — `0`×6,945, `1`×9
- **`Status`** (1 values) — `O`×6,954
- **`TrgAbsEntr`** (2 values) — `-1`×6,926, `NULL`×28
- **`ObjType`** (3 values) — `18`×6,619, `19`×334, `112`×1
- **`Doc1LineNo`** (1 values) — `-1`×6,954
- **`WtLineType`** (1 values) — `D`×6,954
- **`TdsAcc`** (18 values) — `2133010`×2,044, `2133006`×2,044, `2133003`×886, `2133007`×859, `2133022`×226, `2133005`×204, `2133009`×171, `2133018`×165, `2133001`×145, `2133019`×67, `2133012`×54, `2133016`×44, `2133017`×16, `2133021`×12, `2133014`×10, `2133002`×4, `2133023`×2, `2133013`×1
- **`SurAcc`** (18 values) — `2133006`×2,044, `2133010`×2,044, `2133003`×886, `2133007`×859, `2133022`×226, `2133005`×204, `2133009`×171, `2133018`×165, `2133001`×145, `2133019`×67, `2133012`×54, `2133016`×44, `2133017`×16, `2133021`×12, `2133014`×10, `2133002`×4, `2133023`×2, `2133013`×1
- **`CessAcc`** (18 values) — `2133006`×2,044, `2133010`×2,044, `2133003`×886, `2133007`×859, `2133022`×226, `2133005`×204, `2133009`×171, `2133018`×165, `2133001`×145, `2133019`×67, `2133012`×54, `2133016`×44, `2133017`×16, `2133021`×12, `2133014`×10, `2133002`×4, `2133023`×2, `2133013`×1
- **`HscAcc`** (18 values) — `2133010`×2,044, `2133006`×2,044, `2133003`×886, `2133007`×859, `2133022`×226, `2133005`×204, `2133009`×171, `2133018`×165, `2133001`×145, `2133019`×67, `2133012`×54, `2133016`×44, `2133017`×16, `2133021`×12, `2133014`×10, `2133002`×4, `2133023`×2, `2133013`×1
- **`TdsRate`** (5 values) — `2.000000`×3,322, `0.100000`×2,270, `1.000000`×931, `10.000000`×375, `20.000000`×56
- **`TDSType`** (1 values) — `E`×6,954
