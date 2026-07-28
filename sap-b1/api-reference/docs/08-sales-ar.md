# SAP Business One Service Layer — Sales (A/R) Domain

Reference for the **44 services** in the `sales-ar` domain (`catalog/domains.json`).
This is the customer-facing side of the sales cycle: the document flow
**Quotation → Order → Delivery → A/R Invoice** plus the corrections, credit
memos, returns, self-invoices, dunning, forecasts, opportunities and tax-master
services that hang off it.

Every operation below is copied verbatim from `catalog/services.json`; every
one-line purpose and every field name is grounded in
`raw/service-layer-api-reference.html` (v2 API reference). Nothing is invented.

**How to read each entry**

- **Type** is one of:
  - **readable ENTITY** — an OData EntitySet with a `GET` op. You can query it
    read-only with `sapb1 query <Entity> …` (issues `GET`).
  - **function/action Service** — a `…Service_…` RPC-style endpoint (POST-only,
    no `GET`). Not queryable; it performs an action (approval handling,
    preview, batch list retrieval, cancel-with-changes).
- **Fields** for read entities are split into:
  - *Query fields* — the exact names that appear in the reference's `$select`
    example for that entity (safe to `--select`).
  - *Writable fields* — top-level keys from the reference's POST/PATCH payload
    example (real properties, shown for context; the CLI is read-only).
- For the full live property list on your company DB, run
  `sapb1 fields <Entity>` (does `GET <Entity>?$top=1`) or read `$metadata`.
- Reference HTML shows `/b1s/v1/` paths; `/b1s/v1/` is equivalent for these
  reads and is what the examples below use.

> The `sapb1` CLI only ever issues `GET` (+ `POST /Login`, `/Logout`). The
> POST/PATCH/DELETE and action operations are documented for completeness but are
> **not** performed by the read-only CLI.

---

## Quotations

- **Purpose:** A sales quotation — an offer or proposal you send to a customer or a lead.
- **Type:** readable ENTITY
- **Operations:**
  - `GET Quotations(id)`
  - `GET Quotations`
  - `POST Quotations`
  - `PATCH Quotations(id)`
  - `POST Quotations(id)/Close`
  - `POST Quotations(id)/Cancel`
  - `POST Quotations(id)/Reopen`
  - `POST Quotations(id)/CreateCancellationDocument`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `DocumentLines` (`ItemCode`, `Quantity`, `TaxCode`, `UnitPrice`), `Comments`
- **Example:**
  ```
  GET /b1s/v1/Quotations?$select=DocEntry,DocNum,DocType&$orderby=DocNum desc&$top=20
  ```
  ```
  sapb1 query Quotations --select DocEntry,DocNum,DocType --orderby "DocNum desc" --top 20
  ```

## QuotationsService

- **Purpose:** Approval-workflow helper for sales quotations — fetch the applicable approval templates and drive an approval request. *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST QuotationsService_GetApprovalTemplates`
  - `POST QuotationsService_HandleApprovalRequest`

## Orders

- **Purpose:** A sales order — a commitment from a customer or lead to buy a product or service.
- **Type:** readable ENTITY
- **Operations:**
  - `GET Orders(id)`
  - `GET Orders`
  - `POST Orders`
  - `PATCH Orders(id)`
  - `POST Orders(id)/Close`
  - `POST Orders(id)/Cancel`
  - `POST Orders(id)/Reopen`
  - `POST Orders(id)/CreateCancellationDocument`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `DocDueDate`, `DocumentLines` (`ItemCode`, `Quantity`, `TaxCode`, `UnitPrice`), `Comments`
- **Example:**
  ```
  GET /b1s/v1/Orders?$select=DocEntry,DocNum,DocType&$filter=DocNum ge 100&$top=20
  ```
  ```
  sapb1 query Orders --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --top 20
  ```

## OrdersService

- **Purpose:** Order-level helpers — preview an order (pricing/tax/logic) before posting, plus approval-template lookup and approval handling. *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST OrdersService_GetApprovalTemplates`
  - `POST OrdersService_Preview`
  - `POST OrdersService_HandleApprovalRequest`

