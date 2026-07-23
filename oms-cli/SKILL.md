---
name: pp-oms
title: OMS — Printing Press CLI Skill
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: skill
tags: [jivogpt, oms, cli, skill]
description: "Printing Press CLI for Oms. JIVO OMS (Order Management System) CLI — READ-ONLY."
author: "daman8271"
license: "Apache-2.0"
argument-hint: "<command> [args] | install cli|mcp"
allowed-tools: "Read Bash"
metadata:
  openclaw:
    requires:
      bins:
        - oms-pp-cli
---

# Oms — Printing Press CLI

## Prerequisites: Install the CLI

This skill drives the `oms-pp-cli` binary. **You must verify the CLI is installed before invoking any command from this skill.** If it is missing, install it first:

1. Install via the Printing Press installer. It defaults binaries to `$HOME/.local/bin` on macOS/Linux and `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows:
   ```bash
   npx -y @mvanhorn/printing-press-library install oms --cli-only
   ```
2. Verify: `oms-pp-cli --version`
3. Ensure the reported install directory is on `$PATH` for the agent/runtime that will invoke this skill.

If the `npx` install fails before this CLI has a public-library category, install Node or use the category-specific Go fallback after publish.

If `--version` reports "command not found" after install, the runtime cannot see the binary directory on `$PATH`. Do not proceed with skill commands until verification succeeds.

JIVO OMS (Order Management System) CLI — READ-ONLY. Orders, quotations, schemes, approvals, party & product assignments, SAP Business One sync, SAP HANA live stock, invoices/SKU, and the invoice tracker at oms.jivo.in. Every command is a GET; no mutating endpoint is wrapped.

## When Not to Use This CLI

Do not activate this CLI for requests that require creating, updating, deleting, publishing, commenting, upvoting, inviting, ordering, sending messages, booking, purchasing, or changing remote state. This printed CLI exposes read-only commands for inspection, export, sync, and analysis.

## Command Reference

**account** — Authenticated account, users, roles, and reference master data (companies, states, categories, main groups)

- `oms-pp-cli account categories` — List product categories (e.g. OIL)
- `oms-pp-cli account companies` — List companies (Jivo Mart, Jivo Wellness)
- `oms-pp-cli account main-groups` — List main groups (ROI, GT, MT, BRANCH, ...)
- `oms-pp-cli account party-products` — Products assigned to a party (argument is the SAP card_code, not a numeric id)
- `oms-pp-cli account profile` — Show the authenticated user (role, company, main groups, states, category, page permissions)
- `oms-pp-cli account roles` — List roles (admin, auditor, billing, rate approver, manager, etc.)
- `oms-pp-cli account states` — List states
- `oms-pp-cli account user-page-permissions` — Page-permission grants for a user
- `oms-pp-cli account user-parties` — Parties (customers) assigned to a user
- `oms-pp-cli account users` — List app users

**dashboard** — Dashboard KPIs and chart series

- `oms-pp-cli dashboard charts` — Dashboard chart series (visual overview, statewise)
- `oms-pp-cli dashboard summary` — Dashboard KPI block (total orders, total sales, completion)

**hana** — Live SAP HANA queries — product stock, sales orders, customers, and the order-creation wizard lookups

- `oms-pp-cli hana address` — Addresses for a customer. Requires --card-code.
- `oms-pp-cli hana all-customers` — All customers from SAP HANA
- `oms-pp-cli hana batch-details` — Batch details for an item in a warehouse. Requires --item-code and --whs-code.
- `oms-pp-cli hana customer-details` — Customer master detail. Requires --card-code.
- `oms-pp-cli hana fg-items` — Finished-goods items
- `oms-pp-cli hana freight-masters` — Freight master records
- `oms-pp-cli hana inventory-details` — Per-warehouse inventory for an item. Requires --item-code.
- `oms-pp-cli hana item-price` — Price for an item on a price list. Requires --item-code and --price-list.
- `oms-pp-cli hana next-doc-number` — Next document number for a document type. Requires --doc-type.
- `oms-pp-cli hana open-parties` — Parties with open transactions
- `oms-pp-cli hana product-so` — Product sales-order data
- `oms-pp-cli hana product-stock` — Live product stock from SAP HANA
- `oms-pp-cli hana salesperson-details` — Salesperson detail. Requires --slp-code.
- `oms-pp-cli hana so` — Sales orders

**invoices** — Sales invoices, invoice review, and SKU master/image data

- `oms-pp-cli invoices all` — Invoice review queue (all invoices). Optionally filter by status.
- `oms-pp-cli invoices history` — Status-history timeline for an invoice
- `oms-pp-cli invoices sku` — Per-SKU detail
- `oms-pp-cli invoices skus` — All SKUs
- `oms-pp-cli invoices skus-pending` — SKUs pending review

**orders** — Orders: list, detail, status lifecycle, tracking, dispatch, approval-flow config, and the party/product lookups the order screens use

- `oms-pp-cli orders addresses` — Bill-to / ship-to addresses for a party. Requires --card-code.
- `oms-pp-cli orders branch` — SAP branch / BPL list
- `oms-pp-cli orders by-user` — Orders raised by a specific user (source for View Orders / Order Tracking)
- `oms-pp-cli orders detail` — Full order with line items, addresses, rate approvals, SAP doc number
- `oms-pp-cli orders dispatches` — Dispatch-from locations
- `oms-pp-cli orders flow-config` — Global order approval-flow configuration
- `oms-pp-cli orders list` — All orders (admin-wide). Filter by status/stage.
- `oms-pp-cli orders logs` — Status-change audit trail for an order (drives the tracking timeline)
- `oms-pp-cli orders notifications` — Order-status notifications for the current user
- `oms-pp-cli orders parties` — Assigned-party dropdown (card_code -> card_name) for the current user
- `oms-pp-cli orders party-flow-config` — Per-party approval-flow configuration
- `oms-pp-cli orders party-products` — Products (with rates) assigned to a party, for the order product selector
- `oms-pp-cli orders products` — Global product list
- `oms-pp-cli orders schemes` — Sales schemes / promotions
- `oms-pp-cli orders staff-products` — Staff-assigned products
- `oms-pp-cli orders status` — Order status master (id -> name)
- `oms-pp-cli orders status-tracking` — Approval queue for a stage. Requires --mode.
- `oms-pp-cli orders stock-check` — Per-order required-qty vs available-stock (legacy view)

**quotations** — Sales quotations and their SAP push status

- `oms-pp-cli quotations overview` — All quotations with SAP doc numbers and cancellation state
- `oms-pp-cli quotations status` — Open/closed SAP status badges for specific quotations

**sap** — SAP Business One sync — history logs and synced master data (branches, parties, products)

- `oms-pp-cli sap addresses` — SAP addresses
- `oms-pp-cli sap branches` — SAP branches
- `oms-pp-cli sap logs` — SAP sync history (sync_type, status, records processed/created/updated, duration)
- `oms-pp-cli sap parties` — SAP parties (business partners)
- `oms-pp-cli sap party-categories` — SAP parties filtered by category
- `oms-pp-cli sap product-varieties` — SAP product varieties
- `oms-pp-cli sap products` — SAP products
- `oms-pp-cli sap quotation-log` — Per-order SAP quotation push record

**tracker** — Invoice-tracker sub-app (access-gated: returns 403 for non-tracker roles). Read endpoints for a tracker-enabled account.

- `oms-pp-cli tracker admin-lookups` — Tracker admin: lookup set by type
- `oms-pp-cli tracker admin-stages` — Tracker admin: stage definitions
- `oms-pp-cli tracker admin-tracker-users` — Tracker admin: tracker-role users
- `oms-pp-cli tracker admin-users` — Tracker admin: users
- `oms-pp-cli tracker alerts` — Tracker alerts
- `oms-pp-cli tracker all-invoices` — All tracker invoices
- `oms-pp-cli tracker all-invoices-export` — Export of all tracker invoices
- `oms-pp-cli tracker invoice-detail` — Single tracker invoice
- `oms-pp-cli tracker invoices` — Tracker invoices
- `oms-pp-cli tracker lookups` — Tracker lookup reference data
- `oms-pp-cli tracker my-queue` — Current user's tracker work queue
- `oms-pp-cli tracker reports` — Tracker reports
- `oms-pp-cli tracker stage-advanced` — Advanced stage view
- `oms-pp-cli tracker vendors` — Tracker vendors


### Finding the right command

When you know what you want to do but not which command does it, ask the CLI directly:

```bash
oms-pp-cli which "<capability in your own words>"
```

`which` resolves a natural-language capability query to the best matching command from this CLI's curated feature index. Exit code `0` means at least one match; exit code `2` means no confident match — fall back to `--help` or use a narrower query.

## Auth Setup

Run `oms-pp-cli auth setup` for the URL and steps to obtain a token (add `--launch` to open the URL). Then store it:

```bash
oms-pp-cli auth set-token YOUR_TOKEN_HERE
```

Or set `OMS_TOKEN` as an environment variable.

Run `oms-pp-cli doctor` to verify setup.

## Agent Mode

Add `--agent` to any command. Expands to: `--json --compact --no-input --no-color --yes`.

- **Pipeable** — JSON on stdout, errors on stderr
- **Filterable** — `--select` keeps a subset of fields. Dotted paths descend into nested structures; arrays traverse element-wise. Critical for keeping context small on verbose APIs:

  ```bash
  oms-pp-cli orders list --agent --select id,name,status
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
oms-pp-cli feedback "the --since flag is inclusive but docs say exclusive"
oms-pp-cli feedback --stdin < notes.txt
oms-pp-cli feedback list --json --limit 10
```

Entries are stored locally at `~/.local/share/oms-pp-cli/feedback.jsonl`. They are never POSTed unless `OMS_FEEDBACK_ENDPOINT` is set AND either `--send` is passed or `OMS_FEEDBACK_AUTO_SEND=true`. Default behavior is local-only.

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
oms-pp-cli profile save briefing --json
oms-pp-cli --profile briefing orders list
oms-pp-cli profile list --json
oms-pp-cli profile show briefing
oms-pp-cli profile delete briefing --yes
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

1. **Empty, `help`, or `--help`** → show `oms-pp-cli --help` output
2. **Starts with `install`** → ends with `mcp` → MCP installation; otherwise → see Prerequisites above
3. **Anything else** → Direct Use (execute as CLI command with `--agent`)

## MCP Server Installation

Install the MCP binary from this CLI's published public-library entry or pre-built release, then register it:

```bash
claude mcp add oms-pp-mcp -- oms-pp-mcp
```

Verify: `claude mcp list`

## Direct Use

1. Check if installed: `which oms-pp-cli`
   If not found, offer to install (see Prerequisites at the top of this skill).
2. Match the user query to the best command from the Unique Capabilities and Command Reference above.
3. Execute with the `--agent` flag:
   ```bash
   oms-pp-cli <command> [subcommand] [args] --agent
   ```
4. If ambiguous, drill into subcommand help: `oms-pp-cli <command> --help`.

Linked: [[docs/oms/OMS_MAP|OMS_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
