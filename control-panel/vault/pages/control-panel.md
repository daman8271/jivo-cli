---
title: Control Panel
aliases: [home]
route: /
type: page
endpoints: [sales-pulse, health, cogs]
tags: [jivo, control-panel, home, dashboard, kpi]
---

# Control Panel

The landing dashboard shown immediately after login at `/`. Sidebar label **Control Panel**; it is the app "home" for the *Jivo Group — Control Panel* internal Django ERP. Rendered for user `preshit` (role **admin**).

## Purpose
Give a JIVO ops/leadership user a one-glance **P&L pulse** for the current period the moment they sign in, plus the primary navigation hub into every report (Sales, Accounts, Inventory & Production, Master Data, Admin). It is a summary cover page — the deep tables live behind the [[sales-dashboard]] (`/realise/`) dashboard and the report sub-pages.

## What it shows
- **Topbar** — brand ("Jivo Group / Control Panel"), a green **LIVE** pill, and a running ticker chip showing the headline **REALISE** figure (server-rendered, e.g. `REALISE ₹171.07/L`). See [[REALISE]].
- **Sidebar navigation** (frozen rail, collapsible/hover-peek):
  - **Main Menu** — Control Panel (this page, active), [[sales-dashboard]].
  - **Reports → Sales** group — [[compare-sales]], [[sales-cn]], [[hidden-sales]], [[sales-flow]], [[dispatch-details]], [[realise-calculator]], [[rate-list]].
  - **Reports → Accounts** group — [[customer-aging]], [[required-credit-limit]], [[open-payments]], [[claims]], [[reconciliation]] (Wellness–Mart Recon).
  - **Reports → Inventory & Production** group — [[stock-available]], [[non-moving-stock]] (Non Moving Stock), *OIH vs Stock* (nav link `/realise/oih-vs-stock/` — 404s), [[production-plan]] (Production Plan), [[daily-production]].
  - **Reports → Master Data** group — [[customer-master]].
  - **Admin** — [[users]] (User Management).
  - **User badge** — avatar `PR`, name `preshit`, role `admin`, and a **Sign out** form (`POST /accounts/logout/` with CSRF — do not call).
- **Main panel**
  - Greeting: "Welcome, preshit".
  - Section header **P & L Metrics** (pill: *KPIs*).
  - **KPI card grid** (3-up responsive → 2 → 1):
    - **Avg. Realisation** card (green accent) — value `₹171.07/L`, trend pill `▼ -7.1%` "vs last month", compare line `vs last month ₹184.22/L`, sub-line `Revenue: ₹22.94 Cr`. Clickable → **KPI-difference "glimpse" modal**.
    - **COGS** card (`.cogs-kpi-card`) — **rendered only when `can_cogs` is true**. For `preshit` (`can_cogs:false`) the card is **absent** from the DOM. When present it carries an inline form (`param_type` select + `otp` input + submit) that fetches [[cogs]]. See [[COGS]].
- **KPI-difference glimpse modal** — clicking the Avg. Realisation card opens a modal that reads a pre-embedded `<script type="application/json">` payload and renders a per-**Main Group** breakdown table (Category / Current / Last / Difference), e.g. `Commodity - Mustard`, `Premium - Olive`, `Commodity - Sunflower`, `Commodity - Soyabean`, `Premium - Groundnut`, `Premium - Canola`. This is static server-embedded data, **not** an XHR. It illustrates the [[REALISE]] Main Group / sub-group tiering (Commodity vs Premium).

## Data sources
- **KPI cards & ticker** — *server-rendered* into the page HTML by the shared Realise backend (same computation that powers [[sales-data]]); the home template does not XHR these numbers. The Sales dashboard's client sets `API='/realise'`, and the home KPIs reuse that `/realise/api/*` backend server-side. Headline figures map to [[REALISE]] (avg ₹/L), Revenue (₹ Cr), and vs-last-month deltas.
- [[cogs]] — `GET /api/cogs/` — the **only** client-side fetch on this page, bound to the COGS KPI card (OTP-gated; locked for `preshit`).
- [[sales-pulse]] — `GET /realise/api/sales-pulse/?dataset=oils` — lightweight change-fingerprint used by the shared Realise live-refresh loop (driven from [[sales-dashboard]], not fired directly by the home template, but part of the same `/realise/api/*` backend this page fronts).
- [[health]] — `GET /realise/api/health/` — SAP connectivity check surfaced app-wide (SAP Connected / SAP Error dot on [[sales-dashboard]]); same shared backend.

## Key fields & columns
- **Avg. Realisation** → headline [[REALISE]] value in ₹ per litre for the current period; blends all Main Groups.
- **vs last month** → prior-month avg realisation for delta context; trend pill coloured by *meaning* (green = good, red = bad move), not by arrow direction.
- **Revenue: ₹X Cr** → gross sales value for the period (crore rupees).
- **Glimpse rows** → `label` = `<tier> - <commodity>` (Main Group), `current`/`last` = ₹/L this vs prior month, `diff` = signed ₹/L change, `direction` = up/down for colour.
- **COGS card** → see [[COGS]]; when unlocked shows total COGS ₹, COGS per litre, and total litres.

## Notes / gotchas
- The COGS KPI card is **permission-gated**: it only appears when `loginUser.can_cogs` is true. `preshit` has `can_cogs:false`, so the card and its `/api/cogs/` form are not in the served HTML — the endpoint is documented from JS only. See [[cogs]].
- KPI numbers here are **static server-render**, refreshed on full page load — there is no auto-refresh JS on the home page itself (the live heartbeat via [[sales-pulse]] lives on the [[sales-dashboard]] dashboard).
- `window.loginUser` (embedded JSON) exposes the full permission matrix and Django group memberships used to gate sidebar entries and cards (e.g. `can_inventory:false` yet individual `can_stock_available`/`can_production` etc. are true, so Inventory sub-items still render).
- Nav link **OIH vs Stock** points at `/realise/oih-vs-stock/` which **404s** — dead link in the Inventory & Production group.
- **READ-ONLY**: the Sign-out form (`POST /accounts/logout/`) and any COGS submit must not be executed against this live production system.

## Related
[[sales-dashboard]], [[cogs]], [[sales-pulse]], [[health]], [[REALISE]], [[COGS]], [[sales-data]], [[OIH]], [[users]]
