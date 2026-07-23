---
title: "Jivo Ecom CLI"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, ecom-cli, cli]
---

# Jivo Ecom CLI

JIVO e-commerce & quick-commerce analytics CLI (ecom.jivo.in) — read-only dashboards, master data, notifications, and per-platform metrics across Amazon, Blinkit, Zepto, Swiggy, BigBasket, Flipkart, Citymall, JioMart, Zomato

Created by [@daman8271](https://github.com/daman8271).

## Install

The recommended path installs both the `jivo-ecom-pp-cli` binary and the `pp-jivo-ecom` agent skill (Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, and other agents supported by the upstream [`skills`](https://github.com/vercel-labs/skills) CLI) in one shot:

```bash
npx -y @mvanhorn/printing-press-library install jivo-ecom
```

For CLI only (no skill):

```bash
npx -y @mvanhorn/printing-press-library install jivo-ecom --cli-only
```

For skill only — installs the skill into the same agents as the default command above, but skips the CLI binary (use this to update or reinstall just the skill):

```bash
npx -y @mvanhorn/printing-press-library install jivo-ecom --skill-only
```

To constrain the skill install to one or more specific agents (repeatable — agent names match the [`skills`](https://github.com/vercel-labs/skills) CLI):

```bash
npx -y @mvanhorn/printing-press-library install jivo-ecom --agent claude-code
npx -y @mvanhorn/printing-press-library install jivo-ecom --agent claude-code --agent codex
```

### Without Node

The generated install path is category-agnostic until this CLI is published. If `npx` is not available before publish, install Node or use the category-specific Go fallback from the public-library entry after publish.

### Pre-built binary

Download a pre-built binary for your platform from the [latest release](https://github.com/mvanhorn/printing-press-library/releases/tag/jivo-ecom-current). On macOS, clear the Gatekeeper quarantine: `xattr -d com.apple.quarantine <binary>`. On Unix, mark it executable: `chmod +x <binary>`.

<!-- pp-hermes-install-anchor -->
## Install for Hermes

Install the CLI binary first. The installer writes binaries to a per-user managed bin directory by default: `$HOME/.local/bin` on macOS/Linux and `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows.

```bash
npx -y @mvanhorn/printing-press-library install jivo-ecom --cli-only
```

Then install the focused Hermes skill.

From the Hermes CLI:

```bash
hermes skills install mvanhorn/printing-press-library/cli-skills/pp-jivo-ecom --force
```

Inside a Hermes chat session:

```bash
/skills install mvanhorn/printing-press-library/cli-skills/pp-jivo-ecom --force
```

Restart the Hermes session or gateway if the newly installed skill is not visible immediately.

## Install for OpenClaw
Install both the CLI binary and the focused OpenClaw skill. The installer defaults binaries to a per-user bin directory (`$HOME/.local/bin` on macOS/Linux, `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows):

```bash
npx -y @mvanhorn/printing-press-library install jivo-ecom --agent openclaw
```

Restart the OpenClaw session or gateway if the newly installed skill is not visible immediately.

## Use with Claude Desktop

This CLI ships an [MCPB](https://github.com/modelcontextprotocol/mcpb) bundle — Claude Desktop's standard format for one-click MCP extension installs (no JSON config required).

To install:

1. Download the `.mcpb` for your platform from the [latest release](https://github.com/mvanhorn/printing-press-library/releases/tag/jivo-ecom-current).
2. Double-click the `.mcpb` file. Claude Desktop opens and walks you through the install.
3. Fill in `JIVO_ECOM_TOKEN` when Claude Desktop prompts you.

Requires Claude Desktop 1.0.0 or later. Pre-built bundles ship for macOS Apple Silicon (`darwin-arm64`) and Windows (`amd64`, `arm64`); for other platforms, use the manual config below.

<details>
<summary>Manual JSON config (advanced)</summary>

If you can't use the MCPB bundle (older Claude Desktop, unsupported platform), install the MCP binary and configure it manually.


Install the MCP binary from this CLI's published public-library entry or pre-built release.

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "jivo-ecom": {
      "command": "jivo-ecom-pp-mcp",
      "env": {
        "JIVO_ECOM_TOKEN": "<your-key>"
      }
    }
  }
}
```

</details>

## Quick Start

### 1. Install

See [Install](#install) above.

### 2. Set Up Credentials

Get your access token from your API provider's developer portal, then store it:

```bash
jivo-ecom-pp-cli auth set-token YOUR_TOKEN_HERE
```

Or set it via environment variable:

```bash
export JIVO_ECOM_TOKEN="your-token-here"
```

### 3. Verify Setup

```bash
jivo-ecom-pp-cli doctor
```

This checks your configuration and credentials.

### 4. Try Your First Command

```bash
jivo-ecom-pp-cli notifications list
```

## Usage

Run `jivo-ecom-pp-cli --help` for the full command reference and flag list.

## Commands

### account

Authenticated account: current user and permissions

- **`jivo-ecom-pp-cli account me`** - Show the authenticated user (profile, groups, platforms, permissions)
- **`jivo-ecom-pp-cli account permissions`** - List the permission modules granted to the current user

### chatbot

Read-only access to the ecom app's built-in assistant (health + conversation history)

- **`jivo-ecom-pp-cli chatbot conversation`** - Get a chatbot conversation (with messages) by id
- **`jivo-ecom-pp-cli chatbot conversations`** - List chatbot conversations
- **`jivo-ecom-pp-cli chatbot health`** - Chatbot service health

### dashboard

Top-level analytics dashboards aggregated across all platforms

- **`jivo-ecom-pp-cli dashboard category-breakdown`** - Premium vs commodity category breakdown
- **`jivo-ecom-pp-cli dashboard category-litres`** - Category sales measured in litres
- **`jivo-ecom-pp-cli dashboard category-platform-breakdown`** - Category breakdown split by platform
- **`jivo-ecom-pp-cli dashboard category-sku-breakdown`** - SKU-level breakdown within a category (requires --platform)
- **`jivo-ecom-pp-cli dashboard category-trend`** - Category sales trend over time
- **`jivo-ecom-pp-cli dashboard expiry-alerts`** - Expiry alerts for a single platform
- **`jivo-ecom-pp-cli dashboard expiry-alerts-po-items`** - Line items for a PO behind an expiry alert
- **`jivo-ecom-pp-cli dashboard expiry-alerts-pos`** - Purchase orders behind a platform expiry alert
- **`jivo-ecom-pp-cli dashboard fulfilment-health`** - Fulfilment health summary by platform
- **`jivo-ecom-pp-cli dashboard inventory-charts`** - Inventory chart series
- **`jivo-ecom-pp-cli dashboard latest-month`** - Latest data month/year available, with source metadata
- **`jivo-ecom-pp-cli dashboard lead-time-report`** - Distributor lead-time report (rows, slabs, grand total)
- **`jivo-ecom-pp-cli dashboard platform-expiry-alerts`** - Expiry alerts aggregated across platforms
- **`jivo-ecom-pp-cli dashboard primary-po-litres`** - Primary purchase-order volume in litres
- **`jivo-ecom-pp-cli dashboard realise-breakdown`** - Realise dashboard: breakdown (net realisation analytics)
- **`jivo-ecom-pp-cli dashboard realise-overview`** - Realise dashboard: overview (net realisation analytics)
- **`jivo-ecom-pp-cli dashboard realise-trend`** - Realise dashboard: trend (net realisation analytics)
- **`jivo-ecom-pp-cli dashboard realise-waterfall`** - Realise dashboard: waterfall (net realisation analytics)
- **`jivo-ecom-pp-cli dashboard secondary-yoy-growth`** - Secondary sales year-over-year growth
- **`jivo-ecom-pp-cli dashboard state-sales`** - State-wise sales with mapped/unmapped coverage
- **`jivo-ecom-pp-cli dashboard state-sales-detail`** - Detailed state-wise sales rows
- **`jivo-ecom-pp-cli dashboard state-sales-detail-cities`** - State-sales detail drilled to cities
- **`jivo-ecom-pp-cli dashboard state-sales-detail-city-skus`** - State-sales detail drilled to city SKUs
- **`jivo-ecom-pp-cli dashboard state-sales-detail-options`** - Filter options (skus, cities) for state-sales detail
- **`jivo-ecom-pp-cli dashboard state-sales-export`** - Export state-wise sales (file/CSV payload)
- **`jivo-ecom-pp-cli dashboard top-skus`** - Top-selling SKUs with top risers and fallers

### master

Master data: product catalogue and fulfilment centres

- **`jivo-ecom-pp-cli master fcs`** - List fulfilment centres (paginated)
- **`jivo-ecom-pp-cli master products`** - List master products (paginated)

### notifications

Read-only notifications with unread count

- **`jivo-ecom-pp-cli notifications get`** - Get a single notification by id
- **`jivo-ecom-pp-cli notifications inventory-doh`** - Inventory days-of-health detail for a notification id
- **`jivo-ecom-pp-cli notifications list`** - List notifications with unread count

### platform

Per-platform dashboards (Amazon, Blinkit, Zepto, Swiggy, BigBasket, Flipkart, Citymall, JioMart, Zomato)

- **`jivo-ecom-pp-cli platform ads`** - Advertising performance dashboard for a platform
- **`jivo-ecom-pp-cli platform ads-summary`** - Cross-platform advertising summary
- **`jivo-ecom-pp-cli platform ads-total-sales`** - Ads total-sales for a platform
- **`jivo-ecom-pp-cli platform bigbasket-ads-daily-dashboard`** - Bigbasket Ads Daily Dashboard for a platform
- **`jivo-ecom-pp-cli platform bigbasket-ads-dashboard`** - Bigbasket Ads Dashboard for a platform
- **`jivo-ecom-pp-cli platform blinkit-ads-dashboard`** - Blinkit Ads Dashboard for a platform
- **`jivo-ecom-pp-cli platform blinkit-brandfund-dashboard`** - Blinkit Brandfund Dashboard for a platform
- **`jivo-ecom-pp-cli platform call-center-targets`** - Call-center secondary targets (premium/commodity)
- **`jivo-ecom-pp-cli platform comparison`** - Comparison dashboard for a platform
- **`jivo-ecom-pp-cli platform coupon`** - Coupon performance dashboard for a platform
- **`jivo-ecom-pp-cli platform drr`** - Daily run-rate (DRR) dashboard for a platform
- **`jivo-ecom-pp-cli platform flipkart-ads-dashboard`** - Flipkart Ads Dashboard for a platform
- **`jivo-ecom-pp-cli platform flipkart-fsn-dashboard`** - Flipkart Fsn Dashboard for a platform
- **`jivo-ecom-pp-cli platform inventory-match`** - Inventory reconciliation/match for a platform
- **`jivo-ecom-pp-cli platform landing-rate`** - Monthly landing rate (blinkit/zepto/swiggy/bigbasket/flipkart_grocery only)
- **`jivo-ecom-pp-cli platform landing-rate-skus`** - Landing-rate SKUs (blinkit/zepto/swiggy/bigbasket/flipkart_grocery only)
- **`jivo-ecom-pp-cli platform marketplace`** - Marketplace dashboard for a platform
- **`jivo-ecom-pp-cli platform meta`** - Platform metadata (slugs, labels, config)
- **`jivo-ecom-pp-cli platform month-on-month-sale`** - Month-on-month sales for a platform
- **`jivo-ecom-pp-cli platform month-targets`** - Secondary monthly targets for a platform
- **`jivo-ecom-pp-cli platform month-targets-dashboard`** - Secondary month-targets dashboard across platforms
- **`jivo-ecom-pp-cli platform mp-dashboard-version`** - Data version stamp for a platform marketplace dashboard
- **`jivo-ecom-pp-cli platform pendency`** - Order pendency dashboard for a platform
- **`jivo-ecom-pp-cli platform pos`** - Purchase orders for a platform
- **`jivo-ecom-pp-cli platform price`** - Pricing dashboard for a platform
- **`jivo-ecom-pp-cli platform primary`** - Primary (sell-in / PO) dashboard for a platform
- **`jivo-ecom-pp-cli platform primary-month-targets`** - Primary monthly targets for a platform
- **`jivo-ecom-pp-cli platform primary-month-targets-dashboard`** - Primary month-targets dashboard across platforms
- **`jivo-ecom-pp-cli platform primary-overview-total`** - Primary overview totals across platforms
- **`jivo-ecom-pp-cli platform primary-summary`** - Primary sell-in summary across platforms
- **`jivo-ecom-pp-cli platform primary-summary-version`** - Data version stamp for the primary summary
- **`jivo-ecom-pp-cli platform region-doh`** - Region-wise days-of-health dashboard for a platform
- **`jivo-ecom-pp-cli platform secondary`** - Secondary (sell-out) dashboard for a platform
- **`jivo-ecom-pp-cli platform secondary-monthly`** - Monthly secondary-sales dashboard for a platform
- **`jivo-ecom-pp-cli platform secondary-years`** - Years available for the secondary dashboard
- **`jivo-ecom-pp-cli platform soh-doh`** - Stock-on-hand / days-of-health dashboard for a platform
- **`jivo-ecom-pp-cli platform stats`** - Headline stats for a platform (inventory, sells, open POs, active trucks)
- **`jivo-ecom-pp-cli platform swiggy-ads-daily-dashboard`** - Swiggy Ads Daily Dashboard for a platform
- **`jivo-ecom-pp-cli platform swiggy-ads-dashboard`** - Swiggy Ads Dashboard for a platform
- **`jivo-ecom-pp-cli platform swiggy-brandfund-dashboard`** - Swiggy Brandfund Dashboard for a platform
- **`jivo-ecom-pp-cli platform zepto-ads-daily-dashboard`** - Zepto Ads Daily Dashboard for a platform
- **`jivo-ecom-pp-cli platform zepto-ads-dashboard`** - Zepto Ads Dashboard for a platform
- **`jivo-ecom-pp-cli platform zepto-brandfund-dashboard`** - Zepto Brandfund Dashboard for a platform

### reports

Report views: Amazon PO, appointment, and raw report tables

- **`jivo-ecom-pp-cli reports amazon-po`** - Amazon PO report
- **`jivo-ecom-pp-cli reports amazon-po-filter-options`** - Filter options for the Amazon PO report
- **`jivo-ecom-pp-cli reports amazon-po-matrix`** - Amazon PO matrix (by month/year)
- **`jivo-ecom-pp-cli reports amazon-po-new-po`** - Amazon new-PO report
- **`jivo-ecom-pp-cli reports amazon-po-summary`** - Amazon PO report summary
- **`jivo-ecom-pp-cli reports appointment`** - Appointment report
- **`jivo-ecom-pp-cli reports appointment-filter-options`** - Filter options (pos_numbers, destination_fcs) for the appointment report
- **`jivo-ecom-pp-cli reports appointment-summary`** - Appointment report summary
- **`jivo-ecom-pp-cli reports columns`** - Column definitions for a report view
- **`jivo-ecom-pp-cli reports raw`** - Raw rows for a report view

### sap

SAP HANA read layer: distributors, inventory, sales invoices, stock

- **`jivo-ecom-pp-cli sap distributor`** - Get a distributor (profile, addresses, contacts) by card code
- **`jivo-ecom-pp-cli sap distributor-inventory`** - Distributor inventory
- **`jivo-ecom-pp-cli sap distributor-invoices`** - Invoices for a distributor by card code
- **`jivo-ecom-pp-cli sap distributor-orders`** - Orders for a distributor by card code
- **`jivo-ecom-pp-cli sap distributors`** - List SAP distributors
- **`jivo-ecom-pp-cli sap inventory-finished-goods`** - Finished-goods inventory
- **`jivo-ecom-pp-cli sap inventory-overview`** - Inventory overview
- **`jivo-ecom-pp-cli sap inventory-warehouse-comparison`** - Inventory comparison across warehouses
- **`jivo-ecom-pp-cli sap items`** - SAP item master
- **`jivo-ecom-pp-cli sap platform-distributor`** - A platform-distributor mapping by card code
- **`jivo-ecom-pp-cli sap platform-distributors`** - Distributors mapped to a platform
- **`jivo-ecom-pp-cli sap platform-sales-invoices`** - Sales invoices for a platform
- **`jivo-ecom-pp-cli sap sales-analysis`** - Sales analysis over a date range
- **`jivo-ecom-pp-cli sap sales-invoice`** - Get a sales invoice by id
- **`jivo-ecom-pp-cli sap sales-invoice-lines`** - Line items for a sales invoice by id (note: upstream SAP query may 500)
- **`jivo-ecom-pp-cli sap sales-invoices`** - List SAP sales invoices
- **`jivo-ecom-pp-cli sap stock-by-warehouse`** - Stock levels by warehouse

### shipment

Amazon Shipment Planner (read-only). Requires Shipment Planner access; returns 403 without it.

- **`jivo-ecom-pp-cli shipment all-appointments`** - All shipment appointments
- **`jivo-ecom-pp-cli shipment appointment-commits`** - Appointment commit records
- **`jivo-ecom-pp-cli shipment appointment-dates`** - Available appointment dates
- **`jivo-ecom-pp-cli shipment appointment-extra-pos`** - Extra POs for an appointment
- **`jivo-ecom-pp-cli shipment appointment-items`** - Items for an appointment
- **`jivo-ecom-pp-cli shipment appointments`** - Shipment appointments
- **`jivo-ecom-pp-cli shipment asin-catalog`** - ASIN catalog
- **`jivo-ecom-pp-cli shipment inventory`** - Shipment planning inventory
- **`jivo-ecom-pp-cli shipment po-items`** - PO items available to ship
- **`jivo-ecom-pp-cli shipment po-shipment-lookup`** - Lookup shipments for a PO
- **`jivo-ecom-pp-cli shipment po-short-supply`** - PO short-supply report
- **`jivo-ecom-pp-cli shipment record`** - Shipment record
- **`jivo-ecom-pp-cli shipment shipment`** - Get a shipment by id
- **`jivo-ecom-pp-cli shipment shipment-invoice-file`** - Download an invoice file for a shipment
- **`jivo-ecom-pp-cli shipment shipment-invoices`** - Invoices for a shipment
- **`jivo-ecom-pp-cli shipment shipment-po-document`** - A PO document for a shipment
- **`jivo-ecom-pp-cli shipment shipment-po-documents`** - PO documents for a shipment
- **`jivo-ecom-pp-cli shipment shipments`** - List shipments
- **`jivo-ecom-pp-cli shipment shipments-deletion-log`** - Shipment deletion log
- **`jivo-ecom-pp-cli shipment shipments-doh-auto-fill`** - DOH auto-fill suggestions
- **`jivo-ecom-pp-cli shipment shipments-pending-approvals`** - Shipments pending approval
- **`jivo-ecom-pp-cli shipment shipments-stats`** - Shipment stats

### tables

Dynamic data-table browser over the underlying warehouse tables

- **`jivo-ecom-pp-cli tables columns`** - Column definitions for a table
- **`jivo-ecom-pp-cli tables count`** - Row count for a single table
- **`jivo-ecom-pp-cli tables counts`** - Row counts for every available data table
- **`jivo-ecom-pp-cli tables data`** - Paginated rows for a table (server-shaped payload)
- **`jivo-ecom-pp-cli tables distinct`** - Distinct values for a column in a table

### upload

Read-only views of uploaded reference data

- **`jivo-ecom-pp-cli upload ads-master`** - Ads master sheet (columns, rows)
- **`jivo-ecom-pp-cli upload master-sheet`** - Master sheet
- **`jivo-ecom-pp-cli upload pincode-mapping`** - Pincode mapping table

### uploads

Upload job history (read-only)

- **`jivo-ecom-pp-cli uploads get`** - Get an upload job (summary, errors, diagnostics) by id
- **`jivo-ecom-pp-cli uploads list`** - List upload jobs


## Output Formats

```bash
# Human-readable table (default in terminal, JSON when piped)
jivo-ecom-pp-cli notifications list

# JSON for scripting and agents
jivo-ecom-pp-cli notifications list --json

# Filter to specific fields
jivo-ecom-pp-cli notifications list --json --select id,name,status

# Dry run — show the request without sending
jivo-ecom-pp-cli notifications list --dry-run

# Agent mode — JSON + compact + no prompts in one flag
jivo-ecom-pp-cli notifications list --agent
```

## Agent Usage

This CLI is designed for AI agent consumption:

- **Non-interactive** - never prompts, every input is a flag
- **Pipeable** - `--json` output to stdout, errors to stderr
- **Filterable** - `--select id,name` returns only fields you need
- **Previewable** - `--dry-run` shows the request without sending
- **Read-only by default** - this CLI does not create, update, delete, publish, send, or mutate remote resources
- **Offline-friendly** - sync/search commands can use the local SQLite store when available
- **Agent-safe by default** - no colors or formatting unless `--human-friendly` is set

Exit codes: `0` success, `2` usage error, `3` not found, `4` auth error, `5` API error, `7` rate limited, `10` config error.

## Health Check

```bash
jivo-ecom-pp-cli doctor
```

Verifies configuration, credentials, and connectivity to the API.

## Configuration

Config file: `~/.config/jivo-ecom-pp-cli/config.toml`

Static request headers can be configured under `headers`; per-command header overrides take precedence.

Environment variables:

| Name | Kind | Required | Description |
| --- | --- | --- | --- |
| `JIVO_ECOM_TOKEN` | per_call | Yes | Set to your API credential. |

### agentcookie (optional)

If you use agentcookie to sync secrets across machines, this CLI auto-adopts agentcookie-managed credentials with no extra setup. When the daemon writes to this CLI's config, `jivo-ecom-pp-cli doctor` reports `agentcookie: detected` and `auth-status` labels the source as `agentcookie`. Skip this section if you don't use agentcookie - the CLI works the same as any other.

## Troubleshooting
**Authentication errors (exit code 4)**
- Run `jivo-ecom-pp-cli doctor` to check credentials
- Verify the environment variable is set: `echo $JIVO_ECOM_TOKEN`
**Not found errors (exit code 3)**
- Check the resource ID is correct
- Run the `list` command to see available items

---

Generated by [CLI Printing Press](https://github.com/mvanhorn/cli-printing-press)

Linked: [[CLI/ecom-cli/.printing-press-patches/README|Ecom patch ledger]] · [[CLI/ecom-cli/AGENTS|Agent guide]] · [[CLI/ecom-cli/OPERATOR-GUIDE|Operator guide]] · [[CLI/ecom-cli/SETUP|Setup]] · [[CLI/ecom-cli/SKILL|Agent skill]] · [[CLI/ecom-cli/CHANGELOG|Changelog]] · [[docs/ecom/ECOM_MAP|ECOM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
