---
title: OMS to Ecom Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connections, oms, ecom, sap, orders, marketplace, read-only]
---

# OMS to Ecom Connection

> Evidence and contracts in this note are current as of 2026-07-19 and are governed by [[READ_ONLY_LAW]].

## Connection verdict

**Declared SAP item/party/warehouse candidates plus order-to-market reconciliation.** OMS exposes internal parties, quotations, orders, open SAP sales orders, HANA stock, invoices, and status flows. Ecom declares SAP distributor, order/invoice, warehouse-stock, and platform-mapping endpoint families alongside marketplace sales, inventory, geography, and shipment-planning reads; their exact row shapes still require a retained redacted sample.

There is **no running federated join** between OMS and Ecom as of 2026-07-19. Exact joins require a qualified SAP spine; marketplace comparisons require explicit product, platform, geography, unit, and time normalization.

## Why they connect

- OMS captures intended demand and commercial workflow: party assignment, order, quotation, stock check, billing, and invoice context.
- Ecom captures downstream channel execution: platform/distributor activity, SAP sales invoices, marketplace sales and inventory, POs, appointments, state/city views, and shipment planning.
- OMS exposes SAP-style item, party, warehouse, and document fields; Ecom declares corresponding endpoint families whose response fields must be sampled before equality joins.
- The systems use different local order identifiers and may observe different stages of the same commercial flow. Their metrics should be reconciled, not overwritten or assumed equal.

## Evidence from system A

OMS has **73 GET entries in its spec, manifest, and MCP registry but 72 registered runtime endpoint commands** as of 2026-07-19.

- [[OMS_VERIFICATION]] proves the 73-entry coverage and the one runtime exception: `invoice/history/{id}` is absent from the deployed backend and `invoices history` is unregistered in `CLI/oms-cli/internal/cli/invoices.go`.
- OMS orders expose local `id`, `order_number`, `card_code`, party, company, PO number, item lines, quantities, dispatch-from, status, dates, and optional `sap_doc_number`.
- OMS quotation overview and quotation log provide local order id plus SAP quotation `doc_num` / `doc_entry` and status.
- OMS HANA reads expose `ItemCode`, `CardCode`, `DocEntry`, `DocNum`, `BPL_Id`, `WhsCode`, open quantity, prices, dates, and order lines.
- OMS product-stock exposes `item_code`, `warehouse_code`, `warehouse_stock`, `pending_required_qty`, and `left_over_stock`.
- OMS SAP masters expose category-tagged `item_code`, `card_code`, addresses, branches, and sync timestamps. The same `card_code` can recur under multiple categories.
- Only a Jivo Wellness company-1 login was verified. OMS cross-company behavior and Jivo Mart switching remain unproven; some HANA surfaces appear SAP-wide but are not established as company-independent.

## Evidence from system B

Ecom has **138 registered GET commands** as of 2026-07-19: **137 current SPA GETs and one retained legacy `month-on-month-sale` route**.

The current Ecom MCP is a code-orchestration bridge around the Cobra CLI and local helpers, not 138 separately typed MCP tools.

- Ecom's SAP read group declares item-master, stock-by-warehouse, distributor/order/invoice, platform-distributor, and sales-invoice endpoint families. The current retained evidence does not prove their exact response field names.
- The retained Ecom notes prove these SAP endpoint families and their parameters exist, but do not preserve a reproducible response sample for the exact invoice/stock row fields. Those field shapes remain declared candidates until a redacted probe is retained and cited.
- Ecom marketplace dashboards expose platform, report month/year, SKU/product label, category, units/litres/value, inventory/DOH, and state/city dimensions. Marketplace rows require a semantic product bridge unless a stable product/SAP key is preserved and validated in the actual response.
- Ecom state-sales reads expose state, units/value, and per-platform breakdown; deeper city/SKU reads add geography and product dimensions.
- Ecom's current account/profile and CLI expose platform scopes but no canonical company switch. Do not infer an OMS company match from account id, platform access, or JIVO branding.
- Ecom Shipment Planner is 403-gated for the verified account, and sales-invoice line lookup currently returns an upstream HANA 500.

## Join contract table

