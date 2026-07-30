# hana-sql MCP server

`hana-sql mcp` runs a **strictly read-only** [Model Context
Protocol](https://modelcontextprotocol.io) server over stdio (newline-delimited
JSON-RPC on stdin/stdout) by default, or over **streamable HTTP** with
`--transport http`. Register it with an MCP client and an AI agent can ask
JIVO's SAP Business One HANA database real SQL questions — `SUM`, `GROUP BY`,
`JOIN` — instead of hauling rows through the Service Layer.

Both transports expose the identical four tools and share every read-only layer.

## Read-only guarantee

Five layers. The first four are described in detail — including what each one
defends against and what is *not* proven — in [README.md](README.md#read-only-the-five-layers).
The short version:

| Layer | Where | What it does |
|---|---|---|
| 0 | `internal/guard/lex.go` | masks strings / quoted identifiers / comments; **fails closed** on anything unterminated |
| 1 | `internal/guard/guard.go` | first token must be `SELECT` or `WITH` (**no `EXPLAIN`** — it writes `SYS.EXPLAIN_PLAN_TABLE`) |
| 2 | `internal/guard/guard.go` | exactly one statement |
| 3 | `internal/guard/guard.go` | 33 banned keywords anywhere in the masked token stream (including `NEXTVAL` — see below) |
| 4 | `internal/hana/hana.go` | every statement runs in `BeginTx{ReadOnly:true}` and is **always rolled back**; the package contains no `Commit` call, and a test fails the build if one appears |
| 5 | `internal/hana/hana.go` | row cap, byte cap, statement deadline, in-flight semaphore |

There is no tool that writes, and no argument that can make a tool write.

**`NEXTVAL` is banned at layer 3.** `SELECT "SOMESEQ".NEXTVAL FROM DUMMY` passed
layers 0-2 and every other layer-3 entry, yet advancing a sequence is persistent
state that no rollback undoes — and the JIVO schemas hold 796 / 777 / 788
sequences (Oil / Mart / Beverages, counted live 2026-07-30). Until that entry
existed, the sentence above was false. `CURRVAL` is deliberately *not* banned: it
reads the value the session already holds and advances nothing.

**What layer 4 does and does not prove.** `hana_doctor` returns a
`read_only.transaction_proof` field that leads with `UNPROVEN`. HANA accepts
`set transaction read only` (BeginTx succeeds) but resolves object names before
applying the access mode, and on HANA 2.00.059 `SYS.M_TRANSACTIONS` exposes no
`ACCESS_MODE` column, so there is no read-only way to confirm the mode took
effect. Layers 0-3 are load-bearing on their own; the dedicated `SELECT`-only
HANA user is **blocking for a gateway rollout**, not optional hardening.

## The four tools

| Tool | Arguments | Notes |
|---|---|---|
| `hana_query` | `sql` (required), `max_rows?`, `timeout_ms?` | one `SELECT`/`WITH`. Carries the full SAP B1 crib sheet in its description. |
| `hana_tables` | `schema?`, `like?`, `include_views?`, `offset?`, `no_row_counts?` | **one page, not the catalog** — see below |
| `hana_columns` | `schema` (required), `table` (required), `like?` | column names, HANA types, scale, PK flag |
| `hana_doctor` | none | connection, login, version, clock skew, schema readability, the caps in force |

### `hana_tables` returns a PAGE, and says which companies it left out

There are ~9,200 tables across the three companies (Oil 3111 / Mart 3046 /
Beverages 3087, counted live) and the row cap is 1000, so an unfiltered listing
is one page. It is ordered by schema, so that page is *all Beverages* — which is
why the note now names both what it covers and what it does not:

```
PARTIAL CATALOG: rows 1-1000 of the matching objects, covering only
JIVO_BEVERAGES_HANADB; NOTHING from JIVO_OIL_HANADB, JIVO_MART_HANADB is in this
answer; fetch the next page with offset=1000
```

Pass `like` to narrow it, `schema` for one company, `offset` for the next page,
or `no_row_counts` to skip the `SYS.M_TABLES` join (which is what makes a broad
listing slow — 7.1s on the VPS).

### An unknown `schema` is an ERROR, never an empty result

`schema:"JIVO_BEVERAGE_HANADB"` (one missing S), `schema:"Beverages"` and
`schema:"Oil"` are all refused, with a "did you mean". A one-letter typo must not
be indistinguishable from "this company has no data" — that is the same
silent-wrong-answer class the `company` argument is refused for. The same rule
applies to `hana_columns`: a wrong-case table name (`oinv`) comes back as a
refusal naming the correct spelling, not as an empty column list.

Names are `hana_*` deliberately: behind the JIVO MCP gateway this backend is
registered with `Prefix == StripPrefix == "hana_"`, which makes the rename the
identity in both directions, so the names read correctly standalone **and**
through the gateway with no `hana_hana_` stutter.

### There is no `company` parameter — and passing one is an error

You choose the company by **qualifying the table name**:

```sql
SELECT COUNT(*) FROM "JIVO_BEVERAGES_HANADB"."OCRD"
```

`company`, `companyDB`, `db`, `database`, `schema` and any other unrecognised
argument are **rejected**, not ignored:

```
unrecognised argument "company" — refusing rather than ignoring it, because a
silently discarded parameter returns the wrong company's numbers with no tell.
There is no company/database parameter on this tool, and it will NOT be applied
silently: choose the company by qualifying the table name instead, e.g.
"JIVO_BEVERAGES_HANADB"."OINV".
```

This is enforced twice — `additionalProperties: false` in the advertised JSON
Schema (advice) and `DisallowUnknownFields` at decode time (enforcement).

## Response shape

Every tool returns the MCP envelope `{"content":[{"type":"text","text":…}],"isError":…}`
where `text` is one compact JSON object:

```json
{
  "as_of": "2026-07-30T19:19:57+05:30",
  "as_of_source": "mcp-host-clock",
  "elapsed_ms": 259,
  "row_count": 3,
  "max_rows": 1000,
  "truncated": false,
  "columns": [{"name": "NET", "type": "DOUBLE"}],
  "rows": [{"CO": "Oil", "INVOICES": 568, "NET": 410818050.21}],
  "note": "present only when a cap tripped or a degrade applied"
}
```

`max_rows` is **`null`, not `0`,** when no row cap is in force (`--max-rows 0`):
`"max_rows": 0` reads as "zero rows permitted", the opposite of the truth.

`truncated: true` means exactly one thing: **there was at least one more row and
you are not seeing it.** Both caps are checked *before* a row is consumed, so a
result set that happens to end on the cap is reported complete.

Value rules, all of which exist because the naive version is wrong:

- **DECIMAL → an exact decimal string** (`"1074316124.550000"`), never a
  `big.Rat` fraction (`8210929/100`), never a silently rounded float.
- **Dates → `"2026-07-30"`.** SAP B1 declares every business date as HANA
  `TIMESTAMP` with a zero clock, so a midnight timestamp is rendered as a bare
  date rather than an RFC3339 instant. `columns[].type` still reports `TIMESTAMP`.
- **Timestamps with a clock → `"2026-07-30T19:33:19.913"`, with NO zone suffix.**
  A HANA `TIMESTAMP` carries no time zone; it is a wall clock, and on this server
  that wall clock is IST. Rendering it with RFC3339Nano stamped a `Z` on it and
  published the server's local time as a UTC claim 5h30m wrong (measured live:
  `CURRENT_TIMESTAMP` → `2026-07-30 19:33:19.913` while `CURRENT_UTCTIMESTAMP` →
  `2026-07-30 14:03:19.913`). Sub-second digits still survive.
