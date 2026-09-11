# PLAIN LANGUAGE — the rulebook for every word on this site

Daman, 1 Sep 2026: *"this is too complicated language — do you think people in the
factory would understand this?"* They would not. This file fixes that, permanently.

## Who reads this site

- **Gautam** — production in-charge at Kundli. Decides what runs on which machine.
  Reads English, thinks in Hindi. Never studied business or software.
- **The purchase desk** — wants: what to buy, by which date.
- **The godown in-charge** — wants: how full, what is leaving.
- **Gurvinderjeet** — owns the monthly plan, reads on an iPad. Numbers first.
- **Daman** — the owner.

**The test for every sentence:** *Would Gautam read this without asking anyone what
a word means?* If not, rewrite it. **The second test:** *Does it still say the true
thing?* If not, you have lied to make it simple — rewrite it again.

## Ten rules

1. **Short sentences. One idea each.** Under 15 words is the norm. Never a semicolon.
2. **Number first, then what to do.** "41 items are already late. Order them today."
3. **Factory words are fine. Office words are not.** Godown, line, machine, bottle,
   cap, label, carton, oil, truck, invoice, PO, stock, order, shift — all fine.
   SKU, component, cover, binder, throttle, forecast, channel, baseline, simulator,
   calibrated, backtest, horizon, headroom, provenance, cumulative, derated — banned.
   The full swap list is below. Use it.
4. **Indian numbers in sentences.** "27.65 lakh litres", "₹48.9 crore". Exact figures
   stay in tables (27,65,370). Never "2.7M".
5. **Every page opens with one line a person would say out loud.** Then the table.
   The "where does this number come from" note goes at the BOTTOM, small.
6. **Keep the honesty, drop the vocabulary.** "Assumed" becomes *"our guess — not
   measured"*. "Simulated" becomes *"the computer's plan — has not happened"*.
   "Forecast" becomes *"expected — not ordered yet"*. The truth stays. The word goes.
7. **Hindi is welcome where the floor reads.** The run list already says *"Gautam —
   Tuesday ka plan"*. The order-by page and the messages page may carry a one-line
   Hindi/Hinglish headline under the English one. Elsewhere, plain English.
8. **Say what a thing IS, not what field it came from.** Never "po_open_l",
   "docnum", "FCST-W0", "channel=FORECAST", "OITW". Nobody on the floor has seen
   those. "Order no.", "expected — not ordered yet", "SAP stock" instead.
9. **No hedging paragraphs.** One clear caveat line beats three careful sentences.
   "The godown limit is Daman's number, not measured" is enough.
10. **Never type a business number.** Unchanged rule. Every figure comes from `data/`.
    This rewrite changes WORDS, never numbers.

## The swap list — use these exact replacements

