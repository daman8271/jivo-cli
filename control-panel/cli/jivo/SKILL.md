---
name: pp-jivo
description: "Printing Press CLI for Jivo. Jivo Group — Control Panel"
author: "daman8271"
license: "Apache-2.0"
argument-hint: "<command> [args] | install cli|mcp"
allowed-tools: "Read Bash"
metadata:
  openclaw:
    requires:
      bins:
        - jivo-pp-cli
    install:
      - kind: go
        bins: [jivo-pp-cli]
        module: github.com/mvanhorn/printing-press-library/library/sales-and-crm/jivo/cmd/jivo-pp-cli
---

# Jivo — Printing Press CLI

## Prerequisites: Install the CLI

This skill drives the `jivo-pp-cli` binary. **You must verify the CLI is installed before invoking any command from this skill.** If it is missing, install it first:

1. Install via the Printing Press installer. It defaults binaries to `$HOME/.local/bin` on macOS/Linux and `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows:
   ```bash
   npx -y @mvanhorn/printing-press-library install jivo --cli-only
   ```
2. Verify: `jivo-pp-cli --version`
3. Ensure the reported install directory is on `$PATH` for the agent/runtime that will invoke this skill.

If the `npx` install fails (no Node, offline, etc.), fall back to a direct Go install (requires Go 1.26.4 or newer). This installs into `$GOPATH/bin` (default `$HOME/go/bin`), so add that directory to `$PATH` instead:

```bash
go install github.com/mvanhorn/printing-press-library/library/sales-and-crm/jivo/cmd/jivo-pp-cli@latest
```

If `--version` reports "command not found" after install, the runtime cannot see the binary directory on `$PATH`. Do not proceed with skill commands until verification succeeds.

Jivo Group — Control Panel: strictly READ-ONLY CLI over the internal Django ERP/analytics dashboard for JIVO Wellness (sales realise, targets, order-in-hand, receivables aging, master data, inventory & production). Live production system — read/pull endpoints only.

## When Not to Use This CLI

Do not activate this CLI for requests that require creating, updating, deleting, publishing, commenting, upvoting, inviting, ordering, sending messages, booking, purchasing, or changing remote state. This printed CLI exposes read-only commands for inspection, export, sync, and analysis.

## Command Reference

**accounts** — Accounts receivable — customer aging (oil AR flat, mart & beverages pre-bucketed), on-account payments, and the claim register.

- `jivo-pp-cli accounts aging-beverages` — Beverages A/R aging as a pre-bucketed pivot (grouped by salesperson) with KPIs and totals.
- `jivo-pp-cli accounts aging-mart` — Mart A/R aging as a pre-bucketed pivot by Format with book KPIs and totals.
- `jivo-pp-cli accounts aging-oil` — Oil company open A/R ledger as a flat per-open-invoice list (aged to as_of).
- `jivo-pp-cli accounts claims` — Full claim register (hand-maintained customer claims) plus the customer master picklist.
- `jivo-pp-cli accounts open-payments` — Customer payments on account (receipts not yet applied to invoices) for a date range.

**credit** — Required Credit Limit page — no JSON API; data is embedded in the page HTML. Read-only GET of the page, parsing the embedded JSON.

- `jivo-pp-cli credit` — Required credit limits per ASM (Total Outstanding + 2%), lock state, as-of date — read from the page's embedded JSON.

**inventory** — Inventory & production — live on-hand stock, non-moving/ageing stock, production feasibility & catalogues, daily work orders, and Wellness-Mart reconciliation.

- `jivo-pp-cli inventory daily-production` — Standard work-order (OWOR) production transactions for a date range — planned vs completed, warehouse, status, user.
- `jivo-pp-cli inventory non-moving` — Every in-stock finished good with ageing / movement signals (DaysInStock, DaysSinceMoved, last customer
- `jivo-pp-cli inventory non-moving-drill` — Per-warehouse breakdown of a single finished good (code, name, qty, lot production date).
- `jivo-pp-cli inventory production-feasibility` — Read-only feasibility check for one FG at a requested qty
- `jivo-pp-cli inventory production-fg-list` — Catalogue of manufacturable finished goods (those with a BOM) for the production-plan picker.
- `jivo-pp-cli inventory production-warehouses` — Full warehouse master (code + name) for the 'Stock from' selector.
- `jivo-pp-cli inventory reconciliation` — Wellness-Mart inter-company billing chains (PO -> SO -> GRPO -> A/P -> A/R) classified MATCHED/MISMATCH/INCOMPLETE.
- `jivo-pp-cli inventory reconciliation-ledgers` — BP ledgers behind the Wellness-Mart reconciliation, pivoted by document-type origin for each side (Mart vs Wellness).
- `jivo-pp-cli inventory stock` — Live finished-goods on-hand stock for one company: type summaries + per-SKU x per-warehouse rows.

**masterdata** — Reference master data — customer master, saved realise-calculator rate lists, and the FG item master.

- `jivo-pp-cli masterdata calculator-items` — SAP finished-goods item master for the realise-calculator picker (code, name, variety, sku, pcs/box, box litres).
- `jivo-pp-cli masterdata customer-master` — Entire customer master (contact, tax, address, terms, credit limit, balance, status) in one payload.
- `jivo-pp-cli masterdata rate-list` — Saved realise-calculator results (rate lists). Pass --id to fetch a single saved result.

**oih** — Order In Hand (open, uninvoiced sales orders) — line breakdown, per-person totals, and open-quantity rows.

- `jivo-pp-cli oih breakdown` — Line-level OIH breakdown, one row per open SO line, split premium vs commodity value and pieces.
- `jivo-pp-cli oih commodity-rows` — OIH open-order rows filtered to commodity oils (u_type=COMMODITY).
- `jivo-pp-cli oih rows` — OIH as individual open-order rows (open litres per item/customer).
- `jivo-pp-cli oih summary` — Total OIH value summarised per salesperson.

**sales** — Sales realise dashboard feeds — per-product realise, credit notes, hidden sales, document flow, dispatch, drill-downs and beverages (all read-only; POST reads sample the smallest date range).

- `jivo-pp-cli sales beverages` — BEVERAGES dataset feed: beverage sales lines, day-over-day box comparison, customer grading
- `jivo-pp-cli sales beverages-docs` — Documents (invoices / SOs) behind a beverages node — lazily fetched per drilled node.
- `jivo-pp-cli sales channel-docs` — Documents behind a Slide-2 channel card cell — invoices (done) or open SOs (oih)
- `jivo-pp-cli sales cn` — Line-level gross sales vs credit-note rows for one company (oil|beverages) over a date range.
- `jivo-pp-cli sales compare-docs` — Invoice-level drill-down behind a Compare-Sales pivot cell (one month range plus optional dimension filters).
- `jivo-pp-cli sales data` — Core OILS realise feed
- `jivo-pp-cli sales dispatch` — Per-invoice physical dispatch / freight metadata (bilty, transporter, vehicle, driver) for a date range.
- `jivo-pp-cli sales drill-down` — Expand one Slide-1 product row into a chosen dimension (litres + linetotal per value).
- `jivo-pp-cli sales flow` — Sales document chains (Quotation -> Order -> Invoice) with open/closed status and source, for a date range and company.
- `jivo-pp-cli sales flow-open-items` — Drill-down: still-open line items of a single open Sales Order or Quotation.
- `jivo-pp-cli sales hidden` — Hidden sales-invoice lines (SAP U_ARNO='H') over a date range — oil company only.
- `jivo-pp-cli sales historical` — Trailing-period average realise (₹/L) per product and per drilled dimension, as a Slide-1 overlay.
- `jivo-pp-cli sales pulse` — Cheap change-fingerprint / heartbeat for the Realise backend (empty pulse = no signal). Detect change, not data.

**targets** — Monthly target layer — product, flex (per-salesperson), segment, node (main-group x state x person x segment) and per-channel target litres/rates.

- `jivo-pp-cli targets channel` — Monthly target litres per sales channel (main group).
- `jivo-pp-cli targets flex` — Flex (flat, dimension-scoped) litre targets — currently per salesperson — for the target month.
- `jivo-pp-cli targets list` — Product-level monthly targets (tgt_ltrs, tgt_rate, source) keyed by U_TYPE|SUB_GROUP.
- `jivo-pp-cli targets nodes` — Granular target nodes: target litres by main_group x state x sales_person x segment for a month.
- `jivo-pp-cli targets segment` — Saved target overrides scoped to a single segment (empty {} when no overrides saved).

**users** — User Management (Admin) page — no JSON API; data is embedded in the page HTML. Read-only GET of the page, parsing the embedded JSON. No write endpoints (users/save, users/delete, verify-pin) are exposed.

- `jivo-pp-cli users catalog` — Permission-module catalog used by the Users page — read-only, from the page's embedded JSON.
- `jivo-pp-cli users list` — Admin user list + roles/permission groups — read-only, from the page's embedded JSON.


### Finding the right command

When you know what you want to do but not which command does it, ask the CLI directly:

```bash
jivo-pp-cli which "<capability in your own words>"
```

`which` resolves a natural-language capability query to the best matching command from this CLI's curated feature index. Exit code `0` means at least one match; exit code `2` means no confident match — fall back to `--help` or use a narrower query.

## Auth Setup

No authentication required.

Run `jivo-pp-cli doctor` to verify setup.

## Agent Mode

Add `--agent` to any command. Expands to: `--json --compact --no-input --no-color --yes`.

- **Pipeable** — JSON on stdout, errors on stderr
- **Filterable** — `--select` keeps a subset of fields. Dotted paths descend into nested structures; arrays traverse element-wise. Critical for keeping context small on verbose APIs:

  ```bash
  jivo-pp-cli targets list --agent --select id,name,status
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
jivo-pp-cli feedback "the --since flag is inclusive but docs say exclusive"
jivo-pp-cli feedback --stdin < notes.txt
jivo-pp-cli feedback list --json --limit 10
```

Entries are stored locally at `~/.local/share/jivo-pp-cli/feedback.jsonl`. They are never POSTed unless `JIVO_FEEDBACK_ENDPOINT` is set AND either `--send` is passed or `JIVO_FEEDBACK_AUTO_SEND=true`. Default behavior is local-only.

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
jivo-pp-cli profile save briefing --json
jivo-pp-cli --profile briefing targets list
jivo-pp-cli profile list --json
jivo-pp-cli profile show briefing
jivo-pp-cli profile delete briefing --yes
```

