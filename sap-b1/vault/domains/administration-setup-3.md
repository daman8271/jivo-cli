# Administration & Setup (part 3)

Company-wide configuration, part 3 of 4 (see [[administration-setup-1]], [[administration-setup-2]], [[administration-setup-4]]) — the readable setup entities: approvals ([[ApprovalRequests]] — 57k live rows! — plus stages/templates), [[Branches]], the customization layer ([[UserFieldsMD]] 5.6k UDFs, [[UserObjectsMD]], [[UserKeysMD]], [[UserTablesMD]] in part 4, [[FormattedSearches]] 38, [[UserQueries]] 568), document attachments ([[Attachments2]] — 75.5k), per-user UI state ([[FormPreferences]] — 461.6k rows, the biggest table in the DB), query auth groups/categories, [[ShippingTypes]], translations and misc localization code tables.

Part of the [[00-SAP-B1-Atlas]] — 40 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[FormPreferences]] **(461,588 rows)** — Per-user UI form settings (column visibility, width, order per form) saved by the B1 client — hence the huge 461k row count.
- [[Attachments2]] **(75,526 rows)** — File-attachment registry linking uploaded files (paths, names, dates in the lines collection) to SAP documents and master records; heavily used here (75k rows).
- [[ApprovalRequests]] **(57,184 rows)** — Tracks live document-approval workflow requests — which draft/document is awaiting whose sign-off, at which stage, and its decision status.
- [[UserFieldsMD]] **(5,572 rows)** — Metadata of all user-defined fields (UDFs) added to system and user tables — 5,572 custom fields, a major map of this installation's customizations.
- [[UserQueries]] **(568 rows)** — The 568 saved SQL user queries in the Query Manager — a rich trove of this company's reporting logic and table usage.
- [[ReportTypes]] **(453 rows)** — Catalog of every document/report type in the system with its default print layout mapping (453 types).
- [[ApprovalTemplates]] **(93 rows)** — Templates that wire together documents, originating users, stages, and trigger conditions to define when and how approval workflows fire.
- [[MultiLanguageTranslations]] **(65 rows)** — Stores per-field translated values of master-data records (table + field + key → translations per language) for multi-language printing.
- [[FormattedSearches]] **(38 rows)** — Formatted Search (FMS) definitions that attach user queries or valid-value lists to specific form fields to auto-populate or validate them in the B1 client.
- [[QueryCategories]] **(37 rows)** — Categories used to organize saved user queries and gate access to them via permission groups.
- [[IntrastatConfiguration]] **(30 rows)** — EU Intrastat statistical-reporting configuration (transaction nature codes, statistical codes, supplementary units per country and date range).
- [[UserLanguages]] **(28 rows)** — Language master (28 languages) used for user UI language and multi-language descriptions/translations.
- [[UserPermissionTree]] **(28 rows)** — Custom (addon/UDO) permission-tree nodes that plug extension authorizations into B1's General Authorizations screen.
- [[UserObjectsMD]] **(27 rows)** — Metadata of 27 user-defined objects (UDOs) — custom business objects built on user tables with their own forms, menus, and services.
- [[ApprovalStages]] **(26 rows)** — Defines the stages of approval workflows — who the approvers are and how many approvals each stage requires.
- [[ChooseFromList]] **(26 rows)** — UI configuration for the B1 client's Choose-From-List dialogs — which columns show per object lookup.
- [[QueryAuthGroups]] **(23 rows)** — Authorization groups that control which users may run which saved user-query categories.
- [[ElectronicFileFormats]] **(11 rows)** — Registry of electronic file format definitions (EFM/bank-file and legal-reporting export formats) and where their output files land.
- [[AttributeGroups]] **(1 row)** — Groups of resource/production attributes used to characterize resources in production planning.
- [[Branches]] **(1 row)** — Legacy company branch definitions for segmenting employees/transactions by branch (single-branch setup here; India localizations use BusinessPlaces instead).
- [[CustomsGroups]] **(1 row)** — Customs duty groups defining import duty rates and the G/L allocation/expense accounts for landed-cost customs on imported items.
- [[AccrualTypes]] — Defines accrual type codes used to classify expense/revenue accruals in period-end accounting; empty in JIVO_OIL_HANADB.
- [[CertificateSeries]] — Numbering series for withholding-tax certificates (e.g. TDS certificates in India localization); unused here.
- [[CESTCodes]] — Brazil localization CEST tax substitution codes assigned to items; not used in this Indian database.
- [[DNFCodeSetup]] — Brazil localization DNF (fiscal declaration) code setup for items; unused in this Indian database.
- [[EmailGroups]] — Email distribution groups for bulk mailing documents/campaigns to business partner contacts; unused here.
- [[EnhancedDiscountGroups]] — Advanced discount-group rules granting BP-specific percentage discounts by item, item group, or property; unused here.
- [[ExtendedTranslations]] — Extended multi-language translations of master-data field values for foreign-language documents; unused here.
- [[GovPayCodes]] — Government payment codes used in localization payment/reporting files (e.g. tax authority payment identifiers); unused here.
- [[MaterialGroups]] — Brazil localization material groups for item fiscal classification; unused in this Indian database.
- [[NCMCodesSetup]] — Brazil-localization NCM (Mercosur commodity nomenclature) tax classification codes for items; unused/empty in this Indian DB.
- [[Queue]] — Service-module queues for routing incoming service calls to technician teams; empty here.
- [[ReportFilter]] — Saved filter definitions applied to report layouts/printing; empty here.
- [[RetornoCodes]] — Brazil-localization bank-return (retorno) file codes for payment processing; unused in this DB.
- [[ServiceGroups]] — Service group codes (localization-specific, e.g. Brazil service tax groups) for classifying service items; empty here.
- [[ShippingTypes]] — Shipping/transport method master (courier, road, etc.) referenced by marketing documents; surprisingly empty in this DB.
- [[TargetGroups]] — CRM marketing-campaign target group definitions for segmenting business partners; unused here.
- [[TransactionCodes]] — Journal-entry transaction code master for tagging/classifying G/L postings; unused here.
- [[UserDefaultGroups]] — Reusable default-value profiles (default warehouse, BP, printing settings) assignable to users; none defined here.
- [[UserKeysMD]] — Metadata of user-defined unique key indexes on user tables; none defined here.
