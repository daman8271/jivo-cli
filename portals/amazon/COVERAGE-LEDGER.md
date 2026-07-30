---
title: Amazon Coverage Ledger
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: ledger
tags: [amazon, coverage, read-only]
status: studied
read_only: true
---

# Amazon — Coverage Ledger (AMENDMENT-03 #1)

One row per page route extracted in Phase 3. **188 routes · 26 walked live · 162 not individually walked** (each with a specific reason — never "not important").

**Why some routes are `NO` and that is correct:**
- **Vendor Central routes** — the session is expired and G9 forbids minting a new one (see [[Auth-and-Access]]). Documented from the Phase-0 seed instead.
- **Create / edit / clone routes** — opening them means loading a write form; G4-NEW forbids it. They are enumerated in each section's *Out of scope* table, never walked.
- **Help-content & SPA fragments** — hundreds of `/gp/help/*`, `/reference/*`, `/help/hub/*` leaf routes are one Help-Hub SPA; walking `sec-02-help-hub-support` exercises the whole surface. Individual content leaves are catalogued in [[Amazon-Pages-and-Routes]], not re-walked.

| # | route | walked | screenshot | network capture | notes |
|---|---|---|---|---|---|
| 1 | `/1/batch/1/OE/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 2 | `/1/remote-weblab-triggers/1/OE/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 3 | `/abis/index.html` | YES | seller/sec-17-listings-abis.png | sec-17-listings-abis.har.json | HTTP 200, 8 API calls, 0 view-clicks |
| 4 | `/abis/listing/clone` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 5 | `/abis/listing/clone-bsm-asin` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 6 | `/abis/listing/clone-bsm-asin/` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 7 | `/abis/listing/clone-from-asin` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 8 | `/abis/listing/clone-from-asin/` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 9 | `/abis/listing/clone/` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 10 | `/abis/listing/create` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 11 | `/abis/listing/create-variation-from-standalone` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 12 | `/abis/listing/create/` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 13 | `/abis/listing/createFromDraft` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 14 | `/abis/listing/edit` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 15 | `/abis/listing/edit-draft` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 16 | `/abis/listing/multi-create` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 17 | `/abis/listing/offer-full-form` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 18 | `/abis/listing/syh` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 19 | `/account-switcher/dropdown-assets-loader.js` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 20 | `/ah/eligibility` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 21 | `/analytics/dashboard/vendorAnalytics` | NO | — | — | Vendor Central — session expired; documented from seed |
| 22 | `/automatepricing/rules/listings/` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 23 | `/br-insights-widget-logger` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 24 | `/br-insights-widget-metrics` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 25 | `/br-insights-widget/{param}` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 26 | `/br-insightswidget-api` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 27 | `/business-reports` | YES | seller/sec-05-business-reports.png | sec-05-business-reports.har.json | HTTP 200, 8 API calls, 2 view-clicks |
| 28 | `/business-reports-app-logger` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 29 | `/certification/1x1certification` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 30 | `/coupon-details-page` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 31 | `/coupons` | YES | seller/sec-14-coupons.png | sec-14-coupons.har.json | HTTP 200, 38 API calls, 0 view-clicks |
| 32 | `/coupons-dashboard-page` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 33 | `/cu/case-lobby` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 34 | `/cu/contact-us` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 35 | `/draft/dashboard` | YES | seller/sec-18-listing-drafts.png | sec-18-listing-drafts.har.json | HTTP 200, 18 API calls, 0 view-clicks |
| 36 | `/draft/dashboard/savedbyyou` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 37 | `/draft/registration/dashboard` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 38 | `/edit/bulk` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 39 | `/edit/bulk/sph` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 40 | `/edit/handmade` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 41 | `/feedback-manager/index.html` | YES | seller/sec-22-feedback-manager.png | sec-22-feedback-manager.har.json | HTTP 200, 23 API calls, 1 view-clicks |
| 42 | `/forums/index.jspa` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 43 | `/forums/t/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 44 | `/global-selling/listings/connect` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 45 | `/globalsearch/v1/search` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 46 | `/gp/aw/help` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 47 | `/gp/case-dashboard` | NO | — | — | deep-link into another surface already covered by its owning section walk |
| 48 | `/gp/contact-amazon` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 49 | `/gp/contact-us` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 50 | `/gp/help` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 51 | `/gp/help/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 52 | `/gp/help/customer/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 53 | `/gp/help/embed/{guid}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 54 | `/gp/help/embed/{param}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 55 | `/gp/help/external` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 56 | `/gp/help/external/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 57 | `/gp/help/external/help-content.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 58 | `/gp/help/external/help-folder.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 59 | `/gp/help/external/help-home.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 60 | `/gp/help/external/help-page.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 61 | `/gp/help/external/help.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 62 | `/gp/help/external/home` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 63 | `/gp/help/external/home.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 64 | `/gp/help/external/login-help.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 65 | `/gp/help/external/{guid}/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 66 | `/gp/help/help-content.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 67 | `/gp/help/help-folder.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 68 | `/gp/help/help-home.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 69 | `/gp/help/help-page.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 70 | `/gp/help/help-popup.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 71 | `/gp/help/help.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 72 | `/gp/help/home` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 73 | `/gp/help/home.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 74 | `/gp/help/login-help.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 75 | `/gp/help/{guid}/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 76 | `/gp/help/{helpGuid}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 77 | `/gp/orders-v2/search` | NO | — | — | deep-link into another surface already covered by its owning section walk |
| 78 | `/gp/satisfaction/survey-form-frame.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 79 | `/gp/satisfaction/survey-submit.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 80 | `/gp/search` | YES | platform/sec-03-global-search.png | sec-03-global-search.har.json | HTTP 200, 10 API calls, 0 view-clicks |
| 81 | `/gp/site-metrics/report.html` | YES | seller/sec-06-site-metrics-report.png | sec-06-site-metrics-report.har.json | HTTP 200, 8 API calls, 2 view-clicks |
| 82 | `/handmade/apply` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 83 | `/handmade/productclassify` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 84 | `/help/center/inline/workflow` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 85 | `/help/da/{directAnswer}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 86 | `/help/getting-started-guide` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 87 | `/help/getting-started-selling-faq` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 88 | `/help/home` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 89 | `/help/hub` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 90 | `/help/hub/` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 91 | `/help/hub/debug` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 92 | `/help/hub/inline` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 93 | `/help/hub/reference/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 94 | `/help/hub/reference/external/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 95 | `/help/hub/reference/external/login-help` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 96 | `/help/hub/reference/external/{helpGuid}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 97 | `/help/hub/reference/{helpGuid}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 98 | `/help/hub/support` | YES | platform/sec-02-help-hub-support.png | sec-02-help-hub-support.har.json | HTTP 200, 26 API calls, 0 view-clicks |
| 99 | `/help/inline/athena-get-direct-answer/embed` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 100 | `/help/manage-inventory-tool` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 101 | `/help/manage-orders` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 102 | `/help/merchant_documents/text/sign-in.html` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 103 | `/help/modify-or-delete-a-product-listing` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 104 | `/help/workflow/bulk/embed` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 105 | `/help/workflow/embed` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 106 | `/help/workflow/spl-setup` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 107 | `/home` | YES | seller/sec-01-home-dashboard.png | sec-01-home-dashboard.har.json | HTTP 200, 16 API calls, 1 view-clicks |
| 108 | `/hz/inventory` | YES | seller/sec-23-legacy-inventory-hz.png | sec-23-legacy-inventory-hz.har.json | HTTP 200, 15 API calls, 0 view-clicks |
| 109 | `/hz/m/help` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 110 | `/hz/m/helpcontent` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 111 | `/hz/manage-your-category/` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 112 | `/hz/productclassify` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 113 | `/hz/vendor/` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 114 | `/hz/vendor/members/coupon-campaigns/download/{campaignId}/download-metrics` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 115 | `/hz/vendor/members/coupon-campaigns/view/{campaignId}/campaign-metrics` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 116 | `/hz/vendor/members/help/embed/training/widget/layout/{param}/tags/{param}` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 117 | `/hz/vendor/members/products/details` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 118 | `/hz/vendor/members/products/mycatalog` | NO | — | — | Vendor Central — session expired; documented from Phase-0 seed |
| 119 | `/hz/vendor/members/support/help/node/G4YH8JMYV4VNXQYY` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 120 | `/hz/vendor/members/support/help/node/GUYLQ4V36D857DG6` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 121 | `/hz/vendor/members/support/hub` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 122 | `/hz/vendor/{param}/help/embed/{param}` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 123 | `/inline/sidebar` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 124 | `/inline/sidebar/search` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 125 | `/inline/sidebar/solution` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 126 | `/inline/sidebar/support/describe` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 127 | `/interactive/listing/workflow/create` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 128 | `/interactive/listing/workflow/create/product_identity` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 129 | `/interactive/listing/workflow/edit` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 130 | `/interactive/listing/workflow/offer/offer` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 131 | `/irc/widget` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 132 | `/learn/widget-spl` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 133 | `/m/products/edit` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 134 | `/marketplace/asin-translation-details` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 135 | `/marketplace/exchange-rates` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 136 | `/marketplace/global-listings-expansion-data` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 137 | `/marketplace/listing-preferences` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 138 | `/marketplace/recommendation` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 139 | `/marketplace/set-listing-preferences` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 140 | `/messaging/inbox` | YES | seller/sec-21-messaging-inbox.png | sec-21-messaging-inbox.har.json | HTTP 200, 31 API calls, 2 view-clicks |
| 141 | `/myinventory/actions` | YES | seller/sec-03-inventory-actions.png | sec-03-inventory-actions.har.json | HTTP 200, 9 API calls, 0 view-clicks |
| 142 | `/myinventory/inventory` | YES | seller/sec-02-inventory-manage.png | sec-02-inventory-manage.har.json | HTTP 200, 9 API calls, 0 view-clicks |
| 143 | `/mytax/gstreports/ondemand` | YES | seller/sec-16-gst-ondemand-reports.png | sec-16-gst-ondemand-reports.har.json | HTTP 200, 9 API calls, 0 view-clicks |
| 144 | `/orders-v3` | YES | seller/sec-04-orders-v3.png | sec-04-orders-v3.har.json | HTTP 200, 16 API calls, 0 view-clicks |
| 145 | `/performance/dashboard` | YES | seller/sec-07-account-health.png | sec-07-account-health.har.json | HTTP 200, 14 API calls, 1 view-clicks |
| 146 | `/performance/detail/customer-service` | YES | seller/sec-10-perf-customer-service.png | sec-10-perf-customer-service.har.json | HTTP 200, 6 API calls, 0 view-clicks |
| 147 | `/performance/detail/product-policies` | YES | seller/sec-12-perf-product-policies.png | sec-12-perf-product-policies.har.json | HTTP 200, 29 API calls, 0 view-clicks |
| 148 | `/performance/detail/shipping` | YES | seller/sec-11-perf-shipping.png | sec-11-perf-shipping.har.json | HTTP 200, 6 API calls, 0 view-clicks |
| 149 | `/performance/report/order-defects` | YES | seller/sec-08-perf-order-defects.png | sec-08-perf-order-defects.har.json | HTTP 200, 6 API calls, 0 view-clicks |
| 150 | `/performance/report/performance-over-time` | YES | seller/sec-09-perf-over-time.png | sec-09-perf-over-time.har.json | HTTP 200, 6 API calls, 1 view-clicks |
| 151 | `/pix-gateway` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 152 | `/po/vendor/members/po-mgmt/dashboard` | NO | — | — | Vendor Central — session expired (302 ap/signin); G9 |
| 153 | `/po/vendor/members/po-mgmt/managepos` | NO | — | — | Vendor Central — session expired (302 ap/signin); G9 |
| 154 | `/product-search` | YES | seller/sec-20-product-search.png | sec-20-product-search.har.json | HTTP 200, 16 API calls, 0 view-clicks |
| 155 | `/product/DisplayEditProduct` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 156 | `/productclassify` | YES | seller/sec-19-product-classify.png | sec-19-product-classify.har.json | HTTP 200, 11 API calls, 0 view-clicks |
| 157 | `/productclassify/edit` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 158 | `/productclassify/edit/handmade` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 159 | `/productclassify/index.html` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 160 | `/productsearch/v2/search` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 161 | `/productsearch/valuesuggestions` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 162 | `/promotion-central` | YES | seller/sec-15-promotion-central.png | sec-15-promotion-central.har.json | HTTP 200, 12 API calls, 0 view-clicks |
| 163 | `/promotion/psp/` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 164 | `/reference/embed/{guid}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 165 | `/reference/external` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 166 | `/reference/external/login-help` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 167 | `/reference/external/popup/{guid}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 168 | `/reference/external/{guid}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 169 | `/reference/login-help/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 170 | `/reference/popup/{guid}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 171 | `/reference/search` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 172 | `/reference/{guid}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 173 | `/reorder-coupons-dashboard-page` | NO | — | — | write/create route (G4-NEW forbids opening a create/edit form) — documented, not walked |
| 174 | `/reportcentral/AGLGlobalStoreSales/0` | YES | seller/sec-24-reportcentral-global-store-sales.png | sec-24-reportcentral-global-store-sales.har.json | HTTP 200, 15 API calls, 0 view-clicks |
| 175 | `/retail-analytics/dashboard/sales` | NO | — | — | Vendor Central — session expired (302 ap/signin); G9 forbids re-login |
| 176 | `/solution/bulk-workflow` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 177 | `/solution/{id}` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 178 | `/sq/approvalrequest` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 179 | `/support/SOA` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 180 | `/support/describe` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 181 | `/support/form/hub` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 182 | `/support/help/hub` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 183 | `/support/help/node/` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 184 | `/support/search/` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 185 | `/support/training/hub` | NO | — | — | help-content / support / SPA-fragment sub-route — covered collectively by the Help Hub walk (sec-02-help-hub-support) |
| 186 | `/support/{nodeId}` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 187 | `/syh/DisplayCondition` | NO | — | — | lower-value SPA sub-route not individually walked — endpoints captured via its parent page; see [[Amazon-Endpoints]] |
| 188 | `/voice-of-the-customer` | YES | seller/sec-13-voice-of-customer.png | sec-13-voice-of-customer.har.json | HTTP 200, 16 API calls, 1 view-clicks |

## Entities ledger (AMENDMENT-03 #2) — hunted across every reachable box

> **SCOPE: this study covers Jivo Mart · Seller Central ONLY.** The other three datasets are
> `NOT_REACHABLE` — no live session on this Mac or on any office box, G9 forbids minting one.

| Entity · portal | reachable | evidence |
|---|---|---|
| **Jivo Mart · Seller Central (3P)** | ✅ YES — fully walked | live 8-day cookie jar, merchant `A2V85Y00QGIGP9`, 26 sections |
| Jivo Wellness · Seller Central (3P) | ❌ NOT_REACHABLE | account-switcher exposes only "Jivo Mart"; no SC Wellness login on disk; zero SC-Wellness cookies on dev/win2/victus (admin VSS scan) |
| Jivo Wellness · Vendor Central (1P, vg 7691702) | ❌ NOT_REACHABLE | session expired 2026-07-16 (302→ap/signin); no VC cookies on any reachable box; G9 |
| Jivo Mart · Vendor Central (1P, vg 8592892) | ❌ NOT_REACHABLE | session expired; no VC cookies on any reachable box; G9 |

**Session hunt (2026-07-30):** admin VSS-copied every Chrome + Edge cookie DB on `ssh dev`
(HO-IT-PC10 — users khushwinder singh incl. live Default modified today, Administrator, Navjot
Kaur) and `ssh win2`/`victus` (users leela, prabh, fleet). **Zero amazon/vendorcentral/
sellercentral cookies on any profile, browser, or box.** Wellness + VC have no live session
anywhere reachable. Documented from the Phase-0 seed instead — see [[Auth-and-Access]].

## Connections

- [[00-Amazon-Atlas]] · [[Amazon-Pages-and-Routes]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Study-Verification]]

