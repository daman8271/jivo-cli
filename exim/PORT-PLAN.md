---
title: "Port Plan — absorb everything the other EXIM CLI has that mine doesn't"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: plan
tags: [jivogpt, exim, plan]
---

# Port Plan — absorb everything the other EXIM CLI has that mine doesn't

Source of truth: `github.com/daman8271/exim` (the other Claude's complete build). Goal: make my `~/exim` the **union** — keep all my strengths, add every real capability theirs has. Read-only stays absolute.

## Gap list (theirs → mine)
| # | Gap | Action |
|---|---|---|
| 1 | Native `auth login` (email/pw → JWT stored in config) | Port `jivo_login.go` → `exim_login.go` (adapted) |
| 2 | Client **hard-blocks non-GET** (mine exposes Post/Put/Patch/Delete) | Patch `client.go do()` to refuse non-GET |
| 3 | `/sap-sync/customer/balance/` (startDate,endDate) | add endpoint + probe + regen |
| 4 | `/sap-sync/customer/ledger/` (cardCode) | add endpoint |
| 5 | `/sap-sync/vendor/ledger/` (cardCode) | add endpoint |
| 6 | `/stock-status/stock-summary/` | add endpoint |
| 7 | `/license/dfia-license-export-lines/dropdown/` (file_no) | add endpoint |
| 8 | `OPERATOR-GUIDE.md` (agent-facing) | write mine |
| 9 | Root `CLAUDE.md` read-only vow (agents auto-read) | write mine |
| 10 | `.printing-press-patches/` discipline | record client-guard + login as patches |

Kept as MY advantages (theirs lacks): `/rates/*` market family (6), detail endpoints (6), `/jivo-rate/range/`, license line lists, the guarded `raw` escape hatch, enriched real-sample docs, and the GET-that-writes hardening rule. The earlier `./exim grpos` exception was retired after the underscore `/sap_sync/` namespace became categorically blocked.

## Phases
- **A** (main loop) — probe 5 new endpoints live → samples → add to `endpoints.json` + OpenAPI
- **B** (main loop) — regen CLI; port `auth login`; patch client GET-guard; re-wire; rebuild
- **C** ✅ docs: 5 endpoint docs enriched + OPERATOR-GUIDE + CLAUDE vow + pages updated (4-agent Workflow)
- **D** (main loop) — verify: build, `exim auth login`, test 5 new commands, prove client refuses non-GET, no regressions
- **E** — organize + memory + offer push

## Read-only guarantee after port = enforced THREE ways (matching theirs)
1. Spec/OpenAPI has zero write operations.
2. Client `do()` refuses any non-GET method (new).
3. `./exim raw` blocklists GET-that-writes; hard-rule docs + memory.

---
## STATUS (2026-07-19)
- A ✅ 5 endpoints added (customer/vendor ledgers, customer-balance, stock-summary, dfia-dropdown) — live
- B ✅ native `auth login` (config-based JWT) + client non-GET hard-block (compiled, chokepoint) + patches recorded
- C ✅ docs complete; D ✅ verified; E ✅ organized + memory updated. UNION COMPLETE.
- Kept my superset: /rates/* (6), detail endpoints, jivo-rate/range, guarded raw reads, hardening rule. Retired the GRPO sync-route exception.

Linked: [[CLI/exim/INDEX|INDEX]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
