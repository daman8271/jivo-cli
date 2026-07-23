---
title: Factory Connection Hub
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connector-hub
tags: [jivogpt, connections, factory, production, warehouse, read-only]
---

# Factory Connection Hub

Factory is the physical-operations lens across the JIVO campus: gate entry, quality control, GRPO, production, warehouse stock, barcode/packing lineage, intercompany movement, dispatch, maintenance, people, and shared campus services.

## Current connector profile

| Property | Current evidence |
|---|---|
| Read surface | 183 GET endpoints |
| Company scope | `JIVO_OIL`, `JIVO_MART`, `JIVO_BEVERAGES` |
| Scoping mechanism | Shared authentication plus `Company-Code` for company-scoped operations |
| Data shape | A mixture of campus-wide/shared domains and company-scoped operational domains |
| Authority | Current [[FACTORY_MAP]], [[FACTORY_VERIFICATION]], and [[CLI/factory-cli/DATA-MODEL|Factory data model]] |

The company header is part of the data grain. A record queried under one company must never be pooled with another merely because a local id, document number, or SAP-looking item code is equal.

## Canonical fields

| Canonical field | Factory candidates | Qualification required |
|---|---|---|
| `company_key` | `JIVO_OIL`, `JIVO_MART`, `JIVO_BEVERAGES`, company header | Use canonical strings, not numeric ids from another CLI |
| `item_key` | SAP `item_code`, FG/RM code, product description | Company/schema, description, pack, and date |
| `party_key` | vendor/business-partner codes and names | Prefer SAP code; validate normalized name |
| `document_key` | GRPO, PO, transfer, production, dispatch identifiers | Company, object type, source, and id kind |
| `warehouse_key` | SAP/local warehouse code and name | Retain both code and source-local id |
| `batch_key` | batch/lot, barcode box/pallet, production run | Item and company must also match |
| `person_key` | employee code, email, local employee id | Treat as candidate identity; minimize personal data |
| `observed_at` | gate, QC, production, movement, dispatch, snapshot time | Separate event and extraction times |

`FG0000424` is a known warning: the Factory sample and EXIM documentation attach incompatible descriptions to the same code. The resolver must validate description and pack rather than trusting the code alone.

## Five connection edges

| Other connector | Best connection | Note |
|---|---|---|
| EXIM | Inbound material, tank/arrival, item, vendor, GRPO, and warehouse intake | [[EXIM__FACTORY]] |
| OMS | Finished goods, stock, batches, dispatch, orders, and SAP documents | [[FACTORY__OMS]] |
| Ecom | Supply/dispatch versus channel inventory, sell-through, and shipments | [[FACTORY__ECOM]] |
| jivo-desk | Supply availability versus independently observed marketplace availability and price | [[FACTORY__JIVO_DESK]] |
| JSAP | GRPO, QC, inventory audit, documents, employees, and maintenance follow-up | [[FACTORY__JSAP]] |

## Safe adapter contract

1. Send the explicit company header for every company-scoped request and record it in every row.
2. Mark campus-wide/shared data separately from company-scoped data.
3. Preserve SAP and local ids as distinct fields, including `DocEntry` versus `DocNum`.
4. Emit batch/barcode lineage only with item, company, and source provenance.
5. Read into JivoGPT-owned normalized tables; never post QC, GRPO, production, stock, or dispatch changes.

## Exclusions and open evidence gaps

- Factory numeric company ids cannot be reused as JSAP ids: Factory id `2` means Mart, while JSAP id `2` means Beverage.
- A matching item or vendor code is a strong candidate, not proof of a shared SAP schema.
- Shared campus records need an explicit relationship table before they are attributed to one company.
- `DocEntry`, `DocNum`, PO, GRPO, transfer, and dispatch identifiers are different id kinds.
- People and employee joins must be purpose-limited, field-minimized, and tenant-qualified.

## Evidence anchors

[[FACTORY_MAP]] · [[CLI/factory-cli/DATA-MODEL|Factory data model]] · [[FACTORY_VERIFICATION]] · [[CLI/factory-cli/research/COMPANY-SWEEP|Factory company sweep]] · [[DATA_SOURCES]] · [[READ_ONLY_LAW]]

---
Linked: [[/README|README]] · [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[EXIM_HUB]] · [[OMS_HUB]] · [[ECOM_HUB]] · [[JIVO_DESK_HUB]] · [[JSAP_HUB]]
