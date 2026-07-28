---
title: OIH vs Stock
route: /inventory/oih-vs-stock/
type: page
endpoints: []
tags: [jivo, control-panel, inventory]
---
# OIH vs Stock

## Purpose
Intended to compare **Order In Hand ([[OIH]]) — unfulfilled open sales demand — against current finished-goods stock**, so ops can see where committed orders exceed (or fall short of) available stock and prioritise production. See [[OIH]].

## Status — route not implemented under /inventory/
- **`/inventory/oih-vs-stock/` → HTTP 404** (Django "Not Found"). There is **no** inventory-domain view, template, or `…/api/` endpoint for this route. The saved recon file `inventory__oih-vs-stock.html` is just the 404 body.
- **However, the sidebar link actually points to `/realise/oih-vs-stock/`**, and that route **is live (HTTP 200, a full page)**. The working OIH-vs-Stock report is served from the **realise** app, not `/inventory/`.
- User group membership confirms the feature exists and is permissioned: `oih_vs_stock_viewer` / `can_oih_vs_stock: true` on the logged-in admin.

## What it shows
Not documented here — the functioning page lives under the **realise** domain at `/realise/oih-vs-stock/` (outside the inventory slice). Its data almost certainly comes from the shared Realise API OIH endpoints (`/realise/api/order-in-hand/`, `oih-breakdown/`, `commodity-oih-rows/`) combined with stock — see the realise-domain docs and [[OIH]].

## Data sources
- None under `/inventory/` (route 404s). The real page uses `/realise/`-side OIH endpoints — document under the realise/OIH domain, not here.

## Notes / gotchas
- **Do not link the inventory route as a data source** — it 404s. The nav label "OIH vs Stock" resolves to `/realise/oih-vs-stock/`.
- Left in the inventory slice only because the sidebar groups it under **Inventory & Production**; the implementation is realise-side.

## Related
- [[OIH]], [[stock-available]], [[production-plan]]
