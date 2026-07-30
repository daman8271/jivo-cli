# amazon-portal — read-only CLI

A **GET-only** command-line window into JIVO's Amazon Seller Central (and the documented Vendor
Central) read surface. Generated from the portal study in `../vault`.

## Read-only guarantee (three layers, deny-by-default)

1. **Transport** (`client.go`) — `forbidden()` refuses any HTTP method other than `GET` *before a
   socket opens*, and refuses any `signout`/`logout`/`token-refresh` path.
2. **Allowlist** (`endpoints_gen.go`) — only the 141 paths classified `READ`/`READ_FILE` in the
   vault are reachable; a GET to anything else is denied. No path with a write-verb segment
   (`create`/`edit`/`submit`/…) is in the list, and a backstop scan rejects one if it ever appears.
3. **Tests** (`guardrail_test.go`, `guardrail_coverage_test.go`) — assert (a) non-GET is refused,
   (b) known write / POST-read / session paths are blocked, (c) every wired command maps to a READ
   row in `../captures/wired-reads.tsv`, (d) no write-verb segment is wired.

The binary **consumes** the existing Seller Central cookie jar (`~/ecomcliauto/auth/login/out/
amazon-mp.cookies.json`, or `$AMAZON_SC_COOKIE_JAR`). It **never logs in** (G9).

## Build & run

```sh
go build -o amazon-portal .
go test ./...                     # guardrail + coverage tests
./amazon-portal doctor            # is the consumed session live?
./amazon-portal auth whoami       # entity + jar (no secrets)
./amazon-portal --help            # 17 section groups
```

## Examples (all live-verified reads)

```sh
./amazon-portal coupons-promotions coupons-getcouponpromotions   # 18 promotions (16 expired, 2 cancelled)
./amazon-portal coupons-promotions coupons-merchantinfo          # coupon rights
./amazon-portal feedback-manager fbmapi-aggregates               # seller feedback 3.8★ lifetime / 73 reviews
./amazon-portal account-health-performance performance-api-summary   # ODR / claims / chargebacks
./amazon-portal global-selling-expansion account-switcher-merchantMarketplace   # entity model
./amazon-portal --pretty=false orders orders-api-search           # raw JSON
```

## Command groups (17)

`account-health-performance` · `business-reports-analytics` · `coupons-promotions` ·
`feedback-manager` · `global-selling-expansion` · `help-support-center` · `homepage-widgets` ·
`inventory-fba` · `listings-asin-management` · `messaging-buyer-seller` · `orders` ·
`platform-common` · `product-classification` · `purchase-orders` · `retail-analytics-ara` ·
`vc-catalog-products` · `vc-support-help`

## What is deliberately NOT here

- **POST-bodied reads** (`/myinventory/gql`, `/business-reports/api`, `/orders-api/countOrders`,
  `/homepage/casino/data`) — documented as `READ_POST` in the vault, never wired (the CLI is
  GET-only). Their data appears in `../vault/Amazon-Data-Inventory.md`, captured via the live walk.
- **Every write** — coupon create/edit/cancel, listing create/write-offer, report generation
  (enqueue = write, G2), user invite, appeals submit. Catalogued in each section's *Out of scope*
  table.
- **Vendor Central live calls** — wired as commands but will report a session error until a VC
  session exists (expired this run; see `../vault/_meta/Auth-and-Access.md`).

## Regenerating

`endpoints_gen.go` is generated from `../captures/wired-reads.tsv`. If the study's allowlist
changes, regenerate the slice and re-run `go test ./...` — the coverage test will fail if any
wired command is not a READ row.
