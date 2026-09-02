# `IGE1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 53,206 | 9,976 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 750 | 40 | `DocDate` | 2025-03-31 → 2026-08-11 |
| BEV | 6,809 | 1,151 | `DocDate` | 2024-09-30 → 2026-08-22 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 8,422 | |
| `LineNum` | INTEGER | 84% | 90% | 79% | 82% | 48% | 78% | 352 | |
| `TargetType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `TrgetEntry` | INTEGER | <1% | — | — | — | — | — | 1 | |
| `BaseRef` | NVARCHAR(16) | 94% | 5% | 98% | 100% | 70% | 100% | 8,228 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseEntry` | INTEGER | 94% | 5% | 98% | 100% | 70% | 100% | 8,227 | |
| `BaseLine` | INTEGER | 79% | 1% | 78% | 82% | 20% | 78% | 20 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItemCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 1,034 | |
| `Dscription` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 1,060 | |
| `Quantity` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 10,463 | |
| `ShipDate` | TIMESTAMP | 94% | 5% | 98% | 100% | 70% | 100% | 614 | |
| `OpenQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 10,464 | |
| `Price` | DECIMAL | 16% | 94% | 2% | 13% | 30% | <1% | 1,041 | |
| `Currency` | NVARCHAR(3) | 83% | 95% | 99% | 79% | 30% | 98% | 2 | |
| `Rate` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `DiscPrcnt` | DECIMAL | 1% | — | <1% | — | — | — | 11 | |
| `LineTotal` | DECIMAL | 83% | 95% | 99% | 79% | 30% | 98% | 29,124 | |
| `OpenSum` | DECIMAL | 83% | 95% | 99% | 79% | 30% | 98% | 29,124 | |
| `WhsCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 31 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `PriceBefDi` | DECIMAL | 17% | 94% | 2% | 13% | 30% | <1% | 1,110 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 624 | |
| `OpenCreQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 10,464 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TotalSumSy` | DECIMAL | 83% | 95% | 99% | 79% | 30% | 98% | 29,124 | |
| `OpenSumSys` | DECIMAL | 83% | 95% | 99% | 79% | 30% | 98% | 29,124 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `OcrCode` | NVARCHAR(8) | 72% | 9% | 2% | 100% | 5% | 2% | 36 | |
| `Factor1` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 17 | |
| `Factor3` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `Factor4` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 16 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VisOrder` | INTEGER | 84% | 90% | 79% | 82% | 48% | 78% | 352 | |
| `INMPrice` | DECIMAL | 83% | 95% | 99% | 79% | 30% | 98% | 4,242 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxType` | NVARCHAR(1) | <1% | — | <1% | — | — | — | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TrnsCode` | SMALLINT | <1% | <1% | <1% | — | — | — | 1 | |
| `BaseOpnQty` | DECIMAL | 94% | 5% | 98% | 100% | 70% | 100% | 10,122 | |
| `WtLiable` | NVARCHAR(1) | <1% | — | <1% | — | — | — | 1 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `unitMsr` | NVARCHAR(100) | 80% | 98% | 82% | 87% | 100% | 100% | 9 | |
| `NumPerMsr` | DECIMAL | 89% | 100% | 100% | 87% | 100% | 100% | 2 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `StockPrice` | DECIMAL | 97% | 93% | 99% | 98% | 100% | 99% | 7,526 | |
| `StockSum` | DECIMAL | 71% | 95% | 99% | 66% | 30% | 98% | 26,432 | |
| `StockSumSc` | DECIMAL | 71% | 95% | 99% | 66% | 30% | 98% | 26,432 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxOnly` | NVARCHAR(1) | <1% | — | <1% | — | — | — | 1 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OcrCode2` | NVARCHAR(8) | <1% | — | <1% | <1% | — | <1% | 15 | |
| `OcrCode3` | NVARCHAR(8) | <1% | — | <1% | <1% | — | <1% | 2 | |
| `OcrCode5` | NVARCHAR(8) | <1% | — | — | <1% | — | — | 2 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excisable` | NVARCHAR(1) | <1% | — | <1% | — | — | — | 1 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `unitMsr2` | NVARCHAR(100) | 88% | 100% | 100% | 87% | 100% | 100% | 10 | |
| `NumPerMsr2` | DECIMAL | 89% | 100% | 100% | 87% | 100% | 100% | 3 | |
| `SpecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `isSrvCall` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcDocType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatGrpSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NoInvtryMv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UomEntry` | INTEGER | 89% | 100% | 100% | 87% | 100% | 100% | 3 | |
| `UomEntry2` | INTEGER | 89% | 100% | 100% | 87% | 100% | 100% | 4 | |
| `UomCode` | NVARCHAR(20) | 89% | 100% | 100% | 87% | 100% | 100% | 2 | |
| `UomCode2` | NVARCHAR(20) | 89% | 100% | 100% | 87% | 100% | 100% | 4 | |
| `NeedQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartRetire` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQty` | DECIMAL | 89% | 100% | 100% | 87% | 100% | 100% | 9,949 | |
| `OpenInvQty` | DECIMAL | 89% | 100% | 100% | 87% | 100% | 100% | 9,949 | |
| `EnSetCost` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DistribIS` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsByPrdct` | NVARCHAR(1) | 94% | 5% | 98% | 100% | 70% | 100% | 1 | |
| `ItemType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PriceEdit` | NVARCHAR(1) | 94% | 5% | 99% | 100% | 70% | 100% | 2 | |
| `LinePoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FreeChrgBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxRelev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ThirdParty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQtyOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ItmTaxType` | NVARCHAR(2) | <1% | — | <1% | — | — | — | 1 | |
| `NCMCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `HsnEntry` | INTEGER | 89% | 100% | 99% | 87% | 100% | 100% | 119 | |
| `IsPrscGood` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IndEscala` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ListNum` | SMALLINT | <1% | — | — | — | — | — | 1 | |
| `UoMNum` | DECIMAL | 89% | 100% | 100% | 87% | 100% | 100% | 2 | |
| `UoMDen` | DECIMAL | 95% | 100% | 100% | 87% | 100% | 100% | 2 | |
| `UoMNum2` | DECIMAL | 89% | 100% | 100% | 87% | 100% | 100% | 3 | |
| `UoMDen2` | DECIMAL | 95% | 100% | 100% | 87% | 100% | 100% | 2 | |
| `U_SchemeAgst` | NVARCHAR(50) | 73% | 29% | 1% | 100% | — | 1% | 35 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_F_Year` | NVARCHAR(10) | <1% | — | <1% | — | — | — | 1 | |
| `U_PRCHSE_VAL` | DECIMAL | <1% | — | <1% | — | — | — | 2 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BiltyDate` | OIL, BEV | **MART** |
| `U_UNE_CALI` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TargetType`** (2 values) — `-1`×53,200, `59`×6
- **`TrgetEntry`** (2 values) — `NULL`×53,200, `2749`×6
- **`BaseType`** (2 values) — `202`×50,182, `-1`×3,024
- **`BaseLine`** (21 values) — `0`×7,687, `1`×6,514, `2`×6,095, `3`×5,981, `4`×5,892, `5`×5,062, `6`×4,806, `7`×4,107, `NULL`×3,532, `8`×1,758, `9`×808, `10`×284, `11`×221, `12`×122, `13`×120, `14`×112, `15`×87, `17`×6, `18`×4, `19`×4, `16`×4
- **`LineStatus`** (2 values) — `O`×53,200, `C`×6
- **`Currency`** (2 values) — `INR`×44,029, `∅`×9,177
- **`Rate`** (3 values) — `0.000000`×50,182, `NULL`×3,023, `85.000000`×1
- **`DiscPrcnt`** (12 values) — `0.000000`×52,661, `100.000000`×535, `-14.710000`×1, `-4.270000`×1, `-0.480000`×1, `-42.860000`×1, `99.900000`×1, `-13026.610000`×1, `NULL`×1, `-7.720000`×1, `-17.740000`×1, `47.110000`×1
- **`SlpCode`** (1 values) — `-1`×53,206
- **`TreeType`** (2 values) — `N`×53,205, `P`×1
- **`AcctCode`** (12 values) — `1103009`×50,182, `1103013`×1,529, `5100013`×1,073, `5100017`×386, `3200003`×13, `5100003`×12, `5680031`×3, `5000002`×2, `1103005`×2, `1208001`×2, `5680012`×1, `5300015`×1
- **`UseBaseUn`** (1 values) — `Y`×53,206
- **`InvntSttus`** (2 values) — `O`×53,200, `C`×6
- **`Factor1`** (1 values) — `1.000000`×53,206
- **`Factor2`** (17 values) — `1.000000`×52,185, `16.000000`×250, `20.000000`×241, `4.000000`×198, `8.000000`×86, `12.000000`×71, `10.000000`×57, `3.000000`×36, `5.000000`×33, `24.000000`×20, `6.000000`×10, `15.000000`×7, `40.000000`×4, `2.000000`×3, `70.000000`×2, `9.000000`×2, `36.000000`×1
- **`Factor3`** (4 values) — `1.000000`×53,169, `20.000000`×15, `10.000000`×11, `4.000000`×11
- **`Factor4`** (16 values) — `1.000000`×53,124, `1350.000000`×15, `275.000000`×14, `255.000000`×7, `45.000000`×7, `1250.000000`×7, `150.000000`×6, `245.000000`×5, `350.000000`×5, `490.000000`×3, `375.000000`×3, `1650.000000`×3, `1225.000000`×3, `700.000000`×2, `153.000000`×1, `120.000000`×1
- **`UpdInvntry`** (1 values) — `Y`×53,206
- **`FinncPriod`** (24 values) — `10`×3,147, `18`×2,840, `44`×2,653, `9`×2,634, `16`×2,592, `23`×2,589, `11`×2,584, `42`×2,530, `7`×2,438, `43`×2,384, `12`×2,344, `41`×2,271, `22`×2,243, `14`×2,226, `24`×2,220, `17`×2,180, `15`×2,073, `21`×2,072, `45`×1,995, `25`×1,867, `19`×1,835, `20`×1,755, `8`×1,729, `6`×5
- **`ObjType`** (1 values) — `60`×53,206
- **`IsAqcuistn`** (1 values) — `N`×53,206
- **`DropShip`** (1 values) — `N`×53,206
- **`TaxType`** (2 values) — `NULL`×53,201, `Y`×5
- **`PickStatus`** (1 values) — `N`×53,206
- **`TrnsCode`** (2 values) — `NULL`×53,202, `-1`×4
- **`WtLiable`** (2 values) — `NULL`×53,201, `N`×5
- **`DeferrTax`** (1 values) — `N`×53,206
- **`unitMsr`** (10 values) — `PCS`×28,159, `NULL`×10,670, `LTR`×7,784, `MTR`×5,774, `KGS`×755, `∅`×24, `NOS`×22, `GMS`×11, `DRM`×4, `SET`×3
- **`NumPerMsr`** (2 values) — `1.000000`×47,195, `0.000000`×6,011
- **`CEECFlag`** (1 values) — `S`×53,206
- **`LineType`** (2 values) — `R`×47,195, `M`×6,011
- **`BasePrice`** (1 values) — `E`×53,206
- **`DescOW`** (1 values) — `N`×53,206
- **`DetailsOW`** (1 values) — `N`×53,206
- **`TaxOnly`** (2 values) — `NULL`×53,201, `N`×5
- **`WtCalced`** (1 values) — `N`×53,206
- **`CiOppLineN`** (1 values) — `-1`×53,206
- **`OcrCode2`** (16 values) — `∅`×52,657, `NULL`×488, `02-2026`×11, `08-2025`×10, `11-2025`×8, `12-2025`×8, `09-2025`×7, `07-2024`×4, `01-2026`×3, `06-2026`×3, `03-2026`×2, `06-2024`×1, `01-2025`×1, `12-2024`×1, `07-2026`×1, `06-2025`×1
- **`OcrCode3`** (3 values) — `∅`×53,154, `Factory`×29, `NULL`×23
- **`OcrCode5`** (3 values) — `∅`×53,184, `HR`×16, `NULL`×6
- **`PostTax`** (1 values) — `Y`×53,206
- **`Excisable`** (2 values) — `NULL`×53,201, `N`×5
- **`LocCode`** (3 values) — `2`×52,100, `1`×966, `3`×140
- **`unitMsr2`** (11 values) — `PCS`×32,433, `LTR`×7,813, `NULL`×6,065, `MTR`×5,836, `KGS`×833, `∅`×87, `MTS`×47, `NOS`×45, `GMS`×36, `DRM`×8, `SET`×3
- **`NumPerMsr2`** (3 values) — `1.000000`×47,148, `0.000000`×6,011, `1098.900000`×47
- **`SpecPrice`** (2 values) — `N`×53,205, `R`×1
- **`isSrvCall`** (1 values) — `N`×53,206
- **`PcDocType`** (1 values) — `-1`×53,206
- **`LinManClsd`** (1 values) — `N`×53,206
- **`VatGrpSrc`** (1 values) — `N`×53,206
- **`NoInvtryMv`** (1 values) — `N`×53,206
- **`UomEntry`** (3 values) — `-1`×39,425, `2`×7,770, `0`×6,011
- **`UomEntry2`** (4 values) — `-1`×39,425, `2`×7,702, `0`×6,032, `1`×47
- **`UomCode`** (3 values) — `Manual`×39,425, `LTR`×7,770, `NULL`×6,011
- **`UomCode2`** (5 values) — `Manual`×39,425, `LTR`×7,702, `NULL`×6,011, `MTS`×47, `∅`×21
- **`NeedQty`** (1 values) — `N`×53,206
- **`PartRetire`** (1 values) — `N`×53,206
- **`EnSetCost`** (1 values) — `N`×53,206
- **`DistribIS`** (1 values) — `N`×53,206
- **`IsByPrdct`** (2 values) — `N`×50,182, `NULL`×3,024
- **`ItemType`** (2 values) — `4`×47,195, `290`×6,011
- **`PriceEdit`** (3 values) — `N`×50,182, `NULL`×3,012, `Y`×12
- **`LinePoPrss`** (1 values) — `N`×53,206
- **`FreeChrgBP`** (1 values) — `N`×53,206
- **`TaxRelev`** (1 values) — `Y`×53,206
- **`ThirdParty`** (1 values) — `N`×53,206
- **`InvQtyOnly`** (1 values) — `N`×53,206
- **`ReturnRsn`** (1 values) — `-1`×53,206
- **`ReturnAct`** (1 values) — `-1`×53,206
- **`ItmTaxType`** (2 values) — `NULL`×53,201, `GR`×5
- **`NCMCode`** (1 values) — `-1`×53,206
- **`IsPrscGood`** (1 values) — `N`×53,206
- **`IsCstmAct`** (1 values) — `N`×53,206
- **`TaxAmtSrc`** (1 values) — `S`×53,206
- **`IndEscala`** (1 values) — `N`×53,206
- **`CUSplit`** (1 values) — `N`×53,206
- **`RevCharge`** (1 values) — `N`×53,206
- **`ListNum`** (2 values) — `NULL`×53,205, `-2`×1
- **`UoMNum`** (2 values) — `1.000000`×47,195, `0.000000`×6,011
- **`UoMDen`** (2 values) — `1.000000`×50,801, `0.000000`×2,405
- **`UoMNum2`** (3 values) — `1.000000`×47,148, `0.000000`×6,011, `1098.900000`×47
- **`UoMDen2`** (2 values) — `1.000000`×50,801, `0.000000`×2,405
- **`U_UNE_SCHI`** (1 values) — `N`×53,206
- **`U_UNE_CALI`** (1 values) — `Y`×53,206
- **`U_UNE_CUNT`** (1 values) — `Y`×53,206
- **`U_F_Year`** (2 values) — `NULL`×53,205, `2024-25`×1
- **`U_PRCHSE_VAL`** (3 values) — `0.000000`×47,036, `NULL`×6,169, `148100.000000`×1
