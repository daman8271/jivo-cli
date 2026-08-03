---
title: Exclude Factory GET Endpoints That Mutate
created: 2026-08-03
updated: 2026-08-03
project: jivogpt
type: patch
tags: [jivogpt, factory, cli, printing-press, read-only, security, marketplace]
---

# Patch 0007 — a GET-only surface is not a read-only surface

- **Why:** patch 0003 makes both MCP execution paths fail closed on any method
  other than `GET`. That guard is necessary but **not sufficient**, because at
  least one Factory endpoint mutates production data *on GET*. Filtering by
  HTTP method alone would publish it as a read command in both the CLI and the
  agent-facing MCP surface, where an agent would call it freely.

- **Live evidence (2026-08-03 13:23 IST).**
  `GET /marketplace/settings/?channel=<X>` is a Django `get_or_create`. Reading
  it with a channel that has no row **creates** one:

  | channel | id | updated_at |
  |---|---|---|
  | `FLIPKART` | 1 | 2026-07-17T13:29:41 (pre-existing) |
  | `AMAZON` | 2 | 2026-08-03T13:23:06.212 |
  | `MEESHO` | 3 | 2026-08-03T13:23:06.318 |
  | `JIOMART` | 4 | 2026-08-03T13:23:06.417 |
  | `BLINKIT` | 5 | 2026-08-03T13:23:06.519 |
  | `ZEPTO` | 6 | 2026-08-03T13:23:06.625 |
  | `INVALID_XYZ` | 7 | 2026-08-03T13:23:06.736 |

  Ids 2–7 were created by six sequential GETs, ~100 ms apart, in request order.
  A re-GET of `FLIPKART` left its `updated_at` at 2026-07-17, proving reads do
  **not** touch rows that already exist — so ids 2–7 are genuinely new rows,
  including the junk `INVALID_XYZ`. Row 7 remains in production; removing it
  needs a human in the app or Django admin, since this toolkit has no DELETE.

- **Invariant:** an endpoint may be published as a CLI command or an MCP tool
  only when it is **GET and proven side-effect-free**. Method is a filter, not
  a proof.

- **Further suspects (2026-08-03, NOT probed — deliberately).** The per-domain
  study independently applied this rule and flagged two more endpoints matching
  the `get_or_create` shape (takes a key, returns one object with id/timestamps):

  | Endpoint | Why suspected |
  |---|---|
  | `/security-checks/gate-entries/{id}/security/view/` | `.../view/` on a gate entry that may not yet have a security record |
  | `/weighment/gate-entries/{id}/weighment/view/` | `.../view/` on a gate entry that may not yet have a weighment record |

  These were **not** tested live, because the only way to test is to call them
  with an id lacking a record — which is precisely the act that would create
  one. They stay unpublished until someone reads the Django view server-side and
  confirms. "Unproven" resolves to "excluded", never to "probably fine".

- **Change — three layers, all required:**
  1. `/marketplace/settings/` is **not published**: no CLI command, no MCP tool,
     no entry in `spec.yaml` or `tools-manifest.json`.
  2. Every endpoint that takes a lookup key and returns a single object
     carrying `id`/`created_at`/`updated_at` is treated as **suspected
     `get_or_create`** and must be positively cleared before publication. The
     research notes record the cleared/uncleared status per endpoint.
  3. The MCP tool description for any marketplace read states that channel
     values are a closed set drawn from live data, and no command may pass an
     operator-supplied channel through to a settings-shaped endpoint.

- **Never do this again — the process rule that produced the incident:** the
  rows were created by enumerating invented parameter values against the live
  API to discover which ones it accepts. Do not probe an unknown endpoint with
  a value you have not first observed in a real payload or in the UI bundle.

- **Files:** `spec.yaml` (endpoint absent), `tools-manifest.json` (tool absent),
  the marketplace command files, and the research notes recording the cleared
  set.

- **Re-apply after regeneration:** a fresh print works from the endpoint
  inventory, so if `/marketplace/settings/` re-enters the inventory it will be
  published again. After every print, assert its absence from the command tree
  and the manifest before the tree is used.

- **Verification:** `jivo-factory-pp-cli marketplace --help` must not list a
  `settings` command; `grep -c 'marketplace/settings' tools-manifest.json` must
  be `0`; and a test must assert the manifest contains no path on the
  suspected-`get_or_create` list.

- **Team record:** filed as correction **C-0007** in `harness/corrections/`, so
  every operator's session carries the rule.

Linked: [[CLI/factory-cli/.printing-press-patches/README|Factory patch ledger]] · [[CLI/factory-cli/.printing-press-patches/0003-preserve-mcp-get-only-guards|0003 — MCP GET-only guards]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[CLI/factory-cli/README|Jivo Factory CLI]]
