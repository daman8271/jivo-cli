# `RDN1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 8,168 | 502 | `DocDate` | 2024-10-04 → 2026-08-21 |
| MART | 13,220 | 1,598 | `DocDate` | 2025-01-15 → 2026-08-21 |
| BEV | 309 | 21 | `DocDate` | 2024-10-11 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,031 | |
| `LineNum` | INTEGER | 77% | 89% | 40% | 58% | 88% | 29% | 202 | |
| `TargetType` | INTEGER | 96% | 100% | 92% | 90% | 98% | 90% | 4 | |
| `TrgetEntry` | INTEGER | 78% | 59% | 60% | 84% | 37% | 81% | 2,012 | |
| `BaseRef` | NVARCHAR(16) | 21% | 38% | 23% | 10% | 56% | 10% | 397 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BaseEntry` | INTEGER | 21% | 38% | 23% | 10% | 56% | 10% | 391 | |
| `BaseLine` | INTEGER | 18% | 33% | 12% | 7% | 51% | 5% | 89 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItemCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 436 | |
| `Dscription` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 427 | |
| `Quantity` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 344 | |
| `ShipDate` | TIMESTAMP | — | <1% | — | — | — | — | 0 | |
| `OpenQty` | DECIMAL | 1% | <1% | 18% | 6% | 1% | 10% | 59 | |
| `Price` | DECIMAL | 20% | 23% | 18% | 2% | 23% | 29% | 398 | |
| `Currency` | NVARCHAR(3) | 20% | 23% | 18% | 2% | 23% | 29% | 1 | |
| `DiscPrcnt` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `LineTotal` | DECIMAL | 20% | 23% | 18% | 2% | 23% | 29% | 873 | |
| `OpenSum` | DECIMAL | 12% | 2% | 7% | 2% | 9% | 29% | 667 | |
| `WhsCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 16 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 30 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 36 | |
| `TaxStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBuyPr` | DECIMAL | 2% | — | 95% | — | — | 100% | 79 | |
| `PriceBefDi` | DECIMAL | 20% | 23% | 18% | 2% | 23% | 29% | 398 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 401 | |
| `OpenCreQty` | DECIMAL | 1% | <1% | 18% | 6% | 1% | 10% | 59 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseCard` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 139 | |
| `TotalSumSy` | DECIMAL | 20% | 23% | 18% | 2% | 23% | 29% | 873 | |
| `OpenSumSys` | DECIMAL | 12% | 2% | 7% | 2% | 9% | 29% | 667 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `OcrCode` | NVARCHAR(8) | 99% | 100% | 99% | 100% | 100% | 100% | 27 | |
| `VatPrcnt` | DECIMAL | 100% | 100% | 97% | 100% | 100% | 100% | 4 | |
| `VatGroup` | NVARCHAR(8) | 77% | 91% | 40% | 57% | 82% | 29% | 8 | |
| `PriceAfVAT` | DECIMAL | 20% | 23% | 18% | 2% | 23% | 29% | 399 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor1` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `Factor3` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor4` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PackQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 324 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDocNum` | INTEGER | 21% | 38% | 24% | 10% | 56% | 10% | 396 | |
| `BaseAtCard` | NVARCHAR(200) | — | 1% | — | — | 8% | — | 0 | |
| `VatSum` | DECIMAL | 20% | 23% | 16% | 2% | 23% | 29% | 879 | |
| `VatSumSy` | DECIMAL | 20% | 23% | 16% | 2% | 23% | 29% | 879 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrssProfit` | DECIMAL | 21% | 23% | 98% | 2% | 23% | 100% | 983 | |
| `GrssProfSC` | DECIMAL | 21% | 23% | 98% | 2% | 23% | 100% | 983 | |
| `VisOrder` | INTEGER | 75% | 86% | 39% | 58% | 85% | 19% | 202 | |
| `INMPrice` | DECIMAL | 20% | 23% | 18% | 2% | 23% | 29% | 403 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 13 | |
| `TaxCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `TaxType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OrigItem` | NVARCHAR(50) | 5% | <1% | 3% | 5% | 2% | — | 131 | |
| `BackOrdr` | NVARCHAR(1) | 17% | 38% | 16% | — | 55% | — | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TrnsCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatAppld` | DECIMAL | 12% | 2% | 6% | 2% | 9% | 29% | 667 | |
| `VatAppldSC` | DECIMAL | 12% | 2% | 6% | 2% | 9% | 29% | 667 | |
| `BaseQty` | DECIMAL | 21% | 38% | 23% | 10% | 56% | 10% | 149 | |
| `BaseOpnQty` | DECIMAL | 21% | 38% | 24% | 10% | 56% | 10% | 146 | |
| `WtLiable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineVat` | DECIMAL | 20% | 23% | 16% | 2% | 23% | 29% | 879 | |
| `LineVatS` | DECIMAL | 20% | 23% | 16% | 2% | 23% | 29% | 879 | |
| `unitMsr` | NVARCHAR(100) | 95% | 95% | 99% | 100% | 100% | 100% | 7 | |
| `NumPerMsr` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Text` | NCLOB | <1% | — | — | — | — | — | 0 | |
| `OwnerCode` | INTEGER | <1% | — | <1% | — | — | — | 1 | |
| `StockPrice` | DECIMAL | 65% | 52% | 16% | 96% | 37% | — | 1,827 | |
| `ConsumeFCT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StockSum` | DECIMAL | 20% | 23% | 18% | 2% | 23% | 29% | 873 | |
| `StockSumSc` | DECIMAL | 20% | 23% | 18% | 2% | 23% | 29% | 873 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 191 | |
| `ShipToDesc` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 185 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GTotal` | DECIMAL | 20% | 23% | 18% | 2% | 23% | 29% | 835 | |
| `GTotalSC` | DECIMAL | 20% | 23% | 18% | 2% | 23% | 29% | 835 | |
| `DistribExp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 76% | 63% | 99% | 100% | 68% | 100% | 2 | |
| `TaxOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsOcrCod` | NVARCHAR(8) | 99% | 100% | 99% | 100% | 100% | 100% | 38 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsAcct` | NVARCHAR(15) | 100% | 99% | 100% | 100% | 100% | 100% | 29 | |
| `ChgAsmBoMW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ActDelDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 405 | |
| `OcrCode2` | NVARCHAR(8) | 2% | — | 3% | — | — | — | 6 | |
| `OcrCode3` | NVARCHAR(8) | — | — | <1% | — | — | 10% | 0 | |
| `OcrCode4` | NVARCHAR(8) | — | — | <1% | — | — | 10% | 0 | |
| `OcrCode5` | NVARCHAR(8) | — | — | <1% | — | — | 5% | 0 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excisable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsOcrCo2` | NVARCHAR(8) | 2% | — | 3% | — | — | — | 6 | |
| `CogsOcrCo3` | NVARCHAR(8) | — | — | <1% | — | — | 5% | 0 | |
| `CogsOcrCo4` | NVARCHAR(8) | — | — | <1% | — | — | 5% | 0 | |
| `CogsOcrCo5` | NVARCHAR(8) | — | — | <1% | — | — | 5% | 0 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `StockValue` | DECIMAL | 65% | 52% | 16% | 96% | 37% | — | 3,605 | |
| `GPTtlBasPr` | DECIMAL | 2% | — | 95% | — | — | 100% | 119 | |
| `unitMsr2` | NVARCHAR(100) | 76% | 96% | 70% | 100% | 99% | 100% | 8 | |
| `NumPerMsr2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SpecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `isSrvCall` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcDocType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `VatGrpSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `NoInvtryMv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UomEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UomEntry2` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UomCode` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UomCode2` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `NeedQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartRetire` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 344 | |
| `OpenInvQty` | DECIMAL | 1% | <1% | 18% | 6% | 1% | 10% | 59 | |
| `EnSetCost` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RetCost` | DECIMAL | 39% | <1% | — | 96% | — | — | 1,356 | |
| `DistribIS` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsByPrdct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ItemType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PriceEdit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinePoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FreeChrgBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxRelev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ThirdParty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQtyOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GPBefDisc` | DECIMAL | 20% | 23% | 18% | 2% | 23% | 29% | 399 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ItmTaxType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `NCMCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `HsnEntry` | INTEGER | 100% | 100% | 97% | 100% | 100% | 100% | 57 | |
| `IsPrscGood` | NVARCHAR(1) | 97% | 94% | 100% | 100% | 97% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 78% | 68% | 99% | 100% | 85% | 100% | 1 | |
| `IndEscala` | NVARCHAR(1) | 76% | 63% | 99% | 100% | 68% | 100% | 1 | |
| `CESTCode` | INTEGER | 100% | 99% | 100% | 100% | 92% | 100% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ListNum` | SMALLINT | 59% | 27% | 77% | 87% | 20% | 62% | 2 | |
| `UoMNum` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMDen` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMNum2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMDen2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Remarks` | NVARCHAR(100) | 12% | <1% | 33% | 2% | 6% | 14% | 390 | |
| `U_SchemeAgst` | NVARCHAR(50) | 99% | 100% | 99% | 98% | 100% | 100% | 27 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_FCT1` | DECIMAL | <1% | 3% | <1% | — | 2% | — | 2 | |
| `U_UNE_FCT2` | DECIMAL | <1% | 3% | <1% | — | 2% | — | 5 | |
| `U_Purpose` | NVARCHAR(10) | 14% | 40% | 15% | — | 62% | 5% | 3 | |
| `U_F_Year` | NVARCHAR(10) | <1% | — | — | — | — | — | 2 | |
| `U_BiltyDate` | TIMESTAMP | — | n/a | <1% | — | n/a | 5% | 0 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BiltyDate` | OIL, BEV | **MART** |
| `U_UNE_CALI` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TargetType`** (5 values) — `14`×5,726, `-1`×1,484, `15`×330, `NULL`×314, `16`×314
- **`BaseType`** (3 values) — `-1`×6,484, `15`×1,370, `16`×314
- **`LineStatus`** (2 values) — `C`×8,063, `O`×105
- **`Currency`** (2 values) — `NULL`×6,517, `INR`×1,651
- **`WhsCode`** (16 values) — `DL-GR`×2,558, `BH-GR`×2,358, `BH-LR`×1,117, `DL-EC`×671, `DL-FG`×657, `BH-FG`×386, `PB-SG`×199, `GP-FG`×110, `BH-PF`×32, `BH-FU`×25, `PB-RG`×21, `BH-EC`×21, `BH-PS`×7, `BH-PC`×2, `BH-WST`×2, `BH-BT`×2
- **`SlpCode`** (30 values) — `-1`×3,929, `4`×3,115, `18`×548, `94`×241, `17`×102, `63`×55, `46`×47, `28`×33, `33`×16, `103`×12, `49`×11, `58`×10, `80`×10, `107`×6, `102`×5, `11`×4, `9`×4, `98`×3, `54`×2, `25`×2, `7`×2, `81`×2, `6`×2, `93`×1, `109`×1, `66`×1, `110`×1, `99`×1, `35`×1, `53`×1
- **`TreeType`** (4 values) — `P`×4,328, `I`×1,923, `S`×1,664, `N`×253
- **`TaxStatus`** (1 values) — `Y`×8,168
- **`UseBaseUn`** (2 values) — `N`×6,245, `Y`×1,923
- **`InvntSttus`** (2 values) — `C`×8,027, `O`×141
- **`OcrCode`** (28 values) — `OLIVE`×2,338, `MUSTARD`×1,180, `CANOLA`×1,136, `SOYABEAN`×672, `SUNFLOWR`×636, `INFINITE`×428, `GROUNDNT`×401, `GHEE`×374, `BLENDED`×370, `HONEY`×200, `COCONUT`×82, `RICEBRAN`×69, `RICE`×63, `SEEDS`×53, `NULL`×43, `SPICES`×30, `GIFT PK`×26, `COTTONSD`×24, `SESAME`×17, `SlICEDOL`×10, `COFFEE`×5, `KITCHEN`×3, `CARTON`×2, `TEA`×2, `COSMETIC`×1, `TIN`×1, `FLAKES`×1, `POUCH`×1
- **`VatPrcnt`** (4 values) — `5.000000`×7,352, `12.000000`×553, `18.000000`×262, `0.000000`×1
- **`VatGroup`** (8 values) — `IGST@5`×4,892, `∅`×1,840, `CG+SG@5`×703, `IGST@12`×406, `IGST@18`×185, `CG+SG@12`×93, `CG+SG@18`×48, `IGST@0`×1
- **`VolUnit`** (1 values) — `4`×8,168
- **`Factor1`** (1 values) — `1.000000`×8,168
- **`Factor2`** (10 values) — `1.000000`×7,665, `4.000000`×230, `20.000000`×75, `12.000000`×66, `10.000000`×47, `16.000000`×45, `6.000000`×26, `3.000000`×10, `5.000000`×3, `24.000000`×1
- **`Factor3`** (1 values) — `1.000000`×8,168
- **`Factor4`** (2 values) — `1.000000`×8,167, `1250.000000`×1
- **`UpdInvntry`** (1 values) — `Y`×8,168
- **`FinncPriod`** (23 values) — `8`×1,553, `9`×1,275, `10`×1,138, `7`×817, `25`×320, `18`×299, `17`×267, `12`×209, `15`×209, `22`×208, `24`×201, `16`×199, `23`×185, `20`×183, `43`×166, `19`×162, `21`×158, `44`×132, `42`×126, `14`×123, `11`×90, `45`×74, `41`×74
- **`ObjType`** (1 values) — `16`×8,168
- **`IsAqcuistn`** (1 values) — `N`×8,168
- **`DropShip`** (1 values) — `N`×8,168
- **`TaxCode`** (7 values) — `CG+SG@5`×3,995, `IGST@5`×3,357, `CG+SG@12`×472, `CG+SG@18`×219, `IGST@12`×81, `IGST@18`×43, `IGST@0`×1
- **`TaxType`** (1 values) — `Y`×8,168
- **`BackOrdr`** (2 values) — `NULL`×6,787, `Y`×1,381
- **`PickStatus`** (1 values) — `N`×8,168
- **`TrnsCode`** (1 values) — `-1`×8,168
- **`WtLiable`** (2 values) — `N`×8,166, `Y`×2
- **`DeferrTax`** (1 values) — `N`×8,168
- **`unitMsr`** (8 values) — `PCS`×7,358, `NULL`×424, `SET`×359, `KGS`×10, `NOS`×8, `MTR`×4, `LTR`×4, `DRM`×1
- **`NumPerMsr`** (1 values) — `1.000000`×8,168
- **`CEECFlag`** (1 values) — `S`×8,168
- **`LineType`** (1 values) — `R`×8,168
- **`OwnerCode`** (2 values) — `NULL`×8,164, `14`×4
- **`ConsumeFCT`** (1 values) — `N`×8,168
- **`BasePrice`** (1 values) — `E`×8,168
- **`DistribExp`** (2 values) — `Y`×4,600, `N`×3,568
- **`DescOW`** (2 values) — `N`×8,167, `Y`×1
- **`DetailsOW`** (1 values) — `N`×8,168
- **`GrossBase`** (3 values) — `-6`×5,798, `NULL`×1,923, `-1`×447
- **`TaxOnly`** (1 values) — `N`×8,168
- **`WtCalced`** (1 values) — `N`×8,168
- **`CiOppLineN`** (1 values) — `-1`×8,168
- **`CogsAcct`** (29 values) — `5000002`×2,188, `5000004`×1,113, `5000001`×1,028, `5000009`×615, `5000008`×596, `5000049`×466, `5000040`×428, `5000006`×383, `5000007`×353, `5000019`×353, `5000013`×200, `5000005`×70, `5000012`×60, `5000015`×60, `5000010`×53, `1102007`×53, `5000050`×36, `5000021`×27, `5000003`×24, `∅`×17, `5000023`×15, `5000044`×10, `5000020`×10, `5000034`×3, `5000028`×2, `5000027`×2, `5000024`×1, `5000037`×1, `5000042`×1
- **`ChgAsmBoMW`** (1 values) — `N`×8,168
- **`OcrCode2`** (7 values) — `NULL`×8,025, `10-2024`×53, `11-2024`×44, `12-2024`×38, `09-2024`×3, `05-2025`×3, `06-2025`×2
- **`PostTax`** (1 values) — `Y`×8,168
- **`Excisable`** (1 values) — `N`×8,168
- **`CogsOcrCo2`** (7 values) — `NULL`×8,025, `10-2024`×64, `12-2024`×38, `11-2024`×33, `09-2024`×3, `05-2025`×3, `06-2025`×2
- **`LocCode`** (3 values) — `2`×4,062, `1`×3,886, `3`×220
- **`unitMsr2`** (9 values) — `PCS`×6,139, `NULL`×1,999, `NOS`×9, `KGS`×9, `MTR`×4, `LTR`×3, `SET`×3, `DRM`×1, `∅`×1
- **`NumPerMsr2`** (1 values) — `1.000000`×8,168
- **`SpecPrice`** (2 values) — `R`×4,787, `N`×3,381
- **`isSrvCall`** (1 values) — `N`×8,168
- **`PcDocType`** (1 values) — `-1`×8,168
- **`LinManClsd`** (2 values) — `N`×8,081, `Y`×87
- **`VatGrpSrc`** (3 values) — `N`×4,217, `D`×3,946, `M`×5
- **`NoInvtryMv`** (1 values) — `N`×8,168
- **`UomEntry`** (2 values) — `-1`×8,167, `2`×1
- **`UomEntry2`** (2 values) — `-1`×8,167, `2`×1
- **`UomCode`** (2 values) — `Manual`×8,167, `LTR`×1
- **`UomCode2`** (2 values) — `Manual`×8,167, `LTR`×1
- **`NeedQty`** (1 values) — `N`×8,168
- **`PartRetire`** (1 values) — `N`×8,168
- **`EnSetCost`** (2 values) — `N`×4,903, `Y`×3,265
- **`DistribIS`** (1 values) — `N`×8,168
- **`IsByPrdct`** (1 values) — `N`×8,168
- **`ItemType`** (1 values) — `4`×8,168
- **`PriceEdit`** (1 values) — `N`×8,168
- **`LinePoPrss`** (1 values) — `N`×8,168
- **`FreeChrgBP`** (1 values) — `N`×8,168
- **`TaxRelev`** (1 values) — `Y`×8,168
- **`ThirdParty`** (1 values) — `N`×8,168
- **`InvQtyOnly`** (1 values) — `N`×8,168
- **`ReturnRsn`** (1 values) — `-1`×8,168
- **`ReturnAct`** (1 values) — `1`×8,168
- **`ItmTaxType`** (2 values) — `GR`×8,167, `GN`×1
- **`NCMCode`** (1 values) — `-1`×8,168
- **`IsPrscGood`** (2 values) — `N`×7,915, `NULL`×253
- **`IsCstmAct`** (1 values) — `N`×8,168
- **`TaxAmtSrc`** (2 values) — `S`×6,390, `NULL`×1,778
- **`IndEscala`** (2 values) — `N`×6,220, `NULL`×1,948
- **`CESTCode`** (1 values) — `-1`×8,168
- **`CUSplit`** (1 values) — `N`×8,168
- **`RevCharge`** (1 values) — `N`×8,168
- **`ListNum`** (3 values) — `1`×4,062, `NULL`×3,381, `4`×725
- **`UoMNum`** (1 values) — `1.000000`×8,168
- **`UoMDen`** (1 values) — `1.000000`×8,168
- **`UoMNum2`** (1 values) — `1.000000`×8,168
- **`UoMDen2`** (1 values) — `1.000000`×8,168
- **`U_SchemeAgst`** (28 values) — `OLIVE`×2,330, `MUSTARD`×1,184, `CANOLA`×1,129, `SOYABEAN`×671, `SUNFLOWR`×634, `INFINITE`×428, `GROUNDNT`×401, `GHEE`×371, `BLENDED`×370, `HONEY`×200, `COCONUT`×82, `RICEBRAN`×69, `RICE`×63, `NULL`×60, `SEEDS`×53, `SPICES`×30, `GIFT PK`×26, `COTTONSD`×24, `SESAME`×17, `SlICEDOL`×10, `COFFEE`×5, `KITCHEN`×3, `CARTON`×2, `TEA`×2, `COSMETIC`×1, `FLAKES`×1, `TIN`×1, `POUCH`×1
- **`U_UNE_SCHI`** (2 values) — `N`×8,167, `Y`×1
- **`U_UNE_CALI`** (1 values) — `Y`×8,168
- **`U_UNE_CUNT`** (1 values) — `Y`×8,168
- **`U_UNE_FCT1`** (3 values) — `NULL`×8,101, `1.000000`×66, `0.000000`×1
- **`U_UNE_FCT2`** (6 values) — `NULL`×8,102, `1.000000`×29, `4.000000`×23, `16.000000`×7, `20.000000`×6, `6.000000`×1
- **`U_Purpose`** (4 values) — `NULL`×7,034, `SALE`×1,032, `RETURNABLE`×91, `CONSUMABLE`×11
- **`U_F_Year`** (3 values) — `NULL`×8,164, `2024-25`×3, `2023-24`×1
