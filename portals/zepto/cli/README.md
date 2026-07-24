# zepto-portal

A **read-only** Go CLI for JIVO's **Zepto seller portal** (`brands.zepto.co.in`),
entity **Jivo Wellness Pvt. Ltd.** (Manufacturer, STANDARD tier). It is the read
surface generated from the reverse-engineered endpoint inventory in
`../vault/Zepto-Endpoints.md` (25 sections, 741 endpoints across 7 backends).

## Read-only law

Every command is a **READ**: a `GET`, or a `POST`-to-read (list/search). **No**
create/update/delete/upload/approve/schedule/cancel/pay is wired. Three layers
enforce it:

1. **HTTP method allowlist** — the client only ever constructs `GET` and `POST`.
2. **`forbiddenPath()`** hard-errors before any request if the URL path has a
   write-verb segment (`create`, `schedule`, `cancel`, `modify-access`,
   `counterpart`, …) — segment-boundary matched, so `po/scheduled` (read) is
   never confused with `po/schedule` (write). See `guardrail_test.go`.
3. **Command tree** — only READ-classified endpoints are wired as commands.

The one sanctioned side-effect is `reports request` (it *generates* a vendor
report — creates a queue row); it is gated behind an explicit `--export` flag
(and `--yes-export` in `--agent` mode). Prefer `reports list` / `reports
download` (pure reads of already-generated reports).

## Auth

One JWT (`authorization` header, **no** `Bearer` prefix) authorizes every
backend. Credentials are inherited, never invented — resolution order (env wins):

- `ZEPTO_JWT`, `ZEPTO_BASE`, `ZEPTO_ADS_BASE`, `ZEPTO_BRAND_ID`
- else the **existing shared** config at
  `~/Library/Application Support/zepto-cli/config.json` (written by
  `zepto-cli auth import` / `zepto-login.sh`).

The JWT is **daily** (expires 23:59:59 IST). On any 401/403 every command prints:

> token expired (Zepto JWT expires 23:59:59 IST daily): refresh with
> `bash ~/ecomcliauto/orchestrate/zepto-login.sh` or
> `zepto-portal auth import <curlfile>`

⚠️ Zepto is **single-concurrent-session**: a later login on `ecom1@jivo.in`
(e.g. the 10:00 daily cron, or a human) invalidates an earlier token even before
its `exp`. Re-mint if reads start 401ing.

## Build

```sh
cd portals/zepto/cli && go build -o zepto-portal .
```

## Usage

```sh
./zepto-portal doctor                 # config + JWT + one live read
./zepto-portal auth status            # JWT identity + expiry
./zepto-portal <section> <command>    # e.g. po list, reports list, catalog list
./zepto-portal <section> --help       # per-section command list
```

Global flags: `--json` (pretty JSON), `--agent` (stable
`{ok,command,endpoint,count,data|error}` envelope, quiet stderr).

### Section command groups (mirror the study)

**Vendor:** `po` · `reports` · `asn` · `release-orders` · `rtv` · `catalog` ·
`stock` · `invoicing` · `contracts` · `payments` · `ledger` · `receivables` ·
`fbz`
**Ads:** `brands` · `creative` · `campaigns` · `wallet` · `brand-analytics` ·
`insights` · `engagement`
**Platform:** `identity` · `users` · `subscription` · `kyc` · `platform`

Every group's endpoints, methods, and read/write classification are documented
in `../vault/<Section>.md` and the master `../vault/Zepto-Endpoints.md`.

## Notes

- Some list/grid endpoints take a raw `--query "k=v&k2=v2"` (their exact filter
  params were bundle-derived, not yet live-confirmed).
- Path-templated detail endpoints take the id as a positional arg
  (`po get <po_id>`, `campaigns detail <campaign_id>`).
- stdlib + cobra only; no other dependencies.
