# SAP Business One Service Layer — Purchasing (A/P)

Reference for the **Purchasing (A/P)** domain: 24 Service Layer services covering the
A/P purchasing flow — purchase requests, quotations, orders, goods receipt (delivery)
notes, A/P invoices and their corrections, credit notes, returns/return requests,
landed costs, and purchase tax invoices.

**24 services total — 13 are readable entities (have a `GET`), 11 are POST-only
function/action services.** The 11 `*Service` objects are the RPC-style companions to
the document entities: they expose the approval-workflow calls
(`GetApprovalTemplates`, `HandleApprovalRequest`), the pre-cancel editor (`Cancel2`),
a document `Preview`, and the landed-cost list. Every description, operation, and field
below comes from the bundled `catalog/services.json` and
`raw/service-layer-api-reference.html`. Paths are shown at `/b1s/v1/…` exactly as the
reference documents them; the `sapb1` CLI handles the version for you. Nothing here is
invented — where the reference does not list a field, it says so.

Legend:
- **readable ENTITY** — exposes `GET` (collection + by-id); queryable with OData `$select/$filter/$orderby` and the `sapb1 query` tool.
- **function/action Service** — POST-only RPC-style call; not OData-queryable. Invoke by POSTing to the operation path.

> **Field note:** the API-reference HTML only prints the handful of field names that
> appear in each entity's example URL (`$select=…`) and example `POST` payload — it does
> **not** ship a full property table (e.g. `DocTotal`, `DocStatus`, `DocDate` never appear
> in the file). So the "Fields" lists below are the *real* names the reference actually
> shows; for the complete property set of any entity, query the live `$metadata`.

---

# Part 1 — Function / action services (POST-only)

## PurchaseRequestService

1. **Purpose:** Approval-workflow companion service for the `PurchaseRequests` entity. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'PurchaseRequestService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST PurchaseRequestService_GetApprovalTemplates`
   - `POST PurchaseRequestService_HandleApprovalRequest`

To read purchase requests as a queryable table, use the **PurchaseRequests** entity below.

---

## PurchaseQuotationsService

1. **Purpose:** Approval-workflow companion service for the `PurchaseQuotations` entity. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'PurchaseQuotationsService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST PurchaseQuotationsService_GetApprovalTemplates`
   - `POST PurchaseQuotationsService_HandleApprovalRequest`

To read purchase quotations as a queryable table, use the **PurchaseQuotations** entity below.

---

## PurchaseOrdersService

1. **Purpose:** Approval-workflow companion service for the `PurchaseOrders` entity. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'PurchaseOrdersService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST PurchaseOrdersService_GetApprovalTemplates` — reference: "Invoke the method 'GetApprovalTemplates' on this service by specifying the payload 'Document' in the JSON format."
   - `POST PurchaseOrdersService_HandleApprovalRequest`

To read purchase orders as a queryable table, use the **PurchaseOrders** entity below.

---

## PurchaseDeliveryNotesService

1. **Purpose:** Approval-workflow and pre-cancel companion service for the `PurchaseDeliveryNotes` (goods-receipt PO) entity. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'PurchaseDeliveryNotesService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST PurchaseDeliveryNotesService_GetApprovalTemplates`
   - `POST PurchaseDeliveryNotesService_HandleApprovalRequest`
   - `POST PurchaseDeliveryNotesService_Cancel2` — "This method allows you to change some properties before cancelling one document."

To read delivery notes as a queryable table, use the **PurchaseDeliveryNotes** entity below.

---

## PurchaseReturnsService

1. **Purpose:** Approval-workflow and pre-cancel companion service for the `PurchaseReturns` entity. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'PurchaseReturnsService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST PurchaseReturnsService_GetApprovalTemplates`
   - `POST PurchaseReturnsService_HandleApprovalRequest`
   - `POST PurchaseReturnsService_Cancel2` — "This method allows you to change some properties before cancelling one document."

To read purchase returns as a queryable table, use the **PurchaseReturns** entity below.

