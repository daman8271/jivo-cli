# Rosetta — `PurchaseInvoices` (API) ↔ `OPCH` (HANA) · OIL

Derived by value-matching 8 real document(s) (`DocEntry` 49897, 49891, 49887, 49881, 49820, 49818, 49817, 49778) read through both doors. A pair had to agree on **every** document to be reported.

- **33** properties mapped to exactly one column
- **15** of those have a **different name** on the two sides ← the dangerous ones
- 26 ambiguous (several columns held the same value)
- 70 with no column (computed, or on a child table)

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
| `PaymentGroupCode` | **`GroupNum`** |
| `PeriodIndicator` | **`PIndicator`** |
| `SalesPersonCode` | **`SlpCode`** |
| `ShipFrom` | **`ShipToCode`** |
| `TransNum` | **`TransId`** |

## Same name on both sides (18)

`BPLName`, `BaseEntry`, `BaseType`, `CardCode`, `CardName`, `Comments`, `DocEntry`, `ExtraDays`, `NumAtCard`, `PayToCode`, `Series`, `ShipToCode`, `TaxDate`, `U_BilltyNumber`, `U_TransporterName`, `U_UNE_ACTH`, `U_VehicleNoM`, `VATRegNum`

## Ambiguous — value matched more than one column

Usually a field SAP stores twice (document currency and system currency), or two flags that happen to agree. Add `--n` to break the tie.

| API property | Candidate columns |
|---|---|
| `AssetValueDate` | `AssetDate`, `DocDate`, `DocDueDate` |
| `BaseAmount` | `BaseAmnt`, `BaseAmntSC` |
| `BaseAmountSC` | `BaseAmnt`, `BaseAmntSC` |
| `CreationDate` | `CreateDate`, `UpdateDate` |
| `DocDate` | `AssetDate`, `DocDate`, `DocDueDate` |
| `DocDueDate` | `AssetDate`, `DocDate`, `DocDueDate` |
| `DocNum` | `DocNum`, `Ref1` |
| `DocRate` | `ClosingOpt`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `DocTotal` | `DocTotal`, `DocTotalSy` |
| `DocTotalSys` | `DocTotal`, `DocTotalSy` |
| `IssuingReason` | `ClosingOpt`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `NumberOfInstallments` | `ClosingOpt`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `PaidToDate` | `PaidSys`, `PaidToDate` |
| `PaidToDateSys` | `PaidSys`, `PaidToDate` |
| `Reference1` | `DocNum`, `Ref1` |
| `RelatedType` | `AltBaseTyp`, `EnvTypeNFe`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `RoundingDiffAmount` | `RoundDif`, `RoundDifSy` |
| `RoundingDiffAmountSC` | `RoundDif`, `RoundDifSy` |
| `TransportationCode` | `AltBaseTyp`, `EnvTypeNFe`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `U_BiltyDate` | `TaxDate`, `U_BiltyDate` |
| `UpdateDate` | `CreateDate`, `UpdateDate` |
| `UserSign` | `UserSign`, `UserSign2` |
| `VatSum` | `VatSum`, `VatSumSy` |
| `VatSumSys` | `VatSum`, `VatSumSy` |
| `WTAmount` | `WTSum`, `WTSumSC` |
| `WTAmountSC` | `WTSum`, `WTSumSC` |

## No column found (70)

Computed by the Service Layer, held on a child table, or genuinely absent from the header. Not a bug — just not queryable from this table.

`Address`, `Address2`, `ApplyCurrentVATRatesForDownPaymentsToDraw`, `ApplyTaxOnFirstInstallment`, `ArchiveNonremovableSalesQuotation`, `AuthorizationStatus`, `BillOfExchangeReserved`, `BlockDunning`, `CancelStatus`, `Cancelled`, `ClosingOption`, `CommissionTrade`, `CommissionTradeReturn`, `Confirmed`, `CreateOnlineQuotation`, `DeferredTax`, `DocObjectCode`, `DocTime`, `DocType`, `DocumentDelivery`, `DocumentStatus`, `DocumentSubType`, `DownPaymentStatus`, `DownPaymentType`, `DutyStatus`, `EDocGenerationType`, `EDocStatus`, `EndAt`, `ExcludeFromTaxReportControlStatementVAT`, `FatherType`, `GSTTransactionType`, `GroupHandWritten`, `HandWritten`, `InsuranceOperation347`, `InterimType`, `InventoryStatus`, `InvoicePayment`, `IsAlteration`, `IsPayToBank`, `MaximumCashDiscount`, `NTSApproved`, `NetProcedure`, `NotRelevantForMonthlyInvoice`, `OpenForLandedCosts`, `PartialSupply`, `PaymentBlock`, `Pick`, `PickStatus`, `PlasticPackagingTaxRelevant`, `PrintSEPADirect`, `Printed`, `RelevantToGTS`, `Reserve`, `ReserveInvoice`, `ReuseDocumentNum`, `ReuseNotaFiscalNum`, `Revision`, `RevisionPo`, `Rounding`, `ShowSCN`, `StartFrom`, `Submitted`, `SummeryType`, `TaxOnInstallments`, `UpdateTime`, `UseBillToAddrToDetermineTax`, `UseCorrectionVATGroup`, `UseShpdGoodsAct`, `WareHouseUpdateType`, `odata.etag`
