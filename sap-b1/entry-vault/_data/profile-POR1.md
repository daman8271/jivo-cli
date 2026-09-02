# `POR1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 11,851 | 2,237 | `DocDate` | 2024-10-01 → 2026-08-24 |
| MART | 17,020 | 971 | `DocDate` | 2024-10-03 → 2026-08-24 |
| BEV | 3,133 | 247 | `DocDate` | 2024-10-01 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4,325 | |
| `LineNum` | INTEGER | 65% | 87% | 64% | 72% | 60% | 54% | 45 | |
| `TargetType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `TrgetEntry` | INTEGER | 90% | 77% | 77% | 91% | 70% | 77% | 4,532 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItemCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 1,009 | |
| `Dscription` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 1,089 | |
| `Quantity` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,616 | |
| `ShipDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 663 | |
| `OpenQty` | DECIMAL | 6% | 3% | 21% | 10% | 30% | 30% | 258 | |
| `Price` | DECIMAL | 98% | 100% | 100% | 98% | 100% | 100% | 2,958 | |
| `Currency` | NVARCHAR(3) | 98% | 100% | 100% | 98% | 100% | 100% | 3 | |
| `Rate` | DECIMAL | <1% | — | — | <1% | — | — | 42 | |
| `DiscPrcnt` | DECIMAL | <1% | <1% | <1% | 1% | — | <1% | 17 | |
| `LineTotal` | DECIMAL | 98% | 100% | 100% | 98% | 100% | 100% | 4,454 | |
| `TotalFrgn` | DECIMAL | <1% | — | — | <1% | — | — | 73 | |
| `OpenSum` | DECIMAL | 84% | 33% | 93% | 90% | 91% | 99% | 3,707 | |
| `OpenSumFC` | DECIMAL | <1% | — | — | <1% | — | — | 53 | |
| `WhsCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 47 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 79 | |
| `TaxStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PriceBefDi` | DECIMAL | 98% | 100% | 100% | 98% | 100% | 100% | 2,946 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 652 | |
| `OpenCreQty` | DECIMAL | 6% | 3% | 21% | 10% | 30% | 30% | 258 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseCard` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 509 | |
| `TotalSumSy` | DECIMAL | 98% | 100% | 100% | 98% | 100% | 100% | 4,454 | |
| `OpenSumSys` | DECIMAL | 84% | 33% | 93% | 90% | 91% | 99% | 3,707 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `OcrCode` | NVARCHAR(8) | 79% | 98% | 88% | 96% | 98% | 80% | 33 | |
| `VatPrcnt` | DECIMAL | 55% | 100% | 89% | 52% | 100% | 86% | 5 | |
| `VatGroup` | NVARCHAR(8) | 56% | 87% | 63% | 57% | 59% | 50% | 9 | |
| `PriceAfVAT` | DECIMAL | 98% | 100% | 100% | 98% | 100% | 100% | 3,116 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor1` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Factor2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Factor3` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Factor4` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PackQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,049 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatSum` | DECIMAL | 54% | 100% | 89% | 50% | 100% | 86% | 3,344 | |
| `VatSumSy` | DECIMAL | 54% | 100% | 89% | 50% | 100% | 86% | 3,344 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DistribSum` | DECIMAL | 3% | <1% | 9% | 2% | <1% | 3% | 268 | |
| `DstrbSumSC` | DECIMAL | 3% | <1% | 9% | 2% | <1% | 3% | 268 | |
| `VisOrder` | INTEGER | 64% | 87% | 64% | 71% | 60% | 51% | 45 | |
| `INMPrice` | DECIMAL | 98% | 100% | 100% | 98% | 100% | 100% | 2,990 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 13 | |
| `TaxCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `TaxType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OrigItem` | NVARCHAR(50) | 4% | 2% | 2% | 4% | 3% | <1% | 194 | |
| `FreeTxt` | NVARCHAR(100) | — | <1% | — | — | — | — | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TrnsCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatAppld` | DECIMAL | 46% | 77% | 66% | 45% | 70% | 62% | 3,214 | |
| `VatAppldSC` | DECIMAL | 46% | 77% | 66% | 45% | 70% | 62% | 3,214 | |
| `WtLiable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineVat` | DECIMAL | 54% | 100% | 89% | 50% | 100% | 86% | 3,344 | |
| `LineVatS` | DECIMAL | 54% | 100% | 89% | 50% | 100% | 86% | 3,344 | |
| `unitMsr` | NVARCHAR(100) | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `NumPerMsr` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CountryOrg` | NVARCHAR(3) | <1% | — | — | <1% | — | — | 5 | |
| `StckDstSum` | DECIMAL | 1% | <1% | 1% | 2% | <1% | 3% | 103 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Text` | NCLOB | <1% | — | — | <1% | — | — | 0 | |
| `OwnerCode` | INTEGER | <1% | — | — | <1% | — | — | 4 | |
| `ConsumeFCT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LstByDsSum` | DECIMAL | 3% | <1% | 9% | 2% | <1% | 2% | 268 | |
| `StckINMPr` | DECIMAL | 1% | <1% | 1% | 2% | <1% | 3% | 88 | |
| `LstBINMPr` | DECIMAL | 3% | <1% | 9% | 2% | <1% | 2% | 236 | |
| `StckDstSc` | DECIMAL | 1% | <1% | 1% | 2% | <1% | 3% | 103 | |
| `LstByDsSc` | DECIMAL | 3% | <1% | 9% | 2% | <1% | 2% | 268 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 99% | 100% | 100% | 100% | 401 | |
| `ShipToDesc` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `StckAppD` | DECIMAL | <1% | <1% | <1% | 1% | — | 1% | 79 | |
| `StckAppDSC` | DECIMAL | <1% | <1% | <1% | 1% | — | 1% | 79 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GTotal` | DECIMAL | 98% | 100% | 100% | 98% | 100% | 100% | 4,795 | |
| `GTotalFC` | DECIMAL | <1% | — | — | <1% | — | — | 80 | |
| `GTotalSC` | DECIMAL | 98% | 100% | 100% | 98% | 100% | 100% | 4,795 | |
| `DistribExp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ChgAsmBoMW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OcrCode2` | NVARCHAR(8) | 63% | 1% | 81% | 66% | 2% | 75% | 26 | |
| `OcrCode3` | NVARCHAR(8) | 61% | 1% | 81% | 63% | 2% | 75% | 9 | |
| `OcrCode4` | NVARCHAR(8) | 16% | <1% | <1% | 22% | — | — | 8 | |
| `OcrCode5` | NVARCHAR(8) | 51% | — | 78% | 40% | — | 74% | 2 | |
| `TaxDistSum` | DECIMAL | <1% | — | <1% | — | — | <1% | 2 | |
| `TaxDistSSC` | DECIMAL | <1% | — | <1% | — | — | <1% | 2 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excisable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `unitMsr2` | NVARCHAR(100) | 45% | 89% | 44% | 46% | 100% | 47% | 8 | |
| `NumPerMsr2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SpecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `isSrvCall` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcDocType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `VatGrpSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `NoInvtryMv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UomEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `UomEntry2` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `UomCode` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `UomCode2` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `NeedQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartRetire` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,662 | |
| `OpenInvQty` | DECIMAL | 6% | 3% | 21% | 10% | 30% | 30% | 262 | |
| `EnSetCost` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DistribIS` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsByPrdct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ItemType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PriceEdit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinePoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FreeChrgBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxRelev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ThirdParty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQtyOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GPBefDisc` | DECIMAL | 98% | 100% | 100% | 98% | 100% | 100% | 3,123 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItmTaxType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SacEntry` | INTEGER | <1% | — | <1% | <1% | — | <1% | 11 | |
| `NCMCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `HsnEntry` | INTEGER | 99% | 100% | 100% | 100% | 100% | 100% | 269 | |
| `IsPrscGood` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 97% | 100% | 99% | 96% | 99% | 98% | 1 | |
| `IndEscala` | NVARCHAR(1) | 97% | 100% | 99% | 96% | 99% | 98% | 1 | |
| `CESTCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ListNum` | SMALLINT | 1% | <1% | — | 2% | — | — | 2 | |
| `UoMNum` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `UoMDen` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UoMNum2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UoMDen2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `U_Remarks` | NVARCHAR(100) | 29% | <1% | 33% | 35% | — | 30% | 2,174 | |
| `U_SchemeAgst` | NVARCHAR(50) | 78% | 98% | 87% | 94% | 96% | 79% | 32 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_ARNO` | NVARCHAR(100) | <1% | — | — | — | — | — | 13 | |
| `U_Purpose` | NVARCHAR(10) | <1% | — | — | — | — | — | 2 | |
| `U_F_Year` | NVARCHAR(10) | <1% | — | — | — | — | — | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BiltyDate` | OIL, BEV | **MART** |
| `U_UNE_CALI` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TargetType`** (2 values) — `20`×10,626, `-1`×1,225
- **`BaseType`** (1 values) — `-1`×11,851
- **`LineStatus`** (2 values) — `C`×11,081, `O`×770
- **`Currency`** (4 values) — `INR`×11,568, `NULL`×199, `USD`×55, `EUR`×29
- **`DiscPrcnt`** (18 values) — `0.000000`×11,801, `-18.000000`×19, `0.010000`×7, `41.000000`×6, `70.500000`×2, `-136.000000`×2, `60.670000`×2, `76.400000`×2, `NULL`×1, `-99900.570000`×1, `-7.000000`×1, `-92.310000`×1, `4.650000`×1, `15.250000`×1, `80.000000`×1, `-1.320000`×1, `-44.380000`×1, `0.090000`×1
- **`WhsCode`** (24 values) — `BH-FA`×4,878, `BH-PM`×3,333, `DL-FA`×2,158, `BH-GJ`×761, `BH-FG`×331, `DL-EC`×82, `BH-CRUDE`×64, `DL-FG`×50, `GP-FA`×48, `NULL`×38, `BH-VA`×21, `BH-EX`×17, `BH-BS`×13, `BH-SC`×13, `BH-PP`×12, `BH-OT`×11, `DL-POP`×9, `BH-PC`×4, `BH-EC`×2, `BH-PF`×2, `BH-LO`×1, `MY-FA`×1, `DL-PS`×1, `BH-PS`×1
- **`TreeType`** (2 values) — `N`×11,773, `P`×78
- **`TaxStatus`** (1 values) — `Y`×11,851
- **`UseBaseUn`** (1 values) — `N`×11,851
- **`InvntSttus`** (2 values) — `C`×9,816, `O`×2,035
- **`VatPrcnt`** (5 values) — `0.000000`×5,289, `18.000000`×5,051, `5.000000`×1,107, `12.000000`×393, `28.000000`×11
- **`VatGroup`** (9 values) — `∅`×5,195, `CG+SG@18`×2,595, `CG+SG@0`×2,324, `IGST@18`×909, `IGST@0`×401, `CG+SG@5`×147, `IGST@5`×127, `CG+SG@12`×120, `IGST@12`×33
- **`VolUnit`** (2 values) — `4`×11,813, `NULL`×38
- **`Factor1`** (2 values) — `1.000000`×11,813, `0.000000`×38
- **`Factor2`** (2 values) — `1.000000`×11,813, `0.000000`×38
- **`Factor3`** (2 values) — `1.000000`×11,813, `0.000000`×38
- **`Factor4`** (2 values) — `1.000000`×11,813, `0.000000`×38
- **`UpdInvntry`** (1 values) — `Y`×11,851
- **`FinncPriod`** (23 values) — `7`×713, `43`×679, `23`×673, `42`×612, `9`×580, `22`×579, `19`×574, `44`×570, `41`×570, `17`×565, `18`×512, `15`×486, `25`×475, `10`×466, `16`×459, `21`×452, `12`×452, `11`×451, `14`×445, `8`×442, `24`×389, `20`×376, `45`×331
- **`ObjType`** (1 values) — `22`×11,851
- **`IsAqcuistn`** (1 values) — `N`×11,851
- **`DropShip`** (1 values) — `N`×11,851
- **`TaxCode`** (13 values) — `CG+SG@0`×4,179, `CG+SG@18`×3,440, `IGST@18`×1,611, `IGST@0`×1,048, `IGST@5`×803, `CG+SG@5`×303, `CG+SG@12`×268, `IGST@12`×125, `Exampt`×61, `CG+SG@28`×7, `IGST@28`×4, `RIGST@5`×1, `NULL`×1
- **`TaxType`** (1 values) — `Y`×11,851
- **`PickStatus`** (1 values) — `N`×11,851
- **`TrnsCode`** (1 values) — `-1`×11,851
- **`WtLiable`** (2 values) — `N`×11,693, `Y`×158
- **`DeferrTax`** (1 values) — `N`×11,851
- **`unitMsr`** (11 values) — `PCS`×10,691, `MTS`×788, `KGS`×204, `MTR`×51, `NULL`×41, `GMS`×20, `NOS`×18, `LTR`×15, `MTRS`×14, `∅`×6, `KG`×3
- **`NumPerMsr`** (3 values) — `1.000000`×11,026, `1098.900000`×787, `0.000000`×38
- **`CEECFlag`** (1 values) — `S`×11,851
- **`CountryOrg`** (6 values) — `NULL`×11,806, `AE`×23, `ES`×11, `AU`×8, `AT`×2, `XX`×1
- **`LineType`** (1 values) — `R`×11,851
- **`OwnerCode`** (5 values) — `NULL`×11,805, `20`×39, `14`×4, `2`×2, `4`×1
- **`ConsumeFCT`** (2 values) — `N`×11,813, `NULL`×38
- **`BasePrice`** (1 values) — `E`×11,851
- **`DistribExp`** (2 values) — `Y`×10,192, `N`×1,659
- **`DescOW`** (1 values) — `N`×11,851
- **`DetailsOW`** (1 values) — `N`×11,851
- **`TaxOnly`** (1 values) — `N`×11,851
- **`WtCalced`** (1 values) — `N`×11,851
- **`CiOppLineN`** (1 values) — `-1`×11,851
- **`ChgAsmBoMW`** (2 values) — `N`×11,813, `NULL`×38
- **`OcrCode2`** (27 values) — `NULL`×4,347, `01-2026`×474, `04-2026`×468, `07-2026`×454, `12-2024`×429, `06-2026`×415, `07-2025`×362, `09-2025`×361, `12-2025`×357, `08-2025`×348, `10-2024`×347, `05-2025`×344, `05-2026`×344, `11-2025`×324, `03-2026`×310, `02-2026`×280, `03-2025`×269, `06-2025`×257, `11-2024`×251, `04-2025`×236, `02-2025`×232, `10-2025`×229, `01-2025`×202, `08-2026`×196, `04-2024`×13, `05-2024`×1, `09-2024`×1
- **`OcrCode3`** (10 values) — `Factory`×4,681, `NULL`×4,666, `BackOff`×1,774, `FACT_COM`×636, `Sales`×38, `OTE`×36, `Med MKT`×16, `Del Mayp`×2, `JIVOS`×1, `NPD1`×1
- **`OcrCode4`** (9 values) — `NULL`×9,967, `Admin`×1,711, `IT`×60, `GP-GDWN`×56, `E-COM`×29, `POP`×16, `CSD`×5, `GT`×4, `Accounts`×3
- **`OcrCode5`** (3 values) — `NULL`×5,865, `HR`×5,145, `DL`×841
- **`TaxDistSum`** (2 values) — `0.000000`×11,850, `1170.000000`×1
- **`TaxDistSSC`** (2 values) — `0.000000`×11,850, `1170.000000`×1
- **`PostTax`** (1 values) — `Y`×11,851
- **`Excisable`** (2 values) — `N`×11,813, `NULL`×38
- **`LocCode`** (2 values) — `2`×9,537, `1`×2,314
- **`unitMsr2`** (9 values) — `NULL`×5,543, `PCS`×4,365, `∅`×1,011, `LTR`×796, `KGS`×67, `MTR`×61, `GMS`×5, `NOS`×2, `MTRS`×1
- **`NumPerMsr2`** (2 values) — `1.000000`×11,813, `0.000000`×38
- **`SpecPrice`** (2 values) — `N`×11,704, `R`×147
- **`isSrvCall`** (1 values) — `N`×11,851
- **`PcDocType`** (1 values) — `-1`×11,851
- **`LinManClsd`** (2 values) — `N`×10,715, `Y`×1,136
- **`VatGrpSrc`** (3 values) — `N`×9,035, `M`×2,649, `D`×167
- **`NoInvtryMv`** (1 values) — `N`×11,851
- **`UomEntry`** (4 values) — `-1`×11,025, `1`×787, `0`×38, `2`×1
- **`UomEntry2`** (3 values) — `-1`×11,025, `2`×788, `0`×38
- **`UomCode`** (4 values) — `Manual`×11,025, `MTS`×787, `NULL`×38, `LTR`×1
- **`UomCode2`** (3 values) — `Manual`×11,025, `LTR`×788, `NULL`×38
- **`NeedQty`** (1 values) — `N`×11,851
- **`PartRetire`** (1 values) — `N`×11,851
- **`EnSetCost`** (1 values) — `N`×11,851
- **`DistribIS`** (1 values) — `N`×11,851
- **`IsByPrdct`** (1 values) — `N`×11,851
- **`ItemType`** (1 values) — `4`×11,851
- **`PriceEdit`** (1 values) — `N`×11,851
- **`LinePoPrss`** (1 values) — `N`×11,851
- **`FreeChrgBP`** (1 values) — `N`×11,851
- **`TaxRelev`** (1 values) — `Y`×11,851
- **`ThirdParty`** (1 values) — `N`×11,851
- **`InvQtyOnly`** (1 values) — `N`×11,851
- **`ReturnRsn`** (1 values) — `-1`×11,851
- **`ReturnAct`** (2 values) — `1`×11,813, `-1`×38
- **`ItmTaxType`** (3 values) — `GR`×11,764, `NN`×49, `NULL`×38
- **`SacEntry`** (12 values) — `NULL`×11,825, `-187`×13, `-189`×2, `-228`×2, `-153`×2, `-446`×1, `-37`×1, `-405`×1, `-388`×1, `51`×1, `-384`×1, `-193`×1
- **`NCMCode`** (1 values) — `-1`×11,851
- **`IsPrscGood`** (1 values) — `N`×11,851
- **`IsCstmAct`** (1 values) — `N`×11,851
- **`TaxAmtSrc`** (2 values) — `S`×11,550, `NULL`×301
- **`IndEscala`** (2 values) — `N`×11,550, `NULL`×301
- **`CESTCode`** (2 values) — `-1`×11,813, `NULL`×38
- **`CUSplit`** (1 values) — `N`×11,851
- **`RevCharge`** (1 values) — `N`×11,851
- **`ListNum`** (3 values) — `NULL`×11,704, `1`×144, `-1`×3
- **`UoMNum`** (3 values) — `1.000000`×11,026, `1098.900000`×787, `0.000000`×38
- **`UoMDen`** (2 values) — `1.000000`×11,847, `0.000000`×4
- **`UoMNum2`** (2 values) — `1.000000`×11,813, `0.000000`×38
- **`UoMDen2`** (2 values) — `1.000000`×11,847, `0.000000`×4
- **`U_UNE_SCHI`** (1 values) — `N`×11,851
- **`U_UNE_CALI`** (1 values) — `Y`×11,851
- **`U_UNE_CUNT`** (1 values) — `Y`×11,851
- **`U_ARNO`** (14 values) — `NULL`×11,836, `CC62/2025-26`×2, `WD76/2024-25`×2, `WD82/2024-25`×1, `WD67/2024-25`×1, `WD62/2024-25`×1, `WD63/2024-25`×1, `WD84/2024-25`×1, `WD66/2024-25`×1, `WD64/2024-25`×1, `WD81/2024-25`×1, `WD65/2024-25`×1, `WD86/2024-25`×1, `WD80/2024-25`×1
- **`U_Purpose`** (3 values) — `NULL`×11,848, `-`×2, `CONSUMABLE`×1
- **`U_F_Year`** (2 values) — `NULL`×11,850, `2024-25`×1
