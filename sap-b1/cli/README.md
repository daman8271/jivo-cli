# sapb1

A **read-only** command-line client for the SAP Business One Service Layer
(`b1s/v1`), built for SAP B1 for HANA.

It never issues `POST`/`PUT`/`PATCH`/`DELETE` against business data. The only
writes it ever makes are `POST /Login` and `POST /Logout` — establishing and
tearing down a session cookie. Every business-data command (`orders`,
`invoices`, `items`, `partners`, `query`) is a plain OData `GET`.

It also ships with the **entire Service Layer schema embedded offline** — 498
services / 1950 operations — so you can explore what's available (`entities`,
`ops`, `catalog stats`, `fields`) with **zero network access**, before you're
even on the VPN.

## Before you do anything: get on the VPN

The Service Layer host is typically firewalled to the company network. **Get
on the company VPN, or get your IP whitelisted, before running anything
beyond `--help`.** If you're not connected, every network command will fail
with a clear "cannot reach ... are you on the VPN?" message instead of
hanging or crashing — but it still won't work until you're actually
connected.

## Setup

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Key                | Meaning                                              |
|--------------------|-------------------------------------------------------|
| `SAPB1_HOST`       | SAP Service Layer host/IP                              |
| `SAPB1_PORT`       | Service Layer port (default `50000`)                   |
| `SAPB1_COMPANYDB`  | The CompanyDB name — ask your SAP admin for this       |
| `SAPB1_USER`       | SAP username                                           |
| `SAPB1_PASSWORD`   | SAP password                                            |
| `SAPB1_INSECURE`   | `true` to skip TLS verification (self-signed certs)     |
| `SAPB1_TIMEOUT`    | Request timeout in seconds (default `30`)               |

`.env` is already git-ignored — **never commit it**. `.env.example` is the
template that *is* committed and contains no real credentials.

Build the binary:

```bash
go build -o sapb1 ./cmd/sapb1
```

Run it:

```bash
./sapb1 doctor
```

## Configuration precedence

For every setting, highest wins:

```
CLI flag  >  environment variable  >  .env file  >  built-in default
```

Global flags (available on every command): `--host --port --company --user
--insecure --timeout --json --csv`. There is intentionally **no `--password`
flag** — the password only ever comes from `SAPB1_PASSWORD` in the real
environment or `.env`, so it never ends up in your shell history or process
list.

If `SAPB1_COMPANYDB` isn't set, any command that needs it fails with:

> Company database not set — set SAPB1_COMPANYDB in .env or pass --company.
> Ask your SAP admin for the CompanyDB name.

## The read-only guarantee

- `internal/client` only ever sends `GET` (for entity reads), `POST /Login`,
  and `POST /Logout`. There is no code path that issues `POST`/`PUT`/`PATCH`/
  `DELETE` against any business entity set (`Orders`, `Invoices`, `Items`,
  `BusinessPartners`, etc.).
- The password is never printed, logged, or written to the session cache.
  `sapb1 auth status` and `sapb1 doctor` mask it as `****`.
- The session cache (`~/.sapb1-session.json`) stores only the session cookie
  values (`B1SESSION`/`ROUTEID`) and connection metadata — never the
  password — and is written with `0600` permissions.

## Commands

### Offline discovery (no network needed)

These read only the catalog embedded in the binary. They work with **zero
network access** — no VPN, no login, no server — and always exit `0` on
success. Use them to figure out what you can query before you connect.

The catalog lists write operations (`POST`/`PUT`/`PATCH`/`DELETE`) purely for
reference. sapb1 **never executes them** — it stays read-only.

#### `sapb1 entities`

List every service/entity: name, number of operations, HTTP methods present,
and whether it's readable (has a `GET`).

```bash
sapb1 entities                       # all 498
sapb1 entities --search invoice      # case-insensitive name filter
sapb1 entities --read-only           # only services that expose a GET
sapb1 entities --search order --json # machine-readable
```

#### `sapb1 ops <ServiceOrEntity>`

Show every operation (method + name) the catalog records for one service or
entity. Case-insensitive; on a miss it suggests the closest names.

```bash
sapb1 ops Orders                     # the readable Orders entity (GET/POST/PATCH...)
sapb1 ops OrdersService              # the OrdersService actions (POST-only)
sapb1 ops BusinessPartners --json
```

#### `sapb1 catalog stats`

Totals across the catalog: services, operations, per-method breakdown, and how
many services are readable.

```bash
sapb1 catalog stats
sapb1 catalog stats --json
```

#### `sapb1 fields <Entity>`

Answers "what can I `--select`?". **Live**, it does `GET <Entity>?$top=1` and
lists the JSON keys of the first record (sorted). If SAP is unreachable or not
configured, it falls back to showing that entity's catalogued operations, so
it's still useful offline.

```bash
sapb1 fields Orders
sapb1 fields BusinessPartners --json
```

### `sapb1 doctor`

Run this first. End-to-end diagnostic: is config present, is the host
reachable over TCP, does Login succeed. Prints a ✓/✗ checklist with
actionable hints (VPN, whitelist, missing CompanyDB, bad credentials).

```bash
sapb1 doctor
```

### `sapb1 auth login` / `status` / `logout`

```bash
sapb1 auth login              # logs in, caches the session, prints "Connected to <company> as <user>"
sapb1 auth status             # shows resolved config (password masked) + cached-session state
sapb1 auth logout             # logs out and clears the cached session
```

### `sapb1 orders list`

Sales orders (`Orders`).

