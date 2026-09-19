---
id: C-0102
date: 2026-09-19
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [cash-voucher]
---

# Finding a cash voucher's GRPO: every card, and match on the bill number

## Wrong
Listed open GRPOs only on the ORGV imprest cards and matched them by the gate number read off phone scans, so four GRPOs raised on vendors' own cards were missed and vouchers 467/472/473/475 were reported as having none.

## Right
A cash voucher's GRPO may sit on the supplier's own card, not the imprest card. Search open GRPOs across every card in all three books, and match on the bill reference in NumAtCard, which is exact - handwritten gate numbers on phone scans misread easily (634 read as 684, 675 as 678).

## Evidence
2026-09-19, bunch 45939: PO 220826164 carried GRPOs 26731 (bill 1240, G.no.634), 26733 (bill 1262, G.no.675) and 26732 (bill 464, G.no.677) on VENDA001090 ASHOK KITAB GHAR; 26734 (bill 590/07-09-26, G.no.667) on VENDA001182 BAJAJ ELECTRICAL. All four matched their vouchers exactly on NumAtCard.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Hunting a cash voucher's GRPO: search open GRPOs on EVERY CardCode in all three books, not just the ORGV imprest cards, and match on the bill number in OPDN.NumAtCard - never on the handwritten gate number off a scan.
