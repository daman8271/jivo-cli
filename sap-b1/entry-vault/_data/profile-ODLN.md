# `ODLN` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 2,842 | 93 | `DocDate` | 2024-10-04 → 2026-08-01 |
| MART | 6,126 | 804 | `DocDate` | 2025-01-09 → 2026-08-24 |
| BEV | 303 | 1 | `DocDate` | 2024-10-09 → 2026-05-09 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,842 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,842 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 384 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 383 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 52 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 52 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 58 | |
| `NumAtCard` | NVARCHAR(200) | 10% | 3% | — | 49% | 4% | — | 178 | |
| `VatSum` | DECIMAL | 64% | 71% | 94% | 41% | 84% | — | 1,482 | |
| `DiscPrcnt` | DECIMAL | 2% | — | 2% | — | — | — | 30 | |
| `DiscSum` | DECIMAL | 2% | — | 2% | — | — | — | 28 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocTotal` | DECIMAL | 64% | 73% | 95% | 41% | 84% | — | 1,479 | |
| `PaidToDate` | DECIMAL | 63% | 73% | 93% | 41% | 84% | — | 1,473 | |
| `GrosProfit` | DECIMAL | 64% | 72% | 97% | 41% | 85% | — | 1,599 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 2,842 | |
| `Comments` | NVARCHAR(254) | 87% | 96% | 86% | 99% | 100% | — | 1,895 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 61 | |
| `TransId` | INTEGER | 99% | 100% | 80% | 100% | 100% | — | 2,804 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 636 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 73% | 100% | 79% | 100% | 100% | 100% | 50 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatSumSy` | DECIMAL | 64% | 71% | 94% | 41% | 84% | — | 1,482 | |
| `DiscSumSy` | DECIMAL | 2% | — | 2% | — | — | — | 28 | |
| `DocTotalSy` | DECIMAL | 64% | 73% | 95% | 41% | 84% | — | 1,479 | |
| `PaidSys` | DECIMAL | 63% | 73% | 93% | 41% | 84% | — | 1,473 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrosProfSy` | DECIMAL | 64% | 72% | 97% | 41% | 85% | — | 1,599 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 390 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 393 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 18 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | 63% | 71% | 90% | 41% | 84% | — | 1,472 | |
| `VatPaidSys` | DECIMAL | 63% | 71% | 90% | 41% | 84% | — | 1,472 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `draftKey` | INTEGER | 42% | 25% | 88% | 14% | 2% | — | 1,181 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 61 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 49 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 76 | |
| `RoundDif` | DECIMAL | 32% | 20% | 55% | 22% | 70% | — | 563 | |
| `RoundDifSy` | DECIMAL | 32% | 20% | 55% | 22% | 70% | — | 563 | |
| `submitted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rounding` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RevisionPo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Pick` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlockDunn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayBlock` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `MaxDscn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Reserve` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Max1099` | DECIMAL | 64% | 72% | 95% | 41% | 85% | — | 1,567 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 13 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 73 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UseCorrVat` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlkCredMmo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OpenForLaC` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excised` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DutyStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AutoCrtFlw` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatJENum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InsurOp347` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IgnRelDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PQTGrpHW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ClosingOpt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayDuMonth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExtraDays` | SMALLINT | 7% | 3% | <1% | 1% | — | — | 4 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 9% | 31% | — | 51% | 96% | — | 246 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,735 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,721 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AssetDate` | TIMESTAMP | 3% | <1% | <1% | 15% | <1% | — | 38 | |
| `Notify` | NVARCHAR(1) | 16% | 6% | 12% | — | <1% | — | 1 | |
| `ReqType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OriginType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsReuseNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsReuseNFN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDlvry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EnvTypeNFe` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsAlt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AltBaseTyp` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PrintSEPA` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RelatedTyp` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PoDropPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExclTaxRep` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Revision` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GSTTranTyp` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ComTrade` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UseBilAddr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `IssReason` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ComTradeRt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SplitPmnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SelfPosted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EWBGenType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 37 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AplTaxOnFr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Dipatch_Date` | TIMESTAMP | <1% | — | — | — | — | — | 2 | |
| `U_Basement` | NVARCHAR(10) | <1% | — | — | — | — | — | 1 | |
| `U_First_Floor` | NVARCHAR(10) | <1% | — | — | — | — | — | 1 | |
| `U_delbranch` | NVARCHAR(100) | 27% | 2% | 21% | — | — | — | 3 | |
| `U_delbranchnam` | NVARCHAR(100) | 27% | 2% | 21% | — | — | — | 3 | |
| `U_GRNdocentry` | INTEGER | 26% | 2% | 19% | — | — | — | 746 | |
| `U_GRNCardCode` | NVARCHAR(15) | 27% | 2% | 21% | — | — | — | 4 | |
| `U_GRNWhsCode` | NVARCHAR(8) | 27% | 2% | 21% | — | — | — | 13 | |
| `U_Ship_From` | NVARCHAR(8) | <1% | <1% | — | — | — | — | 6 | |
| `U_BilltyNumber` | NVARCHAR(15) | 8% | — | n/a | 47% | — | n/a | 141 | |
| `U_BiltyDate` | TIMESTAMP | 8% | — | — | 47% | — | — | 76 | |
| `U_TransporterName` | NVARCHAR(50) | 8% | — | — | 47% | — | — | 13 | |
| `U_VehicleNoM` | NVARCHAR(12) | 8% | — | n/a | 48% | — | n/a | 52 | |
| `U_DriverName` | NCLOB | <1% | — | — | — | — | — | 0 | |
| `U_Mob_No` | NVARCHAR(12) | <1% | — | — | — | — | — | 2 | |
| `U_AR_NO` | NVARCHAR(12) | 6% | — | n/a | 47% | — | n/a | 24 | |
| `U_LRNUmber` | NVARCHAR(15) | 6% | — | n/a | 47% | — | n/a | 23 | |
| `U_BOEDate` | TIMESTAMP | 6% | — | n/a | 47% | — | n/a | 20 | |
| `U_UNE_MLOC` | NVARCHAR(100) | <1% | — | — | — | — | — | 1 | |
| `U_UNE_ACTH` | NVARCHAR(100) | — | — | 93% | — | — | 100% | 0 | |
| `U_OMS_Order_No` | INTEGER | 12% | — | 12% | — | — | — | 96 | |
| `U_SALES_PERSON` | NVARCHAR(20) | 6% | n/a | n/a | — | n/a | n/a | 5 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (24)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_AR_NO` | OIL, MART | **BEV** |
| `U_BOEDate` | OIL, MART | **BEV** |
| `U_BPCODE` | MART | **OIL, BEV** |
| `U_BilltyNumber` | OIL, MART | **BEV** |
| `U_BiltyNumber` | BEV | **OIL, MART** |
| `U_CreditCreated` | OIL | **MART, BEV** |
| `U_GRPO` | OIL | **MART, BEV** |
| `U_JRId` | OIL, MART | **BEV** |
| `U_JWPL_BASE` | MART | **OIL, BEV** |
| `U_LRNUmber` | OIL, MART | **BEV** |
| `U_MART_DOC_NO` | MART | **OIL, BEV** |
| `U_MartCN` | OIL | **MART, BEV** |
| `U_MartCustomer` | OIL | **MART, BEV** |
| `U_OMS_REF` | OIL | **MART, BEV** |
| `U_POMade` | MART | **OIL, BEV** |
| `U_PONo` | OIL | **MART, BEV** |
| `U_PO_Ship_To` | MART | **OIL, BEV** |
| `U_PRODUCTION_DATE` | OIL, BEV | **MART** |
| `U_Production_Order` | OIL, BEV | **MART** |
| `U_SALES_PERSON` | OIL | **MART, BEV** |
| `U_TDS_LINK` | OIL, MART | **BEV** |
| `U_Total_Gross_Wt` | OIL, BEV | **MART** |
| `U_VechileNom` | BEV | **OIL, MART** |
| `U_VehicleNoM` | OIL, MART | **BEV** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`DocType`** (1 values) — `I`×2,842
- **`CANCELED`** (3 values) — `N`×2,792, `C`×25, `Y`×25
- **`Handwrtten`** (1 values) — `N`×2,842
- **`Printed`** (2 values) — `N`×2,830, `Y`×12
- **`DocStatus`** (2 values) — `C`×2,829, `O`×13
- **`InvntSttus`** (2 values) — `C`×2,487, `O`×355
- **`Transfered`** (1 values) — `N`×2,842
- **`ObjType`** (1 values) — `15`×2,842
- **`DiscPrcnt`** (30 values) — `0.000000`×2,789, `-0.000019`×8, `-0.000025`×3, `-0.000020`×3, `-0.000002`×3, `-0.000001`×3, `-0.000003`×3, `-0.000015`×2, `-0.000036`×2, `-0.000021`×2, `-0.000006`×2, `NULL`×2, `-0.000014`×2, `-0.000016`×1, `-0.000005`×1, `-0.000022`×1, `-0.000008`×1, `0.000095`×1, `-0.000059`×1, `-0.000034`×1, `-0.000024`×1, `-0.000100`×1, `-0.000018`×1, `-0.000027`×1, `-0.000013`×1, `-0.000076`×1, `-0.000046`×1, `-0.000028`×1, `-0.000010`×1, `0.000187`×1
- **`DiscSum`** (28 values) — `0.000000`×2,789, `-0.000100`×10, `-0.000300`×7, `-0.000200`×4, `-0.000700`×3, `-0.002100`×2, `-0.001200`×2, `-0.000400`×2, `-0.001400`×2, `-0.000600`×2, `-0.001900`×2, `0.001900`×1, `-0.003100`×1, `-0.006100`×1, `-0.002200`×1, `-0.000800`×1, `-0.000500`×1, `-0.003500`×1, `0.006800`×1, `-0.008300`×1, `0.006200`×1, `-0.006800`×1, `-0.001100`×1, `-0.003800`×1, `-0.006200`×1, `-0.007700`×1, `-0.001700`×1, `0.004300`×1
- **`DocCur`** (1 values) — `INR`×2,842
- **`DocRate`** (1 values) — `1.000000`×2,842
- **`GroupNum`** (6 values) — `-1`×2,587, `18`×195, `6`×46, `10`×11, `20`×2, `1`×1
- **`SlpCode`** (12 values) — `-1`×2,213, `4`×215, `23`×195, `18`×101, `24`×96, `80`×9, `30`×6, `84`×3, `11`×1, `46`×1, `17`×1, `81`×1
- **`TrnspCode`** (1 values) — `-1`×2,842
- **`PartSupply`** (1 values) — `Y`×2,842
- **`Confirmed`** (1 values) — `Y`×2,842
- **`GrossBase`** (2 values) — `-6`×2,468, `-1`×374
- **`CreateTran`** (1 values) — `N`×2,842
- **`SummryType`** (1 values) — `N`×2,842
- **`UpdInvnt`** (1 values) — `G`×2,842
- **`UpdCardBal`** (1 values) — `D`×2,842
- **`InvntDirec`** (1 values) — `X`×2,842
- **`ShowSCN`** (1 values) — `N`×2,842
- **`SysRate`** (1 values) — `1.000000`×2,842
- **`CurSource`** (1 values) — `L`×2,842
- **`DiscSumSy`** (28 values) — `0.000000`×2,789, `-0.000100`×10, `-0.000300`×7, `-0.000200`×4, `-0.000700`×3, `-0.001400`×2, `-0.001900`×2, `-0.000600`×2, `-0.000400`×2, `-0.002100`×2, `-0.001200`×2, `-0.007700`×1, `0.004300`×1, `0.001900`×1, `-0.003100`×1, `-0.001700`×1, `-0.006200`×1, `-0.001100`×1, `-0.006800`×1, `0.006200`×1, `-0.008300`×1, `0.006800`×1, `-0.003800`×1, `-0.006100`×1, `-0.002200`×1, `-0.000800`×1, `-0.000500`×1, `-0.003500`×1
- **`FatherType`** (1 values) — `P`×2,842
- **`IsICT`** (1 values) — `N`×2,842
- **`VolUnit`** (1 values) — `4`×2,842
- **`WeightUnit`** (2 values) — `3`×2,840, `2`×2
- **`Series`** (23 values) — `323`×601, `322`×478, `321`×378, `324`×267, `1298`×117, `1305`×102, `1304`×101, `1299`×95, `1303`×94, `1301`×80, `1300`×73, `2485`×72, `326`×72, `1302`×70, `325`×69, `2486`×48, `1306`×36, `1307`×27, `2487`×18, `1309`×14, `2489`×12, `2488`×10, `1308`×8
- **`isCrin`** (1 values) — `N`×2,842
- **`FinncPriod`** (23 values) — `9`×601, `8`×478, `7`×378, `10`×267, `14`×117, `21`×102, `20`×101, `15`×95, `19`×94, `17`×80, `16`×73, `41`×72, `12`×72, `18`×70, `11`×69, `42`×48, `22`×36, `23`×27, `43`×18, `25`×14, `45`×12, `44`×10, `24`×8
- **`UserSign`** (18 values) — `37`×765, `22`×732, `26`×590, `15`×265, `31`×217, `25`×120, `44`×63, `24`×36, `40`×15, `33`×10, `1`×8, `35`×7, `19`×5, `38`×4, `21`×2, `47`×1, `39`×1, `20`×1
- **`selfInv`** (1 values) — `N`×2,842
- **`WddStatus`** (3 values) — `-`×1,688, `P`×1,153, `A`×1
- **`Exported`** (1 values) — `N`×2,842
- **`NetProc`** (1 values) — `N`×2,842
- **`submitted`** (1 values) — `N`×2,842
- **`PoPrss`** (1 values) — `N`×2,842
- **`Rounding`** (2 values) — `N`×1,923, `Y`×919
- **`RevisionPo`** (1 values) — `N`×2,842
- **`PickStatus`** (1 values) — `N`×2,842
- **`Pick`** (1 values) — `N`×2,842
- **`BlockDunn`** (1 values) — `N`×2,842
- **`PayBlock`** (1 values) — `N`×2,842
- **`MaxDscn`** (1 values) — `N`×2,842
- **`Reserve`** (1 values) — `N`×2,842
- **`DeferrTax`** (1 values) — `N`×2,842
- **`BoeReserev`** (1 values) — `N`×2,842
- **`Installmnt`** (1 values) — `1`×2,842
- **`VATFirst`** (1 values) — `N`×2,842
- **`CEECFlag`** (1 values) — `N`×2,842
- **`CtlAccount`** (13 values) — `1101008`×759, `1101005`×655, `1102003`×460, `1101012`×287, `1101010`×266, `1102005`×194, `1102001`×118, `1101001`×86, `1101015`×8, `1101004`×4, `1101006`×3, `1101009`×1, `1101016`×1
- **`BPLId`** (3 values) — `2`×1,430, `1`×1,260, `3`×152
- **`BPLName`** (4 values) — `FACTORY`×1,430, `DELHI`×1,251, `PUNJAB`×152, `Delhi`×9
- **`VATRegNum`** (3 values) — `06AACCJ4223F1Z0`×1,430, `07AACCJ4223F1ZY`×1,260, `03AACCJ4223F1Z6`×152
- **`SumAbsId`** (1 values) — `-1`×2,842
- **`PIndicator`** (23 values) — `Dec-24-25`×601, `Nov-24-25`×478, `Oct-24-25`×378, `Jan-24-25`×267, `APR-25-26`×117, `NOV-25-26`×102, `OCT-25-26`×101, `MAY-25-26`×95, `SEP-25-26`×94, `JUL-25-26`×80, `JUN-25-26`×73, `Mar-24-25`×72, `APR-26-27`×72, `AUG-25-26`×70, `Feb-24-25`×69, `MAY-26-27`×48, `DEC-25-26`×36, `JAN-25-26`×27, `JUN-26-27`×18, `MAR-25-26`×14, `AUG-26-27`×12, `JUL-26-27`×10, `FEB-25-26`×8
- **`UseShpdGd`** (1 values) — `N`×2,842
- **`DocSubType`** (1 values) — `--`×2,842
- **`DpmStatus`** (1 values) — `O`×2,842
- **`DpmDrawn`** (1 values) — `N`×2,842
- **`Posted`** (1 values) — `Y`×2,842
- **`IsPaytoBnk`** (1 values) — `N`×2,842
- **`isIns`** (1 values) — `N`×2,842
- **`VersionNum`** (2 values) — `10.00.250.15`×2,622, `10.00.310.21`×220
- **`LangCode`** (1 values) — `8`×2,842
- **`BPNameOW`** (2 values) — `N`×2,552, `Y`×290
- **`BillToOW`** (1 values) — `N`×2,842
- **`ShipToOW`** (1 values) — `N`×2,842
- **`RetInvoice`** (1 values) — `N`×2,842
- **`Model`** (1 values) — `0`×2,842
- **`UseCorrVat`** (1 values) — `N`×2,842
- **`BlkCredMmo`** (1 values) — `N`×2,842
- **`OpenForLaC`** (1 values) — `Y`×2,842
- **`Excised`** (1 values) — `O`×2,842
- **`DutyStatus`** (1 values) — `Y`×2,842
- **`AutoCrtFlw`** (1 values) — `N`×2,842
- **`VatJENum`** (1 values) — `-1`×2,842
- **`InsurOp347`** (1 values) — `N`×2,842
- **`IgnRelDoc`** (1 values) — `N`×2,842
- **`ResidenNum`** (1 values) — `1`×2,842
- **`PQTGrpHW`** (1 values) — `N`×2,842
- **`DocManClsd`** (2 values) — `N`×2,507, `Y`×335
- **`ClosingOpt`** (1 values) — `1`×2,842
- **`Ordered`** (1 values) — `N`×2,842
- **`NTSApprov`** (1 values) — `N`×2,842
- **`PayDuMonth`** (1 values) — `N`×2,842
- **`ExtraDays`** (4 values) — `0`×2,644, `10`×195, `21`×2, `30`×1
- **`EDocGenTyp`** (1 values) — `N`×2,842
- **`OnlineQuo`** (1 values) — `N`×2,842
- **`EDocStatus`** (1 values) — `C`×2,842
- **`EDocProces`** (1 values) — `C`×2,842
- **`EDocCancel`** (1 values) — `N`×2,842
- **`EDocTest`** (1 values) — `N`×2,842
- **`DpmAsDscnt`** (1 values) — `N`×2,842
- **`GTSRlvnt`** (1 values) — `N`×2,842
- **`SrvTaxRule`** (1 values) — `N`×2,842
- **`Notify`** (2 values) — `NULL`×2,396, `N`×446
- **`ReqType`** (1 values) — `12`×2,842
- **`OriginType`** (1 values) — `M`×2,842
- **`IsReuseNum`** (1 values) — `N`×2,842
- **`IsReuseNFN`** (1 values) — `N`×2,842
- **`DocDlvry`** (1 values) — `0`×2,842
- **`EnvTypeNFe`** (1 values) — `-1`×2,842
- **`IsAlt`** (1 values) — `N`×2,842
- **`AltBaseTyp`** (1 values) — `-1`×2,842
- **`PrintSEPA`** (1 values) — `N`×2,842
- **`RelatedTyp`** (1 values) — `-1`×2,842
- **`PoDropPrss`** (1 values) — `N`×2,842
- **`ExclTaxRep`** (1 values) — `N`×2,842
- **`Revision`** (1 values) — `N`×2,842
- **`GSTTranTyp`** (1 values) — `GA`×2,842
- **`BaseType`** (1 values) — `-1`×2,842
- **`ComTrade`** (1 values) — `E`×2,842
- **`UseBilAddr`** (2 values) — `Y`×2,735, `N`×107
- **`IssReason`** (1 values) — `1`×2,842
- **`ComTradeRt`** (1 values) — `N`×2,842
- **`SplitPmnt`** (1 values) — `N`×2,842
- **`SelfPosted`** (1 values) — `N`×2,842
- **`DPPStatus`** (1 values) — `N`×2,842
- **`EWBGenType`** (2 values) — `L`×2,113, `N`×729
- **`EDocType`** (1 values) — `F`×2,842
- **`AggregDoc`** (1 values) — `N`×2,842
- **`IndFinal`** (1 values) — `N`×2,842
- **`PostPmntWT`** (1 values) — `N`×2,842
- **`FCEPmnMean`** (1 values) — `N`×2,842
- **`NotRel4MI`** (1 values) — `N`×2,842
- **`Rel4PPTax`** (1 values) — `N`×2,842
- **`BookeTdsBP`** (1 values) — `N`×2,842
- **`DigPayment`** (1 values) — `N`×2,842
- **`PDueMonEnd`** (1 values) — `N`×2,842
- **`RShipToOW`** (2 values) — `N`×2,840, `Y`×2
- **`AplTaxOnFr`** (1 values) — `N`×2,842
- **`CpyDtyStts`** (1 values) — `N`×2,842
- **`U_Dipatch_Date`** (3 values) — `NULL`×2,840, `2024-10-22 00:00:00.0000000`×1, `2024-10-23 00:00:00.0000000`×1
- **`U_Basement`** (2 values) — `NULL`×2,836, `Y`×6
- **`U_First_Floor`** (2 values) — `NULL`×2,838, `Y`×4
- **`U_delbranch`** (4 values) — `NULL`×2,070, `3`×460, `2`×194, `1`×118
- **`U_delbranchnam`** (4 values) — `NULL`×2,070, `PUNJAB`×460, `FACTORY`×194, `DELHI`×118
- **`U_GRNCardCode`** (5 values) — `NULL`×2,070, `VENDA000003`×574, `VENDA000002`×149, `VENDA000004`×45, `VENDA001004`×4
- **`U_GRNWhsCode`** (14 values) — `NULL`×2,070, `PB-ST`×292, `BH-GR`×142, `PB-SP`×110, `DL-FG`×95, `PB-JP`×56, `BH-FG`×41, `DL-PS`×18, `BH-LR`×6, `DL-J3`×5, `BH-FU`×4, `BH-PS`×1, `PB-RG`×1, `PB-SG`×1
- **`U_Ship_From`** (7 values) — `NULL`×2,826, `BH-FG`×6, `GP-FG`×4, `DL-GR`×3, `BH-FU`×1, `PB-SP`×1, `PB-ST`×1
- **`U_TransporterName`** (14 values) — `NULL`×2,615, `R K TANKER`×58, `R K TANKER SERVICE`×51, `RK TANKER SERVICE`×50, `RK TANKER`×26, `Shri Pawansut Forwarding Service`×16, `BALMUKUND ROADWAYS`×8, `BALMUKUND`×4, `R.K. TANKER SERVICE`×4, `R K TANKER SEVICE`×4, `R K TANKER SERVICES`×3, `R K TAKER`×1, `r k tanker service`×1, `SS LOGISTICS`×1
- **`U_Mob_No`** (3 values) — `NULL`×2,840, `6299630248`×1, `9120908161`×1
- **`U_AR_NO`** (25 values) — `NULL`×2,685, `602526-B`×21, `602507-B`×18, `602526-A`×17, `227361`×15, `42760`×14, `227816`×11, `602507-A`×9, `41914`×9, `227815`×9, `41802`×6, `602507`×4, `42961`×4, `602411`×3, `40677`×3, `42326`×2, `43710`×2, `227817`×2, `227262`×2, `42173`×1, `625025002`×1, `41914,602412`×1, `227729`×1, `625025001`×1, `1198`×1
- **`U_LRNUmber`** (24 values) — `NULL`×2,664, `9829741`×21, `8412487`×19, `7920773`×18, `2381788`×16, `5168506`×15, `4137680`×14, `7317068`×13, `8017181`×9, `9094228`×9, `8017255`×8, `8890469`×6, `6659797`×6, `2288606`×5, `5276495`×4, `8035911`×3, `5622622`×3, `7657527`×2, `485571`×2, `8072204`×1, `6223663`×1, `8530178`×1, `8568599`×1, `8222231`×1
- **`U_BOEDate`** (21 values) — `NULL`×2,672, `2026-06-11 00:00:00.0000000`×21, `2026-04-01 00:00:00.0000000`×19, `2025-08-27 00:00:00.0000000`×18, `2026-03-06 00:00:00.0000000`×18, `2026-03-11 00:00:00.0000000`×17, `2025-05-30 00:00:00.0000000`×15, `2025-10-17 00:00:00.0000000`×15, `2026-02-04 00:00:00.0000000`×13, `2026-01-01 00:00:00.0000000`×6, `2025-03-14 00:00:00.0000000`×6, `2025-05-26 00:00:00.0000000`×5, `2025-03-25 00:00:00.0000000`×4, `2026-03-12 00:00:00.0000000`×3, `2025-02-26 00:00:00.0000000`×2, `2025-10-01 00:00:00.0000000`×2, `2026-02-20 00:00:00.0000000`×2, `2025-01-29 00:00:00.0000000`×1, `2025-05-03 00:00:00.0000000`×1, `2025-12-11 00:00:00.0000000`×1, `2025-02-16 00:00:00.0000000`×1
- **`U_UNE_MLOC`** (2 values) — `NULL`×2,841, `u`×1
- **`U_SALES_PERSON`** (6 values) — `NULL`×2,681, `PUNJAB MT`×133, `PRIVATE`×11, `PUNJAB GT`×7, `ECOM`×5, `BRANCH`×5
