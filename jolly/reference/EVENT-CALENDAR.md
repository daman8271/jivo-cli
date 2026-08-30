---
title: Demand event calendar — festivals and platform sale events
type: reference
last_verified: 2026-08-30
source: "public festival calendars + platform sale announcements; JIVO impact measured from SAP"
tags: [jivo/reference, jivo/planning, jivo/forecast]
---

# The event calendar

**Why this file exists.** Daman's planning spec says a Flipkart or Amazon sale event
must sit in the same calendar as Diwali and drive the same kind of uplift. No JIVO
system holds these dates — not SAP, not ecom, not EXIM. So they are written down
here by hand, and the forecast reads them.

> [!warning] Festival dates move ~3 weeks year to year. Calendar month is not the season.
> A seasonal multiplier keyed to "September" silently assumes the festival sits where
> it sat last year. In 2026 it does not.

## The dates

| | 2025 | 2026 | Shift |
|---|---|---|---|
| Navratri | **22 Sep – 1 Oct** | **11 – 19 Oct** | +19 days |
| Dussehra / Vijayadashami | 2 Oct | 20 Oct | +18 days |
| Diwali | 20 Oct | **8 Nov** | +19 days |
| Flipkart Big Billion Days | **23 Sep – 2 Oct** | not announced | — |
| Amazon Great Indian Festival | **23 Sep →** | not announced | — |

**2026 platform dates are NOT announced.** Both usually confirm 2-3 weeks ahead.
Public projections conflict: one says 23-30 Sep (simply repeating last year's
calendar date), another says 4-10 Oct. The second is the better prior — for three
years running both sales have opened in the same window roughly four weeks before
Diwali, and Diwali 2026 is 8 Nov, which puts the sale in **early-to-mid October**.

## What an event is worth to JIVO — measured, not assumed

Oil finished-goods dispatch, SAP invoice lines, Sept-Oct 2025:

| Window | Litres | Days | L/day |
|---|---:|---:|---:|
| Aug 2025 (clean month) | 2,349,478 | 31 | 75,790 |
| **Sep 1-21** (pre-event) | 1,066,673 | 21 | **50,794** |
| **Sep 22-30** (Navratri + BBD + GIF) | 942,488 | 9 | **104,721** |
| Oct 3-31 (post) | 2,083,368 | 29 | 71,840 |

**The nine event days ran at 2.06x the rest of the month and carried 485,343 L —
24% of the whole of September 2025.**

The e-com channel shows the same event differently: Mart's *volume* per day was flat
through the window, but its *invoice count* went 4.2x (21/day to 89/day) and litres
per invoice collapsed from 650 to 156. That is the platform signature — many small
orders. **The volume lands in Oil; the order count lands in Mart.** Looking only at
Mart's litres hides the event completely.

> [!note] A month-end spike is not an event
> Mart billed 585 invoices on 30 Sep 2025 against 6-34 on a normal early-September
> day. That is NOT proof of a sale event: Mart concentrates billing at every
> month-end — the last 3 days carry 60% of September's lines, but 73% of Feb-2025's
> and 81% of Feb-2026's. Control for month-end before calling anything an event.

## What this does to September 2026

September 2025 contained the entire festival-and-sale window. **September 2026
contains none of it** — Navratri starts 11 October.

A seasonal multiplier measured from Sept-2025 therefore imports an event that will
not happen, and over-forecasts September 2026:

Run both ways with `engine/forecast.py`:

```bash
python3 engine/forecast.py --target 2026-09                                    # event included
python3 engine/forecast.py --target 2026-09 --event-days 2025-09-22:2025-09-30 # event stripped
```

| | Sep index | Sep-2026 projection | Midpoint |
|---|---:|---:|---:|
| As measured from Sep-2025 (event included) | 0.886 / 0.966 | 1,990,320 - 2,276,784 L | 2,133,552 |
| **Event stripped** | 0.852 (level) | **1,682,117 - 1,892,024 L** | **1,787,070** |

**The correction is -346,482 L, about 16%.** A hand estimate from the raw daily
rates put it near -485,000; the engine is lower because it strips the event per SKU
and then shrinks each group's multiplier by credibility, which damps a one-off. The
engine number is the one to use.

### The open scenario — worth half a million litres

JIVO ships *during* the sale, not only before it: the 2025 peak was 22-30 Sep, the
event itself. So where the 2026 sale lands decides how much falls in September:

| If BBD/GIF 2026 opens | September 2026 gets | Sep projection |
|---|---|---:|
| Late Sept (23-30) | the whole event, as in 2025 | 1.99 - 2.28 M L |
| **Early-mid Oct (likely)** | **pre-fill only, if any** | **1.68 - 1.89 M L** |
| Split across the boundary | partial | between |

The two scenarios are **~346,000 L apart** — about 4.5 days of factory output.

**Get the announced dates the moment they are public** — they are the single largest
unknown in the September number. Until then plan the middle and hold the difference
as buildable slack, not committed line-time. And note the corollary: **October 2026
inherits what September loses**, on top of its own Diwali build.

## Maintaining this file

Add a row when a date is announced or a new event appears (Republic Day sale,
Freedom Sale, Prime Day, Holi, Raksha Bandhan). Update the measured-impact table as
each event closes — one measured event is worth more than any assumption.
