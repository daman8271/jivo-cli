---
title: "Jivo Factory CLI — what changed in v0.4.0"
created: 2026-08-03
updated: 2026-08-03
project: jivogpt
type: guide
tags: [jivogpt, factory-cli, migration]
---

# What changed in v0.4.0 (2026-08-03)

The factory app grew a lot between 2026-07-19 and now. This CLI was re-scraped
against the live API and regenerated. **Read the "commands that disappeared"
section if you have scripts or habits built on v0.3.0.**

## The short version

| | v0.3.0 (July) | v0.4.0 (verified) |
|---|---|---|
| Endpoints in the spec | 183 | **386** |
| Leaf commands | 183 | **417** across 47 groups |
| MCP tools | 183 | **386**, 0 non-GET |
| Tools declaring parameters | 19 | **328** (141 with a required param) |
| Response type declared correctly | 50 of 154 | all 386 |
| Endpoints live in the API | 152 | 238 bare + ~170 parameterised detail routes |
| Go toolchain | 1.26.4 (GO-2026-5856) | **1.26.5**, 0 vulnerabilities |

**Command names did not change.** All 168 endpoints shared with v0.3.0 keep their
exact command names, so existing scripts and MCP `endpoint_id` references keep
working. Only genuinely new endpoints got new names.

## Commands that disappeared, and where the capability went

**These eight WMS commands are gone because the endpoints now return HTTP 404
on all three companies.** They were **analytics** endpoints, and — verified
against the live 2026-08 surface — **nothing replaces them.** An earlier draft
of this document claimed the capability had simply moved to `warehouse bst`;
that was wrong, and adversarial re-verification disproved it.

The three families that grew are not substitutes:

- `warehouse bst` / `bom-requests` / `fg-receipts` is a **workflow** system
  (raise a transfer, approve it, scan boxes, mark it through the gate). It does
  not report stock positions. The `gate-core` BST family it supposedly replaced
  is also still live in all three companies.
- `warehouse wms/*` is a **third, unrelated** app for physical rack/pallet
  scanning on the floor.

| Removed command (v0.3.0) | Honest status |
|---|---|
| `warehouse wms-dashboard` | **Lost.** No equivalent. |
| `warehouse wms-stock-overview` | **Lost.** `committed`, `on_order` and `last_purchase_price` are not exposed anywhere in the 2026-08 surface. |
| `warehouse wms-stock-movements` | **Lost.** The SAP-side movement feed has no replacement. |
| `warehouse wms-warehouses-summary` | Partly — `warehouse wms-warehouses` still lists warehouses, without the summary aggregates. |
| `warehouse wms-batches-expiry` | Partly — `/wms/inventory/` and `/wms/pallets/` carry `lotNumber` and `expiryDate`, but only for floor-scanned stock, not SAP batches. |
| `warehouse wms-billing-overview` | **Lost.** Received-vs-billed reconciliation has no replacement. |
| `warehouse wms-sales-orders-backlog` | **Lost.** No equivalent. |
| `warehouse wms-transfers-overview` | **Lost** as analytics. `warehouse bst` tracks individual transfers but reports no overview. |

If you relied on any of the five marked **Lost**, say so — that is a real gap in
the factory app, not a CLI limitation, and it needs raising with whoever owns
the warehouse module.

Two live-verified traps in the new BST commands:

- **`bst-get` only resolves transfers the current company originated.** The same
  id that returns 200 under `--company oil` returns 404 under Mart; use
  `bst-incoming` for transfers coming the other way.
- **`bst-sap-transfers --document-type INVOICE` returns an empty list unless
  `--search` is also given**, even though 69 of Oil's 167 BSTs are
  invoice-sourced. Treat `search` as required in INVOICE mode.

## Commands deliberately NOT shipped

These exist in the API but are excluded on purpose. Each has a reason you can
check.

| Not shipped | Why |
|---|---|
| `marketplace settings` | **Reading it writes.** `GET /marketplace/settings/?channel=X` is a Django `get_or_create` — it creates a settings row for any channel that lacks one. Correction **C-0007**, patch **0007**. |
| `marketplace orders-resolve` | Natural-key lookup (`channel` + `order_id`) on a verb that plausibly writes. Unproven, therefore excluded. |
| `security-checks …/security/view`, `weighment …/weighment/view`, `raw-material-gatein …/po-receipts/view` | Same `get_or_create` shape — a child record keyed by its parent's gate-entry id. Never probed, because the only way to test is to call one for a parent with no child, which is the act that would create it. |
| `grpo draft` | Returns HTTP 500 on all three companies. A command that only ever errors is worse than an absent one. |
| everything under `production-planning` | **The module has no backend.** Every path 404s, including the root — the app ships Production Planning screens whose API is not deployed. Not a CLI limitation. |

## Gotchas worth knowing

- **`--company` matters more than it used to.** 220 endpoints behave identically
  across all three companies, but `marketplace` is enabled only for `JIVO_MART`
  (403 `WRONG_COMPANY` elsewhere — module gating, not permissions), and
  `barcode production-release-oil` works **only** under `--company oil`, because
  its HANA view exists only in the Oil schema.
- **`blowing` data lives in Oil.** The module is enabled in all three companies,
  but Mart and Beverages return empty lists. Use `--company oil`.
- **`--channel` is required across `marketplace`** and is restricted to the
  observed values (`FLIPKART`, `AMAZON`). It is deliberately not free-text:
  channel is the exact key that triggers the `get_or_create` above.
- **Most endpoints do not paginate.** About 70% return a bare JSON array with no
  envelope; only ~15 use `page`/`page_size`. Pagination flags appear only where
  they do something.
- **Four different error shapes** come back from this API (`{error}`,
  `{detail}`, `{code,error}`, and DRF field-error dicts). There is no single
  error contract.
- **`marketplace reconciliation`** works, but returns HTTP 500 if given
  `from_date`/`to_date`. Those params are therefore not exposed.

## Read-only, still

Nothing here writes. 351 write endpoints were found and excluded, including 141
paths that accept both a read and a write on the same URL — those publish their
GET and nothing else. The MCP surface remains read-only and fails closed on any
non-GET method in both execution paths (patch 0003).

Linked: [[CLI/factory-cli/README|Jivo Factory CLI]] · [[CLI/factory-cli/research/SPEC-NOTES-2026-08|Spec decisions & evidence]] · [[CLI/factory-cli/.printing-press-patches/README|Patch ledger]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
