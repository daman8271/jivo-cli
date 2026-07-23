---
name: pp-jivo-ecom
title: Jivo Ecom — Printing Press CLI Skill
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: skill
tags: [jivogpt, ecom, cli, skill]
description: "Printing Press CLI for Jivo Ecom. JIVO e-commerce & quick-commerce analytics CLI (ecom.jivo."
author: "daman8271"
license: "Apache-2.0"
argument-hint: "<command> [args] | install cli|mcp"
allowed-tools: "Read Bash"
metadata:
  openclaw:
    requires:
      bins:
        - jivo-ecom-pp-cli
---

# Jivo Ecom — Printing Press CLI

## Prerequisites: Install the CLI

This skill drives the `jivo-ecom-pp-cli` binary. **You must verify the CLI is installed before invoking any command from this skill.** If it is missing, install it first:

1. Install via the Printing Press installer. It defaults binaries to `$HOME/.local/bin` on macOS/Linux and `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows:
   ```bash
   npx -y @mvanhorn/printing-press-library install jivo-ecom --cli-only
   ```
2. Verify: `jivo-ecom-pp-cli --version`
3. Ensure the reported install directory is on `$PATH` for the agent/runtime that will invoke this skill.

If the `npx` install fails before this CLI has a public-library category, install Node or use the category-specific Go fallback after publish.

If `--version` reports "command not found" after install, the runtime cannot see the binary directory on `$PATH`. Do not proceed with skill commands until verification succeeds.

JIVO e-commerce & quick-commerce analytics CLI (ecom.jivo.in) — read-only dashboards, master data, notifications, and per-platform metrics across Amazon, Blinkit, Zepto, Swiggy, BigBasket, Flipkart, Citymall, JioMart, Zomato

## When Not to Use This CLI

Do not activate this CLI for requests that require creating, updating, deleting, publishing, commenting, upvoting, inviting, ordering, sending messages, booking, purchasing, or changing remote state. This printed CLI exposes read-only commands for inspection, export, sync, and analysis.

## Command Reference

**account** — Authenticated account: current user and permissions

- `jivo-ecom-pp-cli account me` — Show the authenticated user (profile, groups, platforms, permissions)
- `jivo-ecom-pp-cli account permissions` — List the permission modules granted to the current user

**chatbot** — Read-only access to the ecom app's built-in assistant (health + conversation history)

- `jivo-ecom-pp-cli chatbot conversation` — Get a chatbot conversation (with messages) by id
- `jivo-ecom-pp-cli chatbot conversations` — List chatbot conversations
- `jivo-ecom-pp-cli chatbot health` — Chatbot service health

**dashboard** — Top-level analytics dashboards aggregated across all platforms

- `jivo-ecom-pp-cli dashboard category-breakdown` — Premium vs commodity category breakdown
- `jivo-ecom-pp-cli dashboard category-litres` — Category sales measured in litres
- `jivo-ecom-pp-cli dashboard category-platform-breakdown` — Category breakdown split by platform
- `jivo-ecom-pp-cli dashboard category-sku-breakdown` — SKU-level breakdown within a category (requires --platform)
- `jivo-ecom-pp-cli dashboard category-trend` — Category sales trend over time
- `jivo-ecom-pp-cli dashboard expiry-alerts` — Expiry alerts for a single platform
- `jivo-ecom-pp-cli dashboard expiry-alerts-po-items` — Line items for a PO behind an expiry alert
- `jivo-ecom-pp-cli dashboard expiry-alerts-pos` — Purchase orders behind a platform expiry alert
- `jivo-ecom-pp-cli dashboard fulfilment-health` — Fulfilment health summary by platform
- `jivo-ecom-pp-cli dashboard inventory-charts` — Inventory chart series
- `jivo-ecom-pp-cli dashboard latest-month` — Latest data month/year available, with source metadata
- `jivo-ecom-pp-cli dashboard lead-time-report` — Distributor lead-time report (rows, slabs, grand total)
- `jivo-ecom-pp-cli dashboard platform-expiry-alerts` — Expiry alerts aggregated across platforms
- `jivo-ecom-pp-cli dashboard primary-po-litres` — Primary purchase-order volume in litres
- `jivo-ecom-pp-cli dashboard realise-breakdown` — Realise dashboard: breakdown (net realisation analytics)
- `jivo-ecom-pp-cli dashboard realise-overview` — Realise dashboard: overview (net realisation analytics)
- `jivo-ecom-pp-cli dashboard realise-trend` — Realise dashboard: trend (net realisation analytics)
- `jivo-ecom-pp-cli dashboard realise-waterfall` — Realise dashboard: waterfall (net realisation analytics)
- `jivo-ecom-pp-cli dashboard secondary-yoy-growth` — Secondary sales year-over-year growth
- `jivo-ecom-pp-cli dashboard state-sales` — State-wise sales with mapped/unmapped coverage
- `jivo-ecom-pp-cli dashboard state-sales-detail` — Detailed state-wise sales rows
- `jivo-ecom-pp-cli dashboard state-sales-detail-cities` — State-sales detail drilled to cities
- `jivo-ecom-pp-cli dashboard state-sales-detail-city-skus` — State-sales detail drilled to city SKUs
- `jivo-ecom-pp-cli dashboard state-sales-detail-options` — Filter options (skus, cities) for state-sales detail
- `jivo-ecom-pp-cli dashboard state-sales-export` — Export state-wise sales (file/CSV payload)
- `jivo-ecom-pp-cli dashboard top-skus` — Top-selling SKUs with top risers and fallers

**master** — Master data: product catalogue and fulfilment centres

- `jivo-ecom-pp-cli master fcs` — List fulfilment centres (paginated)
- `jivo-ecom-pp-cli master products` — List master products (paginated)

**notifications** — Read-only notifications with unread count

- `jivo-ecom-pp-cli notifications get` — Get a single notification by id
- `jivo-ecom-pp-cli notifications inventory-doh` — Inventory days-of-health detail for a notification id
- `jivo-ecom-pp-cli notifications list` — List notifications with unread count

**platform** — Per-platform dashboards (Amazon, Blinkit, Zepto, Swiggy, BigBasket, Flipkart, Citymall, JioMart, Zomato)

- `jivo-ecom-pp-cli platform ads` — Advertising performance dashboard for a platform
- `jivo-ecom-pp-cli platform ads-summary` — Cross-platform advertising summary
- `jivo-ecom-pp-cli platform ads-total-sales` — Ads total-sales for a platform
- `jivo-ecom-pp-cli platform bigbasket-ads-daily-dashboard` — Bigbasket Ads Daily Dashboard for a platform
- `jivo-ecom-pp-cli platform bigbasket-ads-dashboard` — Bigbasket Ads Dashboard for a platform
- `jivo-ecom-pp-cli platform blinkit-ads-dashboard` — Blinkit Ads Dashboard for a platform
- `jivo-ecom-pp-cli platform blinkit-brandfund-dashboard` — Blinkit Brandfund Dashboard for a platform
- `jivo-ecom-pp-cli platform call-center-targets` — Call-center secondary targets (premium/commodity)
- `jivo-ecom-pp-cli platform comparison` — Comparison dashboard for a platform
- `jivo-ecom-pp-cli platform coupon` — Coupon performance dashboard for a platform
- `jivo-ecom-pp-cli platform drr` — Daily run-rate (DRR) dashboard for a platform
- `jivo-ecom-pp-cli platform flipkart-ads-dashboard` — Flipkart Ads Dashboard for a platform
- `jivo-ecom-pp-cli platform flipkart-fsn-dashboard` — Flipkart Fsn Dashboard for a platform
- `jivo-ecom-pp-cli platform inventory-match` — Inventory reconciliation/match for a platform
- `jivo-ecom-pp-cli platform landing-rate` — Monthly landing rate (blinkit/zepto/swiggy/bigbasket/flipkart_grocery only)
- `jivo-ecom-pp-cli platform landing-rate-skus` — Landing-rate SKUs (blinkit/zepto/swiggy/bigbasket/flipkart_grocery only)
- `jivo-ecom-pp-cli platform marketplace` — Marketplace dashboard for a platform
- `jivo-ecom-pp-cli platform meta` — Platform metadata (slugs, labels, config)
- `jivo-ecom-pp-cli platform month-on-month-sale` — Month-on-month sales for a platform
- `jivo-ecom-pp-cli platform month-targets` — Secondary monthly targets for a platform
- `jivo-ecom-pp-cli platform month-targets-dashboard` — Secondary month-targets dashboard across platforms
- `jivo-ecom-pp-cli platform mp-dashboard-version` — Data version stamp for a platform marketplace dashboard
- `jivo-ecom-pp-cli platform pendency` — Order pendency dashboard for a platform
- `jivo-ecom-pp-cli platform pos` — Purchase orders for a platform
- `jivo-ecom-pp-cli platform price` — Pricing dashboard for a platform
- `jivo-ecom-pp-cli platform primary` — Primary (sell-in / PO) dashboard for a platform
- `jivo-ecom-pp-cli platform primary-month-targets` — Primary monthly targets for a platform
- `jivo-ecom-pp-cli platform primary-month-targets-dashboard` — Primary month-targets dashboard across platforms
- `jivo-ecom-pp-cli platform primary-overview-total` — Primary overview totals across platforms
- `jivo-ecom-pp-cli platform primary-summary` — Primary sell-in summary across platforms
- `jivo-ecom-pp-cli platform primary-summary-version` — Data version stamp for the primary summary
- `jivo-ecom-pp-cli platform region-doh` — Region-wise days-of-health dashboard for a platform
- `jivo-ecom-pp-cli platform secondary` — Secondary (sell-out) dashboard for a platform
- `jivo-ecom-pp-cli platform secondary-monthly` — Monthly secondary-sales dashboard for a platform
- `jivo-ecom-pp-cli platform secondary-years` — Years available for the secondary dashboard
- `jivo-ecom-pp-cli platform soh-doh` — Stock-on-hand / days-of-health dashboard for a platform
- `jivo-ecom-pp-cli platform stats` — Headline stats for a platform (inventory, sells, open POs, active trucks)
- `jivo-ecom-pp-cli platform swiggy-ads-daily-dashboard` — Swiggy Ads Daily Dashboard for a platform
- `jivo-ecom-pp-cli platform swiggy-ads-dashboard` — Swiggy Ads Dashboard for a platform
- `jivo-ecom-pp-cli platform swiggy-brandfund-dashboard` — Swiggy Brandfund Dashboard for a platform
- `jivo-ecom-pp-cli platform zepto-ads-daily-dashboard` — Zepto Ads Daily Dashboard for a platform
- `jivo-ecom-pp-cli platform zepto-ads-dashboard` — Zepto Ads Dashboard for a platform
- `jivo-ecom-pp-cli platform zepto-brandfund-dashboard` — Zepto Brandfund Dashboard for a platform

**reports** — Report views: Amazon PO, appointment, and raw report tables

- `jivo-ecom-pp-cli reports amazon-po` — Amazon PO report
- `jivo-ecom-pp-cli reports amazon-po-filter-options` — Filter options for the Amazon PO report
- `jivo-ecom-pp-cli reports amazon-po-matrix` — Amazon PO matrix (by month/year)
- `jivo-ecom-pp-cli reports amazon-po-new-po` — Amazon new-PO report
- `jivo-ecom-pp-cli reports amazon-po-summary` — Amazon PO report summary
- `jivo-ecom-pp-cli reports appointment` — Appointment report
- `jivo-ecom-pp-cli reports appointment-filter-options` — Filter options (pos_numbers, destination_fcs) for the appointment report
- `jivo-ecom-pp-cli reports appointment-summary` — Appointment report summary
- `jivo-ecom-pp-cli reports columns` — Column definitions for a report view
- `jivo-ecom-pp-cli reports raw` — Raw rows for a report view

**sap** — SAP HANA read layer: distributors, inventory, sales invoices, stock

- `jivo-ecom-pp-cli sap distributor` — Get a distributor (profile, addresses, contacts) by card code
- `jivo-ecom-pp-cli sap distributor-inventory` — Distributor inventory
- `jivo-ecom-pp-cli sap distributor-invoices` — Invoices for a distributor by card code
- `jivo-ecom-pp-cli sap distributor-orders` — Orders for a distributor by card code
- `jivo-ecom-pp-cli sap distributors` — List SAP distributors
- `jivo-ecom-pp-cli sap inventory-finished-goods` — Finished-goods inventory
- `jivo-ecom-pp-cli sap inventory-overview` — Inventory overview
- `jivo-ecom-pp-cli sap inventory-warehouse-comparison` — Inventory comparison across warehouses
- `jivo-ecom-pp-cli sap items` — SAP item master
- `jivo-ecom-pp-cli sap platform-distributor` — A platform-distributor mapping by card code
- `jivo-ecom-pp-cli sap platform-distributors` — Distributors mapped to a platform
- `jivo-ecom-pp-cli sap platform-sales-invoices` — Sales invoices for a platform
- `jivo-ecom-pp-cli sap sales-analysis` — Sales analysis over a date range
- `jivo-ecom-pp-cli sap sales-invoice` — Get a sales invoice by id
- `jivo-ecom-pp-cli sap sales-invoice-lines` — Line items for a sales invoice by id (note: upstream SAP query may 500)
- `jivo-ecom-pp-cli sap sales-invoices` — List SAP sales invoices
- `jivo-ecom-pp-cli sap stock-by-warehouse` — Stock levels by warehouse

**shipment** — Amazon Shipment Planner (read-only). Requires Shipment Planner access; returns 403 without it.

- `jivo-ecom-pp-cli shipment all-appointments` — All shipment appointments
- `jivo-ecom-pp-cli shipment appointment-commits` — Appointment commit records
- `jivo-ecom-pp-cli shipment appointment-dates` — Available appointment dates
- `jivo-ecom-pp-cli shipment appointment-extra-pos` — Extra POs for an appointment
- `jivo-ecom-pp-cli shipment appointment-items` — Items for an appointment
- `jivo-ecom-pp-cli shipment appointments` — Shipment appointments
- `jivo-ecom-pp-cli shipment asin-catalog` — ASIN catalog
- `jivo-ecom-pp-cli shipment inventory` — Shipment planning inventory
- `jivo-ecom-pp-cli shipment po-items` — PO items available to ship
- `jivo-ecom-pp-cli shipment po-shipment-lookup` — Lookup shipments for a PO
- `jivo-ecom-pp-cli shipment po-short-supply` — PO short-supply report
- `jivo-ecom-pp-cli shipment record` — Shipment record
- `jivo-ecom-pp-cli shipment shipment` — Get a shipment by id
- `jivo-ecom-pp-cli shipment shipment-invoice-file` — Download an invoice file for a shipment
- `jivo-ecom-pp-cli shipment shipment-invoices` — Invoices for a shipment
- `jivo-ecom-pp-cli shipment shipment-po-document` — A PO document for a shipment
- `jivo-ecom-pp-cli shipment shipment-po-documents` — PO documents for a shipment
- `jivo-ecom-pp-cli shipment shipments` — List shipments
- `jivo-ecom-pp-cli shipment shipments-deletion-log` — Shipment deletion log
- `jivo-ecom-pp-cli shipment shipments-doh-auto-fill` — DOH auto-fill suggestions
- `jivo-ecom-pp-cli shipment shipments-pending-approvals` — Shipments pending approval
- `jivo-ecom-pp-cli shipment shipments-stats` — Shipment stats

**tables** — Dynamic data-table browser over the underlying warehouse tables

- `jivo-ecom-pp-cli tables columns` — Column definitions for a table
- `jivo-ecom-pp-cli tables count` — Row count for a single table
- `jivo-ecom-pp-cli tables counts` — Row counts for every available data table
- `jivo-ecom-pp-cli tables data` — Paginated rows for a table (server-shaped payload)
- `jivo-ecom-pp-cli tables distinct` — Distinct values for a column in a table

**upload** — Read-only views of uploaded reference data

- `jivo-ecom-pp-cli upload ads-master` — Ads master sheet (columns, rows)
- `jivo-ecom-pp-cli upload master-sheet` — Master sheet
- `jivo-ecom-pp-cli upload pincode-mapping` — Pincode mapping table

**uploads** — Upload job history (read-only)

- `jivo-ecom-pp-cli uploads get` — Get an upload job (summary, errors, diagnostics) by id
- `jivo-ecom-pp-cli uploads list` — List upload jobs


### Finding the right command

When you know what you want to do but not which command does it, ask the CLI directly:

```bash
jivo-ecom-pp-cli which "<capability in your own words>"
```

`which` resolves a natural-language capability query to the best matching command from this CLI's curated feature index. Exit code `0` means at least one match; exit code `2` means no confident match — fall back to `--help` or use a narrower query.

## Auth Setup

Run `jivo-ecom-pp-cli auth setup` for the URL and steps to obtain a token (add `--launch` to open the URL). Then store it:

```bash
jivo-ecom-pp-cli auth set-token YOUR_TOKEN_HERE
```

Or set `JIVO_ECOM_TOKEN` as an environment variable.

Run `jivo-ecom-pp-cli doctor` to verify setup.

## Agent Mode

Add `--agent` to any command. Expands to: `--json --compact --no-input --no-color --yes`.

- **Pipeable** — JSON on stdout, errors on stderr
- **Filterable** — `--select` keeps a subset of fields. Dotted paths descend into nested structures; arrays traverse element-wise. Critical for keeping context small on verbose APIs:

  ```bash
  jivo-ecom-pp-cli notifications list --agent --select id,name,status
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
jivo-ecom-pp-cli feedback "the --since flag is inclusive but docs say exclusive"
jivo-ecom-pp-cli feedback --stdin < notes.txt
jivo-ecom-pp-cli feedback list --json --limit 10
```

Entries are stored locally at `~/.local/share/jivo-ecom-pp-cli/feedback.jsonl`. They are never POSTed unless `JIVO_ECOM_FEEDBACK_ENDPOINT` is set AND either `--send` is passed or `JIVO_ECOM_FEEDBACK_AUTO_SEND=true`. Default behavior is local-only.

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
jivo-ecom-pp-cli profile save briefing --json
jivo-ecom-pp-cli --profile briefing notifications list
jivo-ecom-pp-cli profile list --json
jivo-ecom-pp-cli profile show briefing
jivo-ecom-pp-cli profile delete briefing --yes
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

1. **Empty, `help`, or `--help`** → show `jivo-ecom-pp-cli --help` output
2. **Starts with `install`** → ends with `mcp` → MCP installation; otherwise → see Prerequisites above
3. **Anything else** → Direct Use (execute as CLI command with `--agent`)

## MCP Server Installation

Install the MCP binary from this CLI's published public-library entry or pre-built release, then register it:

```bash
claude mcp add jivo-ecom-pp-mcp -- jivo-ecom-pp-mcp
```

Verify: `claude mcp list`

## Direct Use

1. Check if installed: `which jivo-ecom-pp-cli`
   If not found, offer to install (see Prerequisites at the top of this skill).
2. Match the user query to the best command from the Unique Capabilities and Command Reference above.
3. Execute with the `--agent` flag:
   ```bash
   jivo-ecom-pp-cli <command> [subcommand] [args] --agent
   ```
4. If ambiguous, drill into subcommand help: `jivo-ecom-pp-cli <command> --help`.

Linked: [[docs/ecom/ECOM_MAP|ECOM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
