# `VPM4` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 9,023 | 0 | `—` | — |
| MART | 718 | 0 | `—` | — |
| BEV | 623 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocNum` | INTEGER | 100% | 100% | 100% | · | · | · | 5,062 | |
| `LineId` | INTEGER | 44% | 6% | 53% | · | · | · | 69 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 366 | |
| `SumApplied` | DECIMAL | 100% | 100% | 100% | · | · | · | 3,338 | |
| `AppliedSys` | DECIMAL | 100% | 100% | 100% | · | · | · | 3,338 | |
| `Descrip` | NVARCHAR(250) | 55% | 3% | 82% | · | · | · | 4,576 | |
| `AcctName` | NVARCHAR(200) | 100% | 100% | 100% | · | · | · | 370 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | · | · | · | 1 | |
| `OcrCode` | NVARCHAR(8) | 98% | 24% | 99% | · | · | · | 3 | |
| `GrossAmnt` | DECIMAL | 100% | 100% | 100% | · | · | · | 3,338 | |
| `GrssAmntSC` | DECIMAL | 100% | 100% | 100% | · | · | · | 3,338 | |
| `AmntBase` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `UserChaVat` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `OcrCode2` | NVARCHAR(8) | 99% | 86% | 99% | · | · | · | 30 | |
| `OcrCode3` | NVARCHAR(8) | 58% | 19% | 89% | · | · | · | 10 | |
| `OcrCode4` | NVARCHAR(8) | 56% | 6% | 89% | · | · | · | 13 | |
| `OcrCode5` | NVARCHAR(8) | 11% | 12% | 11% | · | · | · | 3 | |
| `LocCode` | INTEGER | 65% | 34% | 72% | · | · | · | 4 | |
| `U_Remarks` | NVARCHAR(100) | <1% | 4% | — | · | · | · | 54 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`ObjType`** (1 values) — `46`×9,023
- **`OcrCode`** (4 values) — `CANOLA`×8,841, `NULL`×156, `∅`×20, `OLIVE`×6
- **`AmntBase`** (1 values) — `E`×9,023
- **`UserChaVat`** (2 values) — `N`×9,019, `NULL`×4
- **`OcrCode2`** (30 values) — `10-2024`×711, `11-2024`×701, `01-2025`×651, `03-2026`×605, `12-2024`×509, `02-2026`×462, `05-2025`×429, `04-2026`×397, `07-2025`×377, `01-2026`×329, `06-2026`×324, `09-2025`×323, `04-2025`×319, `10-2025`×315, `02-2025`×308, `03-2025`×304, `08-2025`×304, `12-2025`×302, `05-2026`×298, `11-2025`×279, `07-2026`×263, `06-2025`×249, `09-2024`×81, `08-2026`×75, `NULL`×73, `∅`×14, `04-2024`×6, `05-2024`×6, `08-2024`×4, `07-2024`×3
- **`OcrCode3`** (11 values) — `Interest`×5,042, `NULL`×3,469, `∅`×326, `Factory`×99, `OTE`×37, `BackOff`×23, `Sales`×11, `NPD3`×9, `NPD1`×4, `FACT_COM`×2, `Med MKT`×1
- **`OcrCode4`** (14 values) — `BankChgs`×4,605, `NULL`×3,249, `∅`×680, `CC Limit`×260, `Trm Loan`×106, `VHCLLOAN`×75, `IMPORT`×21, `Accounts`×7, `CAL CNTR`×5, `EXPORT`×5, `IT`×4, `Admin`×4, `CSD`×1, `Legal`×1
- **`OcrCode5`** (4 values) — `NULL`×7,466, `DL`×914, `∅`×561, `HR`×82
- **`LocCode`** (5 values) — `1`×5,688, `NULL`×3,180, `2`×145, `5`×8, `4`×2