## DeliveryNotes

- **Purpose:** A delivery — a legally binding document indicating that shipment of goods or delivery of services has occurred.
- **Type:** readable ENTITY
- **Operations:**
  - `GET DeliveryNotes(id)`
  - `GET DeliveryNotes`
  - `POST DeliveryNotes`
  - `PATCH DeliveryNotes(id)`
  - `DELETE DeliveryNotes(id)`
  - `POST DeliveryNotes(id)/Close`
  - `POST DeliveryNotes(id)/Cancel`
  - `POST DeliveryNotes(id)/Reopen`
  - `POST DeliveryNotes(id)/CreateCancellationDocument`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `DocumentLines` (`ItemCode`, `Quantity`, `TaxCode`, `UnitPrice`), `Comments`
- **Example:**
  ```
  GET /b1s/v1/DeliveryNotes?$select=DocEntry,DocNum,DocType&$filter=DocNum ge 100&$top=20
  ```
  ```
  sapb1 query DeliveryNotes --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --top 20
  ```

## DeliveryNotesService

- **Purpose:** Delivery-note helpers — approval-template lookup, approval handling, and `Cancel2` (cancel a delivery while changing some properties first). *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST DeliveryNotesService_GetApprovalTemplates`
  - `POST DeliveryNotesService_HandleApprovalRequest`
  - `POST DeliveryNotesService_Cancel2`

## Returns

- **Purpose:** A return — the clearing document for a delivery.
- **Type:** readable ENTITY
- **Operations:**
  - `GET Returns(id)`
  - `GET Returns`
  - `POST Returns`
  - `PATCH Returns(id)`
  - `DELETE Returns(id)`
  - `POST Returns(id)/Close`
  - `POST Returns(id)/Cancel`
  - `POST Returns(id)/Reopen`
  - `POST Returns(id)/CreateCancellationDocument`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `DocumentLines` (`ItemCode`, `Quantity`, `TaxCode`, `UnitPrice`), `Comments`
- **Example:**
  ```
  GET /b1s/v1/Returns?$select=DocEntry,DocNum,DocType&$filter=DocNum ge 100&$top=20
  ```
  ```
  sapb1 query Returns --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --top 20
  ```

## ReturnsService

- **Purpose:** Return-document helpers — approval-template lookup, approval handling, and `Cancel2` (cancel a return while changing some properties first). *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST ReturnsService_GetApprovalTemplates`
  - `POST ReturnsService_HandleApprovalRequest`
  - `POST ReturnsService_Cancel2`

## ReturnRequest

- **Purpose:** A return request — the clearing document raised before a delivery is actually returned.
- **Type:** readable ENTITY
- **Operations:**
  - `GET ReturnRequest(id)`
  - `GET ReturnRequest`
  - `POST ReturnRequest`
  - `PATCH ReturnRequest(id)`
  - `DELETE ReturnRequest(id)`
  - `POST ReturnRequest(id)/Close`
  - `POST ReturnRequest(id)/Cancel`
  - `POST ReturnRequest(id)/Reopen`
  - `POST ReturnRequest(id)/SaveDraftToDocument`
  - `POST ReturnRequest(id)/CreateCancellationDocument`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `DocumentLines` (`ItemCode`, `Quantity`, `TaxCode`, `UnitPrice`), `Comments`
- **Example:**
  ```
  GET /b1s/v1/ReturnRequest?$select=DocEntry,DocNum,DocType&$filter=DocNum ge 100&$top=20
  ```
  ```
  sapb1 query ReturnRequest --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --top 20
  ```

## ReturnRequestService

