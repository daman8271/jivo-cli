---
title: Buyer-Seller Messaging & Cases
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, seller, messaging-buyer-seller]
status: studied
read_only: true
---

# Buyer-Seller Messaging & Cases

**Portal:** Seller Central (3P) · **Section:** `seller/Messaging-Buyer-Seller` · **Endpoints catalogued:** 21 (17 read-safe, 16 PROVEN live · 1 out-of-scope · 3 unknown/telemetry)

Buyer-Seller Messaging inbox + the global case/contact system. Reads: case list, case detail (71 fields), partner accounts, marketplaces, topic categories, and the contacts-* overview metrics (resolved / needs-response / require-attention / reported-unresolved).

## What it looks like (live, this run)

![21 messaging inbox](../seller/sec-21-messaging-inbox.png)

*Captured live from JIVO Mart's Seller Central session, seller/sec-21-messaging-inbox.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /conversation-api/v1/notifications | 1 | READ |
| ✅ | GET | sellercentral.amazon.in · /conversation-api/v1/sidebarContext | 8 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/api/global/cases | 2 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/api/global/cases/{uuid} | 71 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/api/global/cases/{uuid}/orderContext | 7 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/api/global/cases/{uuid}/responsetemplates | 2 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/api/global/partnerAccounts | 3 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/api/global/partnerAccounts/marketplaces | 5 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/api/global/rights | 2 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/api/global/topics/categories | 2 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/overview/api/metric/contactsReportedUnresolved | 2 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/overview/api/metric/contactsRequireAttention | 2 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/overview/api/metric/contactsResolved | 2 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/overview/api/metric/contactsResponseNeeded | 2 | READ |
| ✅ | GET | sellercentral.amazon.in · /messaging/v2/i18n/en-IN.{hash}.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /messaging/v2/i18n/en-US.{hash}.json | — | READ_FILE |
| · | GET | sellercentral.amazon.in · /messaging/inbox | — | READ |

## Response shapes (full field lists, from live capture)

- **`/conversation-api/v1/notifications`** (1 fields): `notifications`
- **`/conversation-api/v1/sidebarContext`** (8 fields): `availableCapabilities`, `availableCapabilities.capabilityType`, `availableCapabilities.description`, `availableCapabilities.valueOptions`, `betaTagEligible`, `caFTEligible`, `customerIdentifier`, `enabledFeatures`
- **`/messaging/api/global/cases`** (2 fields): `cases`, `displayLanguage`
- **`/messaging/api/global/cases/{uuid}`** (71 fields): `partyCase`, `partyCase.actionNeeded`, `partyCase.actions`, `partyCase.archived`, `partyCase.asinIds`, `partyCase.buyerActive`, `partyCase.buyerGuidelinesDisclaimerDisplay`, `partyCase.buyerLop`, `partyCase.buyerLopTag`, `partyCase.buyerName`, `partyCase.buyerPreferredResolution`, `partyCase.buyerProxyEmail`, `partyCase.caseArtifacts`, `partyCase.caseArtifacts.artifactType`, `partyCase.caseArtifacts.attachments`, `partyCase.caseArtifacts.caseArtifactId`, `partyCase.caseArtifacts.caseId`, `partyCase.caseArtifacts.createdDate`, `partyCase.caseArtifacts.creator`, `partyCase.caseArtifacts.draftAttachments`, `partyCase.caseArtifacts.formattedDate`, `partyCase.caseArtifacts.isRequestedPartySender`, `partyCase.caseArtifacts.message`, `partyCase.caseArtifacts.topicId`, `partyCase.caseId`, `partyCase.caseMetadata`, `partyCase.classifiedTopicId`, `partyCase.closeDate`, `partyCase.formattedLastUpdatedDate`, `partyCase.formattedResolveDate`, `partyCase.important`, `partyCase.isBusinessBuyer`, `partyCase.isOverSla`, `partyCase.lastUpdatedDate`, `partyCase.latestCedrPollId`, `partyCase.latestCedrResponseDate`, `partyCase.latestCedrSurveyResponse`, `partyCase.latestPreferredResolution`, `partyCase.latestSellerMessageId`, `partyCase.latestWhereIsMyStuffStatus` …
- **`/messaging/api/global/cases/{uuid}/orderContext`** (7 fields): `orderContextList`, `orderContextList.a2zClaimsInfo`, `orderContextList.isMFNOrder`, `orderContextList.orderContextButtons`, `orderContextList.orderContextFields`, `orderContextList.preClaimA2ZHint`, `orderContextList.productContextFields`
- **`/messaging/api/global/cases/{uuid}/responsetemplates`** (2 fields): `buyerLop`, `responseTemplates`

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| POST | sellercentral.amazon.in · /messaging/api/resourceError | READ_POST | POST-bodied endpoint, read-shaped (G0 forbids POST) |

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| GET | sellercentral.amazon.in · /messaging/api/global/weblab | NOISE |
| GET | sellercentral.amazon.in · /messaging/api/global/weblab/v2 | NOISE |
| GET | sellercentral.amazon.in · /messaging/api/weblab/marketplace | NOISE |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

