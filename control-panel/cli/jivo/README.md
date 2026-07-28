# Jivo CLI

Jivo Group — Control Panel: strictly READ-ONLY CLI over the internal Django ERP/analytics dashboard for JIVO Wellness (sales realise, targets, order-in-hand, receivables aging, master data, inventory & production). Live production system — read/pull endpoints only.

Created by [@daman8271](https://github.com/daman8271).

## Install

The recommended path installs both the `jivo-pp-cli` binary and the `pp-jivo` agent skill (Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, and other agents supported by the upstream [`skills`](https://github.com/vercel-labs/skills) CLI) in one shot:

```bash
npx -y @mvanhorn/printing-press-library install jivo
```

For CLI only (no skill):

```bash
npx -y @mvanhorn/printing-press-library install jivo --cli-only
```

For skill only — installs the skill into the same agents as the default command above, but skips the CLI binary (use this to update or reinstall just the skill):

```bash
npx -y @mvanhorn/printing-press-library install jivo --skill-only
```

To constrain the skill install to one or more specific agents (repeatable — agent names match the [`skills`](https://github.com/vercel-labs/skills) CLI):

```bash
npx -y @mvanhorn/printing-press-library install jivo --agent claude-code
npx -y @mvanhorn/printing-press-library install jivo --agent claude-code --agent codex
```

### Without Node (Go fallback)

If `npx` isn't available (no Node, offline), install the CLI directly via Go (requires Go 1.26.4 or newer):

```bash
go install github.com/mvanhorn/printing-press-library/library/sales-and-crm/jivo/cmd/jivo-pp-cli@latest
```

This installs the CLI only — no skill.

### Pre-built binary

Download a pre-built binary for your platform from the [latest release](https://github.com/mvanhorn/printing-press-library/releases/tag/jivo-current). On macOS, clear the Gatekeeper quarantine: `xattr -d com.apple.quarantine <binary>`. On Unix, mark it executable: `chmod +x <binary>`.

<!-- pp-hermes-install-anchor -->
## Install for Hermes

Install the CLI binary first. The installer writes binaries to a per-user managed bin directory by default: `$HOME/.local/bin` on macOS/Linux and `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows.

```bash
npx -y @mvanhorn/printing-press-library install jivo --cli-only
```

Then install the focused Hermes skill.

From the Hermes CLI:

```bash
hermes skills install mvanhorn/printing-press-library/cli-skills/pp-jivo --force
```

Inside a Hermes chat session:

```bash
/skills install mvanhorn/printing-press-library/cli-skills/pp-jivo --force
```

Restart the Hermes session or gateway if the newly installed skill is not visible immediately.

## Install for OpenClaw
Install both the CLI binary and the focused OpenClaw skill. The installer defaults binaries to a per-user bin directory (`$HOME/.local/bin` on macOS/Linux, `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows):

```bash
npx -y @mvanhorn/printing-press-library install jivo --agent openclaw
```

Restart the OpenClaw session or gateway if the newly installed skill is not visible immediately.

## Use with Claude Desktop

This CLI ships an [MCPB](https://github.com/modelcontextprotocol/mcpb) bundle — Claude Desktop's standard format for one-click MCP extension installs (no JSON config required).

To install:

1. Download the `.mcpb` for your platform from the [latest release](https://github.com/mvanhorn/printing-press-library/releases/tag/jivo-current).
2. Double-click the `.mcpb` file. Claude Desktop opens and walks you through the install.

Requires Claude Desktop 1.0.0 or later. Pre-built bundles ship for macOS Apple Silicon (`darwin-arm64`) and Windows (`amd64`, `arm64`); for other platforms, use the manual config below.

<details>
<summary>Manual JSON config (advanced)</summary>

If you can't use the MCPB bundle (older Claude Desktop, unsupported platform), install the MCP binary and configure it manually.


```bash
go install github.com/mvanhorn/printing-press-library/library/sales-and-crm/jivo/cmd/jivo-pp-mcp@latest
```

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "jivo": {
      "command": "jivo-pp-mcp"
    }
  }
}
```

</details>

## Quick Start

### 1. Install

See [Install](#install) above.

### 2. Verify Setup

```bash
jivo-pp-cli doctor
```

This checks your configuration.

### 3. Try Your First Command

```bash
jivo-pp-cli targets list
```

## Usage

Run `jivo-pp-cli --help` for the full command reference and flag list.

## Commands

### accounts

Accounts receivable — customer aging (oil AR flat, mart & beverages pre-bucketed), on-account payments, and the claim register.

- **`jivo-pp-cli accounts aging-beverages`** - Beverages A/R aging as a pre-bucketed pivot (grouped by salesperson) with KPIs and totals.
- **`jivo-pp-cli accounts aging-mart`** - Mart A/R aging as a pre-bucketed pivot by Format with book KPIs and totals.
- **`jivo-pp-cli accounts aging-oil`** - Oil company open A/R ledger as a flat per-open-invoice list (aged to as_of).
- **`jivo-pp-cli accounts claims`** - Full claim register (hand-maintained customer claims) plus the customer master picklist.
- **`jivo-pp-cli accounts open-payments`** - Customer payments on account (receipts not yet applied to invoices) for a date range.

### credit

Required Credit Limit page — no JSON API; data is embedded in the page HTML. Read-only GET of the page, parsing the embedded JSON.

- **`jivo-pp-cli credit`** - Required credit limits per ASM (Total Outstanding + 2%), lock state, as-of date — read from the page's embedded JSON.

### inventory

Inventory & production — live on-hand stock, non-moving/ageing stock, production feasibility & catalogues, daily work orders, and Wellness-Mart reconciliation.

- **`jivo-pp-cli inventory daily-production`** - Standard work-order (OWOR) production transactions for a date range — planned vs completed, warehouse, status, user.
- **`jivo-pp-cli inventory non-moving`** - Every in-stock finished good with ageing / movement signals (DaysInStock, DaysSinceMoved, last customer, qty/litres/value).
- **`jivo-pp-cli inventory non-moving-drill`** - Per-warehouse breakdown of a single finished good (code, name, qty, lot production date).
- **`jivo-pp-cli inventory production-feasibility`** - Read-only feasibility check for one FG at a requested qty: max producible count + per-component sufficiency (no production occurs).
- **`jivo-pp-cli inventory production-fg-list`** - Catalogue of manufacturable finished goods (those with a BOM) for the production-plan picker.
- **`jivo-pp-cli inventory production-warehouses`** - Full warehouse master (code + name) for the 'Stock from' selector.
- **`jivo-pp-cli inventory reconciliation`** - Wellness-Mart inter-company billing chains (PO -> SO -> GRPO -> A/P -> A/R) classified MATCHED/MISMATCH/INCOMPLETE.
- **`jivo-pp-cli inventory reconciliation-ledgers`** - BP ledgers behind the Wellness-Mart reconciliation, pivoted by document-type origin for each side (Mart vs Wellness).
- **`jivo-pp-cli inventory stock`** - Live finished-goods on-hand stock for one company: type summaries + per-SKU x per-warehouse rows.

### masterdata

Reference master data — customer master, saved realise-calculator rate lists, and the FG item master.

- **`jivo-pp-cli masterdata calculator-items`** - SAP finished-goods item master for the realise-calculator picker (code, name, variety, sku, pcs/box, box litres).
- **`jivo-pp-cli masterdata customer-master`** - Entire customer master (contact, tax, address, terms, credit limit, balance, status) in one payload. code is the join key.
- **`jivo-pp-cli masterdata rate-list`** - Saved realise-calculator results (rate lists). Pass --id to fetch a single saved result.

### oih

Order In Hand (open, uninvoiced sales orders) — line breakdown, per-person totals, and open-quantity rows.

- **`jivo-pp-cli oih breakdown`** - Line-level OIH breakdown, one row per open SO line, split premium vs commodity value and pieces.
- **`jivo-pp-cli oih commodity-rows`** - OIH open-order rows filtered to commodity oils (u_type=COMMODITY).
- **`jivo-pp-cli oih rows`** - OIH as individual open-order rows (open litres per item/customer).
- **`jivo-pp-cli oih summary`** - Total OIH value summarised per salesperson.

### sales

Sales realise dashboard feeds — per-product realise, credit notes, hidden sales, document flow, dispatch, drill-downs and beverages (all read-only; POST reads sample the smallest date range).

- **`jivo-pp-cli sales beverages`** - BEVERAGES dataset feed: beverage sales lines, day-over-day box comparison, customer grading, month rollup and beverage OIH.
- **`jivo-pp-cli sales beverages-docs`** - Documents (invoices / SOs) behind a beverages node — lazily fetched per drilled node.
- **`jivo-pp-cli sales channel-docs`** - Documents behind a Slide-2 channel card cell — invoices (done) or open SOs (oih), with per-line items and per-warehouse stock.
- **`jivo-pp-cli sales cn`** - Line-level gross sales vs credit-note rows for one company (oil|beverages) over a date range.
- **`jivo-pp-cli sales compare-docs`** - Invoice-level drill-down behind a Compare-Sales pivot cell (one month range plus optional dimension filters).
- **`jivo-pp-cli sales data`** - Core OILS realise feed: per-product litres/₹/realise/target rows plus flattened channel + month line-item rows for a date range.
- **`jivo-pp-cli sales dispatch`** - Per-invoice physical dispatch / freight metadata (bilty, transporter, vehicle, driver) for a date range.
- **`jivo-pp-cli sales drill-down`** - Expand one Slide-1 product row into a chosen dimension (litres + linetotal per value). drill_by is case-sensitive (State|U_Main_Group|U_Chain|ItemName|CardName).
- **`jivo-pp-cli sales flow`** - Sales document chains (Quotation -> Order -> Invoice) with open/closed status and source, for a date range and company.
- **`jivo-pp-cli sales flow-open-items`** - Drill-down: still-open line items of a single open Sales Order or Quotation.
- **`jivo-pp-cli sales hidden`** - Hidden sales-invoice lines (SAP U_ARNO='H') over a date range — oil company only.
- **`jivo-pp-cli sales historical`** - Trailing-period average realise (₹/L) per product and per drilled dimension, as a Slide-1 overlay.
- **`jivo-pp-cli sales pulse`** - Cheap change-fingerprint / heartbeat for the Realise backend (empty pulse = no signal). Detect change, not data.

### targets

Monthly target layer — product, flex (per-salesperson), segment, node (main-group x state x person x segment) and per-channel target litres/rates.

- **`jivo-pp-cli targets channel`** - Monthly target litres per sales channel (main group).
- **`jivo-pp-cli targets flex`** - Flex (flat, dimension-scoped) litre targets — currently per salesperson — for the target month.
- **`jivo-pp-cli targets list`** - Product-level monthly targets (tgt_ltrs, tgt_rate, source) keyed by U_TYPE|SUB_GROUP.
- **`jivo-pp-cli targets nodes`** - Granular target nodes: target litres by main_group x state x sales_person x segment for a month.
- **`jivo-pp-cli targets segment`** - Saved target overrides scoped to a single segment (empty {} when no overrides saved).

### users

User Management (Admin) page — no JSON API; data is embedded in the page HTML. Read-only GET of the page, parsing the embedded JSON. No write endpoints (users/save, users/delete, verify-pin) are exposed.

- **`jivo-pp-cli users catalog`** - Permission-module catalog used by the Users page — read-only, from the page's embedded JSON.
- **`jivo-pp-cli users list`** - Admin user list + roles/permission groups — read-only, from the page's embedded JSON.


## Output Formats

```bash
# Human-readable table (default in terminal, JSON when piped)
jivo-pp-cli targets list

# JSON for scripting and agents
jivo-pp-cli targets list --json

# Filter to specific fields
jivo-pp-cli targets list --json --select id,name,status

# Dry run — show the request without sending
jivo-pp-cli targets list --dry-run

# Agent mode — JSON + compact + no prompts in one flag
jivo-pp-cli targets list --agent
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

Exit codes: `0` success, `2` usage error, `3` not found, `5` API error, `7` rate limited, `10` config error.

## Health Check

```bash
jivo-pp-cli doctor
```

Verifies configuration and connectivity to the API.

## Configuration

Config file: `~/.config/jivo/config.toml`

Static request headers can be configured under `headers`; per-command header overrides take precedence.

## Troubleshooting
**Not found errors (exit code 3)**
- Check the resource ID is correct
- Run the `list` command to see available items

---

Generated by [CLI Printing Press](https://github.com/mvanhorn/cli-printing-press)
