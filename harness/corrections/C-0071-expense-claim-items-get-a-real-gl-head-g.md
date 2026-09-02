---
id: C-0071
date: 2026-09-02
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [expense-heads]
---

# Expense-claim items get a real GL head — GENERAL EXPENSES is not a bucket

## Wrong
Swept four unlike items into 5680000 GENERAL EXPENSES on draft 55798 — nut bolt, nut tool, charger adapter and aux — because the sheet grouped them under a 'Miscellaneous' subtotal.

## Right
Every printed item gets its own proper head; GENERAL EXPENSES is a last resort, not a landing zone for anything awkward. Hardware and fittings (nut bolt, nut tool) go to 5650001 REPAIR & MAINTENANCE OFFICE & BUILDING. Personal/office electronics bought for staff (charger adapter, aux cable) go to 5630003 STAFF WELFARE, the same head as staff medicine.

## Evidence
Daman, 2026-09-02, on draft 55798: 'GL are not complete — for nutbolt things take repair and maintenance office and building; charger adapter: staff welfare'. Rebuilt live: 5680000 now carries nothing on that draft (5650001 Rs 110, 5630003 Rs 1,046, 5680023 Rs 100, 5690002 Rs 287, 5680003 Rs 356, 5630004 Rs 7,020 = Rs 8,919). 5650001 also appears 3x on the vendor's own posted history.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Map every expense-claim row to a real GL head — hardware/fittings to 5650001 R&M OFFICE & BUILDING, staff electronics (charger, aux) to 5630003 STAFF WELFARE. Do not park items in 5680000 GENERAL EXPENSES because the sheet called them Miscellaneous.
