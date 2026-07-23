---
title: "Jivo Mart App-Model — Knowledge Base"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: map
tags: [jivogpt, factory-cli, app-model]
---

# Jivo Mart App-Model — Knowledge Base

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].

Deep per-section study of the `factory.jivo.in` factory app, scoped to the **Jivo Mart (JIVO_MART)** tenant only. Live-verified 2026-06-30.

**Essence:** `factory.jivo.in` is a factory-floor operating system and SAP Business One companion, multi-tenant across Jivo Oil (manufacturer), Jivo Beverages, and Jivo Mart. For **Jivo Mart — the retail/dispatch arm** — it runs as a finished-goods receiving-and-dispatch hub: pre-barcoded cartons arrive from Jivo Oil over an intercompany rail, are held/relayed across 31 warehouses, then scanned onto trucks and gated out against SAP invoices. Gate, vehicle, barcode, dispatch and WMS-read are data-rich; production (MES), maintenance (CMMS), inbound-QC and GRPO-posting are built but largely dormant.

**Start here:**
- [[CLI/factory-cli/app-model/00-OVERVIEW|00-OVERVIEW]] — whole-app model: factory flow, section map, cross-section data graph, SAP-B1 integration, heavy-vs-idle analysis
- [[CLI/factory-cli/app-model/_route-map|_route-map]] — UI route tree per section

## Sections
- [[CLI/factory-cli/app-model/sections/01-admin|Admin]]
- [[CLI/factory-cli/app-model/sections/02-dashboards|Dashboards]]
- [[CLI/factory-cli/app-model/sections/03-dispatch|Dispatch]]
- [[CLI/factory-cli/app-model/sections/04-gate|Gate]]
- [[CLI/factory-cli/app-model/sections/05-vehicle-management|Vehicle Management]]
- [[CLI/factory-cli/app-model/sections/06-quality-control|Quality Control]]
- [[CLI/factory-cli/app-model/sections/07-grpo|GRPO]]
- [[CLI/factory-cli/app-model/sections/08-production|Production]]
- [[CLI/factory-cli/app-model/sections/09-maintenance|Maintenance]]
- [[CLI/factory-cli/app-model/sections/10-warehouse|Warehouse]]
- [[CLI/factory-cli/app-model/sections/11-wms|WMS]]
- [[CLI/factory-cli/app-model/sections/12-barcode|Barcode]]
- [[CLI/factory-cli/app-model/sections/13-notifications|Notifications]]

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
