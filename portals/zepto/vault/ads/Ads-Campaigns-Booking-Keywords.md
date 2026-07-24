---
title: Ads Campaigns, Booking & Keywords
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, ads, ads-campaigns]
status: studied
---

# Ads Campaigns, Booking & Keywords

The **campaign engine** of Zepto Ads — where JIVO (brand *Jivo*, `brand_id
b3550d5d-fc71-47b0-af4f-f221f909b936`, under manufacturer `946950b7-1ce2-4bdf-a7c4-37499e3f5f34`)
**creates, reviews, forecasts and manages** its sponsored-product (PLA) and display
campaigns, and — one level up — the **media-plan "bookings"** those campaigns roll into.
It is the write-heavy heart of the ads lane: campaign CRUD, booking approval workflow,
keyword/bid tooling, and the two AI copilots (**Jarvis** self-serve assistant, **KAM**
key-account-manager agent). Everything lives on `fcc.zepto.co.in` under the **`/ads-bff/`**
(ads back-end-for-frontend) prefix — note several constants in the bundle drop the
`ads-bff` segment in the string literal but resolve to the same BFF host — authenticated by
the one shared `authorization: <jwt>` header (no `Bearer` prefix) that also unlocks the
vendor-reports and finance backends. Endpoint contracts below were extracted from the ads
remote's code-split chunk `captures/js/ads/1183.8940422c8268d8dc.js` (the campaign/booking
module) — they are the API-constant + getter/action bindings in the bundle, **not** live
captures (see probe note).

This is a **study of JIVO's own seller portal, read-only.** The section is dominated by
mutating verbs (create/edit/approve/reject/submit/status-update campaigns and bookings, plus
the AI-chat `send`); those are **documented from the bundle only** and held out of scope in
the writes table. Only the pure-GET reads (lists, details, metadata, config, suggestions,
forecasts) are candidates for a read-only CLI.

## SPA routes

Ads-remote (module federation remote **632**), all under `/ads`:

- **Booking** — `/ads/booking`, `/ads/booking/create`, `/ads/booking/edit/:bookingId`,
  `/ads/booking/add-media-mix/:bookingId` (the media-plan layer over campaigns).
- **Campaign management** — `/ads/campaign-management` (the campaigns grid),
  `/ads/campaign-management/create`, `/ads/campaign-management/edit` &
  `/edit/:campaignId`, `/ads/campaign-management/duplicate` &
  `/duplicate/:campaignId`, `/ads/campaign-management/duplicate/gamification/:campaignId`,
  `/ads/campaign-management/forecast`.
- **Smart-create** — `/ads/campaign-management/smart-create`,
  `/ads/campaign-management/smart-create/:smartCampaignId` (guided/AI campaign builder).
- **Gamification campaigns** — `/ads/campaign-management/gamification`,
  `/gamification/create`, `/gamification/duplicate`, `/gamification/edit` &
  `/gamification/edit/:campaignId`.
- **Analytics** — `/ads/campaign-management/analytics`,
  `/ads/campaign-management/analytics/:campaignId` (per-campaign metrics; the analytics
  data endpoints themselves live in the sibling [[Brand-Analytics]] note under
  `brands/campaigns/analytics/*`).
- **Ad Elevate** — `/ads/ad-elevate` (promotional/upsell surface).

## Backend

Single host: **`fcc.zepto.co.in`**, all paths under **`/ads-bff/api/v1/`** (ads
back-end-for-frontend). Auth = `authorization: <jwt>` header, no `Bearer` prefix (the same
`ecom1@jivo.in` token used across `fcc` vendor-reports and the finance/auth backends). WAF
headers were **not** enforced at last capture.

## Read endpoints

