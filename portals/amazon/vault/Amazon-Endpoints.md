---
title: Amazon Endpoints (master ledger)
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: index
tags: [amazon, endpoints, read-only]
status: studied
read_only: true
---

# Amazon — Master Endpoint Ledger

**432 distinct endpoint contracts** across **20 hosts**, consolidated from the static bundle corpus + the live walk. **162 are PROVEN** (returned HTTP 200 to a read-only GET this run). Classification is the read-only allowlist decision — see [[Read-Only-Guardrails]].

| Class | Count | In the CLI? | Meaning |
|---|---|---|---|
| `READ` | 162 | ✅ allowlisted | pure GET JSON read |
| `READ_FILE` | 91 | ✅ allowlisted | GET of a file / static asset already produced |
| `READ_POST` | 9 | ❌ excluded | semantic read but HTTP **POST** — G0 forbids POST |
| `WRITE` | 55 | ❌ excluded | mutating verb/path (G2/G0) |
| `UNKNOWN` | 91 | ❌ excluded | verb/posture not proven (G1: denied) |
| `NOISE` | 24 | ❌ excluded | telemetry / weblab / instrumentation, not business data |

> The allowlist the CLI is generated from = `READ` + `READ_FILE` = **253** contracts. Everything else is documented here and held out — per AMENDMENT-03 #8, *denied is not the same as undocumented*.

## `d1hw4uzgiurk5n.cloudfront.net` (1 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ | ✅ | GET | `/` |  |

## `d1pp2iw517bkb8.cloudfront.net` (2 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/i18n/translation-en.json` |  |
| READ_FILE | ✅ | GET | `/i18n/translation.json` |  |

## `d1uznvntk80v7s.cloudfront.net` (2 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/metrics.{hash}.js` |  |
| READ_FILE | ✅ | GET | `/metrics.{hash}.js.map` |  |

## `d2pihuraj6wacp.cloudfront.net` (2 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/i18n/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/i18n/en-US.{hash}.i18next.json` |  |

## `d3c9w1p5457qe7.cloudfront.net` (4 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/i18n/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/i18n/en-US.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/i18n/translation-en.{hash}.json` |  |
| READ_FILE | ✅ | GET | `/i18n/translation.{hash}.json` |  |

## `d3h0qy3grrnlx3.cloudfront.net` (1 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ | ✅ | GET | `/` |  |

## `d3ksbe4ctckde3.cloudfront.net` (2 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/en-US.{hash}.i18next.json` |  |

## `d3re0qkvcj2drt.cloudfront.net` (16 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/account-health/en-IN.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/account-health/en-US.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/compliance-request/en-IN.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/compliance-request/en-US.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/contact-us/en-IN.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/contact-us/en-US.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/dominion-dashboard/en-IN.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/dominion-dashboard/en-US.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/policy-warning/en-IN.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/policy-warning/en-US.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/product-policies/en-IN.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/product-policies/en-US.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/reactivate-account/en-IN.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/reactivate-account/en-US.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/shared-strings/en-IN.json` |  |
| READ_FILE | ✅ | GET | `/performance/account/health/i18n/shared-strings/en-US.json` |  |

## `d3rhl38hdptmva.cloudfront.net` (2 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/i18n/translations/translation-en.{hash}.json` |  |
| READ_FILE | ✅ | GET | `/i18n/translations/translation.{hash}.json` |  |

## `d3ttb92cjixe5s.cloudfront.net` (4 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/en-US.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/i18n/en-IN.json` |  |
| READ_FILE | ✅ | GET | `/i18n/en-US.json` |  |

## `d7xm6m3peqvfj.cloudfront.net` (2 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/static/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/static/en-US.{hash}.i18next.json` |  |

## `d84t02egg0ytc.cloudfront.net` (2 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/voc-katal/i18n/translation-en.{hash}.json` |  |
| READ_FILE | ✅ | GET | `/voc-katal/i18n/translation.{hash}.json` |  |

## `dmsjnm3xe0ebz.cloudfront.net` (4 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/i18n/ImageCompliance/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/i18n/ImageCompliance/en-US.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/i18n/QuickListContent/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/i18n/QuickListContent/en-US.{hash}.i18next.json` |  |

## `dp0zvwwqb1q92.cloudfront.net` (2 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ | ✅ | GET | `/Manifest/components.json` |  |
| READ_FILE | ✅ | GET | `/AnyUICore/sdk.js` |  |

