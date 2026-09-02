# `OWTR` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 12,204 | 2,396 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 1,728 | 592 | `DocDate` | 2025-01-15 → 2026-08-24 |
| BEV | 2,200 | 497 | `DocDate` | 2024-10-07 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12,204 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12,204 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 638 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 638 | |
| `CardCode` | NVARCHAR(15) | 16% | 6% | 3% | 11% | 17% | 4% | 71 | |
| `CardName` | NVARCHAR(200) | 16% | 6% | 3% | 11% | 17% | 4% | 71 | |
| `Address` | NVARCHAR(254) | 16% | 6% | 3% | 11% | 17% | 4% | 80 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocRate` | DECIMAL | 10% | 59% | <1% | 10% | 33% | — | 2 | |
| `DocTotal` | DECIMAL | 80% | 100% | 98% | 80% | 99% | 100% | 8,807 | |
| `PaidToDate` | DECIMAL | 1% | 4% | 1% | <1% | 12% | 2% | 141 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 12,204 | |
| `Comments` | NVARCHAR(254) | 24% | 67% | 25% | 28% | 54% | 59% | 2,687 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 76 | |
| `TransId` | INTEGER | 99% | 99% | 99% | 99% | 100% | 100% | 12,089 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 992 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 17 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 98% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 8% | 6% | — | 10% | 17% | — | 67 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocTotalSy` | DECIMAL | 80% | 100% | 98% | 80% | 99% | 100% | 8,807 | |
| `PaidSys` | DECIMAL | 1% | 4% | 1% | <1% | 12% | 2% | 141 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 631 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 638 | |
| `Filler` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 42 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 22 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `draftKey` | INTEGER | 90% | 76% | 95% | 86% | 48% | 95% | 11,033 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 80 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 15% | 6% | 3% | 11% | 17% | 4% | 80 | |
| `submitted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rounding` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevisionPo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Pick` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlockDunn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayBlock` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `MaxDscn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Reserve` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Max1099` | DECIMAL | 80% | 100% | 98% | 80% | 99% | 100% | 8,807 | |
| `DeferrTax` | NVARCHAR(1) | 98% | 72% | 100% | 98% | 68% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 6% | 58% | <1% | 2% | 33% | — | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CtlAccount` | NVARCHAR(15) | 16% | 6% | 3% | 11% | 17% | 4% | 14 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | <1% | <1% | — | <1% | 1% | — | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UseCorrVat` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlkCredMmo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OpenForLaC` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excised` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SrvGpPrcnt` | DECIMAL | 2% | — | <1% | — | — | — | 1 | |
| `DutyStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AutoCrtFlw` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatJENum` | INTEGER | 99% | 100% | 100% | 100% | 99% | 100% | 2 | |
| `InsurOp347` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IgnRelDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PQTGrpHW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ClosingOpt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | <1% | <1% | <1% | — | — | <1% | 9 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 10,532 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 10,582 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ToWhsCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | 100% | 45 | |
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
| `UseBilAddr` | NVARCHAR(1) | <1% | <1% | — | <1% | 1% | — | 2 | |
| `IssReason` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ComTradeRt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SplitPmnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SelfPosted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EWBGenType` | NVARCHAR(1) | 6% | 58% | <1% | 2% | 33% | — | 1 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QRCodeSrc` | NCLOB | <1% | — | — | — | — | — | 0 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 27 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AplTaxOnFr` | NVARCHAR(1) | 49% | 81% | 41% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Dipatch_Date` | TIMESTAMP | 5% | — | <1% | <1% | — | — | 127 | |
| `U_Basement` | NVARCHAR(10) | <1% | — | — | — | — | — | 2 | |
| `U_First_Floor` | NVARCHAR(10) | <1% | — | — | — | — | — | 1 | |
| `U_BilltyNumber` | NVARCHAR(15) | 11% | — | n/a | 10% | — | n/a | 819 | |
| `U_BiltyDate` | TIMESTAMP | 11% | — | <1% | 10% | — | — | 415 | |
| `U_TransporterName` | NVARCHAR(50) | 11% | — | <1% | 10% | — | — | 144 | |
| `U_VehicleNoM` | NVARCHAR(12) | 16% | — | n/a | 18% | — | n/a | 280 | |
| `U_DriverName` | NCLOB | 4% | — | <1% | <1% | — | — | 0 | |
| `U_TransporterInvoice` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 2 | |
| `U_Mob_No` | NVARCHAR(12) | 4% | — | <1% | <1% | — | — | 42 | |
| `U_AR_NO` | NVARCHAR(12) | <1% | — | n/a | — | — | n/a | 28 | |
| `U_InvRevEntry` | NVARCHAR(20) | <1% | — | — | <1% | — | — | 9 | |
| `U_LRNUmber` | NVARCHAR(15) | <1% | — | n/a | <1% | — | n/a | 36 | |
| `U_BOEDate` | TIMESTAMP | <1% | — | n/a | <1% | — | n/a | 32 | |
| `U_UNE_BRCH` | NVARCHAR(100) | <1% | — | — | — | — | — | 1 | |
| `U_UNE_ACTH` | NVARCHAR(100) | 19% | 78% | 97% | 8% | 92% | 100% | 17 | |
| `U_ARNO` | NVARCHAR(100) | <1% | — | — | — | — | — | 1 | |
| `U_OMS_Order_No` | INTEGER | <1% | — | — | — | — | — | 1 | |
| `U_DisDE` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_DisDN` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_Production_Order` | INTEGER | <1% | n/a | 1% | — | n/a | 2% | 19 | |
| `U_PRODUCTION_DATE` | TIMESTAMP | <1% | n/a | — | — | n/a | — | 1 | |
| `U_SALES_PERSON` | NVARCHAR(20) | <1% | n/a | n/a | — | n/a | n/a | 2 | |

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

- **`DocType`** (1 values) — `I`×12,204
- **`CANCELED`** (2 values) — `N`×12,170, `Y`×34
- **`Handwrtten`** (1 values) — `N`×12,204
- **`Printed`** (2 values) — `N`×11,976, `Y`×228
- **`DocStatus`** (2 values) — `O`×12,170, `C`×34
- **`InvntSttus`** (2 values) — `O`×12,051, `C`×153
- **`Transfered`** (1 values) — `N`×12,204
- **`ObjType`** (1 values) — `67`×12,204
- **`DocCur`** (1 values) — `INR`×12,204
- **`DocRate`** (2 values) — `0.000000`×10,962, `1.000000`×1,242
- **`GroupNum`** (4 values) — `-1`×9,720, `1`×1,815, `4`×667, `5`×2
- **`SlpCode`** (17 values) — `-1`×10,997, `24`×443, `2`×185, `23`×179, `107`×101, `14`×96, `6`×66, `8`×65, `142`×30, `110`×13, `29`×9, `9`×5, `64`×4, `108`×4, `0`×3, `4`×3, `121`×1
- **`TrnspCode`** (1 values) — `-1`×12,204
- **`PartSupply`** (1 values) — `Y`×12,204
- **`Confirmed`** (1 values) — `Y`×12,204
- **`GrossBase`** (3 values) — `-6`×11,464, `-1`×450, `0`×290
- **`CreateTran`** (1 values) — `N`×12,204
- **`SummryType`** (1 values) — `N`×12,204
- **`UpdInvnt`** (1 values) — `I`×12,204
- **`UpdCardBal`** (1 values) — `N`×12,204
- **`InvntDirec`** (1 values) — `E`×12,204
- **`ShowSCN`** (1 values) — `N`×12,204
- **`SysRate`** (1 values) — `1.000000`×12,204
- **`CurSource`** (1 values) — `L`×12,204
- **`FatherType`** (1 values) — `P`×12,204
- **`IsICT`** (1 values) — `N`×12,204
- **`VolUnit`** (1 values) — `4`×12,204
- **`WeightUnit`** (2 values) — `3`×12,202, `2`×2
- **`Series`** (24 values) — `2187`×886, `2188`×732, `2658`×694, `2657`×657, `2186`×636, `2659`×587, `2189`×587, `2182`×586, `2656`×580, `2181`×575, `2183`×568, `741`×521, `2184`×493, `2180`×477, `739`×453, `738`×447, `742`×437, `2185`×422, `740`×421, `743`×380, `2178`×372, `2660`×354, `2179`×338, `737`×1
- **`isCrin`** (2 values) — `N`×11,963, `Y`×241
- **`FinncPriod`** (24 values) — `23`×886, `24`×732, `43`×694, `42`×657, `22`×636, `44`×587, `25`×587, `18`×586, `41`×580, `17`×575, `19`×568, `10`×521, `20`×493, `16`×477, `8`×453, `7`×447, `11`×437, `21`×422, `9`×421, `12`×380, `14`×372, `45`×354, `15`×338, `6`×1
- **`UserSign`** (22 values) — `33`×5,385, `36`×2,785, `35`×1,634, `15`×1,021, `26`×372, `19`×260, `22`×209, `44`×150, `49`×119, `32`×63, `1`×56, `24`×42, `52`×30, `10`×21, `30`×18, `38`×13, `20`×9, `40`×7, `21`×5, `47`×3, `39`×1, `23`×1
- **`selfInv`** (1 values) — `N`×12,204
- **`WddStatus`** (3 values) — `P`×10,848, `-`×1,172, `A`×184
- **`Exported`** (1 values) — `N`×12,204
- **`NetProc`** (1 values) — `N`×12,204
- **`submitted`** (1 values) — `N`×12,204
- **`PoPrss`** (1 values) — `N`×12,204
- **`Rounding`** (1 values) — `N`×12,204
- **`RevisionPo`** (1 values) — `N`×12,204
- **`PickStatus`** (1 values) — `N`×12,204
- **`Pick`** (1 values) — `N`×12,204
- **`BlockDunn`** (1 values) — `N`×12,204
- **`PayBlock`** (1 values) — `N`×12,204
- **`MaxDscn`** (1 values) — `N`×12,204
- **`Reserve`** (1 values) — `N`×12,204
- **`DeferrTax`** (2 values) — `N`×11,994, `NULL`×210
- **`BoeReserev`** (1 values) — `N`×12,204
- **`Installmnt`** (1 values) — `1`×12,204
- **`VATFirst`** (2 values) — `NULL`×11,471, `N`×733
- **`CEECFlag`** (1 values) — `N`×12,204
- **`CtlAccount`** (14 values) — `∅`×10,310, `2110001`×697, `1102005`×562, `1102003`×223, `2110005`×160, `2110002`×119, `1102001`×76, `1101012`×23, `1101002`×9, `2110007`×9, `2120002`×8, `2121001`×4, `1101005`×3, `2121002`×1
- **`BPLId`** (3 values) — `2`×11,497, `1`×434, `3`×273
- **`BPLName`** (5 values) — `FACTORY`×11,486, `DELHI`×431, `PUNJAB`×273, `Factory`×11, `Delhi`×3
- **`VATRegNum`** (3 values) — `06AACCJ4223F1Z0`×11,497, `07AACCJ4223F1ZY`×434, `03AACCJ4223F1Z6`×273
- **`SumAbsId`** (1 values) — `-1`×12,204
- **`PIndicator`** (24 values) — `JAN-25-26`×886, `FEB-25-26`×732, `JUN-26-27`×694, `MAY-26-27`×657, `DEC-25-26`×636, `MAR-25-26`×587, `JUL-26-27`×587, `AUG-25-26`×586, `APR-26-27`×580, `JUL-25-26`×575, `SEP-25-26`×568, `Jan-24-25`×521, `OCT-25-26`×493, `JUN-25-26`×477, `Nov-24-25`×453, `Oct-24-25`×447, `Feb-24-25`×437, `NOV-25-26`×422, `Dec-24-25`×421, `Mar-24-25`×380, `APR-25-26`×372, `AUG-26-27`×354, `MAY-25-26`×338, `Sep-24-25`×1
- **`UseShpdGd`** (1 values) — `N`×12,204
- **`DocSubType`** (1 values) — `--`×12,204
- **`DpmStatus`** (1 values) — `O`×12,204
- **`DpmDrawn`** (1 values) — `N`×12,204
- **`Posted`** (1 values) — `Y`×12,204
- **`isIns`** (1 values) — `N`×12,204
- **`VersionNum`** (2 values) — `10.00.250.15`×6,737, `10.00.310.21`×5,467
- **`LangCode`** (2 values) — `NULL`×12,197, `8`×7
- **`BPNameOW`** (1 values) — `N`×12,204
- **`BillToOW`** (1 values) — `N`×12,204
- **`ShipToOW`** (1 values) — `N`×12,204
- **`RetInvoice`** (1 values) — `N`×12,204
- **`Model`** (1 values) — `0`×12,204
- **`UseCorrVat`** (1 values) — `N`×12,204
- **`BlkCredMmo`** (1 values) — `N`×12,204
- **`OpenForLaC`** (1 values) — `Y`×12,204
- **`Excised`** (1 values) — `O`×12,204
- **`SrvGpPrcnt`** (2 values) — `NULL`×11,914, `100.000000`×290
- **`DutyStatus`** (2 values) — `Y`×12,203, `N`×1
- **`AutoCrtFlw`** (1 values) — `N`×12,204
- **`VatJENum`** (2 values) — `-1`×12,038, `0`×166
- **`InsurOp347`** (1 values) — `N`×12,204
- **`IgnRelDoc`** (1 values) — `N`×12,204
- **`ResidenNum`** (1 values) — `1`×12,204
- **`PQTGrpHW`** (1 values) — `N`×12,204
- **`DocManClsd`** (1 values) — `N`×12,204
- **`ClosingOpt`** (1 values) — `1`×12,204
- **`Ordered`** (1 values) — `N`×12,204
- **`NTSApprov`** (1 values) — `N`×12,204
- **`EDocGenTyp`** (1 values) — `N`×12,204
- **`OnlineQuo`** (1 values) — `N`×12,204
- **`EDocStatus`** (1 values) — `C`×12,204
- **`EDocProces`** (1 values) — `C`×12,204
- **`EDocCancel`** (1 values) — `N`×12,204
- **`EDocTest`** (1 values) — `N`×12,204
- **`DpmAsDscnt`** (1 values) — `N`×12,204
- **`AtcEntry`** (10 values) — `NULL`×12,195, `131065`×1, `73921`×1, `124092`×1, `81296`×1, `131067`×1, `130831`×1, `131919`×1, `133188`×1, `133280`×1
- **`GTSRlvnt`** (1 values) — `N`×12,204
- **`SrvTaxRule`** (1 values) — `N`×12,204
- **`ReqType`** (1 values) — `12`×12,204
- **`OriginType`** (1 values) — `M`×12,204
- **`IsReuseNum`** (1 values) — `N`×12,204
- **`IsReuseNFN`** (1 values) — `N`×12,204
- **`DocDlvry`** (1 values) — `0`×12,204
- **`EnvTypeNFe`** (1 values) — `-1`×12,204
- **`IsAlt`** (1 values) — `N`×12,204
- **`AltBaseTyp`** (1 values) — `-1`×12,204
- **`PrintSEPA`** (1 values) — `N`×12,204
- **`RelatedTyp`** (1 values) — `-1`×12,204
- **`PoDropPrss`** (1 values) — `N`×12,204
- **`ExclTaxRep`** (1 values) — `N`×12,204
- **`Revision`** (1 values) — `N`×12,204
- **`GSTTranTyp`** (2 values) — `--`×11,998, `GA`×206
- **`BaseType`** (1 values) — `-1`×12,204
- **`ComTrade`** (1 values) — `E`×12,204
- **`UseBilAddr`** (3 values) — `NULL`×12,197, `N`×6, `Y`×1
- **`IssReason`** (1 values) — `1`×12,204
- **`ComTradeRt`** (1 values) — `N`×12,204
- **`SplitPmnt`** (1 values) — `N`×12,204
- **`SelfPosted`** (1 values) — `N`×12,204
- **`DPPStatus`** (1 values) — `N`×12,204
- **`EWBGenType`** (2 values) — `NULL`×11,471, `N`×733
- **`EDocType`** (1 values) — `F`×12,204
- **`AggregDoc`** (1 values) — `N`×12,204
- **`DataVers`** (27 values) — `1`×11,812, `2`×290, `3`×48, `4`×10, `8`×8, `7`×7, `5`×5, `6`×4, `34`×2, `10`×1, `21`×1, `16`×1, `26`×1, `22`×1, `31`×1, `19`×1, `9`×1, `36`×1, `28`×1, `35`×1, `24`×1, `13`×1, `30`×1, `18`×1, `46`×1, `12`×1, `57`×1
- **`IndFinal`** (1 values) — `N`×12,204
- **`PostPmntWT`** (1 values) — `N`×12,204
- **`FCEPmnMean`** (1 values) — `N`×12,204
- **`NotRel4MI`** (1 values) — `N`×12,204
- **`Rel4PPTax`** (1 values) — `N`×12,204
- **`BookeTdsBP`** (1 values) — `N`×12,204
- **`DigPayment`** (1 values) — `N`×12,204
- **`RShipToOW`** (1 values) — `N`×12,204
- **`AplTaxOnFr`** (2 values) — `NULL`×6,218, `N`×5,986
- **`CpyDtyStts`** (1 values) — `N`×12,204
- **`U_Basement`** (3 values) — `NULL`×12,200, `Y`×3, `N`×1
- **`U_First_Floor`** (2 values) — `NULL`×12,203, `Y`×1
- **`U_TransporterInvoice`** (3 values) — `NULL`×12,199, `.`×4, `na`×1
- **`U_AR_NO`** (29 values) — `NULL`×12,139, `42563`×8, `42101`×6, `42541`×6, `42760`×6, `40816`×4, `227813`×3, `602507-B`×3, `41802`×3, `0016`×2, `42961`×2, `41914`×2, `602411`×2, `602507-A`×2, `227361`×2, `ES24-016457`×1, `42398`×1, `ES24-024262`×1, `ES24-021025`×1, `227816`×1, `1198`×1, `227729`×1, `41680`×1, `42326`×1, `1197`×1, `1186`×1, `ES25-002298`×1, `ES25-018510`×1, `ES24-017395`×1
- **`U_InvRevEntry`** (10 values) — `NULL`×12,195, `MEDUCD999982`×1, `HDMUBCNA96975100`×1, `259807383`×1, `HDMUBCNA20019600`×1, `HDMUALGA51384400`×1, `HDMUALGA29756000`×1, `MEDUCD929781`×1, `MEDUCD905369`×1, `MAXSOK00242425`×1
- **`U_UNE_BRCH`** (2 values) — `NULL`×12,198, `KUNDLI`×6
- **`U_UNE_ACTH`** (18 values) — `NULL`×9,856, `1102007`×2,254, `2120002`×54, `5100013`×9, `1107006`×6, `5300015`×5, `4110001`×3, `1103000`×3, `4140003`×2, `4160000`×2, `4150001`×2, `1100207`×2, `1102005`×1, `4110007`×1, `1110100`×1, `1102001`×1, `2161009`×1, `110207`×1
- **`U_ARNO`** (2 values) — `NULL`×12,203, `12`×1
- **`U_OMS_Order_No`** (2 values) — `NULL`×12,203, `1254`×1
- **`U_DisDE`** (2 values) — `NULL`×12,203, `4848`×1
- **`U_DisDN`** (2 values) — `NULL`×12,203, `4848`×1
- **`U_Production_Order`** (20 values) — `NULL`×12,180, `8739`×2, `8705`×2, `8700`×2, `8702`×2, `8703`×2, `8709`×1, `8776`×1, `8777`×1, `8742`×1, `8744`×1, `8721`×1, `8781`×1, `8736`×1, `8743`×1, `8711`×1, `8723`×1, `8710`×1, `8780`×1, `8715`×1
- **`U_PRODUCTION_DATE`** (2 values) — `NULL`×12,202, `2025-10-01 00:00:00.0000000`×2
- **`U_SALES_PERSON`** (3 values) — `NULL`×12,202, `PRIVATE`×1, `PUNJAB MT`×1
