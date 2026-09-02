# `OIGN` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 8,548 | 1,837 | `DocDate` | 2024-09-30 → 2026-08-24 |
| MART | 75 | 21 | `DocDate` | 2024-12-31 → 2026-08-11 |
| BEV | 1,477 | 253 | `DocDate` | 2024-09-30 → 2026-08-22 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 8,548 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 8,548 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 624 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 624 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DocTotal` | DECIMAL | 99% | 99% | 99% | 99% | 100% | 99% | 8,359 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | 100% | 8,548 | |
| `Ref2` | NVARCHAR(11) | <1% | 1% | — | — | — | — | 1 | |
| `Comments` | NVARCHAR(254) | 5% | 43% | <1% | 2% | 5% | — | 389 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `TransId` | INTEGER | 99% | 99% | 99% | 99% | 100% | 99% | 8,432 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 4 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1,110 | |
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
| `DocTotalSy` | DECIMAL | 99% | 99% | 99% | 99% | 100% | 99% | 8,338 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 615 | |
| `VolUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 624 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 24 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 16 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `draftKey` | INTEGER | <1% | 9% | <1% | <1% | — | — | 22 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 68 | |
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
| `Max1099` | DECIMAL | 99% | 99% | 99% | 99% | 100% | 99% | 8,359 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VATFirst` | NVARCHAR(1) | <1% | — | — | — | — | — | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
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
| `AtcEntry` | INTEGER | <1% | 24% | 4% | <1% | — | — | 72 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 7,881 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 7,861 | |
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
| `EWBGenType` | NVARCHAR(1) | <1% | — | — | — | — | — | 1 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QRCodeSrc` | NCLOB | — | 1% | — | — | 5% | — | 0 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
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
| `U_UNE_ACTH` | NVARCHAR(100) | — | — | 96% | — | — | 100% | 0 | |

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