- **Purpose:** Return-request helpers — preview the request before posting, plus approval-template lookup and approval handling. *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST ReturnRequestService_GetApprovalTemplates`
  - `POST ReturnRequestService_Preview`
  - `POST ReturnRequestService_HandleApprovalRequest`

## Invoices

- **Purpose:** An A/R invoice — the request for payment posted to the customer.
- **Type:** readable ENTITY
- **Operations:**
  - `GET Invoices(id)`
  - `GET Invoices`
  - `POST Invoices`
  - `PATCH Invoices(id)`
  - `POST Invoices(id)/Close`
  - `POST Invoices(id)/Cancel`
  - `POST Invoices(id)/Reopen`
  - `POST Invoices(id)/CreateCancellationDocument`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `DocumentLines` (`ItemCode`, `Quantity`, `TaxCode`, `UnitPrice`), `Comments`
- **Example:**
  ```
  GET /b1s/v1/Invoices?$select=DocEntry,DocNum,DocType&$filter=DocNum ge 100&$orderby=DocNum desc&$top=20
  ```
  ```
  sapb1 query Invoices --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --orderby "DocNum desc" --top 20
  ```

## InvoicesService

- **Purpose:** A/R-invoice helpers — approval-template lookup, approval handling, request approval for a cancellation, and `Cancel2` (cancel while changing some properties first). *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST InvoicesService_GetApprovalTemplates`
  - `POST InvoicesService_HandleApprovalRequest`
  - `POST InvoicesService_RequestApproveCancellation`
  - `POST InvoicesService_Cancel2`

## CreditNotes

- **Purpose:** An A/R credit note — the clearing document for invoices and returns; used to partially or completely reverse a transaction after goods were delivered and invoiced.
- **Type:** readable ENTITY
- **Operations:**
  - `GET CreditNotes(id)`
  - `GET CreditNotes`
  - `POST CreditNotes`
  - `PATCH CreditNotes(id)`
  - `DELETE CreditNotes(id)`
  - `POST CreditNotes(id)/Close`
  - `POST CreditNotes(id)/Cancel`
  - `POST CreditNotes(id)/Reopen`
  - `POST CreditNotes(id)/CreateCancellationDocument`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `DocumentLines` (`ItemCode`, `Price`, `Quantity`, `TaxCode`), `Comments`
- **Example:**
  ```
  GET /b1s/v1/CreditNotes?$select=DocEntry,DocNum,DocType&$filter=DocNum ge 100&$top=20
  ```
  ```
  sapb1 query CreditNotes --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --top 20
  ```

## CreditNotesService

- **Purpose:** Credit-note helpers — approval-template lookup, approval handling, request approval for a cancellation, and `Cancel2` (cancel while changing some properties first). *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST CreditNotesService_GetApprovalTemplates`
  - `POST CreditNotesService_HandleApprovalRequest`
  - `POST CreditNotesService_RequestApproveCancellation`
  - `POST CreditNotesService_Cancel2`

## CorrectionInvoice

- **Purpose:** A correction invoice — used to correct an already-issued A/R invoice (localization-specific). *(inferred)*
- **Type:** readable ENTITY
- **Operations:**
  - `GET CorrectionInvoice(id)`
  - `GET CorrectionInvoice`
  - `POST CorrectionInvoice`
  - `PATCH CorrectionInvoice(id)`
  - `POST CorrectionInvoice(id)/Close`
  - `POST CorrectionInvoice(id)/Cancel`
  - `POST CorrectionInvoice(id)/Reopen`
  - `POST CorrectionInvoice(id)/CreateCancellationDocument`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `Comments`, `DocumentLines` (`CorrectionInvoiceItem`, `ItemCode`, `Price`, `Quantity`, `VatGroup`)
- **Example:**
  ```
  GET /b1s/v1/CorrectionInvoice?$select=DocEntry,DocNum,DocType&$filter=DocNum ge 100&$top=20
  ```
  ```
  sapb1 query CorrectionInvoice --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --top 20
  ```

## CorrectionInvoiceService

- **Purpose:** Correction-invoice approval helper — fetch approval templates and drive an approval request. *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST CorrectionInvoiceService_GetApprovalTemplates`
  - `POST CorrectionInvoiceService_HandleApprovalRequest`

## CorrectionInvoiceReversal

