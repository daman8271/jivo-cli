---
title: Account Health & Performance
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, seller, account-health-performance]
status: studied
read_only: true
---

# Account Health & Performance

**Portal:** Seller Central (3P) · **Section:** `seller/Account-Health-Performance` · **Endpoints catalogued:** 39 (31 read-safe, 31 PROVEN live · 2 out-of-scope · 6 unknown/telemetry)

Account Health Dashboard (AHR), performance metrics (order defect rate, late shipment, cancellation, valid tracking), policy compliance, appeals, and Voice-of-the-Customer / product CX health (PCR). The richest live-proven read cluster in the study — 31 proven GETs including the risk banner, priority actions, and PCR KPIs.

## What it looks like (live, this run)

![07 account health](../seller/sec-07-account-health.png)
![08 perf order defects](../seller/sec-08-perf-order-defects.png)
![09 perf over time](../seller/sec-09-perf-over-time.png)
![10 perf customer service](../seller/sec-10-perf-customer-service.png)
![11 perf shipping](../seller/sec-11-perf-shipping.png)
![12 perf product policies](../seller/sec-12-perf-product-policies.png)
![13 voice of customer](../seller/sec-13-voice-of-customer.png)

*Captured live from JIVO Mart's Seller Central session, seller/sec-07-account-health.png; seller/sec-08-perf-order-defects.png; seller/sec-09-perf-over-time.png; seller/sec-10-perf-customer-service.png; seller/sec-11-perf-shipping.png; seller/sec-12-perf-product-policies.png; seller/sec-13-voice-of-customer.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /ahd/floatingWidget | — | READ |
| ✅ | GET | sellercentral.amazon.in · /ahd/issueTypeTags | — | READ |
| ✅ | GET | sellercentral.amazon.in · /ahd/priorityActions | — | READ |
| ✅ | GET | sellercentral.amazon.in · /appeal/appeals/csrf | 1 | READ |
| ✅ | GET | sellercentral.amazon.in · /pcrHealth/download | 2 | READ |
| ✅ | GET | sellercentral.amazon.in · /pcrHealth/pcrKpi | 5 | READ |
| ✅ | GET | sellercentral.amazon.in · /pcrHealth/pcrListingSummary | — | READ |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/account-health/en-IN.json | 59 | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/account-health/en-US.json | — | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/compliance-request/en-IN.json | 14 | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/compliance-request/en-US.json | 18 | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/contact-us/en-IN.json | 5 | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/contact-us/en-US.json | 43 | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/dominion-dashboard/en-IN.json | — | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/dominion-dashboard/en-US.json | — | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/policy-warning/en-IN.json | — | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/policy-warning/en-US.json | — | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/product-policies/en-IN.json | — | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/product-policies/en-US.json | — | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/reactivate-account/en-IN.json | 33 | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/reactivate-account/en-US.json | — | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/shared-strings/en-IN.json | — | READ_FILE |
| ✅ | GET | d3re0qkvcj2drt.cloudfront.net · /performance/account/health/i18n/shared-strings/en-US.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /performance/api/getriskbanner/ | 60 | READ |
| ✅ | GET | sellercentral.amazon.in · /performance/api/summary | — | READ |
| ✅ | GET | sellercentral.amazon.in · /performance/widget/translations/i18n/translation-en.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /performance/widget/translations/i18n/translation.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /voc-katal/i18n/en-IN.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /voc-katal/i18n/en-US.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | d84t02egg0ytc.cloudfront.net · /voc-katal/i18n/translation-en.{hash}.json | — | READ_FILE |
| ✅ | GET | d84t02egg0ytc.cloudfront.net · /voc-katal/i18n/translation.{hash}.json | — | READ_FILE |

## Response shapes (full field lists, from live capture)