- **CLOB/NCLOB/BLOB** are scanned through a capped LOB target (8 KiB **on the MCP
  server only**; the human CLI has no LOB cap) and marked ` …[clipped]`. Scanning
  a HANA LOB into a plain `any` yields the driver's locator object, not the text.
- `columns[].type` carries the **SQL** type name, not go-hdb's internal storage
  name: `LONGDATE` → `TIMESTAMP`, `DAYDATE` → `DATE`, `SECONDTIME` → `TIME`,
  `FIXED8/12/16` → `DECIMAL`. That is what makes the field usable for its stated
  purpose — telling an exact `DECIMAL` from a float `DOUBLE`.
- **Duplicate column names** are made unique against every name already assigned
  *and* every name a real column claims, so `SELECT 1 AS X, 2 AS X, 3 AS X_2`
  comes back as `X`, `X_3`, `X_2` — all three values kept, the real `X_2` still
  called `X_2`, and `columns` always in agreement with the row keys. It used to
  produce `[X, X_2, X_2]` and a row with two keys, silently dropping the `2`.

Refusals come back as `isError: true` with the layer that refused:

```
REFUSED (read-only layer 3): banned keyword "UPDATE" appears in the statement — only SELECT / WITH reads are allowed
```

## Build

```bash
cd hana-sql
go build -o hana-sql .

# static linux binary for the VPS / a container
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -o bin/hana-sql .
```

