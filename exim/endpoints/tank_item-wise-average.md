---
title: "EXIM endpoint — GET /tank/item-wise-average/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /tank/item-wise-average/
category: tank
kind: read
resource: tankdata/tankitem/tanklog
auth: bearer
---

# `GET /tank/item-wise-average/`

> Weighted average rate + matched qty for one tank item.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/tank/item-wise-average/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `item_code` |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "item_code": "RM00CN",
  "tank_total_capacity": 266500.0,
  "tank_total_capacity_kg": 292856.85,
  "quantity_matched": 266500.0,
  "quantity_matched_kg": 242515.24,
  "quantity_unmatched": 0.0,
  "average_rate(IN_TANK)": 125.55,
  "adjusted_average(STO)": 125.55,
  "average_rate_kg(IN_TANK)": 114.25,
  "adjusted_average_kg(STO)": 137.97,
  "breakdown": [
    {
      "stock_id": 320,
      "created_at": "2026-04-18T08:15:46.496624Z",
      "party": "ALBA EDIBLE OILS PTY LTD",
      "vehicle": "RJ47GA1756",
      "transporter": "N/A",
      "rate_in_litres": 121.94,
      "rate_in_kg": 134.0,
      "batch_quantity": 20651.63,
      "batch_quantity_kg": 18793.0,
      "quantity_consumed": 20651.63,
      "quantity_consumed_kg": 18793.0,
      "batch_total": 2518259.76,
      "batch_total_kg": 2518262.28
    },
    {
      "stock_id": 321,
      "created_at": "2026-04-18T08:16:56.892194Z",
      "party": "ALBA EDIBLE OILS PTY LTD",
      "vehicle": "RJ47GA1756",
      "transporter": "N/A",
      "rate_in_litres": 121.94,
      "rate_in_kg": 134.0,
      "batch_quantity": 25678.0,
      "batch_quantity_kg": 23367.0,
      "quantity_consumed": 25678.0,
      "quantity_consumed_kg": 23367.0,
      "batch_total": 3131175.32,
      "batch_total_kg": 3131178.45
    },
    "...(+5 more of 7)"
  ],
  "warning": null
}
```

## Field reference

- `item_code` — tank item queried (from the `item_code` query param, e.g. `RM00CN`).
- `tank_total_capacity` / `tank_total_capacity_kg` — current in-tank quantity for this item in litres and KG.
- `quantity_matched` / `quantity_matched_kg` — litres/KG of the in-tank quantity that could be matched to inward stock batches for costing.
- `quantity_unmatched` — litres left over that no batch covers (0 here; a non-zero value usually triggers `warning`).
- `average_rate(IN_TANK)` — weighted average purchase rate of the matched in-tank stock, ₹/litre.
- `adjusted_average(STO)` — the same average after stock-transfer-order adjustments, ₹/litre.
- `average_rate_kg(IN_TANK)` / `adjusted_average_kg(STO)` — the two averages expressed in ₹/KG.
- `breakdown[]` — per-batch FIFO matching detail:
  - `stock_id` — linked stock record id.
  - `created_at` — batch inward timestamp (ISO 8601 UTC).
  - `party` / `vehicle` / `transporter` — supplier, tanker number, transporter for the batch.
  - `rate_in_litres` / `rate_in_kg` — batch purchase rate, ₹/litre and ₹/KG.
  - `batch_quantity` / `batch_quantity_kg` — batch size in litres/KG.
  - `quantity_consumed` / `quantity_consumed_kg` — how much of the batch counts toward the in-tank quantity.
  - `batch_total` / `batch_total_kg` — batch value in ₹ (rate × quantity, on the litre and KG basis).
- `warning` — data-quality note (e.g. unmatched quantity); null when matching is clean.

## Used by pages

- [[pages/in-tank-breakdown|In Tank Breakdown]]
- [[pages/tank-monitoring|Tank Monitoring]]

## Related endpoints

- [[endpoints/tank|`GET /tank/`]]
- [[endpoints/tank_capacity-insights|`GET /tank/capacity-insights/`]]
- [[endpoints/tank_in-tank-items|`GET /tank/in-tank-items/`]]
- [[endpoints/tank_item-wise-summary|`GET /tank/item-wise-summary/`]]
- [[endpoints/tank_items|`GET /tank/items/`]]
- [[endpoints/tank_log|`GET /tank/log/`]]
- [[endpoints/tank_tank-summary|`GET /tank/tank-summary/`]]
- [[endpoints/tank_tank_code|`GET /tank/{tank_code}/`]]

## Notes

- Kind: **read**. Resource permission group: `tankdata/tankitem/tanklog`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
