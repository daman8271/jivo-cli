# `OPCH` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 16,334 | 2,051 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 4,864 | 930 | `DocDate` | 2025-01-01 → 2026-08-24 |
| BEV | 3,170 | 431 | `DocDate` | 2024-10-01 → 2026-08-07 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 16,334 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 16,327 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 684 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 918 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 1,161 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 1,177 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 1,003 | |
| `NumAtCard` | NVARCHAR(200) | 100% | 100% | 100% | 99% | 100% | 99% | 15,209 | |
| `VatSum` | DECIMAL | 56% | 86% | 45% | 59% | 80% | 48% | 7,082 | |
| `DiscPrcnt` | DECIMAL | <1% | — | <1% | — | — | — | 15 | |
| `DiscSum` | DECIMAL | <1% | — | <1% | — | — | — | 54 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 72 | |
| `DocTotal` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 10,871 | |
| `DocTotalFC` | DECIMAL | <1% | <1% | — | <1% | — | — | 93 | |
| `PaidToDate` | DECIMAL | 75% | 44% | 84% | 56% | 30% | 36% | 8,458 | |
| `PaidFC` | DECIMAL | <1% | <1% | — | — | — | — | 44 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 16,327 | |
| `Comments` | NVARCHAR(254) | 98% | 78% | 98% | 87% | 81% | 88% | 15,566 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 1,213 | |
| `TransId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 16,334 | |
| `ReceiptNum` | INTEGER | 46% | 36% | 39% | 44% | 23% | 33% | 3,615 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 710 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 91 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 78% | 98% | 80% | 82% | 97% | 83% | 1,066 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `VatSumSy` | DECIMAL | 56% | 86% | 45% | 59% | 80% | 48% | 7,082 | |
| `DiscSumSy` | DECIMAL | <1% | — | <1% | — | — | — | 54 | |
| `DocTotalSy` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 10,871 | |
| `PaidSys` | DECIMAL | 75% | 44% | 84% | 56% | 30% | 36% | 8,458 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 564 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 220 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 1,043 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 19 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | 38% | 32% | 37% | 37% | 17% | 17% | 4,578 | |
| `VatPaidFC` | DECIMAL | <1% | — | — | — | — | — | 2 | |
| `VatPaidSys` | DECIMAL | 38% | 32% | 37% | 37% | 17% | 17% | 4,596 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `draftKey` | INTEGER | 87% | 69% | 97% | 98% | 67% | 97% | 14,264 | |
| `TotalExpns` | DECIMAL | 6% | 2% | 5% | 1% | — | <1% | 847 | |
| `TotalExpSC` | DECIMAL | 6% | 2% | 5% | 1% | — | <1% | 847 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 55 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 873 | |
| `WTSum` | DECIMAL | 38% | 79% | 23% | 38% | 75% | 35% | 2,111 | |
| `WTSumFC` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `WTSumSC` | DECIMAL | 38% | 79% | 23% | 38% | 75% | 35% | 2,111 | |
| `RoundDif` | DECIMAL | 48% | 60% | 33% | 53% | 46% | 43% | 2,543 | |
| `RoundDifSy` | DECIMAL | 48% | 60% | 33% | 53% | 46% | 43% | 2,543 | |
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
| `Max1099` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 11,833 | |
| `ExpAppl` | DECIMAL | 1% | <1% | 4% | <1% | — | <1% | 113 | |
| `ExpApplSC` | DECIMAL | 1% | <1% | 4% | <1% | — | <1% | 113 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WTApplied` | DECIMAL | <1% | 7% | 1% | 1% | 1% | <1% | 135 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WTAppliedS` | DECIMAL | <1% | 7% | 1% | 1% | 1% | <1% | 135 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NnSbAmnt` | DECIMAL | 1% | <1% | 2% | 2% | 2% | 2% | 170 | |
| `NnSbAmntSC` | DECIMAL | 1% | <1% | 2% | 2% | 2% | 2% | 170 | |
| `ExepAmnt` | DECIMAL | — | <1% | — | — | 1% | — | 1 | |
| `ExepAmntSC` | DECIMAL | — | <1% | — | — | 1% | — | 1 | |
| `ExepAmntFC` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseAmnt` | DECIMAL | 38% | 80% | 23% | 38% | 76% | 35% | 5,105 | |
| `BaseAmntSC` | DECIMAL | 38% | 80% | 23% | 38% | 76% | 35% | 5,105 | |
| `BaseAmntFC` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 14 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PaidSum` | DECIMAL | 73% | 40% | 83% | 55% | 28% | 33% | 8,413 | |
| `PaidSumFc` | DECIMAL | <1% | <1% | — | — | — | — | 44 | |
| `PaidSumSc` | DECIMAL | 73% | 40% | 83% | 55% | 28% | 33% | 8,413 | |
| `Header` | NCLOB | <1% | — | — | — | — | — | 0 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OwnerCode` | INTEGER | <1% | — | <1% | <1% | — | <1% | 4 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 100% | 100% | 857 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxOnExp` | DECIMAL | 4% | 2% | 5% | 1% | — | <1% | 622 | |
| `TaxOnExpSc` | DECIMAL | 4% | 2% | 5% | 1% | — | <1% | 622 | |
| `TaxOnExAp` | DECIMAL | <1% | <1% | 2% | <1% | — | <1% | 60 | |
| `TaxOnExApS` | DECIMAL | <1% | <1% | 2% | <1% | — | <1% | 60 | |
| `LastPmnTyp` | NVARCHAR(1) | 46% | 36% | 39% | 44% | 23% | 33% | 2 | |
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
| `ExtraDays` | SMALLINT | 41% | 22% | 50% | 33% | 21% | 40% | 9 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 88% | 97% | 97% | 99% | 95% | 97% | 14,317 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDiscPr` | DECIMAL | <1% | — | <1% | — | — | — | 13 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12,554 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12,592 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AssetDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 684 | |
| `Notify` | NVARCHAR(1) | 41% | 16% | 38% | 47% | 20% | 30% | 1 | |
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
| `RevRefNo` | NVARCHAR(100) | <1% | <1% | — | <1% | <1% | — | 39 | |
| `RevRefDate` | TIMESTAMP | <1% | <1% | — | <1% | <1% | — | 38 | |
| `TaxInvNo` | NVARCHAR(100) | <1% | <1% | — | <1% | — | — | 70 | |
| `FrmBpDate` | TIMESTAMP | <1% | <1% | — | <1% | — | — | 41 | |
| `GSTTranTyp` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseEntry` | INTEGER | 1% | 1% | 1% | 1% | 5% | 3% | 168 | |
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
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 11 | |
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
| `U_deldocnum` | NVARCHAR(100) | 5% | 2% | 2% | — | — | — | 743 | |
| `U_deldocdate` | TIMESTAMP | 5% | 2% | 2% | — | — | — | 260 | |
| `U_delbranch` | NVARCHAR(100) | 5% | 2% | 2% | — | — | — | 3 | |
| `U_delbranchnam` | NVARCHAR(100) | 5% | 2% | 2% | — | — | — | 3 | |
| `U_GRNWhsCode` | NVARCHAR(8) | <1% | — | — | — | — | — | 1 | |
| `U_BilltyNumber` | NVARCHAR(15) | 7% | — | n/a | 11% | — | n/a | 1,004 | |
| `U_BiltyDate` | TIMESTAMP | 7% | — | <1% | 11% | — | <1% | 471 | |
| `U_TransporterName` | NVARCHAR(50) | 7% | — | <1% | 11% | — | <1% | 155 | |
| `U_VehicleNoM` | NVARCHAR(12) | 7% | — | n/a | 11% | — | n/a | 258 | |
| `U_DriverName` | NCLOB | <1% | — | — | — | — | — | 0 | |
| `U_TransporterInvoice` | NVARCHAR(15) | <1% | — | <1% | <1% | — | <1% | 1 | |
| `U_Mob_No` | NVARCHAR(12) | <1% | — | — | — | — | — | 1 | |
| `U_AR_NO` | NVARCHAR(12) | 4% | — | n/a | 2% | — | n/a | 97 | |
| `U_InvRevEntry` | NVARCHAR(20) | 1% | — | — | <1% | — | — | 60 | |
| `U_LRNUmber` | NVARCHAR(15) | 5% | — | n/a | 2% | — | n/a | 99 | |
| `U_BOEDate` | TIMESTAMP | 5% | — | n/a | 2% | — | n/a | 74 | |
| `U_UNE_SCTY` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 1 | |
| `U_UNE_SO` | NVARCHAR(100) | — | <1% | — | — | — | — | 0 | |
| `U_UNE_MLOC` | NVARCHAR(100) | <1% | <1% | — | — | <1% | — | 3 | |
| `U_UNE_ACTH` | NVARCHAR(100) | <1% | 1% | 99% | 1% | 5% | 100% | 3 | |
| `U_TotalAmt` | DECIMAL | <1% | — | <1% | <1% | — | <1% | 4 | |
| `U_ARNO` | NVARCHAR(100) | <1% | — | <1% | <1% | — | <1% | 38 | |
| `U_SALES_PERSON` | NVARCHAR(20) | <1% | n/a | n/a | — | n/a | n/a | 2 | |
| `U_TDS_LINK` | INTEGER | — | <1% | n/a | — | <1% | n/a | 0 | |

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