Base = `https://fcc.zepto.co.in` + path. `{id}` / `{action}` = path params (`${e}`/`${a}` in
the bundle). Method column reflects the getter/`.get()` binding in the chunk; a few list
reads may ride a POST-with-filters body but are **pure reads** (no state change), the same
idiom as the vendor lane. None are PROVEN (see probe note — token expired, 429 on first probe).

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/ads-bff/api/v1/campaigns` | Campaign-management grid — `GET_TABLE_DATA` (list all campaigns for the brand) | READ |
| GET | `/ads-bff/api/v1/campaigns/{id}` | Single campaign detail — `campaignData` | READ |
| GET | `/ads-bff/api/v1/campaigns/pla/{id}` | Single **PLA** (sponsored-product) campaign detail — `plaCampaignData` | READ |
| GET | `/ads-bff/api/v1/campaigns/metadata` | Campaign form/enum metadata — `GET_CAMPAIGN_META` | READ |
| GET | `/ads-bff/api/v1/campaigns/forecast` | Campaign **forecast** — `GET_CAMPAIGN_FORECAST` (projected reach/spend; computed, no state change) | READ |
| GET | `/ads-bff/api/v1/campaigns/debug/{action}` | Campaign diagnostics — debug lookup by keyword/store/pvid/campaign_type (`campaigns/debug/`) | READ |
| GET | `/ads-bff/api/v1/campaigns/recommendations/{id}` | Quick-edit recommendation details for a campaign — `quickEditDetails` | READ |
| GET | `/ads-bff/api/v1/campaigns/utp/{id}` | UTP (unified-targeting-product) detail for a campaign — `getUtpDetails` | READ |
| GET | `/ads-bff/api/v1/campaigns/reviews?ids={ids}` | Campaign-review checklist / rejected-comment lookup — `GET_CAMPAIGN_REVIEW_CHECKLIST` / `GET_REJECTED_COMMENT` (`ads-bff` variant) | READ |
| GET | `/ads-bff/api/v1/campaigns/reviews?ids={ids}` | Same review-checklist read — second binding (`/api` variant in bundle; resolves to same BFF) | READ |
| GET | `/ads-bff/api/v1/campaign-categories` | Campaign category list — `GET_CAMPAIGN_CATEGORIES` | READ |
| GET | `/ads-bff/api/v1/campaign-categories/{id}/metadata/{action}` | Per-category header/metrics metadata — `getCampaignHeadersMeta` | READ |
| GET | `/ads-bff/api/v1/campaign/recommendations/targeting` | Smart-PLA targeting recommendations — `GET_SMART_PLA_TARGETING` | READ |
| GET | `/ads-bff/api/v1/booking` | Media-plan **booking** list — `LIST_BOOKINGS` (the single section entry; a `CREATE_BOOKING` POST reuses the same path — mutating, never call) | READ |
| GET | `/ads-bff/api/v1/booking/{id}` | Single booking detail — `getBooking` | READ |
| GET | `/ads-bff/api/v1/booking/metadata` | Booking form/enum metadata — `GET_METADATA` | READ |
| GET | `/ads-bff/api/v1/booking/expense-metrics` | Booking summary-metric tiles (spend/expense) — `GET_SUMMARY_METRIC` | READ |
| GET | `/ads-bff/api/v1/booking/owner` | Booking owners dropdown list — `GET_OWNERS_LIST` | READ |
| GET | `/ads-bff/api/v1/booking/download` | Bookings list exported as file — `LIST_BOOKINGS_FOR_DOWNLOAD` (serializes existing rows; no async job) | READ (file) |
| GET | `/ads-bff/api/v1/agents/jarvis-agent/sessions` | Jarvis AI copilot — list chat sessions — `GET_SESSIONS` | READ |
| GET | `/ads-bff/api/v1/agents/jarvis-agent/sessions/{id}/messages` | Jarvis — messages in a session — `getSessionMessages` | READ |
| GET | `/ads-bff/api/v1/agents/kam-agent/sessions` | KAM (key-account-manager) agent — list chat sessions — `GET_SESSIONS` | READ |
| GET | `/ads-bff/api/v1/agents/kam-agent/sessions/{id}/messages` | KAM agent — messages in a session — `getSessionMessages` | READ |
| GET | `/ads-bff/api/v1/keyword/config` | Keyword-tooling config — `KEYWORD_CONFIG` | READ |
| GET | `/ads-bff/api/v1/layout/config/booking_approval_terms_and_conditions` | Booking-approval T&C copy — `GET_BOOKING_TERMS_AND_CONDITIONS` | READ |
| GET | `/ads-bff/api/v1/pricing/promo/ads-utp/tabular` | UTP promo pricing tabular data — `UTP_TABULAR_DATA` | READ |
| GET | `/ads-bff/api/v1/suggestions/keyword` | Suggested keywords — `GET_SUGGESTED_KEYWORDS` | READ |
| GET | `/ads-bff/api/v1/suggestions/bid` | Suggested bid — `GET_SUGGESTED_BID` | READ |
| GET | `/ads-bff/api/v1/suggestions/subcategory` | Suggested subcategories — `GET_SUBCATEGORIES` | READ |
| GET | `/ads-bff/api/v1/validate-keywords` | Validate keywords (from CSV/input) — `GET_KEYWORDS_FROM_CSV` (lookup/validation, no state change) | READ |
| GET | `/ads-bff/api/v1/playground/search` | Keyword-playground search — read-only query of playground data | READ |
| GET | `/ads-bff/api/v1/playground/stores` | Keyword-playground stores list | READ |

## Out of scope (writes) — documented from bundle only, never call

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/ads-bff/api/v1/campaigns` | Create a campaign — `POST_CREATE_CAMPAIGN` | WRITE |
| POST | `/ads-bff/api/v1/campaigns/pla` | Create a **PLA** campaign — `POST_PLA_CREATE_CAMPAIGN` | WRITE |
| POST | `/ads-bff/api/v1/campaigns/utp` | Post UTP targeting data — `POST_UTP_DATA` | WRITE |
| POST/PUT | `/ads-bff/api/v1/campaigns/{id}/{action}` | Campaign status mutation (activate/pause/…) — `campaignStatusUpdate` | WRITE |
| POST | `/ads-bff/api/v1/campaigns/{id}/review` | Put a campaign under review — `campaignUnderReview` | WRITE |
| POST | `/ads-bff/api/v1/campaigns/{id}/approve` | Approve a campaign review — `CAMPAIGN_REVIEW_APPROVE` | WRITE |
| POST | `/ads-bff/api/v1/campaigns/{id}/reject` | Reject a campaign review — `CAMPAIGN_REVIEW_REJECT` | WRITE |
| POST | `/ads-bff/api/v1/booking/{id}/approve` | Approve a booking — `approveBooking` | WRITE |
| POST | `/ads-bff/api/v1/booking/{id}/reject` | Reject a booking — `rejectBooking` | WRITE |
| POST | `/ads-bff/api/v1/booking/{id}/submit-for-approval` | Submit a booking for approval — `sendForApproval` | WRITE |
| POST | `/ads-bff/api/v1/booking/{id}/media-mix/closure` | Update/close the booking's media mix — `updateAddMediaMix` | WRITE |
| POST | `/ads-bff/api/v1/booking/{id}/resend-create-booking-notification` | Re-send the approval-follow-up notification — `followUpForApproval` (fires a notification) | WRITE |
| POST | `/ads-bff/api/v1/playground/update-keyword-metadata` | Update keyword metadata in the playground | WRITE |
| POST | `/ads-bff/api/v1/agents/jarvis-agent/chat/send` | Send a message to the Jarvis AI copilot — `SEND_CHAT` (creates a chat turn) | WRITE |
| POST | `/ads-bff/api/v1/agents/kam-agent/chat/send` | Send a message to the KAM agent — `SEND_CHAT` | WRITE |

