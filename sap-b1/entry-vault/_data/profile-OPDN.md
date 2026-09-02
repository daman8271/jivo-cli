# `OPDN` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 11,649 | 1,827 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 3,222 | 562 | `DocDate` | 2024-10-03 → 2026-08-24 |
| BEV | 4,826 | 1,201 | `DocDate` | 2024-09-30 → 2026-08-20 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 11,649 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 11,649 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 661 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 661 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 529 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 530 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 475 | |
| `NumAtCard` | NVARCHAR(200) | 93% | 99% | 99% | 100% | 100% | 100% | 9,520 | |
| `VatSum` | DECIMAL | 59% | 98% | 30% | 56% | 88% | 16% | 5,509 | |
| `DiscPrcnt` | DECIMAL | <1% | — | <1% | — | — | — | 15 | |
| `DiscSum` | DECIMAL | <1% | — | <1% | — | — | — | 15 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 44 | |
| `DocTotal` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 8,121 | |
| `DocTotalFC` | DECIMAL | <1% | — | — | <1% | — | — | 70 | |
| `PaidToDate` | DECIMAL | 97% | 99% | 96% | 83% | 94% | 87% | 7,932 | |
| `PaidFC` | DECIMAL | <1% | — | — | <1% | — | — | 70 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 11,649 | |
| `Comments` | NVARCHAR(254) | 98% | 100% | 99% | 100% | 100% | 100% | 11,018 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 682 | |
| `TransId` | INTEGER | 44% | 94% | 16% | 45% | 82% | 8% | 5,156 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 692 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 53 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 76% | 100% | 96% | 84% | 100% | 99% | 499 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `VatSumSy` | DECIMAL | 59% | 98% | 30% | 56% | 88% | 16% | 5,509 | |
| `DiscSumSy` | DECIMAL | <1% | — | <1% | — | — | — | 15 | |
| `DocTotalSy` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 8,121 | |
| `PaidSys` | DECIMAL | 97% | 99% | 96% | 83% | 94% | 87% | 7,932 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 592 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 709 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 26 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | 57% | 97% | 29% | 48% | 87% | 13% | 5,400 | |
| `VatPaidSys` | DECIMAL | 57% | 97% | 29% | 48% | 87% | 13% | 5,400 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `draftKey` | INTEGER | 37% | 37% | 14% | 30% | 81% | 4% | 4,336 | |
| `TotalExpns` | DECIMAL | 2% | <1% | 3% | 1% | — | <1% | 102 | |
| `TotalExpSC` | DECIMAL | 2% | <1% | 3% | 1% | — | <1% | 102 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 92 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 99% | 100% | 100% | 429 | |
| `RoundDif` | DECIMAL | 35% | 61% | 16% | 52% | 33% | 13% | 1,166 | |
| `RoundDifSy` | DECIMAL | 35% | 61% | 16% | 52% | 33% | 13% | 1,166 | |
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
| `Max1099` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 8,199 | |
| `ExpAppl` | DECIMAL | 2% | <1% | 3% | 1% | — | <1% | 97 | |
| `ExpApplSC` | DECIMAL | 2% | <1% | 3% | 1% | — | <1% | 97 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 13 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OwnerCode` | INTEGER | <1% | — | — | <1% | — | — | 5 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 424 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxOnExp` | DECIMAL | 1% | <1% | 3% | 1% | — | <1% | 82 | |
| `TaxOnExpSc` | DECIMAL | 1% | <1% | 3% | 1% | — | <1% | 82 | |
| `TaxOnExAp` | DECIMAL | 1% | <1% | 3% | 1% | — | <1% | 81 | |
| `TaxOnExApS` | DECIMAL | 1% | <1% | 3% | 1% | — | <1% | 81 | |
| `LndCstNum` | INTEGER | 5% | — | <1% | 4% | — | — | 530 | |
| `UseCorrVat` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlkCredMmo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OpenForLaC` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
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
| `SpecDate` | TIMESTAMP | — | <1% | — | — | — | — | 0 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayDuMonth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExtraDays` | SMALLINT | 53% | 2% | 27% | 39% | 5% | 9% | 9 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 93% | 96% | 99% | 100% | 100% | 100% | 10,454 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDiscPr` | DECIMAL | <1% | — | <1% | — | — | — | 15 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 9,813 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 9,774 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AssetDate` | TIMESTAMP | <1% | — | <1% | — | — | — | 5 | |
| `Notify` | NVARCHAR(1) | 26% | 3% | 49% | 16% | 10% | 47% | 1 | |
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
| `EWBGenType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 38 | |
| `ShipPlace` | NVARCHAR(60) | <1% | — | 5% | <1% | — | 19% | 3 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AplTaxOnFr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Recv_Date` | TIMESTAMP | <1% | — | <1% | — | — | — | 1 | |
| `U_deldocnum` | NVARCHAR(100) | 7% | 4% | 1% | — | — | — | 747 | |
| `U_deldocdate` | TIMESTAMP | 7% | 4% | 1% | — | — | — | 260 | |
| `U_delbranch` | NVARCHAR(100) | 7% | 4% | 1% | — | — | — | 3 | |
| `U_delbranchnam` | NVARCHAR(100) | 7% | 4% | 1% | — | — | — | 3 | |
| `U_BilltyNumber` | NVARCHAR(15) | 8% | — | n/a | 14% | — | n/a | 834 | |
| `U_BiltyDate` | TIMESTAMP | 8% | — | 5% | 14% | — | 21% | 415 | |
| `U_TransporterName` | NVARCHAR(50) | 8% | — | 5% | 14% | — | 21% | 139 | |
| `U_VehicleNoM` | NVARCHAR(12) | 6% | — | n/a | 14% | — | n/a | 239 | |
| `U_DriverName` | NCLOB | <1% | — | — | — | — | — | 0 | |
| `U_TransporterInvoice` | NVARCHAR(15) | <1% | — | 5% | <1% | — | 19% | 11 | |
| `U_AR_NO` | NVARCHAR(12) | <1% | — | n/a | <1% | — | n/a | 37 | |
| `U_InvRevEntry` | NVARCHAR(20) | <1% | — | — | <1% | — | — | 43 | |
| `U_LRNUmber` | NVARCHAR(15) | 1% | — | n/a | 2% | — | n/a | 100 | |
| `U_BOEDate` | TIMESTAMP | <1% | — | n/a | <1% | — | n/a | 49 | |
| `U_UNE_SO` | NVARCHAR(100) | — | <1% | — | — | — | — | 0 | |
| `U_UNE_MLOC` | NVARCHAR(100) | <1% | <1% | — | — | <1% | — | 2 | |
| `U_UNE_ACTH` | NVARCHAR(100) | <1% | — | 99% | — | — | 100% | 1 | |
| `U_TotalAmt` | DECIMAL | <1% | — | 5% | <1% | — | 19% | 12 | |
| `U_ARNO` | NVARCHAR(100) | <1% | — | 5% | <1% | — | 19% | 50 | |

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

