---
title: Swiggy Instamart Data Model
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, data-model]
---

# Swiggy Instamart — how the sections join into one graph

This note is the join map: which identifier connects which surface to which. It is what turns 28
section notes into one queryable picture, and it is the thing you need before writing any analysis
that spans the ads lane and the supply lane.

## The five identifiers that matter

| Id | What it keys | Where it comes from | Appears in |
|---|---|---|---|
| **`SPIN`** (e.g. `L7P0RZ1JUI`) | a sellable product | catalog | sales insights, sales xlsx (`ITEM_CODE`), catalog, ads targeting, sampling |
| **`accountId`** (uuid) | an ads/brand account | `account/list` | every brand-portal call as `x-client-account-id`; campaigns; sales filters |
| **`brandCompanyId`** (sha1-like) | the legal company | `account/list` | supply lane (`supply_companies`), catalog |
| **`cityId`** (numeric, 1–10459) | a city | `configs.IM_ENABLED_CITIES` | sales metric rows, availability, PO facility city |
| **`facility` / `FC`** (e.g. `BLR IM3`, `CBE Ecom`) | a dark store / fulfilment centre | `listAllFCs` | POs, GRN, stock on hand, availability, appointments |

**The critical seam:** the ads lane keys on `SPIN` + `cityId`; the supply lane keys on
`facility` + `vendorCode`. They meet at the product (SPIN) and at the city — a facility belongs to
a city — but **not** at any single shared row. Joining "did we sell out because we were out of
stock?" therefore requires SPIN × city × date on the ads side against SPIN × facility × date on
the supply side, with facility→city resolved from `listAllFCs`.

## The entity hierarchy

```mermaid
graph TD
  U["user ecom1@jivo.in (id 345)"] --> A1["account Jivo Mart Pvt. Ltd<br/>89bafc9c-…"]
  U --> A2["account Jivo Wellness<br/>c9f24655-…"]
  U --> A3["account Jivo<br/>260921c1-…"]
  A1 --> C1["brandCompany Jivo Mart Pvt. Ltd<br/>935ac57d…"]
  A2 --> C2["brandCompany Jivo Wellness<br/>5ecb3c00…"]
  C1 --> BA1["brandAccount e4d59d18-…"]
  C2 --> BA2["brandAccount 260921c1-…"]
  BA2 --> B1["brand Jivo<br/>1bd421f6…"]
  BA1 --> B2["brand Jivo<br/>4d02ec98…"]
```

Note that "Jivo" exists as **both** a selectable account (`260921c1`) and as the brand *inside*
Jivo Wellness — which is why account `260921c1` and account `c9f24655` return identical sales
filters but different campaign counts. Campaigns hang off the parent account; sales hang off the
brand.

## The two lanes and where they meet

```mermaid
graph LR
  subgraph ADS["Ads lane · partner-api + brand-portal-service"]
    SI["Sales Insights<br/>sales/metric · sales/filters"]
    SR["Sales Reports<br/>sales/reports → presigned S3"]
    CMP["Campaigns<br/>campaigns · 33 fields"]
    BI["Brand Insights<br/>advertiser/metrics"]
    KW["Keywords & Bids"]
    CAT["Catalog<br/>list_spins · SPIN change requests"]
  end
  subgraph SUP["Supply lane · picker.swiggy.com"]
    PO["Purchase Orders<br/>searchPurchaseOrder"]
    APPT["PO Booking<br/>fc-appointment"]
    GRN["Goods Received<br/>searchGrns"]
    RET["Returns / RTV"]
    SOH["Stock on Hand<br/>inventory/*"]
    AVL["Availability"]
    PERF["Vendor Performance"]
  end
  SPIN(["SPIN — product id"])
  CITY(["cityId — 141 in config, 132 with sales"])
  FC(["facility / FC — listAllFCs"])

  CAT --> SPIN
  SPIN --> SI
  SPIN --> SR
  SPIN --> CMP
  SPIN --> SOH
  SPIN --> AVL
  CITY --> SI
  CITY --> AVL
  FC --> PO
  FC --> GRN
  FC --> SOH
  FC --> AVL
  FC --> CITY
  PO --> APPT
  APPT --> GRN
  GRN --> RET
  PO --> PERF
  GRN --> PERF
  SOH --> AVL
  AVL --> SI
```

