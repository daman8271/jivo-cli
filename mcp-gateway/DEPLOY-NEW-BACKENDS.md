# Deploying the exim + jsap MCP backends

Written 2026-08-10. Adds two read-only backends to the `/opt/jivo-mcp` stack on
the fleet VPS and repoints the unified gateway at them.

|  | exim | jsap |
|---|---|---|
| compose service | `exim` | `jsap` |
| internal port | **7707** | **7711** |
| gateway prefix | `exim_` | `jsap_` |
| gateway `StripPrefix` | *(none)* | `jsap_` |
| tools | 11 | 10 |
| upstream | `https://eximbe.jivo.in` | `http://103.89.45.75:5001` |
| secret file | `env/exim/config.toml` | `env/jsap/.env` |

Everything below is read-only against JIVO's business systems. The gateway holds
no credential of its own; the two new services do, and those live only in the
files named here.

---

## 0. Before you start

Read `/opt/jivo-mcp/docker-compose.yml` and copy two literals out of a
neighbouring service into the blocks below:

- the Traefik **Host** rule value, and
- the **path base** — the secret prefix each router strips. It is written here
  as `<PATHBASE>`, following the placeholder convention the compose file's own
  header uses. Do not invent it; lift it verbatim from the `factory` or `hana`
  service so all routers stay on one base.

Nothing else in the file changes. The two blocks are appended alongside the
existing services, and the `networks:` stanza at the bottom is left as is.

---

## 1. Binaries to rsync

Built locally for `linux/amd64`, static, from
`/Users/damanpreetsingh/jivo-cli/mcp-gateway/bin/`:

```bash
cd /Users/damanpreetsingh/jivo-cli/mcp-gateway/bin

# Back up what is live before overwriting the gateway (the two new ones are new).
ssh vps 'cp -a /opt/jivo-mcp/bin/jivo-gateway /opt/jivo-mcp/bin/jivo-gateway.prev'

rsync -av --chmod=0755 \
  exim-mcp.linux-amd64      vps:/opt/jivo-mcp/bin/exim-mcp
rsync -av --chmod=0755 \
  exim-pp-cli.linux-amd64   vps:/opt/jivo-mcp/bin/exim-pp-cli
rsync -av --chmod=0755 \
  jsap-mcp.linux-amd64      vps:/opt/jivo-mcp/bin/jsap-mcp
rsync -av --chmod=0755 \
  jivo-gateway.linux-amd64  vps:/opt/jivo-mcp/bin/jivo-gateway
```

`exim-pp-cli` is not optional. Six of exim's eleven tools (`analytics`, `sync`,
`tail`, `workflow`, `workflow_archive`, `workflow_status`) are Cobra-tree mirrors
that **shell out** to the companion CLI — the same arrangement `ecom` already
has with `jivo-ecom-pp-cli`. Without it those six fail at call time with
"companion CLI binary not found", while `tools/list` still looks perfectly
healthy.

The gateway binary must ship in the same pass: the old one has no `exim_` or
`jsap_` prefix compiled in and will never route to either service.

---

## 2. Secret files — VARIABLE NAMES ONLY

Create the two directories and populate the files **on the VPS**. Values are not
in this repo and must not be pasted into it, into a commit, or into a terminal
transcript. Refer to them by name.

### `/opt/jivo-mcp/env/exim/config.toml`

TOML, not dotenv — `exim-pp-cli` and the MCP server both read
`$HOME/.config/exim-pp-cli/config.toml`. Keys, from
`exim/cli/exim-pp-cli/internal/config/config.go`:

| key | required | note |
|---|---|---|
| `base_url` | recommended | `https://eximbe.jivo.in`; the compiled default is the same, so it is documentation |
| `token` | **yes** | the EXIM JWT. `EXIM_TOKEN` in the process environment overrides it |
| `auth_header` | no | pre-formed `Authorization` value; wins over `token` if present |
| `access_token` / `refresh_token` / `token_expiry` | no | OAuth trio, only if the OAuth flow is used instead of a bare JWT |
| `client_id` / `client_secret` | no | OAuth only |

Environment alternatives the container honours: `EXIM_TOKEN`, `EXIM_BASE_URL`,
`EXIM_CONFIG` (config path), `EXIM_CLI_PATH` (companion CLI path).

### `/opt/jivo-mcp/env/jsap/.env`

Dotenv, `KEY=VALUE`, one per line — the same shape and mount arrangement `sapb1`
uses. Keys, from `jsap-mcp/internal/jsap/config.go`:

| key | required | note |
|---|---|---|
| `JSAP_URL` | no | defaults to `http://103.89.45.75:5001` |
| `JSAP_USERNAME` | **yes** | |
| `JSAP_PASSWORD` | **yes** | |
| `JSAP_USER_ID` | no | defaults to `68`, the shared gateway identity |

