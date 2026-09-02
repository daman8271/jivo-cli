# `OACT` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 1,429 | 1,429 | `CreateDate` | 2024-08-27 → 2026-08-20 |
| MART | 1,104 | 1,104 | `CreateDate` | 2024-08-27 → 2026-06-13 |
| BEV | 765 | 765 | `CreateDate` | 2024-08-27 → 2026-08-06 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 1,429 | |
| `AcctName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 1,407 | |
| `CurrTotal` | DECIMAL | 49% | 34% | 36% | 49% | 34% | 36% | 632 | |
| `Finanse` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Budget` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Frozen` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Postable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Fixed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Levels` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `GrpLine` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 710 | |
| `FatherNum` | NVARCHAR(15) | 99% | 99% | 99% | 99% | 99% | 99% | 109 | |
| `CashBox` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GroupMask` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `RateTrans` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxIncome` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ExmIncome` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExtrMatch` | INTEGER | 1% | <1% | <1% | 1% | <1% | <1% | 10 | |
| `ActType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlncTrnsfr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OverType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysMatch` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PrevYear` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ActCurr` | NVARCHAR(3) | 100% | 100% | 99% | 100% | 100% | 99% | 2 | |
| `SysTotal` | DECIMAL | 49% | 34% | 36% | 49% | 34% | 36% | 632 | |
| `Protected` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RealAcct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Advance` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 245 | |
| `FrgnName` | NVARCHAR(200) | <1% | <1% | 1% | <1% | <1% | 1% | 10 | |
| `RevalMatch` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LocMth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `LocManTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ValidFor` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `FrozenFor` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `FrozenComm` | NVARCHAR(30) | <1% | <1% | — | <1% | <1% | — | 2 | |
| `Counter` | INTEGER | 99% | 99% | 99% | 99% | 99% | 99% | 1,420 | |
| `FormatCode` | NVARCHAR(210) | 99% | 99% | 99% | 99% | 99% | 99% | 1,419 | |
| `CfwRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExchRate` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatChange` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxPostAcc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BalDirect` | NVARCHAR(4) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `MultiLink` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PrjRelvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Dim1Relvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Dim2Relvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Dim3Relvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Dim4Relvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Dim5Relvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AccrualTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DatevAutoA` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DatevFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PCN874Rpt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SCAdjust` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ActId` | NVARCHAR(210) | 100% | 100% | 100% | 100% | 100% | 100% | 1,429 | |
| `BlocManPos` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CstAccOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BalanceA` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CemRelvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Emp_Code` | NVARCHAR(8) | 28% | 14% | 16% | 28% | 14% | 16% | 344 | |
| `U_Account_Number` | NVARCHAR(20) | 20% | 6% | 4% | 20% | 6% | 4% | 265 | |
| `U_IFSC` | NVARCHAR(11) | 19% | 6% | 4% | 19% | 6% | 4% | 173 | |
| `U_Bank_Name` | NVARCHAR(30) | 19% | 6% | 4% | 19% | 6% | 4% | 52 | |
| `U_WG_GLNO` | INTEGER | 35% | n/a | n/a | 35% | n/a | n/a | 491 | |
| `U_FA_CODE` | NVARCHAR(12) | 2% | — | 2% | 2% | — | 2% | 25 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_OIL_GLNO` | BEV | **OIL, MART** |
| `U_WG_GLNO` | OIL | **MART, BEV** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`Finanse`** (2 values) — `N`×1,426, `Y`×3
- **`Budget`** (2 values) — `Y`×841, `N`×588
- **`Frozen`** (1 values) — `N`×1,429
- **`Postable`** (2 values) — `Y`×1,313, `N`×116
- **`Fixed`** (2 values) — `N`×1,378, `Y`×51
- **`Levels`** (6 values) — `4`×883, `3`×256, `5`×239, `6`×24, `2`×17, `1`×10
- **`CashBox`** (1 values) — `N`×1,429
- **`GroupMask`** (10 values) — `1`×710, `2`×318, `5`×282, `4`×105, `3`×9, `9`×1, `7`×1, `10`×1, `6`×1, `8`×1
- **`RateTrans`** (1 values) — `Y`×1,429
- **`TaxIncome`** (2 values) — `Y`×1,420, `N`×9
- **`ExmIncome`** (1 values) — `N`×1,429
- **`ExtrMatch`** (11 values) — `NULL`×1,410, `3`×7, `25`×3, `13`×2, `7`×1, `2`×1, `30`×1, `23`×1, `9`×1, `8`×1, `4`×1
- **`ActType`** (3 values) — `N`×1,100, `E`×235, `I`×94
- **`Transfered`** (1 values) — `N`×1,429
- **`BlncTrnsfr`** (1 values) — `N`×1,429
- **`OverType`** (1 values) — `N`×1,429
- **`SysMatch`** (1 values) — `-1`×1,429
- **`PrevYear`** (1 values) — `N`×1,429
- **`ActCurr`** (3 values) — `##`×1,392, `INR`×32, `NULL`×5
- **`Protected`** (2 values) — `N`×1,322, `Y`×107
- **`RealAcct`** (1 values) — `N`×1,429
- **`Advance`** (2 values) — `N`×1,419, `Y`×10
- **`FrgnName`** (11 values) — `NULL`×1,419, `#8`×1, `Revenue`×1, `#7`×1, `Equity`×1, `#9`×1, `#10`×1, `Liabilities`×1, `#6`×1, `Expenditure`×1, `Assets`×1
- **`RevalMatch`** (2 values) — `N`×1,428, `Y`×1
- **`LocMth`** (1 values) — `Y`×1,429
- **`UserSign`** (10 values) — `1`×934, `38`×241, `40`×101, `47`×72, `7`×66, `13`×6, `9`×5, `10`×2, `39`×1, `56`×1
- **`LocManTran`** (2 values) — `N`×1,388, `Y`×41
- **`ObjType`** (1 values) — `1`×1,429
- **`ValidFor`** (2 values) — `Y`×1,245, `N`×184
- **`FrozenFor`** (2 values) — `N`×1,359, `Y`×70
- **`FrozenComm`** (3 values) — `NULL`×1,427, `BY MISTAKE IT WAS MADE`×1, `DUE TO WRONG BRANCH`×1
- **`CfwRlvnt`** (1 values) — `N`×1,429
- **`ExchRate`** (1 values) — `Y`×1,429
- **`VatChange`** (1 values) — `Y`×1,429
- **`TaxPostAcc`** (1 values) — `N`×1,429
- **`BalDirect`** (1 values) — `0`×1,429
- **`MultiLink`** (1 values) — `N`×1,429
- **`PrjRelvnt`** (1 values) — `N`×1,429
- **`Dim1Relvnt`** (1 values) — `N`×1,429
- **`Dim2Relvnt`** (1 values) — `N`×1,429
- **`Dim3Relvnt`** (1 values) — `N`×1,429
- **`Dim4Relvnt`** (1 values) — `N`×1,429
- **`Dim5Relvnt`** (1 values) — `N`×1,429
- **`AccrualTyp`** (1 values) — `N`×1,429
- **`DatevAutoA`** (1 values) — `N`×1,429
- **`DatevFirst`** (1 values) — `Y`×1,429
- **`PCN874Rpt`** (1 values) — `N`×1,429
- **`SCAdjust`** (1 values) — `N`×1,429
- **`BlocManPos`** (2 values) — `N`×1,287, `Y`×142
- **`CstAccOnly`** (1 values) — `N`×1,429
- **`BalanceA`** (1 values) — `N`×1,429
- **`CemRelvnt`** (1 values) — `N`×1,429
- **`U_FA_CODE`** (26 values) — `NULL`×1,404, `FA0000337`×1, `FA0000004`×1, `FA0000044`×1, `FA0000052`×1, `FA0000290`×1, `FA0000024`×1, `FA0000036`×1, `FA0000034`×1, `FA0000048`×1, `FA0000002`×1, `FA0000265`×1, `FA0000050`×1, `FA0000051`×1, `FA0000003`×1, `FA0000189`×1, `FA0000049`×1, `FA0000031`×1, `FA0000273`×1, `FA0000045`×1, `FA0000354`×1, `FA0000013`×1, `FA0000046`×1, `FA0000326`×1, `FA0000315`×1, `FA0000035`×1
