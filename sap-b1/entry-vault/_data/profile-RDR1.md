# `RDR1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 75,568 | 6,447 | `DocDate` | 2024-10-01 → 2026-08-24 |
| MART | 38,783 | 6,805 | `DocDate` | 2024-10-03 → 2026-08-24 |
| BEV | 16,103 | 2,888 | `DocDate` | 2024-10-01 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 15,133 | |
| `LineNum` | INTEGER | 81% | 80% | 66% | 71% | 83% | 51% | 96 | |
| `TargetType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `TrgetEntry` | INTEGER | 61% | 76% | 60% | 68% | 56% | 81% | 12,230 | |
| `BaseRef` | NVARCHAR(16) | 6% | — | 7% | 44% | — | 40% | 1,118 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseEntry` | INTEGER | 6% | — | 7% | 44% | — | 40% | 1,117 | |
| `BaseLine` | INTEGER | 5% | — | 3% | 30% | — | 18% | 39 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItemCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 588 | |
| `Dscription` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 623 | |
| `Quantity` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,722 | |
| `ShipDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 586 | |
| `OpenQty` | DECIMAL | <1% | 7% | 2% | 4% | 29% | 10% | 113 | |
| `Price` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 4,538 | |
| `Currency` | NVARCHAR(3) | 89% | 99% | 81% | 83% | 99% | 96% | 3 | |
| `Rate` | DECIMAL | <1% | — | <1% | — | — | — | 7 | |
| `DiscPrcnt` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `LineTotal` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 21,877 | |
| `TotalFrgn` | DECIMAL | <1% | — | <1% | — | — | — | 7 | |
| `OpenSum` | DECIMAL | 30% | 68% | 46% | 43% | 81% | 85% | 11,475 | |
| `OpenSumFC` | DECIMAL | <1% | — | — | — | — | — | 7 | |
| `WhsCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 65 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 58 | |
| `TaxStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBuyPr` | DECIMAL | 5% | — | 99% | — | — | 100% | 502 | |
| `PriceBefDi` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 4,538 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 586 | |
| `OpenCreQty` | DECIMAL | <1% | 7% | 2% | 4% | 29% | 10% | 113 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseCard` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 453 | |
| `TotalSumSy` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 21,877 | |
| `OpenSumSys` | DECIMAL | 30% | 68% | 46% | 43% | 81% | 85% | 11,475 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `OcrCode` | NVARCHAR(8) | 100% | 100% | 98% | 100% | 100% | 100% | 38 | |
| `VatPrcnt` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `VatGroup` | NVARCHAR(8) | 73% | 80% | 60% | 25% | 83% | 17% | 8 | |
| `PriceAfVAT` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 4,603 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor1` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Factor2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 18 | |
| `Factor3` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `Factor4` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 8 | |
| `PackQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,730 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDocNum` | INTEGER | 6% | — | 7% | 44% | — | 41% | 1,120 | |
| `BaseAtCard` | NVARCHAR(200) | 3% | — | <1% | 7% | — | <1% | 395 | |
| `VatSum` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 22,052 | |
| `VatSumFrgn` | DECIMAL | <1% | — | <1% | — | — | — | 2 | |
| `VatSumSy` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 22,052 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DistribSum` | DECIMAL | <1% | — | — | — | — | — | 3 | |
| `DstrbSumSC` | DECIMAL | <1% | — | — | — | — | — | 3 | |
| `GrssProfit` | DECIMAL | 89% | 99% | 100% | 83% | 99% | 100% | 23,587 | |
| `GrssProfSC` | DECIMAL | 89% | 99% | 100% | 83% | 99% | 100% | 23,587 | |
| `GrssProfFC` | DECIMAL | <1% | — | <1% | — | — | — | 9 | |
| `VisOrder` | INTEGER | 80% | 80% | 65% | 70% | 83% | 49% | 96 | |
| `INMPrice` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 4,587 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 28 | |
| `TaxCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `TaxType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OrigItem` | NVARCHAR(50) | 6% | <1% | 9% | 3% | 1% | 8% | 396 | |
| `BackOrdr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FreeTxt` | NVARCHAR(100) | <1% | — | <1% | — | — | <1% | 3 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PickIdNo` | INTEGER | 18% | 7% | 26% | <1% | — | — | 3,223 | |
| `TrnsCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatAppld` | DECIMAL | 55% | 75% | 51% | 57% | 56% | 79% | 18,624 | |
| `VatAppldSC` | DECIMAL | 55% | 75% | 51% | 57% | 56% | 79% | 18,624 | |
| `BaseQty` | DECIMAL | 6% | — | 7% | 44% | — | 40% | 710 | |
| `BaseOpnQty` | DECIMAL | 6% | — | 7% | 44% | — | 41% | 710 | |
| `WtLiable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineVat` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 22,052 | |
| `LineVatlF` | DECIMAL | <1% | — | <1% | — | — | — | 2 | |
| `LineVatS` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 22,052 | |
| `unitMsr` | NVARCHAR(100) | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `NumPerMsr` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Text` | NCLOB | <1% | — | — | <1% | — | — | 0 | |
| `OwnerCode` | INTEGER | 5% | — | <1% | 16% | — | <1% | 3 | |
| `StockPrice` | DECIMAL | 95% | 96% | 94% | 95% | 92% | 98% | 7,578 | |
| `ConsumeFCT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 711 | |
| `ShipToDesc` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 685 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GTotal` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 19,592 | |
| `GTotalFC` | DECIMAL | <1% | — | <1% | — | — | — | 8 | |
| `GTotalSC` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 19,592 | |
| `DistribExp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `TaxOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DelivrdQty` | DECIMAL | 61% | 76% | 60% | 68% | 56% | 81% | 1,688 | |
| `CogsOcrCod` | NVARCHAR(8) | 100% | 100% | 98% | 100% | 100% | 100% | 41 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsAcct` | NVARCHAR(15) | 99% | 99% | 99% | 100% | 100% | 99% | 41 | |
| `ChgAsmBoMW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OcrCode2` | NVARCHAR(8) | <1% | — | — | — | — | — | 2 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excisable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsOcrCo2` | NVARCHAR(8) | <1% | — | — | — | — | — | 2 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `StockValue` | DECIMAL | 94% | 96% | 94% | 95% | 92% | 98% | 38,271 | |
| `GPTtlBasPr` | DECIMAL | 5% | — | 99% | — | — | 100% | 2,292 | |
| `unitMsr2` | NVARCHAR(100) | 89% | 87% | 72% | 100% | 100% | 100% | 9 | |
| `NumPerMsr2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SpecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `isSrvCall` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcDocType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PcQuantity` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,722 | |
| `LinManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `VatGrpSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `NoInvtryMv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UomEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `UomEntry2` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `UomCode` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `UomCode2` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `NeedQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartRetire` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,724 | |
| `OpenInvQty` | DECIMAL | <1% | 7% | 2% | 4% | 29% | 10% | 113 | |
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
| `GPBefDisc` | DECIMAL | 89% | 99% | 81% | 83% | 99% | 96% | 4,603 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItmTaxType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SacEntry` | INTEGER | <1% | — | — | — | — | — | 3 | |
| `NCMCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `HsnEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 102 | |
| `IsPrscGood` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 98% | 100% | 98% | 98% | 100% | 95% | 1 | |
| `IndEscala` | NVARCHAR(1) | 98% | 100% | 98% | 97% | 100% | 95% | 1 | |
| `CESTCode` | INTEGER | 92% | 100% | 88% | 36% | 100% | 35% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ListNum` | SMALLINT | 17% | <1% | 10% | 4% | <1% | <1% | 3 | |
| `UoMNum` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `UoMDen` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UoMNum2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UoMDen2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `U_Remarks` | NVARCHAR(100) | <1% | — | <1% | — | — | <1% | 18 | |
| `U_SchemeAgst` | NVARCHAR(50) | 98% | 99% | 97% | 99% | 100% | 98% | 45 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_BilltyNumber` | NVARCHAR(100) | <1% | — | — | — | — | — | 3 | |
| `U_ARNO` | NVARCHAR(100) | <1% | — | — | — | — | — | 1 | |
| `U_Sub_Account` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_Purpose` | NVARCHAR(10) | 4% | <1% | 2% | — | — | — | 3 | |
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

