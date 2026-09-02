# gst-portal

A **read-only** Go CLI for the **GST portal** (`gst.gov.in`), covering JIVO
Wellness Pvt Ltd's **8 registrations** (PAN AACCJ4223F — the Oil books). It is
the read surface over the endpoint contract captured live on 2026-08-21 and
written up in [`../API.md`](../API.md): 36 commands in 12 groups over 33
allowlisted endpoints on 4 hosts.

## ⛔ Read-only law

The GST portal is a **live statutory filing system**. Everything here is a READ.
**No** GENERATE / SAVE / SUBMIT / FILE / PROCEED TO FILE / RESET / COMPUTE /
UPDATE / AMEND / SET-OFF / CREATE CHALLAN is wired, and none can be reached.
There is **no PUT, PATCH or DELETE code path in this binary at all**.

Three layers enforce it, plus tests that fail if any of them is weakened:

1. **Only READ rows are wired.** `endpoints.go` is a table of 33 rows — method,
   host, path, and the *exact* query and body keys that row may send. It is
   mirrored line-for-line in [`wired-reads.tsv`](wired-reads.tsv), and
   `guardrail_coverage_test.go` fails if the two ever diverge, so an endpoint
   cannot be added in code without showing up on one reviewable line.
2. **`forbidden()` fails closed before any socket opens.** Method allowlist (GET,
   or POST for a row the table marks POST — nothing else). Host must be one of
   the four GST hosts. Path is scanned for blocked substrings
   (`generate`, `download`, `dwnld`, `upload`, `setoff`, `submit`, `savedraft`,
   `/reset`, `/amend`, `/compute`, `/proceed`, `/cancel`, `logout`, …) and for
   write verbs on **segment boundaries** — so `efiledReturns` and
   `filingsnapshot` (reads containing "file") survive, while
   `/payment/auth/api/challan/create` is refused twice over. Then deny-by-default:
   the row must exist, with this method, on this host, carrying only its own keys.
   A refusal is exit **5** and says *nothing was sent*.
3. **No mutating code path exists.** One function opens sockets. `readonly_ast_test.go`
   walks every non-test `.go` file and fails if anything outside `client.go`
   imports `net/*`, if `net/http/httputil` is imported anywhere (a `--debug` dump
   would print the login body), if `os/exec` appears outside `captcha.go`, or if
   any string literal that looks like a portal path is not a table path.

**The one sanctioned side effect is logging in.** `POST /services/authenticate`,
capped at **one per process** by a constant, not a flag.

`logout` is deliberately unreachable — killing the session of whoever is logged
in as that username is not this tool's business.

## Auth

Username + password + a **6-digit image captcha**, per registration. One cookie
jar (`AuthToken`, on `.gst.gov.in`) authorises all four hosts.

**Credential resolution** — flag > env var > `.env` > nothing. There is
deliberately **no `--password` flag**. `.env` search order:

`$GST_ENV` → `./.env` → `../.env` → `<exe dir>/.env` → `<exe dir>/../.env` →
`~/jivo-cli/portals/gst/.env`

Blocks are `GST_01_STATE / GST_01_GSTIN / GST_01_USER / GST_01_PASS` … through
`GST_08_*`. All four keys or the block is rejected. Missing credentials fail
closed and name the file that was searched. Copy `../.env.example` and fill it
from `env-vault/`.

### The login is two steps, because the captcha is

The portal serves a 182×50 PNG of six digits, bound to the cookie jar that
fetched it. There is no API to answer it and **no OCR here**: the study measured
~50% exact per attempt (`../docs/captcha-ocr.md`) and nobody has measured what
this portal does after N bad logins.

**Interactive (an operator at a keyboard):**

```sh
./gst-portal auth login --state haryana
```

Fetches the login page (for its cookies), fetches the captcha, writes the PNG,
opens it in the system image viewer, and prompts. Type the six digits, or `r` for
a fresh image (free — a re-roll is *not* a login attempt), or blank to abort
(nothing is sent).

**Headless (SSH, an agent, a box with no display)** — the same thing as two
invocations:

