---
title: Amazon Portal Atlas
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: moc
tags: [amazon, portal-study, read-only]
status: studied
read_only: true
---

# Amazon Portal Atlas — JIVO seller/vendor ecosystem (Wave 1)

> ⚠️ **READ-ONLY** study of JIVO's live Amazon accounts. Evidence is navigation + screenshots +
> network capture + static bundle analysis. **Nothing is ever created, edited, submitted,
> approved, uploaded, or generated** — writes are catalogued as out-of-scope contracts, nothing
> more. The read-only guarantee is enforced in code, three layers (see [[Read-Only-Guardrails]]).

> 🔴 **SCOPE — READ THIS BEFORE USING ANY NUMBER.** The live data in this study covers **JIVO
> MART on Seller Central (3P) ONLY.** It is **NOT the whole company's Amazon picture.** JIVO's
> other Amazon datasets — **Jivo Wellness** (a separate Amazon entity) and **Vendor Central (1P)**
> for both Wellness and Mart — were `NOT_REACHABLE` this run: no live session exists on this Mac
> (expired) or on any reachable office box (`dev`, `win2`/`victus` — every Chrome/Edge cookie DB
> checked, zero Amazon cookies), and G9 forbids minting one. Do **not** read the Mart-3P numbers
> (464 SKUs, ₹1.65 L top-listing GMS, 73 feedback reviews, etc.) as "JIVO on Amazon." See
> [[Amazon-Data-Inventory]] §0 for the full four-dataset model and the exact reachability evidence.

## Amazon is TWO portals and FOUR API surfaces — the defining fact

Unlike Zepto (one SPA) or Blinkit (two lightweight portals), JIVO's Amazon presence spans **two
completely separate portals with different logins, hosts, and auth**, and Vendor Central alone
splits into **three unrelated service surfaces**:

| Portal | Host | JIVO's role | Session this run |
|---|---|---|---|
| **Seller Central** (3P marketplace) | `sellercentral.amazon.in` | JIVO *sells on* Amazon (Jivo Mart) | ✅ **LIVE — fully walked** |
| **Vendor Central** (1P) | `www.vendorcentral.in` | JIVO *sells to* Amazon (Wellness + Mart) | ❌ expired — documented from seed |

> **Priority inversion (lead-approved).** The brief named Vendor Central primary. But VC's session
> was dead and G9 forbids re-login, while Seller Central's 8-day-old cookie jar was live with zero
> bot-check. So **Seller Central became the primary live-walked portal** and Vendor Central is
> documented from the Phase-0 seed. This inversion is *why* the study has 162 proven live reads
> rather than zero.

### The four API surfaces

1. **Seller Central** — dozens of micro-frontends on per-tool CloudFront CDNs, all under one
   cookie session. Mixed GET (reads) and POST (GraphQL/RPC reads + writes). **This is where the
   live data is.**
2. **Vendor Central · Retail Analytics (ARA)** — `…/api/retail-analytics/v1/` — POST-bodied report
   RPC. Sales + Inventory datamart. [[Retail-Analytics-ARA]]
3. **Vendor Central · PO Management** — `…/po-api/…` — 4-step async PO export. [[Purchase-Orders]]
4. **Vendor Central · Coupon (legacy hz)** — the one genuine GET file download on VC. [[VC-Coupon-Campaigns]]

## Study status

> **432 distinct endpoint contracts catalogued** across 20 hosts · **162 PROVEN live** (returned
> HTTP 200 to a read-only GET this run) · **20 business sections** · **26 distinct live screenshots**
> (0 duplicates — each asserted unique, unlike the Blinkit reference) · **99 MB / 224-file JS
> corpus**. Classification: 163 `READ` + 91 `READ_FILE` = **254 allowlist** · 9 `READ_POST` (semantic
> reads behind HTTP POST, documented not wired) · 55 `WRITE` · 90 `UNKNOWN` · 24 `NOISE`. Under
> AMENDMENT-04, **147 app-fired non-GET requests** were passed through and logged, **0 of them
> state-changing**. Full roll-up in [[Amazon-Endpoints]]; the honest coverage audit is
> [[Study-Verification]].

## The headline findings (what nobody at JIVO is looking at)

1. **Report Central offers 35 downloadable report types; JIVO's automation pulls 0 of them.** 20
   inventory, 5 payment, 4 sales, 4 removals, 2 customer-concessions. The gap is the study's most
   valuable output. → [[Business-Reports-Analytics]], [[Amazon-Data-Inventory]] §6.
2. **Seller feedback is trending down and unmonitored** — 90-day 3.0★ vs lifetime 3.8★ (73 reviews).
   → [[Feedback-Manager]].
3. **JIVO Mart has 0 live coupons** — all 18 promotions are expired/cancelled. → [[Coupons-Promotions]].
4. **The 1P inventory datamart exposes 38 metrics; JIVO's cron pulls 17.** → [[Retail-Analytics-ARA]].
5. **The account is healthy** (ODR GOOD, 0 defects/claims/chargebacks) but nobody reads the
   dashboard. → [[Account-Health-Performance]].

## Entity facts (see [[Amazon-Data-Inventory]] §0 for the full four-dataset model)

- **Seller Central:** login `ecom1@jivo.in` → global account **"Jivo Mart"**, merchant
  `A2V85Y00QGIGP9`, India marketplace `A21TJRUUN4KGV`. One entity on this login.
- **Vendor Central:** two logins — Wellness (`7691702`/`A2I4CTXZEM9HDK`) and Mart
  (`8592892`/`A2882479L2H86F`). Both sessions expired this run.

## Method

Seed-mine `~/ecomcliauto` → scaffold → harvest the JS corpus (static CDN + headless app-driven
navigation) → static-extract + cluster endpoints into 20 sections → classify READ / READ_FILE /
READ_POST / WRITE / UNKNOWN / NOISE → **live-walk** Seller Central (URL-navigation only, view-only
clicks, network capture as primary evidence) → write the vault → self-verify → generate a
read-only CLI from the allowlist. Never a write; see [[Read-Only-Guardrails]].

## Navigation

- **Index & meta:** [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]] · [[Amazon-Pages-and-Routes]] · `COVERAGE-LEDGER.md` (repo root) · [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

### Seller Central (3P) — live-walked
- [[Orders]] · [[Inventory-FBA]] · [[Listings-ASIN-Management]] · [[Product-Classification]] · [[Coupons-Promotions]] · [[Business-Reports-Analytics]] · [[Account-Health-Performance]] · [[Feedback-Manager]] · [[Messaging-Buyer-Seller]] · [[Tax-GST-Reports]] · [[Global-Selling-Expansion]]

### Vendor Central (1P) — documented from seed
- [[Retail-Analytics-ARA]] · [[Purchase-Orders]] · [[VC-Catalog-Products]] · [[VC-Coupon-Campaigns]] · [[VC-Support-Help]]

### Platform
- [[Homepage-Widgets]] · [[Help-Support-Center]] · [[Platform-Common]] · [[Static-Assets-i18n]]
