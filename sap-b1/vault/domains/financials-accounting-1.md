# Financials & Accounting (part 1)

The G/L backbone, part 1 of 2 (see [[financials-accounting-2]]): [[ChartOfAccounts]] (1,423 accounts) organized by [[AccountCategory]] and segmentation, the cost-accounting layer ([[Dimensions]], [[ProfitCenters]], [[CostElements]], [[CostCenterTypes]], distribution rules), planning via [[Budgets]] / [[BudgetScenarios]] / [[BudgetDistributions]], multi-currency via [[Currencies]], and India-relevant tax masters (deduction/withholding TDS groups and hierarchies). Write-side RPC services for accounts, journal vouchers and tax determinations sit alongside.

Part of the [[00-SAP-B1-Atlas]] — 40 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[ChartOfAccounts]] **(1,423 rows)** — The company's G/L account master (chart of accounts) with hierarchy, types, currencies and live balances — the backbone of all journal postings.
- [[BudgetScenarios]] **(267 rows)** — Named budget scenarios (main/optimistic/pessimistic per fiscal year) that budget amounts are recorded against.
- [[Budgets]] **(164 rows)** — Per-account annual budget amounts and balances by scenario and fiscal year for budget-vs-actual control.
- [[AccountCategory]] **(54 rows)** — Categories used to group G/L accounts for financial-report templates (P&L / balance sheet drawers).
- [[Currencies]] **(6 rows)** — Currency master (INR plus 5 others) with rounding rules and payment tolerance settings used across all documents.
- [[Dimensions]] **(5 rows)** — The five cost-accounting dimensions that profit centers and distribution rules are organized under for multidimensional P&L analysis.
- [[BEMReplicationPeriods]] **(2 rows)** — Tracks Budget/Enterprise Management replication periods and their sync status to external planning systems.
- [[BudgetDistributions]] **(1 row)** — Budget distribution methods that spread an annual budget amount across the 12 months (equal, ascending, etc.).
- [[AccountCategoryService]] — Returns the list of G/L account categories (drawer/level groupings) used to classify accounts in the chart of accounts.
- [[AccountSegmentationCategories]] — Value lists for each account-segment position when segmented chart of accounts is used (empty here — segmentation not in use).
- [[AccountSegmentations]] — Defines the segment structure (name/size) of a segmented G/L account code (unused in this DB).
- [[BEMReplicationPeriodService]] — Lists Budget Extended Module (BEM) replication periods used to sync budget planning periods with posting periods.
- [[BPFiscalRegistryID]] — Stores localization-specific fiscal registry IDs (tax registration numbers) for business partners (empty in this DB).
- [[CostCenterTypes]] — Classification types for cost centers/profit centers in cost accounting (unused in this DB).
- [[CostElements]] — Cost accounting elements that map G/L expense accounts into cost-accounting analysis (unused here).
- [[DeductibleTaxes]] — Deductible-tax percentage definitions for partially deductible input tax (localization feature, unused here).
- [[DeductionTaxGroups]] — Withholding/deduction-at-source tax groups (Israel-style deduction localization, unused in this Indian DB).
- [[DeductionTaxHierarchies]] — Hierarchy levels linking deduction tax groups and subgroups for deduction-at-source reporting (unused).
- [[DeductionTaxSubGroups]] — Subgroup breakdown within deduction tax groups for deduction-at-source (unused).

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[AccountsService]] — Posts opening-balance journal transactions for G/L accounts during system initialization or period migration.
- [[CostCenterTypesService]] — Returns the catalog of cost center types used to classify cost centers in cost accounting.
- [[CostElementService]] — Lists cost elements that map G/L expense accounts into cost accounting for allocation to cost centers.
- [[DeductibleTaxService]] — Returns deductible-tax definitions specifying what portion of input tax is recoverable versus expensed.
- [[DeductionTaxSubGroupsService]] — Lists withholding/deduction tax sub-groups (e.g. Israel/India TDS sub-classifications) under deduction tax groups.
- [[DimensionsService]] — Returns the cost accounting dimensions (up to 5) along which profit centers and distribution rules are organized.
- [[DistributionRulesService]] — Lists distribution rules that allocate revenues and expenses across profit/cost centers by percentage.
- [[FAAccountDeterminationsService]] — Returns fixed-asset account determination sets mapping asset classes to G/L accounts for acquisition, depreciation and retirement postings.
- [[FinancialYearsService]] — Lists fiscal years defined for fixed-asset depreciation and financial reporting.
- [[FiscalPrinterService]] — Returns configured fiscal printer devices used for legally mandated receipt printing in certain localizations.
- [[GLAccountAdvancedRulesService]] — Lists advanced G/L account determination rules that override default inventory posting accounts by criteria like item group or warehouse.
- [[JournalEntryDocumentTypeService]] — Returns the document-type codes assignable to journal entries for classification and reporting.
- [[JournalVouchersService]] — Creates draft journal vouchers (unposted journal entry batches) awaiting review before posting to the general ledger.
- [[NFTaxCategoriesService]] — Lists Nota Fiscal tax categories used in the Brazil localization for electronic invoice tax classification.
- [[OccurrenceCodesService]] — Returns bank occurrence codes (Brazil localization) describing boleto/payment file events exchanged with banks.
- [[ProfitCentersService]] — Lists profit/cost centers used in cost accounting to track revenues and expenses by business unit.
- [[ServiceTaxPostingService]] — India-localization utility that finds taxable deliveries and posts the corresponding service tax liability to the ledger.
- [[TaxCodeDeterminationsService]] — Lists tax code determination rules that auto-select the tax code on documents based on BP, item, and location criteria.
- [[TaxCodeDeterminationsTCDService]] — Returns the newer condition-based (TCD) tax determination rules used by localizations like India GST to derive tax codes on marketing documents.
- [[TaxWebSitesService]] — Lists external tax web sites/services (e.g. US tax lookup providers) configured for automatic tax calculation, including the default provider.
- [[WTaxTypeCodeService]] — RPC helper that returns the list of withholding-tax type codes configured in the company.
