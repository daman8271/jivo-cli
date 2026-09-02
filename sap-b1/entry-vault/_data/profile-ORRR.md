# `ORRR` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 32 | 0 | `DocDate` | 2025-01-06 → 2026-03-11 |
| MART | 1 | 0 | `DocDate` | 2025-03-05 → 2025-03-05 |
| BEV | 0 | — | — | **not used in this book** |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | OIL 120d | MART 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---|
| `DocEntry` | INTEGER | 100% | 100% | · | · | 32 | |
| `DocNum` | INTEGER | 100% | 100% | · | · | 32 | |
| `DocType` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `CANCELED` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Handwrtten` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Printed` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `DocStatus` | NVARCHAR(1) | 100% | 100% | · | · | 2 | |
| `InvntSttus` | NVARCHAR(1) | 100% | 100% | · | · | 2 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | · | · | 1 | |
| `DocDate` | TIMESTAMP | 100% | 100% | · | · | 17 | |
| `DocDueDate` | TIMESTAMP | 100% | 100% | · | · | 17 | |
| `CardCode` | NVARCHAR(15) | 100% | 100% | · | · | 18 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | · | · | 18 | |
| `Address` | NVARCHAR(254) | 100% | 100% | · | · | 20 | |
| `NumAtCard` | NVARCHAR(200) | 3% | 100% | · | · | 2 | |
| `VatSum` | DECIMAL | 100% | 100% | · | · | 28 | |
| `DocCur` | NVARCHAR(3) | 100% | 100% | · | · | 1 | |
| `DocRate` | DECIMAL | 100% | 100% | · | · | 1 | |
| `DocTotal` | DECIMAL | 100% | 100% | · | · | 30 | |
| `PaidToDate` | DECIMAL | 53% | 100% | · | · | 18 | |
| `GrosProfit` | DECIMAL | 100% | 100% | · | · | 28 | |
| `Ref1` | NVARCHAR(11) | 100% | 100% | · | · | 32 | |
| `Comments` | NVARCHAR(254) | 44% | 100% | · | · | 14 | |
| `JrnlMemo` | NVARCHAR(254) | 100% | 100% | · | · | 18 | |
| `GroupNum` | SMALLINT | 100% | 100% | · | · | 2 | |
| `DocTime` | SMALLINT | 100% | 100% | · | · | 32 | |
| `SlpCode` | INTEGER | 100% | 100% | · | · | 6 | |
| `TrnspCode` | SMALLINT | 100% | 100% | · | · | 1 | |
| `PartSupply` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Confirmed` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `GrossBase` | SMALLINT | 100% | 100% | · | · | 2 | |
| `CreateTran` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `SummryType` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `UpdInvnt` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `UpdCardBal` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `InvntDirec` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `CntctCode` | INTEGER | 100% | 100% | · | · | 18 | |
| `ShowSCN` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `SysRate` | DECIMAL | 100% | 100% | · | · | 1 | |
| `CurSource` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `VatSumSy` | DECIMAL | 100% | 100% | · | · | 28 | |
| `DocTotalSy` | DECIMAL | 100% | 100% | · | · | 30 | |
| `PaidSys` | DECIMAL | 53% | 100% | · | · | 18 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `GrosProfSy` | DECIMAL | 100% | 100% | · | · | 28 | |
| `IsICT` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | · | · | 17 | |
| `VolUnit` | SMALLINT | 100% | 100% | · | · | 1 | |
| `WeightUnit` | SMALLINT | 100% | 100% | · | · | 1 | |
| `Series` | INTEGER | 100% | 100% | · | · | 6 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | · | · | 17 | |
| `isCrin` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `FinncPriod` | INTEGER | 100% | 100% | · | · | 6 | |
| `UserSign` | SMALLINT | 100% | 100% | · | · | 3 | |
| `selfInv` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `VatPaid` | DECIMAL | 53% | 100% | · | · | 18 | |
| `VatPaidSys` | DECIMAL | 53% | 100% | · | · | 18 | |
| `WddStatus` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Address2` | NVARCHAR(254) | 100% | 100% | · | · | 20 | |
| `Exported` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `StationID` | INTEGER | 100% | 100% | · | · | 4 | |
| `NetProc` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `ShipToCode` | NVARCHAR(50) | 100% | 100% | · | · | 20 | |
| `RoundDif` | DECIMAL | 66% | — | · | · | 20 | |
| `RoundDifSy` | DECIMAL | 66% | — | · | · | 20 | |
| `submitted` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `PoPrss` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Rounding` | NVARCHAR(1) | 100% | 100% | · | · | 2 | |
| `RevisionPo` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `PickStatus` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Pick` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `BlockDunn` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `PayBlock` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `MaxDscn` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Reserve` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Max1099` | DECIMAL | 100% | 100% | · | · | 28 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `BoeReserev` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Installmnt` | SMALLINT | 100% | 100% | · | · | 1 | |
| `VATFirst` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `CEECFlag` | NVARCHAR(1) | 100% | 100% | · | · | 2 | |
| `CtlAccount` | NVARCHAR(15) | 100% | 100% | · | · | 4 | |
| `BPLId` | INTEGER | 100% | 100% | · | · | 3 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | · | · | 3 | |
| `VATRegNum` | NVARCHAR(32) | 100% | 100% | · | · | 3 | |
| `SumAbsId` | INTEGER | 100% | 100% | · | · | 1 | |
| `PIndicator` | NVARCHAR(10) | 100% | 100% | · | · | 6 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `DocSubType` | NVARCHAR(2) | 100% | 100% | · | · | 1 | |
| `DpmStatus` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `DpmDrawn` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Posted` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `PayToCode` | NVARCHAR(50) | 100% | 100% | · | · | 20 | |
| `IsPaytoBnk` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `isIns` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `VersionNum` | NVARCHAR(13) | 100% | 100% | · | · | 2 | |
| `LangCode` | INTEGER | 100% | 100% | · | · | 1 | |
| `BPNameOW` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `BillToOW` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `ShipToOW` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `RetInvoice` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Model` | NVARCHAR(6) | 100% | 100% | · | · | 1 | |
| `UseCorrVat` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `BlkCredMmo` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `OpenForLaC` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Excised` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `DutyStatus` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `AutoCrtFlw` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `VatJENum` | INTEGER | 100% | 100% | · | · | 1 | |
| `InsurOp347` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `IgnRelDoc` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `PQTGrpHW` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `DocManClsd` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `ClosingOpt` | SMALLINT | 100% | 100% | · | · | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `NTSApprov` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `PayDuMonth` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `ExtraDays` | SMALLINT | 28% | 100% | · | · | 2 | |
| `EDocGenTyp` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `OnlineQuo` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `EDocStatus` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `EDocProces` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `EDocCancel` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `EDocTest` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `DpmAsDscnt` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `AtcEntry` | INTEGER | 41% | — | · | · | 13 | |
| `GTSRlvnt` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `CreateTS` | INTEGER | 100% | 100% | · | · | 32 | |
| `UpdateTS` | INTEGER | 100% | 100% | · | · | 32 | |
| `SrvTaxRule` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `AssetDate` | TIMESTAMP | 12% | — | · | · | 3 | |
| `Notify` | NVARCHAR(1) | 38% | — | · | · | 1 | |
| `ReqType` | INTEGER | 100% | 100% | · | · | 1 | |
| `OriginType` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `IsReuseNum` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `IsReuseNFN` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `DocDlvry` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `EnvTypeNFe` | INTEGER | 100% | 100% | · | · | 1 | |
| `IsAlt` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `AltBaseTyp` | INTEGER | 100% | 100% | · | · | 1 | |
| `PrintSEPA` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `RelatedTyp` | INTEGER | 100% | 100% | · | · | 1 | |
| `PoDropPrss` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `ExclTaxRep` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Revision` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `GSTTranTyp` | NVARCHAR(2) | 100% | 100% | · | · | 1 | |
| `BaseType` | INTEGER | 100% | 100% | · | · | 1 | |
| `ComTrade` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `UseBilAddr` | NVARCHAR(1) | 100% | 100% | · | · | 2 | |
| `IssReason` | SMALLINT | 100% | 100% | · | · | 1 | |
| `ComTradeRt` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `SplitPmnt` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `SelfPosted` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `EWBGenType` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `EDocType` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `DataVers` | INTEGER | 100% | 100% | · | · | 8 | |
| `IndFinal` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `PostPmntWT` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Rel4PPTax` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `ConfrmedBy` | INTEGER | 100% | 100% | · | · | 3 | |
| `ConfrmedOn` | TIMESTAMP | 100% | 100% | · | · | 17 | |
| `BookeTdsBP` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `DigPayment` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `PDueMonEnd` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `Address3` | NVARCHAR(254) | 75% | — | · | · | 5 | |
| `RShipToOW` | NVARCHAR(1) | 75% | — | · | · | 1 | |
| `AplTaxOnFr` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `CpyDtyStts` | NVARCHAR(1) | 100% | 100% | · | · | 1 | |
| `U_Basement` | NVARCHAR(10) | 3% | — | · | · | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (15)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_BPCODE` | MART | **OIL** |
| `U_CreditCreated` | OIL | **MART** |
| `U_GRPO` | OIL | **MART** |
| `U_JWPL_BASE` | MART | **OIL** |
| `U_MART_DOC_NO` | MART | **OIL** |
| `U_MartCN` | OIL | **MART** |
| `U_MartCustomer` | OIL | **MART** |
| `U_OMS_REF` | OIL | **MART** |
| `U_POMade` | MART | **OIL** |
| `U_PONo` | OIL | **MART** |
| `U_PO_Ship_To` | MART | **OIL** |
| `U_PRODUCTION_DATE` | OIL | **MART** |
| `U_Production_Order` | OIL | **MART** |
| `U_SALES_PERSON` | OIL | **MART** |
| `U_Total_Gross_Wt` | OIL | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`DocType`** (1 values) — `I`×32
- **`CANCELED`** (1 values) — `N`×32
- **`Handwrtten`** (1 values) — `N`×32
- **`Printed`** (1 values) — `N`×32
- **`DocStatus`** (2 values) — `C`×17, `O`×15
- **`InvntSttus`** (2 values) — `C`×17, `O`×15
- **`Transfered`** (1 values) — `N`×32
- **`ObjType`** (1 values) — `234000031`×32
- **`DocDate`** (17 values) — `2025-03-18 00:00:00.0000000`×6, `2025-12-25 00:00:00.0000000`×4, `2025-12-19 00:00:00.0000000`×3, `2026-02-18 00:00:00.0000000`×2, `2025-12-29 00:00:00.0000000`×2, `2026-01-05 00:00:00.0000000`×2, `2026-01-21 00:00:00.0000000`×2, `2026-01-19 00:00:00.0000000`×2, `2026-02-19 00:00:00.0000000`×1, `2025-01-06 00:00:00.0000000`×1, `2025-12-05 00:00:00.0000000`×1, `2025-12-26 00:00:00.0000000`×1, `2026-03-11 00:00:00.0000000`×1, `2026-01-13 00:00:00.0000000`×1, `2025-12-18 00:00:00.0000000`×1, `2026-01-03 00:00:00.0000000`×1, `2026-02-21 00:00:00.0000000`×1
- **`DocDueDate`** (17 values) — `2025-03-18 00:00:00.0000000`×6, `2025-12-25 00:00:00.0000000`×4, `2025-12-19 00:00:00.0000000`×3, `2026-01-05 00:00:00.0000000`×2, `2026-01-19 00:00:00.0000000`×2, `2026-01-21 00:00:00.0000000`×2, `2026-02-18 00:00:00.0000000`×2, `2025-12-29 00:00:00.0000000`×2, `2026-02-19 00:00:00.0000000`×1, `2025-01-06 00:00:00.0000000`×1, `2025-12-05 00:00:00.0000000`×1, `2025-12-26 00:00:00.0000000`×1, `2026-03-11 00:00:00.0000000`×1, `2026-01-13 00:00:00.0000000`×1, `2025-12-18 00:00:00.0000000`×1, `2026-01-03 00:00:00.0000000`×1, `2026-02-21 00:00:00.0000000`×1
- **`CardCode`** (18 values) — `CUSTA000496`×8, `CUSTA000596`×3, `CUSTA001029`×3, `CUSTA001009`×2, `CUSTA000357`×2, `CUSTA001028`×2, `CUSTA000614`×1, `CUSTA000993`×1, `CUSTA000510`×1, `CUSTA000912`×1, `CUSTA000007`×1, `CUSTA000246`×1, `CUSTA001047`×1, `CUSTA000232`×1, `CUSTA000581`×1, `CUSTA000595`×1, `CUSTA000022`×1, `CUSTA000606`×1
- **`CardName`** (18 values) — `INNOVATIVE RETAIL CONCEPTS PVT LTD`×8, `MAKKAR GENERAL STORE`×3, `BRIJ LAL SOHAN LAL`×3, `G PURE INDIA`×2, `JINDAL BROTHERS`×2, `R.V TRADING COMPANY`×2, `HK AGENCIES`×1, `STALL AT RAKAB GANJ DSD`×1, `GOLDWAY FOODS PVT LTD`×1, `SHRAY FOOD & BEVERAGES PRIVATE LIMITED`×1, `PARSHOTAM LAL VISHWA NATH`×1, `BRIJ LAL DURGA DASS`×1, `SUBHASH CHANDER TARUN KUMAR`×1, `BHARAT BHUSHAN & SONS`×1, `ARJUN DASS & SONS PUNJAB NEW`×1, `JIVO MART PVT LTD`×1, `WAHEGURU TRADERS`×1, `CHARAN DASS BANARSI DASS`×1
- **`NumAtCard`** (3 values) — `NULL`×28, `∅`×3, `855049`×1
- **`VatSum`** (28 values) — `9491.460000`×3, `24280.623500`×2, `13277.621000`×2, `9160.223000`×1, `52193.718900`×1, `14732.154500`×1, `8100.832500`×1, `21028.578000`×1, `19579.018000`×1, `1523.810000`×1, `9729.585000`×1, `1519.065700`×1, `18369.529600`×1, `9659.979500`×1, `13255.000000`×1, `7718.303500`×1, `1860.000000`×1, `10934.878500`×1, `6085.780000`×1, `50959.789400`×1, `10686.244000`×1, `10171.248000`×1, `790.711000`×1, `10800.530000`×1, `17194.446500`×1, `1695.000000`×1, `7718.328000`×1, `4302.666900`×1
- **`DocCur`** (1 values) — `INR`×32
- **`DocRate`** (1 values) — `1.000000`×32
- **`DocTotal`** (30 values) — `199320.000000`×2, `278830.000000`×2, `35595.000000`×1, `39060.000000`×1, `202859.000000`×1, `229632.000000`×1, `441600.000000`×1, `361083.376500`×1, `1070155.000000`×1, `16604.000000`×1, `213596.000000`×1, `224411.000000`×1, `32000.010000`×1, `509893.000000`×1, `162084.000000`×1, `90356.004100`×1, `192364.000000`×1, `204321.000000`×1, `509893.093500`×1, `127801.000000`×1, `309375.000000`×1, `199320.660000`×1, `226811.000000`×1, `385760.000000`×1, `278355.000000`×1, `31900.000000`×1, `170117.000000`×1, `411159.378000`×1, `1096068.096900`×1, `162084.373500`×1
- **`PaidToDate`** (18 values) — `0.000000`×15, `509893.093500`×1, `411159.378000`×1, `170117.000000`×1, `31900.000000`×1, `385760.000000`×1, `199320.000000`×1, `309375.000000`×1, `278830.000000`×1, `35595.000000`×1, `32000.010000`×1, `1070155.000000`×1, `441600.000000`×1, `90356.004100`×1, `39060.000000`×1, `127801.000000`×1, `202859.000000`×1, `229632.000000`×1
- **`GrosProfit`** (28 values) — `189829.200000`×3, `265552.420000`×2, `485612.470000`×2, `33900.000000`×1, `154366.070000`×1, `194591.700000`×1, `15814.220000`×1, `1019195.788700`×1, `343888.930000`×1, `1043874.378000`×1, `162016.650000`×1, `265100.000000`×1, `86053.337200`×1, `30476.200000`×1, `216010.600000`×1, `154366.560000`×1, `121715.600000`×1, `30381.313000`×1, `218697.570000`×1, `37200.000000`×1, `367390.591000`×1, `66968.380800`×1, `203424.960000`×1, `183204.460000`×1, `420571.560000`×1, `193199.590000`×1, `391580.360000`×1, `294643.090000`×1
- **`JrnlMemo`** (18 values) — `Return Request - CUSTA000496`×8, `Return Request - CUSTA000596`×3, `Return Request - CUSTA001029`×3, `Return Request - CUSTA001028`×2, `Return Request - CUSTA001009`×2, `Return Request - CUSTA000357`×2, `Return Request - CUSTA000595`×1, `Return Request - CUSTA000614`×1, `Return Request - CUSTA000993`×1, `Return Request - CUSTA000246`×1, `Return Request - CUSTA000232`×1, `Return Request - CUSTA000007`×1, `Return Request - CUSTA001047`×1, `Return Request - CUSTA000581`×1, `Return Request - CUSTA000912`×1, `Return Request - CUSTA000606`×1, `Return Request - CUSTA000022`×1, `Return Request - CUSTA000510`×1
- **`GroupNum`** (2 values) — `-1`×23, `1`×9
- **`SlpCode`** (6 values) — `-1`×21, `25`×4, `17`×3, `102`×2, `80`×1, `4`×1
- **`TrnspCode`** (1 values) — `-1`×32
- **`PartSupply`** (1 values) — `Y`×32
- **`Confirmed`** (1 values) — `Y`×32
- **`GrossBase`** (2 values) — `-6`×31, `-1`×1
- **`CreateTran`** (1 values) — `N`×32
- **`SummryType`** (1 values) — `N`×32
- **`UpdInvnt`** (1 values) — `C`×32
- **`UpdCardBal`** (1 values) — `N`×32
- **`InvntDirec`** (1 values) — `X`×32
- **`CntctCode`** (18 values) — `4127`×8, `5533`×3, `4226`×3, `5532`×2, `3988`×2, `5421`×2, `4244`×1, `5311`×1, `4141`×1, `4211`×1, `3654`×1, `3877`×1, `4225`×1, `3863`×1, `4236`×1, `5644`×1, `3639`×1, `4773`×1
- **`ShowSCN`** (1 values) — `N`×32
- **`SysRate`** (1 values) — `1.000000`×32
- **`CurSource`** (1 values) — `L`×32
- **`VatSumSy`** (28 values) — `9491.460000`×3, `24280.623500`×2, `13277.621000`×2, `10171.248000`×1, `790.711000`×1, `8100.832500`×1, `10686.244000`×1, `50959.789400`×1, `6085.780000`×1, `10934.878500`×1, `1860.000000`×1, `13255.000000`×1, `9659.979500`×1, `18369.529600`×1, `1519.065700`×1, `9729.585000`×1, `1523.810000`×1, `7718.328000`×1, `1695.000000`×1, `17194.446500`×1, `19579.018000`×1, `21028.578000`×1, `7718.303500`×1, `14732.154500`×1, `52193.718900`×1, `9160.223000`×1, `4302.666900`×1, `10800.530000`×1
- **`DocTotalSy`** (30 values) — `278830.000000`×2, `199320.000000`×2, `224411.000000`×1, `213596.000000`×1, `16604.000000`×1, `1070155.000000`×1, `361083.376500`×1, `441600.000000`×1, `229632.000000`×1, `202859.000000`×1, `39060.000000`×1, `35595.000000`×1, `32000.010000`×1, `162084.373500`×1, `1096068.096900`×1, `411159.378000`×1, `170117.000000`×1, `31900.000000`×1, `278355.000000`×1, `385760.000000`×1, `226811.000000`×1, `199320.660000`×1, `309375.000000`×1, `127801.000000`×1, `509893.093500`×1, `204321.000000`×1, `192364.000000`×1, `90356.004100`×1, `509893.000000`×1, `162084.000000`×1
- **`PaidSys`** (18 values) — `0.000000`×15, `309375.000000`×1, `278830.000000`×1, `35595.000000`×1, `32000.010000`×1, `1070155.000000`×1, `441600.000000`×1, `90356.004100`×1, `509893.093500`×1, `199320.000000`×1, `127801.000000`×1, `385760.000000`×1, `39060.000000`×1, `31900.000000`×1, `170117.000000`×1, `202859.000000`×1, `411159.378000`×1, `229632.000000`×1
- **`FatherType`** (1 values) — `P`×32
- **`GrosProfSy`** (28 values) — `189829.200000`×3, `265552.420000`×2, `485612.470000`×2, `37200.000000`×1, `367390.591000`×1, `66968.380800`×1, `203424.960000`×1, `183204.460000`×1, `420571.560000`×1, `193199.590000`×1, `391580.360000`×1, `294643.090000`×1, `33900.000000`×1, `154366.560000`×1, `216010.600000`×1, `30476.200000`×1, `86053.337200`×1, `265100.000000`×1, `162016.650000`×1, `1043874.378000`×1, `154366.070000`×1, `121715.600000`×1, `30381.313000`×1, `218697.570000`×1, `15814.220000`×1, `343888.930000`×1, `194591.700000`×1, `1019195.788700`×1
- **`IsICT`** (1 values) — `N`×32
- **`CreateDate`** (17 values) — `2025-03-18 00:00:00.0000000`×6, `2025-12-25 00:00:00.0000000`×4, `2025-12-19 00:00:00.0000000`×3, `2026-01-05 00:00:00.0000000`×2, `2026-01-19 00:00:00.0000000`×2, `2026-01-21 00:00:00.0000000`×2, `2026-02-18 00:00:00.0000000`×2, `2025-12-29 00:00:00.0000000`×2, `2026-02-19 00:00:00.0000000`×1, `2025-01-06 00:00:00.0000000`×1, `2025-12-05 00:00:00.0000000`×1, `2025-12-26 00:00:00.0000000`×1, `2026-03-11 00:00:00.0000000`×1, `2026-01-13 00:00:00.0000000`×1, `2025-12-18 00:00:00.0000000`×1, `2026-01-03 00:00:00.0000000`×1, `2026-02-21 00:00:00.0000000`×1
- **`VolUnit`** (1 values) — `4`×32
- **`WeightUnit`** (1 values) — `3`×32
- **`Series`** (6 values) — `1318`×12, `1319`×8, `296`×6, `1320`×4, `294`×1, `1321`×1
- **`TaxDate`** (17 values) — `2025-03-18 00:00:00.0000000`×6, `2025-12-25 00:00:00.0000000`×4, `2025-12-19 00:00:00.0000000`×3, `2026-01-05 00:00:00.0000000`×2, `2025-12-29 00:00:00.0000000`×2, `2026-02-18 00:00:00.0000000`×2, `2026-01-19 00:00:00.0000000`×2, `2026-01-21 00:00:00.0000000`×2, `2026-02-21 00:00:00.0000000`×1, `2026-01-03 00:00:00.0000000`×1, `2025-12-18 00:00:00.0000000`×1, `2026-01-13 00:00:00.0000000`×1, `2026-03-11 00:00:00.0000000`×1, `2025-12-26 00:00:00.0000000`×1, `2025-12-05 00:00:00.0000000`×1, `2025-01-06 00:00:00.0000000`×1, `2026-02-19 00:00:00.0000000`×1
- **`isCrin`** (1 values) — `N`×32
- **`FinncPriod`** (6 values) — `22`×12, `23`×8, `12`×6, `24`×4, `10`×1, `25`×1
- **`UserSign`** (3 values) — `20`×17, `22`×13, `24`×2
- **`selfInv`** (1 values) — `N`×32
- **`VatPaid`** (18 values) — `0.000000`×15, `18369.529600`×1, `9491.460000`×1, `1695.000000`×1, `24280.623500`×1, `50959.789400`×1, `6085.780000`×1, `10934.878500`×1, `1519.065700`×1, `14732.154500`×1, `21028.578000`×1, `4302.666900`×1, `1523.810000`×1, `13277.621000`×1, `8100.832500`×1, `19579.018000`×1, `1860.000000`×1, `9659.979500`×1
- **`VatPaidSys`** (18 values) — `0.000000`×15, `18369.529600`×1, `9491.460000`×1, `1695.000000`×1, `24280.623500`×1, `50959.789400`×1, `10934.878500`×1, `1519.065700`×1, `9659.979500`×1, `1860.000000`×1, `19579.018000`×1, `8100.832500`×1, `13277.621000`×1, `14732.154500`×1, `1523.810000`×1, `4302.666900`×1, `21028.578000`×1, `6085.780000`×1
- **`WddStatus`** (1 values) — `-`×32
- **`Exported`** (1 values) — `N`×32
- **`StationID`** (4 values) — `9`×25, `335`×5, `223`×1, `58`×1
- **`NetProc`** (1 values) — `N`×32
- **`ShipToCode`** (20 values) — `INNOVATIVE RETAIL CONCEPTS PVT LTD AHMEDABAD`×5, `MAKKAR GENERAL STORE PUNJAB`×3, `BRIJ LAL SOHAN LAL PUNJAB`×3, `R.V TRADING COMPANY GURDASPUR`×2, `G PURE INDIA DELIVERY`×2, `INNOVATIVE RETAIL CONCEPTS PVT LTD THANE`×2, `JINDAL BROTHERS PUNJAB`×2, `WAHEGURU TRADERS MUKTSAR`×1, `CHARAN DASS BANARSI DASS PUNJAB`×1, `INNOVATIVE RETAIL CONCEPTS PVT LTD DWARKA`×1, `PARSHOTAM LAL VISHWA NATH-PUNJAB`×1, `JIVO MART PVT LTD MAYAPURI`×1, `ARJUN DASS & SONS PUNJAB NEW DELIVERY`×1, `GOLDWAY FOODS PVT LTD PUNJAB`×1, `BRIJ LAL DURGA DASS DHURI`×1, `HK AGENCIES SANGRUR`×1, `STALL AT RAKAB GANJ DSD NEW DELHI`×1, `SHRAY FOOD & BEVERAGES PRIVATE LIMITED NEW DELHI`×1, `SUBHASH CHANDER TARUN KUMAR NAWANSHAHR`×1, `BHARAT BHUSHAN & SONS DELIVERY`×1
- **`RoundDif`** (20 values) — `0.000000`×11, `-0.660000`×2, `-0.041000`×2, `-0.130000`×1, `-0.244500`×1, `-0.285000`×1, `-0.208000`×1, `-0.683000`×1, `-0.569500`×1, `-0.120600`×1, `-0.448500`×1, `-0.888000`×1, `-0.124000`×1, `-0.378700`×1, `-0.138000`×1, `-0.380000`×1, `-0.482500`×1, `-0.578100`×1, `-0.931000`×1, `-0.093500`×1
- **`RoundDifSy`** (20 values) — `0.000000`×11, `-0.041000`×2, `-0.660000`×2, `-0.378700`×1, `-0.138000`×1, `-0.380000`×1, `-0.124000`×1, `-0.093500`×1, `-0.482500`×1, `-0.888000`×1, `-0.448500`×1, `-0.120600`×1, `-0.569500`×1, `-0.683000`×1, `-0.208000`×1, `-0.285000`×1, `-0.130000`×1, `-0.244500`×1, `-0.578100`×1, `-0.931000`×1
- **`submitted`** (1 values) — `N`×32
- **`PoPrss`** (1 values) — `N`×32
- **`Rounding`** (2 values) — `Y`×25, `N`×7
- **`RevisionPo`** (1 values) — `N`×32
- **`PickStatus`** (1 values) — `N`×32
- **`Pick`** (1 values) — `N`×32
- **`BlockDunn`** (1 values) — `N`×32
- **`PayBlock`** (1 values) — `N`×32
- **`MaxDscn`** (1 values) — `N`×32
- **`Reserve`** (1 values) — `N`×32
- **`Max1099`** (28 values) — `199320.660000`×3, `278830.041000`×2, `509893.093500`×2, `162084.373502`×1, `1096068.096900`×1, `411159.378000`×1, `147487.168500`×1, `204321.285000`×1, `278355.000000`×1, `1070155.578135`×1, `192364.683000`×1, `39060.000000`×1, `31900.378650`×1, `162084.888000`×1, `213596.208000`×1, `127801.380000`×1, `16604.931000`×1, `32000.010000`×1, `224411.124000`×1, `385760.120550`×1, `226811.130000`×1, `35595.000000`×1, `90356.004060`×1, `309375.244500`×1, `170117.482500`×1, `229632.448500`×1, `202859.569500`×1, `441600.138000`×1
- **`DeferrTax`** (1 values) — `N`×32
- **`BoeReserev`** (1 values) — `N`×32
- **`Installmnt`** (1 values) — `1`×32
- **`VATFirst`** (1 values) — `N`×32
- **`CEECFlag`** (2 values) — `Y`×17, `N`×15
- **`CtlAccount`** (4 values) — `1101001`×21, `1101005`×9, `1101012`×1, `1101007`×1
- **`BPLId`** (3 values) — `3`×16, `2`×14, `1`×2
- **`BPLName`** (3 values) — `PUNJAB`×16, `FACTORY`×14, `DELHI`×2
- **`VATRegNum`** (3 values) — `03AACCJ4223F1Z6`×16, `06AACCJ4223F1Z0`×14, `07AACCJ4223F1ZY`×2
- **`SumAbsId`** (1 values) — `-1`×32
- **`PIndicator`** (6 values) — `DEC-25-26`×12, `JAN-25-26`×8, `Mar-24-25`×6, `FEB-25-26`×4, `Jan-24-25`×1, `MAR-25-26`×1
- **`UseShpdGd`** (1 values) — `N`×32
- **`DocSubType`** (1 values) — `--`×32
- **`DpmStatus`** (1 values) — `O`×32
- **`DpmDrawn`** (1 values) — `N`×32
- **`Posted`** (1 values) — `Y`×32
- **`PayToCode`** (20 values) — `INNOVATIVE RETAIL CONCEPTS PVT LTD AHMEDABAD`×5, `MAKKAR GENERAL STORE PUNJAB`×3, `BRIJ LAL SOHAN LAL PUNJAB`×3, `R.V TRADING COMPANY GURDASPUR`×2, `JINDAL BROTHERS PUNJAB`×2, `G PURE INDIA BILLING`×2, `INNOVATIVE RETAIL CONCEPTS PVT LTD THANE`×2, `HK AGENCIES SANGRUR`×1, `PARSHOTAM LAL VISHWA NATH-PUNJAB`×1, `JIVO MART PVT LTD RAJOURI GARDEN`×1, `CHARAN DASS BANARSI DASS PUNJAB`×1, `WAHEGURU TRADERS MUKTSAR`×1, `SHRAY FOOD & BEVERAGES PRIVATE LIMITED NEW DELHI`×1, `BRIJ LAL DURGA DASS DHURI`×1, `GOLDWAY FOODS PVT LTD PUNJAB`×1, `SUBHASH CHANDER TARUN KUMAR NAWANSHAHR`×1, `INNOVATIVE RETAIL CONCEPT SONIPAT`×1, `STALL AT RAKAB GANJ DSD NEW DELHI`×1, `ARJUN DASS & SONS PUNJAB NEW BILLING`×1, `BHARAT BHUSHAN & SONS BILLING`×1
- **`IsPaytoBnk`** (1 values) — `N`×32
- **`isIns`** (1 values) — `N`×32
- **`VersionNum`** (2 values) — `10.00.310.21`×24, `10.00.250.15`×8
- **`LangCode`** (1 values) — `8`×32
- **`BPNameOW`** (1 values) — `N`×32
- **`BillToOW`** (1 values) — `N`×32
- **`ShipToOW`** (1 values) — `N`×32
- **`RetInvoice`** (1 values) — `N`×32
- **`Model`** (1 values) — `0`×32
- **`UseCorrVat`** (1 values) — `N`×32
- **`BlkCredMmo`** (1 values) — `N`×32
- **`OpenForLaC`** (1 values) — `Y`×32
- **`Excised`** (1 values) — `O`×32
- **`DutyStatus`** (1 values) — `Y`×32
- **`AutoCrtFlw`** (1 values) — `N`×32
- **`VatJENum`** (1 values) — `-1`×32
- **`InsurOp347`** (1 values) — `N`×32
- **`IgnRelDoc`** (1 values) — `N`×32
- **`ResidenNum`** (1 values) — `1`×32
- **`PQTGrpHW`** (1 values) — `N`×32
- **`DocManClsd`** (1 values) — `N`×32
- **`ClosingOpt`** (1 values) — `1`×32
- **`Ordered`** (1 values) — `N`×32
- **`NTSApprov`** (1 values) — `N`×32
- **`PayDuMonth`** (1 values) — `N`×32
- **`ExtraDays`** (2 values) — `0`×23, `30`×9
- **`EDocGenTyp`** (1 values) — `N`×32
- **`OnlineQuo`** (1 values) — `N`×32
- **`EDocStatus`** (1 values) — `C`×32
- **`EDocProces`** (1 values) — `C`×32
- **`EDocCancel`** (1 values) — `N`×32
- **`EDocTest`** (1 values) — `N`×32
- **`DpmAsDscnt`** (1 values) — `N`×32
- **`AtcEntry`** (14 values) — `NULL`×19, `119757`×1, `125229`×1, `120390`×1, `121391`×1, `121611`×1, `123780`×1, `119487`×1, `121604`×1, `119489`×1, `120402`×1, `132452`×1, `125252`×1, `119488`×1
- **`GTSRlvnt`** (1 values) — `N`×32
- **`SrvTaxRule`** (1 values) — `N`×32
- **`AssetDate`** (4 values) — `NULL`×28, `2025-12-29 00:00:00.0000000`×2, `2025-12-19 00:00:00.0000000`×1, `2025-12-25 00:00:00.0000000`×1
- **`Notify`** (2 values) — `NULL`×20, `N`×12
- **`ReqType`** (1 values) — `12`×32
- **`OriginType`** (1 values) — `M`×32
- **`IsReuseNum`** (1 values) — `N`×32
- **`IsReuseNFN`** (1 values) — `N`×32
- **`DocDlvry`** (1 values) — `0`×32
- **`EnvTypeNFe`** (1 values) — `-1`×32
- **`IsAlt`** (1 values) — `N`×32
- **`AltBaseTyp`** (1 values) — `-1`×32
- **`PrintSEPA`** (1 values) — `N`×32
- **`RelatedTyp`** (1 values) — `-1`×32
- **`PoDropPrss`** (1 values) — `N`×32
- **`ExclTaxRep`** (1 values) — `N`×32
- **`Revision`** (1 values) — `N`×32
- **`GSTTranTyp`** (1 values) — `GA`×32
- **`BaseType`** (1 values) — `-1`×32
- **`ComTrade`** (1 values) — `E`×32
- **`UseBilAddr`** (2 values) — `Y`×25, `N`×7
- **`IssReason`** (1 values) — `1`×32
- **`ComTradeRt`** (1 values) — `N`×32
- **`SplitPmnt`** (1 values) — `N`×32
- **`SelfPosted`** (1 values) — `N`×32
- **`DPPStatus`** (1 values) — `N`×32
- **`EWBGenType`** (1 values) — `N`×32
- **`EDocType`** (1 values) — `F`×32
- **`AggregDoc`** (1 values) — `N`×32
- **`DataVers`** (8 values) — `1`×10, `2`×7, `4`×6, `5`×3, `3`×3, `21`×1, `13`×1, `6`×1
- **`IndFinal`** (1 values) — `N`×32
- **`PostPmntWT`** (1 values) — `N`×32
- **`FCEPmnMean`** (1 values) — `N`×32
- **`NotRel4MI`** (1 values) — `N`×32
- **`Rel4PPTax`** (1 values) — `N`×32
- **`ConfrmedBy`** (3 values) — `20`×17, `22`×13, `24`×2
- **`ConfrmedOn`** (17 values) — `2025-03-18 00:00:00.0000000`×6, `2025-12-25 00:00:00.0000000`×4, `2025-12-19 00:00:00.0000000`×3, `2026-01-05 00:00:00.0000000`×2, `2026-01-19 00:00:00.0000000`×2, `2026-01-21 00:00:00.0000000`×2, `2026-02-18 00:00:00.0000000`×2, `2025-12-29 00:00:00.0000000`×2, `2026-02-21 00:00:00.0000000`×1, `2026-01-03 00:00:00.0000000`×1, `2025-12-18 00:00:00.0000000`×1, `2026-01-13 00:00:00.0000000`×1, `2026-03-11 00:00:00.0000000`×1, `2025-12-26 00:00:00.0000000`×1, `2025-12-05 00:00:00.0000000`×1, `2025-01-06 00:00:00.0000000`×1, `2026-02-19 00:00:00.0000000`×1
- **`BookeTdsBP`** (1 values) — `N`×32
- **`DigPayment`** (1 values) — `N`×32
- **`PDueMonEnd`** (1 values) — `N`×32
- **`RShipToOW`** (2 values) — `N`×24, `NULL`×8
- **`AplTaxOnFr`** (1 values) — `N`×32
- **`CpyDtyStts`** (1 values) — `N`×32
- **`U_Basement`** (2 values) — `NULL`×31, `Y`×1
