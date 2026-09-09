# Independent adversarial review — live material supply

Status at 6 September 2026, 21:50 IST: **APPROVED for the reviewed material-supply source/model changes; no confirmed P1 remains in the final candidate.** This is the critic's scoped approval, not a claim that deployment, subsequent live cycles or browser verification have finished. Those operational gates remain with the parent and Proof. This reviews Astha revision 3, not Claude's separate Mark 4 engine.

## P1 repaired — a false posting flag was subtracted twice from an already-net PO balance

Confirmed in the first live candidate, collected `2026-09-06T16:05:47.474634+00:00`.

`site-mark4/scripts/material_supply.py:116` accumulates every receipt with `posted:false`. Lines 150–153 subtract that entire pile from the Factory PO's `remaining_qty`. The source flag does not establish that the receipt is absent from that remaining balance.

Concrete Factory Oil examples:

| PO / item / line | Ordered | Book received | Book remaining | Physical receipts | Current computed not-yet-at-gate |
|---|---:|---:|---:|---:|---:|
| 220826087 / PM0000053 / 0 | 10,000 pcs | 1,800 | 8,200 | 900 marked posted + 900 marked unposted | 7,300 |
| 220826009 / PM0000085 / 1 | 500,000 pcs | 411,000 | 89,000 | 462,000 total; 288,000 marked unposted | 0 |

For the first PO, the two physical receipts total exactly the book's 1,800 received. Deducting the 900 marked unposted again erases another 900 from outstanding. For the second, the complete observed August/September receipts imply 38,000 physically undelivered if those rows are the complete nonduplicate lifetime receipt set; the algorithm instead clamps it to zero. The Factory posting flag and PO book therefore cannot be treated as interchangeable accounting evidence.

Required fix: reconcile exact receipt/posting evidence against the PO book, or explicitly retain unresolved overlap. Do not subtract every false flag, and do not replace that with an arbitrary supplier/item allocation. Do not add accepted-unposted quantities to stock without separate stock-inclusion evidence.

Evidence on VPS:

- `/root/mark4-live-phase3/review/posted-flag-book-conflict.json` — small selected-field comparison.
- `/root/mark4-live-phase3/source-builder/cache/material-raw.json` — private original normalized source rows.
- `/root/mark4-live-phase3/source-builder/cache/orders.json` — private complete supplier book.

Confidence: high. What could change the physical-undelivered inference: duplicated, cancelled or missing lifetime gate records. That would still require unresolved reconciliation; it would not justify blindly deducting every `posted:false` receipt.

### Repair verification

The revised reconciler requires complete lifetime gate coverage and exact PO-line/material/supplier/unit matches. It subtracts only physical receipts above the cumulative PO book-received quantity. Incomplete or inconsistent history becomes unresolved. Physical lot stages and quantities remain intact; ambiguous individual stock inclusion remains unresolved. TypeScript future-credit conservation excludes those noncreditable unresolved history rows. A temporary FIFO bookkeeping patch that relabelled QC states was challenged and removed.

Independent replay against actual `2026-09-06T16:08:14.016037+00:00` rows now produces:

- PO 220826087: outstanding 8,200; extra at gate 0; not yet at gate **8,200**. The 900-piece old receipt remains `accepted_unposted/unresolved`.
- PO 220826009: outstanding 89,000; extra at gate 51,000; not yet at gate **38,000**. Original physical QC/posting stages are unchanged.
- 85 expected receipt rows, with zero repeated lot IDs.

Evidence: `/root/mark4-live-phase3/review/real-posting-fix-replay.json`. The replay derived `historyFrom=2026-07-01` and complete-history status from the actual successful gate dataset IDs; that first raw collector file did not yet carry the newly added history metadata. Therefore this verifies the reconciliation logic on actual rows, not the final fresh collector end-to-end. That final gate remains with Proof and the parent.

## Findings repaired during review

