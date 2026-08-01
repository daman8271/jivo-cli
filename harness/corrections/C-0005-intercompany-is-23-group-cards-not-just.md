---
id: C-0005
date: 2026-08-01
author: daman
area: all
severity: high
status: active
supersedes: C-0002
tags: [intercompany, related-party]
---

# Intercompany is 23 group cards, not just CUSTA000606

## Wrong
Split external vs intercompany by excluding only CUSTA000606 (JIVO MART PVT LTD), per C-0002. That leaves every other group card counted as an outside customer — JIVO WELLNESS DL/HR/PB/HP, JIVO MART HR/DL/PB/KR/RJ/UP/ISD, JIVO BEVERAGES-CUST. June-2026 olive: Mart 'external' came out Rs 10.47 Cr excluding only CUSTA000606, against Rs 9.53 Cr excluding all eight of Mart's group cards — a Rs 1.53 Cr overstatement of outside business.

## Right
There are 23 related-party customer cards across the three companies (Oil 9, Mart 8, Beverages 6). All of them are group entities, so all of them are intercompany. Exclude the whole set, not one card, and name which cards were excluded.

## Evidence
Catalogued live against OCRD 2026-07-31 (hana-sql/internal/domain/relatedparty.go). Measured on June-2026 olive (U_Sub_Group='OLIVE', credit notes netted): Mart external Rs 9,53,17,126 excluding all 8 Mart group cards vs Rs 10,46,93,533 excluding only CUSTA000606. Oil external Rs 3,64,46,055, internal Rs 7,55,90,666. Group external total Rs 13.18 Cr.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Intercompany is 23 group CardCodes, not just CUSTA000606: Oil CUSTA000001/2/3/4/606/827/906/1099/1113, Mart CUSTA000001/827/874/875/876/877/878/926, Bev CUSTA000001/2/3/4/606/827. Exclude all; name them.
