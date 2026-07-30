# postsql

A fast, **strictly read-only**, AI-native command-line browser for PostgreSQL.

`postsql` connects to a Postgres server and lets you explore every database,
schema, table, and row — and run arbitrary `SELECT` queries — without any risk
of writing to it. It emits clean JSON for agents and aligned tables for humans,
and can run as an **MCP server** so Claude can query the database directly.

Built for the JIVO Postgres server (`test_supabse`, 16 databases) but works
against any PostgreSQL 12+ instance via profiles.

---

## The read-only guarantee

Writes are impossible, enforced at three independent layers:

1. **Transaction access mode** — every statement runs inside a
   `BEGIN … READ ONLY` transaction. Postgres refuses any write in that
   transaction *even for a superuser*, and even for tricks like
   `EXPLAIN ANALYZE INSERT …` (→ `SQLSTATE 25006`).
2. **Connection setting** — `default_transaction_read_only=on` is set at
   connect time.
3. **Statement allowlist** — a first-token guard rejects anything that isn't
   `SELECT` / `WITH` / `EXPLAIN` / `SHOW` / `TABLE` / `VALUES` with a friendly
   error before it ever reaches the server.

`--where` filters are validated to reject statement terminators (`;`), so they
stay filters and can't break out into a second statement.

---

## Install

```bash
cd ~/postsql
go build -o postsql .              # macOS / Linux
go build -o postsql.exe .          # Windows
# optionally: cp postsql ~/go/bin/   (or anywhere on PATH)
```

Prebuilt binaries sit next to this README: `postsql` (macOS, arm64) and
`postsql.exe` (Windows, x86-64). Run `./postsql <cmd>` on macOS/Linux,
`.\postsql.exe <cmd>` on Windows — every example below writes just `postsql`
for brevity.

Requires Go 1.24+. Depends on `pgx/v5`, `cobra`, `BurntSushi/toml`.

---

## Configuration

Profiles live in `~/.postsql/config.toml` (keep it `chmod 600` — it holds a
password):

```toml
default = "jivo"

[profiles.jivo]
host = "103.89.45.76"
port = 5432
user = "postgres"
password = "…"
database = "postgres"
```

Select a profile with `--profile <name>` (defaults to the `default` profile).
Every field can be overridden by environment variables — `POSTSQL_HOST`,
`POSTSQL_PORT`, `POSTSQL_USER`, `POSTSQL_PASSWORD`, `POSTSQL_DATABASE`,
`POSTSQL_PROFILE` (with libpq's `PGHOST`/`PGPORT`/`PGUSER`/`PGPASSWORD`/
`PGDATABASE` as fallbacks) — so you can run zero-config against any server:

```bash
POSTSQL_HOST=db.internal POSTSQL_USER=readonly PGPASSWORD=… postsql dbs
```

> **Security note.** The bundled `jivo` profile connects as the `postgres`
> superuser (the only credential available). The READ ONLY transaction blocks
> all writes, but a superuser still has a wide *read* blast radius (server-side
> file reads, RLS bypass, every database). For least privilege, create a
> dedicated login and point the profile at it:
> ```sql
> CREATE ROLE postsql_ro LOGIN PASSWORD '…' NOSUPERUSER NOBYPASSRLS;
> GRANT CONNECT ON DATABASE jivo_ecom TO postsql_ro;
> GRANT USAGE ON SCHEMA public TO postsql_ro;
> GRANT SELECT ON ALL TABLES IN SCHEMA public TO postsql_ro;
> ```
> `postsql` will not silently default to `postgres`: if no user is configured
> it fails closed and asks you to set one.

---

## Global flags

