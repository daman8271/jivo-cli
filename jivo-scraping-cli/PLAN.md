---
title: "jivo-desk — multi-phase build plan"
created: 2026-07-19
updated: 2026-07-20
project: jivogpt
type: plan
tags: [jivogpt, jivo-desk-cli, plan]
---

# jivo-desk — multi-phase build plan

Goal #92 in the owner's goal tracker. Built 2026-07-19 via multi-agent orchestration.

## Phase 1 — Map the godown ✅
Inventory every daily data source on this VPS into [[CLI/jivo-scraping-cli/SOURCES|SOURCES.md]]:
platform sweeps, today/ + today.prev/ snapshots, pricematch CSVs, DRR panel,
reviews, doctor logs, Excel outputs. Capture the JSON shapes agents build against.

## Phase 2 — Scaffold & repo ✅
Package skeleton (`jivo_desk/` with dispatcher + per-command modules), README,
this plan, `.gitignore`, entry script. Private GitHub repo
`daman8271/jivo-desk-cli`, pushed immediately.

## Phase 3 — Implement (multi-agent) 🔨
Three parallel builder agents, each owning disjoint files:
- **Agent A** `sources/sweeps.py` + `commands/{price,avail,compare}.py`
- **Agent B** `sources/{pricematch,drr}.py` + `commands/{match,drr}.py`
- **Agent C** `sources/today.py` + `commands/{today,files,doctor}.py`

Contract: stdlib-only Python 3, read-only, `--json` envelope + `--date` on every
command, freshness (mtime) in every `meta`.

## Phase 4 — Adversarial verify (multi-agent)
Independent verifier agents run the finished CLI against the **raw files** for
today AND yesterday and try to catch it lying: wrong price, missed OOS, stale
data served as fresh, broken `--json`. Confirmed defects → one fixer agent.

## Phase 5 — Ship
Symlink onto PATH, smoke-test real queries, final push, hand the owner the link.

## Phase 6 — Shared product identity ✅

Consume the single released v1 identity artifact from
`CLI/product-identity/v1/product-identity-map.json`. The `product` command group
resolves exact identifiers across price scraping, canonical products/JIDs, and
company/schema-qualified Factory items; name text remains search-only.

The consumer validates the whole release before serving any result: supported
schema, released status, bidirectional price-SKU membership, complete listing
resolutions, valid product and Factory references, explicit physical-pack
bindings (or a three-scope evidenced `reviewed_absent` decision), zero
unresolved/ambiguous/open-conflict gates, and matching source identity sets.
Any failure exits `6` rather than serving a plausible but unsafe join.

The final consumer also requires the co-located detached release attestation
whose SHA-256 is compiled into the CLI. It recomputes the map and all six frozen
evidence-artifact hashes from normalized bundle-relative paths. The production
CLI exposes no flag or environment override for that trust anchor. Real-process
tests prove that `product verify`, `price`, `avail`, `compare`, and `match` all
reject a missing/edited attestation, source drift, the Shikanji cross-company
FG0000315 substitution, the collapsed Sano split, and an edited map plus edited
checksum.

Independent tests cover the critical mixed-pack case (`CANOLA 3L`: Amazon
single 3L versus Flipkart 3 × 1L), qualified Factory keys, exact listing IDs,
the one-listing/multiple-price-group case, nullable-but-real products without a
JID, candidate-only name search, map discovery precedence, and every
fail-closed gate.

Operational price, comparison, availability, and price-match rows now extract
only the live source's authoritative listing-ID field (`asin`, `fsn`, `fk_pid`,
`variant_id`, `prid`, `sku_id`, or `listing_id`). Exact `--sku` resolution
expands a stable identifier to member platform/listing tuples before filtering;
names exit `2` with a `product search` direction. Rows retain their observed ID
and receive exact-only JID/product, price-membership, qualified Factory-binding,
identity-state, dataset-version, and map-hash fields. Catalogue availability
keeps unmapped/missing-ID rows visible, and price-match never invents an ID from
its display SKU column.

## Deliberate non-goals
- No writes to any data directory (the clerk never rearranges the godown).
- No xlsx parsing in v1 (`files` lists them; sweep JSON has the same rows).
- No network calls — this CLI is purely local-file.

Linked: [[docs/DESK_CLI|DESK_CLI]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
