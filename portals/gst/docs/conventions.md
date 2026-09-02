# House conventions for a new JIVO portal CLI (spec for `portals/gst/cli`)

Evidence read: root `README.md`, `NEW-DEVICE.md`, `CLI-HUB-README.md`, `portals/{tankhapay,blinkit,zepto,amazon,flipkart,swiggy-instamart}`, `dsr-cli/`, `sap-b1/cli/`, `mcp-gateway/`, `harness/`, root `.gitignore`, `.claude/settings.json`. All paths below are under `/Users/damanpreetsingh/jivo-cli/`.

One correction to the task framing first: **`portals/tankhapay/` is NOT tracked in the repo** — root `.gitignore:73-75` ignores it entirely (removed 2026-07-31 because its creds leaked). It is still the best *code* precedent (headless login + token cache), but the tracked, canonical portal precedents are `portals/blinkit/cli`, `portals/zepto/cli`, `portals/amazon/cli` (cookie-jar session — closest to GST) and `dsr-cli/` (MCP + guard tests).

---

## 1. Language, packaging, invocation

| Convention | Evidence |
|---|---|
| **Go + cobra, stdlib only** (no other deps) for every portal CLI. | `portals/tankhapay/cli/go.mod:1-6` (cobra only); `portals/zepto/cli/README.md:86` "stdlib + cobra only"; `portals/blinkit/cli/main.go:1-3` |
| Flat `package main` in `portals/<name>/cli/`, one `cmd_<section>.go` per portal section, self-registering via `init() → registerSection(...)`; `root.go` never edited when a section is added. | `portals/zepto/cli/registry.go:5-15`; `portals/tankhapay/cli/registry.go:5-12`; `portals/zepto/cli/cmd_po.go:5` |
| Root command sorts section groups alphabetically and always adds `doctor` + `auth` first. | `portals/zepto/cli/root.go:44-53`; `portals/tankhapay/cli/root.go:43-52` |
| `main.go` is 3 lines: `newRootCmd().Execute()`, error → `error: …` on stderr, `os.Exit(1)`. `SilenceUsage/SilenceErrors: true`. | `portals/zepto/cli/main.go:18-23`; `root.go:23-24` |
| Binary name = `<portal>-portal` (`blinkit-partner` is the one outlier). Built in-place: `go build -o <name> .` (mac) / `go build -o <name>.exe .` (Windows). Docs say "On Windows run `x.exe` wherever this says `./x`". | `portals/zepto/cli/README.md:46-63`; `dsr-cli/README.md:28-33`; `portals/tankhapay/cli/README.md:14-18` |
| **Operators cannot build Go — ship the binaries.** `sapb1`, `dsr`, `dsr.exe`, `blinkit-partner(.exe)`, `zepto-portal(.exe)` are tracked in git; the `.exe` is deliberately tracked because office PCs run it straight from a pull. (amazon/flipkart/swiggy ignore their binary — that is the newer, inconsistent pattern; follow sap-b1/dsr/blinkit/zepto and ship it.) | `sap-b1/cli/.gitignore:10-15`; `dsr-cli/.gitignore:4-5`; root `.gitignore:84-85`; `git ls-files` shows `portals/blinkit/cli/blinkit-partner.exe`, `portals/zepto/cli/zepto-portal.exe`, `dsr-cli/dsr.exe` |
| Cross-compile for Accounts laptops: `GOOS=windows GOARCH=amd64 go build -o ….exe`. Windows installer/PowerShell edits must be tested on a fleet box, nothing local can. | `NEW-DEVICE.md:65-69`; memory `no-powershell-on-fleet` |
| Go version: cobra CLIs use `go 1.23`–`1.26.1`; repo expects ≥1.25.5 to rebuild. | `portals/tankhapay/cli/go.mod:3`; `dsr-cli/go.mod:3`; `NEW-DEVICE.md:15` |

