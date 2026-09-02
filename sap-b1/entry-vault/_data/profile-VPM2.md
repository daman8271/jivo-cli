# `VPM2` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 11,856 | 0 | `—` | — |
| MART | 2,293 | 0 | `—` | — |
| BEV | 1,872 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocNum` | INTEGER | 100% | 100% | 100% | · | · | · | 5,706 | |
| `InvoiceId` | INTEGER | 52% | 58% | 43% | · | · | · | 76 | |
| `DocEntry` | INTEGER | 100% | 100% | 100% | · | · | · | 9,116 | |
| `SumApplied` | DECIMAL | 100% | 100% | 100% | · | · | · | 8,170 | |
| `AppliedSys` | DECIMAL | 100% | 100% | 100% | · | · | · | 8,170 | |
| `InvType` | NVARCHAR(20) | 100% | 100% | 100% | · | · | · | 7 | |
| `IntrsStat` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `DocLine` | INTEGER | 25% | 11% | 24% | · | · | · | 44 | |
| `vatApplied` | DECIMAL | 45% | 64% | 48% | · | · | · | 4,005 | |
| `vatAppldSy` | DECIMAL | 45% | 64% | 49% | · | · | · | 4,037 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | · | · | · | 1 | |
| `BfDcntSum` | DECIMAL | 100% | 100% | 100% | · | · | · | 8,170 | |
| `BfDcntSumS` | DECIMAL | 100% | 100% | 100% | · | · | · | 8,170 | |
| `BfNetDcnt` | DECIMAL | 74% | 88% | 74% | · | · | · | 6,431 | |
| `BfNetDcntS` | DECIMAL | 74% | 88% | 74% | · | · | · | 6,431 | |
| `ExpAppld` | DECIMAL | 1% | <1% | 6% | · | · | · | 83 | |
| `ExpAppldSC` | DECIMAL | 1% | <1% | 6% | · | · | · | 83 | |
| `InstId` | SMALLINT | 100% | 100% | 100% | · | · | · | 1 | |
| `PaidDpm` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `DpmPosted` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `ExpVatSum` | DECIMAL | <1% | <1% | 4% | · | · | · | 59 | |
| `ExpVatSumS` | DECIMAL | <1% | <1% | 4% | · | · | · | 59 | |
| `IsRateDiff` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `WtInvCatS` | DECIMAL | 33% | 58% | 29% | · | · | · | 1,491 | |
| `WtInvCatSS` | DECIMAL | 33% | 58% | 29% | · | · | · | 1,491 | |
| `OcrCode` | NVARCHAR(8) | <1% | — | <1% | · | · | · | 2 | |
| `DocTransId` | INTEGER | 100% | 100% | 100% | · | · | · | 9,170 | |
| `OcrCode2` | NVARCHAR(8) | <1% | — | <1% | · | · | · | 3 | |
| `OcrCode5` | NVARCHAR(8) | <1% | — | — | · | · | · | 2 | |
| `IsSelected` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `baseAbs` | INTEGER | 100% | 100% | 100% | · | · | · | 9,003 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | · | · | · | 3 | |
| `SpltPmtVAT` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `EncryptIV` | NVARCHAR(100) | 7% | 12% | 7% | · | · | · | 1 | |
| `SelOrder` | INTEGER | 52% | 58% | 43% | · | · | · | 76 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`InvType`** (7 values) — `18`×8,503, `30`×2,189, `46`×779, `19`×169, `24`×109, `13`×80, `14`×27
- **`IntrsStat`** (1 values) — `U`×11,856
- **`selfInv`** (1 values) — `N`×11,856
- **`ObjType`** (1 values) — `46`×11,856
- **`InstId`** (1 values) — `1`×11,856
- **`PaidDpm`** (1 values) — `N`×11,856
- **`DpmPosted`** (1 values) — `Y`×11,856
- **`IsRateDiff`** (1 values) — `N`×11,856
- **`OcrCode`** (3 values) — `NULL`×11,810, `CANOLA`×45, `COCONUT`×1
- **`OcrCode2`** (4 values) — `NULL`×11,816, `11-2024`×23, `10-2024`×15, `02-2025`×2
- **`OcrCode5`** (3 values) — `NULL`×11,818, `HR`×21, `DL`×17
- **`IsSelected`** (1 values) — `N`×11,856
- **`DocSubType`** (3 values) — `GA`×6,318, `--`×5,533, `GD`×5
- **`SpltPmtVAT`** (1 values) — `N`×11,856
- **`EncryptIV`** (2 values) — `NULL`×11,011, `N`×845
