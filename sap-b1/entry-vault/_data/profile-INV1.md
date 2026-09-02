# `INV1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 98,170 | 5,318 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 190,840 | 32,664 | `DocDate` | 2024-10-03 → 2026-08-24 |
| BEV | 13,160 | 2,855 | `DocDate` | 2024-10-04 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 31,084 | |
| `LineNum` | INTEGER | 70% | 87% | 59% | 63% | 89% | 45% | 300 | |
| `TargetType` | INTEGER | 98% | 99% | 97% | 98% | 98% | 98% | 4 | |
| `TrgetEntry` | INTEGER | 4% | 2% | 6% | 3% | 3% | 3% | 1,208 | |
| `BaseRef` | NVARCHAR(16) | 85% | 98% | 91% | 93% | 98% | 93% | 12,650 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `BaseEntry` | INTEGER | 85% | 98% | 91% | 93% | 98% | 93% | 11,897 | |
| `BaseLine` | INTEGER | 72% | 91% | 53% | 64% | 92% | 43% | 157 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItemCode` | NVARCHAR(50) | 88% | 100% | 100% | 99% | 100% | 100% | 791 | |
| `Dscription` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 831 | |
| `Quantity` | DECIMAL | 88% | 100% | 100% | 99% | 100% | 100% | 1,767 | |
| `ShipDate` | TIMESTAMP | 52% | 17% | 89% | 92% | 15% | 95% | 572 | |
| `OpenQty` | DECIMAL | 84% | 97% | 91% | 93% | 95% | 95% | 1,787 | |
| `Price` | DECIMAL | 82% | 63% | 85% | 86% | 63% | 97% | 12,267 | |
| `Currency` | NVARCHAR(3) | 82% | 63% | 85% | 86% | 63% | 97% | 3 | |
| `Rate` | DECIMAL | <1% | — | — | — | — | — | 7 | |
| `DiscPrcnt` | DECIMAL | <1% | <1% | — | <1% | — | — | 9 | |
| `LineTotal` | DECIMAL | 82% | 63% | 85% | 86% | 63% | 97% | 30,097 | |
| `TotalFrgn` | DECIMAL | <1% | — | — | — | — | — | 8 | |
| `OpenSum` | DECIMAL | 80% | 62% | 81% | 83% | 59% | 93% | 29,925 | |
| `OpenSumFC` | DECIMAL | <1% | — | — | — | — | — | 8 | |
| `WhsCode` | NVARCHAR(8) | 88% | 100% | 100% | 99% | 100% | 100% | 33 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 66 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 60 | |
| `TaxStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBuyPr` | DECIMAL | 4% | — | 100% | — | — | 100% | 489 | |
| `PriceBefDi` | DECIMAL | 82% | 63% | 85% | 86% | 63% | 97% | 12,266 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 607 | |
| `OpenCreQty` | DECIMAL | 84% | 97% | 91% | 93% | 95% | 95% | 1,787 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseCard` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 628 | |
| `TotalSumSy` | DECIMAL | 82% | 63% | 85% | 86% | 63% | 97% | 30,097 | |
| `OpenSumSys` | DECIMAL | 80% | 62% | 81% | 83% | 59% | 93% | 29,925 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `OcrCode` | NVARCHAR(8) | 89% | 100% | 98% | 100% | 100% | 100% | 36 | |
| `VatPrcnt` | DECIMAL | 89% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `VatGroup` | NVARCHAR(8) | 68% | 92% | 51% | 23% | 89% | 15% | 8 | |
| `PriceAfVAT` | DECIMAL | 82% | 63% | 85% | 86% | 63% | 97% | 12,118 | |
| `VolUnit` | SMALLINT | 88% | 100% | 100% | 99% | 100% | 100% | 1 | |
| `Factor1` | DECIMAL | 88% | 100% | 100% | 99% | 100% | 100% | 2 | |
| `Factor2` | DECIMAL | 88% | 100% | 100% | 99% | 100% | 100% | 17 | |
| `Factor3` | DECIMAL | 88% | 100% | 100% | 99% | 100% | 100% | 4 | |
| `Factor4` | DECIMAL | 88% | 100% | 100% | 99% | 100% | 100% | 2 | |
| `PackQty` | DECIMAL | 88% | 100% | 100% | 99% | 100% | 100% | 1,793 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDocNum` | INTEGER | 86% | 99% | 92% | 95% | 100% | 95% | 12,826 | |
| `BaseAtCard` | NVARCHAR(200) | 29% | 17% | 5% | 26% | 16% | 6% | 5,107 | |
| `VatSum` | DECIMAL | 71% | 63% | 85% | 86% | 63% | 97% | 25,057 | |
| `VatSumSy` | DECIMAL | 71% | 63% | 85% | 86% | 63% | 97% | 25,057 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DedVatSum` | DECIMAL | 71% | 63% | 85% | 86% | 63% | 97% | 25,057 | |
| `DedVatSumS` | DECIMAL | 71% | 63% | 85% | 86% | 63% | 97% | 25,057 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DistribSum` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `DstrbSumSC` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `GrssProfit` | DECIMAL | 70% | 62% | 98% | 83% | 61% | 96% | 26,168 | |
| `GrssProfSC` | DECIMAL | 70% | 62% | 98% | 83% | 61% | 96% | 26,168 | |
| `GrssProfFC` | DECIMAL | <1% | — | — | — | — | — | 8 | |
| `VisOrder` | INTEGER | 68% | 87% | 58% | 55% | 87% | 42% | 150 | |
| `INMPrice` | DECIMAL | 70% | 62% | 84% | 83% | 61% | 93% | 6,478 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Address` | NVARCHAR(254) | 89% | 100% | 100% | 100% | 100% | 100% | 30 | |
| `TaxCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `TaxType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OrigItem` | NVARCHAR(50) | 4% | 2% | 7% | 3% | 3% | 7% | 398 | |
| `BackOrdr` | NVARCHAR(1) | 85% | 98% | 90% | 93% | 98% | 91% | 1 | |
| `FreeTxt` | NVARCHAR(100) | <1% | — | <1% | — | — | <1% | 2 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PickIdNo` | INTEGER | 13% | 1% | 12% | <1% | — | — | 2,832 | |
| `TrnsCode` | SMALLINT | 99% | 100% | 98% | 99% | 98% | 96% | 1 | |
| `VatAppld` | DECIMAL | 3% | 2% | 5% | 3% | 2% | 3% | 2,339 | |
| `VatAppldSC` | DECIMAL | 3% | 2% | 5% | 3% | 2% | 3% | 2,339 | |
| `BaseQty` | DECIMAL | 85% | 98% | 91% | 93% | 98% | 93% | 1,652 | |
| `BaseOpnQty` | DECIMAL | 86% | 99% | 92% | 95% | 100% | 95% | 1,812 | |
| `WtLiable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineVat` | DECIMAL | 71% | 63% | 85% | 86% | 63% | 97% | 25,057 | |
| `LineVatS` | DECIMAL | 71% | 63% | 85% | 86% | 63% | 97% | 25,057 | |
| `unitMsr` | NVARCHAR(100) | 85% | 97% | 100% | 98% | 100% | 100% | 10 | |
| `NumPerMsr` | DECIMAL | 88% | 100% | 100% | 99% | 100% | 100% | 3 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CountryOrg` | NVARCHAR(3) | <1% | <1% | — | — | — | — | 2 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Text` | NCLOB | <1% | — | — | <1% | — | — | 0 | |
| `OwnerCode` | INTEGER | 3% | — | <1% | 15% | — | 2% | 3 | |
| `StockPrice` | DECIMAL | 74% | 63% | 95% | 98% | 63% | 98% | 12,830 | |
| `ConsumeFCT` | NVARCHAR(1) | 88% | 100% | 100% | 99% | 100% | 100% | 2 | |
| `StockSum` | DECIMAL | 46% | 17% | 78% | 81% | 13% | 93% | 19,067 | |
| `StockSumFc` | DECIMAL | <1% | — | — | — | — | — | 8 | |
| `StockSumSc` | DECIMAL | 46% | 17% | 78% | 81% | 13% | 93% | 19,067 | |
| `ShipToCode` | NVARCHAR(50) | 88% | 100% | 100% | 99% | 100% | 100% | 777 | |
| `ShipToDesc` | NVARCHAR(254) | 88% | 100% | 100% | 99% | 100% | 100% | 668 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GTotal` | DECIMAL | 82% | 63% | 85% | 86% | 63% | 97% | 27,532 | |
| `GTotalFC` | DECIMAL | <1% | — | — | — | — | — | 8 | |
| `GTotalSC` | DECIMAL | 82% | 63% | 85% | 86% | 63% | 97% | 27,532 | |
| `DistribExp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `GrossBase` | SMALLINT | 88% | 63% | 100% | 100% | 63% | 100% | 3 | |
| `TaxOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QtyToShip` | DECIMAL | 3% | <1% | 12% | 9% | <1% | 10% | 726 | |
| `OrderedQty` | DECIMAL | 88% | 99% | 100% | 99% | 100% | 100% | 1,676 | |
| `CogsOcrCod` | NVARCHAR(8) | 87% | 100% | 96% | 97% | 98% | 97% | 44 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsAcct` | NVARCHAR(15) | 88% | 99% | 100% | 99% | 100% | 100% | 40 | |
| `ChgAsmBoMW` | NVARCHAR(1) | 88% | 100% | 100% | 99% | 100% | 100% | 1 | |
| `ActDelDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 607 | |
| `OcrCode2` | NVARCHAR(8) | <1% | <1% | 1% | — | <1% | — | 3 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excisable` | NVARCHAR(1) | 88% | 100% | 100% | 99% | 100% | 100% | 1 | |
| `CogsOcrCo2` | NVARCHAR(8) | <1% | <1% | 1% | — | <1% | — | 3 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `StockValue` | DECIMAL | 73% | 62% | 93% | 97% | 60% | 95% | 43,906 | |
| `GPTtlBasPr` | DECIMAL | 15% | <1% | 100% | 1% | <1% | 100% | 8,688 | |
| `unitMsr2` | NVARCHAR(100) | 70% | 95% | 71% | 99% | 99% | 100% | 9 | |
| `NumPerMsr2` | DECIMAL | 88% | 100% | 100% | 99% | 100% | 100% | 2 | |
| `SpecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `isSrvCall` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcDocType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatGrpSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `NoInvtryMv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UomEntry` | INTEGER | 88% | 100% | 100% | 99% | 100% | 100% | 4 | |
| `UomEntry2` | INTEGER | 88% | 100% | 100% | 99% | 100% | 100% | 3 | |
| `UomCode` | NVARCHAR(20) | 88% | 100% | 100% | 99% | 100% | 100% | 3 | |
| `UomCode2` | NVARCHAR(20) | 88% | 100% | 100% | 99% | 100% | 100% | 2 | |
| `NeedQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartRetire` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQty` | DECIMAL | 88% | 100% | 100% | 99% | 100% | 100% | 1,768 | |
| `OpenInvQty` | DECIMAL | 84% | 97% | 91% | 93% | 95% | 95% | 1,787 | |
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
| `GPBefDisc` | DECIMAL | 82% | 63% | 85% | 86% | 63% | 97% | 12,117 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItmTaxType` | NVARCHAR(2) | 88% | 100% | 100% | 99% | 100% | 100% | 1 | |
| `SacEntry` | INTEGER | <1% | <1% | — | 1% | <1% | — | 10 | |
| `NCMCode` | INTEGER | 99% | 100% | 98% | 98% | 98% | 96% | 1 | |
| `HsnEntry` | INTEGER | 88% | 100% | 100% | 99% | 100% | 100% | 103 | |
| `IsPrscGood` | NVARCHAR(1) | 99% | 95% | 100% | 100% | 96% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 88% | 63% | 100% | 99% | 63% | 100% | 1 | |
| `IndEscala` | NVARCHAR(1) | 87% | 63% | 98% | 97% | 63% | 96% | 1 | |
| `CESTCode` | INTEGER | 82% | 99% | 84% | 37% | 94% | 34% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ListNum` | SMALLINT | <1% | — | — | <1% | — | — | 2 | |
| `UoMNum` | DECIMAL | 88% | 100% | 100% | 99% | 100% | 100% | 3 | |
| `UoMDen` | DECIMAL | 100% | 100% | 100% | 99% | 100% | 100% | 2 | |
| `UoMNum2` | DECIMAL | 88% | 100% | 100% | 99% | 100% | 100% | 2 | |
| `UoMDen2` | DECIMAL | 100% | 100% | 100% | 99% | 100% | 100% | 2 | |
| `U_Remarks` | NVARCHAR(100) | <1% | <1% | <1% | <1% | <1% | <1% | 20 | |
| `U_SchemeAgst` | NVARCHAR(50) | 89% | 100% | 98% | 100% | 100% | 100% | 41 | |
| `U_Disp_Qty` | DECIMAL | 38% | 2% | 80% | 80% | 11% | 86% | 1,515 | |
| `U_Recvd_Qty` | DECIMAL | 35% | 1% | 67% | 47% | <1% | 61% | 1,120 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_FCT1` | DECIMAL | 1% | 3% | <1% | <1% | 4% | <1% | 2 | |
| `U_UNE_FCT2` | DECIMAL | 1% | 3% | <1% | <1% | 4% | <1% | 17 | |
| `U_LNDCSTNO` | NVARCHAR(100) | <1% | <1% | — | — | <1% | — | 2 | |
| `U_UNE_LTS` | DECIMAL | <1% | — | — | — | — | — | 55 | |
| `U_UNE_ACTD` | NVARCHAR(100) | <1% | <1% | — | 2% | 2% | — | 2 | |
| `U_BilltyNumber` | NVARCHAR(100) | <1% | — | — | — | — | — | 4 | |
| `U_ARNO` | NVARCHAR(100) | <1% | — | — | — | — | — | 2 | |
| `U_Sub_Account` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_Purpose` | NVARCHAR(10) | 25% | 83% | 4% | 3% | 85% | — | 5 | |
| `U_F_Year` | NVARCHAR(10) | <1% | — | — | — | — | — | 2 | |
| `U_BiltyDate` | TIMESTAMP | <1% | n/a | 22% | 15% | n/a | 58% | 60 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BiltyDate` | OIL, BEV | **MART** |
| `U_UNE_CALI` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TargetType`** (5 values) — `-1`×93,211, `14`×1,968, `NULL`×1,494, `13`×1,494, `234000031`×3
- **`BaseType`** (4 values) — `17`×46,364, `15`×35,898, `-1`×14,414, `13`×1,494
- **`LineStatus`** (2 values) — `O`×93,758, `C`×4,412
- **`Currency`** (4 values) — `INR`×80,750, `NULL`×17,409, `USD`×9, `∅`×2
- **`Rate`** (8 values) — `0.000000`×97,909, `NULL`×252, `86.100000`×4, `85.950000`×1, `86.050000`×1, `85.400000`×1, `86.700000`×1, `84.700000`×1
- **`DiscPrcnt`** (10 values) — `0.000000`×98,154, `NULL`×5, `-18.000000`×2, `-696.710000`×2, `-25.000000`×2, `5.500000`×1, `82.000000`×1, `-542847.430000`×1, `-2952752.350000`×1, `80.000000`×1
- **`TotalFrgn`** (8 values) — `0.000000`×98,161, `211382.250000`×3, `132240.600000`×1, `131839.650000`×1, `342439.500000`×1, `420146.430000`×1, `52695.750000`×1, `134737.500000`×1
- **`OpenSumFC`** (8 values) — `0.000000`×98,162, `211382.250000`×2, `134737.500000`×1, `420146.430000`×1, `342439.500000`×1, `132240.600000`×1, `131839.650000`×1, `52695.750000`×1
- **`TreeType`** (4 values) — `P`×59,161, `N`×15,831, `I`×11,930, `S`×11,248
- **`TaxStatus`** (1 values) — `Y`×98,170
- **`UseBaseUn`** (2 values) — `N`×85,456, `Y`×12,714
- **`InvntSttus`** (2 values) — `O`×93,758, `C`×4,412
- **`VatPrcnt`** (5 values) — `5.000000`×80,594, `0.000000`×11,090, `12.000000`×3,939, `18.000000`×2,545, `0.100000`×2
- **`VatGroup`** (9 values) — `IGST@5`×46,879, `NULL`×16,794, `CG+SG@5`×15,282, `∅`×14,281, `IGST@12`×2,685, `IGST@18`×1,149, `CG+SG@12`×725, `CG+SG@18`×373, `IGST@0`×2
- **`VolUnit`** (2 values) — `4`×86,668, `NULL`×11,502
- **`Factor1`** (2 values) — `1.000000`×86,668, `0.000000`×11,502
- **`Factor2`** (17 values) — `1.000000`×85,008, `0.000000`×11,502, `4.000000`×730, `16.000000`×408, `20.000000`×239, `10.000000`×83, `12.000000`×75, `24.000000`×58, `15.000000`×18, `5.000000`×11, `3.000000`×10, `9.000000`×7, `6.000000`×6, `35.000000`×5, `40.000000`×4, `2.000000`×4, `36.000000`×2
- **`Factor3`** (4 values) — `1.000000`×86,666, `0.000000`×11,502, `4.000000`×1, `10.000000`×1
- **`Factor4`** (2 values) — `1.000000`×86,668, `0.000000`×11,502
- **`UpdInvntry`** (1 values) — `Y`×98,170
- **`FinncPriod`** (24 values) — `9`×13,254, `6`×11,078, `7`×8,887, `8`×7,728, `10`×7,487, `12`×3,656, `15`×3,509, `17`×3,508, `20`×3,478, `23`×3,317, `14`×3,065, `11`×3,022, `19`×2,943, `22`×2,899, `16`×2,889, `24`×2,812, `21`×2,722, `18`×2,716, `25`×2,336, `41`×1,806, `42`×1,555, `44`×1,429, `43`×1,170, `45`×904
- **`ObjType`** (1 values) — `13`×98,170
- **`IsAqcuistn`** (1 values) — `N`×98,170
- **`DistribSum`** (2 values) — `0.000000`×98,167, `7500.000000`×3
- **`DstrbSumSC`** (2 values) — `0.000000`×98,167, `7500.000000`×3
- **`GrssProfFC`** (8 values) — `0.000000`×98,161, `211382.250000`×3, `52695.750000`×1, `131839.650000`×1, `132240.600000`×1, `342439.500000`×1, `420146.430000`×1, `134737.500000`×1
- **`DropShip`** (2 values) — `N`×97,346, `Y`×824
- **`TaxCode`** (10 values) — `IGST@5`×48,567, `CG+SG@5`×32,026, `Exampt`×11,078, `IGST@12`×2,320, `CG+SG@12`×1,620, `CG+SG@18`×1,482, `IGST@18`×1,063, `IGST@0`×9, `CG+SG@0`×3, `IGST@0.1`×2
- **`TaxType`** (1 values) — `Y`×98,170
- **`BackOrdr`** (2 values) — `Y`×83,636, `NULL`×14,534
- **`FreeTxt`** (3 values) — `∅`×68,178, `NULL`×29,991, ```×1
- **`PickStatus`** (1 values) — `N`×98,170
- **`TrnsCode`** (2 values) — `-1`×97,350, `NULL`×820
- **`WtLiable`** (2 values) — `N`×98,066, `Y`×104
- **`DeferrTax`** (1 values) — `N`×98,170
- **`unitMsr`** (11 values) — `PCS`×82,082, `NULL`×14,281, `SET`×1,123, `LTR`×289, `NOS`×148, `MTR`×115, `KGS`×57, `GMS`×47, `DRM`×20, `MTS`×7, `∅`×1
- **`NumPerMsr`** (3 values) — `1.000000`×86,661, `0.000000`×11,502, `1098.900000`×7
- **`CEECFlag`** (1 values) — `S`×98,170
- **`CountryOrg`** (3 values) — `NULL`×98,168, `OM`×1, `∅`×1
- **`LineType`** (1 values) — `R`×98,170
- **`OwnerCode`** (4 values) — `NULL`×95,561, `20`×2,566, `2`×27, `14`×16
- **`ConsumeFCT`** (3 values) — `Y`×50,186, `N`×36,482, `NULL`×11,502
- **`StockSumFc`** (8 values) — `0.000000`×98,161, `211382.250000`×3, `134737.500000`×1, `420146.430000`×1, `342439.500000`×1, `132240.600000`×1, `131839.650000`×1, `52695.750000`×1
- **`BasePrice`** (1 values) — `E`×98,170
- **`GTotalFC`** (8 values) — `0.000000`×98,161, `211382.250000`×3, `52695.750000`×1, `131839.650000`×1, `132240.600000`×1, `342439.500000`×1, `420146.430000`×1, `134737.500000`×1
- **`DistribExp`** (2 values) — `Y`×75,029, `N`×23,141
- **`DescOW`** (2 values) — `N`×97,881, `Y`×289
- **`DetailsOW`** (2 values) — `N`×98,163, `Y`×7
- **`GrossBase`** (4 values) — `-6`×68,402, `NULL`×11,939, `-11`×11,502, `-1`×6,327
- **`TaxOnly`** (2 values) — `N`×97,604, `Y`×566
- **`WtCalced`** (1 values) — `N`×98,170
- **`CiOppLineN`** (1 values) — `-1`×98,170
- **`ChgAsmBoMW`** (2 values) — `N`×86,668, `NULL`×11,502
- **`OcrCode2`** (4 values) — `NULL`×98,152, `11-2024`×12, `06-2025`×5, `04-2024`×1
- **`PostTax`** (1 values) — `Y`×98,170
- **`Excisable`** (2 values) — `N`×86,668, `NULL`×11,502
- **`CogsOcrCo2`** (4 values) — `NULL`×98,152, `11-2024`×12, `06-2025`×5, `04-2024`×1
- **`LocCode`** (3 values) — `2`×55,549, `1`×31,920, `3`×10,701
- **`unitMsr2`** (10 values) — `PCS`×68,243, `NULL`×29,192, `LTR`×289, `NOS`×132, `KGS`×111, `MTR`×106, `SET`×42, `∅`×34, `DRM`×15, `GMS`×6
- **`NumPerMsr2`** (2 values) — `1.000000`×86,668, `0.000000`×11,502
- **`SpecPrice`** (2 values) — `N`×98,154, `R`×16
- **`isSrvCall`** (1 values) — `N`×98,170
- **`PcDocType`** (1 values) — `-1`×98,170
- **`LinManClsd`** (1 values) — `N`×98,170
- **`VatGrpSrc`** (3 values) — `N`×45,031, `D`×40,873, `M`×12,266
- **`NoInvtryMv`** (2 values) — `N`×98,133, `Y`×37
- **`UomEntry`** (4 values) — `-1`×86,392, `0`×11,502, `2`×269, `1`×7
- **`UomEntry2`** (3 values) — `-1`×86,392, `0`×11,502, `2`×276
- **`UomCode`** (4 values) — `Manual`×86,392, `NULL`×11,502, `LTR`×269, `MTS`×7
- **`UomCode2`** (3 values) — `Manual`×86,392, `NULL`×11,502, `LTR`×276
- **`NeedQty`** (1 values) — `N`×98,170
- **`PartRetire`** (1 values) — `N`×98,170
- **`EnSetCost`** (1 values) — `N`×98,170
- **`DistribIS`** (1 values) — `N`×98,170
- **`IsByPrdct`** (1 values) — `N`×98,170
- **`ItemType`** (1 values) — `4`×98,170
- **`PriceEdit`** (1 values) — `N`×98,170
- **`LinePoPrss`** (1 values) — `N`×98,170
- **`FreeChrgBP`** (1 values) — `N`×98,170
- **`TaxRelev`** (1 values) — `Y`×98,170
- **`ThirdParty`** (1 values) — `N`×98,170
- **`InvQtyOnly`** (1 values) — `N`×98,170
- **`ReturnRsn`** (1 values) — `-1`×98,170
- **`ReturnAct`** (2 values) — `-1`×67,566, `1`×30,604
- **`ItmTaxType`** (2 values) — `GR`×86,668, `NULL`×11,502
- **`SacEntry`** (11 values) — `NULL`×97,746, `5`×326, `1`×30, `34`×19, `45`×19, `-398`×15, `7`×6, `-319`×4, `-419`×2, `33`×2, `-309`×1
- **`NCMCode`** (2 values) — `-1`×97,346, `NULL`×824
- **`IsPrscGood`** (2 values) — `N`×97,485, `NULL`×685
- **`IsCstmAct`** (1 values) — `N`×98,170
- **`TaxAmtSrc`** (2 values) — `S`×86,001, `NULL`×12,169
- **`IndEscala`** (2 values) — `N`×85,283, `NULL`×12,887
- **`CESTCode`** (2 values) — `-1`×80,952, `NULL`×17,218
- **`CUSplit`** (1 values) — `N`×98,170
- **`RevCharge`** (1 values) — `N`×98,170
- **`ListNum`** (3 values) — `NULL`×98,154, `4`×9, `1`×7
- **`UoMNum`** (3 values) — `1.000000`×86,661, `0.000000`×11,502, `1098.900000`×7
- **`UoMDen`** (2 values) — `1.000000`×98,023, `0.000000`×147
- **`UoMNum2`** (2 values) — `1.000000`×86,668, `0.000000`×11,502
- **`UoMDen2`** (2 values) — `1.000000`×98,023, `0.000000`×147
- **`U_Remarks`** (21 values) — `NULL`×98,101, `123`×19, `Rent Dec. 2024`×6, `Rent . April 25`×6, `Rent . FEB 2024`×4, `BEING AGAINST ACADEMY CLAIM`×4, `BEING AGAINST CHUNNI KALAN ACDEMY`×4, `Rent Aug 2025`×4, `Rent 2026`×4, `Rent`×3, `Rent . july 2024`×2, `Rent . May 25`×2, `ACADEMY CLAIM CHUNNI KALAN`×2, `Rent . June 25`×2, `Rent Oct. 2024`×1, `BEING AGAINST ACADEMY NIHAL SINGH WALA`×1, `GIFT MANGO`×1, `Suresh`×1, `BEING AGAINST SHORATAGE 6241838`×1, `Rent 2025`×1, `Rent Nov. 2024`×1
- **`U_UNE_SCHI`** (2 values) — `N`×98,112, `Y`×58
- **`U_UNE_CALI`** (1 values) — `Y`×98,170
- **`U_UNE_CUNT`** (1 values) — `Y`×98,170
- **`U_UNE_FCT1`** (3 values) — `NULL`×80,180, `0.000000`×16,967, `1.000000`×1,023
- **`U_UNE_FCT2`** (18 values) — `NULL`×80,181, `0.000000`×16,966, `4.000000`×379, `16.000000`×225, `1.000000`×222, `20.000000`×109, `12.000000`×41, `10.000000`×14, `3.000000`×6, `24.000000`×5, `48.000000`×5, `45.000000`×4, `15.000000`×3, `5.000000`×3, `9.000000`×2, `6.000000`×2, `70.000000`×2, `40.000000`×1
- **`U_LNDCSTNO`** (3 values) — `NULL`×98,168, ```×1, `FG0000223FG0000223`×1
- **`U_UNE_ACTD`** (3 values) — `NULL`×97,423, `1102007`×738, `1102001`×9
- **`U_BilltyNumber`** (5 values) — `NULL`×98,166, `6407`×1, `6072`×1, `1731`×1, `6408`×1
- **`U_ARNO`** (3 values) — `NULL`×98,165, `41350`×3, `H`×2
- **`U_Sub_Account`** (2 values) — `NULL`×98,166, `BST`×4
- **`U_Purpose`** (6 values) — `NULL`×73,210, `SALE`×24,515, `CONSUMABLE`×423, `-`×9, `BST`×7, `RETURNABLE`×6
- **`U_F_Year`** (3 values) — `NULL`×98,163, `2024-25`×5, `2023-24`×2