- **`TargetType`** (3 values) — `13`×43,906, `-1`×29,126, `15`×2,536
- **`BaseType`** (2 values) — `-1`×70,766, `23`×4,802
- **`LineStatus`** (2 values) — `C`×75,281, `O`×287
- **`Currency`** (4 values) — `INR`×67,206, `NULL`×8,294, `∅`×55, `USD`×13
- **`Rate`** (8 values) — `0.000000`×75,554, `86.050000`×6, `85.400000`×2, `86.100000`×2, `86.700000`×1, `85.950000`×1, `NULL`×1, `84.700000`×1
- **`DiscPrcnt`** (3 values) — `0.000000`×75,560, `NULL`×7, `-18.000000`×1
- **`TotalFrgn`** (7 values) — `0.000000`×75,559, `131839.650000`×2, `211382.250000`×2, `342439.500000`×2, `134737.500000`×1, `420146.430000`×1, `132240.600000`×1
- **`OpenSumFC`** (7 values) — `0.000000`×75,562, `420146.430000`×1, `134737.500000`×1, `132240.600000`×1, `131839.650000`×1, `211382.250000`×1, `342439.500000`×1
- **`WhsCode`** (25 values) — `BH-FG`×33,203, `GP-FG`×21,183, `PB-ST`×10,396, `PB-SP`×4,041, `BH-FU`×2,895, `DL-FG`×1,455, `DL-PS`×718, `PB-JP`×620, `PB-SG`×224, `DL-GR`×181, `DL-EC`×173, `BH-GJ`×144, `BH-PS`×140, `PB-RG`×86, `BH-PF`×33, `BH-EX`×25, `BH-LR`×17, `DL-J3`×15, `NULL`×6, `BH-OT`×4, `DL-POP`×3, `PB-PS`×2, `BH-VA`×2, `BH-FA`×1, `DL-FA`×1
- **`TreeType`** (2 values) — `P`×70,990, `N`×4,578
- **`TaxStatus`** (1 values) — `Y`×75,568
- **`UseBaseUn`** (1 values) — `N`×75,568
- **`InvntSttus`** (2 values) — `C`×44,680, `O`×30,888
- **`VatPrcnt`** (5 values) — `5.000000`×72,210, `12.000000`×1,760, `18.000000`×1,582, `0.000000`×14, `0.100000`×2
- **`VatGroup`** (9 values) — `IGST@5`×37,476, `CG+SG@5`×15,501, `∅`×13,882, `NULL`×6,323, `IGST@12`×1,090, `IGST@18`×910, `CG+SG@12`×195, `CG+SG@18`×183, `IGST@0`×8
- **`VolUnit`** (2 values) — `4`×75,562, `NULL`×6
- **`Factor1`** (2 values) — `1.000000`×75,562, `0.000000`×6
- **`Factor2`** (18 values) — `1.000000`×73,359, `4.000000`×810, `16.000000`×629, `20.000000`×356, `10.000000`×111, `24.000000`×101, `12.000000`×94, `5.000000`×29, `15.000000`×16, `9.000000`×13, `3.000000`×12, `6.000000`×9, `36.000000`×9, `0.000000`×6, `35.000000`×6, `2.000000`×5, `40.000000`×2, `18.000000`×1
- **`Factor3`** (5 values) — `1.000000`×75,556, `0.000000`×6, `10.000000`×3, `20.000000`×2, `4.000000`×1
- **`Factor4`** (8 values) — `1.000000`×75,549, `275.000000`×7, `0.000000`×6, `1350.000000`×2, `245.000000`×1, `45.000000`×1, `490.000000`×1, `150.000000`×1
- **`UpdInvntry`** (1 values) — `Y`×75,568
- **`VatSumFrgn`** (2 values) — `0.000000`×75,567, `6591.982500`×1
- **`FinncPriod`** (23 values) — `17`×4,799, `12`×4,394, `15`×4,346, `16`×4,215, `20`×3,994, `10`×3,991, `23`×3,890, `7`×3,885, `11`×3,690, `8`×3,623, `18`×3,587, `14`×3,479, `19`×3,435, `24`×3,413, `9`×3,393, `22`×3,305, `21`×2,972, `25`×2,912, `41`×2,404, `42`×1,900, `44`×1,534, `43`×1,522, `45`×885
- **`ObjType`** (1 values) — `17`×75,568
- **`IsAqcuistn`** (1 values) — `N`×75,568
- **`DistribSum`** (3 values) — `0.000000`×75,558, `7500.000000`×8, `7142.850000`×2
- **`DstrbSumSC`** (3 values) — `0.000000`×75,558, `7500.000000`×8, `7142.850000`×2
- **`GrssProfFC`** (9 values) — `0.000000`×75,550, `11617.065600`×4, `3872.160000`×4, `211382.250000`×3, `342439.500000`×2, `131839.650000`×2, `420146.430000`×1, `134737.500000`×1, `132240.600000`×1
- **`DropShip`** (1 values) — `N`×75,568
- **`TaxCode`** (11 values) — `IGST@5`×46,512, `CG+SG@5`×25,698, `IGST@12`×1,470, `IGST@18`×1,357, `CG+SG@12`×290, `CG+SG@18`×225, `IGST@0`×9, `CG+SG@0`×3, `IGST@0.1`×2, `∅`×1, `NULL`×1
- **`TaxType`** (1 values) — `Y`×75,568
- **`BackOrdr`** (2 values) — `Y`×75,562, `NULL`×6
- **`FreeTxt`** (4 values) — `∅`×68,014, `NULL`×7,552, `HARYANA`×1, ```×1
- **`PickStatus`** (2 values) — `N`×74,315, `R`×1,253
- **`TrnsCode`** (1 values) — `-1`×75,568
- **`WtLiable`** (2 values) — `N`×75,556, `Y`×12
- **`DeferrTax`** (1 values) — `N`×75,568
- **`LineVatlF`** (2 values) — `0.000000`×75,567, `6591.982500`×1
- **`unitMsr`** (11 values) — `PCS`×74,698, `LTR`×303, `MTR`×206, `NOS`×191, `KGS`×72, `DRM`×31, `GMS`×26, `SET`×22, `MTS`×10, `NULL`×7, `∅`×2
- **`NumPerMsr`** (3 values) — `1.000000`×75,552, `1098.900000`×10, `0.000000`×6
- **`CEECFlag`** (1 values) — `S`×75,568
- **`LineType`** (1 values) — `R`×75,568
- **`OwnerCode`** (4 values) — `NULL`×72,146, `20`×3,306, `2`×87, `14`×29
- **`ConsumeFCT`** (2 values) — `Y`×75,562, `NULL`×6
- **`BasePrice`** (1 values) — `E`×75,568
- **`GTotalFC`** (8 values) — `0.000000`×75,559, `342439.500000`×2, `211382.250000`×2, `138431.639600`×1, `131839.650000`×1, `132240.600000`×1, `420146.430000`×1, `134737.500000`×1
- **`DistribExp`** (1 values) — `Y`×75,568
- **`DescOW`** (2 values) — `N`×75,363, `Y`×205
- **`DetailsOW`** (1 values) — `N`×75,568
- **`GrossBase`** (3 values) — `-6`×71,473, `-1`×4,089, `-11`×6
- **`TaxOnly`** (1 values) — `N`×75,568
- **`WtCalced`** (1 values) — `N`×75,568
- **`CiOppLineN`** (1 values) — `-1`×75,568
- **`ChgAsmBoMW`** (2 values) — `N`×75,562, `NULL`×6
- **`OcrCode2`** (3 values) — `NULL`×75,561, `06-2025`×6, `04-2024`×1
- **`PostTax`** (1 values) — `Y`×75,568
- **`Excisable`** (2 values) — `N`×75,562, `NULL`×6
- **`CogsOcrCo2`** (3 values) — `NULL`×75,561, `06-2025`×6, `04-2024`×1
- **`LocCode`** (3 values) — `2`×57,648, `3`×15,369, `1`×2,551
- **`unitMsr2`** (10 values) — `PCS`×66,289, `NULL`×8,595, `LTR`×298, `MTR`×183, `NOS`×76, `KGS`×68, `∅`×22, `SET`×22, `DRM`×13, `GMS`×2
- **`NumPerMsr2`** (2 values) — `1.000000`×75,562, `0.000000`×6
- **`SpecPrice`** (2 values) — `N`×63,071, `R`×12,497
- **`isSrvCall`** (1 values) — `N`×75,568
- **`PcDocType`** (1 values) — `-1`×75,568
- **`LinManClsd`** (2 values) — `N`×45,187, `Y`×30,381
- **`VatGrpSrc`** (3 values) — `N`×57,363, `D`×17,318, `M`×887
- **`NoInvtryMv`** (1 values) — `N`×75,568
- **`UomEntry`** (4 values) — `-1`×75,268, `2`×284, `1`×10, `0`×6
- **`UomEntry2`** (3 values) — `-1`×75,268, `2`×294, `0`×6
- **`UomCode`** (4 values) — `Manual`×75,268, `LTR`×284, `MTS`×10, `NULL`×6
- **`UomCode2`** (3 values) — `Manual`×75,268, `LTR`×294, `NULL`×6
- **`NeedQty`** (1 values) — `N`×75,568
- **`PartRetire`** (1 values) — `N`×75,568
- **`EnSetCost`** (1 values) — `N`×75,568
- **`DistribIS`** (1 values) — `N`×75,568
- **`IsByPrdct`** (1 values) — `N`×75,568
- **`ItemType`** (1 values) — `4`×75,568
- **`PriceEdit`** (1 values) — `N`×75,568
- **`LinePoPrss`** (1 values) — `N`×75,568
- **`FreeChrgBP`** (1 values) — `N`×75,568
- **`TaxRelev`** (1 values) — `Y`×75,568
- **`ThirdParty`** (1 values) — `N`×75,568
- **`InvQtyOnly`** (1 values) — `N`×75,568
- **`ReturnRsn`** (1 values) — `-1`×75,568
- **`ReturnAct`** (2 values) — `1`×69,137, `-1`×6,431
- **`ItmTaxType`** (2 values) — `GR`×75,562, `NULL`×6
- **`SacEntry`** (4 values) — `NULL`×75,562, `1`×3, `-419`×2, `-309`×1
- **`NCMCode`** (1 values) — `-1`×75,568
- **`IsPrscGood`** (1 values) — `N`×75,568
- **`IsCstmAct`** (1 values) — `N`×75,568
- **`TaxAmtSrc`** (2 values) — `S`×74,343, `NULL`×1,225
- **`IndEscala`** (2 values) — `N`×74,293, `NULL`×1,275
- **`CESTCode`** (2 values) — `-1`×69,239, `NULL`×6,329
- **`CUSplit`** (1 values) — `N`×75,568
- **`RevCharge`** (1 values) — `N`×75,568
- **`ListNum`** (4 values) — `NULL`×63,071, `4`×8,448, `1`×3,973, `-1`×76
- **`UoMNum`** (3 values) — `1.000000`×75,552, `1098.900000`×10, `0.000000`×6
- **`UoMDen`** (2 values) — `1.000000`×75,562, `0.000000`×6
- **`UoMNum2`** (2 values) — `1.000000`×75,562, `0.000000`×6
- **`UoMDen2`** (2 values) — `1.000000`×75,562, `0.000000`×6
- **`U_Remarks`** (19 values) — `NULL`×75,470, `CANOLA`×57, `OLIVE`×10, `BEING AGAINST ACADEMY CLAIM`×4, `BLENDED`×4, `BEING AGAINST SUMIT TRADERS`×4, `SPICES`×2, `GHEE`×2, `SESAME`×2, `BEING AGAINST CHUNNI KALAN ACDEMY`×2, `ACADEMY CLAIM CHUNNI KALAN`×2, `MUSTARD`×2, `SOYABEAN`×1, `GROUNDNT`×1, `SUNFLOWR`×1, `GIFT MANGO`×1, `BEING AGAINST ACADEMY NIHAL SINGH WALA`×1, `COFFEE`×1, `BEING AGAINST SHORATAGE 6241838`×1
- **`U_UNE_SCHI`** (2 values) — `N`×75,500, `Y`×68
- **`U_UNE_CALI`** (1 values) — `Y`×75,568
- **`U_UNE_CUNT`** (1 values) — `Y`×75,568
- **`U_BilltyNumber`** (4 values) — `NULL`×75,565, `6072`×1, `6407`×1, `6408`×1
- **`U_ARNO`** (2 values) — `NULL`×75,565, `41350`×3
- **`U_Sub_Account`** (2 values) — `NULL`×75,560, `BST`×8
- **`U_Purpose`** (4 values) — `NULL`×72,663, `SALE`×2,885, `BST`×11, `-`×9
- **`U_F_Year`** (2 values) — `NULL`×75,560, `2024-25`×8
