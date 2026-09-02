# `ODRF` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 49,463 | 8,965 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 14,683 | 2,808 | `DocDate` | 2025-01-01 → 2026-08-24 |
| BEV | 14,346 | 3,010 | `DocDate` | 2024-09-30 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 49,463 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23,653 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 14 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 692 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 723 | |
| `CardCode` | NVARCHAR(15) | 77% | 91% | 85% | 74% | 90% | 84% | 1,492 | |
| `CardName` | NVARCHAR(200) | 77% | 91% | 85% | 74% | 90% | 84% | 1,476 | |
| `Address` | NVARCHAR(254) | 77% | 91% | 85% | 74% | 90% | 84% | 1,441 | |
| `NumAtCard` | NVARCHAR(200) | 52% | 71% | 32% | 44% | 81% | 22% | 18,033 | |
| `VatSum` | DECIMAL | 54% | 72% | 67% | 56% | 76% | 72% | 16,333 | |
| `VatSumFC` | DECIMAL | — | — | <1% | — | — | — | 1 | |
| `DiscPrcnt` | DECIMAL | <1% | 8% | <1% | — | — | — | 57 | |
| `DiscSum` | DECIMAL | <1% | 8% | <1% | <1% | <1% | — | 109 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `DocRate` | DECIMAL | 77% | 97% | 84% | 77% | 93% | 84% | 53 | |
| `DocTotal` | DECIMAL | 92% | 87% | 98% | 92% | 96% | 99% | 28,734 | |
| `DocTotalFC` | DECIMAL | <1% | <1% | <1% | <1% | — | — | 80 | |
| `PaidToDate` | DECIMAL | <1% | — | — | — | — | — | 9 | |
| `GrosProfit` | DECIMAL | 24% | 36% | 46% | 30% | 35% | 59% | 8,929 | |
| `GrosProfFC` | DECIMAL | <1% | — | <1% | — | — | — | 6 | |
| `Ref1` | NVARCHAR(11) | 5% | 2% | 2% | 4% | 7% | 3% | 1,521 | |
| `Comments` | NVARCHAR(254) | 75% | 84% | 79% | 70% | 82% | 85% | 32,842 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 2,620 | |
| `TransId` | INTEGER | <1% | <1% | — | — | — | — | 3 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 19 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1,050 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 112 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 99% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CntctCode` | INTEGER | 66% | 88% | 79% | 68% | 88% | 81% | 1,405 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `VatSumSy` | DECIMAL | 54% | 72% | 67% | 56% | 76% | 72% | 16,333 | |
| `DiscSumSy` | DECIMAL | <1% | 8% | <1% | <1% | <1% | — | 109 | |
| `DocTotalSy` | DECIMAL | 92% | 87% | 98% | 92% | 96% | 99% | 28,734 | |
| `PaidSys` | DECIMAL | <1% | — | — | — | — | — | 9 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrosProfSy` | DECIMAL | 24% | 36% | 46% | 30% | 35% | 59% | 8,929 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 635 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 597 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 762 | |
| `Filler` | NVARCHAR(8) | 25% | 10% | 16% | 26% | 12% | 16% | 36 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 37 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | <1% | — | — | — | — | — | 7 | |
| `VatPaidSys` | DECIMAL | <1% | — | — | — | — | — | 7 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `draftKey` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 153 | |
| `TotalExpns` | DECIMAL | <1% | 1% | 2% | <1% | <1% | <1% | 130 | |
| `TotalExpSC` | DECIMAL | <1% | 1% | 2% | <1% | <1% | <1% | 130 | |
| `Address2` | NVARCHAR(254) | 75% | 90% | 84% | 74% | 88% | 84% | 607 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 124 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 77% | 91% | 84% | 74% | 90% | 84% | 1,481 | |
| `WTSum` | DECIMAL | 13% | 20% | 5% | 10% | 18% | 6% | 2,098 | |
| `WTSumFC` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `WTSumSC` | DECIMAL | 13% | 20% | 5% | 10% | 18% | 6% | 2,098 | |
| `RoundDif` | DECIMAL | 43% | 49% | 56% | 43% | 52% | 66% | 4,982 | |
| `RoundDifFC` | DECIMAL | <1% | — | — | — | — | — | 4 | |
| `RoundDifSy` | DECIMAL | 43% | 49% | 56% | 43% | 52% | 66% | 4,982 | |
| `submitted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rounding` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RevisionPo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReqDate` | TIMESTAMP | <1% | <1% | <1% | — | <1% | — | 17 | |
| `CancelDate` | TIMESTAMP | <1% | <1% | <1% | — | <1% | — | 17 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Pick` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlockDunn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayBlock` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `MaxDscn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Reserve` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Max1099` | DECIMAL | 4% | 2% | 2% | 3% | 7% | 3% | 1,074 | |
| `DeferrTax` | NVARCHAR(1) | 99% | 97% | 100% | 97% | 94% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 77% | 96% | 84% | 74% | 93% | 84% | 1 | |
| `NnSbAmnt` | DECIMAL | 2% | 2% | 1% | 2% | 2% | 1% | 753 | |
| `NnSbAmntSC` | DECIMAL | 2% | 2% | 1% | 2% | 2% | 1% | 753 | |
| `NbSbAmntFC` | DECIMAL | — | <1% | — | — | <1% | — | 1 | |
| `ExepAmnt` | DECIMAL | — | <1% | — | — | <1% | — | 1 | |
| `ExepAmntSC` | DECIMAL | — | <1% | — | — | <1% | — | 1 | |
| `ExepAmntFC` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseAmnt` | DECIMAL | 14% | 21% | 6% | 11% | 19% | 6% | 5,564 | |
| `BaseAmntSC` | DECIMAL | 14% | 21% | 6% | 11% | 19% | 6% | 5,564 | |
| `BaseAmntFC` | DECIMAL | — | <1% | — | — | — | — | 1 | |
| `CtlAccount` | NVARCHAR(15) | 58% | 65% | 69% | 60% | 64% | 78% | 32 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 9 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `WTDetails` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 3 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Header` | NCLOB | <1% | — | — | — | — | — | 0 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OwnerCode` | INTEGER | 2% | — | <1% | 5% | — | <1% | 4 | |
| `PayToCode` | NVARCHAR(50) | 75% | 90% | 84% | 74% | 88% | 84% | 1,395 | |
| `IsPaytoBnk` | NVARCHAR(1) | 75% | 90% | 84% | 74% | 88% | 84% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 75% | 90% | 84% | 74% | 88% | 84% | 2 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxOnExp` | DECIMAL | <1% | 1% | 2% | <1% | <1% | <1% | 108 | |
| `TaxOnExpSc` | DECIMAL | <1% | 1% | 2% | <1% | <1% | <1% | 108 | |
| `UseCorrVat` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlkCredMmo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OpenForLaC` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Excised` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SrvGpPrcnt` | DECIMAL | <1% | — | <1% | — | — | — | 2 | |
| `DutyStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AutoCrtFlw` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatJENum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InsurOp347` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IgnRelDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PQTGrpHW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReopOriDoc` | NVARCHAR(1) | 9% | 14% | 6% | 8% | 12% | 5% | 2 | |
| `ReopManCls` | NVARCHAR(1) | <1% | 1% | <1% | — | <1% | <1% | 1 | |
| `DocManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ClosingOpt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayDuMonth` | NVARCHAR(1) | 75% | 90% | 84% | 74% | 88% | 84% | 1 | |
| `ExtraDays` | SMALLINT | 21% | 32% | 18% | 17% | 9% | 12% | 11 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AtcEntry` | INTEGER | 47% | 44% | 32% | 37% | 50% | 22% | 23,055 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseDiscPr` | DECIMAL | <1% | <1% | <1% | — | — | — | 17 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 28,028 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 28,093 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ToWhsCode` | NVARCHAR(8) | 25% | 10% | 16% | 26% | 12% | 16% | 37 | |
| `AssetDate` | TIMESTAMP | 55% | 57% | 67% | 58% | 58% | 75% | 690 | |
| `Notify` | NVARCHAR(1) | 18% | 11% | 11% | 16% | 10% | 6% | 1 | |
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
| `PoDropPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ExclTaxRep` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Revision` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevRefNo` | NVARCHAR(100) | 6% | 9% | 3% | 5% | 8% | 3% | 2,368 | |
| `RevRefDate` | TIMESTAMP | 6% | 9% | 3% | 5% | 8% | 3% | 747 | |
| `TaxInvNo` | NVARCHAR(100) | <1% | <1% | — | <1% | <1% | — | 77 | |
| `FrmBpDate` | TIMESTAMP | <1% | <1% | — | <1% | <1% | — | 46 | |
| `GSTTranTyp` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BaseEntry` | INTEGER | <1% | <1% | <1% | <1% | <1% | <1% | 14 | |
| `ComTrade` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UseBilAddr` | NVARCHAR(1) | 75% | 90% | 84% | 74% | 88% | 84% | 2 | |
| `IssReason` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `ComTradeRt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SplitPmnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SelfPosted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EWBGenType` | NVARCHAR(1) | 77% | 96% | 84% | 74% | 93% | 84% | 2 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QRCodeSrc` | NCLOB | <1% | — | — | — | — | — | 0 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 12 | |
| `ShipState` | NVARCHAR(3) | <1% | — | — | <1% | — | — | 1 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ConfrmedBy` | INTEGER | <1% | <1% | <1% | <1% | <1% | <1% | 11 | |
| `ConfrmedOn` | TIMESTAMP | <1% | <1% | <1% | <1% | <1% | <1% | 128 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 75% | 90% | 84% | 74% | 88% | 84% | 1 | |
| `RShipToCod` | NVARCHAR(50) | 1% | 1% | <1% | 3% | 3% | 1% | 87 | |
| `Address3` | NVARCHAR(254) | 3% | 4% | 2% | 8% | 12% | 5% | 106 | |
| `RShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `AplTaxOnFr` | NVARCHAR(1) | 87% | 98% | 90% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Dipatch_Date` | TIMESTAMP | 2% | <1% | 1% | 2% | <1% | <1% | 287 | |
| `U_Basement` | NVARCHAR(10) | 9% | — | 11% | <1% | — | <1% | 2 | |
| `U_First_Floor` | NVARCHAR(10) | 3% | — | <1% | — | — | — | 2 | |
| `U_GenType` | NVARCHAR(20) | <1% | — | — | — | — | — | 1 | |
| `U_UTL_ST_ADD` | NVARCHAR(100) | <1% | <1% | <1% | <1% | <1% | <1% | 5 | |
| `U_Recv_Date` | TIMESTAMP | <1% | <1% | <1% | — | — | <1% | 17 | |
| `U_deldocnum` | NVARCHAR(100) | <1% | 1% | — | — | — | — | 5 | |
| `U_deldocdate` | TIMESTAMP | <1% | 1% | — | — | — | — | 4 | |
| `U_delbranch` | NVARCHAR(100) | 2% | 2% | <1% | — | — | — | 4 | |
| `U_delbranchnam` | NVARCHAR(100) | 2% | 2% | <1% | — | — | — | 6 | |
| `U_GRNdocentry` | INTEGER | <1% | — | — | — | — | — | 1 | |
| `U_GRNCardCode` | NVARCHAR(15) | 1% | <1% | <1% | — | — | — | 6 | |
| `U_GRNWhsCode` | NVARCHAR(8) | 1% | <1% | <1% | — | — | — | 13 | |
| `U_Ship_From` | NVARCHAR(8) | <1% | <1% | — | — | — | — | 9 | |
| `U_BilltyNumber` | NVARCHAR(15) | 6% | <1% | n/a | 6% | <1% | n/a | 1,183 | |
| `U_BiltyDate` | TIMESTAMP | 6% | <1% | <1% | 6% | <1% | <1% | 541 | |
| `U_TransporterName` | NVARCHAR(50) | 6% | <1% | <1% | 6% | <1% | <1% | 254 | |
| `U_VehicleNoM` | NVARCHAR(12) | 6% | <1% | n/a | 7% | <1% | n/a | 379 | |
| `U_DriverName` | NCLOB | <1% | — | <1% | <1% | — | — | 0 | |
| `U_TransporterInvoice` | NVARCHAR(15) | <1% | — | <1% | <1% | — | <1% | 5 | |
| `U_Mob_No` | NVARCHAR(12) | <1% | <1% | <1% | <1% | <1% | <1% | 70 | |
| `U_Order_Date` | TIMESTAMP | 1% | — | <1% | 3% | — | 2% | 23 | |
| `U_AR_NO` | NVARCHAR(12) | 2% | <1% | n/a | <1% | — | n/a | 105 | |
| `U_InvRevEntry` | NVARCHAR(20) | <1% | — | — | <1% | — | — | 63 | |
| `U_LRNUmber` | NVARCHAR(15) | 2% | — | n/a | <1% | — | n/a | 105 | |
| `U_BOEDate` | TIMESTAMP | 2% | — | n/a | <1% | — | n/a | 78 | |
| `U_UNE_SCTY` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 1 | |
| `U_UNE_BRCH` | NVARCHAR(100) | <1% | — | — | — | — | — | 1 | |
| `U_UNE_AREA` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 1 | |
| `U_UNE_SO` | NVARCHAR(100) | — | <1% | — | — | — | — | 0 | |
| `U_UNE_MLOC` | NVARCHAR(100) | <1% | <1% | <1% | <1% | <1% | — | 6 | |
| `U_UNE_ACTH` | NVARCHAR(100) | 2% | 7% | 99% | 1% | 10% | 100% | 12 | |
| `U_TotalAmt` | DECIMAL | <1% | — | <1% | <1% | — | <1% | 3 | |
| `U_ARNO` | NVARCHAR(100) | <1% | <1% | <1% | <1% | — | <1% | 45 | |
| `U_OMS_Order_No` | INTEGER | 6% | — | 13% | <1% | — | 2% | 529 | |
| `U_Production_Order` | INTEGER | <1% | n/a | <1% | — | n/a | <1% | 22 | |
| `U_PRODUCTION_DATE` | TIMESTAMP | <1% | n/a | <1% | — | n/a | — | 3 | |
| `U_SALES_PERSON` | NVARCHAR(20) | 12% | n/a | n/a | 26% | n/a | n/a | 22 | |
| `U_GRPO` | NVARCHAR(10) | <1% | n/a | n/a | <1% | n/a | n/a | 2 | |
| `U_PONo` | NVARCHAR(30) | 2% | n/a | n/a | 5% | n/a | n/a | 529 | |
| `U_MartCustomer` | NVARCHAR(200) | <1% | n/a | n/a | <1% | n/a | n/a | 14 | |
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

