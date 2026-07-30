# jivo-gateway — one read-only MCP endpoint for all five JIVO backends

A single MCP server that fronts the five existing read-only MCP backends and
presents them as one tool list. Clients (claude.ai, Claude Desktop, Claude Code)
connect once instead of five times.

| Backend | Prefix | Strips | Compiled-in URL |
|---|---|---|---|
| SAP B1 (`sapb1`) | `sap_` | `sapb1_` | `http://sapb1:7701/mcp` |
| Postgres (`postsql`) | `pg_` | — | `http://postsql:7702/mcp` |
| ecom | `ecom_` | — | `http://ecom:7703/mcp` |
| oms | `oms_` | — | `http://oms:7704/mcp` |
| factory | `fct_` | — | `http://factory:7705/mcp` |

Plus one native tool, `gateway_status`, which reports gateway + backend health.

**Strips** is a redundant prefix the backend already puts on every one of its own
tool names, removed before the gateway prefix goes on, so sapb1's `sapb1_query`
is advertised as `sap_query` rather than `sap_sapb1_query`. It is set only where
*every* tool of that backend shares it (verified against their real tool
registrations): sapb1 names all nine `sapb1_*`; postsql (`postgres_query`,
`list_databases`, `search`, …) and ecom / oms / factory (`<api>_search`,
`<api>_execute` next to bare `search` / `sql` / `context` and the Cobra-tree
mirror) share nothing, so they strip nothing. Routing is the exact inverse: the
gateway prefix comes off and the strip goes back on, so a backend always receives
its own original tool name.

## ⛔ Read-only

Two different guarantees, worth stating separately:

- **Structural, and this module's own.** The gateway can emit exactly four
  methods toward a backend — `initialize`, `notifications/initialized`,
  `tools/list`, `tools/call` — and there is no code path that emits anything
  else, on any error, retry or re-initialization path. On the front side only
  `initialize`, `ping`, `tools/list` and `tools/call` are accepted; every other
  JSON-RPC method is `-32601 method not found`. The gateway itself never creates,
  updates or deletes anything, and holds no compiled-in credential.
- **Downstream, and each backend's own.** Whether a given `tools/call` can change
  anything is a property the *backend* enforces (all five JIVO MCP backends are
  read-only by construction; SAP B1's Service Layer tools are GET-only, postsql
  refuses anything but `SELECT`/`WITH`, and so on). The gateway forwards a
  `tools/call` to the backend that owns the prefix and does not, and cannot,
  audit what the tool then does. It is a faithful pipe with a narrow mouth, not
  a policy engine: if a backend ever grew a writing tool, the gateway would
  forward it. That is why the four-method whitelist is the guarantee that is
  actually tested here (`TestGatewayOnlyEmitsWhitelistedMethods`,
  `TestGatewayWhitelistHoldsThroughRetryPaths`).

## Build

Zero dependencies, stdlib only (`go 1.26.1`).

```sh
go build ./... && go vet ./... && go test ./...

go test -race -count=2 ./...   # the gate this module is held to

# deploy artifact (static linux/amd64, for the alpine container)
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath \
  -ldflags "-s -w -X main.version=0.2.1" -o ./bin/jivo-gateway .
```

## Run

```sh
jivo-gateway --addr :7700          # in a container: bind all interfaces
jivo-gateway --version
```

| Flag | Env | Default | Meaning |
|---|---|---|---|
| `--addr` | `JIVO_GW_ADDR` | `127.0.0.1:7700` | front-side listen address |
| `--ttl` | `JIVO_GW_TTL` | `5m` | how long a merged `tools/list` snapshot stays fresh |
| `--list-timeout` | — | `10s` | per-backend budget for one `tools/list` refresh |
| `--call-timeout` | — | `120s` | budget for one forwarded `tools/call` (SAP can be slow) |
| `--url-<name>` | `JIVO_GW_URL_<NAME>` | see table above | one backend's endpoint |

Flags win over env, env wins over the compiled default. A non-positive `--ttl`,
`--list-timeout` or `--call-timeout` is a startup error, not a silent
everything-is-down (a zero timeout expires every context before it is used).

Endpoints: `POST /mcp` **and** `POST /mcp/` (stateless streamable HTTP — one
JSON-RPC message per POST, one JSON response, no sessions, no SSE) and
`GET /healthz` → `ok`. Both paths are registered because behind a reverse proxy
the surviving path is whatever `stripPrefix` leaves behind, and a 404 there looks
like an outage.

## Behaviour worth knowing

