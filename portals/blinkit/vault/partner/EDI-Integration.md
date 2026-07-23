---
title: EDI Integration
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: studied
---

# EDI Integration

The **EDI Integration** section (sidebar label "EDI Integration", carrying a "new" badge until 01-01-2026) is Blinkit/PartnersBiz's onboarding surface for **Electronic Data Interchange** — letting a manufacturer automate the exchange of Purchase Orders, ASNs (Advance Shipment Notices) and Invoices with Blinkit over **secure APIs and webhooks** instead of doing it by hand in the portal. It is not a data grid; it is a **lead-generation / activation landing page** plus an embedded **API-reference viewer**. A seller picks how they want to integrate (Direct or via a Third-Party aggregator), submits a request ("lead"), and — once the request is approved — completes an OAuth handshake to go live. Page headline in the bundle: *"EDI Integration — Streamlining Invoicing, and Reconciliations"*; subtitle: *"Automate purchase orders, ASNs, and more through secure API and webhook integrations."* Support routes to `edi-support@grofers.com`. For Jivo Wellness (entity 1117) this is a config/activation surface — nothing here returns operational business data, so the read value is limited (see the CLI note below).

Route note: the section lives at **`/app/developers`** (the menu key is literally `developers`, aliased in code to `EDI_INTEGRATION`), with a full-screen documentation sub-route at **`/app/developers/documentation`**. There is also a top-level `/developers` render of the same doc viewer.

## Subpages & tabs

This section has no filter/tab bar. It is composed of screens/modals:

- **Landing (`/app/developers`)** — hero header + "Why partner with Blinkit?" marketing section. Two CTAs:
  - **Activate Now** — opens the integration-choice modal. If a request is already in flight the button/label changes to reflect state (see status flow below); if OAuth is pending it reads **"Complete OAuth setup"**.
  - **View Documentation** — opens `/app/developers/documentation` in a new tab.
- **Integration-choice modal** (`LeadGenerationModalContent`) — two option cards:
  - **Direct Integration** — *"For teams that can manage API integration internally."* Selling points: *No Recurring or Per-Transaction Charges · Standardized APIs & webhooks · No third-party requirement · For companies with Internal IT/Tech Support.* CTA: **"Request Direct Integration."**
  - **Third-Party Integration** — *"Use this option to go live faster with expert partner support."* Selling points: *Service Provider Charges May Apply · Javis, B2BE, Unicommerce, Zoho and others · Implementation and Integration Support Provided.* CTA: **"Request Third-Party Integration."** Requires choosing a certified partner (aggregator) before submitting.
- **Lead-generation-in-progress modal** — shown when a request already has status `IN_PROGRESS`.
- **OAuth setup modal** — shown when status is `OAUTH_PENDING`: *"OAuth setup in progress … Your connection is active. Generate your link to continue the integration."* Its **Generate Link** button calls the aggregator OAuth-link endpoint and opens the returned URL in a new tab.
- **Documentation viewer (`/app/developers/documentation`)** — a **Scalar API-Reference** (`@scalar/api-reference`, sidebar layout, "API Reference" page title) rendering the EDI OpenAPI spec. The spec is fetched at runtime, converted from `swagger: "2.0"` → `openapi: 3.1.0`, then rendered. (An older/alternate code path fetched a static file `/ediStaticDoc.yaml`; the current chunk fetches it from the API — see endpoints.)

## Filters & columns (what the table shows)

None. There is no data table, no filter set, and no column definitions in this section — it is a configuration/activation flow, not a report grid. The only "state" surfaced is the integration request status and the selected aggregator, driven from Redux config (`userConfigs.features.edi_lead_generation`):

- `is_active` — feature flag gating whether the Activate button shows.
- `feat_config.current_lead_status` — one of `DRAFT`, `IN_PROGRESS`, `OAUTH_PENDING`, `COMPLETE` (enum `EDI_LEAD_GENERATION_STATUS`).
- `feat_config.aggregator` — the seller's chosen preferred integration partner (used to generate the OAuth link).
- Request source enum `EDI_LEAD_GENERATION_SOURCE` = `DIRECT_INTEGRATION` | `THIRD_PARTY_INTEGRATION`. Lead source tag = `PARTNERSBIZ`.

## API endpoints

All paths are relative to the Vendor Console API base (`window.VENDOR_CONSOLE_API_URL`, i.e. the same `www.partnersbiz.com` data API; standard headers token + access_token + x-api-key + x-entity-id:1117 + x-entity-type:manufacturer apply).