## `dy8z3jvmvymcp.cloudfront.net` (2 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/i18n/translation-en.json` |  |
| READ_FILE | ✅ | GET | `/i18n/translation.json` |  |

## `m.media-amazon.com` (1 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| NOISE | ✅ | GET | `/images/G/01/csm/showads.v2.js` |  |

## `sellercentral.amazon.in` (359 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| NOISE |  | ? | `/1/batch/1/OE/` |  |
| NOISE |  | ? | `/1/remote-weblab-triggers/1/OE/` |  |
| NOISE |  | ? | `/br-insights-widget-logger` | url |
| NOISE |  | ? | `/business-reports-app-logger` | url |
| NOISE | ✅ | GET | `/coupons/api/weblabs/all` |  |
| NOISE |  | ? | `/coupons/logs` | url |
| NOISE |  | ? | `/homepage/knowhere/events/record` |  |
| NOISE | ✅ | GET | `/messaging/api/global/weblab` |  |
| NOISE | ✅ | GET | `/messaging/api/global/weblab/v2` |  |
| NOISE |  | GET | `/messaging/api/weblab/marketplace` |  |
| NOISE | ✅ | GET | `/mons/weblabs` | weblabPath |
| NOISE |  | ? | `/mons/weblabs/` | url |
| NOISE | ✅ | GET | `/mons/weblabs/merchant/treatment` |  |
| NOISE |  | POST | `/mons/weblabs/merchant/trigger` |  |
| NOISE |  | GET | `/mons/weblabs/vendor/treatment` |  |
| NOISE |  | ? | `/ping` |  |
| NOISE |  | ? | `/spl/logger` | url |
| NOISE |  | POST | `/tricorder/decide/` |  |
| NOISE |  | POST | `/tricorder/e/` |  |
| NOISE |  | ? | `/tricorder/logger` | url |
| READ |  | ? | `/abis/index.html` |  |
| READ | ✅ | GET | `/account-switcher/global-and-regional-account/merchantMarketplace` |  |
| READ | ✅ | GET | `/ahd/floatingWidget` |  |
| READ | ✅ | GET | `/ahd/issueTypeTags` |  |
| READ | ✅ | GET | `/ahd/priorityActions` |  |
| READ | ✅ | GET | `/appeal/appeals/csrf` |  |
| READ |  | GET | `/br-insights-widget/{param}` | url |
| READ | ✅ | GET | `/communities/seller-news/articles` |  |
| READ | ✅ | GET | `/conversation-api/v1/notifications` |  |
| READ | ✅ | GET | `/conversation-api/v1/sidebarContext` |  |
| READ | ✅ | GET | `/coupons/api/banners` |  |
| READ | ✅ | GET | `/coupons/api/config` |  |
| READ | ✅ | GET | `/coupons/api/getCouponPromotions` |  |
| READ | ✅ | GET | `/coupons/api/merchantInfo` |  |
| READ | ✅ | GET | `/coupons/api/tailoring` |  |
| READ | ✅ | GET | `/coupons/undefined` |  |
| READ |  | ? | `/cu/case-lobby` |  |
| READ |  | ? | `/cu/contact-us` | url |
| READ |  | ? | `/draft/dashboard` |  |
| READ |  | ? | `/draft/registration/dashboard` |  |
| READ | ✅ | GET | `/drafts/api/get` |  |
| READ | ✅ | GET | `/drafts/api/getContributors` |  |
| READ | ✅ | GET | `/fba/gstreports/report-history` |  |
| READ | ✅ | GET | `/fbmapi/v1/aggregates` |  |
| READ | ✅ | GET | `/fbmapi/v1/csrf` |  |
| READ | ✅ | GET | `/fbmapi/v1/feedbacks` |  |
| READ | ✅ | GET | `/fbmapi/v1/metadata` |  |
| READ | ✅ | GET | `/fbmapi/v1/orderperformanceSellerBar` |  |
| READ | ✅ | GET | `/fbmapi/v1/orderperformanceUIVersions` |  |
| READ |  | ? | `/forums/index.jspa` | url |
| READ |  | ? | `/forums/t/` |  |
| READ |  | GET | `/gp/help/` |  |
| READ |  | ? | `/gp/help/customer/` | path |
| READ |  | ? | `/gp/help/embed/{guid}` | path |
| READ |  | ? | `/gp/help/embed/{param}` | source |
| READ |  | ? | `/gp/help/external` | path |
| READ |  | GET | `/gp/help/external/` |  |
| READ |  | ? | `/gp/help/external/help-content.html` | path |
| READ |  | ? | `/gp/help/external/help-folder.html` | path |
| READ |  | ? | `/gp/help/external/help-home.html` | path |
| READ |  | ? | `/gp/help/external/help-page.html` | path |
| READ |  | ? | `/gp/help/external/help.html` | path |
| READ |  | ? | `/gp/help/external/home` | path |
| READ |  | ? | `/gp/help/external/home.html` | path |
| READ |  | ? | `/gp/help/external/login-help.html` | path |
| READ |  | ? | `/gp/help/external/{guid}/` | path |
| READ |  | ? | `/gp/help/help-content.html` | path |
| READ |  | ? | `/gp/help/help-folder.html` | path |
| READ |  | ? | `/gp/help/help-home.html` | path |
| READ |  | ? | `/gp/help/help-page.html` | path |
| READ |  | ? | `/gp/help/help-popup.html` | path |
| READ |  | ? | `/gp/help/help.html` | path |
| READ |  | ? | `/gp/help/home` | path |
| READ |  | ? | `/gp/help/home.html` | path |
| READ |  | ? | `/gp/help/login-help.html` | path |
| READ |  | ? | `/gp/help/{guid}/` | path |
| READ |  | ? | `/gp/help/{helpGuid}` | THIRD_PARTY |
| READ |  | ? | `/gp/satisfaction/survey-form-frame.html` | url |
| READ |  | GET | `/gp/satisfaction/survey-submit.html` | RAINFOREST_HMD_ENDPOINT |
| READ |  | ? | `/help/center/inline/workflow` | source |
| READ |  | ? | `/help/da/{directAnswer}` | path |
| READ |  | ? | `/help/getting-started-guide` | path |
| READ |  | ? | `/help/getting-started-selling-faq` | path |
| READ |  | ? | `/help/home` | path |
| READ |  | GET | `/help/hub/` |  |
| READ |  | ? | `/help/hub/debug` | href |
| READ |  | ? | `/help/hub/inline` |  |
| READ | ✅ | GET | `/help/hub/mons-api/GetBootstrapData` |  |
| READ | ✅ | GET | `/help/hub/mons-api/GetFeatureStatus` |  |
| READ | ✅ | GET | `/help/hub/mons-api/GetMeldEligibility` |  |
| READ |  | GET | `/help/hub/reference/` |  |
| READ |  | GET | `/help/hub/reference/external/` |  |
| READ |  | ? | `/help/hub/reference/external/login-help` |  |
| READ |  | ? | `/help/hub/reference/external/{helpGuid}` | href |
| READ |  | ? | `/help/hub/reference/{helpGuid}` |  |
| READ |  | GET | `/help/hub/support` |  |
| READ |  | ? | `/help/inline/athena-get-direct-answer/embed` | source |
| READ |  | ? | `/help/manage-inventory-tool` | path |
| READ |  | ? | `/help/manage-orders` | path |
| READ |  | ? | `/help/merchant_documents/text/sign-in.html` | path |
| READ |  | ? | `/help/workflow/bulk/embed` | source |
| READ |  | ? | `/help/workflow/embed` | source |
| READ |  | ? | `/help/workflow/spl-setup` | providerArgumentSource |
| READ | ✅ | GET | `/hill/hillservice/mons-api/GetBootstrapConfig` |  |
| READ | ✅ | GET | `/hill/hillservice/mons-api/GetSpecialistSupportIngressEligibility` |  |
| READ |  | ? | `/home` | href |
| READ | ✅ | GET | `/homepage/casino/cards/content/async-card/` |  |
| READ |  | ? | `/hz/vendor/members/support/hub` | ADVANTAGE |
| READ | ✅ | GET | `/inventoryplanning/check-unread-message` |  |
| READ | ✅ | GET | `/inventoryplanning/stranded-inventory/autoRemovalSettings` |  |
| READ | ✅ | GET | `/lyp/api/enabledFeatures` |  |
| READ | ✅ | GET | `/meld/mons-api/GetMarketplaceSwitcher` |  |
| READ | ✅ | GET | `/messaging/api/global/cases` |  |
| READ | ✅ | GET | `/messaging/api/global/cases/{uuid}` |  |
| READ | ✅ | GET | `/messaging/api/global/cases/{uuid}/orderContext` |  |
| READ | ✅ | GET | `/messaging/api/global/cases/{uuid}/responsetemplates` |  |
| READ | ✅ | GET | `/messaging/api/global/partnerAccounts` |  |
| READ | ✅ | GET | `/messaging/api/global/partnerAccounts/marketplaces` |  |
| READ | ✅ | GET | `/messaging/api/global/rights` |  |
| READ | ✅ | GET | `/messaging/api/global/topics/categories` |  |
| READ |  | ? | `/messaging/inbox` |  |
| READ | ✅ | GET | `/messaging/overview/api/metric/contactsReportedUnresolved` |  |
| READ | ✅ | GET | `/messaging/overview/api/metric/contactsRequireAttention` |  |
| READ | ✅ | GET | `/messaging/overview/api/metric/contactsResolved` |  |
| READ | ✅ | GET | `/messaging/overview/api/metric/contactsResponseNeeded` |  |
| READ |  | GET | `/multi-channel/listings/api/catalogs` |  |
| READ | ✅ | GET | `/orders-api/adConfig` |  |
| READ | ✅ | GET | `/orders-api/manifest-v3` |  |
| READ | ✅ | GET | `/orders-api/manifest-v3/quick-filters` |  |
| READ | ✅ | GET | `/orders-api/notifications/MYO_LIST_ORDERS_EASYSHIP` |  |
| READ | ✅ | GET | `/orders-api/prefs/table-content` |  |
| READ | ✅ | GET | `/orders-api/search` |  |
| READ | ✅ | GET | `/pcrHealth/download` |  |
| READ | ✅ | GET | `/pcrHealth/pcrKpi` |  |
| READ | ✅ | GET | `/pcrHealth/pcrListingSummary` |  |
| READ | ✅ | GET | `/performance/api/getriskbanner/` |  |
| READ | ✅ | GET | `/performance/api/summary` |  |
| READ | ✅ | GET | `/productclassify/api/browse` |  |
| READ | ✅ | GET | `/productclassify/api/context` |  |
| READ | ✅ | GET | `/productclassify/api/favorites` |  |
| READ |  | ? | `/productclassify/index.html` |  |
| READ |  | GET | `/promotion-central/api/v1/settings` |  |
| READ |  | ? | `/reference/embed/{guid}` | path |
| READ |  | ? | `/reference/external` | path |
| READ |  | ? | `/reference/external/login-help` | path |
| READ |  | ? | `/reference/external/popup/{guid}` | path |
| READ |  | ? | `/reference/external/{guid}` | path |
| READ |  | ? | `/reference/login-help/` | path |
| READ |  | ? | `/reference/popup/{guid}` | path |
| READ |  | ? | `/reference/search` | isSearchView |
| READ |  | ? | `/reference/{guid}` | path |
| READ | ✅ | GET | `/reportcentral/api/v1/getRecentlyVisitedReports` |  |
| READ | ✅ | GET | `/reportcentral/api/v1/getReportConfigurations` |  |
| READ | ✅ | GET | `/reportcentral/api/v1/getReportPreferences` |  |
| READ | ✅ | GET | `/reportcentral/api/v1/getWhatsNewConfiguration` |  |
| READ | ✅ | GET | `/roboapi/v1/sc/announcements` |  |
| READ |  | GET | `/solution/bulk-workflow` | path |
| READ |  | ? | `/support/SOA` |  |
| READ |  | ? | `/support/describe` | path |
| READ |  | ? | `/support/form/hub` |  |
| READ |  | ? | `/support/help/hub` |  |
| READ |  | ? | `/support/help/node/` |  |
| READ |  | ? | `/support/search/` |  |
| READ |  | ? | `/support/training/hub` |  |
| READ |  | ? | `/support/{nodeId}` | path |
| READ | ✅ | GET | `/trim/json/favorites/sellerCentral` |  |
| READ_FILE |  | ? | `/account-switcher/dropdown-assets-loader.js` | src |
| READ_FILE | ✅ | GET | `/coupons/i18n/ar-AE.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/de-DE.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/en-AU.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/en-CA.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/en-GB.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/en-IE.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/en-SG.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/en-US.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/en-ZA.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/es-ES.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/es-MX.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/fr-BE.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/fr-FR.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/it-IT.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/ja-JP.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/nl-NL.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/pl-PL.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/pt-BR.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/sv-SE.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/th-TH.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/coupons/i18n/tr-TR.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/feedback-manager/i18n/en-IN.json` |  |
| READ_FILE | ✅ | GET | `/feedback-manager/i18n/en-US.json` |  |
| READ_FILE | ✅ | GET | `/help/hub/i18n/HelpHubKatalWebsite/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/help/hub/i18n/HelpHubKatalWebsite/en-US.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/hill/website/i18n/HillWebsite/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/hill/website/i18n/HillWebsite/en-US.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/hill/website/i18n/HillWebsiteCaseLobby/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/hill/website/i18n/HillWebsiteCaseLobby/en-US.{hash}.i18next.json` |  |
| READ_FILE |  | ? | `/hz/m/helpcontent` | path |
| READ_FILE |  | ? | `/marketplace/asin-translation-details` |  |
| READ_FILE | ✅ | GET | `/messaging/v2/i18n/en-IN.{hash}.json` |  |
| READ_FILE | ✅ | GET | `/messaging/v2/i18n/en-US.{hash}.json` |  |
| READ_FILE | ✅ | GET | `/performance/widget/translations/i18n/translation-en.json` |  |
| READ_FILE | ✅ | GET | `/performance/widget/translations/i18n/translation.json` |  |
| READ_FILE | ✅ | GET | `/productclassify/i18n/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/productclassify/i18n/en-US.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/reportcentral/i18n/en-GB.json` |  |
| READ_FILE | ✅ | GET | `/reportcentral/i18n/en-IN.json` |  |
| READ_FILE | ✅ | GET | `/reportcentral/i18n/en-US.json` |  |
| READ_FILE | ✅ | GET | `/voc-katal/i18n/en-IN.{hash}.i18next.json` |  |
| READ_FILE | ✅ | GET | `/voc-katal/i18n/en-US.{hash}.i18next.json` |  |
| READ_POST |  | POST | `/br-insightswidget-api` |  |
| READ_POST |  | POST | `/fba/dashboard/bff/graphql` |  |
| READ_POST |  | POST | `/messaging/api/resourceError` |  |
| READ_POST |  | POST | `/performance/api/postBizMetricsWithMap/` |  |
| READ_POST |  | POST | `/pulse/v1/question` |  |
| UNKNOWN |  | ? | `/abis/ajax/EasyListConfig` |  |
| UNKNOWN |  | ? | `/abis/ajax/brand/authorization` |  |
| UNKNOWN |  | ? | `/abis/ajax/detailPageInfo` |  |
| UNKNOWN |  | ? | `/abis/ajax/fix-listing` |  |
| UNKNOWN |  | ? | `/abis/ajax/get-standalone-for-variation` |  |
| UNKNOWN |  | ? | `/abis/ajax/losg-global/get-listing` |  |
| UNKNOWN |  | ? | `/abis/ajax/offer-full-form` |  |
| UNKNOWN |  | ? | `/abis/ajax/offer-prefilled` |  |
| UNKNOWN |  | ? | `/abis/ajax/reconciledDetailsV2` |  |
| UNKNOWN |  | ? | `/abis/ajax/searchSkus` |  |
| UNKNOWN |  | ? | `/abis/listing/offer-full-form` |  |
| UNKNOWN |  | ? | `/abis/listing/syh` |  |
| UNKNOWN |  | ? | `/abis/listing/v1/log` | url |
| UNKNOWN |  | ? | `/abis/product/ajax/FeePreview.ajax` |  |
| UNKNOWN |  | ? | `/abis/product/ajax/MarketplaceListingEvent.ajax` |  |
| UNKNOWN |  | ? | `/ah/eligibility` | href |
| UNKNOWN |  | ? | `/automatepricing/rules/listings/` |  |
| UNKNOWN |  | ? | `/br-insights-widget-metrics` | url |
| UNKNOWN |  | ? | `/business-reports/api` | uri |
| UNKNOWN |  | ? | `/certification/1x1certification` | source |
| UNKNOWN |  | ? | `/coupon-details-page` |  |
| UNKNOWN |  | ? | `/coupons-dashboard-page` |  |
| UNKNOWN |  | ? | `/coupons/api/asin` |  |
| UNKNOWN |  | ? | `/coupons/api/couponPromotion` |  |
| UNKNOWN |  | ? | `/coupons/api/couponPromotion/products` |  |
| UNKNOWN |  | ? | `/coupons/api/feePreview` |  |
| UNKNOWN |  | ? | `/coupons/api/product-selection/sns/` |  |
| UNKNOWN |  | ? | `/coupons/api/recommendations` |  |
| UNKNOWN |  | ? | `/coupons/api/search` |  |
| UNKNOWN |  | ? | `/coupons/api/sku` |  |
| UNKNOWN |  | ? | `/coupons/api/tailoring/merchant` |  |
| UNKNOWN |  | ? | `/coupons/api/v2/bulkItem` |  |
| UNKNOWN |  | ? | `/global-selling/listings/connect` |  |
| UNKNOWN |  | ? | `/globalsearch/v1/search` |  |
| UNKNOWN |  | ? | `/goblin/read` |  |
| UNKNOWN |  | ? | `/gp/aw/help` | path |
| UNKNOWN |  | ? | `/gp/case-dashboard` |  |
| UNKNOWN |  | ? | `/gp/contact-amazon` |  |
| UNKNOWN |  | ? | `/gp/contact-us` |  |
| UNKNOWN |  | ? | `/gp/help` | path |
| UNKNOWN |  | ? | `/gp/orders-v2/search` | url |
| UNKNOWN |  | ? | `/gp/search` | path |
| UNKNOWN |  | ? | `/handmade/productclassify` | legacyHandmadeProductClassify |
| UNKNOWN |  | ? | `/help/hub/mons-api/` |  |
| UNKNOWN |  | ? | `/hz/inventory` | url |
| UNKNOWN |  | ? | `/hz/m/help` | path |
| UNKNOWN |  | ? | `/hz/manage-your-category/` | manageYourCategory |
| UNKNOWN |  | ? | `/hz/productclassify` | legacyProductClassify |
| UNKNOWN |  | ? | `/hz/vendor/` |  |
| UNKNOWN |  | ? | `/hz/vendor/members/help/embed/training/widget/layout/{param}/tags/{param}` | source |
| UNKNOWN |  | ? | `/hz/vendor/members/products/details` | firstPartyOneByOnePage |
| UNKNOWN |  | ? | `/hz/vendor/members/products/mycatalog` |  |
| UNKNOWN |  | ? | `/hz/vendor/members/products/prismo/api/getcsrftoken` | firstPartyOneByOnePageCsrfToken |
| UNKNOWN |  | ? | `/hz/vendor/members/support/help/node/{helpGuid}` | FIRST_PARTY |
| UNKNOWN |  | ? | `/hz/vendor/{param}/help/embed/{param}` | source |
| UNKNOWN |  | ? | `/inline/sidebar` |  |
| UNKNOWN |  | ? | `/inline/sidebar/search` | path |
| UNKNOWN |  | ? | `/inline/sidebar/solution` | path |
| UNKNOWN |  | ? | `/inline/sidebar/support/describe` |  |
| UNKNOWN |  | ? | `/irc/widget` | source |
| UNKNOWN |  | ? | `/learn/widget-spl` | source |
| UNKNOWN |  | GET | `/m/products/edit` | mobileEditWorkflow |
| UNKNOWN |  | ? | `/marketplace/exchange-rates` |  |
| UNKNOWN |  | ? | `/marketplace/global-listings-expansion-data` |  |
| UNKNOWN |  | ? | `/marketplace/listing-preferences` |  |
| UNKNOWN |  | ? | `/marketplace/recommendation` |  |
| UNKNOWN |  | ? | `/myinventory/actions` | source |
| UNKNOWN |  | ? | `/myinventory/inventory` |  |
| UNKNOWN |  | ? | `/performance/detail/customer-service` |  |
| UNKNOWN |  | ? | `/performance/detail/product-policies` |  |
| UNKNOWN |  | ? | `/performance/detail/shipping` |  |
| UNKNOWN |  | ? | `/performance/report/order-defects` |  |
| UNKNOWN |  | ? | `/performance/report/performance-over-time` |  |
| UNKNOWN |  | ? | `/pix-gateway` | uri |
| UNKNOWN |  | ? | `/product-search` | productSearch |
| UNKNOWN |  | ? | `/productclassify/api` |  |
| UNKNOWN |  | ? | `/productclassify/api/browse-nodes` |  |
| UNKNOWN |  | ? | `/productclassify/api/pt-search` |  |
| UNKNOWN |  | ? | `/productsearch/v2/search` |  |
| UNKNOWN |  | ? | `/productsearch/valuesuggestions` |  |
| UNKNOWN |  | ? | `/promotion-central` |  |
| UNKNOWN |  | ? | `/promotion/psp/` |  |
| UNKNOWN |  | ? | `/reorder-coupons-dashboard-page` |  |
| UNKNOWN |  | ? | `/reportcentral/AGLGlobalStoreSales/0` | href |
| UNKNOWN |  | ? | `/solution/{id}` | path |
| UNKNOWN |  | ? | `/spsx/ajax/checkSellerQualification` |  |
| UNKNOWN |  | ? | `/spsx/ajax/getAttributesNormalizedValues` |  |
| UNKNOWN |  | ? | `/spsx/ajax/getContributionScope` |  |
| UNKNOWN |  | ? | `/spsx/ajax/getFBAEligibilityAndRecommendation` |  |
| UNKNOWN |  | ? | `/syh/DisplayCondition` | mobileSYHWorkflow |
| UNKNOWN |  | ? | `/voice-of-the-customer` |  |
| WRITE |  | ? | `/abis/ajax/S3ImageUpload` |  |
| WRITE |  | ? | `/abis/ajax/clone-bsm-asin` |  |
| WRITE |  | ? | `/abis/ajax/clone-from-asin` |  |
| WRITE |  | ? | `/abis/ajax/clone-listing` |  |
| WRITE |  | ? | `/abis/ajax/create-listing` |  |
| WRITE |  | ? | `/abis/ajax/create-offer` |  |
| WRITE |  | ? | `/abis/ajax/create-pt-selection` |  |
| WRITE |  | ? | `/abis/ajax/create-variation-from-standalone` |  |
| WRITE |  | ? | `/abis/ajax/edit` |  |
| WRITE |  | ? | `/abis/ajax/edit-draft` |  |
| WRITE |  | ? | `/abis/ajax/edit-draft/save` |  |
| WRITE |  | ? | `/abis/ajax/write-offer` |  |
| WRITE |  | ? | `/abis/ajax/write-offer-full-form` |  |
| WRITE |  | ? | `/abis/ajax/write-variation-from-standalone` |  |
| WRITE |  | ? | `/abis/listing/clone` |  |
| WRITE |  | ? | `/abis/listing/clone-bsm-asin` |  |
| WRITE |  | ? | `/abis/listing/clone-bsm-asin/` |  |
| WRITE |  | ? | `/abis/listing/clone-from-asin` |  |
| WRITE |  | ? | `/abis/listing/clone-from-asin/` |  |
| WRITE |  | ? | `/abis/listing/clone/` |  |
| WRITE |  | ? | `/abis/listing/create` | oneByOneAddProduct |
| WRITE |  | ? | `/abis/listing/create-variation-from-standalone` |  |
| WRITE |  | ? | `/abis/listing/create/` |  |
| WRITE |  | ? | `/abis/listing/createFromDraft` | oneByOneFixProduct |
| WRITE |  | ? | `/abis/listing/edit` | oneByOneEditProduct |
| WRITE |  | ? | `/abis/listing/edit-draft` |  |
| WRITE |  | ? | `/abis/listing/multi-create` |  |
| WRITE |  | ? | `/abis/product/ajax/CreationValidation` |  |
| WRITE |  | ? | `/abis/product/ajax/EditValidation` |  |
| WRITE |  | ? | `/abis/product/ajax/OfferValidation` |  |
| WRITE |  | ? | `/coupons/api/cancelCouponPromotion` |  |
| WRITE |  | ? | `/coupons/api/editCouponPromotion` |  |
| WRITE |  | ? | `/coupons/api/reportPromotionApprovalDecision` |  |
| WRITE |  | ? | `/coupons/api/v2/bulkUploadHistory` |  |
| WRITE |  | ? | `/coupons/api/v2/uploadBulkFile` |  |
| WRITE |  | ? | `/draft/dashboard/savedbyyou` |  |
| WRITE |  | ? | `/edit/bulk` | editBulk |
| WRITE |  | ? | `/edit/bulk/sph` | editBulkSph |
| WRITE |  | ? | `/edit/handmade` | editHandmade |
| WRITE |  | ? | `/featureOverride` |  |
| WRITE |  | ? | `/goblin/write` |  |
| WRITE |  | ? | `/handmade/apply` | gatingHandmadePage |
| WRITE |  | DELETE | `/help/hub` | url |
| WRITE |  | ? | `/help/modify-or-delete-a-product-listing` | path |
| WRITE |  | ? | `/interactive/listing/workflow/create` |  |
| WRITE |  | ? | `/interactive/listing/workflow/create/product_identity` |  |
| WRITE |  | ? | `/interactive/listing/workflow/edit` |  |
| WRITE |  | ? | `/interactive/listing/workflow/offer/offer` |  |
| WRITE |  | ? | `/marketplace/set-listing-preferences` |  |
| WRITE |  | ? | `/product/DisplayEditProduct` | oldEdit |
| WRITE |  | ? | `/productclassify/edit` |  |
| WRITE |  | ? | `/productclassify/edit/handmade` |  |
| WRITE |  | ? | `/sq/approvalrequest` |  |

