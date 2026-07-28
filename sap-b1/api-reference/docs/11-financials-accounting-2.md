# Financials & Accounting (part 2) — SAP Business One Service Layer

Reference for the 21 services in the `financials-accounting-2` domain. Purposes, operations, and field names are taken from the Service Layer API reference HTML and the catalog — never invented. Where a purpose is interpreted from the entity name/fields rather than stated in the HTML, it is marked **(inferred)**.

Every service in this domain is a **readable ENTITY** (each exposes a `GET` collection and a `GET(id)`). Example request pairs below use only field names that appear verbatim in the reference's `$select` examples.

- REST base path in examples: `/b1s/v1/` (the reference HTML itself uses `/b1s/v1/`; both are valid endpoints).
- Tool: `sapb1 query <Entity> --select <fields> [--filter "<odata>"] [--top N]`

---

## DistributionRules

1. Define cost-accounting distribution rules (allocation factors) used to spread amounts across a dimension's profit centers. **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET DistributionRules(id)`
   - `GET DistributionRules`
   - `POST DistributionRules`
   - `PATCH DistributionRules(id)`
   - `DELETE DistributionRules(id)`
4. Real fields: `FactorCode`, `FactorDescription`, `TotalFactor`, `Active`, `InWhichDimension`, `IsFixedAmount`

```
GET /b1s/v1/DistributionRules?$select=FactorCode,FactorDescription,TotalFactor&$top=20
```
```
sapb1 query DistributionRules --select FactorCode,FactorDescription,TotalFactor --top 20
```

---

## FAAccountDeterminations

1. Maintain fixed-asset account determinations — the G/L accounts posted to for asset acquisition, depreciation, revaluation and retirement. **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET FAAccountDeterminations(id)`
   - `GET FAAccountDeterminations`
   - `POST FAAccountDeterminations`
   - `PATCH FAAccountDeterminations(id)`
   - `DELETE FAAccountDeterminations(id)`
4. Real fields: `Code`, `Description`, `AssetBalanceSheetAccount`, `OrdinaryDepreciation`, `ClearingAccountAcquisition`, `RevaluationReserveAccount`

```
GET /b1s/v1/FAAccountDeterminations?$select=Code,Description,AssetBalanceSheetAccount&$top=20
```
```
sapb1 query FAAccountDeterminations --select Code,Description,AssetBalanceSheetAccount --top 20
```

---

## FinancialYears

1. Define the company's financial (fiscal) years and their date ranges. **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET FinancialYears(id)`
   - `GET FinancialYears`
   - `POST FinancialYears`
   - `PATCH FinancialYears(id)`
   - `DELETE FinancialYears(id)`
4. Real fields: `AbsEntry`, `Code`, `Description`, `StartDate`, `EndDate`, `AssessYear`

```
GET /b1s/v1/FinancialYears?$select=AbsEntry,Code,Description&$top=20
```
```
sapb1 query FinancialYears --select AbsEntry,Code,Description --top 20
```

---

## FiscalPrinter

1. Register fiscal printer devices used for fiscal document printing (localization requirement). **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET FiscalPrinter(id)`
   - `GET FiscalPrinter`
   - `POST FiscalPrinter`
   - `PATCH FiscalPrinter(id)`
   - `DELETE FiscalPrinter(id)`
4. Real fields: `EquipmentNo`, `Model`, `ManufacturerSerialN`, `FiscalDocumentModel`, `RegisterNo`

```
GET /b1s/v1/FiscalPrinter?$select=EquipmentNo,Model,ManufacturerSerialN&$top=20
```
```
sapb1 query FiscalPrinter --select EquipmentNo,Model,ManufacturerSerialN --top 20
```

---

## Forms1099

1. Manipulate 'Forms1099' — defines new Form 1099 types in addition to the existing types (1099 Miscellaneous, 1099 Interest, and 1099 Dividends).
2. Type: readable ENTITY
3. Operations:
   - `GET Forms1099(id)`
   - `GET Forms1099`
   - `POST Forms1099`
   - `PATCH Forms1099(id)`
   - `DELETE Forms1099(id)`
4. Real fields: `FormCode`, `Form1099`, `Boxes1099` (collection: `Box1099`, `BoxDescription`, `Minimum1099Amount`)

```
GET /b1s/v1/Forms1099?$select=FormCode,Form1099&$top=20
```
```
sapb1 query Forms1099 --select FormCode,Form1099 --top 20
```

---

## GLAccountAdvancedRules

1. Define advanced G/L account determination rules by period / financial year for revenues, expenses and clearing accounts. **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET GLAccountAdvancedRules(id)`
   - `GET GLAccountAdvancedRules`
   - `POST GLAccountAdvancedRules`
   - `PATCH GLAccountAdvancedRules(id)`
   - `DELETE GLAccountAdvancedRules(id)`
