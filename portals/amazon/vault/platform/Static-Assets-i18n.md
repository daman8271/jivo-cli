---
title: Static Assets & i18n
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: CDN
tags: [amazon, platform, static-assets-i18n]
status: studied
read_only: true
---

# Static Assets & i18n

**Portal:** CDN · **Section:** `platform/Static-Assets-i18n` · **Endpoints catalogued:** 33 (32 read-safe, 32 PROVEN live · 0 out-of-scope · 1 unknown/telemetry)

The public CDN layer — webpack bundles, chunk manifests, and per-locale i18n/translation JSON for every micro-frontend. No auth, no business data; catalogued so the corpus is fully accounted for and the app's localisation coverage is visible.

> No live screenshot — this is Vendor Central (session expired, see [[Auth-and-Access]]) or a non-visual asset layer. Endpoints below are documented from the Phase-0 seed evidence and the static corpus.

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | d1hw4uzgiurk5n.cloudfront.net · / | — | READ |
| ✅ | GET | d3h0qy3grrnlx3.cloudfront.net · / | — | READ |
| ✅ | GET | dp0zvwwqb1q92.cloudfront.net · /AnyUICore/sdk.js | — | READ_FILE |
| ✅ | GET | dp0zvwwqb1q92.cloudfront.net · /Manifest/components.json | — | READ |
| ✅ | GET | d3ksbe4ctckde3.cloudfront.net · /en-IN.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | d3ttb92cjixe5s.cloudfront.net · /en-IN.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | d3ksbe4ctckde3.cloudfront.net · /en-US.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | d3ttb92cjixe5s.cloudfront.net · /en-US.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | static-assets.prod-dub.sellingpartnerho.homepages.selling-partners.amazon.dev · /homepage/assets/translations/translation-en.{hash}.json | — | READ_FILE |
| ✅ | GET | static-assets.prod-dub.sellingpartnerho.homepages.selling-partners.amazon.dev · /homepage/assets/translations/translation.{hash}.json | — | READ_FILE |
| ✅ | GET | dmsjnm3xe0ebz.cloudfront.net · /i18n/ImageCompliance/en-IN.{hash}.i18next.json | 60 | READ_FILE |
| ✅ | GET | dmsjnm3xe0ebz.cloudfront.net · /i18n/ImageCompliance/en-US.{hash}.i18next.json | 60 | READ_FILE |
| ✅ | GET | dmsjnm3xe0ebz.cloudfront.net · /i18n/QuickListContent/en-IN.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | dmsjnm3xe0ebz.cloudfront.net · /i18n/QuickListContent/en-US.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | d3ttb92cjixe5s.cloudfront.net · /i18n/en-IN.json | — | READ_FILE |
| ✅ | GET | d2pihuraj6wacp.cloudfront.net · /i18n/en-IN.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | d3c9w1p5457qe7.cloudfront.net · /i18n/en-IN.{hash}.i18next.json | 1 | READ_FILE |
| ✅ | GET | d3ttb92cjixe5s.cloudfront.net · /i18n/en-US.json | — | READ_FILE |
| ✅ | GET | d2pihuraj6wacp.cloudfront.net · /i18n/en-US.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | d3c9w1p5457qe7.cloudfront.net · /i18n/en-US.{hash}.i18next.json | 23 | READ_FILE |
| ✅ | GET | d1pp2iw517bkb8.cloudfront.net · /i18n/translation-en.json | — | READ_FILE |
| ✅ | GET | dy8z3jvmvymcp.cloudfront.net · /i18n/translation-en.json | — | READ_FILE |
| ✅ | GET | d3c9w1p5457qe7.cloudfront.net · /i18n/translation-en.{hash}.json | — | READ_FILE |
| ✅ | GET | d1pp2iw517bkb8.cloudfront.net · /i18n/translation.json | — | READ_FILE |
| ✅ | GET | dy8z3jvmvymcp.cloudfront.net · /i18n/translation.json | — | READ_FILE |
| ✅ | GET | d3c9w1p5457qe7.cloudfront.net · /i18n/translation.{hash}.json | — | READ_FILE |
| ✅ | GET | d3rhl38hdptmva.cloudfront.net · /i18n/translations/translation-en.{hash}.json | — | READ_FILE |
| ✅ | GET | d3rhl38hdptmva.cloudfront.net · /i18n/translations/translation.{hash}.json | — | READ_FILE |
| ✅ | GET | d1uznvntk80v7s.cloudfront.net · /metrics.{hash}.js | — | READ_FILE |
| ✅ | GET | d1uznvntk80v7s.cloudfront.net · /metrics.{hash}.js.map | — | READ_FILE |
| ✅ | GET | d7xm6m3peqvfj.cloudfront.net · /static/en-IN.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | d7xm6m3peqvfj.cloudfront.net · /static/en-US.{hash}.i18next.json | — | READ_FILE |

