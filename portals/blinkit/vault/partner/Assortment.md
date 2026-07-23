---
title: Assortment
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: studied
---

# Assortment

The **Assortment** section (SPA route `/app/assortment`, portal title "Assortment") is where a manufacturer sees which of its SKUs are **listed / active per Blinkit facility** — the catalog view that governs what can actually be ordered on a PO and what can carry stock. For JIVO this is Jivo Wellness Pvt. Ltd. (`x-entity-id=1117`, type `manufacturer`).

**Honest scope note:** the captured main bundle `captures/partner/js/index.js` (8.4 MB) does **not** contain the Assortment page's component or its data-fetch code. This is provable by exhaustive grep: the whole bundle carries just **three literal `/v1/…` paths** (`/v1/projects/`, `/v1/validate-otp`, `/v1/verify-fssai`) plus one base-var-constructed call (`` `${…ConsoleEndpoint}v1/get-entity-tabs/` ``) — the Sales/SOH/report-requests/assortment data calls are **all absent**, built inside their own code-split lazy chunks that were not captured. "assortment" itself appears at exactly **three sites**, all plumbing (route-title resolver, support-icon map, support-category map — see below); there is **no** assortment/listing data endpoint, no facility field, and no `active_sku`/`listed_sku`/`is_listed` column anywhere in the bundle. The table shape and the read endpoint therefore have to be confirmed by a live network capture of the page — they are **not** invented here.

## Subpages & tabs

- **`/app/assortment`** — the assortment landing/list. Confirmed as a first-class route: the page-title resolver maps the route segment `"assortment"` → the display title `"Assortment"` (`case"assortment":return"Assortment"`).
- **Signal — assortment is registered "lighter" than the core data pages.** Its title comes back as a **bare string literal** (`return"Assortment"`), whereas every core data page is **enum-backed** in the same resolver: `case"sales":return Jr.SALES`, `case"soh":return Jr.SOH`, `case"report-requests":return Jr.REPORT_REQUEST`, `case"invoice-summary":return Jr.INVOICE_SUMMARY`, `case"scorecard":return Jr.SCORECARD`, `case"appointments":return Jr.PO_SCHEDULING`, `case"developers":return Jr.EDI_INTEGRATION`, `case"brand-fund":return Jr.BRAND_FUND`, `case"fees-charges":return Jr.FEES_AND_CHARGES`, `case"manage-users":return Jr.MANAGE_USER`, `case"account":return Jr.ACCOUNT`, `case"admin-dashboard":return Jr.ADMIN_DASHBOARD`. Assortment (and `po-details`, `help-support`) sit outside that enum table — consistent with a newer / differently-registered section.
- Any sub-tabs (e.g. Active / Inactive / De-listed, or a per-facility breakdown) are **to confirm via live capture** — the tab config lives in the un-captured page chunk, not in `index.js`.
- Help/Support is context-aware here: raising a ticket while on `/assortment` is pre-filed under category `"assortment"` / ticketFilter `"OTHERS"` — the **generic** filter, unlike the dedicated filters its siblings get (`/po`→`PURCHASE_ORDER`, `/invoice-summary`→`PAYMENT`, `/appointments`→`APPOINTMENT`, `/developers`→`edi_asn`). It carries a purple category icon (`iconColor:"#5925DC"` on `iconBgColor:"#F4F3FF"`). This confirms the route exists and is a recognized section, but is support wiring, not the data page.

## Filters & columns (what the table shows)

**Not determinable from local material.** No assortment/listing column definitions, filter names, or facility selectors were found in the captured bundle. By analogy to the sibling data pages ([[Stock-on-Hand]], [[Sales]]) the assortment grid would plausibly be **per-facility** with a status field (listed / active / inactive) and product identifiers (product_id, item_id, product_name, category, brand), but this is an expectation, **not** evidence. Columns and filters: **to confirm via live network capture.**

> Caution — do not conflate: the `PRODUCT_LISTING` sheet referenced in `ecomcliauto/blinkit/VERIFIED-FINDINGS.md` is a **Brand Central ADS campaign type** (an ad format, `brands.blinkit.com`), **not** the partner-portal Assortment page. Likewise the many `is_active` / `LISTED` string hits in `index.js` belong to the analytics/session-replay SDK and unrelated enums — none are assortment column defs.

