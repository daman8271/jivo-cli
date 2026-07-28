# Financials & Accounting (part 2)

The G/L backbone, part 2 of 2 (see [[financials-accounting-1]]): the transaction heart is [[JournalEntries]] — 131k postings, every financial event in the company — typed by [[JournalEntryDocumentTypes]] and framed by [[FinancialYears]]. Tax execution lives here: [[VatGroups]], [[TaxCodeDeterminations]] (India GST determination — readable, though this endpoint reports 0 rows at JIVO), [[WithholdingTaxCodes]] and [[WitholdingTaxDefinition]] for TDS. [[GLAccountAdvancedRules]] (318 rows) drives account determination, [[FAAccountDeterminations]] covers fixed assets, and Brazil-localization tables (Nota Fiscal) plus [[Forms1099]] round out the localization set.

Part of the [[00-SAP-B1-Atlas]] — 21 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[JournalEntries]] **(131,295 rows)** — The core G/L journal — every accounting transaction (manual and document-generated) with debit/credit lines; 131k rows in JIVO_OIL.
- [[GLAccountAdvancedRules]] **(318 rows)** — Advanced G/L account determination rules that override default posting accounts per item/item-group/BP criteria.
- [[ProfitCenters]] **(198 rows)** — Cost/profit centers (198 in JIVO_OIL) used for dimensional cost accounting and P&L segmentation.
- [[DistributionRules]] **(194 rows)** — Cost-accounting distribution rules that allocate revenues/expenses across cost centers (dimensions) by factor weights.
- [[WithholdingTaxCodes]] **(22 rows)** — India TDS/TCS withholding-tax codes (22 active) with rates, sections, and the AP/AR G/L accounts they post to.
- [[NFTaxCategories]] **(9 rows)** — Nota Fiscal tax categories (Brazil localization) grouping tax codes for fiscal document processing.
- [[FAAccountDeterminations]] **(4 rows)** — Maps fixed-asset events (acquisition, depreciation, retirement, revaluation) to the G/L accounts they post to.
- [[TaxCodeDeterminationsTCD]] **(4 rows)** — India/localized TCD tax-code determination setup holding default AP/AR tax codes plus key-field and usage-based rules.
- [[FinancialYears]] **(3 rows)** — Defines fiscal years (start/end dates and assessment year) used for period control and India TCS accumulation.
- [[FiscalPrinter]] — Registers fiscal printer devices for legally mandated receipt printing (localization feature; empty in this India DB).
- [[Forms1099]] — US 1099 tax form/box definitions for vendor payment reporting (US localization; empty in this India DB).
- [[JournalEntryDocumentTypes]] — User-defined document-type codes for classifying manual journal entries (unused here — empty).
- [[NotaFiscalCFOP]] — Brazilian CFOP operation-nature codes for Nota Fiscal documents (Brazil localization; empty in this India DB).
- [[NotaFiscalCST]] — Brazilian CST tax-situation codes for Nota Fiscal tax lines (Brazil localization; empty here).
- [[NotaFiscalUsage]] — Brazilian Nota Fiscal usage codes describing the purpose of goods movement (Brazil localization; empty here).
- [[OccurrenceCodes]] — Bank-file occurrence/return codes for boleto payment processing (Brazil localization; empty here).
- [[TaxCodeDeterminations]] — Rules that auto-assign tax codes on marketing documents based on BP/item/location criteria (unused — empty).
- [[TaxWebSites]] — Configured external tax-service websites/providers (e.g. US sales-tax engines) with a default selector (empty here).
- [[VatGroups]] — VAT/tax group definitions with rates and posting accounts for input/output tax; reports 0 via this endpoint (India GST setup lives in tax-code tables).
- [[WitholdingTaxDefinition]] — Withholding-tax definition master (rate tiers/effective settings) backing withholding tax codes (empty via this endpoint). Note SAP's own "Witholding" spelling in the service name.
- [[WTaxTypeCodes]] — Withholding-tax type codes categorizing withholding codes by nature of payment (empty via this endpoint).
