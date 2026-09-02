# `OITM` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 2,274 | 2,274 | `CreateDate` | 2024-09-07 → 2026-08-19 |
| MART | 1,356 | 1,356 | `CreateDate` | 2024-09-07 → 2026-08-20 |
| BEV | 2,193 | 2,193 | `CreateDate` | 2024-09-07 → 2026-08-06 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `ItemCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 2,274 | |
| `ItemName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 2,222 | |
| `FrgnName` | NVARCHAR(200) | 61% | 81% | 82% | 61% | 81% | 82% | 1,369 | |
| `ItmsGrpCod` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `CstGrpCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatGourpSa` | NVARCHAR(8) | <1% | — | — | <1% | — | — | 2 | |
| `CodeBars` | NVARCHAR(254) | <1% | — | — | <1% | — | — | 1 | |
| `VATLiable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PrchseItem` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `SellItem` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `InvntItem` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `OnHand` | DECIMAL | 59% | 18% | 39% | 59% | 18% | 39% | 799 | |
| `IsCommited` | DECIMAL | 15% | 14% | 8% | 15% | 14% | 8% | 242 | |
| `OnOrder` | DECIMAL | 16% | 14% | 8% | 16% | 14% | 8% | 236 | |
| `IncomeAcct` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 1 | |
| `ExmptIncom` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 1 | |
| `MaxLevel` | DECIMAL | <1% | — | <1% | <1% | — | <1% | 2 | |
| `DfltWH` | NVARCHAR(8) | <1% | <1% | — | <1% | <1% | — | 1 | |
| `CardCode` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 1 | |
| `SuppCatNum` | NVARCHAR(50) | <1% | — | — | <1% | — | — | 1 | |
| `BuyUnitMsr` | NVARCHAR(100) | 99% | 99% | 100% | 99% | 99% | 100% | 12 | |
| `NumInBuy` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `MinLevel` | DECIMAL | 12% | — | 4% | 12% | — | 4% | 140 | |
| `LstEvlPric` | DECIMAL | 27% | 12% | 16% | 27% | 12% | 16% | 376 | |
| `LstEvlDate` | TIMESTAMP | 61% | 81% | 18% | 61% | 81% | 18% | 5 | |
| `Canceled` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `WholSlsTax` | NVARCHAR(1) | <1% | — | — | <1% | — | — | 1 | |
| `RetilrTax` | NVARCHAR(1) | <1% | — | — | <1% | — | — | 1 | |
| `TrackSales` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SalUnitMsr` | NVARCHAR(100) | 95% | 100% | 99% | 95% | 100% | 99% | 11 | |
| `NumInSale` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Consig` | DECIMAL | 5% | 2% | 1% | 5% | 2% | 1% | 79 | |
| `EvalSystem` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `FREE` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PicturName` | NVARCHAR(200) | <1% | — | — | <1% | — | — | 1 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BlncTrnsfr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `UserText` | NCLOB | <1% | — | — | <1% | — | — | 0 | |
| `SerialNum` | NVARCHAR(17) | <1% | — | — | <1% | — | — | 1 | |
| `TreeType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `TreeQty` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 21 | |
| `LastPurPrc` | DECIMAL | 76% | 25% | 43% | 76% | 25% | 43% | 1,156 | |
| `LastPurCur` | NVARCHAR(3) | 76% | 25% | 43% | 76% | 25% | 43% | 4 | |
| `LastPurDat` | TIMESTAMP | 76% | 25% | 43% | 76% | 25% | 43% | 338 | |
| `ExitCur` | NVARCHAR(3) | <1% | — | — | <1% | — | — | 1 | |
| `ExitWH` | NVARCHAR(8) | <1% | — | — | <1% | — | — | 1 | |
| `AssetItem` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `WasCounted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ManSerNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SVolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BVolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FixCurrCms` | NVARCHAR(3) | <1% | — | — | <1% | — | — | 1 | |
| `FirmCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup1` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup2` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup3` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup4` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup5` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup6` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup7` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup8` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup9` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup10` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup11` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup12` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup13` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup14` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup15` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup16` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup17` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup18` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup19` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup20` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup21` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup22` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup23` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup24` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup25` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup26` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup27` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup28` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup29` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup30` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup31` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup32` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup33` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup34` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup35` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup36` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup37` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup38` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup39` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup40` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup41` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup42` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup43` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup44` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup45` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup46` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup47` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup48` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup49` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup50` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup51` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup52` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup53` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup54` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup55` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup56` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup57` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup58` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup59` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup60` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup61` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup62` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup63` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `QryGroup64` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 314 | |
| `ExportCode` | NVARCHAR(20) | <1% | — | — | <1% | — | — | 1 | |
| `SalFactor1` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SalFactor2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 27 | |
| `SalFactor3` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `SalFactor4` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 22 | |
| `PurFactor1` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PurFactor2` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 8 | |
| `PurFactor3` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PurFactor4` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SalFormula` | NVARCHAR(40) | <1% | — | — | <1% | — | — | 1 | |
| `PurFormula` | NVARCHAR(40) | <1% | — | — | <1% | — | — | 1 | |
| `VatGroupPu` | NVARCHAR(8) | <1% | — | — | <1% | — | — | 2 | |
| `AvgPrice` | DECIMAL | — | — | <1% | — | — | <1% | 1 | |
| `PurPackMsr` | NVARCHAR(30) | 97% | 99% | 100% | 97% | 99% | 100% | 12 | |
| `PurPackUn` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `SalPackMsr` | NVARCHAR(30) | 93% | 100% | 99% | 93% | 100% | 99% | 11 | |
| `SalPackUn` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 60 | |
| `ManBtchNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `ManOutOnly` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `validFor` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `frozenFor` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BlockOut` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ValidComm` | NVARCHAR(30) | <1% | <1% | <1% | <1% | <1% | <1% | 11 | |
| `FrozenComm` | NVARCHAR(30) | 6% | <1% | 3% | 6% | <1% | 3% | 18 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SWW` | NVARCHAR(16) | <1% | — | — | <1% | — | — | 1 | |
| `Deleted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,274 | |
| `ExpensAcct` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 1 | |
| `FrgnInAcct` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 1 | |
| `ShipType` | SMALLINT | 2% | 1% | <1% | 2% | 1% | <1% | 1 | |
| `GLMethod` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `ECInAcct` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 1 | |
| `FrgnExpAcc` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 1 | |
| `ECExpAcc` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 1 | |
| `TaxType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ByWh` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `WTLiable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `ItemType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `WarrntTmpl` | NVARCHAR(20) | <1% | — | — | <1% | — | — | 2 | |
| `BaseUnit` | NVARCHAR(20) | <1% | — | — | <1% | — | — | 1 | |
| `CountryOrg` | NVARCHAR(3) | <1% | — | — | <1% | — | — | 1 | |
| `StockValue` | DECIMAL | 31% | — | 14% | 31% | — | 14% | 648 | |
| `Phantom` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `IssueMthd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `FREE1` | NVARCHAR(1) | <1% | — | — | <1% | — | — | 1 | |
| `MngMethod` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntryUom` | NVARCHAR(100) | 89% | 100% | 90% | 89% | 100% | 90% | 11 | |
| `PlaningSys` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `PrcrmntMtd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `IndirctTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `TaxCodeAR` | NVARCHAR(8) | <1% | — | — | <1% | — | — | 1 | |
| `TaxCodeAP` | NVARCHAR(8) | <1% | — | — | <1% | — | — | 1 | |
| `OSvcCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ISvcCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ServiceGrp` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NCMCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `MatType` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `MatGrp` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ProductSrc` | NVARCHAR(2) | 62% | 81% | 71% | 62% | 81% | 71% | 3 | |
| `ServiceCtg` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ItemClass` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Excisable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ChapterID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 379 | |
| `NotifyASN` | NVARCHAR(40) | <1% | — | — | <1% | — | — | 2 | |
| `ProAssNum` | NVARCHAR(20) | <1% | — | — | <1% | — | — | 2 | |
| `DNFEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Spec` | NVARCHAR(30) | <1% | — | — | <1% | — | — | 1 | |
| `TaxCtg` | NVARCHAR(4) | <1% | — | — | <1% | — | — | 1 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 11 | |
| `Number` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 894 | |
| `FuelCode` | INTEGER | 62% | 81% | 71% | 62% | 81% | 71% | 1 | |
| `BeverTblC` | NVARCHAR(2) | <1% | — | — | <1% | — | — | 2 | |
| `BeverGrpC` | NVARCHAR(2) | <1% | — | — | <1% | — | — | 2 | |
| `BeverTM` | INTEGER | 62% | 81% | 71% | 62% | 81% | 71% | 1 | |
| `Attachment` | NCLOB | <1% | <1% | <1% | <1% | <1% | <1% | 0 | |
| `AtcEntry` | INTEGER | <1% | <1% | <1% | <1% | <1% | <1% | 16 | |
| `UgpEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PUoMEntry` | INTEGER | 2% | <1% | — | 2% | <1% | — | 1 | |
| `SUoMEntry` | INTEGER | 2% | <1% | — | 2% | <1% | — | 2 | |
| `IUoMEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `AssetClass` | NVARCHAR(20) | <1% | — | — | <1% | — | — | 2 | |
| `AssetGroup` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 2 | |
| `InventryNo` | NVARCHAR(12) | <1% | — | — | <1% | — | — | 2 | |
| `StatAsset` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Cession` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DeacAftUL` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AsstStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `GLPickMeth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `NoDiscount` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `MgrByQty` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AssetRmk1` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 1 | |
| `AssetRmk2` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 1 | |
| `DeprGroup` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 1 | |
| `AssetSerNo` | NVARCHAR(32) | <1% | — | — | <1% | — | — | 2 | |
| `CntUnitMsr` | NVARCHAR(100) | 2% | <1% | — | 2% | <1% | — | 4 | |
| `NumInCnt` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `INUoMEntry` | INTEGER | 2% | <1% | — | 2% | <1% | — | 2 | |
| `OneBOneRec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `RuleCode` | NVARCHAR(2) | <1% | — | — | <1% | — | — | 1 | |
| `ScsCode` | NVARCHAR(10) | <1% | — | — | <1% | — | — | 1 | |
| `SpProdType` | NVARCHAR(2) | <1% | — | — | <1% | — | — | 1 | |
| `CompoWH` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1,315 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,194 | |
| `VirtAstItm` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SouVirAsst` | NVARCHAR(50) | <1% | — | — | <1% | — | — | 1 | |
| `InCostRoll` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `EnAstSeri` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LinkRsc` | NVARCHAR(50) | <1% | — | — | <1% | — | — | 1 | |
| `PriceUnit` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `GSTRelevnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `SACEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GstTaxCtg` | NVARCHAR(1) | 100% | 99% | 88% | 100% | 99% | 88% | 4 | |
| `SOIExc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `TNVED` | NVARCHAR(10) | <1% | — | — | <1% | — | — | 1 | |
| `Imported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AutoBatch` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CstmActing` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `TaxCatCode` | NVARCHAR(50) | <1% | — | — | <1% | — | — | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `NVECode` | NVARCHAR(6) | <1% | — | — | <1% | — | — | 1 | |
| `CESTCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LegalText` | NVARCHAR(250) | <1% | — | — | <1% | — | — | 1 | |
| `Traceable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `IfrsPsRev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `PlPaTaxCat` | NVARCHAR(2) | <1% | — | — | <1% | — | — | 2 | |
| `PPTExReSa` | NVARCHAR(2) | <1% | — | — | <1% | — | — | 2 | |
| `PPTExRePr` | NVARCHAR(2) | <1% | — | — | <1% | — | — | 2 | |
| `ProdctType` | NVARCHAR(1) | <1% | — | — | <1% | — | — | 1 | |
| `ProdTypeEx` | NVARCHAR(10) | <1% | — | — | <1% | — | — | 1 | |
| `SalUomNum` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SalUomDen` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BuyUomNum` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BuyUomDen` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `IncUomNum` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `IncUomDen` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `NoApDisc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `U_Tax_Rate` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `U_Brand` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `U_Unit` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `U_Variety` | NVARCHAR(50) | 100% | 100% | 97% | 100% | 100% | 97% | 185 | |
| `U_SKU` | NVARCHAR(50) | 66% | 88% | 59% | 66% | 88% | 59% | 71 | |
| `U_Sub_Group` | NVARCHAR(100) | 100% | 100% | 100% | 100% | 100% | 100% | 129 | |
| `U_IsLitre` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `U_Gross_Weight` | DECIMAL | 24% | 17% | 4% | 24% | 17% | 4% | 343 | |
| `U_UTL_ST_ISSERVICE` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `U_MRP` | INTEGER | 14% | 14% | 7% | 14% | 14% | 7% | 134 | |
| `U_JRID` | INTEGER | <1% | — | — | <1% | — | — | 5 | |
| `U_Index_No` | NVARCHAR(10) | <1% | — | <1% | <1% | — | <1% | 11 | |
| `U_Shelflife` | NVARCHAR(10) | <1% | n/a | — | <1% | n/a | — | 2 | |
| `U_UNE_TOTB` | DECIMAL | <1% | <1% | — | <1% | <1% | — | 4 | |
| `U_UNE_TOTL` | DECIMAL | <1% | — | — | <1% | — | — | 7 | |
| `U_FA_Type` | NVARCHAR(20) | 17% | n/a | 18% | 17% | n/a | 18% | 4 | |
| `U_WG_ItemCode` | NVARCHAR(10) | 3% | n/a | n/a | 3% | n/a | n/a | 58 | |
| `U_Packing_Type` | NVARCHAR(12) | 18% | n/a | <1% | 18% | n/a | <1% | 13 | |
| `U_PACK_TYPE` | NVARCHAR(20) | 23% | 7% | 4% | 23% | 7% | 4% | 4 | |
| `U_CONSUMPTION_PER_DAY` | NVARCHAR(50) | 11% | n/a | n/a | 11% | n/a | n/a | 31 | |
| `U_TYPE` | NVARCHAR(10) | 23% | 54% | <1% | 23% | 54% | <1% | 6 | |
| `U_Rev_tax_Rate` | NVARCHAR(3) | 71% | 66% | 49% | 71% | 66% | 49% | 4 | |
| `U_GL_ACCT` | NVARCHAR(15) | 16% | n/a | <1% | 16% | n/a | <1% | 46 | |
| `U_ITEM_LOCK` | NVARCHAR(10) | 100% | n/a | n/a | 100% | n/a | n/a | 3 | |
| `U_Mart_ItemCode` | NVARCHAR(9) | 17% | n/a | n/a | 17% | n/a | n/a | 388 | |
| `U_Is_Plastic` | NVARCHAR(10) | 8% | n/a | n/a | 8% | n/a | n/a | 2 | |
| `U_Is_CSD` | NVARCHAR(10) | <1% | n/a | <1% | <1% | n/a | <1% | 3 | |
| `U_Net_Weight` | DECIMAL | 7% | n/a | 2% | 7% | n/a | 2% | 61 | |
| `U_Qty_In_PCS` | INTEGER | 7% | n/a | 2% | 7% | n/a | 2% | 43 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (18)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_CONSUMPTION_PER_DAY` | OIL | **MART, BEV** |
| `U_FA_TYPE` | MART | **OIL, BEV** |
| `U_FA_Type` | OIL, BEV | **MART** |
| `U_GL_ACCT` | OIL, BEV | **MART** |
| `U_ITEM_LOCK` | OIL | **MART, BEV** |
| `U_Is_CSD` | OIL, BEV | **MART** |
| `U_Is_Plastic` | OIL | **MART, BEV** |
| `U_Mart_ItemCode` | OIL | **MART, BEV** |
| `U_Net_Weight` | OIL, BEV | **MART** |
| `U_OIL_ItemCode` | BEV | **OIL, MART** |
| `U_Oil_ItemCode` | MART | **OIL, BEV** |
| `U_P_WEIGHT` | OIL, BEV | **MART** |
| `U_Packing_Type` | OIL, BEV | **MART** |
| `U_Qty_In_PCS` | OIL, BEV | **MART** |
| `U_RECIPE_NO` | BEV | **OIL, MART** |
| `U_ShelfLife` | MART | **OIL, BEV** |
| `U_Shelflife` | OIL, BEV | **MART** |
| `U_WG_ItemCode` | OIL | **MART, BEV** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`ItmsGrpCod`** (10 values) — `105`×875, `102`×466, `112`×398, `109`×244, `106`×83, `111`×70, `107`×62, `114`×42, `113`×23, `115`×11
- **`CstGrpCode`** (1 values) — `-1`×2,274
- **`VatGourpSa`** (3 values) — `NULL`×2,143, `∅`×130, ``×1
- **`CodeBars`** (2 values) — `NULL`×2,273, ``×1
- **`VATLiable`** (2 values) — `Y`×2,273, ``×1
- **`PrchseItem`** (3 values) — `Y`×2,026, `N`×247, ``×1
- **`SellItem`** (3 values) — `Y`×1,795, `N`×478, ``×1
- **`InvntItem`** (3 values) — `Y`×1,916, `N`×357, ``×1
- **`IncomeAcct`** (2 values) — `NULL`×2,273, ``×1
- **`ExmptIncom`** (2 values) — `NULL`×2,273, ``×1
- **`MaxLevel`** (2 values) — `0.000000`×2,273, `2000.000000`×1
- **`DfltWH`** (2 values) — `NULL`×2,273, ``×1
- **`CardCode`** (2 values) — `NULL`×2,273, ``×1
- **`SuppCatNum`** (2 values) — `NULL`×2,273, ``×1
- **`BuyUnitMsr`** (13 values) — `PCS`×2,014, `SET`×97, `MTS`×41, `KGS`×40, `NULL`×30, `GMS`×18, `MTR`×10, `NOS`×9, `LTR`×6, `∅`×4, `DRM`×3, `MTRS`×1, ``×1
- **`NumInBuy`** (2 values) — `1.000000`×2,235, `1098.900000`×39
- **`LstEvlDate`** (6 values) — `NULL`×892, `2024-10-17 00:00:00.0000000`×718, `2026-08-20 00:00:00.0000000`×412, `2026-04-25 00:00:00.0000000`×234, `2024-11-14 00:00:00.0000000`×16, `2026-08-24 00:00:00.0000000`×2
- **`Canceled`** (2 values) — `N`×2,273, ``×1
- **`WholSlsTax`** (2 values) — `NULL`×2,273, ``×1
- **`RetilrTax`** (2 values) — `NULL`×2,273, ``×1
- **`TrackSales`** (2 values) — `N`×2,273, ``×1
- **`SalUnitMsr`** (12 values) — `PCS`×1,915, `SET`×124, `NULL`×111, `LTR`×44, `KGS`×34, `GMS`×17, `MTR`×10, `NOS`×9, `∅`×4, `DRM`×3, `MTS`×2, ``×1
- **`NumInSale`** (2 values) — `1.000000`×2,273, `2.000000`×1
- **`EvalSystem`** (3 values) — `F`×1,705, `B`×568, ``×1
- **`UserSign`** (7 values) — `1`×1,168, `38`×563, `2`×290, `40`×100, `47`×92, `39`×60, `10`×1
- **`FREE`** (2 values) — `N`×2,273, ``×1
- **`PicturName`** (2 values) — `NULL`×2,273, ``×1
- **`Transfered`** (2 values) — `N`×2,273, ``×1
- **`BlncTrnsfr`** (2 values) — `N`×2,273, ``×1
- **`SerialNum`** (2 values) — `NULL`×2,273, ``×1
- **`TreeType`** (4 values) — `N`×1,648, `P`×383, `S`×242, ``×1
- **`TreeQty`** (21 values) — `1.000000`×2,040, `4.000000`×46, `20.000000`×31, `16.000000`×29, `12.000000`×27, `10.000000`×23, `24.000000`×17, `5.000000`×17, `3.000000`×11, `2.000000`×8, `6.000000`×6, `8.000000`×5, `36.000000`×3, `70.000000`×3, `9.000000`×2, `33.000000`×1, `30.000000`×1, `45.000000`×1, `35.000000`×1, `100.000000`×1, `15.000000`×1
- **`LastPurCur`** (5 values) — `INR`×1,725, `NULL`×517, `∅`×30, ``×1, `USD`×1
- **`ExitCur`** (2 values) — `NULL`×2,273, ``×1
- **`ExitWH`** (2 values) — `NULL`×2,273, ``×1
- **`AssetItem`** (2 values) — `N`×2,273, ``×1
- **`WasCounted`** (2 values) — `N`×2,273, ``×1
- **`ManSerNum`** (2 values) — `N`×2,273, ``×1
- **`SVolUnit`** (1 values) — `4`×2,274
- **`BVolUnit`** (1 values) — `4`×2,274
- **`FixCurrCms`** (2 values) — `NULL`×2,273, ``×1
- **`FirmCode`** (1 values) — `-1`×2,274
- **`QryGroup1`** (2 values) — `N`×2,273, ``×1
- **`QryGroup2`** (2 values) — `N`×2,273, ``×1
- **`QryGroup3`** (2 values) — `N`×2,273, ``×1
- **`QryGroup4`** (2 values) — `N`×2,273, ``×1
- **`QryGroup5`** (2 values) — `N`×2,273, ``×1
- **`QryGroup6`** (2 values) — `N`×2,273, ``×1
- **`QryGroup7`** (2 values) — `N`×2,273, ``×1
- **`QryGroup8`** (2 values) — `N`×2,273, ``×1
- **`QryGroup9`** (2 values) — `N`×2,273, ``×1
- **`QryGroup10`** (2 values) — `N`×2,273, ``×1
- **`QryGroup11`** (2 values) — `N`×2,273, ``×1
- **`QryGroup12`** (2 values) — `N`×2,273, ``×1
- **`QryGroup13`** (2 values) — `N`×2,273, ``×1
- **`QryGroup14`** (2 values) — `N`×2,273, ``×1
- **`QryGroup15`** (2 values) — `N`×2,273, ``×1
- **`QryGroup16`** (2 values) — `N`×2,273, ``×1
- **`QryGroup17`** (2 values) — `N`×2,273, ``×1
- **`QryGroup18`** (2 values) — `N`×2,273, ``×1
- **`QryGroup19`** (2 values) — `N`×2,273, ``×1
- **`QryGroup20`** (2 values) — `N`×2,273, ``×1
- **`QryGroup21`** (2 values) — `N`×2,273, ``×1
- **`QryGroup22`** (2 values) — `N`×2,273, ``×1
- **`QryGroup23`** (2 values) — `N`×2,273, ``×1
- **`QryGroup24`** (2 values) — `N`×2,273, ``×1
- **`QryGroup25`** (2 values) — `N`×2,273, ``×1
- **`QryGroup26`** (2 values) — `N`×2,273, ``×1
- **`QryGroup27`** (2 values) — `N`×2,273, ``×1
- **`QryGroup28`** (2 values) — `N`×2,273, ``×1
- **`QryGroup29`** (2 values) — `N`×2,273, ``×1
- **`QryGroup30`** (2 values) — `N`×2,273, ``×1
- **`QryGroup31`** (2 values) — `N`×2,273, ``×1
- **`QryGroup32`** (2 values) — `N`×2,273, ``×1
- **`QryGroup33`** (2 values) — `N`×2,273, ``×1
- **`QryGroup34`** (2 values) — `N`×2,273, ``×1
- **`QryGroup35`** (2 values) — `N`×2,273, ``×1
- **`QryGroup36`** (2 values) — `N`×2,273, ``×1
- **`QryGroup37`** (2 values) — `N`×2,273, ``×1
- **`QryGroup38`** (2 values) — `N`×2,273, ``×1
- **`QryGroup39`** (2 values) — `N`×2,273, ``×1
- **`QryGroup40`** (2 values) — `N`×2,273, ``×1
- **`QryGroup41`** (2 values) — `N`×2,273, ``×1
- **`QryGroup42`** (2 values) — `N`×2,273, ``×1
- **`QryGroup43`** (2 values) — `N`×2,273, ``×1
- **`QryGroup44`** (2 values) — `N`×2,273, ``×1
- **`QryGroup45`** (2 values) — `N`×2,273, ``×1
- **`QryGroup46`** (2 values) — `N`×2,273, ``×1
- **`QryGroup47`** (2 values) — `N`×2,273, ``×1
- **`QryGroup48`** (2 values) — `N`×2,273, ``×1
- **`QryGroup49`** (2 values) — `N`×2,273, ``×1
- **`QryGroup50`** (2 values) — `N`×2,273, ``×1
- **`QryGroup51`** (2 values) — `N`×2,273, ``×1
- **`QryGroup52`** (2 values) — `N`×2,273, ``×1
- **`QryGroup53`** (2 values) — `N`×2,273, ``×1
- **`QryGroup54`** (2 values) — `N`×2,273, ``×1
- **`QryGroup55`** (2 values) — `N`×2,273, ``×1
- **`QryGroup56`** (2 values) — `N`×2,273, ``×1
- **`QryGroup57`** (2 values) — `N`×2,273, ``×1
- **`QryGroup58`** (2 values) — `N`×2,273, ``×1
- **`QryGroup59`** (2 values) — `N`×2,273, ``×1
- **`QryGroup60`** (2 values) — `N`×2,273, ``×1
- **`QryGroup61`** (2 values) — `N`×2,273, ``×1
- **`QryGroup62`** (2 values) — `N`×2,273, ``×1
- **`QryGroup63`** (2 values) — `N`×2,273, ``×1
- **`QryGroup64`** (2 values) — `N`×2,273, ``×1
- **`ExportCode`** (2 values) — `NULL`×2,273, ``×1
- **`SalFactor1`** (1 values) — `1.000000`×2,274
- **`SalFactor2`** (27 values) — `1.000000`×1,960, `4.000000`×51, `16.000000`×39, `20.000000`×39, `10.000000`×31, `12.000000`×30, `5.000000`×24, `24.000000`×23, `8.000000`×20, `3.000000`×13, `6.000000`×11, `70.000000`×6, `36.000000`×4, `30.000000`×3, `2.000000`×3, `9.000000`×3, `100.000000`×2, `35.000000`×2, `40.000000`×2, `216.000000`×1, `15.000000`×1, `96.000000`×1, `27.000000`×1, `45.000000`×1, `72.000000`×1, `18.000000`×1, `25.000000`×1
- **`SalFactor3`** (6 values) — `1.000000`×2,258, `16.000000`×4, `20.000000`×4, `4.000000`×4, `10.000000`×3, `24.000000`×1
- **`SalFactor4`** (22 values) — `1.000000`×2,247, `275.000000`×3, `700.000000`×2, `1250.000000`×2, `153.000000`×2, `255.000000`×2, `1799.000000`×1, `1650.000000`×1, `55.000000`×1, `999.000000`×1, `1049.000000`×1, `375.000000`×1, `80.000000`×1, `1499.000000`×1, `45.000000`×1, `350.000000`×1, `225.000000`×1, `170.000000`×1, `120.000000`×1, `150.000000`×1, `1350.000000`×1, `159.000000`×1
- **`PurFactor1`** (1 values) — `1.000000`×2,274
- **`PurFactor2`** (8 values) — `1.000000`×2,264, `8.000000`×3, `12.000000`×2, `27.000000`×1, `4.000000`×1, `3.000000`×1, `30.000000`×1, `9.000000`×1
- **`PurFactor3`** (1 values) — `1.000000`×2,274
- **`PurFactor4`** (1 values) — `1.000000`×2,274
- **`SalFormula`** (2 values) — `NULL`×2,273, ``×1
- **`PurFormula`** (2 values) — `NULL`×2,273, ``×1
- **`VatGroupPu`** (3 values) — `NULL`×2,143, `∅`×130, ``×1
- **`PurPackMsr`** (13 values) — `PCS`×2,019, `SET`×95, `NULL`×67, `KGS`×40, `GMS`×18, `MTR`×10, `NOS`×9, `LTR`×6, `∅`×4, `DRM`×3, `MTS`×1, `MTRS`×1, ``×1
- **`PurPackUn`** (3 values) — `1.000000`×2,262, `2.000000`×8, `3.000000`×4
- **`SalPackMsr`** (12 values) — `PCS`×1,918, `NULL`×149, `SET`×120, `KGS`×34, `GMS`×17, `MTR`×10, `NOS`×9, `LTR`×6, `∅`×6, `DRM`×3, `MTS`×1, ``×1
- **`ManBtchNum`** (3 values) — `N`×1,659, `Y`×614, ``×1
- **`ManOutOnly`** (2 values) — `N`×2,273, ``×1
- **`validFor`** (3 values) — `Y`×1,941, `N`×332, ``×1
- **`frozenFor`** (3 values) — `N`×1,925, `Y`×348, ``×1
- **`BlockOut`** (2 values) — `Y`×2,273, ``×1
- **`ValidComm`** (12 values) — `NULL`×2,258, `approved by ginni sir`×4, `APPROVAL BY PRESHIT SIR`×3, `Active after BOM clarification`×1, `APPROVED BY NAVDEEP`×1, `sale q`×1, ``×1, `sales item active for Atul ji`×1, `GS APPROVAL`×1, `SALES Q`×1, `APPROVED BY GINNI SIR`×1, `ACTIVATED BY PRESHIT SINGH`×1
- **`FrozenComm`** (19 values) — `NULL`×2,134, `During bom audit`×74, `During BOM Audit`×24, `NO MRP`×9, `before audit`×9, `During Bom Audit`×5, `DURING BOM AUDIT`×3, `During Bom audit`×3, `During bom Audit`×2, `OLD DELIVERY DONE`×2, `before During bom audit`×1, `During bom Aduit`×1, `NO MRP THATHS WHY INACTIVE`×1, `Before audit`×1, ``×1, `due to duplicate`×1, `NOR MRP THATS WHY INACTIVE`×1, `Approved by preshit sir`×1, `NO MARKS`×1
- **`ObjType`** (2 values) — `4`×2,273, ``×1
- **`SWW`** (2 values) — `NULL`×2,273, ``×1
- **`Deleted`** (2 values) — `N`×2,273, ``×1
- **`ExpensAcct`** (2 values) — `NULL`×2,273, ``×1
- **`FrgnInAcct`** (2 values) — `NULL`×2,273, ``×1
- **`ShipType`** (2 values) — `NULL`×2,223, `-1`×51
- **`GLMethod`** (3 values) — `W`×2,271, `C`×2, ``×1
- **`ECInAcct`** (2 values) — `NULL`×2,273, ``×1
- **`FrgnExpAcc`** (2 values) — `NULL`×2,273, ``×1
- **`ECExpAcc`** (2 values) — `NULL`×2,273, ``×1
- **`TaxType`** (2 values) — `Y`×2,273, ``×1
- **`ByWh`** (2 values) — `Y`×2,273, ``×1
- **`WTLiable`** (3 values) — `N`×2,117, `Y`×156, ``×1
- **`ItemType`** (2 values) — `I`×2,273, ``×1
- **`WarrntTmpl`** (3 values) — `NULL`×1,369, `∅`×904, ``×1
- **`BaseUnit`** (2 values) — `NULL`×2,273, ``×1
- **`CountryOrg`** (2 values) — `NULL`×2,273, ``×1
- **`Phantom`** (2 values) — `N`×2,273, ``×1
- **`IssueMthd`** (3 values) — `M`×1,260, `B`×1,013, ``×1
- **`FREE1`** (2 values) — `NULL`×2,273, ``×1
- **`MngMethod`** (2 values) — `A`×2,273, ``×1
- **`InvntryUom`** (12 values) — `PCS`×1,895, `NULL`×245, `LTR`×45, `KGS`×34, `GMS`×17, `MTR`×11, `NOS`×8, `SET`×7, `∅`×6, `DRM`×3, `MTS`×2, ``×1
- **`PlaningSys`** (3 values) — `N`×2,271, `M`×2, ``×1
- **`PrcrmntMtd`** (3 values) — `B`×2,268, `M`×5, ``×1
- **`IndirctTax`** (2 values) — `N`×2,273, ``×1
- **`TaxCodeAR`** (2 values) — `NULL`×2,273, ``×1
- **`TaxCodeAP`** (2 values) — `NULL`×2,273, ``×1
- **`OSvcCode`** (1 values) — `-1`×2,274
- **`ISvcCode`** (1 values) — `-1`×2,274
- **`ServiceGrp`** (1 values) — `-1`×2,274
- **`NCMCode`** (1 values) — `-1`×2,274
- **`MatType`** (3 values) — `1`×2,261, `3`×12, ``×1
- **`MatGrp`** (1 values) — `-1`×2,274
- **`ProductSrc`** (3 values) — `0`×1,411, `∅`×862, ``×1
- **`ServiceCtg`** (1 values) — `-1`×2,274
- **`ItemClass`** (2 values) — `2`×2,273, ``×1
- **`Excisable`** (2 values) — `N`×2,273, ``×1
- **`NotifyASN`** (3 values) — `NULL`×1,169, `∅`×1,104, ``×1
- **`ProAssNum`** (3 values) — `NULL`×1,169, `∅`×1,104, ``×1
- **`DNFEntry`** (1 values) — `-1`×2,274
- **`Spec`** (2 values) — `NULL`×2,273, ``×1
- **`TaxCtg`** (2 values) — `NULL`×2,273, ``×1
- **`Series`** (11 values) — `391`×894, `389`×446, `390`×398, `394`×245, `395`×71, `392`×64, `393`×62, `821`×41, `820`×23, `2396`×19, `2364`×11
- **`FuelCode`** (2 values) — `-1`×1,411, `NULL`×863
- **`BeverTblC`** (3 values) — `NULL`×1,411, `∅`×862, ``×1
- **`BeverGrpC`** (3 values) — `NULL`×1,411, `∅`×862, ``×1
- **`BeverTM`** (2 values) — `-1`×1,411, `NULL`×863
- **`AtcEntry`** (17 values) — `NULL`×2,258, `85867`×1, `88029`×1, `85888`×1, `105211`×1, `83677`×1, `92504`×1, `159877`×1, `85881`×1, `88023`×1, `87836`×1, `105451`×1, `85176`×1, `93202`×1, `88404`×1, `88028`×1, `162593`×1
- **`UgpEntry`** (2 values) — `-1`×2,233, `1`×41
- **`PUoMEntry`** (2 values) — `NULL`×2,233, `1`×41
- **`SUoMEntry`** (3 values) — `NULL`×2,234, `2`×39, `1`×1
- **`IUoMEntry`** (3 values) — `-1`×2,233, `2`×40, `1`×1
- **`AssetClass`** (2 values) — `∅`×2,273, ``×1
- **`AssetGroup`** (2 values) — `∅`×2,273, ``×1
- **`InventryNo`** (2 values) — `∅`×2,273, ``×1
- **`StatAsset`** (2 values) — `N`×2,273, ``×1
- **`Cession`** (2 values) — `N`×2,273, ``×1
- **`DeacAftUL`** (2 values) — `N`×2,273, ``×1
- **`AsstStatus`** (2 values) — `N`×2,273, ``×1
- **`GLPickMeth`** (4 values) — `W`×1,289, `A`×983, ``×1, `C`×1
- **`NoDiscount`** (3 values) — `N`×2,272, ``×1, `Y`×1
- **`MgrByQty`** (2 values) — `N`×2,273, ``×1
- **`AssetRmk1`** (2 values) — `NULL`×2,273, ``×1
- **`AssetRmk2`** (2 values) — `NULL`×2,273, ``×1
- **`DeprGroup`** (2 values) — `NULL`×2,273, ``×1
- **`AssetSerNo`** (2 values) — `∅`×2,273, ``×1
- **`CntUnitMsr`** (5 values) — `NULL`×2,231, `LTR`×39, `∅`×2, `MTS`×1, ``×1
- **`NumInCnt`** (1 values) — `1.000000`×2,274
- **`INUoMEntry`** (3 values) — `NULL`×2,234, `2`×39, `1`×1
- **`OneBOneRec`** (3 values) — `N`×1,709, `Y`×564, ``×1
- **`RuleCode`** (2 values) — `NULL`×2,273, ``×1
- **`ScsCode`** (2 values) — `NULL`×2,273, ``×1
- **`SpProdType`** (2 values) — `NULL`×2,273, ``×1
- **`CompoWH`** (2 values) — `B`×2,273, ``×1
- **`VirtAstItm`** (2 values) — `N`×2,273, ``×1
- **`SouVirAsst`** (2 values) — `NULL`×2,273, ``×1
- **`InCostRoll`** (2 values) — `Y`×2,273, ``×1
- **`EnAstSeri`** (2 values) — `N`×2,273, ``×1
- **`LinkRsc`** (2 values) — `NULL`×2,273, ``×1
- **`PriceUnit`** (3 values) — `-1`×2,233, `2`×40, `1`×1
- **`GSTRelevnt`** (3 values) — `Y`×2,262, `N`×11, ``×1
- **`SACEntry`** (1 values) — `-1`×2,274
- **`GstTaxCtg`** (5 values) — `R`×2,254, `NULL`×11, `E`×5, `N`×3, ``×1
- **`SOIExc`** (2 values) — `4`×2,273, ``×1
- **`TNVED`** (2 values) — `NULL`×2,273, ``×1
- **`Imported`** (2 values) — `N`×2,273, ``×1
- **`AutoBatch`** (2 values) — `N`×2,273, ``×1
- **`CstmActing`** (2 values) — `N`×2,273, ``×1
- **`TaxCatCode`** (2 values) — `NULL`×2,273, ``×1
- **`DataVers`** (24 values) — `4`×427, `2`×379, `5`×318, `6`×213, `1`×186, `3`×175, `7`×115, `10`×89, `8`×83, `11`×72, `12`×48, `9`×39, `13`×37, `14`×28, `16`×20, `15`×18, `18`×8, `17`×8, `22`×3, `20`×3, `19`×2, `21`×1, `23`×1, `25`×1
- **`NVECode`** (2 values) — `NULL`×2,273, ``×1
- **`CESTCode`** (1 values) — `-1`×2,274
- **`LegalText`** (2 values) — `NULL`×2,273, ``×1
- **`Traceable`** (2 values) — `N`×2,273, ``×1
- **`IfrsPsRev`** (2 values) — `N`×2,273, ``×1
- **`PlPaTaxCat`** (3 values) — `NULL`×1,411, `∅`×862, ``×1
- **`PPTExReSa`** (3 values) — `NULL`×1,411, `∅`×862, ``×1
- **`PPTExRePr`** (3 values) — `NULL`×1,411, `∅`×862, ``×1
- **`ProdctType`** (2 values) — `NULL`×2,273, ``×1
- **`ProdTypeEx`** (2 values) — `NULL`×2,273, ``×1
- **`SalUomNum`** (2 values) — `1.000000`×2,273, `1098.900000`×1
- **`SalUomDen`** (2 values) — `1.000000`×2,273, `1098.900000`×1
- **`BuyUomNum`** (2 values) — `1.000000`×2,233, `1098.900000`×41
- **`BuyUomDen`** (2 values) — `1.000000`×2,273, `1098.900000`×1
- **`IncUomNum`** (2 values) — `1.000000`×2,273, `1098.900000`×1
- **`IncUomDen`** (2 values) — `1.000000`×2,273, `1098.900000`×1
- **`NoApDisc`** (2 values) — `N`×2,273, ``×1
- **`U_Tax_Rate`** (6 values) — `18`×1,323, `5`×731, `12`×157, `0`×44, `28`×18, ``×1
- **`U_Brand`** (10 values) — `JIVO`×2,105, `SANO`×115, `LA RASOI`×16, `ZANO`×11, `RC`×10, `ILHAI`×8, `DIVINE HARVEST`×4, `LE CHEF`×2, `VICTORY`×2, ``×1
- **`U_Unit`** (6 values) — `OIL`×1,721, `FOODS`×328, `CONSUMABLES`×135, `TRADING`×88, `BEVERAGES`×1, ``×1
- **`U_IsLitre`** (3 values) — `N`×1,676, `Y`×597, ``×1
- **`U_UTL_ST_ISSERVICE`** (2 values) — `N`×2,273, ``×1
- **`U_JRID`** (6 values) — `NULL`×2,268, `92`×2, `94`×1, `101`×1, `100`×1, `93`×1
- **`U_Index_No`** (12 values) — `NULL`×2,263, `89099K`×1, `89096I`×1, ``×1, `89097S`×1, `88222D`×1, `89098T`×1, `88220X`×1, `87973H`×1, `87974I`×1, `88221A`×1, `92380D`×1
- **`U_Shelflife`** (3 values) — `NULL`×2,266, `2`×7, ``×1
- **`U_UNE_TOTB`** (5 values) — `NULL`×1,151, `0.000000`×1,119, `1.000000`×2, `0.000100`×1, `12.000000`×1
- **`U_UNE_TOTL`** (8 values) — `NULL`×1,149, `0.000000`×1,118, `1098.900000`×2, `15.000000`×1, `1090.900000`×1, `13.190000`×1, `0.200000`×1, `16.300000`×1
- **`U_FA_Type`** (5 values) — `NULL`×1,653, `MOVABLE`×320, `∅`×226, `FIXED`×74, ``×1
- **`U_Packing_Type`** (14 values) — `NULL`×1,645, `∅`×212, `PET BOTTLE`×176, `TIN`×61, `HDFPE BOTTLE`×49, `POUCH`×34, `PET JAR`×26, `GLASS BOTTLE`×20, `HDPE BOTTLE`×19, `CARTON`×15, `DRUM`×10, `GLASS JAR`×5, ``×1, `STEEL JAR`×1
- **`U_PACK_TYPE`** (5 values) — `NULL`×1,547, `CONSUMER PACK`×463, `∅`×215, `BULK PACK`×48, ``×1
- **`U_CONSUMPTION_PER_DAY`** (30 values) — `NULL`×2,028, `39270`×42, `28050`×35, `5610`×26, `44840`×24, `11781`×24, `4500`×21, `16830`×19, `18513`×14, `0`×4, `1402.5`×4, `1000`×3, `1963.5`×3, `3272.5`×3, `1650`×2, `7012.5`×2, `2454.375`×2, `1636.25`×2, `1157.0625`×2, `1178`×2, ``×1, `2242`×1, `59400`×1, `41.66`×1, `1963.33333333333`×1, `250`×1, `6545`×1, `9350`×1, `100`×1, `1868.33333333333`×1
- **`U_TYPE`** (7 values) — `∅`×973, `∅`×736, `PREMIUM`×261, `OTHERS`×148, `COMMODITY`×120, `NULL`×35, ``×1
- **`U_Rev_tax_Rate`** (5 values) — `18`×910, `5`×673, `NULL`×652, `0`×38, ``×1
- **`U_ITEM_LOCK`** (3 values) — `N`×2,058, `Y`×215, ``×1
- **`U_Is_Plastic`** (3 values) — `NULL`×2,100, `Y`×173, ``×1
- **`U_Is_CSD`** (4 values) — `NULL`×2,259, `Y`×12, `N`×2, ``×1
