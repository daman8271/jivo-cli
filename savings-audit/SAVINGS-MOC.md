---
title: SAVINGS-MOC — JIVO cost-leakage audit
created: 2026-07-28
updated: 2026-07-28
project: jivo-cli
type: moc
tags: [savings-audit, moc]
---

# 💰 Savings Audit — Map of Content

> Goal #92: **save big lakhs**. 8 intelligence lenses × ~100 hypotheses over live SAP HANA (3 companies), payroll, and expenses. Every ₹ figure backed by SQL evidence; top findings adversarially re-derived.

**Status:** AUDIT CLOSED 2026-07-29. 8 finders (146 hypotheses, 68 findings) + 25 adversarial verifier runs across 3 rounds. Every material claim carries a verdict. Live dossier: https://g92-audit.vercel.app

## Lenses (evidence notes)
- [[vendor-money-stuck]] — advances/debits sitting with suppliers
- [[receivables-aging]] — overdue A/R + interest cost of locked cash
- [[duplicate-payments]] — bills entered twice, double payments, overpayments
- [[purchase-price-variance]] — same item bought at different prices
- [[dead-slow-stock]] — locked capital in non-moving inventory
- [[returns-leakage]] — credit-note/return-rate offenders
- [[payroll-leakage]] — TankhaPay attendance vs pay gaps
- [[expense-outliers]] — expense-head spikes, interest & bank charges

## ✅ Verified bankable — ₹8.17 Cr one-time/WC + ₹22.3 L/yr recurring

| Finding | ₹ verified | Next step |
|---|---:|---|
| [[finding-blessing-advertising-overdue]] | **₹3.11 Cr** | ₹29.66 L same-PAN set-off today; demand letter; stop supply |
| [[finding-wip-variance-july]] | **₹1.43 Cr** | 131,789 L of oil in stock at ₹0.00 — revalue BEFORE July close (TransType-162 route) |
| [[finding-receivables-named]] | **₹1.66 Cr** | AB Enterprises ₹64.4 L (legal, 7 days) · long tail ₹72.6 L (30-day clock) · Future Retail ₹23.8 L tax (before 15-Sep) · BSA real balance ₹4.7 L |
| [[finding-stock-discipline]] | **₹1.39 Cr** | Liquidate ₹98 L slow FG/RM; defer ₹41.5 L live POs; ghee PO is a GOOD BUY — leave it |
| [[finding-employee-floats]] | **₹42.8 L** | Per-head imprest caps on JWPL codes; halve top-10 floats |
| [[finding-no-invoice-vendors]] | ₹6.55 L | 7 stale advances — invoice or refund |
| [[finding-dup-payments-small]] | ₹4.73 L | Stop the unpaid duplicates before next payment run |
| [[finding-dormant-vendor-advances]] | ₹4.06 L | Balance-confirmation letters |
| [[finding-trade-spend-as-credit-notes]] | **₹14.5 L/yr** | GST credit notes for promo spend (to ₹47 L restructured) |
| [[finding-statutory-penalties]] | **₹7.8 L/yr** | Statutory payment calendar, named owner |

**Multiplier:** measured CC rate **8.25%** — releasing the ₹8.17 Cr ≈ ₹67 L/yr interest, on top ([[finding-cc-interest-conversion-rate]]).

## ❌ Killed in round 3 (arithmetic right, money absent)
[[finding-stock-discipline]] stale-POs ₹5.94 Cr (zero conversion in 17,093 receipts) · [[finding-inventory-valuation]] ₹3.37 Cr (OITW display artifact vs OINM) · [[finding-payroll-attendance]] ₹34 L/yr (mispunch days are real 9.1h workdays; ghost-employee claim a workbook artifact) · [[finding-gst-itc-reversals]] ₹71.5 L/yr (legally extinguished) · B S A ₹1.11 Cr (RECEIVED 16-Jul, on-account — see [[finding-receivables-named]])

## 🚩 Red flags — worth MORE than the savings (CFO/owner eyes)

- [[finding-off-spec-olive-oil]] — **₹8.21 Cr of "dark olive oil" that was never bought, sold, or moved**: six manually-keyed year-end entries debiting inventory / crediting COGS; the ₹6.99 Cr entry backdated 73 days ("AS PER HK VJI"); quantities reverse-engineered from round rupee targets; reject grade valued 1.91× prime grade. **₹3.89 Cr provably over-valued.** This is profit inflation, not slow stock.
- [[finding-hs-filling-advance]] — ₹2.90 Cr (86% of PO value) paid for Beverages bottling plant **before any delivery**, vendor has **no GSTIN in any company**, delivery 89 days overdue, ₹51.3 L GST input credit unclaimable until an invoice exists.
- [[finding-oil-returns-escalation]] — the "returns explosion" is largely **invoice recycling**: same consignment invoiced/credited/re-invoiced up to 5×. Fake sales + fake returns in the books; billing-discipline and GST-exposure issue.
- [[finding-advances-vs-open-bills]] — A/P is ~95% unreconciled since the 30-Sep-2024 go-live; the open-invoice report overstates payables and can trigger real double payments even though the flagged ₹4.05 Cr itself was float.

## 🚩 New red flags from round 3
- **₹1.41 Cr of GST input credit claimed from suppliers with no GSTIN in the ERP** + ₹52.1 L dead ITC asset ([[finding-gst-itc-reversals]])
- **AB Enterprises**: ₹14.04 Cr lifetime loose-canola sales to a GSTIN-less customer at near-zero recorded COGS; credit limit back-fitted to exposure+₹3 ([[finding-receivables-named]])
- **Unallocated receipts corrupt the debtor book** the same way unreconciled payments corrupt A/P — the B S A lesson ([[finding-receivables-named]])

## Round-1 verification notes (how the big illusions died)
[[verify-ap-subledger-not-reconciled]] (₹186 Cr → control obs) · [[verify-unlinked-credit-notes]] (₹25.8 Cr → ₹1.2 Cr) · [[verify-mangla-fixed-asset-advances]] + [[verify-05-anju-mangla-land-invoice]] (Bakharpur land capex, not leakage) · [[verify-04-mart-return-rate]] (₹9.91 Cr → ₹0.6 Cr) · [[verify-intercompany-stock-reversal]] (Oil↔Mart mirror, nets to zero)

Back-links: [[Chats-MOC]] · [[2026-07-28]]