**For GST:** `portals/gst/cli/` → binary `gst-portal` + `gst-portal.exe`, both committed.

## 2. Credentials

| Convention | Evidence |
|---|---|
| Precedence: **flag > env var > `.env` > built-in default**. Env always wins over `.env`. There is intentionally **no `--password` flag**. | `sap-b1/cli/README.md:61-75`; `portals/tankhapay/cli/config.go:33-42` |
| `.env` lives at the **portal root** (`portals/<name>/.env`, mode 0600), gitignored; search order: `$<PREFIX>_ENV` → `./.env` → `../.env` → `<exe dir>/.env` → `<exe dir>/../.env` → `~/jivo-cli/portals/<name>/.env`. dsr adds `~/.dsr/.env`. Loader is a 25-line hand parser (`export` prefix, `#` comments, quote-strip), never a library. | `portals/tankhapay/cli/config.go:75-125`; `dsr-cli/internal/config/config.go:44-91` |
| Env-var prefix is the portal's uppercase short name: `TPAY_*`, `DSR_*`, `BLINKIT_*`, `ZEPTO_*`, `AMAZON_SC_*`. GST already uses `GST_NN_STATE/GSTIN/USER/PASS` blocks — keep that. | `portals/tankhapay/.env.example:1-7`; `dsr-cli/README.md:34-36`; `portals/gst/.env.example:5-8` |
| Credentials are **never defaulted / never in the binary**; missing creds fail closed with an actionable message naming the vars. | `dsr-cli/internal/config/config.go:34-35,129-133`; `portals/tankhapay/cli/config.go:62-64` |
| Ship a **`.env.example`** with placeholders. **TRAP:** root `.gitignore:12,20` (`.env*`, `*.env.*`) swallows `.env.example` — `dsr-cli/.env.example` is untracked for exactly this reason. `portals/gst/.gitignore:4` already has `!.env.example`, and `git check-ignore` confirms it is un-ignored. Keep that line. | `git check-ignore -v` output; `portals/gst/.gitignore:1-8` |
| Multi-entity selector is a `--company`/alias flag with a fixed map and "unknown value is a clear error". For GST this is the 8-GSTIN selector (`--gstin 06AACCJ4223F1Z0` or `--state haryana`). | `portals/blinkit/cli/root.go:10-18,39-42`; `portals/swiggy-instamart/cli/config.go:56-60` |
| Per-operator named env files exist for SAP only (`sap-b1/cli/lovepreet-veerji.env`); portal CLIs use one shared `.env`. All env files also live in the private `env-vault/` submodule, `all-env.txt`. | `ls sap-b1/cli`; `NEW-DEVICE.md:185-193` |
| `doctor` prints creds **masked** (`s[:4]+"…"+s[-4:]`), never the secret. | `portals/blinkit/cli/doctor.go:106-114` |

## 3. Commands, flags, output, exit codes

