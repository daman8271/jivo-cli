---
title: Subscription & Billing
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, platform, subscription-billing]
status: studied
---

# Subscription & Billing

The **Subscription & Billing** section is the paywall / plan surface for Zepto's **Brand
Analytics** product — the tier gate that decides which analytics, sales, live and landing-page
insights a brand can see, and how it pays for the upgrade (free trial tier vs. a paid plan taken
**on credit**). For JIVO this is Jivo Wellness Pvt. Ltd. (`manufacturer_id
946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, Manufacturer / **STANDARD** tier — i.e. currently *not* on a
paid analytics plan). The section reads the current subscription state (plan, pricing, visibility
of gated features) and, on the write side, lets a user **subscribe** to the free tier or **commit
to a paid plan on credit** — the two purchase actions that change the account's billing state.

The endpoint contracts below were extracted from the root-shell / brand-analytics code-split
chunks — the API-constant maps that build `brand-analytics-web/…` and `brand-analytics-mobile/…`
paths (`GET_PRICING_DETAILS_WEB`, `GET_SUBSCRIPTION_DETAILS_WEB`, `GET_PLAN_VISIBILITY_DETAILS_WEB`,
`SUBSCRIBE_FREE_TIER_WEB/_MOBILE`, `SUBSCRIBE_TO_PLAN_WEB/_MOBILE`) seen in `remoteEntry.js` and
`root-shell-main.8a3af4e6aebe630f.js` — **not** live captures except where a probe is noted. All
calls hit a single host, **`fcc.zepto.co.in`** (the same backend the proven SALES/INVENTORY and ads
pulls use), under the `brand-analytics-{web,mobile}/api/v1/subscription/*` and `…/subscribe/*`
prefixes. One JWT (header `authorization: <jwt>`, **no** `Bearer` prefix) authenticates all of them;
WAF headers were not enforced at last capture.

## SPA route(s)

Two routes mount this surface:

- `/app/plan-subscription` — the **Plan / Subscription** page: current plan + tier, pricing table
  of available plans, gated-feature visibility, and the "subscribe / upgrade" call-to-action (free
  tier vs. on-credit paid plan).
- `/ads/billing-management` — the **Billing Management** entry in the ads shell that surfaces the
  same subscription/billing state alongside the ads wallet.

Rendered by the root-shell (631) with the brand-analytics remotes against the `fcc.zepto.co.in`
backend. (The ads-side wallet / spend money surface is documented separately in
[[Ads-Billing-Wallet]].)

## Backend host(s)

- **`fcc.zepto.co.in`** — the sole host for this section. Path families:
  `brand-analytics-web/api/v1/subscription/*` and its `brand-analytics-mobile/*` twin (read: pricing
  / user / visibility details), and `brand-analytics-{web,mobile}/api/v1/subscribe/*` (write:
  free-tier + on-credit subscribe). The constant maps also expose a **bare** `/api/v1/subscription/*`
  / `/api/v1/subscribe/*` enum-suffix variant of each path (the prefix-stripped enum value); these
  resolve to the same brand-analytics service on `fcc.zepto.co.in` and are listed alongside their
  prefixed twins so no endpoint is dropped.

## API endpoints (READ)

All rows below are pure reads (plan/pricing/subscription-state lookups; no billing state change).
Method shown as wired in the chunk: `GET` = confirmed constant binding; `UNKNOWN` = the bare
enum-suffix variant whose verb was not directly observed on that literal (it is the prefix-stripped
form of the GET-bound `brand-analytics-web` read below it, so its effect is a read — verb to confirm
on a live capture).

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/brand-analytics-web/api/v1/subscription/pricing-details` | Plan **pricing** table (available plans + prices) — `GET_PRICING_DETAILS_WEB` | READ · probed → **401 Token expired** (documented, expired-token) |
| GET | `/brand-analytics-web/api/v1/subscription/user-details` | Current **subscription / plan** state for the user (active plan, tier) — `GET_SUBSCRIPTION_DETAILS_WEB` | READ |
| GET | `/brand-analytics-web/api/v1/subscription/visibility-details` | **Gated-feature visibility** for the plan (what the tier unlocks) — `GET_PLAN_VISIBILITY_DETAILS_WEB` | READ |
| UNKNOWN | `/api/v1/subscription/pricing-details` | Bare enum-suffix variant of the pricing-details read (same brand-analytics service) | READ (verb to confirm) |
| UNKNOWN | `/api/v1/subscription/user-details` | Bare enum-suffix variant of the subscription/plan-state read | READ (verb to confirm) |
| UNKNOWN | `/api/v1/subscription/visibility-details` | Bare enum-suffix variant of the plan-visibility read | READ (verb to confirm) |

**Mobile twins (not counted here).** The same const map defines
`GET_PRICING_DETAILS_MOBILE = brand-analytics-mobile/api/v1/subscription/pricing-details` (referenced
in the note strings) — a mobile-path mirror of the pricing read. Only the endpoints present as
distinct rows in this section's data are tabled; the mobile pricing read appears in-bundle but is
not a separate section entry, so it is noted, not double-counted.

## Out of scope (writes) — never expose in a read-only CLI

Every `subscribe/*` endpoint is a purchase action that **creates / changes the account's
subscription (billing) state** — free-tier enrolment still creates a subscription record, and
on-credit is a paid commitment. All are POST and must never be fired.

| METHOD | Path | Purpose | Why held out |
|---|---|---|---|
| POST | `/brand-analytics-web/api/v1/subscribe/free-tier` | **Subscribe** to the free analytics tier (web) — `SUBSCRIBE_FREE_TIER_WEB` | Creates/changes subscription state. WRITE. |
| POST | `/brand-analytics-web/api/v1/subscribe/on-credit` | **Subscribe to a paid plan on credit** (web) — `SUBSCRIBE_TO_PLAN_WEB` | Commits a paid billing plan. WRITE. |
| POST | `/brand-analytics-mobile/api/v1/subscribe/free-tier` | **Subscribe** to the free tier (mobile) — `SUBSCRIBE_FREE_TIER_MOBILE` | Creates/changes subscription state. WRITE. |
| POST | `/brand-analytics-mobile/api/v1/subscribe/on-credit` | **Subscribe to a paid plan on credit** (mobile) — `SUBSCRIBE_TO_PLAN_MOBILE` | Commits a paid billing plan. WRITE. |
| UNKNOWN (write) | `/api/v1/subscribe/free-tier` | Bare enum-suffix variant of the free-tier subscribe | Prefix-stripped form of a subscribe POST. WRITE. |
| UNKNOWN (write) | `/api/v1/subscribe/on-credit` | Bare enum-suffix variant of the on-credit subscribe | Prefix-stripped form of a subscribe POST. WRITE. |

DOCUMENTED-FROM-BUNDLE ONLY. A strict read-only CLI must never call any `subscribe/*` path. (The
sections extractor mislabels `free-tier` as READ in the raw `read_write` field — it is a WRITE:
subscribing to the free tier still writes a subscription record. All six subscribe rows are held out
of scope.)

## Live probe (evidence)

- **1 probe fired, read-only GET, then halted** (per the guardrails, stop on first 401/403/429).
  `GET https://fcc.zepto.co.in/brand-analytics-web/api/v1/subscription/pricing-details` (const
  `GET_PRICING_DETAILS_WEB`, an unambiguous pure-GET plan-pricing read) with the captured JWT
  returned **`HTTP 401 {"code":401,"message":"Token expired"}`** — the token (`iat 1783887610`,
  `exp 1783967399` = 2026-07-13 18:29:59 UTC) had lapsed ~11 days before this run (2026-07-24). No
  2xx, so **nothing was upgraded to PROVEN**; all endpoints remain **documented (not probed)**.
  Transcript: `captures/platform/subscription-billing-probes.txt`.
- **Auth/base confirmed** by the proven sibling flows on the same host: SALES/INVENTORY
  (`fcc /api/v1/reports*`) and ads (`fcc /ads-bff/api/v1`) work with the identical
  `authorization: <jwt>` header (no `Bearer`), `origin/referer https://brands.zepto.co.in`. Re-run
  these Subscription probes with a fresh token to lock down response shapes.
- **Response shapes:** to confirm via live read-only capture. Expected top-level keys (from the
  plan-page usage): `pricing-details` → an array of plan objects (name/tier + price + billing
  period + feature list); `user-details` → the account's active plan + tier + subscription status
  (JIVO = STANDARD); `visibility-details` → per-feature boolean/enum flags describing what the
  current tier unlocks.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no subscribe / no plan purchase):

- `zepto subscription pricing` → `GET /brand-analytics-web/api/v1/subscription/pricing-details`
  (available plans + prices). Pure READ.
- `zepto subscription status` → `GET /brand-analytics-web/api/v1/subscription/user-details`
  (current plan / tier — expect STANDARD for JIVO). Pure READ.
- `zepto subscription visibility` → `GET /brand-analytics-web/api/v1/subscription/visibility-details`
  (which gated analytics features the tier unlocks). Pure READ.
- **Excluded:** every `subscribe/*` call (free-tier and on-credit, web + mobile) — all are billing
  writes and must never be surfaced in a read-only CLI.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] ·
  [[Read-Only-Guardrails]]
- **Tightest siblings** — the analytics this subscription gates and the money it draws on:
  [[Brand-Analytics]] (the Sales / Live / Landing insights unlocked by the plan) and
  [[Ads-Billing-Wallet]] (the ads-side wallet / spend surface reached from `/ads/billing-management`).
- Platform-lane neighbours that share the identity/config backbone: [[Users-Access]] (who on the
  account can change the plan), [[Auth-Identity]] (the JWT that authenticates every call here), and
  [[KYC-Onboarding]] (vendor onboarding that precedes a billing relationship).
- Config / layout seeds it references live in [[Platform-Common]].
