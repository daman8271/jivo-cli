# Mark 4 — independent review, pass 1

Reviewer: Cassius. 6 September 2026. **V1 is not cleared.** Confidence: high (at least 95%) in the confirmed reproductions below. This is a review of the independent `site-mark4` implementation; no Claude Mark 4 implementation was inspected.

## Scope and evidence

Read the meeting clarifications and `REQUIREMENTS.md`, normalization, machine rules, recursive material ledger, order/storage flow, sanitizer and API loader, and UI labels. Executed `buildModel` on the actual sanitized seed and isolated counterexamples. After V1 launched on the VPS, independently requested `http://127.0.0.1:3404/` and `/api/model`: both returned HTTP 200. The actual API returned 25 days and 31 runs, engine `Mark 4 independent deterministic planner · v1`, input stamp `2026-09-06T05:27:01+05:30`.

The files were being fixed during this review. Findings distinguish the initial reproduction from what was independently observed in the running API. Source locations identify the relevant functions; line numbers refer to the reviewed implementation and may move in subsequent fixes. Local changes alone do not prove the running site is corrected.

## Confirmed findings

### P1 — Company-scoped FG codes were treated as global product identity

Location: `site-mark4/lib/model.ts:52`, `normalizeProducts`, original order filter/canonicalization.

Actual seed: Beverages OMS orders for FG0000328 contained 38,400 pieces, but the Oil item master defines that code as SANO POMACE 200 L drums. V1 interpreted those beverage pieces as 7,680,000 L of Oil drum demand. FG0000324 similarly converted 17,760 beverage pieces into confirmed sesame orders and affected machine priority. The first actual-seed run reported excluded demand of 7,718,560.60 L.

Fix direction: admit only Oil-scoped OMS identity; quarantine other-company rows unless a verified cross-company product map exists. Preserve a visible exclusion explanation.

**Runtime follow-up:** the running API now reports FG0000324 confirmed demand 0, FG0000328 confirmed demand 37.803 allocated ecom pieces, and excluded demand 41,000 L. The specific company collision is corrected in this V1 API. Full regression proof belongs to pass 2.

### P1 — Shortage extrapolation overstates cartons and understates shared material demand

Location: `site-mark4/lib/model.ts:296–315`, blocker and material shortfall calculation; `components/Planner.tsx:1156`, displayed shortage.

Confirmed isolated reproduction: monthly demand 100 pieces, bottle stock 100, carton recipe 0.05 per piece, carton stock 0. The material shortage and proposed quantity were 100 cartons, although five cartons cover the demand. `trial(p, 1)` rounds the one-piece carton consumption to one whole carton, then the old code multiplies that failure by every unmet piece.

Separately, `max` across products gives 20 units for two products needing the same missing component in quantities 10 and 20; the combined shortage is 30. Max over successive dates must not replace summation across independent products.

Running API still exposes carton PM0000838 shortage 12,920 for a 10-piece carton, consistent with the old extrapolation path. API did not yet contain the new proposed quantity fields at this review snapshot.

Fix direction: calculate terminal-material requirements on the full demand ledger, sum shared requirements, net shared stock/accepted arrivals once, and round carton quantities at the relevant batch boundary. Keep a one-product blocker distinct from an aggregate proposed purchase quantity.

### P1 — Earlier reserve production never covers orders arriving later

Location: `site-mark4/lib/model.ts:168`, `existing` FG ledger; daily allocation and run completion.

Confirmed counterexample: Monday has monthly target 20 pieces and materials for 20; an existing input order is dated Tuesday and due Tuesday for 20 pieces. The engine produces 20 Monday as reserve, reaches zero unmet production, then never allocates that reserve to the Tuesday order. No billing or dispatch is scheduled on any later day; all 20 remain unbilled through month end despite the known order.

Fix direction: maintain available FG by canonical product, credit reserve production, and allocate newly active orders from that ledger before deciding new production. This must preserve physical stock and avoid subtracting the same FG twice.

Engine reports a local fix; not yet independently retested in the running V1 when this pass was recorded.

### P1 — Sanitization destroyed stable duplicate identity

Location: `site-mark4/scripts/serve_inputs.py:97`, order sanitization identity, and `lib/model.ts` order deduplication.

