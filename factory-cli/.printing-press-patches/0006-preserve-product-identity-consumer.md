---
title: Preserve the Shared Product Identity Consumer
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, factory, cli, printing-press, product-identity, read-only]
---

# Patch 0006 — preserve the shared product identity consumer

- **Why:** the Factory API's bare `item_code` is not globally unique. The same code can name different products in JIVO_MART, JIVO_OIL, and JIVO_BEVERAGES, while marketplace listing IDs have their own platform-qualified namespace. A generated endpoint tree cannot safely infer the cross-system identity contract.
- **Change:** keep the hand-authored top-level `product` family (`resolve`, `search`, `catalog`, `verify`, and `coverage`) and its registration in `internal/cli/root.go`. It reads the one shared external v1 artifact from `CLI/product-identity/v1/product-identity-map.json`, `JIVO_PRODUCT_IDENTITY_MAP`, or `--identity-map`; it performs no API request.
- **Fail-closed contract:** reject missing, malformed, draft, unsupported-major, incomplete, unresolved, ambiguous, or unproved-absence maps with exit code 6. Require the detached release attestation whose digest is compiled into the consumer; recompute the attested map and all six frozen evidence hashes, with no CLI or environment bypass. Validate all release coverage gates, including active SKUs, every source-membership row, active listings, and observed queue accounting. Every released listing, including retained retired listings, must resolve exactly once. A verified Factory mapping requires an evidence-backed qualified binding; a reviewed absence requires all three Factory scopes plus explicit evidence. Every qualified Factory item also requires exactly one disposition row, and every reused bare item code requires an explicit collision record.
- **Qualification invariant:** never apply the Factory API's historical JIVO_MART default to product identity. Bare Factory codes require explicit `--company`/`JIVO_FACTORY_COMPANY`; `--all-companies` returns every collision as `company_code + sap_schema + factory_item_key`. Text is search-only and is never a resolution join.
- **Selection-safety output:** preserve plural price-SKU memberships, the listing pack fingerprint, resolution provenance, `primary_for_scope`, conversion state, Factory accounting disposition, and collision relation. A `not_proven` conversion stays null; the consumer must never invent a unit ratio or make the first returned binding look authoritative.
- **Files:** `internal/cli/product_identity.go`, `internal/cli/product_identity_test.go`, `internal/cli/testdata/product-identity-map.json`, the narrow registration/company-explicit tracking in `internal/cli/root.go`, product capability entries in `internal/cli/which.go`, the operator contract in `README.md`, and rebuilt workspace binaries `jivo-factory-pp-cli` / `jivo-factory-pp-mcp`.
- **Re-apply after regeneration:** restore the command file, root registration, explicit-company tracking, `which` discovery entries, and README identity section, then rebuild both workspace binaries. Do not copy the shared map into this generated tree; both CLIs must consume the same release artifact.
- **Verification:** run the focused product identity tests plus the full Go test/vet/build suite. The repo-local integration test must load the released shared map, preserve the Flipkart double membership and nullable conversion, prove `FG0000315`/`FG0000391` remain company-qualified different-product hazards, and prove a bare Factory code never defaults to Mart. Adversarial tests must reject source-hash drift, Shikanji cross-company rewrites, Sano product collapse, missing/edited attestations, edited evidence snapshots, and alternate unbundled maps.

Linked: [[CLI/factory-cli/.printing-press-patches/README|Factory patch ledger]] · [[CLI/product-identity/README|Product identity contract]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
