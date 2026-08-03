---
title: "Factory rescrape and reprint — 183 → 386 endpoints"
created: 2026-08-03
project: jivogpt
type: worklog
tags: [jivogpt, factory-cli, printing-press, mcp, rescrape]
---

# Factory rescrape, 2026-08-03

Re-scraped ji.jivo.in, re-studied every domain, reprinted the CLI and MCP.
Commit `25776d3` on branch `factory-cli-v0.4.0-rescrape` (unmerged).
Methodology captured as the `jivo-rescrape` skill.

## Result

183 → 386 endpoints · 417 leaf commands · 386 MCP tools, 0 non-GET ·
params declared 19 → 328 · response types correct 50/154 → all 386 ·
0 unexplained regressions · all 8 patches verified holding.

Command names unchanged for all 168 shared endpoints, so existing scripts
and MCP `endpoint_id` references keep working.

## New modules the CLI had never exposed

marketplace (Flipkart/Amazon fulfilment: 2,171 orders, 2,130 dispatches, SAP
delivery notes, portal-vs-physical reconciliation), blowing (bottle blowing
with a make-vs-buy engine — July: 1.24 lakh bottles, ₹9.87 lakh, verdict MAKE,
₹40,609 saved on 50g), returnable-items, person-gatein, attendance, labour,
security-checks, weighment, and four gate-in families.

## Four things found silently broken

1. **MCP connector dead 10 days** — token expired 07-24, every call 401.
   Undetected because the health check pinged `initialize`, which answers fine
   with dead credentials. Fixed, verified, daily rotation cron installed.
2. **Production Planning has no backend** — every route 404s including the
   module root. The SPA ships screens whose API is not deployed.
3. `/grpo/draft/` → 500 on all three companies.
4. `/marketplace/reconciliation/` → 500 when given date params.

Items 2–4 are the factory app's own; documented with repro steps in
`factory-cli/research/SPEC-NOTES-2026-08.md`.

## The incident

`GET /marketplace/settings/?channel=X` is a Django `get_or_create`. Probing it
with invented channel values **created six production rows**, including junk
`INVALID_XYZ` (id 7) which still needs a human to delete — RULE 0 blocks the
CLI from doing it. Recorded as correction **C-0007**, enforced by patch 0007,
and now rule 1 of the rescrape skill.

## Corrections to prior research

- Patch 0005 blamed missing pagination for a 503; it is **company scope**. The
  HANA view `PRODUCTION_RELEASE_OIL` exists only in `JIVO_OIL_HANADB`. July
  probed under the Mart default and mis-attributed the cause.
- marketplace is **module-gated** to JIVO_MART (403 `WRONG_COMPANY`), not
  permission-gated, not missing data.
- blowing is routed in all three companies but only holds data in Oil.

## Pipeline bugs I introduced and caught

Five, all caught by checks rather than review: refutations treated as deletions
(would have dropped 28 working commands); prose keyword-matching killing a live
endpoint; a completeness fix resurrecting three unsafe endpoints; a hardcoded
`Company-Code` making `--company` a silent no-op; and an invariant check that
asserted a header's *presence* rather than its *value*, so it passed while the
bug was live.

The last one is the lesson: I wrote the check, the check passed, the feature
was broken. Only running the real command against the real API caught it.

## Coverage caveat

The printing-press dogfood matrix was **deliberately not run** — it sends
fabricated parameter values, which is what created the junk row. Commands are
spec-verified, build-verified, 26-invariant-verified and sample-tested per
module; they are not all individually live-exercised.

Linked: [[CLI/factory-cli/DOMAIN-GUIDE-2026-08]] · [[CLI/factory-cli/MIGRATION-2026-08]] ·
[[CLI/factory-cli/research/SPEC-NOTES-2026-08]] · [[docs/READ_ONLY_LAW]]
