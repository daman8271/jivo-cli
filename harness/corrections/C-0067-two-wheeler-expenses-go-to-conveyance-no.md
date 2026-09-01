---
id: C-0067
date: 2026-09-01
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [expense-heads]
---

# Two-wheeler expenses go to CONVEYANCE, not Repair & Maintenance Vehicle

## Wrong
Booked two-wheeler costs (Bullet Service 2665 Rs 8,890; Activa 8826 mudguard repair Rs 200; Activa puncture Rs 50) to 5650002 REPAIR & MAINTENANCE VEHICLE because the paper said 'service' and 'repair'.

## Right
Every expense on a TWO-WHEELER — scooty, Activa, Bullet — books to 5690002 CONVEYANCE, whatever the paper calls it (service, repair, puncture, fuel). 5650002 REPAIR & MAINTENANCE VEHICLE is for four-wheelers only: on the same voucher the Rumion HP-4857 bumper repair correctly stayed on 5650002.

## Evidence
Asserted by Daman (owner) 2026-09-01 reviewing drafts 55798/55799/55800 — 'all 2 wheelers in convence'. UNVERIFIED against history: scanned all 31 ORGV000029 A/P invoices dated 2026 for lines carrying a two-wheeler dimension (DL-8826 Activa, DL-8873 scooty) — zero such lines exist, so the books contained no precedent either way. Applied live: the three drafts were patched 5650002 -> 5690002 and read back.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Any expense on a two-wheeler (scooty/Activa/Bullet) books to 5690002 CONVEYANCE, never 5650002 REPAIR & MAINTENANCE VEHICLE — that account is four-wheelers only.
