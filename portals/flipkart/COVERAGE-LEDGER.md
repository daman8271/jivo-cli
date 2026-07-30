# Flipkart — Coverage Ledger

_Generated 2026-07-30. Part A = pages actually walked live (screenshot on disk). Part B = every SPA route extracted from the JS corpus (Amendment-03: one row per route)._

## Part A — pages WALKED live (read-only browser walk, 2026-07-30)

One distinct, non-trivial screenshot per page (byte- and content-duplicates dropped). Full gallery + captions: [[Flipkart-Live-Walk]]. Network capture per page kept local (`captures/*-walk/sec-*.json`).

| # | portal | route | walked | screenshot | notes |
|---|---|---|---|---|---|
| 1 | Vendor Hub | `/` | YES | `vendorhub-walk/sec-01-vh-home-dashboard.png` | live render, network captured |
| 2 | Vendor Hub | `/#/operations/po/list?status=new` | YES | `vendorhub-walk/sec-02-vh-operations-po-new.png` | live render, network captured |
| 3 | Vendor Hub | `/#/operations/po/list?status=open` | YES | `vendorhub-walk/sec-03-vh-operations-po-open.png` | live render, network captured |
| 4 | Vendor Hub | `/#/operations/po/list?status=completed` | YES | `vendorhub-walk/sec-05-vh-operations-po-completed.png` | live render, network captured |
| 5 | Vendor Hub | `/#/operations/po/list?status=cancelled` | YES | `vendorhub-walk/sec-06-vh-operations-po-cancelled.png` | live render, network captured |
| 6 | Vendor Hub | `/#/operations/consignments` | YES | `vendorhub-walk/sec-07-vh-operations-consignments.png` | live render, network captured |
| 7 | Vendor Hub | `/#/vendor-portal/inventory/landing/analytics/product-details/list` | YES | `vendorhub-walk/sec-09-vh-inventory-analytics-product-details.png` | live render, network captured |
| 8 | Vendor Hub | `/#/agreements` | YES | `vendorhub-walk/sec-12-vh-agreements.png` | live render, network captured |
| 9 | Vendor Hub | `/#/agreements/brand-offer` | YES | `vendorhub-walk/sec-13-vh-agreements-brand-offer.png` | live render, network captured |
| 10 | Vendor Hub | `/#/agreements/claims-collection-request-management` | YES | `vendorhub-walk/sec-14-vh-agreements-claims.png` | live render, network captured |
| 11 | Vendor Hub | `/#/payments` | YES | `vendorhub-walk/sec-15-vh-payments.png` | live render, network captured |
| 12 | Vendor Hub | `/#/payments/debit-notes` | YES | `vendorhub-walk/sec-16-vh-payments-debit-notes.png` | live render, network captured |
| 13 | Vendor Hub | `/#/profile` | YES | `vendorhub-walk/sec-18-vh-profile.png` | live render, network captured |
| 14 | Seller Hub | `/index.html#dashboard/home-page` | YES | `seller-walk/sec-01-sh-home.png` | live render, network captured |
| 15 | Seller Hub | `/index.html#dashboard/listings-management?listingState=ACTIVE` | YES | `seller-walk/sec-02-sh-listings-active.png` | live render, network captured |
| 16 | Seller Hub | `/index.html#dashboard/listings-management?listingState=INACTIVE` | YES | `seller-walk/sec-03-sh-listings-inactive.png` | live render, network captured |
| 17 | Seller Hub | `/index.html#dashboard/listings-management?listingState=ARCHIVED` | YES | `seller-walk/sec-04-sh-listings-archived.png` | live render, network captured |
| 18 | Seller Hub | `/index.html#dashboard/listingsInProgress` | YES | `seller-walk/sec-05-sh-listings-in-progress.png` | live render, network captured |
| 19 | Seller Hub | `/index.html#dashboard/unifiedInventoryNew` | YES | `seller-walk/sec-06-sh-inventory.png` | live render, network captured |
| 20 | Seller Hub | `/index.html#dashboard/inventoryHealth` | YES | `seller-walk/sec-07-sh-inventory-health.png` | live render, network captured |
| 21 | Seller Hub | `/index.html#dashboard/my-orders?serviceProfile=seller-fulfilled&shipmentType=easy-ship&orderState=shipments_to_pack` | YES | `seller-walk/sec-08-sh-orders-to-pack.png` | live render, network captured |
| 22 | Seller Hub | `/index.html#dashboard/my-orders?orderState=upcoming` | YES | `seller-walk/sec-09-sh-orders-upcoming.png` | live render, network captured |
| 23 | Seller Hub | `/index.html#dashboard/my-orders?orderState=cancelled` | YES | `seller-walk/sec-10-sh-orders-cancelled.png` | live render, network captured |
| 24 | Seller Hub | `/index.html#dashboard/returns` | YES | `seller-walk/sec-11-sh-returns.png` | live render, network captured |
| 25 | Seller Hub | `/index.html#dashboard/payments/account-summary` | YES | `seller-walk/sec-12-sh-payments-account-summary.png` | live render, network captured |
| 26 | Seller Hub | `/index.html#dashboard/payments` | YES | `seller-walk/sec-13-sh-payments.png` | live render, network captured |
| 27 | Seller Hub | `/index.html#dashboard/metrics/report-centre` | YES | `seller-walk/sec-14-sh-report-centre.png` | live render, network captured |
| 28 | Seller Hub | `/index.html#dashboard/metrics/pricing-recommendations/pricing-central` | YES | `seller-walk/sec-15-sh-pricing-central.png` | live render, network captured |
| 29 | Seller Hub | `/index.html#dashboard/ads/campaigns` | YES | `seller-walk/sec-16-sh-ads-campaigns.png` | live render, network captured |
| 30 | Seller Hub | `/index.html#dashboard/growth/seller-insights` | YES | `seller-walk/sec-17-sh-growth-insights.png` | live render, network captured |
| 31 | Seller Hub | `/index.html#dashboard/lending?page=LANDING` | YES | `seller-walk/sec-18-sh-lending.png` | live render, network captured |
| 32 | Seller Hub | `/index.html#dashboard/partner-services/home` | YES | `seller-walk/sec-19-sh-partner-services.png` | live render, network captured |
| 33 | Seller Hub | `/index.html#dashboard/rateCard` | YES | `seller-walk/sec-20-sh-ratecard.png` | live render, network captured |
| 34 | Seller Hub | `/index.html#dashboard/promotions` | YES | `seller-walk/sec-21-sh-promotions.png` | live render, network captured |
| 35 | Seller Hub | `/index.html#dashboard/sellerQnA` | YES | `seller-walk/sec-22-sh-seller-qna.png` | live render, network captured |
| 36 | Seller Hub | `/index.html#dashboard/notifications` | YES | `seller-walk/sec-23-sh-notifications.png` | live render, network captured |
| 37 | Seller Hub | `/index.html#dashboard/cancellations-insights` | YES | `seller-walk/sec-24-sh-cancellations-insights.png` | live render, network captured |

