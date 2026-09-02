# `OCTG` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 29 | 0 | `CreateDate` | NULL → NULL |
| MART | 28 | 0 | `CreateDate` | NULL → NULL |
| BEV | 28 | 0 | `CreateDate` | NULL → NULL |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `GroupNum` | SMALLINT | 100% | 100% | 100% | · | · | · | 29 | |
| `PymntGroup` | NVARCHAR(100) | 100% | 100% | 100% | · | · | · | 29 | |
| `PayDuMonth` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `ExtraDays` | SMALLINT | 66% | 68% | 68% | · | · | · | 17 | |
| `ListNum` | SMALLINT | 100% | 100% | 100% | · | · | · | 1 | |
| `Payments` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `NumOfPmnts` | SMALLINT | 100% | 100% | 100% | · | · | · | 1 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | · | · | · | 2 | |
| `OpenRcpt` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `BslineDate` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `CrdMthd` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `CshRelev` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`GroupNum`** (29 values) — `19`×1, `21`×1, `7`×1, `26`×1, `-1`×1, `15`×1, `6`×1, `29`×1, `10`×1, `28`×1, `4`×1, `5`×1, `8`×1, `22`×1, `25`×1, `24`×1, `13`×1, `20`×1, `9`×1, `27`×1, `1`×1, `18`×1, `23`×1, `3`×1, `17`×1, `12`×1, `14`×1, `11`×1, `16`×1
- **`PymntGroup`** (29 values) — `NET-02`×1, `NET-45`×1, `COD`×1, `30 % ADV`×1, `NET-07`×1, `LC 90`×1, `ADVANCE/CASH/0 DAYS`×1, `NET-05`×1, `NET-10`×1, `CAD`×1, `NET-35`×1, `NET-25`×1, `25 % ADV & 75 % ON DISPATCH`×1, `NET-90`×1, `NET-60`×1, `NET-30`×1, `30 % ADV & 90 % ON DISPATCH`×1, `20% ADVANCE`×1, `PDC-15`×1, `45 % ADV`×1, `NET-21`×1, `LC 60`×1, `NET-15`×1, `AS CONVERSED ON MAIL`×1, `NET-01`×1, `NET-03`×1, `NET-40`×1, `50 % ADV`×1, `NET-42`×1
- **`PayDuMonth`** (1 values) — `N`×29
- **`ExtraDays`** (17 values) — `0`×10, `60`×2, `90`×2, `15`×2, `42`×1, `2`×1, `3`×1, `1`×1, `30`×1, `7`×1, `45`×1, `25`×1, `35`×1, `21`×1, `40`×1, `10`×1, `5`×1
- **`ListNum`** (1 values) — `1`×29
- **`Payments`** (1 values) — `N`×29
- **`NumOfPmnts`** (1 values) — `1`×29
- **`UserSign`** (2 values) — `1`×28, `39`×1
- **`OpenRcpt`** (1 values) — `N`×29
- **`BslineDate`** (2 values) — `T`×21, `P`×8
- **`VATFirst`** (1 values) — `N`×29
- **`CrdMthd`** (1 values) — `L`×29
- **`CshRelev`** (1 values) — `N`×29
- **`PDueMonEnd`** (1 values) — `N`×29
