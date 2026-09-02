# `PCH1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 40,247 | 4,744 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 21,854 | 2,286 | `DocDate` | 2025-01-01 → 2026-08-24 |
| BEV | 10,763 | 1,791 | `DocDate` | 2024-09-30 → 2026-08-13 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 16,334 | |
| `LineNum` | INTEGER | 61% | 78% | 72% | 59% | 61% | 79% | 94 | |
| `TargetType` | INTEGER | 99% | 99% | 100% | 100% | 99% | 100% | 3 | |
| `TrgetEntry` | INTEGER | 5% | 5% | 6% | 6% | 4% | 12% | 1,004 | |
| `BaseRef` | NVARCHAR(16) | 56% | 66% | 60% | 64% | 41% | 67% | 10,355 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BaseEntry` | INTEGER | 56% | 66% | 60% | 64% | 41% | 67% | 10,322 | |
| `BaseLine` | INTEGER | 33% | 54% | 21% | 38% | 22% | 13% | 56 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItemCode` | NVARCHAR(50) | 43% | 67% | 27% | 49% | 54% | 16% | 1,119 | |
| `Dscription` | NVARCHAR(200) | 66% | 80% | 62% | 70% | 67% | 71% | 1,953 | |
| `Quantity` | DECIMAL | 43% | 67% | 27% | 49% | 54% | 16% | 3,388 | |
| `ShipDate` | TIMESTAMP | 35% | 65% | 25% | 49% | 53% | 16% | 645 | |
| `OpenQty` | DECIMAL | 42% | 66% | 27% | 48% | 54% | 16% | 3,390 | |
| `Price` | DECIMAL | 98% | 100% | 100% | 97% | 97% | 100% | 15,857 | |
| `Currency` | NVARCHAR(3) | 98% | 100% | 100% | 97% | 97% | 100% | 4 | |
| `Rate` | DECIMAL | <1% | <1% | — | <1% | — | — | 72 | |
| `DiscPrcnt` | DECIMAL | <1% | 2% | <1% | <1% | <1% | — | 36 | |
| `LineTotal` | DECIMAL | 98% | 100% | 100% | 97% | 97% | 100% | 20,201 | |
| `TotalFrgn` | DECIMAL | <1% | <1% | — | <1% | — | — | 109 | |
| `OpenSum` | DECIMAL | 95% | 97% | 98% | 96% | 81% | 95% | 20,183 | |
| `OpenSumFC` | DECIMAL | <1% | <1% | — | <1% | — | — | 109 | |
| `WhsCode` | NVARCHAR(8) | 43% | 67% | 27% | 49% | 54% | 16% | 33 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 91 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 161 | |
| `TaxStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PriceBefDi` | DECIMAL | 98% | 100% | 100% | 97% | 97% | 100% | 15,838 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 685 | |
| `OpenCreQty` | DECIMAL | 42% | 65% | 27% | 48% | 54% | 16% | 3,390 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseCard` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 1,164 | |
| `TotalSumSy` | DECIMAL | 98% | 100% | 100% | 97% | 97% | 100% | 20,201 | |
| `OpenSumSys` | DECIMAL | 95% | 97% | 98% | 96% | 81% | 95% | 20,183 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `OcrCode` | NVARCHAR(8) | 96% | 99% | 99% | 100% | 96% | 98% | 63 | |
| `VatPrcnt` | DECIMAL | 62% | 94% | 64% | 61% | 87% | 73% | 5 | |
| `VatGroup` | NVARCHAR(8) | 18% | 54% | 13% | 24% | 20% | 7% | 9 | |
| `PriceAfVAT` | DECIMAL | 98% | 100% | 100% | 97% | 97% | 100% | 17,130 | |
| `VolUnit` | SMALLINT | 43% | 67% | 27% | 49% | 54% | 16% | 1 | |
| `Factor1` | DECIMAL | 43% | 67% | 27% | 49% | 54% | 16% | 2 | |
| `Factor2` | DECIMAL | 43% | 67% | 27% | 49% | 54% | 16% | 11 | |
| `Factor3` | DECIMAL | 43% | 67% | 27% | 49% | 54% | 16% | 2 | |
| `Factor4` | DECIMAL | 43% | 67% | 27% | 49% | 54% | 16% | 2 | |
| `PackQty` | DECIMAL | 43% | 67% | 27% | 49% | 54% | 16% | 2,705 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDocNum` | INTEGER | 58% | 68% | 61% | 65% | 59% | 71% | 10,522 | |
| `BaseAtCard` | NVARCHAR(200) | 48% | 65% | 57% | 64% | 41% | 67% | 8,995 | |
| `VatSum` | DECIMAL | 60% | 93% | 64% | 58% | 83% | 73% | 16,306 | |
| `VatSumFrgn` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `VatSumSy` | DECIMAL | 60% | 93% | 64% | 58% | 83% | 73% | 16,306 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DedVatSum` | DECIMAL | 60% | 93% | 64% | 58% | 83% | 73% | 16,306 | |
| `DedVatSumF` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `DedVatSumS` | DECIMAL | 60% | 93% | 64% | 58% | 83% | 73% | 16,306 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DistribSum` | DECIMAL | 1% | <1% | 2% | <1% | — | <1% | 301 | |
| `DstrbSumSC` | DECIMAL | 1% | <1% | 2% | <1% | — | <1% | 301 | |
| `VisOrder` | INTEGER | 59% | 78% | 71% | 58% | 60% | 77% | 56 | |
| `INMPrice` | DECIMAL | 39% | 65% | 26% | 45% | 36% | 12% | 4,427 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Address` | NVARCHAR(254) | 66% | 97% | 44% | 68% | 81% | 22% | 25 | |
| `TaxCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 16 | |
| `TaxType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OrigItem` | NVARCHAR(50) | 1% | 1% | <1% | 2% | <1% | <1% | 175 | |
| `FreeTxt` | NVARCHAR(100) | — | <1% | — | — | — | — | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TrnsCode` | SMALLINT | 98% | 98% | 98% | 99% | 83% | 96% | 1 | |
| `VatAppld` | DECIMAL | 4% | 4% | 5% | 5% | 4% | 11% | 1,470 | |
| `VatAppldSC` | DECIMAL | 4% | 4% | 5% | 5% | 4% | 11% | 1,470 | |
| `BaseQty` | DECIMAL | 41% | 65% | 26% | 47% | 36% | 12% | 3,350 | |
| `BaseOpnQty` | DECIMAL | 43% | 67% | 27% | 49% | 53% | 16% | 3,388 | |
| `WtLiable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineVat` | DECIMAL | 60% | 93% | 64% | 58% | 83% | 73% | 16,306 | |
| `LineVatlF` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `LineVatS` | DECIMAL | 60% | 93% | 64% | 58% | 83% | 73% | 16,306 | |
| `unitMsr` | NVARCHAR(100) | 43% | 67% | 27% | 49% | 54% | 16% | 11 | |
| `NumPerMsr` | DECIMAL | 43% | 67% | 27% | 49% | 54% | 16% | 3 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CountryOrg` | NVARCHAR(3) | <1% | — | — | — | — | — | 5 | |
| `StckDstSum` | DECIMAL | <1% | <1% | <1% | <1% | — | <1% | 146 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Text` | NCLOB | <1% | — | — | <1% | — | — | 0 | |
| `OwnerCode` | INTEGER | <1% | — | <1% | <1% | — | — | 5 | |
| `ConsumeFCT` | NVARCHAR(1) | 43% | 67% | 27% | 49% | 54% | 16% | 1 | |
| `LstByDsSum` | DECIMAL | 1% | <1% | 2% | <1% | — | <1% | 299 | |
| `StckINMPr` | DECIMAL | <1% | <1% | <1% | <1% | — | <1% | 118 | |
| `LstBINMPr` | DECIMAL | 1% | <1% | 2% | <1% | — | <1% | 256 | |
| `StckDstSc` | DECIMAL | <1% | <1% | <1% | <1% | — | <1% | 146 | |
| `LstByDsSc` | DECIMAL | 1% | <1% | 2% | <1% | — | <1% | 299 | |
| `StockSum` | DECIMAL | 39% | 65% | 26% | 45% | 36% | 12% | 9,052 | |
| `StockSumFc` | DECIMAL | <1% | — | — | <1% | — | — | 67 | |
| `StockSumSc` | DECIMAL | 39% | 65% | 26% | 45% | 36% | 12% | 9,052 | |
| `StckSumApp` | DECIMAL | <1% | 1% | <1% | 2% | <1% | — | 224 | |
| `StckAppFc` | DECIMAL | <1% | — | — | <1% | — | — | 25 | |
| `StckAppSc` | DECIMAL | <1% | 1% | <1% | 2% | <1% | — | 224 | |
| `ShipToCode` | NVARCHAR(50) | 33% | 63% | 23% | 47% | 36% | 12% | 373 | |
| `ShipToDesc` | NVARCHAR(254) | 43% | 67% | 27% | 49% | 54% | 16% | 21 | |
| `StckAppD` | DECIMAL | <1% | — | — | — | — | — | 22 | |
| `StckAppDSC` | DECIMAL | <1% | — | — | — | — | — | 22 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GTotal` | DECIMAL | 98% | 100% | 100% | 97% | 97% | 100% | 21,617 | |
| `GTotalFC` | DECIMAL | <1% | <1% | — | <1% | — | — | 113 | |
| `GTotalSC` | DECIMAL | 98% | 100% | 100% | 97% | 97% | 100% | 21,617 | |
| `DistribExp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `TaxOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsOcrCod` | NVARCHAR(8) | 6% | 2% | 2% | — | — | — | 2 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ChgAsmBoMW` | NVARCHAR(1) | 43% | 67% | 27% | 49% | 54% | 16% | 1 | |
| `ActDelDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 685 | |
| `OcrCode2` | NVARCHAR(8) | 74% | 35% | 90% | 81% | 57% | 92% | 30 | |
| `OcrCode3` | NVARCHAR(8) | 70% | 34% | 89% | 79% | 47% | 92% | 16 | |
| `OcrCode4` | NVARCHAR(8) | 21% | 14% | 4% | 26% | 41% | 4% | 21 | |
| `OcrCode5` | NVARCHAR(8) | 66% | 24% | 90% | 62% | 36% | 92% | 26 | |
| `TaxDistSum` | DECIMAL | <1% | — | <1% | — | — | — | 2 | |
| `TaxDistSSC` | DECIMAL | <1% | — | <1% | — | — | — | 2 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excisable` | NVARCHAR(1) | 43% | 67% | 27% | 49% | 54% | 16% | 1 | |
| `AssblValue` | DECIMAL | 3% | — | <1% | — | — | — | 633 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `unitMsr2` | NVARCHAR(100) | 26% | 60% | 15% | 29% | 54% | 10% | 9 | |
| `NumPerMsr2` | DECIMAL | 43% | 67% | 27% | 49% | 54% | 16% | 3 | |
| `SpecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isSrvCall` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcDocType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatGrpSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `NoInvtryMv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UomEntry` | INTEGER | 43% | 67% | 27% | 49% | 54% | 16% | 4 | |
| `UomEntry2` | INTEGER | 43% | 67% | 27% | 49% | 54% | 16% | 4 | |
| `UomCode` | NVARCHAR(20) | 43% | 67% | 27% | 49% | 54% | 16% | 3 | |
| `UomCode2` | NVARCHAR(20) | 43% | 67% | 27% | 49% | 54% | 16% | 3 | |
| `NeedQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartRetire` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQty` | DECIMAL | 43% | 67% | 27% | 49% | 54% | 16% | 3,412 | |
| `OpenInvQty` | DECIMAL | 42% | 65% | 27% | 48% | 54% | 16% | 3,401 | |
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
| `GPBefDisc` | DECIMAL | 98% | 100% | 100% | 97% | 97% | 100% | 17,134 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItmTaxType` | NVARCHAR(2) | 43% | 67% | 27% | 49% | 54% | 16% | 2 | |
| `SacEntry` | INTEGER | 33% | 27% | 41% | 33% | 34% | 59% | 168 | |
| `NCMCode` | INTEGER | 98% | 98% | 98% | 99% | 83% | 96% | 1 | |
| `HsnEntry` | INTEGER | 43% | 67% | 27% | 49% | 54% | 16% | 279 | |
| `IsPrscGood` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 98% | 100% | 99% | 98% | 99% | 99% | 1 | |
| `IndEscala` | NVARCHAR(1) | 99% | 100% | 100% | 98% | 100% | 100% | 1 | |
| `CESTCode` | INTEGER | 33% | 63% | 24% | 47% | 36% | 12% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMNum` | DECIMAL | 43% | 67% | 27% | 49% | 54% | 16% | 3 | |
| `UoMDen` | DECIMAL | 80% | 87% | 70% | 49% | 54% | 16% | 2 | |
| `UoMNum2` | DECIMAL | 43% | 67% | 27% | 49% | 54% | 16% | 3 | |
| `UoMDen2` | DECIMAL | 80% | 87% | 70% | 49% | 54% | 16% | 2 | |
| `U_Remarks` | NVARCHAR(100) | 36% | 16% | 48% | 41% | 8% | 70% | 7,935 | |
| `U_SchemeAgst` | NVARCHAR(50) | 41% | 67% | 27% | 49% | 50% | 14% | 36 | |
| `U_UTL_ST_TAXCD` | NVARCHAR(100) | <1% | <1% | <1% | <1% | — | 1% | 4 | |
| `U_UTL_ST_IGST` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `U_UTL_ST_IGAMT` | DECIMAL | <1% | — | — | <1% | — | — | 3 | |
| `U_Disp_Qty` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `U_Recvd_Qty` | DECIMAL | 2% | <1% | <1% | 3% | <1% | <1% | 704 | |
| `U_cartonpc` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 2 | |
| `U_carton` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 2 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_FCT1` | DECIMAL | <1% | <1% | <1% | <1% | 2% | 1% | 2 | |
| `U_UNE_FCT2` | DECIMAL | <1% | <1% | <1% | <1% | 2% | 1% | 17 | |
| `U_UNE_LTS` | DECIMAL | 18% | 23% | 50% | 19% | 27% | 71% | 2,725 | |
| `U_UNE_ACTD` | NVARCHAR(100) | 2% | 3% | — | 1% | 17% | — | 4 | |
| `U_BilltyNumber` | NVARCHAR(100) | 18% | 20% | 36% | 20% | 23% | 55% | 4,847 | |
| `U_ARNO` | NVARCHAR(100) | 23% | 24% | 57% | 22% | 27% | 71% | 7,323 | |
| `U_Sub_Account` | NVARCHAR(20) | 16% | <1% | 41% | 18% | 4% | 67% | 3 | |
| `U_CardCode` | NVARCHAR(15) | 19% | 24% | 56% | 19% | 27% | 71% | 362 | |
| `U_Purpose` | NVARCHAR(10) | <1% | <1% | <1% | — | 1% | — | 2 | |
| `U_F_Year` | NVARCHAR(10) | <1% | — | — | — | — | — | 2 | |
| `U_PRCHSE_VAL` | DECIMAL | <1% | — | — | — | — | — | 5 | |
| `U_BiltyDate` | TIMESTAMP | <1% | n/a | 15% | 5% | n/a | 55% | 46 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BiltyDate` | OIL, BEV | **MART** |
| `U_UNE_CALI` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TargetType`** (4 values) — `-1`×37,805, `19`×1,754, `18`×344, `NULL`×344
- **`BaseType`** (3 values) — `20`×22,125, `-1`×17,778, `18`×344
- **`LineStatus`** (2 values) — `O`×39,492, `C`×755
- **`Currency`** (5 values) — `INR`×39,184, `NULL`×950, `USD`×83, `EUR`×28, `AUD`×2
- **`TreeType`** (2 values) — `N`×36,634, `P`×3,613
- **`TaxStatus`** (1 values) — `Y`×40,247
- **`UseBaseUn`** (2 values) — `N`×39,529, `Y`×718
- **`InvntSttus`** (2 values) — `O`×39,492, `C`×755
- **`VatPrcnt`** (5 values) — `0.000000`×15,129, `18.000000`×12,532, `5.000000`×11,015, `12.000000`×1,559, `28.000000`×12
- **`VatGroup`** (10 values) — `∅`×28,120, `NULL`×4,963, `CG+SG@18`×3,224, `CG+SG@0`×2,076, `IGST@18`×953, `IGST@0`×367, `CG+SG@5`×216, `CG+SG@12`×158, `IGST@5`×137, `IGST@12`×33
- **`VolUnit`** (2 values) — `NULL`×22,961, `4`×17,286
- **`Factor1`** (2 values) — `0.000000`×22,961, `1.000000`×17,286
- **`Factor2`** (11 values) — `0.000000`×22,961, `1.000000`×17,250, `4.000000`×10, `16.000000`×8, `20.000000`×6, `12.000000`×4, `2.000000`×3, `6.000000`×2, `5.000000`×1, `9.000000`×1, `35.000000`×1
- **`Factor3`** (2 values) — `0.000000`×22,961, `1.000000`×17,286
- **`Factor4`** (2 values) — `0.000000`×22,961, `1.000000`×17,286
- **`UpdInvntry`** (1 values) — `Y`×40,247
- **`FinncPriod`** (24 values) — `12`×2,658, `25`×2,113, `23`×2,015, `18`×1,999, `11`×1,995, `9`×1,987, `10`×1,947, `8`×1,893, `20`×1,892, `19`×1,861, `22`×1,838, `43`×1,741, `17`×1,732, `21`×1,718, `15`×1,631, `7`×1,528, `24`×1,524, `42`×1,487, `44`×1,477, `16`×1,474, `41`×1,307, `14`×1,284, `6`×949, `45`×197
- **`ObjType`** (1 values) — `18`×40,247
- **`IsAqcuistn`** (1 values) — `N`×40,247
- **`DropShip`** (2 values) — `N`×39,539, `Y`×708
- **`TaxCode`** (16 values) — `Exampt`×9,935, `CG+SG@18`×7,656, `IGST@18`×4,680, `IGST@5`×4,651, `CG+SG@0`×4,041, `RIGST@5`×3,000, `GST05R`×2,900, `IGST@0`×1,141, `IGST@12`×782, `CG+SG@12`×777, `CG+SG@5`×415, `RISGT@18`×135, `RCGSG@18`×72, `RCGSG@5`×50, `CG+SG@28`×8, `IGST@28`×4
- **`TaxType`** (1 values) — `Y`×40,247
- **`PickStatus`** (1 values) — `N`×40,247
- **`TrnsCode`** (2 values) — `-1`×39,538, `NULL`×709
- **`WtLiable`** (2 values) — `N`×26,450, `Y`×13,797
- **`DeferrTax`** (1 values) — `N`×40,247
- **`unitMsr`** (12 values) — `NULL`×22,981, `PCS`×16,023, `MTS`×854, `KGS`×182, `LTR`×72, `MTR`×67, `GMS`×19, `∅`×15, `MTRS`×13, `NOS`×13, `DRM`×6, `KG`×2
- **`NumPerMsr`** (3 values) — `0.000000`×22,961, `1.000000`×16,432, `1098.900000`×854
- **`CEECFlag`** (1 values) — `S`×40,247
- **`CountryOrg`** (6 values) — `NULL`×40,194, `AE`×23, `ES`×14, `AU`×13, `AT`×2, `XX`×1
- **`LineType`** (1 values) — `R`×40,247
- **`OwnerCode`** (6 values) — `NULL`×40,038, `20`×116, `14`×89, `2`×2, `6`×1, `4`×1
- **`ConsumeFCT`** (2 values) — `NULL`×22,961, `N`×17,286
- **`StckAppFc`** (25 values) — `0.000000`×40,221, `243.555000`×2, `175.792000`×2, `426.295600`×1, `0.050800`×1, `3051.556800`×1, `836.330400`×1, `597.692800`×1, `1768.861800`×1, `599.890200`×1, `3500.000200`×1, `132.588000`×1, `1731.551200`×1, `5000.000000`×1, `11096.297200`×1, `800.359200`×1, `2903.694500`×1, `1757.920000`×1, `855.814800`×1, `6500.000000`×1, `1731.138500`×1, `3018.583200`×1, `192.920000`×1, `994.562400`×1, `216.049400`×1
- **`StckAppD`** (22 values) — `0.000000`×40,225, `243.562700`×2, `597.701600`×1, `132.590000`×1, `836.346600`×1, `3018.663700`×1, `192.920000`×1, `800.382000`×1, `3051.641900`×1, `5000.000000`×1, `1731.574300`×1, `175.792700`×1, `1768.861500`×1, `1757.942900`×1, `1731.138500`×1, `2903.698000`×1, `11096.302000`×1, `855.840400`×1, `426.302800`×1, `175.787200`×1, `994.560000`×1, `599.898500`×1
- **`StckAppDSC`** (22 values) — `0.000000`×40,225, `243.562700`×2, `192.920000`×1, `994.560000`×1, `3018.663700`×1, `132.590000`×1, `597.701600`×1, `599.898500`×1, `855.840400`×1, `426.302800`×1, `175.787200`×1, `800.382000`×1, `3051.641900`×1, `5000.000000`×1, `836.346600`×1, `11096.302000`×1, `2903.698000`×1, `1731.574300`×1, `175.792700`×1, `1768.861500`×1, `1757.942900`×1, `1731.138500`×1
- **`BasePrice`** (1 values) — `E`×40,247
- **`DistribExp`** (2 values) — `Y`×38,646, `N`×1,601
- **`DescOW`** (2 values) — `N`×40,177, `Y`×70
- **`DetailsOW`** (2 values) — `N`×40,241, `Y`×6
- **`TaxOnly`** (2 values) — `N`×39,751, `Y`×496
- **`WtCalced`** (1 values) — `N`×40,247
- **`CogsOcrCod`** (3 values) — `NULL`×37,722, `BST`×2,524, `GHEE`×1
- **`CiOppLineN`** (1 values) — `-1`×40,247
- **`ChgAsmBoMW`** (2 values) — `NULL`×22,961, `N`×17,286
- **`OcrCode2`** (30 values) — `NULL`×10,526, `10-2024`×1,723, `11-2024`×1,512, `12-2024`×1,499, `01-2026`×1,445, `03-2025`×1,442, `08-2025`×1,406, `01-2025`×1,352, `07-2025`×1,346, `05-2025`×1,332, `02-2026`×1,326, `09-2025`×1,322, `10-2025`×1,316, `03-2026`×1,310, `12-2025`×1,287, `11-2025`×1,279, `04-2026`×1,278, `05-2026`×1,253, `04-2025`×1,238, `02-2025`×1,233, `06-2025`×1,133, `06-2026`×1,100, `07-2026`×729, `09-2024`×537, `08-2024`×104, `04-2024`×68, `06-2024`×50, `08-2026`×45, `07-2024`×37, `05-2024`×18
- **`OcrCode3`** (17 values) — `NULL`×11,948, `Del Bkhp`×8,322, `Factory`×8,055, `BackOff`×4,222, `FACT_COM`×2,046, `Sales`×1,983, `Sales RE`×1,745, `Med MKT`×591, `OTE`×386, `Transprt`×245, `Del Mayp`×244, `NPD1`×205, `NPD3`×182, `NPD2`×63, `Interest`×5, `Sal CF`×3, `R & D`×2
- **`OcrCode4`** (22 values) — `NULL`×31,673, `Admin`×2,695, `E-COM`×1,878, `IT`×872, `MT`×487, `CSD`×453, `GT`×429, `DIGTAL M`×398, `Legal`×268, `Accounts`×258, `ROI`×194, `CAL CNTR`×187, `POP`×177, `HR_DEPT`×72, `IMPORT`×56, `MIS`×54, `GP-GDWN`×49, `EXPORT`×25, `HORECA`×14, `BankChgs`×4, `SOCIAL M`×3, `PVT LOAN`×1
- **`OcrCode5`** (27 values) — `NULL`×13,661, `HR`×12,487, `DL`×9,226, `PB`×2,521, `UP`×473, `MH`×313, `WB`×228, `TE`×175, `RJ`×173, `KN`×153, `UK`×147, `GJ`×135, `JK`×122, `AS`×70, `TN`×68, `MP`×55, `GO`×52, `KE`×39, `CD`×34, `AP`×29, `KR`×29, `HP`×21, `JH`×15, `OR`×11, `BH`×5, `CH`×4, `NG`×1
- **`TaxDistSum`** (2 values) — `0.000000`×40,246, `1170.000000`×1
- **`TaxDistSSC`** (2 values) — `0.000000`×40,246, `1170.000000`×1
- **`PostTax`** (1 values) — `Y`×40,247
- **`Excisable`** (2 values) — `NULL`×22,961, `N`×17,286
- **`LocCode`** (5 values) — `2`×27,609, `1`×9,981, `3`×2,205, `5`×439, `4`×13
- **`unitMsr2`** (10 values) — `NULL`×28,939, `PCS`×9,313, `∅`×931, `LTR`×900, `MTR`×78, `KGS`×58, `NOS`×9, `MTS`×8, `DRM`×6, `GMS`×5
- **`NumPerMsr2`** (3 values) — `0.000000`×22,961, `1.000000`×17,278, `1098.900000`×8
- **`SpecPrice`** (1 values) — `N`×40,247
- **`isSrvCall`** (1 values) — `N`×40,247
- **`PcDocType`** (1 values) — `-1`×40,247
- **`LinManClsd`** (1 values) — `N`×40,247
- **`VatGrpSrc`** (3 values) — `M`×28,633, `N`×11,435, `D`×179
- **`NoInvtryMv`** (2 values) — `N`×40,221, `Y`×26
- **`UomEntry`** (4 values) — `0`×22,961, `-1`×16,385, `1`×854, `2`×47
- **`UomEntry2`** (4 values) — `0`×22,961, `-1`×16,385, `2`×893, `1`×8
- **`UomCode`** (4 values) — `NULL`×22,961, `Manual`×16,385, `MTS`×854, `LTR`×47
- **`UomCode2`** (4 values) — `NULL`×22,961, `Manual`×16,385, `LTR`×893, `MTS`×8
- **`NeedQty`** (1 values) — `N`×40,247
- **`PartRetire`** (1 values) — `N`×40,247
- **`EnSetCost`** (1 values) — `N`×40,247
- **`DistribIS`** (1 values) — `N`×40,247
- **`IsByPrdct`** (1 values) — `N`×40,247
- **`ItemType`** (1 values) — `4`×40,247
- **`PriceEdit`** (1 values) — `N`×40,247
- **`LinePoPrss`** (1 values) — `N`×40,247
- **`FreeChrgBP`** (1 values) — `N`×40,247
- **`TaxRelev`** (1 values) — `Y`×40,247
- **`ThirdParty`** (1 values) — `N`×40,247
- **`InvQtyOnly`** (1 values) — `N`×40,247
- **`ReturnRsn`** (1 values) — `-1`×40,247
- **`ReturnAct`** (2 values) — `-1`×37,572, `1`×2,675
- **`ItmTaxType`** (3 values) — `NULL`×22,961, `GR`×17,270, `NN`×16
- **`NCMCode`** (2 values) — `-1`×39,537, `NULL`×710
- **`IsPrscGood`** (1 values) — `N`×40,247
- **`IsCstmAct`** (1 values) — `N`×40,247
- **`TaxAmtSrc`** (2 values) — `S`×39,612, `NULL`×635
- **`IndEscala`** (2 values) — `N`×39,816, `NULL`×431
- **`CESTCode`** (2 values) — `NULL`×26,923, `-1`×13,324
- **`CUSplit`** (1 values) — `N`×40,247
- **`RevCharge`** (1 values) — `N`×40,247
- **`UoMNum`** (3 values) — `0.000000`×22,961, `1.000000`×16,432, `1098.900000`×854
- **`UoMDen`** (2 values) — `1.000000`×32,387, `0.000000`×7,860
- **`UoMNum2`** (3 values) — `0.000000`×22,961, `1.000000`×17,278, `1098.900000`×8
- **`UoMDen2`** (2 values) — `1.000000`×32,387, `0.000000`×7,860
- **`U_UTL_ST_TAXCD`** (5 values) — `NULL`×40,217, `RCGSG@5`×11, `Exempt`×9, `EXEMPT`×8, `0`×2
- **`U_UTL_ST_IGST`** (3 values) — `0.000000`×27,114, `NULL`×13,132, `18.000000`×1
- **`U_UTL_ST_IGAMT`** (4 values) — `0.000000`×27,113, `NULL`×13,132, `9137.290000`×1, `996819.000000`×1
- **`U_cartonpc`** (3 values) — `NULL`×36,994, `∅`×3,252, `5670001`×1
- **`U_carton`** (3 values) — `NULL`×36,994, `∅`×3,252, `CANOLA`×1
- **`U_UNE_SCHI`** (1 values) — `N`×40,247
- **`U_UNE_CALI`** (1 values) — `Y`×40,247
- **`U_UNE_CUNT`** (1 values) — `Y`×40,247
- **`U_UNE_FCT1`** (3 values) — `0.000000`×26,569, `NULL`×13,454, `1.000000`×224
- **`U_UNE_FCT2`** (18 values) — `0.000000`×26,569, `NULL`×13,454, `1.000000`×68, `4.000000`×46, `20.000000`×40, `12.000000`×23, `16.000000`×20, `45.000000`×4, `10.000000`×4, `24.000000`×3, `48.000000`×3, `5.000000`×3, `6.000000`×2, `70.000000`×2, `9.000000`×2, `15.000000`×2, `3.000000`×1, `40.000000`×1
- **`U_UNE_ACTD`** (5 values) — `NULL`×39,582, `1102007`×654, `1102001`×9, `2980`×1, `14400`×1
- **`U_Sub_Account`** (4 values) — `NULL`×33,690, `SALES`×5,978, `BST`×544, `SALES RETURN`×35
- **`U_Purpose`** (3 values) — `NULL`×40,226, `SALE`×19, `-`×2
- **`U_F_Year`** (3 values) — `NULL`×40,234, `2024-25`×12, `2023-24`×1
- **`U_PRCHSE_VAL`** (6 values) — `0.000000`×22,726, `NULL`×17,517, `1910.000000`×1, `4810.000000`×1, `6900.000000`×1, `7800.000000`×1
