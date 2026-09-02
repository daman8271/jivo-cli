# `ORDN` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 2,031 | 213 | `DocDate` | 2024-10-08 → 2026-08-21 |
| MART | 1,847 | 246 | `DocDate` | 2025-01-17 → 2026-08-24 |
| BEV | 187 | 18 | `DocDate` | 2024-10-15 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,031 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2,031 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 400 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 400 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 139 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 139 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 178 | |
| `NumAtCard` | NVARCHAR(200) | 9% | 12% | 2% | 5% | 22% | 6% | 182 | |
| `VatSum` | DECIMAL | 37% | 64% | 11% | 4% | 51% | 17% | 520 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocTotal` | DECIMAL | 37% | 67% | 15% | 4% | 51% | 17% | 528 | |
| `PaidToDate` | DECIMAL | 37% | 67% | 13% | 4% | 50% | 17% | 523 | |
| `GrosProfit` | DECIMAL | 38% | 64% | 99% | 4% | 51% | 100% | 570 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 2,031 | |
| `Comments` | NVARCHAR(254) | 94% | 96% | 94% | 98% | 93% | 94% | 1,757 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 185 | |
| `TransId` | INTEGER | 95% | 91% | 17% | 99% | 58% | 11% | 1,925 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 9 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 592 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 30 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 99% | 99% | 99% | 94% | 98% | 100% | 137 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatSumSy` | DECIMAL | 37% | 64% | 11% | 4% | 51% | 17% | 520 | |
| `DocTotalSy` | DECIMAL | 37% | 67% | 15% | 4% | 51% | 17% | 528 | |
| `PaidSys` | DECIMAL | 37% | 67% | 13% | 4% | 50% | 17% | 523 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrosProfSy` | DECIMAL | 38% | 64% | 99% | 4% | 51% | 100% | 570 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 414 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 400 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 20 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | 37% | 64% | 11% | 4% | 50% | 17% | 512 | |
| `VatPaidSys` | DECIMAL | 37% | 64% | 11% | 4% | 50% | 17% | 512 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `draftKey` | INTEGER | 51% | 24% | 78% | 93% | 29% | 72% | 1,041 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 184 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 51 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 190 | |
| `RoundDif` | DECIMAL | 16% | 11% | 4% | 3% | 46% | 11% | 170 | |
| `RoundDifSy` | DECIMAL | 16% | 11% | 4% | 3% | 46% | 11% | 170 | |
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
| `Max1099` | DECIMAL | 37% | 64% | 15% | 4% | 51% | 17% | 532 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 15 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OwnerCode` | INTEGER | <1% | — | <1% | — | — | — | 1 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 185 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
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
| `ReopOriDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReopManCls` | NVARCHAR(1) | — | <1% | — | — | — | — | 0 | |
| `DocManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ClosingOpt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayDuMonth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExtraDays` | SMALLINT | 18% | 10% | 2% | 4% | 3% | 6% | 7 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 10% | 22% | 2% | 8% | 58% | 6% | 202 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1,964 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1,972 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AssetDate` | TIMESTAMP | 4% | — | — | — | — | — | 9 | |
| `Notify` | NVARCHAR(1) | 41% | 5% | 21% | 59% | 18% | 22% | 1 | |
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
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Address3` | NVARCHAR(254) | 29% | 30% | 29% | 100% | 100% | 100% | 7 | |
| `RShipToOW` | NVARCHAR(1) | 33% | 32% | 40% | 100% | 100% | 100% | 1 | |
| `AplTaxOnFr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_ACTH` | NVARCHAR(100) | — | — | 99% | — | — | 100% | 0 | |
| `U_SALES_PERSON` | NVARCHAR(20) | <1% | n/a | n/a | — | n/a | n/a | 1 | |

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

