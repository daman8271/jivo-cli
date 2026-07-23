---
title: Ecom Connection Hub
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connector-hub
tags: [jivogpt, connections, ecommerce, marketplaces, sap, read-only]
---

# Ecom Connection Hub

Ecom is the downstream marketplace lens: channel sales and dashboards, state/city performance, inventory and DOH/SOH, ads and promotions, uploads and reports, SAP distribution views, and shipment/appointment planning reads.

## Current connector profile

| Property | Current evidence |
|---|---|
| Registered surface | 138 GET commands |
| Composition | 137 current SPA reads plus one retained legacy month-on-month route |
| Command families | Account, chatbot, dashboard, master, notifications, platform, reports, SAP, shipment, tables, upload, uploads |
| Source posture | Reads application database, SAP-backed, uploaded, platform-derived, and report datasets; no evidence that the CLI calls marketplaces directly |
| Publication | Internal/unpublished; release metadata is incomplete |

The present MCP integration is a code-orchestration bridge around the Cobra CLI and local helpers, not 138 separately typed MCP tools. Capability descriptions must reflect the actual interface.

## Canonical fields

| Canonical field | Ecom candidates | Qualification required |
|---|---|---|
| `company_key` | account/brand/business context where exposed | No canonical company switch is yet proven; platform is not company |
| `item_key` | platform SKU, SAP `ItemCode`, product name/pack | Product/SAP mapping, platform, company/schema, and date |
| `party_key` | SAP `CardCode`, distributor/customer fields | Tenant plus normalized name |
| `document_key` | PO, invoice, shipment, appointment ids | Platform, company, object type, and id kind |
| `warehouse_key` | SAP `WhsCode`, FC/warehouse/branch fields | Retain source-local and SAP scopes |
| `geography_key` | state, city, pincode | Normalize; keep pincode as a string |
| `platform_key` | marketplace/platform slug | Map through a dated alias registry |
| `observed_at` | month/year, report date, upload time, snapshot time | Preserve metric period and source freshness |

## Five connection edges

| Other connector | Best connection | Note |
|---|---|---|
| EXIM | Input economics and supply versus downstream channel sales, price, and inventory | [[EXIM__ECOM]] |
| Factory | Production/dispatch versus marketplace inventory, sell-through, and shipment plans | [[FACTORY__ECOM]] |
| OMS | Orders, stock, invoices, geography, marketplace sales, inventory, and POs | [[OMS__ECOM]] |
| jivo-desk | Independent reconciliation of SKU, platform, pincode, price, availability, date, and freshness | [[ECOM__JIVO_DESK]] |
| JSAP | Channel exceptions versus reports, tasks, tickets, MOMs, documents, and owners | [[ECOM__JSAP]] |

## Safe adapter contract

1. Record endpoint family, account/brand context, platform, geography, metric period, access state, and extraction time.
2. Preserve platform SKU and SAP item code separately until a validated product bridge exists.
3. Normalize platform aliases without erasing raw slugs.
4. Treat stored analytics and application views as reported source facts, not live marketplace ground truth.
5. Register only reads; generic client mutation methods and upload actions are outside the Connections surface.

## Exclusions and open evidence gaps

- No current evidence establishes a canonical Ecom company selector or maps Ecom accounts to Factory, OMS, EXIM, or JSAP tenants.
- Current verification saw shipment access return `403` and a SAP line return `500`; those are access/error states, not empty business facts.
- The generic client can express mutations even though no mutation is registered. A hard production GET-only guard would reduce future drift risk.
- Platform aliases differ from jivo-desk, including `swiggy` versus `swiggy-instamart` and `flipkart_grocery` versus `flipkart-minutes`.
- The live token check used during this audit returned `401`, so cross-system row equality was not asserted from that lane.

## Evidence anchors

[[ECOM_MAP]] · [[ECOM_CLI_ENDPOINT_GAP]] · [[ECOM_APP_SURVEY]] · [[DATA_SOURCES]] · [[READ_ONLY_LAW]]

---
Linked: [[/README|README]] · [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[EXIM_HUB]] · [[FACTORY_HUB]] · [[OMS_HUB]] · [[JIVO_DESK_HUB]] · [[JSAP_HUB]]
