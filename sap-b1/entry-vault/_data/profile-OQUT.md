# `OQUT` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 1,692 | 1,249 | `DocDate` | 2025-02-25 → 2026-07-30 |
| MART | 0 | — | — | **not used in this book** |
| BEV | 733 | 733 | `DocDate` | 2026-05-12 → 2026-07-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | BEV all | OIL 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 1,692 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 1,692 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 2 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 133 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 141 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 176 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 175 | |
| `Address` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 215 | |
| `NumAtCard` | NVARCHAR(200) | 32% | 2% | 19% | 2% | 515 | |
| `VatSum` | DECIMAL | 98% | 100% | 98% | 100% | 1,347 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 1 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 1 | |
| `DocTotal` | DECIMAL | 97% | 100% | 97% | 100% | 1,291 | |
| `PaidToDate` | DECIMAL | 94% | 97% | 92% | 97% | 1,276 | |
| `GrosProfit` | DECIMAL | 99% | 100% | 98% | 100% | 1,341 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 1,692 | |
| `Comments` | NVARCHAR(254) | 20% | — | 3% | — | 325 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 481 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 6 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 511 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 36 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 1 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `CntctCode` | INTEGER | 98% | 100% | 98% | 100% | 174 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `VatSumSy` | DECIMAL | 98% | 100% | 98% | 100% | 1,347 | |
| `DocTotalSy` | DECIMAL | 97% | 100% | 97% | 100% | 1,291 | |
| `PaidSys` | DECIMAL | 94% | 97% | 92% | 97% | 1,276 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `GrosProfSy` | DECIMAL | 99% | 100% | 98% | 100% | 1,341 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 133 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 1 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 8 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 133 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 8 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 6 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `VatPaid` | DECIMAL | 66% | 86% | 71% | 86% | 1,017 | |
| `VatPaidSys` | DECIMAL | 66% | 86% | 71% | 86% | 1,017 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 239 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 7 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 241 | |
| `RoundDif` | DECIMAL | 48% | 87% | 65% | 87% | 432 | |
| `RoundDifSy` | DECIMAL | 48% | 87% | 65% | 87% | 432 | |
| `submitted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `PoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Rounding` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 2 | |
| `RevisionPo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Pick` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `BlockDunn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `PayBlock` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `MaxDscn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Reserve` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Max1099` | DECIMAL | 98% | 100% | 98% | 100% | 1,349 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 13 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 3 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 3 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 3 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 8 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 1 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `OwnerCode` | INTEGER | 20% | — | 2% | — | 1 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | 100% | 100% | 223 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 2 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 1 | |
| `UseCorrVat` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `BlkCredMmo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `OpenForLaC` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Excised` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `DutyStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `AutoCrtFlw` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `VatJENum` | INTEGER | 100% | 100% | 100% | 100% | 1 | |
| `InsurOp347` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `IgnRelDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `PQTGrpHW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `DocManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 2 | |
| `ClosingOpt` | SMALLINT | 100% | 100% | 100% | 100% | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `PayDuMonth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `ExtraDays` | SMALLINT | 6% | <1% | 8% | <1% | 6 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 1,633 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 1,477 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `AssetDate` | TIMESTAMP | <1% | — | <1% | — | 1 | |
| `Notify` | NVARCHAR(1) | <1% | <1% | <1% | <1% | 1 | |
| `ReqType` | INTEGER | 100% | 100% | 100% | 100% | 1 | |
| `OriginType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `IsReuseNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `IsReuseNFN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `DocDlvry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `EnvTypeNFe` | INTEGER | 100% | 100% | 100% | 100% | 1 | |
| `IsAlt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `AltBaseTyp` | INTEGER | 100% | 100% | 100% | 100% | 1 | |
| `PrintSEPA` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `RelatedTyp` | INTEGER | 100% | 100% | 100% | 100% | 1 | |
| `PoDropPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `ExclTaxRep` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Revision` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `GSTTranTyp` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 1 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 1 | |
| `ComTrade` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `UseBilAddr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 2 | |
| `IssReason` | SMALLINT | 100% | 100% | 100% | 100% | 1 | |
| `ComTradeRt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `SplitPmnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `SelfPosted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `EWBGenType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 31 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `ConfrmedBy` | INTEGER | 100% | 100% | 100% | 100% | 6 | |
| `ConfrmedOn` | TIMESTAMP | 100% | 100% | 100% | 100% | 133 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `RShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `AplTaxOnFr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 1 | |
| `U_BilltyNumber` | NVARCHAR(15) | <1% | n/a | <1% | n/a | 1 | |
| `U_BiltyDate` | TIMESTAMP | <1% | — | <1% | — | 1 | |
| `U_TransporterName` | NVARCHAR(50) | <1% | — | <1% | — | 1 | |
| `U_VehicleNoM` | NVARCHAR(12) | <1% | n/a | <1% | n/a | 1 | |
| `U_UNE_ACTH` | NVARCHAR(100) | — | 100% | — | 100% | 0 | |
| `U_SALES_PERSON` | NVARCHAR(20) | 21% | n/a | 28% | n/a | 14 | |
| `U_PONo` | NVARCHAR(30) | <1% | n/a | <1% | n/a | 2 | |
| `U_MartCustomer` | NVARCHAR(200) | 5% | n/a | — | n/a | 23 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (16)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_AR_NO` | OIL | **BEV** |
| `U_BOEDate` | OIL | **BEV** |
| `U_BilltyNumber` | OIL | **BEV** |
| `U_BiltyNumber` | BEV | **OIL** |
| `U_CreditCreated` | OIL | **BEV** |
| `U_GRPO` | OIL | **BEV** |
| `U_JRId` | OIL | **BEV** |
| `U_LRNUmber` | OIL | **BEV** |
| `U_MartCN` | OIL | **BEV** |
| `U_MartCustomer` | OIL | **BEV** |
| `U_OMS_REF` | OIL | **BEV** |
| `U_PONo` | OIL | **BEV** |
| `U_SALES_PERSON` | OIL | **BEV** |
| `U_TDS_LINK` | OIL | **BEV** |
| `U_VechileNom` | BEV | **OIL** |
| `U_VehicleNoM` | OIL | **BEV** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`DocType`** (1 values) — `I`×1,692
- **`CANCELED`** (2 values) — `N`×1,658, `Y`×34
- **`Handwrtten`** (1 values) — `N`×1,692
- **`Printed`** (1 values) — `N`×1,692
- **`DocStatus`** (2 values) — `C`×1,632, `O`×60
- **`InvntSttus`** (2 values) — `C`×1,045, `O`×647
- **`Transfered`** (1 values) — `N`×1,692
- **`ObjType`** (1 values) — `23`×1,692
- **`DocCur`** (1 values) — `INR`×1,692
- **`DocRate`** (1 values) — `1.000000`×1,692
- **`GroupNum`** (6 values) — `-1`×1,594, `11`×52, `20`×23, `1`×16, `19`×6, `14`×1
- **`TrnspCode`** (1 values) — `-1`×1,692
- **`PartSupply`** (1 values) — `Y`×1,692
- **`Confirmed`** (1 values) — `Y`×1,692
- **`GrossBase`** (1 values) — `-6`×1,692
- **`CreateTran`** (1 values) — `N`×1,692
- **`SummryType`** (1 values) — `N`×1,692
- **`UpdInvnt`** (1 values) — `N`×1,692
- **`UpdCardBal`** (1 values) — `N`×1,692
- **`InvntDirec`** (1 values) — `X`×1,692
- **`ShowSCN`** (1 values) — `N`×1,692
- **`SysRate`** (1 values) — `1.000000`×1,692
- **`CurSource`** (1 values) — `L`×1,692
- **`FatherType`** (1 values) — `P`×1,692
- **`IsICT`** (1 values) — `N`×1,692
- **`VolUnit`** (1 values) — `4`×1,692
- **`WeightUnit`** (1 values) — `3`×1,692
- **`Series`** (8 values) — `2537`×577, `2538`×399, `2536`×260, `2539`×219, `2445`×138, `2444`×96, `848`×2, `849`×1
- **`isCrin`** (1 values) — `N`×1,692
- **`FinncPriod`** (8 values) — `42`×577, `43`×399, `41`×260, `44`×219, `25`×138, `24`×96, `11`×2, `12`×1
- **`UserSign`** (6 values) — `2`×1,352, `1`×330, `22`×6, `40`×2, `38`×1, `15`×1
- **`selfInv`** (1 values) — `N`×1,692
- **`WddStatus`** (1 values) — `-`×1,692
- **`Exported`** (1 values) — `N`×1,692
- **`StationID`** (7 values) — `6`×1,352, `257`×330, `334`×5, `8`×2, `665`×1, `19`×1, `313`×1
- **`NetProc`** (1 values) — `N`×1,692
- **`submitted`** (1 values) — `N`×1,692
- **`PoPrss`** (1 values) — `N`×1,692
- **`Rounding`** (2 values) — `N`×1,690, `Y`×2
- **`RevisionPo`** (1 values) — `N`×1,692
- **`PickStatus`** (1 values) — `N`×1,692
- **`Pick`** (1 values) — `N`×1,692
- **`BlockDunn`** (1 values) — `N`×1,692
- **`PayBlock`** (1 values) — `N`×1,692
- **`MaxDscn`** (1 values) — `N`×1,692
- **`Reserve`** (1 values) — `N`×1,692
- **`DeferrTax`** (1 values) — `N`×1,692
- **`BoeReserev`** (1 values) — `N`×1,692
- **`Installmnt`** (1 values) — `1`×1,692
- **`VATFirst`** (1 values) — `N`×1,692
- **`CEECFlag`** (1 values) — `N`×1,692
- **`CtlAccount`** (13 values) — `1101001`×782, `1101005`×509, `1101004`×111, `1101006`×91, `1101013`×53, `1101015`×48, `1101007`×47, `1101009`×26, `1102001`×14, `1102002`×5, `1101012`×4, `1101010`×1, `1101008`×1
- **`BPLId`** (3 values) — `2`×1,687, `1`×4, `3`×1
- **`BPLName`** (3 values) — `FACTORY`×1,687, `DELHI`×4, `PUNJAB`×1
- **`VATRegNum`** (3 values) — `06AACCJ4223F1Z0`×1,687, `07AACCJ4223F1ZY`×4, `03AACCJ4223F1Z6`×1
- **`SumAbsId`** (1 values) — `-1`×1,692
- **`PIndicator`** (8 values) — `MAY-26-27`×577, `JUN-26-27`×399, `APR-26-27`×260, `JUL-26-27`×219, `MAR-25-26`×138, `FEB-25-26`×96, `Feb-24-25`×2, `Mar-24-25`×1
- **`UseShpdGd`** (1 values) — `N`×1,692
- **`DocSubType`** (1 values) — `--`×1,692
- **`DpmStatus`** (1 values) — `O`×1,692
- **`DpmDrawn`** (1 values) — `N`×1,692
- **`Posted`** (1 values) — `Y`×1,692
- **`OwnerCode`** (2 values) — `NULL`×1,362, `20`×330
- **`IsPaytoBnk`** (1 values) — `N`×1,692
- **`isIns`** (1 values) — `N`×1,692
- **`VersionNum`** (2 values) — `10.00.310.21`×1,689, `10.00.250.15`×3
- **`LangCode`** (1 values) — `8`×1,692
- **`BPNameOW`** (1 values) — `N`×1,692
- **`BillToOW`** (1 values) — `N`×1,692
- **`ShipToOW`** (1 values) — `N`×1,692
- **`RetInvoice`** (1 values) — `N`×1,692
- **`Model`** (1 values) — `0`×1,692
- **`UseCorrVat`** (1 values) — `N`×1,692
- **`BlkCredMmo`** (1 values) — `N`×1,692
- **`OpenForLaC`** (1 values) — `Y`×1,692
- **`Excised`** (1 values) — `O`×1,692
- **`DutyStatus`** (1 values) — `Y`×1,692
- **`AutoCrtFlw`** (1 values) — `N`×1,692
- **`VatJENum`** (1 values) — `-1`×1,692
- **`InsurOp347`** (1 values) — `N`×1,692
- **`IgnRelDoc`** (1 values) — `N`×1,692
- **`ResidenNum`** (1 values) — `1`×1,692
- **`PQTGrpHW`** (1 values) — `N`×1,692
- **`DocManClsd`** (2 values) — `N`×1,139, `Y`×553
- **`ClosingOpt`** (1 values) — `1`×1,692
- **`Ordered`** (1 values) — `N`×1,692
- **`NTSApprov`** (1 values) — `N`×1,692
- **`PayDuMonth`** (1 values) — `N`×1,692
- **`ExtraDays`** (6 values) — `0`×1,594, `60`×52, `21`×23, `30`×16, `15`×6, `2`×1
- **`EDocGenTyp`** (1 values) — `N`×1,692
- **`OnlineQuo`** (1 values) — `N`×1,692
- **`EDocStatus`** (1 values) — `C`×1,692
- **`EDocProces`** (1 values) — `C`×1,692
- **`EDocCancel`** (1 values) — `N`×1,692
- **`EDocTest`** (1 values) — `N`×1,692
- **`DpmAsDscnt`** (1 values) — `N`×1,692
- **`GTSRlvnt`** (1 values) — `N`×1,692
- **`SrvTaxRule`** (1 values) — `N`×1,692
- **`AssetDate`** (2 values) — `NULL`×1,691, `2026-05-06 00:00:00.0000000`×1
- **`Notify`** (2 values) — `NULL`×1,690, `N`×2
- **`ReqType`** (1 values) — `12`×1,692
- **`OriginType`** (1 values) — `M`×1,692
- **`IsReuseNum`** (1 values) — `N`×1,692
- **`IsReuseNFN`** (1 values) — `N`×1,692
- **`DocDlvry`** (1 values) — `0`×1,692
- **`EnvTypeNFe`** (1 values) — `-1`×1,692
- **`IsAlt`** (1 values) — `N`×1,692
- **`AltBaseTyp`** (1 values) — `-1`×1,692
- **`PrintSEPA`** (1 values) — `N`×1,692
- **`RelatedTyp`** (1 values) — `-1`×1,692
- **`PoDropPrss`** (1 values) — `Y`×1,692
- **`ExclTaxRep`** (1 values) — `N`×1,692
- **`Revision`** (1 values) — `N`×1,692
- **`GSTTranTyp`** (1 values) — `GA`×1,692
- **`BaseType`** (1 values) — `-1`×1,692
- **`ComTrade`** (1 values) — `E`×1,692
- **`UseBilAddr`** (2 values) — `Y`×1,555, `N`×137
- **`IssReason`** (1 values) — `1`×1,692
- **`ComTradeRt`** (1 values) — `N`×1,692
- **`SplitPmnt`** (1 values) — `N`×1,692
- **`SelfPosted`** (1 values) — `N`×1,692
- **`DPPStatus`** (1 values) — `N`×1,692
- **`EWBGenType`** (1 values) — `N`×1,692
- **`EDocType`** (1 values) — `F`×1,692
- **`AggregDoc`** (1 values) — `N`×1,692
- **`IndFinal`** (1 values) — `N`×1,692
- **`PostPmntWT`** (1 values) — `N`×1,692
- **`FCEPmnMean`** (1 values) — `N`×1,692
- **`NotRel4MI`** (1 values) — `N`×1,692
- **`Rel4PPTax`** (1 values) — `N`×1,692
- **`ConfrmedBy`** (6 values) — `2`×1,352, `1`×330, `22`×6, `40`×2, `38`×1, `15`×1
- **`BookeTdsBP`** (1 values) — `N`×1,692
- **`DigPayment`** (1 values) — `N`×1,692
- **`PDueMonEnd`** (1 values) — `N`×1,692
- **`RShipToOW`** (1 values) — `N`×1,692
- **`AplTaxOnFr`** (1 values) — `N`×1,692
- **`CpyDtyStts`** (1 values) — `N`×1,692
- **`U_BilltyNumber`** (2 values) — `NULL`×1,691, `7182`×1
- **`U_BiltyDate`** (2 values) — `NULL`×1,691, `2026-07-11 00:00:00.0000000`×1
- **`U_TransporterName`** (2 values) — `NULL`×1,691, `SS LOGISTICS & CARRIERS`×1
- **`U_VehicleNoM`** (2 values) — `NULL`×1,691, `PB03BB9537`×1
- **`U_SALES_PERSON`** (15 values) — `NULL`×1,337, `PUNJAB GT`×88, `DELHI GT`×52, `HARYANA GT`×46, `PRIVATE`×33, `HORECA/INST`×31, `PRINCE OTHER`×27, `PUNJAB MT`×24, `UP/UK GT`×22, `DELHI MT`×11, `HAPPY`×7, `ECOM`×6, `ROI`×4, `HIMACHAL`×3, `CSD`×1
- **`U_PONo`** (3 values) — `NULL`×1,689, `726224552`×2, `726224557`×1
