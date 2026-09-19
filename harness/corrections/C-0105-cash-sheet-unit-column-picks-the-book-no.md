---
id: C-0105
date: 2026-09-19
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [cash-voucher]
---

# Cash sheet Unit column picks the book, not the GRPO's book

## Wrong
Entered vouchers 460 and 461 in Beverages because their PO 826228033 and GRPOs 2026088342/2026088343 were raised on the Beverages imprest card, although the cash sheet marked both 'Common'.

## Right
The cash sheet's Unit column decides the company book - Common/Canola = Oil, Wg = Beverages. A GRPO raised in the wrong book does not move the voucher; book it in the sheet's book with the expense head read off that GRPO, and hand the stranded GRPO back to the factory to close.

## Evidence
Daman, 2026-09-19: 'the 460 and 461 were supposed to be in oil cuz they were the vouchers for oil... it was also mentioned in the sheet which they gave you.' Beverages draft 16335 deleted; re-entered in Oil as draft 57468 Rs 2,250 on ORGV000465.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Cash voucher: the sheet's Unit column picks the BOOK (Common/Canola = Oil, Wg = Beverages), even when the PO and GRPO were raised in another company. Take the head off that GRPO; the misplaced GRPO is a factory cleanup.
