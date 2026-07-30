---
title: Marketplace-Seller-API-unused
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, public-api, unused, read-only]
status: documented
---

# Marketplace Seller API (`api.flipkart.net/sellers`) — the 4th surface, UNUSED by JIVO

> ⚠️ READ-ONLY documentation. This surface is **not** in the SPA JS corpus (confirmed: the Seller
> Hub bundles reference `seller.flipkart.com`, never `api.flipkart.net`). It is Flipkart's
> **published partner API**, catalogued here from JIVO's own spec
> (`~/ecomcliauto/clis/flipkart-seller-api-cli/spec.yaml`) so the complete surface is on record.
> **JIVO has never used it** — no `FLIPKART_CLIENT_ID` / `FLIPKART_CLIENT_SECRET` exists on disk.
> These rows are **not** counted in [[Flipkart-Endpoints]]'s 968 (that count is the live SPA corpus);
> this is a distinct, documented-from-spec surface.

- **Base:** `https://api.flipkart.net/sellers`
- **Auth:** OAuth2 `client_credentials` → `https://api.flipkart.net/oauth-service/oauth/token`,
  scopes `Seller_Api`, `Default`, then `Authorization: Bearer <token>`. (Not the SPA cookie jar.)
- **Why it matters:** it is a *different product* from the internal SPA API — not a newer generation.
  If JIVO ever wanted a supported, rate-limited, contract-stable integration (vs scraping the SPA),
  this is it. Documented so the option is visible.

## Endpoints (from spec — READ vs WRITE)

| R/W | METHOD | Path | Purpose |
|---|---|---|---|
| READ | GET | `/v3/shipments` | list shipments (health path) |
| READ | GET | `/v3/shipments/{shipmentIds}` | shipment detail |
| READ | GET | `/v3/shipments/{shipmentIds}/labels` | fetch existing labels |
| READ | GET | `/v3/shipments/{shipmentIds}/invoices` | fetch existing invoices |
| READ | GET | `/v3/shipments/handover/counts` | handover counts |
| READ | POST | `/v3/shipments/filter/` | search shipments (POST-read) |
| READ | GET | `/listings/v3/{skuIds}` | listing detail by SKU |
| READ | POST | `/listings/v3/details` | listing details (POST-read) |
| READ | POST | `/listings/v3/search` | listing search (POST-read) |
| READ | GET | `/v2/returns` | list returns |
| WRITE | POST | `/v3/shipments/labels` | **create labels** — out of scope |
| WRITE | POST | `/v3/shipments/dispatch` | dispatch shipments — out of scope |
| WRITE | POST | `/v3/shipments/cancel` | cancel — out of scope |
| WRITE | POST | `/v3/shipments/manifest` | manifest — out of scope |
| WRITE | POST | `/v3/shipments/selfShip/dispatch` | self-ship dispatch — out of scope |
| WRITE | POST | `/v3/shipments/selfShip/delivery` | self-ship delivery — out of scope |
| WRITE | POST | `/listings/v3` | create listing — out of scope |
| WRITE | POST | `/listings/v3/update` | update listing — out of scope |
| WRITE | POST | `/listings/v3/update/price` | **price change** — live money, out of scope |
| WRITE | POST | `/listings/v3/update/inventory` | inventory change — out of scope |
| WRITE | POST | `/v2/returns/approve` · `/reject` · `/complete` · `/pickup` | return actions — out of scope |
| EXPORT | POST | `/reports/{reportTypeIdentifier}` | **generate a report** (enqueue) — out of scope (G2) |
| READ | GET | `/reports/{reportId}/detail` | poll an existing report — read |

## Adjacent Flipkart hosts referenced from the Seller Hub SPA (documented, not studied)

The Seller Hub bundle also links out to these hosts (link-outs / embedded surfaces, not the seller
data API — recorded for completeness):

| Host | What it is |
|---|---|
| `www.partner.flipkart.com` (26 refs) | Partner portal / partner services |
| `advertising.flipkart.com` (1) | Flipkart Ads platform (self-serve ads console) |
| `brandhub.flipkart.com` (1) | Brand Hub (brand/co-op marketing) |
| `dl.flipkart.com` (2) | Download/deep-link host |
| `www.flipkart.com` (66) | Consumer storefront (product PDPs) |

Each is a candidate for its own future study if JIVO wants that surface mapped; none is exercised
here.

## Connections
[[00-Flipkart-Atlas]] · [[Flipkart-Endpoints]] · [[Report-Centre]] · [[Auth-and-Access]]
