# `OWTQ` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 1,325 | 198 | `DocDate` | 2024-10-03 → 2026-08-24 |
| MART | 1,120 | 224 | `DocDate` | 2025-05-19 → 2026-08-11 |
| BEV | 58 | 0 | `DocDate` | 2024-10-10 → 2026-02-03 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 1,325 | |
| `DocNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 1,325 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | · | 318 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | · | 318 | |
| `CardCode` | NVARCHAR(15) | 9% | <1% | 5% | 1% | 3% | · | 29 | |
| `CardName` | NVARCHAR(200) | 9% | <1% | 5% | 1% | 3% | · | 29 | |
| `Address` | NVARCHAR(254) | 9% | <1% | 5% | 1% | 3% | · | 30 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DocRate` | DECIMAL | 24% | — | 26% | — | — | · | 2 | |
| `DocTotal` | DECIMAL | 27% | 100% | 72% | 4% | 99% | · | 352 | |
| `PaidToDate` | DECIMAL | 21% | 91% | 9% | <1% | 88% | · | 277 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | 100% | 100% | 100% | · | 1,325 | |
| `Comments` | NVARCHAR(254) | 75% | 11% | 28% | 94% | 7% | · | 722 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | 100% | 100% | 100% | · | 31 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | · | 3 | |
| `DocTime` | SMALLINT | 100% | 100% | 100% | 100% | 100% | · | 589 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 99% | 100% | · | 12 | |
| `TrnspCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `GrossBase` | SMALLINT | 76% | 100% | 74% | 100% | 100% | · | 3 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `CntctCode` | INTEGER | 8% | <1% | 5% | 1% | 3% | · | 26 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DocTotalSy` | DECIMAL | 27% | 100% | 72% | 4% | 99% | · | 352 | |
| `PaidSys` | DECIMAL | 21% | 91% | 9% | <1% | 88% | · | 277 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | · | 317 | |
| `VolUnit` | SMALLINT | 76% | 100% | 74% | 100% | 100% | · | 1 | |
| `WeightUnit` | SMALLINT | 76% | 100% | 74% | 100% | 100% | · | 2 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 21 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | · | 318 | |
| `Filler` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | · | 16 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 21 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | · | 15 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 2 | |
| `draftKey` | INTEGER | 52% | 2% | — | 96% | 9% | · | 692 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `StationID` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 37 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `ShipToCode` | NVARCHAR(50) | 8% | <1% | 5% | 1% | 3% | · | 30 | |
| `submitted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `PoPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Rounding` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `RevisionPo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Pick` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `BlockDunn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `PayBlock` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `MaxDscn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Reserve` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Max1099` | DECIMAL | 26% | 100% | 69% | 4% | 99% | · | 337 | |
| `DeferrTax` | NVARCHAR(1) | 57% | 52% | 95% | — | — | · | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `VATFirst` | NVARCHAR(1) | 24% | — | 26% | — | — | · | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `CtlAccount` | NVARCHAR(15) | 9% | <1% | 5% | 1% | 3% | · | 9 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 2 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | · | 3 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | · | 2 | |
| `SumAbsId` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | 100% | 100% | 100% | · | 21 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | 100% | 100% | 100% | · | 2 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `UseCorrVat` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `BlkCredMmo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `OpenForLaC` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Excised` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `SrvGpPrcnt` | DECIMAL | 24% | — | 26% | — | — | · | 1 | |
| `DutyStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `AutoCrtFlw` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `VatJENum` | INTEGER | 100% | 100% | 98% | 100% | 100% | · | 1 | |
| `InsurOp347` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `IgnRelDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `PQTGrpHW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DocManClsd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 2 | |
| `ClosingOpt` | SMALLINT | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `AtcEntry` | INTEGER | — | <1% | — | — | — | · | 0 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 1,303 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 1,299 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `ToWhsCode` | NVARCHAR(8) | 100% | 100% | 100% | 100% | 100% | · | 13 | |
| `ReqType` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `OriginType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `IsReuseNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `IsReuseNFN` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DocDlvry` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `EnvTypeNFe` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `IsAlt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `AltBaseTyp` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `PrintSEPA` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `RelatedTyp` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `PoDropPrss` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `ExclTaxRep` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Revision` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `GSTTranTyp` | NVARCHAR(2) | 100% | 100% | 100% | 100% | 100% | · | 2 | |
| `BaseType` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `ComTrade` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `IssReason` | SMALLINT | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `ComTradeRt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `SplitPmnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `SelfPosted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `EWBGenType` | NVARCHAR(1) | 24% | — | 26% | — | — | · | 1 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `QRCodeSrc` | NCLOB | <1% | — | — | — | — | · | 0 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | · | 40 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `RShipToOW` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `AplTaxOnFr` | NVARCHAR(1) | 67% | 48% | 31% | 100% | 100% | · | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | · | 1 | |
| `U_BilltyNumber` | NVARCHAR(15) | 9% | — | n/a | 1% | — | n/a | 112 | |
| `U_BiltyDate` | TIMESTAMP | 9% | — | — | <1% | — | · | 62 | |
| `U_TransporterName` | NVARCHAR(50) | 9% | — | — | 1% | — | · | 24 | |
| `U_VehicleNoM` | NVARCHAR(12) | 9% | — | n/a | 1% | — | n/a | 42 | |
| `U_AR_NO` | NVARCHAR(12) | 1% | — | n/a | — | — | n/a | 7 | |
| `U_InvRevEntry` | NVARCHAR(20) | <1% | — | — | — | — | · | 1 | |
| `U_LRNUmber` | NVARCHAR(15) | 1% | — | n/a | — | — | n/a | 6 | |
| `U_BOEDate` | TIMESTAMP | 1% | — | n/a | — | — | n/a | 5 | |
| `U_UNE_ACTH` | NVARCHAR(100) | — | — | 97% | — | — | · | 0 | |
| `U_PRODUCTION_DATE` | TIMESTAMP | — | n/a | 3% | — | n/a | · | 0 | |

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

