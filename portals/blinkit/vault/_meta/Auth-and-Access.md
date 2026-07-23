---
title: Blinkit Auth & Access
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [blinkit, auth]
---
# Blinkit Auth & Access
- **Partner** (partnersbiz.com): email-OTP → `access_token`/`refresh_token` (v2::uuid). Unattended via `~/ecomcliauto/orchestrate/blinkit-login.sh` (reads OTP from tanuj@jivo.in via himalaya). Data API headers: `token`+`access_token`+`x-api-key: fe25a1da-...`+`x-entity-id: 1117`+`x-entity-type: manufacturer`+`service: partnersbiz`. ⚠️ access_token SHORT-LIVED → refresh or re-login for long crawls.
- **Ads** (brands.blinkit.com): Firebase magic-link → idToken (~1h) via identitytoolkit.googleapis.com. Script `blinkit-ads-generate.sh`.
- Browser session saved: gstack state `blinkit-partner`.
See [[00-Blinkit-Atlas]] · [[Read-Only-Guardrails]].
