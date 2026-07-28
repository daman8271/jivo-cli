---
entity: PaymentDrafts
domain: banking-payments
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1491
---
# PaymentDrafts
Draft incoming/outgoing payments awaiting approval or posting, convertible via SaveDraftToDocument. Live rows in JIVO_OIL_HANADB: 1491.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PaymentDrafts --top 5
./sapb1 query PaymentDrafts --count
./sapb1 query PaymentDrafts --select "DocNum,DocDate,CardName,AuthorizationStatus" --top 10
# drafts still pending approval
./sapb1 query PaymentDrafts --filter "AuthorizationStatus eq 'dasPending'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal key |
| DocNum | Draft number |
| DocDate | Posting date |
| DueDate | Due date |
| CardCode | Partner BP code |
| CardName | Partner name |
| DocType | Customer / vendor / account |
| DocObjectCode | Target document type |
| CashSum | Cash amount |
| BankCode | Bank code |
| BankAccount | Bank account |
| DocCurrency | Draft currency |
| AuthorizationStatus | Approval workflow status |
| Cancelled | Cancellation flag |
## Connections
- Domain: [[banking-payments]]
- [[IncomingPayments]] via DocObjectCode — drafts that post as customer receipts
- [[VendorPayments]] via DocObjectCode — drafts that post as vendor payments
- [[BusinessPartners]] via CardCode — the partner on the draft
- [[HouseBankAccounts]] via BankCode + BankAccount — the bank account used
- [[ApprovalRequests]] via AuthorizationStatus — the approval workflow gating the draft
