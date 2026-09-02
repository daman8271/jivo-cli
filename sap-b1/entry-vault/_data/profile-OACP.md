# `OACP` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 3 | 0 | `—` | — |
| MART | 3 | 0 | `—` | — |
| BEV | 3 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `AbsEntry` | INTEGER | 100% | 100% | 100% | · | · | · | 3 | |
| `PeriodCat` | NVARCHAR(10) | 100% | 100% | 100% | · | · | · | 3 | |
| `FinancYear` | TIMESTAMP | 100% | 100% | 100% | · | · | · | 3 | |
| `Year` | SMALLINT | 100% | 100% | 100% | · | · | · | 3 | |
| `PeriodName` | NVARCHAR(20) | 67% | 67% | 67% | · | · | · | 2 | |
| `SubType` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `PeriodNum` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `F_RefDate` | TIMESTAMP | 67% | 67% | 67% | · | · | · | 2 | |
| `T_RefDate` | TIMESTAMP | 67% | 67% | 67% | · | · | · | 2 | |
| `F_DueDate` | TIMESTAMP | 67% | 67% | 67% | · | · | · | 2 | |
| `T_DueDate` | TIMESTAMP | 67% | 67% | 67% | · | · | · | 2 | |
| `F_TaxDate` | TIMESTAMP | 67% | 67% | 67% | · | · | · | 2 | |
| `T_TaxDate` | TIMESTAMP | 67% | 67% | 67% | · | · | · | 2 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | · | · | · | 1 | |
| `LinkAct_1` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 1 | |
| `LinkAct_9` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 1 | |
| `DfltIncom` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 1 | |
| `DfltExpn` | NVARCHAR(15) | — | — | 33% | · | · | · | 0 | |
| `LinkAct_24` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 1 | |
| `PricDifAct` | NVARCHAR(15) | 67% | — | — | · | · | · | 1 | |
| `BnkChgAct` | NVARCHAR(15) | — | — | 100% | · | · | · | 0 | |
| `ExpClrAct` | NVARCHAR(15) | — | — | 33% | · | · | · | 0 | |
| `WipVarAcct` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 1 | |
| `WipAcct` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 1 | |
| `PlaAct` | NVARCHAR(15) | 67% | — | — | · | · | · | 1 | |
| `ResStdExp1` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 1 | |
| `ResStdExp2` | NVARCHAR(15) | 67% | — | — | · | · | · | 1 | |
| `ResStdExp3` | NVARCHAR(15) | 67% | — | — | · | · | · | 1 | |
| `ResStdExp4` | NVARCHAR(15) | 67% | — | — | · | · | · | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`AbsEntry`** (3 values) — `2`×1, `1`×1, `4`×1
- **`PeriodCat`** (3 values) — `FY2425`×1, `FY2526`×1, `FY2627`×1
- **`FinancYear`** (3 values) — `2024-04-01 00:00:00.0000000`×1, `2025-04-01 00:00:00.0000000`×1, `2026-04-01 00:00:00.0000000`×1
- **`Year`** (3 values) — `2024`×1, `2025`×1, `2026`×1
- **`PeriodName`** (3 values) — `FY2627`×1, `FY2526`×1, `NULL`×1
- **`SubType`** (1 values) — `M`×3
- **`PeriodNum`** (1 values) — `12`×3
- **`F_RefDate`** (3 values) — `NULL`×1, `2025-04-01 00:00:00.0000000`×1, `2026-04-01 00:00:00.0000000`×1
- **`T_RefDate`** (3 values) — `2026-03-31 00:00:00.0000000`×1, `NULL`×1, `2027-03-31 00:00:00.0000000`×1
- **`F_DueDate`** (3 values) — `NULL`×1, `2025-04-01 00:00:00.0000000`×1, `2026-04-01 00:00:00.0000000`×1
- **`T_DueDate`** (3 values) — `2026-03-31 00:00:00.0000000`×1, `NULL`×1, `2027-03-31 00:00:00.0000000`×1
- **`F_TaxDate`** (3 values) — `2026-04-01 00:00:00.0000000`×1, `2025-04-01 00:00:00.0000000`×1, `NULL`×1
- **`T_TaxDate`** (3 values) — `2026-03-31 00:00:00.0000000`×1, `NULL`×1, `2027-03-31 00:00:00.0000000`×1
- **`UserSign`** (1 values) — `1`×3
- **`LinkAct_1`** (1 values) — `1101001`×3
- **`LinkAct_9`** (1 values) — `1101002`×3
- **`DfltIncom`** (1 values) — `1102007`×3
- **`LinkAct_24`** (1 values) — `5680014`×3
- **`PricDifAct`** (2 values) — `5100001`×2, `NULL`×1
- **`WipVarAcct`** (1 values) — `5100003`×3
- **`WipAcct`** (1 values) — `1103009`×3
- **`PlaAct`** (2 values) — `11133147`×2, `NULL`×1
- **`ResStdExp1`** (1 values) — `2163022`×3
- **`ResStdExp2`** (2 values) — `2163025`×2, `NULL`×1
- **`ResStdExp3`** (2 values) — `5100019`×2, `NULL`×1
- **`ResStdExp4`** (2 values) — `5100021`×2, `NULL`×1