## `static-assets.prod-dub.sellingpartnerho.homepages.selling-partners.amazon.dev` (2 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ_FILE | ✅ | GET | `/homepage/assets/translations/translation-en.{hash}.json` |  |
| READ_FILE | ✅ | GET | `/homepage/assets/translations/translation.{hash}.json` |  |

## `unagi.amazon.in` (3 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| NOISE |  | POST | `/1/events/com.amazon.csm.csa.prod` |  |
| NOISE |  | POST | `/1/events/com.amazon.csm.customsg.prod` |  |
| NOISE |  | POST | `/1/events/com.amazon.csm.nexusclient.prod` |  |

## `www.vendorcentral.in` (19 paths)

| Class | Live | Method | Path | Const |
|---|---|---|---|---|
| READ |  | GET | `/analytics/dashboard/vendorAnalytics` | vendorAnalytics |
| READ |  | GET | `/hz/vendor/members/coupon-campaigns/download/{campaignId}/download-metrics` | CouponDownloadMetrics |
| READ |  | GET | `/hz/vendor/members/coupon-campaigns/view/{campaignId}/campaign-metrics` | coupon-referer |
| READ |  | GET | `/hz/vendor/members/products/details` | product-details |
| READ |  | GET | `/hz/vendor/members/products/mycatalog` | mycatalog |
| READ |  | GET | `/hz/vendor/members/products/prismo/api/getcsrftoken` | getcsrftoken |
| READ |  | GET | `/hz/vendor/members/support/hub` | support-hub |
| READ |  | GET | `/po-api/vendor/homepage/homepage-asn-discrepancies` | homepage-asn-discrepancies |
| READ |  | GET | `/po-api/vendor/homepage/homepage-confirmation` | homepage-confirmation |
| READ |  | GET | `/po-api/vendor/homepage/homepage-recently-modified` | homepage-recently-modified |
| READ |  | GET | `/po/vendor/members/po-mgmt/dashboard` | po-dashboard |
| READ |  | GET | `/po/vendor/members/po-mgmt/managepos` | refererManagePOs |
| READ |  | GET | `/retail-analytics/dashboard/sales` | refererDashboard |
| READ_POST |  | POST | `/api/retail-analytics/v1/get-report-data` | get-report-data |
| READ_POST |  | POST | `/api/retail-analytics/v1/list-report-download-workflows` | PathWorkflows |
| READ_POST |  | POST | `/po-api/vendor/members/po-mgmt/search/downloadVendorSearchFile` | PathPODownload |
| READ_POST |  | POST | `/po-api/vendor/members/po-mgmt/search/getVendorSearchFileStatus` | PathPOStatus |
| WRITE |  | POST | `/api/retail-analytics/v1/request-report-download` | PathGenerate |
| WRITE |  | POST | `/po-api/vendor/members/po-mgmt/search/generateVendorSearchFile-v3` | PathPOGenerate |

## Connections

- [[00-Amazon-Atlas]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]] · [[Amazon-Pages-and-Routes]] · [[Read-Only-Guardrails]]

