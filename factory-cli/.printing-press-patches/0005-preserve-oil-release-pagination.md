---
title: Preserve Factory Oil Production Release Pagination
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, factory, cli, printing-press, barcode, pagination, api-contract]
---

# Patch 0005 — preserve required pagination for Oil production release

- **Why:** the upstream HANA-backed `/barcode/production-release-oil/` view returns HTTP 503 when pagination is omitted. The command file records this as live-verified on 2026-07-19.
- **Change:** `internal/cli/barcode_production-release-oil.go` always sends `page` and `page_size`, defaults them to `1` and `100`, and exposes `--page` and `--page-size` for callers. This is a hand-tuned command-file change; `spec.yaml` and `tools-manifest.json` currently declare no parameters for the endpoint.
- **Files:** `internal/cli/barcode_production-release-oil.go`. The spec and generated manifest are evidence of why a normal regeneration can erase the behavior.
- **Re-apply after regeneration:** restore the two integer flags, defaults, and unconditional query-map entries. Do not make pagination conditional unless a new live verification proves the upstream view no longer requires it.
- **Verification:** command help must list both flags; a dry run must show `page=1` and `page_size=100` without issuing a network request.

Linked: [[CLI/factory-cli/.printing-press-patches/README|Factory patch ledger]] · [[CLI/factory-cli/README|Jivo Factory CLI]] · [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
