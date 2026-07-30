---
title: Orders
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, seller, orders]
status: studied
read_only: true
---

# Orders

**Portal:** Seller Central (3P) · **Section:** `seller/Orders` · **Endpoints catalogued:** 7 (6 read-safe, 6 PROVEN live · 0 out-of-scope · 1 unknown/telemetry)

The 3P marketplace order book — Manage Orders (orders-v3). Server-side search over the order table with quick-filters (fulfilment type, order status, ship-by, program), notifications, and table-prefs. Order counts come from a POST endpoint (countOrders) held out of scope.

## What it looks like (live, this run)

![04 orders v3](../seller/sec-04-orders-v3.png)

*Captured live from JIVO Mart's Seller Central session, seller/sec-04-orders-v3.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /orders-api/adConfig | 2 | READ |
| ✅ | GET | sellercentral.amazon.in · /orders-api/manifest-v3 | — | READ |
| ✅ | GET | sellercentral.amazon.in · /orders-api/manifest-v3/quick-filters | — | READ |
| ✅ | GET | sellercentral.amazon.in · /orders-api/notifications/MYO_LIST_ORDERS_EASYSHIP | 1 | READ |
| ✅ | GET | sellercentral.amazon.in · /orders-api/prefs/table-content | 4 | READ |
| ✅ | GET | sellercentral.amazon.in · /orders-api/search | 10 | READ |

## Response shapes (full field lists, from live capture)

- **`/orders-api/adConfig`** (2 fields): `adMetadataList`, `display`
- **`/orders-api/notifications/MYO_LIST_ORDERS_EASYSHIP`** (1 fields): `notifications`
- **`/orders-api/prefs/table-content`** (4 fields): `columns`, `columns.attributes`, `columns.columns`, `columns.id`
- **`/orders-api/search`** (10 fields): `appliedSearchFilters`, `appliedSearchFilters.key`, `appliedSearchFilters.selectedValues`, `debugInfo`, `exceptions`, `featureList`, `offset`, `orders`, `requestId`, `total`

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

_None catalogued in this section._

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| ? | sellercentral.amazon.in · /gp/orders-v2/search | UNKNOWN |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

