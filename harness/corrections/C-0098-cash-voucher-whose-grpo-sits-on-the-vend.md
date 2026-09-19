---
id: C-0098
date: 2026-09-19
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [cash-voucher]
---

# Cash voucher whose GRPO sits on the vendor's card

## Wrong
Booked vouchers 467/472/473/475 as typed expense lines on Arvinder's imprest card because their GRPOs were on ASHOK KITAB GHAR's and BAJAJ ELECTRICAL's cards, leaving those GRPOs open.

## Right
When a cash voucher's GRPO was raised on the real vendor's card, the A/P invoice is made to that vendor (copied from the GRPO, so the GRPO closes), and a separate journal voucher then moves it off the cash holder's float: Dr the vendor, Cr the FACTORY IMPREST card.

## Evidence
Daman, 2026-09-19: 'Enter it to the vendor and raise a JV to take it off his float' and, for voucher 463 whose A/P was already posted on H M PLASTICS (OPCH 51358, Rs 2,596): 'There is already an entry in H M Plastic, u just have to pass JV in Arvinder sir. For future reference, book the invoice and pass JV.' JV 6881 created 2026-09-19.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Cash voucher whose GRPO is on the VENDOR's card: book the A/P to that vendor as a GRPO copy, then pass a JV (Dr vendor / Cr FACTORY IMPREST) to take it off the holder's float. Never retype it on the imprest card.
