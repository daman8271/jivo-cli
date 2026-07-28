# PLAN — Jivo Group Control Panel → Obsidian vault + read-only CLI

**Goal (ledger #81):** reverse-engineer `http://103.89.45.75:9080` into a documented Obsidian vault and a **READ-ONLY** printing-press CLI.
**Hard rule:** LIVE PRODUCTION + admin creds → **never call any write/OTP/export endpoint.** Read/pull/report only. (See `recon/RECIPE.md` blocklist.)

Status keys: ✅ done · 🔄 in progress · ⏳ queued

---

## Phase 0 — Setup & Access  ✅
- ✅ Build `~/software/` workspace (`recon/ vault/ cli/`)
- ✅ Save creds to gitignored `~/software/.env` (+ memory pointer, no plaintext in committed files)
- ✅ Crack Django session login; build reusable `recon/login.sh` + sourceable `recon/jio.sh` (`jget`/`jpost`/`jhead`)
- ✅ Validate 3 API call patterns live (POST-JSON, GET-XHR, GET-query)
- ✅ Record goal #81, save `project_jivo_control_panel` memory
- **Accept:** authenticated read works end-to-end; helpers reusable. ✅

## Phase 1 — Recon & Enumeration  ✅
- ✅ Enumerate all **20 pages** + **62 endpoints**; classify READ vs WRITE vs OTP/EXPORT
- ✅ Write `recon/RECIPE.md` ground-truth brief (auth + endpoints + page→file map + read-only blocklist)
- **Accept:** complete page+endpoint inventory with methods & prefixes. ✅

## Phase 2 — Deep API mapping (multi-agent)  ✅  *(workflow w5amxlep6 — 21 pages, 56 api docs)*
- 🔄 8 domain agents probe every READ endpoint live (smallest range), capture JSON schema
- 🔄 Write `vault/pages/*.md` + `vault/api/*.md` (Obsidian format, trimmed samples)
- **Accept:** every read endpoint has a live-sampled schema doc; every page documented; write endpoints documented-only.

## Phase 3 — Vault assembly (multi-agent)  ✅  *(24 concepts + 00-INDEX + architecture; 0 broken links)*
- 🔄 `vault/00-INDEX.md` (MOC), `vault/architecture.md`, `vault/concepts/*.md` (REALISE, OIH, BAL, COGS, DRR, GT/MT/ROI/ECOM, OILS/BEVERAGES, Wellness-Mart recon)
- 🔄 `[[wikilinks]]` weaving pages ↔ api ↔ concepts
- 🔄 Completeness critic → conditional gap-fill agent
- **Accept:** critic verdict `complete`; all wikilinks resolve; no thin/empty docs.

## Phase 4 — CLI build  ✅  *(jivo CLI, 42 read cmds, printing-press v4.24, LOCAL + READ-ONLY)*
- ⏳ Feed `vault/api/` READ catalog to printing-press as research input
- ⏳ Auth = Django session login (reuse login.sh pattern); config from `.env`
- ⏳ One read command per endpoint group (sales, targets, realise, oih, aging, payments, claims, inventory, master-data …)
- ⏳ **Exclude every write/OTP/export endpoint by construction**
- **Accept:** CLI builds; `--help` lists read commands only; no mutating command exists.

## Phase 5 — CLI verification  ✅  *(live smoke-tests pass; read-only audit PASS; 0 API mutations)*
- ⏳ Smoke-test each command against live API; capture real output
- ⏳ Static audit: grep generated code for POST/PUT/DELETE/save/delete/upload/lock → must be zero write paths
- **Accept:** real command output captured; write-path audit clean.

## Phase 6 — Finalize  ✅  *(README.md written; goal + memory updated)*
- ⏳ `~/software/README.md` (how to open vault in Obsidian + run CLI)
- ⏳ Update goal #81 + memory; optional `git init` (creds already gitignored)
- **Accept:** user can open the vault and run the CLI; nothing left out.

---
### Working order
Do phases in sequence. Phase 2+3 run as one background workflow (Map→Weave→Verify→Fill). On its completion: review critic verdict → if gaps remain, resolve → then Phase 4 (printing-press) → Phase 5 verify → Phase 6 finalize. Update this file's status markers as each phase closes.
