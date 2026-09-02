# Rosetta — `PurchaseCreditNotes` (API) ↔ `ORPC` (HANA) · OIL

Derived by value-matching 8 real document(s) (`DocEntry` 6958, 6957, 6956, 6948, 6825, 6824, 6799, 6794) read through both doors. A pair had to agree on **every** document to be reported.

- **26** properties mapped to exactly one column
- **16** of those have a **different name** on the two sides ← the dangerous ones
- 25 ambiguous (several columns held the same value)
- 71 with no column (computed, or on a child table)

## The names that differ — memorise these or look them up

| API property (what you send) | HANA column (what you query) |
|---|---|
| `AttachmentEntry` | **`AtcEntry`** |
| `BPL_IDAssignedToInvoice` | **`BPLId`** |
| `ContactPersonCode` | **`CntctCode`** |
| `ControlAccount` | **`CtlAccount`** |
| `DataVersion` | **`DataVers`** |
| `DocCurrency` | **`DocCur`** |
| `DraftKey` | **`draftKey`** |
| `FinancialPeriod` | **`FinncPriod`** |
| `JournalMemo` | **`JrnlMemo`** |
| `LanguageCode` | **`LangCode`** |
| `OriginalRefDate` | **`RevRefDate`** |
| `OriginalRefNo` | **`RevRefNo`** |
| `PaymentGroupCode` | **`GroupNum`** |
| `PeriodIndicator` | **`PIndicator`** |
| `SalesPersonCode` | **`SlpCode`** |
| `TransNum` | **`TransId`** |

## Same name on both sides (10)

`BPLName`, `CardCode`, `CardName`, `Comments`, `DocEntry`, `ExtraDays`, `NumAtCard`, `Series`, `TaxDate`, `VATRegNum`

## Ambiguous — value matched more than one column

Usually a field SAP stores twice (document currency and system currency), or two flags that happen to agree. Add `--n` to break the tie.

| API property | Candidate columns |
|---|---|
| `AssetValueDate` | `AssetDate`, `DocDate`, `DocDueDate` |
| `CreationDate` | `CreateDate`, `UpdateDate` |
| `DocDate` | `AssetDate`, `DocDate`, `DocDueDate` |
| `DocDueDate` | `AssetDate`, `DocDate`, `DocDueDate` |
| `DocNum` | `DocNum`, `Ref1` |
| `DocRate` | `ClosingOpt`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `DocTotal` | `DocTotal`, `DocTotalSy` |
| `DocTotalSys` | `DocTotal`, `DocTotalSy` |
| `IssuingReason` | `ClosingOpt`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `NumberOfInstallments` | `ClosingOpt`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `PaidToDate` | `DocTotal`, `DocTotalSy`, `PaidSys`, `PaidToDate` |
| `PaidToDateSys` | `DocTotal`, `DocTotalSy`, `PaidSys`, `PaidToDate` |
| `PayToCode` | `PayToCode`, `RShipToCod`, `ShipToCode` |
| `Reference1` | `DocNum`, `Ref1` |
| `RelatedType` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `RoundingDiffAmount` | `RoundDif`, `RoundDifSy` |
| `RoundingDiffAmountSC` | `RoundDif`, `RoundDifSy` |
| `ShipFrom` | `PayToCode`, `RShipToCod`, `ShipToCode` |
| `ShipToCode` | `PayToCode`, `RShipToCod`, `ShipToCode` |
| `ShipToCodeForReturn` | `PayToCode`, `RShipToCod`, `ShipToCode` |
| `TransportationCode` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `UpdateDate` | `CreateDate`, `UpdateDate` |
| `UserSign` | `UserSign`, `UserSign2` |
| `VatSum` | `VatSum`, `VatSumSy` |
| `VatSumSys` | `VatSum`, `VatSumSy` |

## No column found (71)

Computed by the Service Layer, held on a child table, or genuinely absent from the header. Not a bug — just not queryable from this table.

`Address`, `Address2`, `AddressForReturn`, `ApplyCurrentVATRatesForDownPaymentsToDraw`, `ApplyTaxOnFirstInstallment`, `ArchiveNonremovableSalesQuotation`, `AuthorizationStatus`, `BillOfExchangeReserved`, `BlockDunning`, `CancelStatus`, `Cancelled`, `ClosingOption`, `CommissionTrade`, `CommissionTradeReturn`, `Confirmed`, `CreateOnlineQuotation`, `DeferredTax`, `DocObjectCode`, `DocTime`, `DocType`, `DocumentDelivery`, `DocumentStatus`, `DocumentSubType`, `DownPaymentStatus`, `DownPaymentType`, `DutyStatus`, `EDocGenerationType`, `EDocStatus`, `EndAt`, `ExcludeFromTaxReportControlStatementVAT`, `FatherType`, `GSTTransactionType`, `GroupHandWritten`, `HandWritten`, `InsuranceOperation347`, `InterimType`, `InventoryStatus`, `IsAlteration`, `IsPayToBank`, `MaximumCashDiscount`, `NTSApproved`, `NetProcedure`, `NotRelevantForMonthlyInvoice`, `OpenForLandedCosts`, `PartialSupply`, `PaymentBlock`, `Pick`, `PickStatus`, `PlasticPackagingTaxRelevant`, `PrintSEPADirect`, `Printed`, `RelevantToGTS`, `ReopenOriginalDocument`, `Reserve`, `ReserveInvoice`, `ReuseDocumentNum`, `ReuseNotaFiscalNum`, `Revision`, `RevisionPo`, `Rounding`, `ShowSCN`, `StartFrom`, `Submitted`, `SummeryType`, `TaxOnInstallments`, `UpdateTime`, `UseBillToAddrToDetermineTax`, `UseCorrectionVATGroup`, `UseShpdGoodsAct`, `WareHouseUpdateType`, `odata.etag`
