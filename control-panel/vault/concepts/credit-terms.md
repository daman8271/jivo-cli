---
title: Credit Terms
type: concept
---
# Credit Terms (Payment Terms)

**Definition.** The SAP **payment-terms** assigned to a customer, governing how long they may take to pay. 14 distinct values in use — advance/immediate (`ADVANCE/CASH/0 DAYS`, `COD`, `CAD`, `20% ADVANCE`, `45 % ADV`, `LC 60`) and net-credit ladders `NET-01 … NET-30` (days).

Drives the receivables/credit screens: what is overdue ([[AR-aging]]), and how much credit a party should be allowed ([[required-credit-limit]]).

**Used by:** [[customer-master]], [[required-credit-limit]], [[open-payments]] · API [[customer-master]].
**Related:** [[AR-aging]], [[customer-aging]], [[channels]].
