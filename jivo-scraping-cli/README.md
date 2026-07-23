---
title: "jivo-scrape"
created: 2026-07-19
updated: 2026-07-20
project: jivogpt
type: reference
tags: [jivogpt, jivo-desk-cli, cli]
---

# jivo-scrape — formerly jivo-desk

**The counter clerk at the JIVO data godown.**

Every morning this VPS fills a godown with price sweeps, availability scans,
price-match sheets, and DRR numbers across 10 quick-commerce platforms.
`jivo-desk` is the clerk at the window: you ask a question, it walks the
shelves for you and hands back exactly the answer — today's data, yesterday's,
or any dated snapshot. You never dig through the boxes yourself.

- **Live** — reads the real files the pipeline writes, at query time. No copies, no staging, no sync lag.
- **Read-only** — the clerk never rearranges the godown. Zero writes to any data directory.
- **Uniform** — every command takes `--json` (same `{"meta":...,"results":...}` envelope as the other JIVO CLIs) and `--date today|yesterday|YYYY-MM-DD`.

## Install

```bash
ln -s /root/jivo-desk-cli/bin/jivo-desk ~/.local/bin/jivo-desk   # already on PATH
jivo-desk doctor        # sanity check: can it see the godown?
```

Runs on stock Python 3 — zero third-party dependencies.

## Commands

| Command | Question it answers |
|---|---|
| `jivo-desk price --sku <exact-id> [--platform p] [--pincode z]` | What does this exact product identity sell for now? |
| `jivo-desk avail [--sku <exact-id>] [--platform p]` | Where is it in stock / OOS, or show the whole catalogue? |
| `jivo-desk compare --sku <exact-id>` | One exact identity, all member listings side by side |
| `jivo-desk match [--sku <exact-id>] [--pincode z]` | Price-match rows, optionally narrowed by exact listing membership |
| `jivo-desk drr` | Daily-run-rate panel numbers |
| `jivo-desk today` | What landed today: which sweeps ran, rows, freshness |
| `jivo-desk files [--date D]` | Every file the pipeline produced that day |
| `jivo-desk doctor` | Health: sources present, fresh, readable |
| `jivo-desk product resolve <IDENTIFIER>` | Resolve an exact price SKU, listing, JID/product key, or qualified Factory key |
| `jivo-desk product search <TEXT>` | Find name candidates without using names as join keys |
| `jivo-desk product verify` | Prove the shared identity map is released, complete, and internally consistent |
| `jivo-desk product coverage` | Show exact map accounting and all zero-tolerance release gates |

## Examples

```bash
jivo-desk price --sku JID-0116 --platform amazon
jivo-desk compare --sku "CANOLA 3L" --json 2>/dev/null | jq .results
jivo-desk match --sku "amazon:B0CCVF1XVS" --json
jivo-desk avail --platform blinkit --json
jivo-desk today --date yesterday
jivo-desk files --date 2026-07-15
jivo-desk product resolve "CANOLA 3L"
jivo-desk product resolve "amazon:B078T3Q3SH" --json
jivo-desk product search "canola bottle"
jivo-desk product verify
```

`CANOLA 3L` works because it is an exact upstream price-SKU code, not because
of fuzzy name matching. Free text such as `canola oil bottle` exits `4` and
directs the operator to `product search`.

## Exact product identity

`product resolve` never joins by a display name. It accepts only a stable exact
identifier:

- canonical JID or product key;
- full price-SKU key or its exact source product code;
- full listing key, or `platform:listing-id`;
- full qualified Factory key: company + SAP schema + item code.

If the same short price product code exists in more than one source namespace,
the shorthand exits `5` as ambiguous and names the full keys to use.

A price SKU can group different physical packs. Resolving it therefore returns
every member listing separately, with that listing's own canonical product/JID
and qualified Factory bindings. The inverse is also preserved: if one exact
platform listing appears in two human price groups, its `price_sku_keys` carries
both memberships while `price_sku_key` identifies the primary group. A bare
Factory item code such as `FG0000317` is intentionally rejected because the
same code can mean different products in different company schemas. Factory
unit conversion stays explicitly `not_proven`/null until evidence supports a
ratio; the CLI does not invent carton arithmetic.

