# SAP Business One Service Layer — Financials & Accounting (part 1)

Reference for the 40 services in the `financials-accounting-1` domain of the SAP Business One Service Layer.

**Two kinds of resource:**
- **readable ENTITY** — an OData entity set supporting `GET`/`GET(id)` plus (usually) `POST`/`PATCH`/`DELETE`. Queryable with `$select`/`$filter`/`$top`/`$orderby`/`$skip`. 17 of these here.
- **function/action Service** — a `*Service` endpoint that wraps a named function/action call (typically `POST`, occasionally a convenience `GET`). No queryable field set. 23 of these here.

**Conventions in this doc**
- Operations are copied verbatim from `catalog/services.json` (never invented).
- Field names come from the real `$select` examples in the API-reference HTML (never invented). Where the HTML gives no fields, the doc says "query live `$metadata`".
- The one-line purpose is tagged `(inferred)` when it comes from the resource name / domain knowledge rather than a specific HTML sentence — the HTML's own description text for these resources is the generic "This API enables you to invoke the interfaces defined on 'X'." / "This entity enables you to manipulate 'X'.".
- Examples use base path `/b1s/v1` (the CLI default). The HTML shows the same routes under `/b1s/v2`; both are valid.

---

## AccountCategoryService

1. **Purpose:** Retrieve the list of G/L account categories. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `GET AccountCategoryService_GetCategoryList`
   - `POST AccountCategoryService_GetCategoryList`

## AccountsService

1. **Purpose:** Create an opening balance for G/L accounts. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST AccountsService_CreateOpenBalance`

## BEMReplicationPeriodService

1. **Purpose:** Retrieve the list of BEM (Budget/Enablement) replication periods. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `GET BEMReplicationPeriodService_GetList`
   - `POST BEMReplicationPeriodService_GetList`

## CostCenterTypesService

1. **Purpose:** Retrieve the list of cost center types. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST CostCenterTypesService_GetCostCenterTypeList`

## CostElementService

1. **Purpose:** Retrieve the list of cost elements. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST CostElementService_GetCostElementList`

## DeductibleTaxService

1. **Purpose:** Retrieve the list of deductible taxes. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST DeductibleTaxService_GetList`

## DeductionTaxSubGroupsService

1. **Purpose:** Retrieve the list of deduction tax sub-groups. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST DeductionTaxSubGroupsService_GetDeductionTaxSubGroupList`

## DimensionsService

1. **Purpose:** Retrieve the list of accounting dimensions. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST DimensionsService_GetDimensionList`

## DistributionRulesService

1. **Purpose:** Retrieve the list of cost-accounting distribution rules. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST DistributionRulesService_GetDistributionRuleList`

## FAAccountDeterminationsService

1. **Purpose:** Retrieve the list of fixed-asset account determinations. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST FAAccountDeterminationsService_GetList`

## FinancialYearsService

1. **Purpose:** Retrieve the list of financial (fiscal) years. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST FinancialYearsService_GetFinancialYearList`

## FiscalPrinterService

1. **Purpose:** Retrieve the list of configured fiscal printers. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST FiscalPrinterService_GetFiscalPrinterList`

## GLAccountAdvancedRulesService

1. **Purpose:** Retrieve the list of G/L account advanced (determination) rules. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST GLAccountAdvancedRulesService_GetList`

## JournalEntryDocumentTypeService

1. **Purpose:** Retrieve the list of journal-entry document types. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST JournalEntryDocumentTypeService_GetList`

## JournalVouchersService

