# jivo CLI — Build Notes

**Strictly READ-ONLY** command-line tool over the internal **Jivo Group — Control Panel**
Django ERP/analytics dashboard (`http://103.89.45.75:9080`, internal HTTP, live
production). Generated with `cli-printing-press` v4.24.0 + hand-wired Django session auth.

- Spec: `~/software/cli/jivo-spec.yaml`
- Generated project: `~/software/cli/jivo/` (Go module `jivo-pp-cli`)
- Built binary: `~/software/cli/jivo/jivo`
- Config (session store, mode **0600**): `~/.config/jivo-pp-cli/config.toml`
- **Local only — never published.** No publish flow, no git push, no library touch.

---

## 1. Spec → endpoints

**42 read/pull endpoints** in the spec (0 write/mutating endpoints), grouped into
6 API resources + 2 HTML-page resources, plus `/realise/api/health/` used as
`health_check_path` (not a command). Every endpoint carries `auth.type: none`;
the only static header baked in is `X-Requested-With: XMLHttpRequest`
(`required_headers`). All 11 POST endpoints are **reads** and are tagged
`meta: {"mcp:read-only": "true"}`, which makes the generator route them through
the non-mutating `client.PostQueryWith*` path and annotate the command
`mcp:read-only: true`.

Every write/OTP endpoint from the recon inventory was **deliberately excluded**:
`save-targets, save-closing-remark, rate-list/save, rate-list/delete,
realise-calculator/upload, realise-calculator/order-upload, aging-remark*(+upload/clear
oil & beverages), credit-lock, credit-unlock, verify-pin, users/save, users/delete`,
the OTP-gated `/api/cogs/`, and all `export-*` binary/file endpoints. None appear
in the spec or the generated code.

## 2. Resources & commands generated

Binary invoked as `jivo <resource> <endpoint>`. 42 endpoint-backed read commands:

| Resource | Commands |
|---|---|
| `sales` (13) | `data` `cn` `hidden` `flow` `flow-open-items` `dispatch` `compare-docs` `drill-down` `historical` `beverages` `beverages-docs` `channel-docs` `pulse` |
| `targets` (5) | `list` `flex` `segment` `nodes` `channel` |
| `oih` (4) | `breakdown` `summary` `rows` `commodity-rows` |
| `accounts` (5) | `aging-oil` `aging-mart` `aging-beverages` `open-payments` `claims` |
| `masterdata` (3) | `customer-master` `rate-list` `calculator-items` |
| `inventory` (9) | `stock` `non-moving` `non-moving-drill` `production-fg-list` `production-warehouses` `production-feasibility` `daily-production` `reconciliation` `reconciliation-ledgers` |
| `users` (2) | `list` `catalog` |
| `credit` (1) | promoted top-level `jivo credit` (required-limit page) |

Plus hand-wired **`auth`** group: `login` / `status` / `logout`.

The 2 pages with no JSON API (`credit required-limit`, `users list`/`catalog`) are
modeled as `response_format: html` + `html_extract.mode: embedded-json` with custom
`script_selector`s (`script#credit-data`, `script#um-users`, `script#um-catalog`).
The embedded-json extractor worked as-is on the live pages — **no fallback to plain
HTML was needed**.

`--category`: task said `analytics`, but the generator rejects it (not in its enum).
Used `sales-and-crm` (cosmetic; local-only, never published).

## 3. Auth wiring (Django session, hand-wired, durable across `generate --force`)

Two durable hand-authored files the generator never emits (preserved verbatim on
regen) plus one AST-merge-preserved registration edit:

- **`internal/client/jivo_headers.go`** — single source of truth for the session
  header set. `SessionHeaders(sid, csrf)` returns
  `Cookie: sessionid=…; csrftoken=…`, `X-CSRFToken: <csrf>`, `X-Requested-With:
  XMLHttpRequest`. `AllowInsecureBase()` permits plain HTTP for the internal host
  `103.89.45.75` (and loopback) past the https guard.
- **`internal/cli/jivo_login.go`** — the `auth` command group. `login` ports the
  verified recon flow (`recon/login.sh`): `GET /accounts/login/` (cookie jar +
  scrape `csrfmiddlewaretoken`) → `POST /accounts/login/` form-urlencoded with
  `Referer`/`Origin` → expects **HTTP 302 + `sessionid`**. It writes the session +
  the `[headers]` table (from `SessionHeaders`) to the config file, mode **0600**.
- **`internal/cli/root.go`** — one added line `rootCmd.AddCommand(newAuthCmd(flags))`
  (AST-merge-preserved on `--force`).

**Injection mechanism (zero edits to generated client/config):** the generated
client's `do()` sets every entry of `Config.Headers` on each request. Login persists
`Cookie` + `X-CSRFToken` + `X-Requested-With` into the config file's `[headers]`
table, which the generated `config.Load` reads straight into `Config.Headers`. So
every read command authenticates transparently. `X-Requested-With` is also baked in
via `required_headers`.

