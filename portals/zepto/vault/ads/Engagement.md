---
title: Engagement (Survey, Rewards & Zepto Square)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, ads, engagement]
status: studied
---

# Engagement (Survey, Rewards & Zepto Square)

The **Engagement** section is the ads-lane's **shopper-engagement surface** — the three consumer-facing formats a brand can run on top of ads spend: **Surveys** (build a questionnaire, set its reach + reward, get it approved, then read back response analytics), **Rewards / gamification** (reward creatives tied to a campaign, the reward roster per brand) plus **smart-nudges** (nudge-campaign creation + lookup), and **Zepto Square** (Zepto's social/community feed — the brand's india / city / product leaderboards and order-count stats). It spans **two backends**: the survey + rewards + smart-nudge machinery lives on the **ads-BFF + supporting services mounted on `fcc.zepto.co.in`** (`survey/`, `gamification-service/`, `ads-bff/`, and the consumer-app `echo/` service), while **Zepto Square** stats live on **`auth-backend.zepto.co.in`** (`api/v1/zepto-square/...`). For JIVO this is Jivo Wellness Pvt. Ltd. (Manufacturer, STANDARD tier, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`), ads brand **Jivo** `brand_id b3550d5d-fc71-47b0-af4f-f221f909b936`, login `ecom1@jivo.in`. Auth is the single Zepto JWT in the `authorization` header (no `Bearer` prefix), the same token that works across every Zepto backend. Endpoint contracts below were extracted from the ads/vendor/root-shell webpack module-federation chunks — they are the API-constant bindings (`GET_*` / getter functions / const objects), **not** live captures unless flagged PROVEN (see Evidence).

## SPA routes

- `/ads/create/reward` — reward-creative builder (gamification reward tied to a campaign).
- `/survey` and `/vendor/survey` — survey list / dashboard (created surveys, analytics entry).
- `/survey/create` and `/vendor/survey/create` — survey builder (questions, reach, reward).
- `/dashboard/survey-approval` — survey-approval queue (review created surveys, approve/reject).
- `/zepto-square/` — Zepto Square dashboard (india/city/product leaderboards + order-count stats).

## Backend hosts

- `auth-backend.zepto.co.in` — **Zepto Square** stats (`api/v1/zepto-square/...`). Probed live 2026-07-24: the JWT is **accepted** here (no 401/403/429), but the stats reads require a header **`x-client-id: <zepto-square clientId>`** — a Zepto Square-specific client id that is **not** the `manufacturer_id` or `brand_id` (both returned `Invalid clientId`); the correct value is still to be captured. See Evidence.
- `fcc.zepto.co.in` — the ads/vendor host that fronts the **`survey/`** service (survey CRUD + analytics + approvals), the **`gamification-service/`** (reward creatives), the **`ads-bff/`** smart-nudges, and the consumer-app **`echo/`** survey-render endpoints. One JWT (`authorization: <jwt>`, no `Bearer`) authorizes it; sibling ads-lane probes show `fcc` returns HTTP 429 for the current (expired) token, so `fcc` endpoints here remain documented (not probed).

## What the section exposes (concepts)

- **Surveys** — list/view all surveys for the brand, per-survey details + a creation checklist, a survey-builder config, and a **survey-approval** queue (list created surveys, open a review). Analytics side: dashboard summary metrics, graph data + graph config, and a per-survey **response download** (file). The consumer-app `echo/` endpoints render the survey to shoppers (questions) — response-submission + impression events are **writes**.
- **Rewards (gamification)** — a brand's reward roster (`rewards/brand/{id}`) and a single reward (`rewards/{id}`). Creating a reward creative + logo upload are **writes**.
- **Smart-nudges** — look up a smart-nudge campaign (`smart-nudges/{id}`); creating one is a **write**.
- **Zepto Square** — india-level order stats, city-level stats, product-level stats, and the city leaderboard/ranking for the brand's Zepto Square presence.

## READ endpoints

Base = `https://<host>/` + path. Paths shown as wired in the bundle, with the API-constant for traceability. `${e}` = a brand / parent-brand / survey / campaign / reward id (for JIVO, brand `b3550d5d-fc71-47b0-af4f-f221f909b936`). Method column: `GET` = declared GET (or getter-shaped) constant; `GET?` = getter-shaped constant whose verb was not directly observed in the chunk (a couple of survey list/analytics endpoints may be POST-with-body but are **pure reads**, same idiom as the vendor-side `report-requests` list). None returned 2xx at probe time — all remain **documented (not probed)**; the `x-client-id` requirement for the zepto-square reads was confirmed live.