```sh
./gst-portal auth captcha --state haryana --out /tmp/captcha.png   # prints the path
./gst-portal auth login   --state haryana --captcha 357108         # answers it
```

The pre-login jar is staged at `session-<GSTIN>.pending.json`, valid 10 minutes,
and only replaces the real session file **after** the portal accepts the login —
so an abandoned prompt can never destroy a working session.

**No terminal and no display at all?** Export the cookies from a real browser
(CDP/network-level — the auth cookies are `httpOnly`, `document.cookie` misses
them) and adopt them:

```sh
./gst-portal auth import cookies.json --state haryana
```

### Four rules that are not negotiable

- **One login POST per process.** `maxLoginAttempts = 1`. No loop anywhere can
  spend a second.
- **A credential rejection is never retried.** It is written to
  `rejected-<GSTIN>.json` beside the session file, and every later `auth login`
  for that GSTIN refuses before the POST until a human deletes it. Punjab
  (`03AACCJ4223F1Z6`) is in that state — its password has been wrong since
  2026-08-21. A captcha rejection is different: re-roll and try again.
- **This CLI never handles OTP.** If the portal ever demands one, it says so and
  exits 4. An OTP is a second factor precisely so an unattended program cannot
  pass it.
- **One session per username.** A successful CLI login **ends any browser session
  logged in as that user** — possibly mid-filing. `auth login` warns before it
  does. Do not run it while somebody is filing.

**Session cache:** `os.UserConfigDir()/gst-portal/session-<GSTIN>.json`, dir 0700,
file 0600, one per registration (override the parent with `$GST_STATE_DIR`).
Trusted for **15 minutes of idle**, refreshed on every successful call. That 15
is a conservative guess — the portal's real idle timeout is unmeasured (D9).

On any 401/403/`accessdenied` bounce, every command appends the same line:

> session expired or not established — run `gst-portal auth login --gstin <GSTIN>`
> (a captcha will be shown) or `gst-portal auth import <cookies.json>`

**The session file is a bearer token to a portal that can file returns.** Treat
it like the password. Never copy it to another machine, never attach it to a
ticket.

## Build

```sh
cd portals/gst/cli && go build -o gst-portal .                            # mac/linux
cd portals/gst/cli && GOOS=windows GOARCH=amd64 go build -o gst-portal.exe .   # windows
go test ./... -count=1
```

Go 1.25+; cobra + stdlib only. Both binaries are committed — Accounts PCs run the
`.exe` straight from a `git pull`. **On Windows run `gst-portal.exe` wherever this
doc says `./gst-portal`.**

## Quick start

```sh
./gst-portal doctor --offline          # config + cached sessions, no network
./gst-portal auth list                 # the 8 registrations, credentials masked
./gst-portal auth login --state haryana
./gst-portal doctor                    # + one live read per registration
./gst-portal auth whoami --state haryana
./gst-portal ledger credit --state haryana
```

## Global flags

| Flag | Effect |
|---|---|
| `--gstin 06AACCJ4223F1Z0` | select one registration by GSTIN |
| `--state haryana` | select by state name, code or alias (`haryana`, `hr`, `06`, `delhi isd`) |
| `--json` | JSON for the table-shaped commands (`doctor`, `auth list/status`, `snapshot`). Portal reads are JSON already |
| `--agent` | implies `--json`; wraps output in `{ok, command, endpoint, gstin, count, data\|error}` and silences stderr |

`--all` is **not** global — only `doctor`, `auth status` and `snapshot` can act on
more than one registration, and each declares it locally. Every other command
answers about exactly one; asking without a selector is a usage error (exit 2)
that lists the eight.

Dates: `--from` / `--to` are `YYYY-MM-DD`, IST. `--to` is **inclusive** here
(portal semantics, not the house exclusive rule) and defaults to today. Periods
are the portal's `MMYYYY` (`--period 072026`); financial years are `--fy 2026-27`.

Money prints with Indian grouping and a crore/lakh suffix: `₹4,33,72,582.27 (4.34 Cr)`.

## Commands

