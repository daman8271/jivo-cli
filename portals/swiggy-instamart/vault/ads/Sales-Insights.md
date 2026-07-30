---
title: Sales Insights
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, ads, ads]
status: studied
---


# Sales Insights

> City / product / category sales analytics — 47 metrics, 17 dimensions.

**Sales Insights** (`/instamart/sales-insights`) is the analytical counterpart to
the sales xlsx, and it is the single biggest unexploited surface in this study.
Two endpoints drive it: `sales/filters` returns the queryable vocabularies and
`sales/metric` returns the numbers.

Live for **Jivo Wellness**, default window 2026-07-23 → 2026-07-29:

- **132 city rows**, each with `currentValue`, `priorValue`, a percentage delta
  and lat/lng/state metadata.
- **Total sales Rs 2,35,05,424** against a prior-period Rs 2,21,00,498 = **+6.36%**.
- Top cities: Hyderabad Rs 35.7 L · Bangalore Rs 29.1 L · Delhi Rs 27.3 L ·
  Mumbai Rs 25.5 L · Chennai Rs 11.3 L.

The full vocabulary available here is **47 metric types, 17 dimension types and
25 filter types** (enumerated in [[Swiggy-Instamart-Data-Inventory]]). JIVO's
automation requests exactly **two** of the 47 (`GMV`, `UNITS_SOLD`).

**Endpoints in this section:** 2 (2 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/sales/filters` | `GET_SALES_INSIGHTS_FILTER_OPTIONS` | **PROVEN LIVE 200** | call site .post() on GET_SALES_INSIGHTS_FILTER_OPTIONS | live: ['POST'] -> [200], 15111B |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/sales/metric` | `GET_SALES_INSIGHTS_METRICS` | **PROVEN LIVE 200** | call site .post() on GET_SALES_INSIGHTS_METRICS | live: ['POST'] -> [200], 54214B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- **The default window is 7 days.** Every number on first render is a
  week-to-date figure. Any quoted total must state its window.
- The feature flag `REPORTS_NEW_UI_35_DAYS_WINDOW_ENFORCEMENT_FULL_ROLLOUT` is
  currently **false**, so the 35-day cap is not being enforced on this account —
  but it exists and can be switched on.
- `hasSalesInWindow` on each filter option tells you whether that city/product
  actually transacted in the window — the difference between "listed" and
  "selling".

## Screenshots (live read-only walk, 2026-07-30)

- `sec-23-instamart.png`

  ![screenshot](../captures/walk1/sec-23-instamart.png)
- `sec-22-instamart-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-22-instamart-Jivo-Mart-Pvt-Ltd-.png)
- `sec-23-instamart-sales-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-23-instamart-sales-Jivo-Mart-Pvt-Ltd-.png)
- `sec-24-instamart-sales-insights-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-24-instamart-sales-insights-Jivo-Mart-Pvt-Ltd-.png)
- `sec-25-instamart-reports-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-25-instamart-reports-Jivo-Mart-Pvt-Ltd-.png)
- `sec-26-instamart-bdpo-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-26-instamart-bdpo-Jivo-Mart-Pvt-Ltd-.png)
- `sec-27-instamart-campaign-list-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-27-instamart-campaign-list-Jivo-Mart-Pvt-Ltd-.png)
- `sec-28-instamart-ads-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-28-instamart-ads-Jivo-Mart-Pvt-Ltd-.png)
- `sec-29-instamart-advertisement-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-29-instamart-advertisement-Jivo-Mart-Pvt-Ltd-.png)
- `sec-31-instamart-npi-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-31-instamart-npi-Jivo-Mart-Pvt-Ltd-.png)
- `sec-42-instamart-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-42-instamart-Jivo-Wellness-.png)
- `sec-43-instamart-sales-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-43-instamart-sales-Jivo-Wellness-.png)
- `sec-45-instamart-reports-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-45-instamart-reports-Jivo-Wellness-.png)
- `sec-46-instamart-bdpo-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-46-instamart-bdpo-Jivo-Wellness-.png)
- `sec-47-instamart-campaign-list-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-47-instamart-campaign-list-Jivo-Wellness-.png)
- `sec-48-instamart-ads-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-48-instamart-ads-Jivo-Wellness-.png)
- `sec-62-instamart-Jivo-.png`

  ![screenshot](../captures/walk2/sec-62-instamart-Jivo-.png)
- `sec-63-instamart-sales-Jivo-.png`

  ![screenshot](../captures/walk2/sec-63-instamart-sales-Jivo-.png)
- `sec-65-instamart-reports-Jivo-.png`

  ![screenshot](../captures/walk2/sec-65-instamart-reports-Jivo-.png)
- `sec-66-instamart-bdpo-Jivo-.png`

  ![screenshot](../captures/walk2/sec-66-instamart-bdpo-Jivo-.png)
- `sec-67-instamart-campaign-list-Jivo-.png`

  ![screenshot](../captures/walk2/sec-67-instamart-campaign-list-Jivo-.png)
- `sec-68-instamart-ads-Jivo-.png`

  ![screenshot](../captures/walk2/sec-68-instamart-ads-Jivo-.png)
- `d17-instamart-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d17-instamart-Jivo-Mart-Pvt-Ltd-.png)
- `d18-instamart-sales-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d18-instamart-sales-Jivo-Mart-Pvt-Ltd-.png)
- `d19-instamart-sales-insights-Jivo-Mart-Pvt-Ltd--Category.png`

  ![screenshot](../captures/walk4/d19-instamart-sales-insights-Jivo-Mart-Pvt-Ltd--Category.png)
- `d20-instamart-reports-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d20-instamart-reports-Jivo-Mart-Pvt-Ltd-.png)
- `d21-instamart-bdpo-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d21-instamart-bdpo-Jivo-Mart-Pvt-Ltd-.png)
- `d22-instamart-campaign-list-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d22-instamart-campaign-list-Jivo-Mart-Pvt-Ltd-.png)
- `d23-instamart-ads-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d23-instamart-ads-Jivo-Mart-Pvt-Ltd-.png)
- `d25-instamart-npi-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d25-instamart-npi-Jivo-Mart-Pvt-Ltd-.png)
- `d36-instamart-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d36-instamart-Jivo-Wellness-.png)
- `d37-instamart-sales-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d37-instamart-sales-Jivo-Wellness-.png)
- `d38-instamart-sales-insights-Jivo-Wellness--Category.png`

  ![screenshot](../captures/walk4/d38-instamart-sales-insights-Jivo-Wellness--Category.png)