- **Repeated historical batches shared one lot ID.** Python emitted several expected receipts against one aggregate lot while TypeScript rejected duplicates or read only the first. Builder now emits distinct partial lots and a single undated remainder. Independent probe: a 1,000-piece PO produced ten distinct 100-piece receipts; total remained 1,000.
- **Factory oil contract and EXIM shipment could both offset procurement.** Unmatched contract overlap is now explicitly unresolved; the same physical shipment reconciles into the gate lot. Independent probe produced one QC lot with a shipment link, and an unresolved contract balance.
- **Old scenario switch still invented purchases under the new ledger.** `model.ts` now disables `allowProposedSupply` when `materialSupply` exists. The legacy 7/14-day purchase scenario no longer injects stock into the owned ledger's production plan.
- **Historical posted lots broke outstanding-quantity validation.** TypeScript now excludes historical `usable` lots from future commitment conservation. Posted PM receipts can be recognized as already covered after a subsequent successful stock read; no second stock credit is added.
- **Older unresolved entries could never update their posting envelope.** Collector now includes the arrival months of persisted unresolved entries in refreshed month reads.
- **Material-file failure discarded ownership and reenabled legacy EXIM.** Publisher now retains its prior material envelope with failure status and original clocks.
- **PO-line subtraction did not verify material, supplier and unit.** These are now checked. Independent mismatch probe preserves the outstanding quantity and marks both affected records conflicting.
- **UTC timestamps could shift usable dates one day early.** Historical date parsing now converts aware timestamps to Factory IST. Independent probe correctly maps arrival `2026-09-01T18:00Z` to September 1 and QA `2026-09-01T20:00Z` to September 2.
- **Rejected stock silently vanished from the obligation.** The source outstanding balance remains visible with an explicit replacement/cancellation action. Rejected quantities receive no production credit.

Probe outputs: `/root/mark4-live-phase3/review/reconciliation-probe.json` and `lifecycle-probe.json`. These are narrow independent Python probes, not substitutes for QA's end-to-end replay.

## Actual first candidate and remaining verification

The first candidate had complete reported coverage across 805 datasets, 505 stock items, 212 material PO lines, 1,009 lots and 98 historical expected receipts. It included 470 accepted-but-unposted receipt rows. This is an audit count, not proof that 470 loads remain physically unavailable: the posting-flag defect above makes that interpretation unsafe.

The latest source adds shipment ETA plus same-supplier/material QA-history estimates. Those estimates explicitly assume no additional stores/posting delay after QA. They remain conditional, and an already accepted-but-unposted load is not automatically credited.

Read-only source review also confirmed explicit publication field allowlists, hashed references, a fresh vendor-catalog scan for each full supplier scan, original per-supplier timestamps retained on failure, and legacy EXIM suppression while the owned material ledger is present. No raw supplier or vehicle fields are copied by the new public merger. Proof still owns malformed payload and secret-sentinel tests.

## Final readiness check

The actual fresh candidate dated **2026-09-06 21:46:32 IST** now contains complete reported receipt-history coverage back to **2024-11-01**, 216 material PO lines, 1,206 lots and 110 expected receipts, including eight RM receipt estimates. This is the actual collector output, not replay-injected history metadata.

The corrected live cases are still 8,200 pieces not yet at gate for PO 220826087 and 38,000 for PO 220826009. There are no FIFO book-accounted lot IDs. Original receipt stages remain represented separately from uncertain stock inclusion.

The actual candidate publisher at `127.0.0.1:8795/inputs.json` contains the same 1,206-lot owned ledger, zero legacy inbound events, and **4,445,833 bytes** of public JSON. It fits the 5,000,000-byte consumer cap with 554,167 bytes of headroom. Evidence: `/root/mark4-live-phase3/review/final-candidate-summary.json`.

Final procurement code credits each source PO line's outstanding balance once, instead of summing both its split receipt lots and aggregate order. Unlinked loads that may overlap a same-material PO make the proposed purchase quantity `null`; both material views display that as unresolved, not zero. Such uncertainty also generates a purchase/stores action with a null quantity. Under the owned ledger, proposed purchases have no synthetic 7/14-day dates and never add production stock. Historical or unresolved receipt stages are not promoted to usable to satisfy a quantity guard.

Nonblocking limitation raised with the builder: PO balances and warehouse stock are separate observations. A receipt can change between those reads. A linked receipt with unresolved stock inclusion therefore merits additional conservatism if there is evidence of book/stock timing overlap. No incorrect current purchase amount caused by that race was demonstrated in this candidate; the purchasing calculation remains an estimate from separately timestamped books, not permission to place an order automatically.

Final source/model review is approved. Parent/Proof still own final integrated compatibility confirmation, subsequent real update cycles, deployment and visible UI verification. The payload headroom should be watched as the retained receipt ledger grows; exceeding the cap must remain a visible stale/failure state, never an empty material book.
