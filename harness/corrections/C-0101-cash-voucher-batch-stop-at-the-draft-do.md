---
id: C-0101
date: 2026-09-19
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [cash-voucher]
---

# Cash-voucher batch: stop at the draft, do not submit

## Wrong
Built ten cash-voucher A/P drafts and ran add-draft on all of them the same session, sending them to Bhawani before the operator had seen the list.

## Right
A cash-voucher batch is held at the draft and shown to the operator first. Once a draft is in the approval queue SAP will not delete it, will not let its party or document type change, and will not let a line be removed - so every later correction has to be worked around instead of simply rebuilt.

## Evidence
Daman, 2026-09-19, asked whether to hold the batch: 'Hold the batch at draft, wait for my approval.' Measured the same day: DELETE Drafts(57455) and Drafts(57462) both refused with [SAP -10] 'Cannot remove drafts as Draft No. N is in approval processes'; PATCH CardCode refused with [SAP -2028].

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Cash vouchers: build the drafts, show the operator the list, and WAIT for their word before add-draft. A draft in the approval queue cannot be deleted, re-partied or shortened - corrections after that point are expensive.
