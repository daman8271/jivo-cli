---
title: "Exim CLI"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, exim, cli]
---

# Exim CLI

JIVO EXIM read-only surface. Write and sync-import endpoints are excluded.

Created by [@daman8271](https://github.com/daman8271).

## Install

The recommended path installs both the `exim-pp-cli` binary and the `pp-exim` agent skill (Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, and other agents supported by the upstream [`skills`](https://github.com/vercel-labs/skills) CLI) in one shot:

```bash
npx -y @mvanhorn/printing-press-library install exim
```

For CLI only (no skill):

```bash
npx -y @mvanhorn/printing-press-library install exim --cli-only
```

For skill only — installs the skill into the same agents as the default command above, but skips the CLI binary (use this to update or reinstall just the skill):

```bash
npx -y @mvanhorn/printing-press-library install exim --skill-only
```

To constrain the skill install to one or more specific agents (repeatable — agent names match the [`skills`](https://github.com/vercel-labs/skills) CLI):

```bash
npx -y @mvanhorn/printing-press-library install exim --agent claude-code
npx -y @mvanhorn/printing-press-library install exim --agent claude-code --agent codex
```

### Without Node

The generated install path is category-agnostic until this CLI is published. If `npx` is not available before publish, install Node or use the category-specific Go fallback from the public-library entry after publish.

### Pre-built binary

Download a pre-built binary for your platform from the [latest release](https://github.com/mvanhorn/printing-press-library/releases/tag/exim-current). On macOS, clear the Gatekeeper quarantine: `xattr -d com.apple.quarantine <binary>`. On Unix, mark it executable: `chmod +x <binary>`.

<!-- pp-hermes-install-anchor -->
## Install for Hermes

Install the CLI binary first. The installer writes binaries to a per-user managed bin directory by default: `$HOME/.local/bin` on macOS/Linux and `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows.

```bash
npx -y @mvanhorn/printing-press-library install exim --cli-only
```

Then install the focused Hermes skill.

From the Hermes CLI:

```bash
hermes skills install mvanhorn/printing-press-library/cli-skills/pp-exim --force
```

Inside a Hermes chat session:

```bash
/skills install mvanhorn/printing-press-library/cli-skills/pp-exim --force
```

Restart the Hermes session or gateway if the newly installed skill is not visible immediately.

## Install for OpenClaw
Install both the CLI binary and the focused OpenClaw skill. The installer defaults binaries to a per-user bin directory (`$HOME/.local/bin` on macOS/Linux, `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows):

```bash
npx -y @mvanhorn/printing-press-library install exim --agent openclaw
```

Restart the OpenClaw session or gateway if the newly installed skill is not visible immediately.

## Use with Claude Desktop

This CLI ships an [MCPB](https://github.com/modelcontextprotocol/mcpb) bundle — Claude Desktop's standard format for one-click MCP extension installs (no JSON config required).

To install:

1. Download the `.mcpb` for your platform from the [latest release](https://github.com/mvanhorn/printing-press-library/releases/tag/exim-current).
2. Double-click the `.mcpb` file. Claude Desktop opens and walks you through the install.
3. Fill in `EXIM_TOKEN` when Claude Desktop prompts you.

Requires Claude Desktop 1.0.0 or later. Pre-built bundles ship for macOS Apple Silicon (`darwin-arm64`) and Windows (`amd64`, `arm64`); for other platforms, use the manual config below.

<details>
<summary>Manual JSON config (advanced)</summary>

If you can't use the MCPB bundle (older Claude Desktop, unsupported platform), install the MCP binary and configure it manually.


Install the MCP binary from this CLI's published public-library entry or pre-built release.

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "exim": {
      "command": "exim-pp-mcp",
      "env": {
        "EXIM_TOKEN": "<your-key>"
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
exim-pp-cli auth set-token YOUR_TOKEN_HERE
```

Or set it via environment variable:

```bash
export EXIM_TOKEN="your-token-here"
```

### 3. Verify Setup

```bash
exim-pp-cli doctor
```

This checks your configuration and credentials.

### 4. Try Your First Command

```bash
exim-pp-cli dc get --year example-value
```

## Usage

Run `exim-pp-cli --help` for the full command reference and flag list.

## Commands

### account

Manage account

- **`exim-pp-cli account get-user-id`** - Single user detail.
- **`exim-pp-cli account get-users`** - List of application user accounts (id, name, email).

### daily-price

Manage daily price

- **`exim-pp-cli daily-price get-db-list`** - Historical daily commodity factory-price records (optionally for a date).
- **`exim-pp-cli daily-price get-highest-lowest`** - Highest & lowest commodity prices over a date range.
- **`exim-pp-cli daily-price get-range`** - Daily prices over a from/to range.
- **`exim-pp-cli daily-price get-trends`** - Daily-price trend series (labels + datasets) for charting over a range.

### dc

Manage dc

- **`exim-pp-cli dc get`** - Domestic contracts by FY (re-listed).
- **`exim-pp-cli dc get-dropdown`** - Open-PO dropdown for domestic-contract creation.

### director-inventorty

Manage director inventorty

- **`exim-pp-cli director-inventorty`** - Director rollup: finished + at-factory + in-transit inventory by litre/MT.

### exim-rates

Manage exim rates

- **`exim-pp-cli exim-rates`** - Fetch/refresh custom exchange (EXIM) rates.

### item

Manage item

- **`exim-pp-cli item get-fg-code`** - Single finished-good item detail.
- **`exim-pp-cli item get-rm-code`** - Single raw-material item detail incl movement totals.

### items

Manage items

- **`exim-pp-cli items get-fg`** - Finished-goods item master (SAP-synced).
- **`exim-pp-cli items get-rm`** - Raw-material item master (SAP-synced).
- **`exim-pp-cli items get-rm-summary`** - Aggregate summary of raw-material items (counts, qty, value).
- **`exim-pp-cli items get-rm-varieties`** - Distinct raw-material varieties.

### jivo-rate

Manage jivo rate

- **`exim-pp-cli jivo-rate`** - JIVO pack rates over a range.

### license

Manage license

- **`exim-pp-cli license get-advance-export-lines`** - Advance-license export (shipping bill) lines.
- **`exim-pp-cli license get-advance-headers`** - Advance Authorisation licenses with nested import/export lines.
- **`exim-pp-cli license get-advance-import-lines`** - Advance-license import (BOE) lines.
- **`exim-pp-cli license get-advance-import-lines-dropdown`** - Import-line dropdown for a license.
- **`exim-pp-cli license get-dfia-export-lines-dropdown`** - DFIA export-line dropdown for a license file.
- **`exim-pp-cli license get-dfia-header-list`** - DFIA license headers list.

### parties

Manage parties

- **`exim-pp-cli parties`** - Business partners (vendors + customers) master from SAP.

### party

Manage party

- **`exim-pp-cli party <card_code>`** - Single business-partner detail.

### rates

Manage rates

- **`exim-pp-cli rates get-basic`** - Basic (our) rate rows over a date range.
- **`exim-pp-cli rates get-commodity`** - Commodity master with margin rates.
- **`exim-pp-cli rates get-market-get`** - Market rate rows over a date range.
- **`exim-pp-cli rates get-market-latest`** - Latest market rate per commodity.
- **`exim-pp-cli rates get-packing`** - Packing types with packing margins.
- **`exim-pp-cli rates get-table-latest`** - Composite latest rate table (commodities + rows).

### sap-sync

Manage sap sync

- **`exim-pp-cli sap-sync get-balance-sheet`** - Oil Dr/Cr outstanding balance sheet (SAP).
- **`exim-pp-cli sap-sync get-custa-balance-sheet`** - Customer (custa) outstanding balance sheet (SAP).
- **`exim-pp-cli sap-sync get-customer-aging-balance`** - Customer aging balances (SAP).
- **`exim-pp-cli sap-sync get-customer-balance`** - Customer outstanding balance over a date range (SAP).
- **`exim-pp-cli sap-sync get-customer-ledger`** - Customer ledger entries for one party (SAP).
- **`exim-pp-cli sap-sync get-finished-inventory`** - Finished-goods inventory (SAP).
- **`exim-pp-cli sap-sync get-inventory`** - Raw/factory inventory (SAP).
- **`exim-pp-cli sap-sync get-monthly-planning`** - Monthly SAP planning rows for a given month id.
- **`exim-pp-cli sap-sync get-open-ap`** - Open accounts-payable documents (SAP).
- **`exim-pp-cli sap-sync get-open-ar`** - Open accounts-receivable documents (SAP).
- **`exim-pp-cli sap-sync get-open-pos`** - Open purchase orders (SAP).
- **`exim-pp-cli sap-sync get-planned-months`** - Available planning months (SAP).
- **`exim-pp-cli sap-sync get-vendor-balance-sheet`** - Vendor outstanding balance sheet (SAP).
- **`exim-pp-cli sap-sync get-vendor-ledger`** - Vendor ledger entries for one party (SAP).

### stock-status

Manage stock status

- **`exim-pp-cli stock-status get`** - Core import stock-status rows (optionally filtered by status).
- **`exim-pp-cli stock-status get-contractual-history`** - Contractual history of stock items (rates, contract dates).
- **`exim-pp-cli stock-status get-debit-entries`** - Shortage/debit deduction entries per vehicle/item.
- **`exim-pp-cli stock-status get-debit-insights`** - Aggregate shortage/debit totals.
- **`exim-pp-cli stock-status get-id`** - Single stock-status record detail.
- **`exim-pp-cli stock-status get-stock-dashboard`** - Multi-dimensional stock dashboard (in/outside factory, by status/vendor).
- **`exim-pp-cli stock-status get-stock-insights`** - Aggregate stock KPIs (value, qty, avg price).
- **`exim-pp-cli stock-status get-stock-logs`** - Field-level audit log of stock-status changes.
- **`exim-pp-cli stock-status get-stock-summary`** - Aggregate stock summary KPIs (value, qty, avg price).
- **`exim-pp-cli stock-status get-vehicle-report`** - Vehicle-wise stock grouped by a status.

### sync-logs

Manage sync logs

- **`exim-pp-cli sync-logs`** - History of SAP sync jobs (type, status, counts).

### tank

Manage tank

- **`exim-pp-cli tank get`** - Storage tanks (code, item, capacity, current fill).
- **`exim-pp-cli tank get-capacity-insights`** - Overall tank capacity fill/empty percentages.
- **`exim-pp-cli tank get-code`** - Single tank detail.
- **`exim-pp-cli tank get-in-items`** - Distinct item codes currently in tanks.
- **`exim-pp-cli tank get-item-wise-average`** - Weighted average rate + matched qty for one tank item.
- **`exim-pp-cli tank get-item-wise-summary`** - Per-item tank summary (qty, capacity, tank list).
- **`exim-pp-cli tank get-items`** - Tank item master (code, name, category, colour).
- **`exim-pp-cli tank get-log`** - Tank inflow/outflow log entries.
- **`exim-pp-cli tank get-summary`** - Tank totals (capacity, current stock, utilisation).


## Output Formats

```bash
# Human-readable table (default in terminal, JSON when piped)
exim-pp-cli dc get --year example-value

# JSON for scripting and agents
exim-pp-cli dc get --year example-value --json

# Filter to specific fields
exim-pp-cli dc get --year example-value --json --select id,name,status

# Dry run — show the request without sending
exim-pp-cli dc get --year example-value --dry-run

# Agent mode — JSON + compact + no prompts in one flag
exim-pp-cli dc get --year example-value --agent
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
exim-pp-cli doctor
```

Verifies configuration, credentials, and connectivity to the API.

## Configuration

Config file: `~/.config/jivo-exim-pp-cli/config.toml`

Static request headers can be configured under `headers`; per-command header overrides take precedence.

Environment variables:

| Name | Kind | Required | Description |
| --- | --- | --- | --- |
| `EXIM_TOKEN` | per_call | Yes | Set to your API credential. |

### agentcookie (optional)

If you use agentcookie to sync secrets across machines, this CLI auto-adopts agentcookie-managed credentials with no extra setup. When the daemon writes to this CLI's config, `exim-pp-cli doctor` reports `agentcookie: detected` and `auth-status` labels the source as `agentcookie`. Skip this section if you don't use agentcookie - the CLI works the same as any other.

## Troubleshooting
**Authentication errors (exit code 4)**
- Run `exim-pp-cli doctor` to check credentials
- Verify the environment variable is set: `echo $EXIM_TOKEN`
**Not found errors (exit code 3)**
- Check the resource ID is correct
- Run the `list` command to see available items

---

Generated by [CLI Printing Press](https://github.com/mvanhorn/cli-printing-press)

Linked: [[CLI/exim/cli/exim-pp-cli/.printing-press-patches/README|EXIM patch ledger]] · [[CLI/exim/cli/exim-pp-cli/AGENTS|Agent guide]] · [[CLI/exim/cli/exim-pp-cli/SKILL|Agent skill]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[CLI/exim/HARD-RULE|HARD-RULE]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
