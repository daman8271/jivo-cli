# Wellness dispatch and QC — discussion contract, 9 September 2026

Status: reviewed source audit and local visual prototype; no new live dispatch ledger or hour-level production scheduler deployed by this iteration.

## Settled scope

Daman explicitly ruled on 9 September: finished goods, storage and dispatch-space calculations include only BH-BT and BH-PF. Gupta/GP-FG and GP-FGM are excluded. Packaging retains its separate allow-list. Bulk oil is EXIM only; no BH-LO or BH-GJ oil balance contribution.

Production VPS freeze checked in this turn: `/root/jivo-courier/jolly/live/freeze_live.py`, FG loop uses BH-PF/BH-BT exclusively. Astha inherits the aggregate. Current billed-waiting stock is still a mixed-company Oil-share estimate and cannot be asserted as verified BH-only physical occupancy.

## Current calculation and real comparison

Current input as of 9 September 01:36 IST, FG observation 01:27:05 IST: FG 591451 L, billed-waiting estimate 183190 L. Their sum 774641 L is planning pressure, not a reconciled physical stock count.

8 September audited BH-only gate departures: 54076 L, five gate trips. BH-BT 38956 L; BH-PF 15120 L. GP-FG 26373.6 L is excluded. The previous all-Oil company headline 80449.6 L is not the scoped Wellness/BH dispatch headline.

Never subtract historical gates again from a later refreshed balance without proving the balance did not already reflect them. Establish when each stock source reduces stock: invoice, pick/load, or gate departure. Preserve billed-not-gated physical goods exactly once.

Per warehouse: dated opening physical stock + production/receipts + transfers in - transfers out - gate departures + signed adjustments = calculated closing stock. Compare against an independently observed closing physical stock at the same timestamp. Unknown opening, transfers, returns or stock basis stays unknown, never zero. Track source timestamps and unmatched movements.

Save the original day forecast before results arrive; compare it with actual production/dispatch/closing stock without rewriting history. A matching physical ledger and measured forecast error are different checks.

## QC recommendation

Use timestamp precision. Actual QA approval and stores readiness override estimates. Future QA timing remains explicitly estimated from valid same-supplier/material/unit arrival-to-approval histories; it is not laboratory active time or a promised SLA. Do not apply an extra blanket day. A material ready on 13 September may use the remaining compatible production hours on 13 September, subject to line, crew and stores availability.

The deployed daily engine still rounds estimated readiness into the next daily bucket. Exact shift windows, QA approval windows and Stores-release hours are required for the next intra-day scheduling iteration. Do not invent them. Elapsed historical medians already include observed waiting; avoid adding the same overnight delay twice when modelling calendars.

## Source dates and follow-up

Unknown arrival stays in the open-order / follow-up book, never confirmed usable supply. Source-dated arrivals remain expected commitments and actual receipts remain observed events. Disable invented packaging delivery cadence. Historical supplier lead times may inform a separately labelled procurement risk buffer, never manufacture a shipment promise.

Confirmation request should contain item/code, PO or shipment reference, remaining quantity, requested delivery date AND time, receiving location, confirmation owner, time confirmed, and partial-delivery splits. A changed date preserves its previous promise and reason.

People notes: Shunty/Lovpreet appear in oil purchase/EXIM records. Daman's 29 August contact identifies Bhupinder (Ginni veerji) for packaging; exact all-packaging responsibility remains open. Gurvinder coordinates ownership and escalation. Verify recipient identity and route before sending.

The legacy VPS `jwa doctor` check returned LOGGED_OUT since 3 September; `jolly-wa` inactive. Wati endpoint/token settings exist locally but its current send/receive path was not tested in this iteration. No message was sent.

## Visual prototype

Local Three.js schematic, historical replay for 8 September, five BH-only truck trips. Show load litres / planning tonnes (1000 L = 1 planning tonne), gate reference, exact departure, warehouses, and evidence timestamp. Never label the replay live/GPS. No fabricated rack fill or unknown closing stock. Mirrored keyboard-accessible table and WebGL fallback.

Target 100 planning tonnes is separate from confirmed dispatch commitments. The observed BH-only gap is 45.924 tonnes; that arithmetic does not imply extra trucks exist. Future what-if inputs remain clearly hypothetical and do not modify source records or the live planner.
