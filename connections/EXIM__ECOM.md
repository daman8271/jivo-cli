---
title: EXIM to Ecom Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connection, exim, ecom, pricing, inventory, read-only]
---

# EXIM to Ecom Connection

## Connection verdict

**Primarily a semantic and reconciliation edge.** EXIM supplies upstream commodity, packing, JIVO-rate, imported-stock, and SAP inventory context. Ecom supplies downstream marketplace sales, price, inventory, DOH/SOH, ads, geography, distributors, POs, and SAP sales/inventory reads. This can explain margin and availability pressure, but it is not a proven row-level join and no running federated join exists.

The only plausible deterministic bridge is through verified SAP item and party mappings. Marketplace SKU names, ASINs, FSNs, platform identifiers, and EXIM commodity/pack labels are not interchangeable with SAP item codes.

## Why they connect

- EXIM estimates and records input economics through commodity price, packing cost, tax-inclusive per-kg/per-litre price, and JIVO pack rate.
- Ecom observes marketplace outcome through selling price, sales, inventory, sell-through, DRR, SOH/DOH, and geography.
- Ecom also exposes an SAP read layer for item masters, distributors, invoices, finished-goods inventory, and warehouse stock, which may become a controlled bridge after field-level validation.

## Evidence from system A

System A is EXIM. As of 2026-07-19, the generated surface contains **65 printed CLI tools**. [[API-INVENTORY]] lists 67 read rows but duplicates `GET /dc/`, so the inventory has **66 unique read-labelled routes**.

`GET /sap_sync/open-grpos/` is not part of this edge's safe surface. [[sap_sync_open-grpos]] records a sync permission and possible SAP refresh side effect despite a data response; it is an unresolved GET-that-may-refresh conflict and must remain excluded.

Proven upstream fields include:

- `commodity_name`, `factory_price`, `packing_cost_kg`, `with_gst_kg`, `with_gst_ltr`, and `date` in [[daily-price_range]].
- `pack_type`, `commodity`, `rate`, and `date` in [[jivo-rate_range]].
- SAP `item_code`, `item_name`, category, brand, variety, pack factor, and pack unit in [[items_fg]] and [[items_rm]].
- Warehouse/category inventory totals in [[sap-sync_inventory]] and [[sap-sync_finished-inventory]].

EXIM is described as scoped to **Jivo Wellness** in [[EXIM_MAP]]. That scope must be preserved in any downstream comparison.

## Evidence from system B

System B is Ecom. [[ECOM_MAP]] documents **138 registered GET commands: 137 current SPA reads plus one retained legacy `month-on-month-sale` route**. Its current MCP is a code-orchestration bridge around the Cobra CLI and local helpers, not 138 separately typed tools. [[ECOM_APP_SURVEY]] proves read endpoints for platform price, DRR, SOH/DOH, inventory match, sales, state/city/SKU detail, master products, and an SAP layer.

Relevant Ecom surfaces include:

- platform-scoped price, DRR, SOH/DOH, region DOH, inventory-match, primary, secondary, and marketplace dashboards;
- master product and platform identifiers whose exact mapping grain must be inspected before use;
- SAP item master, distributors by `CardCode`, sales invoices by explicit DocEntry, finished-goods inventory, stock by warehouse, and warehouse comparison in [[ECOM_CLI_ENDPOINT_GAP]].

The Ecom notes prove that these endpoints exist, but do not prove that marketplace SKU rows carry the same SAP item code as EXIM. Therefore the marketplace product bridge remains missing evidence.

## Join contract table

| Canonical key | A field | B field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | implicit Jivo Wellness scope | Ecom account/data scope; SAP JM views where applicable | legal entity, SAP schema, platform business mode, dated alias | **Missing evidence — low** |
| `sap_item_key` | `item_code` / `ItemCode` plus item attributes | fields returned by Ecom SAP item master | company/schema, exact code, item name, pack/UOM, extract date | **Candidate — field shape/live overlap not yet proven** |
| `marketplace_product_key` | commodity + `pack_type`, or validated FG code | platform SKU/product/ASIN/FSN/master-product id | explicit dated product bridge, brand, pack size/count, variant, platform | **Candidate mapping — low** |
| `party_key` | `card_code` / vendor/customer code | Ecom SAP distributor `CardCode` | company/schema, BP type, exact code, platform-distributor mapping | **Candidate — low** |
| `price_reconciliation_key` | commodity/pack + `rate` or cost field + `date` | mapped SKU + platform selling price + observation date | same pack basis, litres/kg conversion, tax, geography, platform, freshness | **Reconciliation join — medium after mapping** |
| `inventory_reconciliation_key` | warehouse/category or item stock + as-of | SAP or platform inventory/SOH + warehouse/platform + date | company, item bridge, warehouse/platform grain, UOM, event and freshness dates | **Reconciliation join — medium-low** |
| `sap_invoice_key` | EXIM AP/AR internal key or invoice number only after its object type and id kind are proven | Ecom sales-invoice lookup by SAP `DocEntry` | same company/database, same A/P or A/R object type, separate `DocEntry`/`DocNum`, posting date | **No same-object bridge proven** |
| `marketplace_document_key` | EXIM PO/GRPO/import identifiers | Ecom marketplace PO, appointment, shipment, or report identifiers | explicit external-reference bridge; never use numeric equality | **Missing direct key** |

Where SAP documents are compared, `DocEntry` and `DocNum` remain separate typed keys. Ecom's sales-invoice lookup explicitly takes DocEntry, while its marketplace POs and shipment/report ids are different namespaces. None may be joined to an EXIM invoice, PO, or GRPO number merely because numeric values match.

## Read-only questions unlocked

- For mapped packs, how does EXIM's dated cost or JIVO-rate context compare with marketplace selling price?
- Which mapped items have upstream stock but weak platform availability or high DOH risk?
- Which commodity-cost movements precede downstream price or sell-through changes, without asserting causation?
- Do Ecom SAP item/distributor records supply a reliable bridge to EXIM item and party masters?

## Gaps/do-not-assume

- No proven EXIM-to-marketplace SKU bridge exists.
- Commodity and pack labels are not SAP item codes; fuzzy text similarity is not a durable key.
- Ecom platform price and EXIM rate/cost fields can differ in tax, unit, pack, geography, and effective date.
- Jivo Wellness must not be silently equated with Jivo Mart or any Ecom SAP/business-mode scope.
- Marketplace inventory, SAP warehouse stock, and EXIM warehouse/category totals have different grains.
- Differences are analytical findings, never values to overwrite. No federated join is running.
- `/sap_sync/open-grpos/` is excluded from all safe query plans.

## Validation checklist

- [ ] Capture Ecom SAP-item response fields and profile exact overlap with EXIM inside a verified company/schema.
- [ ] Build a dated, reviewed bridge from SAP item to marketplace product identifiers per platform.
- [ ] Normalize brand, pack size, pack count, UOM, tax basis, currency, geography, and observation date.
- [ ] Separate SAP DocEntry from DocNum and all marketplace/PO local identifiers.
- [ ] Record event date and source freshness for both sides of every comparison.
- [ ] Measure one-to-many mappings, unmatched products, stale sources, and gated Ecom surfaces.
- [ ] Keep EXIM reads on the printed safe surface and exclude `/sap_sync/open-grpos/`.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[EXIM_HUB]] · [[ECOM_HUB]] · [[EXIM_MAP]] · [[ECOM_MAP]] · [[READ_ONLY_LAW]]