- **`DocType`** (1 values) — `I`×8,548
- **`CANCELED`** (1 values) — `N`×8,548
- **`Handwrtten`** (1 values) — `N`×8,548
- **`Printed`** (1 values) — `N`×8,548
- **`DocStatus`** (1 values) — `O`×8,548
- **`InvntSttus`** (1 values) — `O`×8,548
- **`Transfered`** (1 values) — `N`×8,548
- **`ObjType`** (1 values) — `59`×8,548
- **`DocCur`** (1 values) — `INR`×8,548
- **`DocRate`** (1 values) — `1.000000`×8,548
- **`Ref2`** (2 values) — `NULL`×8,547, `1`×1
- **`JrnlMemo`** (7 values) — `Receipt from Production`×8,241, `Goods Receipt`×283, `Goods Receipt-FIXED ASSET`×10, `Goods Receipt- FIXED ASSET`×8, `Goods Receipt- Fixed Asset`×4, `Goods Receipt-fixed asset`×1, `Goods Receipt-FIXED ASSEY`×1
- **`GroupNum`** (4 values) — `-1`×8,224, `4`×284, `2`×39, `-2`×1
- **`SlpCode`** (1 values) — `-1`×8,548
- **`TrnspCode`** (1 values) — `-1`×8,548
- **`PartSupply`** (1 values) — `Y`×8,548
- **`Confirmed`** (1 values) — `Y`×8,548
- **`GrossBase`** (2 values) — `-6`×8,165, `-1`×383
- **`CreateTran`** (1 values) — `N`×8,548
- **`SummryType`** (1 values) — `N`×8,548
- **`UpdInvnt`** (1 values) — `I`×8,548
- **`UpdCardBal`** (1 values) — `N`×8,548
- **`InvntDirec`** (1 values) — `E`×8,548
- **`ShowSCN`** (1 values) — `N`×8,548
- **`SysRate`** (1 values) — `1.000000`×8,548
- **`CurSource`** (1 values) — `L`×8,548
- **`FatherType`** (1 values) — `P`×8,548
- **`IsICT`** (1 values) — `N`×8,548
- **`VolUnit`** (1 values) — `4`×8,548
- **`WeightUnit`** (2 values) — `3`×8,536, `2`×12
- **`Series`** (24 values) — `720`×637, `2623`×548, `2620`×442, `2624`×425, `2621`×399, `2622`×397, `2253`×395, `2258`×385, `2251`×370, `2259`×367, `717`×363, `719`×344, `2260`×343, `722`×339, `2257`×330, `2249`×328, `2252`×327, `721`×301, `2254`×300, `2256`×299, `2250`×294, `2255`×271, `718`×262, `716`×82
- **`isCrin`** (1 values) — `N`×8,548
- **`FinncPriod`** (24 values) — `10`×637, `44`×548, `41`×442, `45`×425, `42`×399, `43`×397, `18`×395, `23`×385, `16`×370, `24`×367, `7`×363, `9`×344, `25`×343, `12`×339, `22`×330, `14`×328, `17`×327, `11`×301, `19`×300, `21`×299, `15`×294, `20`×271, `8`×262, `6`×82
- **`UserSign`** (16 values) — `33`×6,356, `10`×602, `1`×541, `44`×340, `15`×328, `36`×117, `26`×69, `32`×51, `40`×45, `48`×32, `35`×28, `30`×23, `47`×7, `12`×6, `38`×2, `56`×1
- **`selfInv`** (1 values) — `N`×8,548
- **`WddStatus`** (2 values) — `-`×8,541, `P`×7
- **`draftKey`** (23 values) — `NULL`×8,526, `26745`×1, `49092`×1, `28941`×1, `7282`×1, `24953`×1, `21990`×1, `19532`×1, `26269`×1, `26654`×1, `3803`×1, `16867`×1, `26545`×1, `15172`×1, `4223`×1, `23780`×1, `8756`×1, `25352`×1, `25542`×1, `21325`×1, `52383`×1, `49091`×1, `24088`×1
- **`Exported`** (1 values) — `N`×8,548
- **`NetProc`** (1 values) — `N`×8,548
- **`submitted`** (1 values) — `N`×8,548
- **`PoPrss`** (1 values) — `N`×8,548
- **`Rounding`** (1 values) — `N`×8,548
- **`RevisionPo`** (1 values) — `N`×8,548
- **`PickStatus`** (1 values) — `N`×8,548
- **`Pick`** (1 values) — `N`×8,548
- **`BlockDunn`** (1 values) — `N`×8,548
- **`PayBlock`** (1 values) — `N`×8,548
- **`MaxDscn`** (1 values) — `N`×8,548
- **`Reserve`** (1 values) — `N`×8,548
- **`DeferrTax`** (2 values) — `N`×8,547, `NULL`×1
- **`BoeReserev`** (1 values) — `N`×8,548
- **`Installmnt`** (1 values) — `1`×8,548
- **`VATFirst`** (2 values) — `NULL`×8,546, `N`×2
- **`CEECFlag`** (1 values) — `N`×8,548
- **`BPLId`** (3 values) — `2`×8,417, `1`×113, `3`×18
- **`BPLName`** (6 values) — `FACTORY`×8,396, `DELHI`×109, `Factory`×21, `PUNJAB`×17, `Delhi`×4, `Punjab`×1
- **`VATRegNum`** (3 values) — `06AACCJ4223F1Z0`×8,417, `07AACCJ4223F1ZY`×113, `03AACCJ4223F1Z6`×18
- **`SumAbsId`** (1 values) — `-1`×8,548
- **`PIndicator`** (24 values) — `Jan-24-25`×637, `JUL-26-27`×548, `APR-26-27`×442, `AUG-26-27`×425, `MAY-26-27`×399, `JUN-26-27`×397, `AUG-25-26`×395, `JAN-25-26`×385, `JUN-25-26`×370, `FEB-25-26`×367, `Oct-24-25`×363, `Dec-24-25`×344, `MAR-25-26`×343, `Mar-24-25`×339, `DEC-25-26`×330, `APR-25-26`×328, `JUL-25-26`×327, `Feb-24-25`×301, `SEP-25-26`×300, `NOV-25-26`×299, `MAY-25-26`×294, `OCT-25-26`×271, `Nov-24-25`×262, `Sep-24-25`×82
- **`UseShpdGd`** (1 values) — `N`×8,548
- **`DocSubType`** (1 values) — `--`×8,548
- **`DpmStatus`** (1 values) — `O`×8,548
- **`DpmDrawn`** (1 values) — `N`×8,548
- **`Posted`** (1 values) — `Y`×8,548
- **`isIns`** (1 values) — `N`×8,548
- **`VersionNum`** (2 values) — `10.00.250.15`×5,054, `10.00.310.21`×3,494
- **`BPNameOW`** (1 values) — `N`×8,548
- **`BillToOW`** (1 values) — `N`×8,548
- **`ShipToOW`** (1 values) — `N`×8,548
- **`RetInvoice`** (1 values) — `N`×8,548
- **`Model`** (1 values) — `0`×8,548
- **`UseCorrVat`** (1 values) — `N`×8,548
- **`BlkCredMmo`** (1 values) — `N`×8,548
- **`OpenForLaC`** (1 values) — `Y`×8,548
- **`Excised`** (1 values) — `O`×8,548
- **`DutyStatus`** (1 values) — `Y`×8,548
- **`AutoCrtFlw`** (1 values) — `N`×8,548
- **`VatJENum`** (1 values) — `-1`×8,548
- **`InsurOp347`** (1 values) — `N`×8,548
- **`IgnRelDoc`** (1 values) — `N`×8,548
- **`ResidenNum`** (1 values) — `1`×8,548
- **`PQTGrpHW`** (1 values) — `N`×8,548
- **`DocManClsd`** (1 values) — `N`×8,548
- **`ClosingOpt`** (1 values) — `1`×8,548
- **`Ordered`** (1 values) — `N`×8,548
- **`NTSApprov`** (1 values) — `N`×8,548
- **`EDocGenTyp`** (1 values) — `N`×8,548
- **`OnlineQuo`** (1 values) — `N`×8,548
- **`EDocStatus`** (1 values) — `C`×8,548
- **`EDocProces`** (1 values) — `C`×8,548
- **`EDocCancel`** (1 values) — `N`×8,548
- **`EDocTest`** (1 values) — `N`×8,548
- **`DpmAsDscnt`** (1 values) — `N`×8,548
- **`GTSRlvnt`** (1 values) — `N`×8,548
- **`SrvTaxRule`** (1 values) — `N`×8,548
- **`ReqType`** (1 values) — `12`×8,548
- **`OriginType`** (1 values) — `M`×8,548
- **`IsReuseNum`** (1 values) — `N`×8,548
- **`IsReuseNFN`** (1 values) — `N`×8,548
- **`DocDlvry`** (1 values) — `0`×8,548
- **`EnvTypeNFe`** (1 values) — `-1`×8,548
- **`IsAlt`** (1 values) — `N`×8,548
- **`AltBaseTyp`** (1 values) — `-1`×8,548
- **`PrintSEPA`** (1 values) — `N`×8,548
- **`RelatedTyp`** (2 values) — `-1`×8,544, `60`×4
- **`RelatedEnt`** (5 values) — `NULL`×8,544, `2453`×1, `438`×1, `2923`×1, `3077`×1
- **`PoDropPrss`** (1 values) — `N`×8,548
- **`ExclTaxRep`** (1 values) — `N`×8,548
- **`Revision`** (1 values) — `N`×8,548
- **`GSTTranTyp`** (1 values) — `--`×8,548
- **`BaseType`** (1 values) — `-1`×8,548
- **`ComTrade`** (1 values) — `E`×8,548
- **`IssReason`** (1 values) — `1`×8,548
- **`ComTradeRt`** (1 values) — `N`×8,548
- **`SplitPmnt`** (1 values) — `N`×8,548
- **`SelfPosted`** (1 values) — `N`×8,548
- **`DPPStatus`** (1 values) — `N`×8,548
- **`EWBGenType`** (2 values) — `NULL`×8,546, `N`×2
- **`EDocType`** (1 values) — `F`×8,548
- **`AggregDoc`** (1 values) — `N`×8,548
- **`DataVers`** (7 values) — `1`×8,348, `2`×164, `3`×30, `4`×3, `17`×1, `9`×1, `6`×1
- **`IndFinal`** (1 values) — `N`×8,548
- **`PostPmntWT`** (1 values) — `N`×8,548
- **`FCEPmnMean`** (1 values) — `N`×8,548
- **`NotRel4MI`** (1 values) — `N`×8,548
- **`Rel4PPTax`** (1 values) — `N`×8,548
- **`BookeTdsBP`** (1 values) — `N`×8,548
- **`DigPayment`** (1 values) — `N`×8,548
- **`RShipToOW`** (1 values) — `N`×8,548
- **`AplTaxOnFr`** (1 values) — `N`×8,548
- **`CpyDtyStts`** (1 values) — `N`×8,548
- **`U_UNE_MLOC`** (2 values) — `NULL`×8,545, `USER26`×3
