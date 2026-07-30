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

That boundary is a test, not a promise — three independent ones, because a
read-only guarantee asserted only in metadata is a claim rather than a property:

| Test | Layer | What it would catch |
|---|---|---|
| `TestRegisteredToolsAreReadOnly` | metadata | a tool without `readOnlyHint: true`, marked destructive, or any change to the exact 9-tool set |
| `TestMCPPackageCannotReachWriteAPI` | source | the package so much as *naming* `client.Create`/`Update` or `http.MethodPost/Put/Patch/Delete` (AST walk, so comments and description text can't trip or satisfy it) |
| `TestWholeSurfaceIssuesOnlyReadsAndLogins` | wire | every tool driven for real against a fake Service Layer that fails the test if it receives anything but `GET` plus `POST /Login`/`/Logout` |

Adding a write tool breaks the build.

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

## Choosing a company

JIVO keeps **three separate SAP company databases**, and a figure from one is
not comparable to another's:

| `company` | Business |
|---|---|
| `JIVO_OIL_HANADB` | Oil |
| `JIVO_MART_HANADB` | Mart |
| `JIVO_BEVERAGES_HANADB` | Beverages |

**Every tool takes `company`.** Omit it and the server's configured
`SAPB1_COMPANYDB` is used; pass it and the Service Layer session is genuinely
opened against that database (the company travels in the `POST /Login` body, so
it re-scopes the read itself, not just the label). An unrecognised value is a
hard error — it never falls back to the default, because a silently-defaulted
company is exactly how one company's books get reported as another's.

Every response echoes back the `company` it actually read, so an answer can
always be attributed.

Sessions are cached per `company`+host+port+user — on disk between processes,
and in memory inside the running server. Alternating between companies reuses
each one's session instead of forcing a fresh login on every switch, and a
BURST of concurrent tool calls (which is what an agent batching work looks like
over HTTP) costs **one** `Login` per company, not one per call: the in-memory
store holds a per-identity lock, so the first caller logs in and the rest reuse
its session. That matters because a Service Layer session is a licensed slot
held for its full TTL.

`sapb1_doctor` is the deliberate exception: it always performs its own `Login`,
because reporting on somebody else's session would not answer the question it
exists to answer.

## Tools

All tools are read-only. The catalog tools (`sapb1_entities`, `sapb1_ops`) work
fully **offline** — no VPN or login needed — and `sapb1_fields` falls back to
the catalog when SAP is unreachable.

Every row-returning tool (`sapb1_query`, `sapb1_orders`, `sapb1_invoices`,
`sapb1_items`, `sapb1_partners`) shares the same paging parameters:

| Param | Range | Meaning |
|---|---|---|
| `top` | 1–5000 (default 20) | Max rows. Larger than the Service Layer's ~20-row page is fine — `odata.nextLink` is followed for you. |
| `skip` | ≥ 0 | Offset. Pass a truncated response's `next_skip` to continue. |
| `page_size` | 1–500 | Rows per underlying request (`Prefer: odata.maxpagesize`). Affects round trips only, never the result. |
| `all` | bool | Every matching row, up to 5000. |
| `count` | bool | **Only** the server-side total, in one request that fetches no rows (`$top=0&$inlinecount=allpages`). |

`count`, `all` and `top` are mutually exclusive; so are `count` and
`skip`/`page_size`/`select`/`orderby` (a count returns no rows, so a projection
or an ordering over them cannot be honoured). Conflicts are errors, not "last
one wins".

An explicit `null` is **not** the same as omitting a parameter and is rejected
by name — `"company": null` is what an agent sends when its company variable
evaluated to nothing, and silently reading that as "the default company" is the
one substitution this surface must never make.

The `entity` you pass is an entity-set NAME. It may not contain `#`, `?`, `&`,
`%` or whitespace: those characters change the shape of the request URL rather
than name an entity (a `#` in particular turns `$filter`/`$select`/`$orderby`/
`$top` into a URI fragment that is never sent, and the call then succeeds while
answering a different question). Such a name is a hard error, never a cleanup.

| Tool | Args (beyond `company` + paging) | What it does |
|------|------|--------------|
| `sapb1_doctor`   | *(none)* | Config + TCP reachability + Login, **against the requested company** — this is how you prove Mart or Beverages is reachable. JSON report, password masked. |
| `sapb1_query`    | `entity` (req), `select`, `filter`, `orderby` | Core tool: read-only OData GET against any entity set. |
| `sapb1_entities` | `search`, `readOnly` | Services/entities from the embedded catalog (offline; company-independent). |
| `sapb1_ops`      | `service` (req) | Operations for one service, from the catalog (offline; company-independent). |
| `sapb1_fields`   | `entity` (req) | Live field names (`GET ?$top=1` keys); falls back to catalog ops offline. |
| `sapb1_orders`   | `filter`, `open` | Sales orders, newest first. `open=true` → `DocumentStatus eq 'bost_Open'`. |
| `sapb1_invoices` | `filter`, `open` | A/R invoices, newest first. `open=true` → `DocumentStatus eq 'bost_Open'`. |
| `sapb1_items`    | `filter`, `lowStock` | Items. `lowStock=N` → `QuantityOnStock le N`. **`lowStock=0` is honoured** and means "out of stock"; omit the parameter for no stock filter. |
| `sapb1_partners` | `filter`, `customers`, `suppliers` | Business partners. `customers`/`suppliers` filter by `CardType` (mutually exclusive). |

## The response shape

Every row-returning tool, in every mode, returns exactly this — so an agent
never has to guess which fields it got:

```json
{
  "company": "JIVO_MART_HANADB",
  "entity": "BusinessPartners",
  "rows_in_page": 45,
  "total_count": 2184,
  "truncated": true,
  "next_skip": 45,
  "as_of": "2026-07-30T13:33:43Z",
  "as_of_source": "server",
  "rows": [ … ]
}
```

| Field | Notes |
|---|---|
| `company` | The CompanyDB actually queried. Always present. |
| `rows_in_page` | `len(rows)` in **this** response. **Not** a total. |
| `total_count` | The server's own total (`$inlinecount=allpages`), for the whole filtered set. Present in **every** mode when the server gave one — including the default `top` mode, so a truncated answer always carries a sense of scale. **Omitted when unknown** — never guessed. It is `$skip`-agnostic: with `skip` set it still reports the whole set's total, not what is left. |
| `truncated` | Always present, so "is that everything?" needs no inference. It means "we stopped early **and** `next_skip` gets you further" — so it is never `true` on a page with zero rows, and a `total_count` that disagrees with the rows returned (deleted rows, row-level authorisation, a view) does **not** make a completed sweep truncated. |
| `next_skip` | Present **iff** `truncated`. Pass as `skip` with the *same* filter/orderby. |
| `as_of` / `as_of_source` | RFC3339 stamp from SAP's HTTP `Date` header (`server`), or this machine's clock when the header was absent (`local`). |
| `rows` | Always an array; `[]` in count mode. |

There is **no field called `count`**. The old one was rows-in-a-page sitting
next to a 20-row cap, and it read like a total.

### Recipes

**Count something** — one request, one atomic number, and no rows on the wire
(`$top=0&$inlinecount=allpages`, ~120 bytes). A paged tally can straddle live
postings and land between two truths; a `$top=1` count used to haul a complete
~200-field SAP document back just to read a header:

```json
{ "name": "sapb1_query", "arguments": {
    "entity": "Invoices",
    "filter": "DocumentStatus eq 'bost_Open' and Cancelled eq 'tNO'",
    "count": true } }
→ { "company": "JIVO_OIL_HANADB", "total_count": 12862, "rows_in_page": 0,
    "truncated": false, "as_of": "2026-07-30T13:33:49Z", "rows": [] }
```

If the Service Layer ignores `$inlinecount`, this is a **hard error**. It will
never hand back a page length dressed as a total.

**Sweep a whole set:**

```json
{ "name": "sapb1_items", "arguments": {
    "company": "JIVO_BEVERAGES_HANADB",
    "filter": "MinInventory gt 0 and QuantityOnStock lt MinInventory and InventoryItem eq 'tYES'",
    "all": true } }
```

**Continue after a truncated result** — pass `next_skip` back as `skip`, with
the same filter and orderby. Offsets are not snapshot-consistent on a live
table, so order by a stable key (e.g. `DocEntry`) when paginating and compare
`as_of` stamps if two calls disagree.

```json
{ "name": "sapb1_query", "arguments": { "entity": "Orders", "orderby": "DocEntry", "top": 45, "skip": 45 } }
```

Typical flow: **`sapb1_doctor`** (confirm connectivity) → **`sapb1_entities`** /
**`sapb1_fields`** (discover what to read) → **`sapb1_query`** (fetch the rows).

## Unknown parameters are rejected, never ignored

**This is a deliberate breaking change.** A call carrying an argument the server
does not understand now fails with a tool error naming the offending key *and*
listing the valid ones:

```
unknown parameter "companyDB" for sapb1_query — valid parameters:
company, entity, select, filter, orderby, top, skip, page_size, all, count
```

Previously `sapb1_query` accepted `company`/`companyDB`/`db`/`database`,
silently discarded them, and answered from the one configured company. An agent
that asked for Beverages got Oil, formatted exactly like a correct answer, with
nothing anywhere in the response to say so. An unrecognised argument is not a
harmless extra — it is a statement of intent the answer failed to honour.

Tools also advertise `additionalProperties: false`, so a schema-aware client is
steered away before it sends one. The server-side decoder is still the
authoritative rejection.

Any caller passing stray keys today will start failing. That is the point.

## Field names that cost a round trip to guess

Service Layer property names are **not** the HANA column names:

| Use | Not | Note |
|---|---|---|
| `DocumentStatus` (`'bost_Open'` / `'bost_Close'`) | `DocStatus` | |
| `Cancelled eq 'tNO'` | `Canceled` | Two l's on **every** entity, including `IncomingPayments`/`VendorPayments` whose HANA columns say otherwise. |
| `ReferenceDate` | `DocDate` | `JournalEntries` have no `DocDate`. |
| `CurrentAccountBalance` | `Balance` | **Positive = DEBIT** (party owes JIVO), **negative = CREDIT** (JIVO owes them). |
| `CreditLimit` | `CreditLine` | `0` means no limit set. |
| `QuantityOnStock` | `OnHand` | |
| `MinInventory` | `MinLevel` | `InventoryItem eq 'tYES'` is what makes an item stock-managed. |

Payment entities (`IncomingPayments`/`VendorPayments`) have **no `DocTotal`** —
the amount is `CashSum + TransferSum + BillOfExchangeAmount` plus the line sums
inside `PaymentChecks` and `PaymentCreditCards`.

Turnover/sales = (`Invoices` `DocTotal - VatSum`) − (`CreditNotes`
`DocTotal - VatSum`), by `DocDate`, with `Cancelled eq 'tNO'`.

**What the Service Layer *can* do** (verified live — don't work around these):

- **Field-to-field `$filter` comparison** works server-side:
  `CurrentAccountBalance gt CreditLimit`, `QuantityOnStock lt MinInventory`.
- **Server-side `$orderby` is reliable** for a global top-N — no need to haul
  rows into context and sort them.

What it can't: `$filter` has **no** `toupper()`/`tolower()`, so name matching is
case-exact. There is no server-side `SUM`.

## Verify the server by hand

Pipe an `initialize` + `tools/list` into it and you'll get the tool list back:

```bash
printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | ./sapb1 mcp
```
