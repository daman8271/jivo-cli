# Live Data Census — what actually holds data at JIVO

Which of the 498 catalogued services contain real rows. Source: the `rows_oil` frontmatter cached in every service note (counted against `JIVO_OIL_HANADB`, the default company), plus a fresh three-company comparison run on 2026-07-23 via the read-only CLI. **140 of 307 readable entities have `rows_oil > 0`.** Navigation: [[00-SAP-B1-Atlas]] · [[01-Data-Model]] · [[02-Query-Cookbook]].

## Big-8 live comparison across the three company DBs

Run live on 2026-07-23 (`./sapb1 query <Entity> --count --company <DB>`; all 24 calls succeeded — no errors):

| Entity | JIVO_OIL_HANADB | JIVO_MART_HANADB | JIVO_BEVERAGES_HANADB |
|---|---:|---:|---:|
| [[Orders]] | 14,583 | 7,321 | 5,168 |
| [[Invoices]] | 30,311 | 24,831 | 5,164 |
| [[Items]] | 2,264 | 1,341 | 2,188 |
| [[BusinessPartners]] | 3,384 | 2,182 | 2,924 |
| [[PurchaseOrders]] | 4,168 | 2,096 | 1,107 |
| [[DeliveryNotes]] | 2,821 | 6,036 | 303 |
| [[IncomingPayments]] | 13,759 | 11,017 | 3,795 |
| [[Quotations]] | 1,690 | 0 | 731 |

Observations: Oil is the biggest book on orders/invoices/purchasing; **Mart out-delivers Oil on [[DeliveryNotes]]** (6,036 vs 2,821) and writes zero [[Quotations]]; Beverages runs a much smaller document volume but nearly matches Oil's item-master size. Live counts drift slightly from the cached `rows_oil` below (e.g. [[Invoices]] was 30,306 at capture, 30,311 live today) — the business is posting documents while we read.

## All entities with data in JIVO_OIL_HANADB (rows_oil > 0, sorted desc)

