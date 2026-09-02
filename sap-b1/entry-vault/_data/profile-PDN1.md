# `PDN1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 25,381 | 4,092 | `DocDate` | 2024-09-30 → 2026-08-20 |
| MART | 15,350 | 981 | `DocDate` | 2024-10-03 → 2026-08-24 |
| BEV | 7,254 | 1,458 | `DocDate` | 2024-09-30 → 2026-08-15 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 11,649 | |
| `LineNum` | INTEGER | 60% | 83% | 35% | 63% | 53% | 21% | 56 | |
| `TargetType` | INTEGER | 95% | 96% | 97% | 95% | 98% | 98% | 4 | |
| `TrgetEntry` | INTEGER | 91% | 96% | 92% | 75% | 91% | 81% | 7,692 | |
| `BaseRef` | NVARCHAR(16) | 62% | 96% | 42% | 72% | 81% | 17% | 4,445 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BaseEntry` | INTEGER | 62% | 96% | 42% | 72% | 81% | 17% | 4,362 | |
| `BaseLine` | INTEGER | 39% | 83% | 24% | 50% | 44% | 9% | 43 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItemCode` | NVARCHAR(50) | 73% | 99% | 46% | 74% | 80% | 21% | 1,125 | |
| `Dscription` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 1,274 | |
| `Quantity` | DECIMAL | 73% | 99% | 46% | 74% | 80% | 21% | 3,474 | |
| `ShipDate` | TIMESTAMP | 61% | 96% | 41% | 71% | 80% | 16% | 658 | |
| `OpenQty` | DECIMAL | 69% | 95% | 42% | 67% | 80% | 18% | 3,434 | |
| `Price` | DECIMAL | 96% | 100% | 100% | 96% | 100% | 100% | 9,037 | |
| `Currency` | NVARCHAR(3) | 96% | 100% | 100% | 96% | 100% | 100% | 4 | |
| `Rate` | DECIMAL | <1% | — | — | <1% | — | — | 44 | |
| `DiscPrcnt` | DECIMAL | <1% | 3% | <1% | <1% | — | <1% | 29 | |
| `LineTotal` | DECIMAL | 96% | 100% | 100% | 96% | 100% | 100% | 13,453 | |
| `TotalFrgn` | DECIMAL | <1% | — | — | <1% | — | — | 71 | |
| `OpenSum` | DECIMAL | 66% | 95% | 44% | 69% | 86% | 28% | 9,263 | |
| `OpenSumFC` | DECIMAL | <1% | — | — | <1% | — | — | 71 | |
| `WhsCode` | NVARCHAR(8) | 73% | 99% | 46% | 74% | 80% | 21% | 31 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 52 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 80 | |
| `TaxStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PriceBefDi` | DECIMAL | 96% | 100% | 100% | 96% | 100% | 100% | 9,022 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 674 | |
| `OpenCreQty` | DECIMAL | 2% | <1% | 1% | 12% | <1% | 6% | 208 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseCard` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 529 | |
| `TotalSumSy` | DECIMAL | 96% | 100% | 100% | 96% | 100% | 100% | 13,453 | |
| `OpenSumSys` | DECIMAL | 66% | 95% | 44% | 69% | 86% | 28% | 9,263 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `OcrCode` | NVARCHAR(8) | 95% | 100% | 98% | 100% | 100% | 100% | 40 | |
| `VatPrcnt` | DECIMAL | 76% | 100% | 95% | 68% | 100% | 98% | 5 | |
| `VatGroup` | NVARCHAR(8) | 34% | 82% | 23% | 42% | 42% | 12% | 9 | |
| `PriceAfVAT` | DECIMAL | 96% | 100% | 100% | 96% | 100% | 100% | 9,569 | |
| `VolUnit` | SMALLINT | 73% | 99% | 46% | 74% | 80% | 21% | 1 | |
| `Factor1` | DECIMAL | 73% | 99% | 46% | 74% | 80% | 21% | 2 | |
| `Factor2` | DECIMAL | 73% | 99% | 46% | 74% | 80% | 21% | 2 | |
| `Factor3` | DECIMAL | 73% | 99% | 46% | 74% | 80% | 21% | 2 | |
| `Factor4` | DECIMAL | 73% | 99% | 46% | 74% | 80% | 21% | 2 | |
| `PackQty` | DECIMAL | 73% | 99% | 46% | 74% | 80% | 21% | 2,776 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDocNum` | INTEGER | 62% | 96% | 42% | 72% | 81% | 17% | 4,444 | |
| `BaseAtCard` | NVARCHAR(200) | <1% | 86% | <1% | <1% | 69% | — | 85 | |
| `VatSum` | DECIMAL | 72% | 100% | 94% | 64% | 100% | 97% | 12,747 | |
| `VatSumSy` | DECIMAL | 72% | 100% | 94% | 64% | 100% | 97% | 12,747 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DistribSum` | DECIMAL | 2% | <1% | 4% | <1% | — | <1% | 301 | |
| `DstrbSumSC` | DECIMAL | 2% | <1% | 4% | <1% | — | <1% | 301 | |
| `VisOrder` | INTEGER | 54% | 79% | 33% | 58% | 44% | 20% | 43 | |
| `INMPrice` | DECIMAL | 70% | 99% | 45% | 70% | 80% | 20% | 4,545 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Address` | NVARCHAR(254) | 75% | 99% | 46% | 75% | 85% | 22% | 24 | |
| `TaxCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 15 | |
| `TaxType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OrigItem` | NVARCHAR(50) | 2% | 3% | 1% | 3% | 2% | <1% | 185 | |
| `FreeTxt` | NVARCHAR(100) | <1% | <1% | — | — | — | — | 2 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TrnsCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatAppld` | DECIMAL | 67% | 96% | 87% | 48% | 91% | 79% | 12,246 | |
| `VatAppldSC` | DECIMAL | 67% | 96% | 87% | 48% | 91% | 79% | 12,246 | |
| `BaseQty` | DECIMAL | 61% | 96% | 41% | 71% | 80% | 16% | 1,657 | |
| `BaseOpnQty` | DECIMAL | 61% | 96% | 41% | 71% | 80% | 16% | 4,126 | |
| `WtLiable` | NVARCHAR(1) | 100% | 100% | 98% | 98% | 100% | 91% | 2 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineVat` | DECIMAL | 72% | 100% | 94% | 64% | 100% | 97% | 12,747 | |
| `LineVatS` | DECIMAL | 72% | 100% | 94% | 64% | 100% | 97% | 12,747 | |
| `unitMsr` | NVARCHAR(100) | 73% | 99% | 46% | 74% | 80% | 21% | 10 | |
| `NumPerMsr` | DECIMAL | 73% | 99% | 46% | 74% | 80% | 21% | 3 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CountryOrg` | NVARCHAR(3) | <1% | — | — | — | — | — | 5 | |
| `StckDstSum` | DECIMAL | <1% | <1% | <1% | <1% | — | <1% | 150 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Text` | NCLOB | <1% | — | — | <1% | — | — | 0 | |
| `OwnerCode` | INTEGER | <1% | — | — | <1% | — | — | 5 | |
| `ConsumeFCT` | NVARCHAR(1) | 73% | 99% | 46% | 74% | 80% | 21% | 1 | |
| `LstByDsSum` | DECIMAL | 2% | <1% | 4% | <1% | — | <1% | 301 | |
| `StckINMPr` | DECIMAL | <1% | <1% | <1% | <1% | — | <1% | 127 | |
| `LstBINMPr` | DECIMAL | 2% | <1% | 4% | <1% | — | <1% | 262 | |
| `StckDstSc` | DECIMAL | <1% | <1% | <1% | <1% | — | <1% | 150 | |
| `LstByDsSc` | DECIMAL | 2% | <1% | 4% | <1% | — | <1% | 301 | |
| `StockSum` | DECIMAL | 70% | 99% | 45% | 70% | 80% | 20% | 9,254 | |
| `StockSumFc` | DECIMAL | <1% | — | — | <1% | — | — | 71 | |
| `StockSumSc` | DECIMAL | 70% | 99% | 45% | 70% | 80% | 20% | 9,254 | |
| `StckSumApp` | DECIMAL | 60% | 91% | 38% | 48% | 79% | 12% | 8,860 | |
| `StckAppFc` | DECIMAL | <1% | — | — | <1% | — | — | 67 | |
| `StckAppSc` | DECIMAL | 60% | 91% | 38% | 48% | 79% | 12% | 8,860 | |
| `ShipToCode` | NVARCHAR(50) | 61% | 96% | 42% | 72% | 80% | 21% | 386 | |
| `ShipToDesc` | NVARCHAR(254) | 73% | 99% | 46% | 74% | 80% | 21% | 20 | |
| `StckAppD` | DECIMAL | <1% | <1% | <1% | <1% | — | <1% | 149 | |
| `StckAppDSC` | DECIMAL | <1% | <1% | <1% | <1% | — | <1% | 149 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GTotal` | DECIMAL | 96% | 100% | 100% | 96% | 100% | 100% | 14,269 | |
| `GTotalFC` | DECIMAL | <1% | — | — | <1% | — | — | 77 | |
| `GTotalSC` | DECIMAL | 96% | 100% | 100% | 96% | 100% | 100% | 14,269 | |
| `DistribExp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsOcrCod` | NVARCHAR(8) | 10% | 3% | 3% | — | — | — | 2 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ChgAsmBoMW` | NVARCHAR(1) | 73% | 99% | 46% | 74% | 80% | 21% | 1 | |
| `ActDelDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 661 | |
| `OcrCode2` | NVARCHAR(8) | 59% | 3% | 84% | 69% | 23% | 89% | 30 | |
| `OcrCode3` | NVARCHAR(8) | 57% | 3% | 84% | 67% | 23% | 89% | 11 | |
| `OcrCode4` | NVARCHAR(8) | 10% | 1% | <1% | 17% | 20% | — | 9 | |
| `OcrCode5` | NVARCHAR(8) | 51% | 1% | 83% | 49% | 20% | 89% | 26 | |
| `TaxDistSum` | DECIMAL | <1% | — | <1% | — | — | — | 2 | |
| `TaxDistSSC` | DECIMAL | <1% | — | <1% | — | — | — | 2 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excisable` | NVARCHAR(1) | 73% | 99% | 46% | 74% | 80% | 21% | 1 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `unitMsr2` | NVARCHAR(100) | 42% | 85% | 25% | 40% | 80% | 14% | 9 | |
| `NumPerMsr2` | DECIMAL | 73% | 99% | 46% | 74% | 80% | 21% | 3 | |
| `SpecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `isSrvCall` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcDocType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `VatGrpSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `NoInvtryMv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UomEntry` | INTEGER | 73% | 99% | 46% | 74% | 80% | 21% | 4 | |
| `UomEntry2` | INTEGER | 73% | 99% | 46% | 74% | 80% | 21% | 4 | |
| `UomCode` | NVARCHAR(20) | 73% | 99% | 46% | 74% | 80% | 21% | 3 | |
| `UomCode2` | NVARCHAR(20) | 73% | 99% | 46% | 74% | 80% | 21% | 3 | |
| `NeedQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartRetire` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQty` | DECIMAL | 73% | 99% | 46% | 74% | 80% | 21% | 3,504 | |
| `OpenInvQty` | DECIMAL | 2% | <1% | 1% | 12% | <1% | 6% | 208 | |
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
| `GPBefDisc` | DECIMAL | 96% | 100% | 100% | 96% | 100% | 100% | 9,580 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItmTaxType` | NVARCHAR(2) | 73% | 99% | 46% | 74% | 80% | 21% | 2 | |
| `SacEntry` | INTEGER | 26% | 1% | 54% | 26% | 20% | 79% | 11 | |
| `NCMCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `HsnEntry` | INTEGER | 73% | 99% | 46% | 74% | 80% | 21% | 271 | |
| `IsPrscGood` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IndEscala` | NVARCHAR(1) | 98% | 100% | 99% | 97% | 99% | 99% | 1 | |
| `CESTCode` | INTEGER | 61% | 96% | 42% | 74% | 80% | 21% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ListNum` | SMALLINT | <1% | — | <1% | 2% | — | <1% | 2 | |
| `UoMNum` | DECIMAL | 73% | 99% | 46% | 74% | 80% | 21% | 3 | |
| `UoMDen` | DECIMAL | 90% | 99% | 74% | 74% | 80% | 21% | 2 | |
| `UoMNum2` | DECIMAL | 73% | 99% | 46% | 74% | 80% | 21% | 3 | |
| `UoMDen2` | DECIMAL | 90% | 99% | 74% | 74% | 80% | 21% | 2 | |
| `U_Remarks` | NVARCHAR(100) | 41% | 1% | 62% | 50% | 20% | 81% | 5,896 | |
| `U_SchemeAgst` | NVARCHAR(50) | 69% | 99% | 43% | 72% | 80% | 19% | 33 | |
| `U_UTL_ST_TAXCD` | NVARCHAR(100) | <1% | — | <1% | — | — | — | 1 | |
| `U_Disp_Qty` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `U_Recvd_Qty` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_LTS` | DECIMAL | 26% | 1% | 54% | 24% | 20% | 77% | 2,395 | |
| `U_BilltyNumber` | NVARCHAR(100) | 26% | 1% | 54% | 26% | 20% | 79% | 3,777 | |
| `U_ARNO` | NVARCHAR(100) | 26% | 1% | 54% | 26% | 20% | 79% | 5,935 | |
| `U_Sub_Account` | NVARCHAR(20) | 26% | 1% | 54% | 26% | 18% | 79% | 3 | |
| `U_CardCode` | NVARCHAR(15) | 26% | 1% | 54% | 26% | 20% | 79% | 293 | |
| `U_Purpose` | NVARCHAR(10) | <1% | — | — | — | — | — | 2 | |
| `U_F_Year` | NVARCHAR(10) | <1% | — | — | — | — | — | 1 | |
| `U_BiltyDate` | TIMESTAMP | 1% | n/a | 25% | 9% | n/a | 78% | 57 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BiltyDate` | OIL, BEV | **MART** |
| `U_UNE_CALI` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TargetType`** (5 values) — `18`×21,933, `20`×1,187, `NULL`×1,187, `-1`×1,072, `21`×2
- **`BaseType`** (3 values) — `22`×14,631, `-1`×9,563, `20`×1,187
- **`LineStatus`** (2 values) — `C`×24,607, `O`×774
- **`Currency`** (5 values) — `INR`×24,257, `NULL`×874, `∅`×161, `USD`×56, `EUR`×33
- **`DiscPrcnt`** (30 values) — `0.000000`×25,310, `-18.000000`×18, `41.000000`×6, `100.000000`×6, `-0.010000`×4, `0.010000`×4, `NULL`×3, `-15.000000`×2, `70.500000`×2, `-136.000000`×2, `89.990000`×2, `76.400000`×2, `60.670000`×2, `-44.380000`×2, `-3.850000`×1, `-38.460000`×1, `-1.100000`×1, `-30.000000`×1, `-3.140000`×1, `15.250000`×1, `-2.220000`×1, `-6.050000`×1, `80.000000`×1, `1.000000`×1, `-3.570000`×1, `-3.840000`×1, `-4.960000`×1, `-6.040000`×1, `-5.460000`×1, `-29.930000`×1
- **`TreeType`** (2 values) — `N`×22,504, `P`×2,877
- **`TaxStatus`** (1 values) — `Y`×25,381
- **`UseBaseUn`** (2 values) — `N`×25,341, `Y`×40
- **`InvntSttus`** (2 values) — `C`×24,219, `O`×1,162
- **`VatPrcnt`** (5 values) — `5.000000`×9,539, `18.000000`×8,508, `0.000000`×5,990, `12.000000`×1,331, `28.000000`×13
- **`VatGroup`** (10 values) — `∅`×13,681, `CG+SG@18`×3,679, `NULL`×3,191, `CG+SG@0`×2,740, `IGST@18`×1,079, `IGST@0`×402, `CG+SG@5`×265, `CG+SG@12`×162, `IGST@5`×143, `IGST@12`×39
- **`VolUnit`** (2 values) — `4`×18,645, `NULL`×6,736
- **`Factor1`** (2 values) — `1.000000`×18,645, `0.000000`×6,736
- **`Factor2`** (2 values) — `1.000000`×18,645, `0.000000`×6,736
- **`Factor3`** (2 values) — `1.000000`×18,645, `0.000000`×6,736
- **`Factor4`** (2 values) — `1.000000`×18,645, `0.000000`×6,736
- **`UpdInvntry`** (1 values) — `Y`×25,381
- **`FinncPriod`** (24 values) — `8`×1,505, `12`×1,313, `17`×1,282, `20`×1,258, `43`×1,238, `42`×1,238, `9`×1,234, `18`×1,187, `19`×1,158, `10`×1,157, `11`×1,150, `23`×1,144, `41`×1,123, `44`×1,123, `15`×1,099, `22`×1,046, `21`×1,003, `14`×975, `7`×973, `24`×920, `16`×887, `25`×804, `45`×563, `6`×1
- **`ObjType`** (1 values) — `20`×25,381
- **`IsAqcuistn`** (1 values) — `N`×25,381
- **`DropShip`** (1 values) — `N`×25,381
- **`TaxCode`** (15 values) — `CG+SG@18`×5,795, `CG+SG@0`×4,833, `IGST@5`×4,142, `GST05R`×2,969, `IGST@18`×2,713, `RIGST@5`×1,905, `IGST@0`×1,101, `CG+SG@12`×779, `IGST@12`×550, `CG+SG@5`×523, `Exampt`×56, `CG+SG@28`×9, `IGST@28`×4, `RIGST@12`×1, `RCGSG@12`×1
- **`TaxType`** (1 values) — `Y`×25,381
- **`FreeTxt`** (3 values) — `∅`×14,341, `NULL`×11,039, `BILTY NO 200`×1
- **`PickStatus`** (1 values) — `N`×25,381
- **`TrnsCode`** (1 values) — `-1`×25,381
- **`WtLiable`** (3 values) — `N`×20,080, `Y`×5,218, `NULL`×83
- **`DeferrTax`** (1 values) — `N`×25,381
- **`unitMsr`** (11 values) — `PCS`×17,225, `NULL`×6,758, `MTS`×929, `KGS`×200, `LTR`×131, `MTR`×68, `GMS`×25, `MTRS`×15, `∅`×15, `NOS`×13, `KG`×2
- **`NumPerMsr`** (3 values) — `1.000000`×17,718, `0.000000`×6,736, `1098.900000`×927
- **`CEECFlag`** (1 values) — `S`×25,381
- **`CountryOrg`** (6 values) — `NULL`×25,331, `AE`×27, `ES`×12, `AU`×8, `AT`×2, `XX`×1
- **`LineType`** (1 values) — `R`×25,381
- **`OwnerCode`** (6 values) — `NULL`×25,213, `20`×134, `14`×30, `2`×2, `4`×1, `6`×1
- **`ConsumeFCT`** (2 values) — `N`×18,645, `NULL`×6,736
- **`BasePrice`** (1 values) — `E`×25,381
- **`DistribExp`** (2 values) — `Y`×23,067, `N`×2,314
- **`DescOW`** (2 values) — `N`×25,311, `Y`×70
- **`DetailsOW`** (1 values) — `N`×25,381
- **`TaxOnly`** (1 values) — `N`×25,381
- **`WtCalced`** (1 values) — `N`×25,381
- **`CogsOcrCod`** (3 values) — `NULL`×22,835, `BST`×2,545, `GHEE`×1
- **`CiOppLineN`** (1 values) — `-1`×25,381
- **`ChgAsmBoMW`** (2 values) — `N`×18,645, `NULL`×6,736
- **`OcrCode2`** (30 values) — `NULL`×10,342, `05-2026`×959, `01-2026`×902, `04-2026`×825, `11-2024`×821, `09-2025`×803, `07-2026`×777, `02-2026`×744, `12-2025`×704, `10-2025`×693, `06-2026`×678, `08-2025`×671, `07-2025`×650, `12-2024`×636, `03-2026`×619, `11-2025`×613, `05-2025`×593, `03-2025`×551, `01-2025`×533, `06-2025`×516, `02-2025`×501, `04-2025`×474, `10-2024`×457, `08-2026`×205, `∅`×50, `09-2024`×21, `04-2024`×15, `08-2024`×14, `07-2024`×6, `06-2024`×6
- **`OcrCode3`** (12 values) — `NULL`×10,764, `Del Bkhp`×6,645, `Factory`×4,854, `BackOff`×2,294, `FACT_COM`×631, `OTE`×56, `∅`×50, `Sales`×42, `Med MKT`×22, `Del Mayp`×21, `NPD3`×1, `NPD1`×1
- **`OcrCode4`** (10 values) — `NULL`×22,912, `Admin`×2,231, `IT`×60, `GP-GDWN`×59, `∅`×50, `E-COM`×35, `POP`×22, `Accounts`×5, `CSD`×4, `GT`×3
- **`OcrCode5`** (27 values) — `NULL`×12,270, `HR`×5,903, `DL`×2,678, `PB`×2,322, `UP`×368, `MH`×300, `WB`×207, `TE`×186, `RJ`×166, `GJ`×150, `KN`×139, `UK`×124, `JK`×107, `AS`×74, `KR`×65, `TN`×64, `GO`×56, `MP`×52, `∅`×50, `KE`×27, `AP`×17, `JH`×16, `HP`×13, `OR`×10, `BH`×8, `CH`×8, `NG`×1
- **`TaxDistSum`** (2 values) — `0.000000`×25,380, `1170.000000`×1
- **`TaxDistSSC`** (2 values) — `0.000000`×25,380, `1170.000000`×1
- **`PostTax`** (1 values) — `Y`×25,381
- **`Excisable`** (2 values) — `N`×18,645, `NULL`×6,736
- **`LocCode`** (3 values) — `2`×19,999, `1`×3,595, `3`×1,787
- **`unitMsr2`** (10 values) — `NULL`×13,719, `PCS`×9,389, `∅`×1,065, `LTR`×1,000, `MTR`×81, `KGS`×71, `MTS`×40, `NOS`×9, `GMS`×5, `MTRS`×2
- **`NumPerMsr2`** (3 values) — `1.000000`×18,605, `0.000000`×6,736, `1098.900000`×40
- **`SpecPrice`** (2 values) — `N`×25,237, `R`×144
- **`isSrvCall`** (1 values) — `N`×25,381
- **`PcDocType`** (1 values) — `-1`×25,381
- **`LinManClsd`** (2 values) — `N`×24,993, `Y`×388
- **`VatGrpSrc`** (3 values) — `M`×12,625, `N`×12,567, `D`×189
- **`NoInvtryMv`** (1 values) — `N`×25,381
- **`UomEntry`** (4 values) — `-1`×17,613, `0`×6,736, `1`×927, `2`×105
- **`UomEntry2`** (4 values) — `-1`×17,613, `0`×6,736, `2`×992, `1`×40
- **`UomCode`** (4 values) — `Manual`×17,613, `NULL`×6,736, `MTS`×927, `LTR`×105
- **`UomCode2`** (4 values) — `Manual`×17,613, `NULL`×6,736, `LTR`×992, `MTS`×40
- **`NeedQty`** (1 values) — `N`×25,381
- **`PartRetire`** (1 values) — `N`×25,381
- **`EnSetCost`** (1 values) — `N`×25,381
- **`DistribIS`** (1 values) — `N`×25,381
- **`IsByPrdct`** (1 values) — `N`×25,381
- **`ItemType`** (1 values) — `4`×25,381
- **`PriceEdit`** (1 values) — `N`×25,381
- **`LinePoPrss`** (1 values) — `N`×25,381
- **`FreeChrgBP`** (1 values) — `N`×25,381
- **`TaxRelev`** (1 values) — `Y`×25,381
- **`ThirdParty`** (1 values) — `N`×25,381
- **`InvQtyOnly`** (1 values) — `N`×25,381
- **`ReturnRsn`** (1 values) — `-1`×25,381
- **`ReturnAct`** (2 values) — `-1`×22,231, `1`×3,150
- **`ItmTaxType`** (3 values) — `GR`×18,603, `NULL`×6,736, `NN`×42
- **`SacEntry`** (12 values) — `NULL`×18,658, `2`×6,539, `40`×155, `-446`×17, `-555`×2, `-519`×2, `-418`×2, `-153`×2, `-451`×1, `-274`×1, `-154`×1, `-405`×1
- **`NCMCode`** (1 values) — `-1`×25,381
- **`IsPrscGood`** (1 values) — `N`×25,381
- **`IsCstmAct`** (1 values) — `N`×25,381
- **`TaxAmtSrc`** (2 values) — `S`×25,271, `NULL`×110
- **`IndEscala`** (2 values) — `N`×24,919, `NULL`×462
- **`CESTCode`** (2 values) — `-1`×15,548, `NULL`×9,833
- **`CUSplit`** (1 values) — `N`×25,381
- **`RevCharge`** (1 values) — `N`×25,381
- **`ListNum`** (3 values) — `NULL`×25,237, `-1`×122, `1`×22
- **`UoMNum`** (3 values) — `1.000000`×17,718, `0.000000`×6,736, `1098.900000`×927
- **`UoMDen`** (2 values) — `1.000000`×22,812, `0.000000`×2,569
- **`UoMNum2`** (3 values) — `1.000000`×18,605, `0.000000`×6,736, `1098.900000`×40
- **`UoMDen2`** (2 values) — `1.000000`×22,812, `0.000000`×2,569
- **`U_UTL_ST_TAXCD`** (2 values) — `NULL`×25,373, `Bilty No-12534`×8
- **`U_UNE_SCHI`** (1 values) — `N`×25,381
- **`U_UNE_CALI`** (1 values) — `Y`×25,381
- **`U_UNE_CUNT`** (1 values) — `Y`×25,381
- **`U_Sub_Account`** (4 values) — `NULL`×18,697, `SALES`×6,498, `BST`×161, `SALES RETURN`×25
- **`U_Purpose`** (3 values) — `NULL`×25,377, `CONSUMABLE`×2, `-`×2
- **`U_F_Year`** (2 values) — `NULL`×25,380, `2024-25`×1