- **Purpose:** A correction-invoice reversal — used to reverse the correction invoice.
- **Type:** readable ENTITY
- **Operations:**
  - `GET CorrectionInvoiceReversal(id)`
  - `GET CorrectionInvoiceReversal`
  - `POST CorrectionInvoiceReversal`
  - `PATCH CorrectionInvoiceReversal(id)`
  - `POST CorrectionInvoiceReversal(id)/Close`
  - `POST CorrectionInvoiceReversal(id)/Cancel`
  - `POST CorrectionInvoiceReversal(id)/Reopen`
  - `POST CorrectionInvoiceReversal(id)/CreateCancellationDocument`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `Comments`, `DocDate`, `DocDueDate`, `InternalCorrectedDocNum`
- **Example:**
  ```
  GET /b1s/v1/CorrectionInvoiceReversal?$select=DocEntry,DocNum,DocType&$filter=DocNum ge 100&$top=20
  ```
  ```
  sapb1 query CorrectionInvoiceReversal --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --top 20
  ```

## CorrectionInvoiceReversalService

- **Purpose:** Correction-invoice-reversal approval helper — fetch approval templates and drive an approval request. *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST CorrectionInvoiceReversalService_GetApprovalTemplates`
  - `POST CorrectionInvoiceReversalService_HandleApprovalRequest`

## SelfInvoices

- **Purpose:** A self-invoice — represents a request for payment; also records the cost in a profit-and-loss statement.
- **Type:** readable ENTITY
- **Operations:**
  - `GET SelfInvoices(id)`
  - `GET SelfInvoices`
  - `POST SelfInvoices`
  - `PATCH SelfInvoices(id)`
  - `POST SelfInvoices(id)/Close`
  - `POST SelfInvoices(id)/Cancel`
  - `POST SelfInvoices(id)/Reopen`
  - `POST SelfInvoices(id)/CreateCancellationDocument`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `DocumentLines` (`ItemCode`, `Quantity`, `TaxCode`, `UnitPrice`), `Comments`
- **Example:**
  ```
  GET /b1s/v1/SelfInvoices?$select=DocEntry,DocNum,DocType&$filter=DocNum ge 100&$top=20
  ```
  ```
  sapb1 query SelfInvoices --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --top 20
  ```

## SelfInvoiceService

- **Purpose:** Self-invoice helpers — approval-template lookup, approval handling, and `Cancel2` (cancel while changing some properties first). *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST SelfInvoiceService_GetApprovalTemplates`
  - `POST SelfInvoiceService_HandleApprovalRequest`
  - `POST SelfInvoiceService_Cancel2`

## SalesTaxInvoices

- **Purpose:** A sales Tax Invoice document.
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesTaxInvoices(id)`
  - `GET SalesTaxInvoices`
  - `POST SalesTaxInvoices`
  - `PATCH SalesTaxInvoices(id)`
  - `DELETE SalesTaxInvoices(id)`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `Comments`, `DocType`, `SalesTaxInvoiceLines` (`RefEntry1`), `SalesTaxInvoiceOperationCodes` (`OpCode`)
- **Example:**
  ```
  GET /b1s/v1/SalesTaxInvoices?$select=DocEntry,DocNum,DocType&$filter=DocNum ge 100&$top=20
  ```
  ```
  sapb1 query SalesTaxInvoices --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --top 20
  ```

## Drafts

- **Purpose:** Document drafts — the preliminary version of a document or report (any sales/purchase marketing document saved as a draft).
- **Type:** readable ENTITY
- **Operations:**
  - `GET Drafts(id)`
  - `GET Drafts`
  - `POST Drafts`
  - `PATCH Drafts(id)`
  - `DELETE Drafts(id)`
  - `POST Drafts(id)/Close`
  - `POST Drafts(id)/Cancel`
  - `POST Drafts(id)/Reopen`
  - `POST Drafts(id)/CreateCancellationDocument`
- **Query fields:** `DocEntry`, `DocNum`, `DocType`
- **Writable fields:** `CardCode`, `DocObjectCode`, `DocumentLines` (`ItemCode`, `Quantity`, `TaxCode`, `UnitPrice`), `Comments`
- **Example:**
  ```
  GET /b1s/v1/Drafts?$select=DocEntry,DocNum,DocType&$filter=DocNum ge 100&$top=20
  ```
  ```
  sapb1 query Drafts --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --top 20
  ```

## DraftsService

- **Purpose:** Draft helpers — approval-template lookup, approval handling, and `SaveDraftToDocument` (promote a draft into a real posted document). *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST DraftsService_GetApprovalTemplates`
  - `POST DraftsService_HandleApprovalRequest`
  - `POST DraftsService_SaveDraftToDocument`