| Flag | Meaning |
|------|---------|
| `--profile <name>` | connection profile to use |
| `-d, --db <name>` | target database (default: the profile's database) |
| `--json` | output JSON (array of objects) |
| `--csv` | output CSV |
| `--compact` | single-line JSON |
| `--select <cols>` | comma-separated columns to keep (errors on an unknown column) |
| `-n, --limit <N>` | max rows for `query` / `peek` / `export` (0 = unlimited) |
| `-q, --quiet` | suppress the row-count footer |
| `--timeout <dur>` | per-query timeout (default 30s; also enforced server-side) |

Values are returned exactly as Postgres sends them (like `psql`): `numeric`
keeps full precision, `uuid`/`json`/arrays are verbatim, SQL `NULL` is `null`.

---

## Commands

### Explore

| Command | What it does |
|---------|--------------|
| `dbs` | list all databases with size, owner, encoding |
| `schemas` | list schemas in `--db` with table counts |
| `tables [--schema S]` | list tables with row estimate + size (largest first) |
| `views [--schema S]` | list views + materialized views (type, owner, matview size) |
| `cols <[schema.]table>` | columns: name, type, nullable, default, position |
| `describe <t>` (`desc`) | columns + type + nullable + default + primary-key flag |
| `indexes <t>` | indexes on a table (name, unique, primary, definition) |
| `relationships <t>` (`fks`) | foreign keys in **and** out of a table |
| `search <term> [--all]` | find schemas/tables/columns by name (`--all` = every database) |
| `stats` | top tables by size + total database size for `--db` |
| `functions [--schema S] [--all]` | list functions/procedures (extension funcs hidden unless `--all`) |
| `sequences [--schema S]` | list sequences with current values |
| `roles` (`users`) | list roles/users and their privilege attributes (cluster-wide) |

### Read data

| Command | What it does |
|---------|--------------|
| `peek <t> [-n N] [--where E]` | sample rows (`SELECT * … LIMIT N`, default 20) |
| `count <t> [--where E]` | row count, optional filter |
| `query [sql]` | run any read-only SQL (reads stdin if no arg); `-n` wraps SELECTs |
| `export [<t>] [--query SQL] [--out F]` | dump a table or query to CSV/JSON, stdout or file |

### AI-native

| Command | What it does |
|---------|--------------|
| `schema-dump` (`schema`) | full schema of `--db` as one nested JSON object (columns, PKs, FKs, indexes) — a complete primer for an AI |
| `context` | token-efficient overview: server version, all DBs + sizes, top tables of `--db` |
| `doctor` | health check: reachability, version, read-only status, DB count, config path |
| `mcp` | run as a Model Context Protocol server (see below) |

### Examples

```bash
postsql dbs                                   # every database + size
postsql --db jivo_ecom tables                 # tables in jivo_ecom by size
postsql --db jivo_ecom describe amazon_mp     # column layout of a table
postsql --db jivo_ecom peek amazon_mp -n 5    # sample 5 rows
postsql --db jivo_ecom count amazon_mp --where "brand = 'JIVO'"
postsql --db jivo_ecom search sku --all       # find 'sku' columns across all DBs
postsql --db jivo_ecom query "SELECT brand, count(*) FROM amazon_mp GROUP BY brand" --json
postsql --db CRM export leads --csv --out leads.csv
postsql --db jivo_ecom schema-dump | jq '.schemas.public.tables | keys'
postsql --db jivo_ecom context                # prime an AI about the DB
```

### AI / agent tips

- `--json` everywhere → pipe straight into `jq` or an agent.
- `--select a,b,c` → keep only the columns you need (fewer tokens); errors on a
  typo instead of silently dumping everything.
- `--compact` → single-line JSON for logs/streaming.
- `schema-dump` once to teach an agent the whole shape of a database, then
  `query` for the specifics.
- Typed exit codes: `0` ok · `2` usage · `3` connection · `4` query · `5`
  read-only violation.

---

## MCP server (use it from Claude)

`postsql mcp` speaks the Model Context Protocol, exposing six read-only
tools: `postgres_query`, `list_databases`, `list_tables`, `describe_table`,
`search`, `schema_dump`. Two transports:

- **stdio** (default): newline-delimited JSON-RPC over stdin/stdout.
- **HTTP** (`--transport http`): stateless streamable HTTP — POST one
  JSON-RPC message to `/mcp`, get the single JSON response back (202 for
  notifications; no sessions, no SSE).

```bash
postsql mcp                                         # stdio
postsql mcp --transport http --addr 127.0.0.1:7779  # http://127.0.0.1:7779/mcp
```

Register the HTTP endpoint with Claude Code:

```bash
claude mcp add --transport http postsql http://127.0.0.1:7779/mcp
```

The `--addr` default binds loopback only — keep it that way unless you put
auth in front (it fronts raw production Postgres). Port 7779 follows the
fleet sequence ecom `:7777` / sapb1 `:7778` / postsql `:7779`.

For stdio, add it to Claude Desktop / Claude Code
(`claude_desktop_config.json` or the `mcpServers` block in your settings):

```json
{
  "mcpServers": {
    "postsql": {
      "command": "/Users/damanpreetsingh/postsql/postsql",
      "args": ["mcp"]
    }
  }
}
```

On Windows, point `command` at the `.exe` instead, e.g.
`"C:\\jivo-cli\\postsql\\postsql.exe"`.

Restart the client; Claude can then query the JIVO Postgres server directly —
still fully read-only, through the same three-layer guarantee.

To target a specific database by default, add `"--db", "jivo_ecom"` before
`"mcp"` in `args`, or pass `database` in each tool call.
