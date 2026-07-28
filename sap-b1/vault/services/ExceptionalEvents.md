---
entity: ExceptionalEvents
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# ExceptionalEvents
Catalog of exceptional demand events (promotions, one-off spikes) used to flag anomalies in sales forecasting. Live rows in JIVO_OIL_HANADB: 0 — forecasting anomalies are not catalogued here.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ExceptionalEvents --top 5
./sapb1 query ExceptionalEvents --count
./sapb1 query ExceptionalEvents --select "Code,Description" --top 10
# Look for promotion-type events (if any get defined):
./sapb1 query ExceptionalEvents --filter "contains(Description,'promo')" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Event code key |
| Description | Event description text |

## Connections
- Domain: [[system-other-1]]
- [[SalesForecast]] via exceptional-event code — forecast rows can be flagged with an event to explain demand spikes (recon lists this relation as "Forecasts"; the catalog service is SalesForecast)
