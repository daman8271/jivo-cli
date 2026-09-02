# `RCT2` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 19,514 | 0 | `—` | — |
| MART | 20,577 | 0 | `—` | — |
| BEV | 4,073 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocNum` | INTEGER | 100% | 100% | 100% | · | · | · | 3,053 | |
| `InvoiceId` | INTEGER | 84% | 72% | 74% | · | · | · | 1,288 | |
| `DocEntry` | INTEGER | 100% | 100% | 100% | · | · | · | 16,827 | |
| `SumApplied` | DECIMAL | 100% | 100% | 100% | · | · | · | 13,785 | |
| `AppliedSys` | DECIMAL | 100% | 100% | 100% | · | · | · | 13,785 | |
| `InvType` | NVARCHAR(20) | 100% | 100% | 100% | · | · | · | 7 | |
| `IntrsStat` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `DocLine` | INTEGER | 28% | 6% | 32% | · | · | · | 66 | |
| `vatApplied` | DECIMAL | 65% | 94% | 66% | · | · | · | 10,493 | |
| `vatAppldSy` | DECIMAL | 65% | 94% | 66% | · | · | · | 10,516 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | · | · | · | 1 | |
| `BfDcntSum` | DECIMAL | 100% | 100% | 100% | · | · | · | 13,785 | |
| `BfDcntSumS` | DECIMAL | 100% | 100% | 100% | · | · | · | 13,785 | |
| `BfNetDcnt` | DECIMAL | 71% | 94% | 67% | · | · | · | 10,228 | |
| `BfNetDcntS` | DECIMAL | 71% | 94% | 67% | · | · | · | 10,228 | |
| `ExpAppld` | DECIMAL | <1% | — | — | · | · | · | 2 | |
| `ExpAppldSC` | DECIMAL | <1% | — | — | · | · | · | 2 | |
| `InstId` | SMALLINT | 100% | 100% | 100% | · | · | · | 1 | |
| `PaidDpm` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `DpmPosted` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `ExpVatSum` | DECIMAL | <1% | — | — | · | · | · | 2 | |
| `ExpVatSumS` | DECIMAL | <1% | — | — | · | · | · | 2 | |
| `IsRateDiff` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `WtInvCatS` | DECIMAL | <1% | — | <1% | · | · | · | 26 | |
| `WtInvCatSS` | DECIMAL | <1% | — | <1% | · | · | · | 26 | |
| `OcrCode` | NVARCHAR(8) | <1% | — | <1% | · | · | · | 1 | |
| `DocTransId` | INTEGER | 100% | 100% | 100% | · | · | · | 17,033 | |
| `OcrCode2` | NVARCHAR(8) | <1% | — | — | · | · | · | 1 | |
| `OcrCode5` | NVARCHAR(8) | <1% | — | — | · | · | · | 1 | |
| `IsSelected` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `baseAbs` | INTEGER | 100% | 100% | 100% | · | · | · | 16,452 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | · | · | · | 3 | |
| `SpltPmtVAT` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `EncryptIV` | NVARCHAR(100) | 13% | 19% | 12% | · | · | · | 1 | |
| `SelOrder` | INTEGER | 84% | 72% | 74% | · | · | · | 1,288 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`InvType`** (7 values) — `13`×11,900, `24`×4,747, `14`×1,876, `30`×725, `46`×152, `18`×113, `19`×1
- **`IntrsStat`** (1 values) — `U`×19,514
- **`selfInv`** (1 values) — `N`×19,514
- **`ObjType`** (1 values) — `24`×19,514
- **`ExpAppld`** (2 values) — `0.000000`×19,510, `7500.000000`×4
- **`ExpAppldSC`** (2 values) — `0.000000`×19,510, `7500.000000`×4
- **`InstId`** (1 values) — `1`×19,514
- **`PaidDpm`** (1 values) — `N`×19,514
- **`DpmPosted`** (1 values) — `Y`×19,514
- **`ExpVatSum`** (2 values) — `0.000000`×19,510, `375.000000`×4
- **`ExpVatSumS`** (2 values) — `0.000000`×19,510, `375.000000`×4
- **`IsRateDiff`** (1 values) — `N`×19,514
- **`WtInvCatS`** (26 values) — `0.000000`×19,483, `10129.000000`×2, `3983.000000`×2, `200.000000`×2, `9647.000000`×2, `11576.000000`×2, `11025.000000`×2, `42373.000000`×1, `4982.000000`×1, `1254.000000`×1, `4680.000000`×1, `7307.000000`×1, `5211.000000`×1, `5000.000000`×1, `4044.000000`×1, `3818.000000`×1, `4712.000000`×1, `230.000000`×1, `1800.000000`×1, `5765.000000`×1, `304.000000`×1, `4832.000000`×1, `5206.000000`×1, `122.000000`×1, `2490.000000`×1, `12500.000000`×1
- **`WtInvCatSS`** (26 values) — `0.000000`×19,483, `11576.000000`×2, `9647.000000`×2, `200.000000`×2, `11025.000000`×2, `10129.000000`×2, `3983.000000`×2, `2490.000000`×1, `12500.000000`×1, `1254.000000`×1, `4982.000000`×1, `42373.000000`×1, `4680.000000`×1, `7307.000000`×1, `5211.000000`×1, `304.000000`×1, `3818.000000`×1, `4712.000000`×1, `122.000000`×1, `5206.000000`×1, `4832.000000`×1, `5000.000000`×1, `230.000000`×1, `1800.000000`×1, `5765.000000`×1, `4044.000000`×1
- **`OcrCode`** (2 values) — `NULL`×19,506, `CANOLA`×8
- **`OcrCode2`** (2 values) — `NULL`×19,510, `11-2024`×4
- **`OcrCode5`** (2 values) — `NULL`×19,510, `DL`×4
- **`IsSelected`** (1 values) — `N`×19,514
- **`DocSubType`** (3 values) — `GA`×12,640, `--`×6,861, `GD`×13
- **`SpltPmtVAT`** (1 values) — `N`×19,514
- **`EncryptIV`** (2 values) — `NULL`×16,968, `N`×2,546