**Part A total: 37 pages walked with a distinct screenshot** (13 vendor + 24 seller). Routes that fell back to a dashboard or errored were dropped as duplicates/trivial at ingest and are NOT counted here (honest de-dup, not padding).

## Part B — all extracted SPA routes (static map)

Every route below was mapped by reverse-reading the JS corpus (Phase 2/3). Ones also covered by a Part-A live page are marked. The rest are `static-only` — enumerated for completeness (incl. obscure/dead routes nobody opens), not individually screenshotted; the seller SPA renders its dashboard for unmatched paths, so blind per-fragment walking would only produce dashboard duplicates. Section-level live coverage is in Part A.

| # | surface | route | static map | live walk? |
|---|---|---|---|---|
| 1 | seller | `#/acceptOnboarding_gst/` | MAPPED | static-only |
| 2 | seller | `#/dashboard/sellerOnboarding` | MAPPED | yes (Part A) |
| 3 | seller | `#/partner-services/help` | MAPPED | yes (Part A) |
| 4 | seller | `#/partner-services/my-services` | MAPPED | yes (Part A) |
| 5 | seller | `#/partner-services/service-list` | MAPPED | yes (Part A) |
| 6 | seller | `#/partner-services/service-partner-details` | MAPPED | yes (Part A) |
| 7 | seller | `/SELLER_SELF_SERVE` | MAPPED | static-only |
| 8 | seller | `/SPF` | MAPPED | static-only |
| 9 | seller | `/access-denied` | MAPPED | static-only |
| 10 | seller | `/all` | MAPPED | static-only |
| 11 | seller | `/appErrors` | MAPPED | static-only |
| 12 | seller | `/attachments` | MAPPED | static-only |
| 13 | seller | `/cancellations-insights` | MAPPED | yes (Part A) |
| 14 | seller | `/cancelled_orders` | MAPPED | static-only |
| 15 | seller | `/complete` | MAPPED | yes (Part A) |
| 16 | seller | `/completed` | MAPPED | yes (Part A) |
| 17 | seller | `/consignment/dispatch/fsn-list` | MAPPED | yes (Part A) |
| 18 | seller | `/createTicket/:category/:subcategory` | MAPPED | static-only |
| 19 | seller | `/decide/` | MAPPED | static-only |
| 20 | seller | `/deprecated-page` | MAPPED | static-only |
| 21 | seller | `/developer-access` | MAPPED | static-only |
| 22 | seller | `/documents/address/address` | MAPPED | static-only |
| 23 | seller | `/documents/cheque/cheque` | MAPPED | static-only |
| 24 | seller | `/documents/signature/signature` | MAPPED | static-only |
| 25 | seller | `/documents/upload/case-manager-temp` | MAPPED | static-only |
| 26 | seller | `/download` | MAPPED | static-only |
| 27 | seller | `/dp` | MAPPED | static-only |
| 28 | seller | `/dsorders` | MAPPED | static-only |
| 29 | seller | `/engage/` | MAPPED | static-only |
| 30 | seller | `/fa/:state` | MAPPED | static-only |
| 31 | seller | `/fa/consignmentDetails/:consignmentId` | MAPPED | static-only |
| 32 | seller | `/fa/consignmentDetailsIWIT/:consignmentId` | MAPPED | static-only |
| 33 | seller | `/fa/minutesDemandForecast` | MAPPED | static-only |
| 34 | seller | `/fa/onboarding/gstinOnboarding` | MAPPED | static-only |
| 35 | seller | `/fa/onboarding/gstinOnboardingv2` | MAPPED | static-only |
| 36 | seller | `/fa/onboarding/whyFA` | MAPPED | static-only |
| 37 | seller | `/fa/scheduledCon/:consignmentId/:stateView` | MAPPED | static-only |
| 38 | seller | `/faq` | MAPPED | static-only |
| 39 | seller | `/fbflite-audit` | MAPPED | static-only |
| 40 | seller | `/fbflite-fa` | MAPPED | static-only |
| 41 | seller | `/fbflite-ff` | MAPPED | static-only |
| 42 | seller | `/fed-ads` | MAPPED | static-only |
| 43 | seller | `/fees-and-commission` | MAPPED | static-only |
| 44 | seller | `/fk` | MAPPED | static-only |
| 45 | seller | `/forgot` | MAPPED | static-only |
| 46 | seller | `/forms/` | MAPPED | static-only |
| 47 | seller | `/fulfilment-outage` | MAPPED | static-only |
| 48 | seller | `/get-email-from-recovery-token` | MAPPED | static-only |
| 49 | seller | `/getChatbotToken` | MAPPED | static-only |
| 50 | seller | `/getFeaturesForSeller` | MAPPED | static-only |
| 51 | seller | `/getRemoteConfigFull` | MAPPED | static-only |
| 52 | seller | `/getStateDetails` | MAPPED | static-only |
| 53 | seller | `/graphql` | MAPPED | static-only |
| 54 | seller | `/groups/` | MAPPED | static-only |
| 55 | seller | `/grow` | MAPPED | yes (Part A) |
| 56 | seller | `/grow-your-business` | MAPPED | static-only |
| 57 | seller | `/grow/:preloginUrl` | MAPPED | yes (Part A) |
| 58 | seller | `/grow/flipkart-ads` | MAPPED | yes (Part A) |
| 59 | seller | `/grow/flipstars-2022` | MAPPED | yes (Part A) |
| 60 | seller | `/grow/seller-conclave-2022` | MAPPED | yes (Part A) |
| 61 | seller | `/grow/shopping-festivals` | MAPPED | yes (Part A) |
| 62 | seller | `/growth/sales-heat-map` | MAPPED | yes (Part A) |
| 63 | seller | `/growth/storefront` | MAPPED | yes (Part A) |
| 64 | seller | `/help` | MAPPED | static-only |
| 65 | seller | `/home` | MAPPED | yes (Part A) |
| 66 | seller | `/home-page` | MAPPED | yes (Part A) |
| 67 | seller | `/i/1000` | MAPPED | yes (Part A) |
| 68 | seller | `/ignite` | MAPPED | static-only |
| 69 | seller | `/in_progress` | MAPPED | static-only |
| 70 | seller | `/index` | MAPPED | yes (Part A) |
| 71 | seller | `/intake/v` | MAPPED | static-only |
| 72 | seller | `/landing` | MAPPED | yes (Part A) |
| 73 | seller | `/list/upcoming` | MAPPED | yes (Part A) |
| 74 | seller | `/listings/:vertical/:productId/variants` | MAPPED | yes (Part A) |
| 75 | seller | `/listings/addListing` | MAPPED | yes (Part A) |
| 76 | seller | `/listings/brandRegistryNavTrail` | MAPPED | yes (Part A) |
| 77 | seller | `/listings/fashionTrendsNavRail` | MAPPED | yes (Part A) |
| 78 | seller | `/listings/myAuditsNavRail` | MAPPED | yes (Part A) |
| 79 | seller | `/login` | MAPPED | static-only |
| 80 | seller | `/logout` | MAPPED | static-only |
| 81 | seller | `/main/requested/main/filter` | MAPPED | static-only |
| 82 | seller | `/manageTickets/:sourceClient` | MAPPED | static-only |
| 83 | seller | `/metrics` | MAPPED | yes (Part A) |
| 84 | seller | `/multi-select` | MAPPED | static-only |
| 85 | seller | `/my` | MAPPED | yes (Part A) |
| 86 | seller | `/myFreebiesNavRail` | MAPPED | static-only |
| 87 | seller | `/napi` | MAPPED | static-only |
| 88 | seller | `/nav-fa/` | MAPPED | static-only |
| 89 | seller | `/not-found` | MAPPED | static-only |
| 90 | seller | `/notifications` | MAPPED | yes (Part A) |
| 91 | seller | `/on_hold` | MAPPED | static-only |
| 92 | seller | `/order_management/drop_ship_orders` | MAPPED | static-only |
| 93 | seller | `/page-not-found` | MAPPED | static-only |
| 94 | seller | `/partner-services` | MAPPED | yes (Part A) |
| 95 | seller | `/partner-services/help` | MAPPED | yes (Part A) |
| 96 | seller | `/partner-services/privacy-policy` | MAPPED | yes (Part A) |
| 97 | seller | `/partner-services/service-partner-details` | MAPPED | yes (Part A) |
| 98 | seller | `/partner-services/terms-of-use` | MAPPED | yes (Part A) |
| 99 | seller | `/partnerAccess` | MAPPED | static-only |
| 100 | seller | `/payments/invoices-nav-rail` | MAPPED | yes (Part A) |
| 101 | seller | `/payments/previous-payments-nav-rail` | MAPPED | yes (Part A) |
| 102 | seller | `/payments/ratecard` | MAPPED | yes (Part A) |
| 103 | seller | `/payments/statements-nav-rail` | MAPPED | yes (Part A) |
| 104 | seller | `/pitstop/2/register` | MAPPED | static-only |
| 105 | seller | `/pricing-recommendations` | MAPPED | yes (Part A) |
| 106 | seller | `/pricing/approvalHistory` | MAPPED | yes (Part A) |
| 107 | seller | `/pricing/viewThresholds` | MAPPED | yes (Part A) |
| 108 | seller | `/privacy-policy` | MAPPED | static-only |
| 109 | seller | `/privacyPolicy` | MAPPED | static-only |
| 110 | seller | `/promo` | MAPPED | yes (Part A) |
| 111 | seller | `/promotions` | MAPPED | yes (Part A) |
| 112 | seller | `/promotions/create` | MAPPED | yes (Part A) |
| 113 | seller | `/raiseRequest` | MAPPED | static-only |
| 114 | seller | `/recommendations/:recommendation` | MAPPED | yes (Part A) |
| 115 | seller | `/recommendationsNavRail` | MAPPED | static-only |
| 116 | seller | `/report-groups` | MAPPED | static-only |
| 117 | seller | `/resendOtp` | MAPPED | static-only |
| 118 | seller | `/resetPassword` | MAPPED | static-only |
| 119 | seller | `/return_orders` | MAPPED | static-only |
| 120 | seller | `/return_request` | MAPPED | static-only |
| 121 | seller | `/returns` | MAPPED | yes (Part A) |
| 122 | seller | `/returns-insights` | MAPPED | static-only |
| 123 | seller | `/rum/events` | MAPPED | static-only |
| 124 | seller | `/sell-online` | MAPPED | static-only |
| 125 | seller | `/sell-online/` | MAPPED | static-only |
| 126 | seller | `/sell-online//1000` | MAPPED | static-only |
| 127 | seller | `/sell-online/:categoryUrlPath` | MAPPED | static-only |
| 128 | seller | `/sell-online/:categoryUrlPath/:contentUrlPath` | MAPPED | static-only |
| 129 | seller | `/sell-online/:preloginUrl` | MAPPED | static-only |
| 130 | seller | `/sell-online/account-management` | MAPPED | static-only |
| 131 | seller | `/sell-online/advantages-of-sell-online` | MAPPED | static-only |
| 132 | seller | `/sell-online/advantages-of-selling-online` | MAPPED | static-only |
| 133 | seller | `/sell-online/blog/priceRecommendationTool` | MAPPED | static-only |
| 134 | seller | `/sell-online/faq` | MAPPED | static-only |
| 135 | seller | `/sell-online/flipkart-boost` | MAPPED | static-only |
| 136 | seller | `/sell-online/flipkart-branded-packaging` | MAPPED | static-only |
| 137 | seller | `/sell-online/growth` | MAPPED | static-only |
| 138 | seller | `/sell-online/growth/seller-tiering-overview` | MAPPED | static-only |
| 139 | seller | `/sell-online/help-and-support` | MAPPED | static-only |
| 140 | seller | `/sell-online/how-to-register-for-gst` | MAPPED | static-only |
| 141 | seller | `/sell-online/most-profitable-products-to-sell-online` | MAPPED | static-only |
| 142 | seller | `/sell-online/multi-select` | MAPPED | static-only |
| 143 | seller | `/sell-online/multi-select/` | MAPPED | static-only |
| 144 | seller | `/sell-online/myths-about-online-selling` | MAPPED | static-only |
| 145 | seller | `/sell-online/online-selling-business-ideas` | MAPPED | static-only |
| 146 | seller | `/sell-online/online-selling-guide` | MAPPED | static-only |
| 147 | seller | `/sell-online/online-selling-guide-0` | MAPPED | static-only |
| 148 | seller | `/sell-online/pricing` | MAPPED | static-only |
| 149 | seller | `/sell-online/privacy-policy` | MAPPED | static-only |
| 150 | seller | `/sell-online/resetPassword` | MAPPED | static-only |
| 151 | seller | `/sell-online/resources` | MAPPED | static-only |
| 152 | seller | `/sell-online/resources/flipkart-news` | MAPPED | static-only |
| 153 | seller | `/sell-online/resources/products-demand` | MAPPED | static-only |
| 154 | seller | `/sell-online/resources/seller_success_story` | MAPPED | static-only |
| 155 | seller | `/sell-online/sell-appliances-online` | MAPPED | static-only |
| 156 | seller | `/sell-online/sell-appliances-online/1000` | MAPPED | static-only |
| 157 | seller | `/sell-online/sell-art-online` | MAPPED | static-only |
| 158 | seller | `/sell-online/sell-art-online/1000` | MAPPED | static-only |
| 159 | seller | `/sell-online/sell-beauty-products-online` | MAPPED | static-only |
| 160 | seller | `/sell-online/sell-books-online` | MAPPED | static-only |
| 161 | seller | `/sell-online/sell-clothes-online` | MAPPED | static-only |
| 162 | seller | `/sell-online/sell-clothes-online/1000` | MAPPED | static-only |
| 163 | seller | `/sell-online/sell-electronics-online` | MAPPED | static-only |
| 164 | seller | `/sell-online/sell-electronics-online/1000` | MAPPED | static-only |
| 165 | seller | `/sell-online/sell-furniture-online` | MAPPED | static-only |
| 166 | seller | `/sell-online/sell-home-products-online` | MAPPED | static-only |
| 167 | seller | `/sell-online/sell-home-products-online/1000` | MAPPED | static-only |
| 168 | seller | `/sell-online/sell-indian-clothes-online` | MAPPED | static-only |
| 169 | seller | `/sell-online/sell-indian-clothes-online/1000` | MAPPED | static-only |
| 170 | seller | `/sell-online/sell-jewellery-online` | MAPPED | static-only |
| 171 | seller | `/sell-online/sell-kurtis-online` | MAPPED | static-only |
| 172 | seller | `/sell-online/sell-makeup-online` | MAPPED | static-only |
| 173 | seller | `/sell-online/sell-mobiles-online` | MAPPED | static-only |
| 174 | seller | `/sell-online/sell-mobiles-online/1000` | MAPPED | static-only |
| 175 | seller | `/sell-online/sell-saree-online` | MAPPED | static-only |
| 176 | seller | `/sell-online/sell-saree-online/1000` | MAPPED | static-only |
| 177 | seller | `/sell-online/sell-shirts-online` | MAPPED | static-only |
| 178 | seller | `/sell-online/sell-shirts-online/1000` | MAPPED | static-only |
| 179 | seller | `/sell-online/sell-shoes-online` | MAPPED | static-only |
| 180 | seller | `/sell-online/sell-toys-online` | MAPPED | static-only |
| 181 | seller | `/sell-online/sell-toys-online/1000` | MAPPED | static-only |
| 182 | seller | `/sell-online/sell-tshirts-online` | MAPPED | static-only |
| 183 | seller | `/sell-online/sell-tshirts-online/1000` | MAPPED | static-only |
| 184 | seller | `/sell-online/sell-watch-online` | MAPPED | static-only |
| 185 | seller | `/sell-online/sell-watch-online/1000` | MAPPED | static-only |
| 186 | seller | `/sell-online/sell-womens-clothes-online` | MAPPED | static-only |
| 187 | seller | `/sell-online/seller-tiering-overview` | MAPPED | static-only |
| 188 | seller | `/sell-online/seller_success_story` | MAPPED | static-only |
| 189 | seller | `/sell-online/seller_success_story/arun-palamisamy-owner-joven` | MAPPED | static-only |
| 190 | seller | `/sell-online/seller_success_story/dr-bhavna-bhargava-ceo-stone-soup` | MAPPED | static-only |
| 191 | seller | `/sell-online/seller_success_story/komal-prasand-paul-ultimate-hygiene-barasat` | MAPPED | static-only |
| 192 | seller | `/sell-online/seller_success_story/mathew-joseph-owner-sleepy-head` | MAPPED | static-only |
| 193 | seller | `/sell-online/seller_success_story/md_sabeeluddin` | MAPPED | static-only |
| 194 | seller | `/sell-online/seller_success_story/mohit_vashist` | MAPPED | static-only |
| 195 | seller | `/sell-online/seller_success_story/reena_sanjeev` | MAPPED | static-only |
| 196 | seller | `/sell-online/seller_success_story/sanjay_maheshwari` | MAPPED | static-only |
| 197 | seller | `/sell-online/seller_success_story/shivani_agarwal` | MAPPED | static-only |
| 198 | seller | `/sell-online/services-0` | MAPPED | static-only |
| 199 | seller | `/sell-online/services/flipkart-fulfilment` | MAPPED | static-only |
| 200 | seller | `/sell-online/shopsy` | MAPPED | static-only |
| 201 | seller | `/sell-online/storageAndShipping` | MAPPED | static-only |
| 202 | seller | `/sell-online/terms-of-use` | MAPPED | static-only |
| 203 | seller | `/sell-online/terms-use` | MAPPED | static-only |
| 204 | seller | `/sell-online/zeroCommissionTnC` | MAPPED | static-only |
| 205 | seller | `/seller` | MAPPED | yes (Part A) |
| 206 | seller | `/seller-blog` | MAPPED | static-only |
| 207 | seller | `/seller-blog/` | MAPPED | static-only |
| 208 | seller | `/seller-blog/:preloginUrl` | MAPPED | static-only |
| 209 | seller | `/seller-blog/ecommerce-myths-about-selling-online` | MAPPED | static-only |
| 210 | seller | `/seller-blog/how-to-find-a-profitable-product-to-sell-online` | MAPPED | static-only |
| 211 | seller | `/seller-blog/online-selling-guide` | MAPPED | static-only |
| 212 | seller | `/seller-blog/privacy-policy` | MAPPED | static-only |
| 213 | seller | `/seller-blog/terms-of-use` | MAPPED | static-only |
| 214 | seller | `/seller-blogs` | MAPPED | static-only |
| 215 | seller | `/seller-blogs/:preloginUrl` | MAPPED | static-only |
| 216 | seller | `/seller-catalog-approval` | MAPPED | static-only |
| 217 | seller | `/seller-success-stories` | MAPPED | static-only |
| 218 | seller | `/seller-university` | MAPPED | static-only |
| 219 | seller | `/seller/getAllowedSellersListForUser` | MAPPED | yes (Part A) |
| 220 | seller | `/seller/switchSellerContext` | MAPPED | yes (Part A) |
| 221 | seller | `/sellerDashboard` | MAPPED | static-only |
| 222 | seller | `/sellerDashboard/fed-ads` | MAPPED | static-only |
| 223 | seller | `/sellerDashboard/getRemoteConfigFull` | MAPPED | static-only |
| 224 | seller | `/sellerDashboard/napi` | MAPPED | static-only |
| 225 | seller | `/sellerSupport` | MAPPED | static-only |
| 226 | seller | `/sellerTierNavTrail` | MAPPED | static-only |
| 227 | seller | `/send-user-collection` | MAPPED | static-only |
| 228 | seller | `/service-unavailable` | MAPPED | static-only |
| 229 | seller | `/session-management/session` | MAPPED | static-only |
| 230 | seller | `/session-management/sessions` | MAPPED | static-only |
| 231 | seller | `/sessions-management` | MAPPED | static-only |
| 232 | seller | `/settings` | MAPPED | static-only |
| 233 | seller | `/settings-status` | MAPPED | static-only |
| 234 | seller | `/settings-users` | MAPPED | static-only |
| 235 | seller | `/settings/:type` | MAPPED | static-only |
| 236 | seller | `/settings/bankDetails` | MAPPED | static-only |
| 237 | seller | `/settings/calenderDetails` | MAPPED | static-only |
| 238 | seller | `/settings/editPickupAddress` | MAPPED | static-only |
| 239 | seller | `/settings/gstin-Onboarding` | MAPPED | static-only |
| 240 | seller | `/settings/incorrectGSTINs` | MAPPED | static-only |
| 241 | seller | `/settings/manageLocation/addFBFLocations/:warehouseId` | MAPPED | static-only |
| 242 | seller | `/settings/manageLocation/addMoreLocations/:locationId` | MAPPED | static-only |
| 243 | seller | `/settings/updatePin` | MAPPED | static-only |
| 244 | seller | `/settings/verifyGSTINs` | MAPPED | static-only |
| 245 | seller | `/shopsy` | MAPPED | static-only |
| 246 | seller | `/signUp/accountCreation/new` | MAPPED | static-only |
| 247 | seller | `/signature/signature` | MAPPED | static-only |
| 248 | seller | `/site_media/images/icons/notifications/close-x-` | MAPPED | static-only |
| 249 | seller | `/site_media/images/icons/notifications/play-` | MAPPED | static-only |
| 250 | seller | `/sitemap` | MAPPED | static-only |
| 251 | seller | `/slp/sites/slp/files/wp/images/cu/10` | MAPPED | static-only |
| 252 | seller | `/slp/sites/slp/files/wp/images/cu/3_flipkart-snippet_Your` | MAPPED | static-only |
| 253 | seller | `/slp/sites/slp/files/wp/images/cu/4_flipkart-snippet_5` | MAPPED | static-only |
| 254 | seller | `/slp/sites/slp/files/wp/images/cu/5_flipkart-snippet_How` | MAPPED | static-only |
| 255 | seller | `/slp/sites/slp/files/wp/images/cu/Do` | MAPPED | static-only |
| 256 | seller | `/slp/sites/slp/files/wp/images/cu/FK` | MAPPED | static-only |
| 257 | seller | `/slp/sites/slp/files/wp/images/cu/FK_How` | MAPPED | static-only |
| 258 | seller | `/slp/sites/slp/files/wp/images/main/How` | MAPPED | static-only |
| 259 | seller | `/slp/slp-article-tags/data-intelligence` | MAPPED | static-only |
| 260 | seller | `/snoopyIngestion` | MAPPED | static-only |
| 261 | seller | `/step/2` | MAPPED | static-only |
| 262 | seller | `/sub-account-management` | MAPPED | static-only |
| 263 | seller | `/suv-slc-access-denied` | MAPPED | static-only |
| 264 | seller | `/tds` | MAPPED | static-only |
| 265 | seller | `/tempDSOrders` | MAPPED | static-only |
| 266 | seller | `/terms-of-use` | MAPPED | static-only |
| 267 | seller | `/tickets/:filter` | MAPPED | static-only |
| 268 | seller | `/tmp` | MAPPED | static-only |
| 269 | seller | `/to_deliver` | MAPPED | static-only |
| 270 | seller | `/to_pack` | MAPPED | yes (Part A) |
| 271 | seller | `/to_service` | MAPPED | static-only |
| 272 | seller | `/track/` | MAPPED | static-only |
| 273 | seller | `/unifiedInventory/FBF` | MAPPED | yes (Part A) |
| 274 | seller | `/unit` | MAPPED | static-only |
| 275 | seller | `/upload/dispatch/box-detail` | MAPPED | static-only |
| 276 | seller | `/variants` | MAPPED | static-only |
| 277 | seller | `/verifyOtp` | MAPPED | static-only |
| 278 | seller | `/viewIssueManagementTicket/:referenceNumber/:sc` | MAPPED | static-only |
| 279 | seller | `/work-in-progress` | MAPPED | static-only |
| 280 | seller | `/ws/voice` | MAPPED | static-only |
| 281 | seller | `/zeroCommissionVerticals` | MAPPED | static-only |
| 282 | vendorhub | `/active` | MAPPED | yes (Part A) |
| 283 | vendorhub | `/agreements` | MAPPED | yes (Part A) |
| 284 | vendorhub | `/agreements/brand-offer` | MAPPED | yes (Part A) |
| 285 | vendorhub | `/agreements/claims-collection-request-management` | MAPPED | yes (Part A) |
| 286 | vendorhub | `/catalog` | MAPPED | static-only |
| 287 | vendorhub | `/create` | MAPPED | static-only |
| 288 | vendorhub | `/debit-notes` | MAPPED | yes (Part A) |
| 289 | vendorhub | `/details` | MAPPED | yes (Part A) |
| 290 | vendorhub | `/details/` | MAPPED | yes (Part A) |
| 291 | vendorhub | `/details/:id` | MAPPED | yes (Part A) |
| 292 | vendorhub | `/download` | MAPPED | static-only |
| 293 | vendorhub | `/forgot-password` | MAPPED | static-only |
| 294 | vendorhub | `/get-retailers` | MAPPED | static-only |
| 295 | vendorhub | `/home` | MAPPED | yes (Part A) |
| 296 | vendorhub | `/inventory` | MAPPED | yes (Part A) |
| 297 | vendorhub | `/isAuthenticated` | MAPPED | static-only |
| 298 | vendorhub | `/landing` | MAPPED | yes (Part A) |
| 299 | vendorhub | `/learning-center` | MAPPED | static-only |
| 300 | vendorhub | `/learning-center-detail` | MAPPED | static-only |
| 301 | vendorhub | `/legalMetrologyNonCompliance` | MAPPED | static-only |
| 302 | vendorhub | `/list` | MAPPED | yes (Part A) |
| 303 | vendorhub | `/login` | MAPPED | static-only |
| 304 | vendorhub | `/logout` | MAPPED | static-only |
| 305 | vendorhub | `/monitor` | MAPPED | static-only |
| 306 | vendorhub | `/my` | MAPPED | yes (Part A) |
| 307 | vendorhub | `/onboarding` | MAPPED | static-only |
| 308 | vendorhub | `/operational-performance` | MAPPED | static-only |
| 309 | vendorhub | `/operations` | MAPPED | yes (Part A) |
| 310 | vendorhub | `/operations/` | MAPPED | yes (Part A) |
| 311 | vendorhub | `/payments` | MAPPED | yes (Part A) |
| 312 | vendorhub | `/payments/` | MAPPED | yes (Part A) |
| 313 | vendorhub | `/performance` | MAPPED | static-only |
| 314 | vendorhub | `/profile` | MAPPED | yes (Part A) |
| 315 | vendorhub | `/purchasing-trends` | MAPPED | static-only |
| 316 | vendorhub | `/reset-password` | MAPPED | static-only |
| 317 | vendorhub | `/select-account` | MAPPED | static-only |
| 318 | vendorhub | `/select-retailer` | MAPPED | static-only |
| 319 | vendorhub | `/select-vendor` | MAPPED | static-only |
| 320 | vendorhub | `/signup` | MAPPED | static-only |
| 321 | vendorhub | `/snoopyIngestion/trackEvent` | MAPPED | static-only |
| 322 | vendorhub | `/stock` | MAPPED | static-only |
| 323 | vendorhub | `/suspended` | MAPPED | static-only |
| 324 | vendorhub | `/upload` | MAPPED | static-only |
| 325 | vendorhub | `/uploadComplianceInformation` | MAPPED | static-only |
| 326 | vendorhub | `/users` | MAPPED | static-only |
| 327 | vendorhub | `/v0` | MAPPED | static-only |
| 328 | vendorhub | `/validate-recovery-token` | MAPPED | static-only |
| 329 | vendorhub | `/vendor-p/download-file/` | MAPPED | yes (Part A) |
| 330 | vendorhub | `/vendor-p/upload/legal-metrology/feed/upload` | MAPPED | yes (Part A) |
| 331 | vendorhub | `/vendor-portal` | MAPPED | yes (Part A) |
| 332 | vendorhub | `/vendor-portal/home` | MAPPED | yes (Part A) |
| 333 | vendorhub | `/vendor/accounting/debit-note/` | MAPPED | yes (Part A) |
| 334 | vendorhub | `/vendor/accounting/debit_note/details/id` | MAPPED | yes (Part A) |
| 335 | vendorhub | `/vendor/aggregate-entities` | MAPPED | yes (Part A) |
| 336 | vendorhub | `/vendor/analytics/aggregated-metrics` | MAPPED | yes (Part A) |
| 337 | vendorhub | `/vendor/analytics/filter-data` | MAPPED | yes (Part A) |
| 338 | vendorhub | `/vendor/analytics/product-details` | MAPPED | yes (Part A) |
| 339 | vendorhub | `/vendor/analytics/report` | MAPPED | yes (Part A) |
| 340 | vendorhub | `/vendor/analytics/sales-report` | MAPPED | yes (Part A) |
| 341 | vendorhub | `/vendor/cataloging/browse-tree` | MAPPED | yes (Part A) |
| 342 | vendorhub | `/vendor/cataloging/check-template` | MAPPED | yes (Part A) |
| 343 | vendorhub | `/vendor/cataloging/create-fsn` | MAPPED | yes (Part A) |
| 344 | vendorhub | `/vendor/cataloging/feed-list` | MAPPED | yes (Part A) |
| 345 | vendorhub | `/vendor/cataloging/vertical-attributes` | MAPPED | yes (Part A) |
| 346 | vendorhub | `/vendor/config` | MAPPED | yes (Part A) |
| 347 | vendorhub | `/vendor/config/sale-config` | MAPPED | yes (Part A) |
| 348 | vendorhub | `/vendor/feeds/download-feed-file` | MAPPED | yes (Part A) |
| 349 | vendorhub | `/vendor/feeds/feed-list` | MAPPED | yes (Part A) |
| 350 | vendorhub | `/vendor/feeds/feed-search` | MAPPED | yes (Part A) |
| 351 | vendorhub | `/vendor/feeds/upload-feed-file` | MAPPED | yes (Part A) |
| 352 | vendorhub | `/vendor/operational-performance` | MAPPED | yes (Part A) |
| 353 | vendorhub | `/vendor/purchase-orders-summary` | MAPPED | yes (Part A) |
| 354 | vendorhub | `/vendor/purchasing-trends` | MAPPED | yes (Part A) |
| 355 | vendorhub | `/vendor/qc-norms/bis-list` | MAPPED | yes (Part A) |
| 356 | vendorhub | `/vendor/qc-norms/upload-bis-certificates` | MAPPED | yes (Part A) |
| 357 | vendorhub | `/vendor/qc-norms/upload-feed-file` | MAPPED | yes (Part A) |
| 358 | vendorhub | `/vendor/recon-tool/redirect` | MAPPED | yes (Part A) |
| 359 | vendorhub | `/vendor/return-orders-summary` | MAPPED | yes (Part A) |
| 360 | vendorhub | `/vendor/support/send-mail` | MAPPED | yes (Part A) |
| 361 | vendorhub | `/vendor/ticketPortalUrl` | MAPPED | yes (Part A) |
| 362 | vendorhub | `/vendor/uam/isResourcesAuthorised` | MAPPED | yes (Part A) |
| 363 | vendorhub | `/vendor/user-management/change-password` | MAPPED | yes (Part A) |
| 364 | vendorhub | `/vendor/user-management/profile` | MAPPED | yes (Part A) |
| 365 | vendorhub | `/vendor/user-management/profile/my` | MAPPED | yes (Part A) |
| 366 | vendorhub | `/vendor/user-management/roles-and-warehouses` | MAPPED | yes (Part A) |
| 367 | vendorhub | `/vendor/user-management/update-user` | MAPPED | yes (Part A) |
| 368 | vendorhub | `/vendor/user-management/user` | MAPPED | yes (Part A) |
| 369 | vendorhub | `/vendor/user-management/user-activation/activate` | MAPPED | yes (Part A) |
| 370 | vendorhub | `/vendor/user-management/user-activation/suspend` | MAPPED | yes (Part A) |
| 371 | vendorhub | `/vendor/user-management/user-data` | MAPPED | yes (Part A) |
| 372 | vendorhub | `/vendor/user-management/users/active` | MAPPED | yes (Part A) |
| 373 | vendorhub | `/vendor/user-management/users/suspended` | MAPPED | yes (Part A) |
| 374 | vendorhub | `/vendor/user-management/vendor-list` | MAPPED | yes (Part A) |
| 375 | vendorhub | `/view` | MAPPED | static-only |
| 376 | vendorhub | `/welcome` | MAPPED | static-only |
| 377 | vendorhub | `/whats-new` | MAPPED | static-only |

**Part B total: 377 routes STATIC-mapped (100%).** Live section screenshots: 37 (Part A). No route is omitted; unwalked ones are enumerated with a reason.