- **Backend sessions are handled for you.** mcp-go v0.47.0 (ecom / oms /
  factory) hands out an `Mcp-Session-Id` on `initialize` and answers a stale one
  with a plain-text 404; the gateway keeps one lazily-created session per
  backend and re-initializes + retries **once** on expiry. Stateless backends
  (sapb1 v0.56, postsql) never issue that header, so none is ever sent to them —
  the protocol self-discriminates, nothing is configured per backend.
  Only **404** is read as an expiry: a 400 is a real error, and treating it as an
  expiry would re-initialize on every call forever without ever succeeding. A 404
  to a request that carried *no* session header on a backend we believe is
  initialized also triggers the one re-init, so a backend that answered
  `initialize` without a session id cannot stay wedged.
- **Initializing a backend never blocks another caller.** One caller does the
  handshake; anyone else who arrives meanwhile waits on {that handshake, their
  own deadline}, so a backend that accepts TCP and then never answers costs each
  caller only its own budget instead of parking every caller in a lock. Losing
  that race costs a caller nothing: only a *real* backend failure is charged to
  the one-retry budget, so a caller with seconds left is never billed for other
  callers' impatience, and every error whose only cause was cancellation wraps a
  context error — the status cache can tell "this backend is broken" from
  "somebody hung up".
- **Front side is stateless.** `Mcp-Session-Id` is never emitted, so any client
  or reverse proxy can talk to any instance. `ReadHeaderTimeout` 10s,
  `ReadTimeout` 60s, `IdleTimeout` 120s; no `WriteTimeout`, because a forwarded
  SAP query may legitimately take the full `--call-timeout` before there is
  anything to write.
- **A down backend degrades, it does not break.** `tools/call` returns an MCP
  tool error (`isError: true`, HTTP 200) reading `backend <name> unavailable:
  …`; `tools/list` keeps that backend's last known tools (stale-while-down) so a
  backend restart never churns a client's cached tool list. Backend JSON-RPC
  errors are forwarded with their code, message and data intact.
- **A refresh is never charged to one client's request.** The fan-out runs on a
  context detached from whoever triggered it and bounded only by the per-backend
  `--list-timeout`, so a client that disconnects mid-refresh cannot mark all five
  backends down for a whole TTL. A backend that answers healthily with *zero*
  tools keeps its last known list (`last_error` says so) rather than making every
  one of its tools vanish; a backend whose pagination loops or never terminates is
  a failed refresh, not a tenfold-duplicated list. A caller that arrives during the
  **first-ever** refresh waits for it (bounded by its own deadline) instead of
  being served an empty list — there is nothing stale to serve yet. Once that
  first refresh has landed, a caller arriving mid-refresh gets the last known list
  immediately.
- **`gateway_status` is live, not cached.** It re-lists every backend first, with
  a short per-backend budget (`min(--list-timeout, 5s)`) on a detached context,
  then reports. `last_refresh` is when the merged list was last rebuilt.
