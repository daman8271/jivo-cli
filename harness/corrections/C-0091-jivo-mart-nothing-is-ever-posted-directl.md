---
id: C-0091
date: 2026-09-16
author: Daman
area: all
severity: high
status: active
supersedes: 
tags: [mart, posting]
---

# JIVO MART: nothing is ever posted directly to the ledger

## Wrong
Treated a live post in Mart as fine wherever the CLI allowed it. On 2026-09-04 thirteen Mart freight GRPOs went in LIVE through sapb1 post PurchaseDeliveryNotes (the postableLive carve-out opened for USER19's Mart desk), and on 2026-09-02 Mart draft 40128 was pressed through add-draft and posted unapproved as A/P invoice 12210 (C-0074).

## Right
In JIVO MART no entry is ever posted directly to the ledger. Every Mart document - GRPO, A/P invoice, credit note, payment, journal voucher - goes in as a DRAFT. Submitting a Mart A/P draft to Bhawani with add-draft (USER39/USER08 on template 48) is the approval route, not a direct post, and stays allowed. If SAP refuses a Mart draft, stop and tell the operator; never fall back to a live post. Enforced in sapb1 from 2026-09-16: post refuses every document in Mart, the GRPO included, with no flag.

## Evidence
Daman 2026-09-16 ("in MART there should never be a direct entry posted to the ledger"). Shared write log queries/user05/sap-writes.jsonl: 13x POST PurchaseDeliveryNotes -> 201 in JIVO_MART_HANADB by USER19 on 2026-09-04 18:17-18:18. Read back 2026-09-16: sapb1 query PurchaseDeliveryNotes --company JIVO_MART_HANADB --filter 'DocEntry ge 14012 and DocEntry le 14024' = 13 docs, DocTotal Rs 11,94,900, Cancelled tNO, bost_Open. Code: refuseLivePostInMart in sap-b1/cli/internal/cli/postingdocs.go, test TestPostCommandRefusesLiveGRPOInMart.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
JIVO MART: never post an entry directly to the ledger. Every Mart document (GRPO, A/P, credit note, payment, JV) goes in as a DRAFT; if SAP refuses the draft, stop - never fall back to sapb1 post.
