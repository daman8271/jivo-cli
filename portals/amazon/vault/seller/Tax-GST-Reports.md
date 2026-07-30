---
title: Tax & GST Reports
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, seller, tax-gst-reports]
status: studied
read_only: true
---

# Tax & GST Reports

**Portal:** Seller Central (3P) · **Section:** `seller/Tax-GST-Reports` · **Endpoints catalogued:** 1 (1 read-safe, 1 PROVEN live · 0 out-of-scope · 0 unknown/telemetry)

GST On-Demand Reports (MTR B2B / B2C, STR) — the one Seller Central surface JIVO's ~ecomcliauto automation actually touches (flows 21/22). The report-history list is a GET read; requesting a report is a WRITE (enqueue, G2).

## What it looks like (live, this run)

![16 gst ondemand reports](../seller/sec-16-gst-ondemand-reports.png)

*Captured live from JIVO Mart's Seller Central session, seller/sec-16-gst-ondemand-reports.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /fba/gstreports/report-history | — | READ |

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

_None catalogued in this section._

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

