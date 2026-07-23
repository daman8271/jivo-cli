---
title: Blinkit Portal Atlas
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: moc
tags: [blinkit, portal-study, read-only]
---

# Blinkit Portal Atlas — JIVO seller ecosystem (goal #83, Phase 1)

> ⚠️ READ-ONLY study. Navigation + screenshots + endpoint capture only. Nothing in Blinkit is ever changed.

JIVO's Blinkit presence spans **two separate portals**, each with its own auth:

| Portal | Host | What it is | Auth | Hub |
|---|---|---|---|---|
| **Partner** | `partnersbiz.com/app` | Supply-side: POs, invoices, inventory, sales, scorecard | email-OTP → token (auto) | [[Partner-Hub]] |
| **Ads / Brand Central** | `brands.blinkit.com` | Demand-side: ad campaigns, creatives, budgets, performance | Firebase magic-link → idToken | [[Ads-Hub]] |

**Entity:** Jivo Wellness Pvt. Ltd. (`x-entity-id: 1117`, type manufacturer). Data API base: `www.partnersbiz.com/v1`.

**Foothold (verified 2026-07-24):** auto-login unattended (`blinkit-login.sh`, token in 3s) → browser authenticated → dashboard reached. Session `access_token` is SHORT-LIVED, so the deep crawl runs API-first (refreshable token) + screenshot bursts, not one long browser session.

## Method (per portal)
Walk every page → screenshot + capture data API calls (reads only) → one Obsidian note per section → weave hubs + data model → 0 broken links → then generate READ-ONLY CLIs.

## Navigation
- [[Partner-Hub]] — 9 sections mapped
- [[Ads-Hub]] — to crawl
- Meta: [[Auth-and-Access]] · [[Read-Only-Guardrails]]
