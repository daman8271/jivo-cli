---
title: Score Card
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: studied
---

# Score Card

The **Score Card** (route `/app/scorecard`, nav label "Score Card", icon `monitoring`, sidebar position 4, `vendor_allowed: true`) is Blinkit's **performance / health dashboard** for the vendor (Jivo Wellness, `x-entity-id 1117`, `manufacturer_id 176`). It scores how well the vendor is servicing Blinkit's purchase orders — centred on **Fill Rate** — and adds **benchmarking / ranking** against category peers plus a **"Top 5 potential loss"** view of the SKUs where poor fill-rate is costing the most sales. It is a **read-only analytics page** (no data entry), filtered by a date window. The React route maps `ScoreCard → ScoreCardDashboard → <ScoreCard/>`, and `ScoreCard` is **lazy-loaded from a separate JS chunk `ScoreCard-DK6XTVzq.js` which is NOT in our capture** — so the panel-level data endpoints and exact table columns are inferred from analytics instrumentation + report-queue labels, and the precise API paths are marked **to confirm via live network capture**.

## Subpages & tabs

There are no separate sub-routes — the Score Card is a **single page of stacked panels**. The panels below are proven by the Firebase/analytics visibility+interaction events fired as each renders (found in `index.js`, event enum `Kl`, page group `Jr.SCORECARD = "Scorecard"`):

- **Summary** — `SCORECARD_SUMMARY_VISIBLE` (top-line score / headline KPIs)
- **Fill Rate Metrics** — `SCORECARD_FILL_RATE_METRICS_VISIBLE`; individual metrics are hoverable → `SCORECARD_FILL_RATE_METRIC_HOVERED`
- **Fill Rate Summary** — `SCORECARD_FILL_RATE_SUMMARY_VISIBLE`
- **Benchmarking & Ranking** — `SCORECARD_BENCHMARKING_AND_RANKING_VISIBLE`; category ranks are hoverable → `SCORECARD_CATEGORY_RANK_HOVERED`
- **Key SKUs — Potential Loss** — `SCORECARD_KEY_SKUS_POTENTIAL_LOSS_VISIBLE` (the "Top 5 Potential Loss" list)
- Page view: `SCORE_CARD_VIEWED`

## Filters & columns (what the table shows)

- **Filter — date range.** `SCORECARD_FILTERS_APPLIED` fires on filter change. Both scorecard exports carry a `{ start_date, end_date }` filter pair (confirmed in the report-request render map in the main app chunk), so the page is scoped by a start/end date window. A category filter for the benchmarking panel is likely but **to confirm** (that code is in the un-captured `ScoreCard-DK6XTVzq.js`).
- **Columns.** The exact on-screen column defs live in the un-captured chunk → **to confirm via live network capture**. From the panel semantics: Fill-Rate panels are metric tiles / a summary (fill-rate %); Benchmarking & Ranking is a per-category rank list; Key SKUs Potential Loss is a per-SKU table (item, fill-rate, and an estimated lost-sales / potential-loss value).
- **Not the scorecard:** the `SERIES_CONFIG` chart legend (Appointment / Storage / Fill Rate / Quality, with colours) that also mentions `fill_rate` belongs to the **Fees & Charges** deduction chart (`${BASE}v1/charges-summary/`, route `/fees-charges`), *not* to this page — verified by its surrounding PDF/Excel + Date-Range export modal. Do not attribute it to Score Card.

## API endpoints

All paths are built as `${BASE}v1/...` at runtime (the literal `/v1/...` strings are not in the captured bundles). The scorecard **panel-data** calls are inside the un-captured `ScoreCard-DK6XTVzq.js` chunk, so their exact paths are unconfirmed. The **report-queue** read chain below is proven and shared with [[Sales]] / [[Stock-on-Hand]] / [[Report-Requests]].

