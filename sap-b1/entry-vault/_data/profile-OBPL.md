# `OBPL` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 8 | 0 | `—` | — |
| MART | 20 | 0 | `—` | — |
| BEV | 6 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `BPLId` | INTEGER | 100% | 100% | 100% | · | · | · | 8 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | · | · | · | 8 | |
| `BPLFrName` | NVARCHAR(200) | 100% | 100% | 100% | · | · | · | 8 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | · | · | · | 2 | |
| `AddressFr` | NVARCHAR(254) | 12% | 5% | 17% | · | · | · | 1 | |
| `MainBPL` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `Disabled` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `DflWhs` | NVARCHAR(8) | 100% | 100% | 100% | · | · | · | 8 | |
| `TaxIdNum` | NVARCHAR(32) | 100% | 100% | 100% | · | · | · | 5 | |
| `CompNature` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `EconActT` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `CoopAssocT` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `ProfTax` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `CompQualif` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `DeclType` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `ZipCode` | NVARCHAR(20) | 25% | 55% | — | · | · | · | 1 | |
| `State` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 4 | |
| `Country` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 1 | |
| `PmtClrAct` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 1 | |
| `EnvTypeNFe` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `Opt4ICMS` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `DfltResWhs` | NVARCHAR(8) | 100% | 100% | 100% | · | · | · | 8 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`BPLId`** (8 values) — `7`×1, `5`×1, `6`×1, `4`×1, `8`×1, `1`×1, `3`×1, `2`×1
- **`BPLName`** (8 values) — `HIMACHAL PRADESH`×1, `FACTORY`×1, `HARYANA INFO`×1, `DELHI INFO`×1, `HARYANA SALES`×1, `DELHI ISD`×1, `DELHI`×1, `PUNJAB`×1
- **`BPLFrName`** (8 values) — `DELHI ISD`×1, `HARYANA INFO`×1, `FACTORY`×1, `HIMACHAL PRADESH`×1, `DELHI INFO`×1, `HARYANA SALES`×1, `DELHI`×1, `PUNJAB`×1
- **`Address`** (2 values) — `- IN`×6, `-131101 IN`×2
- **`AddressFr`** (2 values) — `NULL`×7, `- IN`×1
- **`MainBPL`** (2 values) — `N`×7, `Y`×1
- **`Disabled`** (1 values) — `N`×8
- **`DflWhs`** (8 values) — `HP-FG`×1, `HR`×1, `BH-FG`×1, `DL-FG`×1, `PB-FG`×1, `DL`×1, `DL-ISD`×1, `01`×1
- **`TaxIdNum`** (5 values) — `06AACCJ4223F1Z0`×3, `07AACCJ4223F1ZY`×2, `07AACCJ4223F2ZX`×1, `02AACCJ4223F1Z8`×1, `03AACCJ4223F1Z6`×1
- **`CompNature`** (1 values) — `-1`×8
- **`EconActT`** (1 values) — `-1`×8
- **`CoopAssocT`** (1 values) — `-1`×8
- **`ProfTax`** (1 values) — `-1`×8
- **`CompQualif`** (1 values) — `-1`×8
- **`DeclType`** (1 values) — `-1`×8
- **`ZipCode`** (2 values) — `NULL`×6, `131101`×2
- **`State`** (4 values) — `HR`×3, `DL`×3, `HP`×1, `PB`×1
- **`Country`** (1 values) — `IN`×8
- **`PmtClrAct`** (1 values) — `1110301`×8
- **`EnvTypeNFe`** (1 values) — `-1`×8
- **`Opt4ICMS`** (1 values) — `N`×8
- **`DfltResWhs`** (8 values) — `HR`×1, `BH-FG`×1, `DL-FG`×1, `PB-FG`×1, `DL`×1, `DL-ISD`×1, `01`×1, `HP-FG`×1
