---
title: jivo-desk Connection Hub
created: 2026-07-19
updated: 2026-07-20
project: jivogpt
type: connector-hub
tags: [jivogpt, connections, jivo-desk, marketplace, product-identity, files, read-only]
---

# jivo-desk Connection Hub

jivo-desk is the independent file-backed marketplace lens. It reads the VPS godown produced by daily sweeps and exposes price, availability, comparison, price-match, DRR, delivered-file, health/freshness, and exact product-identity views.

## Current connector profile

| Property | Current evidence |
|---|---|
| Command surface | 8 operational commands (`price`, `avail`, `compare`, `match`, `drr`, `today`, `files`, `doctor`) plus `product resolve/search/verify/coverage` |
| Authentication | None; access is governed by local/VPS file permissions |
| Runtime home | VPS godown; the Mac copy is archive/reference and degrades to missing-source states |
| Marketplace coverage | Nine live marketplace families across ten source directories, including a retained legacy Instamart path |
| Upstream status | Phase-3 implementation was imported from an uncommitted, unpushed VPS working tree |

## Canonical fields

| Canonical field | jivo-desk candidates | Qualification required |
|---|---|---|
| `item_key` | reviewed JID/product key plus qualified Factory bindings from the released bridge | Exact bridge lookup; Factory identity keeps company + SAP schema + item code |
| `platform_key` | source platform slug | Dated alias registry; preserve raw slug |
| `geography_key` | pincode | Exact string; never numeric-coerce |
| `price` | selling price and MRP fields | Currency, seller/listing, pincode, source, and observation grain |
| `availability` | in-stock/OOS/availability fields | Platform, pincode, listing, and source freshness |
| `observed_at` | requested date, file date, file mtime | File evidence outranks a mere requested-date label |
| `listing_key` | platform + authoritative source `listing_id` | Exact composite identity; retain listing-ID kind, raw row, and product text |

Operational `--sku` resolution is exact: listing key, JID/product key, price key/code, or qualified Factory key. Plain names exit with guidance to `product search`; search results are candidates and cannot establish a join. The safe observation grain is `date × platform × listing_id × pincode`, with the raw row and file provenance attached.

## Five connection edges

| Other connector | Best connection | Note |
|---|---|---|
| EXIM | Commodity/JIVO rates versus marketplace price, availability, and DRR | [[EXIM__JIVO_DESK]] |
| Factory | Supply/dispatch availability versus observed marketplace availability and price | [[FACTORY__JIVO_DESK]] |
| OMS | Internal stock/order demand versus observed availability, price-match, and DRR | [[OMS__JIVO_DESK]] |
| Ecom | Two marketplace lenses reconciled by product, platform, pincode, date, and freshness | [[ECOM__JIVO_DESK]] |
| JSAP | Market exceptions versus existing tickets, tasks, people, and decision context | [[JIVO_DESK__JSAP]] |

## Safe adapter contract

1. Read source files only; never edit, rename, mark processed, or trigger a sweep.
2. Emit the actual source path class, file date, file mtime, fallback/last-good state, and requested date.
3. Keep raw product text, listing ID, listing-ID kind, and platform slug beside exact identity enrichment.
4. Preserve `mapped`, `unmapped`, and `missing_listing_id` states; never reconstruct a missing identity from a name.
5. Treat `doctor` and `today` as freshness/health evidence, never as source mutation controls.

## Exclusions and open evidence gaps

- `price`, `avail`, and `compare` read the current result or last-good fallback even when a non-today date is requested. They must not be described as point-in-time historical observations without a date-backed file.
- `drr --date` can label output rather than prove historical measurement. Only file-backed inventories and retained dated artifacts support historical claims.
- Product text still has no authority, but the released [[CLI/product-identity/README|Product Identity Bridge]] provides reviewed listing-to-product-to-qualified-Factory joins for the current master.
- The 431 review/unpriced/junk queue entries outside the current price master are accounted separately and are not claimed as mapped operational listings.
- Platform names need aliasing: jivo-desk uses slugs such as `swiggy-instamart` and `flipkart-minutes` that differ from Ecom.
- Known implementation rough edges include broken-pipe exit behavior and raw tracebacks for invalid dates; command failure must remain an access state.

## Evidence anchors

[[DESK_CLI]] · [[CLI/jivo-scraping-cli/README|jivo-scrape CLI README]] · [[CLI/product-identity/README|Product Identity Bridge]] · [[DATA_SOURCES]] · [[READ_ONLY_LAW]]

---
Linked: [[/README|README]] · [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[CLI/product-identity/README|Product Identity Bridge]] · [[EXIM_HUB]] · [[FACTORY_HUB]] · [[OMS_HUB]] · [[ECOM_HUB]] · [[JSAP_HUB]]
