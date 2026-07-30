---
title: Homepage & Casino Widgets
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, platform, homepage-widgets]
status: studied
read_only: true
---

# Homepage & Casino Widgets

**Portal:** Seller Central (3P) · **Section:** `platform/Homepage-Widgets` · **Endpoints catalogued:** 3 (2 read-safe, 1 PROVEN live · 0 out-of-scope · 1 unknown/telemetry)

The Seller Central home shell — the 'Casino' widget framework that renders the KPI tiles (Open Orders, Buyer Messages, Featured Offer %, Payments, IPI, Ad Sales, Account Health, STEP). The tile VALUES load via /homepage/casino/data (POST) held out of scope; the shell, async-card GETs, seller-news and priority-action reads are captured.

## What it looks like (live, this run)

![01 home dashboard](../seller/sec-01-home-dashboard.png)

*Captured live from JIVO Mart's Seller Central session, seller/sec-01-home-dashboard.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /homepage/casino/cards/content/async-card/ | — | READ |
| · | GET | sellercentral.amazon.in · /home | — | READ |

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

_None catalogued in this section._

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| ? | sellercentral.amazon.in · /homepage/knowhere/events/record | NOISE |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

