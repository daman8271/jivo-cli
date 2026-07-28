---
entity: BillOfExchangeTransactions
domain: banking-payments
readable: true
methods: ["GET BillOfExchangeTransactions", "GET BillOfExchangeTransactions(id)", "POST BillOfExchangeTransactions"]
rows_oil: 0
---
# BillOfExchangeTransactions
Bill-of-exchange transactions (drafts/promissory notes) tracking BOE lifecycle from generation to collection. Empty in JIVO_OIL_HANADB — BOE functionality unused; key fields inferred from schema. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BillOfExchangeTransactions --top 5
./sapb1 query BillOfExchangeTransactions --count
./sapb1 query BillOfExchangeTransactions --select "BoeNumber,CardCode,BoeStatus,DueDate,Amount" --top 10
# BOEs maturing by year-end:
./sapb1 query BillOfExchangeTransactions --filter "DueDate le '2026-12-31'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| BoeKey | Internal BOE key |
| BoeNumber | BOE document number |
| CardCode | Business partner code |
| BoeStatus | Lifecycle status |
| BoeType | Incoming or outgoing |
| DueDate | Maturity date |
| Amount | BOE amount |
| Currency | BOE currency |
| BankCode | Handling bank |
| PortfolioNumber | Portfolio grouping number |
## Connections
- Domain: [[banking-payments]]
- [[BusinessPartners]] via CardCode — drawee/drawer partner
- [[Banks]] via BankCode — bank handling the BOE
- [[BOEPortfolios]] via PortfolioNumber — portfolio grouping the BOE
- [[Currencies]] via Currency — BOE currency
