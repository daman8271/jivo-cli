# `INV12` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 31,084 | 0 | `—` | — |
| MART | 25,752 | 0 | `—` | — |
| BEV | 5,590 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | · | · | · | 31,084 | |
| `TaxId0` | NVARCHAR(100) | 38% | 16% | 43% | · | · | · | 298 | |
| `TaxId6` | NVARCHAR(100) | <1% | 1% | <1% | · | · | · | 5 | |
| `State` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 38 | |
| `NfRef` | NVARCHAR(254) | 59% | 97% | 94% | · | · | · | 12,356 | |
| `ObjectType` | NVARCHAR(20) | 100% | 100% | 100% | · | · | · | 1 | |
| `TransCat` | NVARCHAR(100) | <1% | <1% | <1% | · | · | · | 1 | |
| `StreetS` | NVARCHAR(100) | 47% | 29% | 70% | · | · | · | 486 | |
| `BlockS` | NVARCHAR(100) | 25% | 23% | 61% | · | · | · | 375 | |
| `BuildingS` | NCLOB | <1% | — | <1% | · | · | · | 0 | |
| `CityS` | NVARCHAR(100) | 76% | 87% | 99% | · | · | · | 190 | |
| `ZipCodeS` | NVARCHAR(20) | 73% | 98% | 100% | · | · | · | 456 | |
| `CountyS` | NVARCHAR(100) | <1% | <1% | <1% | · | · | · | 2 | |
| `StateS` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 38 | |
| `CountryS` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 4 | |
| `StreetNoS` | NVARCHAR(100) | <1% | — | — | · | · | · | 9 | |
| `StreetB` | NVARCHAR(100) | 46% | 29% | 71% | · | · | · | 430 | |
| `BlockB` | NVARCHAR(100) | 26% | 23% | 62% | · | · | · | 333 | |
| `BuildingB` | NCLOB | 2% | — | <1% | · | · | · | 0 | |
| `CityB` | NVARCHAR(100) | 76% | 87% | 99% | · | · | · | 174 | |
| `ZipCodeB` | NVARCHAR(20) | 73% | 98% | 98% | · | · | · | 420 | |
| `CountyB` | NVARCHAR(100) | <1% | <1% | — | · | · | · | 1 | |
| `StateB` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 37 | |
| `CountryB` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 3 | |
| `StreetNoB` | NVARCHAR(100) | <1% | — | <1% | · | · | · | 7 | |
| `ImpORExp` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `Vat` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `Address2S` | NVARCHAR(50) | 42% | 34% | 25% | · | · | · | 491 | |
| `Address3S` | NVARCHAR(50) | 34% | 19% | 17% | · | · | · | 338 | |
| `Address2B` | NVARCHAR(50) | 40% | 35% | 26% | · | · | · | 449 | |
| `Address3B` | NVARCHAR(50) | 33% | 20% | 17% | · | · | · | 305 | |
| `TaxId12` | NVARCHAR(50) | 56% | 27% | 28% | · | · | · | 396 | |
| `BpGSTType` | INTEGER | 57% | 31% | 59% | · | · | · | 1 | |
| `BpGSTN` | NVARCHAR(15) | 57% | 31% | 59% | · | · | · | 549 | |
| `BpStateCod` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 35 | |
| `BPStatGSTN` | NVARCHAR(2) | 100% | 100% | 100% | · | · | · | 35 | |
| `LocGSTType` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `LocGSTN` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 3 | |
| `LocStatCod` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 3 | |
| `LocStaGSTN` | NVARCHAR(2) | 100% | 100% | 100% | · | · | · | 3 | |
| `BpCountry` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 3 | |
| `ExportType` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `IsIGSTAct` | NVARCHAR(1) | 99% | 100% | 99% | · | · | · | 2 | |
| `ClaimRefun` | NVARCHAR(1) | 99% | 100% | 99% | · | · | · | 1 | |
| `TaxRateDif` | INTEGER | 99% | 100% | 99% | · | · | · | 1 | |
| `TaxId14` | NVARCHAR(250) | <1% | 7% | <1% | · | · | · | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TaxId6`** (6 values) — `NULL`×31,052, `DELA74854D`×27, `∅`×2, `JLDF00202G`×1, `10020041002507`×1, `MUMII5988A`×1
- **`ObjectType`** (1 values) — `13`×31,084
- **`TransCat`** (2 values) — `NULL`×31,080, `Form F`×4
- **`CountyS`** (3 values) — `NULL`×31,081, `∅`×2, `INDIA`×1
- **`CountryS`** (5 values) — `IN`×30,981, `NULL`×81, `AE`×16, `QA`×4, `∅`×2
- **`StreetNoS`** (10 values) — `NULL`×30,906, `S NO 402/2B1`×144, `54/5A STRAND ROAD`×10, `UPSIDC`×9, `P O : KIIT CAMPUS`×8, `THEING ROAD PHILLAUR`×2, `∅`×2, `PASCHIM VIHAR`×1, `B 8 VISHAL ENCLAVE`×1, `INDUSTRIAL AREA`×1
- **`CountyB`** (2 values) — `NULL`×31,083, `INDIA`×1
- **`CountryB`** (4 values) — `IN`×30,987, `NULL`×77, `AE`×16, `QA`×4
- **`StreetNoB`** (8 values) — `NULL`×31,045, `P O : KIIT CAMPUS`×15, `54/5A STRAND ROAD`×10, `UPSIDC`×9, `THEING ROAD PHILLAUR`×2, `PASCHIM VIHAR`×1, `B 8 VISHAL ENCLAVE`×1, `INDUSTRIAL AREA`×1
- **`ImpORExp`** (2 values) — `N`×31,064, `Y`×20
- **`Vat`** (1 values) — `N`×31,084
- **`BpGSTType`** (2 values) — `1`×17,715, `NULL`×13,369
- **`LocGSTType`** (1 values) — `1`×31,084
- **`LocGSTN`** (3 values) — `06AACCJ4223F1Z0`×15,014, `07AACCJ4223F1ZY`×13,474, `03AACCJ4223F1Z6`×2,596
- **`LocStatCod`** (3 values) — `HR`×15,014, `DL`×13,474, `PB`×2,596
- **`LocStaGSTN`** (3 values) — `06`×15,014, `07`×13,474, `03`×2,596
- **`BpCountry`** (4 values) — `IN`×30,990, `NULL`×76, `AE`×14, `QA`×4
- **`ExportType`** (1 values) — `E`×31,084
- **`IsIGSTAct`** (3 values) — `Y`×19,803, `N`×11,086, `NULL`×195
- **`ClaimRefun`** (2 values) — `N`×30,887, `NULL`×197
- **`TaxRateDif`** (2 values) — `100`×30,886, `NULL`×198
- **`TaxId14`** (2 values) — `NULL`×30,983, `Y`×101