- **`DocType`** (1 values) — `I`×2,031
- **`CANCELED`** (3 values) — `N`×1,817, `C`×107, `Y`×107
- **`Handwrtten`** (1 values) — `N`×2,031
- **`Printed`** (2 values) — `N`×2,025, `Y`×6
- **`DocStatus`** (2 values) — `C`×1,991, `O`×40
- **`InvntSttus`** (2 values) — `C`×1,968, `O`×63
- **`Transfered`** (1 values) — `N`×2,031
- **`ObjType`** (1 values) — `16`×2,031
- **`DocCur`** (1 values) — `INR`×2,031
- **`DocRate`** (1 values) — `1.000000`×2,031
- **`GroupNum`** (9 values) — `-1`×1,633, `1`×191, `20`×98, `18`×72, `6`×24, `11`×6, `19`×5, `10`×1, `17`×1
- **`SlpCode`** (30 values) — `-1`×1,159, `4`×506, `18`×101, `94`×84, `17`×42, `28`×30, `63`×30, `33`×16, `103`×11, `46`×7, `58`×7, `107`×6, `102`×5, `49`×4, `98`×3, `80`×3, `25`×2, `7`×2, `54`×2, `110`×1, `9`×1, `99`×1, `6`×1, `81`×1, `53`×1, `93`×1, `109`×1, `11`×1, `35`×1, `66`×1
- **`TrnspCode`** (1 values) — `-1`×2,031
- **`PartSupply`** (1 values) — `Y`×2,031
- **`Confirmed`** (1 values) — `Y`×2,031
- **`GrossBase`** (2 values) — `-6`×1,896, `-1`×135
- **`CreateTran`** (1 values) — `N`×2,031
- **`SummryType`** (1 values) — `N`×2,031
- **`UpdInvnt`** (1 values) — `G`×2,031
- **`UpdCardBal`** (1 values) — `D`×2,031
- **`InvntDirec`** (1 values) — `E`×2,031
- **`ShowSCN`** (1 values) — `N`×2,031
- **`SysRate`** (1 values) — `1.000000`×2,031
- **`CurSource`** (1 values) — `L`×2,031
- **`FatherType`** (1 values) — `P`×2,031
- **`IsICT`** (1 values) — `N`×2,031
- **`VolUnit`** (1 values) — `4`×2,031
- **`WeightUnit`** (1 values) — `3`×2,031
- **`Series`** (23 values) — `316`×254, `314`×200, `315`×175, `313`×126, `1333`×113, `1331`×94, `1330`×92, `1326`×86, `318`×83, `1332`×74, `1324`×74, `1325`×72, `2507`×71, `1327`×71, `1328`×67, `1323`×64, `2505`×56, `1329`×54, `2503`×50, `1322`×49, `317`×37, `2502`×35, `2510`×34
- **`isCrin`** (1 values) — `N`×2,031
- **`FinncPriod`** (23 values) — `10`×254, `8`×200, `9`×175, `7`×126, `25`×113, `23`×94, `22`×92, `18`×86, `12`×83, `24`×74, `16`×74, `17`×72, `44`×71, `19`×71, `20`×67, `15`×64, `43`×56, `21`×54, `42`×50, `14`×49, `11`×37, `41`×35, `45`×34
- **`UserSign`** (20 values) — `44`×805, `35`×262, `37`×241, `26`×215, `20`×191, `25`×99, `40`×46, `38`×41, `49`×34, `28`×32, `1`×31, `22`×12, `16`×6, `47`×5, `24`×3, `21`×2, `31`×2, `27`×2, `30`×1, `33`×1
- **`selfInv`** (1 values) — `N`×2,031
- **`WddStatus`** (3 values) — `P`×1,024, `-`×994, `A`×13
- **`Exported`** (1 values) — `N`×2,031
- **`NetProc`** (1 values) — `N`×2,031
- **`submitted`** (1 values) — `N`×2,031
- **`PoPrss`** (1 values) — `N`×2,031
- **`Rounding`** (2 values) — `N`×1,687, `Y`×344
- **`RevisionPo`** (1 values) — `N`×2,031
- **`PickStatus`** (1 values) — `N`×2,031
- **`Pick`** (1 values) — `N`×2,031
- **`BlockDunn`** (1 values) — `N`×2,031
- **`PayBlock`** (1 values) — `N`×2,031
- **`MaxDscn`** (1 values) — `N`×2,031
- **`Reserve`** (1 values) — `N`×2,031
- **`DeferrTax`** (1 values) — `N`×2,031
- **`BoeReserev`** (1 values) — `N`×2,031
- **`Installmnt`** (1 values) — `1`×2,031
- **`VATFirst`** (1 values) — `N`×2,031
- **`CEECFlag`** (2 values) — `Y`×1,396, `N`×635
- **`CtlAccount`** (15 values) — `1101005`×743, `1101001`×528, `1101004`×408, `1101008`×242, `1101006`×51, `1101012`×12, `1101015`×12, `1101007`×12, `1101013`×9, `1102002`×5, `1101011`×2, `1102003`×2, `1101009`×2, `1101014`×2, `1101016`×1
- **`BPLId`** (3 values) — `2`×1,453, `1`×406, `3`×172
- **`BPLName`** (3 values) — `FACTORY`×1,453, `DELHI`×406, `PUNJAB`×172
- **`VATRegNum`** (3 values) — `06AACCJ4223F1Z0`×1,453, `07AACCJ4223F1ZY`×406, `03AACCJ4223F1Z6`×172
- **`SumAbsId`** (1 values) — `-1`×2,031
- **`PIndicator`** (23 values) — `Jan-24-25`×254, `Nov-24-25`×200, `Dec-24-25`×175, `Oct-24-25`×126, `MAR-25-26`×113, `JAN-25-26`×94, `DEC-25-26`×92, `AUG-25-26`×86, `Mar-24-25`×83, `JUN-25-26`×74, `FEB-25-26`×74, `JUL-25-26`×72, `JUL-26-27`×71, `SEP-25-26`×71, `OCT-25-26`×67, `MAY-25-26`×64, `JUN-26-27`×56, `NOV-25-26`×54, `MAY-26-27`×50, `APR-25-26`×49, `Feb-24-25`×37, `APR-26-27`×35, `AUG-26-27`×34
- **`UseShpdGd`** (1 values) — `N`×2,031
- **`DocSubType`** (1 values) — `--`×2,031
- **`DpmStatus`** (1 values) — `O`×2,031
- **`DpmDrawn`** (1 values) — `N`×2,031
- **`Posted`** (1 values) — `Y`×2,031
- **`OwnerCode`** (2 values) — `NULL`×2,030, `14`×1
- **`IsPaytoBnk`** (1 values) — `N`×2,031
- **`isIns`** (1 values) — `N`×2,031
- **`VersionNum`** (2 values) — `10.00.250.15`×1,450, `10.00.310.21`×581
- **`LangCode`** (1 values) — `8`×2,031
- **`BPNameOW`** (2 values) — `N`×2,025, `Y`×6
- **`BillToOW`** (2 values) — `N`×2,030, `Y`×1
- **`ShipToOW`** (2 values) — `N`×2,029, `Y`×2
- **`RetInvoice`** (1 values) — `N`×2,031
- **`Model`** (1 values) — `0`×2,031
- **`UseCorrVat`** (1 values) — `N`×2,031
- **`BlkCredMmo`** (1 values) — `N`×2,031
- **`OpenForLaC`** (1 values) — `Y`×2,031
- **`Excised`** (1 values) — `O`×2,031
- **`DutyStatus`** (1 values) — `Y`×2,031
- **`AutoCrtFlw`** (1 values) — `N`×2,031
- **`VatJENum`** (1 values) — `-1`×2,031
- **`InsurOp347`** (1 values) — `N`×2,031
- **`IgnRelDoc`** (1 values) — `N`×2,031
- **`ResidenNum`** (1 values) — `1`×2,031
- **`PQTGrpHW`** (1 values) — `N`×2,031
- **`ReopOriDoc`** (1 values) — `N`×2,031
- **`DocManClsd`** (2 values) — `N`×2,009, `Y`×22
- **`ClosingOpt`** (1 values) — `1`×2,031
- **`Ordered`** (1 values) — `N`×2,031
- **`NTSApprov`** (1 values) — `N`×2,031
- **`PayDuMonth`** (1 values) — `N`×2,031
- **`ExtraDays`** (7 values) — `0`×1,658, `30`×191, `21`×98, `10`×72, `60`×6, `15`×5, `7`×1
- **`EDocGenTyp`** (1 values) — `N`×2,031
- **`OnlineQuo`** (1 values) — `N`×2,031
- **`EDocStatus`** (1 values) — `C`×2,031
- **`EDocProces`** (1 values) — `C`×2,031
- **`EDocCancel`** (1 values) — `N`×2,031
- **`EDocTest`** (1 values) — `N`×2,031
- **`DpmAsDscnt`** (1 values) — `N`×2,031
- **`GTSRlvnt`** (1 values) — `N`×2,031
- **`SrvTaxRule`** (1 values) — `N`×2,031
- **`AssetDate`** (10 values) — `NULL`×1,944, `2025-01-02 00:00:00.0000000`×72, `2025-01-06 00:00:00.0000000`×4, `2024-10-08 00:00:00.0000000`×3, `2025-11-30 00:00:00.0000000`×2, `2025-03-25 00:00:00.0000000`×2, `2025-01-30 00:00:00.0000000`×1, `2025-02-25 00:00:00.0000000`×1, `2024-11-22 00:00:00.0000000`×1, `2025-01-22 00:00:00.0000000`×1
- **`Notify`** (2 values) — `NULL`×1,197, `N`×834
- **`ReqType`** (1 values) — `12`×2,031
- **`OriginType`** (1 values) — `M`×2,031
- **`IsReuseNum`** (1 values) — `N`×2,031
- **`IsReuseNFN`** (1 values) — `N`×2,031
- **`DocDlvry`** (1 values) — `0`×2,031
- **`EnvTypeNFe`** (1 values) — `-1`×2,031
- **`IsAlt`** (1 values) — `N`×2,031
- **`AltBaseTyp`** (1 values) — `-1`×2,031
- **`PrintSEPA`** (1 values) — `N`×2,031
- **`RelatedTyp`** (1 values) — `-1`×2,031
- **`PoDropPrss`** (1 values) — `N`×2,031
- **`ExclTaxRep`** (1 values) — `N`×2,031
- **`Revision`** (1 values) — `N`×2,031
- **`GSTTranTyp`** (1 values) — `GA`×2,031
- **`BaseType`** (1 values) — `-1`×2,031
- **`ComTrade`** (1 values) — `E`×2,031
- **`UseBilAddr`** (2 values) — `Y`×1,877, `N`×154
- **`IssReason`** (1 values) — `1`×2,031
- **`ComTradeRt`** (1 values) — `N`×2,031
- **`SplitPmnt`** (1 values) — `N`×2,031
- **`SelfPosted`** (1 values) — `N`×2,031
- **`DPPStatus`** (1 values) — `N`×2,031
- **`EWBGenType`** (1 values) — `L`×2,031
- **`EDocType`** (1 values) — `F`×2,031
- **`AggregDoc`** (1 values) — `N`×2,031
- **`DataVers`** (23 values) — `2`×934, `3`×513, `1`×447, `4`×53, `5`×23, `6`×23, `8`×6, `7`×6, `13`×4, `10`×3, `9`×2, `14`×2, `17`×2, `16`×2, `12`×2, `11`×2, `271`×1, `209`×1, `26`×1, `19`×1, `77`×1, `18`×1, `25`×1
- **`IndFinal`** (1 values) — `N`×2,031
- **`PostPmntWT`** (1 values) — `N`×2,031
- **`FCEPmnMean`** (1 values) — `N`×2,031
- **`NotRel4MI`** (1 values) — `N`×2,031
- **`Rel4PPTax`** (1 values) — `N`×2,031
- **`BookeTdsBP`** (1 values) — `N`×2,031
- **`DigPayment`** (1 values) — `N`×2,031
- **`PDueMonEnd`** (1 values) — `N`×2,031
- **`RShipToOW`** (2 values) — `NULL`×1,359, `N`×672
- **`AplTaxOnFr`** (1 values) — `N`×2,031
- **`CpyDtyStts`** (1 values) — `N`×2,031
- **`U_SALES_PERSON`** (2 values) — `NULL`×2,027, `ECOM`×4
