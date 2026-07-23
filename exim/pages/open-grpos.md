---
title: Open GRPOs
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /contracts/open-grpos
section: Domestic Contracts
---

# Open GRPOs

[[INDEX|JIVO EXIM]] › **Domestic Contracts** › Open GRPOs

**Route:** `/contracts/open-grpos`  ·  **Web:** `https://exim.jivo.in/contracts/open-grpos`

## What this page does

The production page lists goods-receipt POs still open in SAP through `GET /sap_sync/open-grpos/`. Each row shows the GRPO Number, Vendor Ref No, the SAP user who booked it (User Name), Vendor Name, receiving Warehouse (e.g. BH-GJ), and Pending Days since receipt. The route belongs to the mutating underscore sync namespace, so JivoGPT documents the page but does not call the endpoint.

## How it helps

An open GRPO means goods were received but the vendor invoice has not been booked against it in SAP, which blocks contract closure and distorts payables. Ops and accounts open this page to chase aging receipts (Pending Days) with the responsible SAP user and vendor before they pile up.

## Backend endpoints

- [[endpoints/sap_sync_open-grpos|`GET /sap_sync/open-grpos/`]] — Open goods-receipt POs (SAP).

## Key data & interactions

- Columns: GRPO Number, Vendor Ref No, User Name, Vendor Name, Warehouse, Pending Days.
- Pending Days is the aging metric; sort by it to surface the oldest open receipts.
- The page pulls straight from SAP via `/sap_sync/open-grpos/`; refresh may trigger a sync, so the endpoint is excluded under [[HARD-RULE]].

## Related pages (same section)

- [[pages/domestic-contracts|Domestic Contracts (FY 2025-26)]]
- [[pages/domestic-2627|Domestic Contracts (FY 2026-27)]]


Linked: [[INDEX]] · [[API-INVENTORY]]