4. Real fields: `AbsoluteEntry`, `Code`, `Description`, `Period`, `FinancialYear`, `RevenuesAccount`, `ExpensesAccount`

```
GET /b1s/v1/GLAccountAdvancedRules?$select=AbsoluteEntry,Code,Description&$top=20
```
```
sapb1 query GLAccountAdvancedRules --select AbsoluteEntry,Code,Description --top 20
```

---

## JournalEntries

1. Manipulate 'JournalEntries' — represents journal transactions (manual and posted G/L journal entries).
2. Type: readable ENTITY (with a Cancel action)
3. Operations:
   - `GET JournalEntries(id)`
   - `GET JournalEntries`
   - `POST JournalEntries`
   - `PATCH JournalEntries(id)`
   - `POST JournalEntries(id)/Cancel`
4. Real fields: `ReferenceDate`, `Memo`, `Reference` (line collection `JournalEntryLines`: `AccountCode`, `Debit`, `Credit`)

```
GET /b1s/v1/JournalEntries?$select=ReferenceDate,Memo,Reference&$top=20
```
```
sapb1 query JournalEntries --select ReferenceDate,Memo,Reference --top 20
```

Cancel a posted entry: `POST /b1s/v1/JournalEntries(<id>)/Cancel`

---

## JournalEntryDocumentTypes

1. Define custom document types/short names used to classify journal entries. **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET JournalEntryDocumentTypes(id)`
   - `GET JournalEntryDocumentTypes`
   - `POST JournalEntryDocumentTypes`
   - `PATCH JournalEntryDocumentTypes(id)`
   - `DELETE JournalEntryDocumentTypes(id)`
4. Real fields: `JournalEntryType`, `DocTypeDescription`, `ShortName`

```
GET /b1s/v1/JournalEntryDocumentTypes?$select=JournalEntryType,DocTypeDescription,ShortName&$top=20
```
```
sapb1 query JournalEntryDocumentTypes --select JournalEntryType,DocTypeDescription,ShortName --top 20
```

---

## NFTaxCategories

1. Maintain Nota Fiscal tax categories (Brazil localization). **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET NFTaxCategories(id)`
   - `GET NFTaxCategories`
   - `POST NFTaxCategories`
   - `PATCH NFTaxCategories(id)`
   - `DELETE NFTaxCategories(id)`
4. Real fields: `AbsId`, `Code`, `Locked`, `GPCId`

```
GET /b1s/v1/NFTaxCategories?$select=AbsId,Code,Locked&$top=20
```
```
sapb1 query NFTaxCategories --select AbsId,Code,Locked --top 20
```

---

## NotaFiscalCFOP

1. Maintain CFOP codes (Código Fiscal de Operações e Prestações) used on Brazilian Nota Fiscal documents. **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET NotaFiscalCFOP(id)`
   - `GET NotaFiscalCFOP`
   - `POST NotaFiscalCFOP`
   - `PATCH NotaFiscalCFOP(id)`
   - `DELETE NotaFiscalCFOP(id)`
4. Real fields: `ID`, `Code`, `Description`, `Application`

```
GET /b1s/v1/NotaFiscalCFOP?$select=ID,Code,Description&$top=20
```
```
sapb1 query NotaFiscalCFOP --select ID,Code,Description --top 20
```

---

## NotaFiscalCST

1. Maintain CST codes (Código de Situação Tributária) for Brazilian Nota Fiscal tax situations. **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET NotaFiscalCST(id)`
   - `GET NotaFiscalCST`
   - `POST NotaFiscalCST`
   - `PATCH NotaFiscalCST(id)`
   - `DELETE NotaFiscalCST(id)`
