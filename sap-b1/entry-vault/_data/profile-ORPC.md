# `ORPC` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 1,595 | 229 | `DocDate` | 2024-09-30 → 2026-08-20 |
| MART | 781 | 81 | `DocDate` | 2025-01-21 → 2026-08-03 |
| BEV | 248 | 27 | `DocDate` | 2024-10-01 → 2026-08-03 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1,595 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1,523 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 408 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 417 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 205 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 206 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 190 | |
| `NumAtCard` | NVARCHAR(200) | 100% | 90% | 100% | 100% | 84% | 100% | 1,463 | |
| `VatSum` | DECIMAL | 57% | 84% | 37% | 63% | 79% | 33% | 736 | |
| `DiscPrcnt` | DECIMAL | <1% | <1% | — | — | — | — | 4 | |
| `DiscSum` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocTotal` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,157 | |
| `PaidToDate` | DECIMAL | 80% | 56% | 99% | 96% | 60% | 100% | 998 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 1,523 | |
| `Comments` | NVARCHAR(254) | 98% | 56% | 100% | 93% | 58% | 100% | 1,556 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 220 | |
| `TransId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1,595 | |
| `ReceiptNum` | INTEGER | 10% | 5% | 7% | 16% | — | 4% | 119 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 8 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 502 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 34 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 95% | 100% | 97% | 97% | 100% | 100% | 193 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatSumSy` | DECIMAL | 57% | 84% | 37% | 63% | 79% | 33% | 736 | |
| `DiscSumSy` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `DocTotalSy` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1,157 | |
| `PaidSys` | DECIMAL | 80% | 56% | 99% | 96% | 60% | 100% | 998 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 396 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 90 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 510 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 11 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | 38% | 45% | 36% | 59% | 44% | 33% | 498 | |
| `VatPaidSys` | DECIMAL | 39% | 45% | 36% | 59% | 44% | 33% | 499 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `draftKey` | INTEGER | 98% | 63% | 99% | 99% | 90% | 100% | 1,568 | |
| `TotalExpns` | DECIMAL | <1% | — | 2% | <1% | — | — | 15 | |
| `TotalExpSC` | DECIMAL | <1% | — | 2% | <1% | — | — | 15 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 10 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 27 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 99% | 100% | 100% | 100% | 161 | |
| `WTSum` | DECIMAL | <1% | 4% | — | — | 5% | — | 5 | |
| `WTSumSC` | DECIMAL | <1% | 4% | — | — | 5% | — | 5 | |
| `RoundDif` | DECIMAL | 52% | 69% | 26% | 57% | 59% | 41% | 415 | |
| `RoundDifSy` | DECIMAL | 52% | 69% | 26% | 57% | 59% | 41% | 415 | |
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
| `Max1099` | DECIMAL | 99% | 100% | 100% | 99% | 100% | 100% | 1,311 | |
| `ExpAppl` | DECIMAL | <1% | — | 2% | <1% | — | — | 15 | |
| `ExpApplSC` | DECIMAL | <1% | — | 2% | <1% | — | — | 15 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WTApplied` | DECIMAL | <1% | 4% | — | — | 5% | — | 5 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WTAppliedS` | DECIMAL | <1% | 4% | — | — | 5% | — | 5 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NnSbAmnt` | DECIMAL | 40% | 28% | 51% | 59% | 28% | 81% | 555 | |
| `NnSbAmntSC` | DECIMAL | 40% | 28% | 51% | 59% | 28% | 81% | 555 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseAmnt` | DECIMAL | 20% | 20% | 23% | 40% | 9% | — | 251 | |
| `BaseAmntSC` | DECIMAL | 20% | 20% | 23% | 40% | 9% | — | 251 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `WTDetails` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 4 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PaidSum` | DECIMAL | 23% | 13% | 10% | 17% | 10% | 4% | 304 | |
| `PaidSumSc` | DECIMAL | 23% | 13% | 10% | 17% | 10% | 4% | 304 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OwnerCode` | INTEGER | 3% | — | — | — | — | — | 2 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 155 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxOnExp` | DECIMAL | <1% | — | <1% | <1% | — | — | 15 | |
| `TaxOnExpSc` | DECIMAL | <1% | — | <1% | <1% | — | — | 15 | |
| `TaxOnExAp` | DECIMAL | <1% | — | — | <1% | — | — | 15 | |
| `TaxOnExApS` | DECIMAL | <1% | — | — | <1% | — | — | 15 | |
| `LastPmnTyp` | NVARCHAR(1) | 10% | 5% | 7% | 16% | — | 4% | 2 | |
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
| `ReopManCls` | NVARCHAR(1) | <1% | 16% | 10% | — | 7% | 4% | 1 | |
| `DocManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ClosingOpt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayDuMonth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExtraDays` | SMALLINT | 28% | 37% | 42% | 21% | 27% | 22% | 8 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 99% | 89% | 100% | 100% | 95% | 100% | 1,572 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1,547 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1,554 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AssetDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 408 | |
| `Notify` | NVARCHAR(1) | 20% | 14% | <1% | <1% | 11% | — | 1 | |
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
| `RevRefNo` | NVARCHAR(100) | 97% | 98% | 99% | 99% | 100% | 100% | 1,300 | |
| `RevRefDate` | TIMESTAMP | 97% | 98% | 99% | 99% | 100% | 100% | 663 | |
| `TaxInvNo` | NVARCHAR(100) | <1% | 1% | — | 1% | — | — | 5 | |
| `FrmBpDate` | TIMESTAMP | <1% | 1% | — | <1% | — | — | 2 | |
| `GSTTranTyp` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ComTrade` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UseBilAddr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `IssReason` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `ComTradeRt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SplitPmnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SelfPosted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EWBGenType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RShipToCod` | NVARCHAR(50) | 29% | 36% | 26% | 100% | 100% | 100% | 81 | |
| `Address3` | NVARCHAR(254) | 29% | 36% | 26% | 100% | 100% | 100% | 90 | |
| `RShipToOW` | NVARCHAR(1) | 31% | 42% | 28% | 100% | 100% | 100% | 1 | |
| `AplTaxOnFr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Ship_From` | NVARCHAR(8) | — | <1% | — | — | — | — | 0 | |
| `U_BilltyNumber` | NVARCHAR(15) | 10% | — | n/a | 40% | — | n/a | 159 | |
| `U_BiltyDate` | TIMESTAMP | 10% | — | — | 39% | — | — | 124 | |
| `U_TransporterName` | NVARCHAR(50) | 12% | — | — | 41% | — | — | 43 | |
| `U_VehicleNoM` | NVARCHAR(12) | 10% | — | n/a | 40% | — | n/a | 98 | |
| `U_AR_NO` | NVARCHAR(12) | 6% | — | n/a | 4% | — | n/a | 48 | |
| `U_InvRevEntry` | NVARCHAR(20) | <1% | — | — | <1% | — | — | 6 | |
| `U_LRNUmber` | NVARCHAR(15) | 6% | — | n/a | 5% | — | n/a | 48 | |
| `U_BOEDate` | TIMESTAMP | 6% | — | n/a | 5% | — | n/a | 39 | |
| `U_UNE_SO` | NVARCHAR(100) | — | <1% | — | — | — | — | 0 | |
| `U_UNE_MLOC` | NVARCHAR(100) | <1% | <1% | — | — | — | — | 1 | |
| `U_UNE_ACTH` | NVARCHAR(100) | — | <1% | 100% | — | 2% | 100% | 0 | |
| `U_ARNO` | NVARCHAR(100) | <1% | — | — | — | — | — | 1 | |

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

- **`DocType`** (2 values) — `S`×1,295, `I`×300
- **`CANCELED`** (3 values) — `N`×1,567, `C`×14, `Y`×14
- **`Handwrtten`** (2 values) — `N`×1,583, `Y`×12
- **`Printed`** (2 values) — `N`×1,561, `Y`×34
- **`DocStatus`** (2 values) — `C`×1,276, `O`×319
- **`InvntSttus`** (2 values) — `C`×1,496, `O`×99
- **`Transfered`** (1 values) — `N`×1,595
- **`ObjType`** (1 values) — `19`×1,595
- **`DiscPrcnt`** (5 values) — `0.000000`×1,591, `0.000001`×1, `0.000002`×1, `NULL`×1, `-0.000005`×1
- **`DocCur`** (1 values) — `INR`×1,595
- **`DocRate`** (1 values) — `1.000000`×1,595
- **`GroupNum`** (8 values) — `-1`×1,154, `1`×196, `21`×102, `20`×78, `19`×45, `18`×12, `17`×6, `22`×2
- **`TrnspCode`** (1 values) — `-1`×1,595
- **`PartSupply`** (1 values) — `Y`×1,595
- **`Confirmed`** (1 values) — `Y`×1,595
- **`GrossBase`** (3 values) — `-6`×1,496, `-1`×63, `-10`×36
- **`CreateTran`** (1 values) — `Y`×1,595
- **`SummryType`** (1 values) — `N`×1,595
- **`UpdInvnt`** (1 values) — `I`×1,595
- **`UpdCardBal`** (1 values) — `B`×1,595
- **`InvntDirec`** (1 values) — `X`×1,595
- **`ShowSCN`** (1 values) — `N`×1,595
- **`SysRate`** (1 values) — `1.000000`×1,595
- **`CurSource`** (1 values) — `L`×1,595
- **`FatherType`** (1 values) — `P`×1,595
- **`IsICT`** (1 values) — `N`×1,595
- **`VolUnit`** (1 values) — `4`×1,595
- **`WeightUnit`** (1 values) — `3`×1,595
- **`isCrin`** (1 values) — `N`×1,595
- **`FinncPriod`** (24 values) — `10`×180, `7`×131, `8`×91, `18`×87, `44`×76, `20`×73, `9`×71, `12`×71, `16`×68, `21`×68, `11`×68, `17`×67, `43`×63, `22`×62, `42`×59, `19`×59, `25`×58, `15`×53, `23`×44, `24`×42, `41`×36, `45`×29, `14`×27, `6`×12
- **`UserSign`** (11 values) — `16`×461, `17`×363, `18`×345, `15`×335, `53`×41, `1`×22, `11`×17, `40`×6, `20`×2, `13`×2, `48`×1
- **`selfInv`** (1 values) — `N`×1,595
- **`WddStatus`** (2 values) — `P`×1,566, `-`×29
- **`TotalExpns`** (15 values) — `0.000000`×1,580, `3500.000000`×2, `5943.000000`×1, `232.960000`×1, `6787.000000`×1, `132.590000`×1, `994.560000`×1, `5465.000000`×1, `3000.000000`×1, `5000.000000`×1, `160313.000000`×1, `800.000000`×1, `14000.000000`×1, `9050.000000`×1, `26060.620000`×1
- **`TotalExpSC`** (15 values) — `0.000000`×1,580, `3500.000000`×2, `160313.000000`×1, `5943.000000`×1, `9050.000000`×1, `14000.000000`×1, `26060.620000`×1, `232.960000`×1, `6787.000000`×1, `132.590000`×1, `800.000000`×1, `994.560000`×1, `5465.000000`×1, `3000.000000`×1, `5000.000000`×1
- **`Exported`** (1 values) — `N`×1,595
- **`StationID`** (27 values) — `9`×795, `208`×164, `63`×134, `418`×119, `190`×74, `75`×62, `289`×45, `236`×45, `191`×27, `207`×21, `29`×18, `302`×18, `324`×12, `5`×12, `665`×11, `8`×6, `192`×6, `179`×4, `316`×4, `292`×4, `301`×3, `27`×3, `683`×3, `7`×2, `313`×1, `58`×1, `189`×1
- **`NetProc`** (1 values) — `N`×1,595
- **`WTSum`** (5 values) — `0.000000`×1,591, `6.000000`×1, `140.000000`×1, `3839.000000`×1, `1992.000000`×1
- **`WTSumSC`** (5 values) — `0.000000`×1,591, `1992.000000`×1, `3839.000000`×1, `140.000000`×1, `6.000000`×1
- **`submitted`** (1 values) — `N`×1,595
- **`PoPrss`** (1 values) — `N`×1,595
- **`Rounding`** (2 values) — `N`×899, `Y`×696
- **`RevisionPo`** (1 values) — `N`×1,595
- **`PickStatus`** (1 values) — `N`×1,595
- **`Pick`** (1 values) — `N`×1,595
- **`BlockDunn`** (1 values) — `N`×1,595
- **`PayBlock`** (1 values) — `N`×1,595
- **`MaxDscn`** (1 values) — `N`×1,595
- **`Reserve`** (1 values) — `N`×1,595
- **`ExpAppl`** (15 values) — `0.000000`×1,580, `3500.000000`×2, `160313.000000`×1, `502.652300`×1, `14000.000000`×1, `210.138400`×1, `800.000000`×1, `5943.000000`×1, `26060.620000`×1, `232.960000`×1, `6787.000000`×1, `132.590000`×1, `994.560000`×1, `3000.000000`×1, `5000.000000`×1
- **`ExpApplSC`** (15 values) — `0.000000`×1,580, `3500.000000`×2, `502.652300`×1, `14000.000000`×1, `800.000000`×1, `160313.000000`×1, `5000.000000`×1, `3000.000000`×1, `994.560000`×1, `6787.000000`×1, `232.960000`×1, `26060.620000`×1, `5943.000000`×1, `210.138400`×1, `132.590000`×1
- **`DeferrTax`** (1 values) — `N`×1,595
- **`WTApplied`** (5 values) — `0.000000`×1,591, `6.000000`×1, `140.000000`×1, `3839.000000`×1, `1992.000000`×1
- **`BoeReserev`** (1 values) — `N`×1,595
- **`WTAppliedS`** (5 values) — `0.000000`×1,591, `6.000000`×1, `140.000000`×1, `3839.000000`×1, `1992.000000`×1
- **`Installmnt`** (1 values) — `1`×1,595
- **`VATFirst`** (1 values) — `N`×1,595
- **`CEECFlag`** (2 values) — `N`×1,581, `Y`×14
- **`CtlAccount`** (6 values) — `2110004`×1,051, `2110001`×282, `2110005`×243, `2110003`×13, `2110002`×3, `2121002`×3
- **`BPLId`** (4 values) — `2`×1,325, `5`×200, `1`×66, `6`×4
- **`BPLName`** (4 values) — `FACTORY`×1,325, `HARYANA SALES`×200, `DELHI`×66, `DELHI ISD`×4
- **`VATRegNum`** (3 values) — `06AACCJ4223F1Z0`×1,525, `07AACCJ4223F1ZY`×66, `07AACCJ4223F2ZX`×4
- **`WTDetails`** (5 values) — `NULL`×960, `∅`×632, `0`×1, `]`×1, `00`×1
- **`SumAbsId`** (1 values) — `-1`×1,595
- **`PIndicator`** (24 values) — `Jan-24-25`×180, `Oct-24-25`×131, `Nov-24-25`×91, `AUG-25-26`×87, `JUL-26-27`×76, `OCT-25-26`×73, `Dec-24-25`×71, `Mar-24-25`×71, `NOV-25-26`×68, `Feb-24-25`×68, `JUN-25-26`×68, `JUL-25-26`×67, `JUN-26-27`×63, `DEC-25-26`×62, `SEP-25-26`×59, `MAY-26-27`×59, `MAR-25-26`×58, `MAY-25-26`×53, `JAN-25-26`×44, `FEB-25-26`×42, `APR-26-27`×36, `AUG-26-27`×29, `APR-25-26`×27, `Sep-24-25`×12
- **`UseShpdGd`** (1 values) — `N`×1,595
- **`DocSubType`** (2 values) — `GA`×1,160, `--`×435
- **`DpmStatus`** (1 values) — `O`×1,595
- **`DpmDrawn`** (1 values) — `N`×1,595
- **`Posted`** (1 values) — `Y`×1,595
- **`OwnerCode`** (3 values) — `NULL`×1,555, `2`×32, `14`×8
- **`IsPaytoBnk`** (1 values) — `N`×1,595
- **`isIns`** (1 values) — `N`×1,595
- **`VersionNum`** (2 values) — `10.00.250.15`×1,118, `10.00.310.21`×477
- **`LangCode`** (1 values) — `8`×1,595
- **`BPNameOW`** (1 values) — `N`×1,595
- **`BillToOW`** (1 values) — `N`×1,595
- **`ShipToOW`** (2 values) — `N`×1,269, `Y`×326
- **`RetInvoice`** (1 values) — `N`×1,595
- **`Model`** (1 values) — `0`×1,595
- **`TaxOnExp`** (15 values) — `0.000000`×1,580, `630.000000`×2, `2520.000000`×1, `3127.274400`×1, `1629.000000`×1, `983.700000`×1, `96.000000`×1, `1069.740000`×1, `1221.660000`×1, `41.932800`×1, `23.866200`×1, `28856.340000`×1, `179.020800`×1, `540.000000`×1, `900.000000`×1
- **`TaxOnExpSc`** (15 values) — `0.000000`×1,580, `630.000000`×2, `2520.000000`×1, `3127.274400`×1, `1629.000000`×1, `983.700000`×1, `96.000000`×1, `1069.740000`×1, `1221.660000`×1, `41.932800`×1, `23.866200`×1, `28856.340000`×1, `179.020800`×1, `900.000000`×1, `540.000000`×1
- **`TaxOnExAp`** (15 values) — `0.000000`×1,580, `630.000000`×2, `900.000000`×1, `540.000000`×1, `2520.000000`×1, `37.824900`×1, `90.477400`×1, `96.000000`×1, `1069.740000`×1, `179.020800`×1, `1221.660000`×1, `3127.274400`×1, `41.932800`×1, `28856.340000`×1, `23.866200`×1
- **`TaxOnExApS`** (15 values) — `0.000000`×1,580, `630.000000`×2, `41.932800`×1, `540.000000`×1, `900.000000`×1, `179.020800`×1, `28856.340000`×1, `23.866200`×1, `3127.274400`×1, `1221.660000`×1, `1069.740000`×1, `96.000000`×1, `90.477400`×1, `37.824900`×1, `2520.000000`×1
- **`LastPmnTyp`** (3 values) — `NULL`×1,434, `V`×160, `R`×1
- **`UseCorrVat`** (1 values) — `N`×1,595
- **`BlkCredMmo`** (1 values) — `N`×1,595
- **`OpenForLaC`** (1 values) — `Y`×1,595
- **`Excised`** (1 values) — `O`×1,595
- **`DutyStatus`** (1 values) — `Y`×1,595
- **`AutoCrtFlw`** (1 values) — `N`×1,595
- **`VatJENum`** (1 values) — `-1`×1,595
- **`InsurOp347`** (1 values) — `N`×1,595
- **`IgnRelDoc`** (1 values) — `N`×1,595
- **`ResidenNum`** (1 values) — `1`×1,595
- **`PQTGrpHW`** (1 values) — `N`×1,595
- **`ReopOriDoc`** (2 values) — `N`×1,581, `Y`×14
- **`ReopManCls`** (2 values) — `NULL`×1,581, `Y`×14
- **`DocManClsd`** (1 values) — `N`×1,595
- **`ClosingOpt`** (1 values) — `1`×1,595
- **`Ordered`** (1 values) — `N`×1,595
- **`NTSApprov`** (1 values) — `N`×1,595
- **`PayDuMonth`** (1 values) — `N`×1,595
- **`ExtraDays`** (8 values) — `0`×1,154, `30`×196, `25`×102, `21`×78, `15`×45, `10`×12, `7`×6, `35`×2
- **`EDocGenTyp`** (1 values) — `N`×1,595
- **`OnlineQuo`** (1 values) — `N`×1,595
- **`EDocStatus`** (1 values) — `C`×1,595
- **`EDocProces`** (1 values) — `C`×1,595
- **`EDocCancel`** (1 values) — `N`×1,595
- **`EDocTest`** (1 values) — `N`×1,595
- **`DpmAsDscnt`** (1 values) — `N`×1,595
- **`GTSRlvnt`** (1 values) — `N`×1,595
- **`SrvTaxRule`** (1 values) — `N`×1,595
- **`Notify`** (2 values) — `NULL`×1,276, `N`×319
- **`ReqType`** (1 values) — `12`×1,595
- **`OriginType`** (1 values) — `M`×1,595
- **`IsReuseNum`** (1 values) — `N`×1,595
- **`IsReuseNFN`** (1 values) — `N`×1,595
- **`DocDlvry`** (1 values) — `0`×1,595
- **`EnvTypeNFe`** (1 values) — `-1`×1,595
- **`IsAlt`** (1 values) — `N`×1,595
- **`AltBaseTyp`** (1 values) — `-1`×1,595
- **`PrintSEPA`** (1 values) — `N`×1,595
- **`RelatedTyp`** (1 values) — `-1`×1,595
- **`PoDropPrss`** (1 values) — `N`×1,595
- **`ExclTaxRep`** (1 values) — `N`×1,595
- **`Revision`** (1 values) — `N`×1,595
- **`TaxInvNo`** (6 values) — `NULL`×1,590, `19`×1, `∅`×1, `21`×1, `PBC/1484/25-26`×1, `24`×1
- **`FrmBpDate`** (3 values) — `NULL`×1,593, `2025-11-17 00:00:00.0000000`×1, `2026-05-06 00:00:00.0000000`×1
- **`GSTTranTyp`** (2 values) — `GA`×1,160, `--`×435
- **`BaseType`** (1 values) — `-1`×1,595
- **`ComTrade`** (1 values) — `E`×1,595
- **`UseBilAddr`** (2 values) — `N`×1,527, `Y`×68
- **`IssReason`** (4 values) — `1`×1,583, `2`×9, `7`×2, `3`×1
- **`ComTradeRt`** (1 values) — `N`×1,595
- **`SplitPmnt`** (1 values) — `N`×1,595
- **`SelfPosted`** (1 values) — `N`×1,595
- **`DPPStatus`** (1 values) — `N`×1,595
- **`EWBGenType`** (2 values) — `L`×1,391, `N`×204
- **`EDocType`** (1 values) — `F`×1,595
- **`AggregDoc`** (1 values) — `N`×1,595
- **`DataVers`** (4 values) — `1`×1,385, `2`×185, `3`×15, `4`×10
- **`IndFinal`** (1 values) — `N`×1,595
- **`PostPmntWT`** (1 values) — `N`×1,595
- **`FCEPmnMean`** (1 values) — `N`×1,595
- **`NotRel4MI`** (1 values) — `N`×1,595
- **`Rel4PPTax`** (1 values) — `N`×1,595
- **`BookeTdsBP`** (1 values) — `N`×1,595
- **`DigPayment`** (1 values) — `N`×1,595
- **`PDueMonEnd`** (1 values) — `N`×1,595
- **`RShipToOW`** (2 values) — `NULL`×1,104, `N`×491
- **`AplTaxOnFr`** (1 values) — `N`×1,595
- **`CpyDtyStts`** (1 values) — `N`×1,595
- **`U_InvRevEntry`** (7 values) — `NULL`×1,586, `CPISOKNSA210825`×3, `HDMUBCNA96975100`×2, `MEDUEZ075338`×1, `DXBF09903400`×1, `247509491`×1, `EPIRAEESAD259371`×1
- **`U_ARNO`** (2 values) — `NULL`×1,594, `150`×1
