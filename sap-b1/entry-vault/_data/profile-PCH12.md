# `PCH12` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 16,334 | 0 | `—` | — |
| MART | 4,864 | 0 | `—` | — |
| BEV | 3,170 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | · | · | · | 16,334 | |
| `TaxId0` | NVARCHAR(100) | 53% | 80% | 39% | · | · | · | 700 | |
| `TaxId6` | NVARCHAR(100) | 4% | 3% | 5% | · | · | · | 127 | |
| `State` | NVARCHAR(3) | 99% | 100% | 100% | · | · | · | 31 | |
| `NfRef` | NVARCHAR(254) | 46% | 63% | 51% | · | · | · | 7,435 | |
| `ObjectType` | NVARCHAR(20) | 100% | 100% | 100% | · | · | · | 1 | |
| `TransCat` | NVARCHAR(100) | <1% | <1% | <1% | · | · | · | 1 | |
| `FormNo` | NVARCHAR(100) | <1% | — | — | · | · | · | 3 | |
| `TaxId11` | NVARCHAR(100) | <1% | <1% | — | · | · | · | 2 | |
| `StreetS` | NVARCHAR(100) | 41% | 56% | 40% | · | · | · | 11 | |
| `BlockS` | NVARCHAR(100) | 41% | 56% | 39% | · | · | · | 11 | |
| `BuildingS` | NCLOB | — | <1% | — | · | · | · | 0 | |
| `CityS` | NVARCHAR(100) | 41% | 55% | 40% | · | · | · | 7 | |
| `ZipCodeS` | NVARCHAR(20) | 65% | 91% | 40% | · | · | · | 8 | |
| `CountyS` | NVARCHAR(100) | <1% | — | — | · | · | · | 1 | |
| `StateS` | NVARCHAR(3) | 100% | 93% | 99% | · | · | · | 4 | |
| `CountryS` | NVARCHAR(3) | 100% | 93% | 99% | · | · | · | 1 | |
| `AddrTypeS` | NVARCHAR(100) | 7% | 10% | 19% | · | · | · | 4 | |
| `StreetNoS` | NVARCHAR(100) | 12% | 10% | 19% | · | · | · | 4 | |
| `StreetB` | NVARCHAR(100) | 59% | 75% | 52% | · | · | · | 777 | |
| `BlockB` | NVARCHAR(100) | 37% | 72% | 47% | · | · | · | 649 | |
| `BuildingB` | NCLOB | 2% | — | <1% | · | · | · | 0 | |
| `CityB` | NVARCHAR(100) | 90% | 48% | 95% | · | · | · | 207 | |
| `ZipCodeB` | NVARCHAR(20) | 84% | 92% | 80% | · | · | · | 404 | |
| `CountyB` | NVARCHAR(100) | <1% | <1% | <1% | · | · | · | 4 | |
| `StateB` | NVARCHAR(3) | 99% | 93% | 100% | · | · | · | 31 | |
| `CountryB` | NVARCHAR(3) | 100% | 93% | 100% | · | · | · | 11 | |
| `StreetNoB` | NVARCHAR(100) | <1% | — | — | · | · | · | 1 | |
| `ImpORExp` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `Vat` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `Address2B` | NVARCHAR(50) | 46% | 21% | 36% | · | · | · | 450 | |
| `Address3B` | NVARCHAR(50) | 32% | 17% | 22% | · | · | · | 235 | |
| `TaxId12` | NVARCHAR(50) | 52% | 25% | 54% | · | · | · | 461 | |
| `BpGSTType` | INTEGER | 70% | 91% | 53% | · | · | · | 1 | |
| `BpGSTN` | NVARCHAR(15) | 70% | 91% | 53% | · | · | · | 854 | |
| `BpStateCod` | NVARCHAR(3) | 99% | 100% | 100% | · | · | · | 30 | |
| `BPStatGSTN` | NVARCHAR(2) | 99% | 99% | 100% | · | · | · | 24 | |
| `LocGSTType` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `LocGSTN` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 5 | |
| `LocStatCod` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 6 | |
| `LocStaGSTN` | NVARCHAR(2) | 100% | 100% | 100% | · | · | · | 6 | |
| `BpCountry` | NVARCHAR(3) | 100% | 100% | 100% | · | · | · | 11 | |
| `ExportType` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `IsIGSTAct` | NVARCHAR(1) | 99% | 99% | 99% | · | · | · | 2 | |
| `ClaimRefun` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `TaxRateDif` | INTEGER | 99% | 99% | 99% | · | · | · | 1 | |
| `TaxId14` | NVARCHAR(250) | 38% | 71% | 20% | · | · | · | 7 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`ObjectType`** (1 values) — `18`×16,334
- **`TransCat`** (2 values) — `NULL`×16,330, `Form F`×4
- **`FormNo`** (4 values) — `NULL`×16,327, `.67`×5, `1`×1, `.38`×1
- **`TaxId11`** (3 values) — `NULL`×16,330, `NA`×3, `Y`×1
- **`CityS`** (8 values) — `NULL`×9,644, `Sonipat`×5,618, `New Delhi`×578, `Ludhiana`×304, `Ludhiana Punjab India`×70, `SANGRUR`×61, `SANGRUR PUNJAB INDIA`×48, `Jhajjar`×11
- **`ZipCodeS`** (9 values) — `131101`×9,528, `NULL`×5,761, `110064`×550, `141421`×316, `148029`×83, `142026`×57, `110001`×19, `124108`×11, `110027`×9
- **`CountyS`** (2 values) — `NULL`×16,225, `148029`×109
- **`StateS`** (5 values) — `HR`×11,035, `DL`×4,596, `PB`×640, `NULL`×55, `HP`×8
- **`CountryS`** (2 values) — `IN`×16,279, `NULL`×55
- **`AddrTypeS`** (5 values) — `NULL`×15,264, `Jivo Wellness Pvt. Ltd.`×934, `Old Grain Market`×68, `BXIX-1233 Back Side Anubarat School`×57, `Unit No A, Building B-750`×11
- **`CountyB`** (5 values) — `NULL`×16,190, `India`×119, `INDIA`×18, `110077`×6, `110058`×1
- **`CountryB`** (12 values) — `IN`×16,164, `US`×62, `AE`×45, `ES`×21, `AU`×19, `CA`×9, `EG`×9, `GB`×1, `SG`×1, `IE`×1, `SW`×1, `NULL`×1
- **`StreetNoB`** (2 values) — `NULL`×16,333, `B-408 KHASRA NO. 13/23`×1
- **`ImpORExp`** (2 values) — `N`×16,165, `Y`×169
- **`Vat`** (1 values) — `N`×16,334
- **`BpGSTType`** (2 values) — `1`×11,404, `NULL`×4,930
- **`BpStateCod`** (30 values) — `HR`×6,755, `DL`×5,439, `GJ`×1,085, `PB`×721, `UP`×596, `UK`×440, `RJ`×395, `MH`×250, `HP`×166, `NULL`×111, `WB`×75, `TN`×33, `JK`×31, `CH`×30, `CA`×30, `KT`×26, `MP`×23, `TE`×23, `KR`×22, `WA`×14, `AUS`×12, `AS`×11, `TO`×9, `BH`×8, `AP`×7, `JH`×7, `NSW`×6, `GO`×4, `AZ`×3, `DN`×1
- **`BPStatGSTN`** (25 values) — `06`×6,755, `07`×5,439, `24`×1,085, `03`×721, `09`×596, `05`×440, `08`×395, `27`×250, `NULL`×185, `02`×166, `19`×75, `33`×33, `01`×31, `04`×30, `29`×26, `36`×23, `23`×23, `32`×22, `18`×11, `10`×8, `20`×7, `37`×7, `30`×4, `26`×1, `22`×1
- **`LocGSTType`** (1 values) — `1`×16,334
- **`LocGSTN`** (5 values) — `06AACCJ4223F1Z0`×11,054, `07AACCJ4223F1ZY`×4,235, `03AACCJ4223F1Z6`×640, `07AACCJ4223F2ZX`×396, `02AACCJ4223F1Z8`×9
- **`LocStatCod`** (7 values) — `HR`×11,038, `DL`×4,642, `PB`×640, `HP`×9, `NULL`×3, `GJ`×1, `UP`×1
- **`LocStaGSTN`** (7 values) — `06`×11,038, `07`×4,642, `03`×640, `02`×9, `NULL`×3, `24`×1, `09`×1
- **`BpCountry`** (12 values) — `IN`×16,149, `US`×61, `AE`×45, `ES`×21, `AU`×18, `NULL`×18, `EG`×9, `CA`×9, `SG`×1, `GB`×1, `SW`×1, `IE`×1
- **`ExportType`** (1 values) — `E`×16,334
- **`IsIGSTAct`** (3 values) — `Y`×11,670, `N`×4,492, `NULL`×172
- **`ClaimRefun`** (1 values) — `N`×16,334
- **`TaxRateDif`** (2 values) — `100`×16,162, `NULL`×172
- **`TaxId14`** (8 values) — `NULL`×10,048, `Y`×6,141, `∅`×86, `y`×53, `NA`×3, `YES`×1, `AAOCS0564L`×1, `Yes`×1
