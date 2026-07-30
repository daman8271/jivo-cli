---
title: Flipkart Data Model
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, data-model, read-only]
---

# Flipkart — Data Model (how the sections join)

Two independent business graphs behind one brand, joined only at the JIVO-entity level (the same
company sells 3P via Seller Hub and 1P via Vendor Hub). They do **not** share IDs: Seller Hub keys
on `sellerId` + `FSN`/`SKU ID`; Vendor Hub keys on `vendor_id` (`VEN…`) + `FSN` + warehouse
(`VS…`).

```mermaid
graph TD
  subgraph SELLER["Seller Hub — 3P marketplace (sellerId e56b4e65e27e4162)"]
    LIST["Listings & Catalog<br/>FSN / SKU"]
    PRICE["Pricing & RateCard"]
    INV["Inventory & Stock<br/>(unified / SFX)"]
    ORD["Orders & Shipments<br/>consignment / self-ship"]
    FBF["Fulfilment FBF / FBF-Lite"]
    RET["Returns & Recall"]
    PAY["Payments & Finance<br/>settlement / TDS"]
    ADS["Flipkart Ads + FSN<br/>(fed-ads campaigns)"]
    RPT["Report Centre<br/>earn_more / tax / invoice"]
    LIST --> PRICE --> ORD --> FBF --> RET
    ORD --> PAY
    LIST --> ADS
    ORD --> RPT
    INV --> ORD
  end

  subgraph VENDOR["Vendor Hub — 1P grocery (vendor_id VEN…, warehouse VS…)"]
    VPO["Purchase Orders + GRN"]
    VAN["Analytics<br/>sales / inventory / trends"]
    VCAT["Catalog & Feeds<br/>FSN / QC-norms"]
    VPAY["Payments<br/>debit notes"]
    VRET["Return Orders / RTV"]
    VUSR["Users & Access<br/>roles / warehouses"]
    VDOC["Documents<br/>getFile / getDocument"]
    VUSR --> VPO
    VPO --> GRN2["GRN receipt"]
    VPO --> VAN
    VCAT --> VPO
    VPO --> VPAY
    VPO --> VRET
    VPO --> VDOC
  end

  subgraph PLAT["Platform / shell (both)"]
    GQL["GraphQL data core<br/>(seller widgets)"]
    IDN["Profile / Onboarding / SPF"]
    PRN["Printing (labels/invoices)"]
  end

  JIVO["JIVO Wellness / JIVO Mart<br/>(one company, 2 lanes)"]
  JIVO --> SELLER
  JIVO --> VENDOR
  SELLER -.same brand, no shared id.- VENDOR
  GQL --> SELLER
  IDN --> SELLER
  IDN --> VENDOR
```

## Join keys

| Concept | Seller Hub | Vendor Hub |
|---|---|---|
| Account | `sellerId` (`e56b4e65e27e4162`) | `vendor_id` (`VEN23097` …) under an `accountId` (`ACC…`) |
| Product | `FSN`, `SKU ID`, `listingId` | `FSN`, `sku_id` |
| Location | fulfilment `Location Id` / warehouse | vendor site `VS…` (warehouse) |
| Order | consignment id / shipment id | PO number → GRN id |
| Money | settlement / payment id | debit-note id / invoice id |
| Report | `request_id` (report-centre) | `document_id` (`CONA…`) / getDocument token |

## Lifecycles

- **Seller 3P sale:** Listing (FSN) → Price set → Customer order → Shipment (self-ship / FBF) →
  Delivered or Return/RTO → Settlement/Payment → captured in Report Centre + Ads attribution.
- **Vendor 1P supply:** Flipkart raises **PO** to a JIVO vendor → JIVO ships → **GRN** at the FK
  warehouse → sales/inventory analytics → debit notes / returns (RTV) → payment.

Both lifecycles are **read-only** in this study; every state-changing transition
(accept/dispatch/approve/settle/upload) is catalogued out-of-scope in the section notes and
[[Flipkart-Endpoints]].

## Connections
[[00-Flipkart-Atlas]] · [[Flipkart-Endpoints]] · [[Flipkart-Data-Inventory]] · [[Auth-and-Access]]