| Canonical key | OMS field | Ecom field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | login company, order `company`, SAP `category`, branch/BPL context | no canonical company field or switch proven | Dated external alias/tenant table; source system; never raw numeric id | **Incomplete** |
| `item_key` | `item_code` / `ItemCode`, name, category, pack fields | declared SAP item field; marketplace product identifier or label | Preserve a redacted Ecom sample; then require company/database + item name + pack/UOM and a semantic bridge where no stable code exists | **Candidate; Ecom row shape not yet retained** |
| `party_key` | `card_code` / `CardCode`, category, party name | declared distributor/BP field and platform-distributor code | Preserve a response sample; then require company/category/database + exact code; name only validates | **Candidate; Ecom row shape not yet retained** |
| `warehouse_key` | `warehouse_code`, `WhsCode`, dispatch-from | declared SAP warehouse field | Preserve a response sample; then require company/database + warehouse alias + unit/grain | **Candidate; Ecom row shape not yet retained** |
| `sap_document_key` | `DocEntry`, `DocNum`, quotation `doc_entry`/`doc_num`, `sap_doc_number` | declared invoice entry/number and distributor order/invoice ids | Preserve a response sample; require same SAP object type + company/database + id kind; never cross-type equality | **Candidate; unsafe and unverified unqualified** |
| `oms_order_key` | local `id`, `order_number` | no proven OMS order id; marketplace PO/shipment ids are separate | Explicit bridge through a qualified SAP document or stored external reference | **Missing direct key** |
| `platform_key` | party chain/category where present, such as HANA `U_Chain` | platform slug | Dated alias map; validate party/distributor relationship | **Candidate** |
| `geography_key` | party/address state, city, zip, dispatch-from | state, city, pincode, distributor geography | Normalized geography reference + company/party + date; pincode string | **Semantic candidate** |
| `stock_sales_reconciliation_key` | item × warehouse stock/open demand/order qty + timestamp | item/SKU × platform/geography inventory/sales/PO qty + period | Product + unit/pack + warehouse/geography + platform + event/as-of time | **Reconciliation only** |
| `observed_at` | order, quotation, SO, invoice, sync dates | report month/year, declared invoice date, or data-version time where returned | Preserve response evidence; then require event type + timezone + source freshness | **OMS proven; Ecom conditional on response evidence** |

## Read-only questions unlocked

1. Which OMS open-order items have low Ecom inventory or weak marketplace availability after product and geography mapping?
2. Which Ecom platform/distributor invoice candidates can be reconciled with OMS invoice-workflow context after a live OMS SAP-invoice identifier, company/database, and id kind are proven?
3. Do OMS HANA stock and Ecom SAP stock agree for the same item, warehouse, company/database, unit, and extraction time?
4. Which OMS parties map to Ecom platform distributors, and what downstream sales or inventory do those mappings report?
5. Which states or cities show Ecom demand that is not supported by OMS open-order, stock, or dispatch-from context?
6. Where does an OMS order/quotation status disagree with downstream Ecom evidence, after resolving the correct SAP object and expected lag?

## Gaps/do-not-assume

- Do not claim a shared database, direct API bridge, or running federated query.
- Do not join raw numeric company or account ids. OMS company `1` and Ecom account id values are source-local.
- Do not infer an Ecom company scope; no canonical company switch is proven.
- Do not equate `DocEntry` with `DocNum`, or compare quotation, sales-order, and A/R-invoice numbers as the same object.
- Do not equate OMS `order_number` with marketplace PO, appointment, shipment, or distributor-order ids.
- Do not join dashboard product names to OMS item codes when a stable Ecom product code is missing or unproven without a reviewed mapping.
- Do not treat OMS stock, Ecom stock, marketplace inventory, open-order demand, sales, or DOH as the same metric.
- OMS invoice history is dead/unregistered; Ecom invoice-line detail is upstream-broken. Neither gap may be represented as an empty audit trail.
- OMS role-gated/empty queues and Ecom Shipment Planner 403s are visibility states, not zero activity.
- The Ecom 138 count includes one retained legacy route; only 137 are current SPA GETs.

## Validation checklist

- [ ] Establish canonical company/database scope on both sides; keep Ecom unresolved until proven.
- [ ] Profile SAP item and CardCode overlap, including category, names, pack, and duplicates.
- [ ] Validate warehouse-code and unit equivalence at a single extraction time.
- [ ] Classify every document by SAP object type and ID kind before matching.
- [ ] Test OMS order → quotation log → SAP object mappings before seeking an Ecom document.
- [ ] Build reviewed product aliases for Ecom dashboard rows without a proven stable product code.
- [ ] Build platform, distributor, and geography alias tables with dated provenance.
- [ ] Define metric grains and lag windows before stock/sales/order reconciliation.
- [ ] Preserve role-gated, 403, 404-dead, upstream-error, empty, and stale states.
- [ ] Publish matched, ambiguous, conflicting, and unmatched counts; keep all source access read-only.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[OMS_HUB]] · [[ECOM_HUB]] · [[OMS_MAP]] · [[OMS_VERIFICATION]] · [[OMS_Orders]] · [[OMS_Stock]] · [[OMS_Sales_Quotation]] · [[OMS_Invoices]] · [[ECOM_MAP]] · [[ECOM_APP_SURVEY]] · [[ECOM_CLI_ENDPOINT_GAP]] · [[READ_ONLY_LAW]]
