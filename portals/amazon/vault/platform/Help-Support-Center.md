---
title: Help & Support Center
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, platform, help-support-center]
status: studied
read_only: true
---

# Help & Support Center

**Portal:** Seller Central (3P) · **Section:** `platform/Help-Support-Center` · **Endpoints catalogued:** 107 (85 read-safe, 14 PROVEN live · 2 out-of-scope · 20 unknown/telemetry)

Seller University, Help Hub, the Hill/MELD support-case system, contact-us, forums, and the whole self-service help surface. Large route surface (help-content GETs) plus the bootstrap/feature/eligibility mons-api reads.

## What it looks like (live, this run)

![02 help hub support](../platform/sec-02-help-hub-support.png)

*Captured live from JIVO Mart's Seller Central session, platform/sec-02-help-hub-support.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /communities/seller-news/articles | 4 | READ |
| ✅ | GET | sellercentral.amazon.in · /help/hub/i18n/HelpHubKatalWebsite/en-IN.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /help/hub/i18n/HelpHubKatalWebsite/en-US.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /help/hub/mons-api/GetBootstrapData | 25 | READ |
| ✅ | GET | sellercentral.amazon.in · /help/hub/mons-api/GetFeatureStatus | 5 | READ |
| ✅ | GET | sellercentral.amazon.in · /help/hub/mons-api/GetMeldEligibility | 1 | READ |
| ✅ | GET | sellercentral.amazon.in · /hill/hillservice/mons-api/GetBootstrapConfig | 19 | READ |
| ✅ | GET | sellercentral.amazon.in · /hill/hillservice/mons-api/GetSpecialistSupportIngressEligibility | 3 | READ |
| ✅ | GET | sellercentral.amazon.in · /hill/website/i18n/HillWebsite/en-IN.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /hill/website/i18n/HillWebsite/en-US.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /hill/website/i18n/HillWebsiteCaseLobby/en-IN.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /hill/website/i18n/HillWebsiteCaseLobby/en-US.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /roboapi/v1/sc/announcements | 1 | READ |
| ✅ | GET | sellercentral.amazon.in · /trim/json/favorites/sellerCentral | 12 | READ |
| · | GET | sellercentral.amazon.in · /cu/case-lobby | — | READ |
| · | GET | sellercentral.amazon.in · /cu/contact-us | — | READ |
| · | GET | sellercentral.amazon.in · /forums/index.jspa | — | READ |
| · | GET | sellercentral.amazon.in · /forums/t/ | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/ | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/customer/ | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/embed/{guid} | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/embed/{param} | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/external | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/external/ | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/external/help-content.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/external/help-folder.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/external/help-home.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/external/help-page.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/external/help.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/external/home | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/external/home.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/external/login-help.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/external/{guid}/ | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/help-content.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/help-folder.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/help-home.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/help-page.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/help-popup.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/help.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/home | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/home.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/login-help.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/{guid}/ | — | READ |
| · | GET | sellercentral.amazon.in · /gp/help/{helpGuid} | — | READ |
| · | GET | sellercentral.amazon.in · /help/center/inline/workflow | — | READ |
| · | GET | sellercentral.amazon.in · /help/da/{directAnswer} | — | READ |
| · | GET | sellercentral.amazon.in · /help/getting-started-guide | — | READ |
| · | GET | sellercentral.amazon.in · /help/getting-started-selling-faq | — | READ |
| · | GET | sellercentral.amazon.in · /help/home | — | READ |
| · | GET | sellercentral.amazon.in · /help/hub/ | — | READ |
| · | GET | sellercentral.amazon.in · /help/hub/debug | — | READ |
| · | GET | sellercentral.amazon.in · /help/hub/inline | — | READ |
| · | GET | sellercentral.amazon.in · /help/hub/reference/ | — | READ |
| · | GET | sellercentral.amazon.in · /help/hub/reference/external/ | — | READ |
| · | GET | sellercentral.amazon.in · /help/hub/reference/external/login-help | — | READ |
| · | GET | sellercentral.amazon.in · /help/hub/reference/external/{helpGuid} | — | READ |
| · | GET | sellercentral.amazon.in · /help/hub/reference/{helpGuid} | — | READ |
| · | GET | sellercentral.amazon.in · /help/hub/support | — | READ |
| · | GET | sellercentral.amazon.in · /help/inline/athena-get-direct-answer/embed | — | READ |
| · | GET | sellercentral.amazon.in · /help/manage-inventory-tool | — | READ |