- **`DocType`** (1 values) — `I`×1,325
- **`CANCELED`** (1 values) — `N`×1,325
- **`Handwrtten`** (1 values) — `N`×1,325
- **`Printed`** (1 values) — `N`×1,325
- **`DocStatus`** (2 values) — `C`×1,227, `O`×98
- **`InvntSttus`** (2 values) — `C`×1,186, `O`×139
- **`Transfered`** (1 values) — `N`×1,325
- **`ObjType`** (1 values) — `1250000001`×1,325
- **`CardCode`** (30 values) — `NULL`×1,207, `VENDA000279`×15, `VENDA000959`×14, `VENDA000599`×11, `VENDA000930`×8, `VENDA001531`×8, `VENDA000950`×8, `CUSTA000341`×7, `VENDA000052`×6, `VENDA001555`×5, `VENDA001035`×5, `VENDA000614`×4, `VENDA001490`×4, `VENDA001287`×3, `VENDA001375`×2, `VENDA001424`×2, `CUSTA000002`×2, `VENDA000724`×2, `VENDA001423`×1, `VENDA000698`×1, `VENDA001373`×1, `VENDA001326`×1, `VENDA001450`×1, `VENDA001347`×1, `VENDA000149`×1, `VENDA001263`×1, `VENDA000003`×1, `CUSTA000940`×1, `VENDA001421`×1, `VENDA000224`×1
- **`CardName`** (30 values) — `NULL`×1,172, `∅`×35, `DIL EXIM COMMODITIES PRIVATE LIMITED`×15, `ILAHI CO`×14, `EDIBLE OIL CO D LLC`×11, `VAISHNODEVI OIL SEEDS PROCESSING INDUSTRIES`×8, `VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED`×8, `BD EDIBLE OILS PVT LTD`×8, `LEGACY COMMODITIES PRIVATE LIMITED`×7, `VEE KAY ENTERPRISES`×6, `ALBA EDIBLE OILS PTY LTD`×5, `NURTURING FOODS LLP`×5, `DHANLAXMI EDIBLES PRIVATE LIMITED`×4, `MAHA MAYA FOOD PRODUCTS PRIVATE LIMITED`×4, `JIVO WELLNESS PVT LTD - HR`×3, `LEGACY COMMODITIES PRIVATE LIMITED(VEND)`×3, `AL GHURAIR RESOURCES OILS & PROTIENS L L C`×2, `SAMSON GLOBAL PRIVATE LIMITED`×2, `MODI OIL TRADERS`×2, `AWL AGRI BUSINESS LIMITED`×1, `NATIONAL AGRO FOODS`×1, `NETAJI OIL DEPOT PVT LTD`×1, `GOYAL AGRITRADE PRIVATE LIMITED`×1, `WASTAGE DURING PRODUCTION`×1, `ARIHANT SOLVEX PRIVATE LIMITED`×1, `MIGASA ACEITES S L U`×1, `INDRANI FOODS`×1, `CONCEPT COLOUR`×1, `TIRUPATI AGRO INDUSTRIES`×1, `VINOD AGRO INDUSTRIES PRIVATE LIMITED`×1
- **`DocCur`** (1 values) — `INR`×1,325
- **`DocRate`** (2 values) — `0.000000`×1,011, `1.000000`×314
- **`GroupNum`** (3 values) — `-1`×630, `4`×577, `1`×118
- **`SlpCode`** (12 values) — `-1`×1,212, `24`×77, `8`×11, `2`×8, `14`×7, `0`×4, `29`×1, `64`×1, `107`×1, `4`×1, `108`×1, `23`×1
- **`TrnspCode`** (1 values) — `-1`×1,325
- **`PartSupply`** (1 values) — `Y`×1,325
- **`Confirmed`** (1 values) — `Y`×1,325
- **`GrossBase`** (3 values) — `-6`×1,007, `0`×314, `-1`×4
- **`CreateTran`** (1 values) — `N`×1,325
- **`SummryType`** (1 values) — `N`×1,325
- **`UpdInvnt`** (1 values) — `C`×1,325
- **`UpdCardBal`** (1 values) — `N`×1,325
- **`InvntDirec`** (1 values) — `E`×1,325
- **`CntctCode`** (26 values) — `0`×1,223, `2122`×15, `4609`×14, `2441`×11, `4509`×8, `5870`×8, `3972`×7, `1895`×6, `5923`×5, `2456`×4, `5775`×4, `5351`×3, `5665`×2, `5572`×2, `2566`×2, `5663`×1, `4934`×1, `5447`×1, `5661`×1, `5296`×1, `2067`×1, `5497`×1, `5719`×1, `2540`×1, `5569`×1, `1992`×1
- **`ShowSCN`** (1 values) — `N`×1,325
- **`SysRate`** (1 values) — `1.000000`×1,325
- **`CurSource`** (1 values) — `L`×1,325
- **`FatherType`** (1 values) — `P`×1,325
- **`IsICT`** (1 values) — `N`×1,325
- **`VolUnit`** (2 values) — `4`×1,011, `NULL`×314
- **`WeightUnit`** (3 values) — `3`×1,010, `NULL`×314, `2`×1
- **`Series`** (21 values) — `2195`×342, `2197`×156, `2198`×154, `2196`×147, `2199`×105, `2200`×85, `2201`×63, `2645`×62, `2646`×60, `2644`×56, `2648`×33, `2647`×32, `2194`×8, `736`×5, `731`×4, `734`×4, `732`×3, `735`×2, `2191`×2, `2193`×1, `2192`×1
- **`Filler`** (16 values) — `BH-LO`×573, `BH-PM`×541, `BH-GJ`×118, `BH-PF`×22, `BH-PP`×16, `BH-FG`×13, `BH-PC`×9, `BH-NM`×9, `BH-BS`×8, `GP-PM`×6, `BH-EC`×5, `DL-PS`×1, `BH-LR`×1, `DL-FG`×1, `BH-GR`×1, `GP-FA`×1
- **`isCrin`** (1 values) — `N`×1,325
- **`FinncPriod`** (21 values) — `19`×342, `21`×156, `22`×154, `20`×147, `23`×105, `24`×85, `25`×63, `42`×62, `43`×60, `41`×56, `45`×33, `44`×32, `18`×8, `12`×5, `10`×4, `7`×4, `8`×3, `11`×2, `15`×2, `17`×1, `16`×1
- **`UserSign`** (15 values) — `15`×689, `33`×499, `36`×91, `24`×14, `32`×7, `49`×7, `22`×6, `40`×4, `21`×2, `47`×1, `30`×1, `35`×1, `38`×1, `44`×1, `19`×1
- **`selfInv`** (1 values) — `N`×1,325
- **`WddStatus`** (2 values) — `P`×692, `-`×633
- **`Exported`** (1 values) — `N`×1,325
- **`NetProc`** (1 values) — `N`×1,325
- **`ShipToCode`** (30 values) — `NULL`×1,214, `RAJKOT GUJARAT`×15, `ILAHI CO DELHI`×14, `DUBAI`×11, `VAISHNODEVI AGRO RESOURCES RADHANPUR PATAN`×8, `VAISHNODEVI OIL SEEDS GUJARAT`×8, `LEGACY COMMODITIES PRIVATE LIMITED RAJKOT`×7, `KIRTI NAGAR`×6, `ALBA EDIBLE OILS`×5, `NURTURING FOODS LLP NEW DELHI`×5, `GONDAL`×4, `MAHA MAYA FOOD PRODUCTS PVT LTD HARYANA`×4, `LEGACY COMMODITIES RAJKOT`×3, `SHIPTO`×2, `MODI OIL TRADERS PUNJAB`×2, `SAMSON GLOBAL PRIVATE LIMITED TAMIL NADU`×2, `INDRANI FOODS YAMUNANAGAR`×1, `ARIHANT SOLVEX BIKANER`×1, `BHAKHARPUR`×1, `WASTAGE DURING PRODUCTION KUNDLI`×1, `NATIONAL AGRO FOODS HARYANA`×1, `AHMEDABAD`×1, `VINOD AGRO INDUSTRIES PRIVATE LIMITED RAJASTHAN`×1, `GOYAL AGRITRADE PRIVATE LIMITED DELHI`×1, `TIRUPATI AGRO INDUSTRIES RAJASTHAN`×1, `BD EDIBLE OILS PVT LTD RAJASTHAN`×1, `JIVO WELLNESS PVT LTD - HR BHAKHARPUR HARYANA`×1, `NEW DELHI`×1, `NETAJI OIL DEPOT PVT LTD GUJRAT`×1, `SPAIN`×1
- **`submitted`** (1 values) — `N`×1,325
- **`PoPrss`** (1 values) — `N`×1,325
- **`Rounding`** (1 values) — `N`×1,325
- **`RevisionPo`** (1 values) — `N`×1,325
- **`PickStatus`** (1 values) — `N`×1,325
- **`Pick`** (1 values) — `N`×1,325
- **`BlockDunn`** (1 values) — `N`×1,325
- **`PayBlock`** (1 values) — `N`×1,325
- **`MaxDscn`** (1 values) — `N`×1,325
- **`Reserve`** (1 values) — `N`×1,325
- **`DeferrTax`** (2 values) — `N`×754, `NULL`×571
- **`BoeReserev`** (1 values) — `N`×1,325
- **`Installmnt`** (1 values) — `1`×1,325
- **`VATFirst`** (2 values) — `NULL`×1,011, `N`×314
- **`CEECFlag`** (1 values) — `N`×1,325
- **`CtlAccount`** (9 values) — `∅`×1,207, `2110001`×58, `2110005`×30, `2110002`×14, `1101002`×7, `2110007`×5, `1102005`×2, `2120002`×1, `1101012`×1
- **`BPLId`** (2 values) — `2`×1,323, `1`×2
- **`BPLName`** (3 values) — `FACTORY`×1,320, `Factory`×3, `DELHI`×2
- **`VATRegNum`** (2 values) — `06AACCJ4223F1Z0`×1,323, `07AACCJ4223F1ZY`×2
- **`SumAbsId`** (1 values) — `-1`×1,325
- **`PIndicator`** (21 values) — `SEP-25-26`×342, `NOV-25-26`×156, `DEC-25-26`×154, `OCT-25-26`×147, `JAN-25-26`×105, `FEB-25-26`×85, `MAR-25-26`×63, `MAY-26-27`×62, `JUN-26-27`×60, `APR-26-27`×56, `AUG-26-27`×33, `JUL-26-27`×32, `AUG-25-26`×8, `Mar-24-25`×5, `Oct-24-25`×4, `Jan-24-25`×4, `Nov-24-25`×3, `Feb-24-25`×2, `MAY-25-26`×2, `JUN-25-26`×1, `JUL-25-26`×1
- **`UseShpdGd`** (1 values) — `N`×1,325
- **`DocSubType`** (1 values) — `--`×1,325
- **`DpmStatus`** (1 values) — `O`×1,325
- **`DpmDrawn`** (1 values) — `N`×1,325
- **`Posted`** (1 values) — `Y`×1,325
- **`isIns`** (1 values) — `N`×1,325
- **`VersionNum`** (2 values) — `10.00.250.15`×754, `10.00.310.21`×571
- **`BPNameOW`** (1 values) — `N`×1,325
- **`BillToOW`** (1 values) — `N`×1,325
- **`ShipToOW`** (1 values) — `N`×1,325
- **`RetInvoice`** (1 values) — `N`×1,325
- **`Model`** (1 values) — `0`×1,325
- **`UseCorrVat`** (1 values) — `N`×1,325
- **`BlkCredMmo`** (1 values) — `N`×1,325
- **`OpenForLaC`** (1 values) — `Y`×1,325
- **`Excised`** (1 values) — `O`×1,325
- **`SrvGpPrcnt`** (2 values) — `NULL`×1,011, `100.000000`×314
- **`DutyStatus`** (1 values) — `Y`×1,325
- **`AutoCrtFlw`** (1 values) — `N`×1,325
- **`VatJENum`** (1 values) — `-1`×1,325
- **`InsurOp347`** (1 values) — `N`×1,325
- **`IgnRelDoc`** (1 values) — `N`×1,325
- **`ResidenNum`** (1 values) — `1`×1,325
- **`PQTGrpHW`** (1 values) — `N`×1,325
- **`DocManClsd`** (2 values) — `N`×1,284, `Y`×41
- **`ClosingOpt`** (1 values) — `1`×1,325
- **`Ordered`** (1 values) — `N`×1,325
- **`NTSApprov`** (1 values) — `N`×1,325
- **`EDocGenTyp`** (1 values) — `N`×1,325
- **`OnlineQuo`** (1 values) — `N`×1,325
- **`EDocStatus`** (1 values) — `C`×1,325
- **`EDocProces`** (1 values) — `C`×1,325
- **`EDocCancel`** (1 values) — `N`×1,325
- **`EDocTest`** (1 values) — `N`×1,325
- **`DpmAsDscnt`** (1 values) — `N`×1,325
- **`GTSRlvnt`** (1 values) — `N`×1,325
- **`SrvTaxRule`** (1 values) — `N`×1,325
- **`ToWhsCode`** (13 values) — `BH-PC`×1,113, `BH-LO`×103, `BH-FG`×48, `GP-FG`×20, `BH-PF`×13, `BH-EC`×9, `BH-PM`×8, `BH-FU`×3, `BH-PP`×2, `BH-BS`×2, `BH-GR`×2, `BH-INT`×1, `BH-BT`×1
- **`ReqType`** (1 values) — `12`×1,325
- **`OriginType`** (1 values) — `M`×1,325
- **`IsReuseNum`** (1 values) — `N`×1,325
- **`IsReuseNFN`** (1 values) — `N`×1,325
- **`DocDlvry`** (1 values) — `0`×1,325
- **`EnvTypeNFe`** (1 values) — `-1`×1,325
- **`IsAlt`** (1 values) — `N`×1,325
- **`AltBaseTyp`** (1 values) — `-1`×1,325
- **`PrintSEPA`** (1 values) — `N`×1,325
- **`RelatedTyp`** (1 values) — `-1`×1,325
- **`PoDropPrss`** (1 values) — `N`×1,325
- **`ExclTaxRep`** (1 values) — `N`×1,325
- **`Revision`** (1 values) — `N`×1,325
- **`GSTTranTyp`** (2 values) — `--`×1,323, `GA`×2
- **`BaseType`** (1 values) — `-1`×1,325
- **`ComTrade`** (1 values) — `E`×1,325
- **`IssReason`** (1 values) — `1`×1,325
- **`ComTradeRt`** (1 values) — `N`×1,325
- **`SplitPmnt`** (1 values) — `N`×1,325
- **`SelfPosted`** (1 values) — `N`×1,325
- **`DPPStatus`** (1 values) — `N`×1,325
- **`EWBGenType`** (2 values) — `NULL`×1,011, `N`×314
- **`EDocType`** (1 values) — `F`×1,325
- **`AggregDoc`** (1 values) — `N`×1,325
- **`IndFinal`** (1 values) — `N`×1,325
- **`PostPmntWT`** (1 values) — `N`×1,325
- **`FCEPmnMean`** (1 values) — `N`×1,325
- **`NotRel4MI`** (1 values) — `N`×1,325
- **`Rel4PPTax`** (1 values) — `N`×1,325
- **`BookeTdsBP`** (1 values) — `N`×1,325
- **`DigPayment`** (1 values) — `N`×1,325
- **`RShipToOW`** (1 values) — `N`×1,325
- **`AplTaxOnFr`** (2 values) — `N`×885, `NULL`×440
- **`CpyDtyStts`** (1 values) — `N`×1,325
- **`U_TransporterName`** (25 values) — `NULL`×1,211, `R.K. TANKER SERVICE`×53, `RK TANKER SERVICE`×21, `Shri Pawansut Forwarding Service`×8, `R K TANKER SERVICE`×5, `RK TANKER`×4, `SHRI PAWANSUT FOR & CLE.`×2, `SS LOGISTICS & CARRIERS`×2, `R.K Tanker Service`×2, `OM LOGISTICS SUPPLY CHAIN PVT LTD`×2, `R.K TANKER SERVICE`×1, `R K Tanker Service`×1, `R K TANKER SERVICES`×1, `R K TANKER`×1, `REKS TANKERS`×1, `SHRI PAWANSUT`×1, `Ravi Cargo Movers`×1, `SHRI PAWNSUT`×1, `PANKAJ KUMAR JAIN`×1, `MODI BULK CARRIER`×1, `RK tanker Service`×1, `NATIONAL AGRO FOOD`×1, `vijay tempo`×1, `Shri Pawansut For& Cle.`×1, `POONIA BULK CARRIER`×1
- **`U_AR_NO`** (8 values) — `NULL`×1,307, `42760`×6, `42563`×4, `227729`×2, `42961`×2, `227361`×2, `41680`×1, `ES25-018510`×1
- **`U_InvRevEntry`** (2 values) — `NULL`×1,324, `259807383`×1
- **`U_LRNUmber`** (7 values) — `NULL`×1,307, `4137680`×7, `3493766`×4, `5276495`×2, `5168506`×2, `6223663`×2, `5579572`×1
- **`U_BOEDate`** (6 values) — `NULL`×1,307, `2025-08-27 00:00:00.0000000`×9, `2025-07-25 00:00:00.0000000`×4, `2025-12-11 00:00:00.0000000`×2, `2025-10-17 00:00:00.0000000`×2, `2025-11-08 00:00:00.0000000`×1
