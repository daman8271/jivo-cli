# `WTR1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 53,701 | 12,478 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 12,490 | 4,500 | `DocDate` | 2025-01-15 → 2026-08-24 |
| BEV | 7,100 | 1,645 | `DocDate` | 2024-10-07 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12,204 | |
| `LineNum` | INTEGER | 78% | 87% | 70% | 82% | 87% | 70% | 380 | |
| `TargetType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `TrgetEntry` | INTEGER | 1% | 5% | 2% | <1% | 13% | 5% | 175 | |
| `BaseRef` | NVARCHAR(16) | 10% | 71% | 3% | 5% | 52% | 5% | 1,327 | |
| `BaseType` | INTEGER | 100% | 99% | 98% | 100% | 98% | 96% | 4 | |
| `BaseEntry` | INTEGER | 10% | 71% | 3% | 5% | 52% | 5% | 1,327 | |
| `BaseLine` | INTEGER | 8% | 63% | 2% | 3% | 47% | 4% | 76 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItemCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 1,155 | |
| `Dscription` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 1,207 | |
| `Quantity` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 7,449 | |
| `ShipDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 638 | |
| `OpenQty` | DECIMAL | 99% | 95% | 98% | 100% | 87% | 95% | 7,450 | |
| `Price` | DECIMAL | 90% | 98% | 97% | 93% | 96% | 100% | 5,706 | |
| `Currency` | NVARCHAR(3) | 90% | 98% | 97% | 93% | 96% | 100% | 2 | |
| `DiscPrcnt` | DECIMAL | <1% | — | — | — | — | — | 4 | |
| `LineTotal` | DECIMAL | 90% | 98% | 97% | 93% | 96% | 100% | 26,503 | |
| `OpenSum` | DECIMAL | 90% | 98% | 97% | 93% | 96% | 100% | 26,503 | |
| `VendorNum` | NVARCHAR(50) | — | <1% | — | — | — | — | 1 | |
| `SerialNum` | NVARCHAR(17) | <1% | — | — | — | — | — | 1 | |
| `WhsCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 45 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PriceBefDi` | DECIMAL | 90% | 98% | 97% | 93% | 96% | 100% | 5,704 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 638 | |
| `OpenCreQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 7,449 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TotalSumSy` | DECIMAL | 90% | 98% | 97% | 93% | 96% | 100% | 26,503 | |
| `OpenSumSys` | DECIMAL | 90% | 98% | 97% | 93% | 96% | 100% | 26,503 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `OcrCode` | NVARCHAR(8) | 50% | 68% | 22% | 83% | 53% | 27% | 36 | |
| `Factor1` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 14 | |
| `Factor3` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor4` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VisOrder` | INTEGER | 77% | 86% | 69% | 81% | 87% | 70% | 380 | |
| `INMPrice` | DECIMAL | 90% | 98% | 97% | 93% | 96% | 100% | 5,706 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TrnsCode` | SMALLINT | 2% | <1% | 1% | <1% | <1% | 3% | 1 | |
| `BaseQty` | DECIMAL | 10% | 71% | 3% | 5% | 53% | 7% | 1,364 | |
| `BaseOpnQty` | DECIMAL | 10% | 71% | 3% | 5% | 53% | 7% | 1,400 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `unitMsr` | NVARCHAR(100) | 91% | 94% | 83% | 100% | 100% | 100% | 9 | |
| `NumPerMsr` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StockPrice` | DECIMAL | 97% | 98% | 98% | 96% | 99% | 99% | 12,179 | |
| `StockSum` | DECIMAL | 90% | 98% | 97% | 93% | 96% | 100% | 26,503 | |
| `StockSumSc` | DECIMAL | 90% | 98% | 97% | 93% | 96% | 100% | 26,503 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OcrCode2` | NVARCHAR(8) | <1% | <1% | <1% | — | — | — | 3 | |
| `OcrCode3` | NVARCHAR(8) | <1% | <1% | — | — | — | — | 1 | |
| `OcrCode4` | NVARCHAR(8) | — | <1% | — | — | — | — | 0 | |
| `OcrCode5` | NVARCHAR(8) | <1% | <1% | <1% | — | — | — | 1 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `unitMsr2` | NVARCHAR(100) | 100% | 100% | 100% | 100% | 100% | 100% | 9 | |
| `NumPerMsr2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SpecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isSrvCall` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcDocType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatGrpSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NoInvtryMv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UomEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UomEntry2` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `UomCode` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UomCode2` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `FromWhsCod` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 42 | |
| `NeedQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartRetire` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 7,449 | |
| `OpenInvQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 7,449 | |
| `EnSetCost` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DistribIS` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsByPrdct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ItemType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PriceEdit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinePoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FreeChrgBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxRelev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ThirdParty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQtyOnly` | NVARCHAR(1) | 11% | 65% | <1% | 6% | 40% | — | 1 | |
| `AllocBinC` | NVARCHAR(11) | 32% | 91% | 37% | 19% | 86% | 26% | 1 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ItmTaxType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `NCMCode` | INTEGER | 2% | — | <1% | — | — | — | 1 | |
| `HsnEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 112 | |
| `IsPrscGood` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IndEscala` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMNum` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMDen` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMNum2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMDen2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Remarks` | NVARCHAR(100) | <1% | — | <1% | — | — | — | 10 | |
| `U_SchemeAgst` | NVARCHAR(50) | 51% | 50% | 22% | 83% | 35% | 27% | 37 | |
| `U_UTL_ST_TAXCD` | NVARCHAR(100) | <1% | — | <1% | — | — | — | 2 | |
| `U_UTL_ST_CGST` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `U_UTL_ST_SGST` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `U_UTL_ST_CGAMT` | DECIMAL | <1% | — | — | — | — | — | 4 | |
| `U_Disp_Qty` | DECIMAL | — | <1% | <1% | — | <1% | — | 1 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_FCT1` | DECIMAL | 2% | 3% | 12% | <1% | 6% | 23% | 2 | |
| `U_UNE_FCT2` | DECIMAL | 2% | 3% | 12% | <1% | 6% | 23% | 19 | |
| `U_LNDCSTNO` | NVARCHAR(100) | — | <1% | — | — | — | — | 0 | |
| `U_UNE_ACTD` | NVARCHAR(100) | 5% | 69% | <1% | 1% | 87% | — | 9 | |
| `U_Purpose` | NVARCHAR(10) | <1% | <1% | — | — | — | — | 2 | |
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

