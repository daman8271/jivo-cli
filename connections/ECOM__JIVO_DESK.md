---
title: Ecom to jivo-desk Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connections, ecom, jivo-desk, marketplace, reconciliation, read-only]
---

# Ecom ↔ jivo-desk

Evidence below is repository-verified as of 2026-07-19 unless a narrower date is stated.

## Connection verdict

**The strongest current marketplace reconciliation edge, but still not an automatic row join.** Ecom supplies the application/API view of marketplace sales, inventory, pricing, DRR, fulfilment, platform reports, SAP distribution, products, and geography. jivo-desk supplies file-backed listing sweeps, price-match history, availability, DRR-panel output, and source freshness.

There is no running federated service between Ecom and jivo-desk as of 2026-07-19. The versioned [[CLI/product-identity/README|Product Identity Bridge]] now supplies exact current-master listing/product identities using Ecom master evidence; platform alias, geography, metric-grain, and truthful time semantics are still required for a fact comparison.

## Why they connect

- Both systems expose marketplace-facing product, platform, price, availability/inventory, geography, and date-like dimensions.
- Ecom represents curated application data and operational analytics; jivo-desk represents raw/current sweep files and dated price-match or health artifacts.
- Comparing them can reveal stale application data, coverage gaps, price disagreement, platform alias drift, and source failures while retaining both values and their provenance.

## Evidence from system A — Ecom

- [[ECOM_MAP]] and [[ECOM_CLI_ENDPOINT_GAP]] establish **138 registered GET commands as of 2026-07-19: 137 current SPA reads plus one retained legacy `month-on-month-sale` route**. The legacy route remains callable but is not evidence of current SPA use.
- The current Ecom MCP is a code-orchestration bridge around the Cobra CLI and local helpers, not 138 separately typed MCP tools; integrations must dispatch through the interface that actually exists.
- [[ECOM_APP_SURVEY]] records current platform slugs including `amazon`, `amazon_mp`, `blinkit`, `swiggy`, `zepto`, `bigbasket`, `flipkart`, `flipkart_grocery`, `zomato`, `citymall`, `jiomart`, `meta`, and `callcenter`.
- The current spec exposes top-SKU and SKU-level dashboard reads, product master reads, price/comparison/DRR/SOH-DOH/inventory views, state/city/SKU drill-downs, pincode mapping, landing rates, fulfilment health, platform metadata, and data-version endpoints.
- Ecom also exposes SAP item, distributor `CardCode`, inventory, warehouse, and sales-invoice reads. These can help build a product bridge but do not prove that a marketplace SKU text equals a SAP item code.
- Current Ecom evidence does **not** prove a canonical company switch or a universal `company_key`. The API/CLI surface is token- and permission-scoped; a company mapping must not be inferred from route labels such as JM or from account groups.

## Evidence from system B — jivo-desk

- [[DESK_CLI]] documents eight operational commands plus the exact `product` group over `/opt/ecom-intel` and the DRR-panel build, with explicit file mtime, staleness, partial, last-good, and missing-source metadata.
- The sweep normalizer preserves each platform's authoritative listing ID and enriches exact matches with listing key, reviewed product/JID, price memberships, qualified Factory bindings, dataset version, and map hash.
- Operational `--sku` filters require exact bridge identities. Only `product search` uses text, and its candidates never become joins automatically.
- The platform registry differs materially from Ecom: jivo-desk uses `amazon-fresh`, `amazon-now`, `flipkart-minutes`, `instamart`, and `swiggy-instamart`; `instamart` is a stale legacy directory while `swiggy-instamart` is the live sweep. Exact shared labels still need scope validation.
- `price`, `avail`, and `compare` read current structured sweep rows even for historical `--date` requests. `match` has dated CSV history; `drr` is one fixed monthly snapshot; price-match may have no pincode dimension.

## Join contract table