## Response shapes (full field lists, from live capture)

- **`/i18n/ImageCompliance/en-IN.{hash}.i18next.json`** (60 fields): `accept`, `decline`, `defectCorrection_accept`, `defectCorrection_aiOptimizedImage`, `defectCorrection_disclaimer`, `defectCorrection_errorMessage`, `defectCorrection_issuesText`, `defectCorrection_nwb`, `defectCorrection_nwbError`, `defectCorrection_nwbRemoval`, `defectCorrection_optimizationText`, `defectCorrection_originalImage`, `defectCorrection_pinchZoomInstruction`, `defectCorrection_placeholder`, `defectCorrection_productGuidelines`, `defectCorrection_productImage`, `defectCorrection_resetZoom`, `defectCorrection_save`, `defectCorrection_showAiOptimizedImage`, `defectCorrection_showOriginal`, `defectCorrection_tlgw`, `defectCorrection_tlgwError`, `defectCorrection_tlgwRemoval`, `defectCorrection_uploadNewImage`, `defectCorrection_zoomIn`, `defectCorrection_zoomOut`, `defectDetection_fixImage`, `defectDetection_fixMyImage`, `defectDetection_issueDetected`, `defectDetection_listingSuppressionRisk`, `defectDetection_mainImageLabel`, `dimensions_minHeight`, `dimensions_minWidth`, `examplePhoto_title`, `imageCompliance_disclaimer`, `imageCompliance_disclaimerTitle`, `imageGuidelines_done`, `imageSpecs_bestFormat`, `imageSpecs_maximumSize`, `imageSpecs_minimumSize` …
- **`/i18n/ImageCompliance/en-US.{hash}.i18next.json`** (60 fields): `accept`, `decline`, `defectCorrection_accept`, `defectCorrection_aiOptimizedImage`, `defectCorrection_disclaimer`, `defectCorrection_errorMessage`, `defectCorrection_issuesText`, `defectCorrection_nwb`, `defectCorrection_nwbError`, `defectCorrection_nwbRemoval`, `defectCorrection_optimizationText`, `defectCorrection_originalImage`, `defectCorrection_pinchZoomInstruction`, `defectCorrection_placeholder`, `defectCorrection_productGuidelines`, `defectCorrection_productImage`, `defectCorrection_resetZoom`, `defectCorrection_save`, `defectCorrection_showAiOptimizedImage`, `defectCorrection_showOriginal`, `defectCorrection_tlgw`, `defectCorrection_tlgwError`, `defectCorrection_tlgwRemoval`, `defectCorrection_uploadNewImage`, `defectCorrection_zoomIn`, `defectCorrection_zoomOut`, `defectDetection_fixImage`, `defectDetection_fixMyImage`, `defectDetection_issueDetected`, `defectDetection_listingSuppressionRisk`, `defectDetection_mainImageLabel`, `dimensions_minHeight`, `dimensions_minWidth`, `examplePhoto_title`, `imageCompliance_disclaimer`, `imageCompliance_disclaimerTitle`, `imageGuidelines_done`, `imageSpecs_bestFormat`, `imageSpecs_maximumSize`, `imageSpecs_minimumSize` …
- **`/i18n/en-IN.{hash}.i18next.json`** (1 fields): `katal_hmd_send_feedback`
- **`/i18n/en-US.{hash}.i18next.json`** (23 fields): `addTab_label`, `alert_variant_demo_description`, `alert_variant_explanation_text`, `components_containing_html_text`, `continue_button_label`, `custom_elements_text`, `demo_complex_header_text`, `demo_components_header_text`, `demo_javascript_header_text`, `design_approved_text`, `documentation_label`, `greeting_description`, `greeting_description_mons_app`, `greeting_header`, `katal_hmd_send_feedback`, `primary_button_label`, `sample_app_page_title_text`, `secondary_button_label`, `tab_demo_generated_text`, `tab_demo_name`, `tab_demo_selected_name`, `tab_demo_selected_text`, `tab_demo_text`

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

_None catalogued in this section._

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| GET | m.media-amazon.com · /images/G/01/csm/showads.v2.js | NOISE |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