| Group | Leaf | Answers | Endpoint |
|---|---|---|---|
| `doctor` | | config → cached session → one live `ustatus` per registration (`--offline` skips the network, `--all` is the default) | `services/api/ustatus` |
| `auth` | `list` | the 8 registrations, usernames masked, passwords shown only as `present`/`MISSING` | — |
| | `login` | the one sanctioned POST (`--captcha`, `--captcha-out`) | `services/authenticate` |
| | `captcha` | mint a captcha PNG for the two-step login (`--out`) | `services/captcha` |
| | `status` | cached session age per registration (`--all`) | — |
| | `whoami` | who the portal thinks the session belongs to | `services/api/ustatus` |
| | `import <cookies.json>` | adopt a browser-exported cookie jar | — |
| `returns` | `calendar` | last 5 periods of GSTR-1/IFF and 3B, filed or not | `returns/auth/api/filingsnapshot` |
| | `periods` | financial years and their `MMYYYY` codes | `returns/auth/api/dropdown` |
| | `status --period` | per-form tiles for a period; with `--form`, the **ARN + filing date** | `rolestatus`, `formdetails` |
| | `filed --fy [--form --freq]` | the filed-returns register: ARN, date, mode, who filed | `efiledReturns` (POST) |
| `ledger` | `cash [--from --to]` | electronic cash ledger: balance by head, or the statement | `cashbalance`, `cashdetls` |
| | `credit [--from --to]` | electronic credit (ITC) ledger: balance, or the statement | `itcbalance`, `itcdtls` |
| | `challans --from --to` | challan ARNs paid in a range | `searcharnusngdate` |
| | `liability --from --to` | liability register Part-I (return related), by month range | `returns/auth/api/retdtl` |
| | `liability-other --from --to` | liability register Part-II (demands) | `payment/auth/api/liabdetails` |
| `gstr3b` | `summary --period` | the filed 3B: tables 3.1, 3.2, 4, 5.1, 6.1 | `gstr3b/summary` |
| | `autopop --period` | what the portal pre-filled from GSTR-1, vs what was declared | `gstr3b/getr1r3bliab` |
| | `status --period` | ARN, filing date, due date | `formdetails` |
| `gstr2b` | `summary --period` | the ITC statement: summary **and** every supplier document | `gstr2b/getdata`, `getuserdtls` |
| `gstr1` | `summary --period` | filing status + per-section document counts | `formdetails`, `totalsummarycount` |
| | `section --period --section` | per-counterparty counts inside one section | `totalsummarycount` |
| | `docs --period [--section --ctin --inum]` | the documents themselves (B2B, CDNR, B2CS, HSN, DOC…) | `gstr1/invoice` |
| `gstr2a` | `suppliers --period` | who filed against this GSTIN, with their filing dates | `gstr2a/ctin` |
| | `docs --period --ctin` | one supplier's B2B documents | `gstr2a/b2b` |
| | `status --period` | 2A form status | `formdetails` |
| | `amendments` | **deferred** — `b2ba` never replayed live; says so, sends nothing | — |
| `compare` | `--fy` | the portal's own GSTR-1-vs-3B and 2A-vs-3B tables, 13 rows each, whole FY in one call | `gstr3bvs1/getdata` |
| `profile` | | legal name, status, constitution, jurisdictions, address, signatory | `services/auth/profile/detail` (POST) |
| `masters` | `forms` `fy` `months` `quarters` `halfyears` `states` | the portal's own dropdown tables | `/master/*` |
| `snapshot` | `--fy --out [--all --skip-documents]` | a whole FY of returns + ledgers to disk: raw bodies, normalised `.jsonl`, `manifest.json` | all of the above |

### `snapshot` is the primary operator verb

A GST login costs a hand-typed captcha and the session is short, so the useful
shape is *one login, then pull everything*:

```sh
./gst-portal auth login --state haryana
./gst-portal snapshot --state haryana --fy 2026-27 --out ~/gst-snap
```

It **never prompts** (a registration with no session is recorded as "needs login"
and skipped) and **never aborts on one registration** (Punjab's failure is
recorded; the other seven still land). Output:

