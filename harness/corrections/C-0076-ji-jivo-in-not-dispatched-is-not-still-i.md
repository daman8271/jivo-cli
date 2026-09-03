---
id: C-0076
date: 2026-09-03
author: Claude (self-correction, live-verified 2026-09-03; ruling: ji.jivo.in is the factory truth — Daman)
area: factory
severity: high
status: active
supersedes: 
tags: [dispatch]
---

# ji.jivo.in: 'not DISPATCHED' is not 'still in the godown'

## Wrong
Treated every sales bill whose dispatch plan never reached DISPATCHED (booking_status PENDING/BOOKED) as goods still sitting in the FG godown, and fed the 14-day bills-window undispatched litres (1,260,504 L Oil) to the planner as the storage pile — the first live Mark 3 plan made ZERO litres for two days because the godown read 152% full.

## Right
The dock/gate module in ji.jivo.in is filled in for only ~45% of loads, so 'pending' includes bills that physically left. The storage pile is dispatch-fulfilment-summary's live PENDING+BOOKED backlog (cheap path, ~285k L all-company on 3 Sep 2026); the bills window is information only.

## Evidence
2026-09-03, jivo-factory-pp-cli: dispatch-plans bills --company oil --date-from 2026-08-01 --date-to 2026-08-31 → 644 Oil invoices, 292 DISPATCHED / 352 PENDING (Rs 37.72 Cr); vehicle-management vehicle-entries-count --entry-type SALES_DISPATCH same window → 126 COMPLETED trucks = 16,819 L/truck if all August output (2,119,237 L) rode them — impossible; Rs 37.72 Cr ≈ 2.1M L 'pending' vs an 827,000 L FG godown — impossible. Cross-check: dispatch-fulfilment-summary --from 2026-09-01 --to 2026-09-03 → PENDING 418 bills / 216,846 L + BOOKED 20 / 70,703 L = 287,549 L, plausible (34% of ceiling).

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
ji.jivo.in: 'not DISPATCHED' ≠ 'still in godown' — the dock module records ~45% of loads. For storage use dispatch-fulfilment-summary's PENDING+BOOKED backlog, never the bills window.