- **`TargetType`** (2 values) — `-1`×53,012, `67`×689
- **`BaseType`** (4 values) — `-1`×48,186, `1250000001`×4,532, `67`×841, `0`×142
- **`LineStatus`** (2 values) — `O`×53,559, `C`×142
- **`Currency`** (2 values) — `INR`×48,421, `∅`×5,280
- **`DiscPrcnt`** (4 values) — `0.000000`×53,697, `-67.500000`×2, `0.010000`×1, `-10.830000`×1
- **`SerialNum`** (2 values) — `NULL`×53,700, `1`×1
- **`SlpCode`** (1 values) — `-1`×53,701
- **`TreeType`** (1 values) — `N`×53,701
- **`UseBaseUn`** (1 values) — `Y`×53,701
- **`InvntSttus`** (2 values) — `O`×53,012, `C`×689
- **`Factor1`** (1 values) — `1.000000`×53,701
- **`Factor2`** (14 values) — `1.000000`×53,319, `4.000000`×152, `20.000000`×58, `16.000000`×54, `10.000000`×28, `5.000000`×25, `3.000000`×19, `12.000000`×17, `6.000000`×9, `2.000000`×8, `24.000000`×6, `35.000000`×3, `9.000000`×2, `70.000000`×1
- **`Factor3`** (1 values) — `1.000000`×53,701
- **`Factor4`** (2 values) — `1.000000`×53,700, `275.000000`×1
- **`UpdInvntry`** (1 values) — `Y`×53,701
- **`FinncPriod`** (24 values) — `24`×4,161, `44`×3,902, `43`×3,201, `23`×3,182, `41`×2,991, `18`×2,918, `42`×2,879, `25`×2,798, `22`×2,574, `16`×2,544, `21`×2,342, `20`×2,244, `45`×2,094, `9`×1,817, `17`×1,798, `19`×1,761, `10`×1,668, `12`×1,617, `11`×1,557, `15`×1,476, `7`×1,465, `14`×1,457, `8`×1,208, `6`×47
- **`ObjType`** (1 values) — `67`×53,701
- **`IsAqcuistn`** (1 values) — `N`×53,701
- **`DropShip`** (1 values) — `N`×53,701
- **`PickStatus`** (1 values) — `N`×53,701
- **`TrnsCode`** (2 values) — `NULL`×52,594, `-1`×1,107
- **`DeferrTax`** (1 values) — `N`×53,701
- **`unitMsr`** (10 values) — `PCS`×44,505, `NULL`×4,606, `LTR`×2,583, `MTR`×1,253, `KGS`×660, `∅`×30, `DRM`×25, `NOS`×20, `GMS`×15, `SET`×4
- **`NumPerMsr`** (1 values) — `1.000000`×53,701
- **`CEECFlag`** (1 values) — `S`×53,701
- **`LineType`** (1 values) — `R`×53,701
- **`BasePrice`** (1 values) — `E`×53,701
- **`DescOW`** (1 values) — `N`×53,701
- **`DetailsOW`** (1 values) — `N`×53,701
- **`WtCalced`** (1 values) — `N`×53,701
- **`CiOppLineN`** (1 values) — `-1`×53,701
- **`OcrCode2`** (4 values) — `NULL`×53,606, `09-2025`×92, `10-2025`×2, `03-2025`×1
- **`OcrCode3`** (2 values) — `NULL`×53,627, `Factory`×74
- **`OcrCode5`** (2 values) — `NULL`×53,357, `HR`×344
- **`PostTax`** (1 values) — `Y`×53,701
- **`LocCode`** (4 values) — `2`×51,022, `1`×1,913, `3`×738, `NULL`×28
- **`unitMsr2`** (10 values) — `PCS`×48,801, `LTR`×2,590, `MTR`×1,262, `KGS`×703, `∅`×128, `NULL`×109, `NOS`×56, `DRM`×31, `GMS`×17, `SET`×4
- **`NumPerMsr2`** (1 values) — `1.000000`×53,701
- **`SpecPrice`** (1 values) — `N`×53,701
- **`isSrvCall`** (1 values) — `N`×53,701
- **`PcDocType`** (1 values) — `-1`×53,701
- **`LinManClsd`** (1 values) — `N`×53,701
- **`VatGrpSrc`** (1 values) — `N`×53,701
- **`NoInvtryMv`** (1 values) — `N`×53,701
- **`UomEntry`** (2 values) — `-1`×51,144, `2`×2,557
- **`UomEntry2`** (3 values) — `-1`×51,144, `2`×2,529, `0`×28
- **`UomCode`** (2 values) — `Manual`×51,144, `LTR`×2,557
- **`UomCode2`** (3 values) — `Manual`×51,144, `LTR`×2,529, `∅`×28
- **`NeedQty`** (1 values) — `N`×53,701
- **`PartRetire`** (1 values) — `N`×53,701
- **`EnSetCost`** (1 values) — `N`×53,701
- **`DistribIS`** (1 values) — `N`×53,701
- **`IsByPrdct`** (1 values) — `N`×53,701
- **`ItemType`** (1 values) — `4`×53,701
- **`PriceEdit`** (1 values) — `N`×53,701
- **`LinePoPrss`** (1 values) — `N`×53,701
- **`FreeChrgBP`** (1 values) — `N`×53,701
- **`TaxRelev`** (1 values) — `Y`×53,701
- **`ThirdParty`** (1 values) — `N`×53,701
- **`InvQtyOnly`** (2 values) — `NULL`×48,000, `N`×5,701
- **`AllocBinC`** (2 values) — `NULL`×36,647, `0`×17,054
- **`ReturnRsn`** (1 values) — `-1`×53,701
- **`ReturnAct`** (1 values) — `-1`×53,701
- **`ItmTaxType`** (3 values) — `GR`×53,690, `GN`×8, `NN`×3
- **`NCMCode`** (2 values) — `NULL`×52,692, `-1`×1,009
- **`IsPrscGood`** (1 values) — `N`×53,701
- **`IsCstmAct`** (1 values) — `N`×53,701
- **`TaxAmtSrc`** (1 values) — `S`×53,701
- **`IndEscala`** (1 values) — `N`×53,701
- **`CUSplit`** (1 values) — `N`×53,701
- **`RevCharge`** (1 values) — `N`×53,701
- **`UoMNum`** (1 values) — `1.000000`×53,701
- **`UoMDen`** (1 values) — `1.000000`×53,701
- **`UoMNum2`** (1 values) — `1.000000`×53,701
- **`UoMDen2`** (1 values) — `1.000000`×53,701
- **`U_Remarks`** (11 values) — `NULL`×53,637, `CANOLA`×54, `STOCK TRANSFER AS PER LOADING WEIGHT`×2, `6877`×1, `8849`×1, `EMERGENCY TRANSFERRED BECAUSE OF BILL.`×1, `STOCK TRANSFER ON LOADING WEIGHT 40300`×1, `can`×1, `EMERGENCY STOCK TRANSFERRED BECAUSE OF BILL`×1, `6840`×1, `gro`×1
- **`U_UTL_ST_TAXCD`** (3 values) — `NULL`×53,696, `CG+SG@18`×3, `IGST@5`×2
- **`U_UTL_ST_CGST`** (2 values) — `0.000000`×53,698, `9.000000`×3
- **`U_UTL_ST_SGST`** (2 values) — `0.000000`×53,698, `9.000000`×3
- **`U_UTL_ST_CGAMT`** (4 values) — `0.000000`×53,698, `0.027900`×1, `2525.644800`×1, `3499.356700`×1
- **`U_UNE_SCHI`** (1 values) — `N`×53,701
- **`U_UNE_CALI`** (1 values) — `Y`×53,701
- **`U_UNE_CUNT`** (1 values) — `Y`×53,701
- **`U_UNE_FCT1`** (3 values) — `0.000000`×52,042, `1.000000`×1,056, `NULL`×603
- **`U_UNE_FCT2`** (20 values) — `0.000000`×52,042, `1.000000`×650, `NULL`×603, `4.000000`×140, `16.000000`×76, `20.000000`×73, `12.000000`×50, `10.000000`×13, `3.000000`×12, `5.000000`×10, `6.000000`×8, `48.000000`×5, `24.000000`×4, `9.000000`×4, `45.000000`×4, `15.000000`×2, `70.000000`×2, `18.000000`×1, `40.000000`×1, `35.000000`×1
- **`U_UNE_ACTD`** (10 values) — `NULL`×50,889, `1102007`×2,778, `1102001`×9, `5100013`×7, `1100207`×6, `4140003`×4, `5300015`×3, `4110001`×3, `4110007`×1, `110207`×1
- **`U_Purpose`** (3 values) — `NULL`×53,670, `SALE`×29, `BST`×2
- **`U_F_Year`** (2 values) — `NULL`×53,700, `2019-20`×1
- **`U_PRCHSE_VAL`** (3 values) — `0.000000`×49,797, `NULL`×3,903, `140000.000000`×1
