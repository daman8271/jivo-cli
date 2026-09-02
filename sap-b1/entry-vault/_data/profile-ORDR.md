# `ORDR` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 15,133 | 1,919 | `DocDate` | 2024-10-01 → 2026-08-24 |
| MART | 7,675 | 1,174 | `DocDate` | 2024-10-03 → 2026-08-24 |
| BEV | 5,578 | 1,481 | `DocDate` | 2024-10-01 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 15,133 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 15,133 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 586 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 586 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 453 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 453 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 607 | |
| `NumAtCard` | NVARCHAR(200) | 40% | 98% | 7% | 31% | 97% | 7% | 5,912 | |
| `VatSum` | DECIMAL | 99% | 100% | 99% | 100% | 99% | 100% | 11,303 | |
| `VatSumFC` | DECIMAL | <1% | — | <1% | — | — | — | 2 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `DocTotal` | DECIMAL | 100% | 100% | 99% | 100% | 99% | 100% | 11,147 | |
| `DocTotalFC` | DECIMAL | <1% | — | <1% | — | — | — | 8 | |
| `PaidToDate` | DECIMAL | 99% | 97% | 98% | 97% | 88% | 94% | 11,106 | |
| `PaidFC` | DECIMAL | <1% | — | <1% | — | — | — | 8 | |
| `GrosProfit` | DECIMAL | 99% | 100% | 100% | 100% | 99% | 100% | 11,529 | |
| `GrosProfFC` | DECIMAL | <1% | — | <1% | — | — | — | 9 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 15,133 | |
| `Comments` | NVARCHAR(254) | 4% | <1% | 2% | <1% | <1% | 5% | 406 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 453 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 764 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 65 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 94% | 89% | 99% | 98% | 100% | 100% | 447 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `VatSumSy` | DECIMAL | 99% | 100% | 99% | 100% | 99% | 100% | 11,303 | |
| `DocTotalSy` | DECIMAL | 100% | 100% | 99% | 100% | 99% | 100% | 11,147 | |
| `PaidSys` | DECIMAL | 99% | 97% | 98% | 97% | 88% | 94% | 11,106 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrosProfSy` | DECIMAL | 99% | 100% | 100% | 100% | 99% | 100% | 11,529 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 584 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 589 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | 69% | 83% | 74% | 79% | 72% | 86% | 8,936 | |
| `VatPaidSys` | DECIMAL | 69% | 83% | 74% | 79% | 72% | 86% | 8,936 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `draftKey` | INTEGER | <1% | <1% | <1% | — | <1% | — | 11 | |
| `TotalExpns` | DECIMAL | <1% | — | — | <1% | — | — | 3 | |
| `TotalExpSC` | DECIMAL | <1% | — | — | <1% | — | — | 3 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 691 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 47 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 717 | |
| `RoundDif` | DECIMAL | 50% | 90% | 68% | 72% | 82% | 88% | 3,156 | |
| `RoundDifFC` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `RoundDifSy` | DECIMAL | 50% | 90% | 68% | 72% | 82% | 88% | 3,156 | |
| `submitted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rounding` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RevisionPo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReqDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 586 | |
| `CancelDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 586 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Pick` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlockDunn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayBlock` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `MaxDscn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Reserve` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Max1099` | DECIMAL | 99% | 100% | 99% | 100% | 99% | 100% | 11,423 | |
| `ExpAppl` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `ExpApplSC` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 19 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OwnerCode` | INTEGER | 4% | — | <1% | 19% | — | <1% | 3 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 625 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxOnExp` | DECIMAL | <1% | — | — | <1% | — | — | 3 | |
| `TaxOnExpSc` | DECIMAL | <1% | — | — | <1% | — | — | 3 | |
| `TaxOnExAp` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `TaxOnExApS` | DECIMAL | <1% | — | — | — | — | — | 2 | |
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
| `ExtraDays` | SMALLINT | 28% | 54% | 4% | 14% | <1% | 7% | 8 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 2% | <1% | <1% | <1% | — | <1% | 302 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12,095 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 10,695 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AssetDate` | TIMESTAMP | 29% | 2% | 22% | 14% | <1% | 15% | 533 | |
| `Notify` | NVARCHAR(1) | 55% | 74% | 36% | 16% | 67% | 43% | 1 | |
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
| `EWBGenType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 54 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ConfrmedBy` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `ConfrmedOn` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 584 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AplTaxOnFr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Basement` | NVARCHAR(10) | <1% | — | — | — | — | — | 2 | |
| `U_First_Floor` | NVARCHAR(10) | <1% | — | — | — | — | — | 1 | |
| `U_GRNdocentry` | INTEGER | <1% | — | — | — | — | — | 1 | |
| `U_Ship_From` | NVARCHAR(8) | 6% | <1% | — | — | — | — | 14 | |
| `U_BilltyNumber` | NVARCHAR(15) | <1% | — | n/a | <1% | — | n/a | 89 | |
| `U_BiltyDate` | TIMESTAMP | <1% | — | <1% | <1% | — | — | 57 | |
| `U_TransporterName` | NVARCHAR(50) | <1% | — | <1% | <1% | — | — | 14 | |
| `U_VehicleNoM` | NVARCHAR(12) | <1% | — | n/a | <1% | — | n/a | 27 | |
| `U_Mob_No` | NVARCHAR(12) | <1% | — | — | — | — | — | 1 | |
| `U_Order_Date` | TIMESTAMP | 5% | — | 1% | 10% | — | 3% | 25 | |
| `U_AR_NO` | NVARCHAR(12) | <1% | — | n/a | — | — | n/a | 12 | |
| `U_InvRevEntry` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_LRNUmber` | NVARCHAR(15) | <1% | — | n/a | — | — | n/a | 11 | |
| `U_BOEDate` | TIMESTAMP | <1% | — | n/a | — | — | n/a | 10 | |
| `U_UNE_MLOC` | NVARCHAR(100) | <1% | <1% | <1% | <1% | — | — | 4 | |
| `U_UNE_ACTH` | NVARCHAR(100) | — | — | 98% | — | — | 100% | 0 | |
| `U_ARNO` | NVARCHAR(100) | <1% | — | — | — | — | — | 1 | |
| `U_OMS_Order_No` | INTEGER | 41% | — | 33% | <1% | — | 3% | 756 | |
| `U_SALES_PERSON` | NVARCHAR(20) | 42% | n/a | n/a | 91% | n/a | n/a | 21 | |
| `U_GRPO` | NVARCHAR(10) | <1% | n/a | n/a | <1% | n/a | n/a | 2 | |
| `U_PONo` | NVARCHAR(30) | 4% | n/a | n/a | 17% | n/a | n/a | 579 | |
| `U_MartCustomer` | NVARCHAR(200) | <1% | n/a | n/a | <1% | n/a | n/a | 14 | |

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

