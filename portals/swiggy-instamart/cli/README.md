# `swiggy-instamart-portal` — read-only CLI

Generated from the READ allowlist in `../vault/Swiggy-Instamart-Endpoints.md`.

```bash
go build -o swiggy-instamart-portal .
./swiggy-instamart-portal doctor        # session, clock, allowlist size
./swiggy-instamart-portal auth whoami   # who the inherited token is, and the 3 account ids
./swiggy-instamart-portal endpoints     # every endpoint this binary may read
```

**76 read commands across 25 section groups**, plus `doctor`, `auth whoami` and `endpoints`.
`go build` is clean and `go test ./...` is green.

## What it will not do

There is no login, no refresh, no logout, no create, update, delete, approve, cancel, pay, upload,
book, or generate-a-report command — not disabled, **absent**. Three layers make a mutation
impossible to send:

1. **Transport** (`client.go` → `forbiddenRequest`) — refuses any method other than `GET`/`POST`
   (Swiggy serves most reads over POST, so POST cannot be banned outright), then checks the URL
   against the allowlist and a hard denylist. It throws **before a socket opens**.
2. **Allowlist** (`allowlist.go`, generated) — only the 76 paths the study classified `READ`/
   `READ_FILE` **with a proven HTTP method** are reachable. `WRITE`, `EXPORT` and `UNKNOWN` rows are
   absent by construction, and an explicit `deniedPaths` set is consulted **before** template
   matching so an id placeholder can never admit an excluded sibling.
3. **Tests** — `guardrail_test.go` asserts ~40 write/session/enqueue endpoints are refused
   (including the platform's traps) and that the proven reads are *not*;
   `guardrail_coverage_test.go` asserts every wired command passes the guardrail, that the command
   count equals the allowlist size, and that no write builder exists in the source.

### A real hole these tests caught

`/api/v1/campaign/{0}` is a legitimate READ (sampling campaign detail). Its `{0}` placeholder also
matched the literal segment `batch`, so `/api/v1/campaign/batch` — a **bulk bid and budget
update** — was being admitted by the template matcher. Found by `guardrail_test.go`, not by
review. Fixed by making explicit exclusions beat template matches. Recorded because it is exactly
the class of bug a generated allowlist is supposed to prevent and nearly didn't.

## Auth is inherited, never minted

Tokens come from the config JIVO's existing `swiggy-instamart-cli` already maintains, or from the
environment (see `../.env.example`). Two schemes, and getting them wrong is the easiest 401:

| Host | Header |
|---|---|
| `picker.swiggy.com` (vendor lane) | `Abacus-Token: <jwt>` |
| everything else | `authorization: Bearer <jwt>` |

Calls to `brand-portal-service-http.swiggy.com` additionally need an **HMAC request signature**
over a server-synced timestamp. The pepper is a secret, is **not** in this repo, and is read from
`SWIGGY_SIGN_PEPPER` at runtime.

## The honest limitation

Swiggy runs a **server-side session-activation wall**: a correctly-signed hand-built request is
rejected even when issued from inside the human's own logged-in browser. So while this CLI is a
faithful, safe read surface over the allowlist, on the `brand-portal-service-http` host it will
usually receive `403 "Please reload the browser"`. `doctor` says so plainly rather than pretending.

The authoritative read path for those endpoints is the portal walk in `../captures/walk*/`, where
the application fired its own requests. `partner-api.swiggy.com` (`/time`, `configs`, `account/*`)
and `picker.swiggy.com` (the vendor lane, `Abacus-Token`, no signature observed) do **not** appear
to be behind that wall — the vendor lane is where this CLI is most likely to return live data.

## Regenerating

```bash
python3 ../captures/extract.py     # re-classify from the corpus + live-walk evidence
python3 ../captures/build_cli.py   # regenerate allowlist.go + cmd_*.go
go build -o swiggy-instamart-portal . && go test ./...
```

Never hand-edit `allowlist.go` or `cmd_*.go` — they are generated, and the coverage test fails if
they drift from the inventory.
