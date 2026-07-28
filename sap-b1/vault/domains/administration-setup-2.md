# Administration & Setup (part 2)

Company-wide configuration, part 2 of 4 (see [[administration-setup-1]], [[administration-setup-3]], [[administration-setup-4]]) — the remaining RPC services: user management ([[UsersService]], [[UserMenuService]]), document numbering ([[SeriesService]]), recurring transactions, report layouts/filters, QR codes, SBObob helper queries ([[SBOBobService]]), predefined texts, and the whole Web Client personalization family (dashboards, launchpads, tiles, variants, notifications, form settings). Workflow tasks and mobile-app config close it out.

Part of the [[00-SAP-B1-Atlas]] — 40 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[MaterialRevaluationSNBService]] — Lists material revaluation data for serial- and batch-managed items so inventory value adjustments can be reviewed per serial/batch.
- [[MessagesService]] — Reads the internal B1 messaging system (inbox, outbox, sent) used for user-to-user and alert messages inside SAP Business One.
- [[MobileAppService]] — Backend for the SAP B1 Sales and Service mobile apps: server time, technician schedules/settings, and mobile report configuration.
- [[NatureOfAssesseesService]] — Lists India-localization 'nature of assessee' classifications used for TDS/withholding-tax treatment of business partners.
- [[NCMCodesSetupService]] — Lists Brazil-localization NCM (Mercosur nomenclature) commodity codes assigned to items for fiscal classification.
- [[NFModelsService]] — Lists Brazil-localization Nota Fiscal document models used to classify fiscal documents.
- [[PredefinedTextsService]] — Lists reusable predefined text snippets that users insert into document remarks and long-text fields.
- [[QRCodeService]] — Generates or updates QR codes attached to documents (e.g., e-invoice/payment QR codes required by localizations such as India GST).
- [[QueryService]] — Executes ad-hoc cross-entity queries (Service Layer query API) via POST, returning arbitrary result sets.
- [[RecurringTransactionService]] — Manages and executes recurring transaction instances generated from recurring document/posting templates.
- [[ReportFilterService]] — Returns saved filter definitions for tax reports used in statutory tax reporting.
- [[ReportLayoutsService]] — Manages print/report layouts (Crystal/PLD) per report type, including defaults and printer settings for document printing.
- [[ReportTypesService]] — Lists the system report types (e.g., AR Invoice, Sales Order) to which print layouts can be assigned.
- [[RetornoCodesService]] — Lists Brazil-localization bank 'retorno' (return-file) codes used to interpret bank statement/payment return files.
- [[RouteStagesService]] — Lists production routing stages used to sequence operations in production orders.
- [[SBOBobService]] — Utility 'bridge of business objects' functions: system/local currency, exchange and index rates, due-date calculation, permissions, and money formatting.
- [[SectionsService]] — Lists India-localization TDS sections (Income Tax Act sections) used for withholding-tax classification.
- [[SelfCreditMemoService]] — Handles self-issued credit memo workflows: fetching approval templates, processing approval requests, and cancellation.
- [[SeriesService]] — Manages document numbering series (including electronic-document series): creation, per-user/global defaults, and attachment to document types.
- [[ServiceGroupsService]] — Lists service groups (e.g., India SAC service accounting code groupings) used to classify service-type items for taxation.
- [[ShortLinkMappingsService]] — Batch-deletes short-link mappings (shortened URLs generated for sharing documents/attachments).
- [[StatesService]] — Lists states/provinces per country used in business partner and document addresses (and GST state codes in India).
- [[TargetGroupsService]] — Returns the list of CRM campaign target groups defined in the system.
- [[TerminationReasonService]] — Returns the list of employee termination reasons used in HR master data.
- [[TrackingNotesService]] — Returns tracking notes (audit/tracking annotations) recorded against documents or service processes.
- [[TransactionCodesService]] — Returns the list of journal transaction codes used to classify journal entries in financials.
- [[TSRExceptionalEventService]] — Returns exceptional events (holidays/absence exceptions) for time sheet recording (TSR).
- [[UserMenuService]] — Reads and updates the personalized SAP B1 menu layout for the current or a specified user.
- [[UsersService]] — Returns the profile of the user currently logged in to the Service Layer session.
- [[ValueMappingService]] — Translates codes between SAP B1 values and third-party system values for integration scenarios.
- [[WebClientBookmarkTileService]] — Lists bookmark tiles saved by users on the SAP B1 Web Client home screen.
- [[WebClientDashboardService]] — Lists analytical dashboards configured in the SAP B1 Web Client.
- [[WebClientFormSettingService]] — Lists per-user form/field layout settings for SAP B1 Web Client screens.
- [[WebClientLaunchpadService]] — Lists launchpad (home page tile group) configurations in the SAP B1 Web Client.
- [[WebClientListviewFilterService]] — Lists saved list-view filters users have created in the SAP B1 Web Client.
- [[WebClientNotificationService]] — Lists in-app notifications delivered to users in the SAP B1 Web Client.
- [[WebClientPreferenceService]] — Lists per-user preference settings (locale, display options) for the SAP B1 Web Client.
- [[WebClientVariantGroupService]] — Lists variant groups that bundle saved view variants in the SAP B1 Web Client.
- [[WebClientVariantService]] — Lists saved view variants (personalized screen states) in the SAP B1 Web Client.
- [[WorkflowTaskService]] — Retrieves and completes workflow approval tasks assigned to users in document approval processes.
