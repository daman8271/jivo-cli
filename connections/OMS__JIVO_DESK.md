---
title: OMS to jivo-desk Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connections, oms, jivo-desk, reconciliation, read-only]
---

# OMS ↔ jivo-desk

Evidence below is repository-verified as of 2026-07-19 unless a narrower date is stated.

## Connection verdict

**Reconciliation edge, not a fact join.** OMS exposes internal order demand, SAP item codes, warehouse stock, prices, parties, and order dates. jivo-desk exposes independently file-backed marketplace listing price, MRP, availability, pincode, price-match, DRR, and source freshness. They can answer useful supply-versus-market questions only after JivoGPT owns a validated product bridge and aligns the observation windows.

There is no running federated join between these systems as of 2026-07-19. jivo-desk now resolves exact listing identities through a reviewed product/qualified-Factory bridge; equivalence to an OMS `item_code` still requires matching company/schema and pack/UOM evidence.

## Why they connect

- OMS measures internal demand and supply: ordered quantity, pending required quantity, warehouse stock, available stock, open sales orders, and internal price-list values.
- jivo-desk measures the market-facing result: whether a listing is present and in stock, its observed selling price and MRP, pincode coverage, cross-platform price position, and DRR-panel signals.
- At a validated product, geography, and time grain, differences can identify possible stock-distribution gaps, stale market listings, or price exposure. A difference is a finding to investigate, never a value to overwrite.

## Evidence from system A — OMS

- [[OMS_VERIFICATION]] establishes **73 GET entries in the spec, tools manifest, and MCP endpoint registry, but 72 registered runtime endpoint commands as of 2026-07-19**. `invoices history` remains described in the generated surfaces but is deliberately unregistered because the live backend route is absent.
- [[OMS_Stock]] documents OMS HANA stock rows with `item_code`, `item_name`, `warehouse_code`, `warehouse_stock`, `pending_required_qty`, `left_over_stock`, `on_hand`, and `total_on_hand`. Its open-sales-order reads add `DocEntry`, `DocNum`, `CardCode`, dates, and lines containing `ItemCode`, `OpenQty`, `Price`, and `WhsCode`.
- [[OMS_Orders]] documents order detail and stock-check rows with `order_number`, `card_code`, `company`, `party_state`, `created_at`, `delivery_date`, and item-level `item_code`, `required_qty`, and `available_stock`.
- [[OMS_Reports]] shows state-item sales at an `item_code + state + period + order-status` grain and line-level quantity, boxes, litres, and sales value.
- OMS company scope is not a safe join shortcut. The observed login is Jivo Wellness id `1`; Jivo Mart is id `2`, while some SAP/HANA reads appear category- or shared-master-scoped and their Mart behavior remains unverified.

## Evidence from system B — jivo-desk

- [[DESK_CLI]] documents eight operational read commands plus `product resolve/search/verify/coverage` over live VPS files.
- The sweep normalizer preserves `platform + listing_id` and exact-enriches mapped rows with reviewed product/JID and company-qualified Factory bindings. Operational `--sku` is exact; text is confined to candidate-only `product search`.
- `price`, `avail`, and `compare` accept `--date`, but the sweep source retains only current `result.json` and `result.last-good.json` structured rows. Historical requests therefore still read current rows and add a warning; they do not become historical facts.
- `match` is genuinely dated through price-match history, but some price-match rows are national/modal and have no pincode dimension. `drr` is a fixed monthly build whose `--date` flag does not select another snapshot.
- Every result carries file mtime/freshness and partial or last-good fallback state. Those fields are part of the reconciliation key, not display metadata.

## Join contract table

