# `OPOR` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 4,325 | 654 | `DocDate` | 2024-10-01 → 2026-08-24 |
| MART | 2,258 | 392 | `DocDate` | 2024-10-03 → 2026-08-24 |
| BEV | 1,141 | 120 | `DocDate` | 2024-10-01 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4,325 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4,325 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 652 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 662 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 509 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 510 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 462 | |
| `NumAtCard` | NVARCHAR(200) | 2% | 87% | <1% | <1% | 85% | — | 85 | |
| `VatSum` | DECIMAL | 71% | 100% | 86% | 73% | 100% | 87% | 2,410 | |
| `DiscPrcnt` | DECIMAL | <1% | — | <1% | <1% | — | — | 20 | |
| `DiscSum` | DECIMAL | <1% | — | <1% | <1% | — | — | 20 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 42 | |
| `DocTotal` | DECIMAL | 99% | 100% | 100% | 100% | 100% | 100% | 3,284 | |
| `DocTotalFC` | DECIMAL | 2% | — | — | <1% | — | — | 58 | |
| `PaidToDate` | DECIMAL | 94% | 98% | 88% | 91% | 91% | 78% | 3,198 | |
| `PaidFC` | DECIMAL | 2% | — | — | <1% | — | — | 58 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 4,325 | |
| `Comments` | NVARCHAR(254) | 15% | 3% | 10% | 16% | 4% | 20% | 564 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 507 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 626 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 47 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 87% | 100% | 95% | 87% | 100% | 97% | 482 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `VatSumSy` | DECIMAL | 71% | 100% | 86% | 73% | 100% | 87% | 2,410 | |
| `DiscSumSy` | DECIMAL | <1% | — | <1% | <1% | — | — | 20 | |
| `DocTotalSy` | DECIMAL | 99% | 100% | 100% | 100% | 100% | 100% | 3,284 | |
| `PaidSys` | DECIMAL | 94% | 98% | 88% | 91% | 91% | 78% | 3,198 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 569 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 652 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | 62% | 85% | 72% | 64% | 83% | 62% | 2,312 | |
| `VatPaidSys` | DECIMAL | 62% | 85% | 72% | 64% | 83% | 62% | 2,312 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `draftKey` | INTEGER | 51% | 9% | 84% | 76% | 19% | 99% | 2,179 | |
| `TotalExpns` | DECIMAL | 4% | <1% | 10% | 3% | <1% | 6% | 96 | |
| `TotalExpSC` | DECIMAL | 4% | <1% | 10% | 3% | <1% | 6% | 96 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 59 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 412 | |
| `RoundDif` | DECIMAL | 25% | 58% | 33% | 40% | 28% | 28% | 360 | |
| `RoundDifFC` | DECIMAL | <1% | — | — | <1% | — | — | 2 | |
| `RoundDifSy` | DECIMAL | 25% | 58% | 33% | 40% | 28% | 28% | 360 | |
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
| `Max1099` | DECIMAL | 99% | 100% | 100% | 100% | 100% | 100% | 3,240 | |
| `ExpAppl` | DECIMAL | 3% | <1% | 7% | 2% | — | 2% | 80 | |
| `ExpApplSC` | DECIMAL | 3% | <1% | 7% | 2% | — | 2% | 80 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OwnerCode` | INTEGER | <1% | — | — | <1% | — | — | 4 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 409 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxOnExp` | DECIMAL | 3% | <1% | 9% | 3% | <1% | 6% | 74 | |
| `TaxOnExpSc` | DECIMAL | 3% | <1% | 9% | 3% | <1% | 6% | 74 | |
| `TaxOnExAp` | DECIMAL | 2% | <1% | 6% | 2% | — | 2% | 58 | |
| `TaxOnExApS` | DECIMAL | 2% | <1% | 6% | 2% | — | 2% | 58 | |
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
| `ExtraDays` | SMALLINT | 35% | 1% | 32% | 31% | 3% | 32% | 9 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 1% | 3% | <1% | <1% | 4% | — | 57 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4,082 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4,040 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AssetDate` | TIMESTAMP | 10% | 2% | 4% | 6% | 5% | 10% | 255 | |
| `Notify` | NVARCHAR(1) | 16% | 39% | 13% | 29% | 44% | 12% | 1 | |
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
| `GSTTranTyp` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
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
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 49 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ConfrmedBy` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `ConfrmedOn` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 569 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AplTaxOnFr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_BilltyNumber` | NVARCHAR(15) | <1% | — | n/a | — | — | n/a | 18 | |
| `U_BiltyDate` | TIMESTAMP | <1% | — | — | — | — | — | 12 | |
| `U_TransporterName` | NVARCHAR(50) | <1% | — | — | — | — | — | 6 | |
| `U_VehicleNoM` | NVARCHAR(12) | <1% | — | n/a | — | — | n/a | 14 | |
| `U_AR_NO` | NVARCHAR(12) | <1% | — | n/a | — | — | n/a | 14 | |
| `U_InvRevEntry` | NVARCHAR(20) | <1% | — | — | — | — | — | 3 | |
| `U_LRNUmber` | NVARCHAR(15) | <1% | — | n/a | — | — | n/a | 8 | |
| `U_BOEDate` | TIMESTAMP | <1% | — | n/a | — | — | n/a | 5 | |
| `U_UNE_SO` | NVARCHAR(100) | — | <1% | — | — | — | — | 0 | |
| `U_UNE_MLOC` | NVARCHAR(100) | <1% | <1% | — | — | — | — | 1 | |
| `U_UNE_ACTH` | NVARCHAR(100) | — | — | 98% | — | — | 100% | 0 | |

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

- **`DocType`** (2 values) — `I`×4,294, `S`×31
- **`CANCELED`** (2 values) — `N`×4,292, `Y`×33
- **`Handwrtten`** (1 values) — `N`×4,325
- **`Printed`** (2 values) — `N`×2,267, `Y`×2,058
- **`DocStatus`** (2 values) — `C`×3,975, `O`×350
- **`InvntSttus`** (2 values) — `C`×3,182, `O`×1,143
- **`Transfered`** (1 values) — `N`×4,325
- **`ObjType`** (1 values) — `22`×4,325
- **`DiscPrcnt`** (21 values) — `0.000000`×4,302, `NULL`×4, `0.000219`×1, `0.003614`×1, `0.002190`×1, `-0.000733`×1, `0.001054`×1, `-0.000684`×1, `0.001243`×1, `1.950000`×1, `0.004159`×1, `-0.000057`×1, `0.007739`×1, `0.000271`×1, `-0.196564`×1, `0.000638`×1, `0.000529`×1, `0.299103`×1, `0.003081`×1, `-0.001049`×1, `0.001028`×1
- **`DiscSum`** (20 values) — `0.000000`×4,306, `0.169500`×1, `0.642900`×1, `103.780200`×1, `0.254200`×1, `-0.185800`×1, `0.105900`×1, `0.369900`×1, `0.152600`×1, `0.338500`×1, `0.178600`×1, `0.762700`×1, `-0.345800`×1, `-0.214300`×1, `0.237700`×1, `-0.357100`×1, `-247.178700`×1, `0.170600`×1, `0.300000`×1, `0.339000`×1
- **`DocCur`** (3 values) — `INR`×4,255, `USD`×49, `EUR`×21
- **`GroupNum`** (12 values) — `-1`×2,806, `1`×990, `22`×144, `16`×138, `19`×81, `21`×74, `18`×58, `17`×16, `4`×8, `7`×6, `20`×2, `3`×2
- **`TrnspCode`** (1 values) — `-1`×4,325
- **`PartSupply`** (1 values) — `Y`×4,325
- **`Confirmed`** (1 values) — `Y`×4,325
- **`GrossBase`** (2 values) — `-6`×4,093, `-1`×232
- **`CreateTran`** (1 values) — `N`×4,325
- **`SummryType`** (1 values) — `N`×4,325
- **`UpdInvnt`** (1 values) — `O`×4,325
- **`UpdCardBal`** (1 values) — `O`×4,325
- **`InvntDirec`** (1 values) — `E`×4,325
- **`ShowSCN`** (1 values) — `N`×4,325
- **`SysRate`** (1 values) — `1.000000`×4,325
- **`CurSource`** (2 values) — `L`×4,255, `C`×70
- **`DiscSumSy`** (20 values) — `0.000000`×4,306, `0.237700`×1, `0.369900`×1, `0.169500`×1, `0.642900`×1, `103.780200`×1, `0.254200`×1, `-0.185800`×1, `0.105900`×1, `0.152600`×1, `0.338500`×1, `0.178600`×1, `0.762700`×1, `-0.345800`×1, `-0.214300`×1, `0.339000`×1, `0.300000`×1, `0.170600`×1, `-247.178700`×1, `-0.357100`×1
- **`FatherType`** (1 values) — `P`×4,325
- **`IsICT`** (1 values) — `N`×4,325
- **`VolUnit`** (1 values) — `4`×4,325
- **`WeightUnit`** (2 values) — `3`×4,322, `2`×3
- **`Series`** (23 values) — `703`×326, `708`×253, `705`×231, `2211`×218, `704`×212, `706`×211, `2203`×210, `707`×203, `2205`×199, `2463`×193, `2204`×191, `2202`×189, `2210`×186, `2207`×175, `2461`×175, `2462`×173, `2206`×170, `2464`×155, `2213`×154, `2209`×148, `2212`×128, `2208`×116, `2465`×109
- **`isCrin`** (1 values) — `N`×4,325
- **`FinncPriod`** (23 values) — `7`×326, `12`×253, `9`×231, `23`×218, `8`×212, `10`×211, `15`×210, `11`×203, `17`×199, `43`×193, `16`×191, `14`×189, `22`×186, `19`×175, `41`×175, `42`×173, `18`×170, `44`×155, `25`×154, `21`×148, `24`×128, `20`×116, `45`×109
- **`UserSign`** (12 values) — `31`×1,749, `32`×1,006, `15`×694, `16`×407, `30`×369, `36`×69, `29`×11, `22`×10, `1`×4, `10`×3, `40`×2, `12`×1
- **`selfInv`** (1 values) — `N`×4,325
- **`WddStatus`** (2 values) — `-`×2,166, `P`×2,159
- **`Exported`** (1 values) — `N`×4,325
- **`NetProc`** (1 values) — `N`×4,325
- **`RoundDifFC`** (2 values) — `0.000000`×4,324, `0.500000`×1
- **`submitted`** (1 values) — `N`×4,325
- **`PoPrss`** (1 values) — `N`×4,325
- **`Rounding`** (2 values) — `N`×3,356, `Y`×969
- **`RevisionPo`** (1 values) — `N`×4,325
- **`PickStatus`** (1 values) — `N`×4,325
- **`Pick`** (1 values) — `N`×4,325
- **`BlockDunn`** (1 values) — `N`×4,325
- **`PayBlock`** (1 values) — `N`×4,325
- **`MaxDscn`** (1 values) — `N`×4,325
- **`Reserve`** (1 values) — `N`×4,325
- **`DeferrTax`** (1 values) — `N`×4,325
- **`BoeReserev`** (1 values) — `N`×4,325
- **`Installmnt`** (1 values) — `1`×4,325
- **`VATFirst`** (1 values) — `N`×4,325
- **`CEECFlag`** (1 values) — `N`×4,325
- **`CtlAccount`** (10 values) — `2110005`×2,120, `2110004`×1,089, `2110001`×514, `2110003`×509, `2110002`×61, `2110007`×12, `2121002`×11, `2121001`×5, `2121003`×3, `2110006`×1
- **`BPLId`** (2 values) — `2`×3,907, `1`×418
- **`BPLName`** (4 values) — `FACTORY`×3,899, `DELHI`×417, `Factory`×8, `Delhi`×1
- **`VATRegNum`** (2 values) — `06AACCJ4223F1Z0`×3,907, `07AACCJ4223F1ZY`×418
- **`SumAbsId`** (1 values) — `-1`×4,325
- **`PIndicator`** (23 values) — `Oct-24-25`×326, `Mar-24-25`×253, `Dec-24-25`×231, `JAN-25-26`×218, `Nov-24-25`×212, `Jan-24-25`×211, `MAY-25-26`×210, `Feb-24-25`×203, `JUL-25-26`×199, `JUN-26-27`×193, `JUN-25-26`×191, `APR-25-26`×189, `DEC-25-26`×186, `APR-26-27`×175, `SEP-25-26`×175, `MAY-26-27`×173, `AUG-25-26`×170, `JUL-26-27`×155, `MAR-25-26`×154, `NOV-25-26`×148, `FEB-25-26`×128, `OCT-25-26`×116, `AUG-26-27`×109
- **`UseShpdGd`** (1 values) — `N`×4,325
- **`DocSubType`** (1 values) — `--`×4,325
- **`DpmStatus`** (1 values) — `O`×4,325
- **`DpmDrawn`** (1 values) — `N`×4,325
- **`Posted`** (1 values) — `Y`×4,325
- **`OwnerCode`** (5 values) — `NULL`×4,282, `20`×39, `2`×2, `4`×1, `14`×1
- **`IsPaytoBnk`** (1 values) — `N`×4,325
- **`isIns`** (1 values) — `N`×4,325
- **`VersionNum`** (2 values) — `10.00.250.15`×2,883, `10.00.310.21`×1,442
- **`LangCode`** (1 values) — `8`×4,325
- **`BPNameOW`** (2 values) — `N`×4,324, `Y`×1
- **`BillToOW`** (1 values) — `N`×4,325
- **`ShipToOW`** (1 values) — `N`×4,325
- **`RetInvoice`** (1 values) — `N`×4,325
- **`Model`** (1 values) — `0`×4,325
- **`UseCorrVat`** (1 values) — `N`×4,325
- **`BlkCredMmo`** (1 values) — `N`×4,325
- **`OpenForLaC`** (1 values) — `Y`×4,325
- **`Excised`** (1 values) — `O`×4,325
- **`DutyStatus`** (1 values) — `Y`×4,325
- **`AutoCrtFlw`** (1 values) — `N`×4,325
- **`VatJENum`** (1 values) — `-1`×4,325
- **`InsurOp347`** (1 values) — `N`×4,325
- **`IgnRelDoc`** (1 values) — `N`×4,325
- **`ResidenNum`** (1 values) — `1`×4,325
- **`PQTGrpHW`** (1 values) — `N`×4,325
- **`DocManClsd`** (2 values) — `N`×3,537, `Y`×788
- **`ClosingOpt`** (1 values) — `1`×4,325
- **`Ordered`** (1 values) — `N`×4,325
- **`NTSApprov`** (1 values) — `N`×4,325
- **`PayDuMonth`** (1 values) — `N`×4,325
- **`ExtraDays`** (9 values) — `0`×2,822, `30`×990, `35`×144, `5`×138, `15`×81, `25`×74, `10`×58, `7`×16, `21`×2
- **`EDocGenTyp`** (1 values) — `N`×4,325
- **`OnlineQuo`** (1 values) — `N`×4,325
- **`EDocStatus`** (1 values) — `C`×4,325
- **`EDocProces`** (1 values) — `C`×4,325
- **`EDocCancel`** (1 values) — `N`×4,325
- **`EDocTest`** (1 values) — `N`×4,325
- **`DpmAsDscnt`** (1 values) — `N`×4,325
- **`GTSRlvnt`** (1 values) — `N`×4,325
- **`SrvTaxRule`** (1 values) — `N`×4,325
- **`Notify`** (2 values) — `NULL`×3,645, `N`×680
- **`ReqType`** (1 values) — `12`×4,325
- **`OriginType`** (1 values) — `M`×4,325
- **`IsReuseNum`** (1 values) — `N`×4,325
- **`IsReuseNFN`** (1 values) — `N`×4,325
- **`DocDlvry`** (1 values) — `0`×4,325
- **`EnvTypeNFe`** (1 values) — `-1`×4,325
- **`IsAlt`** (1 values) — `N`×4,325
- **`AltBaseTyp`** (1 values) — `-1`×4,325
- **`PrintSEPA`** (1 values) — `N`×4,325
- **`RelatedTyp`** (1 values) — `-1`×4,325
- **`PoDropPrss`** (1 values) — `N`×4,325
- **`ExclTaxRep`** (1 values) — `N`×4,325
- **`Revision`** (1 values) — `N`×4,325
- **`GSTTranTyp`** (2 values) — `GA`×3,588, `--`×737
- **`BaseType`** (1 values) — `-1`×4,325
- **`ComTrade`** (1 values) — `E`×4,325
- **`UseBilAddr`** (2 values) — `N`×4,025, `Y`×300
- **`IssReason`** (1 values) — `1`×4,325
- **`ComTradeRt`** (1 values) — `N`×4,325
- **`SplitPmnt`** (1 values) — `N`×4,325
- **`SelfPosted`** (1 values) — `N`×4,325
- **`DPPStatus`** (1 values) — `N`×4,325
- **`EWBGenType`** (1 values) — `N`×4,325
- **`EDocType`** (1 values) — `F`×4,325
- **`AggregDoc`** (1 values) — `N`×4,325
- **`IndFinal`** (1 values) — `N`×4,325
- **`PostPmntWT`** (1 values) — `N`×4,325
- **`FCEPmnMean`** (1 values) — `N`×4,325
- **`NotRel4MI`** (1 values) — `N`×4,325
- **`Rel4PPTax`** (1 values) — `N`×4,325
- **`ConfrmedBy`** (12 values) — `31`×1,752, `32`×1,003, `15`×694, `16`×407, `30`×369, `36`×69, `29`×11, `22`×10, `1`×4, `10`×3, `40`×2, `12`×1
- **`BookeTdsBP`** (1 values) — `N`×4,325
- **`DigPayment`** (1 values) — `N`×4,325
- **`PDueMonEnd`** (1 values) — `N`×4,325
- **`RShipToOW`** (1 values) — `N`×4,325
- **`AplTaxOnFr`** (1 values) — `N`×4,325
- **`CpyDtyStts`** (1 values) — `N`×4,325
- **`U_BilltyNumber`** (19 values) — `NULL`×4,301, `6365`×5, `6089`×2, `6138`×2, `6148`×1, `6100`×1, `6119`×1, `6061`×1, `6093`×1, `6058`×1, `118`×1, `6140`×1, `24542`×1, `5707`×1, `6083`×1, `6858`×1, `6111`×1, `6117`×1, `5686`×1
- **`U_BiltyDate`** (13 values) — `NULL`×4,310, `2025-01-13 00:00:00.0000000`×3, `2024-12-27 00:00:00.0000000`×2, `2025-01-02 00:00:00.0000000`×1, `2024-12-18 00:00:00.0000000`×1, `2025-01-06 00:00:00.0000000`×1, `2024-11-18 00:00:00.0000000`×1, `2024-12-28 00:00:00.0000000`×1, `2025-03-17 00:00:00.0000000`×1, `2025-04-28 00:00:00.0000000`×1, `2024-12-21 00:00:00.0000000`×1, `2026-01-30 00:00:00.0000000`×1, `2024-12-30 00:00:00.0000000`×1
- **`U_TransporterName`** (7 values) — `NULL`×4,306, `R K TANKER SERVICES`×10, `R K TANKER SERVICE`×5, `SKY BRIDGE SUPPLY CHAIN SOLUTION LLP`×1, `R K TANKER`×1, `ARSH TRANSPORT`×1, `R.K. TANKER SERVICE`×1
- **`U_VehicleNoM`** (15 values) — `NULL`×4,305, `RJ47GA1956`×4, `RJ47GA7523`×3, `RJ14GQ1756`×2, `RJ47GA7521`×1, `HR42J6791`×1, `RJ47GA7522`×1, `RJ32GD2788`×1, `RJ47GA3356`×1, `RJ47GA6770`×1, `RJ04GB4051`×1, `RJ47GA1756`×1, `RJ47GA6771`×1, `RJ47GA2009`×1, `PB03BE7511`×1
- **`U_AR_NO`** (15 values) — `NULL`×4,310, `40816`×2, `1198`×1, `41479`×1, `1205`×1, `41914`×1, `1197`×1, `602412`×1, `41350`×1, `ES24-024262`×1, `1206`×1, `AEL1963621`×1, `41802`×1, `1196`×1, `ES24-016457`×1
- **`U_InvRevEntry`** (4 values) — `NULL`×4,321, `EPIRAEESAD259371`×2, `EPIRAEESAD261749`×1, `247509491`×1
- **`U_LRNUmber`** (9 values) — `NULL`×4,317, `8562896`×1, `8072845`×1, `8254803`×1, `7969788`×1, `7963510`×1, `5963810`×1, `8072204`×1, `8833384`×1
- **`U_BOEDate`** (6 values) — `NULL`×4,318, `2025-01-29 00:00:00.0000000`×2, `2025-01-24 00:00:00.0000000`×2, `2025-02-08 00:00:00.0000000`×1, `2025-11-27 00:00:00.0000000`×1, `2025-03-11 00:00:00.0000000`×1
