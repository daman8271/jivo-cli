---
id: C-0007
date: 2026-08-03
author: claude (live-verified during factory API rescrape)
area: factory
severity: high
status: active
supersedes: 
tags: [factory-api, read-only]
---

# Factory API: GET can write — /marketplace/settings/ is a get_or_create

## Wrong
Assumed every GET on the factory API is a safe read, and probed GET /marketplace/settings/?channel=<X> with invented channel values to discover which ones the API accepts.

## Right
GET /marketplace/settings/?channel=<X> CREATES a settings row when none exists for that channel. Probing six values (AMAZON, MEESHO, JIOMART, BLINKIT, ZEPTO, INVALID_XYZ) created six production rows, ids 2-7. The pre-existing FLIPKART row (id 1) kept its 2026-07-17 updated_at, proving reads do not touch existing rows and the six were genuinely new. A method-level read-only guard does not protect this API; safety must be established per endpoint.

## Evidence
Live 2026-08-03 13:23 IST: curl -H 'Company-Code: JIVO_MART' 'https://factory.jivo.in/api/v1/marketplace/settings/?channel=<X>' for X in FLIPKART,AMAZON,MEESHO,JIOMART,BLINKIT,ZEPTO,INVALID_XYZ returned ids 1..7; ids 2-7 all carried updated_at within 700ms of each other in request order, while re-GET of FLIPKART still showed updated_at 2026-07-17T13:29:41.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Factory API: a GET can write. Never send an invented parameter value to it. GET /marketplace/settings/?channel=X creates a row; treat any key-lookup endpoint returning a single object with id/created_at as suspected get_or_create and do not probe it with a novel key.
