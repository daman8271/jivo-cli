---
title: Blinkit Ads Portal (Brand Central)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: hub
tags: [blinkit, ads, portal-study]
status: to-crawl
---

# Ads Portal — brands.blinkit.com (Brand Central)

Demand-side: ad campaigns, creatives, budgets, keyword/placement bids, performance (ROAS). Auth: Firebase magic-link → idToken (~1h), script `blinkit-ads-generate.sh`. Back to [[00-Blinkit-Atlas]].

## To crawl (Phase 1)
- [ ] Campaigns (how many are running, types, budgets, status) ← user specifically wants this
- [ ] Creatives / ad groups
- [ ] Keywords / placements / bids
- [ ] Performance reports (spend, impressions, ROAS)
- [ ] Wallet / billing

Existing narrow coverage: blinkit-cli 'ads pull' (the Ads .xlsx via emailed S3 link) — export only, not the live campaign surface.
