# Material planning decisions — 6 September 2026

These are implementation decisions and checked source findings. Deployment and completion are recorded separately in ROLLOUT.md.

1. **Use Factory for material balances and receipts.** Read the same Factory routes used by its CLI; read EXIM for tanks and shipments. Do not use SAP stock or Mark 3's invented delivery calendar.
2. **An order is a commitment, not an arrival date.** Current supplier PO responses do not contain a promised date. A new undated order must appear automatically, with a confirmation action. It does not justify silently adding all its material tomorrow.
3. **Arrival and usability are separate.** A truck already at the gate must leave the road list. Material waiting for QC cannot be treated as usable just because the ETA has passed.
4. **Do not trust the posting flag alone.** Independent review found Factory's PO received balance can already include a receipt whose gate record still says unposted. Example: PO220826087, PM0000053, ordered10,000, bookreceived1,800, remaining8,200; two900 receipts include one markedunposted. Deducting that900 again wrongly predicts7,300 still due. Reconcile physical receipts and book quantities with explicit history coverage.
5. **Estimate only from relevant evidence.** Supplier/material history must have at least three distinct observations. Blanket-order part-load cadence is different from a new supplier's first delivery. Do not multiply one supplier's delivery rate by the number of open POs. Show sample period and date window.
6. **Keep uncertainties actionable.** Missing supplier dates go to Purchase; QC release to Quality; receipt-versus-stock differences and unit identity to Stores. Link each material to affected products and dates. No outbound messages are sent by this work.
7. **Make material changes trigger replanning.** Scan new suppliers and their orders automatically. Hash full material content for model caching, so a changed PO cannot hide behind an unchanged page timestamp. Preserve source observation times on failure.
8. **Keep the two supply views clear.** Expected existing supply may use qualified estimates; recorded-only uses recorded usable dates. Proposed purchases are not issued orders and do not enter this live plan.
9. **Preserve original units.** Live stock includes packaging in pieces, metres and kilograms. Tape in metres cannot disappear because a collector assumes all packaging is pieces. Oil mass-to-volume conversion must stay explicit.
10. **Protect the user's existing work.** Modify only Astha's independent app and services. Preserve dark mode, approved machine rules and the existing monthly target. Do not deploy to Mark 3 or Claude's Mark 4.

Known business decisions that remain open: usability of BH-NM/GP-NM non-moving stock; missing supplier promises; exact stock inclusion for some accepted-unposted receipts. The application must expose these rather than mark them confirmed. A larger production total is not the acceptance test; correct quantities, source-to-plan updates and visible qualifications are.
