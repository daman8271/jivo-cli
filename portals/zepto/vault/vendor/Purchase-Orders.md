---
title: Purchase Orders
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, purchase-orders]
status: studied
---

# Purchase Orders

The **Purchase Orders** section is Zepto's inbound-demand surface — every PO that **Zepto raises to JIVO** (Jivo Wellness Pvt. Ltd., Manufacturer, STANDARD tier, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, login `ecom1@jivo.in`). Each PO carries an ordered qty/value, a delivery facility (mother-hub / MH), an issue + expiry date, and a lifecycle status (Created → Unscheduled → Scheduled → Delivered/GRN'd, or Cancelled). From here JIVO reviews the PO grid + summary tiles, drills into one PO's **items · checklist · attachments · activity logs · linked ASN · linked GRN**, tracks the downstream **GRN** (Goods Receipt Note — what the hub actually received), and hands a PO into the **scheduling / appointment** flow (schedule / reschedule / unschedule / cancel — all writes, held out of scope). All calls hit **`fcc.zepto.co.in`** (the vendor-reports backend) under the `api/v1/po/*` and `api/v1/grn/*` prefixes, using the single JWT in the `authorization` header (no `Bearer` prefix) documented in [[Auth-and-Access]]. Endpoint contracts below were read out of the vendor remote (635) code-split chunk `captures/js/vendor/3539.64ab07c46b8741b5.js` — the API-constant map (`GET_PO_LISTING`, `getPoDetailsById`, `GET_GRN_LISTING`, …) plus its `getPoActivityLogsById`/`getGrnDetailsById` id-templating bindings — not live captures (the only JWT on disk is expired; see evidence).

## Subpages & tabs

**List page** — `/po` (and the `/vendor/po` shell alias)
- The PO grid (`GET_PO_LISTING` = `api/v1/po/filter`), server-filtered by facility + vendor + status + date.
- Summary tiles (`GET_PO_SUMMARY` = `api/v1/po/listing-stat`) — aggregated open/scheduled/delivered counts and value.
- Scheduling views: **Scheduled PO summary** (`GET_SCHEDULED_PO_SUMMARY` = `api/v1/po/scheduled`) and **inbound-capacity** slots (`GET_IB_CAPACITY` = `api/v1/po/ib-capacity`) that drive the appointment picker.
- Filter dropdowns: **Facility / MH list** (`api/v1/po/user/mh-list`) and **Vendor list** (`api/v1/po/user/vendor-list`).
- Non-trade twin at `/po-non-trade` (+ `/po-non-trade/summary`, `/po-non-trade/asn`, `/po-non-trade/grn`) — the same grid for non-trade POs; endpoints reuse the `po`/`grn` constants.

**Detail page** — `/po/lifecycle` → `/vendor/po/lifecycle/:poId`, tabbed:
- **PO detail** (`getPoDetailsById` = `api/v1/po/{id}`) — header: facility, issue/expiry date, vendor, status.
- **Items tab** (`getPoItemsById` = `api/v1/po/{id}/items`) — ordered line items (SKU, qty, value).
- **Checklist tab** (`getPoChecklistById` = `api/v1/po/{id}/checklist`) — pre-dispatch / appointment checklist.
- **Attachments** (`getPoDocumentsById` = `api/v1/po/{id}/attachments`) — PO document links.
- **Activity logs** (`getPoActivityLogsById` = `api/v1/po/{id}/logs`) — PO state-change audit trail.
- **Linked ASN** (`getAsnByPoId` = `api/v1/po/{id}/asn`) → hands off to [[ASN]].
- **Linked GRN** (`getGrnByPoId` = `api/v1/po/{id}/grn`) → the receipt view below.

**GRN views** — `/po/grn` → `/vendor/po/grn/:grnId` (goods actually received against the PO)
- GRN grid (`GET_GRN_LISTING` = `api/v1/grn/filter`) with its own facility (`api/v1/grn/user/mh-list`) + vendor (`api/v1/grn/user/vendor-list`) filters.
- GRN detail (`getGrnDetailsById` = `api/v1/grn/{id}`), GRN items (`getGrnItemsById` = `api/v1/grn/{id}/items`), and the ASN that produced it (`getAsnByGrnId` = `api/v1/grn/{id}/asn-info`).

**Returns** — `/po/returns` → `/vendor/po/returns/:rtvId` links the PO lifecycle into the return flow documented under [[RTV]].

