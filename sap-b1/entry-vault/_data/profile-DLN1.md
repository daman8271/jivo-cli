# `DLN1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 24,253 | 89 | `DocDate` | 2024-10-04 → 2026-08-05 |
| MART | 59,549 | 6,964 | `DocDate` | 2025-01-09 → 2026-08-24 |
| BEV | 807 | 7 | `DocDate` | 2024-10-09 → 2026-05-09 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,842 | |
| `LineNum` | INTEGER | 89% | 90% | 63% | 35% | 89% | 86% | 157 | |
| `TargetType` | INTEGER | 99% | 99% | 97% | 100% | 100% | 100% | 4 | |
| `TrgetEntry` | INTEGER | 90% | 98% | 93% | 38% | 98% | — | 3,416 | |
| `BaseRef` | NVARCHAR(16) | 13% | 3% | 32% | — | 2% | — | 683 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `BaseEntry` | INTEGER | 13% | 3% | 32% | — | 2% | — | 678 | |
| `BaseLine` | INTEGER | 11% | 3% | 25% | — | 2% | — | 61 | |
| `LineStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItemCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 859 | |
| `Dscription` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 861 | |
| `Quantity` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,115 | |
| `ShipDate` | TIMESTAMP | 11% | <1% | 30% | — | — | — | 185 | |
| `OpenQty` | DECIMAL | <1% | <1% | 1% | 2% | <1% | — | 10 | |
| `Price` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 770 | |
| `Currency` | NVARCHAR(3) | 33% | 37% | 95% | 16% | 36% | — | 1 | |
| `DiscPrcnt` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `LineTotal` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 2,473 | |
| `OpenSum` | DECIMAL | 32% | 37% | 91% | 16% | 35% | — | 2,402 | |
| `WhsCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `AcctCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 42 | |
| `TaxStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBuyPr` | DECIMAL | 6% | — | 96% | — | — | — | 277 | |
| `PriceBefDi` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 770 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 410 | |
| `OpenCreQty` | DECIMAL | <1% | <1% | 1% | 2% | <1% | — | 12 | |
| `UseBaseUn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseCard` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 52 | |
| `TotalSumSy` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 2,473 | |
| `OpenSumSys` | DECIMAL | 32% | 37% | 91% | 16% | 35% | — | 2,399 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `OcrCode` | NVARCHAR(8) | 100% | 100% | 96% | 100% | 100% | 100% | 27 | |
| `VatPrcnt` | DECIMAL | 100% | 100% | 99% | 100% | 100% | 100% | 4 | |
| `VatGroup` | NVARCHAR(8) | 89% | 90% | 64% | 35% | 85% | 86% | 9 | |
| `PriceAfVAT` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 758 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor1` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 9 | |
| `Factor3` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Factor4` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PackQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 813 | |
| `UpdInvntry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDocNum` | INTEGER | 13% | 3% | 32% | — | 2% | — | 682 | |
| `BaseAtCard` | NVARCHAR(200) | <1% | <1% | — | — | <1% | — | 8 | |
| `VatSum` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 2,548 | |
| `VatSumSy` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 2,548 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsAqcuistn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrssProfit` | DECIMAL | 34% | 37% | 96% | 16% | 36% | — | 3,143 | |
| `GrssProfSC` | DECIMAL | 34% | 37% | 96% | 16% | 36% | — | 3,143 | |
| `VisOrder` | INTEGER | 88% | 90% | 62% | 35% | 88% | 86% | 151 | |
| `INMPrice` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 850 | |
| `DropShip` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 26 | |
| `TaxCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 8 | |
| `TaxType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OrigItem` | NVARCHAR(50) | 4% | 2% | 5% | 4% | 2% | — | 260 | |
| `BackOrdr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FreeTxt` | NVARCHAR(100) | <1% | — | — | — | — | — | 2 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PickIdNo` | INTEGER | <1% | <1% | <1% | — | — | — | 11 | |
| `TrnsCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatAppld` | DECIMAL | 32% | 37% | 89% | 16% | 35% | — | 2,451 | |
| `VatAppldSC` | DECIMAL | 32% | 37% | 89% | 16% | 35% | — | 2,451 | |
| `BaseQty` | DECIMAL | 13% | 3% | 32% | — | 2% | — | 333 | |
| `BaseOpnQty` | DECIMAL | 13% | 3% | 32% | — | 2% | — | 345 | |
| `WtLiable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LineVat` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 2,548 | |
| `LineVatS` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 2,548 | |
| `unitMsr` | NVARCHAR(100) | 93% | 96% | 99% | 100% | 100% | 100% | 9 | |
| `NumPerMsr` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CountryOrg` | NVARCHAR(3) | — | <1% | — | — | — | — | 0 | |
| `LineType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Text` | NCLOB | <1% | — | — | — | — | — | 0 | |
| `StockPrice` | DECIMAL | 64% | 67% | 77% | 99% | 67% | — | 3,000 | |
| `ConsumeFCT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `StockSum` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 2,499 | |
| `StockSumSc` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 2,499 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 75 | |
| `ShipToDesc` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 61 | |
| `BasePrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GTotal` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 2,095 | |
| `GTotalSC` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 2,095 | |
| `DistribExp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DescOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DetailsOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 71% | 68% | 99% | 100% | 69% | 100% | 2 | |
| `TaxOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WtCalced` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QtyToShip` | DECIMAL | 1% | <1% | <1% | — | — | — | 93 | |
| `OrderedQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,116 | |
| `CogsOcrCod` | NVARCHAR(8) | 100% | 100% | 96% | 100% | 100% | 100% | 33 | |
| `CiOppLineN` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsAcct` | NVARCHAR(15) | 100% | 99% | 100% | 100% | 100% | 100% | 36 | |
| `ChgAsmBoMW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ActDelDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 397 | |
| `OcrCode2` | NVARCHAR(8) | — | <1% | 23% | — | <1% | — | 0 | |
| `PostTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excisable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CogsOcrCo2` | NVARCHAR(8) | — | <1% | 23% | — | <1% | — | 0 | |
| `LocCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `StockValue` | DECIMAL | 64% | 67% | 77% | 99% | 67% | — | 7,867 | |
| `GPTtlBasPr` | DECIMAL | 6% | — | 96% | — | — | — | 778 | |
| `unitMsr2` | NVARCHAR(100) | 66% | 94% | 38% | 100% | 99% | 100% | 9 | |
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
| `InvQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,115 | |
| `OpenInvQty` | DECIMAL | <1% | <1% | 1% | 2% | <1% | — | 12 | |
| `EnSetCost` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RetCost` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `DistribIS` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsByPrdct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ItemType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PriceEdit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LinePoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FreeChrgBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxRelev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ThirdParty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvQtyOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GPBefDisc` | DECIMAL | 33% | 37% | 95% | 16% | 36% | — | 758 | |
| `ReturnRsn` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReturnAct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ItmTaxType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NCMCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `HsnEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 74 | |
| `IsPrscGood` | NVARCHAR(1) | 97% | 95% | 100% | 100% | 95% | 100% | 1 | |
| `IsCstmAct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxAmtSrc` | NVARCHAR(1) | 72% | 68% | 99% | 100% | 70% | 100% | 1 | |
| `IndEscala` | NVARCHAR(1) | 71% | 68% | 99% | 100% | 69% | 100% | 1 | |
| `CESTCode` | INTEGER | 100% | 100% | 100% | 100% | 96% | 100% | 1 | |
| `CUSplit` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevCharge` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ListNum` | SMALLINT | 36% | 29% | 3% | 82% | 33% | 100% | 2 | |
| `UoMNum` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMDen` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMNum2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UoMDen2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Remarks` | NVARCHAR(100) | <1% | <1% | <1% | 60% | — | — | 81 | |
| `U_SchemeAgst` | NVARCHAR(50) | 100% | 100% | 96% | 100% | 100% | 100% | 30 | |
| `U_UNE_SCHI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `U_UNE_CALI` | NVARCHAR(1) | 100% | n/a | 100% | 100% | n/a | 100% | 1 | |
| `U_UNE_CUNT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_FCT1` | DECIMAL | 3% | 7% | 4% | 7% | 7% | 14% | 2 | |
| `U_UNE_FCT2` | DECIMAL | 3% | 7% | 4% | 7% | 7% | 14% | 11 | |
| `U_LNDCSTNO` | NVARCHAR(100) | <1% | <1% | — | — | <1% | — | 2 | |
| `U_BilltyNumber` | NVARCHAR(100) | <1% | — | — | 2% | — | — | 18 | |
| `U_ARNO` | NVARCHAR(100) | <1% | — | — | 2% | — | — | 2 | |
| `U_Sub_Account` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_Purpose` | NVARCHAR(10) | 69% | 100% | 76% | 100% | 100% | 100% | 5 | |
| `U_F_Year` | NVARCHAR(10) | <1% | — | — | — | — | — | 2 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BiltyDate` | OIL, BEV | **MART** |
| `U_UNE_CALI` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TargetType`** (5 values) — `13`×20,539, `-1`×2,152, `16`×1,204, `NULL`×179, `15`×179
- **`BaseType`** (4 values) — `-1`×21,031, `17`×2,708, `16`×335, `15`×179
- **`LineStatus`** (2 values) — `C`×24,230, `O`×23
- **`OpenQty`** (10 values) — `0.000000`×24,235, `1.000000`×7, `2.000000`×4, `92.994400`×1, `7.000000`×1, `4.000000`×1, `49.862600`×1, `900.000000`×1, `3.000000`×1, `200.000000`×1
- **`Currency`** (2 values) — `NULL`×16,290, `INR`×7,963
- **`WhsCode`** (24 values) — `DL-EC`×10,479, `DL-FG`×4,517, `BH-LR`×3,640, `BH-FG`×2,385, `BH-PP`×751, `DL-GR`×380, `GP-FG`×375, `BH-FU`×328, `BH-GJ`×272, `BH-GR`×259, `BH-WST`×231, `BH-PC`×156, `DL-PS`×155, `PB-SG`×95, `PB-ST`×55, `PB-RG`×49, `PB-SP`×48, `BH-PF`×21, `DL-POP`×19, `BH-EX`×13, `PB-JP`×13, `BH-EC`×8, `BH-CRUDE`×2, `BH-PM`×2
- **`SlpCode`** (12 values) — `-1`×16,356, `4`×5,318, `23`×1,502, `18`×909, `24`×103, `80`×36, `30`×17, `11`×4, `84`×3, `46`×2, `81`×2, `17`×1
- **`TreeType`** (4 values) — `P`×7,976, `I`×6,922, `S`×6,204, `N`×3,151
- **`TaxStatus`** (1 values) — `Y`×24,253
- **`OpenCreQty`** (12 values) — `0.000000`×24,231, `1.000000`×8, `2.000000`×5, `7.000000`×1, `6.000000`×1, `40.000000`×1, `3.000000`×1, `4.000000`×1, `49.862600`×1, `900.000000`×1, `200.000000`×1, `92.994400`×1
- **`UseBaseUn`** (2 values) — `N`×17,371, `Y`×6,882
- **`InvntSttus`** (2 values) — `C`×22,435, `O`×1,818
- **`OcrCode`** (28 values) — `OLIVE`×6,795, `CANOLA`×3,872, `BST`×2,974, `MUSTARD`×2,226, `SUNFLOWR`×1,433, `GHEE`×1,320, `GROUNDNT`×1,138, `INFINITE`×1,127, `SOYABEAN`×773, `BLENDED`×659, `HONEY`×545, `RICE`×424, `COCONUT`×355, `SEEDS`×164, `SPICES`×163, `RICEBRAN`×117, `GIFT PK`×78, `NULL`×28, `COFFEE`×15, `FLAKES`×14, `KITCHEN`×9, `PAIN OIL`×7, `SlICEDOL`×6, `COTTONSD`×5, `SESAME`×3, `GADGETS`×1, `ATTA`×1, `VITAMINS`×1
- **`VatPrcnt`** (4 values) — `5.000000`×19,845, `18.000000`×2,425, `12.000000`×1,941, `0.000000`×42
- **`VatGroup`** (9 values) — `IGST@5`×13,484, `CG+SG@5`×4,255, `∅`×2,674, `CG+SG@18`×1,497, `IGST@12`×1,026, `IGST@18`×687, `CG+SG@12`×609, `CG+SG@0`×11, `IGST@0`×10
- **`VolUnit`** (1 values) — `4`×24,253
- **`Factor1`** (1 values) — `1.000000`×24,253
- **`Factor2`** (9 values) — `1.000000`×23,970, `4.000000`×193, `16.000000`×36, `20.000000`×31, `12.000000`×10, `10.000000`×6, `3.000000`×5, `2.000000`×1, `24.000000`×1
- **`Factor3`** (1 values) — `1.000000`×24,253
- **`Factor4`** (1 values) — `1.000000`×24,253
- **`UpdInvntry`** (1 values) — `Y`×24,253
- **`FinncPriod`** (23 values) — `9`×6,601, `8`×5,190, `7`×4,475, `10`×2,895, `15`×607, `16`×540, `41`×527, `12`×478, `14`×429, `20`×395, `18`×344, `21`×343, `19`×313, `11`×287, `17`×277, `22`×166, `23`×121, `42`×109, `24`×55, `25`×48, `44`×23, `43`×18, `45`×12
- **`ObjType`** (1 values) — `15`×24,253
- **`IsAqcuistn`** (1 values) — `N`×24,253
- **`DropShip`** (1 values) — `N`×24,253
- **`TaxCode`** (8 values) — `CG+SG@5`×13,132, `IGST@5`×6,713, `CG+SG@18`×2,191, `CG+SG@12`×1,486, `IGST@12`×455, `IGST@18`×234, `CG+SG@0`×25, `IGST@0`×17
- **`TaxType`** (1 values) — `Y`×24,253
- **`BackOrdr`** (1 values) — `Y`×24,253
- **`FreeTxt`** (3 values) — `∅`×17,200, `NULL`×7,052, `TEST`×1
- **`PickStatus`** (1 values) — `N`×24,253
- **`PickIdNo`** (12 values) — `NULL`×24,187, `516`×14, `3450`×12, `3510`×10, `528`×8, `3924`×7, `4351`×6, `793`×3, `4191`×2, `3511`×2, `529`×1, `2798`×1
- **`TrnsCode`** (1 values) — `-1`×24,253
- **`WtLiable`** (1 values) — `N`×24,253
- **`DeferrTax`** (1 values) — `N`×24,253
- **`unitMsr`** (10 values) — `PCS`×20,954, `NULL`×1,649, `SET`×1,164, `LTR`×358, `NOS`×46, `MTR`×43, `KGS`×27, `DRM`×7, `GMS`×4, `∅`×1
- **`NumPerMsr`** (1 values) — `1.000000`×24,253
- **`CEECFlag`** (1 values) — `S`×24,253
- **`LineType`** (1 values) — `R`×24,253
- **`ConsumeFCT`** (2 values) — `N`×21,470, `Y`×2,783
- **`BasePrice`** (1 values) — `E`×24,253
- **`DistribExp`** (2 values) — `N`×13,077, `Y`×11,176
- **`DescOW`** (1 values) — `N`×24,253
- **`DetailsOW`** (1 values) — `N`×24,253
- **`GrossBase`** (3 values) — `-6`×14,559, `NULL`×6,917, `-1`×2,777
- **`TaxOnly`** (1 values) — `N`×24,253
- **`WtCalced`** (1 values) — `N`×24,253
- **`CiOppLineN`** (1 values) — `-1`×24,253
- **`ChgAsmBoMW`** (1 values) — `N`×24,253
- **`PostTax`** (1 values) — `Y`×24,253
- **`Excisable`** (1 values) — `N`×24,253
- **`LocCode`** (3 values) — `1`×15,550, `2`×8,443, `3`×260
- **`unitMsr2`** (10 values) — `PCS`×15,389, `NULL`×8,303, `LTR`×357, `NOS`×75, `KGS`×43, `MTR`×41, `SET`×20, `∅`×15, `DRM`×7, `GMS`×3
- **`NumPerMsr2`** (1 values) — `1.000000`×24,253
- **`SpecPrice`** (2 values) — `N`×15,609, `R`×8,644
- **`isSrvCall`** (1 values) — `N`×24,253
- **`PcDocType`** (1 values) — `-1`×24,253
- **`LinManClsd`** (2 values) — `N`×22,419, `Y`×1,834
- **`VatGrpSrc`** (3 values) — `D`×13,046, `N`×11,182, `M`×25
- **`NoInvtryMv`** (1 values) — `N`×24,253
- **`UomEntry`** (2 values) — `-1`×23,896, `2`×357
- **`UomEntry2`** (2 values) — `-1`×23,896, `2`×357
- **`UomCode`** (2 values) — `Manual`×23,896, `LTR`×357
- **`UomCode2`** (2 values) — `Manual`×23,896, `LTR`×357
- **`NeedQty`** (1 values) — `N`×24,253
- **`PartRetire`** (1 values) — `N`×24,253
- **`OpenInvQty`** (12 values) — `0.000000`×24,231, `1.000000`×8, `2.000000`×5, `200.000000`×1, `49.862600`×1, `900.000000`×1, `4.000000`×1, `6.000000`×1, `7.000000`×1, `92.994400`×1, `3.000000`×1, `40.000000`×1
- **`EnSetCost`** (2 values) — `N`×24,252, `Y`×1
- **`RetCost`** (2 values) — `0.000000`×24,252, `139.064100`×1
- **`DistribIS`** (1 values) — `N`×24,253
- **`IsByPrdct`** (1 values) — `N`×24,253
- **`ItemType`** (1 values) — `4`×24,253
- **`PriceEdit`** (1 values) — `N`×24,253
- **`LinePoPrss`** (1 values) — `N`×24,253
- **`FreeChrgBP`** (1 values) — `N`×24,253
- **`TaxRelev`** (1 values) — `Y`×24,253
- **`ThirdParty`** (1 values) — `N`×24,253
- **`InvQtyOnly`** (1 values) — `N`×24,253
- **`ReturnRsn`** (1 values) — `-1`×24,253
- **`ReturnAct`** (2 values) — `1`×21,197, `-1`×3,056
- **`ItmTaxType`** (1 values) — `GR`×24,253
- **`NCMCode`** (1 values) — `-1`×24,253
- **`IsPrscGood`** (2 values) — `N`×23,543, `NULL`×710
- **`IsCstmAct`** (1 values) — `N`×24,253
- **`TaxAmtSrc`** (2 values) — `S`×17,392, `NULL`×6,861
- **`IndEscala`** (2 values) — `N`×17,299, `NULL`×6,954
- **`CESTCode`** (1 values) — `-1`×24,253
- **`CUSplit`** (1 values) — `N`×24,253
- **`RevCharge`** (1 values) — `N`×24,253
- **`ListNum`** (3 values) — `NULL`×15,609, `1`×8,636, `-1`×8
- **`UoMNum`** (1 values) — `1.000000`×24,253
- **`UoMDen`** (1 values) — `1.000000`×24,253
- **`UoMNum2`** (1 values) — `1.000000`×24,253
- **`UoMDen2`** (1 values) — `1.000000`×24,253
- **`U_SchemeAgst`** (30 values) — `OLIVE`×6,795, `CANOLA`×3,871, `BST`×2,972, `MUSTARD`×2,226, `SUNFLOWR`×1,433, `GHEE`×1,320, `GROUNDNT`×1,138, `INFINITE`×1,126, `SOYABEAN`×773, `BLENDED`×659, `HONEY`×545, `RICE`×424, `COCONUT`×355, `SEEDS`×164, `SPICES`×163, `RICEBRAN`×115, `GIFT PK`×78, `NULL`×31, `COFFEE`×15, `FLAKES`×14, `KITCHEN`×9, `PAIN OIL`×7, `SlICEDOL`×6, `COTTONSD`×5, `SESAME`×3, `GADGETS`×1, `ATTA`×1, `VITAMINS`×1, `b`×1, `AUS`×1
- **`U_UNE_SCHI`** (2 values) — `N`×24,252, `Y`×1
- **`U_UNE_CALI`** (1 values) — `Y`×24,253
- **`U_UNE_CUNT`** (1 values) — `Y`×24,253
- **`U_UNE_FCT1`** (3 values) — `NULL`×23,463, `1.000000`×768, `0.000000`×22
- **`U_UNE_FCT2`** (12 values) — `NULL`×23,465, `1.000000`×339, `4.000000`×207, `16.000000`×118, `20.000000`×69, `0.000000`×20, `12.000000`×16, `10.000000`×8, `3.000000`×6, `6.000000`×2, `24.000000`×2, `15.000000`×1
- **`U_LNDCSTNO`** (3 values) — `NULL`×24,251, ```×1, `FG0000223FG0000223`×1
- **`U_BilltyNumber`** (19 values) — `NULL`×24,223, `6754`×2, `6834`×2, `6813`×2, `6791`×2, `6719`×2, `8033`×2, `6708`×2, `6747`×2, `6826`×2, `6796`×2, `6704`×2, `6820`×2, `6265`×1, `6264`×1, `7596`×1, `7094`×1, `6267`×1, `6817`×1
- **`U_ARNO`** (3 values) — `NULL`×24,251, `602507-A`×1, `JOB/OUT/JIVO/120`×1
- **`U_Sub_Account`** (2 values) — `NULL`×24,249, `BST`×4
- **`U_Purpose`** (6 values) — `SALE`×14,447, `NULL`×7,509, `CONSUMABLE`×1,480, `-`×741, `RETURNABLE`×69, `BST`×7
- **`U_F_Year`** (3 values) — `NULL`×24,248, `2024-25`×4, `2023-24`×1
