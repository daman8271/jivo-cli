# flipkart-portal — read-only Flipkart explorer CLI

Generated from the vault READ allowlist (`../captures/wired-reads.tsv`). **216 read commands across
24 groups**, plus `doctor`, `auth`, `list`. It reads over Flipkart's Seller Hub + Vendor Hub and
**cannot write** — the transport refuses any verb but `GET`.

## Build & test

```sh
cd portals/flipkart/cli
go build -o flipkart-portal .
go test ./...        # guardrail_test.go + guardrail_coverage_test.go — both green
./flipkart-portal doctor
```

## Three-layer read-only guarantee (code-level, deny-by-default)

1. **Transport** (`client.go` `guardMethod`) — the HTTP client throws before opening a socket for
   any method other than `GET`. There is no login/write path in the binary at all.
2. **Path guard** (`forbiddenPath`) — even a `GET` is refused if its path contains a mutating verb
   segment (`create/update/delete/upload/generate/activate/suspend/...`, incl. camelCase like
   `generateReport`).
3. **Allowlist + tests** — `registry.go` is generated to contain **only** `READ`/`READ_FILE`
   endpoints. `guardrail_coverage_test.go` fails the build if any wired row is not a GET READ, or if
   any wired path contains a write verb. `guardrail_test.go` proves writes are blocked and reads pass.

## Session (consume, never mint — G9)

The CLI reads the existing session jar from the environment; it never logs in:

```sh
export FLIPKART_VENDOR_COOKIE='access_token=…; _csrf=…'   # from the production login on HO-IT-PC10
export FLIPKART_VENDOR_CSRF='…'                            # x-csrf-token (Vendor Hub)
export FLIPKART_SELLER_COOKIE='T=…; connect.sid=…; sellerId=…; …'
```

A dead session yields `HTTP 401/403` and a re-login hint — the CLI will **not** attempt a login.

## Usage

```sh
./flipkart-portal list                                  # every wired endpoint
./flipkart-portal list --group vendor-users-access
./flipkart-portal vendor-users-access vendor-list --json
./flipkart-portal vendor-purchase-orders purchase-orders --param status=new --param page_size=50 --json
./flipkart-portal report-centre reportcategories --json
# path {id} params:
./flipkart-portal <group> <cmd> --id <value> --param k=v --json
```

## Scope & honesty

- All **216 READ/READ_FILE** endpoints are wired and are issued as `GET`. A handful are actually
  **POST-backed on the server** (`graphql`, `getReportsV2`, `getReportsCount`,
  `vendor/feeds/download-feed-file`); a `GET` to those returns `405/404` — harmless, never a write.
  They stay in the registry for catalogue completeness, but to read them you need the app's own POST
  (a live browser walk, Amendment-02), not this GET-only CLI. Everything the CLI *can* exercise, it
  exercises safely.
- Report *generation* / export / any mutation is **never** exposed (see
  `../vault/_meta/Read-Only-Guardrails.md`).
- Full endpoint map + classification: `../vault/Flipkart-Endpoints.md`.
