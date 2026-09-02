# `OIPF` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 534 | 75 | `DocDate` | 2024-10-01 → 2026-08-21 |
| MART | 0 | — | — | **not used in this book** |
| BEV | 6 | 0 | `DocDate` | 2025-01-14 → 2026-03-01 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | BEV all | OIL 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | · | 534 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | · | 534 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | · | 325 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | · | 326 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | · | 49 | |
| `SuppName` | NVARCHAR(200) | 100% | 100% | 100% | · | 49 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | · | 2 | |
| `AgentNum` | NVARCHAR(16) | 95% | — | 99% | · | 481 | |
| `Descr` | NVARCHAR(250) | 100% | 100% | 100% | · | 534 | |
| `Ref1` | NVARCHAR(11) | 2% | 67% | 1% | · | 13 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | · | 1 | |
| `BeforeVat` | DECIMAL | 100% | 100% | 100% | · | 525 | |
| `DocTotal` | DECIMAL | 100% | 100% | 100% | · | 525 | |
| `CostSum` | DECIMAL | 99% | 100% | 99% | · | 508 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | · | 306 | |
| `Canceled` | NVARCHAR(1) | 100% | 100% | 100% | · | 1 | |
| `BeforVatFC` | DECIMAL | 15% | — | 4% | · | 68 | |
| `DocTotalFC` | DECIMAL | 15% | — | 4% | · | 68 | |
| `CostFactor` | DECIMAL | 99% | 100% | 99% | · | 230 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | · | 309 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | · | 1 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | · | 325 | |
| `Series` | INTEGER | 100% | 100% | 100% | · | 23 | |
| `JdtNum` | INTEGER | 100% | 100% | 100% | · | 534 | |
| `JdtMemo` | NVARCHAR(254) | 100% | 100% | 100% | · | 534 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | · | 6 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | · | 1 | |
| `TtlCostSC` | DECIMAL | 99% | 100% | 99% | · | 508 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | · | 2 | |
| `OpenForLaC` | NVARCHAR(1) | 100% | 100% | 100% | · | 2 | |
| `incCustom` | NVARCHAR(1) | 100% | 100% | 100% | · | 2 | |
| `AtcEntry` | INTEGER | 1% | 33% | — | · | 7 | |
| `CustDate` | TIMESTAMP | 100% | 100% | 100% | · | 310 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | · | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | · | 1 | |
| `U_UNE_MLOC` | NVARCHAR(80) | 31% | — | — | · | 156 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`DocStatus`** (2 values) — `O`×532, `C`×2
- **`Ref1`** (14 values) — `NULL`×521, `106`×1, `BD/26-27/97`×1, `111`×1, `CC35`×1, `2361`×1, `104`×1, `00546`×1, `787`×1, `624114136`×1, `0097`×1, `GT/92`×1, `JWPL/TN/1`×1, `42243`×1
- **`DocCur`** (1 values) — `INR`×534
- **`Canceled`** (1 values) — `N`×534
- **`Transfered`** (1 values) — `N`×534
- **`Series`** (23 values) — `746`×46, `2276`×35, `2279`×33, `745`×32, `2282`×32, `2277`×30, `2670`×28, `747`×28, `2281`×27, `2280`×25, `2278`×24, `750`×23, `2671`×21, `2284`×19, `749`×19, `2273`×18, `2275`×18, `2669`×17, `748`×16, `2274`×15, `2668`×11, `2283`×9, `2672`×8
- **`UserSign`** (6 values) — `15`×523, `53`×4, `1`×3, `11`×2, `17`×1, `10`×1
- **`ObjType`** (1 values) — `69`×534
- **`VersionNum`** (2 values) — `10.00.250.15`×373, `10.00.310.21`×161
- **`OpenForLaC`** (2 values) — `Y`×529, `N`×5
- **`incCustom`** (2 values) — `Y`×532, `N`×2
- **`AtcEntry`** (8 values) — `NULL`×527, `125370`×1, `125366`×1, `8994`×1, `42236`×1, `125361`×1, `42221`×1, `7783`×1
- **`BPLId`** (2 values) — `2`×533, `NULL`×1
- **`DPPStatus`** (1 values) — `N`×534