## Probe / evidence note

- **Not probed (documented only).** The one gentle read-only probe attempted —
  `GET /ads-bff/api/v1/campaigns` — returned **HTTP 429** on the first request because the
  only available `ecom1@jivo.in` JWT (exp **2026-07-13 18:29:59 UTC**) was **expired** at run
  time (2026-07-24), the same expiry that halted the sibling [[Brands-Audiences]] and
  vendor-lane probes. Per the read-only guardrail (any 401/403/429/WAF halts probing),
  probing **stopped after 1 request**; all 47 endpoints are documented from the bundle only,
  **none are PROVEN**, and no live response shapes were captured. Transcript:
  `captures/ads/ads-campaigns-probes.txt`.
- **Source of truth.** Endpoint constants, path builders, the AI-agent (`GET_SESSIONS` /
  `getSessionMessages` / `SEND_CHAT`) maps, the booking approval workflow verbs, and the
  campaign-review (`approve`/`reject`/`review`) verbs were read out of the ads-remote chunk
  `captures/js/ads/1183.8940422c8268d8dc.js`. Adjacent maps in the same chunk point at the
  billing (`GET_BILLING_DATA`, `GET_BILLING_SUMMARY` → [[Ads-Billing-Wallet]]), analytics
  (`brands/campaigns/analytics/metrics` → [[Brand-Analytics]]), creative
  (`creative-management/bundles` → [[Creative-Management]]) and brands/targeting
  (`brands/targeting-options` → [[Brands-Audiences]]) surfaces.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no create/edit/approve/reject/submit/status-update, no