Explicit flags always win over profile values; profile values win over defaults. `agent-context` lists all available profiles under `available_profiles` so introspecting agents discover them at runtime.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Usage error (wrong arguments) |
| 3 | Resource not found |
| 5 | API error (upstream issue) |
| 7 | Rate limited (wait and retry) |
| 10 | Config error |

## Argument Parsing

Parse `$ARGUMENTS`:

1. **Empty, `help`, or `--help`** → show `jivo-pp-cli --help` output
2. **Starts with `install`** → ends with `mcp` → MCP installation; otherwise → see Prerequisites above
3. **Anything else** → Direct Use (execute as CLI command with `--agent`)

## MCP Server Installation

1. Install the MCP server:
   ```bash
   go install github.com/mvanhorn/printing-press-library/library/sales-and-crm/jivo/cmd/jivo-pp-mcp@latest
   ```
2. Register with Claude Code:
   ```bash
   claude mcp add jivo-pp-mcp -- jivo-pp-mcp
   ```
3. Verify: `claude mcp list`

## Direct Use

1. Check if installed: `which jivo-pp-cli`
   If not found, offer to install (see Prerequisites at the top of this skill).
2. Match the user query to the best command from the Unique Capabilities and Command Reference above.
3. Execute with the `--agent` flag:
   ```bash
   jivo-pp-cli <command> [subcommand] [args] --agent
   ```
4. If ambiguous, drill into subcommand help: `jivo-pp-cli <command> --help`.
