# `ORPD` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 117 | 37 | `DocDate` | 2024-10-10 → 2026-08-19 |
| MART | 59 | 4 | `DocDate` | 2025-06-03 → 2026-07-07 |
| BEV | 33 | 10 | `DocDate` | 2024-12-16 → 2026-08-11 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 117 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 117 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 94 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 94 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 32 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 32 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 31 | |
| `NumAtCard` | NVARCHAR(200) | 89% | 19% | 70% | 95% | 50% | 80% | 96 | |
| `VatSum` | DECIMAL | 100% | 100% | 91% | 100% | 100% | 100% | 103 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocTotal` | DECIMAL | 100% | 100% | 94% | 100% | 100% | 100% | 103 | |
| `PaidToDate` | DECIMAL | 94% | 75% | 85% | 89% | 50% | 90% | 97 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 117 | |
| `Comments` | NVARCHAR(254) | 83% | 90% | 76% | 86% | 50% | 90% | 86 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 38 | |
| `TransId` | INTEGER | 97% | 100% | 100% | 95% | 100% | 100% | 113 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 103 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 9 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 86% | 100% | 91% | 97% | 100% | 100% | 28 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatSumSy` | DECIMAL | 100% | 100% | 91% | 100% | 100% | 100% | 103 | |
| `DocTotalSy` | DECIMAL | 100% | 100% | 94% | 100% | 100% | 100% | 103 | |
| `PaidSys` | DECIMAL | 94% | 75% | 85% | 89% | 50% | 90% | 97 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 92 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 22 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 94 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 22 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | 86% | 75% | 73% | 76% | 50% | 60% | 88 | |
| `VatPaidSys` | DECIMAL | 86% | 75% | 73% | 76% | 50% | 60% | 88 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `draftKey` | INTEGER | 84% | 37% | 61% | 86% | 50% | 80% | 98 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 15 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 27 | |
| `RoundDif` | DECIMAL | 77% | 73% | 61% | 92% | 75% | 70% | 64 | |
| `RoundDifSy` | DECIMAL | 77% | 73% | 61% | 92% | 75% | 70% | 64 | |
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
| `Max1099` | DECIMAL | 100% | 100% | 94% | 100% | 100% | 100% | 103 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 22 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 27 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
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
| `ReopOriDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ReopManCls` | NVARCHAR(1) | 2% | 2% | — | — | — | — | 1 | |
| `DocManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ClosingOpt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayDuMonth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExtraDays` | SMALLINT | 58% | 5% | 39% | 51% | — | 50% | 7 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 55% | 22% | 24% | 73% | 75% | 50% | 60 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 117 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 117 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AssetDate` | TIMESTAMP | <1% | — | — | — | — | — | 1 | |
| `Notify` | NVARCHAR(1) | 3% | 5% | — | 8% | — | — | 1 | |
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
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RShipToCod` | NVARCHAR(50) | 57% | 20% | 36% | 100% | 100% | 100% | 20 | |
| `Address3` | NVARCHAR(254) | 57% | 20% | 36% | 100% | 100% | 100% | 21 | |
| `RShipToOW` | NVARCHAR(1) | 61% | 37% | 67% | 100% | 100% | 100% | 1 | |
| `AplTaxOnFr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_ACTH` | NVARCHAR(100) | — | — | 100% | — | — | 100% | 0 | |

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

