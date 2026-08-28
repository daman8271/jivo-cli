---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-29
confidence: high
system: ARY / FusionERP8
---

# Pricing fairness — ARY does not exploit its captive market

The most serious reputational risk in this exercise, tested directly rather than assumed
away. **Rs 300 a year of above-MRP selling on packaged goods, across three rounding-level
SKUs.** ARY is, if anything, under-pricing.

If the fairness question is ever raised about a charitable trust running a monopoly shop,
these are the numbers that answer it.

## The evidence

The single most serious reputational risk in this whole exercise is that a charitable
trust's shop, the only one for 5,000 people who cannot shop elsewhere, might be
over-charging them. It was tested directly.

### On packaged branded goods — where MRP is legally binding — there is essentially nothing

Every SKU whose 12-month weighted-average sale rate exceeds the MRP recorded on its own sale
lines, restricted to **branded packaged goods** (excluding canteen dishes, own-brand "Ary"
items and the loose `_L`/`_Z` bulk lines, none of which carry a legal MRP):

| Product | Brand | Units | MRP | Sale rate | % over | 12m overcharge |
|---|---|---|---|---|---|---|
| Curtain Ring | Tulsi | 400 | ₹1.50 | ₹2.00 | 33.3% | **₹200** |
| Masoor Malka 1 Kg | Raja | 240 | ₹76.50 | ₹76.88 | 0.5% | **₹90** |
| Button | Mahajan | 100 | ₹0.90 | ₹1.00 | 11.1% | **₹10** |
| **Total** | | | | | | **₹300** |

**Three SKUs, ₹300 a year, on a ₹7.55 crore business.** Curtain rings and buttons rounded to
the nearest rupee. That is rounding, not exploitation. **On the metric that carries actual
Legal Metrology exposure, ARY is clean.**

### The apparent breaches are all canteen food and loose goods, where MRP does not apply

The unfiltered query returns 20 lines, and the top ones are:

| Product | Units | "MRP" | Sale rate | What it actually is |
|---|---|---|---|---|
| Softy Ice Cream | 6,647 | ₹20.00 | ₹29.13 | **canteen-made** — no MRP exists |
| Grilled Sandwich Gc | 1,849 | ₹60.00 | ₹66.71 | canteen dish |
| Masala Fries Gc | 2,298 | ₹40.00 | ₹43.69 | canteen dish |
| Sugar Cane Juice | 1,685 | ₹15.00 | ₹19.13 | canteen |
| Special Thali 99/- | 519 | ₹99.00 | ₹109.45 | canteen meal |
| Soyabean Fortune_L, Sugar_L, Tea_L, Besan, Rajma, Mung | | | | **loose/bulk** — sold by weight |

A prepared dish has no MRP, and a loose commodity sold by weight has none either. The "MRP"
field on those lines is a stale menu or reference price. **This is a data-hygiene point, not
a pricing one** — though it does mean the MRP field cannot be used for margin work
(consistent with §37's finding that the price master is unreliable).

### Read together with the margin evidence, the fairness picture is clear

| Evidence | Finding |
|---|---|
| Above-MRP on packaged goods | **₹300/year on 3 rounding-level SKUs** |
| Institutional / mess margin (§25) | **7.2%** — barely above cost |
| 27 SKUs (§37) | sold **below** purchase cost, −₹2.75 lakh/yr |
| Loose milk | **₹47.00/L against a ₹55 cost** for nine months |
| Retail margin (§25) | 31.0% — normal Indian retail, not captive-market pricing |

**ARY is if anything under-pricing.** It loses money on milk, sells the campus's feeding
programme goods at 7.2%, and its retail margin is ordinary. If the fairness question is ever
raised — by the Trust, by residents, or by anyone examining a charitable institution running
a monopoly shop — **these are the numbers that answer it**, and they answer it well.

The corollary matters for §37's judgement call: since ARY is not profiteering anywhere else,
the ₹47 milk price is much more likely to be **deliberate subsidy** than neglect. It should
still be recorded as a subsidy rather than absorbed silently as a phantom +35% margin.

## See also

- [[Below-Cost-Leak]] — the strongest single piece of the same evidence
- [[Institutional]] — the 7.2% margin on the campus feeding programme