## BlanketAgreements

- **Purpose:** A blanket (framework) agreement with a business partner covering planned quantities/prices over a period. *(inferred)*
- **Type:** readable ENTITY
- **Operations:**
  - `GET BlanketAgreements(id)`
  - `GET BlanketAgreements`
  - `POST BlanketAgreements`
  - `PATCH BlanketAgreements(id)`
  - `POST BlanketAgreements(id)/CancelBlanketAgreement`
  - `POST BlanketAgreements(id)/GetRelatedDocuments`
- **Query fields:** `AgreementNo`, `BPCode`, `BPName`
- **Writable fields:** `AgreementType`, `BPCode`, `Description`, `Status`, `EndDate`, `BlanketAgreements_ItemsLines` (`ItemNo`, `PlannedQuantity`, `UnitPrice`)
- **Example:**
  ```
  GET /b1s/v1/BlanketAgreements?$select=AgreementNo,BPCode,BPName&$orderby=AgreementNo desc&$top=20
  ```
  ```
  sapb1 query BlanketAgreements --select AgreementNo,BPCode,BPName --orderby "AgreementNo desc" --top 20
  ```

## BlanketAgreementsService

- **Purpose:** Batch retrieval of blanket agreements via `GetBlanketAgreementList`. *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST BlanketAgreementsService_GetBlanketAgreementList`

## DunningTerms

- **Purpose:** Dunning terms — the reminder-level/interest configuration used when running the dunning wizard. *(inferred)*
- **Type:** readable ENTITY
- **Operations:**
  - `GET DunningTerms(id)`
  - `GET DunningTerms`
  - `POST DunningTerms`
  - `PATCH DunningTerms(id)`
  - `DELETE DunningTerms(id)`
- **Query fields:** `Code`, `Name`, `GroupingMethod`
- **Writable fields:** `Code`, `Name`, `GroupingMethod`, `DaysInMonth`, `DaysInYear`, `LetterFormat`, `DunningTermLines` (`LevelNum`, `Effectiveafter`)
- **Example:**
  ```
  GET /b1s/v1/DunningTerms?$select=Code,Name,GroupingMethod&$top=20
  ```
  ```
  sapb1 query DunningTerms --select Code,Name,GroupingMethod --top 20
  ```

## DunningTermsService

- **Purpose:** Batch retrieval of dunning terms via `GetDunningTermList`. *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST DunningTermsService_GetDunningTermList`

## DunningLetters

- **Purpose:** Dunning letters — a list of dunning levels used as a template when creating a new dunning term.
- **Type:** readable ENTITY
- **Operations:**
  - `GET DunningLetters(id)`
  - `GET DunningLetters`
  - `POST DunningLetters`
  - `PATCH DunningLetters(id)`
  - `DELETE DunningLetters(id)`
- **Query fields:** `FeeCurrency`, `RowNumber`, `LetterFormat`
- **Writable fields:** `LetterFormat`, `RowNumber`, `Effectiveafter`, `Feeperletter`, `FeeCurrency`, `MinimumBalance`, `MinimumBalanceCurrency`
- **Example:**
  ```
  GET /b1s/v1/DunningLetters?$select=FeeCurrency,RowNumber,LetterFormat&$top=20
  ```
  ```
  sapb1 query DunningLetters --select FeeCurrency,RowNumber,LetterFormat --top 20
  ```

## SalesForecast