| METHOD | path | purpose | read / write |
|---|---|---|---|
| GET/POST | `…/v1/…scorecard-summary…` (exact path unknown) | Summary panel data | **READ** — endpoint: to confirm via live network capture |
| GET/POST | `…/v1/…fill-rate…` (exact path unknown) | Fill Rate metrics + fill-rate summary | **READ** — endpoint: to confirm via live network capture |
| GET/POST | `…/v1/…benchmark/ranking…` (exact path unknown) | Benchmarking & category ranking | **READ** — endpoint: to confirm via live network capture |
| GET/POST | `…/v1/…potential-loss…` (exact path unknown) | Top-5 key-SKUs potential loss | **READ** — endpoint: to confirm via live network capture |
| POST | `/v1/report-requests/` (body `{}`) | List the async report queue; scorecard rows appear as `type: "Scorecard Details Excel"` and `type: "Top 5 Potential Loss"` (filters `{start_date, end_date}`) | **READ** — proven ([[Report-Requests]]) |
| GET | `/v1/report-requests/download/{id}/` | Presigned-S3 download URL for a completed scorecard report | **READ** — proven ([[Report-Requests]]) |
| POST | `/v1/reports/scorecard-details-excel/` *(name inferred from the `…-excel/` pattern; exact path to confirm)* | **Generate** the "Scorecard Details Excel" async export | **WRITE (generate) — OUT OF SCOPE** |
| POST | `/v1/reports/…top-5-potential-loss…/` *(exact path to confirm)* | **Generate** the "Top 5 Potential Loss" async export | **WRITE (generate) — OUT OF SCOPE** |

Note on writes: the two `POST /v1/reports/…` calls queue a new report file (fired by `SCORECARD_BULK_DATA_REQUESTED`). They create an artifact and are treated as **generate = out of scope** — never invoke them. Only the queue **list** and **download** are read-safe.

## Real data seen (evidence)

- **Code evidence (this capture, 2026-07-24):** route/nav config `ScoreCard:{id:"/app/scorecard", component:"ScoreCardDashboard", url:"/scorecard", title:"Score Card", tab:"scorecard", iconName:"monitoring", position:4, vendor_allowed:true}` (in `js/useFirebasePageTracking-CGSyAZ_Q.js`); the lazy import `ScoreCard=React.lazy(()=>import("./ScoreCard-DK6XTVzq.js"))`; the full set of `SCORECARD_*` analytics events (in `js/index.js`); and the report-request render map keys **"Scorecard Details Excel"** and **"Top 5 Potential Loss"**, each displaying **Start Date / End Date**.
- **No scorecard data rows were captured.** The section screenshot `sec-06-score-card.png` is the logged-out PartnersBiz login page (no authed content); the `api/*.json` captures are `appointment-stats` + `profile-user` (unrelated). The live report-queue snapshot in [[Report-Requests]] (20 rows) contained only Invoices / Bulk PO / SOH / Sales reports — i.e. **no scorecard export had been generated at capture time**, so no scorecard file has been pulled yet.
- **No CLI coverage yet:** `blinkit-cli` (Flows 5–8: Sales, SOH, Brand Fund, Ads) has **no** scorecard command.

## What a READ-ONLY CLI would expose (candidate commands)

Read-only surface (needs one live authenticated `/app/scorecard` network capture to lock the panel-data paths before wiring):

- `blinkit scorecard summary --from <d> --to <d>` — Summary panel KPIs *(endpoint to confirm)*
- `blinkit scorecard fill-rate --from <d> --to <d>` — Fill Rate metrics + summary *(endpoint to confirm)*
- `blinkit scorecard ranking` — Benchmarking & category ranking *(endpoint to confirm)*
- `blinkit scorecard potential-loss` — Top-5 key-SKUs potential loss *(endpoint to confirm)*
- `blinkit scorecard reports` — list scorecard rows in the report queue (`Scorecard Details Excel`, `Top 5 Potential Loss`) — **read, proven** (`POST /v1/report-requests/`, filter by `type`)
- `blinkit scorecard download <id>` — fetch a **pre-existing** completed scorecard report's presigned S3 file — **read, proven** (`GET /v1/report-requests/download/{id}/`)

Explicitly **excluded (writes):** generating a fresh "Scorecard Details Excel" / "Top 5 Potential Loss" export (`POST /v1/reports/…`). Same auth as the rest of the portal (headers `token` + `access_token` + `x-api-key fe25a1da-…` + `x-entity-id 1117` + `x-entity-type manufacturer` + `service partnersbiz` + `app_client partnerbiz-web`).

## Connections

- Portal home: [[Partner-Hub]] · [[00-Blinkit-Atlas]]
- Exports land in and download via [[Report-Requests]] (same async queue + `download/{id}/` chain as [[Sales]] and [[Stock-on-Hand]])
- Scores fulfilment of [[PO-Summary]] purchase orders (Fill Rate = ordered vs supplied); [[Assortment]] feeds which SKUs are rated