- **`/appeal/appeals/csrf`** (1 fields): `encryptionProfile`
- **`/pcrHealth/download`** (2 fields): `records`, `status`
- **`/pcrHealth/pcrKpi`** (5 fields): `excellentCount`, `fairCount`, `goodCount`, `poorCount`, `veryPoorCount`
- **`/performance/account/health/i18n/account-health/en-IN.json`** (59 fields): `AHD_NEW_STACKED_ENFORCEMENT`, `SPD_HMD_LEAVE_FEEDBACK`, `ahd_pp_table_header_available_actions`, `copy_of_sp_health_reserve_dialog_footer_ok_button`, `sp_health_inaccurate_pricing`, `sp_health_shipment_count_non_exempt`, `sp_health_shipment_count_non_exempt_na`, `sp_health_shipped_with_valid_tracking`, `sp_health_shipped_with_valid_tracking_na`, `sp_vtr_list_item_1`, `sp_vtr_list_item_2`, `sp_vtr_list_item_3`, `sp_vtr_list_item_4`, `sp_vtr_non_exampt_description`, `sp_vtr_non_exempted_shipments`, `sp_vtr_tab_categories_below_target`, `sp_vtr_tab_categories_below_target_one`, `spd_generic_error_heading`, `spd_generic_error_msg`, `spd_generic_not_applicable_info_heading`, `spd_generic_not_applicable_info_msg`, `spd_health_amazon_fulfilled_metrics_caption`, `spd_health_atoz_guarantee_claims_caption`, `spd_health_cancellation_rate_caption`, `spd_health_cancellation_rate_subtitle`, `spd_health_chargeback_claims_caption`, `spd_health_customer_satisfaction_information_label`, `spd_health_dashboard_title`, `spd_health_fulfilled_by_seller_amazon`, `spd_health_intellectual_property_customer_complaints`, `spd_health_late_shipment_rate_caption`, `spd_health_late_shipment_rate_subtitle`, `spd_health_listing_policy_customer_complaints`, `spd_health_nav_eligibilities`, `spd_health_nav_orders_with_defects`, `spd_health_nav_performance_over_time`, `spd_health_nav_reports`, `spd_health_negative_feedback_caption`, `spd_health_not_available`, `spd_health_number_days` …
- **`/performance/account/health/i18n/compliance-request/en-IN.json`** (14 fields): `Documentation-requests`, `ahd_cr_information_requested`, `ahd_cr_intro_paragraph`, `ahd_cr_no_requests_alert_description`, `ahd_cr_provide_information`, `ahd_cr_seller_forum_with_link`, `ahd_gating_error_code_pq_por_enf`, `ahd_gating_error_code_pq_transp_enf`, `ahd_product_policy_compliance_documentation_requested`, `ahd_product_policy_compliance_page_sub_title`, `ahd_warning_compliance_information_requested`, `compliance_documentation_requests`, `due-date`, `provide-documentation`
- **`/performance/account/health/i18n/compliance-request/en-US.json`** (18 fields): `Documentation-requests`, `ahd_cr_bulk_appeal_link`, `ahd_cr_information_requested`, `ahd_cr_intro_paragraph`, `ahd_cr_no_requests_alert_description`, `ahd_cr_no_requests_alert_header`, `ahd_cr_pars_us_supplement_requests`, `ahd_cr_provide_information`, `ahd_cr_seller_forum_with_link`, `ahd_gating_error_code_pq_por_enf`, `ahd_gating_error_code_pq_transp_enf`, `ahd_product_policy_compliance_documentation_requested`, `ahd_product_policy_compliance_page_sub_title`, `ahd_warning_compliance_information_requested`, `ahdpars_spx_myc_dashboard_mainHeader1`, `compliance_documentation_requests`, `due-date`, `provide-documentation`

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| POST | sellercentral.amazon.in · /performance/api/postBizMetricsWithMap/ | READ_POST | app-issued POST read (GraphQL/RPC) — G0 forbids POST, gate k |
| ? | sellercentral.amazon.in · /sq/approvalrequest | WRITE | write-verb constant/path token (G1: deny) |

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| ? | sellercentral.amazon.in · /performance/detail/customer-service | UNKNOWN |
| ? | sellercentral.amazon.in · /performance/detail/product-policies | UNKNOWN |
| ? | sellercentral.amazon.in · /performance/detail/shipping | UNKNOWN |
| ? | sellercentral.amazon.in · /performance/report/order-defects | UNKNOWN |
| ? | sellercentral.amazon.in · /performance/report/performance-over-time | UNKNOWN |
| ? | sellercentral.amazon.in · /voice-of-the-customer | UNKNOWN |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