- **Purpose:** A sales forecast for a specified period.
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesForecast(id)`
  - `GET SalesForecast`
  - `POST SalesForecast`
  - `PATCH SalesForecast(id)`
  - `DELETE SalesForecast(id)`
- **Query fields:** `ForecastStartDate`, `ForecastEndDate`, `ForecastCode`
- **Writable fields:** `ForecastCode`, `ForecastName`, `View`, `SalesForecastLines` (`ForecastedDay`, `ItemNo`, `Quantity`)
- **Example:**
  ```
  GET /b1s/v1/SalesForecast?$select=ForecastCode,ForecastStartDate,ForecastEndDate&$top=20
  ```
  ```
  sapb1 query SalesForecast --select ForecastCode,ForecastStartDate,ForecastEndDate --top 20
  ```

## SalesOpportunities

- **Purpose:** Sales opportunities — potential sale volumes that may arise from business with customers and interested parties.
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesOpportunities(id)`
  - `GET SalesOpportunities`
  - `POST SalesOpportunities`
  - `PATCH SalesOpportunities(id)`
  - `DELETE SalesOpportunities(id)`
  - `POST SalesOpportunities(id)/Close`
- **Query fields:** `SequentialNo`, `CardCode`, `SalesPerson`
- **Writable fields:** `OpportunityName` (plus opportunity lines) — for the full writable set run `sapb1 fields SalesOpportunities`
- **Example:**
  ```
  GET /b1s/v1/SalesOpportunities?$select=SequentialNo,CardCode,SalesPerson&$filter=SequentialNo ge 1&$top=20
  ```
  ```
  sapb1 query SalesOpportunities --select SequentialNo,CardCode,SalesPerson --filter "SequentialNo ge 1" --top 20
  ```

## SalesStages

- **Purpose:** Sales stages — defines the stages of a deal and the closing probability each stage represents.
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesStages(id)`
  - `GET SalesStages`
  - `POST SalesStages`
  - `PATCH SalesStages(id)`
- **Query fields:** `SequenceNo`, `Name`, `Stageno`
- **Writable fields:** `Name`, `Stageno`, `ClosingPercentage`
- **Example:**
  ```
  GET /b1s/v1/SalesStages?$select=SequenceNo,Name,Stageno&$orderby=Stageno&$top=20
  ```
  ```
  sapb1 query SalesStages --select SequenceNo,Name,Stageno --orderby "Stageno" --top 20
  ```

## SalesOpportunityCompetitorsSetup

- **Purpose:** Setup list of competitors selectable on a sales opportunity. *(inferred)*
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesOpportunityCompetitorsSetup(id)`
  - `GET SalesOpportunityCompetitorsSetup`
  - `POST SalesOpportunityCompetitorsSetup`
  - `PATCH SalesOpportunityCompetitorsSetup(id)`
  - `DELETE SalesOpportunityCompetitorsSetup(id)`
- **Query fields:** `SequenceNo`, `Name`, `ThreatLevel`
- **Writable fields:** `Name`, `SequenceNo`, `ThreatLevel`, `Details`
- **Example:**
  ```
  GET /b1s/v1/SalesOpportunityCompetitorsSetup?$select=SequenceNo,Name,ThreatLevel&$top=20
  ```
  ```
  sapb1 query SalesOpportunityCompetitorsSetup --select SequenceNo,Name,ThreatLevel --top 20
  ```

## SalesOpportunityCompetitorsSetupService

- **Purpose:** Batch retrieval of the sales-opportunity competitor setup list via `GetSalesOpportunityCompetitorSetupList`. *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST SalesOpportunityCompetitorsSetupService_GetSalesOpportunityCompetitorSetupList`

## SalesOpportunityInterestsSetup

- **Purpose:** Setup list of "interest" values selectable on a sales opportunity. *(inferred)*
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesOpportunityInterestsSetup(id)`
  - `GET SalesOpportunityInterestsSetup`
  - `POST SalesOpportunityInterestsSetup`
  - `PATCH SalesOpportunityInterestsSetup(id)`
  - `DELETE SalesOpportunityInterestsSetup(id)`
