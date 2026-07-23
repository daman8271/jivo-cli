---
title: Open POs
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /accounts/open-pos
section: Accounts
---

# Open POs

[[INDEX|JIVO EXIM]] › **Accounts** › Open POs

**Route:** `/accounts/open-pos`  ·  **Web:** `https://exim.jivo.in/accounts/open-pos`

## What this page does

Shows all open purchase orders from `GET /sap-sync/open-pos/` (about 18 live POs synced from SAP). Each row is a PO line: PO_NUMBER, PO_DATE, DUE_DATE, vendor (VENDOR_CODE/VENDOR_NAME, e.g. AWL AGRI or importer MIGASA ACEITES), the RM item (ItemCode like `RM0000003`, ITEM_NAME like MUSTARD LOOSE OIL), quantities in the PO's UOM (typically MTS) split into ORDERED_QTY, RECEIVED_QTY, and PENDING_QTY, plus UNIT_PRICE, the pending OPEN_VALUE in INR, and the receiving WAREHOUSE (e.g. BH-GJ).

## How it helps

Procurement and ops track undelivered oil purchases here: PENDING_QTY against DUE_DATE flags vendors running late, and OPEN_VALUE quantifies the money still committed per PO. It answers "what raw material is still due to arrive, from whom, at which warehouse" ahead of production planning.

## Backend endpoints

- [[endpoints/sap-sync_open-pos|`GET /sap-sync/open-pos/`]] — Open purchase orders (SAP).

## Key data & interactions

- PO line table: PO_NUMBER, PO_DATE, DUE_DATE, VENDOR_CODE, VENDOR_NAME, ItemCode, ITEM_NAME, WAREHOUSE, UOM
- Quantity columns: ORDERED_QTY, RECEIVED_QTY, PENDING_QTY (in MTS per the UOM field)
- Value columns: UNIT_PRICE and OPEN_VALUE (INR)
- Filter/sort by vendor, RM item, or due date; client-side (endpoint takes no query params)

## Related pages (same section)

- [[pages/exim-account|Oil Dr/Cr Outstanding]]
- [[pages/vendor-outstanding|Vendor Outstanding]]
- [[pages/customer-outstanding|Customer Outstanding]]
- [[pages/customer-aging|Customer Aging]]
- [[pages/open-ars|Open ARs]]
- [[pages/open-aps|Open APs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