---

## PurchaseInvoicesService

1. **Purpose:** Approval-workflow and pre-cancel companion service for the `PurchaseInvoices` (A/P invoice) entity. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'PurchaseInvoicesService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST PurchaseInvoicesService_GetApprovalTemplates`
   - `POST PurchaseInvoicesService_HandleApprovalRequest`
   - `POST PurchaseInvoicesService_Cancel2` — "This method allows you to change some properties before cancelling one document."

To read A/P invoices as a queryable table, use the **PurchaseInvoices** entity below.

---

## PurchaseCreditNotesService

1. **Purpose:** Approval-workflow and pre-cancel companion service for the `PurchaseCreditNotes` (A/P credit memo) entity. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'PurchaseCreditNotesService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST PurchaseCreditNotesService_GetApprovalTemplates`
   - `POST PurchaseCreditNotesService_HandleApprovalRequest`
   - `POST PurchaseCreditNotesService_Cancel2` — "This method allows you to change some properties before cancelling one document."

To read A/P credit notes as a queryable table, use the **PurchaseCreditNotes** entity below.

---

## CorrectionPurchaseInvoiceService

1. **Purpose:** Approval-workflow companion service for the `CorrectionPurchaseInvoice` entity. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'CorrectionPurchaseInvoiceService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST CorrectionPurchaseInvoiceService_GetApprovalTemplates`
   - `POST CorrectionPurchaseInvoiceService_HandleApprovalRequest`

To read correction invoices as a queryable table, use the **CorrectionPurchaseInvoice** entity below.

---

## CorrectionPurchaseInvoiceReversalService

1. **Purpose:** Approval-workflow companion service for the `CorrectionPurchaseInvoiceReversal` entity. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'CorrectionPurchaseInvoiceReversalService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST CorrectionPurchaseInvoiceReversalService_GetApprovalTemplates`
   - `POST CorrectionPurchaseInvoiceReversalService_HandleApprovalRequest`

To read correction-invoice reversals as a queryable table, use the **CorrectionPurchaseInvoiceReversal** entity below.

---

## GoodsReturnRequestService