- `d39-instamart-reports-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d39-instamart-reports-Jivo-Wellness-.png)
- `d40-instamart-bdpo-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d40-instamart-bdpo-Jivo-Wellness-.png)
- `d41-instamart-campaign-list-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d41-instamart-campaign-list-Jivo-Wellness-.png)
- `d42-instamart-ads-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d42-instamart-ads-Jivo-Wellness-.png)
- `d55-instamart-Jivo-.png`

  ![screenshot](../captures/walk4/d55-instamart-Jivo-.png)
- `d56-instamart-sales-Jivo-.png`

  ![screenshot](../captures/walk4/d56-instamart-sales-Jivo-.png)
- `d57-instamart-sales-insights-Jivo--Category.png`

  ![screenshot](../captures/walk4/d57-instamart-sales-insights-Jivo--Category.png)
- `d58-instamart-reports-Jivo-.png`

  ![screenshot](../captures/walk4/d58-instamart-reports-Jivo-.png)
- `d59-instamart-bdpo-Jivo-.png`

  ![screenshot](../captures/walk4/d59-instamart-bdpo-Jivo-.png)
- `d60-instamart-campaign-list-Jivo-.png`

  ![screenshot](../captures/walk4/d60-instamart-campaign-list-Jivo-.png)
- `d61-instamart-ads-Jivo-.png`

  ![screenshot](../captures/walk4/d61-instamart-ads-Jivo-.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
