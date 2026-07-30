---
title: Product Classification & Search
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, seller, product-classification]
status: studied
read_only: true
---

# Product Classification & Search

**Portal:** Seller Central (3P) · **Section:** `seller/Product-Classification` · **Endpoints catalogued:** 19 (6 read-safe, 5 PROVEN live · 3 out-of-scope · 10 unknown/telemetry)

Product-type / browse-node classification (productclassify) and catalog product search (productsearch). Reads: classification context, favourites, browse nodes, PT-search, value suggestions, image-compliance.

## What it looks like (live, this run)

![19 product classify](../seller/sec-19-product-classify.png)
![20 product search](../seller/sec-20-product-search.png)

*Captured live from JIVO Mart's Seller Central session, seller/sec-19-product-classify.png; seller/sec-20-product-search.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /productclassify/api/browse | — | READ |
| ✅ | GET | sellercentral.amazon.in · /productclassify/api/context | 12 | READ |
| ✅ | GET | sellercentral.amazon.in · /productclassify/api/favorites | 16 | READ |
| ✅ | GET | sellercentral.amazon.in · /productclassify/i18n/en-IN.{hash}.i18next.json | 52 | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /productclassify/i18n/en-US.{hash}.i18next.json | 52 | READ_FILE |
| · | GET | sellercentral.amazon.in · /productclassify/index.html | — | READ |

## Response shapes (full field lists, from live capture)

- **`/productclassify/api/context`** (12 fields): `domain`, `encryptedMarketplaceId`, `encryptedMerchantId`, `hmdSurveyId`, `isSearchSupported`, `realm`, `searchSupported`, `siteType`, `weblabTreatments`, `weblabTreatments.CONTENT_LANGUAGE_SELECTION_327205`, `weblabTreatments.HEADER_LANGUAGE_SELECTION_313515`, `weblabTreatments.ONE_BY_ONE_PREFERRED_LANGUAGE_338345`
- **`/productclassify/api/favorites`** (16 fields): `browseElements`, `browseElements.browsePath`, `browseElements.confidence`, `browseElements.displayPath`, `browseElements.gatingReason`, `browseElements.handmade`, `browseElements.id`, `browseElements.isSellable`, `browseElements.itemType`, `browseElements.label`, `browseElements.level`, `browseElements.metadataContext`, `browseElements.productType`, `browseElements.recommendedBrowseNode`, `debugInfo`, `missingBrowseNodePaths`
- **`/productclassify/i18n/en-IN.{hash}.i18next.json`** (52 fields): `Category_picker_browse_node_product_type_label`, `category_picker_product_type_help_content`, `generic_learn_more`, `picker_add_products_upload`, `picker_browse_default_breadcrumb`, `picker_browse_title`, `picker_change_categories`, `picker_check_product_exists`, `picker_date`, `picker_discard`, `picker_dont_see_category`, `picker_empty_favorites`, `picker_error`, `picker_error_message`, `picker_favorites`, `picker_favorites_add_error`, `picker_favorites_empty`, `picker_favorites_loading_error`, `picker_favorites_refresh_msg`, `picker_favorites_removal_msg`, `picker_favorites_removal_msg_hdr`, `picker_favorites_remove_error`, `picker_favorites_try_again`, `picker_found_listing`, `picker_handmade_browse_default_breadcrumb`, `picker_header_description`, `picker_header_title`, `picker_mobile_handmade`, `picker_not_listing_handmade`, `picker_ok`, `picker_product_category`, `picker_provide_feedback`, `picker_restore`, `picker_retry`, `picker_search_matching_categories_plural_title`, `picker_search_matching_categories_singular_title`, `picker_search_no_results_header`, `picker_search_no_results_message`, `picker_search_placeholder`, `picker_search_title` …
- **`/productclassify/i18n/en-US.{hash}.i18next.json`** (52 fields): `Category_picker_browse_node_product_type_label`, `category_picker_product_type_help_content`, `generic_learn_more`, `picker_add_products_upload`, `picker_browse_default_breadcrumb`, `picker_browse_title`, `picker_change_categories`, `picker_check_product_exists`, `picker_date`, `picker_discard`, `picker_dont_see_category`, `picker_empty_favorites`, `picker_error`, `picker_error_message`, `picker_favorites`, `picker_favorites_add_error`, `picker_favorites_empty`, `picker_favorites_loading_error`, `picker_favorites_refresh_msg`, `picker_favorites_removal_msg`, `picker_favorites_removal_msg_hdr`, `picker_favorites_remove_error`, `picker_favorites_try_again`, `picker_found_listing`, `picker_handmade_browse_default_breadcrumb`, `picker_header_description`, `picker_header_title`, `picker_mobile_handmade`, `picker_not_listing_handmade`, `picker_ok`, `picker_product_category`, `picker_provide_feedback`, `picker_restore`, `picker_retry`, `picker_search_matching_categories_plural_title`, `picker_search_matching_categories_singular_title`, `picker_search_no_results_header`, `picker_search_no_results_message`, `picker_search_placeholder`, `picker_search_title` …

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| ? | sellercentral.amazon.in · /handmade/apply | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /productclassify/edit | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /productclassify/edit/handmade | WRITE | write-verb constant/path token (G1: deny) |

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| ? | sellercentral.amazon.in · /certification/1x1certification | UNKNOWN |
| ? | sellercentral.amazon.in · /handmade/productclassify | UNKNOWN |
| ? | sellercentral.amazon.in · /hz/manage-your-category/ | UNKNOWN |
| ? | sellercentral.amazon.in · /hz/productclassify | UNKNOWN |
| ? | sellercentral.amazon.in · /product-search | UNKNOWN |
| ? | sellercentral.amazon.in · /productclassify/api | UNKNOWN |
| ? | sellercentral.amazon.in · /productclassify/api/browse-nodes | UNKNOWN |
| ? | sellercentral.amazon.in · /productclassify/api/pt-search | UNKNOWN |
| ? | sellercentral.amazon.in · /productsearch/v2/search | UNKNOWN |
| ? | sellercentral.amazon.in · /productsearch/valuesuggestions | UNKNOWN |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