- **`DocType`** (2 values) — `I`×7,379, `S`×4,270
- **`CANCELED`** (3 values) — `N`×10,703, `C`×473, `Y`×473
- **`Handwrtten`** (1 values) — `N`×11,649
- **`Printed`** (2 values) — `N`×9,151, `Y`×2,498
- **`DocStatus`** (2 values) — `C`×11,279, `O`×370
- **`InvntSttus`** (2 values) — `C`×11,354, `O`×295
- **`Transfered`** (1 values) — `N`×11,649
- **`ObjType`** (1 values) — `20`×11,649
- **`DiscPrcnt`** (15 values) — `0.000000`×11,634, `-0.196564`×2, `0.001055`×1, `0.003614`×1, `-0.000684`×1, `0.001243`×1, `0.002190`×1, `0.007739`×1, `0.299103`×1, `0.000271`×1, `1.950000`×1, `0.003082`×1, `-0.000057`×1, `0.000529`×1, `-0.000169`×1
- **`DiscSum`** (15 values) — `0.000000`×11,634, `-247.178700`×2, `0.169500`×1, `0.178700`×1, `0.254200`×1, `-0.310600`×1, `0.762700`×1, `-0.345800`×1, `0.376300`×1, `0.161000`×1, `0.105900`×1, `0.237700`×1, `-0.184700`×1, `103.780200`×1, `0.067200`×1
- **`DocCur`** (3 values) — `INR`×11,561, `USD`×56, `EUR`×32
- **`GroupNum`** (12 values) — `-1`×5,425, `1`×3,079, `21`×1,369, `20`×682, `19`×550, `22`×235, `16`×135, `18`×107, `17`×48, `4`×12, `7`×6, `3`×1
- **`TrnspCode`** (1 values) — `-1`×11,649
- **`PartSupply`** (1 values) — `Y`×11,649
- **`Confirmed`** (1 values) — `Y`×11,649
- **`GrossBase`** (2 values) — `-6`×11,115, `-1`×534
- **`CreateTran`** (1 values) — `N`×11,649
- **`SummryType`** (1 values) — `N`×11,649
- **`UpdInvnt`** (1 values) — `I`×11,649
- **`UpdCardBal`** (1 values) — `D`×11,649
- **`InvntDirec`** (1 values) — `E`×11,649
- **`ShowSCN`** (1 values) — `N`×11,649
- **`SysRate`** (1 values) — `1.000000`×11,649
- **`CurSource`** (3 values) — `L`×11,558, `C`×88, `S`×3
- **`DiscSumSy`** (15 values) — `0.000000`×11,634, `-247.178700`×2, `0.161000`×1, `0.762700`×1, `-0.345800`×1, `0.237700`×1, `-0.184700`×1, `0.169500`×1, `0.178700`×1, `0.254200`×1, `-0.310600`×1, `103.780200`×1, `0.067200`×1, `0.105900`×1, `0.376300`×1
- **`FatherType`** (1 values) — `P`×11,649
- **`IsICT`** (1 values) — `N`×11,649
- **`VolUnit`** (1 values) — `4`×11,649
- **`WeightUnit`** (1 values) — `3`×11,649
- **`Series`** (24 values) — `683`×782, `687`×648, `2097`×635, `2475`×587, `2095`×571, `686`×557, `2098`×542, `685`×542, `2100`×519, `2103`×516, `2102`×507, `684`×491, `2099`×482, `2096`×473, `2094`×471, `2473`×470, `2474`×462, `2476`×462, `682`×450, `2101`×439, `2105`×414, `2104`×381, `2477`×247, `681`×1
- **`isCrin`** (1 values) — `N`×11,649
- **`FinncPriod`** (24 values) — `8`×782, `12`×648, `17`×635, `43`×587, `15`×571, `11`×557, `18`×542, `10`×542, `20`×519, `23`×516, `22`×507, `9`×491, `19`×482, `16`×473, `14`×471, `41`×470, `42`×462, `44`×462, `7`×450, `21`×439, `25`×414, `24`×381, `45`×247, `6`×1
- **`UserSign`** (26 values) — `28`×3,450, `36`×2,529, `31`×1,583, `44`×669, `30`×624, `22`×565, `16`×499, `2`×300, `29`×252, `15`×232, `1`×172, `35`×161, `40`×157, `10`×134, `38`×125, `32`×56, `47`×55, `24`×29, `37`×20, `19`×16, `48`×13, `33`×3, `39`×2, `53`×1, `26`×1, `12`×1
- **`selfInv`** (1 values) — `N`×11,649
- **`WddStatus`** (3 values) — `-`×7,368, `P`×4,148, `A`×133
- **`Exported`** (1 values) — `N`×11,649
- **`NetProc`** (1 values) — `N`×11,649
- **`submitted`** (1 values) — `N`×11,649
- **`PoPrss`** (1 values) — `N`×11,649
- **`Rounding`** (2 values) — `N`×8,520, `Y`×3,129
- **`RevisionPo`** (1 values) — `N`×11,649
- **`PickStatus`** (1 values) — `N`×11,649
- **`Pick`** (1 values) — `N`×11,649
- **`BlockDunn`** (1 values) — `N`×11,649
- **`PayBlock`** (1 values) — `N`×11,649
- **`MaxDscn`** (1 values) — `N`×11,649
- **`Reserve`** (1 values) — `N`×11,649
- **`DeferrTax`** (1 values) — `N`×11,649
- **`BoeReserev`** (1 values) — `N`×11,649
- **`Installmnt`** (1 values) — `1`×11,649
- **`VATFirst`** (1 values) — `N`×11,649
- **`CEECFlag`** (1 values) — `N`×11,649
- **`CtlAccount`** (13 values) — `2110004`×5,483, `2110005`×3,639, `2110003`×890, `2110001`×754, `2120002`×570, `2120006`×149, `2110002`×76, `2120001`×56, `2110007`×12, `2121002`×11, `2121001`×5, `2121003`×3, `2110006`×1
- **`BPLId`** (4 values) — `2`×10,527, `1`×666, `3`×455, `8`×1
- **`BPLName`** (7 values) — `FACTORY`×10,523, `DELHI`×665, `PUNJAB`×451, `Punjab`×4, `Factory`×4, `HARYANA INFO`×1, `Delhi`×1
- **`VATRegNum`** (3 values) — `06AACCJ4223F1Z0`×10,528, `07AACCJ4223F1ZY`×666, `03AACCJ4223F1Z6`×455
- **`SumAbsId`** (1 values) — `-1`×11,649
- **`PIndicator`** (24 values) — `Nov-24-25`×782, `Mar-24-25`×648, `JUL-25-26`×635, `JUN-26-27`×587, `MAY-25-26`×571, `Feb-24-25`×557, `Jan-24-25`×542, `AUG-25-26`×542, `OCT-25-26`×519, `JAN-25-26`×516, `DEC-25-26`×507, `Dec-24-25`×491, `SEP-25-26`×482, `JUN-25-26`×473, `APR-25-26`×471, `APR-26-27`×470, `JUL-26-27`×462, `MAY-26-27`×462, `Oct-24-25`×450, `NOV-25-26`×439, `MAR-25-26`×414, `FEB-25-26`×381, `AUG-26-27`×247, `Sep-24-25`×1
- **`UseShpdGd`** (1 values) — `N`×11,649
- **`DocSubType`** (1 values) — `--`×11,649
- **`DpmStatus`** (1 values) — `O`×11,649
- **`DpmDrawn`** (1 values) — `N`×11,649
- **`Posted`** (1 values) — `Y`×11,649
- **`OwnerCode`** (6 values) — `NULL`×11,574, `20`×53, `14`×18, `2`×2, `4`×1, `6`×1
- **`IsPaytoBnk`** (1 values) — `N`×11,649
- **`isIns`** (1 values) — `N`×11,649
- **`VersionNum`** (2 values) — `10.00.250.15`×7,644, `10.00.310.21`×4,005
- **`LangCode`** (1 values) — `8`×11,649
- **`BPNameOW`** (2 values) — `N`×11,618, `Y`×31
- **`BillToOW`** (1 values) — `N`×11,649
- **`ShipToOW`** (2 values) — `N`×11,352, `Y`×297
- **`RetInvoice`** (1 values) — `N`×11,649
- **`Model`** (1 values) — `0`×11,649
- **`UseCorrVat`** (1 values) — `N`×11,649
- **`BlkCredMmo`** (1 values) — `N`×11,649
- **`OpenForLaC`** (2 values) — `Y`×11,110, `N`×539
- **`Excised`** (1 values) — `O`×11,649
- **`DutyStatus`** (1 values) — `Y`×11,649
- **`AutoCrtFlw`** (1 values) — `N`×11,649
- **`VatJENum`** (1 values) — `-1`×11,649
- **`InsurOp347`** (1 values) — `N`×11,649
- **`IgnRelDoc`** (1 values) — `N`×11,649
- **`ResidenNum`** (1 values) — `1`×11,649
- **`PQTGrpHW`** (1 values) — `N`×11,649
- **`DocManClsd`** (2 values) — `N`×11,439, `Y`×210
- **`ClosingOpt`** (1 values) — `1`×11,649
- **`Ordered`** (1 values) — `N`×11,649
- **`NTSApprov`** (1 values) — `N`×11,649
- **`PayDuMonth`** (1 values) — `N`×11,649
- **`ExtraDays`** (9 values) — `0`×5,444, `30`×3,079, `25`×1,369, `21`×682, `15`×550, `35`×235, `5`×135, `10`×107, `7`×48
- **`EDocGenTyp`** (1 values) — `N`×11,649
- **`OnlineQuo`** (1 values) — `N`×11,649
- **`EDocStatus`** (1 values) — `C`×11,649
- **`EDocProces`** (1 values) — `C`×11,649
- **`EDocCancel`** (1 values) — `N`×11,649
- **`EDocTest`** (1 values) — `N`×11,649
- **`DpmAsDscnt`** (1 values) — `N`×11,649
- **`GTSRlvnt`** (1 values) — `N`×11,649
- **`BaseDiscPr`** (16 values) — `0.000000`×11,624, `NULL`×10, `-0.196564`×2, `0.001055`×1, `0.002190`×1, `0.003614`×1, `0.004160`×1, `-0.000684`×1, `0.001243`×1, `0.000529`×1, `-0.000057`×1, `0.003082`×1, `1.950000`×1, `0.000271`×1, `0.299103`×1, `0.007739`×1
- **`SrvTaxRule`** (1 values) — `N`×11,649
- **`AssetDate`** (6 values) — `NULL`×11,633, `2025-06-26 00:00:00.0000000`×8, `2024-12-10 00:00:00.0000000`×5, `2024-10-22 00:00:00.0000000`×1, `2025-06-23 00:00:00.0000000`×1, `2025-01-11 00:00:00.0000000`×1
- **`Notify`** (2 values) — `NULL`×8,582, `N`×3,067
- **`ReqType`** (1 values) — `12`×11,649
- **`OriginType`** (1 values) — `M`×11,649
- **`IsReuseNum`** (1 values) — `N`×11,649
- **`IsReuseNFN`** (1 values) — `N`×11,649
- **`DocDlvry`** (1 values) — `0`×11,649
- **`EnvTypeNFe`** (1 values) — `-1`×11,649
- **`IsAlt`** (1 values) — `N`×11,649
- **`AltBaseTyp`** (1 values) — `-1`×11,649
- **`PrintSEPA`** (1 values) — `N`×11,649
- **`RelatedTyp`** (1 values) — `-1`×11,649
- **`PoDropPrss`** (1 values) — `N`×11,649
- **`ExclTaxRep`** (1 values) — `N`×11,649
- **`Revision`** (1 values) — `N`×11,649
- **`GSTTranTyp`** (2 values) — `GA`×9,440, `--`×2,209
- **`BaseType`** (1 values) — `-1`×11,649
- **`ComTrade`** (1 values) — `E`×11,649
- **`UseBilAddr`** (2 values) — `N`×9,623, `Y`×2,026
- **`IssReason`** (1 values) — `1`×11,649
- **`ComTradeRt`** (1 values) — `N`×11,649
- **`SplitPmnt`** (1 values) — `N`×11,649
- **`SelfPosted`** (1 values) — `N`×11,649
- **`DPPStatus`** (1 values) — `N`×11,649
- **`EWBGenType`** (2 values) — `N`×6,426, `L`×5,223
- **`EDocType`** (1 values) — `F`×11,649
- **`AggregDoc`** (1 values) — `N`×11,649
- **`ShipPlace`** (4 values) — `NULL`×11,638, `DL`×6, `HR`×4, `PB`×1
- **`IndFinal`** (1 values) — `N`×11,649
- **`PostPmntWT`** (1 values) — `N`×11,649
- **`FCEPmnMean`** (1 values) — `N`×11,649
- **`NotRel4MI`** (1 values) — `N`×11,649
- **`Rel4PPTax`** (1 values) — `N`×11,649
- **`BookeTdsBP`** (1 values) — `N`×11,649
- **`DigPayment`** (1 values) — `N`×11,649
- **`PDueMonEnd`** (1 values) — `N`×11,649
- **`RShipToOW`** (1 values) — `N`×11,649
- **`AplTaxOnFr`** (1 values) — `N`×11,649
- **`CpyDtyStts`** (1 values) — `N`×11,649
- **`U_Recv_Date`** (2 values) — `NULL`×11,647, `2024-10-03 00:00:00.0000000`×2
- **`U_delbranch`** (4 values) — `NULL`×10,883, `2`×562, `3`×149, `1`×55
- **`U_delbranchnam`** (4 values) — `NULL`×10,883, `FACTORY`×562, `PUNJAB`×149, `DELHI`×55
- **`U_TransporterInvoice`** (12 values) — `NULL`×11,638, `626050630`×1, `626060537`×1, `626050624`×1, `626060154`×1, `626070356`×1, `626050653`×1, `626070108`×1, `626050617`×1, `626050679`×1, `626050299`×1, `626060157`×1
- **`U_UNE_ACTH`** (2 values) — `NULL`×11,648, `CC30/2025-26`×1
- **`U_TotalAmt`** (13 values) — `0.000000`×11,342, `NULL`×296, `1201000.000000`×1, `16296.000000`×1, `2287400.000000`×1, `213751.000000`×1, `391499.000000`×1, `2039999.000000`×1, `2139995.000000`×1, `350004.000000`×1, `315000.000000`×1, `5537004.000000`×1, `3088702.000000`×1
