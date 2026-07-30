---
title: Profile-and-Account
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, platform, read-only]
status: studied
---

# Profile-and-Account

> ⚠️ READ-ONLY. Manage profile, multi-seller select, partner permissions, myp account surfaces.

**Endpoints in this section:** 76 — 10 read-safe (READ/READ_FILE), 34 write/export (out of scope), 32 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/manageProfile/cygnetGstin` | — | READ |
| R-file | GET | `seller.flipkart.com/napi/manageProfile/download-document/` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/manageProfile/get-pincode-details` | — | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/getAppSessions` | — | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/getNFBFLocation` | — | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/getSellerAccountDetails` | fetchApi | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/getSellerBusinessDetails` | fetchApi | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/getSellerIdentity` | — | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/kycGstin` | fetchApi | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/myp/download-eligible-listings` | downloadListApi | READ_FILE |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/api/partnerPermissions/deletePartnerAccess` | deletePartnerAccess | WRITE |
| GET | `seller.flipkart.com/napi/manageProfile/addSellerHoliday` | submitUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/create-` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/createRegisteredApplication` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteAccountWithOtp` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteAllAppSession` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteAppSession` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteCalendarHolidays` | submitUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteOtherAppSession` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteRegisteredApplication` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/dummyFileUpload-multilocation` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/fileUpload` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/generateOTPSelfServePhone` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/generateOtp` | updateApi | WRITE |
| GET | `seller.flipkart.com/napi/manageProfile/getRegisteredApplications` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/revokeRegisteredApplication` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/rules-confirmation` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/saveLogisticsSetting` | submitUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/submitEmailDetails` | submitUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/update-gstin-loc-details` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateBankDetails` | submitUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateBusinessDetails` | submitUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateContactDetails` | submitUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateDisplayDetails` | submitUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateEmailOtp` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateFADetails` | submitUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateGstin` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateInvoiceAddress` | — | WRITE |
| GET | `seller.flipkart.com/napi/manageProfile/updateOTPSelfServePhone` | submitUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updatePocDetails` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateSellerPreference` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateTwoFactorDetails/v2` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateWorkingHours` | submitUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/myp/delete-uploaded-listings` | deleteUploadedFile | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/api/partnerPermissions/checkPartnerAccess` | checkPartnerAccess |
| UNKNOWN | `seller.flipkart.com/api/partnerPermissions/invokePartnerAccess` | invokePartnerAccess |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/` | submitUrl |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/check-serviceability` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/fieldExists` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/get-location-rules` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/get-location-tasks` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/get-reactivation-clause` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/get-seller-pan` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/getBankDetails` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/getLocationsList` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/getReturnLocations` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/getSellerCalendarDetails` | getUrl |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/getSellerPreference` | — |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/getSellerSettingsDetails` | — |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/goingWithoutGSTin` | submitUrl |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/gstinExists` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/partnerSearch` | searchUrl |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/requestAMREcallback` | amreRCBUrl |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/resendEmailVerification` | verifyEmailUrl |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/seller-has-gstin` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/validateSellerHoliday` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/verifyEmailOtp` | submitUrl |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/verifyMobile` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/verifyOTPSelfServePhone` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/verifyProperty` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/weekly-off-metadata` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/myp/eligible-listings-count` | eligibleListingsCount |
| UNKNOWN | `seller.flipkart.com/napi/myp/get-category-tree` | categoryFetchApi |
| UNKNOWN | `seller.flipkart.com/napi/myp/get-seller-brands` | brandsFetchApi |
| UNKNOWN | `seller.flipkart.com/napi/myp/search-by-listing-id` | searchByListingIdApi |
| UNKNOWN | `seller.flipkart.com/napi/myp/search-by-sku` | searchBySkuApi |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