- **Tool results are forwarded verbatim** (`encoding/json` may escape `<`, `>`,
  `&` as `\uXXXX` — same JSON value; postsql's own endpoint does the same).
- Startup lists every backend once, non-fatally, and logs a line per backend.
  Backends that are down at boot are picked up on the next lazy refresh.

## Known behaviours (deliberate, documented rather than fixed)

Each of these was raised in review and kept on purpose. They are listed so the
next reader does not have to rediscover the reasoning.

- **An unknown tool name under a *known* prefix is forwarded.** `sap_nonsense`
  goes to sapb1 and comes back with sapb1's own error. Routing is prefix-table
  only, deliberately: the cached tool list must never be able to mis-route or
  block a call, and the backend is the authority on what it owns. Only an unknown
  *prefix* is rejected locally.
- **No JSON-RPC batches.** An array body is a parse error, exactly as postsql's
  endpoint behaves. No JIVO client sends batches; the 2025-06-18 MCP spec removed
  them.
- **No front-side response size cap** beyond the 32 MiB the backend response
  parser enforces. Request bodies are capped at 4 MiB.
- **`_meta` / `progressToken` are dropped**, and a client `cursor` on `tools/list`
  is ignored: the merged list is always returned whole and unpaginated. The
  gateway does not proxy progress notifications, because the front side has no
  stream to put them on.
- **`protocolVersion` is echoed verbatim** on `initialize` (postsql's behaviour):
  whatever the client asks for is what it is told, and the backend side always
  negotiates `2025-03-26` independently.
- **Tool-definition keys come back alphabetized.** Definitions are decoded to
  rewrite `name` and re-marshalled, so `encoding/json` orders the object keys.
  Every *value* — description, `inputSchema`, `outputSchema`, `annotations`,
  anything the backend invented — is byte-identical.
- **Backend error bodies are relayed, up to 512 bytes**, into the error text.
  The five backends are trusted internal infrastructure and their message is the
  most useful thing an operator can be given.
- **Internal topology is visible in `gateway_status` and in error text.** Backend
  `host:port` URLs are reported as-is, on purpose: this is a read-only service
  behind a secret path, and knowing *which* backend is down is the point of the
  tool. **Credentials never are** — if a backend URL carries userinfo, the
  password is masked as `***` everywhere it is displayed or logged, and the URL
  put on the wire has the userinfo stripped (it travels as a basic-auth header
  instead) so it cannot leak through a `net/http` error string.
- **A duplicate advertised tool name is dropped, not de-duplicated by renaming.**
  First backend in configured order wins; the loser's `last_error` names what it
  lost. Renaming would make a tool's name unstable across refreshes.
- **A leader whose `initialize` times out can orphan one upstream session.** If
  the backend answers the handshake after the leader's deadline has passed, that
  session id is never learned and never used — and the gateway sends no
  `DELETE`, because the only write it performs is Login. mcp-go's idle sweeper
  reaps it. The cost is one idle session object on the backend until then, which
  is cheaper than adding a write path to a read-only gateway.
- **Re-initializing mid-pagination is bounded, not free.** Each `tools/list` page
  is its own request, and each request allows exactly one re-init on expiry, so
  one client message costs at most 2 × `maxToolPages` (20) initializes in the
  worst case — a 4-page list whose session expires between every page was
  measured at 4. A real `initialize` failure gets one retry
  (`maxInitFailures = 2`); a lost leadership race gets none. Nothing here loops.
- **A cursor from an old session may be replayed on a new one** when the session
  expires mid-pagination: the retry re-sends the same `nextCursor` under the
  fresh session. MCP cursors are opaque, and every JIVO backend derives them from
  the tool list rather than from session state, so at worst a page is repeated —
  which the merge's duplicate-name drop already nets out. A backend that rejects
  a foreign cursor fails the refresh, which keeps the last complete list.

## Deploy (docker compose, sixth service)

Add alongside the five existing MCP services. The gateway needs no credentials
and no backend env — the compiled defaults are the compose service names.

```yaml
  gateway:
    image: alpine:3.20
    container_name: jivo-mcp-gateway
    restart: unless-stopped
    volumes:
      - ./bin/jivo-gateway:/usr/local/bin/jivo-gateway:ro
    command: ["jivo-gateway", "--addr", ":7700"]
    networks: [jivo-mcp]
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:7700/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.jivo-gateway.rule=Host(`<host>`) && PathPrefix(`/<secret-base>/jivo`)"
      - "traefik.http.routers.jivo-gateway.entrypoints=websecure"
      - "traefik.http.routers.jivo-gateway.tls.certresolver=<resolver>"
      - "traefik.http.routers.jivo-gateway.middlewares=jivo-gateway-strip"
      - "traefik.http.middlewares.jivo-gateway-strip.stripprefix.prefixes=/<secret-base>/jivo"
      - "traefik.http.services.jivo-gateway.loadbalancer.server.port=7700"
```

Notes for whoever deploys this:

- `--addr :7700`, **not** `127.0.0.1:7700` — Traefik reaches the container
  across the bridge network and a loopback bind is unreachable.
- Copy the Traefik label block from an existing service in
  `/opt/jivo-mcp/docker-compose.yml` and change only the router/middleware/
  service name, the `PathPrefix` leaf (`/<secret-base>/jivo`), the matching
  `stripprefix` value and the port. The host and the secret path base are **not**
  written down in this repo on purpose.
- Check Traefik's `respondingTimeouts` is above the gateway's 120s
  `--call-timeout`, or slow SAP queries will be cut off at the proxy.
- Client URL once it is up: `https://<host>/<secret-base>/jivo/mcp`.

## Layout

```
main.go                       flags, config assembly, warmup, ListenAndServe
internal/gateway/config.go    backends, timeouts, JIVO_GW_* env
internal/gateway/rpc.go       JSON-RPC 2.0 wire types
internal/gateway/backend.go   one backend: sessions, POST, JSON + SSE parsing
internal/gateway/registry.go  merge/prefix/TTL/single-flight/status
internal/gateway/gateway.go   the MCP method whitelist, routing, gateway_status
internal/gateway/http.go      stateless streamable HTTP front (ported from postsql)
```

Tests are `httptest` only — no live network, no backend required. The fake
backend in `backend_test.go` reproduces the verified mcp-go v0.47.0 contract
(mandatory `application/json`, session header issue + enforcement, plain-text
404 on expiry, SSE-upgraded responses, `nextCursor` pagination) plus every
failure mode the gateway has to survive: a hung `initialize`, an `initialize`
that returns no session header, a permanent 400, a repeating pagination cursor,
a decoy response id, malformed tool definitions and a backend that starts
answering with zero tools.