| Convention | Evidence |
|---|---|
| Shape: `<binary> <section-group> <leaf> [flags]`, kebab-case, groups mirror the portal's own menu sections; `doctor`, `auth login|whoami|status` always present. Path-templated ids are positional (`po get <po_id>`); list filters are flags (`--from --to --limit --offset`) or raw `--query "k=v"` / `--body '{…}'` / `--set k=v` when the shape isn't confirmed. | `portals/zepto/cli/README.md:53-85`; `portals/blinkit/cli/README.md:67-146`; `portals/tankhapay/cli/README.md:49-63` |
| Global flags on every portal CLI: `--json` (pretty JSON) and `--agent` (implies `--json`, silences stderr progress, wraps in the **stable envelope `{ok, command, endpoint, count, data|error}`**). `count` is `bestEffortCount` (top-level array, else common list keys, else 1). | `portals/zepto/cli/root.go:41-42`; `portals/zepto/cli/output.go:60-99,130-161`; `portals/blinkit/cli/output.go:38-76` |
| Default (no flag) output for portal CLIs is pretty JSON (schemas unconfirmed); SQL-style CLIs default to an aligned `tabwriter` table with `(N rows)` footer and offer `--csv --compact -q --select`. Go CLIs elsewhere also accept `--agent`. | `portals/blinkit/cli/output.go:34-37`; `dsr-cli/internal/render/render.go:25-39,95-125`; `dsr-cli/internal/cli/root.go:138-147`; root `README.md:139` |
| Progress/diagnostics go to **stderr** (`logf`), suppressed under `--agent`, so stdout stays parseable. | `portals/zepto/cli/output.go:32-36`; `sap-b1/cli/README.md:98` |
| On 401/403 every command appends one uniform `reLoginMsg` telling the operator the exact re-auth command. | `portals/zepto/cli/output.go:29,83-87`; `portals/blinkit/cli/output.go:25` |
| `doctor` = config → token/session → **one harmless live read**, with `--offline` to skip the network; emits the agent envelope under `--agent`; exits non-zero if the live read fails. | `portals/tankhapay/cli/doctor.go:10-60`; `portals/blinkit/cli/doctor.go:23-97` |
| "Deferred" endpoints (seen in UI, contract not captured) stay in the tree but return `endpoint to confirm — capture live first: …` rather than being invented. | `portals/blinkit/cli/root.go:92-97`; `portals/zepto/cli/output.go:53-58` |
| **Exit codes** (house table, from sapb1; dsr uses the same numbering for 0/1/2/5): `0` ok · `1` generic error · `2` usage · `3` config missing/invalid · `4` auth failed · `5` network/read-only guard ("nothing was sent") · `6` API error · `7` write-outcome-unknown (n/a for a read-only CLI). Implement via an `ExitCode() int` error interface mapped in `Execute()`. | `sap-b1/cli/internal/cli/exitcode.go:10-20`; `sap-b1/cli/README.md:539-549`; `dsr-cli/internal/cli/root.go:21-29,85-93,153-161` |
| **Money is INR with Indian grouping and a crore/lakh suffix**: `₹4,33,72,582.27 (4.34 Cr)`. Copy `inr()`/`groupIndian()` verbatim. Dates: `--from` inclusive / `--to` exclusive, `YYYY-MM-DD`, IST wall-clock via `time.LoadLocation("Asia/Kolkata")` with a fixed +05:30 fallback. GST period codes are `MMYYYY` (`RECON.md:28`) — accept `--period 072026` and `--fy 2026-27`. | `dsr-cli/internal/cli/domain.go:147-183`; `portals/zepto/cli/dates.go:8-18`; `dsr-cli/ASK-EXAMPLES.md:5-6` |
| `user-agent` identifies the tool: `"<name>/1.0 (read-only)"` — except where the portal WAF needs a browser UA (swiggy sets Chrome UA + Origin/Referer). GST's F5 WAF needs the browser-style headers + `Referer` (`RECON.md:18-21`). | `portals/tankhapay/cli/client.go:141-148`; `portals/swiggy-instamart/cli/config.go:43-46` |

## 4. Session / cookie / token handling for a browser-login portal

