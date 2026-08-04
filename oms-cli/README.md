# Oms CLI

JIVO OMS (Order Management System) CLI — READ-ONLY. Orders, quotations, schemes, approvals, party & product assignments, the SAP Business One mirror, live SAP HANA stock and pricing, the invoice review queue, FSSAI label compliance, and the invoice tracker at oms.jivo.in. Every command is a GET; no mutating endpoint is wrapped. HANA commands require --branch (OIL or BEVERAGE) — it picks the SAP company database.

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

### Without Node (Go fallback)

If `npx` isn't available (no Node, offline), install the CLI directly via Go (requires Go 1.26.4 or newer):

```bash
go install github.com/mvanhorn/printing-press-library/library/developer-tools/oms/cmd/oms-pp-cli@latest
```

This installs the CLI only — no skill.

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


```bash
go install github.com/mvanhorn/printing-press-library/library/developer-tools/oms/cmd/oms-pp-mcp@latest
```

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

Authenticated account, users, roles, permissions and reference master data (companies, states, categories, main groups), plus the device registry and UI label config

- **`oms-pp-cli account categories`** - List product categories (e.g. OIL)
- **`oms-pp-cli account companies`** - List companies (Jivo Mart, Jivo Wellness)
- **`oms-pp-cli account device`** - Full record for one enrolled device — model, OS, app build, first and last login — for when you need to confirm exactly what a specific user was running.
- **`oms-pp-cli account device-analytics`** - One-screen rollout health for the OMS apps — how many devices are on each Android/iOS/web build, and how many have been seen recently. Use it to answer "has everyone updated?" before blaming the backend.
- **`oms-pp-cli account devices`** - The device registry — every browser and phone that has logged into OMS, who was on it, and when it was last seen. This is how you find out which app build a salesperson is actually running before you believe a bug report from the field.
- **`oms-pp-cli account main-groups`** - List main groups (ROI, GT, MT, BRANCH, ...)
- **`oms-pp-cli account my-devices`** - Push-notification devices registered to the calling user. Returns an empty list if you have never enrolled a browser or handset.
- **`oms-pp-cli account party-products`** - Products assigned to a party (argument is the SAP card_code, not a numeric id)
- **`oms-pp-cli account profile`** - Show the authenticated user (role, company, main groups, states, category, page permissions)
- **`oms-pp-cli account roles`** - List roles (admin, auditor, billing, rate approver, manager, etc.)
- **`oms-pp-cli account states`** - List states
- **`oms-pp-cli account ui-label-config`** - The editable definitions behind OMS's renameable field labels — the admin view, with the description and the active flag.
- **`oms-pp-cli account ui-labels`** - The resolved label map the app renders with — what the UI currently calls each renameable field. Useful when a user's screenshot says something your data dictionary doesn't.
- **`oms-pp-cli account user-page-permissions`** - Page-permission grants for a user
- **`oms-pp-cli account user-parties`** - Parties (customers) assigned to a user
- **`oms-pp-cli account users`** - List app users

### dashboard

Order dashboard widgets and charts

- **`oms-pp-cli dashboard charts`** - Dashboard chart series (visual overview, statewise)
- **`oms-pp-cli dashboard summary`** - Dashboard KPI block (total orders, total sales, completion)

### einvoice



- **`oms-pp-cli einvoice companies`** - The JIVO legal entities enrolled for GST e-invoicing, with their GSTINs.
- **`oms-pp-cli einvoice health`** - Whether the GST e-invoicing integration is up and authenticated.
- **`oms-pp-cli einvoice invoices`** - Invoices that have been through GST e-invoicing, with their IRN status.
- **`oms-pp-cli einvoice logs`** - IRN generation attempts and their outcomes — the place to look when an e-invoice fails.

### hana

Live SAP HANA reads. EVERY command needs --branch (OIL or BEVERAGE) - it selects the SAP company database and the answer is meaningless without it