## Filters & columns (what the grid shows)

The PO and GRN grids share the same two server-driven filter dropdowns:
| UI label | Endpoint | Source |
|---|---|---|
| Facility / Mother-Hub | `api/v1/po/user/mh-list` · `api/v1/grn/user/mh-list` | `EXTERNAL_LOCATION_FILTER_LIST` |
| Vendor | `api/v1/po/user/vendor-list` · `api/v1/grn/user/vendor-list` | `EXTERNAL_VENDOR_FILTER_LIST` |

(The generic commons variants `api/v1/commons/user/mh-list` / `api/v1/commons/user/vendor-list` seen alongside these constants belong to the shared filter layer in [[Platform-Common]]; the PO-scoped ones above are the section's own.) Status set (Created / Unscheduled / Scheduled / Rescheduled / Delivered / Cancelled) and the exact column array render client-side in `3539.…js`; a logged-in grid capture is still owed (JWT expired at capture time).

## API endpoints

Base = `https://fcc.zepto.co.in/` + path. `{id}` = a PO id (or GRN id) path parameter (the bundle wires these as `` e=>`api/v1/po/${e}` ``). Auth = `authorization: <jwt>` (no `Bearer`), `accept: application/json`; WAF headers not enforced as of last capture. All rows below are pure GETs (no state change).

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/api/v1/po/filter` | PO list grid (`GET_PO_LISTING`) | READ |
| GET | `/api/v1/po/listing-stat` | PO summary tiles — aggregated counts/value (`GET_PO_SUMMARY`) | READ |
| GET | `/api/v1/po/scheduled` | Scheduled-PO summary (`GET_SCHEDULED_PO_SUMMARY`) | READ |
| GET | `/api/v1/po/ib-capacity` | Inbound-capacity slots for scheduling (`GET_IB_CAPACITY`) | READ |
| GET | `/api/v1/po/user/mh-list` | Facility / mother-hub filter values (`EXTERNAL_LOCATION_FILTER_LIST`) | READ |
| GET | `/api/v1/po/user/vendor-list` | Vendor filter values (`EXTERNAL_VENDOR_FILTER_LIST`) | READ |
| GET | `/api/v1/po/{id}` | Single PO detail (`getPoDetailsById`) | READ |
| GET | `/api/v1/po/{id}/items` | Ordered line items of a PO (`getPoItemsById`) | READ |
| GET | `/api/v1/po/{id}/checklist` | PO pre-dispatch/appointment checklist (`getPoChecklistById`) | READ |
| GET | `/api/v1/po/{id}/attachments` | PO document/attachment links (`getPoDocumentsById`) | READ (file) |
| GET | `/api/v1/po/{id}/logs` | PO activity / state-change audit log (`getPoActivityLogsById`) | READ |
| GET | `/api/v1/po/{id}/asn` | ASN(s) linked to a PO (`getAsnByPoId`) → [[ASN]] | READ |
| GET | `/api/v1/po/{id}/grn` | GRN(s) linked to a PO (`getGrnByPoId`) | READ |
| GET | `/api/v1/grn/filter` | GRN list grid (`GET_GRN_LISTING`) | READ |
| GET | `/api/v1/grn/{id}` | Single GRN detail (`getGrnDetailsById`) | READ |
| GET | `/api/v1/grn/{id}/items` | Received line items of a GRN (`getGrnItemsById`) | READ |
| GET | `/api/v1/grn/{id}/asn-info` | ASN behind a GRN (`getAsnByGrnId`) | READ |
| GET | `/api/v1/grn/user/mh-list` | GRN-grid facility filter values (`EXTERNAL_LOCATION_FILTER_LIST`) | READ |
| GET | `/api/v1/grn/user/vendor-list` | GRN-grid vendor filter values (`EXTERNAL_VENDOR_FILTER_LIST`) | READ |

> Probe status: `GET /api/v1/po/listing-stat` fired once (read-only) → **HTTP 401 `{"code":401,"message":"Token expired"}`**; halted per guardrails. **0 PROVEN**; all 19 reads remain **documented (not probed)**. Transcript: `captures/vendor/purchase-orders-probes.txt`.

**Out of scope (writes) — documented from the bundle only, never called by a read-only CLI:**

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/api/v1/po/cancel` | Cancel a scheduled-PO request (`CANCEL_REQUEST`) | WRITE |
| POST* | `/api/v1/po/acknowledge` | Acknowledge/accept a PO (`ACKNOWLEDGE_PO`) | WRITE |
| POST* | `/api/v1/po/schedule` | Schedule a PO appointment (`SCHEDULE_PO`) | WRITE |
| POST* | `/api/v1/po/request-schedule` | Request a scheduling slot (`REQUEST_PO`) | WRITE |
| POST* | `/api/v1/po/reschedule` | Reschedule a PO appointment (`RESCHEDULE_PO`) | WRITE |
| POST* | `/api/v1/po/unschedule` | Unschedule a PO appointment (`UNSCHEDULE_PO`) | WRITE |

\* method not literally observed in the bundle (constant is a bare path string, not bound to `doHttpGet`); verb inferred from the mutating action name. Treated as WRITE and excluded regardless — the appointment/scheduling verbs change PO state and are covered on the fulfilment side by [[ASN]].

## Real data seen (evidence)

- **Endpoint set** extracted from the vendor remote (module federation remote 635) chunk `captures/js/vendor/3539.64ab07c46b8741b5.js` — the `GET_PO_LISTING`/`GET_PO_SUMMARY`/`GET_GRN_LISTING` constant map and the `` e=>`api/v1/po/${e}/...` `` id-templated bindings (`getPoDetailsById`, `getPoItemsById`, `getPoChecklistById`, `getPoDocumentsById`, `getPoActivityLogsById`, `getAsnByPoId`, `getGrnByPoId`, `getGrnDetailsById`, `getGrnItemsById`, `getAsnByGrnId`).
- **Backend confirmed** = `fcc.zepto.co.in` (same host as the already-proven SALES + INVENTORY `api/v1/reports*` pulls in `zepto-cli`), so the auth model and host are live; only the token is stale.
- **Live probe (read-only, 2026-07-24):** `GET /api/v1/po/listing-stat` → **401 `Token expired`** (JWT `exp` 2026-07-13 18:29:59 UTC). Same expired-token state as the [[RTV]], [[Release-Orders-Amendment-Requests]] and [[Vendor-Reports-Queue]] probes. Nothing upgraded to PROVEN; a fresh JWT is needed to capture response shapes for the PO/GRN grid + detail bodies.
- **No `captures/vendor/*.json` response body** exists for any PO/GRN endpoint yet — exact filter keys, column arrays and status enums want a live (read-only) capture once a valid token is available.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no schedule/acknowledge/cancel writes):
- `zepto po list [--facility … --vendor … --status …]` → `GET api/v1/po/filter`; `zepto po summary` → `api/v1/po/listing-stat`.
- `zepto po scheduled` → `api/v1/po/scheduled`; `zepto po capacity` → `api/v1/po/ib-capacity`.
- `zepto po facets facilities|vendors` → `api/v1/po/user/{mh-list,vendor-list}`.
- `zepto po get <poId>` → `api/v1/po/{id}`; `… items` / `… checklist` / `… attachments` / `… logs` → the per-id sub-resources.
- `zepto po asn <poId>` → `api/v1/po/{id}/asn`; `zepto po grn <poId>` → `api/v1/po/{id}/grn`.
- `zepto grn list [--facility … --vendor …]` → `api/v1/grn/filter`; `zepto grn get <grnId>` → `api/v1/grn/{id}`; `… items` / `… asn-info`.

Explicitly **excluded** from the read-only surface: PO acknowledge, schedule, request-schedule, reschedule, unschedule, and cancel — all state-changing.

## Connections

- Portal shell & index: [[00-Zepto-Atlas]] · [[00-Zepto-Atlas]] · master endpoint index [[Zepto-Endpoints]]
- Auth model & token: [[Auth-and-Access]] · scope rules: [[Read-Only-Guardrails]]
- **Tightest siblings** (same vendor lane, linked from the PO lifecycle): [[ASN]] (the shipment notices a PO's `/asn` sub-resource points at), [[RTV]] (returns reached via `/po/returns`), [[Release-Orders-Amendment-Requests]] (RO / amendment requests against POs).
- Downstream money view of received goods: [[Invoicing]] · [[Payments]]; bulk PO/GRN exports land in [[Vendor-Reports-Queue]]; the SKUs a PO references live in [[Catalog-Health]]; received qty reconciles against [[Stock-View-Inventory]].
