---
title: "JIVO E-Com CLI — VPS Setup & Operator Guide"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: guide
tags: [jivogpt, ecom-cli, setup]
---

# JIVO E-Com CLI — VPS Setup & Operator Guide

This box (`srv1685505`) has a fully working, **read-only** command-line interface to
JIVO's internal e-commerce / quick-commerce analytics platform at
**https://ecom.jivo.in**, plus the **Printing Press** toolchain that generated it.

Everything here was installed and verified on 2026-06-26.

---

## TL;DR — use it right now

```bash
# (a fresh shell already has the right PATH via ~/.bashrc)
jivo-ecom-pp-cli doctor                       # health + auth check
jivo-ecom-pp-cli account me --json            # who am I
jivo-ecom-pp-cli platform stats amazon --json # headline stats for a platform
jivo-ecom-pp-cli dashboard top-skus --platform blinkit --json
jivo-ecom-pp-cli --help                        # full command tree
```

A login token is already stored. **It is valid for 1 HOUR, not 24** (verified
2026-08-29 by decoding the token's own `exp` claim). When it expires, renew it
from the refresh token — see "Renewing the token" below — or log in again:

```bash
# Recommended (password not visible in `ps`/history):
JIVO_ECOM_EMAIL='<your-account>@jivo.in' JIVO_ECOM_PASSWORD='********' jivo-ecom-pp-cli auth login
# or pipe it:
printf '%s' '********' | jivo-ecom-pp-cli auth login --email <your-account>@jivo.in --password-stdin
```

---

## What is `ecom.jivo.in`?

A React single-page app (`e-com-app`) backed by a REST API at
`https://ecom.jivo.in/api/...`. It aggregates sales/inventory/ads/PO data across
**Amazon, BigBasket, Blinkit, Citymall, Flipkart, Flipkart Grocery, JioMart,
Swiggy Instamart, Zepto, Zomato**.

### Auth model (important)
- **NOT cookies.** The `.jivo.in` cookies are analytics only (`_ga`, `_fbp`, …) and
  do not authenticate.
- Auth is a **JWT bearer token**: `POST /api/auth/login` with `{email, password}`
  returns an `access` token **valid 1 hour**, sent as `Authorization: Bearer <token>`
  on every call, plus a `refresh` token **valid 30 days**.
- The CLI's `auth login` does this exchange and stores the token at
  `~/.config/jivo-ecom-pp-cli/config.toml` (mode 0600). The password is never stored.
- You can also bypass login by exporting `JIVO_ECOM_TOKEN=<jwt>` (env wins over config).

### Renewing the token without a password (added 2026-08-29)

`POST /api/auth/refresh` with `{"refresh": "<refresh-token>"}` returns a fresh
`access` **and a fresh `refresh`** — the endpoint **rotates**: the refresh token
you sent is invalidated on use, so the new one must be written back or the chain
breaks permanently and you need the browser again.

Endpoint discovery note: it is `/api/auth/refresh` with **no trailing slash**.
`/api/auth/refresh/`, `/api/token/refresh` and `/api/token/refresh/` all 404.

Helper scripts (Mac Air, not in this repo — they sit next to the config and are
0600/0700 because the refresh token is a 30-day credential):

```
~/.config/jivo-ecom-pp-cli/refresh.token         # the 30-day token, 0600
~/.config/jivo-ecom-pp-cli/renew.sh              # refresh -> prints new access, rotates+saves
~/.config/jivo-ecom-pp-cli/renew-and-store.sh    # the above + 'auth set-token'
~/.local/bin/ecom                                # wrapper: auto-renews under 5 min left
```

`ecom <any cli args>` decodes the stored token's `exp`, renews if it is nearly
dead, then forwards to the CLI — so the 1-hour expiry stops mattering:

```bash
ecom doctor
ecom platform stats --platform blinkit --json
ecom --renew        # force a renewal, run nothing
```

If a refresh returns `token_not_valid`, the 30-day window is over. Re-grab both
tokens from Chrome DevTools -> Console on ecom.jivo.in:

```js
copy(localStorage.token + "\n" + localStorage.refreshToken)
```

The CLI has **no `auth refresh` command** — `auth` is only
`login / logout / set-token / setup / status`. That is why these scripts exist.

---

## The CLI: `jivo-ecom-pp-cli`

**44 read-only endpoints across 6 command groups.** Every command supports
`--json`, `--select <fields>`, `--csv`, `--compact`, `--quiet`. JSON is emitted on
stdout as `{"meta":{"source":"live"},"results":{...}}`; an informational caching
warning may go to **stderr** (parse with `... --json 2>/dev/null | jq .`).

| Group | What it gives you | Examples |
|---|---|---|
| `account` | current user, permissions | `account me`, `account permissions` |
| `dashboard` | cross-platform analytics | `dashboard latest-month`, `dashboard top-skus --platform amazon`, `dashboard category-breakdown --platform amazon`, `dashboard state-sales`, `dashboard fulfilment-health`, `dashboard expiry-alerts amazon` |
| `tables` | dynamic warehouse table browser (41 tables) | `tables counts`, `tables columns <table>`, `tables data <table>`, `tables distinct <table> <column>` |
| `master` | product & FC master data (paginated) | `master products --search oil --page-size 20`, `master fcs` |
| `notifications` | notifications + unread count | `notifications list` |
| `platform <slug> ...` | per-platform dashboards | `platform stats --platform blinkit`, `platform primary --platform amazon`, `platform ads --platform amazon`, `platform price --platform amazon`, `platform soh-doh --platform amazon`, … (19 leaves). **The slug is a `--platform` flag, not a positional argument.** |

Platform slugs: `amazon bigbasket blinkit citymall flipkart flipkart_grocery jiomart swiggy zepto zomato`.

### Read-only by design
No write commands are exposed (no landing-rate upsert, target edits, or
change-password). This was a deliberate scope decision.

### Known, expected behaviours (not bugs)
- Some `platform` sub-dashboards are **gated server-side per platform** — e.g.
  `platform pendency` works on `blinkit` but returns HTTP 400 on `amazon`;
  `platform month-on-month-sale` is only `bigbasket`/`flipkart_grocery`;
  `platform region-doh` is only `swiggy`/`zepto`. The CLI faithfully surfaces the
  API's own message.
- `dashboard category-sku-breakdown` **requires** `--platform`.
- `--select` uses bare field names (`--select month`), not dotted paths.

### Exit codes
`0` ok · `2` usage · `3` not-found · `4` auth · `5` API error · `7` rate-limited · `10` config.

---

## The Printing Press toolchain

The CLI was generated by **`cli-printing-press`** (v4.26.1, installed at
`~/go/bin/cli-printing-press`) from a hand-authored spec. The skill docs live in
`~/.claude/skills/printing-press*` (11 skills) for use by a Claude Code agent on
this box.

- **Spec:** `~/printing-press/library/jivo-ecom/spec.yaml`
- **Generated source:** `~/printing-press/library/jivo-ecom/`
- **Hand-authored login command:** `~/printing-press/library/jivo-ecom/internal/cli/jivo_login.go`

### Regenerating after a spec change
```bash
cd ~/printing-press/library/jivo-ecom
cli-printing-press generate --spec ./spec.yaml --force --validate
# IMPORTANT: --force resets auth.go and drops the hand-wired login line.
# Re-add this one line inside newAuthCmd() in internal/cli/auth.go:
#   cmd.AddCommand(newAuthLoginCmd(flags)) // hand-authored login (jivo_login.go)
go build -buildvcs=false -o ~/go/bin/jivo-ecom-pp-cli ./cmd/jivo-ecom-pp-cli
```

---

## File locations
| Thing | Path |
|---|---|
| CLI binary | `~/go/bin/jivo-ecom-pp-cli` |
| Printing Press binary | `~/go/bin/cli-printing-press` |
| CLI source + spec | `~/printing-press/library/jivo-ecom/` |
| Token / config | `~/.config/jivo-ecom-pp-cli/config.toml` (0600) |
| Local cache DB (after `sync`) | `~/.local/share/jivo-ecom-pp-cli/data.db` |
| Skills | `~/.claude/skills/printing-press*`, `~/.claude/skills/goal` |
| Go | `/usr/local/go` (on PATH via `~/.bashrc`) |
| This guide | `~/JIVO-ECOM-CLI-SETUP.md` |

## tmux
A session named **`app`** is running. Attach with `tmux attach -t app`.

## Security notes
- The stored JWT is owner-readable only (0600) and expires in **1 hour**.
- `auth login` posts only over HTTPS (refuses a non-https base URL).
- Never paste the password into shell history — use the env-var or `--password-stdin` forms above.
- `auth logout` clears the stored token.

Linked: [[docs/ecom/ECOM_MAP|ECOM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
