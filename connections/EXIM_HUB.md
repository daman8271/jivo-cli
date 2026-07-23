---
title: EXIM Connection Hub
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connector-hub
tags: [jivogpt, connections, exim, sap, imports, read-only]
---

# EXIM Connection Hub

EXIM is the inbound-supply lens: import and export contracts, raw-material stock, tanks, commodity and FX rates, licenses, vehicles, vendors, open purchase documents, GRPOs, and SAP Business One reference data for Jivo Wellness.

> ⛔ Use only the proven read surface under [[READ_ONLY_LAW]]. The apparent `GET /sap_sync/open-grpos/` route is not safe for connection recipes while its documented refresh behavior conflicts with [[CLI/exim/HARD-RULE|EXIM HARD-RULE]].

## Current connector profile

| Property | Current evidence |
|---|---|
| Read surface | 65 generated/manifest tools; 66 unique read-labelled routes when the wrapper-only GRPO route is counted |
| Scope | Jivo Wellness EXIM operations and connected SAP-derived reference views |
| Main domains | Contracts, rates, tanks, stock lifecycle, licenses, vehicles, vendors, RM/FG masters, POs, GRPOs, accounts |
| Authority | Current wrapper, route inventory, endpoint notes, and verification records take precedence over imported summaries |
| Publication | Internal connector; capability counts describe this workspace snapshot, not a public compatibility promise |

The route counts disagree because the API inventory contains one duplicate `/dc/` row and the wrapper exposes one disputed route outside the 65 generated tools. Keep all three facts visible instead of forcing a false single number.

## Canonical fields

| Canonical field | EXIM candidates | Qualification required |
|---|---|---|
| `company_key` | Jivo Wellness | Do not infer equivalence to Factory or JSAP company ids |
| `sap_schema` | EXIM/SAP company context | Preserve whenever the response identifies it |
| `item_key` | `item_code`, RM/FG codes | Company/schema, description, pack, and as-of date |
| `party_key` | `card_code`, vendor/customer code | Normalize case/space only; preserve the raw code |
| `document_key` | PO number, GRPO number, contract id | Add company, object type, source, and id kind |
| `warehouse_key` | warehouse code/name | Prefer SAP code; retain the source label |
| `batch_key` | stock lot, tank, vehicle/date lifecycle fields | Item and company must also match |
| `observed_at` | contract, arrival, posting, rate, or snapshot date | Keep event time separate from extraction time |

Bare SAP code equality is unsafe. `FG0000424` already has incompatible descriptions in EXIM and a Factory sample, so an automated item bridge must reject or quarantine that mismatch.

## Five connection edges

| Other connector | Best connection | Note |
|---|---|---|
| Factory | Imported material, tank/arrival, item, vendor, GRPO, and warehouse intake | [[EXIM__FACTORY]] |
| OMS | Items, business partners, open SAP documents, stock, and demand planning | [[EXIM__OMS]] |
| Ecom | Input economics and supply context versus downstream sales, inventory, and price | [[EXIM__ECOM]] |
| jivo-desk | Commodity/JIVO rates versus observed marketplace price, availability, and DRR | [[EXIM__JIVO_DESK]] |
| JSAP | SAP parties and documents plus bills, approvals, reports, and audit context | [[EXIM__JSAP]] |

## Safe adapter contract

1. Call only routes admitted by the current read-only allowlist.
2. Emit raw fields alongside canonical fields; never rewrite source identifiers.
3. Stamp company/schema, endpoint family, access state, event date, and extraction time.
4. Quarantine ambiguous item, party, and document matches instead of choosing one.
5. Store normalized results only in JivoGPT-owned storage and cite the contributing EXIM response.

## Exclusions and open evidence gaps

- Exclude the entire disputed `/sap_sync/open-grpos/` wrapper path until maintainers reconcile the route, endpoint note, and [[CLI/exim/HARD-RULE|EXIM HARD-RULE]]. A GET verb does not make a refresh side effect read-only.
- No source proves that Jivo Wellness is the same tenant as Factory `JIVO_OIL`, `JIVO_MART`, or `JIVO_BEVERAGES`.
- No durable foreign key currently maps an EXIM import lot or tank lifecycle directly to a Factory batch.
- Document values must retain whether they are PO, GRPO, `DocEntry`, `DocNum`, or a local id.
- Empty or upstream-gated results describe visibility, not zero inventory or zero business activity.

## Evidence anchors

[[EXIM_MAP]] · [[CLI/exim/DOMAIN-MODEL|EXIM domain model]] · [[CLI/exim/ARCHITECTURE|EXIM architecture]] · [[CLI/exim/API-INVENTORY|EXIM API inventory]] · [[DATA_SOURCES]] · [[READ_ONLY_LAW]]

---
Linked: [[/README|README]] · [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[FACTORY_HUB]] · [[OMS_HUB]] · [[ECOM_HUB]] · [[JIVO_DESK_HUB]] · [[JSAP_HUB]]
