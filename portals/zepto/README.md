# Zepto portal study → CLI (goal #84)

⚠️ **READ-ONLY** study of JIVO's Zepto seller ecosystem. NO data is ever changed — corpus harvest + endpoint capture + gentle GET-probes only. No create/edit/save/delete/schedule/approve/dispute/upload/pay, ever.

**One portal, one JWT:** `brands.zepto.co.in` is a webpack **module-federation micro-frontend** (remotes: `vendor`=635, `ads`=632, `root-shell`=631; live manifest at `/manifest.json`). A single email-OTP → JWT (auto, no browser, `zepto-login.sh`) authorizes **all** backends:

| Backend | Serves |
|---|---|
| `fcc.zepto.co.in` | vendor reports (`/api/v1`) + ads (`/ads-bff/api/v1`) |
| `auth-backend.zepto.co.in` | identity, access-management, subscription, kyc, brands, config |
| `financenew.zepto.co.in` | finance / receivables / ledger |
| `scpfin.zepto.co.in` | supply-chain finance |
| `brands-onboarding.zepto.co.in` | onboarding / KYC (VMS) |
| `ads-platform.zepto.co.in` | ads platform |
| `partner.zepto.co.in` | partner |

Auth: email-OTP → JWT (`authorization` header, **no** `Bearer` prefix). NO refresh token → re-login daily (JWT expires 23:59:59 IST). Unattended via `~/ecomcliauto/orchestrate/zepto-login.sh` (OTP read from `ecom1@jivo.in` via himalaya). See [[Auth-and-Access]].

## The deliverable

- **`vault/`** — Obsidian study notes, wikilinked (the Phase-1 deliverable). Start at **`vault/00-Zepto-Atlas.md`**.
  - `vault/vendor/` — 13 sections: Purchase-Orders, ASN, Release-Orders-Amendment-Requests, RTV, Catalog-Health, Stock-View-Inventory, Vendor-Reports-Queue, Invoicing, Vendor-Contracts-Margins, Payments, Ledger-Recon-Upload, Receivables, Fulfilled-by-Zepto.
  - `vault/ads/` — 7 sections: Brands-Audiences, Creative-Management, Ads-Campaigns-Booking-Keywords, Ads-Billing-Wallet, Brand-Analytics, Market-Geo-Consumer-Insights, Engagement.
  - `vault/platform/` — 5 sections: Auth-Identity, Users-Access, Subscription-Billing, KYC-Onboarding, Platform-Common.
  - `vault/Zepto-Endpoints.md` — master read-only endpoint inventory (source of truth for a generated CLI).
  - `vault/Zepto-Data-Model.md` — how the sections join into one relational graph.
  - `vault/_meta/` — Auth-and-Access, Read-Only-Guardrails, Study-Verification.
- **`captures/`** — JS corpus (273 chunks / 17 MB), probe transcripts, working JSONs (gitignored — live session data).

## Study status (2026-07-24)

**25 sections mapped · 741 distinct endpoint contracts catalogued** from the harvested SPA corpus across 7 backends. First-pass classification: **~304 read-safe** (263 JSON reads + 41 file downloads), **141 write/export held out of scope**, **296 to-confirm**; the master [[Zepto-Endpoints]] index carries the refined per-section split.

## Method (per section)

Harvest the module-federation corpus → cluster all endpoints into coherent business sections → classify READ vs WRITE/export → gently GET-probe pure reads (read-only, allowlist, stop-on-WAF) to upgrade documented → PROVEN → one wikilinked Obsidian note per section → weave the atlas + master endpoint index + data model → then generate/expand a READ-ONLY CLI.

## Existing CLI coverage vs backlog

`zepto-cli` (`~/ecomcliauto/clis/zepto-cli`) already pulls **6 flows** read-only: `sales pull` + `inventory pull` (Vendor-Reports-Queue: SALES / INVENTORY report types) and `ads pull` 2×2 (products/brands × range/daily). That is a thin slice of [[Vendor-Reports-Queue]] + [[Brand-Analytics]]. The **other ~21 sections** (POs, ASN, GRN, invoicing, ledger, payments, receivables, catalog, stock, contracts, campaigns, creatives, wallet, geo/market/persona/survey insights, users/access, subscription, KYC) are the read-only CLI **expansion backlog** — every endpoint they need is already catalogued in [[Zepto-Endpoints]].
