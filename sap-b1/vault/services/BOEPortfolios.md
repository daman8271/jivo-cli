---
entity: BOEPortfolios
domain: banking-payments
readable: true
methods: ["GET BOEPortfolios", "GET BOEPortfolios(id)", "POST BOEPortfolios", "PATCH BOEPortfolios(id)", "DELETE BOEPortfolios(id)"]
rows_oil: 0
---
# BOEPortfolios
Setup table of BOE portfolios grouping bills of exchange by bank and G/L account for collection/discounting. Empty in JIVO_OIL_HANADB; key fields inferred from schema. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BOEPortfolios --top 5
./sapb1 query BOEPortfolios --count
./sapb1 query BOEPortfolios --select "Code,Description,BankCode,AccountCode" --top 10
# Portfolios held at one bank:
./sapb1 query BOEPortfolios --filter "BankCode eq 'HDFC'"
```
## Key fields
| Field | Meaning |
|---|---|
| AbsoluteEntry | Internal numeric key |
| Code | Portfolio code |
| Description | Portfolio name |
| BankCode | Bank holding the portfolio |
| AccountCode | Linked G/L account |
## Connections
- Domain: [[banking-payments]]
- [[Banks]] via BankCode — bank the portfolio sits at
- [[ChartOfAccounts]] via AccountCode — G/L account for portfolio postings
- [[BillOfExchangeTransactions]] via PortfolioNumber — BOEs grouped in the portfolio
