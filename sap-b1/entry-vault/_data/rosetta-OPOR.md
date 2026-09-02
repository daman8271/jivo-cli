# Rosetta — `PurchaseOrders` (API) ↔ `OPOR` (HANA) · OIL

Derived by value-matching 8 real document(s) (`DocEntry` 13372, 13371, 13368, 13367, 13362, 13360, 13359, 13358) read through both doors. A pair had to agree on **every** document to be reported.

- **26** properties mapped to exactly one column
- **14** of those have a **different name** on the two sides ← the dangerous ones
- 15 ambiguous (several columns held the same value)
- 67 with no column (computed, or on a child table)

## The names that differ — memorise these or look them up

| API property (what you send) | HANA column (what you query) |
|---|---|
| `BPL_IDAssignedToInvoice` | **`BPLId`** |
| `ContactPersonCode` | **`CntctCode`** |
| `ControlAccount` | **`CtlAccount`** |
| `DataVersion` | **`DataVers`** |
| `DocCurrency` | **`DocCur`** |
| `DraftKey` | **`draftKey`** |
| `FinancialPeriod` | **`FinncPriod`** |
| `JournalMemo` | **`JrnlMemo`** |
| `LanguageCode` | **`LangCode`** |
| `PaymentGroupCode` | **`GroupNum`** |
| `PeriodIndicator` | **`PIndicator`** |
| `Reference1` | **`Ref1`** |
| `SalesPersonCode` | **`SlpCode`** |
| `ShipFrom` | **`ShipToCode`** |

## Same name on both sides (12)

`BPLName`, `CardCode`, `CardName`, `Comments`, `DocDueDate`, `DocEntry`, `DocNum`, `ExtraDays`, `PayToCode`, `Series`, `ShipToCode`, `VATRegNum`

## Ambiguous — value matched more than one column

Usually a field SAP stores twice (document currency and system currency), or two flags that happen to agree. Add `--n` to break the tie.

| API property | Candidate columns |
|---|---|
| `CreationDate` | `ConfrmedOn`, `CreateDate`, `UpdateDate` |
| `DocDate` | `DocDate`, `TaxDate` |
| `DocRate` | `ClosingOpt`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `DocTotal` | `DocTotal`, `DocTotalSy` |
| `DocTotalSys` | `DocTotal`, `DocTotalSy` |
| `NumberOfInstallments` | `ClosingOpt`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `RelatedType` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `RoundingDiffAmount` | `RoundDif`, `RoundDifSy` |
| `RoundingDiffAmountSC` | `RoundDif`, `RoundDifSy` |
| `TaxDate` | `DocDate`, `TaxDate` |
| `TransportationCode` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `UpdateDate` | `ConfrmedOn`, `CreateDate`, `UpdateDate` |
| `UserSign` | `ConfrmedBy`, `UserSign`, `UserSign2` |
| `VatSum` | `VatSum`, `VatSumSy` |
| `VatSumSys` | `VatSum`, `VatSumSy` |

## No column found (67)

Computed by the Service Layer, held on a child table, or genuinely absent from the header. Not a bug — just not queryable from this table.

`Address`, `Address2`, `ApplyCurrentVATRatesForDownPaymentsToDraw`, `ApplyTaxOnFirstInstallment`, `ArchiveNonremovableSalesQuotation`, `AuthorizationStatus`, `BillOfExchangeReserved`, `BlockDunning`, `CancelStatus`, `Cancelled`, `ClosingOption`, `CommissionTrade`, `CommissionTradeReturn`, `Confirmed`, `CreateOnlineQuotation`, `DeferredTax`, `DocObjectCode`, `DocTime`, `DocType`, `DocumentDelivery`, `DocumentStatus`, `DocumentSubType`, `DownPaymentStatus`, `DownPaymentType`, `DutyStatus`, `EDocGenerationType`, `EDocStatus`, `EndAt`, `ExcludeFromTaxReportControlStatementVAT`, `FatherType`, `GroupHandWritten`, `HandWritten`, `InsuranceOperation347`, `InterimType`, `InventoryStatus`, `IsAlteration`, `IsPayToBank`, `MaximumCashDiscount`, `NTSApproved`, `NetProcedure`, `NotRelevantForMonthlyInvoice`, `OpenForLandedCosts`, `PartialSupply`, `PaymentBlock`, `Pick`, `PickStatus`, `PlasticPackagingTaxRelevant`, `PrintSEPADirect`, `Printed`, `RelevantToGTS`, `Reserve`, `ReserveInvoice`, `ReuseDocumentNum`, `ReuseNotaFiscalNum`, `RevisionPo`, `Rounding`, `ShowSCN`, `StartFrom`, `Submitted`, `SummeryType`, `TaxOnInstallments`, `UpdateTime`, `UseBillToAddrToDetermineTax`, `UseCorrectionVATGroup`, `UseShpdGoodsAct`, `WareHouseUpdateType`, `odata.etag`
