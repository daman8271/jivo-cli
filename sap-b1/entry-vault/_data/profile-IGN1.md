# `IGN1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 18,015 | 3,366 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 717 | 29 | `DocDate` | 2024-12-31 → 2026-08-11 |
| BEV | 3,285 | 450 | `DocDate` | 2024-09-30 → 2026-08-22 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 8,548 | |
| `LineNum` | INTEGER | 53% | 90% | 55% | 45% | 28% | 44% | 413 | |
| `TargetType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseRef` | NVARCHAR(16) | 64% | 4% | 55% | 100% | 69% | 100% | 8,234 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BaseEntry` | INTEGER | 64% | 4% | 55% | 100% | 69% | 100% | 8,232 | |
| `BaseLine` | INTEGER | 19% | — | 14% | 45% | — | 44% | 20 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ItemCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 1,322 | |
| `Dscription` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 1,369 | |
| `Quantity` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 4,904 | |
| `ShipDate` | TIMESTAMP | 64% | 4% | 55% | 100% | 69% | 100% | 614 | |
| `OpenQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 4,904 | |
| `Price` | DECIMAL | 89% | 99% | 96% | 83% | 100% | 99% | 8,521 | |
| `Currency` | NVARCHAR(3) | 89% | 99% | 96% | 83% | 100% | 99% | 2 | |
| `DiscPrcnt` | DECIMAL | 4% | 2% | 6% | — | — | — | 627 | |
| `LineTotal` | DECIMAL | 89% | 99% | 96% | 83% | 100% | 99% | 14,196 | |
| `OpenSum` | DECIMAL | 89% | 99% | 96% | 83% | 100% | 99% | 14,196 | |
| `WhsCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 35 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 11 | |
| `PriceBefDi` | DECIMAL | 89% | 99% | 96% | 83% | 100% | 99% | 8,166 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 624 | |
| `OpenCreQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 4,904 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `TotalSumSy` | DECIMAL | 89% | 99% | 96% | 83% | 100% | 99% | 14,196 | |
| `OpenSumSys` | DECIMAL | 89% | 99% | 96% | 83% | 100% | 99% | 14,196 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OcrCode` | NVARCHAR(8) | 51% | 5% | 12% | 85% | — | 42% | 29 | |
| `Factor1` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `Factor3` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor4` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VisOrder` | INTEGER | 53% | 90% | 55% | 45% | 28% | 44% | 413 | |
| `INMPrice` | DECIMAL | 89% | 99% | 96% | 83% | 100% | 99% | 8,521 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxType` | NVARCHAR(1) | <1% | — | — | — | — | — | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TrnsCode` | SMALLINT | <1% | <1% | — | — | — | — | 1 | |
| `BaseQty` | DECIMAL | <1% | — | — | — | — | — | 7 | |
| `BaseOpnQty` | DECIMAL | <1% | — | — | — | — | — | 7 | |
| `WtLiable` | NVARCHAR(1) | <1% | — | — | — | — | — | 1 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `unitMsr` | NVARCHAR(100) | 81% | 90% | 68% | 100% | 100% | 100% | 9 | |
| `NumPerMsr` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TranType` | NVARCHAR(1) | 42% | 4% | 39% | 47% | 69% | 48% | 1 | |
| `StockPrice` | DECIMAL | 89% | 99% | 96% | 83% | 100% | 99% | 8,538 | |
| `StockSum` | DECIMAL | 89% | 99% | 96% | 83% | 100% | 99% | 14,196 | |
| `StockSumSc` | DECIMAL | 89% | 99% | 96% | 83% | 100% | 99% | 14,196 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxOnly` | NVARCHAR(1) | <1% | — | — | — | — | — | 1 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OcrCode2` | NVARCHAR(8) | <1% | <1% | <1% | — | — | — | 9 | |
| `OcrCode3` | NVARCHAR(8) | <1% | — | <1% | — | — | — | 2 | |
| `OcrCode5` | NVARCHAR(8) | <1% | — | — | — | — | — | 2 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excisable` | NVARCHAR(1) | <1% | — | — | — | — | — | 1 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `unitMsr2` | NVARCHAR(100) | 99% | 100% | 100% | 100% | 100% | 100% | 11 | |
| `NumPerMsr2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SpecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `isSrvCall` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcDocType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatGrpSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NoInvtryMv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UomEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `UomEntry2` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `UomCode` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `UomCode2` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `NeedQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartRetire` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 4,904 | |
| `OpenInvQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 4,904 | |
| `EnSetCost` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DistribIS` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsByPrdct` | NVARCHAR(1) | 64% | 4% | 55% | 100% | 69% | 100% | 1 | |
| `ItemType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PriceEdit` | NVARCHAR(1) | 82% | 85% | 66% | 100% | 100% | 100% | 2 | |
| `LinePoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FreeChrgBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxRelev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ThirdParty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQtyOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ItmTaxType` | NVARCHAR(2) | <1% | — | — | — | — | — | 1 | |
| `NCMCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `HsnEntry` | INTEGER | 100% | 100% | 97% | 100% | 100% | 100% | 245 | |
| `IsPrscGood` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IndEscala` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ListNum` | SMALLINT | <1% | — | — | — | — | — | 1 | |
| `UoMNum` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UoMDen` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMNum2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UoMDen2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Remarks` | NVARCHAR(100) | <1% | — | — | — | — | — | 2 | |
| `U_SchemeAgst` | NVARCHAR(50) | 58% | 34% | 19% | 85% | — | 32% | 46 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Purpose` | NVARCHAR(10) | <1% | — | — | — | — | — | 1 | |
| `U_F_Year` | NVARCHAR(10) | 3% | — | 16% | — | — | — | 7 | |
| `U_PRCHSE_VAL` | DECIMAL | 4% | — | 18% | — | — | — | 546 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BiltyDate` | OIL, BEV | **MART** |
| `U_UNE_CALI` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TargetType`** (1 values) — `-1`×18,015
- **`BaseType`** (3 values) — `202`×11,574, `-1`×6,435, `60`×6
- **`BaseLine`** (21 values) — `NULL`×13,256, `0`×1,413, `1`×644, `2`×543, `3`×489, `4`×446, `5`×423, `6`×350, `7`×184, `8`×105, `9`×47, `10`×39, `11`×21, `12`×20, `13`×18, `14`×12, `18`×1, `19`×1, `16`×1, `15`×1, `17`×1
- **`LineStatus`** (1 values) — `O`×18,015
- **`Currency`** (2 values) — `INR`×15,995, `∅`×2,020
- **`SlpCode`** (1 values) — `-1`×18,015
- **`TreeType`** (2 values) — `N`×18,014, `P`×1
- **`AcctCode`** (11 values) — `1103009`×11,574, `3200003`×2,318, `5100013`×2,014, `1103013`×1,877, `5100017`×203, `5100003`×17, `5640001`×7, `5000002`×2, `1212009`×1, `1212012`×1, `1212010`×1
- **`UseBaseUn`** (2 values) — `Y`×18,014, `N`×1
- **`InvntSttus`** (1 values) — `O`×18,015
- **`OcrCode`** (30 values) — `∅`×8,778, `CANOLA`×3,884, `OLIVE`×1,566, `MUSTARD`×1,221, `SOYABEAN`×745, `SUNFLOWR`×491, `GROUNDNT`×337, `BLENDED`×225, `NULL`×116, `GIFT PK`×111, `GHEE`×111, `RICEBRAN`×105, `SEEDS`×73, `COCONUT`×54, `SESAME`×43, `DRY FRTS`×42, `COTTONSD`×38, `LABEL`×18, `SPICES`×16, `COFFEE`×15, `RICE`×8, `TEA`×4, `CAP`×4, `FLAKES`×2, `POUCH`×2, `SOYA CHK`×2, `SNACKS`×1, `HONEY`×1, `ATTA`×1, `PAIN OIL`×1
- **`Factor1`** (1 values) — `1.000000`×18,015
- **`Factor2`** (5 values) — `1.000000`×17,970, `12.000000`×40, `4.000000`×3, `3.000000`×1, `8.000000`×1
- **`Factor3`** (1 values) — `1.000000`×18,015
- **`Factor4`** (1 values) — `1.000000`×18,015
- **`UpdInvntry`** (1 values) — `Y`×18,015
- **`FinncPriod`** (24 values) — `6`×2,323, `10`×1,773, `44`×1,264, `11`×1,191, `9`×1,190, `45`×1,179, `41`×996, `24`×982, `18`×949, `25`×768, `23`×690, `7`×560, `42`×418, `43`×415, `12`×392, `16`×376, `22`×369, `14`×328, `17`×327, `20`×323, `21`×314, `19`×304, `15`×301, `8`×283
- **`ObjType`** (1 values) — `59`×18,015
- **`IsAqcuistn`** (1 values) — `N`×18,015
- **`DropShip`** (1 values) — `N`×18,015
- **`TaxType`** (2 values) — `NULL`×18,014, `Y`×1
- **`PickStatus`** (1 values) — `N`×18,015
- **`TrnsCode`** (2 values) — `NULL`×18,011, `-1`×4
- **`BaseQty`** (7 values) — `0.000000`×18,009, `3.000000`×1, `327.600000`×1, `435.000000`×1, `74.135000`×1, `200.000000`×1, `1935.000000`×1
- **`BaseOpnQty`** (7 values) — `0.000000`×18,009, `74.135000`×1, `200.000000`×1, `435.000000`×1, `327.600000`×1, `3.000000`×1, `1935.000000`×1
- **`WtLiable`** (2 values) — `NULL`×18,014, `N`×1
- **`DeferrTax`** (1 values) — `N`×18,015
- **`unitMsr`** (10 values) — `PCS`×11,323, `NULL`×3,371, `LTR`×2,529, `MTR`×535, `KGS`×197, `∅`×22, `NOS`×18, `SET`×9, `DRM`×9, `GMS`×2
- **`NumPerMsr`** (2 values) — `1.000000`×18,014, `1.098900`×1
- **`CEECFlag`** (1 values) — `S`×18,015
- **`LineType`** (1 values) — `R`×18,015
- **`TranType`** (2 values) — `NULL`×10,483, `C`×7,532
- **`BasePrice`** (1 values) — `E`×18,015
- **`DescOW`** (1 values) — `N`×18,015
- **`DetailsOW`** (1 values) — `N`×18,015
- **`TaxOnly`** (2 values) — `NULL`×18,014, `N`×1
- **`WtCalced`** (1 values) — `N`×18,015
- **`CiOppLineN`** (1 values) — `-1`×18,015
- **`OcrCode2`** (10 values) — `∅`×17,378, `NULL`×585, `02-2026`×16, `09-2025`×8, `12-2025`×8, `11-2025`×8, `08-2025`×6, `01-2026`×4, `01-2025`×1, `03-2026`×1
- **`OcrCode3`** (3 values) — `∅`×17,969, `NULL`×36, `Factory`×10
- **`OcrCode5`** (3 values) — `∅`×18,011, `NULL`×3, `HR`×1
- **`PostTax`** (1 values) — `Y`×18,015
- **`Excisable`** (2 values) — `NULL`×18,014, `N`×1
- **`LocCode`** (3 values) — `2`×16,396, `1`×1,310, `3`×309
- **`unitMsr2`** (12 values) — `PCS`×14,366, `MTS`×2,512, `MTR`×506, `KGS`×286, `NULL`×116, `LTR`×86, `NOS`×52, `MTRS`×34, `GMS`×24, `DRM`×19, `SET`×9, `∅`×5
- **`NumPerMsr2`** (2 values) — `1.000000`×15,503, `1098.900000`×2,512
- **`SpecPrice`** (2 values) — `N`×18,014, `R`×1
- **`isSrvCall`** (1 values) — `N`×18,015
- **`PcDocType`** (1 values) — `-1`×18,015
- **`LinManClsd`** (1 values) — `N`×18,015
- **`VatGrpSrc`** (1 values) — `N`×18,015
- **`NoInvtryMv`** (1 values) — `N`×18,015
- **`UomEntry`** (3 values) — `-1`×15,497, `2`×2,517, `3`×1
- **`UomEntry2`** (3 values) — `-1`×15,497, `1`×2,512, `2`×6
- **`UomCode`** (3 values) — `Manual`×15,497, `LTR`×2,517, `KGS`×1
- **`UomCode2`** (3 values) — `Manual`×15,497, `MTS`×2,512, `LTR`×6
- **`NeedQty`** (1 values) — `N`×18,015
- **`PartRetire`** (1 values) — `N`×18,015
- **`EnSetCost`** (1 values) — `N`×18,015
- **`DistribIS`** (1 values) — `N`×18,015
- **`IsByPrdct`** (2 values) — `N`×11,580, `NULL`×6,435
- **`ItemType`** (1 values) — `4`×18,015
- **`PriceEdit`** (3 values) — `N`×11,576, `Y`×3,268, `NULL`×3,171
- **`LinePoPrss`** (1 values) — `N`×18,015
- **`FreeChrgBP`** (1 values) — `N`×18,015
- **`TaxRelev`** (1 values) — `Y`×18,015
- **`ThirdParty`** (1 values) — `N`×18,015
- **`InvQtyOnly`** (1 values) — `N`×18,015
- **`ReturnRsn`** (1 values) — `-1`×18,015
- **`ReturnAct`** (1 values) — `-1`×18,015
- **`ItmTaxType`** (2 values) — `NULL`×18,014, `GR`×1
- **`NCMCode`** (1 values) — `-1`×18,015
- **`IsPrscGood`** (1 values) — `N`×18,015
- **`IsCstmAct`** (1 values) — `N`×18,015
- **`TaxAmtSrc`** (1 values) — `S`×18,015
- **`IndEscala`** (1 values) — `N`×18,015
- **`CUSplit`** (1 values) — `N`×18,015
- **`RevCharge`** (1 values) — `N`×18,015
- **`ListNum`** (2 values) — `NULL`×18,014, `-2`×1
- **`UoMNum`** (2 values) — `1.000000`×18,014, `1.098900`×1
- **`UoMDen`** (1 values) — `1.000000`×18,015
- **`UoMNum2`** (2 values) — `1.000000`×15,503, `1098.900000`×2,512
- **`UoMDen2`** (1 values) — `1.000000`×18,015
- **`U_Remarks`** (3 values) — `NULL`×18,012, `Jan 2026`×2, `Feb 2026`×1
- **`U_UNE_SCHI`** (1 values) — `N`×18,015
- **`U_UNE_CALI`** (1 values) — `Y`×18,015
- **`U_UNE_CUNT`** (1 values) — `Y`×18,015
- **`U_Purpose`** (2 values) — `NULL`×18,014, `-`×1
- **`U_F_Year`** (8 values) — `NULL`×17,432, `2023-24`×153, `2022-23`×138, `2018-19`×90, `2024-25`×68, `2021-22`×61, `2020-21`×40, `2019-20`×33