4. Real fields: `ID`, `Code`, `Situation`, `CSTCodeOutgoing`, `DescriptionOutgoing`, `TaxCategory`

```
GET /b1s/v1/NotaFiscalCST?$select=ID,Code,Situation&$top=20
```
```
sapb1 query NotaFiscalCST --select ID,Code,Situation --top 20
```

---

## NotaFiscalUsage

1. Maintain Nota Fiscal usage codes and their mapped incoming/outgoing CFOP codes (in-state, out-state, import/export). **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET NotaFiscalUsage(id)`
   - `GET NotaFiscalUsage`
   - `POST NotaFiscalUsage`
   - `PATCH NotaFiscalUsage(id)`
   - `DELETE NotaFiscalUsage(id)`
4. Real fields: `ID`, `Usage`, `Description`, `IncomingInStateCFOPCode`, `OutgoingInStateCFOPCode`, `OutgoingExportCFOPCode`

```
GET /b1s/v1/NotaFiscalUsage?$select=ID,Usage,IncomingInStateCFOPCode&$top=20
```
```
sapb1 query NotaFiscalUsage --select ID,Usage,IncomingInStateCFOPCode --top 20
```

---

## OccurrenceCodes

1. Maintain occurrence codes used with Bills of Exchange (BoE) processing / status changes. **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET OccurrenceCodes(id)`
   - `GET OccurrenceCodes`
   - `POST OccurrenceCodes`
   - `PATCH OccurrenceCodes(id)`
   - `DELETE OccurrenceCodes(id)`
4. Real fields: `AbsEntry`, `Code`, `Description`, `RequestedBoeStatus`

```
GET /b1s/v1/OccurrenceCodes?$select=AbsEntry,Code,Description&$top=20
```
```
sapb1 query OccurrenceCodes --select AbsEntry,Code,Description --top 20
```

---

## ProfitCenters

1. Define profit centers (cost-accounting dimensions members) with effective date ranges. **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET ProfitCenters(id)`
   - `GET ProfitCenters`
   - `POST ProfitCenters`
   - `PATCH ProfitCenters(id)`
   - `DELETE ProfitCenters(id)`
4. Real fields: `CenterCode`, `CenterName`, `GroupCode`, `EffectiveFrom`, `EffectiveTo`

```
GET /b1s/v1/ProfitCenters?$select=CenterCode,CenterName,GroupCode&$top=20
```
```
sapb1 query ProfitCenters --select CenterCode,CenterName,GroupCode --top 20
```

---

## TaxCodeDeterminations

1. Define rules that automatically determine the tax code on document lines based on conditions. **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET TaxCodeDeterminations(id)`
   - `GET TaxCodeDeterminations`
   - `POST TaxCodeDeterminations`
   - `PATCH TaxCodeDeterminations(id)`
   - `DELETE TaxCodeDeterminations(id)`
4. Real fields: `DocEntry`, `LineNumber`, `DocumentType`, `TaxCode`, `BusinessArea`, `Condition1`

```
GET /b1s/v1/TaxCodeDeterminations?$select=DocEntry,LineNumber,DocumentType&$top=20
```
```
sapb1 query TaxCodeDeterminations --select DocEntry,LineNumber,DocumentType --top 20
```

---

## TaxCodeDeterminationsTCD

1. Configure the newer tax-code determination (TCD) settings — key fields, default AP/AR codes, usages and default withholding taxes. **(inferred)**
2. Type: readable ENTITY (read + update only — no POST/DELETE)
3. Operations:
   - `GET TaxCodeDeterminationsTCD(id)`
   - `GET TaxCodeDeterminationsTCD`
   - `PATCH TaxCodeDeterminationsTCD(id)`
4. Real fields: `AbsId`, `TcdType`, `DftArCode`, `NTSApproval`, `ETaxWebSite`, `ETaxNo`

