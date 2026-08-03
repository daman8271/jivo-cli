---
title: Preserve Factory Oil Production Release Company Scope
created: 2026-07-19
updated: 2026-08-03
project: jivogpt
type: patch
tags: [jivogpt, factory, cli, printing-press, barcode, company-scope, api-contract]
---

# Patch 0005 — scope the Oil production release to JIVO_OIL

> **Revised 2026-08-03.** The original entry recorded the contract as "the
> upstream view returns HTTP 503 when pagination is omitted" and mandated an
> unconditional `page`/`page_size` pair. Live re-verification **disproved that
> cause**. The 503 is a **company-scope** fault, not a pagination fault. The
> pagination flags are kept — they are useful and were never shown to be
> harmful — but they are no longer the reason the endpoint fails, and a future
> maintainer must not treat them as the fix. The July finding was reached by
> probing under the CLI's `JIVO_MART` default, which masks the real cause.

- **Why:** `/barcode/production-release-oil/` is backed by the HANA view
  `PRODUCTION_RELEASE_OIL`, which exists **only in the `JIVO_OIL_HANADB`
  schema**. Called under any other company code the upstream raises
  `(259, 'invalid table name: Could not find table/view PRODUCTION_RELEASE_OIL
  in schema <company>')` and the API returns HTTP 503. Because the CLI defaults
  to `JIVO_MART`, the endpoint looks permanently broken to anyone who does not
  pass `--company oil`.
- **Live evidence (2026-08-03), isolating both variables:**

  | Company | Pagination | Result |
  |---|---|---|
  | `JIVO_OIL` | omitted | **HTTP 200**, rows returned (doc_entry 12778, post_date 2026-08-01) |
  | `JIVO_OIL` | `page=1&page_size=100` | **HTTP 200** |
  | `JIVO_MART` | `page=1&page_size=100` | HTTP 503 — view missing in `JIVO_MART_HANADB` |
  | `JIVO_BEVERAGES` | `page=1&page_size=100` | HTTP 503 — view missing in `JIVO_BEVERAGES_HANADB` |

  The first row — 200 with pagination omitted — is what falsifies the original
  claim.
- **Change:** keep `--page` / `--page-size` on
  `internal/cli/barcode_production-release-oil.go` with their `1` / `100`
  defaults, and additionally make the command's Oil-only nature explicit: help
  text must state that this command requires `--company oil`, and a 503 from
  this endpoint must be surfaced to the operator as "this view exists only in
  the Oil company" rather than as a generic upstream outage.
- **Files:** `internal/cli/barcode_production-release-oil.go`.
- **Re-apply after regeneration:** restore the two integer flags and their
  defaults, and restore the company-scope note in both the command help and the
  503 error path. Do not drop the pagination flags on the strength of this
  revision — they were proven *not to be the cause*, not proven harmful.
- **Read-only boundary:** unchanged. This is a GET-only report command.
- **Verification:** command help must list both flags and must name the Oil
  company requirement; a dry run must still emit `page=1` and `page_size=100`
  without issuing a network request. Any live check must pass `--company oil`.

Linked: [[CLI/factory-cli/.printing-press-patches/README|Factory patch ledger]] · [[CLI/factory-cli/README|Jivo Factory CLI]] · [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
