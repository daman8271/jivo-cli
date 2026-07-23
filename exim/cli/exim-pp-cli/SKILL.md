---
name: pp-exim
title: EXIM — Printing Press CLI Skill
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: skill
tags: [jivogpt, exim, cli, skill]
description: "Printing Press CLI for Exim. JIVO EXIM read-only surface; write and sync-import endpoints are excluded."
author: "daman8271"
license: "Apache-2.0"
argument-hint: "<command> [args] | install cli|mcp"
allowed-tools: "Read Bash"
metadata:
  openclaw:
    requires:
      bins:
        - exim-pp-cli
---

# Exim — Printing Press CLI

## Prerequisites: Install the CLI

This skill drives the `exim-pp-cli` binary. **You must verify the CLI is installed before invoking any command from this skill.** If it is missing, install it first:

1. Install via the Printing Press installer. It defaults binaries to `$HOME/.local/bin` on macOS/Linux and `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows:
   ```bash
   npx -y @mvanhorn/printing-press-library install exim --cli-only
   ```
2. Verify: `exim-pp-cli --version`
3. Ensure the reported install directory is on `$PATH` for the agent/runtime that will invoke this skill.

If the `npx` install fails before this CLI has a public-library category, install Node or use the category-specific Go fallback after publish.

If `--version` reports "command not found" after install, the runtime cannot see the binary directory on `$PATH`. Do not proceed with skill commands until verification succeeds.

JIVO EXIM read-only surface. Write and sync-import endpoints are excluded.

## When Not to Use This CLI

Do not activate this CLI for requests that require creating, updating, deleting, publishing, commenting, upvoting, inviting, ordering, sending messages, booking, purchasing, or changing remote state. This printed CLI exposes read-only commands for inspection, export, sync, and analysis.

## Command Reference

**account** — Manage account

- `exim-pp-cli account get-user-id` — Single user detail.
- `exim-pp-cli account get-users` — List of application user accounts (id, name, email).

**daily-price** — Manage daily price

- `exim-pp-cli daily-price get-db-list` — Historical daily commodity factory-price records (optionally for a date).
- `exim-pp-cli daily-price get-highest-lowest` — Highest & lowest commodity prices over a date range.
- `exim-pp-cli daily-price get-range` — Daily prices over a from/to range.
- `exim-pp-cli daily-price get-trends` — Daily-price trend series (labels + datasets) for charting over a range.

**dc** — Manage dc

- `exim-pp-cli dc get` — Domestic contracts by FY (re-listed).
- `exim-pp-cli dc get-dropdown` — Open-PO dropdown for domestic-contract creation.

**director-inventorty** — Manage director inventorty

- `exim-pp-cli director-inventorty` — Director rollup: finished + at-factory + in-transit inventory by litre/MT.

**exim-rates** — Manage exim rates

- `exim-pp-cli exim-rates` — Fetch/refresh custom exchange (EXIM) rates.

**item** — Manage item

- `exim-pp-cli item get-fg-code` — Single finished-good item detail.
- `exim-pp-cli item get-rm-code` — Single raw-material item detail incl movement totals.

**items** — Manage items

- `exim-pp-cli items get-fg` — Finished-goods item master (SAP-synced).
- `exim-pp-cli items get-rm` — Raw-material item master (SAP-synced).
- `exim-pp-cli items get-rm-summary` — Aggregate summary of raw-material items (counts, qty, value).
- `exim-pp-cli items get-rm-varieties` — Distinct raw-material varieties.

**jivo-rate** — Manage jivo rate

- `exim-pp-cli jivo-rate` — JIVO pack rates over a range.

**license** — Manage license

- `exim-pp-cli license get-advance-export-lines` — Advance-license export (shipping bill) lines.
- `exim-pp-cli license get-advance-headers` — Advance Authorisation licenses with nested import/export lines.
- `exim-pp-cli license get-advance-import-lines` — Advance-license import (BOE) lines.
- `exim-pp-cli license get-advance-import-lines-dropdown` — Import-line dropdown for a license.
- `exim-pp-cli license get-dfia-export-lines-dropdown` — DFIA export-line dropdown for a license file.
- `exim-pp-cli license get-dfia-header-list` — DFIA license headers list.

**parties** — Manage parties

- `exim-pp-cli parties` — Business partners (vendors + customers) master from SAP.

**party** — Manage party

- `exim-pp-cli party <card_code>` — Single business-partner detail.

**rates** — Manage rates

- `exim-pp-cli rates get-basic` — Basic (our) rate rows over a date range.
- `exim-pp-cli rates get-commodity` — Commodity master with margin rates.
- `exim-pp-cli rates get-market-get` — Market rate rows over a date range.
- `exim-pp-cli rates get-market-latest` — Latest market rate per commodity.
- `exim-pp-cli rates get-packing` — Packing types with packing margins.
- `exim-pp-cli rates get-table-latest` — Composite latest rate table (commodities + rows).

**sap-sync** — Manage sap sync

- `exim-pp-cli sap-sync get-balance-sheet` — Oil Dr/Cr outstanding balance sheet (SAP).
- `exim-pp-cli sap-sync get-custa-balance-sheet` — Customer (custa) outstanding balance sheet (SAP).
- `exim-pp-cli sap-sync get-customer-aging-balance` — Customer aging balances (SAP).
- `exim-pp-cli sap-sync get-customer-balance` — Customer outstanding balance over a date range (SAP).
- `exim-pp-cli sap-sync get-customer-ledger` — Customer ledger entries for one party (SAP).
- `exim-pp-cli sap-sync get-finished-inventory` — Finished-goods inventory (SAP).
- `exim-pp-cli sap-sync get-inventory` — Raw/factory inventory (SAP).
- `exim-pp-cli sap-sync get-monthly-planning` — Monthly SAP planning rows for a given month id.
- `exim-pp-cli sap-sync get-open-ap` — Open accounts-payable documents (SAP).
- `exim-pp-cli sap-sync get-open-ar` — Open accounts-receivable documents (SAP).
- `exim-pp-cli sap-sync get-open-pos` — Open purchase orders (SAP).
- `exim-pp-cli sap-sync get-planned-months` — Available planning months (SAP).
- `exim-pp-cli sap-sync get-vendor-balance-sheet` — Vendor outstanding balance sheet (SAP).
- `exim-pp-cli sap-sync get-vendor-ledger` — Vendor ledger entries for one party (SAP).

**stock-status** — Manage stock status

- `exim-pp-cli stock-status get` — Core import stock-status rows (optionally filtered by status).
- `exim-pp-cli stock-status get-contractual-history` — Contractual history of stock items (rates, contract dates).
- `exim-pp-cli stock-status get-debit-entries` — Shortage/debit deduction entries per vehicle/item.
- `exim-pp-cli stock-status get-debit-insights` — Aggregate shortage/debit totals.
- `exim-pp-cli stock-status get-id` — Single stock-status record detail.
- `exim-pp-cli stock-status get-stock-dashboard` — Multi-dimensional stock dashboard (in/outside factory, by status/vendor).
- `exim-pp-cli stock-status get-stock-insights` — Aggregate stock KPIs (value, qty, avg price).
- `exim-pp-cli stock-status get-stock-logs` — Field-level audit log of stock-status changes.
- `exim-pp-cli stock-status get-stock-summary` — Aggregate stock summary KPIs (value, qty, avg price).
- `exim-pp-cli stock-status get-vehicle-report` — Vehicle-wise stock grouped by a status.

**sync-logs** — Manage sync logs

- `exim-pp-cli sync-logs` — History of SAP sync jobs (type, status, counts).

**tank** — Manage tank

- `exim-pp-cli tank get` — Storage tanks (code, item, capacity, current fill).
- `exim-pp-cli tank get-capacity-insights` — Overall tank capacity fill/empty percentages.
- `exim-pp-cli tank get-code` — Single tank detail.
- `exim-pp-cli tank get-in-items` — Distinct item codes currently in tanks.
- `exim-pp-cli tank get-item-wise-average` — Weighted average rate + matched qty for one tank item.
- `exim-pp-cli tank get-item-wise-summary` — Per-item tank summary (qty, capacity, tank list).
- `exim-pp-cli tank get-items` — Tank item master (code, name, category, colour).
- `exim-pp-cli tank get-log` — Tank inflow/outflow log entries.
- `exim-pp-cli tank get-summary` — Tank totals (capacity, current stock, utilisation).


### Finding the right command

When you know what you want to do but not which command does it, ask the CLI directly:

```bash
exim-pp-cli which "<capability in your own words>"
```

`which` resolves a natural-language capability query to the best matching command from this CLI's curated feature index. Exit code `0` means at least one match; exit code `2` means no confident match — fall back to `--help` or use a narrower query.

## Auth Setup

Run `exim-pp-cli auth setup` for the URL and steps to obtain a token (add `--launch` to open the URL). Then store it:

```bash
exim-pp-cli auth set-token YOUR_TOKEN_HERE
```

Or set `EXIM_TOKEN` as an environment variable.

Run `exim-pp-cli doctor` to verify setup.

## Agent Mode

Add `--agent` to any command. Expands to: `--json --compact --no-input --no-color --yes`.

- **Pipeable** — JSON on stdout, errors on stderr
- **Filterable** — `--select` keeps a subset of fields. Dotted paths descend into nested structures; arrays traverse element-wise. Critical for keeping context small on verbose APIs:

  ```bash
  exim-pp-cli dc get --year example-value --agent --select id,name,status
  ```
- **Previewable** — `--dry-run` shows the request without sending
- **Offline-friendly** — sync/search commands can use the local SQLite store when available
- **Non-interactive** — never prompts, every input is a flag
- **Read-only** — do not use this CLI for create, update, delete, publish, comment, upvote, invite, order, send, or other mutating requests

### Response envelope

Commands that read from the local store or the API wrap output in a provenance envelope:

```json
{
  "meta": {"source": "live" | "local", "synced_at": "...", "reason": "..."},
  "results": <data>
}
```

Parse `.results` for data and `.meta.source` to know whether it's live or local. A human-readable `N results (live)` summary is printed to stderr only when stdout is a terminal AND no machine-format flag (`--json`, `--csv`, `--compact`, `--quiet`, `--plain`, `--select`) is set — piped/agent consumers and explicit-format runs get pure JSON on stdout.

## Agent Feedback

When you (or the agent) notice something off about this CLI, record it:

```
exim-pp-cli feedback "the --since flag is inclusive but docs say exclusive"
exim-pp-cli feedback --stdin < notes.txt
exim-pp-cli feedback list --json --limit 10
```

Entries are stored locally at `~/.local/share/exim-pp-cli/feedback.jsonl`. They are never POSTed unless `EXIM_FEEDBACK_ENDPOINT` is set AND either `--send` is passed or `EXIM_FEEDBACK_AUTO_SEND=true`. Default behavior is local-only.

Write what *surprised* you, not a bug report. Short, specific, one line: that is the part that compounds.

## Output Delivery

Every command accepts `--deliver <sink>`. The output goes to the named sink in addition to (or instead of) stdout, so agents can route command results without hand-piping. Three sinks are supported:

| Sink | Effect |
|------|--------|
| `stdout` | Default; write to stdout only |
| `file:<path>` | Atomically write output to `<path>` (tmp + rename) |
| `webhook:<url>` | POST the output body to the URL (`application/json` or `application/x-ndjson` when `--compact`) |

Unknown schemes are refused with a structured error naming the supported set. Webhook failures return non-zero and log the URL + HTTP status on stderr.

## Named Profiles

A profile is a saved set of flag values, reused across invocations. Use it when a scheduled agent calls the same command every run with the same configuration - HeyGen's "Beacon" pattern.

```
exim-pp-cli profile save briefing --json
exim-pp-cli --profile briefing dc get --year example-value
exim-pp-cli profile list --json
exim-pp-cli profile show briefing
exim-pp-cli profile delete briefing --yes
```

Explicit flags always win over profile values; profile values win over defaults. `agent-context` lists all available profiles under `available_profiles` so introspecting agents discover them at runtime.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Usage error (wrong arguments) |
| 3 | Resource not found |
| 4 | Authentication required |
| 5 | API error (upstream issue) |
| 7 | Rate limited (wait and retry) |
| 10 | Config error |

## Argument Parsing

Parse `$ARGUMENTS`:

1. **Empty, `help`, or `--help`** → show `exim-pp-cli --help` output
2. **Starts with `install`** → ends with `mcp` → MCP installation; otherwise → see Prerequisites above
3. **Anything else** → Direct Use (execute as CLI command with `--agent`)

## MCP Server Installation

Install the MCP binary from this CLI's published public-library entry or pre-built release, then register it:

```bash
claude mcp add exim-pp-mcp -- exim-pp-mcp
```

Verify: `claude mcp list`

## Direct Use

1. Check if installed: `which exim-pp-cli`
   If not found, offer to install (see Prerequisites at the top of this skill).
2. Match the user query to the best command from the Unique Capabilities and Command Reference above.
3. Execute with the `--agent` flag:
   ```bash
   exim-pp-cli <command> [subcommand] [args] --agent
   ```
4. If ambiguous, drill into subcommand help: `exim-pp-cli <command> --help`.

Linked: [[docs/EXIM_MAP|EXIM_MAP]] · [[CLI/exim/HARD-RULE|HARD-RULE]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
