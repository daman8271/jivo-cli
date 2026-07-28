# System & Other (part 1)

Session control plus the catch-all entity set, part 1 of 2 (see [[system-other-2]]): [[Login]] / [[Logout]] manage the B1SESSION cookie (the CLI does this automatically; [[B1Sessions]] is the session registry), and [[Entities:]] is the catalog's section marker note. Notables with live JIVO data: [[Messages]] (149k internal alerts/messages — second-biggest table), [[IndiaHsn]] (517 GST HSN codes), [[Departments]] (7), [[BusinessPlaces]] (8 GST branch registrations), [[Manufacturers]], [[Holidays]], [[LengthMeasures]]/[[WeightMeasures]], and [[InternalReconciliations]]. Brazil indexer tables and other localization leftovers read but are empty here.

Part of the [[00-SAP-B1-Atlas]] — 40 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[Messages]] **(149,242 rows)** — Internal B1 messaging/alert inbox (system alerts and user messages with recipients and attachments). Live rows in JIVO_OIL_HANADB: 149,242 — a heavy alert stream (latest sampled messages are "Document generation approved" notices to internal user 35).
- [[IndiaHsn]] **(517 rows)** — India GST HSN code master (chapter/heading/sub-heading) assigned to items for tax classification. Live rows in JIVO_OIL_HANADB: 517 codes.
- [[Countries]] **(243 rows)** — Standard country master (243 rows) with ISO codes and bank/tax validation rules, referenced by all addresses and business partners.
- [[MaterialRevaluation]] **(100 rows)** — Inventory revaluation documents adjusting item cost/value with offsetting expense/income G/L postings. Live rows in JIVO_OIL_HANADB: 100 documents.
- [[CycleCountDeterminations]] **(55 rows)** — Per-warehouse setup (55 warehouses) of cycle-count scheduling rules that drive periodic inventory counting recommendations.
- [[Cockpits]] **(15 rows)** — Stores B1 cockpit (dashboard/workbench) definitions per user for the client UI — 15 cockpit layouts exist.
- [[DeterminationCriterias]] **(14 rows)** — Configures G/L account determination criteria (by warehouse, item group, etc.) that steer automatic journal-account selection.
- [[AlertManagements]] **(13 rows)** — Configures automatic internal alerts (query-based or predefined) with schedules and recipient lists for notifying users of business events.
- [[AdditionalExpenses]] **(11 rows)** — Defines freight/additional expense types (e.g. shipping, handling) that can be added to marketing documents, with their G/L account and tax mappings.
- [[Holidays]] **(11 rows)** — Company holiday calendars (holiday dates and weekend definitions) driving due-date and delivery-date calculations. Live rows in JIVO_OIL_HANADB: 11 — yearly calendars named "2004 Holidays" through "2016 Holidays" (nothing newer, so the active calendar is stale).
- [[BusinessPlaces]] **(8 rows)** — Master data for the company's branches/business places (8 for JIVO — likely GST-registered branches), each with its tax ID, address and default warehouse.
- [[DynamicSystemStrings]] **(8 rows)** — Stores customized UI field labels/strings per form and column so companies can rename screen captions. Live rows in JIVO_OIL_HANADB: 8 (e.g. form 139 "Order No.", form 133 "Document No").
- [[Departments]] **(7 rows)** — Simple lookup of company departments (7 at JIVO) assigned to employees and users for HR/organizational grouping.
- [[KPIs]] **(6 rows)** — Definitions of key-performance-indicator widgets shown on B1 cockpit/Fiori dashboards. Live rows in JIVO_OIL_HANADB: 6 defined.
- [[LengthMeasures]] **(6 rows)** — Length unit-of-measure lookup (mm-based conversions) used for item dimension fields. Live rows in JIVO_OIL_HANADB: 6 units.
- [[NatureOfAssessees]] **(3 rows)** — India TDS lookup classifying business partners by assessee type (company/individual/others) for withholding-tax determination. Live rows in JIVO_OIL_HANADB: 3 — COM "Company" (atCompany), IND "Individual" (atOthers), HUF "HUF" (atOthers).
- [[ClosingDateProcedure]] **(1 row)** — Read-only setup for due-date closing procedures (month-end payment-date rules) used by payment terms calculations.
- [[Manufacturers]] **(1 row)** — Item manufacturer lookup referenced by the item master Manufacturer field. Live rows in JIVO_OIL_HANADB: 1 — and it's only the built-in placeholder (Code -1, "- No Manufacturer -"), so no real manufacturers are maintained.
- [[AlternateCatNum]] — Maps a business partner's own catalog numbers to internal item codes so documents can use the partner's part numbers (empty in JIVO).
- [[BPPriorities]] — Defines priority levels that can be assigned to business partners for segmentation/service ranking (empty in JIVO).
- [[BrazilBeverageIndexers]] — Brazil-localization lookup of beverage tax indexer codes for fiscal reporting; irrelevant to Indian localization (empty).
- [[BrazilFuelIndexers]] — Brazil-localization lookup of fuel tax indexer codes (ANP) for fiscal documents; irrelevant here (empty).
- [[BrazilMultiIndexers]] — Brazil-localization multi-value tax indexer assignments for items; irrelevant to this Indian DB (empty).
- [[BrazilNumericIndexers]] — Brazil-localization numeric tax indexer values used in fiscal calculations; irrelevant here (empty).
- [[BrazilStringIndexers]] — Brazil-localization string tax indexer values for fiscal documents; irrelevant here (empty).
- [[CashDiscounts]] — Defines cash discount schemes (early-payment discount rules) attachable to payment terms (empty in JIVO).
- [[Counties]] — Lookup of counties/districts within states used in addresses and tax jurisdiction determination (empty in JIVO).
- [[CustomsDeclaration]] — Records import customs declarations linking foreign purchases to customs/broker data for landed-cost handling (empty — imports not tracked here).
- [[EmploymentCategorys]] — HR lookup of employment categories (e.g. full-time, contract) assigned to employee master records. Live rows in JIVO_OIL_HANADB: 0 — the HR module's category list is unused here.
- [[Entities:]] — Service-document root that lists all entity sets exposed by the Service Layer (metadata/discovery endpoint, not business data).
- [[ExceptionalEvents]] — Catalog of exceptional demand events (promotions, one-off spikes) used to flag anomalies in sales forecasting. Live rows in JIVO_OIL_HANADB: 0 — forecasting anomalies are not catalogued here.
- [[FactoringIndicators]] — Localization lookup marking receivables sold to a factoring company on invoices/BPs. Live rows in JIVO_OIL_HANADB: 0 — no factoring arrangements are modelled.
- [[InternalReconciliations]] — Internal reconciliation records matching open debits/credits on BP or G/L accounts. Live rows in JIVO_OIL_HANADB: unknown — the collection GET returned HTTP 502 during recon, so no count is available; only by-key GET is catalogued.
- [[LegalData]] — Localization store of statutory/legal registration details attached to the company or business partners. Live rows in JIVO_OIL_HANADB: 0 — statutory registrations live elsewhere (BP fiscal fields) in this India setup.
- [[LocalEra]] — Localization calendar-era definitions (e.g. Japanese imperial eras) for date display. Live rows in JIVO_OIL_HANADB: 0 — unused in the India localization.
- [[NFModels]] — Brazil localization Nota Fiscal model codes for fiscal document types. Live rows in JIVO_OIL_HANADB: 0 — unused in this India database.
- [[POSDailySummary]] — Aggregated point-of-sale daily sales summary documents for consolidated POS posting. Live rows in JIVO_OIL_HANADB: 0 — no POS integration posts here.

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[B1Sessions]] — Internal session-management endpoint for Service Layer session state; exposes no callable operations here.
- [[Login]] — Authenticates a user against a company database and opens a Service Layer session (returns B1SESSION cookie).
- [[Logout]] — Terminates the current Service Layer session and invalidates the session cookie.
