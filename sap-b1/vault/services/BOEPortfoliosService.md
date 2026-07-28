---
entity: BOEPortfoliosService
domain: banking-payments
readable: false
methods: ["BOEPortfoliosService_GetBOEPortfolioList"]
rows_oil: null
---
# BOEPortfoliosService
RPC helper that lists bill-of-exchange portfolios (groupings of BOEs by bank/status).
## Operations
- `BOEPortfoliosService_GetBOEPortfolioList`

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity set: query [[BOEPortfolios]] directly. Browse this service's operations with `./sapb1 ops BOEPortfoliosService`.
## Connections
- Domain: [[banking-payments]]
- [[BOEPortfolios]] — the entity set holding the portfolio definitions (query this instead)
