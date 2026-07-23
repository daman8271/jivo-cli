---
title: "jsap — read-only CLI for the JSAP platform"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, jsap-cli, cli]
---

# jsap — read-only CLI for the JSAP platform

A terminal client for **JSAP** (JIVO's internal ops platform, `http://103.89.45.75:5001`).
It mirrors JSAP's pages as commands so the whole platform is queryable from the shell —
and, later, so JivoGPT can read JSAP as a data source.

> ⛔ **READ-ONLY, by construction.** This CLI performs `GET` reads and a small set of
> guarded POST-to-read queries only. It has **no** create/update/delete path and never
> mutates JIVO data — see [[docs/READ_ONLY_LAW|the Read-Only Law]]. The client
> exposes exactly one data verb (`get`) plus `read_post` (which refuses any endpoint whose
> action name is not a read verb). `tests/test_readonly.py` fails the build if a write
> surface ever appears.

## Quick start

```bash
cd CLI/jsap-cli
./jsap-cli --help                 # or:  python3 -m jsap --help
./jsap-cli meta whoami            # confirm identity & company scope
./jsap-cli reports insight --month 06-2026
```

Credentials are read from the project `.env` (`JSAP_USERNAME`, `JSAP_PASSWORD`,
`JSAP_URL`). No install step — pure Python 3 standard library, no dependencies. The
session cookie is bootstrapped once (login → websession) and cached in `~/.jsap/`.

## Global flags (work before **or** after the subcommand)

| Flag | Meaning |
|---|---|
| `-c, --company {1,2}` | Company scope — `1`=JIVO OIL (default), `2`=JIVO BEVERAGE |
| `--json` | Emit JSON instead of a table |
| `--raw` | Show the full `{success, message, data}` envelope |
| `--select F1,F2` | Keep only these fields (lists of objects) |
| `--limit N` | Cap rows shown |
| `--timeout N` | HTTP timeout (seconds) |

## Command groups (13 modules · 146 commands)

Each group mirrors a JSAP module; each command is one read endpoint. Full per-page
detail lives in `docs/jsap/` (indexed by `JSAP_MAP.md`).

| Group | Commands | Covers |
|---|---|---|
| `dashboards` | 18 | IT / Task / Client / MoM / Budget dashboards |
| `inventory` | 12 | Inventory-audit sessions, units, locations, item groups |
| `documents` | 11 | Dispatch/receive/rejected queues + SAP source docs (PO/GRPO/GR/AP) |
| `users` | 12 | Users, roles, states, branches, budgets, permissions |
| `reports` | 7 | Approval Status / Budget Approval report + drill-downs |
| `bpmaster` | 14 | Business-Partner master + lookups (groups, GST, PAN, banks…) |
| `qc` | 2 | Parameter quality-check reads |
| `tasks` | 7 | Task list & dashboard (POST-reads), team, tree, details, progress |
| `tickets` | 11 | Helpdesk tickets (POST-to-read), projects, timeline, comments |
| `hierarchy` | 24 | Employee / HO / Sales hierarchy, salary sessions, custom fields |
| `bills` | 14 | Bill verification: maker / checker / payment / admin reads |
| `dochub` | 10 | Document Hub folders, versions, backups, activity |
| `meta` | 4 | whoami, companies, departments, effective permissions |

Run `./jsap-cli <group> --help` to list a group's commands, and
`./jsap-cli <group> <command> --help` for its flags.

## Examples

```bash
# Budget approval counts per user for a month, top 10 by pending
jsap reports insight --month 06-2026 --select userID,userName,totalPending --limit 10

# Every open ticket (admin view), just the essentials
jsap tickets all --select ticketId,title,status,priority --json

# Business partners for JIVO BEVERAGE
jsap -c 2 bpmaster cards --limit 20

# Full employee hierarchy tree
jsap hierarchy tree --json

# Open purchase orders from SAP (both companies)
jsap documents po --limit 5
```

## How it works

1. **Auth** — `POST /api/auth/Login` → `POST /websession/set` →
   `POST /websession/updateSelectedCompany`; the `.AspNetCore.Session` cookie is cached
   in `~/.jsap/session.json` (hourly TTL, `0600`). These three POSTs authenticate a
   session and mutate no JIVO data — the only non-read traffic the client allows.
2. **Reads** — every command issues one `GET` (or a guarded POST-to-read for JSAP's
   `Get*`-with-body endpoints) and unwraps the standard `{success, data}` envelope.
3. **Read-only guarantee** — enforced in code (`jsap/client.py`) and tested
   (`tests/test_readonly.py`, 6 checks).

## Layout

```
jsap/
  config.py     # reads .env, company map
  client.py     # session bootstrap + cookie cache + READ-ONLY guard (get / read_post)
  _reg.py       # declarative group()/endpoint() helpers
  output.py     # table / --json / --select / --limit / --raw
  cli.py        # argparse root + global flags
  modules/      # one file per JSAP module (auto-discovered)
tests/
  test_readonly.py   # 6 read-only enforcement checks
```

## Run the read-only checks

```bash
python3 tests/test_readonly.py     # 6/6 must pass
```

Linked: [[docs/jsap/JSAP_MAP|JSAP_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
