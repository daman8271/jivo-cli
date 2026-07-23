---
title: "JIVO EXIM — Knowledge Base"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, exim, knowledge-base]
---

# JIVO EXIM — Knowledge Base

> ## ⛔ HARD RULE — READ-ONLY
> **JIVO EXIM is READ-ONLY. Only ever READ / FETCH. NEVER write, create, update, delete, PATCH/POST/PUT/DELETE, or trigger a sync against exim.jivo.in / eximbe.jivo.in.** This is live JIVO + SAP production data. No writes, ever, without explicit per-request approval from Daman. See [[HARD-RULE]].


Reverse-engineered documentation of the **JIVO EXIM** platform (edible-oil import/export, stock, tanks, domestic contracts, licenses, rates, and accounts for JIVO Wellness), plus a **read-only CLI** for its API.

- Web SPA: `https://exim.jivo.in`
- REST API: `https://eximbe.jivo.in` (JWT bearer auth, trailing-slash routes)
- Upstream system of record: SAP B1, pulled in via `sap-sync` / `sap_sync` endpoints

Scale: 38 pages, 65 unique safe GET routes as CLI commands, and 34 write/sync catalogue entries excluded from the CLI. Start at [[INDEX]].

## Folder layout

| Path | What |
|---|---|
| `INDEX.md` | Map of content: every page and section, linked |
| `ARCHITECTURE.md` | How the app is built (SPA + REST + SAP sync + data flow) |
| `AUTH.md` | Login / JWT / refresh flow |
| `DOMAIN-MODEL.md` | Entities + the permission-resource table from the token |
| `API-INVENTORY.md` | One table of all endpoints |
| `pages/` | One note per SPA page (route, what it shows, endpoints it calls) |
| `endpoints/` | One note per API endpoint (desc, query params, response sample) |
| `cli/` | `exim-pp-cli` — generated read-only Go CLI + its OpenAPI spec |
| `scripts/` | Helpers: `eximapi.py` (auth client), `login.sh`, `get.sh`, doc generators |
| `_raw/` | Raw captures the docs were derived from |
| `endpoints.json`, `pages.json` | Machine-readable source data behind the notes |
| `.secrets/` | `token.json` token cache (gitignored, never commit); `EXIM_*` creds live in the jivogpt root `.env` |

## Open as an Obsidian vault

Open the `~/jivogpt/CLI/exim` folder in Obsidian ("Open folder as vault"). All cross-references are `[[wikilinks]]`, so the graph view and backlinks work out of the box. `INDEX.md` is the intended home note.

## Auth

The API uses JWT access + refresh tokens: `POST /account/login/` with `{email, password}`, then `Authorization: Bearer <access>` on every call, refresh via `POST /account/login/refresh/`. Full flow and the do-not-call-logout warning: [[AUTH]]. Credentials (`EXIM_*`) live in the jivogpt root `.env` (consolidated 2026-07-19); `scripts/eximapi.py` handles login and auto-refresh for scripting.

## Using the exim CLI

`cli/exim-pp-cli/` is a read-only fetch CLI generated with **Printing Press** from `cli/exim-openapi.json`. It wraps every GET endpoint; it never writes to EXIM.

### Native login (config-based)

```bash
exim-pp-cli auth login          # reads ~/jivogpt/.env; stores JWT in CLI config
exim-pp-cli tank get-summary    # works with no EXIM_TOKEN env after login
```

### Turnkey wrapper (recommended)

`./exim` (EXIM workspace root) auto-mints/refreshes the JWT from the jivogpt root `.env` and runs the binary — no manual token handling:

```bash
./exim tank get-summary                          # tank totals + utilisation
./exim stock-status get-stock-insights           # ₹ value / qty / avg-price KPIs
./exim stock-status get --status MUNDRA_PORT      # stock lots at a status
./exim dc get --year 2026                        # domestic contracts for FY
./exim tank get-item-wise-average --item-code RM00CN
./exim sap-sync get-open-pos                      # open purchase orders (SAP)
./exim daily-price get-range --from-date 2026-06-01 --to-date 2026-07-18
./exim director-inventorty get                    # director inventory rollup
```

Add `--json` for machine output, `--select <fields>` to narrow, `--csv` for spreadsheets.

### Manual (binary directly)

```bash
export EXIM_TOKEN="$(python3 scripts/eximapi.py --token)"   # fresh access token
cli/exim-pp-cli/exim-pp-cli doctor
cli/exim-pp-cli/exim-pp-cli tank get-summary --json
```

Discover commands: `cli/exim-pp-cli/exim-pp-cli --help`, then `<resource> --help`. Each command maps 1:1 to an endpoint note in `endpoints/`; the full catalogue is in [[API-INVENTORY]].

> Note: `cli/exim-openapi.json` intentionally contains only the **read** surface, so the CLI cannot mutate EXIM. The write/sync endpoints are documented (see [[API-INVENTORY]]) but not wired.

_Part of [[INDEX]]_

Linked: [[CLI/exim/CLAUDE|EXIM read-only instructions]] · [[CLI/exim/OPERATOR-GUIDE|Operator guide]] · [[CLI/exim/PLAN|Plan]] · [[CLI/exim/PORT-PLAN|Port plan]] · [[CLI/exim/cli/exim-pp-cli/README|EXIM CLI]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[CLI/exim/INDEX|INDEX]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
