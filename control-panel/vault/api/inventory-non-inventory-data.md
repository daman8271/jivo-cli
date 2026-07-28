---
endpoint: /inventory/non-inventory/api/data/
method: GET
auth: session + XHR header (X-Requested-With) + X-CSRFToken
readonly: true
used_by: [non-moving-stock]
tags: [jivo, api, inventory, ageing]
---
# `GET /inventory/non-inventory/api/data/`

## Purpose
Returns every finished-good currently in stock with its **ageing / movement signals** — how long it has sat (`DaysInStock`), when it was last billed (`DaysSinceBilled` / `DaysSinceMoved`), last customer, and current qty/litres/boxes/value — so the [[non-moving-stock]] page can list **slow-moving / dead stock**. The page's "not moved ≥ N days" threshold (default 60) is applied **client-side** on `DaysSinceMoved`; the API always returns the full item list.

## Request
| Param | Type | Meaning |
|---|---|---|
| `schema` | `jivo_oil` \| `jivo_mart` \| `jivo_beverages` | Company DB. **Default `jivo_oil`**. Toggled by the company segment. |

No date param.

## Response
HTTP 200 · `application/json`. Top key `data`:

| Key | Shape | Meaning |
|---|---|---|
| `items` | object[] | One row per in-stock finished good (111 for oil at probe). |
| `unit` | string | Headline unit — `litres` (oil) / boxes (beverages). |
| `schema` | string | Echo of requested schema. |
| `warehouses` | string[] | Finished-goods warehouses represented (e.g. `["BH-EC","BH-FG","BH-PF","GP-FG"]`). See [[warehouses]]. |

`items[]` row (key fields):

| Field | Type | Meaning |
|---|---|---|
| `ItemCode` / `ItemName` | string | SAP FG code + description. |
| `SubGroup` / `Variety` / `SKU` / `PremComm` | string | Classification (sub-group, variety, pack size, PREMIUM/COMMODITY). |
| `ProdDate` | date | Production/first-in date of the on-hand lot. |
| `DaysInStock` | int | Days since `ProdDate` (age of oldest lot). |
| `LastBillDate` | date | Last date this item was sold/billed. |
| `DaysSinceBilled` | int | Days since `LastBillDate` (ageing colour: >180 hot, >90 warm else cool). |
| `LastCustomer` / `LastCode` | string | Party name + SAP card code of the last buyer. |
| `LastQty` | number | Quantity on that last bill. |
| `DaysSinceMoved` | int | Days since last movement — **the field the "≥ N days" filter uses**. |
| `Qty` | number | On-hand physical units. |
| `Litres` / `Boxes` | number | On-hand converted to litres / boxes. |
| `Value` | number | On-hand stock value (₹, at cost/price). |
| `LitrePer` / `BoxPer` / `PricePer` | number | Per-unit conversion factors (litres per unit, units per box, price per unit). |
| `wh` | object | `{warehouse_code: qty}` where the stock physically sits. |

Trimmed sample:
```json
{"data":{"unit":"litres","schema":"jivo_oil","warehouses":["BH-EC","BH-FG","BH-PF","GP-FG"],
 "items":[{"ItemCode":"FG0000441","ItemName":"COLD PRESS GROUNDNUT 200 MLS 70 PCS - BH",
   "SubGroup":"GROUNDNUT","Variety":"COLD PRESS","SKU":"200 MLS","PremComm":"PREMIUM",
   "ProdDate":"2026-06-01","DaysInStock":52,"LastBillDate":"2026-07-09","DaysSinceBilled":14,
   "LastCustomer":"JIVO MART PVT LTD","LastCode":"CUSTA000606","LastQty":9590.0,"DaysSinceMoved":14,
   "Qty":23170.0,"Litres":4634.0,"Boxes":331.0,"Value":775087.0,
   "LitrePer":0.2,"BoxPer":70.0,"PricePer":33.4522,"wh":{"BH-PF":23170.0}}]}}
```

## Used by
- [[non-moving-stock]] — main ageing table + KPIs; row click drills via [[inventory-non-inventory-drill]].

## Notes
- Read-only live snapshot. The "non-moving" definition is purely the client-side `DaysSinceMoved ≥ moveDays` filter, not a server flag.
