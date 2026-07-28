# sapb1 MCP server

`sapb1 mcp` runs a **read-only** [Model Context Protocol](https://modelcontextprotocol.io)
server over stdio (stdin/stdout JSON-RPC). Register it with an MCP client
(Claude Code, Claude Desktop, …) and an AI agent can query the SAP Business One
Service Layer as tools.

## Read-only guarantee

Every tool resolves to only these HTTP operations against the Service Layer:
`GET` (entity reads), `POST /Login`, and `POST /Logout` (session
establishment/teardown). There is **no tool, and no code path,** that issues
`POST`/`PUT`/`PATCH`/`DELETE` against business data. Read-only is asserted in
the tool metadata (`readOnlyHint: true`, `destructiveHint: false`) and enforced
in code — the server reuses `internal/client`, which only ever sends
`GET` + `Login`/`Logout`. The password is never returned in a tool result,
logged, or embedded in any error message.

## Build

```bash
cd /Users/damanpreetsingh/sapb1-cli
go build -o sapb1 ./cmd/sapb1
```

## Configuration

The MCP server resolves config exactly like the CLI: **`SAPB1_*` env vars > `.env` > built-in defaults**.
Because an MCP client launches the process with an arbitrary working directory,
the server **also** loads `.env` from the directory holding the `sapb1` binary,
so `~/sapb1-cli/.env` is picked up wherever it's launched from.

Two equally valid ways to supply credentials:

1. **`.env` next to the binary** (`~/sapb1-cli/.env`) — the file is already
   git-ignored. Simplest; nothing sensitive goes in the client config.
2. **`env` block in the MCP client config** (shown below) — handy if the binary
   lives elsewhere. Never commit a config file that contains a real password.

## Register with Claude Code

Add this to `~/.claude.json` under `mcpServers` (create the key if absent):

```json
{
  "mcpServers": {
    "sapb1": {
      "command": "/Users/damanpreetsingh/sapb1-cli/sapb1",
      "args": ["mcp"]
    }
  }
}
```

If you'd rather pass config through the client instead of `~/sapb1-cli/.env`,
add an `env` block (fill in your real values — do not commit this):

```json
{
  "mcpServers": {
    "sapb1": {
      "command": "/Users/damanpreetsingh/sapb1-cli/sapb1",
      "args": ["mcp"],
      "env": {
        "SAPB1_HOST": "your.sap.server.ip",
        "SAPB1_PORT": "50000",
        "SAPB1_COMPANYDB": "YOUR_COMPANY_DB",
        "SAPB1_USER": "manager",
        "SAPB1_PASSWORD": "your-password",
        "SAPB1_INSECURE": "true"
      }
    }
  }
}
```

Restart Claude Code (or reload MCP servers). The `sapb1_*` tools appear in the
tool list.

## Register with Claude Desktop

Edit `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Same shape as above:

```json
{
  "mcpServers": {
    "sapb1": {
      "command": "/Users/damanpreetsingh/sapb1-cli/sapb1",
      "args": ["mcp"]
    }
  }
}
```

Fully quit and reopen Claude Desktop so it picks up the new server.

## Tools

All tools are read-only. The catalog tools (`sapb1_entities`, `sapb1_ops`) work
fully **offline** — no VPN or login needed.

| Tool | Args | What it does |
|------|------|--------------|
| `sapb1_doctor`   | *(none)* | Checks config + TCP reachability + Login; returns a JSON status report (password masked). |
| `sapb1_query`    | `entity` (req), `select`, `filter`, `top` (def 20), `orderby` | Core tool: read-only OData GET against any entity set; returns rows as JSON. |
| `sapb1_entities` | `search`, `readOnly` | Lists services/entities from the embedded catalog (offline). |
| `sapb1_ops`      | `service` (req) | Lists the operations for one service from the catalog (offline). |
| `sapb1_fields`   | `entity` (req) | Live-discovers field names (`GET ?$top=1` keys); offline-fallback to catalog ops. |
| `sapb1_orders`   | `filter`, `top`, `open` | Sales orders (Orders), newest first. `open=true` → `DocStatus eq 'O'`. |
| `sapb1_invoices` | `filter`, `top`, `open` | A/R invoices (Invoices), newest first. `open=true` → `DocStatus eq 'O'`. |
| `sapb1_items`    | `filter`, `top`, `lowStock` | Items (Items). `lowStock=N` → `QuantityOnStock le N`. |
| `sapb1_partners` | `filter`, `top`, `customers`, `suppliers` | Business partners (BusinessPartners). `customers`/`suppliers` filter by `CardType`. |

## Example

Once registered, an agent can call `sapb1_query` for open sales orders:

```json
{
  "name": "sapb1_query",
  "arguments": {
    "entity": "Orders",
    "filter": "DocStatus eq 'O'",
    "select": "DocEntry,DocNum,CardName,DocTotal",
    "top": 25,
    "orderby": "DocDate desc"
  }
}
```

Or the convenience equivalent:

```json
{ "name": "sapb1_orders", "arguments": { "open": true, "top": 25 } }
```

Typical flow: **`sapb1_doctor`** (confirm connectivity) → **`sapb1_entities`** /
**`sapb1_fields`** (discover what to read) → **`sapb1_query`** (fetch the rows).

## Verify the server by hand

Pipe an `initialize` + `tools/list` into it and you'll get the tool list back:

```bash
printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | ./sapb1 mcp
```
