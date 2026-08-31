---
id: C-0061
date: 2026-08-31
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# A transporter bill can span two companies — each bilty is booked in its own book

## Wrong
Every bilty on one transporter's bill belongs to the same company, so the GRPOs total to the bill footer.

## Right
The company follows the SALE INVOICE on the bilty, not the bill it is printed on. A bill of Oil bilties can carry one Beverages (or Mart) bilty; that one is booked in the Beverages book, against the Beverages CardCode for the same transporter, as its own GRPO — never merged into the Oil document. Nothing on the paper announces it: the only way to see it is to look up EVERY invoice number on the bill, not a sample. Expect each company's GRPO total to be LESS than the bill footer, and the two to add back to it.

## Evidence
Daman 2026-08-31 on MAHAVIR bill 678: 14 bilties Oil, but GR 3670 (ROHINI, freight 3,000 + labour 380) is invoice 626077983 = RM HYPERMARKET, present only in JIVO_BEVERAGES_HANADB. Oil drafts 55600-55613 total 72,440; 72,440 + 3,380 = 75,820 = the bill's G.TOTAL. Same transporter, three CardCodes: VENDA001523 Oil / VENDA001010 Mart / VENDA001214 Bev.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Transporter bill: look up EVERY invoice number to find its company; a bilty whose sale invoice lives in another book is keyed in THAT book against that transporter's CardCode there. Never merge two companies into one GRPO.
