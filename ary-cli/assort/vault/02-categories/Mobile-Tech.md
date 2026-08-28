---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-29
confidence: high
system: ARY / FusionERP8
---

# Mobile and tech — a real business hidden in three SKU codes

The Rs 2,690 "Mobile group" figure that opened this investigation was never the business.
The real one is ~59x larger, sits under **Accessories**, and runs at 39-44% margin on three
generic catch-all codes. A textbook case of [[Data-Quality-Traps]].

## The numbers

Verified at SKU level, 12 months:

| Code | Product name | Units | 12m sales | Bills | Avg rate | Cost | Price | **Margin** |
|---|---|---|---|---|---|---|---|---|
| **07P1** | Mobile Adapter | 126 | **₹52,568** | 123 | ₹418 | ₹221.00 | ₹362.33 | **39.1%** |
| **07P0** | Mobile Datacable | 600 | **₹50,927** | 580 | ₹85 | ₹65.08 | ₹115.91 | **44.3%** |
| **0AWR** | Bluetooth Buds | 77 | **₹50,790** | 75 | ₹660 | ₹441.63 | ₹730.41 | **40.2%** |
| 01F4/01F5 | Charger 38 / 41 | 5 | ₹2,690 | 5 | ₹538 | | | |
| 02SD | Mobile Earphone 02 | 8 | ₹1,320 | 8 | ₹165 | | | |
| **Tech total** | | **816** | **₹1,58,295** | **791** | | | | **~40%** |

(Cotton Buds and Tulip Ear Buds, ₹24,208, are toiletries caught by the same name search —
excluded above.)

**What the numbers actually say:**

- **This is a real, repeat business: 791 separate bills a year.** Not a one-off. Students
  and staff are buying cables and adapters roughly **twice a week**, every week.
- **The margin is 39-44%**, verified from `ProductChildMaster` cost and price — well above
  ARY's 31% retail average and 5× the institutional channel's 7.2%.
- **It runs on THREE generic product codes.** "Mobile Datacable" sold 600 units at an
  average ₹85 — meaning every cable type, length and connector in the store is booked to one
  SKU. Nobody can tell whether the demand is USB-C or Lightning, 1 m or 2 m, or which price
  point sells.
- **The ₹2,690 "Mobile group" figure that opened this investigation was never the business.**
  It is the two "Charger 38/41" SKUs — the only ones filed under the Mobile group tag. The
  real business is ~59× larger and sits under **Accessories**. This is §22's taxonomy problem
  producing a two-orders-of-magnitude error on a live category.

**The cheapest high-return action in this whole exercise:** split those three codes into real
SKUs. It costs nothing, needs no stock, no licence and no supplier — it is data entry — and
it converts an invisible ₹1.58 lakh line into a category that can be bought, priced and grown
deliberately. Until it is done, no one can answer "which cable should we stock more of?"

The research lane costed a full 130-SKU tech bay at ₹3.10 lakh one-off for ~₹59,000/month of
incremental revenue, plus fitted tempered glass and covers (₹25,000 one-off, ~₹28,750/month).
Those are **ESTIMATES from that lane and were not independently verified here.** The
₹1.58 lakh, the 791 bills and the 39-44% margins are VERIFIED.

## See also

- [[Catalogue-Shape]] — the same pattern across the catalogue
- [[Ten-Moves]] — splitting the codes costs nothing and is the cheapest high-return action