## API endpoints

| METHOD | path | purpose | read?/write? |
|---|---|---|---|
| — | assortment data / listing feed | populate the Assortment grid (listed/active SKUs per facility) | **read — endpoint: to confirm via live network capture** (not present in captured bundle) |
| GET | `/v1/get-entity-tabs/` | returns which sections/tabs entity 1117 is allowed to see; gates whether Assortment renders (401 → force-logout `invalid_entity_tab_401`) | read |
| POST | `/v1/report-requests/` | shared async report queue — **if** an Assortment/Listing export exists it would surface here (proven queue currently shows only Invoices Excel, Bulk PO Excel, SOH Details Excel, Sales Details Excel — **no** assortment report type observed) | read |
| GET | `/v1/report-requests/download/{id}/` | download a completed report by id (generic, used by [[Report-Requests]]) | read |

Notes:
- **No dedicated `/v1/...assortment...` or `...listing...` data endpoint appears anywhere in the captured bundle.** The only `/v1/*` literals present are EDI/user-management/support paths; the sales/soh/assortment data calls are constructed inside their own un-captured page chunks.
- **Out of scope (writes):** the Assortment page may, in some seller portals, expose list / de-list / activate actions on a SKU. If such controls exist here they are **mutating writes and are OUT-OF-SCOPE** — they must never be documented as usable and are not to be exercised. None were found in local material; their existence is unknown pending a live (read-only) capture.

## Real data seen (evidence)

- **Route confirmed live** as a real portal section (title resolver + support-icon map + support-ticket category map in `index.js`, all three verified by grep).
- **No assortment data captured.** The blinkit-cli (`ecomcliauto/clis/blinkit-cli/` — `main.go`, `client.go`, `config.go`, `dates.go`, `email.go`) covers only report-requests + Sales (`/v1/reports/sales-details-excel/`) + SOH (`/v1/reports/soh-details-excel/`) + Brand Fund + Ads; grep for `assortment|listing|catalog` across it returns **only** one hit — the ads `PRODUCT_LISTING` sheet name in the README (a Brand Central ad format, not this page). It has **no** assortment command and never hit an assortment endpoint.
- **Report queue evidence** (live, `/v1/report-requests/`, entity 1117): 20 rows, types = Invoices Excel / Bulk PO Excel / SOH Details Excel / Sales Details Excel — **Assortment/Listing is not among them**, so assortment likely renders inline (a direct data call) rather than via the async report queue.
- The closest first-party SKU-level truth we already pull is the **SOH snapshot** ([[Stock-on-Hand]]) — stock-on-hand per SKU is effectively the intersection of "assortment ∩ has inventory", so SOH is a partial proxy until the assortment feed itself is captured.

## What a READ-ONLY CLI would expose (candidate commands)

All read-only; all gated on first capturing the real endpoint. Proposed once the live network trace is available:

- `assortment list [--facility <id>] [--status listed|active|inactive] [--json]` — dump the listed/active SKU roster per facility (the grid).
- `assortment facilities` — enumerate the facilities the assortment view is broken down by.
- `assortment doctor` — verify `/v1/get-entity-tabs/` grants the Assortment tab for entity 1117 before attempting the data call.
- (If, and only if, a read-only export is confirmed in the report queue) `assortment export` → poll `/v1/report-requests/` → `download/{id}/`, mirroring the Sales/SOH flow in [[Report-Requests]].

Explicitly **excluded**: any list / de-list / activate / edit command — those are writes and OUT-OF-SCOPE for this read-only study.

## Connections

- Portal shell & nav: [[Partner-Hub]] · index: [[00-Blinkit-Atlas]]
- Governs the SKU universe that flows into [[PO-Summary]] (only listed SKUs get POs) and [[Stock-on-Hand]] (SOH is assortment ∩ inventory).
- Shares the async export pattern with [[Report-Requests]], [[Sales]], [[Stock-on-Hand]] (if an assortment export exists).
- Ads-side `PRODUCT_LISTING` (Brand Central) is a **different** thing — see the ads notes, not this page.
