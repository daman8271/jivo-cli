---
title: Factory to Jivo Desk Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connections, factory, jivo-desk, product-identity, availability, price, reconciliation, read-only]
---

# Factory to Jivo Desk Connection

> Evidence and contracts in this note are current as of 2026-07-19 and are governed by [[READ_ONLY_LAW]].

## Connection verdict

**A released, exact product-identity bridge now connects Factory and jivo-desk.** Both CLIs consume the same versioned artifact under [[CLI/product-identity/README|Product Identity Bridge]]. Operational joins no longer decide identity from product names.

The bridge is a local, read-only contract rather than a service that writes into either source system:

- Marketplace listing key: `platform + listing_id`.
- Factory item key: `company + SAP schema + item_code`.
- Product key: reviewed JID, or a reviewed local product key where no valid JID exists.
- Price-group names remain display/grouping metadata; every listing is resolved separately because one group can contain different physical packs.

This qualification is mandatory. A bare code such as `FG0000315` identifies three different products across Beverages, Mart, and Oil, so the Factory CLI rejects it unless the company is supplied or all qualified matches are explicitly requested.

## Released coverage

Dataset `2026-07-19.1` records:

- **114/114 price groups accounted:** 113 active and one retired.
- **334/334 source membership rows accounted:** 333 distinct `platform + listing_id` identities.
- **333/333 listings resolved:** zero unresolved and zero ambiguous listings.
- **151/151 JIDs accounted:** reviewed aliases and conflicts are explicit.
- **1,906/1,906 observed Factory FG/FB/SL items accounted** as company- and schema-qualified identities.
- **333/333 listing resolutions have Factory bindings:** 266 unique Factory items are linked to the current price catalogue; 1,640 are explicitly `not_in_price_scraping_scope`.
- **666 reused bare Factory codes documented:** zero unknown collision rows.
- **431 heterogeneous queue entries outside the current price master recorded separately:** they are not falsely labelled as current mapped listings.

The independent verifier checks the source hashes, schema, identity sets, collision accounting, release status, reviewed exceptions, and consumer-critical hazards. The current released artifact passes **74,761 checks** with SHA-256 `ec0998527760a9e47450d0a7c81d1216b299ecaade069a08c6b02c932de7a5b9`.

Both consumers also pin detached attestation SHA-256 `ae8d1ad9892d20f6d2e5f36eba3c54488f78788b6f4fab496c9d7b296e49b6ac`. On every operational load they recompute the map and all six frozen evidence hashes. Editing only the map, its source-hash claims, a reviewed decision, or a bundled evidence snapshot therefore exits `6`; the map cannot approve its own replacement.

## CLI behavior

### jivo-desk

`price`, `avail`, `compare`, and `match` preserve the source listing ID and enrich rows only through an exact bridge lookup. Supplying `--sku` requires an exact registered identifier: a qualified listing identity, JID/product key, or exact upstream price-SKU code. Arbitrary product-name text exits with guidance to use `product search`. Catalogue-wide reads preserve mapped, unmapped, and missing-ID rows instead of name-joining them.

The local `product` command group provides `resolve`, `search`, `verify`, and `coverage`. Search may help a human discover a candidate, but it cannot establish an operational join.

### Factory

The local `product` command group provides `resolve`, `search`, `catalog`, `verify`, and `coverage`. It reads the same released map, validates the map before use, understands reviewed JID aliases and nullable-JID products, and fails closed on source or identity drift.

Factory resolution always returns qualified company/schema/item identities. A reused bare item code requires `--company`; `--all-companies` is the explicit way to inspect every collision.

## Proven hazard cases

| Case | Unsafe interpretation | Released resolution |
|---|---|---|
| `FG0000315` | One globally unique Factory SKU | Beverages Shikanji 160 ml, Mart Extra Virgin 1+1 L, and Oil Vedaka Extra Virgin 500 ml remain three qualified identities |
| `CANOLA 3L` | One physical SKU for every platform | Amazon single 3 L resolves to `JID-0116`; Flipkart 3 × 1 L resolves to `JID-0016` |
| Sano 1 L group | Amazon and Flipkart are the same variant | Amazon Extra Light and Flipkart Classic remain separate products and Factory bindings |
| Jivo Water 500 ml | Choose one company by text similarity | Both reviewed Mart and Beverages Factory equivalents remain qualified bindings |

## Read-only questions unlocked

1. Which exactly mapped Factory items have stock or recent dispatch evidence while their marketplace listings are observed out of stock?
2. Which listing-level pack or variant explains a price difference inside a human-readable price group?
3. After a qualified Factory transfer or dispatch, how long until the exact listing appears available by platform and pincode?
4. Which marketplace observations remain outside the current identity map, without inventing a name-based link?

## Boundaries and remaining work

- The released scope proves the current price master and the observed Factory FG/FB/SL namespaces. A future source listing, queue promotion, or previously unseen sellable prefix requires a new collected dataset and release verification.
- A future release must generate a new detached attestation and deliberately update both compiled consumer trust anchors; copying an alternate map alone is rejected.
- Factory products outside the price-scraping catalog are accounted as outside that scope; they are not claimed to have marketplace listings.
- Carton-to-piece and other UOM conversion ratios remain `not_proven`; the bridge does not invent quantity arithmetic.
- Marketplace availability is an observation, not physical Factory stock. Reconciliation must retain both source values and their timestamps.
- Warehouse-to-pincode/service-area mapping remains a separate dated contract.
- The bridge never writes to Factory, the scraper, Ecom, or any other JIVO source.

## Validation checklist

- [x] Release a reviewed listing-to-product-to-qualified-Factory bridge.
- [x] Publish mapped, ambiguous, unresolved, collision, and outside-scope counts.
- [x] Reject bare cross-company Factory codes.
- [x] Remove fuzzy-name identity decisions from operational jivo-desk commands.
- [x] Verify both consumers against the same released map and source hashes.
- [x] Preserve source data and keep all generated artifacts inside JivoGPT.
- [ ] Add dated warehouse/site-to-pincode mappings when business evidence supports them.
- [ ] Add UOM conversions only when their source and effective date are proven.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[FACTORY_HUB]] · [[JIVO_DESK_HUB]] · [[FACTORY_MAP]] · [[FACTORY_VERIFICATION]] · [[DESK_CLI]] · [[CLI/product-identity/README|Product Identity Bridge]] · [[DATA_SOURCES]] · [[READ_ONLY_LAW]]