```
GET /b1s/v1/TaxCodeDeterminationsTCD?$select=AbsId,TcdType,DftArCode&$top=20
```
```
sapb1 query TaxCodeDeterminationsTCD --select AbsId,TcdType,DftArCode --top 20
```

---

## TaxWebSites

1. Maintain tax authority web sites (e-tax portals), including which one is the default. **(inferred)**
2. Type: readable ENTITY (with a SetAsDefault action)
3. Operations:
   - `GET TaxWebSites(id)`
   - `GET TaxWebSites`
   - `POST TaxWebSites`
   - `PATCH TaxWebSites(id)`
   - `DELETE TaxWebSites(id)`
   - `POST TaxWebSites(id)/SetAsDefault`
4. Real fields: `AbsEntry`, `WebSiteName`, `WebSiteURL`, `Description`

```
GET /b1s/v1/TaxWebSites?$select=AbsEntry,WebSiteName,WebSiteURL&$top=20
```
```
sapb1 query TaxWebSites --select AbsEntry,WebSiteName,WebSiteURL --top 20
```

Set default site: `POST /b1s/v1/TaxWebSites(<id>)/SetAsDefault`

---

## VatGroups

1. Manipulate 'VatGroups' — defines tax groups that can be assigned to business partners and items in sales and purchase documents.
2. Type: readable ENTITY
3. Operations:
   - `GET VatGroups(id)`
   - `GET VatGroups`
   - `POST VatGroups`
   - `PATCH VatGroups(id)`
   - `DELETE VatGroups(id)`
4. Real fields: `Code`, `Name`, `Category`, `TaxAccount`, `Rate`, `Effectivefrom`

```
GET /b1s/v1/VatGroups?$select=Code,Name,Category&$filter=Category eq 'bovcInputTax'&$top=20
```
```
sapb1 query VatGroups --select Code,Name,Category --filter "Category eq 'bovcInputTax'" --top 20
```

---

## WithholdingTaxCodes

1. Manipulate 'WithholdingTaxCodes' — defines withholding tax codes that can be applied to business partners, payments, and documents.
2. Type: readable ENTITY
3. Operations:
   - `GET WithholdingTaxCodes(id)`
   - `GET WithholdingTaxCodes`
   - `POST WithholdingTaxCodes`
   - `PATCH WithholdingTaxCodes(id)`
   - `DELETE WithholdingTaxCodes(id)`
4. Real fields: `WTCode`, `WTName`, `Category`, `Account`, `Effectivefrom`

```
GET /b1s/v1/WithholdingTaxCodes?$select=WTCode,WTName,Category&$top=20
```
```
sapb1 query WithholdingTaxCodes --select WTCode,WTName,Category --top 20
```

---

## WitholdingTaxDefinition

1. Manipulate 'WitholdingTaxDefinition' — functionally overlaps `WithholdingTaxCodes` (note the single-'h' entity-name spelling in the API).
2. Type: readable ENTITY
3. Operations:
   - `GET WitholdingTaxDefinition(id)`
   - `GET WitholdingTaxDefinition`
   - `POST WitholdingTaxDefinition`
   - `PATCH WitholdingTaxDefinition(id)`
   - `DELETE WitholdingTaxDefinition(id)`
4. Real fields: `AbsEntry`, `WTaxCode`, `WTaxName`

```
GET /b1s/v1/WitholdingTaxDefinition?$select=AbsEntry,WTaxCode,WTaxName&$top=20
```
```
sapb1 query WitholdingTaxDefinition --select AbsEntry,WTaxCode,WTaxName --top 20
```

---

## WTaxTypeCodes

1. Maintain withholding-tax type codes (categories of withholding tax). **(inferred)**
2. Type: readable ENTITY
3. Operations:
   - `GET WTaxTypeCodes(id)`
   - `GET WTaxTypeCodes`
   - `POST WTaxTypeCodes`
   - `PATCH WTaxTypeCodes(id)`
   - `DELETE WTaxTypeCodes(id)`
4. Real fields: `Code`, `Description` (further fields: query live `$metadata`)

```
GET /b1s/v1/WTaxTypeCodes?$select=Code,Description&$top=20
```
```
sapb1 query WTaxTypeCodes --select Code,Description --top 20
```