```bash
sapb1 orders list
sapb1 orders list --open --top 50
sapb1 orders list --filter "CardCode eq 'C0001'" --orderby "DocDate desc"
sapb1 orders list --all --json | jq '.[] | .DocTotal'
```

### `sapb1 invoices list`

A/R invoices (`Invoices`). Same flag shape as `orders list`.

```bash
sapb1 invoices list --open --top 50
sapb1 invoices list --filter "DocTotal gt 10000"
```

### `sapb1 items list`

Items/products (`Items`).

```bash
sapb1 items list
sapb1 items list --low-stock 10          # QuantityOnStock le 10
sapb1 items list --filter "ItemsGroupCode eq 100"
```

### `sapb1 partners list`

Business partners — customers & suppliers (`BusinessPartners`).

```bash
sapb1 partners list --customers --top 50
sapb1 partners list --suppliers --json
```

### `sapb1 query <EntitySet>`

The power tool: a generic read against **any** Service Layer entity set.
This is what lets you (or an AI agent) pull data with no new code —
`Quotations`, `PurchaseOrders`, `PurchaseInvoices`, `Warehouses`,
`ItemGroups`, `Users`, `JournalEntries`, `BusinessPartnerGroups`, or
anything else in your schema.

```bash
sapb1 query Quotations --top 10
sapb1 query Warehouses --select "WarehouseCode,WarehouseName"
sapb1 query JournalEntries --filter "ReferenceDate ge '2024-01-01'" --all
sapb1 query Items --filter "ItemCode eq 'A0001'" --json
```

### Shared list flags

`orders list`, `invoices list`, `items list`, `partners list`, and `query`
all share:

| Flag           | Meaning                                                          |
|----------------|-------------------------------------------------------------------|
| `--filter`     | raw OData `$filter` expression                                    |
| `--select`     | comma-separated fields (also sets the table's column order)       |
| `--top`        | max rows (default 20, ignored with `--all`)                       |
| `--skip`       | pagination offset                                                  |
| `--orderby`    | raw OData `$orderby` expression                                    |
| `--all`        | paginate through everything via `odata.nextLink` (capped at 200 pages) |
| `--page-size`  | rows per page while paginating (`Prefer: odata.maxpagesize`)       |
| `--count`      | print only the server-side total row count (`$inlinecount=allpages`) |

### `--count`

On any list command or `query`, `--count` requests the server-side total via
OData `$inlinecount=allpages` and prints just the number (SAP returns it as
`odata.count`). If the server ignores it, sapb1 falls back to counting the
returned rows and says so. With `--json`, you get `{"count": N, "serverSide":
true|false}`.

```bash
sapb1 orders list --open --count
sapb1 query Invoices --filter "DocTotal gt 10000" --count --json
```

### Output format: `--json` / `--csv`

Every read command (`orders`, `invoices`, `items`, `partners`, `query`)
supports two global output formats, mutually exclusive with each other:

- `--json` — the raw OData `value` array as indented JSON, for piping into `jq`
  or feeding an AI agent.
- `--csv` — a header row plus one CSV row per record. Columns come from
  `--select` (in that order) if given, otherwise from the union of keys in the
  returned rows. Object/array cell values are JSON-encoded.

Without either flag, output is an aligned text table of the most useful
columns. The offline discovery commands support `--json` too.

```bash
sapb1 items list --select "ItemCode,ItemName,QuantityOnStock" --csv > stock.csv
sapb1 orders list --all --json | jq '.[] | .DocTotal'
```

## MCP server (for AI agents)

`sapb1 mcp` runs a **read-only** [Model Context Protocol](https://modelcontextprotocol.io)
server over stdio, so an AI agent (Claude Code / Claude Desktop) can call the
Service Layer as tools. It reuses the same client, catalog, and config as the
CLI — and stays strictly read-only: every tool is a `GET` (plus `Login`/`Logout`
for the session), with `readOnlyHint: true` in the tool metadata. The password
is never returned in a tool result or error.

It exposes nine tools:

- `sapb1_doctor` — config + reachability + login self-check.
- `sapb1_query` — the core generic read (`entity`, `select`, `filter`, `top`, `orderby`).
- `sapb1_entities` / `sapb1_ops` — offline catalog discovery.
- `sapb1_fields` — live field discovery with offline fallback.
- `sapb1_orders` / `sapb1_invoices` / `sapb1_items` / `sapb1_partners` — convenience wrappers.

Register it with Claude Code by adding this to `~/.claude.json` under
`mcpServers`:

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

Once registered, an agent can call `sapb1_query` with
`entity="Orders"`, `filter="DocStatus eq 'O'"` to pull open sales orders.

Full copy-paste registration for Claude Code and Claude Desktop, the tool
reference, and a stdio smoke-test are in **[MCP.md](MCP.md)**.

## Exit codes

| Code | Meaning              |
|------|----------------------|
| 0    | success              |
| 2    | usage error          |
| 3    | config missing/invalid |
| 4    | authentication failed |
| 5    | network/unreachable  |
| 6    | API error (server reached, request failed) |

## Session handling

`Login` returns `B1SESSION`/`ROUTEID` cookies which are sent on every
subsequent request. Sessions idle out after roughly 30 minutes; when a
request comes back `401`, sapb1 transparently re-logs-in once and retries
before giving up. The session is cached at `~/.sapb1-session.json` (mode
`0600`) so you don't have to re-login for every command.

## Self-signed certificates

SAP boxes commonly run with self-signed TLS certificates, even on port
50000 (the Service Layer is HTTPS-only). Set `SAPB1_INSECURE=true` in
`.env`, or pass `--insecure`, to skip certificate verification.
