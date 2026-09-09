# Actual-run filling estimates — 9 September 2026

Daman requested full-batch and remaining filling hours using the factory batch target and saved speed. Implemented on Today's review and Shift board through the shared `ActualTiming` component.

## Source and calculation

- Factory `required_qty` is cases; target pieces = required quantity × pieces per case.
- Factory run `rated_speed` is pieces/hour; it is passed unchanged as `ratedSpeedPiecesPerHour` through the collector and public feed.
- Full-batch estimate = target pieces ÷ saved speed.
- Remaining filling estimate = max(target pieces − entered output pieces, 0) ÷ saved speed.
- These are filling estimates at the source reading. They exclude setup, breaks, breakdowns and slower operation. No finish clock or browser countdown is inferred.
- Missing/zero/invalid inputs and conflicting records cannot produce false zero-hour answers. Completed runs describe any target balance as a shortfall, not scheduled further work. Stopped runs say the estimate applies if production resumes.

## Runtime check

Public factory feed at 2026-09-09 13:33:53 IST:

| Machine | Target pieces | Entered output | Saved pieces/hour | Full-batch hours | Remaining hours |
| --- | ---: | ---: | ---: | ---: | ---: |
| JP Machine | 18,000 | 11,700 | 5,400 | 3.333333 | 1.166667 |
| Clear Pack | 26,000 | 12,000 | 4,800 | 5.416667 | 2.916667 |
| 10 Head | 20,000 | 8,000 | 2,100 | 9.523810 | 5.714286 |
| 6 Head | 4,000 | 2,080 | 600 | 6.666667 | 3.200000 |

All four were STOPPED at that reading. Tin Head and Pouch Machine had no reported run; no duration was invented.

Updated active collector `/root/mark4-astha/app/scripts/collect_factory_now.py` and publisher whitelist `/root/mark4-astha/feed/live_board_feed.py`; both services active and public feed contains saved speeds.

The 9 September original baseline remains unchanged, SHA256 `22aeb344a5d390d0700f45d8a857597f1278ed64f7124a4b0f0a4933f12b9549`.

## Verification and release

- 24 focused Python tests passed.
- 46 focused TypeScript tests passed, also independently rerun by reviewer.
- Seven independent rendered-component checks passed, covering normal, unknown, conflicting, stopped, completed and historical cases.
- Typecheck and Vercel production build passed.
- Production deployment: `dpl_FQggjmWNNXPBXHBfncLdoiqJPSnv`.
- Public URL: https://jivo-mark4-astha.vercel.app
- Logged-out production URL returned HTTP 200 after deploy. Both actual views rendered the four source-based estimates; desktop 1440px and mobile 390px had no horizontal overflow or console errors. Screenshots are saved beside runtime evidence.
- Runtime backup/evidence: `/root/mark4-run-duration-20260909/`.

Confidence is high in the data path and arithmetic. Future elapsed running time remains an estimate because downtime and reporting completeness are not known in advance.
