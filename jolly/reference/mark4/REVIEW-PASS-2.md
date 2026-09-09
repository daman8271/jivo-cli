# Mark 4 — independent review, pass 2

Reviewer: Cassius. 6 September 2026. **Status: no unresolved engine correctness blocker found after fixes; final rendered/persistence verification pending.** Confidence: high (at least 95%) for the observed results below. No Claude Mark 4 implementation was inspected or reused.

## First-pass findings rechecked

| Finding | Independent second-pass evidence | Result |
|---|---|---|
| Company-code collision | Running API excludes Beverages/Mart identity from Oil; FG0000324 no longer inherits beverage orders; excluded drums are 41,000 L. | Corrected; unrelated orders remain outside this Oil planner, not declared nonexistent. |
| Carton and shared procurement quantities | Re-ran isolated fixture: 100 bottles at 20/carton now produce shortage/proposed quantity 5 cartons. Two products needing 10+20 shared bottles now propose 30. | Corrected. The separate blocking gap remains the largest individual first-component gap, not aggregate purchasing need. |
| Reserve never covers later orders | Re-ran Monday make 20 / Tuesday order 20 fixture. Tuesday moves 20 into billed waiting, Thursday dispatches 20, final stock 0. | Corrected with per-product available-FG ledger. |
| Unstable order/backlog identity | Reversed only the real private backlog. Raw overlap 105; sanitized overlap 105. | Corrected, independent of enumeration order; feed tests also preserve duplicate-line multiplicity. |
| Ecom inferred allocation presented as exact | Live API now has ecom allocation rule/meta text and separate exact/allocated order quantities. Source note now correctly says current open-PO mix, not historical sales mix. | Corrected. Aggregate demand is real; SKU/date mix remains explicitly inferred. |
| Failed update could wear Live | Independently ran the three source-loader regressions: retained response→stale with original date; old stock→stale; failed first fetch→dated seed. All three passed. Source reader recognizes retained/error headers. | Corrected. |
| Replacement FG counted twice | Live opening storage exactly 596,589 L, matching source physical FG 410,265 plus standing estimate 186,324. | Corrected. |
| Scenario lost on reload | Frontend now persists only successfully applied, validated scenarios and guards malformed storage. | Source corrected; final browser reload evidence pending below. |

## New second-pass findings and corrections

### P1 — Product changes across dates were missing setup time

Original location: `site-mark4/lib/model.ts`, daily `campaignCount` reset and setup calculation. Running API showed JP changing from FG0000030 on 7 September to FG0000429 on 8 September with setup 0; Clear Pack also changed products across dates with setup 0. The meeting requires time for a needed change, not just the second campaign inside one date.

Engine now retains `lastProductByLine` across dates and charges the provisional one-hour change time for a different product. Candidate feasibility, allocation and reasons account for it. Same-product continuation has no new setup. Opening-horizon setup is explicitly unknown and provisionally zero. Independently reran the new cross-day and whole-session labour regressions: both passed. The final synchronized API has 24 product changes and every one carries exactly one setup hour, including JP7→8September. No uncharged switch remains in that runtime schedule.

### P2 — Material and invoice labels contradicted the represented quantities

The revised API had PM0000914 `shortage=0`, `proposedQty=9916`, `firstNeeded=null`. UI said “Not required” beside the proposed purchase and hid it with “Only shortages”. The blocking gap represents one production blockage; purchasing quantities come from the shared gross-target ledger.

Frontend now uses “Blocking or purchase needs”, includes positive proposed quantities, labels the gap separately, and says “No dated production shortfall” where no blocking date exists. The unreconciled windowed invoice-volume metric is now “Open invoice volume”, not an asserted physical pile awaiting dispatch.

### P2 — Two remaining assumptions were missing or overstated

The Gurvinder questions now include yellow mustard's normal bottle/line choice. Legacy16-piece FG is explicitly only provisional bottle-demand cover: recartoning costs/20-case-ready status are not verified, and the remaining-stock question asks whether it may ship as-is or must be repacked. The verified old→new recipe transition does not prove existing cartons are already repacked.

## Scope audit against the original requirements

