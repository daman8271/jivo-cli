# Rosetta — `Drafts` (API) ↔ `ODRF` (HANA) · OIL

Derived by value-matching 8 real document(s) (`DocEntry` 55184, 55177, 55176, 55175, 55174, 55173, 55172, 55171) read through both doors. A pair had to agree on **every** document to be reported.

- **31** properties mapped to exactly one column
- **12** of those have a **different name** on the two sides ← the dangerous ones
- 26 ambiguous (several columns held the same value)
- 73 with no column (computed, or on a child table)

## The names that differ — memorise these or look them up

| API property (what you send) | HANA column (what you query) |
|---|---|
| `AttachmentEntry` | **`AtcEntry`** |
| `BPL_IDAssignedToInvoice` | **`BPLId`** |
| `ContactPersonCode` | **`CntctCode`** |
| `ControlAccount` | **`CtlAccount`** |
| `DataVersion` | **`DataVers`** |
| `DocCurrency` | **`DocCur`** |
| `FinancialPeriod` | **`FinncPriod`** |
| `JournalMemo` | **`JrnlMemo`** |
| `LanguageCode` | **`LangCode`** |
| `PeriodIndicator` | **`PIndicator`** |
| `SalesPersonCode` | **`SlpCode`** |
| `ShipFrom` | **`ShipToCode`** |

## Same name on both sides (19)

`BPLName`, `CardCode`, `CardName`, `Comments`, `DocDueDate`, `DocEntry`, `DocNum`, `NumAtCard`, `PayToCode`, `ReqType`, `Series`, `ShipToCode`, `TaxDate`, `U_BilltyNumber`, `U_PONo`, `U_SALES_PERSON`, `U_TransporterName`, `U_VehicleNoM`, `VATRegNum`

## Ambiguous — value matched more than one column

Usually a field SAP stores twice (document currency and system currency), or two flags that happen to agree. Add `--n` to break the tie.

| API property | Candidate columns |
|---|---|
| `AssetValueDate` | `AssetDate`, `DocDate` |
| `BaseAmount` | `BaseAmnt`, `BaseAmntSC` |
| `BaseAmountSC` | `BaseAmnt`, `BaseAmntSC` |
| `CreationDate` | `CreateDate`, `UpdateDate` |
| `DocDate` | `AssetDate`, `DocDate` |
| `DocRate` | `ClosingOpt`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `DocTotal` | `DocTotal`, `DocTotalSy` |
| `DocTotalSys` | `DocTotal`, `DocTotalSy` |
| `DraftKey` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `GroupNum`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum`, `draftKey` |
| `IssuingReason` | `ClosingOpt`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `NumberOfInstallments` | `ClosingOpt`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `OriginalRefDate` | `RevRefDate`, `TaxDate`, `U_BiltyDate` |
| `OriginalRefNo` | `NumAtCard`, `RevRefNo` |
| `PaymentGroupCode` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `GroupNum`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum`, `draftKey` |
| `RelatedType` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `GroupNum`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum`, `draftKey` |
| `RoundingDiffAmount` | `RoundDif`, `RoundDifSy` |
| `RoundingDiffAmountSC` | `RoundDif`, `RoundDifSy` |
| `ShipToCodeForReturn` | `PayToCode`, `RShipToCod` |
| `TransportationCode` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `GroupNum`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum`, `draftKey` |
| `U_BiltyDate` | `RevRefDate`, `TaxDate`, `U_BiltyDate` |
| `UpdateDate` | `CreateDate`, `UpdateDate` |
| `UserSign` | `UserSign`, `UserSign2` |
| `VatSum` | `VatSum`, `VatSumSy` |
| `VatSumSys` | `VatSum`, `VatSumSy` |
| `WTAmount` | `WTSum`, `WTSumSC` |
| `WTAmountSC` | `WTSum`, `WTSumSC` |

## No column found (73)

Computed by the Service Layer, held on a child table, or genuinely absent from the header. Not a bug — just not queryable from this table.

`Address`, `Address2`, `AddressForReturn`, `ApplyCurrentVATRatesForDownPaymentsToDraw`, `ApplyTaxOnFirstInstallment`, `ArchiveNonremovableSalesQuotation`, `AuthorizationStatus`, `BillOfExchangeReserved`, `BlockDunning`, `CancelStatus`, `Cancelled`, `ClosingOption`, `CommissionTrade`, `CommissionTradeReturn`, `Confirmed`, `CreateOnlineQuotation`, `DeferredTax`, `DocObjectCode`, `DocTime`, `DocType`, `DocumentDelivery`, `DocumentStatus`, `DocumentSubType`, `DownPaymentStatus`, `DownPaymentType`, `EDocGenerationType`, `EDocStatus`, `EDocType`, `EndAt`, `ExcludeFromTaxReportControlStatementVAT`, `FCEAsPaymentMeans`, `FatherType`, `GSTTransactionType`, `GroupHandWritten`, `HandWritten`, `InsuranceOperation347`, `InterimType`, `InventoryStatus`, `InvoicePayment`, `IsAlteration`, `IsPayToBank`, `MaximumCashDiscount`, `NTSApproved`, `NetProcedure`, `NotRelevantForMonthlyInvoice`, `OpenForLandedCosts`, `PartialSupply`, `PaymentBlock`, `Pick`, `PickStatus`, `PlasticPackagingTaxRelevant`, `PrintSEPADirect`, `Printed`, `RelevantToGTS`, `ReopenOriginalDocument`, `Reserve`, `ReserveInvoice`, `ReuseDocumentNum`, `ReuseNotaFiscalNum`, `Revision`, `RevisionPo`, `Rounding`, `ShowSCN`, `StartFrom`, `Submitted`, `SummeryType`, `TaxOnInstallments`, `UpdateTime`, `UseBillToAddrToDetermineTax`, `UseCorrectionVATGroup`, `UseShpdGoodsAct`, `WareHouseUpdateType`, `odata.etag`
