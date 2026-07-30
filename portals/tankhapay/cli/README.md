# tankhapay-portal — read-only CLI for the TankhaPay Business portal

Read-only command-line access to **JIVO's TankhaPay** HR/payroll portal
(`business.tankhapay.com`, an HR SaaS by Akal Information Systems). One JWT — auto
minted daily from `.env` — authorizes all four backends. Every command is a
**read**; a three-layer guardrail makes a mutation impossible to send.

> ⛔ **READ-ONLY.** This CLI holds live payroll data for **593 real employees**. It
> never creates/updates/deletes/saves/approves/pays/uploads/submits anything. The
> only non-read call in the entire binary is the sanctioned login token exchange.

## Install

```sh
cd ~/jivo-cli/portals/tankhapay/cli
go build -buildvcs=false -o ~/go/bin/tankhapay-portal .   # macOS/Linux — on PATH
go build -buildvcs=false -o tankhapay-portal.exe .        # Windows — run from this folder, or move onto PATH
```

Credentials come from a gitignored `.env` at the portal root (never hardcoded):

```
TPAY_USERNAME=shunty@jivo.in
TPAY_PASSWORD=********
TPAY_BODY_KEY=0123456789abcdef
# backend bases are defaulted; override only if they move:
# TPAY_API / TPAY_EMPLOYER_API / TPAY_PAY_API / TPAY_TND_API
```

Environment variables win over `.env`. The 24h JWT is cached at
`~/.config/tankhapay-portal/token.json` (0600); the CLI re-logs-in only when it is
missing or expired (capped to one login per run to avoid lockout).

## Quick start

```sh
tankhapay-portal doctor                       # config + token + one live read
tankhapay-portal auth whoami                   # cached token's account context (offline)
tankhapay-portal <group> <command> [flags]     # any read
```

```sh
# headline dashboard (593 employees):
tankhapay-portal dashboard tpay-dashboard-data --set action=get_employee_list
# master data:
tankhapay-portal org all-state
```

## How reads are shaped

Every read is an AES-encrypted POST. The CLI auto-injects the account context it
decoded from your JWT — `accountId`, `geo_location_id`, `ouIds` — into each
payload, so most list reads work with no arguments. Provide the rest per-endpoint:

- `--set key=value` (repeatable). Values may reference context tokens:
  `@accountId @geo @ouIds @productType @userid`.
  e.g. `--set customerAccountId=@accountId --set financialYear=2025-2026`
- `--body '{...}'` — supply the whole JSON payload yourself (overrides `--set`).
- `--no-ctx` — do not auto-inject account context.

The exact payload each endpoint expects (field names, which need `customerAccountId`,
the AES-encrypted `CJHUB` employee key, date formats, etc.) is documented per
section in the study vault at `../vault/<Section>.md`.

Output: pretty JSON by default; `--json` / `--agent` for a stable
`{ok,command,endpoint,count,data|error}` envelope. `TP_DEBUG=1` prints the exact
request payload to stderr.

## Command groups (297 read endpoints across 14 sections)

| Group | Reads | Group | Reads |
|---|--:|---|--:|
| `dashboard` | 7 | `reports` | 46 |
| `employee` | 53 | `recruit` | 9 |
| `attendance` | 37 | `masters` | 33 |
| `leave` | 19 | `org` | 25 |
| `payouts` | 11 | `broadcast` | 13 |
| `approvals` | 19 | `contract` | 9 |
| `accounts` | 8 | `training` | 8 |

Run `tankhapay-portal <group> --help` to list a group's commands.

## The read-only guarantee (3 layers)

1. **Only reads are wired.** Commands are generated *only* from the 297 endpoints in
   `../captures/wired-reads.tsv` = 287 confirmed reads + 10 hand-vetted reads promoted
   from UNKNOWN. The 35 rows the extractor mis-tagged as READ but which are actually
   writes (`saveDesignation`, `disburseLiability`, `verify_OTP`, …) are excluded
   (`../captures/reclassified-writes.tsv`), and **61 UNKNOWN endpoints were deliberately
   held out** (`../captures/unknown-excluded.tsv`) — they are behavioral writes / auth /
   dual-mode `manage_*` endpoints that the read-only vow forbids wiring on a guess.
2. **`forbiddenPath` fails closed.** Before any request leaves the process, the
   method+path is scanned for write verbs (`client.go`); anything that looks like a
   mutation, or any method other than GET/POST, is refused.
3. **No mutating code path exists.** `doRead` only ever POSTs an encrypted read; no
   PUT/PATCH/DELETE is implemented anywhere.

`go test ./...` enforces all three: it proves the wired set equals the inventory
1:1 (no unwired read, nothing extra), that every wired path passes the guardrail
(no dead commands), and that all 35 reclassified writes are blocked.

## Regenerate the command tree

The command files are generated from the inventory — edit the manifest, not the
generated `cmd_*.go`/`wired_manifest.go`:

```sh
python3 ../scripts/gen_commands.py && go build -buildvcs=false -o ~/go/bin/tankhapay-portal .   # macOS/Linux
python3 ../scripts/gen_commands.py && go build -buildvcs=false -o tankhapay-portal.exe .        # Windows
```

## Files

```
cli/
  crypto.go client.go auth.go jwt.go config.go   # AES-ECB cipher, guardrail, headless login, token cache
  output.go helpers.go registry.go root.go main.go doctor.go cmd_auth.go
  wired_manifest.go cmd_<section>.go             # GENERATED (scripts/gen_commands.py)
  guardrail_test.go guardrail_coverage_test.go   # read-only + coverage proofs
../vault/                                         # Obsidian study vault (per-section endpoint docs)
../captures/                                      # inventory + JS corpus the CLI was generated from
```
