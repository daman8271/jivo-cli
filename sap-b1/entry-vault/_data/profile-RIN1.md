# `RIN1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 15,431 | 984 | `DocDate` | 2024-09-30 → 2026-08-21 |
| MART | 29,622 | 3,554 | `DocDate` | 2025-01-04 → 2026-08-21 |
| BEV | 792 | 90 | `DocDate` | 2024-10-09 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 6,434 | |
| `LineNum` | INTEGER | 62% | 86% | 47% | 58% | 89% | 27% | 202 | |
| `TargetType` | INTEGER | 98% | 99% | 96% | 99% | 100% | 100% | 2 | |
| `TrgetEntry` | INTEGER | 2% | 1% | 4% | <1% | <1% | — | 144 | |
| `BaseRef` | NVARCHAR(16) | 71% | 80% | 63% | 46% | 73% | 53% | 2,426 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `BaseEntry` | INTEGER | 71% | 80% | 63% | 46% | 73% | 53% | 2,407 | |
| `BaseLine` | INTEGER | 56% | 76% | 30% | 24% | 68% | 23% | 202 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItemCode` | NVARCHAR(50) | 86% | 99% | 81% | 93% | 97% | 76% | 462 | |
| `Dscription` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 512 | |
| `Quantity` | DECIMAL | 86% | 99% | 81% | 93% | 97% | 76% | 546 | |
| `ShipDate` | TIMESTAMP | 13% | 6% | 37% | 7% | 6% | 37% | 133 | |
| `OpenQty` | DECIMAL | 68% | 91% | 36% | 85% | 90% | 39% | 448 | |
| `Price` | DECIMAL | 83% | 61% | 92% | 95% | 66% | 96% | 3,953 | |
| `Currency` | NVARCHAR(3) | 83% | 61% | 92% | 95% | 66% | 96% | 1 | |
| `DiscPrcnt` | DECIMAL | <1% | <1% | 5% | <1% | <1% | 4% | 12 | |
| `LineTotal` | DECIMAL | 83% | 61% | 92% | 95% | 66% | 96% | 6,933 | |
| `OpenSum` | DECIMAL | 68% | 53% | 55% | 89% | 58% | 62% | 5,787 | |
| `WhsCode` | NVARCHAR(8) | 86% | 99% | 81% | 93% | 97% | 76% | 22 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 40 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 52 | |
| `TaxStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBuyPr` | DECIMAL | 1% | — | 81% | — | — | 76% | 88 | |
| `PriceBefDi` | DECIMAL | 83% | 61% | 92% | 95% | 66% | 96% | 3,948 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 539 | |
| `OpenCreQty` | DECIMAL | 68% | 91% | 36% | 85% | 90% | 39% | 448 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseCard` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 235 | |
| `TotalSumSy` | DECIMAL | 83% | 61% | 92% | 95% | 66% | 96% | 6,933 | |
| `OpenSumSys` | DECIMAL | 68% | 53% | 55% | 89% | 58% | 62% | 5,787 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `OcrCode` | NVARCHAR(8) | 91% | 99% | 89% | 100% | 93% | 99% | 27 | |
| `VatPrcnt` | DECIMAL | 86% | 99% | 82% | 92% | 97% | 76% | 4 | |
| `VatGroup` | NVARCHAR(8) | 65% | 92% | 40% | 54% | 90% | 16% | 8 | |
| `PriceAfVAT` | DECIMAL | 83% | 61% | 92% | 95% | 66% | 96% | 3,927 | |
| `VolUnit` | SMALLINT | 86% | 99% | 81% | 93% | 97% | 76% | 1 | |
| `Factor1` | DECIMAL | 86% | 99% | 81% | 93% | 97% | 76% | 2 | |
| `Factor2` | DECIMAL | 86% | 99% | 81% | 93% | 97% | 76% | 14 | |
| `Factor3` | DECIMAL | 86% | 99% | 81% | 93% | 97% | 76% | 2 | |
| `Factor4` | DECIMAL | 86% | 99% | 81% | 93% | 97% | 76% | 2 | |
| `PackQty` | DECIMAL | 86% | 99% | 81% | 93% | 97% | 76% | 528 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDocNum` | INTEGER | 71% | 80% | 63% | 46% | 73% | 53% | 2,426 | |
| `BaseAtCard` | NVARCHAR(200) | 11% | 8% | 7% | 4% | 8% | 1% | 851 | |
| `VatSum` | DECIMAL | 69% | 60% | 74% | 88% | 63% | 71% | 5,710 | |
| `VatSumSy` | DECIMAL | 69% | 60% | 74% | 88% | 63% | 71% | 5,710 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DedVatSum` | DECIMAL | 69% | 60% | 74% | 88% | 63% | 71% | 5,710 | |
| `DedVatSumS` | DECIMAL | 69% | 60% | 74% | 88% | 63% | 71% | 5,710 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrssProfit` | DECIMAL | 69% | 60% | 81% | 88% | 63% | 76% | 5,721 | |
| `GrssProfSC` | DECIMAL | 69% | 60% | 81% | 88% | 63% | 76% | 5,721 | |
| `VisOrder` | INTEGER | 58% | 85% | 45% | 57% | 88% | 19% | 202 | |
| `INMPrice` | DECIMAL | 69% | 60% | 73% | 88% | 63% | 71% | 2,645 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Address` | NVARCHAR(254) | 89% | 100% | 92% | 96% | 100% | 83% | 26 | |
| `TaxCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 8 | |
| `TaxType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OrigItem` | NVARCHAR(50) | 4% | <1% | 8% | 4% | <1% | 4% | 165 | |
| `BackOrdr` | NVARCHAR(1) | 13% | 7% | 37% | 7% | 7% | 37% | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PickIdNo` | INTEGER | 2% | <1% | 1% | — | — | — | 93 | |
| `TrnsCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatAppld` | DECIMAL | 2% | 1% | 4% | <1% | <1% | — | 310 | |
| `VatAppldSC` | DECIMAL | 2% | 1% | 4% | <1% | <1% | — | 310 | |
| `BaseQty` | DECIMAL | 70% | 80% | 62% | 46% | 72% | 53% | 456 | |
| `BaseOpnQty` | DECIMAL | 70% | 80% | 62% | 46% | 72% | 53% | 506 | |
| `WtLiable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineVat` | DECIMAL | 69% | 60% | 74% | 88% | 63% | 71% | 5,710 | |
| `LineVatS` | DECIMAL | 69% | 60% | 74% | 88% | 63% | 71% | 5,710 | |
| `unitMsr` | NVARCHAR(100) | 83% | 95% | 81% | 93% | 97% | 76% | 6 | |
| `NumPerMsr` | DECIMAL | 86% | 99% | 81% | 93% | 97% | 76% | 2 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CountryOrg` | NVARCHAR(3) | <1% | — | — | <1% | — | — | 3 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Text` | NCLOB | <1% | — | — | — | — | — | 0 | |
| `OwnerCode` | INTEGER | <1% | — | <1% | 1% | — | — | 3 | |
| `StockPrice` | DECIMAL | 62% | 38% | 42% | 85% | 10% | 38% | 2,677 | |
| `ConsumeFCT` | NVARCHAR(1) | 86% | 99% | 81% | 93% | 97% | 76% | 2 | |
| `StockSum` | DECIMAL | 29% | 25% | 54% | 52% | 30% | 54% | 2,884 | |
| `StockSumSc` | DECIMAL | 29% | 25% | 54% | 52% | 30% | 54% | 2,884 | |
| `ShipToCode` | NVARCHAR(50) | 86% | 99% | 81% | 93% | 97% | 76% | 353 | |
| `ShipToDesc` | NVARCHAR(254) | 86% | 99% | 81% | 93% | 97% | 76% | 288 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GTotal` | DECIMAL | 83% | 61% | 92% | 95% | 66% | 96% | 6,824 | |
| `GTotalSC` | DECIMAL | 83% | 61% | 92% | 95% | 66% | 96% | 6,824 | |
| `DistribExp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 85% | 61% | 100% | 100% | 66% | 100% | 3 | |
| `TaxOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsOcrCod` | NVARCHAR(8) | 86% | 99% | 80% | 93% | 92% | 74% | 36 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsAcct` | NVARCHAR(15) | 86% | 99% | 81% | 93% | 97% | 76% | 30 | |
| `ChgAsmBoMW` | NVARCHAR(1) | 86% | 99% | 81% | 93% | 97% | 76% | 1 | |
| `ActDelDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 537 | |
| `OcrCode2` | NVARCHAR(8) | 13% | 4% | 19% | 7% | 16% | 24% | 28 | |
| `OcrCode3` | NVARCHAR(8) | 11% | <1% | 19% | 7% | 3% | 27% | 7 | |
| `OcrCode4` | NVARCHAR(8) | 10% | <1% | 18% | 7% | 3% | 27% | 13 | |
| `OcrCode5` | NVARCHAR(8) | 8% | <1% | <1% | 6% | — | 1% | 6 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excisable` | NVARCHAR(1) | 86% | 99% | 81% | 93% | 97% | 76% | 1 | |
| `CogsOcrCo2` | NVARCHAR(8) | 7% | 4% | — | — | 13% | — | 19 | |
| `CogsOcrCo3` | NVARCHAR(8) | 5% | — | <1% | — | — | 1% | 5 | |
| `CogsOcrCo4` | NVARCHAR(8) | 4% | — | <1% | — | — | 1% | 8 | |
| `CogsOcrCo5` | NVARCHAR(8) | 3% | — | <1% | — | — | 1% | 4 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `StockValue` | DECIMAL | 62% | 38% | 42% | 85% | 10% | 38% | 5,841 | |
| `GPTtlBasPr` | DECIMAL | 15% | <1% | 99% | 7% | 3% | 100% | 1,604 | |
| `unitMsr2` | NVARCHAR(100) | 70% | 96% | 57% | 93% | 96% | 76% | 7 | |
| `NumPerMsr2` | DECIMAL | 86% | 99% | 81% | 93% | 97% | 76% | 2 | |
| `SpecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `isSrvCall` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcDocType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatGrpSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `NoInvtryMv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UomEntry` | INTEGER | 86% | 99% | 81% | 93% | 97% | 76% | 3 | |
| `UomEntry2` | INTEGER | 86% | 99% | 81% | 93% | 97% | 76% | 3 | |
| `UomCode` | NVARCHAR(20) | 86% | 99% | 81% | 93% | 97% | 76% | 2 | |
| `UomCode2` | NVARCHAR(20) | 86% | 99% | 81% | 93% | 97% | 76% | 2 | |
| `NeedQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartRetire` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQty` | DECIMAL | 86% | 99% | 81% | 93% | 97% | 76% | 546 | |
| `OpenInvQty` | DECIMAL | 68% | 91% | 36% | 85% | 90% | 39% | 448 | |
| `EnSetCost` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RetCost` | DECIMAL | 37% | 1% | — | 79% | 4% | — | 1,545 | |
| `DistribIS` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsByPrdct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ItemType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PriceEdit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinePoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FreeChrgBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxRelev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ThirdParty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQtyOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GPBefDisc` | DECIMAL | 83% | 61% | 92% | 95% | 66% | 96% | 3,928 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItmTaxType` | NVARCHAR(2) | 86% | 99% | 81% | 93% | 97% | 76% | 1 | |
| `SacEntry` | INTEGER | <1% | <1% | <1% | <1% | — | — | 2 | |
| `NCMCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `HsnEntry` | INTEGER | 86% | 99% | 81% | 93% | 97% | 76% | 54 | |
| `IsPrscGood` | NVARCHAR(1) | 98% | 93% | 100% | 100% | 94% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 85% | 61% | 99% | 99% | 66% | 100% | 1 | |
| `IndEscala` | NVARCHAR(1) | 84% | 61% | 99% | 99% | 66% | 99% | 1 | |
| `CESTCode` | INTEGER | 85% | 99% | 79% | 89% | 97% | 56% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ListNum` | SMALLINT | 1% | <1% | 2% | 10% | — | 1% | 2 | |
| `UoMNum` | DECIMAL | 86% | 99% | 81% | 93% | 97% | 76% | 2 | |
| `UoMDen` | DECIMAL | 98% | 99% | 94% | 93% | 97% | 76% | 2 | |
| `UoMNum2` | DECIMAL | 86% | 99% | 81% | 93% | 97% | 76% | 2 | |
| `UoMDen2` | DECIMAL | 98% | 99% | 94% | 93% | 97% | 76% | 2 | |
| `U_Remarks` | NVARCHAR(100) | 11% | <1% | 20% | 6% | 2% | 10% | 886 | |
| `U_SchemeAgst` | NVARCHAR(50) | 85% | 99% | 80% | 92% | 92% | 74% | 28 | |
| `U_Disp_Qty` | DECIMAL | <1% | <1% | 17% | <1% | 2% | 20% | 90 | |
| `U_Recvd_Qty` | DECIMAL | 3% | <1% | 4% | — | — | 4% | 163 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_FCT1` | DECIMAL | <1% | <1% | — | — | <1% | — | 2 | |
| `U_UNE_FCT2` | DECIMAL | <1% | <1% | — | — | <1% | — | 3 | |
| `U_UNE_LTS` | DECIMAL | <1% | — | — | — | — | — | 49 | |
| `U_ARNO` | NVARCHAR(100) | <1% | — | — | — | — | — | 1 | |
| `U_Sub_Account` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_Purpose` | NVARCHAR(10) | 3% | 8% | <1% | 7% | 27% | 1% | 3 | |
| `U_F_Year` | NVARCHAR(10) | <1% | — | <1% | — | — | — | 2 | |
| `U_BiltyDate` | TIMESTAMP | — | n/a | 1% | — | n/a | 6% | 0 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BiltyDate` | OIL, BEV | **MART** |
| `U_UNE_CALI` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TargetType`** (3 values) — `-1`×14,663, `14`×384, `NULL`×384
- **`BaseType`** (5 values) — `16`×8,447, `-1`×4,530, `13`×1,993, `14`×384, `234000031`×77
- **`LineStatus`** (2 values) — `O`×12,694, `C`×2,737
- **`Currency`** (2 values) — `INR`×12,841, `NULL`×2,590
- **`DiscPrcnt`** (13 values) — `0.000000`×15,416, `NULL`×3, `-12111.110000`×2, `-146.940000`×1, `-0.690000`×1, `4.870000`×1, `-0.010000`×1, `-48.240000`×1, `-38.610000`×1, `0.420000`×1, `-16566.670000`×1, `-11566.670000`×1, `-9733.330000`×1
- **`WhsCode`** (23 values) — `DL-GR`×3,059, `BH-GR`×2,654, `BH-LR`×2,631, `NULL`×2,204, `PB-SG`×1,481, `BH-FG`×1,004, `PB-RG`×574, `GP-FG`×522, `DL-EC`×281, `PB-ST`×164, `BH-PS`×160, `BH-EC`×153, `DL-FG`×112, `DL-J3`×101, `BH-PF`×74, `BH-BT`×65, `BH-FU`×64, `PB-JP`×53, `DL-PS`×51, `PB-SP`×17, `BH-FA`×3, `BH-SC`×2, `BH-GJ`×2
- **`TreeType`** (4 values) — `P`×8,637, `N`×2,411, `I`×2,329, `S`×2,054
- **`TaxStatus`** (1 values) — `Y`×15,431
- **`UseBaseUn`** (2 values) — `N`×13,098, `Y`×2,333
- **`InvntSttus`** (2 values) — `O`×12,694, `C`×2,737
- **`OcrCode`** (28 values) — `OLIVE`×3,290, `MUSTARD`×2,595, `CANOLA`×2,464, `SOYABEAN`×1,545, `NULL`×1,445, `SUNFLOWR`×1,077, `GROUNDNT`×680, `BLENDED`×608, `GHEE`×538, `INFINITE`×351, `HONEY`×292, `RICEBRAN`×134, `COCONUT`×103, `SEEDS`×83, `GIFT PK`×48, `SPICES`×47, `COTTONSD`×33, `RICE`×28, `COFFEE`×16, `SESAME`×16, `SlICEDOL`×16, `TEA`×9, `KITCHEN`×7, `BST`×2, `COSMETIC`×1, `TROLLYBG`×1, `PAIN OIL`×1, `TIN`×1
- **`VatPrcnt`** (4 values) — `5.000000`×12,307, `0.000000`×2,197, `12.000000`×690, `18.000000`×237
- **`VatGroup`** (9 values) — `IGST@5`×7,418, `∅`×4,057, `CG+SG@5`×1,787, `NULL`×1,398, `IGST@12`×577, `IGST@18`×179, `CG+SG@12`×11, `CG+SG@18`×3, `IGST@0`×1
- **`VolUnit`** (2 values) — `4`×13,227, `NULL`×2,204
- **`Factor1`** (2 values) — `1.000000`×13,227, `0.000000`×2,204
- **`Factor2`** (14 values) — `1.000000`×12,669, `0.000000`×2,204, `4.000000`×221, `16.000000`×87, `20.000000`×85, `12.000000`×63, `10.000000`×39, `6.000000`×23, `24.000000`×17, `3.000000`×9, `15.000000`×5, `5.000000`×5, `9.000000`×3, `2.000000`×1
- **`Factor3`** (2 values) — `1.000000`×13,227, `0.000000`×2,204
- **`Factor4`** (2 values) — `1.000000`×13,227, `0.000000`×2,204
- **`UpdInvntry`** (1 values) — `Y`×15,431
- **`FinncPriod`** (24 values) — `8`×1,595, `9`×1,452, `7`×1,361, `6`×1,266, `10`×1,173, `41`×966, `25`×818, `12`×705, `18`×559, `15`×523, `16`×519, `19`×511, `11`×493, `14`×489, `17`×418, `20`×397, `23`×372, `21`×356, `22`×333, `44`×302, `42`×288, `24`×229, `43`×208, `45`×98
- **`ObjType`** (1 values) — `14`×15,431
- **`IsAqcuistn`** (1 values) — `N`×15,431
- **`DropShip`** (1 values) — `N`×15,431
- **`TaxCode`** (8 values) — `IGST@5`×6,729, `CG+SG@5`×5,578, `Exampt`×2,194, `IGST@12`×357, `CG+SG@12`×332, `CG+SG@18`×175, `IGST@18`×63, `CG+SG@0`×3
- **`TaxType`** (1 values) — `Y`×15,431
- **`BackOrdr`** (2 values) — `NULL`×13,437, `Y`×1,994
- **`PickStatus`** (1 values) — `N`×15,431
- **`TrnsCode`** (1 values) — `-1`×15,431
- **`WtLiable`** (1 values) — `N`×15,431
- **`DeferrTax`** (1 values) — `N`×15,431
- **`unitMsr`** (7 values) — `PCS`×12,333, `NULL`×2,695, `SET`×358, `NOS`×19, `LTR`×17, `KGS`×6, `MTR`×3
- **`NumPerMsr`** (2 values) — `1.000000`×13,227, `0.000000`×2,204
- **`CEECFlag`** (1 values) — `S`×15,431
- **`CountryOrg`** (4 values) — `NULL`×15,425, `IN`×3, `∅`×2, `AU`×1
- **`LineType`** (1 values) — `R`×15,431
- **`OwnerCode`** (4 values) — `NULL`×15,305, `20`×121, `14`×4, `2`×1
- **`ConsumeFCT`** (3 values) — `N`×11,298, `NULL`×2,204, `Y`×1,929
- **`BasePrice`** (1 values) — `E`×15,431
- **`DistribExp`** (2 values) — `Y`×11,054, `N`×4,377
- **`DescOW`** (2 values) — `N`×15,417, `Y`×14
- **`DetailsOW`** (1 values) — `N`×15,431
- **`GrossBase`** (4 values) — `-6`×10,262, `NULL`×2,329, `-11`×2,204, `-1`×636
- **`TaxOnly`** (1 values) — `N`×15,431
- **`WtCalced`** (1 values) — `N`×15,431
- **`CiOppLineN`** (1 values) — `-1`×15,431
- **`CogsAcct`** (30 values) — `5000002`×2,738, `5000004`×2,252, `NULL`×2,204, `5000001`×1,742, `5000049`×1,357, `5000008`×1,295, `5000009`×994, `5000006`×637, `5000019`×527, `5000007`×492, `5000040`×350, `5000013`×285, `5000005`×90, `5000012`×89, `5000050`×88, `5000010`×68, `1102007`×68, `5000021`×38, `5000003`×32, `5000015`×27, `5000023`×13, `5000020`×12, `5000027`×9, `5000044`×7, `5000034`×5, `∅`×3, `4300002`×3, `5000051`×2, `5000047`×2, `5000033`×1
- **`ChgAsmBoMW`** (2 values) — `N`×13,227, `NULL`×2,204
- **`OcrCode2`** (29 values) — `NULL`×13,488, `02-2025`×253, `01-2025`×200, `11-2024`×198, `04-2025`×192, `12-2024`×187, `10-2024`×141, `03-2025`×130, `05-2025`×84, `09-2024`×79, `06-2025`×68, `10-2025`×51, `07-2025`×49, `12-2025`×44, `08-2024`×40, `09-2025`×32, `01-2026`×31, `03-2026`×30, `08-2025`×27, `11-2025`×26, `06-2026`×15, `04-2026`×13, `02-2026`×13, `07-2026`×10, `07-2024`×9, `05-2026`×7, `04-2024`×6, `05-2024`×4, `06-2024`×4
- **`OcrCode3`** (8 values) — `NULL`×13,795, `Sales`×1,218, `Sales RE`×325, `BackOff`×28, `OTE`×26, `Del Bkhp`×24, `Factory`×9, `FACT_COM`×6
- **`OcrCode4`** (14 values) — `NULL`×13,839, `MT`×943, `ROI`×306, `GT`×272, `Admin`×17, `CSD`×16, `Legal`×11, `E-COM`×9, `HORECA`×9, `GP-GDWN`×4, `PLANT`×2, `Accounts`×1, `IMPORT`×1, `EXPORT`×1
- **`OcrCode5`** (7 values) — `NULL`×14,203, `HR`×575, `PB`×556, `DL`×94, `UP`×1, `WB`×1, `KE`×1
- **`PostTax`** (1 values) — `Y`×15,431
- **`Excisable`** (2 values) — `N`×13,227, `NULL`×2,204
- **`CogsOcrCo2`** (20 values) — `NULL`×14,416, `02-2025`×217, `11-2024`×148, `01-2025`×126, `04-2025`×125, `12-2024`×115, `10-2024`×114, `05-2025`×58, `06-2025`×43, `03-2025`×19, `08-2024`×16, `07-2025`×9, `09-2024`×8, `12-2025`×6, `04-2024`×5, `11-2025`×2, `09-2025`×1, `08-2025`×1, `10-2025`×1, `02-2026`×1
- **`CogsOcrCo3`** (6 values) — `NULL`×14,721, `Sales`×699, `Sal CF`×4, `Sales RE`×4, `Factory`×2, `OTE`×1
- **`CogsOcrCo4`** (9 values) — `NULL`×14,739, `MT`×604, `GT`×62, `MIS`×10, `ROI`×5, `POP`×5, `E-COM`×4, `Accounts`×1, `HORECA`×1
- **`CogsOcrCo5`** (5 values) — `NULL`×14,904, `PB`×452, `HR`×66, `DL`×8, `HP`×1
- **`LocCode`** (3 values) — `2`×7,998, `1`×5,019, `3`×2,414
- **`unitMsr2`** (8 values) — `PCS`×10,728, `NULL`×4,664, `LTR`×16, `NOS`×12, `KGS`×6, `MTR`×3, `SET`×1, `∅`×1
- **`NumPerMsr2`** (2 values) — `1.000000`×13,227, `0.000000`×2,204
- **`SpecPrice`** (2 values) — `N`×15,271, `R`×160
- **`isSrvCall`** (1 values) — `N`×15,431
- **`PcDocType`** (1 values) — `-1`×15,431
- **`LinManClsd`** (1 values) — `N`×15,431
- **`VatGrpSrc`** (3 values) — `D`×7,306, `N`×5,748, `M`×2,377
- **`NoInvtryMv`** (2 values) — `N`×15,281, `Y`×150
- **`UomEntry`** (3 values) — `-1`×13,217, `0`×2,204, `2`×10
- **`UomEntry2`** (3 values) — `-1`×13,217, `0`×2,204, `2`×10
- **`UomCode`** (3 values) — `Manual`×13,217, `NULL`×2,204, `LTR`×10
- **`UomCode2`** (3 values) — `Manual`×13,217, `NULL`×2,204, `LTR`×10
- **`NeedQty`** (1 values) — `N`×15,431
- **`PartRetire`** (1 values) — `N`×15,431
- **`EnSetCost`** (2 values) — `N`×9,556, `Y`×5,875
- **`DistribIS`** (1 values) — `N`×15,431
- **`IsByPrdct`** (1 values) — `N`×15,431
- **`ItemType`** (1 values) — `4`×15,431
- **`PriceEdit`** (1 values) — `N`×15,431
- **`LinePoPrss`** (1 values) — `N`×15,431
- **`FreeChrgBP`** (1 values) — `N`×15,431
- **`TaxRelev`** (1 values) — `Y`×15,431
- **`ThirdParty`** (1 values) — `N`×15,431
- **`InvQtyOnly`** (1 values) — `N`×15,431
- **`ReturnRsn`** (1 values) — `-1`×15,431
- **`ReturnAct`** (2 values) — `1`×13,227, `-1`×2,204
- **`ItmTaxType`** (2 values) — `GR`×13,227, `NULL`×2,204
- **`SacEntry`** (3 values) — `NULL`×15,421, `34`×8, `5`×2
- **`NCMCode`** (1 values) — `-1`×15,431
- **`IsPrscGood`** (2 values) — `N`×15,162, `NULL`×269
- **`IsCstmAct`** (1 values) — `N`×15,431
- **`TaxAmtSrc`** (2 values) — `S`×13,071, `NULL`×2,360
- **`IndEscala`** (2 values) — `N`×13,010, `NULL`×2,421
- **`CESTCode`** (2 values) — `-1`×13,095, `NULL`×2,336
- **`CUSplit`** (1 values) — `N`×15,431
- **`RevCharge`** (1 values) — `N`×15,431
- **`ListNum`** (3 values) — `NULL`×15,271, `4`×149, `1`×11
- **`UoMNum`** (2 values) — `1.000000`×13,227, `0.000000`×2,204
- **`UoMDen`** (2 values) — `1.000000`×15,139, `0.000000`×292
- **`UoMNum2`** (2 values) — `1.000000`×13,227, `0.000000`×2,204
- **`UoMDen2`** (2 values) — `1.000000`×15,139, `0.000000`×292
- **`U_SchemeAgst`** (29 values) — `OLIVE`×3,170, `MUSTARD`×2,489, `NULL`×2,259, `CANOLA`×2,021, `SOYABEAN`×1,452, `SUNFLOWR`×1,073, `GROUNDNT`×679, `BLENDED`×604, `GHEE`×534, `INFINITE`×351, `HONEY`×290, `RICEBRAN`×133, `COCONUT`×103, `SEEDS`×83, `SPICES`×47, `COTTONSD`×33, `RICE`×28, `GIFT PK`×20, `SESAME`×16, `SlICEDOL`×15, `COFFEE`×10, `TEA`×9, `KITCHEN`×5, `BST`×2, `TIN`×1, `PAIN OIL`×1, `COSMETIC`×1, `BEING AGAINST CLAIM MONTH OF OCT`×1, `TROLLYBG`×1
- **`U_UNE_SCHI`** (2 values) — `N`×15,428, `Y`×3
- **`U_UNE_CALI`** (1 values) — `Y`×15,431
- **`U_UNE_CUNT`** (1 values) — `Y`×15,431
- **`U_UNE_FCT1`** (3 values) — `NULL`×13,120, `0.000000`×2,308, `1.000000`×3
- **`U_UNE_FCT2`** (4 values) — `NULL`×13,119, `0.000000`×2,309, `16.000000`×2, `20.000000`×1
- **`U_ARNO`** (2 values) — `NULL`×15,430, `H`×1
- **`U_Sub_Account`** (2 values) — `NULL`×15,430, `SALES`×1
- **`U_Purpose`** (4 values) — `NULL`×14,952, `SALE`×250, `RETURNABLE`×226, `CONSUMABLE`×3
- **`U_F_Year`** (3 values) — `NULL`×15,427, `2024-25`×3, `2023-24`×1
