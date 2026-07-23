# Blinkit portal study → CLI (goal #83, Phase 1)

⚠️ READ-ONLY study of JIVO's Blinkit seller ecosystem. NO data is ever changed — navigation + screenshots + network capture only. No create/edit/save/delete/launch/submit, ever.

Two portals:
- **partner** — `partnersbiz.com/app/*` (PO, invoices, inventory/SOH, sales, reports…). Auth: email-OTP → token (auto, `blinkit-login.sh`).
- **ads** — `brands.blinkit.com` (campaigns, creatives, budgets, performance…). Auth: Firebase magic-link → idToken (`blinkit-ads-generate.sh`).

- `vault/` — Obsidian study notes (partner/ + ads/), wikilinked. The deliverable of Phase 1.
- `captures/` — screenshots + network logs per page (gitignored — holds live session data).