- **`DocType`** (2 values) — `S`×9,562, `I`×6,772
- **`CANCELED`** (3 values) — `N`×16,108, `C`×113, `Y`×113
- **`Handwrtten`** (2 values) — `N`×15,385, `Y`×949
- **`Printed`** (2 values) — `N`×15,293, `Y`×1,041
- **`DocStatus`** (2 values) — `C`×12,025, `O`×4,309
- **`InvntSttus`** (2 values) — `C`×9,677, `O`×6,657
- **`Transfered`** (1 values) — `N`×16,334
- **`ObjType`** (1 values) — `18`×16,334
- **`DiscPrcnt`** (16 values) — `0.000000`×16,292, `NULL`×28, `0.001055`×1, `0.007739`×1, `0.003614`×1, `-0.000169`×1, `0.000271`×1, `1.950000`×1, `0.000529`×1, `0.001243`×1, `-0.000684`×1, `16.037211`×1, `0.003082`×1, `-0.002130`×1, `22.958364`×1, `-0.000057`×1
- **`DocCur`** (4 values) — `INR`×16,237, `USD`×73, `EUR`×22, `AUD`×2
- **`GroupNum`** (12 values) — `-1`×9,629, `1`×5,278, `21`×487, `19`×252, `22`×226, `20`×164, `16`×134, `18`×118, `17`×32, `4`×9, `7`×4, `3`×1
- **`TrnspCode`** (1 values) — `-1`×16,334
- **`PartSupply`** (1 values) — `Y`×16,334
- **`Confirmed`** (1 values) — `Y`×16,334
- **`GrossBase`** (3 values) — `-6`×15,415, `-1`×842, `-10`×77
- **`CreateTran`** (1 values) — `Y`×16,334
- **`SummryType`** (1 values) — `N`×16,334
- **`UpdInvnt`** (1 values) — `I`×16,334
- **`UpdCardBal`** (1 values) — `B`×16,334
- **`InvntDirec`** (1 values) — `E`×16,334
- **`ShowSCN`** (1 values) — `N`×16,334
- **`SysRate`** (1 values) — `1.000000`×16,334
- **`CurSource`** (3 values) — `L`×16,223, `C`×97, `S`×14
- **`FatherType`** (1 values) — `P`×16,334
- **`IsICT`** (1 values) — `N`×16,334
- **`VolUnit`** (1 values) — `4`×16,334
- **`WeightUnit`** (1 values) — `3`×16,334
- **`isCrin`** (1 values) — `N`×16,334
- **`FinncPriod`** (24 values) — `12`×1,037, `6`×949, `10`×855, `8`×821, `20`×783, `25`×778, `17`×774, `43`×740, `11`×734, `18`×732, `7`×692, `23`×691, `15`×677, `22`×676, `16`×662, `24`×662, `21`×627, `9`×612, `19`×610, `42`×606, `44`×535, `14`×503, `41`×492, `45`×86
- **`UserSign`** (19 values) — `17`×4,164, `16`×4,014, `18`×2,925, `15`×1,850, `1`×990, `22`×864, `53`×581, `11`×386, `20`×134, `24`×95, `48`×91, `39`×63, `46`×51, `13`×45, `38`×40, `40`×27, `12`×7, `47`×6, `10`×1
- **`selfInv`** (1 values) — `N`×16,334
- **`VatPaidFC`** (2 values) — `0.000000`×16,333, `541216.095000`×1
- **`WddStatus`** (2 values) — `P`×14,250, `-`×2,084
- **`Exported`** (1 values) — `N`×16,334
- **`NetProc`** (1 values) — `N`×16,334
- **`submitted`** (1 values) — `N`×16,334
- **`PoPrss`** (1 values) — `N`×16,334
- **`Rounding`** (2 values) — `N`×9,550, `Y`×6,784
- **`RevisionPo`** (1 values) — `N`×16,334
- **`PickStatus`** (1 values) — `N`×16,334
- **`Pick`** (1 values) — `N`×16,334
- **`BlockDunn`** (1 values) — `N`×16,334
- **`PayBlock`** (1 values) — `N`×16,334
- **`MaxDscn`** (1 values) — `N`×16,334
- **`Reserve`** (1 values) — `N`×16,334
- **`DeferrTax`** (1 values) — `N`×16,334
- **`BoeReserev`** (1 values) — `N`×16,334
- **`Installmnt`** (1 values) — `1`×16,334
- **`VATFirst`** (1 values) — `N`×16,334
- **`CEECFlag`** (2 values) — `N`×15,348, `Y`×986
- **`CtlAccount`** (14 values) — `2110004`×6,800, `2110005`×3,661, `2110003`×2,911, `2110001`×1,545, `2120002`×741, `2110008`×243, `2120006`×186, `2110002`×83, `2120001`×77, `2121002`×44, `2110006`×15, `2110007`×14, `2121003`×7, `2121001`×7
- **`BPLId`** (6 values) — `2`×9,558, `1`×4,220, `5`×1,513, `3`×639, `6`×395, `4`×9
- **`BPLName`** (6 values) — `FACTORY`×9,558, `DELHI`×4,220, `HARYANA SALES`×1,513, `PUNJAB`×639, `DELHI ISD`×395, `HIMACHAL PRADESH`×9
- **`VATRegNum`** (5 values) — `06AACCJ4223F1Z0`×11,071, `07AACCJ4223F1ZY`×4,220, `03AACCJ4223F1Z6`×639, `07AACCJ4223F2ZX`×395, `02AACCJ4223F1Z8`×9
- **`SumAbsId`** (1 values) — `-1`×16,334
- **`PIndicator`** (24 values) — `Mar-24-25`×1,037, `Sep-24-25`×949, `Jan-24-25`×855, `Nov-24-25`×821, `OCT-25-26`×783, `MAR-25-26`×778, `JUL-25-26`×774, `JUN-26-27`×740, `Feb-24-25`×734, `AUG-25-26`×732, `Oct-24-25`×692, `JAN-25-26`×691, `MAY-25-26`×677, `DEC-25-26`×676, `FEB-25-26`×662, `JUN-25-26`×662, `NOV-25-26`×627, `Dec-24-25`×612, `SEP-25-26`×610, `MAY-26-27`×606, `JUL-26-27`×535, `APR-25-26`×503, `APR-26-27`×492, `AUG-26-27`×86
- **`UseShpdGd`** (1 values) — `N`×16,334
- **`DocSubType`** (3 values) — `GA`×10,391, `--`×5,902, `GD`×41
- **`DpmStatus`** (1 values) — `O`×16,334
- **`DpmDrawn`** (1 values) — `N`×16,334
- **`Posted`** (1 values) — `Y`×16,334
- **`OwnerCode`** (5 values) — `NULL`×16,217, `14`×59, `20`×55, `2`×2, `4`×1
- **`IsPaytoBnk`** (1 values) — `N`×16,334
- **`isIns`** (1 values) — `N`×16,334
- **`VersionNum`** (2 values) — `10.00.250.15`×11,054, `10.00.310.21`×5,280
- **`LangCode`** (1 values) — `8`×16,334
- **`BPNameOW`** (2 values) — `N`×16,332, `Y`×2
- **`BillToOW`** (2 values) — `N`×16,333, `Y`×1
- **`ShipToOW`** (2 values) — `N`×14,974, `Y`×1,360
- **`RetInvoice`** (1 values) — `N`×16,334
- **`Model`** (1 values) — `0`×16,334
- **`LastPmnTyp`** (3 values) — `NULL`×8,834, `V`×7,388, `R`×112
- **`UseCorrVat`** (1 values) — `N`×16,334
- **`BlkCredMmo`** (1 values) — `N`×16,334
- **`OpenForLaC`** (1 values) — `Y`×16,334
- **`Excised`** (1 values) — `O`×16,334
- **`DutyStatus`** (1 values) — `Y`×16,334
- **`AutoCrtFlw`** (1 values) — `N`×16,334
- **`VatJENum`** (1 values) — `-1`×16,334
- **`InsurOp347`** (1 values) — `N`×16,334
- **`IgnRelDoc`** (1 values) — `N`×16,334
- **`ResidenNum`** (1 values) — `1`×16,334
- **`PQTGrpHW`** (1 values) — `N`×16,334
- **`DocManClsd`** (1 values) — `N`×16,334
- **`ClosingOpt`** (1 values) — `1`×16,334
- **`Ordered`** (1 values) — `N`×16,334
- **`NTSApprov`** (1 values) — `N`×16,334
- **`PayDuMonth`** (1 values) — `N`×16,334
- **`ExtraDays`** (9 values) — `0`×9,643, `30`×5,278, `25`×487, `15`×252, `35`×226, `21`×164, `5`×134, `10`×118, `7`×32
- **`EDocGenTyp`** (1 values) — `N`×16,334
- **`OnlineQuo`** (1 values) — `N`×16,334
- **`EDocStatus`** (1 values) — `C`×16,334
- **`EDocProces`** (1 values) — `C`×16,334
- **`EDocCancel`** (1 values) — `N`×16,334
- **`EDocTest`** (1 values) — `N`×16,334
- **`DpmAsDscnt`** (1 values) — `N`×16,334
- **`GTSRlvnt`** (1 values) — `N`×16,334
- **`BaseDiscPr`** (13 values) — `0.000000`×16,322, `-0.000684`×1, `0.003614`×1, `0.001243`×1, `0.002190`×1, `-0.000057`×1, `0.003082`×1, `0.000529`×1, `1.950000`×1, `0.000271`×1, `-0.000169`×1, `0.001055`×1, `0.007739`×1
- **`SrvTaxRule`** (1 values) — `N`×16,334
- **`Notify`** (2 values) — `NULL`×9,620, `N`×6,714
- **`ReqType`** (1 values) — `12`×16,334
- **`OriginType`** (1 values) — `M`×16,334
- **`IsReuseNum`** (1 values) — `N`×16,334
- **`IsReuseNFN`** (1 values) — `N`×16,334
- **`DocDlvry`** (1 values) — `0`×16,334
- **`EnvTypeNFe`** (1 values) — `-1`×16,334
- **`IsAlt`** (1 values) — `N`×16,334
- **`AltBaseTyp`** (1 values) — `-1`×16,334
- **`PrintSEPA`** (1 values) — `N`×16,334
- **`RelatedTyp`** (1 values) — `-1`×16,334
- **`PoDropPrss`** (1 values) — `N`×16,334
- **`ExclTaxRep`** (1 values) — `N`×16,334
- **`Revision`** (1 values) — `N`×16,334
- **`GSTTranTyp`** (3 values) — `GA`×10,391, `--`×5,902, `GD`×41
- **`BaseType`** (2 values) — `-1`×16,162, `67`×172
- **`ComTrade`** (1 values) — `E`×16,334
- **`UseBilAddr`** (2 values) — `N`×14,615, `Y`×1,719
- **`IssReason`** (2 values) — `1`×16,333, `3`×1
- **`ComTradeRt`** (1 values) — `N`×16,334
- **`SplitPmnt`** (1 values) — `N`×16,334
- **`SelfPosted`** (1 values) — `N`×16,334
- **`DPPStatus`** (1 values) — `N`×16,334
- **`EWBGenType`** (2 values) — `L`×10,711, `N`×5,623
- **`EDocType`** (1 values) — `F`×16,334
- **`AggregDoc`** (1 values) — `N`×16,334
- **`DataVers`** (11 values) — `1`×8,341, `2`×6,496, `3`×791, `4`×440, `5`×140, `6`×75, `7`×28, `8`×11, `9`×9, `10`×2, `11`×1
- **`IndFinal`** (1 values) — `N`×16,334
- **`PostPmntWT`** (1 values) — `N`×16,334
- **`FCEPmnMean`** (1 values) — `N`×16,334
- **`NotRel4MI`** (1 values) — `N`×16,334
- **`Rel4PPTax`** (1 values) — `N`×16,334
- **`BookeTdsBP`** (1 values) — `N`×16,334
- **`DigPayment`** (1 values) — `N`×16,334
- **`PDueMonEnd`** (1 values) — `N`×16,334
- **`RShipToOW`** (1 values) — `N`×16,334
- **`AplTaxOnFr`** (1 values) — `N`×16,334
- **`CpyDtyStts`** (1 values) — `N`×16,334
- **`U_Recv_Date`** (2 values) — `NULL`×16,332, `2024-10-03 00:00:00.0000000`×2
- **`U_delbranch`** (4 values) — `NULL`×15,518, `2`×613, `3`×149, `1`×54
- **`U_delbranchnam`** (4 values) — `NULL`×15,518, `FACTORY`×613, `PUNJAB`×149, `DELHI`×54
- **`U_GRNWhsCode`** (2 values) — `NULL`×16,333, `BH-GJ`×1
- **`U_TransporterInvoice`** (2 values) — `NULL`×16,333, `626050630`×1
- **`U_Mob_No`** (2 values) — `NULL`×16,333, `8950357509`×1
- **`U_UNE_SCTY`** (2 values) — `NULL`×16,333, `+`×1
- **`U_UNE_ACTH`** (4 values) — `NULL`×16,179, `1102007`×153, `1102001`×1, `CC30/2025-26`×1
- **`U_TotalAmt`** (5 values) — `0.000000`×16,003, `NULL`×328, `40286.000000`×1, `16296.000000`×1, `89.000000`×1
- **`U_SALES_PERSON`** (3 values) — `NULL`×16,332, `PRIVATE`×1, `PUNJAB MT`×1
