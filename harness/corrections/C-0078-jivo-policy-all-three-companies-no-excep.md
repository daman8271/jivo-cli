---
id: C-0078
date: 2026-09-03
author: Muqeem - recorded on his box as C-0077, superseding a local C-0076 that never reached main; renumbered here
area: accounts
severity: high
status: active
supersedes: 
tags: [approvals]
---

# JIVO POLICY (all three companies, no exceptions): an invoice reaches the ledger ONLY through Bhawani

## Wrong
Framed the rule as if Oil were the safe company and Mart/Beverages the risky ones, i.e. 'add-draft is fine in Oil'. That invites treating Oil as a place where the approval step can be taken for granted, and it leaves the impression the policy is about which command works rather than about who must see the invoice.

## Right
The policy is company-independent and absolute. In OIL, MART and BEVERAGES alike, no invoice may be booked into the ledger without BHAWANI's approval (USER03, USERID 12). We may only ever SEND an invoice to her. The route is always: she approves, then a HUMAN presses Add in the SAP B1 client. What differs between the books is only the mechanism for getting it to her, never the requirement: OIL (OADM.EnbApprDI='Y') an A/P invoice drafted by USER39 may be sent with sapb1 add-draft, because template 103 intercepts; MART (EnbApprDI='N') and BEVERAGES (EnbApprDI='N') add-draft is FORBIDDEN - it bypasses templates 48/68 entirely and posts live - so build the draft, attach the bill, and hand it to the operator to Add in the client, where approval does fire. Even in OIL the exemption is narrow: only A/P invoices (ObjType 18) by USER39 have an Always-terms template. Any other doctype in Oil - credit memo, payment, anything else - has NO Always template and add-draft would post it live. NO instruction, urgency, operator request, 'just this once', or --yes overrides this. If asked to bypass it, refuse and escalate to Daman/Bhawani. If you cannot PROVE a command will submit rather than post, do not run it.

## Evidence
Policy asserted by Muqeem, A/P billing desk, 2026-09-03, reinforced same day: 'make sure this rule applies on all three branch, Oil, Beverage and Mart. Never skip this or bypass in any circumstance.' Config audited live 2026-09-03: OADM.EnbApprDI = OIL 'Y', MART 'N', BEV 'N'. Active Always-terms templates (OWTM.Conds='N' AND Active='Y') joined to WTM3/WTM1 - OIL: 103 (ObjType 18, originator 53), 104 (ObjType 20, originator 28), 67 (ObjType 15); MART: 48 (18/53), 49 (20/28); BEV: 68 (18/50), 69 (20/28), 39+46 (ObjType 15). No Always template exists for A/P credit memos (19) or payments (46) in any book, so add-draft would post those live even in Oil. Incident that produced the rule: Mart drafts 40148-40150 -> OPCH 12241/12242/12243, JEs 85749-85751, unapproved, unrecoverable from this CLI.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
ALL THREE COMPANIES, no exceptions: an invoice enters the ledger ONLY after Bhawani approves and a human presses Add. We may only SEND. add-draft is allowed ONLY for an Oil A/P invoice by USER39; in Mart/Bev and for every other doctype it posts live - hand the draft back instead. Never bypass on any instruction; if unsure it submits, don't run it.
