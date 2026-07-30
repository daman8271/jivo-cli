---
title: Catalog SPIN Management
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, brand, brand]
status: studied
---


# Catalog SPIN Management

> Product catalogue: SPIN attributes, change requests and approvals.

**Catalog** (`/im-catalog`) is the `imCatalogClient` remote and the most
surprising find of the study: JIVO can read and (with permission) drive its own
Instamart product catalogue from here. It has three routes — my catalogue
(`/im-catalog`), **approvals** (`/im-catalog/approvals`) and **update requests**
(`/im-catalog/update-requests`) — over a SPIN-change-request workflow.

Reads: `list_spins`, `get_spin_details`, `get_spin_metrics`,
`list_spin_change_requests`, `get_spin_change_workflow_details`,
`get_spin_change_attribute_details`, `search_brands`, `search_categories`.

Live: **43 SPINs total** for Jivo Wellness (10 on the first page) and **9** for
Jivo Mart. `CATALOG_FULL_ROLLOUT` is **true**.

**Endpoints in this section:** 14 (8 read, 3 write/export, 3 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/v1/get_spin_change_attribute_details` | `GET_SPIN_CHANGE_ATTRIBUTE_DETAILS` | documented (not observed live) | call site .post() on GET_SPIN_CHANGE_ATTRIBUTE_DETAILS |
| READ | POST | `brand-portal-service-http.swiggy.com/v1/get_spin_change_workflow_details` | `GET_SPIN_CHANGE_WORKFLOW_DETAILS` | documented (not observed live) | call site .post() on GET_SPIN_CHANGE_WORKFLOW_DETAILS |
| READ | POST | `brand-portal-service-http.swiggy.com/v1/get_spin_details` | `GET_SPIN_DETAILS` | documented (not observed live) | call site .post() on GET_SPIN_DETAILS |
| READ | POST | `brand-portal-service-http.swiggy.com/v1/get_spin_metrics` | `GET_SPIN_METRICS` | **PROVEN LIVE 200** | call site .post() on GET_SPIN_METRICS | live: ['POST'] -> [200], 514B |
| READ | POST | `brand-portal-service-http.swiggy.com/v1/list_spin_change_requests` | `LIST_SPIN_CHANGE_REQUESTS` | **PROVEN LIVE 200** | call site .post() on LIST_SPIN_CHANGE_REQUESTS | live: ['POST'] -> [200], 79B |
| READ | POST | `brand-portal-service-http.swiggy.com/v1/list_spins` | `LIST_SPINS` | **PROVEN LIVE 200** | call site .post() on LIST_SPINS | live: ['POST'] -> [200], 8382B |
| READ | POST | `brand-portal-service-http.swiggy.com/v1/search_brands` | `SEARCH_BRANDS` | documented (not observed live) | call site .post() on SEARCH_BRANDS |
| READ | POST | `brand-portal-service-http.swiggy.com/v1/search_categories` | `SEARCH_CATEGORIES` | **PROVEN LIVE 200** | call site .post() on SEARCH_CATEGORIES | live: ['POST'] -> [200], 399B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| POST | `brand-portal-service-http.swiggy.com/v1/create_spin_change_request` | `CREATE_SPIN_CHANGE_REQUEST` | WRITE — call site .post() on CREATE_SPIN_CHANGE_REQUEST |
| POST | `brand-portal-service-http.swiggy.com/v1/generate_signed_url` | `GENERATE_SIGNED_URL` | EXPORT — call site .post() on GENERATE_SIGNED_URL |
| PUT | `brand-portal-service-http.swiggy.com/v1/update_spin_change_workflow` | `UPDATE_SPIN_CHANGE_WORKFLOW` | WRITE — call site .put() on UPDATE_SPIN_CHANGE_WORKFLOW |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

| METHOD | Host · Path | Const | Why it stays denied |
|---|---|---|---|
| POST | `brand-portal-service-http.swiggy.com/v1/reassign_spin_change_request` | `REASSIGN_SPIN_CHANGE_REQUEST` | call site .post() on REASSIGN_SPIN_CHANGE_REQUEST |
| POST | `brand-portal-service-http.swiggy.com/v1/transition_spin_change_request` | `TRANSITION_SPIN_CHANGE_REQUEST` | call site .post() on TRANSITION_SPIN_CHANGE_REQUEST |
| POST | `brand-portal-service-http.swiggy.com/v1/validate_spin_change_request` | `VALIDATE_SPIN_CHANGE_REQUEST` | call site .post() on VALIDATE_SPIN_CHANGE_REQUEST |

## Gotchas

- The `/im-catalog/update-requests` route was **missed in walk pass 1** because
  my own transport gate blocked the page navigation — the route string contains
  the word "update". Fixed under AMENDMENT-04 and walked in a later pass. Logged
  rather than quietly dropped.
- `create_spin_change_request`, `reassign_spin_change_request`,
  `update_spin_change_workflow` are writes against JIVO's own catalogue —
  excluded. `transition_` and `validate_` are UNKNOWN → denied.
- `generate_signed_url` is an upload enabler → EXPORT, excluded.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-39-im-catalog-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-39-im-catalog-Jivo-Mart-Pvt-Ltd-.png)
- `sec-40-im-catalog-approvals-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-40-im-catalog-approvals-Jivo-Mart-Pvt-Ltd-.png)
- `sec-59-im-catalog-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-59-im-catalog-Jivo-Wellness-.png)
- `sec-60-im-catalog-approvals-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-60-im-catalog-approvals-Jivo-Wellness-.png)
- `sec-61-im-catalog-update-requests-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-61-im-catalog-update-requests-Jivo-Wellness-.png)
- `sec-79-im-catalog-Jivo-.png`

  ![screenshot](../captures/walk2/sec-79-im-catalog-Jivo-.png)
- `sec-80-im-catalog-approvals-Jivo-.png`

  ![screenshot](../captures/walk2/sec-80-im-catalog-approvals-Jivo-.png)
- `d33-im-catalog-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d33-im-catalog-Jivo-Mart-Pvt-Ltd-.png)
- `d34-im-catalog-approvals-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d34-im-catalog-approvals-Jivo-Mart-Pvt-Ltd-.png)
- `d35-im-catalog-update-requests-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d35-im-catalog-update-requests-Jivo-Mart-Pvt-Ltd-.png)
- `d52-im-catalog-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d52-im-catalog-Jivo-Wellness-.png)
- `d53-im-catalog-approvals-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d53-im-catalog-approvals-Jivo-Wellness-.png)
- `d54-im-catalog-update-requests-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d54-im-catalog-update-requests-Jivo-Wellness-.png)
- `d71-im-catalog-Jivo-.png`

  ![screenshot](../captures/walk4/d71-im-catalog-Jivo-.png)
- `d72-im-catalog-approvals-Jivo-.png`

  ![screenshot](../captures/walk4/d72-im-catalog-approvals-Jivo-.png)
- `d73-im-catalog-update-requests-Jivo-.png`

  ![screenshot](../captures/walk4/d73-im-catalog-update-requests-Jivo-.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
