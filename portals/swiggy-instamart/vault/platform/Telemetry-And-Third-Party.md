---
title: Telemetry And Third Party
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, platform, platform]
status: studied
---


# Telemetry And Third Party

> New Relic and Swiggy analytics beacons — out of scope, documented.

The portal ships two telemetry channels that are not JIVO business surfaces but
do appear in any honest network capture, so they are recorded rather than
silently filtered:

- **New Relic Browser** on `bam.nr-data.net` (`/1/<key>`, `/events/1/<key>`,
  `/browser/blobs`), configured in-app with a `NR_ENDPOINT` on
  `insights-collector.newrelic.com` for account `737486`. The shell also names an
  `appVCode` of `0.0.34`.
- **Swiggy analytics** on `analytics.swiggy.com/message-set`.

Neither carries JIVO data worth reading; both are excluded from the CLI.

**Endpoints in this section:** 0 (0 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

_No read endpoint is assigned to this section — it is a route/UI surface that renders from endpoints documented in sibling notes._

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- These are **third-party hosts**, so they are listed for completeness of the
  network record and explicitly kept out of the endpoint allowlist.
- The New Relic browser key appeared in captured URLs and has been **redacted**
  per G6 by `captures/scrub.py`.
- Because they are non-GET beacons, they would otherwise clutter the
  AMENDMENT-04 audit trail; they are filtered out of
  `nonget-allowed.tsv` by host, and that filter is stated here so the omission
  is not mistaken for completeness.

## Screenshots (live read-only walk, 2026-07-30)

_No screenshot is attributed to this section; its endpoints are exercised from pages captured under sibling notes. See [[Swiggy-Instamart-Screenshot-Index]] for the full set._

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
