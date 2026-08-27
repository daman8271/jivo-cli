---
id: C-0046
date: 2026-08-27
author: Daman
area: accounts
severity: high
status: superseded
supersedes: 
tags: [grpo]
---

# Freight GRPO Dim1: litres rule, and the transport desk is the reference

## Wrong
Derived a Dim1 (Variety) rule from AR-invoice composition, then labelled the 12.6% of USER19 GURCHARAN's transport GRPOs that disagreed with it 'exceptions' — implying the operator had deviated. Reported GRPO 26081 (bilty 7339) as an exception because OLIVE was the largest category (720 L) but she keyed SOYABEAN (600 L).

## Right
Her freight GRPOs are the reference standard, not a sample to be scored. The best mechanical basis for Dim1 is the AR invoice's largest category by litres, and it reproduces her on 87.4% of mixed-category lines. Every rival basis is worse: top printed row 85.9%, boxes 83.2%, value 82.1%, most lines 58.3%, first line 53.5%, last line 34.9%. The residual is NOT parser noise (restricting to invoices where every item is a clean LTR/ML pack moves it only to 87.6%), not de-duplication across the GRPO's lines (only 444 of 946 two-line freight GRPOs have distinct Dim1s), and not a category exclusion (OLIVE is keyed 1,413 times). So the residual is a reason the rule does not yet capture — ask her.

## Evidence
hana-sql JIVO_OIL_HANADB: 3,887 freight GRPOs / 6,091 lines on AcctCode 5670001, CANCELED='N', 2024-10-01..2026-08-24; 5,222 lines joined to their AR invoice via U_ARNO->OINV.DocNum, of which 2,338 mixed-category. Litres = pack size parsed from ItemName with weight packs at 1/0.91 L per kg (median 1.09890 over 1,068 purely weight-packed invoices). USER19 raised 601/601 Oil service GRPOs. Worked example: invoice 626080289 prints OLIVE 400+320, CANOLA 300, SOYABEAN 600; GRPO 26081 line 3 keyed SOYABEAN. Measured 2026-08-27.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO Dim1 = the AR invoice's biggest category by litres (87.4%). Where a keyed value differs, GURCHARAN/USER19's entry is right and the rule incomplete — ask her, never 'correct' it.
