---
id: C-0055
date: 2026-08-30
author: Daman
area: all
severity: high
status: active
supersedes: 
tags: [forecast]
---

# Seasonality is keyed to the festival, not the calendar month

## Wrong
Measured September's seasonal multiplier as 'September 2025 vs the months before it', concluded September is a weak month (index 0.886), and reported that as the shape of JIVO's year. Then, finding no event feed in any JIVO system, wrote that platform sale events 'cannot be computed - nothing in the stack knows them'.

## Right
Hindu festival dates move up to three weeks year to year, so a multiplier keyed to a calendar month silently assumes the festival sits where it sat last year. September 2025 contained Navratri (22 Sep-1 Oct), Flipkart Big Billion Days (23 Sep-2 Oct) and Amazon Great Indian Festival (23 Sep). September 2026 contains none of them - Navratri is 11-19 Oct, Dussehra 20 Oct, Diwali 8 Nov. Measuring the calendar month imported a festival that will not happen and overstated September 2026 by 346,482 L (16%). Separately: festival and platform-sale dates are PUBLIC. No JIVO system holds them, and that is not a reason to call them unknowable - look them up and write them into reference/EVENT-CALENDAR.md.

## Evidence
Measured live 2026-08-30 from JIVO_OIL_HANADB OINV/INV1 finished goods: Sep 1-21 2025 ran 50,794 L/day, Sep 22-30 2025 ran 104,721 L/day = 2.06x, carrying 485,343 L or 24% of the month. Mart's signature is order count not volume: invoices 21/day pre-event vs 89/day in window (4.2x), litres per invoice 650 -> 156. Control for month-end first: Mart books 60% of September lines in the last 3 days but 73% of Feb-2025 and 81% of Feb-2026, so a month-end spike is not an event. engine/forecast.py --event-days 2025-09-22:2025-09-30 moves the Sep-2026 midpoint from 2,133,552 L to 1,787,070 L. Dates from public calendars, see jolly/reference/EVENT-CALENDAR.md.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Before any seasonal figure, check WHERE the festival fell that year (dates move ~3 weeks) and strip event days from the baseline. Festival + platform-sale dates are public - look them up, never call them unknowable.
