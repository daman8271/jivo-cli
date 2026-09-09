# MARK V implementation and acceptance

Date: 10 September 2026. Status: implemented and released; see RELEASE-VERIFICATION.md.

## User outcome

MARK V is the website used to plan tomorrow, compare the agreed plan with what
is running now, and see AI recommendations and their resulting actions. The
main page must be simple enough for a factory planner to understand without
opening dispatch, valuation, or supply investigations.

The user-approved source is the complete 64-page Machine Changeover Planning
Red Notes Edition PDF. Revised notes override the retained historical transcript.
See WORKING-RULES.md, PDF-REVIEW-2026-09-10.md and machines/ for exact extraction.
The two user task attachments were read in full on 10 September. They explicitly
request implementation, multiple phases and separate machine review jobs.

## Decisions

- Build in the existing codex-mark4 worktree, in a separate site-mark5 app.
  MARK IV has already been committed as e6d787f9 and merged into local main as
  003c2114. Its live site and collectors remain the existing source integration.
- Reuse tested input identity, BOM, material lifecycle and EXIM-only oil logic.
  Replace scheduling policy with the approved machine rules.
- Minimum daily objective: 100,000 litres; desirable range: 115,000–125,000 litres.
  These are planning tonnes at 1,000 litres per tonne. They do not create orders,
  material, storage space or guaranteed production.
- Allocate all day work before considering night, using one shared material and
  storage ledger. Retain the standing limit of one night line and Sunday closure.
- Use conservative range endpoints with the source ranges visible: JP 4,500/h,
  Clear Pack 4/5 L 1,500/h, 10 Head 1 L 1,800/h, Samarpan 1,800/h; JP change 6h.
- Setup occupies shift time. JP cleaning and flushing are inside its six hours.
  Clear Pack mechanical and flushing work can both apply. Do not double-count
  the 10 Head combined entry. Reuse flushing oil; never create stock from it.
- Retain ten effective hours per day and night session. Initial clock choice is
  07:30–17:30 day and 19:30–05:30 night, explicitly a planning assumption rather
  than a measured roster. No extra blanket 80% speed reduction.
- A missing prior machine campaign is not evidence of zero setup. Reserve six
  hours provisionally for an unknown JP campaign. Other unknown setup reserves
  remain explicitly conditional. Open-ended one-hour-plus durations are never
  described as guaranteed one-hour completion.
- Separate Hitech and Samarpan capacity. Current live Oil MES line IDs distinguish
  only aggregate Pouch Machine (5); do not duplicate aggregate actual output.
- Public reading, protected operator edits. Save and approve actual server-side
  plan revisions; show the latest suggestion separately from the agreed plan.
- AI runs as a real asynchronous Codex job on the VPS and returns typed proposed
  changes, checked by the same deterministic rules. Store its result and activity.
- Expose an authenticated, idempotent webhook. Polling can produce source-change
  events; native factory webhook registration must not be claimed without evidence.
- Factory-run submission is a separate pending user clarification. Website plan
  persistence, AI review and live comparison are fully in scope now.

## Architecture and ownership

Atlas reviewed the current source and recommended a separate Next.js app plus
Python standard-library HTTP/SQLite service. Full-month computation currently
happens inside the MARK IV model request and is repeated by its shift board.

1. Source review: seven machine documents, complete PDF audit, live factory form.
2. Engine: approved routes/rates, shared transition evaluator, continuous forward
   inventory, day-first allocation, validated operator and AI changes.
3. Service: persistent revisions, background refresh, coalesced jobs, atomic
   snapshots, protected edits, idempotent events and genuine AI execution.
4. Interface: Today, Tomorrow, Activity; source dates, machine comparison, clear
   holds and deliberate editing. Material details are contextual.
5. Verification: independent correctness/security review, meaningful engine and
   persistence tests, real AI job, desktop/iPad browser flows and performance.
6. Release: separate public MARK V app and isolated owned VPS service, with
   logged-out reads, protected writes and a tested rollback path.

Shared contract: site-mark5/lib/planning-types.ts. Engine owns business lib and
run-engine.ts; service owns service/, app/api/, service-client.ts and ops/mark5/;
UI owns page/layout/styles, components/ and use-dashboard.ts. Root integrates
package/config, deployment and evidence. No overlapping edits without a message.

## Acceptance evidence required

- Correct rates, pack restrictions and case/container conversion; no invented
  200 ml, 15 kg or pouch-volume ratings.
- Day and night share material reservations; no stock deficit, premature QC use
  or warehouse overflow. Continuing a campaign avoids unnecessary setup.
- Tomorrow uses the continuous current-day projection, not a rewritten source
  timestamp or a second subtraction of already-reflected production.
- Edits save, reload and approve the exact reviewed revision. Stale writes return
  a conflict. Agreed plans survive refresh and service restart.
- Unauthenticated and malformed writes fail. Duplicate webhook delivery produces
  one job. A late older job cannot overwrite a newer snapshot.
- A real AI job produces a traceable, validated draft or an honest failure.
- Source fresh, stale, missing and conflicting states are displayed correctly.
- Target service read p95 <250ms; deployed warm dashboard p95 <1s; refresh
  acknowledgement <500ms. Record actual performance, not just targets.

Initial live MARK IV baseline, 10 September: GET /api/model returned HTTP 200,
3,986,172 bytes in 17.004518 seconds from the Mac. This is one observed request,
not a measured p95. Raw response is kept privately in /tmp/mark5-evidence/.
