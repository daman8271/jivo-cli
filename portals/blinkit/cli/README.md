# blinkit-partner

A **read-only** Go CLI for the Blinkit **PartnersBiz** (Partner) portal
(`https://www.partnersbiz.com`), entity **Jivo Wellness** (`x-entity-id: 1117`,
`manufacturer`). It is the read surface generated from the reverse-engineered
endpoint inventory in `../vault/partner/Partner-Endpoints.md`.

## Read-only law

Every command is a **READ**: a `GET`, a POST-to-read (list/search/count), or a
poll-and-download of an *already-generated* report. **No** create/update/delete/
upload/approve/cancel/dispute is wired. Three layers enforce this:

1. **No write methods** exist on the HTTP client.
2. `forbiddenPath()` hard-errors before any request if the method+path matches an
   out-of-scope write or a non-sanctioned report export (defense-in-depth).
3. HTTP method allowlist: only `GET` and `POST` are ever constructed.

The **only** sanctioned side-effects are `sales pull` and `soh pull` — they
enqueue a report **and email a copy to the account owner**, so they are gated
behind an explicit `--export` flag (and `--yes-export` in `--agent` mode). The
pure-read alternatives (`sales table`, `soh queue`/`latest`/`download`) have no
side-effects and are preferred.

## Auth

Credentials are inherited, never invented. Resolution order (env wins):

- `BLINKIT_TOKEN`, `BLINKIT_API_KEY`, `BLINKIT_ENTITY_ID`, `BLINKIT_ENTITY_TYPE`,
  `BLINKIT_BASE`
- else the **existing shared** config at
  `~/Library/Application Support/blinkit-cli/config.json` on macOS —
  `%AppData%\blinkit-cli\config.json` on Windows (written by the
  original `blinkit-cli auth import`).

The `access_token` (`v2::<uuid>`) is **short-lived**. On any `401` every command
prints:

> token expired: refresh with `blinkit-partner auth import <curlfile>` or
> re-run orchestrate/blinkit-login.sh

Refresh a token unattended with
`~/ecomcliauto/orchestrate/blinkit-login.sh` (email-OTP via himalaya on
`tanuj@jivo.in`), then either it writes the shared config directly or you run
`blinkit-partner auth import <captured-curl>`.

## Global flags

- `--json` — pretty JSON output.
- `--agent` — implies `--json`, silences stderr progress, and wraps output in a
  stable envelope `{ok, command, endpoint, count, data|error}` for deterministic
  parsing by a dispatched agent.
- `--company` — friendly entity selector (default `jivo` → `1117`/manufacturer,
  `manufacturer_id 176`). Unknown value is a clear error.

## Build

```sh
cd /Users/damanpreetsingh/jivo-cli/portals/blinkit/cli
go build -o blinkit-partner .        # macOS/Linux → ./blinkit-partner
go build -o blinkit-partner.exe .    # Windows     → blinkit-partner.exe
```

Run it as `./blinkit-partner <cmd>` on macOS/Linux, `blinkit-partner.exe <cmd>`
on Windows (the command names below are identical on both).

## Commands

