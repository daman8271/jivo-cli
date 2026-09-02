# Rosetta — `Invoices` (API) ↔ `OINV` (HANA) · OIL

Derived by value-matching 8 real document(s) (`DocEntry` 78973, 78970, 78968, 78964, 78963, 78961, 78960, 78959) read through both doors. A pair had to agree on **every** document to be reported.

- **25** properties mapped to exactly one column
- **13** of those have a **different name** on the two sides ← the dangerous ones
- 23 ambiguous (several columns held the same value)
- 74 with no column (computed, or on a child table)

## The names that differ — memorise these or look them up

| API property (what you send) | HANA column (what you query) |
|---|---|
| `BPL_IDAssignedToInvoice` | **`BPLId`** |
| `ContactPersonCode` | **`CntctCode`** |
| `ControlAccount` | **`CtlAccount`** |
| `DocCurrency` | **`DocCur`** |
| `DocumentsOwner` | **`OwnerCode`** |
| `DraftKey` | **`draftKey`** |
| `FinancialPeriod` | **`FinncPriod`** |
| `JournalMemo` | **`JrnlMemo`** |
| `LanguageCode` | **`LangCode`** |
| `PeriodIndicator` | **`PIndicator`** |
| `SalesPersonCode` | **`SlpCode`** |
| `ShipFrom` | **`ShipToCode`** |
| `TransNum` | **`TransId`** |

## Same name on both sides (12)

`BPLName`, `CardCode`, `CardName`, `Comments`, `DocEntry`, `NumAtCard`, `PayToCode`, `Series`, `ShipToCode`, `U_PONo`, `U_SALES_PERSON`, `VATRegNum`

## Ambiguous — value matched more than one column

Usually a field SAP stores twice (document currency and system currency), or two flags that happen to agree. Add `--n` to break the tie.

| API property | Candidate columns |
|---|---|
| `AssetValueDate` | `AssetDate`, `CreateDate`, `DocDate`, `DocDueDate`, `TaxDate`, `UpdateDate` |
| `BaseType` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `GroupNum`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `CreationDate` | `AssetDate`, `CreateDate`, `DocDate`, `DocDueDate`, `TaxDate`, `UpdateDate` |
| `DataVersion` | `ClosingOpt`, `DataVers`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `DocDate` | `AssetDate`, `CreateDate`, `DocDate`, `DocDueDate`, `TaxDate`, `UpdateDate` |
| `DocDueDate` | `AssetDate`, `CreateDate`, `DocDate`, `DocDueDate`, `TaxDate`, `UpdateDate` |
| `DocNum` | `DocNum`, `Ref1` |
| `DocRate` | `ClosingOpt`, `DataVers`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `DocTotal` | `DocTotal`, `DocTotalSy` |
| `DocTotalSys` | `DocTotal`, `DocTotalSy` |
| `IssuingReason` | `ClosingOpt`, `DataVers`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `NumberOfInstallments` | `ClosingOpt`, `DataVers`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `PaymentGroupCode` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `GroupNum`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `Reference1` | `DocNum`, `Ref1` |
| `RelatedType` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `GroupNum`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `RoundingDiffAmount` | `RoundDif`, `RoundDifSy` |
| `RoundingDiffAmountSC` | `RoundDif`, `RoundDifSy` |
| `TaxDate` | `AssetDate`, `CreateDate`, `DocDate`, `DocDueDate`, `TaxDate`, `UpdateDate` |
| `TransportationCode` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `GroupNum`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `UpdateDate` | `AssetDate`, `CreateDate`, `DocDate`, `DocDueDate`, `TaxDate`, `UpdateDate` |
| `UserSign` | `UserSign`, `UserSign2` |
| `VatSum` | `VatSum`, `VatSumSy` |
| `VatSumSys` | `VatSum`, `VatSumSy` |

## No column found (74)

Computed by the Service Layer, held on a child table, or genuinely absent from the header. Not a bug — just not queryable from this table.

`Address`, `Address2`, `ApplyCurrentVATRatesForDownPaymentsToDraw`, `ApplyTaxOnFirstInstallment`, `ArchiveNonremovableSalesQuotation`, `AuthorizationStatus`, `BillOfExchangeReserved`, `BlockDunning`, `CancelStatus`, `Cancelled`, `ClosingOption`, `CommissionTrade`, `CommissionTradeReturn`, `Confirmed`, `CreateOnlineQuotation`, `DeferredTax`, `DigitalPayments`, `DocObjectCode`, `DocTime`, `DocType`, `DocumentDelivery`, `DocumentStatus`, `DocumentSubType`, `DownPaymentStatus`, `DownPaymentType`, `DutyStatus`, `EDocGenerationType`, `EDocStatus`, `EDocType`, `EndAt`, `ExcludeFromTaxReportControlStatementVAT`, `FCEAsPaymentMeans`, `FatherType`, `GSTTransactionType`, `GroupHandWritten`, `HandWritten`, `IndFinal`, `InsuranceOperation347`, `InterimType`, `InventoryStatus`, `InvoicePayment`, `IsAlteration`, `IsPayToBank`, `MaximumCashDiscount`, `NTSApproved`, `NetProcedure`, `NotRelevantForMonthlyInvoice`, `OpenForLandedCosts`, `PartialSupply`, `PaymentBlock`, `Pick`, `PickStatus`, `PlasticPackagingTaxRelevant`, `PrintSEPADirect`, `Printed`, `RelevantToGTS`, `Reserve`, `ReserveInvoice`, `ReuseDocumentNum`, `ReuseNotaFiscalNum`, `Revision`, `RevisionPo`, `Rounding`, `ShowSCN`, `StartFrom`, `Submitted`, `SummeryType`, `TaxOnInstallments`, `UpdateTime`, `UseBillToAddrToDetermineTax`, `UseCorrectionVATGroup`, `UseShpdGoodsAct`, `WareHouseUpdateType`, `odata.etag`