| Convention | Evidence |
|---|---|
| Two accepted models: **(a) headless login from `.env`, token cached** (tankhapay, dsr portal); **(b) consume a session minted elsewhere, never log in** (amazon, swiggy, blinkit/zepto via `~/ecomcliauto` login scripts). GST has a captcha, so it is model (a) only if captcha can be solved headlessly; otherwise a `gst-portal auth import <cookie-jar|curl>` path like amazon/blinkit. Recon D1/D10 decide this. | `portals/tankhapay/cli/auth.go:18-54`; `portals/amazon/cli/config.go:11-13,33-62`; `portals/blinkit/cli/README.md:72-73` |
| Cache location: **`os.UserConfigDir()/<binary-name>/token.json`** (mac: `~/Library/Application Support/…`, Windows `%AppData%\…`), dir 0700, file 0600, JSON `{token, cached_at}`. sapb1 caches cookies at `~/.sapb1-session.json` 0600. Cookie-jar CLIs read a Playwright-style `[{name,value,domain}]` JSON. | `portals/tankhapay/cli/config.go:127-161`; `portals/blinkit/cli/config.go:67-100`; `sap-b1/cli/README.md:574-580`; `portals/amazon/cli/config.go:20-31` |
| `ensureAuth`: in-memory → disk cache → **one** fresh login per process (`attempted` flag, "avoids account lockout"); auto-relogin once on 401/403 then give up. Decode JWT/cookie expiry client-side (no signature check) to fail fast with a clear message. | `portals/tankhapay/cli/auth.go:56-88`; `portals/tankhapay/cli/client.go:187-201`; `portals/zepto/cli/jwt.go:11-47` |
| Cookie-session client = `http.Client{Jar: cookiejar.New(nil), Timeout: 30–90s}`; `CheckRedirect` refuses redirects to sign-in pages and surfaces "session expired"; content-sniff an HTML shell returned with 200 as expiry. For GST: a 302 to `/services/error/accessdenied` or a "Request Rejected" page must map to the same error (`RECON.md:19-21`). | `dsr-cli/internal/portal/portal.go:24-37`; `portals/amazon/cli/client.go:20-29,110-118` |
| Login is the **only sanctioned non-read call**; logout/sign-out/token-rotate paths are explicitly refused by the guardrail (self-preservation — don't kill the human's session). | `portals/tankhapay/cli/auth.go:18`; `portals/amazon/cli/client.go:52-57`; `portals/zepto/cli/guardrail_test.go:23` |
| **gitignore** at portal root (already present for GST, matches precedent): `.env`, `.env.*`, `!.env.example`, `*.token`, `cookies*.json`, `session*.json`, `captures/`. Root also ignores `*.token .token token.json session.json *.har *.session.json *.jwt`. | `portals/gst/.gitignore`; `portals/zepto/.gitignore`; root `.gitignore:23-27` |
| Don't duplicate scheduled logins on a second box — single-concurrent-session portals invalidate the other token. | `NEW-DEVICE.md:168-170`; `portals/zepto/cli/README.md:42-44` |

## 5. MCP exposure and gateway registration

