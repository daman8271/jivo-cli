---
title: Vendor-Purchase-Orders
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, vendorhub, read-only]
status: studied
---

# Vendor-Purchase-Orders

> ⚠️ READ-ONLY. Vendor Hub 1P purchase orders, PO workbook download, GRN.

**Endpoints in this section:** 1 — 1 read-safe (READ/READ_FILE), 0 write/export (out of scope), 0 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/purchase-orders-summary` | — | READ |

## PROVEN detail & live findings (JIVO MART, this session)

**PROVEN-READ (GET, replayed 200 live this session):**

| Verb | Path | Result | Posture |
|---|---|---|---|
| GET | `vendor/purchase-orders?…&status&from_date&thru_date&sort_column=order_date` | live grid; the constructed GET returned 0 (wrong scope) but the **PO dashboard shows the true tallies** below | READ |
| GET | `vendor/purchase-order-download?id=<PO>` | per-PO Excel workbook (the real PO source; the page's "Download List" only exports the table) | READ_FILE |

**Live finding (VERIFIED via the browser walk — screenshots `sec-05`/`sec-06` in [[Flipkart-Live-Walk]]):**
JIVO MART (`VEN23097`) is an **active, high-volume** 1P vendor: **1 Open to fulfil (3.3K units, ₹6.49 L),
~750 Completed (75 pages × 10), ~570 Cancelled (57 pages × 10), 0 New-in-2-days, 0 Pending-Ack, 0
Expiring**. Sample completed POs `FDGN07597805`/`FDGN07589834`/`FBSWN07587432` — Category **Gourmet**,
FK warehouse "Delhi Grocery NCR Warehouse 1", vendor warehouse West Delhi VS58039, Fulfilment
"Merchandising". ⚠️ The constructed `GET /vendor/purchase-orders` earlier returned 0 (wrong
scope/params) — the app's own dashboard calls give the truth; **the live walk is authoritative.**
The other 8 vendor entities are **PENDING_AUTH** (vendor switch is `POST /select-vendor`, not authored).

**Filters/dimensions:** `status` (new / …), `from_date`, `thru_date`, `order` (asc/desc),
`sort_column` (order_date …), `page_number`, `page_size`, warehouse (`VS58039`, `VS96323011`),
vendor (the 6 vendors). GRN and the PO summary tiles (`purchase-orders-summary`) need warehouse+date
params (bare call → 400 `PURCHASE_ORDERS_SUMMARY_ERROR`) — param shape PENDING_AUTH.

**Out of scope (writes):** PO accept / acknowledge / schedule-appointment, ASN create, GRN actions —
all catalogued, never fired.

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
