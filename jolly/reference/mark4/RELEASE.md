# Astha Mark 4 — release record

Released 6 September 2026. Public app: **https://jivo-mark4-astha.vercel.app**.

Vercel CLI inspection confirms project `jivo-mark4-astha`, target `production`, deployment `dpl_G9wqxSDW1EpSbuGhanBEkEumH2Mx`, status Ready, created 05:44:44 IST. Logged-out requests return HTTP 200 without an SSO redirect. Deployment uses only `site-mark4/` from the isolated `codex/mark4-local` worktree.

## Delivered behavior

This is an independently implemented deterministic planner and UI. It reads sanitized source inputs; it does not reuse Mark 3's computed forward schedule or Claude's new implementation. Existing Mark 3 collectors and deployment continue unchanged.

Eight views cover the shift board, month plan, machines, materials, godown/dispatch, demand, actual history, and rules/questions. The operator can select one night line, no night, or automatic selection; adjust efficiency; and separately explore proposed supplies or narrowly supported provisional carton substitutions. Applying a scenario recomputes the plan and saves the successfully applied settings in browser storage.

The agreed defaults are 10 effective hours per session, at most one additional night session, 80% applied once to the published rate basis, no Sunday production, and continued modeled physical dispatch. Machine compatibility, product preferences, BOM container identity, shared stock, carton consumption, cross-date changeovers and storage conservation shape actual allocation. Current confirmed demand and the monthly projection remain distinguishable. Completed days show booked and MES observations separately, including missing/partial reads.

## Acceptance evidence

| Scope | Evidence |
|---|---|
| Attachment and full clarification recovery | `meeting-transcript.md`, `clarifications.md`, `REQUIREMENTS.md`; final user overrides preserved, including deferred drums, WhatsApp and August backtest. |
| Multi-phase and multi-agent work | `PLAN.md`, `ARCHITECTURE.md`, `UI-DESIGN.md`; independent engine, frontend, source-contract, security, critic and tester work. |
| M1–M12 eligibility/preferences and container routing | `lib/rules.ts`, `lib/model.ts`; independent acceptance fixtures and final source-contract review in `COMPLETENESS.md`. |
| Time, 80%, night bound, Sunday, setup, labour | `tests/acceptance.test.ts`, `tests/model-edge.test.ts`; 35 passing tests in `TESTS-FINAL.log`, including the reproduced and corrected overnight-changeover defect. |
| Shared stock, recursive blends, cartons, future order reserve and warehouse conservation | Independent nonempty fixtures and full-seed reconciliation in the same suite; `QA-PASS-1.md`, `QA-PASS-2.md`, `REVIEW-PASS-1.md`, `REVIEW-PASS-2.md`. |
| Projection, actuals, partial values and source honesty | Model tests for monthly target/MTD/FG separation, absent history, company identity, ecom allocation and unknown valuation; rendered Demand/Actuals/Rules views in `BROWSER-FINAL.log`. |
| Replacement recipe evidence | `DATA-EVIDENCE.md`, `scripts/supplements.json`, rule/run explanations. Verified groundnut identity is implemented; unsupported mappings are held and explained. Positive and mismatched provisional fixtures exercise the optional hypothesis. |
| Public data boundary and freshness | `SECURITY-PASS-1.md`; 15 feed tests including canaries, exact routes, original timestamps, failed-source retention and stable hashed order IDs. Loader tests cover stale stock, retained inputs and dated-seed fallback. |
| Real scenario API, invalid requests and response scan | `HTTP-PREVIEW.json`, `HTTP-PUBLIC.json`: valid default/scenario responses 200; invalid/malformed 400; oversized 413; public response scan passed. |
| Operator interaction and responsive rendering | `BROWSER-FINAL.log`: all eight public views, run drawer/Escape focus, search, corrected pendency labels, actual/forward separation, scenario persistence after reload, failure retention and recovery. Parent visually inspected final 1440px, 768px and 375px screenshots. |
| Two substantive review/fix passes | Pass 1 fixed identity, carton, storage and future-reserve defects. Pass 2 found and fixed cross-day setup, material/purchase labels and missing assumption explanations. Both passes have independent reports and regression evidence. |
| Build and public release | `BUILD-FINAL.log`, Vercel Ready inspection above, public HTTP 200 and actual API/browser verification. No August accuracy claim is attached to the changed planner. |

All app-relative code/test paths in the table are under `site-mark4/`. Reports are in this directory. Test figures and screenshots are dated verification evidence, not promises of current factory output.

## Boundaries visible in the product

- Only one 16-to-20 replacement family has verified SKU/BOM identity. Other mappings stay held; the optional physical-fit hypothesis is conditional and has no additional eligible family in the release snapshot. Existing old FG treatment and any repacking effort remain provisional.
- The monthly sheet is provisionally interpreted as goods made during the month, net of known booked MTD. The daily-value denominator is production days. Both interpretations are owner questions. Missing values prevent claiming a complete target gap.
- Historical GT/MT coverage is incomplete and no averaging window was chosen. The authorized monthly projection remains; a calibrated trailing-demand ranking is not claimed. Ecom SKU/date allocations are explicitly inferred from aggregate open-PO evidence.
- Exact 3 L tin routing, some pack rates, broken-labeller workflow, setup duration, staffing/session labour, non-moving stock usability and physical dispatch timing still need business confirmation. Their assumed behavior is disclosed, not presented as measured fact.
- Drums, live WhatsApp/employee feedback, autonomous rule changes and August backtesting were expressly deferred. They are outside this release.

Confidence is high in the specifically tested behavior and deployment. This release does not establish predictive accuracy or resolve the listed business questions.

## Operation and isolation

Source of truth: `/Users/damanpreetsingh/jivo-cli/.claude/worktrees/codex-mark4/jolly/site-mark4`.

Public sanitized input feed: https://mark4-astha.srv1685505.hstgr.cloud/inputs.json, health at `/healthz`. VPS service `mark4-astha-inputs` reads existing source snapshots without altering them and listens on loopback port 8794. Its distinct Traefik route and service definition are in `ops/mark4/`. Keep this service running: the Vercel app depends on it for refreshed inputs. Source timestamps remain visible, and failures retain dated inputs honestly.

The isolated VPS preview and gstack automation are temporary QA processes and are stopped after release verification. No user apps, Claude session, Mark 3 service or collector is stopped. Credentials remain private/ignored; `.env*` is excluded from the Vercel upload.

Cleanup was verified: `mark4-astha-preview` is inactive/dead with MainPID 0; the isolated browser state was removed and no gstack/headless browser process remained. The gstack stop wrapper reported a lost connection while shutting down, so process state was checked separately rather than trusting its exit status. `mark4-astha-inputs` remains active/running. `RELEASE-HEALTH.json` records the post-cleanup public HTML/API/feed check at 00:29 UTC: all 200, nonempty independent plan, current source input at 05:57:01 IST, and no retained-feed error. This establishes that the public release is independent of the temporary preview.

Source comparison against the tested VPS copy found only the final UI header correction, “Recorded at” → “Source read at,” plus local ignore/build metadata differences. The Vercel build includes that correction and completed after its source edit; the engine and test sources are identical. The original engine, Mark 2 site and Mark 3 site have no source diff in this worktree.

To redeploy, run `vercel deploy --prod --yes` from `site-mark4/`, run the user's `vercel-public.py jivo-mark4-astha`, then repeat logged-out HTML and API verification. To remove this release, disable only `mark4-astha-inputs` and remove only its named Traefik route; do not alter the existing Mark 3 system. No commit or Git push was part of this release.
