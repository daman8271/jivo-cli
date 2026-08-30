# Finding 02 — the Aug plan, and the production lines

**Date:** 2026-08-11 · **Company:** Jivo Oil
**Sources:** `AUG MONTHLY PLANNING 2026 By Gurvinder Vj 03.08.2026.xlsx` ·
`ji.jivo.in/production/execution/line-management` (read-only browse, logged in as
JIVO_OIL) · SAP HANA read-only

---

## A. The monthly plan

Four sheets. `FINAL (2)` is the working one (99 SKUs); `FINAL` is the weekly
breakdown (186 SKUs); `Sheet2` is a pack-size capacity summary.

**Columns that matter:**

```
CODE · BRAND · HEAD · CATEGORY · SUB-CATEGORY · SKU · PER LTRS · PACK TYPE ·
LTRS/BOX · CASE PACK · AUG MONTHLY PLANNING (commodity) · (premium) ·
TOTAL PCS · GT/MT/ROI (IN TONS) · ECOM PLANNING (IN TONS) ·
TOTAL PLANNING (IN TONS) · + first-week splits
```

**The plan keys on `CODE` = the SAP FG item code.** That is the join that makes
everything else possible: plan → `OITT`/`ITT1` BOM → packaging + raw material →
stock → purchase. No mapping table needed, no name matching, no guessing.

**August totals** (`FINAL`, row 2):

| | Litres |
|---|---|
| Commodity | 1,232,500 |
| Premium | 799,400 |
| Ecom | 2,358,000 |
| **Total** | **4,389,900** |

`PACK TYPE` is also carried per SKU — PET 26GM, PET 40GM, PET 52 GRAM, 5 LTR JAR,
TIN, POUCH. That is the bridge to the filling line.

**Data-quality note:** `PER LTRS` holds text (`"200 ML"`, `"500ML"`) on some rows
instead of a number, and `LTRS/BOX` shows `#VALUE!` on those same rows (95, 96, 98).
A few rows have component tonnages that don't sum to their own total (e.g. row 6:
40 + 150 ≠ 240). It is a hand-maintained spreadsheet and it has arithmetic bugs in
it today. Anything reading it must validate, not trust.

---

## B. ⚠️ The tonne means two different things

**The plan uses 1 MT = 1,000 L.** Verified: FG0000030, 220,000 pcs × 1 L =
220,000 L, and the sheet's `GT/MT/ROI (IN TONS)` column says **220**. Clean.

**SAP purchases mustard oil at 1 MT = 1,098.9 L.** Not an assumption — this is
what live purchase orders actually post:

| PO | Date | Vendor | Qty | UoM | NumPerMsr | Inventory qty booked |
|---|---|---|---|---|---|---|
| 220826044 | 2026-08-08 | AWL AGRI BUSINESS | 80 | MTS | 1098.9 | **87,912 L** |
| 220826025 | 2026-08-04 | VAISHNODEVI REFOILS | 120 | MTS | 1098.9 | **131,868 L** |
| 220826034 | 2026-08-04 | ARORA AGRI BUSINESS | 150 | MTS | 1098.9 | **164,835 L** |

1,098.9 is the density conversion (mustard oil ≈ 0.91 kg/L). Physically it is the
correct one. The planning sheet's 1,000 is a convenience.

**Why it matters:** if the pilot reads "we need 220 T" from the plan and asks
procurement for 220 MTS, SAP books **241,758 L** — 9.89% more oil than planned.
At ₹173,500/MT that is ~₹38 lakh of unplanned oil on one line item.

**The rule this system will follow:** never convert tonnes to litres with a
constant. Carry the unit on every number, and when talking to SAP use that item's
own `OITM.NumInBuy` / `POR1.NumPerMsr`. Planning tonnes and purchasing tonnes are
different units that share a name, and the pilot must never silently mix them.

---

## C. The production lines — they exist, and they're mostly empty

`ji.jivo.in → Production → Execution → Line Management`, company Jivo Oil.
**Seven lines. Five configured speeds. Five of seven lines have nothing.**

| Line | Configs | Speeds (bottles/hr) |
|---|---|---|
| **10 Head** | 3 | 1 LTR **2,100** · 2 LTR **1,260** · 5 LTR **900** |
| **Pouch Machine** | 2 | Hitech **1,800** · Samarpan **2,400** |
| 6 Head | 0 | — |
| Clear Pack | 0 | — |
| JP Machine | 0 | — |
| Manual | 0 | — |
| Tin Head | 0 | — |

Every line carries the same line settings: **std hours/month 572 · std hours/day
22** (= 26 days). Identical across all seven, which reads like a default rather
than a measured value. **Electricity units/hour is blank everywhere.**

**Two columns are empty on every single config row:**

- **SKU → `-`.** The material-to-machine map does not exist yet. The column is
  there; nothing is in it.
- **Labour / Other Manpower → `0`, Supervisor / Operators → `-`.** No manpower
  attached to any configuration.

### The capacity gap this already implies

August plan for 1 LTR packs (Sheet2): **2,189.5** → 2,189,500 one-litre bottles.

10 Head at 2,100/hr × 22 h/day × 26 days = **1,201,200 bottles/month**.

**Shortfall ≈ 988,300 bottles** that must run on lines whose speed nobody has
entered. Confidence: medium-high on the arithmetic, medium on the premise —
it assumes Sheet2's figures are MT and that 10 Head is the only 1 LTR line, and
the second assumption is exactly what the blank SKU column prevents me from
confirming.

Sheet2 also flags **200 ML and 500 ML as "Machine Pending"** in its own notes —
so the planners already know some pack sizes have no line.

---

## D. Scorecard, updated

| Input | Status |
|---|---|
| Sales history · live stock · BOM | ✅ in SAP, confirmed |
| Lead times | ✅ derivable from PO→GRPO, per vendor |
| Monthly plan | ✅ exists, keyed on SAP FG code, hand-maintained, has bugs |
| **Machine capacity** | ⚠️ **container exists in ji.jivo.in, 5 speeds filled, 5 of 7 lines empty** |
| **Material-to-machine map** | ❌ **does not exist — SKU column blank on every row** |
| Labour per line | ❌ not filled |
| Electricity per line | ❌ not filled |

Correction to Finding 01: machine capacity is **not** absent from every system —
it is absent from *SAP*, but ji.jivo.in has a purpose-built home for it that is
mostly unfilled. That is a much better position: the schema is decided, someone
just has to enter the numbers.

---

## E. What the pilot needs next

1. **Who fills the SKU column** on line configs — that single column is the
   material-to-machine map, and without it no production sequencing is possible.
2. **Speeds for the other five lines** (6 Head, Clear Pack, JP Machine, Manual,
   Tin Head).
3. **Confirmation** that 572 h/month · 22 h/day is real and not a template default.
4. **Which tonne governs procurement** — see section B. This one is worth money.
