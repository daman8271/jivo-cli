---
title: BAL — Balance to Target
type: concept
---
# BAL (and variants)

Family of "gap to monthly target" measures shown on the Sales dashboard.

- **BAL** — balance still to achieve = `TGT − DONE` (see [[TGT]], [[DONE]]).
- **BAL W/O OIH** — balance remaining *after* subtracting the open order book = `TGT − DONE − OIH` (what still needs fresh orders). See [[OIH]].
- **BAL RLZ** — the realisation (₹/L) required on the remaining balance to hit the target value.
- **OIH RLZ** — the realisation (₹/L) already locked inside the [[OIH]].

**Used by:** [[sales-dashboard]], [[control-panel]] · APIs [[sales-data]], [[targets]], [[oih-breakdown]].
**Related:** [[REALISE]], [[TGT]], [[DONE]], [[OIH]].
