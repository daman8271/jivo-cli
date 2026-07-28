---
entity: SalesForecast
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 23
---
# SalesForecast
Sales forecasts of item quantities per period feeding MRP planning; 23 forecasts defined. Live rows in JIVO_OIL_HANADB: 23.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SalesForecast --top 5
./sapb1 query SalesForecast --count
./sapb1 query SalesForecast --select "ForecastCode,ForecastName,ForecastStartDate,ForecastEndDate" --top 10
# Forecasts whose horizon is still current or future:
./sapb1 query SalesForecast --filter "ForecastEndDate ge '2026-07-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| ForecastCode | Forecast code (key) |
| ForecastName | Forecast description |
| ForecastStartDate | Horizon start date |
| ForecastEndDate | Horizon end date |
| Numerator | Internal numeric key |
| SalesForecastLines | Item/period quantity lines |

## Connections
- Domain: [[sales-ar]]
- [[Items]] via SalesForecastLines.ItemNo
- [[Warehouses]] via SalesForecastLines.Warehouse
