# `OIGE` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 8,422 | 1,835 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 73 | 21 | `DocDate` | 2025-03-31 → 2026-08-11 |
| BEV | 1,405 | 254 | `DocDate` | 2024-09-30 → 2026-08-22 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 8,422 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 8,422 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 624 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 624 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocTotal` | DECIMAL | 81% | 70% | 99% | 70% | 5% | 98% | 6,749 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 8,422 | |
| `Ref2` | NVARCHAR(11) | <1% | — | — | <1% | — | — | 1 | |
| `Comments` | NVARCHAR(254) | 4% | 45% | 1% | 2% | 5% | — | 357 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `TransId` | INTEGER | 99% | 100% | 99% | 99% | 100% | 98% | 8,365 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1,111 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocTotalSy` | DECIMAL | 81% | 70% | 99% | 70% | 5% | 98% | 6,742 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 613 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 624 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 18 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `draftKey` | INTEGER | <1% | 5% | <1% | — | 5% | <1% | 5 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 67 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
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
| `Max1099` | DECIMAL | 81% | 70% | 99% | 70% | 5% | 98% | 6,749 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | <1% | — | <1% | — | — | — | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
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
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
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
| `AtcEntry` | INTEGER | <1% | 23% | <1% | <1% | — | <1% | 24 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 7,752 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 7,726 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ReqType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OriginType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsReuseNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsReuseNFN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDlvry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EnvTypeNFe` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsAlt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AltBaseTyp` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PrintSEPA` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RelatedTyp` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `RelatedEnt` | INTEGER | <1% | — | <1% | — | — | — | 4 | |
| `PoDropPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ExclTaxRep` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Revision` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GSTTranTyp` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ComTrade` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IssReason` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ComTradeRt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SplitPmnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SelfPosted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EWBGenType` | NVARCHAR(1) | <1% | — | <1% | — | — | — | 1 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QRCodeSrc` | NCLOB | <1% | — | — | <1% | — | — | 0 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AplTaxOnFr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_UNE_MLOC` | NVARCHAR(100) | <1% | — | — | — | — | — | 1 | |
| `U_UNE_ACTH` | NVARCHAR(100) | — | — | 97% | — | — | 100% | 0 | |

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

- **`DocType`** (1 values) — `I`×8,422
- **`CANCELED`** (1 values) — `N`×8,422
- **`Handwrtten`** (1 values) — `N`×8,422
- **`Printed`** (1 values) — `N`×8,422
- **`DocStatus`** (2 values) — `O`×8,421, `C`×1
- **`InvntSttus`** (2 values) — `O`×8,421, `C`×1
- **`Transfered`** (1 values) — `N`×8,422
- **`ObjType`** (1 values) — `60`×8,422
- **`DocCur`** (1 values) — `INR`×8,422
- **`DocRate`** (1 values) — `1.000000`×8,422
- **`Ref2`** (2 values) — `NULL`×8,421, `GRAIN CORP`×1
- **`JrnlMemo`** (3 values) — `Issue for Production`×8,243, `Goods Issue`×178, `Goods Issue-RM0000002`×1
- **`GroupNum`** (4 values) — `-1`×8,095, `4`×283, `2`×39, `-2`×5
- **`SlpCode`** (1 values) — `-1`×8,422
- **`TrnspCode`** (1 values) — `-1`×8,422
- **`PartSupply`** (1 values) — `Y`×8,422
- **`Confirmed`** (1 values) — `Y`×8,422
- **`GrossBase`** (2 values) — `-6`×8,057, `-1`×365
- **`CreateTran`** (1 values) — `N`×8,422
- **`SummryType`** (1 values) — `N`×8,422
- **`UpdInvnt`** (1 values) — `I`×8,422
- **`UpdCardBal`** (1 values) — `N`×8,422
- **`InvntDirec`** (1 values) — `X`×8,422
- **`ShowSCN`** (1 values) — `N`×8,422
- **`SysRate`** (1 values) — `1.000000`×8,422
- **`CurSource`** (1 values) — `L`×8,422
- **`FatherType`** (1 values) — `P`×8,422
- **`IsICT`** (1 values) — `N`×8,422
- **`VolUnit`** (1 values) — `4`×8,422
- **`WeightUnit`** (2 values) — `3`×8,420, `2`×2
- **`Series`** (24 values) — `727`×628, `2635`×548, `2632`×441, `2636`×424, `2633`×399, `2634`×397, `2270`×390, `2265`×389, `2263`×370, `724`×363, `2271`×348, `729`×339, `726`×337, `2272`×336, `2269`×332, `2261`×330, `2264`×328, `728`×299, `2268`×297, `2262`×297, `2266`×296, `2267`×269, `725`×262, `723`×3
- **`isCrin`** (1 values) — `N`×8,422
- **`FinncPriod`** (24 values) — `10`×628, `44`×548, `41`×441, `45`×424, `42`×399, `43`×397, `23`×390, `18`×389, `16`×370, `7`×363, `24`×348, `12`×339, `9`×337, `25`×336, `22`×332, `14`×330, `17`×328, `11`×299, `21`×297, `15`×297, `19`×296, `20`×269, `8`×262, `6`×3
- **`UserSign`** (18 values) — `33`×6,364, `10`×582, `1`×477, `44`×336, `15`×327, `36`×117, `26`×65, `32`×51, `35`×30, `40`×30, `30`×23, `38`×6, `47`×6, `12`×4, `56`×1, `48`×1, `53`×1, `49`×1
- **`selfInv`** (1 values) — `N`×8,422
- **`WddStatus`** (2 values) — `-`×8,421, `P`×1
- **`draftKey`** (6 values) — `NULL`×8,417, `37662`×1, `7807`×1, `21484`×1, `37669`×1, `3916`×1
- **`Exported`** (1 values) — `N`×8,422
- **`NetProc`** (1 values) — `N`×8,422
- **`submitted`** (1 values) — `N`×8,422
- **`PoPrss`** (1 values) — `N`×8,422
- **`Rounding`** (1 values) — `N`×8,422
- **`RevisionPo`** (1 values) — `N`×8,422
- **`PickStatus`** (1 values) — `N`×8,422
- **`Pick`** (1 values) — `N`×8,422
- **`BlockDunn`** (1 values) — `N`×8,422
- **`PayBlock`** (1 values) — `N`×8,422
- **`MaxDscn`** (1 values) — `N`×8,422
- **`Reserve`** (1 values) — `N`×8,422
- **`DeferrTax`** (1 values) — `N`×8,422
- **`BoeReserev`** (1 values) — `N`×8,422
- **`Installmnt`** (1 values) — `1`×8,422
- **`VATFirst`** (2 values) — `NULL`×8,417, `N`×5
- **`CEECFlag`** (1 values) — `N`×8,422
- **`BPLId`** (3 values) — `2`×8,316, `1`×92, `3`×14
- **`BPLName`** (4 values) — `FACTORY`×8,306, `DELHI`×92, `PUNJAB`×14, `Factory`×10
- **`VATRegNum`** (3 values) — `06AACCJ4223F1Z0`×8,316, `07AACCJ4223F1ZY`×92, `03AACCJ4223F1Z6`×14
- **`SumAbsId`** (1 values) — `-1`×8,422
- **`PIndicator`** (24 values) — `Jan-24-25`×628, `JUL-26-27`×548, `APR-26-27`×441, `AUG-26-27`×424, `MAY-26-27`×399, `JUN-26-27`×397, `JAN-25-26`×390, `AUG-25-26`×389, `JUN-25-26`×370, `Oct-24-25`×363, `FEB-25-26`×348, `Mar-24-25`×339, `Dec-24-25`×337, `MAR-25-26`×336, `DEC-25-26`×332, `APR-25-26`×330, `JUL-25-26`×328, `Feb-24-25`×299, `MAY-25-26`×297, `NOV-25-26`×297, `SEP-25-26`×296, `OCT-25-26`×269, `Nov-24-25`×262, `Sep-24-25`×3
- **`UseShpdGd`** (1 values) — `N`×8,422
- **`DocSubType`** (1 values) — `--`×8,422
- **`DpmStatus`** (1 values) — `O`×8,422
- **`DpmDrawn`** (1 values) — `N`×8,422
- **`Posted`** (1 values) — `Y`×8,422
- **`isIns`** (1 values) — `N`×8,422
- **`VersionNum`** (2 values) — `10.00.250.15`×4,950, `10.00.310.21`×3,472
- **`BPNameOW`** (1 values) — `N`×8,422
- **`BillToOW`** (1 values) — `N`×8,422
- **`ShipToOW`** (1 values) — `N`×8,422
- **`RetInvoice`** (1 values) — `N`×8,422
- **`Model`** (1 values) — `0`×8,422
- **`UseCorrVat`** (1 values) — `N`×8,422
- **`BlkCredMmo`** (1 values) — `N`×8,422
- **`OpenForLaC`** (1 values) — `Y`×8,422
- **`Excised`** (1 values) — `O`×8,422
- **`DutyStatus`** (1 values) — `Y`×8,422
- **`AutoCrtFlw`** (1 values) — `N`×8,422
- **`VatJENum`** (1 values) — `-1`×8,422
- **`InsurOp347`** (1 values) — `N`×8,422
- **`IgnRelDoc`** (1 values) — `N`×8,422
- **`ResidenNum`** (1 values) — `1`×8,422
- **`PQTGrpHW`** (1 values) — `N`×8,422
- **`DocManClsd`** (1 values) — `N`×8,422
- **`ClosingOpt`** (1 values) — `1`×8,422
- **`Ordered`** (1 values) — `N`×8,422
- **`NTSApprov`** (1 values) — `N`×8,422
- **`EDocGenTyp`** (1 values) — `N`×8,422
- **`OnlineQuo`** (1 values) — `N`×8,422
- **`EDocStatus`** (1 values) — `C`×8,422
- **`EDocProces`** (1 values) — `C`×8,422
- **`EDocCancel`** (1 values) — `N`×8,422
- **`EDocTest`** (1 values) — `N`×8,422
- **`DpmAsDscnt`** (1 values) — `N`×8,422
- **`AtcEntry`** (25 values) — `NULL`×8,398, `170131`×1, `170138`×1, `132719`×1, `147514`×1, `139566`×1, `147375`×1, `170136`×1, `100603`×1, `130081`×1, `112478`×1, `146391`×1, `109657`×1, `147361`×1, `147502`×1, `109325`×1, `81190`×1, `76368`×1, `167592`×1, `108858`×1, `60055`×1, `94060`×1, `77180`×1, `132740`×1, `146353`×1
- **`GTSRlvnt`** (1 values) — `N`×8,422
- **`SrvTaxRule`** (1 values) — `N`×8,422
- **`ReqType`** (1 values) — `12`×8,422
- **`OriginType`** (1 values) — `M`×8,422
- **`IsReuseNum`** (1 values) — `N`×8,422
- **`IsReuseNFN`** (1 values) — `N`×8,422
- **`DocDlvry`** (1 values) — `0`×8,422
- **`EnvTypeNFe`** (1 values) — `-1`×8,422
- **`IsAlt`** (1 values) — `N`×8,422
- **`AltBaseTyp`** (1 values) — `-1`×8,422
- **`PrintSEPA`** (1 values) — `N`×8,422
- **`RelatedTyp`** (2 values) — `-1`×8,418, `59`×4
- **`RelatedEnt`** (5 values) — `NULL`×8,418, `2439`×1, `501`×1, `2944`×1, `3132`×1
- **`PoDropPrss`** (1 values) — `N`×8,422
- **`ExclTaxRep`** (1 values) — `N`×8,422
- **`Revision`** (1 values) — `N`×8,422
- **`GSTTranTyp`** (1 values) — `--`×8,422
- **`BaseType`** (1 values) — `-1`×8,422
- **`ComTrade`** (1 values) — `E`×8,422
- **`IssReason`** (1 values) — `1`×8,422
- **`ComTradeRt`** (1 values) — `N`×8,422
- **`SplitPmnt`** (1 values) — `N`×8,422
- **`SelfPosted`** (1 values) — `N`×8,422
- **`DPPStatus`** (1 values) — `N`×8,422
- **`EWBGenType`** (2 values) — `NULL`×8,417, `N`×5
- **`EDocType`** (1 values) — `F`×8,422
- **`AggregDoc`** (1 values) — `N`×8,422
- **`DataVers`** (3 values) — `1`×8,386, `2`×33, `3`×3
- **`IndFinal`** (1 values) — `N`×8,422
- **`PostPmntWT`** (1 values) — `N`×8,422
- **`FCEPmnMean`** (1 values) — `N`×8,422
- **`NotRel4MI`** (1 values) — `N`×8,422
- **`Rel4PPTax`** (1 values) — `N`×8,422
- **`BookeTdsBP`** (1 values) — `N`×8,422
- **`DigPayment`** (1 values) — `N`×8,422
- **`RShipToOW`** (1 values) — `N`×8,422
- **`AplTaxOnFr`** (1 values) — `N`×8,422
- **`CpyDtyStts`** (1 values) — `N`×8,422
- **`U_UNE_MLOC`** (2 values) — `NULL`×8,420, `USER26`×2
