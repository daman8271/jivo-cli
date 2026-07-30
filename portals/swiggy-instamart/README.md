# Swiggy Instamart portal study → read-only CLI

⚠️ **READ-ONLY** study of JIVO's Swiggy Instamart brand + supply ecosystem. Navigation,
screenshots and network capture only. Nothing was created, changed, approved, cancelled, paid,
uploaded, generated or deleted. No request was authored by hand; no captured request was replayed.
See `vault/_meta/Read-Only-Guardrails.md` for the auditable form of that claim, including the
complete log of every non-GET the application itself fired.

## One portal, two businesses, six apps

`partner.instamart.in` is a single React SPA that is **both** the Brand/Ads portal and the
Supply/Vendor portal — its own account-select screen says so. Structurally it is a webpack
**module-federation shell** (`brand-portal-client`, host name `partnerHost`) that mounts **six
remotes at runtime**:

| Remote | Route | Version | Surface | Data host |
|---|---|---|---|---|
| `imAdsClient` | `/instamart` | 1.4.128 | ads, sales, sales-insights, campaigns, reports, NPI | `partner-api` + `brand-portal-service-http` |
| `imVendorClient` | `/im-vendor` | 2.2.28 | **Supply Portal** — POs, booking, GRN, RTV, stock, availability, vendor scores | **`picker.swiggy.com`** |
| `imBdpoClient` | `/im-discounts` | 1.19.0 | brand-funded discounts (BDPO) | `brand-portal-service-http` |
| `brandverseClient` | `/brandverse` | 0.0.7 | cross-surface brand campaigns | `brand-portal-service-http` `/api/v1/3p/` |
| `imSamplingClient` | `/im-sampling` | 0.1.11 | product sampling campaigns | `brand-portal-service-http` |
| `imCatalogClient` | `/im-catalog` | 0.1.5 | catalogue + SPIN change requests | `brand-portal-service-http` |

**Auth:** passwordless email OTP → Bearer JWT, **plus an HMAC request signature** on every
brand-portal call, **plus** a different header (`Abacus-Token`) on the vendor lane. The session
lives in `localStorage`, not cookies — so a cookie-jar import cannot authenticate this portal.
Full model: `vault/_meta/Auth-and-Access.md`.

## Three corrections to the mission brief (all verified live)

- `partner.swiggy.com` is **not** this portal — it 302s to `/food/` and serves the Swiggy
  restaurant Partner App, a different product.
- `brands-im-kba.swiggy.com` **does not resolve** (NXDOMAIN). The real host is
  `ozone-idp-brands-im-kba.swiggy.com`, the identity provider.
- **`picker.swiggy.com` was missing from the brief entirely** and carries 37 endpoints — the whole
  supply lane. JIVO's existing automation has never touched it.

## The deliverable

- **`vault/`** — 37 wikilinked Obsidian notes. Start at **`vault/00-Swiggy-Instamart-Atlas.md`**.
  - `vault/supply/` — 10 sections: Purchase-Orders, PO-Booking-Appointments, Goods-Received-GRN,
    Returns-RTV-and-Purchase-Returns, Stock-On-Hand-and-Low-Stock, Availability-and-Fill-Rate,
    Vendor-Performance-Scores, Vendor-Downloads, Local-Buying, Vendor-FAQ-Help.
  - `vault/ads/` — 10 sections: Sales-Reports, Sales-Insights, Ad-Campaigns,
    Brand-Insights-Metrics, Keyword-And-Bid-Suggestions, Creatives, Requisition-Orders,
    Products-And-SPINs, Ads-AI-Chat, NPI-New-Product-Introduction.
  - `vault/brand/` — 4 sections: Discounts-BDPO, Sampling-Campaigns, Brandverse,
    Catalog-SPIN-Management.
  - `vault/platform/` — 4 sections: Accounts-And-Entities, Config-And-Feature-Flags,
    Auth-Sessions-And-Login, Telemetry-And-Third-Party.
  - `Swiggy-Instamart-Endpoints.md` — the master read-only allowlist (source of truth for the CLI).
  - `Swiggy-Instamart-Data-Model.md` — how the two lanes join, with Mermaid graphs.
  - `Swiggy-Instamart-Data-Inventory.md` — **the live numbers**, each with its source endpoint.
  - `Swiggy-Instamart-Pages-and-Routes.md` · `Swiggy-Instamart-Screenshot-Index.md`
  - `_meta/` — Auth-and-Access, Read-Only-Guardrails, Study-Verification.