- **`DocType`** (2 values) — `I`×38,196, `S`×11,267
- **`CANCELED`** (1 values) — `N`×49,463
- **`Handwrtten`** (2 values) — `N`×49,462, `Y`×1
- **`Printed`** (2 values) — `N`×49,446, `Y`×17
- **`DocStatus`** (2 values) — `C`×45,457, `O`×4,006
- **`InvntSttus`** (2 values) — `O`×49,461, `C`×2
- **`Transfered`** (1 values) — `N`×49,463
- **`ObjType`** (14 values) — `18`×15,352, `67`×11,655, `13`×9,790, `20`×4,488, `19`×1,696, `22`×1,631, `14`×1,488, `15`×1,388, `16`×1,116, `1250000001`×704, `21`×102, `17`×34, `59`×14, `60`×5
- **`DocCur`** (3 values) — `INR`×49,328, `USD`×99, `EUR`×36
- **`PaidToDate`** (9 values) — `0.000000`×49,455, `282117.808000`×1, `9667.000000`×1, `-1.510400`×1, `5310.000000`×1, `-0.000500`×1, `6584502.750000`×1, `430.700000`×1, `6378891.750000`×1
- **`GrosProfFC`** (7 values) — `0.000000`×41,986, `NULL`×7,471, `420146.430000`×2, `134737.500000`×1, `342439.500000`×1, `211382.250000`×1, `132240.600000`×1
- **`TransId`** (4 values) — `NULL`×49,442, `0`×19, `79498`×1, `1246`×1
- **`GroupNum`** (19 values) — `-1`×36,276, `1`×7,951, `4`×1,304, `21`×980, `20`×661, `11`×589, `22`×527, `19`×397, `16`×322, `18`×303, `17`×57, `6`×44, `10`×19, `7`×12, `14`×9, `29`×4, `9`×4, `3`×3, `5`×1
- **`TrnspCode`** (1 values) — `-1`×49,463
- **`PartSupply`** (1 values) — `Y`×49,463
- **`Confirmed`** (1 values) — `Y`×49,463
- **`GrossBase`** (4 values) — `-6`×46,800, `-1`×2,231, `0`×308, `-10`×124
- **`CreateTran`** (2 values) — `Y`×28,326, `N`×21,137
- **`SummryType`** (1 values) — `N`×49,463
- **`UpdInvnt`** (4 values) — `I`×44,590, `G`×2,504, `O`×1,631, `C`×738
- **`UpdCardBal`** (4 values) — `B`×28,326, `N`×12,378, `D`×7,094, `O`×1,665
- **`InvntDirec`** (2 values) — `E`×36,448, `X`×13,015
- **`ShowSCN`** (1 values) — `N`×49,463
- **`SysRate`** (1 values) — `1.000000`×49,463
- **`CurSource`** (3 values) — `L`×49,311, `C`×135, `S`×17
- **`PaidSys`** (9 values) — `0.000000`×49,455, `-1.510400`×1, `5310.000000`×1, `282117.808000`×1, `9667.000000`×1, `6584502.750000`×1, `6378891.750000`×1, `430.700000`×1, `-0.000500`×1
- **`FatherType`** (1 values) — `P`×49,463
- **`IsICT`** (1 values) — `N`×49,463
- **`VolUnit`** (1 values) — `4`×49,463
- **`WeightUnit`** (2 values) — `3`×49,440, `2`×23
- **`isCrin`** (1 values) — `N`×49,463
- **`FinncPriod`** (24 values) — `23`×2,760, `42`×2,513, `43`×2,420, `25`×2,387, `24`×2,381, `9`×2,349, `44`×2,338, `22`×2,333, `12`×2,277, `17`×2,179, `18`×2,129, `20`×2,101, `8`×2,090, `19`×2,075, `7`×2,052, `10`×2,050, `41`×2,049, `11`×1,993, `15`×1,979, `16`×1,915, `21`×1,903, `14`×1,861, `45`×1,324, `6`×5
- **`selfInv`** (1 values) — `N`×49,463
- **`VatPaid`** (7 values) — `0.000000`×49,457, `-0.000100`×1, `303756.750000`×1, `313547.750000`×1, `810.000000`×1, `65.700000`×1, `30226.908000`×1
- **`VatPaidSys`** (7 values) — `0.000000`×49,457, `-0.000100`×1, `313547.750000`×1, `303756.750000`×1, `810.000000`×1, `65.700000`×1, `30226.908000`×1
- **`WddStatus`** (6 values) — `-`×45,646, `C`×2,967, `N`×481, `Y`×184, `W`×184, `P`×1
- **`Exported`** (1 values) — `N`×49,463
- **`NetProc`** (1 values) — `N`×49,463
- **`RoundDifFC`** (4 values) — `0.000000`×49,459, `-0.430000`×2, `0.500000`×1, `63.250000`×1
- **`submitted`** (1 values) — `N`×49,463
- **`PoPrss`** (1 values) — `N`×49,463
- **`Rounding`** (2 values) — `N`×31,456, `Y`×18,007
- **`RevisionPo`** (1 values) — `N`×49,463
- **`ReqDate`** (18 values) — `NULL`×49,433, `2026-02-03 00:00:00.0000000`×6, `2026-03-30 00:00:00.0000000`×4, `2026-03-06 00:00:00.0000000`×3, `2024-10-30 00:00:00.0000000`×3, `2026-01-30 00:00:00.0000000`×2, `2026-01-13 00:00:00.0000000`×1, `2025-02-28 00:00:00.0000000`×1, `2025-01-26 00:00:00.0000000`×1, `2026-02-10 00:00:00.0000000`×1, `2026-01-09 00:00:00.0000000`×1, `2025-09-20 00:00:00.0000000`×1, `2025-05-08 00:00:00.0000000`×1, `2026-03-23 00:00:00.0000000`×1, `2025-05-05 00:00:00.0000000`×1, `2026-04-15 00:00:00.0000000`×1, `2025-02-01 00:00:00.0000000`×1, `2025-02-13 00:00:00.0000000`×1
- **`CancelDate`** (18 values) — `NULL`×49,433, `2026-03-05 00:00:00.0000000`×6, `2026-04-29 00:00:00.0000000`×4, `2024-11-29 00:00:00.0000000`×3, `2026-04-05 00:00:00.0000000`×3, `2026-03-01 00:00:00.0000000`×2, `2026-05-15 00:00:00.0000000`×1, `2025-03-15 00:00:00.0000000`×1, `2025-03-30 00:00:00.0000000`×1, `2025-03-03 00:00:00.0000000`×1, `2025-02-25 00:00:00.0000000`×1, `2026-02-08 00:00:00.0000000`×1, `2025-06-04 00:00:00.0000000`×1, `2026-04-22 00:00:00.0000000`×1, `2026-03-12 00:00:00.0000000`×1, `2025-10-20 00:00:00.0000000`×1, `2026-02-12 00:00:00.0000000`×1, `2025-06-07 00:00:00.0000000`×1
- **`PickStatus`** (1 values) — `N`×49,463
- **`Pick`** (1 values) — `N`×49,463
- **`BlockDunn`** (1 values) — `N`×49,463
- **`PayBlock`** (1 values) — `N`×49,463
- **`MaxDscn`** (2 values) — `N`×49,462, `Y`×1
- **`Reserve`** (1 values) — `N`×49,463
- **`DeferrTax`** (2 values) — `N`×48,773, `NULL`×690
- **`BoeReserev`** (1 values) — `N`×49,463
- **`Installmnt`** (1 values) — `1`×49,463
- **`VATFirst`** (2 values) — `N`×37,860, `NULL`×11,603
- **`CEECFlag`** (1 values) — `N`×49,463
- **`BPLId`** (7 values) — `2`×42,175, `1`×4,881, `5`×1,756, `6`×413, `3`×224, `4`×13, `7`×1
- **`BPLName`** (9 values) — `FACTORY`×42,151, `DELHI`×4,874, `HARYANA SALES`×1,756, `DELHI ISD`×413, `PUNJAB`×224, `Factory`×24, `HIMACHAL PRADESH`×13, `Delhi`×7, `DELHI INFO`×1
- **`VATRegNum`** (5 values) — `06AACCJ4223F1Z0`×43,931, `07AACCJ4223F1ZY`×4,882, `07AACCJ4223F2ZX`×413, `03AACCJ4223F1Z6`×224, `02AACCJ4223F1Z8`×13
- **`WTDetails`** (4 values) — `NULL`×42,783, `∅`×6,677, `0`×2, `]`×1
- **`SumAbsId`** (1 values) — `-1`×49,463
- **`PIndicator`** (24 values) — `JAN-25-26`×2,760, `MAY-26-27`×2,513, `JUN-26-27`×2,420, `MAR-25-26`×2,387, `FEB-25-26`×2,381, `Dec-24-25`×2,349, `JUL-26-27`×2,338, `DEC-25-26`×2,333, `Mar-24-25`×2,277, `JUL-25-26`×2,179, `AUG-25-26`×2,129, `OCT-25-26`×2,101, `Nov-24-25`×2,090, `SEP-25-26`×2,075, `Oct-24-25`×2,052, `Jan-24-25`×2,050, `APR-26-27`×2,049, `Feb-24-25`×1,993, `MAY-25-26`×1,979, `JUN-25-26`×1,915, `NOV-25-26`×1,903, `APR-25-26`×1,861, `AUG-26-27`×1,324, `Sep-24-25`×5
- **`UseShpdGd`** (1 values) — `N`×49,463
- **`DocSubType`** (3 values) — `--`×27,008, `GA`×22,407, `GD`×48
- **`DpmStatus`** (1 values) — `O`×49,463
- **`DpmDrawn`** (1 values) — `N`×49,463
- **`Posted`** (1 values) — `Y`×49,463
- **`OwnerCode`** (5 values) — `NULL`×48,312, `20`×1,025, `14`×78, `2`×46, `4`×2
- **`IsPaytoBnk`** (2 values) — `N`×37,085, `NULL`×12,378
- **`isIns`** (1 values) — `N`×49,463
- **`VersionNum`** (2 values) — `10.00.250.15`×29,673, `10.00.310.21`×19,790
- **`LangCode`** (3 values) — `8`×37,088, `NULL`×12,374, `33`×1
- **`BPNameOW`** (2 values) — `N`×49,425, `Y`×38
- **`BillToOW`** (2 values) — `N`×49,460, `Y`×3
- **`ShipToOW`** (2 values) — `N`×47,383, `Y`×2,080
- **`RetInvoice`** (1 values) — `N`×49,463
- **`Model`** (1 values) — `0`×49,463
- **`UseCorrVat`** (1 values) — `N`×49,463
- **`BlkCredMmo`** (1 values) — `N`×49,463
- **`OpenForLaC`** (1 values) — `Y`×49,463
- **`Excised`** (1 values) — `O`×49,463
- **`SrvGpPrcnt`** (3 values) — `NULL`×37,422, `0.000000`×11,734, `100.000000`×307
- **`DutyStatus`** (1 values) — `Y`×49,463
- **`AutoCrtFlw`** (1 values) — `N`×49,463
- **`VatJENum`** (2 values) — `-1`×49,333, `0`×130
- **`InsurOp347`** (1 values) — `N`×49,463
- **`IgnRelDoc`** (1 values) — `N`×49,463
- **`ResidenNum`** (1 values) — `1`×49,463
- **`PQTGrpHW`** (1 values) — `N`×49,463
- **`ReopOriDoc`** (3 values) — `NULL`×45,063, `N`×4,341, `Y`×59
- **`ReopManCls`** (2 values) — `NULL`×49,404, `Y`×59
- **`DocManClsd`** (1 values) — `N`×49,463
- **`ClosingOpt`** (1 values) — `1`×49,463
- **`Ordered`** (1 values) — `N`×49,463
- **`NTSApprov`** (1 values) — `N`×49,463
- **`PayDuMonth`** (2 values) — `N`×37,085, `NULL`×12,378
- **`ExtraDays`** (12 values) — `0`×26,504, `NULL`×12,378, `30`×6,736, `25`×980, `21`×661, `60`×589, `35`×527, `15`×397, `5`×322, `10`×303, `7`×57, `2`×9
- **`EDocGenTyp`** (1 values) — `N`×49,463
- **`OnlineQuo`** (1 values) — `N`×49,463
- **`EDocStatus`** (1 values) — `C`×49,463
- **`EDocProces`** (1 values) — `C`×49,463
- **`EDocCancel`** (1 values) — `N`×49,463
- **`EDocTest`** (1 values) — `N`×49,463
- **`DpmAsDscnt`** (1 values) — `N`×49,463
- **`GTSRlvnt`** (1 values) — `N`×49,463
- **`BaseDiscPr`** (18 values) — `0.000000`×49,427, `NULL`×10, `0.002190`×2, `0.001243`×2, `-0.000684`×2, `0.003614`×2, `0.001055`×2, `0.003082`×2, `-0.000057`×2, `0.000271`×2, `0.000529`×2, `0.007739`×2, `0.004160`×1, `-0.000001`×1, `0.299103`×1, `0.000005`×1, `1.950000`×1, `-0.000169`×1
- **`SrvTaxRule`** (1 values) — `N`×49,463
- **`Notify`** (2 values) — `NULL`×40,450, `N`×9,013
- **`ReqType`** (1 values) — `12`×49,463
- **`OriginType`** (1 values) — `M`×49,463
- **`IsReuseNum`** (1 values) — `N`×49,463
- **`IsReuseNFN`** (1 values) — `N`×49,463
- **`DocDlvry`** (1 values) — `0`×49,463
- **`EnvTypeNFe`** (1 values) — `-1`×49,463
- **`IsAlt`** (1 values) — `N`×49,463
- **`AltBaseTyp`** (1 values) — `-1`×49,463
- **`PrintSEPA`** (1 values) — `N`×49,463
- **`RelatedTyp`** (1 values) — `-1`×49,463
- **`PoDropPrss`** (2 values) — `N`×49,429, `Y`×34
- **`ExclTaxRep`** (1 values) — `N`×49,463
- **`Revision`** (1 values) — `N`×49,463
- **`GSTTranTyp`** (4 values) — `GA`×30,535, `--`×18,879, `GD`×48, `NULL`×1
- **`BaseType`** (2 values) — `-1`×49,449, `67`×14
- **`BaseEntry`** (15 values) — `NULL`×49,449, `16873`×1, `15117`×1, `15067`×1, `15064`×1, `15013`×1, `15244`×1, `21157`×1, `15109`×1, `15114`×1, `15078`×1, `15102`×1, `15033`×1, `15095`×1, `15892`×1
- **`ComTrade`** (1 values) — `E`×49,463
- **`UseBilAddr`** (3 values) — `N`×23,093, `Y`×13,996, `NULL`×12,374
- **`IssReason`** (5 values) — `1`×49,449, `2`×9, `3`×2, `7`×2, `4`×1
- **`ComTradeRt`** (1 values) — `N`×49,463
- **`SplitPmnt`** (1 values) — `N`×49,463
- **`SelfPosted`** (1 values) — `N`×49,463
- **`DPPStatus`** (1 values) — `N`×49,463
- **`EWBGenType`** (3 values) — `N`×22,837, `L`×15,023, `NULL`×11,603
- **`EDocType`** (1 values) — `F`×49,463
- **`AggregDoc`** (1 values) — `N`×49,463
- **`DataVers`** (12 values) — `1`×38,976, `2`×7,097, `3`×2,241, `4`×678, `5`×270, `6`×130, `7`×44, `8`×16, `9`×6, `10`×3, `11`×1, `14`×1
- **`ShipState`** (2 values) — `NULL`×49,462, `HR`×1
- **`IndFinal`** (1 values) — `N`×49,463
- **`PostPmntWT`** (1 values) — `N`×49,463
- **`FCEPmnMean`** (1 values) — `N`×49,463
- **`NotRel4MI`** (1 values) — `N`×49,463
- **`Rel4PPTax`** (1 values) — `N`×49,463
- **`ConfrmedBy`** (12 values) — `NULL`×49,271, `32`×95, `30`×36, `31`×25, `15`×17, `36`×7, `24`×4, `19`×2, `10`×2, `22`×2, `16`×1, `1`×1
- **`BookeTdsBP`** (1 values) — `N`×49,463
- **`DigPayment`** (1 values) — `N`×49,463
- **`PDueMonEnd`** (2 values) — `N`×37,085, `NULL`×12,378
- **`RShipToOW`** (3 values) — `N`×49,412, `Y`×40, `NULL`×11
- **`AplTaxOnFr`** (2 values) — `N`×42,968, `NULL`×6,495
- **`CpyDtyStts`** (1 values) — `N`×49,463
- **`U_Basement`** (3 values) — `NULL`×45,068, `Y`×4,351, `N`×44
- **`U_First_Floor`** (3 values) — `NULL`×47,923, `Y`×1,504, `N`×36
- **`U_GenType`** (2 values) — `NULL`×49,459, `N`×4
- **`U_Recv_Date`** (18 values) — `NULL`×49,441, `2025-09-15 00:00:00.0000000`×3, `2025-04-07 00:00:00.0000000`×2, `2025-02-14 00:00:00.0000000`×2, `2024-11-22 00:00:00.0000000`×2, `2025-01-22 00:00:00.0000000`×1, `2025-02-11 00:00:00.0000000`×1, `2025-04-02 00:00:00.0000000`×1, `2025-02-18 00:00:00.0000000`×1, `2025-12-27 00:00:00.0000000`×1, `2026-01-17 00:00:00.0000000`×1, `2025-08-05 00:00:00.0000000`×1, `2024-10-03 00:00:00.0000000`×1, `2025-05-28 00:00:00.0000000`×1, `2025-02-06 00:00:00.0000000`×1, `2025-09-10 00:00:00.0000000`×1, `2026-04-15 00:00:00.0000000`×1, `2025-04-14 00:00:00.0000000`×1
- **`U_deldocnum`** (6 values) — `NULL`×49,456, `1524111001`×3, `1524101283`×1, `1524101058`×1, `1524101056`×1, `1524111255`×1
- **`U_deldocdate`** (5 values) — `NULL`×49,456, `2024-11-02 00:00:00.0000000`×3, `2024-10-09 00:00:00.0000000`×2, `2024-11-20 00:00:00.0000000`×1, `2024-10-28 00:00:00.0000000`×1
- **`U_delbranch`** (5 values) — `NULL`×48,717, `3`×532, `1`×139, `2`×74, `5`×1
- **`U_GRNdocentry`** (2 values) — `NULL`×49,462, `203`×1
- **`U_GRNCardCode`** (7 values) — `NULL`×48,727, `VENDA000003`×650, `VENDA000004`×69, `VENDA000002`×13, `CUSTA000002`×2, `ORGV000044`×1, `VENDA001004`×1
- **`U_GRNWhsCode`** (14 values) — `NULL`×48,723, `PB-ST`×340, `PB-SP`×123, `DL-FG`×95, `PB-JP`×69, `BH-FG`×43, `DL-PS`×30, `BH-GR`×16, `BH-LR`×12, `DL-J3`×7, `DL-GR`×2, `BH-GJ`×1, `PB-SG`×1, `PB-RG`×1
- **`U_Ship_From`** (10 values) — `NULL`×48,979, `BH-FG`×361, `BH-FU`×83, `DL-FG`×19, `DL-J3`×9, `GP-FG`×5, `BH-OT`×3, `DL-GR`×2, `∅`×1, `PB-JP`×1
- **`U_TransporterInvoice`** (6 values) — `NULL`×49,457, `9872987038`×2, `626050630`×1, `na`×1, `.`×1, `626070356`×1
- **`U_Order_Date`** (24 values) — `NULL`×48,903, `2026-07-22 00:00:00.0000000`×68, `2026-06-17 00:00:00.0000000`×56, `2026-05-25 00:00:00.0000000`×55, `2026-04-17 00:00:00.0000000`×51, `2026-03-20 00:00:00.0000000`×39, `2025-12-26 00:00:00.0000000`×26, `2025-02-28 00:00:00.0000000`×25, `2025-04-23 00:00:00.0000000`×25, `2025-02-07 00:00:00.0000000`×23, `2025-05-23 00:00:00.0000000`×23, `2026-01-23 00:00:00.0000000`×22, `2025-06-26 00:00:00.0000000`×22, `2025-04-01 00:00:00.0000000`×22, `2026-02-16 00:00:00.0000000`×21, `2024-11-08 00:00:00.0000000`×20, `2025-11-20 00:00:00.0000000`×20, `2025-01-06 00:00:00.0000000`×19, `2024-12-10 00:00:00.0000000`×11, `2025-08-29 00:00:00.0000000`×7, `2025-05-30 00:00:00.0000000`×2, `2025-07-18 00:00:00.0000000`×1, `2025-01-27 00:00:00.0000000`×1, `2025-10-16 00:00:00.0000000`×1
- **`U_UNE_SCTY`** (2 values) — `NULL`×49,462, `+`×1
- **`U_UNE_BRCH`** (2 values) — `NULL`×49,457, `KUNDLI`×6
- **`U_UNE_ACTH`** (13 values) — `NULL`×48,506, `1102007`×899, `2120002`×30, `5100013`×11, `1103000`×4, `5300015`×3, `1107006`×3, `CC30/2025-26`×2, `1102005`×1, `4150001`×1, `4140003`×1, `4110001`×1, `4110002`×1
- **`U_TotalAmt`** (4 values) — `0.000000`×48,612, `NULL`×849, `16296.000000`×1, `2139995.000000`×1
- **`U_Production_Order`** (23 values) — `NULL`×49,432, `8703`×4, `9958`×2, `8705`×2, `8702`×2, `8739`×2, `8715`×2, `8700`×2, `8742`×1, `8744`×1, `8721`×1, `6500`×1, `8780`×1, `8713`×1, `8710`×1, `8709`×1, `8777`×1, `8776`×1, `8723`×1, `8711`×1, `8743`×1, `8736`×1, `8781`×1
- **`U_PRODUCTION_DATE`** (4 values) — `NULL`×49,456, `2025-10-01 00:00:00.0000000`×3, `2026-03-25 00:00:00.0000000`×2, `2025-10-02 00:00:00.0000000`×2
- **`U_SALES_PERSON`** (23 values) — `NULL`×43,397, `ECOM`×1,751, `PUNJAB GT`×751, `DELHI GT`×538, `PRIVATE`×515, `HARYANA GT`×381, `CSD`×365, `CASH SALE`×286, `PUNJAB MT`×280, `PRINCE OTHER`×240, `HAPPY`×217, `UP/UK GT`×166, `HORECA/INST`×126, `DELHI MT`×123, `TARUN`×117, `ROI`×84, `BRANCH`×44, `HIMACHAL`×29, `FREE SAMPLE`×23, `HYDERABAD`×9, `BANGLORE`×8, `HP GT`×7, `EXPORT`×6
- **`U_GRPO`** (3 values) — `NULL`×49,416, `Y`×40, `N`×7
- **`U_OMS_REF`** (2 values) — `NULL`×49,462, `mrg62n5jtvaam07`×1
