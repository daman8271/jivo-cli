# sapb1 MCP server

`sapb1 mcp` runs a **read-only** [Model Context Protocol](https://modelcontextprotocol.io)
server over stdio (stdin/stdout JSON-RPC) by default, or over **streamable
HTTP** with `--transport http`. Register it with an MCP client (Claude Code,
Claude Desktop, …) and an AI agent can query the SAP Business One Service
Layer as tools. Both transports expose the identical read-only tool set.

## Read-only guarantee

Every tool resolves to only these HTTP operations against the Service Layer:
`GET` (entity reads), `POST /Login`, and `POST /Logout` (session
establishment/teardown). There is **no tool** that issues `POST`/`PATCH` against
business data. Read-only is asserted in the tool metadata (`readOnlyHint: true`,
`destructiveHint: false`). The password is never returned in a tool result,
logged, or embedded in any error message.

**The CLI can write; the MCP surface deliberately cannot.** `sapb1` itself has
three operator-invoked write commands (`draft`, `post`, `patch`) — see the
"Writing to SAP" section of [README.md](README.md) — and `internal/client`
therefore carries `Create`/`Update`. None of that is wired to a tool, on
purpose: a write needs a human reading a preview and typing `yes`, which is
exactly what an agent transport can't provide. So the whole write path stays out
of the MCP server, and an agent that wants a document created has to ask the
operator to run `sapb1 draft …` themselves.

That boundary is a test, not a promise: `TestRegisteredToolsAreReadOnly`
(`internal/mcp/server_test.go`) walks every registered tool and fails if any of
them lacks `readOnlyHint: true`, is marked destructive, or if the tool set
changes at all without the expected list being updated. Adding a write tool
breaks the build.

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

## HTTP transport (streamable HTTP)

Instead of letting the client spawn the process over stdio, you can run the
server yourself and point clients at it over HTTP:

```bash
sapb1 mcp --transport http                      # serves http://127.0.0.1:7778/mcp
sapb1 mcp --transport http --addr 127.0.0.1:9000
```

Register it with Claude Code:

```bash
claude mcp add --transport http sapb1 http://127.0.0.1:7778/mcp
```

The **default bind is loopback (`127.0.0.1:7778`) on purpose** — there is no
auth layer in front of production SAP, so only processes on this machine can
reach the server out of the box. Binding wider (e.g. a tailscale IP, or
`--addr 0.0.0.0:7778`) is an explicit `--addr` choice you make knowingly.
The endpoint path is `/mcp`; the server is stateless, so clients don't need to
carry an `Mcp-Session-Id`. Config resolution (`.env` next to the binary, etc.)
is identical to stdio mode.

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
