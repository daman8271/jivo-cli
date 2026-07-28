---
title: COGS
type: concept
---
# COGS — Cost of Goods Sold

**Definition.** Landed cost of the goods sold — the basis for gross-margin / P&L views (net sales − COGS = gross margin).

⚠️ **Sensitive & OTP-gated.** The `/api/cogs/` endpoint requires `param_type` + a one-time `otp`; it is **not** part of the open `/realise/api/*` surface and must never be bypassed — document only.

**Used by:** [[control-panel]] (P&L cards) · API [[cogs]] (OTP-gated), [[verify-pin]] (PIN/OTP gate).
**Related:** [[REALISE]], [[OILS]], [[BEVERAGES]].