1. **Purpose:** Approval-workflow and preview companion service for the `GoodsReturnRequest` entity. *(inferred — reference text: "This API enables you to invoke the interfaces defined on 'GoodsReturnRequestService'.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST GoodsReturnRequestService_GetApprovalTemplates`
   - `POST GoodsReturnRequestService_Preview` — reference: "Invoke the method 'Preview' on this service by specifying the payload 'Document' in the JSON format."
   - `POST GoodsReturnRequestService_HandleApprovalRequest`

To read goods-return requests as a queryable table, use the **GoodsReturnRequest** entity below.

---

## LandedCostsService

1. **Purpose:** Returns the landed-cost list (RPC companion to the `LandedCosts` entity). *(inferred — reference text is generic: "Invoke the method 'GetLandedCostList' on this service.")*
2. **Type:** function/action Service (POST-only; no GET).
3. **Operations:**
   - `POST LandedCostsService_GetLandedCostList`

To read landed-cost documents as a queryable table, use the **LandedCosts** entity below.

---

# Part 2 — Readable entities

## PurchaseRequests

1. **Purpose:** A/P purchase request — lets users and employees initiate a purchasing process by submitting their needs for certain goods or services. (from reference: "It allows users and employees in an organization to initiate a purchasing process by submitting their needs for certain goods or services.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET PurchaseRequests(id)`
   - `GET PurchaseRequests`
   - `POST PurchaseRequests`
   - `PATCH PurchaseRequests(id)`
   - `DELETE PurchaseRequests(id)`
   - `POST PurchaseRequests(id)/Close`
   - `POST PurchaseRequests(id)/Cancel`
   - `POST PurchaseRequests(id)/Reopen`
   - `POST PurchaseRequests(id)/CreateCancellationDocument`
4. **Fields (real, from the reference examples):** header `DocEntry`, `DocNum`, `DocType`; line-level (in `DocumentLines`) `ItemCode`, `Quantity`, `LineVendor`, `RequriedDate` (SAP's spelling), `Comments` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/PurchaseRequests?$select=DocEntry,DocNum,DocType&$filter=DocEntry ge 123&$top=20
   ```
   ```
   sapb1 query PurchaseRequests --select "DocEntry,DocNum,DocType" --filter "DocEntry ge 123" --top 20
   ```

---

## PurchaseQuotations

1. **Purpose:** A/P purchase quotation — an invitation to a number of vendors to find the best offer for goods or services that you require. (from reference: "It represents an invitation to a number of vendors to find the best offer for goods or services that you require.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET PurchaseQuotations(id)`
   - `GET PurchaseQuotations`
   - `POST PurchaseQuotations`
   - `PATCH PurchaseQuotations(id)`
   - `POST PurchaseQuotations(id)/Close`
   - `POST PurchaseQuotations(id)/Cancel`
   - `POST PurchaseQuotations(id)/Reopen`
   - `POST PurchaseQuotations(id)/CreateCancellationDocument`
4. **Fields (real, from the reference examples):** header `DocEntry`, `DocNum`, `DocType`, `CardCode`, `Comments`; line-level (in `DocumentLines`) `ItemCode`, `Quantity`, `UnitPrice`, `TaxCode`, `RequriedDate` (SAP's spelling) — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/PurchaseQuotations?$select=DocEntry,DocNum,CardCode,DocType&$filter=CardCode eq 'V10000'&$top=20
   ```
   ```
   sapb1 query PurchaseQuotations --select "DocEntry,DocNum,CardCode,DocType" --filter "CardCode eq 'V10000'" --top 20
   ```

---

## PurchaseOrders

1. **Purpose:** A/P purchase order — a document used to request items or services from a vendor at an agreed upon price. (from reference: "It is a document used to request items or services from a vendor at an agreed upon price.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET PurchaseOrders(id)`
   - `GET PurchaseOrders`
   - `POST PurchaseOrders`
   - `PATCH PurchaseOrders(id)`
   - `POST PurchaseOrders(id)/Close`
   - `POST PurchaseOrders(id)/Cancel`
   - `POST PurchaseOrders(id)/Reopen`
   - `POST PurchaseOrders(id)/CreateCancellationDocument`
4. **Fields (real, from the reference examples):** header `DocEntry`, `DocNum`, `DocType`, `CardCode`, `Comments`; line-level (in `DocumentLines`) `ItemCode`, `Quantity`, `UnitPrice`, `TaxCode` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/PurchaseOrders?$select=DocEntry,DocNum,CardCode,DocType&$filter=DocEntry ge 123&$top=20
   ```
   ```
   sapb1 query PurchaseOrders --select "DocEntry,DocNum,CardCode,DocType" --filter "DocEntry ge 123" --top 20
   ```

---

## PurchaseDeliveryNotes

1. **Purpose:** A/P goods receipt PO (purchase delivery note) — a legally binding document indicating that a shipment of goods or a delivery of services has occurred. (from reference: "It represents a legally binding document indicating that a shipment of goods or a delivery of services has occurred.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET PurchaseDeliveryNotes(id)`
   - `GET PurchaseDeliveryNotes`
   - `POST PurchaseDeliveryNotes`
   - `PATCH PurchaseDeliveryNotes(id)`
   - `DELETE PurchaseDeliveryNotes(id)`
   - `POST PurchaseDeliveryNotes(id)/Close`
   - `POST PurchaseDeliveryNotes(id)/Cancel`
   - `POST PurchaseDeliveryNotes(id)/Reopen`
   - `POST PurchaseDeliveryNotes(id)/CreateCancellationDocument`
4. **Fields (real, from the reference examples):** header `DocEntry`, `DocNum`, `DocType`, `CardCode`, `Comments`; line-level (in `DocumentLines`) `ItemCode`, `Quantity`, `UnitPrice`, `TaxCode` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/PurchaseDeliveryNotes?$select=DocEntry,DocNum,CardCode,DocType&$filter=CardCode eq 'V10000'&$top=20
   ```
   ```
   sapb1 query PurchaseDeliveryNotes --select "DocEntry,DocNum,CardCode,DocType" --filter "CardCode eq 'V10000'" --top 20
   ```

---

## PurchaseReturns

1. **Purpose:** A/P goods return — used to return delivered goods to vendors, or to reverse completely or partially a purchasing transaction for an item. (from reference: "It is used to return delivered goods to vendors or to reverse completely or partially a purchasing transaction for an item.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET PurchaseReturns(id)`
   - `GET PurchaseReturns`
   - `POST PurchaseReturns`
   - `PATCH PurchaseReturns(id)`
   - `POST PurchaseReturns(id)/Close`
   - `POST PurchaseReturns(id)/Cancel`
   - `POST PurchaseReturns(id)/Reopen`
   - `POST PurchaseReturns(id)/CreateCancellationDocument`
4. **Fields (real, from the reference examples):** header `DocEntry`, `DocNum`, `DocType`, `CardCode`, `Comments`; line-level (in `DocumentLines`) `ItemCode`, `Quantity`, `UnitPrice`, `TaxCode` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/PurchaseReturns?$select=DocEntry,DocNum,CardCode,DocType&$filter=DocEntry ge 123&$top=20
   ```
   ```
   sapb1 query PurchaseReturns --select "DocEntry,DocNum,CardCode,DocType" --filter "DocEntry ge 123" --top 20
   ```

---

## PurchaseInvoices

1. **Purpose:** A/P invoice — a request for payment that also records the cost in a profit and loss statement. (from reference: "It represents a request for payment. It also records the cost in a profit and loss statement.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET PurchaseInvoices(id)`
   - `GET PurchaseInvoices`
   - `POST PurchaseInvoices`
   - `PATCH PurchaseInvoices(id)`
   - `POST PurchaseInvoices(id)/Close`
   - `POST PurchaseInvoices(id)/Cancel`
   - `POST PurchaseInvoices(id)/Reopen`
   - `POST PurchaseInvoices(id)/CreateCancellationDocument`
4. **Fields (real, from the reference examples):** header `DocEntry`, `DocNum`, `DocType`, `CardCode`, `Comments`; line-level (in `DocumentLines`) `ItemCode`, `Quantity`, `UnitPrice`, `TaxCode` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/PurchaseInvoices?$select=DocEntry,DocNum,CardCode,DocType&$filter=CardCode eq 'V10000'&$top=20
   ```
   ```
   sapb1 query PurchaseInvoices --select "DocEntry,DocNum,CardCode,DocType" --filter "CardCode eq 'V10000'" --top 20
   ```

---

## PurchaseCreditNotes

1. **Purpose:** A/P credit memo — the clearing document for the A/P invoice; if the vendor delivered goods and an A/P invoice already exists, you can reverse the transaction partially or completely with a purchase credit note. (from reference: "It represents the clearing document for the A/P invoice…")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET PurchaseCreditNotes(id)`
   - `GET PurchaseCreditNotes`
   - `POST PurchaseCreditNotes`
   - `PATCH PurchaseCreditNotes(id)`
   - `DELETE PurchaseCreditNotes(id)`
   - `POST PurchaseCreditNotes(id)/Close`
   - `POST PurchaseCreditNotes(id)/Cancel`
   - `POST PurchaseCreditNotes(id)/Reopen`
   - `POST PurchaseCreditNotes(id)/CreateCancellationDocument`
4. **Fields (real, from the reference examples):** header `DocEntry`, `DocNum`, `DocType`, `CardCode`, `Comments`; line-level (in `DocumentLines`) `ItemCode`, `Quantity`, `UnitPrice`, `TaxCode` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/PurchaseCreditNotes?$select=DocEntry,DocNum,CardCode,DocType&$filter=DocEntry ge 123&$top=20
   ```
   ```
   sapb1 query PurchaseCreditNotes --select "DocEntry,DocNum,CardCode,DocType" --filter "DocEntry ge 123" --top 20
   ```

---

## CorrectionPurchaseInvoice

1. **Purpose:** Correction A/P invoice — used to correct a purchase invoice. (from reference: "It is used to correct the purchase invoice.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET CorrectionPurchaseInvoice(id)`
   - `GET CorrectionPurchaseInvoice`
   - `POST CorrectionPurchaseInvoice`
   - `PATCH CorrectionPurchaseInvoice(id)`
   - `POST CorrectionPurchaseInvoice(id)/Close`
   - `POST CorrectionPurchaseInvoice(id)/Cancel`
   - `POST CorrectionPurchaseInvoice(id)/Reopen`
   - `POST CorrectionPurchaseInvoice(id)/CreateCancellationDocument`
4. **Fields (real, from the reference examples):** header `DocEntry`, `DocNum`, `DocType`, `CardCode`, `Comments`; line-level (in `DocumentLines` / `CorrectionInvoiceItem`) `ItemCode`, `Price`, `Quantity`, `VatGroup` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/CorrectionPurchaseInvoice?$select=DocEntry,DocNum,CardCode,DocType&$filter=DocEntry ge 123&$top=20
   ```
   ```
   sapb1 query CorrectionPurchaseInvoice --select "DocEntry,DocNum,CardCode,DocType" --filter "DocEntry ge 123" --top 20
   ```

---

## CorrectionPurchaseInvoiceReversal

1. **Purpose:** Correction A/P invoice reversal — used to reverse the correction purchase invoice. (from reference: "It is used to reverse the correction purchase invoice.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET CorrectionPurchaseInvoiceReversal(id)`
   - `GET CorrectionPurchaseInvoiceReversal`
   - `POST CorrectionPurchaseInvoiceReversal`
   - `PATCH CorrectionPurchaseInvoiceReversal(id)`
   - `POST CorrectionPurchaseInvoiceReversal(id)/Close`
   - `POST CorrectionPurchaseInvoiceReversal(id)/Cancel`
   - `POST CorrectionPurchaseInvoiceReversal(id)/Reopen`
   - `POST CorrectionPurchaseInvoiceReversal(id)/CreateCancellationDocument`
4. **Fields (real, from the reference examples):** header `DocEntry`, `DocNum`, `DocType`, `CardCode`, `DocDate`, `DocDueDate`, `InternalCorrectedDocNum`, `Comments` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/CorrectionPurchaseInvoiceReversal?$select=DocEntry,DocNum,CardCode,DocType&$filter=DocEntry ge 123&$top=20
   ```
   ```
   sapb1 query CorrectionPurchaseInvoiceReversal --select "DocEntry,DocNum,CardCode,DocType" --filter "DocEntry ge 123" --top 20
   ```

---

## GoodsReturnRequest

1. **Purpose:** Goods return request — the clearing document for a delivery (a draft/request stage of a return). (from reference: "A return is the clearing document for a delivery.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET GoodsReturnRequest(id)`
   - `GET GoodsReturnRequest`
   - `POST GoodsReturnRequest`
   - `PATCH GoodsReturnRequest(id)`
   - `DELETE GoodsReturnRequest(id)`
   - `POST GoodsReturnRequest(id)/Close`
   - `POST GoodsReturnRequest(id)/Cancel`
   - `POST GoodsReturnRequest(id)/Reopen`
   - `POST GoodsReturnRequest(id)/SaveDraftToDocument`
   - `POST GoodsReturnRequest(id)/CreateCancellationDocument`
4. **Fields (real, from the reference examples):** header `DocEntry`, `DocNum`, `DocType`, `CardCode`, `Comments`; line-level (in `DocumentLines`) `ItemCode`, `Quantity`, `UnitPrice`, `TaxCode` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/GoodsReturnRequest?$select=DocEntry,DocNum,CardCode,DocType&$filter=DocEntry ge 123&$top=20
   ```
   ```
   sapb1 query GoodsReturnRequest --select "DocEntry,DocNum,CardCode,DocType" --filter "DocEntry ge 123" --top 20
   ```

---

## LandedCosts

1. **Purpose:** Landed-costs document — records additional acquisition costs (freight, insurance, customs, etc.) and allocates them to received goods. *(inferred — reference text is generic: "This entity enables you to manipulate 'LandedCosts'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET LandedCosts(id)`
   - `GET LandedCosts`
   - `POST LandedCosts`
   - `PATCH LandedCosts(id)`
   - `DELETE LandedCosts(id)`
   - `POST LandedCosts(id)/CloseLandedCost`
   - `POST LandedCosts(id)/CancelLandedCost`
4. **Fields (real, from the reference examples):** `DocEntry`, `LandedCostNumber`, `PostingDate`, `JournalRemarks` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/LandedCosts?$select=DocEntry,LandedCostNumber,PostingDate&$filter=DocEntry ge 123&$top=20
   ```
   ```
   sapb1 query LandedCosts --select "DocEntry,LandedCostNumber,PostingDate" --filter "DocEntry ge 123" --top 20
   ```

---

## LandedCostsCodes

1. **Purpose:** Landed-cost type codes — defines types of landed costs (e.g. insurance, customs) and their default distribution rules; when you record landed costs for deliveries, costs are allocated to goods per each type's distribution rule. (from reference: "It defines various types of landed costs (for example, insurance, customs) and their default distribution rules…")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET LandedCostsCodes(id)`
   - `GET LandedCostsCodes`
   - `POST LandedCostsCodes`
   - `PATCH LandedCostsCodes(id)`
   - `DELETE LandedCostsCodes(id)`
4. **Fields (real, from the reference examples):** `Code`, `Name`, `AllocationBy` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/LandedCostsCodes?$select=Code,Name,AllocationBy&$top=20
   ```
   ```
   sapb1 query LandedCostsCodes --select "Code,Name,AllocationBy" --top 20
   ```

---

## PurchaseTaxInvoices

1. **Purpose:** Purchase tax invoice — represents the data of a purchase Tax Invoice document. (from reference: "It represents the data of a purchase Tax Invoice document.")
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET PurchaseTaxInvoices(id)`
   - `GET PurchaseTaxInvoices`
   - `POST PurchaseTaxInvoices`
   - `PATCH PurchaseTaxInvoices(id)`
4. **Fields (real, from the reference examples):** header `DocEntry`, `DocNum`, `DocType`, `CardCode`, `Comments`, `RefEntry1`; line-level (in `PurchaseTaxInvoiceLines` / `PurchaseTaxInvoiceOperationCodes`) `OpCode` — for anything else, query live `$metadata`.

   ```
   GET /b1s/v1/PurchaseTaxInvoices?$select=DocEntry,DocNum,CardCode,DocType&$filter=DocEntry ge 123&$top=20
   ```
   ```
   sapb1 query PurchaseTaxInvoices --select "DocEntry,DocNum,CardCode,DocType" --filter "DocEntry ge 123" --top 20
   ```

---

## Notes

- **`DocType`** on the document entities is an enum (`dDocument_Items` vs `dDocument_Service`), so it is safe to `$select` but filter on it with quoted enum values only if you know them; the reference does not enumerate them here.
- **`RequriedDate`** is spelled exactly that way in SAP's reference (a long-standing SAP typo for "Required date") — use the misspelling as-is.
- The `*/Close`, `*/Cancel`, `*/Reopen`, and `*/CreateCancellationDocument` actions are document-lifecycle transitions; the corresponding `*Service` object adds approval-workflow (`GetApprovalTemplates`/`HandleApprovalRequest`) and, for delivery/return/invoice/credit-note docs, a `Cancel2` that lets you edit fields before cancelling.
