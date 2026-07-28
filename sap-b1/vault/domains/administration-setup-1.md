# Administration & Setup (part 1)

Company-wide configuration, part 1 of 4 (see [[administration-setup-2]], [[administration-setup-3]], [[administration-setup-4]]) — this part is all write-side RPC services: company settings ([[CompanyService]]), approvals workflow (requests/stages/templates), org structure ([[BranchesService]], [[DepartmentsService]]), master-data reconciliations (internal/external), credit lines, India HSN codes ([[IndiaHsnService]]), material revaluation, KPIs/cockpits, licensing and change-log access. The readable twins of most of these live in parts 3–4 and in [[system-other-1]].

Part of the [[00-SAP-B1-Atlas]] — 40 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities
- [[AccrualTypesService]] — Lists accrual types used for period-end expense/revenue accrual postings in financial accounting.
- [[AttributeGroupsService]] — Lists attribute groups used to classify resources/assets for grouping and reporting.
- [[CompanyService]] — Exposes company-wide configuration: company/admin settings, posting periods, feature toggles, and utility calls like item price lookup and decimal rounding.

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[ApprovalRequestsService]] — Retrieves pending and historical document approval requests routed through SAP B1 approval workflows.
- [[ApprovalStagesService]] — Lists the defined approval stages (who must approve, how many approvers) used in approval templates.
- [[ApprovalTemplatesService]] — Lists approval templates that define which documents and originators trigger approval workflows.
- [[BPOpeningBalanceService]] — Creates opening balance journal postings for business partners during system initialization (write-only; off-limits in this read-only setup).
- [[BranchesService]] — Lists company branches used in multi-branch accounting and document segregation.
- [[BrazilBeverageIndexersService]] — Lists Brazil-specific beverage tax indexer codes for fiscal compliance (irrelevant to an Indian localization DB).
- [[BrazilFuelIndexersService]] — Lists Brazil-specific fuel tax indexer codes for fiscal compliance (irrelevant to an Indian localization DB).
- [[CashDiscountsService]] — Lists cash discount definitions applied via payment terms for early-payment incentives.
- [[CertificateSeriesService]] — Lists certificate series used for numbering tax/withholding certificates in certain localizations.
- [[ChangeLogsService]] — Retrieves the audit change-log history and field-level differences for a given object instance.
- [[CockpitsService]] — Manages and lists user dashboard cockpits (personal and template) in the B1 client UI.
- [[CountiesService]] — Lists county master data used in addresses for certain localizations.
- [[CountriesService]] — Lists country master data used in business partner and company addresses.
- [[CreditLinesService]] — Retrieves bank credit line definitions and the currently valid credit lines available to the company.
- [[CycleCountDeterminationsService]] — Lists cycle-count determination rules that schedule periodic inventory counting per warehouse/item group.
- [[DepartmentsService]] — Lists company departments used to classify employees and users.
- [[DeterminationCriteriasService]] — Lists advanced G/L account determination criteria rules that drive automatic account assignment on postings.
- [[DNFCodeSetupService]] — Lists Brazil DNF (fiscal declaration) code setup entries for item tax reporting (Brazil localization only).
- [[ElectronicCommunicationActionService]] — Drives the electronic document communication workflow (e.g. e-invoicing exchanges), fetching actions and reporting their success or failure.
- [[ElectronicCommunicationActionsService]] — Manages electronic communication (ECM) actions and their logs for legally-mandated electronic document exchange with authorities or partners.
- [[ElectronicFileFormatsService]] — Lists the electronic file format definitions (e.g. bank/tax file layouts) configured for electronic document generation.
- [[EmailGroupsService]] — Lists email groups used to batch-send documents or campaigns to sets of business partner contacts.
- [[EmploymentCategoryService]] — Lists HR employment categories used to classify employees for payroll and reporting.
- [[EnhancedDiscountGroupsService]] — Lists enhanced discount group rules that grant percentage discounts to business partners by item, item group, or property.
- [[ExceptionalEventService]] — Lists exceptional calendar events (holidays/closures) that override normal business availability, e.g. for service scheduling.
- [[ExtendedTranslationsService]] — Lists multi-language translations of field values (item names, remarks etc.) for multilingual document printing.
- [[ExternalCallsService]] — Sends and tracks calls to external systems/services (e.g. tax authority or e-invoicing endpoints) from within SAP B1.
- [[ExternalReconciliationsService]] — Performs and manages external reconciliations matching G/L or BP transactions against bank/external statements.
- [[GovPayCodesService]] — Lists government payment codes used to classify payments to authorities in localized statutory reporting.
- [[GTIsService]] — Imports Golden Tax Interface (GTI) data — the China VAT invoice interface — into SAP B1.
- [[IndiaHsnService]] — Lists India HSN (Harmonized System of Nomenclature) codes used for GST classification of items — directly relevant to JIVO's Indian GST setup.
- [[InternalReconciliationsService]] — Manages internal reconciliation of open BP/G/L transactions (e.g. matching invoices to payments) including cancellation workflows.
- [[IntrastatConfigurationService]] — Lists Intrastat configuration settings for EU intra-community trade statistical reporting.
- [[KPIsService]] — Lists key performance indicator definitions used by SAP B1 analytics/cockpit dashboards.
- [[LicenseService]] — Returns the SAP B1 installation number for license administration.
- [[MaterialGroupsService]] — Lists material groups (localization-specific item classification, e.g. for Indian excise/GST) used to categorize items for tax purposes.
- [[MaterialRevaluationFIFOService]] — Retrieves FIFO-layer material revaluation data for adjusting inventory cost of FIFO-managed items.