- **`COVERAGE-LEDGER.md`** — one row per route, walked YES/NO, with a specific reason for every NO.
- **`captures/`** — the JS corpus (140 files / 11.8 MB across the shell + 6 remotes), 170
  screenshots and per-page network logs from 5 live walk passes, three already-generated vendor
  reports downloaded read-only (`captures/reports/`), the endpoint partitions, and the AMENDMENT-04
  non-GET audit trail (`nonget-allowed.tsv`, `nonget-flagged.tsv`). Gitignored: live session data.
- **`cli/swiggy-instamart-portal`** — read-only Cobra Go CLI generated from the READ allowlist.

## Headline live findings (2026-07-30, all VERIFIED)

- **134 distinct endpoints** across 4 production hosts; **119 SPA routes**; **6 remotes**.
- **Three JIVO accounts**, walked separately because their data differs materially:
  Jivo Wellness (`c9f24655…`) — **27 campaigns, 132 cities with sales, 43 catalog SPINs**;
  Jivo Mart Pvt. Ltd (`89bafc9c…`) — **0 campaigns, 22 cities, 9 SPINs**; Jivo (`260921c1…`).
- **Sales, 2026-07-23 → 07-29 (the default 7-day window): ₹2,35,05,424**, +6.36% period-on-period,
  across 132 cities. Top: Hyderabad ₹35.7 L, Bangalore ₹29.1 L, Delhi ₹27.3 L, Mumbai ₹25.5 L.
  Jivo Mart was **₹0** for the same week.
- The portal exposes **47 metric types, 17 dimensions, 25 filter types**. JIVO's automation
  requests **two** of the 47.
- **141 enabled Instamart cities** and **74 config/feature-flag keys** come back from one
  unauthenticated-shape endpoint on every page load.
- Live POs against JIVO's distributors are visible with facility, vendor code, quantity and expiry
  — a surface JIVO reads nowhere.
- The portal ships an **in-app AI assistant** over JIVO's own ads data (currently flag-gated off).
- **₹2.84 Cr of `PotentialGmvLoss`** across 735 SKU×store rows — 189 of them at **zero stock on the
  shelf** — sitting in an inventory export JIVO's own user generated on 29 July and nothing reads.
  Obtained read-only by downloading an already-completed report, not by generating one.

## Reproducing / running

The study artefacts are static. The CLI:

```bash
cd cli && go build -o swiggy-instamart-portal .
./swiggy-instamart-portal doctor
./swiggy-instamart-portal auth whoami
```

Auth is **inherited, never minted** (G9): the CLI reads the token JIVO's existing
`~/.config/swiggy-instamart-cli/config.json` already holds. It will never log in, never refresh,
and never sign out — those rotate a single-use token and would break the live session belonging to
JIVO's e-com team and the production keepalive cron.

Note the platform reality documented in `vault/_meta/Auth-and-Access.md`: a correctly-signed
hand-built request is rejected by a server-side session-activation wall even from inside the
human's own logged-in browser. The CLI is therefore a **read surface over a live session**, and
the authoritative way to exercise these endpoints remains letting the SPA fire them.

## The gap this study measures

`~/ecomcliauto/` pulls **one** report — the Instamart sales xlsx — twice a day into one table.
Against this map that is a few percent of the portal: the entire supply lane, sales-insights'
45 unused metrics, campaigns, brand insights, keywords, creatives, requisition orders, catalog,
sampling, brandverse and discounts are all unread. `COVERAGE-LEDGER.md` and
`vault/Swiggy-Instamart-Data-Inventory.md` quantify it endpoint by endpoint.
