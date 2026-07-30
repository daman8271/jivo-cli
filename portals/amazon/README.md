# Amazon portal study → CLI (Portal-Atlas Wave 1)

⚠️ **READ-ONLY** study of JIVO's Amazon presence. Evidence is **navigation + screenshots +
network capture + static bundle analysis**. Nothing is ever created, edited, submitted, approved,
uploaded, or generated. Writes are catalogued as out-of-scope contracts, nothing more. The
read-only guarantee is enforced in code (see `vault/_meta/Read-Only-Guardrails.md`).

## Two portals, one study

| Portal | Host | JIVO role | This run |
|---|---|---|---|
| **Seller Central** (3P) | `sellercentral.amazon.in` | JIVO *sells on* Amazon (Jivo Mart) | ✅ live-walked |
| **Vendor Central** (1P) | `www.vendorcentral.in` | JIVO *sells to* Amazon (Wellness + Mart) | ❌ session expired — documented from seed |

The brief named Vendor Central primary, but its session was dead and G9 forbids re-login, while
Seller Central's session was live. So **Seller Central is the live-walked primary** and Vendor
Central is documented from the `~/ecomcliauto` seed evidence (lead-approved inversion).

## The deliverable

- **`vault/`** — the Obsidian study, wikilinked. Start at **`vault/00-Amazon-Atlas.md`**.
  - `vault/seller/` (11) · `vault/vendor/` (5) · `vault/platform/` (4) — 20 section notes
  - `vault/Amazon-Endpoints.md` — master ledger, **432 contracts / 421 distinct paths, 100% indexed**
  - `vault/Amazon-Data-Inventory.md` — **the live business numbers** (what Daman asked for most)
  - `vault/Amazon-Data-Model.md` · `vault/Amazon-Pages-and-Routes.md`
  - `vault/_meta/` — Auth-and-Access, Read-Only-Guardrails, Study-Verification (PASS)
- **`COVERAGE-LEDGER.md`** — one row per route (193), walked YES/NO with a reason for every NO.
- **`captures/`** — 99 MB / 224-file JS corpus, 26 live screenshots + per-page `.har.json` network
  logs, `nonget-allowed.tsv` (147 app-fired non-GET audit rows), `endpoints-raw.tsv` (the
  classified inventory), `seed-intel.md` (Phase-0). Corpus + probes are gitignored.
- **`cli/`** — the read-only Cobra CLI (below).

## Headline findings (what nobody at JIVO is looking at)

1. **464 SKUs listed on Amazon 3P, but only 5 Active and 390 Out of Stock** — the storefront is
   99% dark. (`POST /myinventory/gql`, VERIFIED)
2. **Report Central offers 35 report types; JIVO's automation pulls 0 of them.**
3. **Seller feedback trending down** — 90-day 3.0★ vs lifetime 3.8★ (73 reviews).
4. **0 live coupons** — all 18 promotions expired/cancelled.
5. **731 days of daily sales history** available (2024-07-28 → 2026-07-28); the 1P ARA datamart
   exposes 38 inventory metrics, JIVO's cron pulls 17.

All numbers are tagged `VERIFIED` / `PENDING_AUTH` / `NOT_REACHABLE` — see the Data Inventory.

## The CLI — `cli/amazon-portal`

A generated read-only surface: **141 GET read commands across 17 section groups** (+ `doctor`,
`auth whoami`). GET-only, three-layer guardrail, consumes the existing Seller Central session.

```sh
cd cli && go build -o amazon-portal .
./amazon-portal doctor                                   # is the session live?
./amazon-portal coupons-promotions coupons-getcouponpromotions   # 18 promotions
./amazon-portal feedback-manager fbmapi-aggregates       # seller feedback
```

Every command maps to a READ row in `vault/Amazon-Endpoints.md`; writes/POST-reads are never
wired. See `cli/README.md`.

## Method (the nine phases + 3 amendments)

Seed-mine `~/ecomcliauto` → scaffold → harvest the JS corpus → extract + cluster into 20 sections
→ classify READ / READ_FILE / READ_POST / WRITE / UNKNOWN / NOISE → **live-walk** Seller Central
(URL-navigation only, view-only clicks, network capture as primary evidence — AMENDMENT-02;
app-fired non-GETs passed & audited — AMENDMENT-04) → write the vault → self-verify (13/13 auditor
checks PASS) → generate the read-only CLI → completeness sweep (AMENDMENT-03). Never a write.

## Status (2026-07-30)

**20 sections · 432 endpoint contracts (162 PROVEN live) · 26 distinct screenshots · 141 read
commands · auditor 13/13 PASS · coverage 421/421 (100%).** Vendor Central live data is
`NOT_REACHABLE` (expired session, documented from seed). See `vault/_meta/Study-Verification.md`.
