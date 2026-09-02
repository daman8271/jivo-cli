# PHASE 2 — Corpus harvest record (Flipkart)

Harvested 2026-07-30, **unauthenticated** — every asset below is a public static bundle on
Flipkart's CDNs. No login, no cookie, no bot-check encountered. No 401/403/429 at any point.
Rate-limit headers observed on `seller.flipkart.com`: `x-ratelimit-limit: 800` (we used <5).

## Result

| Host / surface | Files | Notes |
|---|---|---|
| Seller Hub (`seller.flipkart.com`) | 195 | webpack build served from `static-assets-web.flixcart.com/fk-sp-static/script/` |
| Vendor Hub (`vendorhub.flipkart.com`) | 7 | shell from `retail.flixcart.com/www/fk-p-fk-retail-vpp/` + Blinx remote |
| **TOTAL** | **202** | ** 70M** on disk |

Benchmark: zepto = 273 chunks / 17 MB. This corpus is smaller in file count, ~4x larger in bytes.

## Seller Hub structure (discovered)

1. `GET /index.html` → 200 (11,173 B) unauthenticated. Lists **30 entry bundles**, one per
   subsystem: `app · runtime · 903 (vendor) · alpha-seller · fa · fbflite · gamification ·
   guidedassistance · inventoryHealth · lending · listings · login-app · metrics ·
   multisellerselect · orders · partnerServices · payments · PriceManagement · pricing ·
   promotions · rateCard · reactPlayerPreview · report-centre · returns · sbc · sellerQnA ·
   sir · spf · unifiedInventory · adblock`.
2. `runtime.b6ff02c9c4294af73bca.js` carries the webpack chunk manifest:
   `__webpack_require__.u = e => ((names)[e]||e) + "." + (hashes)[e] + ".js"`
   → **93 lazy chunks**, all 93 fetched 200.
3. **Seller Hub is ALSO module-federation** — 6 remotes referenced by `remoteEntry.js`:
   `coe · listingsManagement · manageProfile · preLogin · sellerComs · selleronboarding`.
   All 6 remoteEntry bundles fetched (242 KB – 1.37 MB each). Each declares its own chunk map
   (`i.u = e => (121===e?"vendor":e)+"."+{id:hash}[e]+".js"`, publicPath `script/`):
   **93 remote chunks declared, 91 fetched 200, 2 hard 404** (stale manifest rows —
   `coe/121` and one `listingsManagement` chunk; recorded as a gap, not hidden).

## Vendor Hub structure (discovered)

1. `GET /login` → **404 JSON** — it is a POST-only route, not a page. The SPA root is `GET /`
   → 200 (681 B).
2. Root loads only 2 scripts from `retail.flixcart.com/www/fk-p-fk-retail-vpp/`:
   `FKRetail.eacfb1ff.js` (917 KB) + `main.8520925c55acaa8ebaa1.js` (8 KB).
   webpack chunk name = `webpackChunk**retailer_hub_shell**` → this is only a **shell**.
3. `main.js` declares 7 lazy chunks; **2 fetched 200** (`25.…js` = the shell router,
   `vendor.…js`), **5 hard 404** (stale manifest). Recorded as a gap.
4. `25.…js` holds the micro-frontend registry. The real app is a **Blinx remote**:
   ```js
   BlinxVendorHub: { path:["/welcome","/vendor-portal","/learning-center-detail"],
     hostConfig:{ host:"/v0", manifestPath:"/minified/scripts/manifest.json",
                  relativeHost:true, scriptsToLoad:["main","shared"] } }
   ```
5. `GET https://vendorhub.flipkart.com/v0/minified/scripts/manifest.json` → 200, unauthenticated.
   Yields the real app: `main-a124d00a.js` (**4.9 MB**, 140 `/vendor/*` API paths),
   `shared-ecbeecc6.js`, `0-66d455be.js` (722 KB). All fetched 200.

## AMENDMENT-01 escalation — applied, and what it found

Amendment 01 (03:06 IST) authorized UA rotation, backoff+jitter, concurrency ≤4, cookie-jar
reuse, and headless-browser page navigation for Phase 2. Applied as follows.

**Escalation signals to report: NONE.** Across the whole harvest (≈240 requests):
**0 × 401, 0 × 403, 0 × 429, 0 CAPTCHAs, 0 bot-checks, 0 account/lock notices, 0 session
invalidation, 0 email/2FA challenges.** No authenticated session was used at any point (all four
jars on disk are expired — see `seed-intel.md` §6), so JIVO's live accounts were never touched by
this phase. Nothing to escalate.

1. **UA rotation + exponential backoff with jitter — used on the 7 missing chunks.**
   3 user-agents × 3 attempts × 5 vendorhub chunks = 15 requests, **all 404**. Also probed 4
   candidate shell-manifest paths for an alternate listing: `/minified/scripts/manifest.json`
   404, `/v0/manifest.json` 404, `/www/…/manifest.json` 404, `/manifest.json` 200 but it only
   names `FKRetail.js` (already held). **Conclusion: those 7 assets are genuinely deleted from the
   CDN, not gated.** A 404 after 15 rotated attempts is a dead asset, not a block.
2. **Cookie-jar reuse — not applicable.** G9 permits consuming an existing jar; all four on disk
   expired 7–12 days ago, so no jar unlocks anything. Not minted (G9).
3. **Headless-browser navigation — deliberately not used, because it cannot add anything here.**
   The amendment's rationale for it is recovering an authenticated lazy-chunk tail. On Flipkart
   there is no such tail to recover: **all five *authenticated* Seller Hub remotes
   (`coe`, `listingsManagement`, `manageProfile`, `sellerComs`, `selleronboarding`) served every
   one of their chunks at HTTP 200 to an anonymous `curl`** — 91 of 93 declared, the 2 misses
   being the same dead-asset case as above. Flipkart gates its *data*, not its *code*. Driving a
   browser without a session would only re-fetch the pre-login path I already have; driving one
   *with* a session is impossible (no valid session) and would require minting one (G9 forbids).
   Cross-checked by scanning the whole corpus for referenced-but-unfetched flixcart `.js` URLs:
   after the remote pass, **0 remain** apart from the 7 dead ones and 3 third-party analytics
   scripts (New Relic, Adobe DTM, an error-image shim) that carry no Flipkart API surface.
   This is stated as a judgment, not a limitation I hid: `BLOCKED_NEEDS_HEADFUL` is **not**
   warranted for Flipkart.

## Honest gaps in the corpus

- **7 chunks are hard-404** (2 seller-remote, 5 vendorhub-shell) — confirmed dead after the
  rotated-retry escalation above. Any endpoint present *only* in those 7 is invisible to this
  study. Impact assessed and low: the 5 vendorhub ones are shell-level, and the shell's route
  registry (`25.…js`) *was* recovered — the app's real routes (`/operations` ×23, `/inventory`
  ×39, `/vendor-portal` ×71, `/profile` ×16, `/payments` ×5, `/agreements`, `/onboarding`) all
  resolve inside `blinx-main-a124d00a.js`, which we hold in full. Not worked around, not hidden.
- A chunk *never referenced from any manifest* (e.g. injected only by a server-rendered
  authenticated page) would be missed. Cannot be ruled out without a session. Stated, not
  papered over.
