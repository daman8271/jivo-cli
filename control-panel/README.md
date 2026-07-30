# software/ — Jivo Group Control Panel: reverse-engineered

Complete, **read-only** capture of the internal **Jivo Group Control Panel** Django ERP
(`http://103.89.45.75:9080`) — an Obsidian knowledge vault documenting every page +
endpoint, and a local CLI (`jivo`) that pulls the same data from the terminal.

> ⚠️ **This is a LIVE PRODUCTION internal system** and the login is an **Admin** account.
> Everything here is strictly **READ-ONLY** — no write/OTP/export-mutation endpoint is ever
> called. Nothing here is published anywhere; it all stays on this machine.

## Two deliverables

### 1. `vault/` — the Obsidian knowledge base
Open `vault/` as an Obsidian vault. Start at **`00-INDEX.md`** (map of content).
- `pages/` — one doc per UI page (21), grouped by sidebar section
- `api/` — one doc per endpoint (56) with live-captured request params + response schema
- `concepts/` — domain terms (24): REALISE, OIH, BAL, COGS, DRR, GT/MT/ROI/ECOM, OILS/BEVERAGES, Wellness-Mart recon…
- `architecture.md` — stack, auth model, endpoint namespacing, read-only posture
- 94 interlinked notes, 0 broken `[[wikilinks]]`.

### 2. `cli/jivo` — the read-only terminal client
Binary: `cli/jivo/jivo` (Windows: `cli\jivo\jivo.exe`). **42 read commands** across 8 groups + a `auth` group.

```bash
JIVO=~/software/cli/jivo/jivo          # Windows (PowerShell): $JIVO="$HOME\software\cli\jivo\jivo.exe"

# 1. Log in once (creds from flags, JIVO_USER/JIVO_PASS env, or ~/software/.env)
$JIVO auth login                      # stores session in ~/.config/jivo-pp-cli/config.toml (0600)
$JIVO auth status

# 2. Pull reports (all read-only; --json for machine output)
$JIVO sales data --start-date 2026-07-22 --end-date 2026-07-22 --json
$JIVO targets list --month 7 --year 2026
$JIVO oih breakdown
$JIVO accounts aging-oil                  # customer aging (oil AR)
$JIVO accounts open-payments --json
$JIVO accounts claims
$JIVO masterdata customer-master --json   # 1167 rows
$JIVO masterdata rate-list
$JIVO inventory stock --schema jivo_oil
$JIVO inventory non-moving
$JIVO inventory daily-production --start 2026-07-22 --end 2026-07-22
$JIVO inventory reconciliation
$JIVO credit                              # Required Credit Limit (from page-embedded JSON)
$JIVO users list                          # admin user roles (read-only, page-embedded JSON)
```

Command groups: **sales**(13) · **targets**(5) · **oih**(4) · **accounts**(5) · **masterdata**(3) · **inventory**(9) · **users**(2, HTML) · **credit**(1, HTML) · **auth**(login/status/logout). Plus framework commands: `search`, `sync` (→ local SQLite), `doctor`, `which`, `agent-context`.

## Coverage
Every page that exposes readable data is captured. The only page not covered is **OIH vs Stock**, whose nav link returns **404** (feature isn't built server-side). The COGS card is **OTP-gated** and deliberately not bypassed. All write/OTP/export sub-actions (target editing, credit lock/unlock, rate-list save, aging remarks, user CRUD, `verify-pin`) are documented in the vault but excluded from the CLI by construction.

## Auth
Django session login: `POST /accounts/login/` (username/password/CSRF) → `sessionid` + `csrftoken` cookies. The CLI sends `Cookie: sessionid; csrftoken` + `X-CSRFToken` (POST) + `X-Requested-With: XMLHttpRequest` on every call. If a call 401s / redirects to login, re-run `jivo auth login`.

## Layout
```
software/
├─ README.md            # this file
├─ PLAN.md              # the multiphase build plan (all phases ✅)
├─ .env                 # creds (gitignored)   .gitignore
├─ recon/               # login.sh, jio.sh (bash auth helpers), RECIPE.md, page/api dumps
├─ vault/               # the Obsidian knowledge base  ← open in Obsidian
└─ cli/
   ├─ jivo-spec.yaml    # the internal spec the CLI was generated from
   ├─ jivo/             # the generated Go CLI (binary: jivo/jivo)
   └─ BUILD_NOTES.md    # build log, smoke-test evidence, read-only audit, minor gaps
```

## Provenance
Vault built by a multi-agent workflow (8 domain mappers → weave → completeness critic → gap-fill). CLI generated with `cli-printing-press` v4.24 (internal-spec mode) + hand-wired Django session auth (`internal/cli/jivo_login.go`, `internal/client/jivo_headers.go`), modeled on the `jivo-ecom` internal CLI. Read-only audited: 0 mutating API verbs; the only `save`/`delete` commands are local flag-profile management; the one generic API `POST` command is unregistered dead code.
