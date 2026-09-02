# `OINV` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 31,084 | 2,513 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 25,752 | 4,195 | `DocDate` | 2024-10-03 → 2026-08-24 |
| BEV | 5,590 | 1,693 | `DocDate` | 2024-10-04 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 31,084 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 31,083 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 606 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 1,190 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 628 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 630 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 723 | |
| `NumAtCard` | NVARCHAR(200) | 56% | 29% | 6% | 28% | 36% | 5% | 17,257 | |
| `VatSum` | DECIMAL | 64% | 100% | 100% | 100% | 100% | 100% | 14,959 | |
| `DiscPrcnt` | DECIMAL | <1% | 6% | <1% | — | — | — | 53 | |
| `DiscSum` | DECIMAL | <1% | 6% | <1% | — | — | — | 114 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `DocTotal` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 18,315 | |
| `DocTotalFC` | DECIMAL | <1% | — | — | — | — | — | 8 | |
| `PaidToDate` | DECIMAL | 64% | 84% | 83% | 60% | 60% | 64% | 13,984 | |
| `PaidFC` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `GrosProfit` | DECIMAL | 62% | 99% | 99% | 96% | 97% | 99% | 15,124 | |
| `GrosProfFC` | DECIMAL | <1% | — | — | — | — | — | 8 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 31,083 | |
| `Comments` | NVARCHAR(254) | 92% | 99% | 98% | 97% | 100% | 99% | 16,190 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 723 | |
| `TransId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 31,078 | |
| `ReceiptNum` | INTEGER | 33% | 62% | 44% | 31% | 53% | 32% | 2,156 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 910 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 66 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 96% | 97% | 98% | 98% | 100% | 99% | 617 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `VatSumSy` | DECIMAL | 64% | 100% | 100% | 100% | 100% | 100% | 14,959 | |
| `DiscSumSy` | DECIMAL | <1% | 6% | <1% | — | — | — | 114 | |
| `DocTotalSy` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 18,315 | |
| `PaidSys` | DECIMAL | 64% | 84% | 83% | 60% | 60% | 64% | 13,984 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrosProfSy` | DECIMAL | 62% | 99% | 99% | 96% | 97% | 99% | 15,124 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 604 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 139 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 1,093 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | 51% | 84% | 83% | 60% | 60% | 64% | 12,427 | |
| `VatPaidSys` | DECIMAL | 51% | 84% | 84% | 60% | 60% | 66% | 12,433 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `draftKey` | INTEGER | 27% | 14% | 88% | 87% | 18% | 88% | 8,402 | |
| `TotalExpns` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `TotalExpSC` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 805 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 85 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 981 | |
| `RoundDif` | DECIMAL | 52% | 84% | 96% | 71% | 81% | 95% | 4,886 | |
| `RoundDifFC` | DECIMAL | <1% | — | — | — | — | — | 3 | |
| `RoundDifSy` | DECIMAL | 52% | 84% | 96% | 71% | 81% | 95% | 4,886 | |
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
| `Max1099` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 21,483 | |
| `ExpAppl` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `ExpApplSC` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 18 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PaidSum` | DECIMAL | 61% | 80% | 77% | 56% | 54% | 61% | 13,630 | |
| `PaidSumSc` | DECIMAL | 61% | 80% | 77% | 56% | 54% | 61% | 13,630 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OwnerCode` | INTEGER | 3% | — | <1% | 16% | — | 2% | 3 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 895 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxOnExp` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `TaxOnExpSc` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `TaxOnExAp` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `TaxOnExApS` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `LastPmnTyp` | NVARCHAR(1) | 33% | 62% | 44% | 31% | 53% | 32% | 2 | |
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
| `DocManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ClosingOpt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayDuMonth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExtraDays` | SMALLINT | 38% | 17% | 5% | 11% | 2% | 11% | 8 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 31% | 31% | 71% | 43% | 77% | 65% | 9,495 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDiscPr` | DECIMAL | <1% | — | <1% | — | — | — | 32 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 18,990 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 18,761 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AssetDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 606 | |
| `Notify` | NVARCHAR(1) | 12% | 50% | 1% | 7% | 45% | <1% | 1 | |
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
| `RevRefNo` | NVARCHAR(100) | <1% | <1% | — | <1% | <1% | — | 19 | |
| `RevRefDate` | TIMESTAMP | <1% | <1% | — | <1% | <1% | — | 18 | |
| `GSTTranTyp` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseEntry` | INTEGER | <1% | <1% | <1% | 1% | 2% | <1% | 177 | |
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
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 17 | |
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
| `U_Dipatch_Date` | TIMESTAMP | 34% | 4% | 85% | 76% | 24% | 88% | 625 | |
| `U_Basement` | NVARCHAR(10) | 15% | <1% | 31% | <1% | <1% | <1% | 2 | |
| `U_First_Floor` | NVARCHAR(10) | 5% | <1% | 5% | — | <1% | — | 2 | |
| `U_GenType` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_UTL_ST_ADD` | NVARCHAR(100) | 2% | <1% | 34% | 3% | 3% | 77% | 238 | |
| `U_Recv_Date` | TIMESTAMP | 29% | 3% | 69% | 38% | <1% | 64% | 418 | |
| `U_deldocnum` | NVARCHAR(100) | <1% | — | — | — | — | — | 1 | |
| `U_deldocdate` | TIMESTAMP | <1% | — | <1% | — | — | — | 1 | |
| `U_delbranch` | NVARCHAR(100) | 2% | <1% | 1% | — | — | — | 3 | |
| `U_delbranchnam` | NVARCHAR(100) | 2% | <1% | 1% | — | — | — | 3 | |
| `U_GRNdocentry` | INTEGER | 2% | <1% | <1% | — | — | — | 741 | |
| `U_GRNCardCode` | NVARCHAR(15) | 2% | <1% | 1% | — | — | — | 4 | |
| `U_GRNWhsCode` | NVARCHAR(8) | 2% | <1% | 1% | — | — | — | 13 | |
| `U_Ship_From` | NVARCHAR(8) | 3% | <1% | — | — | — | — | 15 | |
| `U_BilltyNumber` | NVARCHAR(15) | 30% | 4% | n/a | 71% | 24% | n/a | 4,088 | |
| `U_BiltyDate` | TIMESTAMP | 29% | 4% | 80% | 69% | 24% | 88% | 628 | |
| `U_TransporterName` | NVARCHAR(50) | 29% | 4% | 77% | 66% | 24% | 83% | 234 | |
| `U_VehicleNoM` | NVARCHAR(12) | 28% | 4% | n/a | 62% | 24% | n/a | 1,139 | |
| `U_DriverName` | NCLOB | 2% | <1% | 3% | <1% | — | — | 0 | |
| `U_TransporterInvoice` | NVARCHAR(15) | <1% | <1% | — | — | <1% | — | 1 | |
| `U_Mob_No` | NVARCHAR(12) | 20% | 4% | 61% | 54% | 24% | 82% | 844 | |
| `U_Order_Date` | TIMESTAMP | 2% | <1% | 1% | 9% | <1% | 3% | 25 | |
| `U_AR_NO` | NVARCHAR(12) | <1% | <1% | n/a | — | — | n/a | 2 | |
| `U_InvRevEntry` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_LRNUmber` | NVARCHAR(15) | <1% | <1% | n/a | — | <1% | n/a | 11 | |
| `U_BOEDate` | TIMESTAMP | <1% | <1% | n/a | — | <1% | n/a | 10 | |
| `U_UNE_TOTL` | DECIMAL | <1% | — | — | <1% | — | — | 2 | |
| `U_UNE_AREA` | NVARCHAR(100) | <1% | <1% | — | <1% | <1% | — | 17 | |
| `U_UNE_MLOC` | NVARCHAR(100) | <1% | 3% | <1% | <1% | 20% | — | 18 | |
| `U_UNE_ACTH` | NVARCHAR(100) | <1% | <1% | 98% | <1% | 2% | 100% | 3 | |
| `U_TotalAmt` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `U_BiltAmt` | DECIMAL | <1% | — | — | — | — | — | 3 | |
| `U_ARNO` | NVARCHAR(100) | <1% | <1% | 2% | 6% | — | 6% | 4 | |
| `U_OMS_Order_No` | INTEGER | 15% | — | 29% | <1% | — | 3% | 668 | |
| `U_DisDE` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_DisDN` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_SALES_PERSON` | NVARCHAR(20) | 27% | n/a | n/a | 93% | n/a | n/a | 22 | |
| `U_GRPO` | NVARCHAR(10) | 2% | n/a | n/a | 2% | n/a | n/a | 2 | |
| `U_PONo` | NVARCHAR(30) | 3% | n/a | n/a | 18% | n/a | n/a | 570 | |
| `U_MartCustomer` | NVARCHAR(200) | <1% | n/a | n/a | — | n/a | n/a | 13 | |
| `U_OMS_REF` | NVARCHAR(15) | <1% | n/a | n/a | <1% | n/a | n/a | 1 | |

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

- **`DocType`** (2 values) — `I`×19,585, `S`×11,499
- **`CANCELED`** (3 values) — `N`×30,444, `C`×320, `Y`×320
- **`Handwrtten`** (2 values) — `N`×20,006, `Y`×11,078
- **`Printed`** (2 values) — `N`×19,823, `Y`×11,261
- **`DocStatus`** (2 values) — `C`×18,028, `O`×13,056
- **`InvntSttus`** (2 values) — `O`×18,637, `C`×12,447
- **`Transfered`** (1 values) — `N`×31,084
- **`ObjType`** (1 values) — `13`×31,084
- **`DocCur`** (2 values) — `INR`×31,075, `USD`×9
- **`DocRate`** (7 values) — `1.000000`×31,075, `86.100000`×4, `84.700000`×1, `85.950000`×1, `85.400000`×1, `86.050000`×1, `86.700000`×1
- **`DocTotalFC`** (8 values) — `0.000000`×31,075, `211382.250000`×3, `134738.000000`×1, `342439.500000`×1, `132240.600000`×1, `131839.650000`×1, `420146.000000`×1, `52695.750000`×1
- **`PaidFC`** (2 values) — `0.000000`×31,082, `211382.250000`×2
- **`GrosProfFC`** (9 values) — `0.000000`×27,936, `NULL`×3,139, `211382.250000`×3, `131839.650000`×1, `134737.500000`×1, `420146.430000`×1, `342439.500000`×1, `132240.600000`×1, `52695.750000`×1
- **`GroupNum`** (12 values) — `-1`×16,185, `18`×4,599, `17`×3,081, `6`×2,993, `1`×2,562, `20`×819, `11`×694, `19`×84, `10`×41, `9`×12, `14`×10, `29`×4
- **`TrnspCode`** (1 values) — `-1`×31,084
- **`PartSupply`** (1 values) — `Y`×31,084
- **`Confirmed`** (1 values) — `Y`×31,084
- **`GrossBase`** (2 values) — `-6`×18,307, `-1`×12,777
- **`CreateTran`** (1 values) — `Y`×31,084
- **`SummryType`** (1 values) — `N`×31,084
- **`UpdInvnt`** (1 values) — `I`×31,084
- **`UpdCardBal`** (1 values) — `B`×31,084
- **`InvntDirec`** (1 values) — `X`×31,084
- **`ShowSCN`** (1 values) — `N`×31,084
- **`SysRate`** (1 values) — `1.000000`×31,084
- **`CurSource`** (2 values) — `L`×31,075, `C`×9
- **`FatherType`** (1 values) — `P`×31,084
- **`IsICT`** (1 values) — `N`×31,084
- **`VolUnit`** (1 values) — `4`×31,084
- **`WeightUnit`** (2 values) — `3`×31,055, `2`×29
- **`isCrin`** (1 values) — `N`×31,084
- **`FinncPriod`** (24 values) — `6`×11,078, `9`×1,916, `7`×1,343, `8`×1,334, `10`×1,158, `20`×998, `23`×973, `17`×873, `19`×861, `18`×861, `15`×818, `24`×817, `22`×815, `12`×781, `21`×757, `14`×749, `44`×730, `16`×709, `25`×694, `42`×692, `11`×689, `41`×527, `43`×474, `45`×437
- **`UserSign`** (23 values) — `1`×11,158, `22`×8,904, `25`×3,624, `24`×2,609, `21`×1,301, `35`×1,017, `19`×790, `37`×784, `20`×158, `40`×149, `15`×140, `26`×116, `38`×113, `39`×77, `27`×36, `2`×28, `47`×27, `10`×24, `49`×9, `56`×9, `52`×8, `33`×2, `23`×1
- **`selfInv`** (1 values) — `N`×31,084
- **`WddStatus`** (3 values) — `-`×22,712, `P`×8,370, `A`×2
- **`TotalExpns`** (2 values) — `0.000000`×31,081, `7500.000000`×3
- **`TotalExpSC`** (2 values) — `0.000000`×31,081, `7500.000000`×3
- **`Exported`** (1 values) — `N`×31,084
- **`NetProc`** (1 values) — `N`×31,084
- **`RoundDifFC`** (3 values) — `0.000000`×31,082, `-0.430000`×1, `0.500000`×1
- **`submitted`** (1 values) — `N`×31,084
- **`PoPrss`** (1 values) — `N`×31,084
- **`Rounding`** (2 values) — `N`×15,891, `Y`×15,193
- **`RevisionPo`** (1 values) — `N`×31,084
- **`PickStatus`** (1 values) — `N`×31,084
- **`Pick`** (1 values) — `N`×31,084
- **`BlockDunn`** (1 values) — `N`×31,084
- **`PayBlock`** (1 values) — `N`×31,084
- **`MaxDscn`** (1 values) — `N`×31,084
- **`Reserve`** (1 values) — `N`×31,084
- **`ExpAppl`** (2 values) — `0.000000`×31,082, `7500.000000`×2
- **`ExpApplSC`** (2 values) — `0.000000`×31,082, `7500.000000`×2
- **`DeferrTax`** (1 values) — `N`×31,084
- **`BoeReserev`** (1 values) — `N`×31,084
- **`Installmnt`** (1 values) — `1`×31,084
- **`VATFirst`** (1 values) — `N`×31,084
- **`CEECFlag`** (2 values) — `N`×29,898, `Y`×1,186
- **`CtlAccount`** (18 values) — `1101005`×15,988, `1101001`×4,659, `1101004`×3,413, `1101008`×1,360, `1101014`×1,080, `1101006`×827, `1101013`×749, `1101015`×691, `1102003`×556, `1101012`×514, `1101009`×491, `1102005`×266, `1101007`×191, `1102001`×169, `1102002`×65, `1101010`×40, `1101002`×24, `1101011`×1
- **`BPLId`** (4 values) — `2`×15,016, `1`×13,458, `3`×2,596, `7`×14
- **`BPLName`** (7 values) — `FACTORY`×14,994, `DELHI`×13,444, `PUNJAB`×2,580, `Factory`×22, `Punjab`×16, `Delhi`×14, `DELHI INFO`×14
- **`VATRegNum`** (3 values) — `06AACCJ4223F1Z0`×15,016, `07AACCJ4223F1ZY`×13,472, `03AACCJ4223F1Z6`×2,596
- **`SumAbsId`** (1 values) — `-1`×31,084
- **`PIndicator`** (24 values) — `Sep-24-25`×11,078, `Dec-24-25`×1,916, `Oct-24-25`×1,343, `Nov-24-25`×1,334, `Jan-24-25`×1,158, `OCT-25-26`×998, `JAN-25-26`×973, `JUL-25-26`×873, `AUG-25-26`×861, `SEP-25-26`×861, `MAY-25-26`×818, `FEB-25-26`×817, `DEC-25-26`×815, `Mar-24-25`×781, `NOV-25-26`×757, `APR-25-26`×749, `JUL-26-27`×730, `JUN-25-26`×709, `MAR-25-26`×694, `MAY-26-27`×692, `Feb-24-25`×689, `APR-26-27`×527, `JUN-26-27`×474, `AUG-26-27`×437
- **`UseShpdGd`** (1 values) — `N`×31,084
- **`DocSubType`** (3 values) — `GA`×19,982, `--`×11,078, `GD`×24
- **`DpmStatus`** (1 values) — `O`×31,084
- **`DpmDrawn`** (1 values) — `N`×31,084
- **`Posted`** (1 values) — `Y`×31,084
- **`OwnerCode`** (4 values) — `NULL`×30,238, `20`×809, `2`×27, `14`×10
- **`IsPaytoBnk`** (1 values) — `N`×31,084
- **`isIns`** (1 values) — `N`×31,084
- **`VersionNum`** (2 values) — `10.00.250.15`×25,193, `10.00.310.21`×5,891
- **`LangCode`** (1 values) — `8`×31,084
- **`BPNameOW`** (2 values) — `N`×31,076, `Y`×8
- **`BillToOW`** (2 values) — `N`×31,080, `Y`×4
- **`ShipToOW`** (2 values) — `N`×31,075, `Y`×9
- **`RetInvoice`** (1 values) — `N`×31,084
- **`Model`** (1 values) — `0`×31,084
- **`TaxOnExp`** (2 values) — `0.000000`×31,081, `375.000000`×3
- **`TaxOnExpSc`** (2 values) — `0.000000`×31,081, `375.000000`×3
- **`TaxOnExAp`** (2 values) — `0.000000`×31,082, `375.000000`×2
- **`TaxOnExApS`** (2 values) — `0.000000`×31,082, `375.000000`×2
- **`LastPmnTyp`** (3 values) — `NULL`×20,768, `R`×10,238, `V`×78
- **`UseCorrVat`** (1 values) — `N`×31,084
- **`BlkCredMmo`** (1 values) — `N`×31,084
- **`OpenForLaC`** (1 values) — `Y`×31,084
- **`Excised`** (1 values) — `O`×31,084
- **`DutyStatus`** (1 values) — `Y`×31,084
- **`AutoCrtFlw`** (1 values) — `N`×31,084
- **`VatJENum`** (1 values) — `-1`×31,084
- **`InsurOp347`** (1 values) — `N`×31,084
- **`IgnRelDoc`** (1 values) — `N`×31,084
- **`ResidenNum`** (1 values) — `1`×31,084
- **`PQTGrpHW`** (1 values) — `N`×31,084
- **`DocManClsd`** (1 values) — `N`×31,084
- **`ClosingOpt`** (1 values) — `1`×31,084
- **`Ordered`** (1 values) — `N`×31,084
- **`NTSApprov`** (1 values) — `N`×31,084
- **`PayDuMonth`** (1 values) — `N`×31,084
- **`ExtraDays`** (8 values) — `0`×19,235, `10`×4,599, `7`×3,081, `30`×2,562, `21`×819, `60`×694, `15`×84, `2`×10
- **`EDocGenTyp`** (1 values) — `N`×31,084
- **`OnlineQuo`** (1 values) — `N`×31,084
- **`EDocStatus`** (1 values) — `C`×31,084
- **`EDocProces`** (1 values) — `C`×31,084
- **`EDocCancel`** (1 values) — `N`×31,084
- **`EDocTest`** (1 values) — `N`×31,084
- **`DpmAsDscnt`** (1 values) — `N`×31,084
- **`GTSRlvnt`** (1 values) — `N`×31,084
- **`SrvTaxRule`** (1 values) — `N`×31,084
- **`Notify`** (2 values) — `NULL`×27,253, `N`×3,831
- **`ReqType`** (1 values) — `12`×31,084
- **`OriginType`** (1 values) — `M`×31,084
- **`IsReuseNum`** (1 values) — `N`×31,084
- **`IsReuseNFN`** (1 values) — `N`×31,084
- **`DocDlvry`** (1 values) — `0`×31,084
- **`EnvTypeNFe`** (1 values) — `-1`×31,084
- **`IsAlt`** (1 values) — `N`×31,084
- **`AltBaseTyp`** (1 values) — `-1`×31,084
- **`PrintSEPA`** (1 values) — `N`×31,084
- **`RelatedTyp`** (1 values) — `-1`×31,084
- **`PoDropPrss`** (1 values) — `N`×31,084
- **`ExclTaxRep`** (1 values) — `N`×31,084
- **`Revision`** (1 values) — `N`×31,084
- **`RevRefNo`** (20 values) — `NULL`×31,060, `626060319`×3, `625011023`×2, `625012504`×2, `607265907`×2, `625100209`×1, `624101500`×1, `625110324`×1, `624111743`×1, `625022512`×1, `325092542`×1, `FM`×1, `626010850`×1, `607265909`×1, `626030474`×1, `625011718`×1, `625110346`×1, `625062540`×1, `625102522`×1, `OCT`×1
- **`RevRefDate`** (19 values) — `NULL`×31,060, `2026-06-15 00:00:00.0000000`×3, `2026-07-22 00:00:00.0000000`×3, `2025-01-03 00:00:00.0000000`×2, `2025-01-02 00:00:00.0000000`×2, `2026-03-25 00:00:00.0000000`×1, `2025-06-10 00:00:00.0000000`×1, `2025-11-17 00:00:00.0000000`×1, `2025-10-09 00:00:00.0000000`×1, `2025-01-31 00:00:00.0000000`×1, `2025-02-07 00:00:00.0000000`×1, `2026-01-31 00:00:00.0000000`×1, `2024-09-10 00:00:00.0000000`×1, `2025-11-13 00:00:00.0000000`×1, `2024-11-30 00:00:00.0000000`×1, `2024-11-11 00:00:00.0000000`×1, `2025-09-25 00:00:00.0000000`×1, `2025-10-08 00:00:00.0000000`×1, `2024-10-28 00:00:00.0000000`×1
- **`GSTTranTyp`** (3 values) — `GA`×19,982, `--`×11,078, `GD`×24
- **`BaseType`** (2 values) — `-1`×30,886, `67`×198
- **`ComTrade`** (1 values) — `E`×31,084
- **`UseBilAddr`** (2 values) — `Y`×25,495, `N`×5,589
- **`IssReason`** (1 values) — `1`×31,084
- **`ComTradeRt`** (1 values) — `N`×31,084
- **`SplitPmnt`** (1 values) — `N`×31,084
- **`SelfPosted`** (1 values) — `N`×31,084
- **`DPPStatus`** (1 values) — `N`×31,084
- **`EWBGenType`** (2 values) — `L`×17,952, `N`×13,132
- **`EDocType`** (1 values) — `F`×31,084
- **`AggregDoc`** (1 values) — `N`×31,084
- **`DataVers`** (17 values) — `1`×15,184, `3`×4,851, `2`×4,817, `4`×3,874, `5`×998, `6`×581, `7`×458, `8`×164, `9`×78, `10`×32, `11`×18, `13`×14, `12`×7, `17`×2, `15`×2, `16`×2, `14`×2
- **`IndFinal`** (1 values) — `N`×31,084
- **`PostPmntWT`** (1 values) — `N`×31,084
- **`FCEPmnMean`** (1 values) — `N`×31,084
- **`NotRel4MI`** (1 values) — `N`×31,084
- **`Rel4PPTax`** (1 values) — `N`×31,084
- **`BookeTdsBP`** (1 values) — `N`×31,084
- **`DigPayment`** (1 values) — `N`×31,084
- **`PDueMonEnd`** (1 values) — `N`×31,084
- **`RShipToOW`** (2 values) — `N`×30,664, `Y`×420
- **`AplTaxOnFr`** (1 values) — `N`×31,084
- **`CpyDtyStts`** (1 values) — `N`×31,084
- **`U_Basement`** (3 values) — `NULL`×26,500, `Y`×4,511, `N`×73
- **`U_First_Floor`** (3 values) — `NULL`×29,505, `Y`×1,521, `N`×58
- **`U_GenType`** (2 values) — `NULL`×31,081, `N`×3
- **`U_deldocnum`** (2 values) — `NULL`×31,083, `1524121043`×1
- **`U_deldocdate`** (2 values) — `NULL`×31,083, `2024-12-03 00:00:00.0000000`×1
- **`U_delbranch`** (4 values) — `NULL`×30,310, `3`×460, `2`×194, `1`×120
- **`U_delbranchnam`** (4 values) — `NULL`×30,310, `PUNJAB`×460, `FACTORY`×194, `DELHI`×120
- **`U_GRNCardCode`** (5 values) — `NULL`×30,310, `VENDA000003`×576, `VENDA000002`×149, `VENDA000004`×45, `VENDA001004`×4
- **`U_GRNWhsCode`** (14 values) — `NULL`×30,310, `PB-ST`×293, `BH-GR`×134, `PB-SP`×109, `DL-FG`×92, `PB-JP`×56, `BH-FG`×48, `DL-PS`×23, `BH-LR`×6, `BH-FU`×5, `DL-J3`×5, `PB-SG`×1, `PB-RG`×1, `BH-PS`×1
- **`U_Ship_From`** (16 values) — `NULL`×30,078, `BH-FG`×438, `PB-ST`×284, `PB-JP`×108, `BH-FU`×89, `DL-FG`×35, `DL-PS`×18, `DL-J3`×10, `PB-SP`×7, `GP-FG`×5, `BH-PS`×3, `DL-GR`×3, `BH-OT`×3, `PB-RG`×1, `∅`×1, `PB-PS`×1
- **`U_TransporterInvoice`** (2 values) — `NULL`×31,083, `.`×1
- **`U_Order_Date`** (26 values) — `NULL`×30,446, `2026-07-22 00:00:00.0000000`×68, `2026-06-17 00:00:00.0000000`×54, `2026-05-25 00:00:00.0000000`×53, `2026-04-17 00:00:00.0000000`×49, `2026-03-20 00:00:00.0000000`×39, `2025-09-30 00:00:00.0000000`×26, `2025-02-28 00:00:00.0000000`×25, `2025-04-23 00:00:00.0000000`×25, `2025-08-29 00:00:00.0000000`×24, `2025-05-23 00:00:00.0000000`×24, `2026-01-23 00:00:00.0000000`×23, `2025-07-18 00:00:00.0000000`×23, `2025-12-26 00:00:00.0000000`×22, `2025-06-26 00:00:00.0000000`×22, `2025-04-01 00:00:00.0000000`×22, `2025-10-16 00:00:00.0000000`×22, `2025-11-20 00:00:00.0000000`×21, `2025-02-07 00:00:00.0000000`×21, `2026-02-16 00:00:00.0000000`×20, `2025-01-06 00:00:00.0000000`×19, `2024-11-08 00:00:00.0000000`×12, `2024-12-10 00:00:00.0000000`×11, `2024-09-27 00:00:00.0000000`×11, `2025-05-30 00:00:00.0000000`×1, `2025-01-27 00:00:00.0000000`×1
- **`U_AR_NO`** (3 values) — `∅`×23,186, `NULL`×7,874, `T`×24
- **`U_InvRevEntry`** (2 values) — `NULL`×31,082, `AEL1823134`×2
- **`U_LRNUmber`** (12 values) — `NULL`×31,041, `8568599`×10, `8562896`×10, `8072845`×7, `8890469`×6, `9081998`×3, `9094228`×2, `8222231`×1, `8530178`×1, `1325575`×1, `7597874`×1, `9116436`×1
- **`U_BOEDate`** (11 values) — `NULL`×31,043, `2025-02-26 00:00:00.0000000`×11, `2025-02-25 00:00:00.0000000`×10, `2025-01-29 00:00:00.0000000`×7, `2025-03-14 00:00:00.0000000`×4, `2025-03-17 00:00:00.0000000`×3, `2025-03-25 00:00:00.0000000`×2, `2025-04-28 00:00:00.0000000`×1, `2025-02-16 00:00:00.0000000`×1, `2025-01-03 00:00:00.0000000`×1, `2025-03-18 00:00:00.0000000`×1
- **`U_UNE_TOTL`** (3 values) — `0.000000`×30,844, `NULL`×239, `626070136.000000`×1
- **`U_UNE_ACTH`** (4 values) — `NULL`×30,906, `1102007`×176, `1102001`×1, `T`×1
- **`U_TotalAmt`** (3 values) — `0.000000`×30,660, `NULL`×423, `4000.000000`×1
- **`U_BiltAmt`** (4 values) — `0.000000`×30,660, `NULL`×420, `2220.000000`×3, `4184.000000`×1
- **`U_ARNO`** (5 values) — `∅`×23,171, `NULL`×7,617, `H`×215, `T`×77, `h`×4
- **`U_DisDE`** (2 values) — `NULL`×31,083, `.`×1
- **`U_DisDN`** (2 values) — `NULL`×31,083, `.`×1
- **`U_SALES_PERSON`** (23 values) — `NULL`×22,817, `ECOM`×2,527, `PUNJAB MT`×1,012, `PUNJAB GT`×816, `PRIVATE`×782, `DELHI GT`×587, `CASH SALE`×455, `CSD`×403, `HARYANA GT`×386, `PRINCE OTHER`×253, `HAPPY`×222, `UP/UK GT`×178, `TARUN`×126, `HORECA/INST`×121, `DELHI MT`×121, `FREE SAMPLE`×82, `BRANCH`×57, `EXPORT`×38, `HIMACHAL`×33, `ROI`×26, `BANGLORE`×16, `HYDERABAD`×14, `HP GT`×12
- **`U_GRPO`** (3 values) — `NULL`×30,533, `Y`×520, `N`×31
- **`U_OMS_REF`** (2 values) — `NULL`×31,083, `mrabl7uf0l90cnc`×1
