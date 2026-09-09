# Factory Plan 44 and What Can We Run versus MARK IV

Verified 8 September 2026, approximately 23:35–23:47 IST. Company: JIVO_OIL. Confidence: high for the retrieved values and inspected calculation contracts; this is not a physical stock audit.

Sources inspected in the authenticated factory UI:

- https://ji.jivo.in/planning-purchase/plans/44
- https://ji.jivo.in/planning-purchase/what-can-run
- https://ji.jivo.in/production/execution
- https://ji.jivo.in/production/execution/reports/daily

Underlying reads used the existing factory CLI authentication at `factory.jivo.in/api/v1`: Plan 44 detail, requirement and producible GETs; a DAY detail GET; and the page's stateless `producible/simulate/` calculation. No production, purchase, or other business record was changed. MARK IV evidence came from its public inputs and model endpoints in the same observation window. Raw responses remain private on the VPS in `/root/mark4-plan44-audit/`.

## Monthly plan

All 84 source product codes match. Factory Plan 44 totals 4,320,330.744 L and 3,053,094 inventory units. MARK IV's input target totals 4,323,300 L and 3,082,924 units: 2,969.256 L higher (0.0687%). Its displayed input litres contain rounded targets; recomputing pieces × pack gives 4,323,287.5824 L.

| Product | Factory Plan 44 | MARK IV input |
|---|---:|---:|
| FG0000422 mustard 869 g | 60,000 pieces; 57,294 L | 62,831 pieces; 60,000 L |
| FG0000381 olive 10 ml | 3,000 pieces; 30 L | 30,000 pieces; 300 L |
| FG0000178 mustard 15 kg | 2,124 pieces; 35,010.954 L | 2,123 pieces; 35,000 L |

Eight other differences affect litres only. Full reconciliation: `plan44-vs-mark4-monthly-2026-09-08.csv`.

MARK IV's monthly target remains the August 31 freeze of the EXIM September plan uploaded August 27. `live/freeze_live.py` copies the base plan; `site-mark4/scripts/serve_inputs.py` reads the resulting live input file. A fresh overall input timestamp does not mean that target was refreshed from Plan 44. Its groundnut FG0000142 → FG0000461 transition preserves 385,000 pieces; the replacement carton recipe changes packaging demand.

Plan 44 reports 535,951.576 L of production across its planned products. Its 14.2% attainment uses inventory units even while the display selector shows litres. Litres attainment is 12.4053%. Its footer explicitly identifies production receipts from SAP OINM movement type 59, not line-run entries. MARK IV's historical actual headline covers September 1–7, with today's receipts separate; comparing those headlines directly would mix periods and product scopes. The DAY detail endpoint supplies derived plan buckets, not daily production quantities, so it does not resolve this difference.

## Material feasibility

What Can We Run is useful for a proposed mix: it subtracts shared materials in entered priority order or uses fair-share allocation. Its **achievable** column is additive; its **alone, could make** column is not. The Plan 44 producible page also contains independent per-SKU alternatives that cannot be summed.

An explicit request for 5,000 pieces each of sunflower 1 L (FG0000081), groundnut 1 L (FG0000142), and Gold 1 L (FG0000149), on-hand basis, returned 45, 284, and 0 pieces respectively. Both allocation choices gave 329 L for this particular mix. These are calculation results, not observed production. The page does not schedule machines, time, changeovers, labour, storage, or customer priorities, and does not deduct work in progress or credit future receipts.

| Material | MARK IV engine opening | Factory calculation | Evidence explaining difference |
|---|---:|---:|---|
| Sunflower oil RM0000009 | 45.41 L | 45.410 L | Same stock |
| Groundnut oil RM0000011 | 98,000 L | 284.085 L | MARK IV uses EXIM tanks; factory uses this item's BH-LO book balance |
| Caps PM0000085 | 21,000 | 90,880 | MARK IV BH-PM + BH-NM; factory BH-PM + BH-PC |
| 40 g bottles PM0000194 | 74,080 | 98,422 | MARK IV BH-BS + GP-NM; factory BH-PC |
| Cartons PM0000006 | 626.4 | 1,410.35 | MARK IV GP-NM; factory BH-PC |
| Gold front label PM0000397 | 10 | 0 | MARK IV's ten are in GP-NM |
| Tape PM0000075 | 610,958.3836 m | 86,112.2 m | MARK IV includes a large GP-NM balance; factory includes BH-PC instead |

The packaging differences are verified warehouse-scope differences; both warehouse reads were fresh within minutes. Groundnut differs because MARK IV uses EXIM tank readings instead of the item's warehouse book balance. MARK IV omits BH-PC/BH-PS and includes rooms whose non-moving availability is unresolved. Factory scope is packaging BH-PS/BH-PC/BH-PM and raw BH-LO/BH-OT, excluding BH-WST. This is a material unresolved planning-policy discrepancy, not proof that every factory-page stock value is the correct physical balance.

Groundnut's 98,000 L is EXIM GROUNDNUT FILTER 73,000 L plus GROUNDNUT 2B 25,000 L. The dip dataset timestamp is September 8, 14:09 IST. Tank readings supersede equivalent book stock in MARK IV; they are not added to the book balance. Full warehouse evidence: `plan44-vs-mark4-stock-2026-09-08.csv`.

## Actual runs today

The execution and daily-report pages identify the line-run records. On September 8 the daily report displays zero production, while underlying run segments carry 34,020 L of entered output across five product/line combinations. All eight run headers still have zero totals; two are draft and six are in progress with stopped segments. Therefore zero at the report header does not establish no production. Segment totals are entered output, not finalized whole-plant production.

The separate MARK IV today-review page uses dated line evidence and the original saved plan. September 8's baseline was captured at 19:32 IST after the runs started, without capture counters. Its comparison must remain descriptive; it cannot prove that the saved plan predicted or would have improved the earlier decisions. Factory stop remarks are evidence for stops, not proof of why a product was selected. Overlapping recorded segments and unresolved material scope also prevent a defensible winner claim.

## Assessment

Use Plan 44 as a monthly-target and receipt-reconciliation source; use What Can We Run as a material check for a specified mix. Keep MARK IV's scheduling layer for machines, time, setups, order priorities, arrivals and storage, but reconcile its target refresh and warehouse policy before claiming agreement or superiority. This investigation does not silently change either source's numbers.