| # | Entity | Rows (oil) | Domain |
|---:|---|---:|---|
| 1 | [[FormPreferences]] | 461,588 | [[administration-setup-3]] |
| 2 | [[Messages]] | 149,242 | [[system-other-1]] |
| 3 | [[JournalEntries]] | 131,295 | [[financials-accounting-2]] |
| 4 | [[StockTakings]] | 126,820 | [[inventory-warehouse-2]] |
| 5 | [[Attachments2]] | 75,526 | [[administration-setup-3]] |
| 6 | [[ApprovalRequests]] | 57,184 | [[administration-setup-3]] |
| 7 | [[StockTransferDrafts]] | 47,115 | [[inventory-warehouse-2]] |
| 8 | [[Drafts]] | 47,115 | [[sales-ar]] |
| 9 | [[Invoices]] | 30,306 | [[sales-ar]] |
| 10 | [[ResourceCapacities]] | 19,003 | [[production-mrp]] |
| 11 | [[BatchNumberDetails]] | 17,257 | [[inventory-warehouse-1]] |
| 12 | [[PurchaseInvoices]] | 15,858 | [[purchasing]] |
| 13 | [[Orders]] | 14,583 | [[sales-ar]] |
| 14 | [[VendorPayments]] | 14,197 | [[banking-payments]] |
| 15 | [[IncomingPayments]] | 13,759 | [[banking-payments]] |
| 16 | [[StockTransfers]] | 11,668 | [[inventory-warehouse-2]] |
| 17 | [[PurchaseDeliveryNotes]] | 11,183 | [[purchasing]] |
| 18 | [[InventoryGenEntries]] | 7,892 | [[inventory-warehouse-1]] |
| 19 | [[InventoryGenExits]] | 7,765 | [[inventory-warehouse-1]] |
| 20 | [[ProductionOrders]] | 7,683 | [[production-mrp]] |
| 21 | [[CreditNotes]] | 6,351 | [[sales-ar]] |
| 22 | [[UserFieldsMD]] | 5,572 | [[administration-setup-3]] |
| 23 | [[PurchaseOrders]] | 4,168 | [[purchasing]] |
| 24 | [[PickLists]] | 3,598 | [[inventory-warehouse-1]] |
| 25 | [[BusinessPartners]] | 3,384 | [[business-partners-crm]] |
| 26 | [[DeliveryNotes]] | 2,821 | [[sales-ar]] |
| 27 | [[Items]] | 2,264 | [[inventory-warehouse-1]] |
| 28 | [[Returns]] | 1,976 | [[sales-ar]] |
| 29 | [[Quotations]] | 1,690 | [[sales-ar]] |
| 30 | [[PurchaseCreditNotes]] | 1,517 | [[purchasing]] |
| 31 | [[PaymentDrafts]] | 1,491 | [[banking-payments]] |
| 32 | [[ChartOfAccounts]] | 1,423 | [[financials-accounting-1]] |
| 33 | [[InventoryTransferRequests]] | 1,282 | [[inventory-warehouse-1]] |
| 34 | [[ProductTrees]] | 620 | [[system-other-2]] |
| 35 | [[UserQueries]] | 568 | [[administration-setup-3]] |
| 36 | [[LandedCosts]] | 522 | [[purchasing]] |
| 37 | [[IndiaHsn]] | 517 | [[system-other-1]] |
| 38 | [[ReportTypes]] | 453 | [[administration-setup-3]] |
| 39 | [[WebClientVariants]] | 320 | [[system-other-2]] |
| 40 | [[GLAccountAdvancedRules]] | 318 | [[financials-accounting-2]] |
| 41 | [[BudgetScenarios]] | 267 | [[financials-accounting-1]] |
| 42 | [[Countries]] | 243 | [[system-other-1]] |
| 43 | [[ProfitCenters]] | 198 | [[financials-accounting-2]] |
| 44 | [[DistributionRules]] | 194 | [[financials-accounting-2]] |
| 45 | [[Budgets]] | 164 | [[financials-accounting-1]] |
| 46 | [[SalesPersons]] | 155 | [[sales-ar]] |
| 47 | [[PurchaseReturns]] | 107 | [[purchasing]] |
| 48 | [[MaterialRevaluation]] | 100 | [[system-other-1]] |
| 49 | [[States]] | 98 | [[system-other-2]] |
| 50 | [[WebClientRecentActivities]] | 97 | [[business-partners-crm]] |
| 51 | [[ApprovalTemplates]] | 93 | [[administration-setup-3]] |
| 52 | [[MultiLanguageTranslations]] | 65 | [[administration-setup-3]] |
| 53 | [[Banks]] | 65 | [[banking-payments]] |
| 54 | [[ResourceProperties]] | 64 | [[production-mrp]] |
| 55 | [[ItemProperties]] | 64 | [[inventory-warehouse-1]] |
| 56 | [[BusinessPartnerProperties]] | 64 | [[business-partners-crm]] |
| 57 | [[UserTablesMD]] | 59 | [[administration-setup-4]] |
| 58 | [[Warehouses]] | 58 | [[inventory-warehouse-2]] |
| 59 | [[Users]] | 55 | [[administration-setup-4]] |
| 60 | [[CycleCountDeterminations]] | 55 | [[system-other-1]] |
| 61 | [[AccountCategory]] | 54 | [[financials-accounting-1]] |
| 62 | [[BusinessPartnerGroups]] | 47 | [[business-partners-crm]] |
| 63 | [[SalesTaxAuthorities]] | 40 | [[sales-ar]] |
| 64 | [[FormattedSearches]] | 38 | [[administration-setup-3]] |
| 65 | [[QueryCategories]] | 37 | [[administration-setup-3]] |
| 66 | [[ReturnRequest]] | 32 | [[sales-ar]] |
| 67 | [[CashFlowLineItems]] | 31 | [[inventory-warehouse-1]] |
| 68 | [[IntrastatConfiguration]] | 30 | [[administration-setup-3]] |
| 69 | [[PaymentTermsTypes]] | 29 | [[banking-payments]] |
| 70 | [[UserPermissionTree]] | 28 | [[administration-setup-3]] |
| 71 | [[UserLanguages]] | 28 | [[administration-setup-3]] |
| 72 | [[UserObjectsMD]] | 27 | [[administration-setup-3]] |
| 73 | [[Sections]] | 26 | [[system-other-2]] |
| 74 | [[ChooseFromList]] | 26 | [[administration-setup-3]] |
| 75 | [[ApprovalStages]] | 26 | [[administration-setup-3]] |
| 76 | [[LandedCostsCodes]] | 24 | [[purchasing]] |
| 77 | [[SalesTaxCodes]] | 23 | [[sales-ar]] |
| 78 | [[SalesForecast]] | 23 | [[sales-ar]] |
| 79 | [[QueryAuthGroups]] | 23 | [[administration-setup-3]] |
| 80 | [[WithholdingTaxCodes]] | 22 | [[financials-accounting-2]] |
| 81 | [[SpecialPrices]] | 22 | [[inventory-warehouse-2]] |
| 82 | [[SalesTaxAuthoritiesTypes]] | 18 | [[sales-ar]] |
| 83 | [[EmployeesInfo]] | 17 | [[hr-resources]] |
| 84 | [[Cockpits]] | 15 | [[system-other-1]] |
| 85 | [[DeterminationCriterias]] | 14 | [[system-other-1]] |
| 86 | [[BinLocationFields]] | 14 | [[inventory-warehouse-1]] |
| 87 | [[AlertManagements]] | 13 | [[system-other-1]] |
| 88 | [[Holidays]] | 11 | [[system-other-1]] |
| 89 | [[ElectronicFileFormats]] | 11 | [[administration-setup-3]] |
| 90 | [[AdditionalExpenses]] | 11 | [[system-other-1]] |
| 91 | [[WebClientBookmarkTiles]] | 10 | [[system-other-2]] |
| 92 | [[PriceLists]] | 10 | [[inventory-warehouse-2]] |
| 93 | [[ItemGroups]] | 10 | [[inventory-warehouse-1]] |
| 94 | [[NFTaxCategories]] | 9 | [[financials-accounting-2]] |
| 95 | [[DynamicSystemStrings]] | 8 | [[system-other-1]] |
| 96 | [[BusinessPlaces]] | 8 | [[system-other-1]] |
| 97 | [[Resources]] | 7 | [[production-mrp]] |
| 98 | [[Departments]] | 7 | [[system-other-1]] |
| 99 | [[LengthMeasures]] | 6 | [[system-other-1]] |
| 100 | [[KPIs]] | 6 | [[system-other-1]] |
| 101 | [[Currencies]] | 6 | [[financials-accounting-1]] |
| 102 | [[WeightMeasures]] | 5 | [[system-other-2]] |
| 103 | [[WarehouseLocations]] | 5 | [[inventory-warehouse-2]] |
| 104 | [[HouseBankAccounts]] | 5 | [[banking-payments]] |
| 105 | [[Dimensions]] | 5 | [[financials-accounting-1]] |
| 106 | [[UnitOfMeasurements]] | 4 | [[inventory-warehouse-2]] |
| 107 | [[UnitOfMeasurementGroups]] | 4 | [[inventory-warehouse-2]] |
| 108 | [[TaxCodeDeterminationsTCD]] | 4 | [[financials-accounting-2]] |
| 109 | [[FAAccountDeterminations]] | 4 | [[financials-accounting-2]] |
| 110 | [[DepreciationTypes]] | 4 | [[fixed-assets]] |
| 111 | [[WebClientVariantGroups]] | 3 | [[administration-setup-4]] |
| 112 | [[ServiceCallStatus]] | 3 | [[service-contracts]] |
| 113 | [[ServiceCallSolutionStatus]] | 3 | [[service-contracts]] |
| 114 | [[ServiceCallOrigins]] | 3 | [[service-contracts]] |
| 115 | [[NatureOfAssessees]] | 3 | [[system-other-1]] |
| 116 | [[IntegrationPackagesConfigure]] | 3 | [[inventory-warehouse-1]] |
| 117 | [[FinancialYears]] | 3 | [[financials-accounting-2]] |
| 118 | [[EmployeeRolesSetup]] | 3 | [[hr-resources]] |
| 119 | [[DepreciationAreas]] | 3 | [[fixed-assets]] |
| 120 | [[AssetClasses]] | 3 | [[fixed-assets]] |
| 121 | [[WebClientLaunchpads]] | 2 | [[system-other-2]] |
| 122 | [[CampaignResponseType]] | 2 | [[business-partners-crm]] |
| 123 | [[BEMReplicationPeriods]] | 2 | [[financials-accounting-1]] |
| 124 | [[ActivityStatuses]] | 2 | [[business-partners-crm]] |
| 125 | [[Territories]] | 1 | [[business-partners-crm]] |
| 126 | [[ResourceGroups]] | 1 | [[production-mrp]] |
| 127 | [[ProjectManagementTimeSheet]] | 1 | [[projects]] |
| 128 | [[Manufacturers]] | 1 | [[system-other-1]] |
| 129 | [[Industries]] | 1 | [[business-partners-crm]] |
| 130 | [[EmployeePosition]] | 1 | [[hr-resources]] |
| 131 | [[DepreciationTypePools]] | 1 | [[fixed-assets]] |
| 132 | [[CustomsGroups]] | 1 | [[administration-setup-3]] |
| 133 | [[CreditCards]] | 1 | [[banking-payments]] |
| 134 | [[CommissionGroups]] | 1 | [[business-partners-crm]] |
| 135 | [[ClosingDateProcedure]] | 1 | [[system-other-1]] |
| 136 | [[BudgetDistributions]] | 1 | [[financials-accounting-1]] |
| 137 | [[Branches]] | 1 | [[administration-setup-3]] |
| 138 | [[AttributeGroups]] | 1 | [[administration-setup-3]] |
| 139 | [[ActivityTypes]] | 1 | [[business-partners-crm]] |
| 140 | [[ActivityLocations]] | 1 | [[business-partners-crm]] |

## Reading the census

- The three biggest tables — [[FormPreferences]] (462k, per-user UI state), [[Messages]] (149k, internal alerts) and [[StockTakings]] (127k, count sheets) — are system noise, not business documents. The business core starts at [[JournalEntries]] (131k) and the document chain of [[01-Data-Model]].
- Anything NOT in this table read back 0 rows (or is a write-side RPC service) in the oil DB — the endpoint works, the module is just unused there. Mart and Beverages were only censused for the big 8; other entities may hold data in those DBs.
- Re-run any count live: `./sapb1 query <Entity> --count [--company <DB>]` — read-only, cheap, server-side.