| METHOD | Path | Purpose (const) | Read/Write |
|---|---|---|---|
| GET | `auth-backend · /api/v1/zepto-square/india-level-stats` | Zepto Square india-level order counts (`GET_ORDER_COUNTS`); needs header `x-client-id` | READ |
| GET | `auth-backend · /api/v1/zepto-square/city-level-stats` | Zepto Square city-level order stats (`GET_CITY_LEVEL_ORDERS`) | READ |
| GET | `auth-backend · /api/v1/zepto-square/product-level-stats` | Zepto Square product-level stats (`GET_PRODUCT_LEVEL_STATS`) | READ |
| GET | `auth-backend · /api/v1/zepto-square/city-leaderboard` | Zepto Square city leaderboard / ranking (`GET_CITY_RANKING`) | READ |
| GET? | `fcc · /survey/api/v1/survey/list` | Surveys list for the brand (`GET_SURVEYS_FOR_BRAND`) | READ |
| GET? | `fcc · /survey/api/v1/survey/view-all` | View all surveys (`VIEW_ALL_SURVEYS`) | READ |
| GET? | `fcc · /survey/api/v1/survey/${e}` | Single survey details (`getSurveyDetails`) | READ |
| GET? | `fcc · /survey/api/v1/survey-creation/${e}/checklist` | Survey-creation checklist (`getSurveyChecklist`) | READ |
| GET? | `fcc · /survey/api/v1/survey-creation/config` | Survey-builder config (`GET_SURVEY_CONFIG`) | READ |
| GET? | `fcc · /survey/api/v1/approvals/list` | Created-surveys approval queue (`GET_CREATED_SURVEYS`) | READ |
| GET? | `fcc · /survey/api/v1/approvals/review` | Open a survey for approval review — read of the item under review (`REVIEW_APPROVAL`; verb unconfirmed) | READ |
| GET? | `fcc · /survey/api/v1/survey-analytics/metrics` | Survey dashboard summary metrics (`GET_DASHBOARD_SUMMARY`) | READ |
| GET? | `fcc · /survey/api/v1/survey-analytics/graph-data` | Survey dashboard graph data (`GET_DASHBOARD_GRAPH_DATA`) | READ |
| GET? | `fcc · /survey/api/v1/survey-analytics/graph-details` | Survey dashboard graph config (`GET_DASHBOARD_GRAPH_CONFIG`) | READ |
| GET | `fcc · /survey/api/v1/survey-analytics/download-responses` | Download survey responses (`DOWNLOAD_SURVEY_RESPONSES`) — file/export blob, pure read | READ (file) |
| GET? | `fcc · /echo/api/v2/survey/questions` | Consumer-app render: survey questions (`ye`) — pure read of the questionnaire | READ |
| GET? | `fcc · /gamification-service/api/v1/rewards/brand/${e}` | Reward roster for a brand (`getRewardList`) | READ |
| GET? | `fcc · /gamification-service/api/v1/rewards/${e}` | Single reward by id (`getRewardById`) | READ |
| GET? | `fcc · /ads-bff/api/v1/smart-nudges/${e}` | Smart-nudge campaign details (`getSmartCampaignDetails`) | READ |

## Out of scope (writes / exports) — never expose in a read-only CLI

| METHOD | Path | Purpose (const) | Class |
|---|---|---|---|
| PUT | `fcc · /survey/api/v1/survey-creation/upsert` | **Create / update** a survey (`UPDATE_SURVEY`) | WRITE |
| PUT | `fcc · /survey/api/v1/survey-creation/${e}/questions` | **Update** a survey's questions (`updateSurveyQuestions`) | WRITE |
| PUT | `fcc · /survey/api/v1/survey-creation/rewards` | **Update** a survey's reward + reach (`UPDATE_REWARDS_AND_REACH`) | WRITE |
| PUT | `fcc · /survey/api/v1/survey/update-reward` | **Update** a survey reward (`UPDATE_REWARD`) | WRITE |
| POST | `fcc · /gamification-service/api/v1/rewards` | **Create** a reward creative (`CREATE_REWARD_CREATIVE`) | WRITE |
| POST | `fcc · /ads-bff/api/v1/smart-nudges/campaign` | **Create** a smart-nudge campaign (`SMART_CAMPAIGN_CREATION`) | WRITE |
| POST | `fcc · /echo/api/v2/survey/question-responses` | **Submit** a shopper's survey answers (`Pe`) — persists responses | WRITE |
| POST | `fcc · /echo/api/v1/survey/events` | **Log** survey impression / interaction events (`xe`) — event ingest | WRITE |

These are held out of scope per [[Read-Only-Guardrails]]: the survey-creation `upsert` / `questions` / `rewards` / `update-reward` PUTs mutate survey definitions; `CREATE_REWARD_CREATIVE` and `SMART_CAMPAIGN_CREATION` create engagement assets; and the `echo/` `question-responses` / `events` POSTs write shopper-side data. A strict read-only CLI must not fire any of them. (The `REVIEW_APPROVAL` approve/reject *decision* is likewise a write when submitted; only the read of the item under review is surfaced above, and its verb is unconfirmed.)

## Evidence

