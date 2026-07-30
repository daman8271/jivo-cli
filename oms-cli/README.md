---
title: "Oms CLI"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, oms-cli, cli]
---

# Oms CLI

JIVO OMS (Order Management System) CLI — READ-ONLY. Orders, quotations, schemes, approvals, party & product assignments, SAP Business One sync, SAP HANA live stock, invoices/SKU, and the invoice tracker at oms.jivo.in. Every command is a GET; no mutating endpoint is wrapped.

Created by [@daman8271](https://github.com/daman8271).

## Install

The recommended path installs both the `oms-pp-cli` binary and the `pp-oms` agent skill (Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, and other agents supported by the upstream [`skills`](https://github.com/vercel-labs/skills) CLI) in one shot:

```bash
npx -y @mvanhorn/printing-press-library install oms
```

For CLI only (no skill):

```bash
npx -y @mvanhorn/printing-press-library install oms --cli-only
```

For skill only — installs the skill into the same agents as the default command above, but skips the CLI binary (use this to update or reinstall just the skill):

```bash
npx -y @mvanhorn/printing-press-library install oms --skill-only
```

To constrain the skill install to one or more specific agents (repeatable — agent names match the [`skills`](https://github.com/vercel-labs/skills) CLI):

```bash
npx -y @mvanhorn/printing-press-library install oms --agent claude-code
npx -y @mvanhorn/printing-press-library install oms --agent claude-code --agent codex
```

### Without Node

The generated install path is category-agnostic until this CLI is published. If `npx` is not available before publish, install Node or use the category-specific Go fallback from the public-library entry after publish.

### Pre-built binary

Download a pre-built binary for your platform from the [latest release](https://github.com/mvanhorn/printing-press-library/releases/tag/oms-current). On macOS, clear the Gatekeeper quarantine: `xattr -d com.apple.quarantine <binary>`. On Unix, mark it executable: `chmod +x <binary>`.

<!-- pp-hermes-install-anchor -->
## Install for Hermes

Install the CLI binary first. The installer writes binaries to a per-user managed bin directory by default: `$HOME/.local/bin` on macOS/Linux and `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows.

```bash
npx -y @mvanhorn/printing-press-library install oms --cli-only
```

Then install the focused Hermes skill.

From the Hermes CLI:

```bash
hermes skills install mvanhorn/printing-press-library/cli-skills/pp-oms --force
```

Inside a Hermes chat session:

```bash
/skills install mvanhorn/printing-press-library/cli-skills/pp-oms --force
```

Restart the Hermes session or gateway if the newly installed skill is not visible immediately.

## Install for OpenClaw
Install both the CLI binary and the focused OpenClaw skill. The installer defaults binaries to a per-user bin directory (`$HOME/.local/bin` on macOS/Linux, `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows):

```bash
npx -y @mvanhorn/printing-press-library install oms --agent openclaw
```

Restart the OpenClaw session or gateway if the newly installed skill is not visible immediately.

## Use with Claude Desktop

This CLI ships an [MCPB](https://github.com/modelcontextprotocol/mcpb) bundle — Claude Desktop's standard format for one-click MCP extension installs (no JSON config required).

To install:

1. Download the `.mcpb` for your platform from the [latest release](https://github.com/mvanhorn/printing-press-library/releases/tag/oms-current).
2. Double-click the `.mcpb` file. Claude Desktop opens and walks you through the install.
3. Fill in `OMS_TOKEN` when Claude Desktop prompts you.

Requires Claude Desktop 1.0.0 or later. Pre-built bundles ship for macOS Apple Silicon (`darwin-arm64`) and Windows (`amd64`, `arm64`); for other platforms, use the manual config below.

<details>
<summary>Manual JSON config (advanced)</summary>

If you can't use the MCPB bundle (older Claude Desktop, unsupported platform), install the MCP binary and configure it manually.


Install the MCP binary from this CLI's published public-library entry or pre-built release.

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "oms": {
      "command": "oms-pp-mcp",
      "env": {
        "OMS_TOKEN": "<your-key>"
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
oms-pp-cli auth set-token YOUR_TOKEN_HERE
```

Or set it via environment variable:

```bash
export OMS_TOKEN="your-token-here"
```

On Windows (PowerShell):

```powershell
$env:OMS_TOKEN = "your-token-here"
```

### 3. Verify Setup

```bash
oms-pp-cli doctor
```

This checks your configuration and credentials.

### 4. Try Your First Command

```bash
oms-pp-cli orders list
```

## Usage

Run `oms-pp-cli --help` for the full command reference and flag list.

## Commands

### account

Authenticated account, users, roles, and reference master data (companies, states, categories, main groups)

- **`oms-pp-cli account categories`** - List product categories (e.g. OIL)
- **`oms-pp-cli account companies`** - List companies (Jivo Mart, Jivo Wellness)
- **`oms-pp-cli account main-groups`** - List main groups (ROI, GT, MT, BRANCH, ...)
- **`oms-pp-cli account party-products`** - Products assigned to a party (argument is the SAP card_code, not a numeric id)
- **`oms-pp-cli account profile`** - Show the authenticated user (role, company, main groups, states, category, page permissions)
- **`oms-pp-cli account roles`** - List roles (admin, auditor, billing, rate approver, manager, etc.)
- **`oms-pp-cli account states`** - List states
- **`oms-pp-cli account user-page-permissions`** - Page-permission grants for a user
- **`oms-pp-cli account user-parties`** - Parties (customers) assigned to a user
- **`oms-pp-cli account users`** - List app users

### dashboard

Dashboard KPIs and chart series

- **`oms-pp-cli dashboard charts`** - Dashboard chart series (visual overview, statewise)
- **`oms-pp-cli dashboard summary`** - Dashboard KPI block (total orders, total sales, completion)

### hana

Live SAP HANA queries — product stock, sales orders, customers, and the order-creation wizard lookups

- **`oms-pp-cli hana address`** - Addresses for a customer. Requires --card-code.
- **`oms-pp-cli hana all-customers`** - All customers from SAP HANA
- **`oms-pp-cli hana batch-details`** - Batch details for an item in a warehouse. Requires --item-code and --whs-code.
- **`oms-pp-cli hana customer-details`** - Customer master detail. Requires --card-code.
- **`oms-pp-cli hana fg-items`** - Finished-goods items
- **`oms-pp-cli hana freight-masters`** - Freight master records
- **`oms-pp-cli hana inventory-details`** - Per-warehouse inventory for an item. Requires --item-code.
- **`oms-pp-cli hana item-price`** - Price for an item on a price list. Requires --item-code and --price-list.
- **`oms-pp-cli hana next-doc-number`** - Next document number for a document type. Requires --doc-type.
- **`oms-pp-cli hana open-parties`** - Parties with open transactions
- **`oms-pp-cli hana product-so`** - Product sales-order data
- **`oms-pp-cli hana product-stock`** - Live product stock from SAP HANA
- **`oms-pp-cli hana salesperson-details`** - Salesperson detail. Requires --slp-code.
- **`oms-pp-cli hana so`** - Sales orders

### invoices

Sales invoices, invoice review, and SKU master/image data

- **`oms-pp-cli invoices all`** - Invoice review queue (all invoices). Optionally filter by status.
- **`oms-pp-cli invoices history`** - Status-history timeline for an invoice
- **`oms-pp-cli invoices sku`** - Per-SKU detail
- **`oms-pp-cli invoices skus`** - All SKUs
- **`oms-pp-cli invoices skus-pending`** - SKUs pending review

### orders

Orders: list, detail, status lifecycle, tracking, dispatch, approval-flow config, and the party/product lookups the order screens use

- **`oms-pp-cli orders addresses`** - Bill-to / ship-to addresses for a party. Requires --card-code.
- **`oms-pp-cli orders branch`** - SAP branch / BPL list
- **`oms-pp-cli orders by-user`** - Orders raised by a specific user (source for View Orders / Order Tracking)
- **`oms-pp-cli orders detail`** - Full order with line items, addresses, rate approvals, SAP doc number
- **`oms-pp-cli orders dispatches`** - Dispatch-from locations
- **`oms-pp-cli orders flow-config`** - Global order approval-flow configuration
- **`oms-pp-cli orders list`** - All orders (admin-wide). Filter by status/stage.
- **`oms-pp-cli orders logs`** - Status-change audit trail for an order (drives the tracking timeline)
- **`oms-pp-cli orders notifications`** - Order-status notifications for the current user
- **`oms-pp-cli orders parties`** - Assigned-party dropdown (card_code -> card_name) for the current user
- **`oms-pp-cli orders party-flow-config`** - Per-party approval-flow configuration
- **`oms-pp-cli orders party-products`** - Products (with rates) assigned to a party, for the order product selector
- **`oms-pp-cli orders products`** - Global product list
- **`oms-pp-cli orders schemes`** - Sales schemes / promotions
- **`oms-pp-cli orders staff-products`** - Staff-assigned products
- **`oms-pp-cli orders status`** - Order status master (id -> name)
- **`oms-pp-cli orders status-tracking`** - Approval queue for a stage. Requires --mode.
- **`oms-pp-cli orders stock-check`** - Per-order required-qty vs available-stock (legacy view)

### quotations

Sales quotations and their SAP push status

- **`oms-pp-cli quotations overview`** - All quotations with SAP doc numbers and cancellation state
- **`oms-pp-cli quotations status`** - Open/closed SAP status badges for specific quotations

### sap

SAP Business One sync — history logs and synced master data (branches, parties, products)

- **`oms-pp-cli sap addresses`** - SAP addresses
- **`oms-pp-cli sap branches`** - SAP branches
- **`oms-pp-cli sap logs`** - SAP sync history (sync_type, status, records processed/created/updated, duration)
- **`oms-pp-cli sap parties`** - SAP parties (business partners)
- **`oms-pp-cli sap party-categories`** - SAP parties filtered by category
- **`oms-pp-cli sap product-varieties`** - SAP product varieties
- **`oms-pp-cli sap products`** - SAP products
- **`oms-pp-cli sap quotation-log`** - Per-order SAP quotation push record

### tracker

Invoice-tracker sub-app (access-gated: returns 403 for non-tracker roles). Read endpoints for a tracker-enabled account.

- **`oms-pp-cli tracker admin-lookups`** - Tracker admin: lookup set by type
- **`oms-pp-cli tracker admin-stages`** - Tracker admin: stage definitions
- **`oms-pp-cli tracker admin-tracker-users`** - Tracker admin: tracker-role users
- **`oms-pp-cli tracker admin-users`** - Tracker admin: users
- **`oms-pp-cli tracker alerts`** - Tracker alerts
- **`oms-pp-cli tracker all-invoices`** - All tracker invoices
- **`oms-pp-cli tracker all-invoices-export`** - Export of all tracker invoices
- **`oms-pp-cli tracker invoice-detail`** - Single tracker invoice
- **`oms-pp-cli tracker invoices`** - Tracker invoices
- **`oms-pp-cli tracker lookups`** - Tracker lookup reference data
- **`oms-pp-cli tracker my-queue`** - Current user's tracker work queue
- **`oms-pp-cli tracker reports`** - Tracker reports
- **`oms-pp-cli tracker stage-advanced`** - Advanced stage view
- **`oms-pp-cli tracker vendors`** - Tracker vendors


## Output Formats

```bash
# Human-readable table (default in terminal, JSON when piped)
oms-pp-cli orders list

# JSON for scripting and agents
oms-pp-cli orders list --json

# Filter to specific fields
oms-pp-cli orders list --json --select id,name,status

# Dry run — show the request without sending
oms-pp-cli orders list --dry-run

# Agent mode — JSON + compact + no prompts in one flag
oms-pp-cli orders list --agent
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
oms-pp-cli doctor
```

Verifies configuration, credentials, and connectivity to the API.

## Configuration

Config file: `~/.config/oms-pp-cli/config.toml`

Static request headers can be configured under `headers`; per-command header overrides take precedence.

Environment variables:

| Name | Kind | Required | Description |
| --- | --- | --- | --- |
| `OMS_TOKEN` | per_call | Yes | Set to your API credential. |

### agentcookie (optional)

If you use agentcookie to sync secrets across machines, this CLI auto-adopts agentcookie-managed credentials with no extra setup. When the daemon writes to this CLI's config, `oms-pp-cli doctor` reports `agentcookie: detected` and `auth-status` labels the source as `agentcookie`. Skip this section if you don't use agentcookie - the CLI works the same as any other.

## Troubleshooting
**Authentication errors (exit code 4)**
- Run `oms-pp-cli doctor` to check credentials
- Verify the environment variable is set: `echo $OMS_TOKEN`
**Not found errors (exit code 3)**
- Check the resource ID is correct
- Run the `list` command to see available items

## Regeneration Safety

This printed tree has deliberate local safeguards and live-API corrections. Before or after any regeneration, review [[CLI/oms-cli/.printing-press-patches/README|the OMS local patch ledger]] and re-apply every entry whose evidence still holds.

---

Generated by [CLI Printing Press](https://github.com/mvanhorn/cli-printing-press)

Linked: [[CLI/oms-cli/.printing-press-patches/README|OMS patch ledger]] · [[CLI/oms-cli/AGENTS|Agent guide]] · [[CLI/oms-cli/SKILL|Agent skill]] · [[docs/oms/OMS_MAP|OMS_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
