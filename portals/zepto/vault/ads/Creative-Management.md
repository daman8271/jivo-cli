---
title: Creative Management
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, ads, creative-management]
status: studied
---

# Creative Management

The **Creative Management** section is the ads-lane's **creative + asset surface** for the campaign
builder: it enumerates the ad-unit **inventory / placements** an advertiser can book, the existing
**creative banners** for a brand, the **asset formats / bundle-config** (dimensions, targeting-audience
reach a creative can serve), the saved **campaign bundles** (v1 + v2 — a bundle is a packaged set of
creative assets reused across campaigns), the per-brand creative **metadata**, and the **AI
banner-generation** jobs (list + status-by-id) that back the "generate a banner" walkthrough. It is the
step between picking a brand/audience ([[Brands-Audiences]]) and booking a campaign
([[Ads-Campaigns-Booking-Keywords]]): here the advertiser assembles/chooses the visual assets (banners, bundles) that a
booking then attaches to inventory. For JIVO this is Jivo Wellness Pvt. Ltd. (Manufacturer, STANDARD
tier, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`), ads brand **Jivo**
`brand_id b3550d5d-fc71-47b0-af4f-f221f909b936`, login `ecom1@jivo.in`. Every call hits the **ads-BFF
mounted on `fcc.zepto.co.in`** (constants built with the `ads-bff/api/v1/...` prefix; the v2 bundles
list uses `ads-bff/api/v2/...`). Auth is the single Zepto JWT in the `authorization` header (**no**
`Bearer` prefix), the same token that works across every Zepto backend; WAF headers were not enforced
at last verified capture. Endpoint contracts below were extracted from the ads code-split webpack chunk
**`captures/js/ads/1183.8940422c8268d8dc.js`** — the `CREATIVE_MANAGEMENT` constant map (`u={…}` +
getter fns) and the neighbouring `CAMPAIGN_CONFIG` map (bundle/asset-format consts) — **not** live
captures (see the probe note under Evidence).

## SPA route(s)

- `/ads/creative-manager` — the Creative Manager landing (creative/banner + bundle assembly surface,
  entered from the campaign-create walkthrough).

## Backend hosts

- `fcc.zepto.co.in` — ads-BFF (`/ads-bff/api/v1/...`, plus `/ads-bff/api/v2/...` for v2 bundles); the
  only host this section talks to. One JWT (`authorization: <jwt>`, no `Bearer`) authorizes it; WAF
  headers were not enforced at last verified capture (a probe on 2026-07-23/24 with an already-expired
  token returned HTTP 429 — see Evidence).

## What the section exposes (concepts)

- **Inventory / ad-units** — the bookable ad-unit placements a creative can serve into
  (`GET_INVENTORY_AD_UNITS` → `inventory/details`).
- **Creative banners** — the existing banner creatives for a brand (`GET_CREATIVE_BANNERS` →
  `banners`). Creating/saving a new banner (`CREATE_BANNERS`, POST) is a **write** — held out of scope.
- **AI banner generation** — list AI-generated banner jobs (`BANNER_GENERATION`, GET, returns
  `{banners:[], total:…}`) and fetch one job by id (`BANNER_GENERATION_BY_ID`, GET). **Triggering** a
  generation (POST `banner-generation?brand_id=`) is a side-effecting generate — held out of scope.
- **Asset formats & bundle-config** — the creative asset formats / dimension config plus the
  targeting-audience reach a bundle can serve (`GET_CAMPAIGN_ASSETS_FORMATS` /
  `GET_USER_TARGETING_AUDIENCE_REACH` → `bundle-config`).
- **Campaign bundles** — the saved creative bundles reused across campaigns, v1 paged list
  (`GET_EXISTING_CAMPAIGN_BUNDLES` → `bundles`, params `{page, brand_id, limit:6}`) and v2
  (`GET_EXISTING_CAMPAIGN_BUNDLES_V2` → `v2/…/bundles`, params `{campaign_type, ad_format_id, …}`).
  **Uploading** assets into a bundle (`POST_UPLOAD_ASSETS` / `_V2`, POST to the same `bundles` path)
  is a write — held out of scope.
- **Creative metadata** — per-brand creative metadata (`GET_METADATA(brand_id)` → `metadata?brand_id=`).

## READ endpoints

Base = `https://fcc.zepto.co.in/` + path. Paths shown as stored in the bundle; constants are given for
traceability. `${e}` / `{brand_id}` = a brand id (for JIVO, brand `b3550d5d-fc71-47b0-af4f-f221f909b936`);
`${id}` = a banner-generation job id. Method column: `GET` = declared `.get(...)` in the chunk. None
probed live (token expired at capture; all remain **documented, not probed** — see Evidence).

| METHOD | Path | Purpose (const) | Read/Write |
|---|---|---|---|
| GET | `/ads-bff/api/v1/creative-management/inventory/details` | Bookable ad-unit inventory / placements (`GET_INVENTORY_AD_UNITS`) | READ |
| GET | `/ads-bff/api/v1/creative-management/banners` | Existing creative banners for a brand (`GET_CREATIVE_BANNERS`) | READ |
| GET | `/ads-bff/api/v1/creative-management/metadata?brand_id=${e}` | Per-brand creative metadata (`GET_METADATA(brand_id)`) | READ |
| GET | `/ads-bff/api/v1/creative-management/bundle-config` | Creative asset formats + targeting-audience reach config (`GET_CAMPAIGN_ASSETS_FORMATS` / `GET_USER_TARGETING_AUDIENCE_REACH`) | READ |
| GET | `/ads-bff/api/v1/creative-management/bundles` | Existing campaign bundles, v1 paged list, params `{page,brand_id,limit:6}` (`GET_EXISTING_CAMPAIGN_BUNDLES`). NOTE: same path also serves `POST_UPLOAD_ASSETS` (write, out of scope) | READ |
| GET | `/ads-bff/api/v2/creative-management/bundles` | Existing campaign bundles, v2 list, params `{campaign_type,ad_format_id,…}` (`GET_EXISTING_CAMPAIGN_BUNDLES_V2`) | READ |
| GET | `/ads-bff/api/v1/creative-management/banner-generation/${id}` | Single AI banner-generation job by id (`BANNER_GENERATION_BY_ID`; status/result read — not probed, name contains "generation") | READ |

## Out of scope (writes / exports) — never expose in a read-only CLI

| METHOD | Path | Purpose (const) | Class |
|---|---|---|---|
| POST | `/ads-bff/api/v1/creative-management/banner` | **Create / save** a creative banner (`CREATE_BANNERS`) — persists a new banner | WRITE |
| POST | `/ads-bff/api/v1/creative-management/banner-generation?brand_id=${e}` | **Trigger** an AI banner-generation job (`BANNER_GENERATION`, POST-with-body) — side-effecting generate. (A GET on the same base path lists existing jobs `{banners:[],total}`, but the endpoint's write verb is held out per the generate guardrail.) | WRITE / generate |
| POST | `/ads-bff/api/v1/creative-management/bundles` (+ v2) | **Upload / save** assets into a campaign bundle (`POST_UPLOAD_ASSETS` / `POST_UPLOAD_ASSETS_V2`) — persists new creative assets; shares the `bundles` path with the v1 READ above | WRITE / upload |

These are held out of scope per [[Read-Only-Guardrails]]: `CREATE_BANNERS` and `POST_UPLOAD_ASSETS`
mutate ads state (persist banners / upload assets), and `BANNER_GENERATION` (POST) triggers an AI
generate — a strict read-only CLI must not fire any of them. The `banner-generation` **GET** list and
`banner-generation/${id}` GET are true reads, but were not probed (name contains "generation", excluded
by the read-only probe allowlist).

## Evidence

- **Endpoint set** extracted from the ads code-split chunk **`captures/js/ads/1183.8940422c8268d8dc.js`**
  — the `CREATIVE_MANAGEMENT` constant object `u={GET_INVENTORY_AD_UNITS, GET_CREATIVE_BANNERS,
  CREATE_BANNERS, BANNER_GENERATION, BANNER_GENERATION_BY_ID:e=>`…/banner-generation/${e}`,
  GET_METADATA:e=>`…/metadata?brand_id=${e}`}` and the `CAMPAIGN_CONFIG` map
  (`GET_CAMPAIGN_ASSETS_FORMATS` + `GET_USER_TARGETING_AUDIENCE_REACH` → `bundle-config`,
  `GET_EXISTING_CAMPAIGN_BUNDLES` → `bundles`, `GET_EXISTING_CAMPAIGN_BUNDLES_V2` → `v2/…/bundles`,
  `POST_UPLOAD_ASSETS` / `_V2`). Method verbs read from the surrounding `.get(...)` / `.post(...)`
  call-sites in the same chunk. Source of truth = the JS corpus on disk.
- **Live probe (read-only, halted):** on 2026-07-23/24 a single
  `GET https://fcc.zepto.co.in/ads-bff/api/v1/creative-management/inventory/details?brand_id=…` was
  fired with the only available JWT (`ecom1@jivo.in`, `exp 2026-07-13 18:29:59 UTC` — **expired**).
  Response = **HTTP 429**. Per the guardrail (stop on any 401/403/429), probing halted immediately after
  probe 1; **no endpoint upgraded to PROVEN**, all remain **documented (not probed)**. Transcript:
  `captures/ads/creative-management-probes.txt`.
- **Request/response bodies uncaptured** — no `captures/ads/*.json` exists for any creative endpoint yet;
  the banner-list schema, the `bundle-config` asset-format shape, and the bundles v1/v2 row schema want
  a live (read-only) capture with a fresh token to finalise.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no banner create, no asset upload, no generate trigger):

- `zepto creative inventory` → `GET /ads-bff/api/v1/creative-management/inventory/details`.
- `zepto creative banners <brandId>` → `banners`; `zepto creative metadata <brandId>` →
  `metadata?brand_id=`.
- `zepto creative bundle-config` → `bundle-config` (asset formats + audience reach).
- `zepto creative bundles <brandId> [--page N]` → `bundles` (v1); `zepto creative bundles-v2
  [--campaign-type … --ad-format …]` → `v2/…/bundles`.
- `zepto creative generation <jobId>` → `banner-generation/${id}` (read the status/result of an existing
  AI banner-generation job only — never trigger one).

Explicitly **excluded**: `CREATE_BANNERS` (create banner), `BANNER_GENERATION` POST (trigger AI
generate), and `POST_UPLOAD_ASSETS` / `_V2` (upload bundle assets).

## Connections

- Index & shared refs: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- **Tightest siblings** (same ads BFF): audiences/brands that feed a creative in [[Brands-Audiences]];
  the campaign booking that attaches these bundles/banners to inventory in [[Ads-Campaigns-Booking-Keywords]]; creative
  spend/wallet in [[Ads-Billing-Wallet]]; creative performance in [[Brand-Analytics]]; geo/consumer
  overlays in [[Market-Geo-Consumer-Insights]] and engagement creatives in [[Engagement]].
