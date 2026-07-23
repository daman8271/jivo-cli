---
title: "JIVO EXIM — Operator Guide (read-only CLI)"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: guide
tags: [jivogpt, exim, operations]
---

# JIVO EXIM — Operator Guide (read-only CLI)

Agent-facing runbook for the `exim` CLI: a read-only lens over the JIVO EXIM
edible-oil import/export platform (web `https://exim.jivo.in`, API
`https://eximbe.jivo.in`, JWT bearer). This is live JIVO + SAP B1 production
data. You FETCH. You never write.

See also: [[CLI/exim/README|README]], [[CLI/exim/INDEX|INDEX]], [[CLI/exim/DOMAIN-MODEL|DOMAIN-MODEL]], [[CLI/exim/API-INVENTORY|API-INVENTORY]], [[CLI/exim/HARD-RULE|HARD-RULE]].

## Read-only, enforced

The read-only vow is not a convention. It is enforced in three independent
layers, so a write cannot slip through by accident. See [[HARD-RULE]] for the
full write-vs-read decision rules.

1. **The spec has zero writes.** `cli/exim-openapi.json` is generated from
   `endpoints.json` keeping only `kind` in `{read, detail}`. The 34 write/sync
   endpoints (all POST/PUT/PATCH/DELETE, the `/sap_sync/` mutating GETs, and
   the `/fetch/`-with-fetch-permission GETs) never become commands. There is
   nothing to call.
2. **The HTTP client hard-blocks non-GET.** In
   `cli/exim-pp-cli/internal/client/client.go`, `doInternal` refuses any method
   other than GET before it reaches the wire (the sole exception is
   `auth login`, which calls `/account/login/` for a token, not a data write).
   Even if a mutating path were somehow requested, the transport drops it.
3. **`./exim raw` blocklists GET-that-writes.** The wrapper's `guard()` refuses
   the entire underscore `/sap_sync/` namespace plus `/daily-price/fetch/`,
   `/jivo-rate/fetch/`, `/account/logout/`, `/stock-status/opening-stock/` —
   with `REFUSED: ... mutates data (read-only rule)`.

Remember: **GET is not a safety guarantee here.** The app fires several GETs
on page load to refresh SAP data. The three layers above encode exactly which
GETs are safe. Do not route around them.

## Quick start

```bash
# 1. Authenticate once (reads ~/jivogpt/.env; also honors EXIM_EMAIL/EXIM_PASSWORD)
exim auth login

# 2. Fetch data — <group> then a get-* verb
./exim tank get                       # storage tanks: code, item, capacity, fill
./exim stock-status get-stock-insights
./exim license get-advance-headers

# 3. Guarded raw reader (safe paths only)
./exim raw /stock-status/ status=in   # arbitrary k=v query params
```

- Add `--agent` to any command for JSON + non-interactive output.
- `./exim doctor` verifies auth and connectivity.
- `auth login` is the only command that sends a non-GET; it hits
  `/account/login/` and stores the JWT. Everything else is GET.

## The command groups

Each group is a resource family; run `./exim <group> --help` for its `get-*`
verbs. Groups (from the OpenAPI tags in `cli/exim-openapi.json`):

| Group | What it reads |
|---|---|
| `tank` | Storage tanks — code, item, capacity, current fill, per-item summaries, weighted-average rates, capacity insights. |
| `stock-status` | Import stock-status rows, contractual history, shortage/debit entries, stock dashboard, aggregate stock KPIs. |
| `sap-sync` | Reads of already-synced SAP data — balance sheets, customer ledgers/aging/balances, finished + raw inventory. (Hyphen family = reads; the underscore `/sap_sync/` mutating GETs are excluded.) |
| `license` | Advance Authorisation + DFIA licenses — headers with nested import/export lines, shipping-bill / BOE lines, dropdowns. |
| `items` | Item masters — finished goods (`get-fg`), raw material (`get-rm`), RM summary + varieties. |
| `dc` | Domestic contracts by FY, plus the open-PO dropdown. |
| `rates` | Basic/market/commodity/packing rate rows and latest-rate tables. |
| `parties` | Business-partner master (vendors + customers) from SAP. |
| `party` | Single business-partner detail. |
| `daily-price` | Daily price data (read side only; the `/fetch/` refresh is blocked). |
| `jivo-rate` | JIVO pack rates over a date range (read side; `/fetch/` blocked). |
| `director-inventorty` | Director rollup — finished + at-factory + in-transit inventory by litre/MT. (Spelling matches the upstream API.) |
| `exim-rates` | Custom EXIM exchange rates (`/exim-rates/fetch/` is permission=view, plain data — kept as a read). |

Also top-level: `sync-logs` (SAP sync job history), `search`, `analytics`,
`workflow`, `api` (browse endpoints), `which`, `agent-context`.

## Params to remember

Passed as `--flag value` on group commands, or as `k=v` on `./exim raw`.
The API is inconsistent about casing — match the endpoint's note in
`endpoints/`.

| Param | Notes |
|---|---|
| `from_date` / `to_date` | Snake-case date range (some rate/report endpoints). |
| `start_date` / `end_date` | Snake-case range variant. |
| `startDate` / `endDate` | camelCase range variant (rates, jivo-rate, etc.). |
| `cardCode` | SAP business-partner code (party/ledger/balance lookups). |
| `monthId` | Period selector; CLI flag is `--month-id`. |
| `status` | Stock-status filter (e.g. `in`). |
| `year` | Financial year (domestic contracts, license lists). |
| `item_code` | Item master / tank item filter. |
| `license_no` | License header/line lookups. |
| `file_no` | DFIA file selector. |

When unsure which casing an endpoint wants, check its
`endpoints/<name>.md` note (`query_params` block) or `endpoints.json`.

## Rebuild / regenerate

If `endpoints.json` changes, or the CLI must be re-minted:

```bash
# 1. Regenerate the read-only OpenAPI surface from endpoints.json
python3 scripts/gen_openapi.py            # -> cli/exim-openapi.json

# 2. Re-generate the CLI from the spec
cli-printing-press generate               # (printing-press skill)

# 3. Re-apply the local patches — regeneration overwrites them
#    cli/exim-pp-cli/.printing-press-patches/
#      - auth-login.md            (root .env / EXIM_EMAIL flow)
#      - client-readonly-guard.md (doInternal non-GET hard-block)
#      - generic-import-disabled.md (generated POST import stays unreachable)

# 4. Rebuild the binary
cd cli/exim-pp-cli && go build ./...
```

All three patches are load-bearing: `auth-login` wires credential sources,
`client-readonly-guard` is enforcement layer 2 above, and
`generic-import-disabled` keeps the generator's POST import unreachable. Never
ship a rebuild without re-applying all three.

## Knowledge vault

The docs are the same data as the CLI, in prose. Start at [[INDEX]].

- `pages/` — one note per SPA page (route, what it shows, endpoints it calls) — 38 pages.
- `endpoints/` — one note per API endpoint (desc, query params, response sample) — 100 notes.
- `endpoints.json` / `pages.json` — machine-readable source behind the notes.
- `API-INVENTORY.md` — every endpoint in one table.
- `_raw/` — raw captures the docs were derived from.

95+ endpoint/page notes total; when an agent needs the shape of a response or
which params an endpoint accepts, read the note before calling.

Linked: [[CLI/exim/INDEX|INDEX]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
