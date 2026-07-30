---
title: Amazon Data Model
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [amazon, data-model, read-only]
status: studied
read_only: true
---

# Amazon — Data Model (how the sections join into one graph)

Amazon does not expose one relational schema; it exposes **two portals over the same physical
inventory of ASINs**. The join key that ties almost everything together is the **ASIN**
(child) / **parent-ASIN** and, on the 1P side, the **vendorGroupId**. This note maps how the 20
sections relate.

## The spine: ASIN → everything

```mermaid
graph TD
  MERCH["Merchant / Entity<br/>Jivo Mart A2V85Y00QGIGP9 (3P)<br/>Wellness 7691702 / Mart 8592892 (1P)"]
  ASIN["ASIN (product)<br/>parent + child variations"]
  MERCH --> ASIN

  ASIN --> LIST["Listings / Offers<br/>[[Listings-ASIN-Management]]"]
  ASIN --> INV["Inventory / FBA<br/>[[Inventory-FBA]]"]
  ASIN --> ORD["Orders<br/>[[Orders]]"]
  ASIN --> COUP["Coupons / Promotions<br/>[[Coupons-Promotions]]"]
  ASIN --> PCR["CX Health / VoC<br/>[[Account-Health-Performance]]"]
  ASIN --> CLASS["Product Classification<br/>[[Product-Classification]]"]

  ORD --> FB["Seller Feedback<br/>[[Feedback-Manager]]"]
  ORD --> MSG["Buyer-Seller Messaging<br/>[[Messaging-Buyer-Seller]]"]
  ORD --> GST["GST / Tax Reports<br/>[[Tax-GST-Reports]]"]
  ORD --> PERF["Account Health<br/>[[Account-Health-Performance]]"]

  INV --> RC["Report Central (35 types)<br/>[[Business-Reports-Analytics]]"]
  ORD --> RC
  ORD --> BR["Business Reports<br/>[[Business-Reports-Analytics]]"]

  ASIN --> GS["Global Selling<br/>[[Global-Selling-Expansion]]"]

  subgraph VC["Vendor Central (1P) — same physical products, Amazon as buyer"]
    PO["Purchase Orders<br/>[[Purchase-Orders]]"] --> ARA["Retail Analytics ARA<br/>[[Retail-Analytics-ARA]]"]
    ARA --> VCAT["VC Catalog<br/>[[VC-Catalog-Products]]"]
    PO --> VCOUP["VC Coupons<br/>[[VC-Coupon-Campaigns]]"]
  end
  ASIN -.same product, different program.-> ARA

  subgraph PLAT["Platform (shared shell)"]
    HOME["Homepage Widgets<br/>[[Homepage-Widgets]]"]
    HELP["Help & Support<br/>[[Help-Support-Center]]"]
    COMMON["Platform Common<br/>[[Platform-Common]]"]
    STATIC["Static / i18n<br/>[[Static-Assets-i18n]]"]
  end
  MERCH --> HOME
```

## The join keys

| Key | Where it appears | Ties together |
|---|---|---|
| **ASIN** (`B0…`) | listings, inventory, orders, coupons, PCR, ARA | the product spine — the one id present in nearly every section |
| **parent ASIN** | listings variations, coupons (`asinCount`) | variation families |
| **merchantId** `A2V85Y00QGIGP9` | every 3P response (`merchantId`/`merchantAccountId`) | scopes all Seller Central data to Jivo Mart |
| **marketplaceId** `A21TJRUUN4KGV` | every 3P response | scopes to Amazon India |
| **vendorGroupId** `7691702`/`8592892` | ARA `amz-ara-custom-context`, PO responses | scopes all 1P data to a VC entity |
| **orderId** (`4NN-NNNNNNN-NNNNNNN`) | orders, messaging cases, feedback, GST MTR | one order across fulfilment → feedback → tax |
| **reportType** (`FBA_MYI_…`) | Report Central config + workflows | the 35 report catalogue |
| **campaignId / promotionId** (`obfuscatedPromotionId`) | coupons, VC coupons | a promotion and its metrics file |

## The two-portal duality

The same physical bottle of Jivo oil is:
- an **ASIN** in Seller Central (3P) — JIVO owns the listing, Amazon is the storefront; JIVO is
  paid by the customer (minus fees). Data: [[Orders]], [[Inventory-FBA]], [[Coupons-Promotions]].
- a **line on a Purchase Order** in Vendor Central (1P) — Amazon *buys* it from JIVO wholesale and
  owns the retail listing; JIVO is paid by Amazon. Data: [[Purchase-Orders]], [[Retail-Analytics-ARA]].

There is **no single endpoint that unifies 1P and 3P** — they are separate logins on separate
hosts. The unification happens only in JIVO's own downstream systems (SAP, the ecom hub). That is
why this study keeps the two portals as distinct section groups.

## Connections
- [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Pages-and-Routes]] · [[Read-Only-Guardrails]]
