# `ORIN` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 6,434 | 470 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 4,545 | 428 | `DocDate` | 2025-01-13 → 2026-08-24 |
| BEV | 438 | 105 | `DocDate` | 2024-10-09 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 6,434 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 6,434 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 482 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 594 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 235 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 235 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 331 | |
| `NumAtCard` | NVARCHAR(200) | 52% | 39% | 19% | 10% | 56% | <1% | 3,233 | |
| `VatSum` | DECIMAL | 71% | 98% | 79% | 89% | 94% | 79% | 3,153 | |
| `DiscPrcnt` | DECIMAL | <1% | 3% | <1% | — | — | — | 26 | |
| `DiscSum` | DECIMAL | <1% | 2% | <1% | — | 1% | — | 33 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocTotal` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 3,675 | |
| `PaidToDate` | DECIMAL | 75% | 90% | 92% | 73% | 78% | 80% | 3,065 | |
| `GrosProfit` | DECIMAL | 71% | 98% | 78% | 89% | 94% | 79% | 3,213 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 6,434 | |
| `Comments` | NVARCHAR(254) | 71% | 76% | 77% | 76% | 76% | 68% | 3,428 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 265 | |
| `TransId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 6,434 | |
| `ReceiptNum` | INTEGER | 28% | 33% | 25% | 40% | 47% | 14% | 413 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 649 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 41 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 99% | 96% | 100% | 94% | 99% | 100% | 234 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatSumSy` | DECIMAL | 71% | 98% | 79% | 89% | 94% | 79% | 3,153 | |
| `DiscSumSy` | DECIMAL | <1% | 2% | <1% | — | 1% | — | 33 | |
| `DocTotalSy` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 3,675 | |
| `PaidSys` | DECIMAL | 75% | 90% | 92% | 73% | 78% | 80% | 3,065 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrosProfSy` | DECIMAL | 71% | 98% | 78% | 89% | 94% | 79% | 3,213 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 482 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 145 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 589 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 17 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | 56% | 88% | 74% | 65% | 74% | 66% | 2,660 | |
| `VatPaidSys` | DECIMAL | 56% | 88% | 74% | 65% | 74% | 66% | 2,658 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `draftKey` | INTEGER | 20% | 22% | 59% | 37% | 32% | 68% | 1,293 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 352 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 45 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 430 | |
| `RoundDif` | DECIMAL | 62% | 82% | 75% | 82% | 80% | 76% | 1,261 | |
| `RoundDifSy` | DECIMAL | 62% | 82% | 75% | 82% | 80% | 76% | 1,261 | |
| `submitted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rounding` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RevisionPo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Pick` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlockDunn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayBlock` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `MaxDscn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Reserve` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Max1099` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 4,394 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PaidSum` | DECIMAL | 57% | 70% | 53% | 60% | 48% | 44% | 2,454 | |
| `PaidSumSc` | DECIMAL | 57% | 70% | 53% | 60% | 48% | 44% | 2,454 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OwnerCode` | INTEGER | <1% | — | <1% | 2% | — | — | 3 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 411 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `LastPmnTyp` | NVARCHAR(1) | 28% | 33% | 25% | 40% | 47% | 14% | 2 | |
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
| `ReopOriDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ReopManCls` | NVARCHAR(1) | 3% | 3% | 2% | — | — | — | 1 | |
| `DocManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ClosingOpt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayDuMonth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExtraDays` | SMALLINT | 50% | 25% | 3% | 7% | 9% | <1% | 7 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 79% | 100% | 97% | 100% | 100% | 100% | 5,024 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDiscPr` | DECIMAL | <1% | 3% | <1% | — | — | — | 12 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 5,227 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 5,258 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AssetDate` | TIMESTAMP | 6% | <1% | 12% | 11% | 3% | 11% | 141 | |
| `Notify` | NVARCHAR(1) | 31% | 61% | 4% | 16% | 39% | 2% | 1 | |
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
| `RevRefNo` | NVARCHAR(100) | 60% | 51% | 81% | 81% | 68% | 77% | 2,966 | |
| `RevRefDate` | TIMESTAMP | 59% | 51% | 81% | 81% | 68% | 77% | 656 | |
| `GSTTranTyp` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ComTrade` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UseBilAddr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `IssReason` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ComTradeRt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SplitPmnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SelfPosted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EWBGenType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 8 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Address3` | NVARCHAR(254) | 22% | 25% | 39% | 100% | 100% | 100% | 13 | |
| `RShipToOW` | NVARCHAR(1) | 25% | 27% | 43% | 97% | 100% | 93% | 2 | |
| `AplTaxOnFr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Dipatch_Date` | TIMESTAMP | <1% | <1% | 15% | 2% | 7% | 12% | 46 | |
| `U_Basement` | NVARCHAR(10) | 2% | <1% | 14% | — | <1% | 6% | 1 | |
| `U_First_Floor` | NVARCHAR(10) | <1% | — | <1% | — | — | — | 2 | |
| `U_UTL_ST_ADD` | NVARCHAR(100) | <1% | <1% | 5% | <1% | <1% | 14% | 4 | |
| `U_Recv_Date` | TIMESTAMP | 4% | 1% | 5% | <1% | — | 4% | 67 | |
| `U_Ship_From` | NVARCHAR(8) | 1% | — | — | — | — | — | 4 | |
| `U_BilltyNumber` | NVARCHAR(15) | <1% | <1% | n/a | 2% | 7% | n/a | 30 | |
| `U_BiltyDate` | TIMESTAMP | <1% | <1% | 16% | 2% | 7% | 15% | 36 | |
| `U_TransporterName` | NVARCHAR(50) | <1% | <1% | 16% | 1% | 7% | 15% | 22 | |
| `U_VehicleNoM` | NVARCHAR(12) | <1% | <1% | n/a | 1% | 7% | n/a | 35 | |
| `U_DriverName` | NCLOB | <1% | — | 1% | — | — | — | 0 | |
| `U_Mob_No` | NVARCHAR(12) | <1% | <1% | 13% | 1% | 7% | 15% | 25 | |
| `U_Order_Date` | TIMESTAMP | <1% | — | — | — | — | — | 2 | |
| `U_AR_NO` | NVARCHAR(12) | — | <1% | n/a | — | — | n/a | 1 | |
| `U_UNE_AREA` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 1 | |
| `U_UNE_MLOC` | NVARCHAR(100) | <1% | <1% | — | <1% | 6% | — | 1 | |
| `U_UNE_ACTH` | NVARCHAR(100) | — | — | 99% | — | — | 100% | 0 | |
| `U_ARNO` | NVARCHAR(100) | <1% | <1% | — | <1% | — | — | 2 | |
| `U_OMS_Order_No` | INTEGER | 5% | — | 8% | — | — | — | 101 | |
| `U_SALES_PERSON` | NVARCHAR(20) | 9% | n/a | n/a | 10% | n/a | n/a | 20 | |
| `U_GRPO` | NVARCHAR(10) | <1% | n/a | n/a | <1% | n/a | n/a | 2 | |
| `U_PONo` | NVARCHAR(30) | <1% | n/a | n/a | 1% | n/a | n/a | 24 | |
| `U_MartCustomer` | NVARCHAR(200) | <1% | n/a | n/a | — | n/a | n/a | 5 | |
| `U_MartCN` | NVARCHAR(10) | 1% | n/a | n/a | — | n/a | n/a | 1 | |

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

- **`DocType`** (2 values) — `I`×4,585, `S`×1,849
- **`CANCELED`** (3 values) — `N`×6,148, `C`×143, `Y`×143
- **`Handwrtten`** (2 values) — `N`×5,168, `Y`×1,266
- **`Printed`** (2 values) — `N`×5,165, `Y`×1,269
- **`DocStatus`** (2 values) — `C`×4,751, `O`×1,683
- **`InvntSttus`** (2 values) — `O`×3,451, `C`×2,983
- **`Transfered`** (1 values) — `N`×6,434
- **`ObjType`** (1 values) — `14`×6,434
- **`DiscPrcnt`** (27 values) — `0.000000`×6,370, `0.000003`×8, `-0.000001`×8, `0.000001`×7, `-0.000004`×5, `-0.000011`×5, `NULL`×4, `-0.000002`×4, `0.000002`×3, `0.000009`×2, `-0.000005`×2, `0.000006`×1, `-0.000008`×1, `-0.000313`×1, `-0.000065`×1, `-0.000006`×1, `0.000016`×1, `-0.000003`×1, `-0.000083`×1, `0.000011`×1, `-0.000111`×1, `-0.000186`×1, `0.000007`×1, `-0.000063`×1, `0.000005`×1, `0.000031`×1, `-0.000007`×1
- **`DocCur`** (1 values) — `INR`×6,434
- **`DocRate`** (1 values) — `1.000000`×6,434
- **`GroupNum`** (10 values) — `-1`×2,851, `1`×1,846, `18`×817, `6`×380, `17`×300, `20`×200, `11`×24, `19`×12, `9`×3, `10`×1
- **`TrnspCode`** (1 values) — `-1`×6,434
- **`PartSupply`** (1 values) — `Y`×6,434
- **`Confirmed`** (1 values) — `Y`×6,434
- **`GrossBase`** (2 values) — `-6`×4,934, `-1`×1,500
- **`CreateTran`** (1 values) — `Y`×6,434
- **`SummryType`** (1 values) — `N`×6,434
- **`UpdInvnt`** (1 values) — `I`×6,434
- **`UpdCardBal`** (1 values) — `B`×6,434
- **`InvntDirec`** (1 values) — `E`×6,434
- **`ShowSCN`** (1 values) — `N`×6,434
- **`SysRate`** (1 values) — `1.000000`×6,434
- **`CurSource`** (1 values) — `L`×6,434
- **`FatherType`** (1 values) — `P`×6,434
- **`IsICT`** (1 values) — `N`×6,434
- **`VolUnit`** (1 values) — `4`×6,434
- **`WeightUnit`** (1 values) — `3`×6,434
- **`isCrin`** (1 values) — `N`×6,434
- **`FinncPriod`** (24 values) — `6`×1,266, `10`×420, `12`×376, `11`×337, `25`×333, `9`×298, `18`×286, `41`×276, `8`×267, `14`×266, `19`×239, `7`×224, `15`×216, `16`×216, `23`×212, `20`×210, `17`×155, `22`×151, `21`×146, `42`×137, `24`×131, `44`×127, `43`×90, `45`×55
- **`UserSign`** (17 values) — `20`×3,206, `1`×1,299, `25`×1,215, `24`×228, `22`×169, `19`×121, `40`×92, `21`×26, `26`×21, `47`×15, `38`×14, `37`×12, `39`×9, `23`×3, `15`×2, `27`×1, `48`×1
- **`selfInv`** (1 values) — `N`×6,434
- **`WddStatus`** (3 values) — `-`×5,171, `P`×1,262, `A`×1
- **`Exported`** (1 values) — `N`×6,434
- **`NetProc`** (1 values) — `N`×6,434
- **`submitted`** (1 values) — `N`×6,434
- **`PoPrss`** (1 values) — `N`×6,434
- **`Rounding`** (2 values) — `Y`×3,705, `N`×2,729
- **`RevisionPo`** (1 values) — `N`×6,434
- **`PickStatus`** (1 values) — `N`×6,434
- **`Pick`** (1 values) — `N`×6,434
- **`BlockDunn`** (1 values) — `N`×6,434
- **`PayBlock`** (1 values) — `N`×6,434
- **`MaxDscn`** (2 values) — `N`×6,433, `Y`×1
- **`Reserve`** (1 values) — `N`×6,434
- **`DeferrTax`** (1 values) — `N`×6,434
- **`BoeReserev`** (1 values) — `N`×6,434
- **`Installmnt`** (1 values) — `1`×6,434
- **`VATFirst`** (1 values) — `N`×6,434
- **`CEECFlag`** (2 values) — `N`×6,291, `Y`×143
- **`CtlAccount`** (12 values) — `1101005`×2,869, `1101004`×2,249, `1101001`×818, `1101006`×242, `1101012`×75, `1101015`×68, `1101008`×33, `1101013`×33, `1101007`×26, `1101009`×11, `1102002`×7, `1101002`×3
- **`BPLId`** (3 values) — `2`×3,114, `3`×1,662, `1`×1,658
- **`BPLName`** (3 values) — `FACTORY`×3,114, `PUNJAB`×1,662, `DELHI`×1,658
- **`VATRegNum`** (3 values) — `06AACCJ4223F1Z0`×3,114, `03AACCJ4223F1Z6`×1,662, `07AACCJ4223F1ZY`×1,658
- **`SumAbsId`** (1 values) — `-1`×6,434
- **`PIndicator`** (24 values) — `Sep-24-25`×1,266, `Jan-24-25`×420, `Mar-24-25`×376, `Feb-24-25`×337, `MAR-25-26`×333, `Dec-24-25`×298, `AUG-25-26`×286, `APR-26-27`×276, `Nov-24-25`×267, `APR-25-26`×266, `SEP-25-26`×239, `Oct-24-25`×224, `MAY-25-26`×216, `JUN-25-26`×216, `JAN-25-26`×212, `OCT-25-26`×210, `JUL-25-26`×155, `DEC-25-26`×151, `NOV-25-26`×146, `MAY-26-27`×137, `FEB-25-26`×131, `JUL-26-27`×127, `JUN-26-27`×90, `AUG-26-27`×55
- **`UseShpdGd`** (1 values) — `N`×6,434
- **`DocSubType`** (2 values) — `GA`×4,595, `--`×1,839
- **`DpmStatus`** (1 values) — `O`×6,434
- **`DpmDrawn`** (1 values) — `N`×6,434
- **`Posted`** (1 values) — `Y`×6,434
- **`OwnerCode`** (4 values) — `NULL`×6,397, `20`×34, `14`×2, `2`×1
- **`IsPaytoBnk`** (1 values) — `N`×6,434
- **`isIns`** (1 values) — `N`×6,434
- **`VersionNum`** (2 values) — `10.00.250.15`×4,988, `10.00.310.21`×1,446
- **`LangCode`** (1 values) — `8`×6,434
- **`BPNameOW`** (2 values) — `N`×6,432, `Y`×2
- **`BillToOW`** (2 values) — `N`×6,433, `Y`×1
- **`ShipToOW`** (2 values) — `N`×6,430, `Y`×4
- **`RetInvoice`** (1 values) — `N`×6,434
- **`Model`** (1 values) — `0`×6,434
- **`LastPmnTyp`** (3 values) — `NULL`×4,611, `R`×1,797, `V`×26
- **`UseCorrVat`** (1 values) — `N`×6,434
- **`BlkCredMmo`** (1 values) — `N`×6,434
- **`OpenForLaC`** (1 values) — `Y`×6,434
- **`Excised`** (1 values) — `O`×6,434
- **`DutyStatus`** (1 values) — `Y`×6,434
- **`AutoCrtFlw`** (1 values) — `N`×6,434
- **`VatJENum`** (1 values) — `-1`×6,434
- **`InsurOp347`** (1 values) — `N`×6,434
- **`IgnRelDoc`** (1 values) — `N`×6,434
- **`ResidenNum`** (1 values) — `1`×6,434
- **`PQTGrpHW`** (1 values) — `N`×6,434
- **`ReopOriDoc`** (2 values) — `N`×6,255, `Y`×179
- **`ReopManCls`** (2 values) — `NULL`×6,255, `Y`×179
- **`DocManClsd`** (1 values) — `N`×6,434
- **`ClosingOpt`** (1 values) — `1`×6,434
- **`Ordered`** (1 values) — `N`×6,434
- **`NTSApprov`** (1 values) — `N`×6,434
- **`PayDuMonth`** (1 values) — `N`×6,434
- **`ExtraDays`** (7 values) — `0`×3,235, `30`×1,846, `10`×817, `7`×300, `21`×200, `60`×24, `15`×12
- **`EDocGenTyp`** (1 values) — `N`×6,434
- **`OnlineQuo`** (1 values) — `N`×6,434
- **`EDocStatus`** (1 values) — `C`×6,434
- **`EDocProces`** (1 values) — `C`×6,434
- **`EDocCancel`** (1 values) — `N`×6,434
- **`EDocTest`** (1 values) — `N`×6,434
- **`DpmAsDscnt`** (1 values) — `N`×6,434
- **`GTSRlvnt`** (1 values) — `N`×6,434
- **`BaseDiscPr`** (12 values) — `0.000000`×6,410, `-0.000001`×5, `0.000002`×4, `0.000001`×3, `-0.000002`×3, `-0.000004`×2, `0.000003`×2, `0.000004`×1, `0.000012`×1, `0.000005`×1, `-0.000003`×1, `-0.000005`×1
- **`SrvTaxRule`** (1 values) — `N`×6,434
- **`Notify`** (2 values) — `NULL`×4,469, `N`×1,965
- **`ReqType`** (1 values) — `12`×6,434
- **`OriginType`** (1 values) — `M`×6,434
- **`IsReuseNum`** (1 values) — `N`×6,434
- **`IsReuseNFN`** (1 values) — `N`×6,434
- **`DocDlvry`** (1 values) — `0`×6,434
- **`EnvTypeNFe`** (1 values) — `-1`×6,434
- **`IsAlt`** (1 values) — `N`×6,434
- **`AltBaseTyp`** (1 values) — `-1`×6,434
- **`PrintSEPA`** (1 values) — `N`×6,434
- **`RelatedTyp`** (1 values) — `-1`×6,434
- **`PoDropPrss`** (1 values) — `N`×6,434
- **`ExclTaxRep`** (1 values) — `N`×6,434
- **`Revision`** (1 values) — `N`×6,434
- **`GSTTranTyp`** (2 values) — `GA`×4,595, `--`×1,839
- **`BaseType`** (1 values) — `-1`×6,434
- **`ComTrade`** (1 values) — `E`×6,434
- **`UseBilAddr`** (2 values) — `Y`×5,407, `N`×1,027
- **`IssReason`** (2 values) — `1`×6,433, `4`×1
- **`ComTradeRt`** (1 values) — `N`×6,434
- **`SplitPmnt`** (1 values) — `N`×6,434
- **`SelfPosted`** (1 values) — `N`×6,434
- **`DPPStatus`** (1 values) — `N`×6,434
- **`EWBGenType`** (2 values) — `L`×5,547, `N`×887
- **`EDocType`** (1 values) — `F`×6,434
- **`AggregDoc`** (1 values) — `N`×6,434
- **`DataVers`** (8 values) — `1`×4,401, `2`×1,804, `3`×134, `4`×79, `5`×12, `6`×2, `8`×1, `11`×1
- **`IndFinal`** (1 values) — `N`×6,434
- **`PostPmntWT`** (1 values) — `N`×6,434
- **`FCEPmnMean`** (1 values) — `N`×6,434
- **`NotRel4MI`** (1 values) — `N`×6,434
- **`Rel4PPTax`** (1 values) — `N`×6,434
- **`BookeTdsBP`** (1 values) — `N`×6,434
- **`DigPayment`** (1 values) — `N`×6,434
- **`PDueMonEnd`** (1 values) — `N`×6,434
- **`RShipToOW`** (3 values) — `NULL`×4,808, `N`×1,621, `Y`×5
- **`AplTaxOnFr`** (1 values) — `N`×6,434
- **`CpyDtyStts`** (1 values) — `N`×6,434
- **`U_Basement`** (2 values) — `NULL`×6,281, `Y`×153
- **`U_First_Floor`** (3 values) — `NULL`×6,401, `Y`×32, `N`×1
- **`U_Ship_From`** (5 values) — `NULL`×6,360, `PB-ST`×59, `BH-FG`×10, `DL-FG`×3, `BH-FU`×2
- **`U_BilltyNumber`** (30 values) — `NULL`×6,384, `NA`×12, `12737`×4, `.`×3, `1`×2, `JIV8`×2, `6602`×2, `5951`×2, `2768`×1, `SELF`×1, `10897`×1, `7088`×1, `1304266`×1, `6507`×1, `6047`×1, `..`×1, `2520`×1, `848060`×1, `13131`×1, `6655`×1, `13102`×1, `DEL260014`×1, `130229`×1, `1623`×1, `13143`×1, `6109`×1, `12161`×1, `520307`×1, `4785`×1, `45408`×1
- **`U_TransporterName`** (23 values) — `NULL`×6,387, `Delhi Punjab`×10, `Arnav Transport`×9, `Jivo Vehicle`×4, `AIR TRANS`×2, `ARNAV TRANSPORT SERVICE`×2, `Priya Road Carrier`×2, `NA`×2, `SELF PICKUP`×2, `SS LOGISTICS & CARRIERS`×1, `Om Logistics Ltd.`×1, `om logistics`×1, `Pick & Ship`×1, `Mahadev`×1, `Abhiman Express`×1, `Guru Nanak`×1, `Rohit Cargo`×1, `jivo vehicle`×1, `JIVO VEHICLE`×1, `SELF`×1, `Mahaveer Transport`×1, `Bombey Sri Nagar`×1, `OM LOGISTICS LTD`×1
- **`U_Mob_No`** (26 values) — `NULL`×6,400, `9729209416`×4, `9990378712`×2, `9671976908`×2, `6377479730`×2, `9899885211`×2, `9896437186`×2, `9120908161`×2, `7409558563`×1, `9718858411`×1, `8887029930`×1, `9599891437`×1, `9805378825`×1, `8930015762`×1, `8199818237`×1, `9582295755`×1, `6392566119`×1, `8376811303`×1, `8459773534`×1, `8684015172`×1, `9354218659`×1, `9956958533`×1, `9999855966`×1, `9468020665`×1, `7318074430`×1, `9517660092`×1
- **`U_Order_Date`** (3 values) — `NULL`×6,429, `2024-11-08 00:00:00.0000000`×4, `2025-07-18 00:00:00.0000000`×1
- **`U_UNE_MLOC`** (2 values) — `NULL`×6,433, `KHASRA NO 75/26 75/14 75/18/1 AMRITSAR-143109 IN`×1
- **`U_ARNO`** (3 values) — `∅`×4,675, `NULL`×1,749, `H`×10
- **`U_SALES_PERSON`** (21 values) — `NULL`×5,883, `PUNJAB MT`×206, `ECOM`×200, `PUNJAB GT`×29, `PRIVATE`×19, `TARUN`×19, `DELHI MT`×18, `HARYANA GT`×13, `HAPPY`×13, `DELHI GT`×10, `BRANCH`×4, `UP/UK GT`×3, `PRINCE OTHER`×3, `BANGLORE`×3, `FREE SAMPLE`×3, `EXPORT`×2, `HP GT`×2, `HYDERABAD`×1, `HIMACHAL`×1, `CSD`×1, `HORECA/INST`×1
- **`U_GRPO`** (3 values) — `NULL`×6,396, `Y`×33, `N`×5
- **`U_PONo`** (25 values) — `NULL`×6,394, `226224586`×5, `326224603`×3, `626224568`×3, `326224595`×2, `226224623`×2, `326224619`×2, `226224574`×2, `326224609`×2, `126224636`×2, `226224601`×2, `226224560`×2, `326224610`×1, `226224503`×1, `326224537`×1, `326224530`×1, `826224559`×1, `326224511`×1, `126224626`×1, `226224624`×1, `326224627`×1, `226224631`×1, `326224536`×1, `326224630`×1, `226224516`×1
- **`U_MartCN`** (2 values) — `NULL`×6,368, `N`×66