```
<out>/manifest.json            what was pulled, when, from where, with what result
<out>/<gstin>/raw/<name>.json  the portal body, verbatim
<out>/<gstin>/records.jsonl    one normalised record per line (../docs/comparison-spec.md §3)
```

Written 0700/0600 — a snapshot is turnover, ITC, both ledgers and
counterparty-level documents. `--out` **refuses to point inside any git
checkout**: this repo is public, and `.gitignore` only covers the literal `out/`.

## Exit codes

House table (sapb1, dsr). There is deliberately **no exit 7** — this CLI never
writes, so "write outcome unknown" cannot happen.

| Code | Means |
|---|---|
| `0` | ok — *including* the portal's "no data" answers (see below) |
| `1` | generic error |
| `2` | usage — bad flag, no registration selected, unparseable period/FY |
| `3` | config — no `.env`, a `GST_NN_` block missing a key |
| `4` | **auth** — no session, expired session, GSTIN mismatch, credentials refused, captcha refused, OTP demanded |
| `5` | network failure **or** a read-only guard refusal — either way **nothing was sent** |
| `6` | the portal answered, and its answer was an error |

**"No data" is exit 0, not exit 6.** Four portal codes are answers, not failures:
`RET13510` (no record), `LG9221` (no challans), `GTR2B-002` (2B not generated for
that period), `RETWEB_07` (no rows in that GSTR-1 section). They come back as
`data: null`, `count: 0`, with the portal's own message in `note` — otherwise a
run over all 8 would abort on the first nil-filing registration.

## Notes and traps

- **Referer is the gate.** `return`/`payment`/`gstr2b` return `302 →
  /services/error/accessdenied` without one. That is a header bug, **not** an
  expired session — do not re-login. The client sends the right one per host.
- **Never send a branded Chrome User-Agent.** `services.gst.gov.in` TCP-resets
  it (reproduced 6×) and ASM-rejects a bare `Mozilla/5.0`. One UA is used
  everywhere, the only one verified 200 on all four hosts.
- **`filingsnapshot` is called on `services.`**, not `return.` — the same path on
  the return host is an ASM block for a plain client.
- **`itcbalance.dt` is garbage** (`16/02/0027`). The `itcdtls` dates are fine.
- **Never fetch the login page with a live session** — it replaces `AuthToken`
  with a pre-auth placeholder and logs you straight out. Only `auth login` and
  `auth captcha` touch it, and only when logging in.
- **Politeness:** a 350 ms floor between calls; a `429` is exit 6 and is never
  retried in a loop.
- **The ISD registration (`07AACCJ4223F2ZX`) files GSTR-6**, not GSTR-1/3B.
  `snapshot` picks its form list from `ustatus`, so it does not report a missing
  3B as a finding.
- Test fixtures in `testdata/` are **scrubbed** (`../discovery/scrub.py` redacts by
  key name: password, captcha, mFP, deviceID, AuthToken, mobNum, email…). Raw
  captures live only in the gitignored `../captures/` and `../fixtures/`.

## Files

```
cli/
  main.go root.go registry.go exitcode.go output.go format.go dates.go
  config.go        .env discovery, the 8 registrations, the --gstin/--state selector
  endpoints.go     THE ALLOWLIST — 33 rows, one per reachable endpoint
  guard.go         forbidden(): the pre-socket refusal
  wired-reads.tsv  the same 33 rows, in review-readable form
  session.go       per-GSTIN cookie jars, the pending-login jar, rejection records
  client.go        the only file that may open a socket
  captcha.go       PNG handling + the operator prompt (the only file that may exec)
  login.go         the one sanctioned POST
  doctor.go cmd_auth.go cmd_returns.go cmd_ledger.go cmd_gstr1.go cmd_gstr2a.go
  cmd_gstr2b.go cmd_gstr3b.go cmd_masters.go cmd_profile.go cmd_compare.go
  normalise.go snapshot.go
  *_test.go        incl. guardrail_test.go, guardrail_coverage_test.go, readonly_ast_test.go
  testdata/        scrubbed fixtures + golden .jsonl
  gst-portal  gst-portal.exe
```
