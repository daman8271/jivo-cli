---
id: C-0049
date: 2026-08-27
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# Freight GRPO: tax code follows the TRANSPORTER's state, and weight-packs use 0.769 L

## Wrong
Assumed the reverse-charge tax code on a freight GRPO follows the destination, that SAC is always 2 (9967), that the line description is always 'EDIBLE OIL', and that U_UNE_LTS is always the AR invoice's printed Product-Category total even for weight-packed goods.

## Right
Verified by a blind reconstruction of three GRPOs (26082/26057/26056) from their bilty attachments alone, scored 104 of 113 fields. (1) The reverse-charge code follows the TRANSPORTER's own GSTIN state against JIVO's Haryana(06) branch, NOT the destination: ARNAV 07ACBPY4022H1ZO = Delhi -> inter-state -> RIGST@5, even on a Gurugram delivery; DELHI PUNJAB TRANSPORT CO 06AANFD7642N1ZV = Haryana -> intra-state -> GST05R, on a Punjab delivery. (2) SacEntry is NOT constant: 2 = SAC 9967 'Freight' (~85%) and 40 = SAC 9965 'FREIGHT' (~15%) are both live, driven by neither vendor, state, tax code nor date — ask before assuming. (3) ItemDescription is free text: 'EDIBLE OIL' 676, 'Oil' 95, 'edible oil' 23. (4) For LITRE/ML packs the invoice's printed Product-Category total is exact (4 of 4 hit). For WEIGHT packs it is not: on invoice 626080458 the PDF prints 9,959.6016 L but the keyed U_UNE_LTS is 9,957.012 = 12,948 pouches x 0.769 L, i.e. a 700 g pouch is taken as 0.769 L. (5) Two same-name vendor cards existed for DPTC; the bilty's printed PAN AANFD7642N picked VENDA000636 (validFor Y) over VENDA000973 (no PAN, validFor N) — disambiguate by PAN, never by name.

## Evidence
Blind test 2026-08-27: bilty PDFs pulled via GET Attachments2(172735/172539/172535)/$value, predictions written and sha256-locked (f882b9b03750ee271c38ba9f3c6c7a6ad99abb9cadf7d3ac444ae208954c8628) BEFORE any PDN1 query. Actuals: 26082 RIGST@5/SAC 2/DL; 26057 RIGST@5/SAC 40/HR; 26056 GST05R/SAC 40/PB. 9957.012/12948 = 0.769 exactly. SacEntry split by month CreateDate 2026-05..08: 2 = 201/486/292/255 vs 40 = 3/66/6/32. Dscription counts from PDN1 since 2026-06-01.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO tax code follows the TRANSPORTER's GSTIN state vs the 06 branch (ARNAV Delhi=RIGST@5, DPTC Haryana=GST05R), never the destination. Weight packs: a 700g pouch = 0.769 L, not the invoice's printed total.