## Configuration

Resolved by `internal/config`, highest precedence first:

1. process environment — `HANA_HOST` / `HANA_PORT` / `HANA_USER` / `HANA_PASSWORD`
2. the env file — `-env <path>`, else `$HANA_ENV`, else the nearest
   `connections/hana.env` walking up from the working directory
3. built-in default for the port only (`30015`)

The process environment wins so a container can be configured with plain env
vars and no file. **No credential value is ever printed** — `hana_doctor`
reports `"password": "**** (set)"` and refers to the env file by path, and every
error and audit line is scrubbed before it leaves the process.

If credentials cannot be resolved the server still **starts** and reports the
problem through `hana_doctor`, rather than crash-looping a container because the
office tunnel blinked.

## Register with Claude Code (stdio)

```json
{
  "mcpServers": {
    "hana": {
      "command": "/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql",
      "args": ["mcp"],
      "env": {
        "HANA_ENV": "/Users/damanpreetsingh/jivo-cli/connections/hana.env"
      }
    }
  }
}
```

Or supply the credentials directly (never commit a file containing a real password):

```json
{
  "mcpServers": {
    "hana": {
      "command": "/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql",
      "args": ["mcp"],
      "env": {
        "HANA_HOST": "127.0.0.1",
        "HANA_PORT": "47301",
        "HANA_USER": "…",
        "HANA_PASSWORD": "…"
      }
    }
  }
}
```

Logs go to **stderr only** — stdout is the protocol stream and must stay clean.

### Protocol version

`initialize` answers with a revision this server actually implements —
`2025-06-18`, `2025-03-26` or `2024-11-05` (the default). It used to echo back
whatever string arrived, including `1999-01-01-BOGUS`, which makes negotiation a
no-op: a client could not discover that the server does not speak its revision.
A client that asks for something unsupported now gets the default back and can
compare the two. JSON-RPC batching, which both `2024-11-05` and `2025-03-26`
mandate, is implemented on both transports.

## HTTP transport (streamable HTTP)

```bash
hana-sql mcp --transport http                       # http://127.0.0.1:7706/mcp
hana-sql mcp --transport http --addr 127.0.0.1:9000
```

```bash
claude mcp add --transport http hana http://127.0.0.1:7706/mcp
```

The endpoint is `POST /mcp` only. It is fully stateless — no `Mcp-Session-Id`,
no SSE stream — so `GET`/`DELETE` return `405` with `Allow: POST`. Bodies are
capped at 4 MiB, notifications get `202` with an empty body, and unparseable
JSON gets `400` with JSON-RPC code `-32700`. JSON-RPC **batches** (a top-level
array) are answered with an array of responses; an all-notification batch gets
`202`.

### Loopback binding is not the mitigation — these three checks are

A web page a JIVO machine visits can POST to `http://127.0.0.1:7706/mcp`, and a
`Content-Type: text/plain` POST is a CORS **simple** request, so it needs no
preflight. Binding to loopback does not stop a browser, and DNS rebinding makes
the responses readable. So the transport validates, before parsing any JSON:

