---
title: OMS Connection Hub
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connector-hub
tags: [jivogpt, connections, oms, orders, sap, read-only]
---

# OMS Connection Hub

OMS is the order-to-SAP lens: parties and products, schemes, quotations, orders, HANA inventory/batches, invoices, dashboard metrics, and SAP transfer/log views.

## Current connector profile

| Property | Current evidence |
|---|---|
| Declared surface | 73 GET entries in the specification/manifest/MCP inventory |
| Runtime surface | 72 registered endpoint commands |
| Company model | Jivo Wellness id `1`; Jivo Mart id `2` |
| Current verification scope | Admin verification covered Wellness; role and Mart coverage remain incomplete |
| Publication | Internal/unpublished; generated public-install wording is not authoritative |

The missing runtime command is invoice history: it remains documented in the spec/MCP inventory, but registration is commented because the upstream route is absent. Do not advertise or query it as a working runtime capability.

## Canonical fields

| Canonical field | OMS candidates | Qualification required |
|---|---|---|
| `company_key` | company id/name, request scope | Map through an OMS-specific dated table |
| `item_key` | `item_code`, product/SKU fields | Company/schema, description, pack, and as-of date |
| `party_key` | `card_code`, party/customer/distributor id | Tenant plus normalized name; duplicate codes are possible |
| `document_key` | internal id, order number, quotation, invoice, SAP doc number | Object type, company, system, and id kind |
| `warehouse_key` | `WhsCode`, warehouse/branch fields | Retain local and SAP values separately |
| `batch_key` | HANA batch/lot fields | Item, warehouse, and company must also match |
| `geography_key` | state, branch, category/distributor geography | Normalize through dated references |
| `observed_at` | creation, posting, invoice, sync, snapshot time | Preserve event and extraction times |

## Five connection edges

| Other connector | Best connection | Note |
|---|---|---|
| EXIM | Items, business partners, open documents, stock, and planning | [[EXIM__OMS]] |
| Factory | Finished goods, warehouse stock, batches, dispatch, orders, and SAP docs | [[FACTORY__OMS]] |
| Ecom | Orders, stock, invoices, geography, channel sales, inventory, and POs | [[OMS__ECOM]] |
| jivo-desk | Internal availability/demand versus observed marketplace price, availability, and DRR | [[OMS__JIVO_DESK]] |
| JSAP | Parties, orders, invoices, SAP logs, approvals, bills, reports, and history | [[OMS__JSAP]] |

## Safe adapter contract

1. Record company, authenticated role, endpoint family, and access state with every response.
2. Distinguish working runtime commands from spec-only or dead entries.
3. Preserve internal id, order number, SAP document number, `DocEntry`, and `DocNum` as separate id kinds.
4. Emit `403-gated`, `empty`, or `upstream-error` states explicitly; never coerce them to zero.
5. Keep all client mutations and SAP transfer actions outside the registered connection surface.

## Exclusions and open evidence gaps

- Invoice-history is not a working runtime endpoint despite its residual spec/MCP entry.
- Tracker reads returned `403` in current verification; visibility depends on role and must not be generalized.
- The generic client contains mutation-capable methods. Structural omission of write commands is the present safety control; a production GET-only transport guard is still desirable.
- Only Wellness received the documented admin verification pass; Jivo Mart and other role combinations need explicit re-verification.
- A repeated `card_code` may have different names. Require tenant and normalized-name checks before merging parties.

## Evidence anchors

[[OMS_MAP]] · [[OMS_VERIFICATION]] · [[OMS_API_INVENTORY]] · [[DATA_SOURCES]] · [[READ_ONLY_LAW]]

---
Linked: [[/README|README]] · [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[EXIM_HUB]] · [[FACTORY_HUB]] · [[ECOM_HUB]] · [[JIVO_DESK_HUB]] · [[JSAP_HUB]]
