---
title: "JIVO EXIM — Reverse-Engineering & CLI Build Plan"
created: 2026-07-18
updated: 2026-07-19
project: jivogpt
type: plan
tags: [jivogpt, exim, plan]
---

# JIVO EXIM — Reverse-Engineering & CLI Build Plan

**Goal:** Fully understand exim.jivo.in (JIVO's export/import + stock/tank/contract/license platform), document every page and every API endpoint as identical Obsidian-linked MD files, then build a CLI (via `/printing-press`) that can fetch any data from the app.

**Web:** https://exim.jivo.in  ·  **API:** https://eximbe.jivo.in  ·  **User:** Daman (id 34)
**Stack:** Vite + React SPA (Radix UI, charts, excel) · nginx · JWT auth (`/account/login/` → `access`+`refresh`, `Authorization: Bearer`, refresh via `/account/login/refresh/`)

---

## Phase 0 — Recon & Setup ✅ DONE
- [x] Pull SPA shell + JS bundles, confirm build (Vite/React)
- [x] Extract API base URL (`https://eximbe.jivo.in`) + auth contract
- [x] Enumerate ~40 frontend routes + ~70 backend endpoints statically
- [x] Confirm login works via curl; cache token; capture full permission/resource map
- [x] Workspace: `pages/ endpoints/ _raw/ scripts/ cli/ notes/` + gitignored secrets + auth helpers

## Phase 1 — Authenticated API crawl (main loop, GET-only, SAFE)
- [ ] Build curated GET-safe endpoint list (exclude POST/PUT/DELETE, sync-triggers, logout, move, dispatch, create)
- [ ] Crawl every read endpoint with token → save real JSON to `_raw/api/<slug>.json`
- [ ] For parameterized endpoints, pull IDs from list endpoints first, then a detail sample
- [ ] Record status, params, response shape per endpoint → `_raw/api/_manifest.json`

## Phase 2 — Live UI exploration (browser via /browse, serial)
- [ ] Walk every sidebar page, note dashboards/filters/toggles/buttons, map page → endpoints
- [ ] Capture the page inventory + anything static analysis missed (AI chat, search, etc.)

## Phase 3 — Documentation fan-out (multi-agent Workflow)
- [ ] `pages/<page>.md` — one per page, identical template, `[[wikilinks]]` to its endpoints
- [ ] `endpoints/<endpoint>.md` — one per endpoint, identical template (method, path, auth, params, response schema, sample, which page uses it)
- [ ] `INDEX.md` (Map of Content) + `API-INVENTORY.md` (all endpoints table) + `DOMAIN-MODEL.md` (resources/permissions)

## Phase 4 — CLI via /printing-press
- [ ] Feed consolidated API inventory into Printing Press
- [ ] Generate read-first `exim` CLI (stock, tanks, contracts, licenses, rates, accounts, reports)
- [ ] Write ops documented but NOT wired to runnable commands in v1 (safety)
- [ ] Build + shipcheck

## Phase 5 — Verify & hand off
- [ ] Run CLI against live API, confirm real data returns for representative commands
- [ ] Update memory `project_exim.md`; summary report

---
## Safety rules
- **GET-only** during all automated probing. Never POST/PUT/DELETE against production.
- Never call `/account/logout/` (invalidates token), sync-triggers, or `create/update/delete/move/dispatch`.
- Secrets + raw dumps are gitignored.

---
## STATUS: COMPLETE (2026-07-18)
- Phase 0 recon ✅ · Phase 1 API crawl ✅ (64 read endpoints, real JSON) · Phase 2 browser page-walk ✅ (38 pages mapped)
- Phase 3 docs ✅ — 38 page + 95 endpoint identical-format Obsidian notes, enriched via 17-agent Workflow, + INDEX/API-INVENTORY/DOMAIN-MODEL/AUTH/ARCHITECTURE/README
- Phase 4 CLI ✅ — Printing Press generated `cli/exim-pp-cli` (Go/Cobra, 18MB), read-only, verified live
- Phase 5 verify ✅ — turnkey `./exim` wrapper auto-auths; live fetches confirmed (tank/stock/dc/rates/sap-sync)
- Note: `cli-printing-press --validate` govulncheck flagged Go **stdlib** TLS advisory GO-2026-5856 (fixed in go1.26.5) — not a code defect; binary builds & runs clean.

Linked: [[CLI/exim/INDEX|INDEX]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
