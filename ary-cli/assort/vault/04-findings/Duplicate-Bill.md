---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-29
confidence: high
system: ARY / FusionERP8
---

# Flagged for Accounts — a probable duplicate bill

Reported, not acted on. This CLI cannot write, and nobody asked for a correction.

## The two identical bills

Customer 002CM (Hunger Heroes), 11 May 2026, four bills keyed between 17:49 and 18:57:

| Serial | Bill | Voucher time | Entered | Lines | Value |
|---|---|---|---|---|---|
| 2002747.0001 | Hp1 | 17:49 | 17:50 | 59 | ₹5,45,332.29 |
| 2002751.0001 | Hp2 | 18:54 | 18:55 | 59 | **₹5,91,370.12** |
| 2002752.0001 | Hp3 | 18:56 | 18:56 | 59 | **₹5,91,370.12** |
| 2002753.0001 | Hp4 | 18:57 | 18:57 | 59 | ₹5,50,114.12 |

**Hp2 and Hp3 are identical to the paisa on the same 59 lines, entered one minute apart.**
That looks like a double-keyed bill worth **₹5.91 lakh**. ARY has no bill-cancellation
document, so a duplicate can only be reversed by a sale return — and no matching return
exists. Reported, not acted on: this CLI cannot write, and nobody asked for a correction.

## See also

- [[Institutional]] — the customer is the langar feeding programme