| METHOD | path | purpose | read/write |
|---|---|---|---|
| GET | `/v1/vis/enabled-aggregators/` | List enabled EDI integration partners / aggregators (Javis, B2BE, Unicommerce, Zoho, …) — populates the Third-Party partner picker (`INTEGRATION_PARTNERS_ENDPOINT`). | **read** |
| GET | `/v1/vis/generate-url/?aggregator=<name>` | Generate the aggregator/OAuth authorization URL for the chosen partner; returns `{ data: { url } }`, opened in a new tab (`ZOHO_LEAD_GENERATION_ENDPOINT`, called by `generateOAuthLink`). GET-shaped, but it is part of the activation handshake — treat as activation-only, not a data read. | read (activation) |
| GET | `/v1/sandbox/edi/yaml-doc` | Fetch the EDI API OpenAPI/Swagger YAML spec rendered by the Scalar viewer at `/app/developers/documentation`. | **read** |
| GET | `/ediStaticDoc.yaml` (static asset) | Older/alternate path: static YAML spec fetched by the top-level `/developers` doc component and rendered via Scalar. Likely superseded by `v1/sandbox/edi/yaml-doc`. | **read** (to confirm which is live via network capture) |
| POST | `/v1/client-requests/` | Submit the EDI integration request / "lead" (Direct or Third-Party, with chosen aggregator). `LEAD_GENERATION_ENDPOINT`, called via `doHttpPost`. | **write — OUT OF SCOPE** |

Notes / honesty:
- **`POST /v1/client-requests/` is a write** (it creates a seller integration request). It is listed only to document the flow; a read-only CLI must never call it.
- The **current request status** (`current_lead_status`, `is_active`, `aggregator`) is delivered inside the app-wide user/features config (Redux `userConfigs.features.edi_lead_generation`), not via an EDI-specific GET. The exact bootstrap config endpoint that carries this block is **to confirm via live network capture** — it is a global config fetch, not scoped to EDI.
- No EDI endpoint was found under the previously-proven `partnersbiz.com` report-request paths; these `/v1/vis/*` and `/v1/sandbox/edi/*` routes are unique to this section and **not yet exercised by our blinkit-cli** (grep of `~/ecomcliauto/clis/blinkit-cli` and `VERIFIED-FINDINGS.md` shows zero EDI/aggregator/client-request references — this section is newly mapped).

## Real data seen (evidence)

- **Bundle-level (static) evidence only.** Analytics event enum present in `index.js` and `useFirebasePageTracking-CGSyAZ_Q.js`: `EDI_INTEGRATION_PAGE_VIEWED`, `EDI_INTEGRATION_VIEW_DOCUMENTATION_CLICKED`, `EDI_INTEGRATION_ACTIVATE_NOW_CLICKED`, `EDI_INTEGRATION_DIRECT_INTEGRATION_CLICKED`, `EDI_INTEGRATION_3RD_PART_INTEGRATION_CLICKED`, `EDI_INTEGRATION_DIRECT_INTEGRATION_DETAILS_SUBMITTED(_SUCCESSFULLY)`, `EDI_INTEGRATION_3RD_PARTY_DETAILS_SUBMITTED(_SUCCESSFULLY)`.
- Route wiring confirmed in `captures/partner/routes.js`: `N("developers/documentation", $t)` and `N("developers", Xt)`; menu mapping `case "developers": return …EDI_INTEGRATION`; help-ticket mapping `"/developers":{category:"edi_asn",ticketFilter:"OTHERS"}` (so support tickets from this page are categorized `edi_asn`).
- Support contact hard-coded: `edi-support@grofers.com`.
- **No live API response captured.** The screenshot `captures/partner/sec-09-edi-integration.png` is a placeholder (it is the PartnersBiz login page, identical byte-size to every other `sec-*` capture) — not an actual EDI screen. No request/response bodies for `/v1/vis/*` or `/v1/client-requests/` exist in the local captures. For Jivo (entity 1117) we have **no evidence of an existing EDI request/lead** — current status is unknown from local material.

## What a READ-ONLY CLI would expose (candidate commands)

Genuinely read-only, low-value-but-safe candidates (all GET):

- `blinkit edi partners` → `GET /v1/vis/enabled-aggregators/` — list the certified EDI integration partners/aggregators available for third-party integration.
- `blinkit edi doc [--out spec.yaml]` → `GET /v1/sandbox/edi/yaml-doc` — download the EDI API OpenAPI/Swagger spec (useful reference for anyone building the actual EDI integration; this is the same spec the portal renders in Scalar).
- `blinkit edi status` → read `edi_lead_generation` (`is_active`, `current_lead_status`, chosen `aggregator`) from the app config bootstrap — **endpoint to confirm via live network capture** before wiring; do not invent a path.

Explicitly **excluded from a read-only CLI (writes / side-effects):**
- `POST /v1/client-requests/` (submit a Direct/Third-Party integration request) — **OUT OF SCOPE.**
- `GET /v1/vis/generate-url/?aggregator=…` — although GET-shaped, it initiates the OAuth activation handshake and opens an authorization flow; **exclude** from a read-only tool (activation, not reporting).

Overall: this section carries no operational business data, so a read-only CLI adds little beyond the aggregator list and the spec download. The valuable, actionable capability (activating EDI) is entirely write/activation and therefore out of scope.

## Connections

- Portal shell: [[Partner-Hub]] · [[00-Blinkit-Atlas]]
- Automates the document flows owned by [[PO-Summary]] (Purchase Orders), [[Invoices]] (Vendor Invoices) and ASNs — EDI is the machine-to-machine alternative to those manual portal screens.
- Related async-export surface (the other "give me my data programmatically" path): [[Report-Requests]], feeding [[Sales]] and [[Stock-on-Hand]].
- Support tickets raised here are categorized `edi_asn` and land in [[Partner-Hub]]'s Help & Support.