| Requirement group | Evidence and boundary |
|---|---|
| M1–M3 pack exclusions and3L routing | `rules.ts` plus independent eligibility tests: no 3 L/15 L Clear Pack; 15 L tins only Tin Head; 3 L plastic on 10/6 Head, derived speed disclosed.3L tins remain visible unresolved. |
| M4–M9 machine nature | Mustard-first JP, groundnut allowed, yellow excluded from JP,40 g preferred/52 g allowed Clear Pack, sesame restriction,10 Head small-pack preference and6 Head 5 L/printed-tin preference retain eligible alternatives. Broken-labeller workaround remains provisional. |
| M10–M12 pouches, drums and BOM truth | Pouches isolated to pouch line; conservative physical pouch capacity is not summed under one night slot. Drums excluded, not labelled physically impossible. Container and combo bottle count come from BOM; two 1 L bottles consume two containers and halve sales-unit throughput. |
| Session, efficiency and changeovers | Ten effective day hours, one optional ten-hour night line,80% applied once with raw unit/basis, source-stamped derived rates, setup in line capacity. Cross-day setup is independently verified in both a targeted regression and the final API schedule. |
| Sunday and stock conservation | No Sunday runs/target; dispatch continues. Shared recursive stock, blends, inbound and physical warehouse ledger tested independently. Billing transfers buckets and never creates space. |
| Labour | Missing verified session cost stays unavailable. If provided, each started session is charged once. Recorded-run cost is not misrepresented as a ten-hour session rate. |
| Monthly projection and order focus | Projection retained; MTD uses booked-by-item once, never adds MES, never subtracts current FG twice. Missing calendar days remain unknown. Exact Oil OMS demand ranks above inferred ecom allocation; remaining target prepares reserve. Production-target interpretation stays an explicit owner question. |
| Historical ranking | Read-only evidence documents incomplete prior-month/channel coverage. No calibrated GT/MT average or fabricated low-demand rank is claimed. Continuing the authorized monthly projection is explicit. |
| Carton transition | Verified groundnut identity preserves piece demand and uses replacement carton consumption. Unmapped legacy 16 recipes held by default. Narrow optional compatibility hypothesis keeps identity and conditional quantities distinct, compared with a strict baseline. Existing legacy FG handling is explicitly provisional. |
| Production value | Desired ₹2.5 crore/day and discussed ₹2 crore minimum are production value, not billing. Sunday denominator disclosed. Missing valuation leaves full value/gap unknown and preserves known subtotal/unvalued litres. Input collection date is not falsely called a price-validation date. |
| Operator explanation | Line-first shift board, actual line observations, product eligibility, fallback explanation, run material/rate detail, monthly schedule, missing-material procurement and dedicated rules/questions. Actual completed days stay separate. |
| Storage and pendency | Declared 827,000L working limit; BH-BT/BH-PF unbilled plus waiting split. Physical opening tally reconciles. Open invoice volume/aging are qualified; usual 2 day and14 day tail are assumptions/measurements, not truck appointments. |
| Source and safety boundaries | Current/retained/seed dates explicit; no missing-as-zero history. Sanitized feed, no customer/phone payload. No source-system writes, messaging, August calibration claim or drum capacity added. Security release review is separate. |
| Delivery process | Multi-phase plan and specialist implementation; this is the second independent review after fixes. Final public Vercel URL, logged-out200 and final rendered/browser tests remain the parent release gate. |

## Runtime evidence before the final synchronization

Independently called the running VPS `/api/model` with default settings and both optional switches. Both returned HTTP 200. Default warm response took 0.04 s; uncached both-switch response took 16.53 s, including strict-baseline recomputation. That latency is observable, not an instant interaction; it remains under the configured 30-second function limit in this measured run.

At that snapshot, default produced 567,928.6065L; supply plus provisional recipes produced 1,605,763.3655L. Both had zero Sunday runs and at most one actual night line. Provisional recipe output was 0 and its strict baseline was identical: none of this source snapshot's legacy families passes the narrow compatibility gate. Do not claim the recipe switch improved this actual snapshot. The positive/mismatched independent fixtures establish that the option works when its evidence is present and holds when it is not.

These figures predate the final cross-day setup correction and are retained only as test evidence, not final deliverable totals.

## Final verification

Final synchronized preview: `/root/mark4-astha/app` on VPS port3404. Independently inspected its actual API: all24 product changes have setup1h, including the originally failing JP7→8September transition; opening storage596,589L and drum exclusion41,000L still reconcile. Current output567,928.6065L; known valuation₹89,008,581.453615, with7,244L unvalued, so full valuation/gap correctly remain unknown. Inputs dated2026-09-06T05:42:02+05:30. Yellow-mustard and legacy-stock questions are present, and carton-rule status is provisional.

Proof’s refreshed suite reports35/35 tests passing; this reviewer independently reran the two changed setup/labour tests and all three source-loader failure tests.

Browser persistence/mobile results and the parent public-release audit remain pending. The last copy-only change renames observation-clock columns to “Source read at”; its final Vercel build is the parent’s responsibility.

## Parent release closure — 6 September 2026

The pending release checks above are now complete. This addition records the parent's verification, not a new claim of observations by Cassius. The final app is public at https://jivo-mark4-astha.vercel.app. `HTTP-PUBLIC.json` records successful default and scenario API executions and invalid-payload gates. `BROWSER-FINAL.log` records all eight views, current invoice-age labels, run detail/Escape focus restoration, responsive layouts, applied scenario persistence across reload, and a synthetic refresh failure followed by successful retry while retaining the previous plan. Parent visually reviewed all three final viewport screenshots. Final source includes cross-day setup and the final copy corrections; `TESTS-FINAL.log` reports 35/35 passing tests and `BUILD-FINAL.log` records the successful build.