- **`DocType`** (2 values) — `I`×15,127, `S`×6
- **`CANCELED`** (2 values) — `N`×15,062, `Y`×71
- **`Handwrtten`** (2 values) — `N`×15,132, `Y`×1
- **`Printed`** (2 values) — `N`×15,046, `Y`×87
- **`DocStatus`** (2 values) — `C`×15,053, `O`×80
- **`InvntSttus`** (2 values) — `C`×7,622, `O`×7,511
- **`Transfered`** (1 values) — `N`×15,133
- **`ObjType`** (1 values) — `17`×15,133
- **`VatSumFC`** (2 values) — `0.000000`×15,132, `6591.982500`×1
- **`DocCur`** (2 values) — `INR`×15,124, `USD`×9
- **`DocRate`** (7 values) — `1.000000`×15,124, `86.100000`×2, `85.400000`×2, `86.050000`×2, `86.700000`×1, `84.700000`×1, `85.950000`×1
- **`DocTotalFC`** (8 values) — `0.000000`×15,124, `342439.500000`×2, `211382.250000`×2, `138431.632500`×1, `132240.600000`×1, `131839.650000`×1, `420146.000000`×1, `134737.500000`×1
- **`PaidFC`** (8 values) — `0.000000`×15,124, `211382.250000`×2, `342439.500000`×2, `131839.650000`×1, `132240.600000`×1, `138431.632500`×1, `420146.000000`×1, `134737.500000`×1
- **`GrosProfFC`** (9 values) — `0.000000`×15,124, `211382.250000`×2, `131839.650000`×1, `-0.003900`×1, `30978.451200`×1, `420146.430000`×1, `210198.900000`×1, `400.950000`×1, `134737.500000`×1
- **`GroupNum`** (12 values) — `-1`×10,805, `1`×2,602, `20`×905, `11`×742, `10`×18, `19`×17, `14`×11, `17`×10, `9`×10, `29`×9, `6`×3, `18`×1
- **`TrnspCode`** (1 values) — `-1`×15,133
- **`PartSupply`** (1 values) — `Y`×15,133
- **`Confirmed`** (1 values) — `Y`×15,133
- **`GrossBase`** (2 values) — `-6`×14,103, `-1`×1,030
- **`CreateTran`** (1 values) — `N`×15,133
- **`SummryType`** (1 values) — `N`×15,133
- **`UpdInvnt`** (1 values) — `C`×15,133
- **`UpdCardBal`** (1 values) — `O`×15,133
- **`InvntDirec`** (1 values) — `X`×15,133
- **`ShowSCN`** (1 values) — `N`×15,133
- **`SysRate`** (1 values) — `1.000000`×15,133
- **`CurSource`** (3 values) — `L`×15,123, `C`×9, `S`×1
- **`FatherType`** (1 values) — `P`×15,133
- **`IsICT`** (1 values) — `N`×15,133
- **`VolUnit`** (1 values) — `4`×15,133
- **`WeightUnit`** (2 values) — `3`×15,026, `2`×107
- **`Series`** (24 values) — `305`×946, `1337`×930, `1335`×817, `306`×789, `1336`×778, `1340`×764, `308`×752, `1343`×718, `310`×709, `307`×699, `1338`×686, `1334`×669, `309`×665, `1339`×654, `1342`×631, `1344`×584, `1341`×575, `2450`×541, `2448`×533, `2447`×487, `1345`×477, `2449`×454, `2451`×274, `-1`×1
- **`isCrin`** (1 values) — `N`×15,133
- **`FinncPriod`** (23 values) — `7`×946, `17`×930, `15`×817, `8`×789, `16`×778, `20`×764, `10`×752, `23`×718, `12`×709, `9`×699, `18`×686, `14`×669, `11`×666, `19`×654, `22`×631, `24`×584, `21`×575, `44`×541, `42`×533, `41`×487, `25`×477, `43`×454, `45`×274
- **`UserSign`** (12 values) — `19`×6,814, `24`×4,387, `22`×2,282, `21`×648, `20`×481, `1`×322, `15`×168, `40`×19, `10`×8, `23`×2, `37`×1, `2`×1
- **`selfInv`** (1 values) — `N`×15,133
- **`WddStatus`** (2 values) — `-`×15,131, `P`×2
- **`draftKey`** (12 values) — `NULL`×15,122, `36353`×1, `42552`×1, `36555`×1, `36558`×1, `1`×1, `39162`×1, `36008`×1, `27298`×1, `40059`×1, `7330`×1, `16130`×1
- **`TotalExpns`** (3 values) — `0.000000`×15,122, `7500.000000`×9, `7142.850000`×2
- **`TotalExpSC`** (3 values) — `0.000000`×15,122, `7500.000000`×9, `7142.850000`×2
- **`Exported`** (1 values) — `N`×15,133
- **`NetProc`** (1 values) — `N`×15,133
- **`RoundDifFC`** (2 values) — `0.000000`×15,132, `-0.430000`×1
- **`submitted`** (1 values) — `N`×15,133
- **`PoPrss`** (1 values) — `N`×15,133
- **`Rounding`** (2 values) — `N`×8,284, `Y`×6,849
- **`RevisionPo`** (1 values) — `N`×15,133
- **`PickStatus`** (1 values) — `N`×15,133
- **`Pick`** (1 values) — `N`×15,133
- **`BlockDunn`** (1 values) — `N`×15,133
- **`PayBlock`** (1 values) — `N`×15,133
- **`MaxDscn`** (1 values) — `N`×15,133
- **`Reserve`** (1 values) — `N`×15,133
- **`ExpAppl`** (2 values) — `0.000000`×15,130, `7500.000000`×3
- **`ExpApplSC`** (2 values) — `0.000000`×15,130, `7500.000000`×3
- **`DeferrTax`** (1 values) — `N`×15,133
- **`BoeReserev`** (1 values) — `N`×15,133
- **`Installmnt`** (1 values) — `1`×15,133
- **`VATFirst`** (1 values) — `N`×15,133
- **`CEECFlag`** (1 values) — `N`×15,133
- **`CtlAccount`** (19 values) — `1101001`×4,956, `1101004`×3,637, `1101005`×2,774, `1101006`×911, `1101013`×808, `1102003`×450, `1101009`×375, `1102005`×266, `1101015`×230, `1101007`×212, `1101012`×175, `1102001`×144, `1102002`×67, `1101010`×50, `1101008`×49, `1101002`×21, `1101014`×4, `1101003`×3, `1101011`×1
- **`BPLId`** (3 values) — `2`×11,336, `3`×3,375, `1`×422
- **`BPLName`** (6 values) — `FACTORY`×11,281, `PUNJAB`×3,333, `DELHI`×405, `Factory`×55, `Punjab`×42, `Delhi`×17
- **`VATRegNum`** (3 values) — `06AACCJ4223F1Z0`×11,336, `03AACCJ4223F1Z6`×3,375, `07AACCJ4223F1ZY`×422
- **`SumAbsId`** (1 values) — `-1`×15,133
- **`PIndicator`** (23 values) — `Oct-24-25`×946, `JUL-25-26`×930, `MAY-25-26`×817, `Nov-24-25`×789, `JUN-25-26`×778, `OCT-25-26`×764, `Jan-24-25`×752, `JAN-25-26`×718, `Mar-24-25`×709, `Dec-24-25`×699, `AUG-25-26`×686, `APR-25-26`×669, `Feb-24-25`×666, `SEP-25-26`×654, `DEC-25-26`×631, `FEB-25-26`×584, `NOV-25-26`×575, `JUL-26-27`×541, `MAY-26-27`×533, `APR-26-27`×487, `MAR-25-26`×477, `JUN-26-27`×454, `AUG-26-27`×274
- **`UseShpdGd`** (1 values) — `N`×15,133
- **`DocSubType`** (1 values) — `--`×15,133
- **`DpmStatus`** (1 values) — `O`×15,133
- **`DpmDrawn`** (1 values) — `N`×15,133
- **`Posted`** (1 values) — `Y`×15,133
- **`OwnerCode`** (4 values) — `NULL`×14,507, `20`×606, `14`×15, `2`×5
- **`IsPaytoBnk`** (1 values) — `N`×15,133
- **`isIns`** (1 values) — `N`×15,133
- **`VersionNum`** (2 values) — `10.00.250.15`×10,648, `10.00.310.21`×4,485
- **`LangCode`** (1 values) — `8`×15,133
- **`BPNameOW`** (2 values) — `N`×15,109, `Y`×24
- **`BillToOW`** (2 values) — `N`×15,132, `Y`×1
- **`ShipToOW`** (2 values) — `N`×15,129, `Y`×4
- **`RetInvoice`** (1 values) — `N`×15,133
- **`Model`** (1 values) — `0`×15,133
- **`TaxOnExp`** (3 values) — `0.000000`×15,122, `375.000000`×9, `357.142500`×2
- **`TaxOnExpSc`** (3 values) — `0.000000`×15,122, `375.000000`×9, `357.142500`×2
- **`TaxOnExAp`** (2 values) — `0.000000`×15,130, `375.000000`×3
- **`TaxOnExApS`** (2 values) — `0.000000`×15,130, `375.000000`×3
- **`UseCorrVat`** (1 values) — `N`×15,133
- **`BlkCredMmo`** (1 values) — `N`×15,133
- **`OpenForLaC`** (1 values) — `Y`×15,133
- **`Excised`** (1 values) — `O`×15,133
- **`DutyStatus`** (1 values) — `Y`×15,133
- **`AutoCrtFlw`** (1 values) — `N`×15,133
- **`VatJENum`** (1 values) — `-1`×15,133
- **`InsurOp347`** (1 values) — `N`×15,133
- **`IgnRelDoc`** (1 values) — `N`×15,133
- **`ResidenNum`** (1 values) — `1`×15,133
- **`PQTGrpHW`** (1 values) — `N`×15,133
- **`DocManClsd`** (2 values) — `N`×7,772, `Y`×7,361
- **`ClosingOpt`** (1 values) — `1`×15,133
- **`Ordered`** (1 values) — `N`×15,133
- **`NTSApprov`** (1 values) — `N`×15,133
- **`PayDuMonth`** (1 values) — `N`×15,133
- **`ExtraDays`** (8 values) — `0`×10,845, `30`×2,602, `21`×905, `60`×742, `15`×17, `2`×11, `7`×10, `10`×1
- **`EDocGenTyp`** (1 values) — `N`×15,133
- **`OnlineQuo`** (1 values) — `N`×15,133
- **`EDocStatus`** (1 values) — `C`×15,133
- **`EDocProces`** (1 values) — `C`×15,133
- **`EDocCancel`** (1 values) — `N`×15,133
- **`EDocTest`** (1 values) — `N`×15,133
- **`DpmAsDscnt`** (1 values) — `N`×15,133
- **`GTSRlvnt`** (1 values) — `N`×15,133
- **`SrvTaxRule`** (1 values) — `N`×15,133
- **`Notify`** (2 values) — `N`×8,296, `NULL`×6,837
- **`ReqType`** (1 values) — `12`×15,133
- **`OriginType`** (1 values) — `M`×15,133
- **`IsReuseNum`** (1 values) — `N`×15,133
- **`IsReuseNFN`** (1 values) — `N`×15,133
- **`DocDlvry`** (1 values) — `0`×15,133
- **`EnvTypeNFe`** (1 values) — `-1`×15,133
- **`IsAlt`** (1 values) — `N`×15,133
- **`AltBaseTyp`** (1 values) — `-1`×15,133
- **`PrintSEPA`** (1 values) — `N`×15,133
- **`RelatedTyp`** (1 values) — `-1`×15,133
- **`PoDropPrss`** (1 values) — `Y`×15,133
- **`ExclTaxRep`** (1 values) — `N`×15,133
- **`Revision`** (1 values) — `N`×15,133
- **`GSTTranTyp`** (1 values) — `GA`×15,133
- **`BaseType`** (1 values) — `-1`×15,133
- **`ComTrade`** (1 values) — `E`×15,133
- **`UseBilAddr`** (2 values) — `Y`×14,326, `N`×807
- **`IssReason`** (1 values) — `1`×15,133
- **`ComTradeRt`** (1 values) — `N`×15,133
- **`SplitPmnt`** (1 values) — `N`×15,133
- **`SelfPosted`** (1 values) — `N`×15,133
- **`DPPStatus`** (1 values) — `N`×15,133
- **`EWBGenType`** (1 values) — `N`×15,133
- **`EDocType`** (1 values) — `F`×15,133
- **`AggregDoc`** (1 values) — `N`×15,133
- **`IndFinal`** (1 values) — `N`×15,133
- **`PostPmntWT`** (1 values) — `N`×15,133
- **`FCEPmnMean`** (1 values) — `N`×15,133
- **`NotRel4MI`** (1 values) — `N`×15,133
- **`Rel4PPTax`** (1 values) — `N`×15,133
- **`ConfrmedBy`** (12 values) — `19`×6,814, `24`×4,387, `22`×2,282, `21`×648, `20`×481, `1`×322, `15`×168, `40`×19, `10`×8, `23`×2, `37`×1, `2`×1
- **`BookeTdsBP`** (1 values) — `N`×15,133
- **`DigPayment`** (1 values) — `N`×15,133
- **`PDueMonEnd`** (1 values) — `N`×15,133
- **`RShipToOW`** (2 values) — `N`×14,634, `Y`×499
- **`AplTaxOnFr`** (1 values) — `N`×15,133
- **`CpyDtyStts`** (1 values) — `N`×15,133
- **`U_Basement`** (3 values) — `NULL`×15,120, `Y`×12, `N`×1
- **`U_First_Floor`** (2 values) — `NULL`×15,132, `N`×1
- **`U_GRNdocentry`** (2 values) — `NULL`×15,132, `15396`×1
- **`U_Ship_From`** (15 values) — `NULL`×14,237, `BH-FG`×630, `BH-FU`×112, `PB-JP`×58, `PB-ST`×49, `DL-FG`×20, `GP-FG`×6, `DL-J3`×5, `DL-GR`×4, `DL-PS`×3, `BH-PS`×3, `PB-PS`×2, `BH-OT`×2, `PB-SP`×1, `∅`×1
- **`U_TransporterName`** (15 values) — `NULL`×15,030, `R K TANKER`×31, `R K TANKER SERVICE`×25, `R K TANKER SERVICES`×19, `RK TANKER SERVICE`×12, `RK TANKER SERVICES`×4, `ABC Express`×3, `RK TANKER`×2, `R K TANKER SEVICES`×1, `R. K TANKER SERVICES`×1, `SHREE BHOLENATH CARRIER`×1, `ARSH TRANSPORT`×1, `SS LOGISTICS & CARRIERS`×1, `RK TANKER SERVIES`×1, `R K TANKER SERVEICES`×1
- **`U_VehicleNoM`** (28 values) — `NULL`×15,030, `RJ47GA7523`×11, `RJ47GA1756`×8, `RJ47GA6771`×8, `RJ47GA7520`×7, `RJ47GA7522`×7, `RJ47GA3356`×7, `RJ47GA2009`×7, `RJ47GA1956`×6, `RJ47GA7521`×5, `RJ14GQ1756`×5, `RJ47GA8221`×4, `RJ47GA8216`×3, `RJ47GA7911`×3, `RJ47GA3056`×3, `GJ39T3128`×3, `RJ47GB0056`×2, `RJ47GB0492`×2, `RJ47GA8217`×2, `RJ47GA8215`×2, `RJ47GA6770`×1, `RJ32GD2788`×1, `RJ47GQ1756`×1, `PB03AY7137`×1, `RJ47GB2009`×1, `GJ12BV 8847`×1, `RJ47GA75223`×1, `PB03BB9537`×1
- **`U_Mob_No`** (2 values) — `NULL`×15,130, `9001476065`×3
- **`U_Order_Date`** (26 values) — `NULL`×14,452, `2026-07-22 00:00:00.0000000`×75, `2026-06-17 00:00:00.0000000`×57, `2026-05-25 00:00:00.0000000`×55, `2026-04-17 00:00:00.0000000`×49, `2026-03-20 00:00:00.0000000`×42, `2025-07-18 00:00:00.0000000`×32, `2026-02-16 00:00:00.0000000`×29, `2025-08-29 00:00:00.0000000`×27, `2025-02-28 00:00:00.0000000`×27, `2025-12-26 00:00:00.0000000`×27, `2025-05-23 00:00:00.0000000`×26, `2025-04-23 00:00:00.0000000`×26, `2025-10-16 00:00:00.0000000`×24, `2025-06-26 00:00:00.0000000`×24, `2025-09-30 00:00:00.0000000`×23, `2025-02-07 00:00:00.0000000`×23, `2026-01-23 00:00:00.0000000`×23, `2025-11-20 00:00:00.0000000`×23, `2025-04-01 00:00:00.0000000`×22, `2025-01-06 00:00:00.0000000`×19, `2024-12-10 00:00:00.0000000`×13, `2024-11-08 00:00:00.0000000`×12, `2025-01-27 00:00:00.0000000`×1, `2025-05-30 00:00:00.0000000`×1, `2020-06-26 00:00:00.0000000`×1
- **`U_AR_NO`** (13 values) — `NULL`×15,084, `602411`×12, `602412`×10, `41479`×7, `41802`×7, `42101`×2, `41914`×2, `625037000`×2, `625025002`×2, `1196`×2, `625025001`×1, `625037001`×1, `41350`×1
- **`U_InvRevEntry`** (2 values) — `NULL`×15,131, `AEL1823134`×2
- **`U_LRNUmber`** (12 values) — `NULL`×15,086, `8568599`×11, `8562896`×10, `8072845`×7, `8890469`×7, `9081998`×2, `8530178`×2, `9644176`×2, `8254803`×2, `9094228`×2, `7597874`×1, `9116436`×1
- **`U_BOEDate`** (11 values) — `NULL`×15,088, `2025-02-26 00:00:00.0000000`×13, `2025-02-25 00:00:00.0000000`×10, `2025-01-29 00:00:00.0000000`×7, `2025-03-14 00:00:00.0000000`×5, `2025-04-22 00:00:00.0000000`×2, `2025-03-17 00:00:00.0000000`×2, `2025-02-08 00:00:00.0000000`×2, `2025-03-25 00:00:00.0000000`×2, `2025-01-03 00:00:00.0000000`×1, `2025-03-18 00:00:00.0000000`×1
- **`U_UNE_MLOC`** (5 values) — `NULL`×15,126, `u`×4, `-3.88`×1, `-`×1, `U`×1
- **`U_ARNO`** (2 values) — `NULL`×15,073, `T`×60
- **`U_SALES_PERSON`** (22 values) — `NULL`×8,851, `ECOM`×1,383, `PUNJAB MT`×1,049, `PUNJAB GT`×795, `PRIVATE`×528, `DELHI GT`×522, `CSD`×439, `HARYANA GT`×397, `HAPPY`×207, `PRINCE OTHER`×200, `UP/UK GT`×150, `HORECA/INST`×145, `TARUN`×97, `DELHI MT`×95, `ROI`×87, `BRANCH`×84, `EXPORT`×38, `HIMACHAL`×23, `FREE SAMPLE`×19, `BANGLORE`×9, `HYDERABAD`×8, `HP GT`×7
- **`U_GRPO`** (3 values) — `NULL`×15,128, `N`×3, `Y`×2
