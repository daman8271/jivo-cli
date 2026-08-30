---
title: Electricity — the real cost, and why SAP hides it
type: reference
company: JIVO_OIL_HANADB
told_by: Daman
last_verified: 2026-08-29
tags: [jivo/reference, jivo/cost, jivo/factory]
---

# Electricity

**Last month's bill: ₹26,04,139.** Confirmed by Daman, 2026-08-29.

> [!warning] CORRECTED 2026-08-30 — the books do NOT hide it. That was a scope error.
> The Rs 26 L is the **whole Kundli plant, shared with Beverages** — and Daman's tip
> says why it is big: *"when we are producing water, water takes up a lot of
> electricity since the machine is heavy... water was the main player in that."*
> Water is Beverages. Checked per month, May-Jul 2026:
>
> | Company | Account | Rs/month |
> |---|---|---:|
> | `JIVO_BEVERAGES_HANADB` | 5680011 ELECTRICITY | **15,76,107** |
> | `JIVO_OIL_HANADB` | 5680011 + 5100020 | **11,74,510** |
> | | | **27,50,617** ~= the plant bill |
>
> The split is already in the books and **Beverages carries the larger share**, exactly
> as the water story predicts. The finding below stands only for the August timing gap;
> it is NOT true that electricity never reaches an expense line. **Oil's conversion cost
> takes Oil's own power only** — loading the full Rs 26 L into Oil overstated it by
> Rs 14.3 lakh a month. Same trap as C-0032: a whole-group figure compared against one
> company's books.

## Why you will not find it by searching for "electricity"

The August money posted to **`2110004 SUNDRY CREDITOR SERVICE`** — a balance-sheet
creditor account. **It never touches an expense line in any month.** There are ZERO
A/P invoices from either power utility dated August 2026; only the outgoing payments
of 2026-08-22 (₹23,46,448) and 2026-08-24 (₹45,221), plus BSES ₹2,12,470.

**The VENDOR is named electricity, the ACCOUNT is not.** Search the vendor side:

| CardCode | Vendor |
|---|---|
| `VENDA000521` | UTTAR HARYANA BIJLI VITRAN NIGAM LTD — **ELECTRICITY KUNDLI** (the plant) |
| `VENDA000222` | BSES RAJDHANI POWER LTD — ELECTRICITY DELHI (office) |

When a bill IS booked it lands on `5680011 ELECTRICITY` (₹63.7 L / 68 lines over 12m)
or `5100020 ELECTRICITY DIRECT EXPENSE` (₹15.6 L / 6 lines), plus `5680005 PENALTY
CHARGES`. But booking is irregular, so **any monthly expense query understates it.**

## The bill has spiked

| Period | Kundli, billed |
|---|---:|
| Oct-25 → Jun-26 average | ₹3,88,007/mo |
| **July 2026** | **₹15,36,778 — 3.4x** |
| **August 2026** | **₹26,04,139** (per Daman; unbooked in SAP) |

## What it means for scheduling — the counter-intuitive part

The plant's draw is largely **FIXED**: it runs whether a line runs or not. So the cost
per litre is set by UTILISATION, not by the tariff.

| Line utilisation | Line-hours/month | **₹/L electricity** |
|---:|---:|---:|
| **11% — what August achieved** | 206 | **₹3.43** |
| 25% | 468 | ₹1.51 |
| 50% | 936 | ₹0.75 |
| 100% | 1,872 | **₹0.38** |

**Running the plant harder cuts electricity per litre by 9x.** Idling is what makes
power expensive here.

> **Therefore electricity is an argument FOR longer shifts, not against them.** An
> earlier reading in this repo said power was negligible so shift length did not
> matter. Both halves were wrong: it is not negligible (₹12,542 per productive
> line-hour in August), and it argues for more hours, not fewer.

Rate for marginal machine draw: **₹7/kWh** (factory Cost Master,
`ELECTRICITY_MACHINE PER_UNIT`).

## Links
[[PLAN-AND-LINES]] · [[PLANNING-MODEL]]
