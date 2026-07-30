---
title: Inventory & FBA
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, seller, inventory-fba]
status: studied
read_only: true
---

# Inventory & FBA

**Portal:** Seller Central (3P) · **Section:** `seller/Inventory-FBA` · **Endpoints catalogued:** 7 (2 read-safe, 2 PROVEN live · 1 out-of-scope · 4 unknown/telemetry)

Manage Inventory (Manage FBA/MFN listings), inventory actions, stranded-inventory and auto-removal settings, inventory planning, and the FBA dashboard. The core inventory grid loads via a GraphQL POST (/myinventory/gql) held out of scope — the page shell and planning/stranded reads are GET.

## What it looks like (live, this run)

![02 inventory manage](../seller/sec-02-inventory-manage.png)
![03 inventory actions](../seller/sec-03-inventory-actions.png)
![23 legacy inventory hz](../seller/sec-23-legacy-inventory-hz.png)

*Captured live from JIVO Mart's Seller Central session, seller/sec-02-inventory-manage.png; seller/sec-03-inventory-actions.png; seller/sec-23-legacy-inventory-hz.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /inventoryplanning/check-unread-message | 1 | READ |
| ✅ | GET | sellercentral.amazon.in · /inventoryplanning/stranded-inventory/autoRemovalSettings | — | READ |

## Response shapes (full field lists, from live capture)

- **`/inventoryplanning/check-unread-message`** (1 fields): `hasMessage`

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| POST | sellercentral.amazon.in · /fba/dashboard/bff/graphql | READ_POST | app-issued POST read (GraphQL/RPC) — G0 forbids POST, gate k |

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| ? | sellercentral.amazon.in · /automatepricing/rules/listings/ | UNKNOWN |
| ? | sellercentral.amazon.in · /hz/inventory | UNKNOWN |
| ? | sellercentral.amazon.in · /myinventory/actions | UNKNOWN |
| ? | sellercentral.amazon.in · /myinventory/inventory | UNKNOWN |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