_+25 more read rows in [[Amazon-Endpoints]]._

## Response shapes (full field lists, from live capture)

- **`/communities/seller-news/articles`** (4 fields): `newsArticles`, `newsArticles.effectiveDateTime`, `newsArticles.id`, `newsArticles.title`
- **`/help/hub/mons-api/GetBootstrapData`** (25 fields): `advertisingDomain`, `browseTreeEnabled`, `browseTreeVersion`, `countryCode`, `customerStatus`, `delegationContext`, `domain`, `enabled`, `encryptedMarketplaceId`, `helpRootNode`, `hmdSurveyId`, `internal`, `landingPageVersion`, `locale`, `recentlyViewedCustomerDirectedId`, `recentlyViewedMerchantDirectedId`, `retailDomain`, `sellerType`, `sellingPlan`, `siteName`, `soaFooterURL`, `soaHeaderURL`, `suspended`, `systemTime`, `uid`
- **`/help/hub/mons-api/GetFeatureStatus`** (5 fields): `features`, `features.describeIssue`, `features.describeIssue.enabled`, `features.describeIssue.enabledLocales`, `features.describeIssue.variant`
- **`/help/hub/mons-api/GetMeldEligibility`** (1 fields): `redirectUrl`
- **`/hill/hillservice/mons-api/GetBootstrapConfig`** (19 fields): `businessGroupData`, `defaultPhoneWidgetCountryCode`, `domain`, `gacdRegion`, `localeName`, `marketplaceName`, `phoneWidgetCallableCountries`, `privacyUrl`, `realm`, `site`, `uiFeatureStatusMap`, `uiFeatureStatusMap.UiFeatureIntegrationTest`, `uiFeatureStatusMap.UiFeatureIntegrationTest.enabled`, `uiFeatureStatusMap.UiFeatureIntegrationTest.weblabToTrigger`, `uiFeatureStatusMap.UiFeatureIntegrationTest.weblabToTrigger.weblabName`, `uiFeatureStatusMap.UiFeatureIntegrationTest.weblabToTrigger.weblabTreatment`, `uiFeatureStatusMap.UiFeatureIntegrationTest.weblabToTrigger.weblabType`, `vendorIssueTreeVariant`, `wafApiKey`
- **`/hill/hillservice/mons-api/GetSpecialistSupportIngressEligibility`** (3 fields): `eligibility`, `ineligibleReasons`, `program`

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| DELETE | sellercentral.amazon.in · /help/hub | WRITE | observed ['DELETE'] |
| ? | sellercentral.amazon.in · /help/modify-or-delete-a-product-listing | WRITE | write-verb constant/path token (G1: deny) |

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| ? | sellercentral.amazon.in · /gp/aw/help | UNKNOWN |
| ? | sellercentral.amazon.in · /gp/case-dashboard | UNKNOWN |
| ? | sellercentral.amazon.in · /gp/contact-amazon | UNKNOWN |
| ? | sellercentral.amazon.in · /gp/contact-us | UNKNOWN |
| ? | sellercentral.amazon.in · /gp/help | UNKNOWN |
| ? | sellercentral.amazon.in · /help/hub/mons-api/ | UNKNOWN |
| ? | sellercentral.amazon.in · /hz/m/help | UNKNOWN |
| ? | sellercentral.amazon.in · /hz/vendor/members/support/help/node/{helpGuid} | UNKNOWN |
| ? | sellercentral.amazon.in · /inline/sidebar | UNKNOWN |
| ? | sellercentral.amazon.in · /inline/sidebar/search | UNKNOWN |
| ? | sellercentral.amazon.in · /inline/sidebar/solution | UNKNOWN |
| ? | sellercentral.amazon.in · /inline/sidebar/support/describe | UNKNOWN |
| ? | sellercentral.amazon.in · /irc/widget | UNKNOWN |
| ? | sellercentral.amazon.in · /learn/widget-spl | UNKNOWN |
| GET | sellercentral.amazon.in · /mons/weblabs | NOISE |
| ? | sellercentral.amazon.in · /mons/weblabs/ | NOISE |
| GET | sellercentral.amazon.in · /mons/weblabs/merchant/treatment | NOISE |
| POST | sellercentral.amazon.in · /mons/weblabs/merchant/trigger | NOISE |
| GET | sellercentral.amazon.in · /mons/weblabs/vendor/treatment | NOISE |
| ? | sellercentral.amazon.in · /solution/{id} | UNKNOWN |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