1. **Purpose:** Add a journal voucher (a batch of draft journal entries). (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST JournalVouchersService_Add`

## NFTaxCategoriesService

1. **Purpose:** Retrieve the list of Nota Fiscal tax categories (Brazil localization). (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST NFTaxCategoriesService_GetList`

## OccurrenceCodesService

1. **Purpose:** Retrieve the list of occurrence codes. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST OccurrenceCodesService_GetList`

## ProfitCentersService

1. **Purpose:** Retrieve the list of profit centers (cost centers). (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST ProfitCentersService_GetProfitCenterList`

## ServiceTaxPostingService

1. **Purpose:** Post service tax and retrieve the taxable deliveries it applies to. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST ServiceTaxPostingService_PostServiceTax`
   - `POST ServiceTaxPostingService_GetTaxableDeliveries`

## TaxCodeDeterminationsService

1. **Purpose:** Retrieve the list of tax code determination rules. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST TaxCodeDeterminationsService_GetTaxCodeDeterminationList`

## TaxCodeDeterminationsTCDService

1. **Purpose:** Retrieve the list of tax code determinations for the TCD (tax-code-determination) engine. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST TaxCodeDeterminationsTCDService_GetTaxCodeDeterminationTCDList`

## TaxWebSitesService

1. **Purpose:** Retrieve the list of tax web sites and the default tax web site. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST TaxWebSitesService_GetTaxWebSiteList`
   - `POST TaxWebSitesService_GetDefaultWebSite`

## WTaxTypeCodeService

1. **Purpose:** Retrieve the list of withholding-tax (WTax) type codes. (inferred)
2. **Type:** function/action Service
3. **Operations:**
   - `POST WTaxTypeCodeService_GetWTaxTypeCodeList`

---

## AccountCategory

1. **Purpose:** Manage account categories used to classify/group G/L accounts. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET AccountCategory(id)`
   - `GET AccountCategory`
   - `POST AccountCategory`
   - `PATCH AccountCategory(id)`
   - `DELETE AccountCategory(id)`
4. **Fields (real, from HTML):** `CategoryCode`, `CategoryName`, `CategorySource`
   - `GET /b1s/v1/AccountCategory?$select=CategoryCode,CategoryName,CategorySource&$filter=CategoryCode ge 123&$top=10`
   - `sapb1 query AccountCategory --select CategoryCode,CategoryName,CategorySource --filter "CategoryCode ge 123" --top 10`

## AccountSegmentationCategories

1. **Purpose:** Manage segmentation categories used in segmented chart-of-accounts numbering. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET AccountSegmentationCategories(id)`
   - `GET AccountSegmentationCategories`
   - `POST AccountSegmentationCategories`
   - `PATCH AccountSegmentationCategories(id)`
   - `DELETE AccountSegmentationCategories(id)`
4. **Fields (real, from HTML):** `SegmentID`, `Code`, `Name`
   - `GET /b1s/v1/AccountSegmentationCategories?$select=SegmentID,Code,Name&$filter=SegmentID ge 123&$top=10`
   - `sapb1 query AccountSegmentationCategories --select SegmentID,Code,Name --filter "SegmentID ge 123" --top 10`

## AccountSegmentations

1. **Purpose:** Manage the individual account segments (segment numerator, name, size) of the segmented account structure. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET AccountSegmentations(id)`
   - `GET AccountSegmentations`
   - `POST AccountSegmentations`
   - `PATCH AccountSegmentations(id)`
   - `DELETE AccountSegmentations(id)`
4. **Fields (real, from HTML):** `Numerator`, `Name`, `Size`
   - `GET /b1s/v1/AccountSegmentations?$select=Numerator,Name,Size&$filter=Numerator ge 123&$top=10`
   - `sapb1 query AccountSegmentations --select Numerator,Name,Size --filter "Numerator ge 123" --top 10`

## BEMReplicationPeriods

1. **Purpose:** Manage BEM replication periods (scope, schedule and status of budget/enablement data replication). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET BEMReplicationPeriods(id)`
   - `GET BEMReplicationPeriods`
   - `POST BEMReplicationPeriods`
   - `PATCH BEMReplicationPeriods(id)`
4. **Fields (real, from HTML):** `ScopeKey`, `ScopeName`, `Periodic`, `StartDate`, `Status`, `UpdateDate`
   - `GET /b1s/v1/BEMReplicationPeriods?$select=ScopeName,StartDate,Status&$filter=startswith(ScopeName,'a')&$top=10`
   - `sapb1 query BEMReplicationPeriods --select ScopeName,StartDate,Status --filter "startswith(ScopeName,'a')" --top 10`

## BPFiscalRegistryID

1. **Purpose:** Manage business-partner fiscal registry IDs (e.g. CNAE activity codes) used for tax reporting. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET BPFiscalRegistryID(id)`
   - `GET BPFiscalRegistryID`
   - `POST BPFiscalRegistryID`
   - `PATCH BPFiscalRegistryID(id)`
   - `DELETE BPFiscalRegistryID(id)`
4. **Fields (real, from HTML):** `Numerator`, `CNAECode`, `Description`
   - `GET /b1s/v1/BPFiscalRegistryID?$select=Numerator,CNAECode,Description&$filter=Numerator ge 123&$top=10`
   - `sapb1 query BPFiscalRegistryID --select Numerator,CNAECode,Description --filter "Numerator ge 123" --top 10`

## BudgetDistributions

1. **Purpose:** Manage budget distribution methods that spread an annual budget across the individual months. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET BudgetDistributions(id)`
   - `GET BudgetDistributions`
   - `POST BudgetDistributions`
   - `PATCH BudgetDistributions(id)`
   - `DELETE BudgetDistributions(id)`
4. **Fields (real, from HTML):** `September`, `August`, `July` (per-month distribution percentages; `DivisionCode` is the key)
   - `GET /b1s/v1/BudgetDistributions?$select=September,August,July&$filter=DivisionCode ge 123&$top=10`
   - `sapb1 query BudgetDistributions --select September,August,July --filter "DivisionCode ge 123" --top 10`

## Budgets

1. **Purpose:** Manage budgets defined on G/L accounts (stated in HTML: "manipulate 'Budgets' based on G/L accounts").
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Budgets(id)`
   - `GET Budgets`
   - `POST Budgets`
   - `PATCH Budgets(id)`
   - `DELETE Budgets(id)`
4. **Fields (real, from HTML):** `FutureAnnualExpensesCreditSys`, `FutureAnnualExpensesCreditLoc`, `FutureAnnualExpensesDebitSys` (`Numerator` is the key)
   - `GET /b1s/v1/Budgets?$select=FutureAnnualExpensesCreditSys,FutureAnnualExpensesCreditLoc,FutureAnnualExpensesDebitSys&$filter=Numerator ge 123&$top=10`
   - `sapb1 query Budgets --select FutureAnnualExpensesCreditSys,FutureAnnualExpensesCreditLoc,FutureAnnualExpensesDebitSys --filter "Numerator ge 123" --top 10`

## BudgetScenarios

1. **Purpose:** Manage budget scenarios (named budget versions with a ratio and fiscal-year start). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET BudgetScenarios(id)`
   - `GET BudgetScenarios`
   - `POST BudgetScenarios`
   - `PATCH BudgetScenarios(id)`
   - `DELETE BudgetScenarios(id)`
4. **Fields (real, from HTML):** `Name`, `InitialRatioPercentage`, `StartofFiscalYear` (`Numerator` is the key)
   - `GET /b1s/v1/BudgetScenarios?$select=Name,InitialRatioPercentage,StartofFiscalYear&$filter=Numerator ge 123&$top=10`
   - `sapb1 query BudgetScenarios --select Name,InitialRatioPercentage,StartofFiscalYear --filter "Numerator ge 123" --top 10`

## ChartOfAccounts

1. **Purpose:** Manage G/L accounts in the chart of accounts (code, name, running balance). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET ChartOfAccounts(id)`
   - `GET ChartOfAccounts`
   - `POST ChartOfAccounts`
   - `PATCH ChartOfAccounts(id)`
   - `DELETE ChartOfAccounts(id)`
4. **Fields (real, from HTML):** `Code`, `Name`, `Balance`
   - `GET /b1s/v1/ChartOfAccounts?$select=Code,Name,Balance&$filter=startswith(Code,'a')&$top=10`
   - `sapb1 query ChartOfAccounts --select Code,Name,Balance --filter "startswith(Code,'a')" --top 10`

## CostCenterTypes

1. **Purpose:** Manage cost center types (groupings of profit/cost centers). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET CostCenterTypes(id)`
   - `GET CostCenterTypes`
   - `POST CostCenterTypes`
   - `PATCH CostCenterTypes(id)`
   - `DELETE CostCenterTypes(id)`
4. **Fields (real, from HTML):** `CostCenterTypeCode`, `CostCenterTypeName`
   - `GET /b1s/v1/CostCenterTypes?$select=CostCenterTypeCode,CostCenterTypeName&$filter=startswith(CostCenterTypeCode,'test')&$top=10`
   - `sapb1 query CostCenterTypes --select CostCenterTypeCode,CostCenterTypeName --filter "startswith(CostCenterTypeCode,'test')" --top 10`

## CostElements

1. **Purpose:** Manage cost elements used in cost accounting. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET CostElements(id)`
   - `GET CostElements`
   - `POST CostElements`
   - `PATCH CostElements(id)`
   - `DELETE CostElements(id)`
4. **Fields (real, from HTML):** `Code`, `Description`, `IsActive`
   - `GET /b1s/v1/CostElements?$select=Code,Description,IsActive&$filter=startswith(Code,'a')&$top=10`
   - `sapb1 query CostElements --select Code,Description,IsActive --filter "startswith(Code,'a')" --top 10`

## Currencies

1. **Purpose:** Manage the currency master (code, name, document code). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Currencies(id)`
   - `GET Currencies`
   - `POST Currencies`
   - `PATCH Currencies(id)`
   - `DELETE Currencies(id)`
4. **Fields (real, from HTML):** `Code`, `Name`, `DocumentsCode`
   - `GET /b1s/v1/Currencies?$select=Code,Name,DocumentsCode&$filter=startswith(Code,'a')&$top=10`
   - `sapb1 query Currencies --select Code,Name,DocumentsCode --filter "startswith(Code,'a')" --top 10`

## DeductibleTaxes

1. **Purpose:** Manage deductible tax definitions. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET DeductibleTaxes(id)`
   - `GET DeductibleTaxes`
   - `POST DeductibleTaxes`
   - `PATCH DeductibleTaxes(id)`
   - `DELETE DeductibleTaxes(id)`
4. **Fields (real, from HTML):** `Code`, `Name`, `Inactive`
   - `GET /b1s/v1/DeductibleTaxes?$select=Code,Name,Inactive&$filter=startswith(Code,'a')&$top=10`
   - `sapb1 query DeductibleTaxes --select Code,Name,Inactive --filter "startswith(Code,'a')" --top 10`

## DeductionTaxGroups

1. **Purpose:** Manage deduction tax groups. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET DeductionTaxGroups(id)`
   - `GET DeductionTaxGroups`
   - `POST DeductionTaxGroups`
   - `PATCH DeductionTaxGroups(id)`
   - `DELETE DeductionTaxGroups(id)`
4. **Fields (real, from HTML):** `GroupKey`, `GroupCode`, `GroupName`
   - `GET /b1s/v1/DeductionTaxGroups?$select=GroupKey,GroupCode,GroupName&$filter=GroupKey ge 123&$top=10`
   - `sapb1 query DeductionTaxGroups --select GroupKey,GroupCode,GroupName --filter "GroupKey ge 123" --top 10`

## DeductionTaxHierarchies

1. **Purpose:** Manage deduction tax hierarchies linking business partners to hierarchy codes. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET DeductionTaxHierarchies(id)`
   - `GET DeductionTaxHierarchies`
   - `POST DeductionTaxHierarchies`
   - `PATCH DeductionTaxHierarchies(id)`
   - `DELETE DeductionTaxHierarchies(id)`
4. **Fields (real, from HTML):** `AbsEntry`, `BPCode`, `HierarchyCode`
   - `GET /b1s/v1/DeductionTaxHierarchies?$select=AbsEntry,BPCode,HierarchyCode&$filter=AbsEntry ge 123&$top=10`
   - `sapb1 query DeductionTaxHierarchies --select AbsEntry,BPCode,HierarchyCode --filter "AbsEntry ge 123" --top 10`

## DeductionTaxSubGroups

1. **Purpose:** Manage deduction tax sub-groups (child groups under deduction tax groups). (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET DeductionTaxSubGroups(id)`
   - `GET DeductionTaxSubGroups`
   - `POST DeductionTaxSubGroups`
   - `PATCH DeductionTaxSubGroups(id)`
4. **Fields (real, from HTML):** `GroupCode`, `GroupName`
   - `GET /b1s/v1/DeductionTaxSubGroups?$select=GroupCode,GroupName&$filter=startswith(GroupCode,'99')&$top=10`
   - `sapb1 query DeductionTaxSubGroups --select GroupCode,GroupName --filter "startswith(GroupCode,'99')" --top 10`

## Dimensions

1. **Purpose:** Manage accounting dimensions used for cost-accounting distribution. (inferred)
2. **Type:** readable ENTITY
3. **Operations:**
   - `GET Dimensions(id)`
   - `GET Dimensions`
   - `PATCH Dimensions(id)`
4. **Fields (real, from HTML):** `DimensionCode`, `DimensionName`, `IsActive`
   - `GET /b1s/v1/Dimensions?$select=DimensionCode,DimensionName,IsActive&$filter=DimensionCode ge 123&$top=10`
   - `sapb1 query Dimensions --select DimensionCode,DimensionName,IsActive --filter "DimensionCode ge 123" --top 10`
