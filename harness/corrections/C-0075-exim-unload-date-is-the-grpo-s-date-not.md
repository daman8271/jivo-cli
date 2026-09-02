---
id: C-0075
date: 2026-09-02
author: Lovepreet
area: accounts
severity: high
status: active
supersedes: 
tags: [exim]
---

# EXIM unload date is the GRPO's date, not EXIM's created_at

## Wrong
Used /stock-status/debit-entries/ created_at as the date the truck was unloaded, and put it on the Unloading register as 'Unload Date'.

## Right
created_at is only when somebody keyed the row into EXIM. The oil was actually taken in on the SAP GRPO's DocDate (OPDN.DocDate). The two drift: on 71 of 205 matched rows they differed, by up to 51 days (RJ47GA6771: EXIM 2026-04-25 vs GRPO 2026-06-15). Tie the truck to its GRPO via OPDN.U_VehicleNoM, and use vehicle + received QUANTITY - a lorry makes many trips, so the plate alone hands every trip the same GRPO.

## Evidence
Joined GET /stock-status/debit-entries/ (209 rows) to OPDN/PDN1 on U_VehicleNoM for RM oil lines, 2026-09-01: 205 matched, 134 same day, 71 different (-51 to +71 days). Same truck across trips collided onto one GRPO until quantity was added to the key.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
EXIM debit-entries.created_at is when the row was keyed, NOT the unload date. Take it from the matching SAP GRPO (OPDN.DocDate); match the truck on U_VehicleNoM + quantity, not the plate alone.