- **`oms-pp-cli hana address`** - Addresses for a customer. Requires --card-code.
- **`oms-pp-cli hana all-customers`** - All customers from SAP HANA
- **`oms-pp-cli hana batch-details`** - Batch details for an item in a warehouse. Requires --item-code and --whs-code.
- **`oms-pp-cli hana customer-details`** - Customer master detail. Requires --card-code.
- **`oms-pp-cli hana fg-items`** - Finished-goods items
- **`oms-pp-cli hana freight-masters`** - Freight master records
- **`oms-pp-cli hana inventory-details`** - Per-warehouse inventory for an item. Requires --item-code.
- **`oms-pp-cli hana invoice-drafts`** - READ of the A/R invoice drafts sitting in SAP for a branch. This reads drafts; it never creates one.
- **`oms-pp-cli hana item-price`** - Price for an item on a price list. Requires --item-code and --price-list.
- **`oms-pp-cli hana next-doc-number`** - Next document number for a document type. Requires --doc-type.
- **`oms-pp-cli hana open-parties`** - Parties with open transactions
- **`oms-pp-cli hana product-so`** - BROKEN UPSTREAM (2026-08-04): the OMS backend raises "get_sales_orders_for_product() takes 1 positional argument but 2 were given" and returns HTTP 500 on every call. Reported to the OMS team. | Product sales-order data for an item. Requires --item-code.
- **`oms-pp-cli hana product-stock`** - BROKEN UPSTREAM (2026-08-04): the OMS backend raises "name 'unique_schemas' is not defined" and returns HTTP 502 on every call, for both branches. Reported to the OMS team. | Live product stock from SAP HANA
- **`oms-pp-cli hana salesperson-details`** - Salesperson detail. Requires --slp-code.
- **`oms-pp-cli hana series`** - SAP document numbering series for a branch — the series a document will draw its number from.
- **`oms-pp-cli hana so`** - Sales orders for a party. Requires --card-code.
- **`oms-pp-cli hana state-chain`** - The state-to-state routing chain used for freight and GST place-of-supply decisions.
- **`oms-pp-cli hana vendor-states`** - States JIVO's vendors operate in, per branch — used to work out interstate vs intrastate GST.
- **`oms-pp-cli hana warehouse-details`** - Warehouse master for a branch: codes, names and locations behind every WhsCode you see in stock and batch data.

### invoices

The invoice review-and-approval queue, credit limits and SKU master data

- **`oms-pp-cli invoices all`** - BROKEN UPSTREAM (2026-08-04): returns HTTP 400 "Warehouse Code is a required parameter" for every parameter name tried, and the OMS web app never calls this route. Use `invoices logs` instead. Reported to the OMS team. | Invoice review queue (all invoices). Optionally filter by status.
- **`oms-pp-cli invoices credit-limit-cards`** - The credit-limit master for every customer account in one SAP company — how much each party currently owes, the credit line they are allowed, and the debt line. This is what the reviewer looks at before releasing an invoice for a party who is close to their limit.
- **`oms-pp-cli invoices credit-limit-flow`** - The approval chain for a credit-limit override request raised against one invoice — which named approver sits at which stage, in what order, and whether they approved, rejected or have not acted.
- **`oms-pp-cli invoices crystal`** - The Crystal Reports print payload for one posted invoice, by SAP document number.
- **`oms-pp-cli invoices history`** - Status-history timeline for an invoice (BACKEND ROUTE MISSING — unregistered)
- **`oms-pp-cli invoices logs`** - The invoice review-and-approval queue. One row per invoice a salesperson has submitted out of a sales order, carrying the full SAP B1 document payload, the finished-goods stock position at the time of submission, and where it currently sits between "submitted" and "posted into SAP".
- **`oms-pp-cli invoices sku`** - Per-SKU detail
- **`oms-pp-cli invoices skus`** - All SKUs
- **`oms-pp-cli invoices skus-pending`** - BROKEN UPSTREAM (2026-08-04): the OMS backend raises "getFGItems() missing 1 required positional argument: 'branch'" and returns HTTP 500 on every call. Reported to the OMS team. | SKUs pending review

### legal

FSSAI food-label compliance: pack artwork checked against the statutory declarations for an item

- **`oms-pp-cli legal item-nutrition`** - The nutritional facts JIVO has declared for one product — the reference values an uploaded label is checked against.
- **`oms-pp-cli legal items`** - The food products whose pack labels are checked for FSSAI compliance. One row per product.
- **`oms-pp-cli legal nutrition`** - The master list of nutrition rows (the nutrient lines that can appear in a nutritional-information table).
- **`oms-pp-cli legal uoms`** - The units of measure used when declaring nutritional values on a label (g, kcal, mg …).

### orders

Sales orders, quotations, schemes, dispatches, approval flows and the order dashboard

