# ARY MAXIMISATION — "everything the 5,000 need"

**Objective (Daman, 2026-08-28):** Baru Sahib is a closed township of ~5,000
residents whose *only* retail outlet is ARY. Make ARY carry everything those
5,000 people need to live — every category, every SKU that matters — and prove
the gap with data, not opinion.

**Method:** research demand *blind to our catalogue*, then diff against ARY's
19,481 active SKUs, then rank what to add.

## Phase 0 — Foundation ✅ (done 2026-08-28)
- ARY live: `FR8HODBNEW` @ 138.252.101.118, 290 tables, read-only guard proven
- Catalogue dumped: 21 departments · 84 product groups · 846 subgroups · 1,180 brands
- 12-month demand baseline per group: `assort/data/sales-by-group-12m.csv`
- Revenue: FY23-24 ₹6.22 Cr → FY24-25 ₹5.84 Cr → FY25-26 ₹6.92 Cr →
  FY26-27 annualising **₹8.96 Cr** (+29%)
- Per resident: **₹1,493/month · 7.2 bills/month · ₹208/bill**

## Phase 1 — Population & wallet model
Who the 5,000 are (students / university / staff / married families / kids /
elderly), and the total addressable wallet per cohort per category. Establishes
the denominator every gap is measured against.

## Phase 2 — Demand-side research (multi-agent, blind to ARY)
46 category lanes. For each: the canonical SKU-line assortment an Indian
retailer serving a residential township must carry, 2026 trends, leading
brands, price points, pack sizes, and cohort fit. **No agent sees ARY's
catalogue at this stage** — that keeps the demand list honest.

## Phase 3 — Coverage diff
Per lane: match the research assortment against ARY's live SKUs
(`ary products list --group …`). Output coverage %, the SKU lines we hold,
and the SKU lines we do not.

## Phase 4 — Prioritisation
Score every gap: resident demand × wallet leaking off-campus × margin ×
shelf/cold-chain feasibility × supply reachability from Rajgarh (HP).
Adversarial verify every top finding before it goes in the report.

## Phase 5 — `ary assort` CLI module
Ships the whole thing as commands, so this is repeatable and not a one-off deck:
`taxonomy` `coverage` `gaps` `priority` `dead` `wallet` `research`.

## Phase 6 — Report
Single HTML deliverable: what the 5,000 need, what we hold, what to add first,
sized in ₹.

## Live gaps already visible from Phase 0 (to be confirmed in Phase 3)
| Category | ARY 12-month sales | Active SKUs | Read |
|---|---|---|---|
| Medicare | ₹3.40 L | 272 | ₹68/resident/**year** on medicine — no real pharmacy |
| Baby care | — | 3 (an "accessories" subgroup) | no diapers / formula / baby food, on a campus with married staff families |
| Mobile | ₹2,690 | 8 | 5,000 phone owners, 8 SKUs |
| Dairy | ₹10.09 L | 41 | loose milk only; no curd/paneer/cheese depth |
| Frozen | ₹51,677 | 57 | no peas/parathas/nuggets |
| Kids Wear | ₹42,738 | 83 | families on campus |
| Pet care | — | 0 | category does not exist |
| Optical / eyewear | — | 0 | category does not exist |
| Hardware / DIY | — | — | Electricals 123 SKUs, no tools |
| Dead tail | — | ~13,400 | active SKUs with no sale in 12 months |