The shared map is discovered in this order: `--identity-map`,
`JIVO_PRODUCT_IDENTITY_MAP`, then `CLI/product-identity/v1/product-identity-map.json`
by walking repository parents. An alternate path selects a release bundle; it
does not make that bundle trusted. The co-located `release-attestation.json`
must match the digest compiled into `jivo-desk`, must identify the requested
map, and must reproduce the SHA-256 of the map and every frozen evidence
artifact. `jivo-desk` only reads these files. Every product command fails
closed with exit code `6` if the attestation is missing/edited, evidence drifts,
the map is unreleased, uses an
unsupported schema major, has a broken reference, or reports any unresolved,
ambiguous, conflicted, or unaccounted identity. A reviewed product that truly
does not exist in Factory may carry an explicit `reviewed_absent` record, but
only after all three Factory scopes were checked and evidence was retained.

The operational `price`, `compare`, `avail`, and `match` commands use the same
released map. Their `--sku` value is an exact JID/product key, price code/key,
qualified listing key, or qualified Factory key. A plain name exits `2` and
points to `jivo-desk product search`; it is never used to filter source rows.
Each source row keeps its authoritative `listing_id`, `listing_id_kind`, and
qualified `listing_key`, then receives exact-only product/JID, price-membership,
qualified Factory-binding, dataset-version, and map-hash fields. Price-match
history retains the literal CSV `listing_id`; an empty value stays empty rather
than being reconstructed from `sku` text.

Catalogue-wide `avail` (no `--sku`) keeps every source row and labels identity
as `mapped`, `unmapped`, or `missing_listing_id`. This is an accounting state,
not a fuzzy matching opportunity.

## Where the clerk looks (data sources)

See [[CLI/jivo-scraping-cli/SOURCES|SOURCES.md]] for the full inventory. In short:

| Shelf | Path |
|---|---|
| Live sweep results (10 platforms) | `/opt/ecom-intel/platforms/<p>/result.json` (+ `.last-good`) |
| Daily snapshot — today | `/opt/ecom-intel/today/` |
| Daily snapshot — yesterday | `/opt/ecom-intel/today.prev/` |
| Price-match | `/opt/ecom-intel/data/pricematch/daily.csv`, `history.csv` |
| DRR panel | `/root/jivo-drr-panel/build/panel.json` |
| QC reviews / doctor | `/opt/ecom-intel/reviews/`, `/opt/ecom-intel/logs/doctor/` |
| Excel deliverables | `/opt/ecom-intel/output/*.xlsx` (listed, not parsed) |
| Shared product identity | `CLI/product-identity/v1/product-identity-map.json` + pinned co-located release attestation/evidence bundle |

## Guarantees

1. **Never writes** outside its own repo. All data dirs opened read-only.
2. **Freshness is explicit** — every answer carries the source file's mtime;
   stale data is flagged, never silently served.
3. **Yesterday means yesterday** — `--date yesterday` resolves to `today.prev/`
   or the dated file, whichever the source keeps.
4. **Names never become joins** — `product search` surfaces candidates; every
   operational `--sku` and `product resolve` requires a stable exact identifier.
5. **Factory codes stay qualified** — company + SAP schema + item code are kept
   together so a reused bare code cannot silently map to the wrong product.
6. **Release data cannot approve itself** — the detached attestation is pinned
   in code, and all four operational SKU commands verify it and its evidence
   files before reading live rows. No CLI or environment trust override exists.


## Archive commands (jivo-scrape, 2026-07-19)

Renamed **jivo-scrape** (alias `jivo-desk` still works). The root is any checkout of
`daman8271/ecom-intel` — set `JIVO_SCRAPE_ROOT=/path/to/checkout` (default `/opt/ecom-intel`).
Five commands reach the months-deep archive, not just today's godown:

| Command | Question it answers |
|---|---|
| `jivo-scrape history --platform p [--sku q] [--from D] [--to D]` | price/stock rows over the months (`data/<p>/history.csv`) |
| `jivo-scrape asof --platform p --date D` | what the archive held on date D (git time machine; notes when only the tracked view exists) |
| `jivo-scrape runs [--date D] [--limit N]` | which sweeps ran when (sweep-commit ledger) |
| `jivo-scrape vault [--section S] [--name PAT] [--show REL]` | daily/monthly/competitor/pricematch notes since 2026-05-21 |
| `jivo-scrape reports [--show REL]` | ad-hoc investigation reports + coverage ground-truth runs |

Git access is read-only by construction (verb allow-list: `rev-list show log rev-parse ls-tree`).

Linked: [[CLI/jivo-scraping-cli/PLAN|Build plan]] · [[CLI/jivo-scraping-cli/SOURCES|Sources]] · [[docs/SCRAPING_CLI|SCRAPING_CLI]] · [[docs/DESK_CLI|DESK_CLI]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
