---
title: EXIM to Jivo Desk Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connection, exim, jivo-desk, price, drr, read-only]
---

# EXIM to Jivo Desk Connection

## Connection verdict

**Semantic price and availability reconciliation only.** EXIM supplies dated commodity, packing, tax-inclusive, and JIVO pack rates plus upstream stock context. jivo-desk supplies independent file-backed marketplace price, MRP, availability, price-match, and DRR observations. The connection can answer margin-pressure and market-availability questions after an explicit product mapping, but it has no proven stable row key and no running federated join.

## Why they connect

- EXIM answers what a commodity or JIVO pack cost/rate looked like on a date.
- jivo-desk answers what marketplace listings cost, whether they were in stock, and what the DRR/price-match files observed.
- Comparing them can expose price gaps, potential margin pressure, and upstream-versus-market availability patterns while preserving both independent sources.

## Evidence from system A

System A is EXIM. As of 2026-07-19 it exposes **65 printed CLI tools**. [[API-INVENTORY]] contains 67 read-labelled rows but repeats `GET /dc/`, yielding **66 unique read-labelled routes**.

The ambiguous `GET /sap_sync/open-grpos/` is excluded. Its sync namespace and `open_grpos:[sync]` permission leave open the possibility that a GET refreshes SAP, as documented in [[sap_sync_open-grpos]]. This price/availability edge does not need it.

Relevant EXIM evidence:

- [[daily-price_range]] exposes commodity, factory price, packing cost, tax-inclusive per-kg/per-litre values, and date.
- [[jivo-rate_range]] exposes `commodity`, human `pack_type`, pack `rate`, and date.
- [[items_fg]] exposes SAP item code, description, brand, variety, pack factor, and pack unit that could seed a reviewed product bridge.
- [[sap-sync_inventory]] and [[sap-sync_finished-inventory]] expose upstream warehouse/category totals.

EXIM is scoped to Jivo Wellness; that source scope must remain attached to every observation.

## Evidence from system B

System B is jivo-desk. [[DESK_CLI]] documents eight operational file-backed commands plus an exact product group and explicit freshness metadata. [[SOURCES]] and the implementation show that platform rows vary by marketplace and retain their raw fields alongside normalized market observations.

jivo-desk now preserves `platform + listing_id` and exact-enriches current-master rows with reviewed product/JID and qualified Factory item keys through [[CLI/product-identity/README|Product Identity Bridge]]. Operational filters never join by name; `product search` remains candidate-only. An EXIM item still needs its own company/pack evidence before equality with one of those Factory bindings is claimed.

Its temporal semantics also differ by shelf:

- live platform sweeps retain structured `result.json` plus last-good only; a historical `--date` can still return the current structured snapshot with an explicit note;
- price-match history carries dated rows;
- the DRR panel is a fixed monthly snapshot with its own `as_of`, window, platform max date, and file mtime.

## Join contract table

| Canonical key | A field | B field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | implicit Jivo Wellness scope | no company field on normalized marketplace rows | explicit product ownership/scope mapping | **Missing evidence — low** |
| `product_key` | `item_code` plus `item_name`, brand, pack fields | exact listing/product key plus qualified Factory bindings | prove EXIM-to-Factory company/item equivalence, platform, brand, variant, pack size/count | **Bridge available; EXIM equivalence still candidate** |
| `commodity_pack_key` | `commodity` + `pack_type` | normalized product text / price-match `sku` | commodity taxonomy, pack volume, pack count, variant, brand | **Semantic join — medium-low** |
| `price_observation_key` | rate/cost field + `date` | price/MRP or Jivo-reference/rival price + observation date | same pack/UOM, tax basis, platform, pincode/geography, freshness | **Reconciliation join — medium after mapping** |
| `availability_context_key` | item/category warehouse stock + source date | mapped product + platform + pincode + `in_stock` + file mtime | product bridge, geography, inventory grain, timing window | **Semantic/reconciliation join — low** |
| `drr_context_key` | mapped item/commodity and dated rate context | DRR item label/platform + panel `as_of` and window | product bridge, platform, common window, unit conversion | **Semantic join — low** |

## Read-only questions unlocked

- For a manually validated product/pack, how does EXIM's dated JIVO rate compare with observed marketplace price or MRP?
- Which mapped commodities show a rising cost context while marketplace prices remain flat?
- Which mapped products have upstream stock context but repeated marketplace OOS observations?
- Is a surprising price comparison based on a fresh live sweep, a last-good fallback, dated price-match history, or a fixed DRR panel?

## Gaps/do-not-assume

- Desk search text is never a join key. Use its exact bridge identities, then separately prove the EXIM-to-qualified-Factory relationship.
- Similar names do not prove identical brand, variant, volume, or units-per-case.
- EXIM costs/rates and marketplace listing prices can use different tax and pack bases.
- A requested historical Desk date does not guarantee historical structured sweep rows; inspect its note and file mtime.
- National/modal price-match rows may lack pincode, while live sweep rows may be per-pincode.
- Upstream warehouse stock is not marketplace availability, and a difference is not automatically an error.
- No running federated join exists; `/sap_sync/open-grpos/` stays excluded.

## Validation checklist

- [ ] Create a human-reviewed bridge from EXIM SAP item/pack attributes to each Desk platform listing identity.
- [ ] Require exact brand, variant, pack volume, pack count, and UOM checks before accepting a mapping.
- [ ] Normalize per-kg, per-litre, and per-pack amounts, including GST and currency basis.
- [ ] Carry platform, pincode/geography, event date, file mtime, fallback state, and missing-source state.
- [ ] Refuse historical claims when Desk only has current live/last-good structured rows.
- [ ] Publish mapping confidence, unmatched listings, and one-to-many collisions.
- [ ] Use only safe EXIM reads and keep `/sap_sync/open-grpos/` excluded.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[EXIM_HUB]] · [[JIVO_DESK_HUB]] · [[EXIM_MAP]] · [[DESK_CLI]] · [[READ_ONLY_LAW]]