- **Endpoint set** extracted from the webpack module-federation chunks under the ads / vendor / root-shell remotes (`root-shell-main.8a3af4e6aebe630f.js` + the code-split chunks under `captures/js/{ads,vendor,root-shell}/`). The survey constants are the `Ue`/`ye`/`Pe`/`xe` const objects (`GET_SURVEYS_FOR_BRAND`, `GET_CREATED_SURVEYS`, `getSurveyDetails`, `getSurveyChecklist`, `GET_SURVEY_CONFIG`, `GET_DASHBOARD_*`, `DOWNLOAD_SURVEY_RESPONSES`, `UPDATE_SURVEY`, `updateSurveyQuestions`, `UPDATE_REWARDS_AND_REACH`, `UPDATE_REWARD`, `REVIEW_APPROVAL`, `VIEW_ALL_SURVEYS`); the reward constants are the gamification `g` object (`CREATE_REWARD_CREATIVE`, `getRewardList`, `getRewardById`, `UPLOAD_LOGO`); the smart-nudge + zepto-square constants are the `ads-bff` / auth-backend `y` enum (`SMART_CAMPAIGN_CREATION`, `getSmartCampaignDetails`, `GET_ORDER_COUNTS`, `GET_CITY_LEVEL_ORDERS`, `GET_PRODUCT_LEVEL_STATS`, `GET_CITY_RANKING`). Source of truth = the JS corpus on disk (`captures/js/sections.json`, slug `engagement`).
- **Live probe (read-only, 8/8 cap reached, none PROVEN):** on 2026-07-24, 8 `GET` probes were fired at the **Zepto Square** reads on `auth-backend.zepto.co.in` with the only available JWT (`ecom1@jivo.in`, `exp 2026-07-13` — **expired**). Every call was **accepted** (no 401/403/429/WAF — auth-backend does not enforce token expiry or WAF headers for these routes). `zepto-square/india-level-stats` returned **HTTP 400 `Missing clientId`**, and adding header **`x-client-id`** flipped the error to **`Invalid clientId`** — proving the header name is `x-client-id` but that neither `manufacturer_id` nor `brand_id` is the correct Zepto Square client id. `city-leaderboard` at the bare path returned **404** (needs the right clientId context / route args). **No endpoint returned 2xx → nothing upgraded to PROVEN.** The `fcc` survey/rewards/smart-nudge reads were not probed (cap spent on auth-backend; sibling probes show `fcc` = 429 for this token). Transcript: `captures/ads/engagement-probes.txt`.
- **Request/response bodies uncaptured** — no `captures/ads/*.json` exists for any survey / reward / zepto-square endpoint; the survey list/detail schema, the analytics graph payloads, the reward roster shape, and (crucially) the correct `x-client-id` value for the zepto-square stats want a live (read-only) capture with a fresh token to finalise.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no survey create/update, no reward/nudge creation, no response submission):

- `zepto survey list` → `survey/api/v1/survey/list` (or `view-all`); `zepto survey get <id>` → `survey/api/v1/survey/${e}`; `zepto survey checklist <id>` → `survey-creation/${e}/checklist`; `zepto survey config` → `survey-creation/config`.
- `zepto survey approvals` → `survey/api/v1/approvals/list`; `zepto survey review <id>` (read of item under review) → `approvals/review`.
- `zepto survey analytics <id> [summary|graph]` → `survey-analytics/{metrics,graph-data,graph-details}`; `zepto survey responses <id> --out FILE` → `survey-analytics/download-responses` (file).
- `zepto rewards list <brandId>` → `gamification-service/api/v1/rewards/brand/${e}`; `zepto rewards get <id>` → `rewards/${e}`.
- `zepto nudge get <id>` → `ads-bff/api/v1/smart-nudges/${e}`.
- `zepto square india|city|product|leaderboard` → `api/v1/zepto-square/{india-level-stats,city-level-stats,product-level-stats,city-leaderboard}` — **once the correct `x-client-id` is captured**.

Explicitly **excluded**: survey `upsert` / `questions` / `rewards` / `update-reward` (writes), `CREATE_REWARD_CREATIVE`, `SMART_CAMPAIGN_CREATION`, and the `echo/` `question-responses` / `events` submissions.

## Connections

- Index & shared refs: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- **Tightest siblings** (same ads BFF): the brand + audience context this section engages comes from [[Brands-Audiences]]; reward/nudge creatives overlap [[Creative-Management]]; nudge + survey campaigns run alongside [[Ads-Campaigns-Booking-Keywords]]; survey/engagement outcomes surface in [[Brand-Analytics]] and geo/consumer overlays in [[Market-Geo-Consumer-Insights]]; ads spend behind rewards ties to [[Ads-Billing-Wallet]].
- Approver/reviewer identities on the survey-approval queue tie back to platform identity: [[Users-Access]] · [[Auth-Identity]].
