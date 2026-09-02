# `DRF1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 166,843 | 27,865 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 97,867 | 10,268 | `DocDate` | 2025-01-01 → 2026-08-24 |
| BEV | 39,835 | 7,322 | `DocDate` | 2024-09-30 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 49,462 | |
| `LineNum` | INTEGER | 73% | 86% | 66% | 72% | 76% | 62% | 380 | |
| `TargetType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `TrgetEntry` | INTEGER | <1% | — | — | — | — | — | 17 | |
| `BaseRef` | NVARCHAR(16) | 45% | 44% | 58% | 39% | 60% | 62% | 22,346 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `BaseEntry` | INTEGER | 45% | 44% | 58% | 39% | 60% | 62% | 17,687 | |
| `BaseLine` | INTEGER | 31% | 36% | 30% | 25% | 45% | 25% | 95 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItemCode` | NVARCHAR(50) | 84% | 91% | 77% | 88% | 86% | 73% | 1,792 | |
| `Dscription` | NVARCHAR(200) | 91% | 95% | 89% | 94% | 90% | 92% | 3,153 | |
| `Quantity` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 9,204 | |
| `ShipDate` | TIMESTAMP | 72% | 41% | 71% | 82% | 68% | 68% | 690 | |
| `OpenQty` | DECIMAL | <1% | 2% | <1% | <1% | <1% | <1% | 65 | |
| `Price` | DECIMAL | 85% | 57% | 92% | 90% | 87% | 98% | 24,348 | |
| `Currency` | NVARCHAR(3) | 85% | 57% | 92% | 90% | 87% | 98% | 4 | |
| `Rate` | DECIMAL | <1% | <1% | <1% | <1% | — | — | 52 | |
| `DiscPrcnt` | DECIMAL | <1% | <1% | <1% | <1% | <1% | <1% | 77 | |
| `LineTotal` | DECIMAL | 85% | 57% | 92% | 90% | 87% | 98% | 58,553 | |
| `TotalFrgn` | DECIMAL | <1% | <1% | <1% | <1% | — | — | 87 | |
| `OpenSum` | DECIMAL | <1% | 2% | <1% | <1% | <1% | <1% | 145 | |
| `OpenSumFC` | DECIMAL | <1% | — | — | — | — | — | 4 | |
| `VendorNum` | NVARCHAR(50) | — | <1% | — | — | — | — | 1 | |
| `SerialNum` | NVARCHAR(17) | <1% | — | — | — | — | — | 2 | |
| `WhsCode` | NVARCHAR(8) | 84% | 91% | 77% | 88% | 86% | 73% | 51 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 111 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `AcctCode` | NVARCHAR(15) | 66% | 89% | 82% | 54% | 74% | 79% | 246 | |
| `TaxStatus` | NVARCHAR(1) | 66% | 89% | 82% | 54% | 74% | 79% | 2 | |
| `GrossBuyPr` | DECIMAL | 1% | — | 40% | — | — | 42% | 404 | |
| `PriceBefDi` | DECIMAL | 85% | 57% | 92% | 90% | 87% | 98% | 24,324 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 693 | |
| `OpenCreQty` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 9,190 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseCard` | NVARCHAR(15) | 66% | 89% | 82% | 54% | 74% | 79% | 1,490 | |
| `TotalSumSy` | DECIMAL | 85% | 57% | 92% | 90% | 87% | 98% | 58,553 | |
| `OpenSumSys` | DECIMAL | <1% | <1% | <1% | <1% | <1% | <1% | 116 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `OcrCode` | NVARCHAR(8) | 79% | 94% | 82% | 90% | 79% | 82% | 72 | |
| `VatPrcnt` | DECIMAL | 54% | 87% | 70% | 43% | 70% | 71% | 6 | |
| `VatGroup` | NVARCHAR(8) | 32% | 69% | 33% | 16% | 44% | 13% | 9 | |
| `PriceAfVAT` | DECIMAL | 55% | 46% | 75% | 48% | 61% | 77% | 20,714 | |
| `VolUnit` | SMALLINT | 49% | 80% | 59% | 42% | 60% | 52% | 1 | |
| `Factor1` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 2 | |
| `Factor2` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 18 | |
| `Factor3` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 4 | |
| `Factor4` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 4 | |
| `PackQty` | DECIMAL | 49% | 80% | 59% | 42% | 60% | 52% | 3,689 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDocNum` | INTEGER | 42% | 36% | 58% | 37% | 45% | 63% | 21,268 | |
| `BaseAtCard` | NVARCHAR(200) | 23% | 30% | 21% | 20% | 40% | 25% | 12,327 | |
| `VatSum` | DECIMAL | 43% | 44% | 63% | 37% | 57% | 69% | 32,214 | |
| `VatSumFrgn` | DECIMAL | — | <1% | <1% | — | — | — | 1 | |
| `VatSumSy` | DECIMAL | 43% | 44% | 63% | 37% | 57% | 69% | 32,214 | |
| `FinncPriod` | INTEGER | <1% | 2% | <1% | <1% | <1% | <1% | 18 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 14 | |
| `DedVatSum` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `DedVatSumS` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DistribSum` | DECIMAL | <1% | <1% | 1% | <1% | <1% | <1% | 327 | |
| `DstrbSumSC` | DECIMAL | <1% | <1% | 1% | <1% | <1% | <1% | 327 | |
| `GrssProfit` | DECIMAL | 23% | 19% | 40% | 18% | 30% | 42% | 17,707 | |
| `GrssProfSC` | DECIMAL | 23% | 19% | 40% | 18% | 30% | 42% | 17,707 | |
| `GrssProfFC` | DECIMAL | <1% | — | <1% | — | — | — | 6 | |
| `VisOrder` | INTEGER | 70% | 85% | 64% | 69% | 73% | 60% | 380 | |
| `INMPrice` | DECIMAL | 69% | 48% | 70% | 78% | 73% | 71% | 12,098 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Address` | NVARCHAR(254) | 56% | 88% | 64% | 46% | 69% | 54% | 29 | |
| `TaxCode` | NVARCHAR(8) | 66% | 89% | 82% | 54% | 74% | 79% | 18 | |
| `TaxType` | NVARCHAR(1) | 66% | 89% | 82% | 54% | 74% | 79% | 1 | |
| `OrigItem` | NVARCHAR(50) | 2% | 1% | 4% | 2% | 1% | 3% | 653 | |
| `BackOrdr` | NVARCHAR(1) | 28% | 50% | 37% | 19% | 38% | 40% | 1 | |
| `FreeTxt` | NVARCHAR(100) | <1% | — | <1% | — | — | <1% | 2 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PickIdNo` | INTEGER | 7% | 3% | 4% | <1% | — | — | 2,316 | |
| `TrnsCode` | SMALLINT | 66% | 89% | 82% | 54% | 73% | 80% | 1 | |
| `VatAppld` | DECIMAL | <1% | — | — | — | — | — | 15 | |
| `VatAppldSC` | DECIMAL | <1% | — | — | — | — | — | 15 | |
| `BaseQty` | DECIMAL | 40% | 43% | 46% | 34% | 58% | 44% | 4,810 | |
| `BaseOpnQty` | DECIMAL | 37% | 35% | 46% | 33% | 44% | 44% | 6,159 | |
| `WtLiable` | NVARCHAR(1) | 66% | 89% | 82% | 54% | 74% | 79% | 2 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineVat` | DECIMAL | 43% | 44% | 63% | 37% | 57% | 69% | 32,214 | |
| `LineVatlF` | DECIMAL | — | <1% | <1% | — | — | — | 1 | |
| `LineVatS` | DECIMAL | 43% | 44% | 63% | 37% | 57% | 69% | 32,214 | |
| `unitMsr` | NVARCHAR(100) | 80% | 87% | 74% | 88% | 86% | 73% | 13 | |
| `NumPerMsr` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 4 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CountryOrg` | NVARCHAR(3) | <1% | <1% | <1% | <1% | — | — | 7 | |
| `StckDstSum` | DECIMAL | <1% | <1% | <1% | <1% | <1% | <1% | 168 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Text` | NCLOB | <1% | — | — | <1% | — | — | 0 | |
| `OwnerCode` | INTEGER | 2% | — | <1% | 3% | — | 1% | 5 | |
| `StockPrice` | DECIMAL | 28% | 36% | 37% | 23% | 33% | 41% | 8,968 | |
| `ConsumeFCT` | NVARCHAR(1) | 49% | 80% | 59% | 42% | 60% | 52% | 2 | |
| `LstByDsSum` | DECIMAL | <1% | <1% | 1% | <1% | <1% | <1% | 327 | |
| `StckINMPr` | DECIMAL | <1% | <1% | <1% | <1% | <1% | <1% | 147 | |
| `LstBINMPr` | DECIMAL | <1% | <1% | 1% | <1% | <1% | <1% | 288 | |
| `StckDstSc` | DECIMAL | <1% | <1% | <1% | <1% | <1% | <1% | 168 | |
| `LstByDsSc` | DECIMAL | <1% | <1% | 1% | <1% | <1% | <1% | 327 | |
| `StockSum` | DECIMAL | <1% | — | — | — | — | — | 8 | |
| `StockSumSc` | DECIMAL | <1% | — | — | — | — | — | 8 | |
| `ShipToCode` | NVARCHAR(50) | 49% | 79% | 59% | 42% | 60% | 52% | 999 | |
| `ShipToDesc` | NVARCHAR(254) | 49% | 80% | 59% | 42% | 60% | 52% | 586 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GTotal` | DECIMAL | 55% | 46% | 75% | 48% | 61% | 77% | 36,264 | |
| `GTotalFC` | DECIMAL | <1% | <1% | <1% | <1% | — | — | 93 | |
| `GTotalSC` | DECIMAL | 55% | 46% | 75% | 48% | 61% | 77% | 36,264 | |
| `DistribExp` | NVARCHAR(1) | 66% | 89% | 82% | 54% | 74% | 79% | 2 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `GrossBase` | SMALLINT | 30% | 39% | 41% | 23% | 38% | 43% | 3 | |
| `TaxOnly` | NVARCHAR(1) | 66% | 89% | 82% | 54% | 74% | 79% | 2 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QtyToShip` | DECIMAL | 2% | <1% | 5% | 2% | 3% | 3% | 662 | |
| `DelivrdQty` | DECIMAL | <1% | — | — | — | — | — | 5 | |
| `OrderedQty` | DECIMAL | 28% | 49% | 39% | 20% | 36% | 40% | 1,755 | |
| `CogsOcrCod` | NVARCHAR(8) | 32% | 62% | 39% | 23% | 42% | 42% | 44 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsAcct` | NVARCHAR(15) | 32% | 61% | 41% | 23% | 43% | 42% | 43 | |
| `ChgAsmBoMW` | NVARCHAR(1) | 49% | 80% | 59% | 42% | 60% | 52% | 1 | |
| `ActDelDate` | TIMESTAMP | 54% | 61% | 67% | 44% | 61% | 71% | 684 | |
| `OcrCode2` | NVARCHAR(8) | 24% | 10% | 36% | 22% | 16% | 32% | 31 | |
| `OcrCode3` | NVARCHAR(8) | 23% | 9% | 35% | 21% | 15% | 32% | 17 | |
| `OcrCode4` | NVARCHAR(8) | 6% | 4% | 1% | 5% | 13% | 2% | 22 | |
| `OcrCode5` | NVARCHAR(8) | 22% | 6% | 35% | 17% | 9% | 31% | 27 | |
| `TaxDistSum` | DECIMAL | <1% | — | <1% | — | — | <1% | 2 | |
| `TaxDistSSC` | DECIMAL | <1% | — | <1% | — | — | <1% | 2 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excisable` | NVARCHAR(1) | 49% | 80% | 59% | 42% | 60% | 52% | 2 | |
| `AssblValue` | DECIMAL | <1% | — | — | — | — | — | 3 | |
| `CogsOcrCo2` | NVARCHAR(8) | <1% | <1% | <1% | — | 1% | — | 17 | |
| `CogsOcrCo3` | NVARCHAR(8) | <1% | — | <1% | — | — | <1% | 3 | |
| `CogsOcrCo4` | NVARCHAR(8) | <1% | — | <1% | — | — | <1% | 4 | |
| `CogsOcrCo5` | NVARCHAR(8) | <1% | — | <1% | — | — | <1% | 3 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `StockValue` | DECIMAL | 28% | 36% | 37% | 23% | 32% | 41% | 31,993 | |
| `GPTtlBasPr` | DECIMAL | 2% | <1% | 41% | <1% | <1% | 43% | 2,182 | |
| `unitMsr2` | NVARCHAR(100) | 71% | 86% | 57% | 81% | 86% | 69% | 11 | |
| `NumPerMsr2` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 3 | |
| `SpecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `isSrvCall` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcDocType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcQuantity` | DECIMAL | <1% | — | <1% | <1% | — | <1% | 6 | |
| `LinManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatGrpSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `NoInvtryMv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UomEntry` | INTEGER | 84% | 91% | 77% | 88% | 86% | 73% | 5 | |
| `UomEntry2` | INTEGER | 84% | 91% | 77% | 88% | 86% | 73% | 4 | |
| `UomCode` | NVARCHAR(20) | 84% | 91% | 77% | 88% | 86% | 73% | 4 | |
| `UomCode2` | NVARCHAR(20) | 84% | 91% | 77% | 88% | 86% | 73% | 4 | |
| `FromWhsCod` | NVARCHAR(8) | 34% | 11% | 18% | 46% | 26% | 21% | 36 | |
| `NeedQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartRetire` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQty` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 8,957 | |
| `OpenInvQty` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 8,941 | |
| `EnSetCost` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RetCost` | DECIMAL | 2% | <1% | — | 2% | <1% | — | 1,327 | |
| `DistribIS` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsByPrdct` | NVARCHAR(1) | 100% | 99% | 100% | 100% | 100% | 100% | 1 | |
| `ItemType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PriceEdit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LinePoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FreeChrgBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxRelev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ThirdParty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQtyOnly` | NVARCHAR(1) | 70% | 97% | 82% | 58% | 89% | 79% | 1 | |
| `AllocBinC` | NVARCHAR(11) | 10% | 10% | 6% | 7% | 24% | 5% | 1 | |
| `GPBefDisc` | DECIMAL | 55% | 46% | 75% | 48% | 61% | 77% | 20,736 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItmTaxType` | NVARCHAR(2) | 84% | 91% | 77% | 88% | 86% | 73% | 3 | |
| `SacEntry` | INTEGER | 10% | 7% | 13% | 7% | 10% | 20% | 153 | |
| `NCMCode` | INTEGER | 66% | 89% | 82% | 54% | 73% | 79% | 1 | |
| `HsnEntry` | INTEGER | 84% | 91% | 77% | 88% | 86% | 73% | 326 | |
| `IsPrscGood` | NVARCHAR(1) | 100% | 96% | 100% | 100% | 99% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 97% | 77% | 100% | 99% | 94% | 100% | 1 | |
| `IndEscala` | NVARCHAR(1) | 96% | 77% | 99% | 98% | 94% | 98% | 1 | |
| `CESTCode` | INTEGER | 46% | 79% | 54% | 29% | 59% | 25% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 97% | 78% | 100% | 100% | 95% | 100% | 1 | |
| `ListNum` | SMALLINT | 5% | 19% | <1% | 2% | 5% | <1% | 3 | |
| `UoMNum` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 4 | |
| `UoMDen` | DECIMAL | 94% | 96% | 90% | 88% | 86% | 73% | 2 | |
| `UoMNum2` | DECIMAL | 84% | 91% | 77% | 88% | 86% | 73% | 3 | |
| `UoMDen2` | DECIMAL | 94% | 96% | 90% | 88% | 86% | 73% | 2 | |
| `U_Remarks` | NVARCHAR(100) | 12% | 4% | 19% | 11% | 3% | 24% | 9,359 | |
| `U_SchemeAgst` | NVARCHAR(50) | 62% | 84% | 59% | 76% | 63% | 54% | 54 | |
| `U_UTL_ST_TAXCD` | NVARCHAR(100) | <1% | <1% | <1% | <1% | — | <1% | 7 | |
| `U_UTL_ST_CGST` | DECIMAL | <1% | — | — | — | — | — | 3 | |
| `U_UTL_ST_SGST` | DECIMAL | <1% | — | — | — | — | — | 3 | |
| `U_UTL_ST_IGST` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `U_UTL_ST_CGAMT` | DECIMAL | <1% | — | — | — | — | — | 6 | |
| `U_UTL_ST_SGAMT` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `U_UTL_ST_IGAMT` | DECIMAL | <1% | — | — | <1% | — | — | 3 | |
| `U_Disp_Qty` | DECIMAL | <1% | <1% | <1% | <1% | <1% | <1% | 105 | |
| `U_Recvd_Qty` | DECIMAL | <1% | <1% | <1% | <1% | <1% | <1% | 774 | |
| `U_cartonpc` | NVARCHAR(100) | <1% | <1% | — | <1% | — | — | 2 | |
| `U_carton` | NVARCHAR(100) | <1% | <1% | — | <1% | — | — | 2 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_FCT1` | DECIMAL | <1% | 3% | 2% | <1% | 2% | 5% | 2 | |
| `U_UNE_FCT2` | DECIMAL | <1% | 3% | 2% | <1% | 2% | 5% | 16 | |
| `U_LNDCSTNO` | NVARCHAR(100) | — | <1% | — | — | <1% | — | 0 | |
| `U_UNE_LTS` | DECIMAL | 5% | 6% | 16% | 4% | 7% | 23% | 2,738 | |
| `U_UNE_ACTD` | NVARCHAR(100) | <1% | 7% | <1% | <1% | 21% | — | 7 | |
| `U_BilltyNumber` | NVARCHAR(100) | 6% | 5% | 12% | 5% | 7% | 19% | 4,845 | |
| `U_ARNO` | NVARCHAR(100) | 7% | 6% | 18% | 5% | 8% | 23% | 7,402 | |
| `U_Sub_Account` | NVARCHAR(20) | 5% | <1% | 13% | 4% | 1% | 22% | 3 | |
| `U_CardCode` | NVARCHAR(15) | 5% | 6% | 17% | 4% | 8% | 23% | 369 | |
| `U_Purpose` | NVARCHAR(10) | 6% | 36% | 2% | — | 12% | <1% | 5 | |
| `U_F_Year` | NVARCHAR(10) | <1% | — | <1% | — | — | — | 7 | |
| `U_PRCHSE_VAL` | DECIMAL | <1% | — | <1% | — | — | — | 106 | |
| `U_BiltyDate` | TIMESTAMP | <1% | n/a | 6% | 1% | n/a | 19% | 48 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BiltyDate` | OIL, BEV | **MART** |
| `U_UNE_CALI` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TargetType`** (5 values) — `-1`×166,818, `20`×14, `13`×6, `15`×4, `18`×1
- **`TrgetEntry`** (18 values) — `NULL`×143,707, `0`×23,111, `42740`×6, `1225`×3, `19495`×2, `9371`×2, `20986`×1, `241`×1, `9426`×1, `4593`×1, `19496`×1, `22053`×1, `19498`×1, `1194`×1, `19494`×1, `616`×1, `19499`×1, `6720`×1
- **`BaseType`** (12 values) — `-1`×92,110, `17`×35,018, `20`×20,321, `22`×8,885, `1250000001`×4,763, `18`×1,870, `15`×1,761, `13`×1,230, `16`×643, `21`×133, `23`×68, `234000031`×41
- **`LineStatus`** (2 values) — `O`×166,824, `C`×19
- **`Currency`** (5 values) — `INR`×141,733, `NULL`×18,218, `∅`×6,735, `USD`×114, `EUR`×43
- **`OpenSumFC`** (4 values) — `0.000000`×166,839, `562500.000000`×2, `37605.000000`×1, `577315.200000`×1
- **`SerialNum`** (3 values) — `NULL`×152,975, `∅`×13,867, `1`×1
- **`TreeType`** (4 values) — `N`×116,872, `P`×41,406, `I`×4,613, `S`×3,952
- **`TaxStatus`** (3 values) — `Y`×109,534, `NULL`×57,308, `N`×1
- **`UseBaseUn`** (2 values) — `N`×104,829, `Y`×62,014
- **`InvntSttus`** (2 values) — `O`×166,826, `C`×17
- **`VatPrcnt`** (6 values) — `0.000000`×76,845, `5.000000`×60,739, `18.000000`×25,288, `12.000000`×3,955, `28.000000`×14, `0.100000`×2
- **`VatGroup`** (10 values) — `NULL`×63,522, `∅`×49,951, `IGST@5`×30,062, `CG+SG@18`×8,899, `CG+SG@5`×5,350, `CG+SG@0`×3,376, `IGST@18`×3,094, `IGST@12`×1,186, `IGST@0`×775, `CG+SG@12`×628
- **`VolUnit`** (2 values) — `NULL`×84,320, `4`×82,523
- **`Factor1`** (2 values) — `1.000000`×139,831, `0.000000`×27,012
- **`Factor2`** (18 values) — `1.000000`×138,201, `0.000000`×27,012, `4.000000`×555, `16.000000`×326, `20.000000`×278, `12.000000`×146, `10.000000`×107, `24.000000`×70, `3.000000`×34, `6.000000`×33, `5.000000`×30, `15.000000`×18, `2.000000`×11, `9.000000`×10, `35.000000`×5, `40.000000`×4, `36.000000`×2, `70.000000`×1
- **`Factor3`** (4 values) — `1.000000`×139,829, `0.000000`×27,012, `4.000000`×1, `10.000000`×1
- **`Factor4`** (4 values) — `1.000000`×139,828, `0.000000`×27,012, `275.000000`×2, `1350.000000`×1
- **`UpdInvntry`** (1 values) — `Y`×166,843
- **`FinncPriod`** (19 values) — `NULL`×166,670, `45`×46, `23`×20, `42`×18, `22`×15, `7`×13, `10`×11, `20`×9, `41`×6, `25`×6, `44`×6, `8`×6, `15`×5, `43`×4, `18`×2, `9`×2, `24`×2, `14`×1, `12`×1
- **`ObjType`** (14 values) — `67`×55,403, `18`×37,713, `13`×34,943, `15`×11,787, `20`×9,173, `22`×4,379, `16`×4,123, `14`×4,106, `19`×2,903, `1250000001`×1,502, `59`×273, `17`×263, `21`×145, `60`×130
- **`IsAqcuistn`** (1 values) — `N`×166,843
- **`GrssProfFC`** (6 values) — `0.000000`×166,837, `420146.430000`×2, `134737.500000`×1, `132240.600000`×1, `211382.250000`×1, `342439.500000`×1
- **`DropShip`** (2 values) — `N`×166,745, `Y`×98
- **`TaxCode`** (19 values) — `NULL`×57,309, `IGST@5`×35,212, `CG+SG@5`×17,805, `CG+SG@18`×16,782, `Exampt`×10,845, `IGST@18`×8,326, `CG+SG@0`×6,351, `RIGST@5`×3,955, `GST05R`×3,693, `IGST@0`×2,303, `CG+SG@12`×2,204, `IGST@12`×1,749, `RISGT@18`×138, `RCGSG@5`×73, `RCGSG@18`×61, `∅`×21, `CG+SG@28`×9, `IGST@28`×5, `IGST@0.1`×2
- **`TaxType`** (2 values) — `Y`×109,535, `NULL`×57,308
- **`BackOrdr`** (2 values) — `NULL`×119,328, `Y`×47,515
- **`FreeTxt`** (3 values) — `NULL`×98,083, `∅`×68,759, ```×1
- **`PickStatus`** (1 values) — `N`×166,843
- **`TrnsCode`** (2 values) — `-1`×110,604, `NULL`×56,239
- **`VatAppld`** (15 values) — `0.000000`×166,829, `303756.750000`×1, `11300.400000`×1, `313547.750000`×1, `9027.708000`×1, `198588.000000`×1, `847.560000`×1, `9898.800000`×1, `225000.000000`×1, `15714.286000`×1, `65.700000`×1, `810.000000`×1, `38571.420000`×1, `12499.999500`×1, `42857.142000`×1
- **`VatAppldSC`** (15 values) — `0.000000`×166,829, `9027.708000`×1, `42857.142000`×1, `225000.000000`×1, `38571.420000`×1, `810.000000`×1, `65.700000`×1, `12499.999500`×1, `9898.800000`×1, `15714.286000`×1, `847.560000`×1, `198588.000000`×1, `313547.750000`×1, `303756.750000`×1, `11300.400000`×1
- **`WtLiable`** (3 values) — `N`×93,496, `NULL`×57,308, `Y`×16,039
- **`DeferrTax`** (1 values) — `N`×166,843
- **`unitMsr`** (14 values) — `PCS`×123,628, `NULL`×32,711, `LTR`×4,216, `MTS`×1,861, `MTR`×1,634, `KGS`×1,320, `SET`×1,038, `NOS`×214, `GMS`×83, `∅`×56, `MTRS`×41, `DRM`×34, `KG`×5, `GRM`×2
- **`NumPerMsr`** (4 values) — `1.000000`×137,970, `0.000000`×27,012, `1098.900000`×1,860, `1.098900`×1
- **`CEECFlag`** (1 values) — `S`×166,843
- **`CountryOrg`** (8 values) — `NULL`×166,746, `AE`×56, `ES`×19, `AU`×15, `∅`×2, `XX`×2, `AT`×2, `IN`×1
- **`LineType`** (1 values) — `R`×166,843
- **`OwnerCode`** (6 values) — `NULL`×163,307, `20`×3,348, `14`×140, `2`×45, `4`×2, `6`×1
- **`ConsumeFCT`** (3 values) — `NULL`×84,320, `N`×45,603, `Y`×36,920
- **`StockSum`** (8 values) — `0.000000`×166,836, `3428.560000`×1, `1066.660000`×1, `1000.000000`×1, `160715.000000`×1, `20952.400000`×1, `79185.780000`×1, `1007427.200000`×1
- **`StockSumSc`** (8 values) — `0.000000`×166,836, `20952.400000`×1, `1007427.200000`×1, `160715.000000`×1, `1000.000000`×1, `1066.660000`×1, `3428.560000`×1, `79185.780000`×1
- **`BasePrice`** (1 values) — `E`×166,843
- **`DistribExp`** (3 values) — `Y`×99,047, `NULL`×57,308, `N`×10,488
- **`DescOW`** (2 values) — `N`×166,364, `Y`×479
- **`DetailsOW`** (2 values) — `N`×166,840, `Y`×3
- **`GrossBase`** (4 values) — `NULL`×116,212, `-6`×47,419, `-1`×2,314, `-11`×898
- **`TaxOnly`** (3 values) — `N`×109,498, `NULL`×57,308, `Y`×37
- **`WtCalced`** (1 values) — `N`×166,843
- **`DelivrdQty`** (6 values) — `0.000000`×162,579, `NULL`×4,260, `200.000000`×1, `300.000000`×1, `6000.000000`×1, `400.000000`×1
- **`CiOppLineN`** (1 values) — `-1`×166,843
- **`ChgAsmBoMW`** (2 values) — `NULL`×84,320, `N`×82,523
- **`OcrCode3`** (18 values) — `NULL`×127,670, `Factory`×13,743, `Del Bkhp`×9,881, `BackOff`×4,671, `FACT_COM`×2,840, `Sales RE`×2,789, `Sales`×2,616, `Med MKT`×657, `OTE`×482, `∅`×403, `Transprt`×316, `Del Mayp`×277, `NPD1`×225, `NPD3`×192, `NPD2`×72, `Interest`×4, `R & D`×3, `Sal CF`×2
- **`OcrCode4`** (23 values) — `NULL`×155,605, `Admin`×3,013, `E-COM`×2,645, `IT`×929, `MT`×840, `GT`×582, `ROI`×504, `CSD`×500, `DIGTAL M`×422, `∅`×403, `Legal`×313, `Accounts`×263, `CAL CNTR`×205, `POP`×203, `GP-GDWN`×105, `IMPORT`×75, `HR_DEPT`×75, `MIS`×65, `EXPORT`×42, `HORECA`×33, `PLANT`×9, `SOCIAL M`×8, `BankChgs`×4
- **`OcrCode5`** (28 values) — `NULL`×130,170, `HR`×19,917, `DL`×10,429, `PB`×3,158, `UP`×515, `∅`×403, `MH`×356, `WB`×296, `TE`×223, `RJ`×213, `KN`×191, `UK`×160, `GJ`×148, `JK`×134, `AS`×91, `TN`×79, `GO`×65, `MP`×62, `KE`×43, `KR`×42, `CD`×36, `AP`×36, `HP`×28, `JH`×17, `OR`×13, `CH`×10, `BH`×7, `NG`×1
- **`TaxDistSum`** (2 values) — `0.000000`×166,841, `1170.000000`×2
- **`TaxDistSSC`** (2 values) — `0.000000`×166,841, `1170.000000`×2
- **`PostTax`** (1 values) — `Y`×166,843
- **`Excisable`** (3 values) — `NULL`×84,239, `N`×82,523, `∅`×81
- **`AssblValue`** (3 values) — `0.000000`×166,841, `1447142.850000`×1, `1040000.000000`×1
- **`CogsOcrCo2`** (18 values) — `NULL`×166,698, `11-2024`×55, `10-2024`×20, `08-2024`×16, `12-2024`×14, `01-2025`×7, `06-2025`×6, `02-2025`×5, `05-2025`×4, `09-2024`×4, `12-2025`×3, `04-2025`×3, `04-2024`×2, `03-2025`×2, `08-2025`×1, `09-2025`×1, `11-2025`×1, `10-2025`×1
- **`CogsOcrCo3`** (4 values) — `NULL`×166,782, `Sales`×59, `Sales RE`×1, `OTE`×1
- **`CogsOcrCo4`** (5 values) — `NULL`×166,791, `GT`×24, `MT`×22, `E-COM`×3, `ROI`×3
- **`CogsOcrCo5`** (4 values) — `NULL`×166,819, `HR`×20, `PB`×3, `HP`×1
- **`LocCode`** (6 values) — `2`×142,999, `1`×22,426, `3`×791, `5`×463, `NULL`×148, `4`×16
- **`unitMsr2`** (12 values) — `PCS`×109,878, `NULL`×46,214, `LTR`×5,977, `∅`×1,764, `MTR`×1,669, `KGS`×997, `NOS`×183, `SET`×49, `GMS`×44, `DRM`×37, `MTS`×30, `MTRS`×1
- **`NumPerMsr2`** (3 values) — `1.000000`×139,801, `0.000000`×27,012, `1098.900000`×30
- **`SpecPrice`** (3 values) — `N`×159,048, `R`×7,104, `2`×691
- **`isSrvCall`** (1 values) — `N`×166,843
- **`PcDocType`** (1 values) — `-1`×166,843
- **`PcQuantity`** (6 values) — `0.000000`×166,837, `250.000000`×2, `200.000000`×1, `400.000000`×1, `300.000000`×1, `6000.000000`×1
- **`LinManClsd`** (1 values) — `N`×166,843
- **`VatGrpSrc`** (3 values) — `N`×117,073, `M`×32,160, `D`×17,610
- **`NoInvtryMv`** (2 values) — `N`×166,435, `Y`×408
- **`UomEntry`** (5 values) — `-1`×133,864, `0`×27,012, `2`×4,106, `1`×1,860, `3`×1
- **`UomEntry2`** (4 values) — `-1`×133,864, `0`×27,058, `2`×5,891, `1`×30
- **`UomCode`** (5 values) — `Manual`×133,864, `NULL`×27,012, `LTR`×4,106, `MTS`×1,860, `KGS`×1
- **`UomCode2`** (5 values) — `Manual`×133,864, `NULL`×27,012, `LTR`×5,891, `∅`×46, `MTS`×30
- **`NeedQty`** (1 values) — `N`×166,843
- **`PartRetire`** (1 values) — `N`×166,843
- **`EnSetCost`** (2 values) — `N`×163,369, `Y`×3,474
- **`DistribIS`** (1 values) — `N`×166,843
- **`IsByPrdct`** (2 values) — `N`×166,440, `NULL`×403
- **`ItemType`** (1 values) — `4`×166,843
- **`PriceEdit`** (3 values) — `N`×166,440, `NULL`×212, `Y`×191
- **`LinePoPrss`** (1 values) — `N`×166,843
- **`FreeChrgBP`** (1 values) — `N`×166,843
- **`TaxRelev`** (1 values) — `Y`×166,843
- **`ThirdParty`** (1 values) — `N`×166,843
- **`InvQtyOnly`** (2 values) — `N`×116,976, `NULL`×49,867
- **`AllocBinC`** (2 values) — `NULL`×150,128, `0`×16,715
- **`ReturnRsn`** (1 values) — `-1`×166,843
- **`ReturnAct`** (2 values) — `-1`×138,017, `1`×28,826
- **`ItmTaxType`** (4 values) — `GR`×139,317, `NULL`×27,415, `NN`×93, `GN`×18
- **`NCMCode`** (2 values) — `-1`×110,924, `NULL`×55,919
- **`IsPrscGood`** (2 values) — `N`×166,188, `NULL`×655
- **`IsCstmAct`** (1 values) — `N`×166,843
- **`TaxAmtSrc`** (2 values) — `S`×161,223, `NULL`×5,620
- **`IndEscala`** (2 values) — `N`×160,368, `NULL`×6,475
- **`CESTCode`** (2 values) — `NULL`×90,427, `-1`×76,416
- **`CUSplit`** (1 values) — `N`×166,843
- **`RevCharge`** (2 values) — `N`×161,988, `NULL`×4,855
- **`ListNum`** (4 values) — `NULL`×159,048, `1`×6,805, `4`×858, `-1`×132
- **`UoMNum`** (4 values) — `1.000000`×137,970, `0.000000`×27,012, `1098.900000`×1,860, `1.098900`×1
- **`UoMDen`** (2 values) — `1.000000`×157,317, `0.000000`×9,526
- **`UoMNum2`** (3 values) — `1.000000`×139,801, `0.000000`×27,012, `1098.900000`×30
- **`UoMDen2`** (2 values) — `1.000000`×157,317, `0.000000`×9,526
- **`U_UTL_ST_TAXCD`** (8 values) — `NULL`×166,792, `RCGSG@5`×18, `Exempt`×9, `EXEMPT`×8, `IGST@5`×7, `CG+SG@18`×6, `0`×2, `BILTY NO 1201`×1
- **`U_UTL_ST_CGST`** (4 values) — `0.000000`×90,710, `NULL`×76,125, `9.000000`×7, `139.290000`×1
- **`U_UTL_ST_SGST`** (4 values) — `0.000000`×90,690, `NULL`×76,145, `9.000000`×7, `139.290000`×1
- **`U_UTL_ST_IGST`** (3 values) — `0.000000`×90,696, `NULL`×76,146, `18.000000`×1
- **`U_UTL_ST_CGAMT`** (7 values) — `0.000000`×90,695, `NULL`×76,143, `0.027900`×1, `3499.356700`×1, `2525.644800`×1, `15825.600000`×1, `675.000000`×1
- **`U_UTL_ST_SGAMT`** (3 values) — `0.000000`×90,700, `NULL`×76,142, `15825.600000`×1
- **`U_UTL_ST_IGAMT`** (4 values) — `0.000000`×90,698, `NULL`×76,143, `996819.000000`×1, `9137.290000`×1
- **`U_cartonpc`** (3 values) — `NULL`×166,783, `∅`×59, `5670001`×1
- **`U_carton`** (3 values) — `NULL`×166,783, `∅`×59, `CANOLA`×1
- **`U_UNE_SCHI`** (2 values) — `N`×166,811, `Y`×32
- **`U_UNE_CALI`** (1 values) — `Y`×166,843
- **`U_UNE_CUNT`** (1 values) — `Y`×166,843
- **`U_UNE_FCT1`** (3 values) — `0.000000`×89,318, `NULL`×76,419, `1.000000`×1,106
- **`U_UNE_FCT2`** (17 values) — `0.000000`×89,316, `NULL`×76,421, `1.000000`×767, `4.000000`×106, `16.000000`×72, `20.000000`×63, `12.000000`×34, `3.000000`×14, `6.000000`×12, `10.000000`×9, `5.000000`×8, `24.000000`×5, `48.000000`×5, `15.000000`×5, `45.000000`×3, `9.000000`×2, `18.000000`×1
- **`U_UNE_ACTD`** (8 values) — `NULL`×165,345, `1102007`×1,345, `5100013`×147, `5300015`×2, `2980`×1, `4110002`×1, `4140003`×1, `14400`×1
- **`U_Sub_Account`** (4 values) — `NULL`×158,847, `SALES`×7,291, `BST`×658, `SALES RETURN`×47
- **`U_Purpose`** (6 values) — `NULL`×156,128, `SALE`×8,762, `CONSUMABLE`×1,536, `-`×236, `RETURNABLE`×177, `BST`×4
- **`U_F_Year`** (8 values) — `NULL`×166,734, `2022-23`×31, `2024-25`×31, `2023-24`×14, `2021-22`×12, `2020-21`×9, `2019-20`×6, `2018-19`×6