| Never say | Say instead |
|---|---|
| SKU / SKUs | product / products |
| component | material — and say which: oil, bottle, cap, label, carton, pouch |
| binder / blocking binder | the missing item / what is stopping it |
| cover, cover %, days of cover | stock lasts N days / enough for N days / X% of the month's need |
| cover<1% / near-zero | almost nothing in stock |
| at zero / literal zero | nothing in stock |
| lead time (6 d / 11 d) | takes 6 days to arrive / oil takes 11 days |
| order-by date | last date to order |
| late (order-by passed) | already late — order today |
| backlog / open orders | pending customer orders (ordered, not yet sent) |
| forecast / FORECAST / FCST rows | expected — not ordered yet |
| real orders / PO-backed | confirmed orders / has a customer order |
| demand / demand stream | what customers want this month |
| the plan / EXIM plan | this month's target |
| realise, ₹/L | selling price per litre |
| ₹ per line-hour | earns ₹ per hour of machine time |
| utilisation / util | machines busy % |
| line / lines | machine / machines (use the machine's name: JP Machine, Clear Pack…) |
| slot | bottle size |
| changeover / flush / clearance | oil change — about 1 hour (wash with 400 L of the next oil, then cleaning) |
| derated / "observed rate, then 50% efficiency" | machines run at half their normal speed (this is what we measured) |
| storage ceiling / roof / 827,000 L working | godown full at 8.27 lakh litres |
| headroom | space left in the godown |
| physical occupancy | how full the godown really is |
| standing stock / invoiced-not-gated-out / invoiced-not-trucked | billed, but the truck has not left yet |
| gated out / dispatched | truck left |
| invoice→truck lag (2 days) | after billing, the truck leaves 2 days later |
| STORAGE_THROTTLE / throttled | godown full — production slowed |
| LINES_IDLE | machines waiting for material |
| PACKAGING_ZERO | packing material finished |
| OIL_SHORT | oil short |
| ORDERED_BLOCKER → UNBLOCKED | ordered → arrived, can run again |
| the loop (block→order→land→run) | stuck → ordered → arrived → running |
| unproducible | no machine can fill this (3-litre bottles, 200-litre drums) |
| BOM | recipe — what goes into one bottle |
| opening / opening position / frozen | stock counted on <date> |
| as-of / horizon / the month | from <date> to 30 Sep |
| simulator / simulation / engine / algorithm / planner | the computer plan / the planner |
| calibrated / backtest / 0.16% | tested on August: the computer said 21.2 lakh L, the factory made 21.2 lakh L |
| baseline / baseline pattern | the normal shift — 12 hours, Sundays off |
| scenario | option / what-if |
| % of extra hours used | of the extra hours, how many actually ran |
| marginal | extra |
| conservation law | oil in = oil out (checked) |
| provenance / declared / flagged in the data | where this number comes from (or drop it) |
| assumption / assumed | our guess — not measured |
| measured | measured — real |
| derived | worked out from other numbers |
| HANA / OITW / ORDR / EXIM | SAP (the factory knows SAP) / the monthly plan |
| cumulative value ordered | total ordered this month (not what is still pending) |
| po_open_l | still to be sent |
| WhatsApp simulated drafts | messages the computer wrote — NOT sent |
| Overview | Summary |
| Lines (nav) | Machines |
| Storage (nav) | Godown |
| Materials (nav) | Stock |
| Order-by (nav) | Order by when |
| Build list (nav) | Run list |
| WhatsApp (nav) | Messages (not sent) |
| Floor 3D (nav) | Floor map |

## The banner (every page) — this and nothing more

> **This is a PLAN for September, made by computer. Nothing here has happened yet.**
> Stock was counted on 31 Aug evening. Messages on this site were never sent.

## Facts that MUST survive the rewrite (plain words, but never dropped)

- The godown limit (8.27 lakh L) is **Daman's number — not measured**.
- About **64% of what customers want is expected, not ordered yet**.
- **Every open PO is already late.** The plan assumes they arrive in week 1.
- Stock **billed but not yet trucked** on day 1 is **not counted** — the godown is really fuller.
- **E-com demand is spread evenly** across the month — our guess.
- **4 products have no machine** (3-litre bottles, 200-litre drums).
- **Machines run at half speed** — that is what we measured, not a fault.
- The **messages were never sent**. Nobody replied.
- The plan was **tested on August**: computer 21.2 lakh L, factory 21.2 lakh L.

## Before → after (real sentences from the site)

**Before:** "A FORWARD PLAN, not a backtest. September has not happened. Only the 1-Sept opening is observed."
**After:** "Only the starting stock is real. Everything else is what the computer expects."

**Before:** "64% of the September plan gets made under the baseline pattern. Run the floor as it runs today and September makes 27,65,370 L — ₹48.93 Cr of output — and ships 27,60,307 L, against a plan of 43,23,300 L across 84 SKUs. The missing 15,57,930 L is not idle will — it is storage, materials and the clock, plus 66,000 L that no configured line can make at all."
**After:** "Running as we do today — 12 hours, Sundays off — September makes 27.65 lakh litres, worth ₹48.9 crore. The target is 43.2 lakh. That is 64%. The rest is lost to three things: godown space, materials arriving late, and hours. And 66,000 litres are products no machine can fill."

**Before:** "Everything the September plan has to buy, with the last day each item can go on a PO before a run slips. At the 31 Aug freeze, 41 of 209 components were already past that day; 47 must be ordered inside week 1."
**After:** "What to buy, and the last date to order it. **41 items are already late — order them today.** 47 must be ordered this week."
**Hindi line:** "41 cheezein pehle se late hain — aaj hi order karo."

**Before:** "The moment an invoice is cut, SAP takes the stock off the books. On paper, it is gone. … standing in that amber state — space the book says is already empty."
**After:** "When a bill is made, SAP removes the stock. But the cartons are still in the godown until the truck leaves — about 2 days. The orange part of each bar is that: billed, not yet gone."

**Before:** "No storage call today — the plan fit under the assumed roof."
**After:** "Godown had space today."

**Before:** "The rule: only this day's opening is observed — the 31-Aug SAP close. Everything that then 'happens' below — runs, arrivals, invoices — is the calibrated simulator playing the plan forward."
**After:** "Real: the stock at the start of the day (from SAP). Computer's plan: everything below it."