| Convention | Evidence |
|---|---|
| MCP lives **inside the same binary** as a `mcp` subcommand (`dsr mcp`, `sapb1 mcp`, `postsql mcp`, `hana-sql mcp`) using `github.com/mark3labs/mcp-go`; default transport stdio, `--transport http --addr 127.0.0.1:77NN` serves streamable HTTP at `/mcp`. "HTTP adds a transport, never a capability." | `dsr-cli/internal/cli/mcp.go:3-63`; `sap-b1/cli/MCP.md:1-8`; `postsql/README.md:181-192` |
| Tools are a **hand-authored allowlist** (dsr: 15 grouped tools, each `action` pinned to a literal argv into the CLI; unknown action = error, never passthrough), not a cobra-tree mirror. Every tool sets `WithReadOnlyHintAnnotation(true)`, `WithDestructiveHintAnnotation(false)`; a test pins the exact tool-name set. Shared param defs (`pFrom`, `pTo`, `pLimit`) so the same concept has one name across tools. | `dsr-cli/internal/mcp/tools.go:7-34,36-60`; `sap-b1/cli/internal/mcp/server.go:208-209`; `sap-b1/cli/MCP.md:33-40` |
| Password/creds never appear in any tool result or error (`safeErr`, `MaskedPassword`). | `sap-b1/cli/internal/mcp/server.go:20-22`; `dsr-cli/internal/mcp/server.go:26-27` |
| Gateway registration = add one `BackendConf{Name, Prefix, StripPrefix, URL: "http://<svc>:77NN/mcp"}` to `DefaultBackends()`, cross-compile `CGO_ENABLED=0 GOOS=linux GOARCH=amd64` into `mcp-gateway/bin/<name>-mcp.linux-amd64` (gitignored), rsync to `vps:/opt/jivo-mcp/bin/`, add a compose service with `--transport http --addr :77NN` + single-file env bind mount, `docker compose up -d --force-recreate <svc> gateway`, verify with a real `tools/call`, not `initialize`. Ports in use: 7701 sapb1, 7702 postsql, 7703 ecom, 7704 oms, 7705 factory, 7706 hana, 7707 exim, 7709 dsr (built, not wired), 7711 jsap. **`StripPrefix` only if every tool shares the prefix** (name all tools `gst_*` and set Prefix=StripPrefix=`gst_`, like hana/jsap). | `mcp-gateway/internal/gateway/config.go:88-146`; `mcp-gateway/DEPLOY-NEW-BACKENDS.md:38-57,118-177,202-227,244-252`; `mcp-gateway/README.md:7-16,26-50` |
| MCP endpoints are **never** password-gated (Daman 08-18). dsr is deliberately NOT in the gateway (over-privileged login) — GST would be a candidate only after the read-only guard (§8) is in place. | memory `feedback-never-password-the-mcp`, `dsr-cli-sql-guard-hole` |
| Claude Desktop for Accounts: `claude_desktop_config.json` with `"command": "C:\\jivo-<x>\\<x>.exe", "args": ["mcp"], "env": {…}`, shipped in an `accounts-kit/` with `SETUP.md` + `ASK-EXAMPLES.md`. | `sap-b1/accounts-kit/claude_desktop_config.json`; `sap-b1/accounts-kit/SETUP.md:1-30` |

## 6. Doc shape

