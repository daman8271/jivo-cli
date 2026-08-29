---
id: C-0050
date: 2026-08-29
author: Daman
area: all
severity: high
status: active
supersedes: 
tags: [units]
---

# A tonne means litres on the sale side, kilos on the purchase side

## Wrong
Read the planning sheet's 'IN TONS' column as weight and called it a mislabelled column / data-quality error, then quoted 4,156.4 T as if it were 4,156.4 metric tonnes of oil.

## Right
JIVO runs two tonne conventions on purpose, and both are correct in their own half of the business. SALE / PLANNING side: 1 T = 1,000 L (volume). PURCHASE side: 1 T = 1,000 kg (weight). Oil is 910 g/L, so one purchase-tonne is 1,098.9 L. A sales-side figure carried into a purchase order without converting overstates the buy by 9.89%. The August plan's 4,156.4 sale-tonnes = 4,156,400 L = 3,782.3 purchase-tonnes.

## Evidence
Plan FINAL(2): 76 of 76 testable rows satisfy TONS = TOTAL_PCS * PER_LTRS / 1000, i.e. volume (e.g. FG0000030: 220,000 pcs x 1 L = 220 'T'). SAP live POs 220826044 / 220826025 / 220826034 book MTS at POR1.NumPerMsr = 1098.9 L/MT, which is exactly 1,000,000 / 910. Convention stated by Daman 2026-08-29.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
JIVO tonnes: sale/planning side 1 T = 1000 L (volume); purchase side 1 T = 1000 kg. Oil = 910 g/L, so 1 purchase-MT = 1098.9 L. Never carry a tonne across sides without converting.