| Canonical key | A field | B field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | No canonical company switch proven in current Ecom evidence | No company field | Explicit external company attribution, if any; never infer from token, route label, or platform | Missing evidence |
| `item_key` | exact Ecom platform product code, master-product row, SAP item row | `platform + listing_id`, reviewed product/JID, qualified Factory bindings | Released bridge plus matching platform/grain, brand, pack, UOM, and effective date | Exact for the released listing set; fact-grain validation still required |
| `platform_key` | Ecom platform slug | jivo-desk sweep directory / row `platform` | Dated alias registry and commercial-surface validation | Proven shared dimension; candidate equivalence, medium |
| `geography_key` | pincode mapping; state/city detail filters and rows | listing `pincode`; some price-match rows have none | String-preserved pincode, state/city reference, and proof the endpoint has that grain | Candidate join; medium where present |
| `observed_at` | month/year filters, latest-month metadata, version stamps, report dates | file mtime, snapshot date, price-match date, DRR `as_of`/window | Event time versus ingestion time, timezone, data window, and fallback state | Proven time evidence; alignment required |
| `price_measure` | price dashboard, comparison dashboard, landing rate, marketplace analytics | `price`, `mrp`, `jivo_ref`, rival modal/min/max | Same item/pack, platform alias, geography, price basis, tax, and observation time | Reconciliation only; medium |
| `availability_measure` | inventory, SOH/DOH, fulfilment, expiry, marketplace views | tri-state listing `in_stock` / availability text | Same item, platform, location, time, and metric definition; inventory is not listing availability | Reconciliation only; medium |
| `drr_measure` | platform DRR endpoint and sales windows | fixed DRR panel rollups | Same units/window and proven data lineage to avoid circular comparison | Semantic/reconciliation only; low |
| `source_freshness_key` | latest-month/version/source metadata where returned | exact path, mtime, partial/last-good/missing state | Connector, endpoint/file, extraction time, and access state | Strong provenance join; high |

## Read-only questions unlocked

1. For a validated product and platform mapping, does Ecom's price view agree with the latest jivo-desk listing sweep or dated price-match record?
2. Which Ecom products have inventory or sales evidence but no current jivo-desk listing, OOS listings, or missing pincode coverage?
3. Is a surprising Ecom metric corroborated by an independent current sweep, or is one side stale, partial, gated, or using a different period?
4. Which platform aliases or product mappings produce the largest unmatched populations?
5. Do Ecom DRR and the jivo-desk DRR panel disagree after their units, windows, and upstream lineage are proven comparable?

## Gaps/do-not-assume

- Do not promote `product search` text to an Ecom SKU or SAP item. Use only the released exact bridge and report identities outside its current scope.
- Do not equate Ecom `swiggy` with jivo-desk `swiggy-instamart`, or `flipkart_grocery` with `flipkart-minutes`, without sampled evidence. `amazon_mp`, `amazon-fresh`, and `amazon-now` are also distinct labels until mapped.
- Do not treat `price/avail/compare --date <past>` as historical jivo-desk data; those commands still read current rows.
- Do not use a national/modal price-match row as pincode evidence when the source has no pincode column.
- Do not assume Ecom inventory, SOH, or DOH is the same fact as marketplace listing availability.
- Do not claim Ecom has a canonical company switch; current evidence does not establish one.
- Do not call the retained legacy Ecom route “current SPA coverage.”
- Do not call correlated DRR values independent until source lineage is known.

## Validation checklist

- [x] Build and version a product bridge using stable marketplace IDs plus Ecom/Factory product-master evidence for the current price master.
- [ ] Create a dated platform alias registry and test exact overlaps plus non-overlapping slugs.
- [ ] Preserve pincode as a string and distinguish national, state, city, and pincode grains.
- [ ] Capture Ecom period/version metadata and jivo-desk file mtime/fallback state on every comparison.
- [ ] Use dated price-match/history sources for historical questions; reject current-sweep substitution.
- [ ] Define each price, inventory, availability, and DRR metric before computing a delta.
- [ ] Measure matched, unmatched, ambiguous, stale, partial, and gated populations separately.
- [ ] Verify whether the sources are operationally independent before describing a comparison as corroboration.
- [ ] Use GET/read commands only; never invoke uploads, refreshes, target updates, or source-file writes.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[ECOM_HUB]] · [[JIVO_DESK_HUB]] · [[ECOM_MAP]] · [[ECOM_CLI_ENDPOINT_GAP]] · [[ECOM_APP_SURVEY]] · [[DESK_CLI]] · [[READ_ONLY_LAW]]