| File | Shape | Evidence |
|---|---|---|
| `portals/<name>/README.md` | ⚠️ READ-ONLY banner first line; auth model table ("cracked & proven <date>"); backends table; "The deliverable" (`vault/`, `captures/`, `cli/`); study status with date; pointer to the CLI README. | `portals/tankhapay/README.md:1-42`; `portals/zepto/README.md:1-42`; `portals/amazon/README.md:1-58` |
| `portals/<name>/cli/README.md` | Title + one-paragraph purpose → ⛔ read-only block → **Read-only law (3 layers)** → Auth (resolution order, expiry, re-login message verbatim) → Build (mac + Windows lines) → Quick start (`doctor`, `auth whoami`, one real read) → Global flags → Command groups table with counts → Notes/Deferred → Regenerate → Files tree. | `portals/tankhapay/cli/README.md`; `portals/zepto/cli/README.md`; `portals/blinkit/cli/README.md` |
| `RECON.md` / `vault/` | Recon notes exist for GST already; mature portals promote them to an Obsidian `vault/` with `00-<Name>-Atlas.md`, `<Name>-Endpoints.md` master index (the generator's source of truth), `_meta/{Auth-and-Access,Read-Only-Guardrails,Study-Verification}.md`, plus a `COVERAGE-LEDGER.md` (one row per route, YES/NO with a reason for every NO). | `portals/amazon/README.md:19-31`; `portals/amazon/COVERAGE-LEDGER.md:12-20`; `dsr-cli/study/vault/00-INDEX.md` |
| `HANDOFF.md` | "You are picking up a **finished** project…" → What exists (done + verified, with counts) → First steps (4 commands) → Auth already cracked, do not re-derive → Read shaping → Coverage numbers → Regenerate/re-verify → Optional next steps (all READ-ONLY). Root `HANDOFF-*.md` files are gitignored (self-deleting); the portal-local `HANDOFF.md` is kept. | `portals/tankhapay/HANDOFF.md:1-75`; root `.gitignore:77-78` |
| `ASK-EXAMPLES.md` | "You want to know… / Run" tables per topic, plain English, first-time setup line at top. | `dsr-cli/ASK-EXAMPLES.md:1-60` |
| Root `README.md` "The grid" table + `NEW-DEVICE.md` "What is NOT automatic" get one row/line for the new CLI. | root `README.md:57-72`; `NEW-DEVICE.md:164-171` |
| Work log: `chats/YYYY-MM-DD.md` (Context / What we did / Decisions / Next) indexed in `chats/Chats-MOC.md`; per-operator `chats/<name>/`, `queries/<name>/` are tracked. | `chats/README.md:14-26`; root `.gitignore:45-49` |
| Honesty floor in docs: tag numbers `VERIFIED / PENDING_AUTH / NOT_REACHABLE`, and a "What was verified, and what was not" section. | `portals/amazon/README.md:43`; `mcp-gateway/DEPLOY-NEW-BACKENDS.md:290-313` |

## 7. Tests

| Convention | Evidence |
|---|---|
| Plain `go test ./...`, stdlib `testing` only, **no live network** in unit tests; MCP/gateway use `httptest` fakes. | `mcp-gateway/README.md:385-393`; `sap-b1/cli/MCP.md:39` |
| Mandatory trio in every portal CLI: `guardrail_test.go` (table of blocked writes + allowed reads, incl. segment-boundary false-friends), `guardrail_coverage_test.go` (every wired path passes the guard — "no dead commands" — and the wired set equals `../captures/wired-reads.tsv` 1:1), plus small unit tests for parsers (`TestCurlHeader`, `TestDefaultSalesRange`). | `portals/tankhapay/cli/guardrail_test.go:7-60`; `portals/tankhapay/cli/guardrail_coverage_test.go:33-82`; `portals/zepto/cli/guardrail_coverage_test.go:17-51`; `portals/blinkit/cli/guardrail_test.go:60-80` |
| Recorded-response fixtures are rare: only `factory-cli/internal/cli/testdata/` (identity map) and `distribution/testdata`. Captured bodies stay in gitignored `captures/` because they hold live business data. If GST ships fixtures, scrub them and keep to shape-only samples. | `factory-cli/internal/cli/product_identity_test.go:18`; `portals/swiggy-instamart/.gitignore` (captures rationale) |
| Guard tests carry the regression that motivated them in the comment (e.g. dsr batch-bypass reproduced live). | `dsr-cli/internal/db/guard_test.go:29-33` |
| Gateway gate: `go test -race -count=2 ./...`. | `mcp-gateway/README.md:81` |

## 8. Read-only guard pattern (the part that must not be skipped)

Three structural layers + tests, every portal CLI, word-for-word in each README:

1. **Only READ rows are wired.** Command tree is generated from a classified inventory (`captures/wired-reads.tsv`); writes, exports, auth and "unknown" endpoints are held out in `reclassified-writes.tsv` / `unknown-excluded.tsv`, never guessed in. — `portals/tankhapay/cli/README.md:85-91`; `portals/tankhapay/HANDOFF.md:55-62`
2. **`forbiddenPath(method, url)` fails closed before any socket opens**: method allowlist (GET, or GET+POST-to-read), write-verb scan on path segments (`anyWrite` always, `leadingWrite` only as first token so `get_Last_sync_status` isn't killed), refuse logout/refresh paths, and (amazon) deny-by-default allowlist lookup. — `portals/tankhapay/cli/client.go:18-123`; `portals/amazon/cli/client.go:43-73`
3. **No mutating code path exists** — the client has no PUT/PATCH/DELETE method at all; the single data path (`doRead`/`get`) calls the guard first. — `portals/tankhapay/cli/client.go:167-175`; `dsr-cli/internal/portal/portal.go:1-5`

Plus, for the MCP surface, the **AST guard test**: walk every non-test `.go` file with `go/parser` (comments dropped), fail if any `SelectorExpr` names `os.WriteFile/Create/MkdirAll/Remove/…`, `http.MethodPost/Put/Patch/Delete`, `http.Post/PostForm`, `ioutil.WriteFile`, or `.Exec/.ExecContext`; also pin the exact tool set and prove unknown actions error. Copy `dsr-cli/internal/mcp/readonly_guard_test.go:25-128` and `sap-b1/cli/internal/mcp/readonly_guard_test.go:12-40` (sapb1 additionally bans `client.Create/Update`, and its wire test drives every tool against a fake server that fails on anything but GET + `POST /Login|/Logout`). — `sap-b1/cli/MCP.md:29-40`

Sanctioned side-effects (report *generation* = enqueue) are gated behind explicit `--export` (+ `--yes-export` under `--agent`) and the pure-read alternative is documented as preferred. GST's "generate-then-download" for GSTR views (`RECON.md:49`, D8) falls in this class. — `portals/blinkit/cli/README.md:19-23`; `portals/zepto/cli/README.md:20-24`

## Harness hooks a new CLI must satisfy

- The `PostToolUse` hook only captures commands whose payload matches `(sapb1|postsql|hana-sql|hanasql|dsr|ecom|oms|factory|exim)`; **add `gst` to the bash pre-filter and one `TOOL_ALIASES` entry** (`"gst-portal": "gst"`), optionally a `_KNOWN_SUBCOMMANDS` vocabulary. Writes verbs are never logged; outputs are never logged. — `harness/hooks/post-tool-use.sh:42`; `harness/bin/patterns.py:366-385,404-415`; `harness/PATTERNS.md:474-476`
- Any HTML/Excel report the CLI writes gets watermarked by `post-write.sh`; nothing else in the harness touches the CLI. — `.claude/settings.json:28-38`
- Business truths discovered (e.g. the `dt` field "16/02/0027" quirk, `MMYYYY` period codes, credit-ledger sign) go through `jivo-correct` as corrections with the proving command, not into README prose alone. — `harness/README.md:96-116`

## Concrete spec summary for the builder

```
portals/gst/
  README.md            (banner, auth model, 8 GSTINs, deliverable, status date)
  RECON.md             (exists) → later vault/00-GST-Atlas.md + GST-Endpoints.md
  HANDOFF.md, ASK-EXAMPLES.md
  .env / .env.example / .gitignore   (exist; keep !.env.example)
  captures/wired-reads.tsv, reclassified-writes.tsv   (generator inputs, gitignored bodies)
  cli/
    main.go root.go registry.go config.go auth.go client.go jwt.go|session.go
    output.go helpers.go doctor.go cmd_auth.go
    cmd_returns.go cmd_ledgers.go cmd_filed.go cmd_profile.go cmd_masters.go ...
    guardrail_test.go guardrail_coverage_test.go
    internal/mcp/{server.go,tools.go,readonly_guard_test.go,tools_test.go}  (for `gst-portal mcp`)
    gst-portal, gst-portal.exe   (committed)
    README.md
```

Env: `GST_01..08_{STATE,GSTIN,USER,PASS}` + `--gstin/--state` selector; session cache `UserConfigDir()/gst-portal/session-<gstin>.json` 0600 (one jar per registration); global `--json --agent`; exit codes 0/1/2/3/4/5/6; INR via `inr()`; dates IST, `--period MMYYYY`; `doctor` = config → session → `GET /services/api/ustatus`; MCP tools all `gst_*` on port **7710** (unassigned) with Prefix=StripPrefix=`gst_` in the gateway; guard layers 1-3 + AST test copied from dsr/sapb1; `TOOL_ALIASES` + hook pre-filter updated.

Confidence: high (~95%) on every convention above — each is cited from tracked source. The one thing I did not verify is whether any portal CLI has a working headless *captcha* login precedent; none does (tankhapay bypassed reCAPTCHA via `localhost:true`, amazon/swiggy consume a browser session), so GST's auth mode is an open design choice pending recon D1/D10.