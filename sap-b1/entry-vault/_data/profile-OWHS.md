# `OWHS` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 58 | 0 | `—` | — |
| MART | 48 | 0 | `—` | — |
| BEV | 44 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `WhsCode` | NVARCHAR(8) | 100% | 100% | 100% | · | · | · | 58 | |
| `WhsName` | NVARCHAR(100) | 100% | 100% | 100% | · | · | · | 58 | |
| `Locked` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | · | · | · | 3 | |
| `Street` | NVARCHAR(100) | 100% | 96% | 100% | · | · | · | 14 | |
| `Block` | NVARCHAR(100) | 90% | 88% | 86% | · | · | · | 12 | |
| `ZipCode` | NVARCHAR(20) | 97% | 96% | 100% | · | · | · | 9 | |
| `City` | NVARCHAR(100) | 95% | 85% | 89% | · | · | · | 6 | |
| `County` | NVARCHAR(100) | 3% | — | — | · | · | · | 1 | |
| `Country` | NVARCHAR(3) | 100% | 96% | 100% | · | · | · | 1 | |
| `State` | NVARCHAR(3) | 100% | 96% | 100% | · | · | · | 4 | |
| `Location` | INTEGER | 100% | 100% | 100% | · | · | · | 5 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `UseTax` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `Building` | NCLOB | — | 2% | — | · | · | · | 0 | |
| `Nettable` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `objType` | NVARCHAR(20) | 100% | 100% | 100% | · | · | · | 1 | |
| `createDate` | TIMESTAMP | 100% | 100% | 100% | · | · | · | 32 | |
| `userSign2` | SMALLINT | 76% | 50% | 57% | · | · | · | 6 | |
| `updateDate` | TIMESTAMP | 100% | 100% | 100% | · | · | · | 32 | |
| `BPLid` | INTEGER | 97% | 67% | 98% | · | · | · | 6 | |
| `OwnerCode` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `AddrType` | NVARCHAR(100) | 7% | 8% | 18% | · | · | · | 3 | |
| `StreetNo` | NVARCHAR(100) | 17% | 12% | 11% | · | · | · | 3 | |
| `Excisable` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `BinActivat` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `BinSeptor` | NVARCHAR(5) | 100% | 100% | 100% | · | · | · | 1 | |
| `DftBinEnfd` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `ManageSnB` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `RecBinEnab` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `RecvEmpBin` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `Inactive` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `RecvMaxQty` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `RecvMaxWT` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `RecvUpTo` | NVARCHAR(6) | 100% | 100% | 100% | · | · | · | 1 | |
| `External` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `U_UNE_SUBC` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `U_UNE_APPR` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `U_UNE_JAPP` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `U_UNE_VRWK` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `U_UNE_REJT` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `U_UNE_RWK` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `U_PriceList` | NVARCHAR(3) | 5% | — | — | · | · | · | 1 | |
| `U_Owner` | SMALLINT | 66% | — | n/a | · | · | n/a | 9 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (1)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_Owner` | OIL, MART | **BEV** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`Locked`** (1 values) — `N`×58
- **`UserSign`** (3 values) — `1`×46, `40`×10, `47`×2
- **`ZipCode`** (10 values) — `131101`×34, `110064`×10, `148029`×4, `141421`×2, `110027`×2, `NULL`×2, `142026`×1, `173101`×1, `124108`×1, `110001`×1
- **`City`** (7 values) — `Sonipat`×34, `New Delhi`×13, `Ludhiana`×4, `NULL`×3, `SANGRUR`×2, `Sirmour`×1, `Jhajjar`×1
- **`County`** (2 values) — `NULL`×56, `148029`×2
- **`Country`** (1 values) — `IN`×58
- **`State`** (4 values) — `HR`×35, `DL`×13, `PB`×9, `HP`×1
- **`Location`** (5 values) — `2`×35, `1`×12, `3`×9, `4`×1, `5`×1
- **`DropShip`** (2 values) — `N`×55, `Y`×3
- **`UseTax`** (1 values) — `N`×58
- **`Nettable`** (2 values) — `Y`×53, `N`×5
- **`objType`** (1 values) — `64`×58
- **`createDate`** (30 values) — `2024-09-20 00:00:00.0000000`×13, `2025-12-16 00:00:00.0000000`×6, `2024-08-27 00:00:00.0000000`×5, `2024-10-21 00:00:00.0000000`×2, `2024-10-05 00:00:00.0000000`×2, `2024-10-08 00:00:00.0000000`×2, `2024-11-14 00:00:00.0000000`×2, `2026-02-10 00:00:00.0000000`×2, `2025-04-29 00:00:00.0000000`×1, `2025-12-12 00:00:00.0000000`×1, `2025-06-30 00:00:00.0000000`×1, `2024-10-25 00:00:00.0000000`×1, `2025-11-18 00:00:00.0000000`×1, `2025-05-09 00:00:00.0000000`×1, `2025-04-04 00:00:00.0000000`×1, `2024-11-25 00:00:00.0000000`×1, `2024-12-23 00:00:00.0000000`×1, `2025-12-24 00:00:00.0000000`×1, `2025-04-05 00:00:00.0000000`×1, `2025-01-22 00:00:00.0000000`×1, `2025-07-09 00:00:00.0000000`×1, `2026-07-22 00:00:00.0000000`×1, `2025-03-12 00:00:00.0000000`×1, `2025-02-14 00:00:00.0000000`×1, `2025-05-13 00:00:00.0000000`×1, `2026-04-04 00:00:00.0000000`×1, `2024-09-25 00:00:00.0000000`×1, `2025-08-04 00:00:00.0000000`×1, `2024-10-16 00:00:00.0000000`×1, `2025-04-28 00:00:00.0000000`×1
- **`userSign2`** (7 values) — `1`×16, `NULL`×14, `40`×13, `47`×11, `38`×2, `56`×1, `20`×1
- **`updateDate`** (30 values) — `2025-12-08 00:00:00.0000000`×11, `2025-08-28 00:00:00.0000000`×7, `2025-12-16 00:00:00.0000000`×6, `2025-09-11 00:00:00.0000000`×4, `2024-11-06 00:00:00.0000000`×3, `2025-04-29 00:00:00.0000000`×1, `2026-02-28 00:00:00.0000000`×1, `2026-02-10 00:00:00.0000000`×1, `2025-11-11 00:00:00.0000000`×1, `2025-12-24 00:00:00.0000000`×1, `2026-08-06 00:00:00.0000000`×1, `2026-03-25 00:00:00.0000000`×1, `2025-05-09 00:00:00.0000000`×1, `2025-11-18 00:00:00.0000000`×1, `2024-11-14 00:00:00.0000000`×1, `2026-07-11 00:00:00.0000000`×1, `2026-07-22 00:00:00.0000000`×1, `2026-01-02 00:00:00.0000000`×1, `2024-11-25 00:00:00.0000000`×1, `2025-12-12 00:00:00.0000000`×1, `2026-05-02 00:00:00.0000000`×1, `2026-04-13 00:00:00.0000000`×1, `2026-05-26 00:00:00.0000000`×1, `2026-07-27 00:00:00.0000000`×1, `2024-11-29 00:00:00.0000000`×1, `2026-01-29 00:00:00.0000000`×1, `2024-10-23 00:00:00.0000000`×1, `2024-10-21 00:00:00.0000000`×1, `2026-02-12 00:00:00.0000000`×1, `2025-01-13 00:00:00.0000000`×1
- **`BPLid`** (7 values) — `2`×33, `1`×11, `3`×9, `NULL`×2, `5`×1, `6`×1, `4`×1
- **`OwnerCode`** (1 values) — `1`×58
- **`AddrType`** (4 values) — `NULL`×54, `Old Grain Market`×2, `Unit No A Building B-750`×1, `BXIX-1233 Back Side Anubarat School`×1
- **`Excisable`** (1 values) — `N`×58
- **`BinActivat`** (1 values) — `N`×58
- **`BinSeptor`** (1 values) — `-`×58
- **`DftBinEnfd`** (1 values) — `N`×58
- **`ManageSnB`** (1 values) — `N`×58
- **`RecBinEnab`** (1 values) — `N`×58
- **`RecvEmpBin`** (1 values) — `Y`×58
- **`Inactive`** (2 values) — `N`×46, `Y`×12
- **`RecvMaxQty`** (1 values) — `N`×58
- **`RecvMaxWT`** (1 values) — `N`×58
- **`RecvUpTo`** (1 values) — `0`×58
- **`External`** (1 values) — `N`×58
- **`U_UNE_SUBC`** (1 values) — `N`×58
- **`U_UNE_APPR`** (1 values) — `N`×58
- **`U_UNE_JAPP`** (1 values) — `N`×58
- **`U_UNE_VRWK`** (1 values) — `N`×58
- **`U_UNE_REJT`** (1 values) — `N`×58
- **`U_UNE_RWK`** (1 values) — `N`×58
- **`U_PriceList`** (2 values) — `NULL`×55, `3`×3
- **`U_Owner`** (10 values) — `NULL`×20, `35`×10, `33`×7, `22`×7, `37`×6, `36`×4, `27`×1, `20`×1, `15`×1, `10`×1