`jsap-mcp` starts **without** credentials on purpose — it warns on stderr and
serves `tools/list`, so a missing `.env` shows up as failing tool *calls*, not as
a container that will not boot. Do not read a healthy `docker compose ps` as
proof the credentials landed; use the verification in §5.

```bash
ssh vps 'mkdir -p /opt/jivo-mcp/env/exim /opt/jivo-mcp/env/jsap && chmod 700 /opt/jivo-mcp/env/exim /opt/jivo-mcp/env/jsap'
# then create the two files on the box, chmod 600, values never echoed
```

---

## 3. The compose service blocks

Append both to `services:` in `/opt/jivo-mcp/docker-compose.yml`.

```yaml
  # EXIM — imports/exports (licences, shipments, tanks, stock status).
  # READ-ONLY: the generated OpenAPI spec contains zero write operations and the
  # HTTP client refuses any non-GET, so this container cannot mutate EXIM.
  exim:
    image: alpine:3.20
    restart: unless-stopped
    working_dir: /srv
    # -transport/-addr are BOTH required: the binary defaults to stdio on :7777.
    command: ["/srv/exim-mcp", "-transport", "http", "-addr", ":7707"]
    volumes:
      - ./bin/exim-mcp:/srv/exim-mcp:ro
      # Six of the eleven tools shell out to the companion CLI. Resolution order
      # is sibling-of-executable, then $EXIM_CLI_PATH, then PATH — /usr/local/bin
      # is on PATH in alpine, matching how ecom mounts jivo-ecom-pp-cli.
      - ./bin/exim-pp-cli:/usr/local/bin/exim-pp-cli:ro
      # exim-pp-cli config path: $HOME/.config/exim-pp-cli/config.toml ($HOME=/root).
      - ./env/exim/config.toml:/root/.config/exim-pp-cli/config.toml:ro
    networks: [traefik]
    labels:
      - traefik.enable=true
      - traefik.http.routers.jivo-exim.entrypoints=websecure
      - traefik.http.routers.jivo-exim.tls.certresolver=letsencrypt
      - traefik.http.routers.jivo-exim.rule=Host(`<HOST>`) && PathPrefix(`/<PATHBASE>/exim`)
      - traefik.http.routers.jivo-exim.middlewares=jivo-exim-strip
      - traefik.http.middlewares.jivo-exim-strip.stripprefix.prefixes=/<PATHBASE>/exim
      - traefik.http.services.jivo-exim.loadbalancer.server.port=7707

  # JSAP — JIVO's internal ops platform (budget approvals, tickets, tasks, org
  # hierarchy, Document Hub, inventory audits).
  # READ-ONLY: jsap_execute dispatches by catalogued command id only — it accepts
  # no URL and no path — and the write-shaped surfaces are excluded from the
  # catalogue, not merely undocumented.
  jsap:
    image: alpine:3.20
    restart: unless-stopped
    working_dir: /srv
    # --addr IS NOT OPTIONAL. jsap-mcp's compiled default is :7707, which is
    # exim's port; omit the flag and the two services race for it. See the trap
    # in §6.
    command: ["/srv/jsap-mcp", "--transport", "http", "--addr", ":7711"]
    volumes:
      - ./bin/jsap-mcp:/srv/jsap-mcp:ro
      # jsap-mcp loads .env from cwd AND from the directory holding the binary;
      # /srv is both, so this single mount satisfies it (same shape as sapb1).
      - ./env/jsap/.env:/srv/.env:ro
    networks: [traefik]
    labels:
      - traefik.enable=true
      - traefik.http.routers.jivo-jsap.entrypoints=websecure
      - traefik.http.routers.jivo-jsap.tls.certresolver=letsencrypt
      - traefik.http.routers.jivo-jsap.rule=Host(`<HOST>`) && PathPrefix(`/<PATHBASE>/jsap`)
      - traefik.http.routers.jivo-jsap.middlewares=jivo-jsap-strip
      - traefik.http.middlewares.jivo-jsap-strip.stripprefix.prefixes=/<PATHBASE>/jsap
      - traefik.http.services.jivo-jsap.loadbalancer.server.port=7711
```

The gateway reaches both by compose service name on the `jivo-mcp` bridge —
`http://exim:7707/mcp` and `http://jsap:7711/mcp` — which is exactly what is
compiled into `DefaultBackends()`. The Traefik labels are only for reaching a
backend *directly*, the way `hana` and `factory` can be; the unified endpoint
needs none of them.

Neither service needs a `-allow-host` flag. That is a `hana-sql` defence
(it rejects any non-loopback `Host`, so the compose stack has to allow
`hana:7706` explicitly); mcp-go's streamable HTTP server has no such check.

---

## 4. Bring it up

```bash
ssh vps 'cd /opt/jivo-mcp && docker compose up -d --force-recreate exim jsap gateway'
```

`gateway` is in that list because its binary changed. Leave it out and the stack
comes up with two healthy new backends that nothing routes to.

