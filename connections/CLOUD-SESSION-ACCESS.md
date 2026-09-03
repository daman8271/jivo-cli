# Claude Code CLOUD sessions (claude.ai/code, the iPad) → JIVO systems

*Built and verified 2026-09-03. The cloud sandbox cannot SSH, ever; it can only
speak HTTPS to hostnames its environment allows. So SAP is published as HTTPS
on the VPS, and the environment is told to allow it. Two halves, both needed.*

## 1 · What the sandbox actually is (measured from inside, 2026-09-03)

| Probe | Result | Meaning |
|---|---|---|
| `187.127.129.132:22` (VPS SSH) | refused | the SSH-tunnel plan is dead |
| `138.252.101.222:50000` (SAP direct) | refused | as expected |
| `/dev/tcp` to any host `:443` | "OPEN" | **meaningless** — the proxy accepts every handshake, then decides |
| `curl https://jivo-mcp.srv1685505.hstgr.cloud/` | `CONNECT tunnel failed, response 403` | the real answer: host not on the allowlist |
| `command -v ssh` | none | no client either |
| `env` | `HTTPS_PROXY=http://127.0.0.1:42179`, `CCR_AGENT_PROXY_ENABLED=1` | all egress via one CONNECT proxy |

Anthropic's own docs (`code.claude.com/docs/en/cloud-environments`): every
environment has a **Network access** level — `None` / `Trusted` (package
registries + GitHub) / `Full` / `Custom` (your own domain list). GitHub goes
through its own proxy regardless. Nothing a prompt can do inside the session
changes the level; it is a setting on the claude.ai account that owns the
environment.

## 2 · The door: SAP Service Layer over HTTPS 443

```
cloud sandbox ──CONNECT proxy──> https://sl-14fce609.srv1685505.hstgr.cloud (VPS Traefik, Let's Encrypt)
                                   └─> 127.0.0.1:45000 on the VPS  (the SAP box's own reverse tunnel)
                                         └─> Service Layer :50000 on hanadb 138.252.101.222
```

- Config: `connections/cloud-session/sap-sl.traefik.yml` = `/docker/traefik/dynamic/sap-sl.yml`
  on the VPS (Traefik's file provider watches the directory; copying the file is
  the deploy). **Rollback:** `ssh vps rm /docker/traefik/dynamic/sap-sl.yml`.
