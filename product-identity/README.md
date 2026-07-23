---
title: JIVO Product Identity Bridge
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, identity, sku, factory, price-scraping, read-only]
---

# JIVO Product Identity Bridge

This directory owns the read-only bridge between the price-scraping catalogue,
marketplace listing IDs, JIVO product identities, and company-qualified Factory
items. Both `jivo-desk` and `jivo-factory-pp-cli` consume the same versioned map.
They do not keep independent copies.

## The non-negotiable keys

- Marketplace listing: `platform + listing_id`.
- Factory item: `company_code + sap_schema + item_code`.
- A bare Factory code such as `FG0000315` is never a global identity.
- A human SKU name is display/search text. It is never an operational join key.

The bridge is resolved per marketplace listing. One price-monitoring group can
contain physically different packs, and one listing can be observed by more
than one price-monitoring group. Those facts are preserved rather than hidden.

## Layout

- `v1/sources/` — JivoGPT-owned read-only snapshots plus source fingerprints.
- `v1/review-decisions.json` — narrow, evidence-backed decisions that cannot be
  safely inferred from flat names or unqualified SAP codes.
- `v1/product-identity-map.schema.json` — the published v1 shape.
- `v1/product-identity-map.json` — generated shared map.
- `v1/release-attestation.schema.json` — strict detached-attestation shape.
- `v1/release-attestation.json` — trusted map and six-evidence-artifact digest set.
- `tools/collect_sources.py` — GET/read-only inventory collector.
- `tools/generate_map.py` — deterministic map generator.
- `tools/attest_release.py` — semantic verification plus deterministic detached-attestation generator/checker.
- `tools/verify_map.py` — independent semantic and coverage gate.

## Current release

Dataset `2026-07-19.1` is released with map SHA-256 `ec0998527760a9e47450d0a7c81d1216b299ecaade069a08c6b02c932de7a5b9` and detached-attestation SHA-256 `ae8d1ad9892d20f6d2e5f36eba3c54488f78788b6f4fab496c9d7b296e49b6ac`:

| Surface | Accounted | Expected | Gap |
|---|---:|---:|---:|
| Price groups | 114 | 114 | 0 |
| Active price groups | 113 | 113 | 0 |
| Source membership rows | 334 | 334 | 0 |
| Distinct listings/resolutions | 333 | 333 | 0 |
| JIDs | 151 | 151 | 0 |
| Observed Factory FG/FB/SL items | 1,906 | 1,906 | 0 |

All 333 listing resolutions have evidence-backed Factory bindings. Those bindings reach **266 unique Factory items**; the remaining **1,640 Factory items** are explicitly `not_in_price_scraping_scope`, not silently unmatched or falsely assigned. The release has zero unresolved listings, zero ambiguous listings, zero open JID conflicts, and zero unknown Factory-code collisions. Its 431 review/unpriced/junk queue entries are likewise explicitly outside the current price master; they are accounted but not falsely described as mapped listings.

Verify the checked-in release from the repository root:

```bash
python3 -m unittest discover -s CLI/product-identity/tests -q
python3 CLI/product-identity/tools/attest_release.py --check
python3 CLI/product-identity/tools/verify_map.py --json
```

The current verifier performs 74,761 structural, source-fingerprint, identity-set, collision, evidence, and coverage checks.

The release attestation is detached from the map and records the exact map
digest plus the digest and bundle-relative URI of all six frozen evidence
artifacts. Both production CLI consumers compile the attestation digest as a
trust anchor. They strict-parse it, recompute the map digest, and recompute every
evidence digest before loading any identity. Therefore an edited map cannot
approve itself by editing its own status or checksum, and an edited map plus a
regenerated attestation remains untrusted. Missing files, absolute paths, `..`
escapes, source drift, or a different alternate bundle all fail closed with
exit code `6`.

## Release rule

A map may say `release_status: released` only after the verifier recomputes the
source inventories and proves every in-scope price product and every primary or
alternate listing is accounted for exactly. Ambiguity is an error. A reviewed
absence is explicit; it is never replaced with a fuzzy guess.

`attest_release.py` creates a candidate attestation only after the independent
semantic verifier is clean. Creation does **not** make a release trusted. A
reviewer must verify the candidate and deliberately update the compiled trust
anchor in each consumer. There is no CLI flag or environment variable that can
replace that trust anchor at runtime.

The Factory inventory scope is the observed sellable product families exposed
by the read-only Factory APIs: barcode OITM `FG/FB`, plus the broader SAP
product lookup `FG/FB/SL`. Raw materials and packaging are outside this product
bridge unless a future authoritative source explicitly adds them.

All collection uses GET or file reads. Generated files are written only inside
this JivoGPT-owned directory, in accordance with [[READ_ONLY_LAW]].

Linked: [[CLI/README|CLI Hub]] · [[FACTORY__JIVO_DESK]] · [[ECOM__JIVO_DESK]] · [[READ_ONLY_LAW]] · [[ROADMAP]]