AI-chat send):

- `zepto ads campaigns list` → `GET /ads-bff/api/v1/campaigns` (`GET_TABLE_DATA`).
- `zepto ads campaign get <id>` / `zepto ads campaign pla <id>` → `campaigns/{id}` /
  `campaigns/pla/{id}`.
- `zepto ads campaign forecast <id>` → `campaigns/forecast`; `zepto ads campaign meta` →
  `campaigns/metadata`; `zepto ads campaign categories` → `campaign-categories`.
- `zepto ads campaign reviews <ids>` → `campaigns/reviews?ids=` (read the checklist / rejected
  comment only — never `approve`/`reject`).
- `zepto ads bookings list` → `booking`; `zepto ads booking get <id>` → `booking/{id}`;
  `zepto ads booking metrics` → `booking/expense-metrics`; `zepto ads booking owners` →
  `booking/owner`; `zepto ads bookings download` → `booking/download` (file).
- `zepto ads keywords suggest <seed>` / `zepto ads bid suggest` / `zepto ads subcat suggest`
  → `suggestions/{keyword,bid,subcategory}`; `zepto ads keywords validate` →
  `validate-keywords`; `zepto ads playground {search,stores}` → `playground/{search,stores}`.
- `zepto ads agent sessions {jarvis|kam}` / `zepto ads agent messages <id>` → the AI-copilot
  **session/message reads only** (never `chat/send`).

Explicitly **excluded** from the read-only surface: every row in the writes table — campaign
& booking create/edit/duplicate/status-update, review approve/reject/submit, media-mix
closure, follow-up notification, keyword-metadata update, and both AI `chat/send` verbs.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] ·
  [[Read-Only-Guardrails]]
- **Ads-lane siblings** — this note is campaign/booking CRUD; the surrounding ads surfaces
  are [[Brands-Audiences]] (brand/targeting options, audience reach), [[Creative-Management]]
  (asset bundles a campaign attaches), [[Ads-Billing-Wallet]] (what a booking spends —
  `billing`/`billing/summary`), and [[Brand-Analytics]] (the `/analytics` route + per-campaign
  metrics feeds).
- **Auth** — every call reuses the single `authorization: <jwt>` token minted in
  [[Auth-Identity]]; the same `fcc.zepto.co.in` host also serves the vendor
  [[Vendor-Reports-Queue]] pulls the existing zepto-cli already proves.