- **`oms-pp-cli orders addresses`** - Bill-to / ship-to addresses for a party. Requires --card-code.
- **`oms-pp-cli orders branch`** - SAP branch / BPL list
- **`oms-pp-cli orders by-item`** - Every order line for one FG item — who ordered it, how much, and in what state.
- **`oms-pp-cli orders by-user`** - Orders raised by a specific user (source for View Orders / Order Tracking)
- **`oms-pp-cli orders dashboard`** - Order dashboard headline counters. Note this is a DIFFERENT endpoint from the shipped `orders dashboardW`, which the web app uses; both are live.
- **`oms-pp-cli orders dashboard-charts`** - Chart series behind the order dashboard. Large — 268 KB in one unpaginated response; use --compact or --csv.
- **`oms-pp-cli orders detail`** - Full order with line items, addresses, rate approvals, SAP doc number
- **`oms-pp-cli orders dispatches`** - Dispatch-from locations
- **`oms-pp-cli orders flow-config`** - Global order approval-flow configuration
- **`oms-pp-cli orders list`** - All orders (admin-wide). Filter by status/stage. TRAPS: bare `orders list` is NOT the order book - it returns one slice (263 of 2,163 orders). `status` accepts a comma-separated list and unions them. `billing=true` DISCARDS any `status` you also pass (proven: six query strings, byte-identical bodies). `approval_pending=true` alone is a no-op.
- **`oms-pp-cli orders logs`** - Status-change audit trail for an order (drives the tracking timeline)
- **`oms-pp-cli orders notifications`** - Order-status notifications for the current user
- **`oms-pp-cli orders notifications-history`** - The full notification feed for the current user, paged — including alerts already read, which the live `orders notifications` call drops.
- **`oms-pp-cli orders parties`** - Assigned-party dropdown (card_code -> card_name) for the current user
- **`oms-pp-cli orders party-flow-config`** - Per-party approval-flow configuration
- **`oms-pp-cli orders party-products`** - Products (with rates) assigned to a party, for the order product selector
- **`oms-pp-cli orders product-filters`** - The filter options (brand, variety, pack size) offered by the order product selector.
- **`oms-pp-cli orders products`** - Global product list
- **`oms-pp-cli orders schemes`** - Sales schemes / promotions
- **`oms-pp-cli orders schemes-manage`** - The full scheme table behind the scheme admin screen — each scheme joined to the SKU it applies to, its pack size, its state, and whether it is switched on.
- **`oms-pp-cli orders staff-products`** - Staff-assigned products
- **`oms-pp-cli orders status`** - Order status master (id -> name)
- **`oms-pp-cli orders status-tracking`** - Approval queue for a stage. Requires --mode.
- **`oms-pp-cli orders stock-check`** - Per-order required-qty vs available-stock (legacy view)
- **`oms-pp-cli orders template-orders`** - Previous orders for one party, offered as templates for a new order.
- **`oms-pp-cli orders template-parties`** - Parties available as an order template — the 'repeat a previous order' picker. Empty for a user with no assigned parties.
- **`oms-pp-cli orders web-push-key`** - The VAPID public key the browser needs to register for OMS push notifications. Infrastructure, not business data.

### quotations

Quotation overview and per-order quotation status

- **`oms-pp-cli quotations overview`** - All quotations with SAP doc numbers and cancellation state The SAP doc numbers here are real: sampled (doc_num, doc_entry) pairs resolve exactly to SAP OQUT quotations. Note doc_num is NOT unique across companies - the same number exists in Oil and Beverages, so always pair it with the branch.
- **`oms-pp-cli quotations status`** - Open/closed SAP status badges for specific quotations

### sap

The SAP Business One mirror inside OMS: synced parties, products, addresses, branches and sync logs. Covers all three SAP companies

- **`oms-pp-cli sap addresses`** - SAP addresses
- **`oms-pp-cli sap branches`** - SAP branches
- **`oms-pp-cli sap logs`** - SAP sync history (sync_type, status, records processed/created/updated, duration)
- **`oms-pp-cli sap parties`** - SAP parties (business partners)
- **`oms-pp-cli sap party-categories`** - SAP parties filtered by category
- **`oms-pp-cli sap product-varieties`** - SAP product varieties
- **`oms-pp-cli sap products`** - SAP products
- **`oms-pp-cli sap quotation-log`** - Per-order SAP quotation push record
- **`oms-pp-cli sap schedules`** - Configured SAP sync schedules. Read-only view; the toggle that enables one is a write and is not wrapped.
- **`oms-pp-cli sap sync-status`** - Current state of the SAP mirror sync: what ran, when, and whether it finished.

### tracker

The OMS invoice tracker: invoices moving through stages, queues, vendors, alerts and reports. Needs a tracker grant separate from your app role - a plain admin gets HTTP 403

- **`oms-pp-cli tracker admin-lookups`** - Tracker admin: lookup set by type
- **`oms-pp-cli tracker admin-stages`** - Tracker admin: stage definitions
- **`oms-pp-cli tracker admin-tracker-users`** - Tracker admin: tracker-role users
- **`oms-pp-cli tracker admin-users`** - Tracker admin: users
- **`oms-pp-cli tracker alerts`** - Tracker alerts
- **`oms-pp-cli tracker all-invoices`** - All tracker invoices
- **`oms-pp-cli tracker all-invoices-export`** - Export of all tracker invoices
- **`oms-pp-cli tracker invoice-detail`** - Single tracker invoice
- **`oms-pp-cli tracker invoice-jsap`** - Whether this tracker invoice has reached **JSAP** (JIVO's internal ops platform at `103.89.45.75:5001`, the system `jsap-cli` talks to) and what JSAP's approvers did with it — approved, rejected, or still sitting there. Answers "the invoice is stuck at JSAP Approval, has JSAP actually seen it?"
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

---

Generated by [CLI Printing Press](https://github.com/mvanhorn/cli-printing-press)