## The PO lifecycle (supply lane)

`searchPurchaseOrder` → a PO with a facility, vendor, ordered qty and expiry
→ **PO Booking** turns it into an appointment (`fc-appointment/*`)
→ the facility receives it, producing a **GRN** (`searchGrns` / `grn/searchGrnLines`)
→ shortfalls and rejections flow into **Returns / RTV**
→ receipt performance is scored in **Vendor Performance**
→ what actually sits in the store is **Stock on Hand**, and whether it was buyable is
**Availability**.

Ordered qty (PO) minus received qty (GRN) is the fill-rate gap; GRN qty against Stock-on-Hand
movement is the sell-through. **Both halves are readable and JIVO reads neither.**

## The report model — identical on every surface

Every reporting surface on this portal follows one three-step shape:

```mermaid
graph LR
  G["1. GENERATE / initiate<br/>POST …/report · …/initiate-*-report<br/>WRITE — creates a queue row (G2)"]
  L["2. LIST / POLL<br/>POST …/reports · …/report/list<br/>READ"]
  D["3. DOWNLOAD<br/>GET presigned S3<br/>im-brand-reports-in-west.s3.ap-south-1.amazonaws.com<br/>READ_FILE — the presign IS the auth"]
  G --> L --> D
```

Step 2 and step 3 are reads and are exposed. **Step 1 is a write and is not** — it creates a row
and consumes the account's report quota. `reportStatus` moves to `STATUS_COMPLETED` before
`downloadUrl` is populated. Report families found: sales (`sales/reports`), ads summary
(`advertiser/metrics/report/list`), BDPO/discount (`discount/reports`, `report/list-bdpo`) and the
vendor lane's own queue (`/im-vendor/downloads`).

## Metric vocabulary as a dimension cube

`sales/metric` and `advertiser/metrics` are the same shape: pick metrics, pick a dimension
grouping, pick filters.

- **47 metric types** — sales, units sold, orders, customers, GMV, market share, three
  share-of-voice variants, impressions, clicks, CTR, CVR, conversions, spend, budget burnt
  (incl. realtime), ROAS, ROI, CPO, eCPS, AOV, reach, sessions, new-user counts, product rating,
  and benchmark CTR/CVR/ROI.
- **17 dimension types** — day, week, month, date, city, product, brand, account, campaign name,
  campaign source, keyword, L-category.
- **25 filter types** — date/start/end, account, brand, brand company, campaign id/name/status/
  type, category, city, product, keyword (+ match type, + type), creative, placement, channel,
  ad candidate id/type, impressions, zero-values.

Every response row carries `currentValue`, `priorValue`, `delta` and `deltaUnit`, so
period-over-period comparison is built in and does not need computing locally.

## Connections

- [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] ·
  [[Swiggy-Instamart-Data-Inventory]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- Product identity: [[Catalog-SPIN-Management]] · [[Products-And-SPINs]]
- City/geo: [[Config-And-Feature-Flags]] · [[Sales-Insights]] · [[Availability-and-Fill-Rate]]
- PO lifecycle: [[Purchase-Orders]] → [[PO-Booking-Appointments]] → [[Goods-Received-GRN]] →
  [[Returns-RTV-and-Purchase-Returns]] → [[Vendor-Performance-Scores]]
- Reporting: [[Sales-Reports]] · [[Vendor-Downloads]] · [[Discounts-BDPO]] ·
  [[Brand-Insights-Metrics]]
- Entities: [[Accounts-And-Entities]]