| Check | Default | Escape hatch |
|---|---|---|
| `Origin` | **absent, or refused** — a request carrying an Origin came from a browser | `--allow-origin https://…` (comma-separated, `*` disables) |
| `Host` | loopback only (`127.0.0.1`, `localhost`, `::1`) — the anti-DNS-rebinding check | `--allow-host name:port` (comma-separated, `*` disables) |
| `Content-Type` | must be `application/json` — this is what forces a browser to preflight, and no CORS header is ever emitted | none; it is the protocol's content type |

A wrong `Origin`/`Host` is `403`, a wrong `Content-Type` is `415`. Non-browser
clients (the MCP client, the gateway, `curl`) send no `Origin` and reach the
server by its loopback name, so nothing legitimate changes.

Optionally add a shared secret with `--auth-token <token>` (or `HANA_MCP_TOKEN`),
which requires `Authorization: Bearer <token>` on every request. **If you front
this endpoint with a reverse proxy or reach it by service name inside Docker, you
must pass `--allow-host`** — otherwise the Host check refuses it.

None of this replaces the dedicated `SELECT`-only HANA user. It is the difference
between "a visited web page can query the books" and "it cannot".

## Tuning the caps

| Flag | Default | Why you'd change it |
|---|---|---|
| `--max-rows` | `1000` | hard row ceiling; a per-call `max_rows` may only lower it. `0` means unlimited, reported as `"max_rows": null` |
| `--max-bytes` | `1048576` | approximate response payload cap, checked **before** each row is added — so it is a genuine ceiling, and `truncated` never fires on an exact fit |
| `--timeout` | `60s` | per-statement deadline. go-hdb turns this into a real **server-side cancel**, so it bounds HANA CPU, not just our wait. It also bounds the queue wait: a call that dies waiting for a slot was never sent. Keep it under the gateway's 120s call timeout. |
| `--max-concurrent` | `2` | in-flight queries, so a model cannot stampede the database the business is actually using |
| `--quiet` | off | suppress the per-query audit line |
| `--allow-origin` | none (all refused) | permit a browser origin on the HTTP transport |
| `--allow-host` | loopback only | permit an extra `Host` value (a reverse proxy, a Docker service name) |
| `--auth-token` | none | require `Authorization: Bearer <token>` (also `HANA_MCP_TOKEN`) |

A timeout that elapses while the **connection** is being opened is reported as
such ("this call's own deadline elapsed during connection SETUP"), not as "could
not connect to HANA (tried plaintext and TLS)" — the first call after startup
pays for the dial, and blaming the office tunnel for the caller's own limit sends
whoever is on call to the wrong place.

## Audit

One line per call on stderr — verdict, policy, rows, truncation, elapsed, error
class and the first 500 characters of the statement, always scrubbed:

```
hana-sql audit ts=2026-07-30T19:19:58+05:30 verdict=accepted policy=mcp rows=5 truncated=true elapsed=218ms err="-" sql="SELECT \"DocEntry\",\"DocDate\" FROM \"JIVO_OIL_HANADB\".\"OINV\" ORDER BY \"DocEntry\""
hana-sql audit ts=2026-07-30T19:19:57+05:30 verdict=refused  policy=mcp rows=0 truncated=false elapsed=0s   err="REFUSED (read-only layer 2): multiple statements are not allowed (found ';')" sql="SELECT 1 FROM DUMMY; DROP TABLE \"JIVO_OIL_HANADB\".\"OINV\""
```

Refused statements are logged too — that is the record of what a client *tried*
to do.

## Deploying behind the gateway (stage 2, not done here)

Two things to get right, both of which have bitten this stack before:

1. **A container cannot reach the host's `127.0.0.1:47301`.** Inside the
   `jivo-mcp` network HANA is at **`172.16.1.1:30015`** via the existing
   `hana-bridge` socat. Two env files with two different `host:port` pairs is
   the confusion to expect; `hana_doctor`'s `tcp` check hints at exactly this.
2. **Single-file bind-mounted env files swap inodes on edit.** After changing
   `hana.env`, use `docker compose up -d --force-recreate hana`, never `restart`.