- **`DocType`** (1 values) — `I`×117
- **`CANCELED`** (3 values) — `N`×103, `C`×7, `Y`×7
- **`Handwrtten`** (1 values) — `N`×117
- **`Printed`** (2 values) — `N`×100, `Y`×17
- **`DocStatus`** (2 values) — `C`×109, `O`×8
- **`InvntSttus`** (2 values) — `C`×100, `O`×17
- **`Transfered`** (1 values) — `N`×117
- **`ObjType`** (1 values) — `21`×117
- **`DocCur`** (1 values) — `INR`×117
- **`DocRate`** (1 values) — `1.000000`×117
- **`GroupNum`** (7 values) — `-1`×49, `1`×45, `21`×13, `18`×7, `17`×1, `16`×1, `22`×1
- **`SlpCode`** (9 values) — `11`×34, `26`×27, `2`×16, `107`×10, `-1`×10, `23`×9, `29`×6, `81`×4, `32`×1
- **`TrnspCode`** (1 values) — `-1`×117
- **`PartSupply`** (1 values) — `Y`×117
- **`Confirmed`** (1 values) — `Y`×117
- **`GrossBase`** (2 values) — `-6`×115, `-1`×2
- **`CreateTran`** (1 values) — `N`×117
- **`SummryType`** (1 values) — `N`×117
- **`UpdInvnt`** (1 values) — `I`×117
- **`UpdCardBal`** (1 values) — `D`×117
- **`InvntDirec`** (1 values) — `X`×117
- **`CntctCode`** (28 values) — `2357`×22, `0`×16, `6031`×9, `5743`×9, `4523`×8, `2354`×7, `2343`×7, `4880`×6, `4837`×5, `2359`×3, `2767`×3, `2467`×2, `2191`×2, `5078`×2, `2523`×2, `1874`×2, `5756`×1, `5072`×1, `2636`×1, `5642`×1, `2311`×1, `4884`×1, `4653`×1, `2119`×1, `2314`×1, `2443`×1, `2178`×1, `2752`×1
- **`ShowSCN`** (1 values) — `N`×117
- **`SysRate`** (1 values) — `1.000000`×117
- **`CurSource`** (1 values) — `L`×117
- **`FatherType`** (1 values) — `P`×117
- **`IsICT`** (1 values) — `N`×117
- **`VolUnit`** (1 values) — `4`×117
- **`WeightUnit`** (1 values) — `3`×117
- **`Series`** (22 values) — `2525`×19, `2174`×10, `2520`×8, `2169`×8, `2522`×7, `691`×7, `2524`×7, `2177`×6, `690`×5, `2175`×5, `2172`×4, `2173`×4, `2176`×4, `2168`×4, `2527`×3, `693`×3, `2171`×3, `2170`×3, `694`×2, `692`×2, `689`×2, `2167`×1
- **`isCrin`** (1 values) — `N`×117
- **`FinncPriod`** (22 values) — `44`×19, `22`×10, `41`×8, `17`×8, `43`×7, `9`×7, `42`×7, `25`×6, `8`×5, `23`×5, `20`×4, `21`×4, `24`×4, `16`×4, `11`×3, `45`×3, `19`×3, `18`×3, `7`×2, `12`×2, `10`×2, `15`×1
- **`UserSign`** (7 values) — `36`×97, `30`×11, `1`×4, `40`×2, `47`×1, `31`×1, `35`×1
- **`selfInv`** (1 values) — `N`×117
- **`WddStatus`** (2 values) — `P`×98, `-`×19
- **`Exported`** (1 values) — `N`×117
- **`StationID`** (15 values) — `9`×37, `688`×21, `61`×14, `23`×12, `220`×8, `260`×7, `233`×3, `316`×3, `68`×2, `8`×2, `313`×2, `690`×2, `169`×2, `222`×1, `194`×1
- **`NetProc`** (1 values) — `N`×117
- **`submitted`** (1 values) — `N`×117
- **`PoPrss`** (1 values) — `N`×117
- **`Rounding`** (2 values) — `N`×60, `Y`×57
- **`RevisionPo`** (1 values) — `N`×117
- **`PickStatus`** (1 values) — `N`×117
- **`Pick`** (1 values) — `N`×117
- **`BlockDunn`** (1 values) — `N`×117
- **`PayBlock`** (1 values) — `N`×117
- **`MaxDscn`** (1 values) — `N`×117
- **`Reserve`** (1 values) — `N`×117
- **`DeferrTax`** (1 values) — `N`×117
- **`BoeReserev`** (1 values) — `N`×117
- **`Installmnt`** (1 values) — `1`×117
- **`VATFirst`** (1 values) — `N`×117
- **`CEECFlag`** (2 values) — `Y`×84, `N`×33
- **`CtlAccount`** (2 values) — `2110005`×113, `2110004`×4
- **`BPLId`** (1 values) — `2`×117
- **`BPLName`** (1 values) — `FACTORY`×117
- **`VATRegNum`** (1 values) — `06AACCJ4223F1Z0`×117
- **`SumAbsId`** (1 values) — `-1`×117
- **`PIndicator`** (22 values) — `JUL-26-27`×19, `DEC-25-26`×10, `APR-26-27`×8, `JUL-25-26`×8, `MAY-26-27`×7, `Dec-24-25`×7, `JUN-26-27`×7, `MAR-25-26`×6, `JAN-25-26`×5, `Nov-24-25`×5, `FEB-25-26`×4, `OCT-25-26`×4, `NOV-25-26`×4, `JUN-25-26`×4, `AUG-25-26`×3, `SEP-25-26`×3, `Feb-24-25`×3, `AUG-26-27`×3, `Jan-24-25`×2, `Mar-24-25`×2, `Oct-24-25`×2, `MAY-25-26`×1
- **`UseShpdGd`** (1 values) — `N`×117
- **`DocSubType`** (1 values) — `--`×117
- **`DpmStatus`** (1 values) — `O`×117
- **`DpmDrawn`** (1 values) — `N`×117
- **`Posted`** (1 values) — `Y`×117
- **`IsPaytoBnk`** (1 values) — `N`×117
- **`isIns`** (1 values) — `N`×117
- **`VersionNum`** (2 values) — `10.00.310.21`×67, `10.00.250.15`×50
- **`LangCode`** (1 values) — `8`×117
- **`BPNameOW`** (2 values) — `N`×115, `Y`×2
- **`BillToOW`** (1 values) — `N`×117
- **`ShipToOW`** (2 values) — `N`×116, `Y`×1
- **`RetInvoice`** (1 values) — `N`×117
- **`Model`** (1 values) — `0`×117
- **`UseCorrVat`** (1 values) — `N`×117
- **`BlkCredMmo`** (1 values) — `N`×117
- **`OpenForLaC`** (1 values) — `Y`×117
- **`Excised`** (1 values) — `O`×117
- **`DutyStatus`** (1 values) — `Y`×117
- **`AutoCrtFlw`** (1 values) — `N`×117
- **`VatJENum`** (1 values) — `-1`×117
- **`InsurOp347`** (1 values) — `N`×117
- **`IgnRelDoc`** (1 values) — `N`×117
- **`ResidenNum`** (1 values) — `1`×117
- **`PQTGrpHW`** (1 values) — `N`×117
- **`ReopOriDoc`** (2 values) — `N`×115, `Y`×2
- **`ReopManCls`** (2 values) — `NULL`×115, `Y`×2
- **`DocManClsd`** (2 values) — `N`×108, `Y`×9
- **`ClosingOpt`** (1 values) — `1`×117
- **`Ordered`** (1 values) — `N`×117
- **`NTSApprov`** (1 values) — `N`×117
- **`PayDuMonth`** (1 values) — `N`×117
- **`ExtraDays`** (7 values) — `0`×49, `30`×45, `25`×13, `10`×7, `7`×1, `5`×1, `35`×1
- **`EDocGenTyp`** (1 values) — `N`×117
- **`OnlineQuo`** (1 values) — `N`×117
- **`EDocStatus`** (1 values) — `C`×117
- **`EDocProces`** (1 values) — `C`×117
- **`EDocCancel`** (1 values) — `N`×117
- **`EDocTest`** (1 values) — `N`×117
- **`DpmAsDscnt`** (1 values) — `N`×117
- **`GTSRlvnt`** (1 values) — `N`×117
- **`SrvTaxRule`** (1 values) — `N`×117
- **`AssetDate`** (2 values) — `NULL`×116, `2025-12-27 00:00:00.0000000`×1
- **`Notify`** (2 values) — `NULL`×113, `N`×4
- **`ReqType`** (1 values) — `12`×117
- **`OriginType`** (1 values) — `M`×117
- **`IsReuseNum`** (1 values) — `N`×117
- **`IsReuseNFN`** (1 values) — `N`×117
- **`DocDlvry`** (1 values) — `0`×117
- **`EnvTypeNFe`** (1 values) — `-1`×117
- **`IsAlt`** (1 values) — `N`×117
- **`AltBaseTyp`** (1 values) — `-1`×117
- **`PrintSEPA`** (1 values) — `N`×117
- **`RelatedTyp`** (1 values) — `-1`×117
- **`PoDropPrss`** (1 values) — `N`×117
- **`ExclTaxRep`** (1 values) — `N`×117
- **`Revision`** (1 values) — `N`×117
- **`GSTTranTyp`** (2 values) — `GA`×116, `--`×1
- **`BaseType`** (1 values) — `-1`×117
- **`ComTrade`** (1 values) — `E`×117
- **`UseBilAddr`** (2 values) — `N`×111, `Y`×6
- **`IssReason`** (1 values) — `1`×117
- **`ComTradeRt`** (1 values) — `N`×117
- **`SplitPmnt`** (1 values) — `N`×117
- **`SelfPosted`** (1 values) — `N`×117
- **`DPPStatus`** (1 values) — `N`×117
- **`EWBGenType`** (2 values) — `L`×114, `N`×3
- **`EDocType`** (1 values) — `F`×117
- **`AggregDoc`** (1 values) — `N`×117
- **`DataVers`** (6 values) — `2`×60, `3`×30, `1`×16, `4`×6, `5`×3, `6`×2
- **`IndFinal`** (1 values) — `N`×117
- **`PostPmntWT`** (1 values) — `N`×117
- **`FCEPmnMean`** (1 values) — `N`×117
- **`NotRel4MI`** (1 values) — `N`×117
- **`Rel4PPTax`** (1 values) — `N`×117
- **`BookeTdsBP`** (1 values) — `N`×117
- **`DigPayment`** (1 values) — `N`×117
- **`PDueMonEnd`** (1 values) — `N`×117
- **`RShipToCod`** (21 values) — `NULL`×50, `ECHO PLAST INDIA UNIT-II`×10, `STOCK GOODS ISSUE HARYANA`×9, `A A ENTERPRISES UTTAR PRADESH`×9, `RAJ TECHNOPACK PVT LTD SONIPAT`×7, `JOY PACK INDIA DELHI`×4, `PIONEER PET SWASTIC PET INDUSTRIES UTTRAKHAND`×4, `SONIPAT`×4, `SANGRUR`×3, `TPAC PACKAGING INDIA PVT LTD II HARIDWAR`×2, `JAIPUR`×2, `HAPUR`×2, `HARYANA GENERAL INDUSTRIES HISAR`×2, `BR AGROTECH LTD KALA AMB`×2, `GHAZIABAD`×1, `SSY CONTAINERS PVT LTD SONIPAT`×1, `TPAC PACKAGING INDIA PVT LTD UTTARAKHAND`×1, `NEW DELHI`×1, `HARYANA INDUSTRIAL COMPANY HISAR`×1, `FIROZABAD`×1, `ALWAR`×1
- **`RShipToOW`** (2 values) — `N`×71, `NULL`×46
- **`AplTaxOnFr`** (1 values) — `N`×117
- **`CpyDtyStts`** (1 values) — `N`×117