- Gates: tokenized hostname (obscurity — Let's Encrypt logs it in CT) → SAP's
  own login → 20 req/s per source IP. Nothing answers without `SAPB1_USER` /
  `SAPB1_PASSWORD`, which the private repo carries in `sap-b1/cli/.env`.
- Verified from a home IP 2026-09-03: `sapb1 doctor --host sl-14fce609.srv1685505.hstgr.cloud --port 443`
  → login OK; `BusinessPartners --count` Oil 3,424 / Mart 2,192 / Bev 2,974;
  `--all --page-size 200` (18 pages) in 4.4 s, so the rate limit never bites
  normal paging.
- **The sapb1 binaries were rebuilt the same day to honour `HTTPS_PROXY`**
  (`internal/client`: `Proxy: http.ProxyFromEnvironment`). Proven with a local
  CONNECT proxy: the new binary tunnels through it and *fails* when the proxy is
  dead; the old binary bypassed the proxy entirely — which is exactly why it
  could never work in the sandbox. A checkout older than 2026-09-03 will say
  "cannot reach SAP Service Layer" in the cloud: `git pull`.
- The read-only **MCP gateway** (75 tools: ecom, oms, factory, exim, postsql,
  hana, sapb1) was already on the same wildcard host —
  `https://jivo-mcp.srv1685505.hstgr.cloud/<pathbase>/jivo/mcp` — so one
  allowlist line opens both. The path base is in
  `mcp-gateway/bin/deploy-factory-mcp.sh`.

## 3 · The setting (2 minutes, once per environment)

**Personal environment (Pro / Max account):** claude.ai/code → the environment
selector (cloud icon beside the task box) → hover the environment → settings icon
→ *Update cloud environment*:

1. **Network access → Custom.** Allowed domains, one per line:
   ```
   *.srv1685505.hstgr.cloud
   ```
   Tick **Also include default list of common package managers** (keeps npm,
   PyPI, GitHub raw). `Full` also works; Custom is the tighter choice.
2. **Environment variables** (visible to anyone using the environment — hostnames
   are not secrets; the SAP password stays in the repo's `.env`, never here):
   ```
   SAPB1_HOST=sl-14fce609.srv1685505.hstgr.cloud
   SAPB1_PORT=443
   ```
   Real environment variables beat the `.env` file (config.go precedence), so
   every `sapb1` call in the session lands on the door with no flags.
3. Save, then **start a new session** — a running VM keeps the level it booted with.

**Team organisation (the Alise Team plan the operators sit under):** only an
**Owner** can do it, and does it once for everyone: claude.ai/admin-settings →
*Cloud environments* → create a shared environment with the same three fields →
claude.ai/admin-settings/claude-code → make it the default. Members see it
read-only in their selector. There is no org-level allowlist that pushes into
members' personal environments (docs, verified).

## 4 · The verification prompt (paste into a NEW cloud session, verbatim)

```
Run this exactly as one bash block and paste the raw output, nothing summarised:

echo "=== env"; env | grep -E '^SAPB1_(HOST|PORT)=' || echo "  SAPB1_HOST/PORT NOT SET -> the environment variables step was skipped"
echo "=== door"; curl -sS -o /dev/null --max-time 20 -w "  HTTP %{http_code}  (401 = the door is open; 000 = domain still not allowed)\n" https://sl-14fce609.srv1685505.hstgr.cloud/b1s/v1/
echo "=== gateway"; PB=$(grep -o 'mcp-[0-9a-f]\{20\}' mcp-gateway/bin/deploy-factory-mcp.sh | head -1); curl -sS -o /dev/null --max-time 20 -w "  HTTP %{http_code}  (200 = 75 read tools reachable)\n" -X POST "https://jivo-mcp.srv1685505.hstgr.cloud/$PB/jivo/mcp" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}'
echo "=== sapb1"; cd sap-b1/cli && ./sapb1.linux doctor && for c in JIVO_OIL_HANADB JIVO_MART_HANADB JIVO_BEVERAGES_HANADB; do printf "  %-24s BPs: " $c; ./sapb1.linux query BusinessPartners --count --company $c; done

Then tell me in one line whether all three companies answered.
```

Expected when everything is in place: `HTTP 401`, `HTTP 200`, three green
doctor ticks, and three counts (Oil 3,424 / Mart 2,192 / Bev 2,974 on 09-03).
`CONNECT tunnel failed, response 403` on the door = §3 step 1 not done. Doctor
green but counts erroring = the checkout predates the proxy-aware rebuild.

## 5 · Optional fourth gate (cloud-only door)

The environment editor's **API credentials** attach a header to requests for a
host *outside* the sandbox — the value never enters the VM. Host
`sl-14fce609.srv1685505.hstgr.cloud`, custom header `X-Jivo-Key`, any long
random value; then append `&& Header(`X-Jivo-Key`, `<that value>`)` to the
router rule in `sap-sl.traefik.yml` and redeploy. Cost: the door then answers
**only** cloud sessions of environments carrying that credential — the Mac
check in §2 stops working (test via `ssh vps` on loopback instead), and on the
Team plan only an Owner can add it. Not enabled by default for that reason.

## 6 · What still does not work from the cloud, and why

- **SSH, in any form.** HTTP-only proxy, port 22 refused, no client. `Full`
  network access has not been tested for port-22 CONNECT; assume no.
- **HANA raw SQL (30015) and Postgres (5432)** — not HTTP-shaped, so
  `hana-sql/` and `postsql/` CLIs cannot pass. Use the gateway's `hana_*` /
  `pg_*` tools. `jolly/engine/freeze_sep.py` uses the HANA CLI, so a re-freeze
  is still a laptop/VPS job.
- **Vercel deploys** need `*.vercel.app`, `vercel.com`, `api.vercel.com` on the
  allowlist plus a token — untested. `engine/refresh.sh` stays a VPS job.
- **Writes go through the door too.** `sapb1 draft / post / patch / delete draft`
  all work over it; RULE 0 in the root CLAUDE.md applies unchanged, and the write
  log lands in the session's branch, not on `main`, until merged.

## 7 · Why not a GitHub courier

GitHub is reachable from every level, so "cloud pushes a request file, VPS cron
answers, cloud polls" would work with no setting at all. It was not built: the
setting takes two minutes, the courier adds a minute of latency per question and
a second moving part, and it would not have made `sapb1` itself work.
