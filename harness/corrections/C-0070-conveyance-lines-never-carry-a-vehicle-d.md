---
id: C-0070
date: 2026-09-02
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [expense-heads]
---

# Conveyance lines never carry a vehicle dimension — Dim1 is CANOLA

## Wrong
Put the vehicle code on a CONVEYANCE line — Dim1 DL-8826 on an Activa tyre puncture and on Activa fuel, reasoning that the cost belonged to that scooter.

## Right
A 5690002 CONVEYANCE line always carries Dim1 CANOLA. A vehicle number is not eligible on conveyance, even when the expense is plainly for that vehicle — two-wheeler costs land on CONVEYANCE (C-0067) and therefore lose the vehicle dimension with it. Vehicle codes belong on 5650015 FUEL - VEHICLES, 5650002 REPAIR & MAINTENANCE VEHICLE and 5660005 TOLL, i.e. the four-wheeler heads.

## Evidence
Daman, 2026-09-02, on draft 55798 line 5: 'in conveyance a car no. is not eligible to be there, should be canola only'. Matches the books: every 5690002 line on posted ORGV000029 invoice 50274 (4 lines) and 47491 carries CostingCode CANOLA, none carries a vehicle. Corrected live on drafts 55798 (1 line) and 55804 (2 lines); 55799/55800/55805 were already clean.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
AccountCode 5690002 CONVEYANCE takes Dim1 CANOLA always — never a vehicle code, not even for a named two-wheeler.
