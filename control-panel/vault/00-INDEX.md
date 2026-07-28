---
title: 00 — INDEX (Map of Content)
type: moc
tags: [jivo, control-panel, moc]
---
# Jivo Group — Control Panel · Map of Content

Internal **Django ERP/analytics dashboard** for **JIVO Wellness**, reading live data out of **SAP Business One**. Server-rendered HTML shells hydrated by `/…/api/` JSON, behind a Django **session cookie + CSRF**. Base `http://103.89.45.75:9080`. ⚠️ **Live production — READ-ONLY.**

- **Start here:** [[architecture]] — stack, auth model, the three call patterns, endpoint namespacing, read-only posture.

---
## Pages — by sidebar section

### Control Panel
| Page | Route |
|---|---|
| [[control-panel]] | `/` |

### Sales
| Page | Route |
|---|---|
| [[sales-dashboard]] (Sales Channel Dashboard / Realise) | `/realise/` |
| [[compare-sales]] | `/realise/compare-sales/` |
| [[sales-cn]] (Sales vs Credit Notes) | `/realise/sales-cn/` |
| [[hidden-sales]] | `/realise/hidden-sales/` |
| [[sales-flow]] (Sales Document Flow) | `/realise/sales-flow/` |
| [[dispatch-details]] | `/realise/dispatch-details/` |
| [[realise-calculator]] | `/realise/realise-calculator/` |
| [[rate-list]] | `/realise/rate-list/` |

### Accounts
| Page | Route |
|---|---|
| [[customer-aging]] | `/realise/customer-aging/` |
| [[required-credit-limit]] | `/realise/required-credit-limit/` |
| [[open-payments]] | `/realise/open-payments/` |
| [[claims]] | `/realise/claims/` |

### Inventory & Production
| Page | Route |
|---|---|
| [[stock-available]] | `/inventory/stock-available/` |
| [[non-moving-stock]] (Non Moving Stock) | `/inventory/non-inventory/` |
| [[oih-vs-stock]] ⚠️ nav 404s | `/inventory/oih-vs-stock/` |
| [[production-plan]] | `/inventory/production/` |
| [[daily-production]] | `/inventory/daily-production/` |
| [[reconciliation]] (Wellness–Mart Recon) | `/inventory/reconciliation/` |

### Master Data
| Page | Route |
|---|---|
| [[customer-master]] | `/realise/customer-master/` |

### Admin
| Page | Route |
|---|---|
| [[users]] (User Management) | `/users/` |

---
## API endpoints — by area
Full call semantics in [[architecture]]. **Bold = write/mutating or gated — documented, never executed.**

### A. Shared Realise API — `/realise/api/*`
Serves Control Panel + Sales + Accounts.

**Reads — POST (JSON):** [[sales-data]] · [[sales-cn]] · [[hidden-sales]] · [[sales-flow]] · [[sales-flow-open-items]] · [[dispatch-details]] · [[compare-docs]] · [[open-payments]] · [[drill-down]] · [[historical-realise]] · [[beverages-data]] · [[export-xlsx]]

**Reads — GET (XHR / query):** [[customer-master]] · [[customer-aging-oil-ar]] · [[customer-aging-mart]] · [[customer-aging-beverages]] · [[claims]] · [[rate-list]] · [[realise-calculator-items]] · [[targets]] · [[flex-targets]] · [[segment-targets]] · [[target-nodes]] · [[channel-targets]] · [[channel-detail-docs]] · [[oih-breakdown]] · [[order-in-hand]] · [[order-in-hand-rows]] · [[commodity-oih-rows]] · [[sales-pulse]] · [[beverages-docs]] · [[health]] · [[export-excel]] · [[export-aging-detail]] · [[realise-calculator-export]]

**Writes / gated (skip):** **[[save-targets]]** · **[[save-closing-remark]]** · **[[rate-list-save]]** · **[[rate-list-delete]]** · **[[realise-calculator-upload]]** · **[[realise-calculator-order-upload]]** · **[[aging-remark]]** · **[[credit-lock-unlock]]** · **[[verify-pin]]**

### B. Inventory API — `/inventory/<page>/api/*`
[[inventory-stock-available-data]] · [[inventory-non-inventory-data]] · [[inventory-non-inventory-drill]] · [[inventory-production-plan]] · [[inventory-production-feasibility]] · [[inventory-production-fg-list]] · [[inventory-production-warehouses]] · [[inventory-daily-production-data]] · [[inventory-reconciliation-data]] · [[inventory-reconciliation-ledgers]]

### C. Top-level — `/api/*`
**[[cogs]]** (OTP-gated COGS/margin) · **[[users]]** (admin write: save/delete)

---
## Concepts

### KPIs & metrics
[[REALISE]] · [[OIH]] · [[BAL]] · [[TGT]] · [[DONE]] · [[DRR]] · [[COGS]]

### Channels & segments
[[channels]] · [[GT]] · [[MT]] · [[ROI]] · [[ECOM]] · [[segments-oils-beverages]] · [[OILS]] · [[BEVERAGES]] · [[COMMODITY]] · [[Main Group]]

### Finance & receivables
[[AR-aging]] · [[credit-terms]] · [[credit-note]]

### Operations & master data
[[oms]] · [[warehouses]] · [[wellness-mart-reconciliation]]