```
doctor                         config → token → one live read (report count + granted entity tabs)

auth import <curlfile>         extract creds from a captured cURL into the shared blinkit-cli config
auth login                     [DEFERRED] email-OTP — use orchestrate/blinkit-login.sh

reports list [--type --state --limit]       list the async report queue (newest first)
reports download <id> [--out]               mint presigned URL + download a completed report
reports url <id>                            print a freshly-minted presigned URL (no fetch)

sales table [--from --to --offset --limit --body]   PURE-READ sell-out grid (recommended default)
sales pull  [--from --to --out --timeout --export --yes-export]   [EXPORT] generate→poll→download CSV

soh queue [--limit]                         SOH rows in the report queue (pure read)
soh latest [--out]                          download the newest successful SOH report
soh download <id> [--out]                   download a specific SOH report
soh pull [--out --timeout --export --yes-export]     [EXPORT] live SOH snapshot CSV

po list [--status --facility --city --vendor --po-number --order-by --limit --offset --body]
po get <po_number>                          single PO detail
po items <po_id>                            line items in a PO
po grn [--po-number]                        GRN details
po invoices [--po-number]                   invoices tied to a PO
po delivered [--po-number]                  delivered-item count
po count [filters]                          aggregated PO count  (method to confirm)
po amount [filters]                         aggregated PO amount (method to confirm)
po facets-cities                            city filter dropdown values
po facets-facilities                        facility filter dropdown values
po amendments [--body]                      list existing amendments (read only)
po amendment-items [--body]                 items available for amendment (read only)
po pod --po-numbers <csv> [--out]           download POD PDF(s)
po pdf [--po-numbers <csv>] [--out]         download bulk PO PDF zip

invoices reports [--limit]                  'Invoices Excel' rows in the queue (proven)
invoices download <id> [--out]              download bulk_invoice_csv-<id>.csv
invoices summary                            [DEFERRED] path to confirm
invoices detail                             [DEFERRED] path to confirm

payments invoices [--status --from --to --body]       invoice/payment list (v2)
payments invoice-details [--invoice-id --order-number --body]
payments grn [--invoice-id --body]          GRN line items behind an invoice
payments utr [--invoice-id --body]          UTR / bank settlement reference
payments aggregate [--from --to --body]     headline payout totals
payments charges [--gran --from --to --status --body]  fees & charges list
payments charge <id>                        single charge detail
payments charges-summary                    summary tiles
payments charges-stats                      stat totals
payments charges-filters                    filter options
payments advice [--from --to --out]         payment-advice remittance ZIP
payments invoice-download [--invoice-id --out --body]  single invoice PDF (POST-to-read)

offers summary                              Total Spend + Unique Products cards
offers cities                               brand-fund city reference list
offers history [--from --to --state --limit --offset]  single-offer upload history
offers sheet <sheetId> [--row --limit]      single offer — row-wise detail
offers sheet-rows <sheetId>                 single offer — row list
offers bundle-sheet <sheetId> [--row --limit]          bundle offer — row-wise detail
offers bundle-sheet-rows <sheetId> [--limit --offset]  bundle offer — row list
offers jobs                                 bulk-upload job status list

appointments stats                          Pending/Upcoming/Fulfilled counters
appointments list [--tab --facility --po --from --to --body]   appointments grid
appointments cancel-info [--po]             reads cancellability (does NOT cancel)
appointments couriers                       courier dropdown options
appointments invoices [--po --body]         invoices for PO(s)
appointments slots [--po --body]            inspect available slots (no booking)
appointments existing [--po --body]         existing appointments (club/merge)
appointments clubbing-charges [--po --into] preview merge charges only

scorecard reports [--limit]                 Scorecard / Top-5-Potential-Loss queue rows (proven)
scorecard download <id> [--out]             download a completed scorecard report
scorecard summary                           [DEFERRED] ScoreCard panel — path to confirm
scorecard fill-rate                         [DEFERRED] ScoreCard panel — path to confirm

assortment tabs                             entity-tab gate check for entity 1117
assortment reports [--limit]                generic report-queue view
assortment list                             [DEFERRED] assortment data feed — path to confirm
```

## Deferred endpoints

Some feeds have a binding but no directly-observed method/path (invoices
summary/detail, scorecard summary/fill-rate panels, the SOH inline grid, the
assortment data feed, `auth login` request-OTP). They are present in the tree so
it is complete, but each returns an `endpoint to confirm — capture live first`
notice rather than guessing a path. Promote them once a live authenticated
network capture confirms the contract.

## Notes

- The report download path contains an intentional literal double slash
  (`/v1/report-requests/download//{id}/`) — do not "fix" it.
- The `{status:1,data}` envelope is asserted **only** for `report-requests` and
  `get-sales-details` (proven). Every other endpoint uses the raw
  status-checked reader, so unconfirmed schemas print honestly.
- For POST list endpoints whose exact filter body is unconfirmed, pass
  `--body '<raw JSON>'` to override the minimal built body.
