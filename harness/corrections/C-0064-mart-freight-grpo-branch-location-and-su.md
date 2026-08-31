---
id: C-0064
date: 2026-08-31
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# MART freight GRPO: branch, location and sub-budget all follow OUR bill-to address

## Wrong
Clone the branch (BPLId), Location and Dim4 sub-budget from that transporter's last Mart GRPO.

## Right
In MART they are decided by the address the transporter billed US at, printed in the bill's To block. Delhi address (GSTIN 07AAFCJ4102J1ZS) -> Branch DELHI (BPLId 1), Location/place of supply DELHI (LocationCode 1), sub-budget CostingCode4 SC-WARH. Haryana address (06AAFCJ4102J1ZU) -> Branch HARYANA (BPLId 2), LocationCode 2, CostingCode4 SC-BHKR. The three move together and are read off the paper, never inherited. LocationCode IS the place of supply: OLCT carries the GSTIN. MART ONLY — Oil and Beverages do not work this way (Oil BPL 2, Dim4 empty).

## Evidence
Daman 2026-08-31 on PICK & SHIP bill NCR-349, billed to JIVO MART PVT LTD, Mayapuri New Delhi, GSTIN 07AAFCJ4102J1ZS. JIVO_MART_HANADB.OBPL: 1=DELHI 07AAFCJ4102J1ZS, 2=HARYANA 06AAFCJ4102J1ZU; OLCT: 1=DELHI DL 07AAFCJ4102J1ZS, 2=HARYANA HR 06AAFCJ4102J1ZU (Bhakarpur Sonipat). 8 of 9 posted PICK & SHIP Mart GRPOs use BPL 1 / LocCode 1 / SC-WARH; the lone outlier 13733 (BPL 2 / LocCode 2 / SC-BHKR) is the one a clone-the-last-GRPO approach picks, and it is wrong. Corrected draft 40072.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
MART freight GRPO only: read OUR bill-to address on the transporter's bill. Delhi -> BPLId 1 + LocationCode 1 + CostingCode4 SC-WARH; Haryana -> BPLId 2 + LocationCode 2 + CostingCode4 SC-BHKR. Never clone these from the last GRPO.
