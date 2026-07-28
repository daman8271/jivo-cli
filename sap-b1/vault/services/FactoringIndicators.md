---
entity: FactoringIndicators
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# FactoringIndicators
Localization lookup marking receivables sold to a factoring company on invoices/BPs. Live rows in JIVO_OIL_HANADB: 0 — no factoring arrangements are modelled.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query FactoringIndicators --top 5
./sapb1 query FactoringIndicators --count
./sapb1 query FactoringIndicators --select "Code,Description" --top 10
# Look up one indicator by its code (if any get defined):
./sapb1 query FactoringIndicators --filter "Code eq 'F1'" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Indicator code key |
| Description | Indicator description text |

## Connections
- Domain: [[system-other-1]]
- [[BusinessPartners]] via FactoringIndicator — default indicator set on the BP payment terms
- [[Invoices]] via FactoringIndicator — per-document flag that the receivable is factored
