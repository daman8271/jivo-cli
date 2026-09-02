# GST portal → CLI — handoff (2026-08-21)

You are picking up a **working v0.1**: a read-only Go CLI over the GST portal for
JIVO Wellness's 8 registrations, built in one day from a live study of the portal.
Everything is on disk in `portals/gst/`. Read [`README.md`](README.md) then
[`cli/README.md`](cli/README.md); the endpoint contract is [`API.md`](API.md) and
it is the source of truth — do not re-derive it from the browser.

**The golden rule:** the GST portal is a live statutory filing system. Reads only,
always. Login is the single sanctioned side effect. If you find yourself wanting
to wire a `generate`, `download`, `submit` or `file` path, the answer is no — see
`cli/guard.go`, where the guard will refuse it before a socket opens anyway.

## State of play

| | |
|---|---|
| Endpoints proven live | **33**, on 4 hosts, all written up in `API.md` with request + response shapes |
| CLI | `cli/gst-portal` (+ `.exe`) — 36 commands in 12 groups, cobra + stdlib only |
| Logins verified | **7 of 8**, 2026-08-21 17:00–17:25 IST. Punjab failed (below) |
| Guard | 3 layers + `guardrail_test.go`, `guardrail_coverage_test.go`, `readonly_ast_test.go` |
| Tests | `go test ./...` — **3 failures**, all stale test expectations, see below |
| Docs | README · cli/README · SETUP (Windows operator) · ASK-EXAMPLES · API · RECON · docs/{conventions,comparison-spec,captcha-ocr} |
| Not built | MCP (port 7710 reserved), auto-OCR, GSTR-2A amendments |

### Already cracked — do not re-derive

- **Login** is `POST /services/authenticate` with a **plaintext** password (no RSA,
  no client-side hash) plus a 6-digit captcha and a fixed `mFP` device-fingerprint
  blob. Always HTTP 200; the *body* carries the verdict.
- **The WAF keys on Referer and User-Agent, not on being a browser.** A plain Go
  client with the cookie jar reaches every JSON API. `services.gst.gov.in`
  **TCP-resets a branded desktop-Chrome UA** and ASM-rejects a bare `Mozilla/5.0`;
  one HeadlessChrome UA string is verified 200 on all four hosts. `return`,
  `payment` and `gstr2b` **require** their own host's dashboard Referer or they
  302 to `accessdenied`.
- **`TS*` (F5) cookies are not required.** The bearer is `AuthToken` on
  `.gst.gov.in`, shared by all four hosts.
- **Never fetch `/services/login` with a live session** — it replaces `AuthToken`
  with a pre-auth placeholder and logs you out. Three logins were burned learning
  that.
- **`filingsnapshot` only answers on `services.`**, not `return.`

## Open items

### D-items still open

| Item | What is missing | Cost of leaving it |
|---|---|---|
| **D1b** | The `errorCode` for a credential rejection (only the page *text* "Invalid Username or Password" was seen). Needs a deliberately wrong password — **never on a live JIVO credential, and never on Punjab** | Low. `interpretLogin` treats "any errorCode that is not `SWEB_9000`" as a credential rejection, which is correct but broader than it needs to be |
| **D9** | The portal's real idle timeout. `sessionMaxAge = 15 * time.Minute` is a conservative guess; the window is refreshed on every successful call. Cheapest route: read the SPA bundle's keepalive/idle constants, or base64-decode `AuthToken` in case it is a JWT with an `exp` | Medium. Too short = needless captchas; too long = a mid-snapshot 302 |
| **GSTN-EXEC1003** | `totalsummarycount?sec_name=B2B` is a **server-side error on GSTN's side**, reproduced 3×. Not auth, not the WAF. Retry another day | Low. Per-`ctin` B2B document lists work |
| **B2CL** | No current GSTIN has a "5 — B2C Large" document, so the section name is inferred | Low |
| **GSTR-2A `b2ba`** | Amendments never replayed. `gstr2a amendments` is a deferred leaf that says so and sends nothing | Low |

### Punjab (`03AACCJ4223F1Z6`) — a wrong password, not a bug

The portal refused these credentials twice on 2026-08-21, both times with a
captcha it had accepted. **This is an Accounts task, not an engineering one:** get
a corrected password, put it in `GST_03_PASS`, and only then try again.

The CLI will not try again on its own. The rejection is recorded at
`<UserConfigDir>/gst-portal/rejected-03AACCJ4223F1Z6.json` and every `auth login`
for that GSTIN stops before the POST until a human deletes that file. Repeated
attempts on a wrong password are how a GST account gets locked, and only the
department can unlock one.

