---
title: AR Aging
type: concept
---
# AR Aging (Receivables Aging)

**Definition.** The **accounts-receivable aging** of a customer's balance due, split into overdue buckets: `b0_30 / b31_60 / b61_90 / b91_120 / b121` days. `0–30 = current`, `121+ = seriously overdue`; the buckets sum to Balance Due. Tracked separately for oil-AR, mart and beverages.

**Used by:** [[customer-aging]], [[open-payments]], [[required-credit-limit]] · APIs [[customer-aging-oil-ar]], [[customer-aging-mart]], [[customer-aging-beverages]], [[export-aging-detail]].
**Related:** [[credit-terms]], [[credit-note]], [[REALISE]].
