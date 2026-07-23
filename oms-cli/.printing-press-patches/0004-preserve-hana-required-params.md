---
title: Preserve the OMS HANA Required Query Parameters
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, oms, cli, printing-press, hana, api-contract]
---

# Patch 0004 — preserve the live HANA query-parameter contracts

- **Why:** live verification on 2026-07-19 proved that `/api/hana/so/` always returns HTTP 400 without `card_code`, and `/api/hana/product-so/` always returns HTTP 400 without `item_code`. The earlier generated commands declared neither input.
- **Change:** `oms-spec.yaml` declares `card_code` and `item_code` as required query parameters. `internal/cli/hana_so.go` exposes required `--card-code` and sends `card_code`; `internal/cli/hana_product-so.go` exposes required `--item-code` and sends `item_code`. Both files carry explicit hand-patch provenance.
- **Files:** `oms-spec.yaml`, `internal/cli/hana_so.go`, `internal/cli/hana_product-so.go`, plus regenerated command metadata derived from the spec.
- **Re-apply after regeneration:** preserve the spec parameters before printing. If a print uses an older spec, restore both flags, required-input checks, query-map assignments, examples, and descriptions in the generated command files.
- **Verification:** `hana so --help` must list `--card-code`; `hana product-so --help` must list `--item-code`. The recorded live proof is 15 rows for a valid customer and HTTP 200 for a valid item as of 2026-07-19; do not repeat live calls merely to validate a reprint.

Linked: [[CLI/oms-cli/.printing-press-patches/README|OMS patch ledger]] · [[CLI/oms-cli/README|OMS CLI]] · [[docs/oms/OMS_VERIFICATION|OMS_VERIFICATION]] · [[docs/oms/OMS_Stock|OMS Stock]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