**Credential resolution** (login): `--username/--password` → `JIVO_USER`/`JIVO_PASS`
env → `~/software/.env` (`JIVO_USER=preshit`, `JIVO_PASS=…`). Password is never
written to disk or logged; only the session tokens are persisted. Verify/dry-run
short-circuits before any network call (won't touch live prod).

## 4. Build

`go build ./...` and `go build -o ./jivo ./cmd/jivo-pp-cli` — **clean**.
`go vet ./...` clean. `gofmt -l` clean on hand-authored files + root.go.
(`--validate` at generation tripped only on `govulncheck`: Go stdlib advisory
GO-2026-5856 in crypto/tls, fixed in go1.26.5 — irrelevant here; this CLI talks
plain HTTP to an internal host and calls no TLS. Not a code defect.)

## 5. Smoke test — LIVE, read-only, single-day ranges (all real)

`jivo auth login` → `Logged in as preshit — session saved to
~/.config/jivo-pp-cli/config.toml` (file mode `-rw-------` / 0600). Then:

| Command | Result (HTTP success + top-level JSON keys) |
|---|---|
| `targets list --month 7 --year 2026` | `status:"ok"`, `month:7`, `year:2026`, `data{16}` (e.g. `PREMIUM\|OLIVE {tgt_ltrs:310000,tgt_rate:253}`) |
| `sales data --start-date 2026-07-22 --end-date 2026-07-22` | POST **200**, `success:true`, `data{5}` (status/data/count/channel_rows/channel_month_rows) |
| `masterdata customer-master` | `status:"ok"`, `rows[1167]`, `count:1167` |
| `inventory stock --schema jivo_oil` | `data{3}` (warehouses/products/items) |
| `credit` (required-limit, HTML embedded-json) | `as_of:"2026-07-23"`, `asms[12]`, `lock`, `total{2}` |
| `users list` (HTML embedded-json) | `array[2]` users (email/groups/realise_role/…) |
| `users catalog` (HTML embedded-json) | `module_perms[5]`, `page_perms[16]`, `realise_roles[4]` |
| `oih summary` (post-rebuild) | `status:"ok"`, `data{11}` salesperson buckets |

**Auth-injection proof (negative test):** the same endpoint with an empty config
returns `HTTP 401 {"error":"Authentication required"}`. Authenticated reads only
succeed because the Cookie + X-CSRFToken + X-Requested-With injection is working.

## 6. Read-only audit — **PASS**

Mechanical audit of every endpoint-backed command's `pp:method`/`pp:path`/read-only
annotations:

- **42** endpoint commands: **31 GET + 11 read-only POST**. Every one carries
  `mcp:read-only: true`.
- The 11 POSTs are exactly the read-data endpoints (sales data/cn/hidden/flow/
  flow-open-items/dispatch/compare-docs/drill-down/historical/beverages,
  accounts/open-payments) — all routed through the non-mutating `PostQueryWith*`.
- **0** unmarked-mutating commands. **0** banned-path commands (no
  save/delete/upload/lock/verify-pin/cogs/export).
- Whole-package grep for mutating client calls (`c.Post/Put/Delete/Patch`) found a
  **single** hit: the generator's generic `import` command (`import.go` `c.Post`).
  It was **unregistered** from the command tree (root.go) so it is absent from both
  the CLI and MCP surfaces. `sync` and `workflow archive` are GET-only into a local
  SQLite (read-only w.r.t. the ERP).
- The only POST commands in the tree are the 11 read-data endpoints + `auth login`
  (Django session establishment, `mcp:hidden`). Confirmed: `jivo import --help` →
  absent.

## 7. Gaps / TODOs

- **Session-expired wording.** An expired/absent session surfaces as the generated
  client's `HTTP 401` (or an HTML/redirect body) error with a generic hint
  ("check your API credentials / Run doctor"). It does **not** emit the exact
  "re-run `jivo auth login`" wording (that would require editing the generated
  client error path). Behavior is correct; only the hint text differs.
- **`generate --force` re-apply.** The `import` removal and the `newAuthCmd`
  registration are hand-edits to generated `root.go`. `--force` uses AST merge to
  preserve hand-edits, but if a future regen re-adds `import`/drops the auth line,
  re-apply both (novel files `jivo_login.go` / `jivo_headers.go` are always
  preserved verbatim).
- **`doctor` health probe.** `health_check_path` is `/realise/api/health/`, which
  needs the session cookie; `doctor` sends `X-Requested-With` but not the stored
  Cookie, so its health check may report unauth. Reads are unaffected (they carry
  the full `[headers]` set). Not wired further to stay in scope.
- **`drill-down` `filters`.** Modeled as an object body property → a `--filters`
  JSON-string flag (per spec-format). Not exercised in the smoke test.