- **Query fields:** `SequenceNo`, `Description`, `Sort`
- **Writable fields:** `SequenceNo`, `Description`, `Sort`
- **Example:**
  ```
  GET /b1s/v1/SalesOpportunityInterestsSetup?$select=SequenceNo,Description,Sort&$top=20
  ```
  ```
  sapb1 query SalesOpportunityInterestsSetup --select SequenceNo,Description,Sort --top 20
  ```

## SalesOpportunityInterestsSetupService

- **Purpose:** Batch retrieval of the sales-opportunity interest setup list via `GetSalesOpportunityInterestSetupList`. *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST SalesOpportunityInterestsSetupService_GetSalesOpportunityInterestSetupList`

## SalesOpportunityReasonsSetup

- **Purpose:** Setup list of "reason" values selectable on a sales opportunity. *(inferred)*
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesOpportunityReasonsSetup(id)`
  - `GET SalesOpportunityReasonsSetup`
  - `POST SalesOpportunityReasonsSetup`
  - `PATCH SalesOpportunityReasonsSetup(id)`
  - `DELETE SalesOpportunityReasonsSetup(id)`
- **Query fields:** `SequenceNo`, `Description`, `Sort`
- **Writable fields:** `SequenceNo`, `Description`, `Sort`
- **Example:**
  ```
  GET /b1s/v1/SalesOpportunityReasonsSetup?$select=SequenceNo,Description,Sort&$top=20
  ```
  ```
  sapb1 query SalesOpportunityReasonsSetup --select SequenceNo,Description,Sort --top 20
  ```

## SalesOpportunityReasonsSetupService

- **Purpose:** Batch retrieval of the sales-opportunity reason setup list via `GetSalesOpportunityReasonSetupList`. *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST SalesOpportunityReasonsSetupService_GetSalesOpportunityReasonSetupList`

## SalesOpportunitySourcesSetup

- **Purpose:** Setup list of "source" values (lead sources) selectable on a sales opportunity. *(inferred)*
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesOpportunitySourcesSetup(id)`
  - `GET SalesOpportunitySourcesSetup`
  - `POST SalesOpportunitySourcesSetup`
  - `PATCH SalesOpportunitySourcesSetup(id)`
  - `DELETE SalesOpportunitySourcesSetup(id)`
- **Query fields:** `SequenceNo`, `Description`, `Sort`
- **Writable fields:** `SequenceNo`, `Description`, `Sort`
- **Example:**
  ```
  GET /b1s/v1/SalesOpportunitySourcesSetup?$select=SequenceNo,Description,Sort&$top=20
  ```
  ```
  sapb1 query SalesOpportunitySourcesSetup --select SequenceNo,Description,Sort --top 20
  ```

## SalesOpportunitySourcesSetupService

- **Purpose:** Batch retrieval of the sales-opportunity source setup list via `GetSalesOpportunitySourceSetupList`. *(inferred)*
- **Type:** function/action Service
- **Operations:**
  - `POST SalesOpportunitySourcesSetupService_GetSalesOpportunitySourceSetupList`

## SalesPersons

- **Purpose:** Sales employees and their commission rates.
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesPersons(id)`
  - `GET SalesPersons`
  - `POST SalesPersons`
  - `PATCH SalesPersons(id)`
  - `DELETE SalesPersons(id)`
- **Query fields:** `SalesEmployeeCode`, `SalesEmployeeName`, `Remarks`
- **Writable fields:** `SalesEmployeeName`, `Active`, `Remarks`
- **Example:**
  ```
  GET /b1s/v1/SalesPersons?$select=SalesEmployeeCode,SalesEmployeeName,Remarks&$top=20
  ```
  ```
  sapb1 query SalesPersons --select SalesEmployeeCode,SalesEmployeeName,Remarks --top 20
  ```

## SalesTaxAuthorities

- **Purpose:** Sales tax jurisdictions (US/Canada localizations) or sales tax types (Latin America localization).
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesTaxAuthorities(id)`
  - `GET SalesTaxAuthorities`
  - `POST SalesTaxAuthorities`
  - `PATCH SalesTaxAuthorities(id)`
  - `DELETE SalesTaxAuthorities(id)`