| Canonical key | A field | B field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | OMS login company and row `category`/`company` | No company field | Dated company/category mapping; never infer from a raw id | Missing evidence |
| `item_key` | `item_code` / `ItemCode` plus `item_name` | exact listing/product key plus qualified Factory bindings | Prove OMS company/schema equivalence to the qualified Factory key; validate brand, pack size, UOM, and effective date | Bridge available; OMS equivalence still candidate |
| `platform_key` | No native marketplace platform on core OMS stock/order rows | `platform` | A separate allocation/channel mapping; do not invent a platform from party or warehouse name | Semantic only |
| `geography_key` | `party_state`, address state/city/zip, dispatch branch | listing `pincode`; price-match may be national/modal | Normalized state/pincode reference, leading-zero preservation, and proof that the OMS geography is the relevant fulfilment geography | Candidate join; low |
| `observed_at` | `created_at`, `delivery_date`, `DocDate`, or query time for live stock | source mtime, true snapshot date, DRR `as_of`/window | Same timezone and explicit event-time versus extraction-time semantics | Proven time fields; alignment required |
| `stock_availability_measure` | `warehouse_stock`, `left_over_stock`, `available_stock`, `OpenQty` | `in_stock` tri-state / availability text | Mapped item, relevant warehouse-to-market area, units, order status, and same observation window | Reconciliation only; medium |
| `price_measure` | `basic_price`, line `Price`, or HANA item price-list value | `price`, `mrp`, `jivo_ref`, `rival_modal` | Price basis, tax, pack/UOM, pincode, platform, currency, and timestamp | Reconciliation only; medium |
| `demand_measure` | ordered `qty`/`ltrs`, `pending_required_qty`, state-item sales | DRR panel pace and stock-out-risk fields | Product bridge, unit conversion, platform scope, panel lineage, and identical window | Semantic/reconciliation only; low |

## Read-only questions unlocked

1. For validated product mappings, which marketplace listings are OOS while OMS shows relevant available stock, and are the two observations actually contemporaneous?
2. Which mapped products have OMS pending demand or negative `left_over_stock` together with weak marketplace availability?
3. Where does an OMS internal price basis materially differ from observed marketplace price after pack, tax, platform, geography, and time are aligned?
4. Do state-level OMS order signals and pincode-level listing availability tell a consistent story, with unmatched geographies reported rather than dropped?
5. Is a surprising answer explained by a partial/last-good jivo-desk sweep, an OMS role gate, or genuinely divergent data?

## Gaps/do-not-assume

- Do not join OMS `item_code` from name text. Start from the released exact bridge, then prove OMS company/schema and pack/UOM equivalence.
- Do not describe `price`, `avail`, or `compare --date <past>` as historical; those commands still serve current structured sweep rows.
- Do not equate internal OMS stock with marketplace availability. Warehouse allocation, fulfilment geography, listing state, and timing can legitimately differ.
- Do not treat OMS company ids as universal. OMS id `1` means Jivo Wellness and id `2` means Jivo Mart; other systems use those numbers differently.
- Do not treat an empty OMS role-gated result, a missing jivo-desk file, or a partial fallback as zero.
- Do not assume the DRR panel is independent of OMS or Ecom inputs until its lineage is profiled; circular reconciliation would not be validation.

## Validation checklist

- [ ] Build a JivoGPT-owned product bridge from OMS SAP code to marketplace listing identity; retain raw names and effective dates.
- [ ] Validate brand, pack, UOM, and company/schema for a sample before enabling equality joins.
- [ ] Capture OMS query time and jivo-desk source mtime/snapshot date in every result.
- [ ] Separate current sweep reconciliation from genuinely dated price-match/review evidence.
- [ ] Add an explicit warehouse/branch-to-geography rule and publish unmatched rows.
- [ ] Verify units and price basis before computing deltas or ratios.
- [ ] Record access state such as live, empty, role-gated, partial, last-good, missing, or stale.
- [ ] Use only the registered read surfaces; never call an OMS mutation or write to jivo-desk source files.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[OMS_HUB]] · [[JIVO_DESK_HUB]] · [[OMS_VERIFICATION]] · [[OMS_Stock]] · [[OMS_Orders]] · [[OMS_Reports]] · [[DESK_CLI]] · [[READ_ONLY_LAW]]
