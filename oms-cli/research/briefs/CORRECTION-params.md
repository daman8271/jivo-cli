# CORRECTION — param attribution was wrong in the first cut of these briefs

Issued 2026-08-04, mid-study, after the tracker study caught it.

`extract_calls.py` originally captured a flat 160-character window after each
call site and searched it for a `params:{...}` object. In a minified bundle the
next call begins immediately, so that window ran past the closing paren and
credited the FOLLOWING call's params to the current path.

**6 of 15 param sets were wrong.** Specifically, these were WRONG and have been
removed:

| path | was wrongly credited | the param actually belongs to |
|---|---|---|
| `/api/orders/status` | `mode` | `/api/orders/status-tracking` |
| `/api/sap/addresses` | `category` | `/api/sap/parties/category` |
| `/api/orders/staff-products` | `flow_type` | `/api/orders/flow-config` |
| `/api/orders/{id}/orderlogs` | `order_ids` | `/api/orders/quotation-status` |
| `/api/tracker/my-queue` | `stage` | `/api/tracker/stage-advanced` |
| `/api/sap/parties` | `category` | `/api/sap/parties/category` (`search` is genuine) |

The extractor now balances parentheses to the real end of the argument list.
The corrected set cross-checks clean against the server's own 400 bodies on
every overlapping case (`item_code`, `card_code`, `mode`, `category`), which is
independent evidence rather than a second opinion from the same source.

**If your study asserted any param in the "was wrongly credited" column, drop
it.** Do not carry a flag that the app never sends.
