---
title: JIVO EXIM — Read-Only Vow
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: instructions
tags: [jivogpt, exim, read-only, instructions]
---

# JIVO EXIM — READ-ONLY VOW (read this first)

This folder is a **read-only knowledge vault + CLI** over JIVO EXIM (web https://exim.jivo.in, API https://eximbe.jivo.in). It holds **production JIVO + SAP data**. You are here to READ, never to change.

## CARDINAL RULE
**READ-ONLY. Only GET requests to eximbe.jivo.in.**
The ONLY permitted non-GET is the auth exchange — `POST /account/login/`, token refresh, and logout — which mints/clears JWTs and creates **zero business data**. Everything else is a GET or it does not happen.

No writes, ever, without explicit per-request approval from Daman.

## Never call write/sync endpoints
Do not POST/PUT/PATCH/DELETE, and do not fire any create/dispatch/move/register/sync/fetch endpoint. Non-exhaustive blocklist:
- `/account/register/`
- `/dc/contract/create/`
- `/stock-status/dispatch/`, `/stock-status/move/`, `/stock-status/arrive-batch/`, `/stock-status/opening-stock/`
- `/tank/` (POST)
- `/license/*/create/`
- `/sap_sync/*/items/`
- `/daily-price/fetch/`
- `/jivo-rate/fetch/`

## "GET is NOT safe here"
Method alone does not tell you a call is safe. Several EXIM GETs **mutate** — the app fires them on page load to refresh SAP data. Treat as a WRITE (exclude) if ANY hold:
1. Path is in the underscore `/sap_sync/` namespace (the hyphen `/sap-sync/` family are reads of already-synced data).
2. Its token permission is only `fetch` or `sync` (no `view`) — rm, fg, po, inventory, open_grpos, balance_sheet, daily_price, jivo_rate.
3. Response is an import-result shape: `{status, count, preview_data}` or `{success, Items_processed}`.
4. Path ends in `/fetch/` with a fetch permission, or contains create/dispatch/move/register/update/delete.

See **[[HARD-RULE]]** for the full test.

## Enforced three ways (defense in depth)
1. **OpenAPI spec** — `cli/exim-openapi.json` contains **zero write operations**; the generated CLI physically cannot emit one.
2. **HTTP client** — the CLI's client refuses any non-GET at `internal/client/client.go` `doInternal`.
3. **`./exim raw`** — blocklists the GET-that-writes paths, backed by **[[HARD-RULE]]** and fleet memory.

## Credentials
JWT only. `EXIM_*` credentials live in the **jivogpt root `.env`** (`../../.env`, gitignored, consolidated 2026-07-19) plus CLI config; the token cache stays in `.secrets/token.json`. The password is **never committed**. Auth is the login/refresh/logout exchange and nothing more.

## What this repo is
- `vault/` and the top-level `.md` docs — Obsidian knowledge (`DOMAIN-MODEL.md`, `API-INVENTORY.md`, `HARD-RULE.md`, `endpoints.json`).
- `cli/exim-openapi.json` — the read-only spec (no writes by construction).
- `cli/exim-pp-cli/` — the generated, read-only Printing Press CLI.
- `./exim` — auto-authenticated wrapper (guards `raw`, blocks GET-that-writes).

Ground every claim in real data: read `endpoints.json` (each endpoint has desc, query_params, response_sample), `DOMAIN-MODEL.md`, and `HARD-RULE.md` before answering.

Linked: [[CLI/exim/INDEX|INDEX]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