---

## 5. Verify — a tool call, not just a 200

`initialize` returns 200 from a server with dead credentials. That is how the
factory backend served HTTP 401 unnoticed for ten days (2026-07-24 → 08-03), and
it is why the check below asks the gateway what it can actually see.

```bash
U="https://<HOST>/<PATHBASE>/jivo/mcp"

# 1. Both backends up, with their tool counts.
curl -s --max-time 30 -X POST "$U" \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"gateway_status","arguments":{}}}'
```

Expected: eight backends, `backends_up` `8/8`, `exim` contributing **11** tools
and `jsap` **10**. A backend that is up with 0 tools is a half-booted container,
not a success.

```bash
# 2. A real read through each new prefix.
#    exim_context and jsap_context are the cheapest live calls; both are
#    read-only and take no arguments.
... "params":{"name":"exim_context","arguments":{}}
... "params":{"name":"jsap_context","arguments":{}}
```

`isError: true` on either one after a healthy `tools/list` means the credentials
file did not land, or landed stale — go to §6.

Also confirm the names came through un-mangled:

- exim advertises `exim_search` **and** `exim_exim_search` — both, distinctly.
  Only one of them appearing means someone set `StripPrefix` on exim; that
  collides the two names and mis-routes the other nine tools. exim strips
  nothing, by design.
- jsap advertises `jsap_context`, never `jsap_jsap_context`.

---

## 6. Traps

**Env files are SINGLE-FILE bind mounts.** `./env/jsap/.env` and
`./env/exim/config.toml` are mounted as individual files, not directories. An
in-place edit with `sed -i` does not rewrite the file — it writes a new one and
renames it over the old — so the inode the running container is bound to is the
*old* one, and the process keeps serving stale values while the file on disk
looks correct. `docker compose restart` is not a reliable fix for this.

> **Rule: after touching anything under `env/`, use
> `docker compose up -d --force-recreate <service>` — never `restart`.**

Force-recreate destroys and rebuilds the container, so the mount is re-established
against the current inode. The corrections digest avoids the whole problem by
mounting the *directory* (`./corrections:/srv/corrections:ro`) instead; the
credential files cannot do that without exposing the neighbouring `.prev` and
`.bak` copies, so they pay for it with `--force-recreate`.

**jsap's compiled default port is 7707 — exim's.** `jsap-mcp`'s source predates
the port assignment and defaults to `:7707`. The explicit `--addr :7711` in the
service block is load-bearing. If jsap is ever run without it, the two containers
both try to serve 7707 on their own network namespaces and Traefik's
`loadbalancer.server.port` sends jsap traffic nowhere.

**A missing credential file is not a boot failure.** Both servers start, answer
`tools/list`, and fail only at call time. `docker compose ps` showing `Up` proves
nothing about credentials.

**exim's token is mounted read-only.** If EXIM's JWT expires, the CLI cannot
refresh it in place — the mount is `:ro` and the container is not the right place
to hold a refresh loop anyway. `ecom`, `oms` and `factory` solve this with
rotation scripts in `mcp-gateway/bin/rotate_*_mcp_token.py`. **There is no
`rotate_exim_mcp_token.py` yet.** Until there is, an expired EXIM token shows up
as every `exim_*` tool erroring while `gateway_status` reports the backend up —
plan for that or write the rotator.

**Rollback.** The gateway is the only binary being replaced:

```bash
ssh vps 'cd /opt/jivo-mcp && mv bin/jivo-gateway.prev bin/jivo-gateway && \
  docker compose up -d --force-recreate gateway'
```

The old gateway simply does not know about `exim` or `jsap`; the two new services
can be left running, or stopped with `docker compose stop exim jsap`.

---

## What was verified, and what was not

Verified before writing this:

- Both upstreams are reachable **from the VPS**: TCP to `eximbe.jivo.in:443` and
  `103.89.45.75:5001` both connect; HTTP `404` and `200` respectively (an
  unauthenticated liveness probe, no business call).
- No process on the VPS is listening on `:7700–:7719`, so neither port collides
  with something already published.
- The cross-compiled gateway embeds `http://exim:7707/mcp` and
  `http://jsap:7711/mcp` (checked with `strings` on the ELF).
- The env-file **key names** above come from the two config loaders' source, not
  from reading any live credential file.

**Not** verified — these need the deploy itself:

- That the containers can reach the upstreams (host reachability is not container
  reachability; `jivo-mcp` is a user-defined bridge with its own routing).
- That the mounted credentials are valid. No authenticated call was made.
- That Traefik routes the two new PathPrefixes — the labels follow the existing
  services exactly, but the router only exists once compose applies them.
- The exact live tool count per backend. The 11 and 10 above are the counts each
  server *registers* in source; a backend that fails to build a tool at runtime
  would report fewer, which is precisely what §5 checks.