- **Query fields:** `UseTaxAccount`, `UserSignature`, `Type`
- **Writable fields:** `Code`, `Name`, `Type`, `UseTaxAccount`, `AOrPTaxAccount`, `AOrRTaxAccount`, `TaxDefinitions` (`Effectivefrom`, `Rate`)
- **Example:**
  ```
  GET /b1s/v1/SalesTaxAuthorities?$select=UserSignature,Type,UseTaxAccount&$top=20
  ```
  ```
  sapb1 query SalesTaxAuthorities --select UserSignature,Type,UseTaxAccount --top 20
  ```

## SalesTaxAuthoritiesTypes

- **Purpose:** Types of sales tax authorities — specifies whether the sales tax authority includes VAT.
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesTaxAuthoritiesTypes(id)`
  - `GET SalesTaxAuthoritiesTypes`
  - `POST SalesTaxAuthoritiesTypes`
  - `PATCH SalesTaxAuthoritiesTypes(id)`
  - `DELETE SalesTaxAuthoritiesTypes(id)`
- **Query fields:** `UserSignature`, `Name`, `VAT`
- **Writable fields:** `Name`
- **Example:**
  ```
  GET /b1s/v1/SalesTaxAuthoritiesTypes?$select=UserSignature,Name,VAT&$top=20
  ```
  ```
  sapb1 query SalesTaxAuthoritiesTypes --select UserSignature,Name,VAT --top 20
  ```

## SalesTaxCodes

- **Purpose:** Inclusive sales tax codes — each tax code consists of one or more sales taxes.
- **Type:** readable ENTITY
- **Operations:**
  - `GET SalesTaxCodes(id)`
  - `GET SalesTaxCodes`
  - `POST SalesTaxCodes`
  - `PATCH SalesTaxCodes(id)`
  - `DELETE SalesTaxCodes(id)`
- **Query fields:** `ValidForAR`, `ValidForAP`, `UserSignature`
- **Writable fields:** `Code`, `Name`, `STACode`, `STAType`
- **Example:**
  ```
  GET /b1s/v1/SalesTaxCodes?$select=ValidForAR,ValidForAP,UserSignature&$top=20
  ```
  ```
  sapb1 query SalesTaxCodes --select ValidForAR,ValidForAP,UserSignature --top 20
  ```

## TaxInvoiceReport

- **Purpose:** Tax invoice report — records tax-invoice reporting/e-tax details (e.g. NTS e-tax reporting, localization-specific). *(inferred)*
- **Type:** readable ENTITY
- **Operations:**
  - `GET TaxInvoiceReport(id)`
  - `GET TaxInvoiceReport`
  - `PATCH TaxInvoiceReport(id)`
  - `POST TaxInvoiceReport(id)/CancelTaxInvoiceReport`
- **Query fields:** `NTSApproval`, `ETaxWebSite`, `ETaxNo`
- **Writable fields:** `Remarks`
- **Example:**
  ```
  GET /b1s/v1/TaxInvoiceReport?$select=ETaxNo,NTSApproval,ETaxWebSite&$top=20
  ```
  ```
  sapb1 query TaxInvoiceReport --select ETaxNo,NTSApproval,ETaxWebSite --top 20
  ```

---

### Domain summary

- **44 services total** — **27 readable entities** + **17 function/action services**.
- Common per-document action ops: `Close`, `Cancel`, `Reopen`,
  `CreateCancellationDocument` (invoke on `<Entity>(id)/<Action>`).
- Common per-service ops: `GetApprovalTemplates`, `HandleApprovalRequest`,
  `Preview`, `Cancel2` (cancel while changing some properties first),
  `SaveDraftToDocument`, and the `Get…List` batch retrievers.
- Field names are grounded in the API-reference `$select`/payload examples. For
  the full live property set on your company DB use `sapb1 fields <Entity>` or
  read `$metadata`.
