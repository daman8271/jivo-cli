# SAP Business One Service Layer — Banking & Payments

Reference for the **Banking & Payments** domain of the SAP Business One Service Layer (38 services). Covers incoming/outgoing payments, drafts, deposits, down payments, checks, bills of exchange (BOE), bank master data, and the supporting code lists and helper action-services.

Grounded against `catalog/services.json` (exact operations) and `raw/service-layer-api-reference.html` (descriptions + real field names from the reference's own `$select` / payload examples). Where the HTML gives no functional description, the purpose is marked **(inferred)** from the service/operation name. Fields shown are only those that appear verbatim in the HTML examples; anything else should be read from the live `$metadata`.

Two kinds of service appear here:

- **readable ENTITY** — a CRUD resource with a `GET` collection you can query with OData (`$select`, `$filter`, `$orderby`, `$top`, `$skip`). 24 of these.
- **function/action Service** — a helper endpoint with no `GET`; you `POST` a payload to invoke a named method. 14 of these.

Examples use the tool shape:

```
GET /b1s/v1/IncomingPayments?$select=DocNum,DocType,CardCode&$top=20&$filter=DocType eq 'rCustomer'
sapb1 query IncomingPayments --select DocNum,DocType,CardCode --filter "DocType eq 'rCustomer'" --top 20
```

---

## IncomingPayments

- **Purpose:** Incoming payments received from customers (or from vendors for returned goods). Payment means: cash, credit cards, checks, bank transfers, and in some localizations bills of exchange.
- **Type:** readable ENTITY
- **Operations:**
  - GET `IncomingPayments(id)`
  - GET `IncomingPayments`
  - POST `IncomingPayments`
  - PATCH `IncomingPayments(id)`
  - POST `IncomingPayments(id)/Cancel`
  - POST `IncomingPayments(id)/GetApprovalTemplates`
  - POST `IncomingPayments(id)/CancelbyCurrentSystemDate`
  - POST `IncomingPayments(id)/RequestApproveCancellation`
- **Fields (real, from HTML):** `DocNum`, `DocType`, `HandWritten`
- **Example:**
  ```
  GET /b1s/v1/IncomingPayments?$select=DocNum,DocType,HandWritten&$top=20&$filter=DocNum ge 100
  sapb1 query IncomingPayments --select DocNum,DocType,HandWritten --filter "DocNum ge 100" --top 20
  ```

---

## VendorPayments

- **Purpose:** Outgoing payments made to vendors (or to customers for returned goods). Payment means: cash, credit cards, checks, bank transfers, and in some localizations bills of exchange.
- **Type:** readable ENTITY
- **Operations:**
  - GET `VendorPayments(id)`
  - GET `VendorPayments`
  - POST `VendorPayments`
  - PATCH `VendorPayments(id)`
  - POST `VendorPayments(id)/Cancel`
  - POST `VendorPayments(id)/GetApprovalTemplates`
  - POST `VendorPayments(id)/CancelbyCurrentSystemDate`
- **Fields (real, from HTML):** `DocNum`, `DocType`, `HandWritten`
- **Example:**
  ```
  GET /b1s/v1/VendorPayments?$select=DocNum,DocType,HandWritten&$top=20&$filter=DocNum ge 100
  sapb1 query VendorPayments --select DocNum,DocType,HandWritten --filter "DocNum ge 100" --top 20
  ```

---

## PaymentDrafts

- **Purpose:** Draft payment documents (incoming/outgoing) held before they are posted to real payment documents.
- **Type:** readable ENTITY
- **Operations:**
  - GET `PaymentDrafts(id)`
  - GET `PaymentDrafts`
  - POST `PaymentDrafts`
  - PATCH `PaymentDrafts(id)`
  - DELETE `PaymentDrafts(id)`
  - POST `PaymentDrafts(id)/Cancel`
  - POST `PaymentDrafts(id)/SaveDraftToDocument`
  - POST `PaymentDrafts(id)/GetApprovalTemplates`
  - POST `PaymentDrafts(id)/CancelbyCurrentSystemDate`
- **Fields (real, from HTML):** `DocNum`, `DocType`, `HandWritten`
- **Example:**
  ```
  GET /b1s/v1/PaymentDrafts?$select=DocNum,DocType,HandWritten&$top=20
  sapb1 query PaymentDrafts --select DocNum,DocType,HandWritten --top 20
  ```

---

## Deposits

- **Purpose:** Bank deposits (grouping checks/cash/credit-card receipts for deposit into a bank account).
- **Type:** readable ENTITY
- **Operations:**
  - GET `Deposits(id)`
  - GET `Deposits`
  - POST `Deposits`
  - PATCH `Deposits(id)`
  - POST `Deposits(id)/CancelDeposit`
  - POST `Deposits(id)/CancelDepositbyCurrentSystemDate`
- **Fields (real, from HTML):** `DepositNumber`, `AbsEntry`, `DepositType`
- **Example:**
  ```
  GET /b1s/v1/Deposits?$select=DepositNumber,AbsEntry,DepositType&$top=20
  sapb1 query Deposits --select DepositNumber,AbsEntry,DepositType --top 20
  ```

---

## DownPayments

- **Purpose:** Customer down-payment documents — a document ensuring a customer is committed to and will follow through with a placed order.
- **Type:** readable ENTITY
- **Operations:**
  - GET `DownPayments(id)`
  - GET `DownPayments`
  - POST `DownPayments`
  - PATCH `DownPayments(id)`
  - DELETE `DownPayments(id)`
  - POST `DownPayments(id)/Close`
  - POST `DownPayments(id)/Cancel`
  - POST `DownPayments(id)/Reopen`
  - POST `DownPayments(id)/CreateCancellationDocument`
- **Fields (real, from HTML):** `DocEntry`, `DocNum`, `DocType`
- **Example:**
  ```
  GET /b1s/v1/DownPayments?$select=DocEntry,DocNum,DocType&$top=20&$filter=DocNum ge 100
  sapb1 query DownPayments --select DocEntry,DocNum,DocType --filter "DocNum ge 100" --top 20
  ```

---

## PurchaseDownPayments

- **Purpose:** Purchase (vendor) down-payment documents — a document ensuring commitment to a placed order.
- **Type:** readable ENTITY
- **Operations:**
  - GET `PurchaseDownPayments(id)`
  - GET `PurchaseDownPayments`
  - POST `PurchaseDownPayments`
  - PATCH `PurchaseDownPayments(id)`
  - DELETE `PurchaseDownPayments(id)`
  - POST `PurchaseDownPayments(id)/Close`
  - POST `PurchaseDownPayments(id)/Cancel`
  - POST `PurchaseDownPayments(id)/Reopen`
  - POST `PurchaseDownPayments(id)/CreateCancellationDocument`
- **Fields (real, from HTML):** `DocEntry`, `DocNum`, `DocType`
- **Example:**
  ```
  GET /b1s/v1/PurchaseDownPayments?$select=DocEntry,DocNum,DocType&$top=20
  sapb1 query PurchaseDownPayments --select DocEntry,DocNum,DocType --top 20
  ```

---

## ChecksforPayment

- **Purpose:** Checks payable that are not tied to a document (standalone outgoing checks).
- **Type:** readable ENTITY
- **Operations:**
  - GET `ChecksforPayment(id)`
  - GET `ChecksforPayment`
  - POST `ChecksforPayment`
  - PATCH `ChecksforPayment(id)`
- **Fields (real, from HTML):** `CheckKey`, `CheckNumber`, `BankCode`
- **Example:**
  ```
  GET /b1s/v1/ChecksforPayment?$select=CheckKey,CheckNumber,BankCode&$top=20
  sapb1 query ChecksforPayment --select CheckKey,CheckNumber,BankCode --top 20
  ```

---

## BankStatements

- **Purpose:** Bank statements used in the Bank Statement Processing / reconciliation flow.
- **Type:** readable ENTITY
- **Operations:**
  - GET `BankStatements(id)`
  - GET `BankStatements`
  - POST `BankStatements`
  - PATCH `BankStatements(id)`
  - DELETE `BankStatements(id)`
- **Fields (real, from HTML):** `InternalNumber`, `BankAccountKey`, `StatementNumber`
- **Example:**
  ```
  GET /b1s/v1/BankStatements?$select=InternalNumber,BankAccountKey,StatementNumber&$top=20
  sapb1 query BankStatements --select InternalNumber,BankAccountKey,StatementNumber --top 20
  ```

---

## BankPages

- **Purpose:** External bank statement lines/pages in the Banking module.
- **Type:** readable ENTITY
- **Operations:**
  - GET `BankPages(id)`
  - GET `BankPages`
  - POST `BankPages`
  - PATCH `BankPages(id)`
  - DELETE `BankPages(id)`
- **Fields (real, from HTML):** `AccountCode`, `Sequence`, `AccountName`
- **Example:**
  ```
  GET /b1s/v1/BankPages?$select=AccountCode,Sequence,AccountName&$top=20
  sapb1 query BankPages --select AccountCode,Sequence,AccountName --top 20
  ```

---

## Banks

- **Purpose:** Bank master data (the banks known to the company).
- **Type:** readable ENTITY
- **Operations:**
  - GET `Banks(id)`
  - GET `Banks`
  - POST `Banks`
  - PATCH `Banks(id)`
  - DELETE `Banks(id)`
- **Fields (real, from HTML):** `BankCode`, `BankName`, `AccountforOutgoingChecks`
- **Example:**
  ```
  GET /b1s/v1/Banks?$select=BankCode,BankName,AccountforOutgoingChecks&$top=20
  sapb1 query Banks --select BankCode,BankName,AccountforOutgoingChecks --top 20
  ```

---

## HouseBankAccounts

- **Purpose:** The company's own ("house") bank accounts used for making and receiving payments.
- **Type:** readable ENTITY
- **Operations:**
  - GET `HouseBankAccounts(id)`
  - GET `HouseBankAccounts`
  - POST `HouseBankAccounts`
  - PATCH `HouseBankAccounts(id)`
  - DELETE `HouseBankAccounts(id)`
- **Fields (real, from HTML):** `BankCode`, `AccNo`, `Branch`
- **Example:**
  ```
  GET /b1s/v1/HouseBankAccounts?$select=BankCode,AccNo,Branch&$top=20
  sapb1 query HouseBankAccounts --select BankCode,AccNo,Branch --top 20
  ```

---

## CreditCards

- **Purpose:** Credit cards the company can use for incoming and outgoing payments.
- **Type:** readable ENTITY
- **Operations:**
  - GET `CreditCards(id)`
  - GET `CreditCards`
  - POST `CreditCards`
  - PATCH `CreditCards(id)`
  - DELETE `CreditCards(id)`
- **Fields (real, from HTML):** `CreditCardCode`, `CreditCardName`, `GLAccount`
- **Example:**
  ```
  GET /b1s/v1/CreditCards?$select=CreditCardCode,CreditCardName,GLAccount&$top=20
  sapb1 query CreditCards --select CreditCardCode,CreditCardName,GLAccount --top 20
  ```

---

## CreditCardPayments

- **Purpose:** Credit-card payment due-date definitions — the dates on which the credit card company credits the cardholder.
- **Type:** readable ENTITY
- **Operations:**
  - GET `CreditCardPayments(id)`
  - GET `CreditCardPayments`
  - POST `CreditCardPayments`
  - PATCH `CreditCardPayments(id)`
  - DELETE `CreditCardPayments(id)`
- **Fields (real, from HTML):** `DueDateCode`, `DueDateName`, `DueDatesType`
- **Example:**
  ```
  GET /b1s/v1/CreditCardPayments?$select=DueDateCode,DueDateName,DueDatesType&$top=20
  sapb1 query CreditCardPayments --select DueDateCode,DueDateName,DueDatesType --top 20
  ```

---

## CreditPaymentMethods

- **Purpose:** Credit-card payment methods.
- **Type:** readable ENTITY
- **Operations:**
  - GET `CreditPaymentMethods(id)`
  - GET `CreditPaymentMethods`
  - POST `CreditPaymentMethods`
  - PATCH `CreditPaymentMethods(id)`
  - DELETE `CreditPaymentMethods(id)`
- **Fields (real, from HTML):** `PaymentMethodCode`, `Name`, `AssignedtoCreditCard`
- **Example:**
  ```
  GET /b1s/v1/CreditPaymentMethods?$select=PaymentMethodCode,Name,AssignedtoCreditCard&$top=20
  sapb1 query CreditPaymentMethods --select PaymentMethodCode,Name,AssignedtoCreditCard --top 20
  ```

---

## WizardPaymentMethods

- **Purpose:** Payment methods (check, bank transfer, and in some localizations bills of exchange) usable in Payment Wizard runs.
- **Type:** readable ENTITY
- **Operations:**
  - GET `WizardPaymentMethods(id)`
  - GET `WizardPaymentMethods`
  - POST `WizardPaymentMethods`
  - PATCH `WizardPaymentMethods(id)`
  - DELETE `WizardPaymentMethods(id)`
- **Fields (real, from HTML):** `PaymentMethodCode`, `Description`, `Type`
- **Example:**
  ```
  GET /b1s/v1/WizardPaymentMethods?$select=PaymentMethodCode,Description,Type&$top=20
  sapb1 query WizardPaymentMethods --select PaymentMethodCode,Description,Type --top 20
  ```

---

## PaymentRunExport

- **Purpose:** Export of automatic-payment run data for both incoming and outgoing (vendor) payments. Read-only.
- **Type:** readable ENTITY (read-only — GET only)
- **Operations:**
  - GET `PaymentRunExport(id)`
  - GET `PaymentRunExport`
- **Fields (real, from HTML):** `AbsoluteEntry`, `RunDate`, `VendorNum`
- **Example:**
  ```
  GET /b1s/v1/PaymentRunExport?$select=AbsoluteEntry,RunDate,VendorNum&$top=20
  sapb1 query PaymentRunExport --select AbsoluteEntry,RunDate,VendorNum --top 20
  ```

---

## PaymentBlocks

- **Purpose:** Payment block codes (reasons to hold/block a payment).
- **Type:** readable ENTITY
- **Operations:**
  - GET `PaymentBlocks(id)`
  - GET `PaymentBlocks`
  - POST `PaymentBlocks`
  - PATCH `PaymentBlocks(id)`
  - DELETE `PaymentBlocks(id)`
- **Fields (real, from HTML):** `AbsEntry`, `PaymentBlockCode`
- **Example:**
  ```
  GET /b1s/v1/PaymentBlocks?$select=AbsEntry,PaymentBlockCode&$top=20
  sapb1 query PaymentBlocks --select AbsEntry,PaymentBlockCode --top 20
  ```

---

## PaymentReasonCodes

- **Purpose:** Payment reason codes (code list used to classify payments).
- **Type:** readable ENTITY
- **Operations:**
  - GET `PaymentReasonCodes(id)`
  - GET `PaymentReasonCodes`
  - POST `PaymentReasonCodes`
  - PATCH `PaymentReasonCodes(id)`
  - DELETE `PaymentReasonCodes(id)`
- **Fields (real, from HTML):** `Code` (additional fields: query live `$metadata`)
- **Example:**
  ```
  GET /b1s/v1/PaymentReasonCodes?$select=Code&$top=20
  sapb1 query PaymentReasonCodes --select Code --top 20
  ```

---

## PaymentTermsTypes

- **Purpose:** Payment-terms types in the Banking module — the standing agreements that apply to transactions with customers and vendors.
- **Type:** readable ENTITY
- **Operations:**
  - GET `PaymentTermsTypes(id)`
  - GET `PaymentTermsTypes`
  - POST `PaymentTermsTypes`
  - PATCH `PaymentTermsTypes(id)`
  - DELETE `PaymentTermsTypes(id)`
- **Fields (real, from HTML):** `GroupNumber`, `PaymentTermsGroupName`, `StartFrom`
- **Example:**
  ```
  GET /b1s/v1/PaymentTermsTypes?$select=GroupNumber,PaymentTermsGroupName,StartFrom&$top=20
  sapb1 query PaymentTermsTypes --select GroupNumber,PaymentTermsGroupName,StartFrom --top 20
  ```

---

## BankChargesAllocationCodes

- **Purpose:** Bank-charges allocation codes (map bank charges to accounts).
- **Type:** readable ENTITY
- **Operations:**
  - GET `BankChargesAllocationCodes(id)`
  - GET `BankChargesAllocationCodes`
  - POST `BankChargesAllocationCodes`
  - PATCH `BankChargesAllocationCodes(id)`
  - DELETE `BankChargesAllocationCodes(id)`
  - POST `BankChargesAllocationCodes(id)/SetDefaultBankChargesAllocationCode`
- **Fields (real, from HTML):** `Code`, `Description`
- **Example:**
  ```
  GET /b1s/v1/BankChargesAllocationCodes?$select=Code,Description&$top=20
  sapb1 query BankChargesAllocationCodes --select Code,Description --top 20
  ```

---

## BillOfExchangeTransactions

- **Purpose:** Bill-of-exchange (BOE) transactions — records of status transitions on bills of exchange.
- **Type:** readable ENTITY
- **Operations:**
  - GET `BillOfExchangeTransactions(id)`
  - GET `BillOfExchangeTransactions`
  - POST `BillOfExchangeTransactions`
- **Fields (real, from HTML):** `StatusFrom`, `StatusTo`, `TransactionDate`
- **Example:**
  ```
  GET /b1s/v1/BillOfExchangeTransactions?$select=StatusFrom,StatusTo,TransactionDate&$top=20
  sapb1 query BillOfExchangeTransactions --select StatusFrom,StatusTo,TransactionDate --top 20
  ```

---

## BOEDocumentTypes

- **Purpose:** Bill-of-exchange document types (code list).
- **Type:** readable ENTITY
- **Operations:**
  - GET `BOEDocumentTypes(id)`
  - GET `BOEDocumentTypes`
  - POST `BOEDocumentTypes`
  - PATCH `BOEDocumentTypes(id)`
  - DELETE `BOEDocumentTypes(id)`
- **Fields (real, from HTML):** `DocEntry`, `DocType`, `DocDescription`
- **Example:**
  ```
  GET /b1s/v1/BOEDocumentTypes?$select=DocEntry,DocType,DocDescription&$top=20
  sapb1 query BOEDocumentTypes --select DocEntry,DocType,DocDescription --top 20
  ```

---

## BOEInstructions

- **Purpose:** Bill-of-exchange instructions (code list of BOE handling instructions).
- **Type:** readable ENTITY
- **Operations:**
  - GET `BOEInstructions(id)`
  - GET `BOEInstructions`
  - POST `BOEInstructions`
  - PATCH `BOEInstructions(id)`
  - DELETE `BOEInstructions(id)`
- **Fields (real, from HTML):** `InstructionEntry`, `InstructionCode`, `InstructionDesc`
- **Example:**
  ```
  GET /b1s/v1/BOEInstructions?$select=InstructionEntry,InstructionCode,InstructionDesc&$top=20
  sapb1 query BOEInstructions --select InstructionEntry,InstructionCode,InstructionDesc --top 20
  ```

---

## BOEPortfolios

- **Purpose:** Bill-of-exchange portfolios (groupings of bills of exchange).
- **Type:** readable ENTITY
- **Operations:**
  - GET `BOEPortfolios(id)`
  - GET `BOEPortfolios`
  - POST `BOEPortfolios`
  - PATCH `BOEPortfolios(id)`
  - DELETE `BOEPortfolios(id)`
- **Fields (real, from HTML):** `PortfolioEntry`, `PortfolioID`, `PortfolioCode`
- **Example:**
  ```
  GET /b1s/v1/BOEPortfolios?$select=PortfolioEntry,PortfolioID,PortfolioCode&$top=20
  sapb1 query BOEPortfolios --select PortfolioEntry,PortfolioID,PortfolioCode --top 20
  ```

---

## BankChargesAllocationCodesService

- **Purpose:** Helper service to list bank-charges allocation codes. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `BankChargesAllocationCodesService_GetBankChargesAllocationCodeList`

---

## BankStatementsService

- **Purpose:** Helper service to list bank statements. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `BankStatementsService_GetBankStatementList`

---

## BOEDocumentTypesService

- **Purpose:** Helper service to list bill-of-exchange document types. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `BOEDocumentTypesService_GetBOEDocumentTypeList`

---

## BOEInstructionsService

- **Purpose:** Helper service to list bill-of-exchange instructions. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `BOEInstructionsService_GetBOEInstructionList`

---

## BOELinesService

- **Purpose:** Helper service to retrieve a single bill-of-exchange line. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `BOELinesService_GetBOELine`

---

## BOEPortfoliosService

- **Purpose:** Helper service to list bill-of-exchange portfolios. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `BOEPortfoliosService_GetBOEPortfolioList`

---

## CheckLinesService

- **Purpose:** Helper service to retrieve a check line and to list valid check lines. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `CheckLinesService_GetCheckLine`
  - POST `CheckLinesService_GetValidCheckLineList`

---

## DepositsService

- **Purpose:** Helper service for deposits — list deposits, and cancel a check row within a deposit (payload `CancelCheckRowParams`), either by document date or by the current system date. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `DepositsService_GetDepositList`
  - POST `DepositsService_CancelCheckRow`
  - POST `DepositsService_CancelCheckRowbyCurrentSystemDate`

---

## DownPaymentsService

- **Purpose:** Approval-workflow helper for customer down-payment documents — fetch applicable approval templates and handle an approval request. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `DownPaymentsService_GetApprovalTemplates`
  - POST `DownPaymentsService_HandleApprovalRequest`

---

## PurchaseDownPaymentsService

- **Purpose:** Approval-workflow helper for purchase (vendor) down-payment documents — fetch applicable approval templates and handle an approval request. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `PurchaseDownPaymentsService_GetApprovalTemplates`
  - POST `PurchaseDownPaymentsService_HandleApprovalRequest`

---

## PaymentBlocksService

- **Purpose:** Helper service to list payment block codes. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `PaymentBlocksService_GetPaymentBlockList`

---

## PaymentCalculationService

- **Purpose:** Helper service to calculate a payment amount. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `PaymentCalculationService_GetPaymentAmount`

---

## PaymentReasonCodeService

- **Purpose:** Helper service to list payment reason codes. (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `PaymentReasonCodeService_GetPaymentReasonCodeList`

---

## PaymentTermsTypesService

- **Purpose:** Helper service to update a payment-terms type together with its linked business partners (payload `PaymentTermsType`). (inferred)
- **Type:** function/action Service
- **Operations:**
  - POST `PaymentTermsTypesService_UpdateWithBPs`