Confirmed on the real private freeze without printing document identities: reverse only the backlog array. Raw input still has 105 identical orders shared by `orders` and `backlog`; the original sanitizer leaves only one matching identity, because its hash includes the array enumeration index. The engine can therefore count the other 104 twice. The ordinary seed happened to have matching enumeration order and did not expose this.

Fix direction: stable source identity independent of array order/date clamping, while preserving legitimate repeated identical order lines through explicit occurrence identity. Feed owner reports the implementation and regression are fixed; pass 2 must verify the final artifact.

### P1 — Inferred ecom SKU/date allocations were described as precise confirmed orders

Locations: `live/freeze_live.py:1394–1427` (source construction), `site-mark4/lib/model.ts` priority/allocation and run reason, `components/Planner.tsx` demand labels.

The source collector has litres by date and litres by SKU separately. It distributes each date across the platform SKU mix, explicitly recording an assumption in the private freeze. Thus the 1,878 ECOM-PO rows are inferred SKU/date allocations of real aggregate PO demand, not original exact SKU/date lines.

V1 drops that provenance and presents exact-looking confirmed pieces and due dates. The running API has no ecom rule detail and only the company-scope note in its metadata; a run says **“40,905.513 pieces cover real orders”** without qualifying that allocation. Priority was also delayed to the collector's assigned required-by date, treating it like order creation.

Fix direction: retain real aggregate demand, explicitly expose the allocation method wherever SKU/date precision is implied, and distinguish exact Oil OMS lines from modeled ecom allocations. Known demand should not become unknown until its due date. Do not relabel the entire stream as fabricated demand; the aggregate POs are real.

### P1 — Upstream failure could still produce a Live label

Locations: `site-mark4/scripts/serve_inputs.py:195–201`, retained-last-good response; `site-mark4/lib/load-input.ts:12–30`.

The original feed retained its last successful JSON after a source read/validation failure and returned it from `/inputs.json` with HTTP 200 and no failure marker. Only `/healthz` exposed the failure. The loader fetched only `/inputs.json` and called the input live when its stamp was under four hours old and the old embedded sources were all okay. A failed refresh could therefore remain labelled Live.

Fix direction: propagate retained/error status on the input response and honor it through the loader, API cache, and UI without altering the underlying observation timestamps. Feed and engine report local header/loader fixes; final failure-path evidence is required in pass 2.

### P2 — Replacement stock was counted in two warehouse buckets

Location: `site-mark4/lib/model.ts:155–164`, opening unbilled stock calculation.

Actual seed contains FG0000461 replacement stock 4,240 pieces outside the original monthly-sheet codes. `opening.fg_other_l` already includes those 4,240 L. Canonicalization adds FG0000461 to its old product family, and the original opening calculation counted the replacement there plus unchanged `fg_other_l`.

Initial engine opening = 600,828.9718 L; source FG total 410,265 plus standing 186,324 = 596,589 L. Difference is the duplicated replacement, apart from source rounding.

**Runtime follow-up:** running API opening = 596,588.9718 L, so the specific double count is corrected. Pass 2 should retain reconciliation with the source-room total and test future non-plan products brought into the canonical set.

### P2 — Applied scenario did not survive reload

Location: `site-mark4/components/Planner.tsx`, initial loader/scenario state.

Initial component kept scenario only in memory and reloaded the default GET after browser refresh. An operator's night-line, efficiency and supply decisions silently reset. Frontend has since added validated localStorage persistence after successful application; browser reload verification remains part of the second pass.

## Pass-1 conclusion

The runnable V1 is a real independent engine/API, but it is not ready to publish as verified. Company identity and warehouse reclassification are already corrected in the inspected API; the remaining material/order/provenance/failure/persistence findings need the revised build and independent reruns. Production and shared-material invariants alone do not prove purchasing quantities, demand identity, or truthful labels.

Independently viewed the parent-captured rendered desktop screenshot `../.mark4-local/study/pass1-desktop.png` from the same preview. The line-first board, readable product/run quantities, night indication, scenario controls and explicit Sunday-to-next-production-day banner render coherently. The screenshot confirms the visible Live source label discussed above. It is not proof of corrected demand or material logic. Mobile interaction and scenario-reload verification remain for the revised build. Final pass 2 must include those rendered results and the corrected runtime, not merely the existence of local fixes.
