# Rosetta — `PurchaseDeliveryNotes` (API) ↔ `OPDN` (HANA) · OIL

Derived by value-matching 8 real document(s) (`DocEntry` 25995, 25994, 25993, 25992, 25991, 25990, 25988, 25987) read through both doors. A pair had to agree on **every** document to be reported.

- **28** properties mapped to exactly one column
- **13** of those have a **different name** on the two sides ← the dangerous ones
- 19 ambiguous (several columns held the same value)
- 67 with no column (computed, or on a child table)

## The names that differ — memorise these or look them up

| API property (what you send) | HANA column (what you query) |
|---|---|
| `AttachmentEntry` | **`AtcEntry`** |
| `BPL_IDAssignedToInvoice` | **`BPLId`** |
| `ContactPersonCode` | **`CntctCode`** |
| `ControlAccount` | **`CtlAccount`** |
| `DocCurrency` | **`DocCur`** |
| `DraftKey` | **`draftKey`** |
| `FinancialPeriod` | **`FinncPriod`** |
| `JournalMemo` | **`JrnlMemo`** |
| `LanguageCode` | **`LangCode`** |
| `PeriodIndicator` | **`PIndicator`** |
| `SalesPersonCode` | **`SlpCode`** |
| `ShipFrom` | **`ShipToCode`** |
| `TransNum` | **`TransId`** |

## Same name on both sides (15)

`BPLName`, `CardCode`, `CardName`, `Comments`, `DocEntry`, `NumAtCard`, `PayToCode`, `Series`, `ShipToCode`, `TaxDate`, `U_BilltyNumber`, `U_BiltyDate`, `U_TransporterName`, `U_VehicleNoM`, `VATRegNum`

## Ambiguous — value matched more than one column

Usually a field SAP stores twice (document currency and system currency), or two flags that happen to agree. Add `--n` to break the tie.

| API property | Candidate columns |
|---|---|
| `CreationDate` | `CreateDate`, `UpdateDate` |
| `DataVersion` | `ClosingOpt`, `DataVers`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `DocDate` | `DocDate`, `DocDueDate` |
| `DocDueDate` | `DocDate`, `DocDueDate` |
| `DocNum` | `DocNum`, `Ref1` |
| `DocRate` | `ClosingOpt`, `DataVers`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `DocTotal` | `DocTotal`, `DocTotalSy` |
| `DocTotalSys` | `DocTotal`, `DocTotalSy` |
| `NumberOfInstallments` | `ClosingOpt`, `DataVers`, `DocRate`, `Installmnt`, `IssReason`, `ResidenNum`, `SysRate` |
| `PaymentGroupCode` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `GroupNum`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `Reference1` | `DocNum`, `Ref1` |
| `RelatedType` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `GroupNum`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `RoundingDiffAmount` | `RoundDif`, `RoundDifSy` |
| `RoundingDiffAmountSC` | `RoundDif`, `RoundDifSy` |
| `TransportationCode` | `AltBaseTyp`, `BaseType`, `EnvTypeNFe`, `GroupNum`, `RelatedTyp`, `SumAbsId`, `TrnspCode`, `VatJENum` |
| `UpdateDate` | `CreateDate`, `UpdateDate` |
| `UserSign` | `UserSign`, `UserSign2` |
| `VatSum` | `VatSum`, `VatSumSy` |
| `VatSumSys` | `VatSum`, `VatSumSy` |

## No column found (67)

Computed by the Service Layer, held on a child table, or genuinely absent from the header. Not a bug — just not queryable from this table.

`Address`, `Address2`, `ApplyCurrentVATRatesForDownPaymentsToDraw`, `ApplyTaxOnFirstInstallment`, `ArchiveNonremovableSalesQuotation`, `AuthorizationStatus`, `BillOfExchangeReserved`, `BlockDunning`, `CancelStatus`, `Cancelled`, `ClosingOption`, `CommissionTrade`, `CommissionTradeReturn`, `Confirmed`, `CreateOnlineQuotation`, `DeferredTax`, `DocObjectCode`, `DocTime`, `DocType`, `DocumentDelivery`, `DocumentStatus`, `DocumentSubType`, `DownPaymentStatus`, `DownPaymentType`, `DutyStatus`, `EDocGenerationType`, `EDocStatus`, `EndAt`, `ExcludeFromTaxReportControlStatementVAT`, `FatherType`, `GroupHandWritten`, `HandWritten`, `InsuranceOperation347`, `InterimType`, `InventoryStatus`, `IsAlteration`, `IsPayToBank`, `MaximumCashDiscount`, `NTSApproved`, `NetProcedure`, `NotRelevantForMonthlyInvoice`, `OpenForLandedCosts`, `PartialSupply`, `PaymentBlock`, `Pick`, `PickStatus`, `PlasticPackagingTaxRelevant`, `PrintSEPADirect`, `Printed`, `RelevantToGTS`, `Reserve`, `ReserveInvoice`, `ReuseDocumentNum`, `ReuseNotaFiscalNum`, `RevisionPo`, `Rounding`, `ShowSCN`, `StartFrom`, `Submitted`, `SummeryType`, `TaxOnInstallments`, `UpdateTime`, `UseBillToAddrToDetermineTax`, `UseCorrectionVATGroup`, `UseShpdGoodsAct`, `WareHouseUpdateType`, `odata.etag`