### Test suite is red — 3 failures, all stale expectations

`go test ./... -count=1` fails on three tests that were written against behaviour
that then deliberately changed. **None of them is a production bug**; each is a
one-line test edit, and each needs a decision from whoever owns the change:

1. `cli_e2e_test.go:33` runs `auth list --all`. `--all` was deliberately made
   local to `doctor`/`auth status`/`snapshot` (`root.go`), and `auth list` ignores
   selectors by design. Either drop `--all` from the test, or decide `auth list`
   should accept it.
2. `commands_test.go` `auth whoami`: the fake portal answers every endpoint with
   `{"status":1,"data":{}}`, and `client.go` correctly reads a `ustatus` with no
   `gstin` as an expired session. The stub needs a `gstin` field.
3. `login_test.go:90` looks for the pre-login jar via `loadSession`; it is
   deliberately staged at `pendingSessionPath()` so an abandoned captcha cannot
   clobber a working session. Use `loadPendingSession`.

Fix these before anything else — a red suite means the guard tests are not being
watched either.

## Next steps

### 1. MCP on port **7710** (the reserved slot)

Port 7710 is free and reserved (`mcp-gateway/internal/gateway/config.go` — 7701
sapb1, 7702 postsql, 7703 ecom, 7704 oms, 7705 factory, 7706 hana, 7707 exim,
7709 dsr — built but deliberately not wired, 7711 jsap; the gateway itself is 7700). Shape, per `docs/conventions.md` §5:

- `gst-portal mcp` inside the same binary, `mark3labs/mcp-go`, stdio by default,
  `--transport http --addr 127.0.0.1:7710` serving `/mcp`.
- Tools all named `gst_*`; gateway `BackendConf{Prefix: "gst_", StripPrefix: "gst_"}`.
- **Hand-authored allowlist, not a mirror of the cobra tree.** Every tool
  `WithReadOnlyHintAnnotation(true)`, `WithDestructiveHintAnnotation(false)`; a
  test pins the exact tool-name set.
- **`auth login` must not be exposed.** The MCP surface is read-only forever
  (memory `mcp-never-exposes-writes`), and an agent that can log in can end an
  accountant's browser session and, on a wrong password, walk an account toward a
  lockout. Expose `auth status`/`whoami`; leave login to the CLI, where a human is
  typing a captcha anyway. Copy `dsr-cli/internal/mcp/readonly_guard_test.go` and
  add the AST guard.
- Not before the test suite is green, and not before someone has run `snapshot`
  over all 8 registrations once by hand.

### 2. The OCR gate

Auto-OCR is **not** in v0.1 and should not be added on a hunch. The measured rate
(`docs/captcha-ocr.md`, n=4, tesseract + a Pillow/numpy pipeline) is **~50% exact
per attempt, ~83–88% per digit** — and it degrades further on the real 182×50
input. Two conditions, both required, before `--captcha auto` ships as anything
but an opt-in experiment:

1. **≥80% exact over ≥100 fresh labelled captchas.** Below ~70% the operator-typed
   path is both faster and safer. Tesseract will not get there; the realistic
   route is a small fixed-length digit CNN trained on labelled samples, and every
   captcha an operator types by hand is a free label — wire the
   `(png, digits, succeeded?)` capture into a gitignored `captcha-labels/` dir
   under `UserConfigDir` first, and collect for a few weeks.
2. **Proof that a wrong captcha does not count toward the GST account-lock
   counter.** Nobody has measured this. Until someone has, every automatic retry
   is off, and `maxLoginAttempts = 1` stays a constant rather than a flag. Test it
   on a throwaway/expired credential, never on a live JIVO one.

### 3. Smaller things worth doing

- **Walk `SETUP.md` once on a Windows fleet box** (VICTUS 23001, over the tunnel).
  Specifically: does the captcha PNG actually open? `captcha.go` uses
  `rundll32 url.dll,FileProtocolHandler` — deliberately not `cmd /c start`, which
  re-parses `& | ^ >` before dequoting. **That branch has never been executed on
  Windows.** Nothing on a Mac can test it (memory `no-powershell-on-fleet`).
- **Re-run `snapshot --all --fy 2026-27`** after each month's filings and diff it
  against SAP per `docs/comparison-spec.md`. That spec has no consumer yet — it is
  the actual point of this CLI, and the reconciliation script is unwritten.
- **Rotate the GST passwords.** They sat in `env-vault/all-env.txt`, which was
  publicly readable (memory `env-vault-public-leak`, 2026-08-05).
- **Fix Punjab**, then re-verify with `gst-portal doctor --state punjab`.
