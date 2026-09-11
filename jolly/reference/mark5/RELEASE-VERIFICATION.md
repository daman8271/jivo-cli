# MARK V release verification

10 September 2026. Public application: https://jivo-mark5.vercel.app
Owned service: https://mark5.srv1685505.hstgr.cloud/healthz

## Delivered behavior

- Today compares attributed factory observations, the agreed plan and the latest
  suggestion for seven physical machines. Unreported actuals remain unknown.
- Tomorrow supports exact quantities in pieces or verified cases, product
  priority, machine availability and one night allocation. Draft and approval
  are separate persistent revisions. Refresh and AI do not replace an agreement.
- Activity exposes background refresh, revision and genuine AI jobs. The real
  Codex provider returns a bounded proposal which the engine validates before
  saving. Signed, idempotent events can request a source refresh.
- Day allocation precedes night. The minimum is 100,000 planning litres and the
  desirable range is 115,000–125,000 litres. Targets do not create demand or stock.
- The approved 64-page PDF supplies machine rates and changeovers. Source ranges
  remain visible; selected lower speed endpoints and six-hour JP changeover are
  recorded. Flushing oil is reused, while setup still occupies clock time.

## Final automated checks

Executed on the VPS in /root/mark5-build/app, with the final synchronized source:

```
npm run build -- --webpack
npm run typecheck
node --experimental-strip-types --test tests/*.test.ts service/tests/proxy.test.ts
python3 -m unittest discover -s service/tests -p 'test*.py' -v
```

Build and TypeScript passed. JavaScript: 34 passed, zero failed or skipped.
Python service: 25 passed, zero failed. Total: 59 checks.

Coverage includes rates and routes, case/container identity, material/time/space
conservation, timed QC availability, day-first and one-night allocation, exact
commitment chronology, optimistic concurrency, revision persistence, bounded
controls, authenticated requests, signed duplicate events and stale background
jobs. Independent critic and tester reviews accompanied the implementation.

VPS evidence directory: /root/mark5-build/evidence/.
Final logs: build-final.log, typecheck-final.log, node-final.tap,
service-final.log, service-restart-control-verification.json,
browser-revisions-final.json and http-release.json.

## Browser loop performed by the root reviewer

Fresh isolated Chromium sessions were launched through gstack on the VPS. Tests
used the real Next.js production build, Python service, SQLite and engine.
Positive manufacturing fixtures were explicitly named QA SYNTHETIC and isolated
from the production database. No real factory run was created or started.

1. Loaded Today, Tomorrow, Activity, machine rules, constraints and source dates.
2. Tested desktop 1440×1000, iPad 768×1024 and phone 375×812. No horizontal
   overflow; captured screenshots were opened and visually reviewed.
3. Opened a machine drawer, moved keyboard focus, pressed Escape and verified
   focus returned to its original machine button.
4. Added 100 cases of the synthetic 20-piece SKU: the saved JP run was exactly
   2,000 pieces / 100 cases. Approved fixture revision 1, then reloaded it.
5. A genuine AI review produced draft revision 2, preserving approved revision 1.
6. Stopped the owned fixture service. Refresh showed an availability error while
   retaining the loaded board. Restarted against the existing database: approved
   JSON exactly matched the pre-restart record, with each run scheduled once.
7. Saved no-night in revision 3 and product priority in revision 4. The earlier
   exact 2,000-piece run remained in the cumulative saved controls.
8. A stale revision write returned 409. An impossible 9,999,999-piece request
   failed validation and created no revision; revision 4 and the agreement stayed.
9. Disabled JP in revision 5: the run was suspended and its control retained.
   Re-enabled it in revision 6: exactly 2,000 pieces / 100 cases returned.
10. Verified the public production page without login, operator login, protected
    cookie flags and an unauthenticated write returning 401. Public browser
    navigation remained usable while a refresh job was queued. No unexpected
    console errors were found in the public session.

The final public-browser AI request also completed successfully against the
released service: job fb5addee631546258eeff848bca9db82 saved a validated AI draft.
Its explanation retained the conditional warehouse limitation and did not claim
factory execution or approval.

The loop found and fixed lost unsaved tab edits, focus restoration, cumulative
control loss, disabled-machine exact-run conflicts, duplicate approved/exact
work, premature future setup validation and overly restrictive future SKU
continuity. Each fix received a corresponding browser or regression recheck.

## Live HTTP and performance evidence

Independent public service tests returned 202 for a valid signed event and its
duplicate, with the same job ID; invalid signatures and unsigned writes returned
401; conditional reads returned 304. Ten public service reads from the VPS had
median 22.839 ms and sample p95 133.948 ms. See HTTP-VERIFICATION.md.

The earlier MARK IV /api/model baseline was one observed Mac request: 17.004518 s
and 3,986,172 bytes. Ten MARK V /api/dashboard reads from this Mac returned 200
with 203,637 bytes each, median 1.064265 s and sample p95 2.25015 s (the first
request). Excluding that first request, the slowest was 1.11415 s. Requests
included connection setup; these are measured samples, not a universal SLA.

A public browser refresh acknowledgement took 1.3774 s and returned 202; the
work ran asynchronously and navigation remained available. The original targets
of deployed p95 below 1 s and refresh acknowledgement below 500 ms were not met
in these network samples. The service read target below 250 ms was met in the
ten-read VPS sample. The large synchronous model computation has been removed
from the dashboard request path.

## Operational interpretation and boundaries

At the release check, the live model included 626,699 L finished goods and an
estimated 179,320 L billed-stock pile against the declared 827,000 L ceiling.
This left 20,981 L modelled opening space. The displayed warehouse restriction
is conditional: the billed-stock estimate is not a reconciled physical count,
and future dispatch release is not invented. A zero tomorrow suggestion under
that assumption is not evidence of a confirmed factory stop.

Planning T means 1,000 L, not measured oil mass. Staff availability, the chosen
shift clock, uncertain starting campaigns, material readiness and source gaps
remain visible qualifications. Scheduling is a validated heuristic, not proof
of global optimality or guaranteed factory output.

Plans are saved and approved in MARK V. Submission to ji.jivo.in's separate
production-run form is not implemented or claimed. The MARK V webhook is live;
native factory webhook registration is not claimed. Polling provides current
source changes through the existing sanitized MARK IV input integration.

## Release placement and access

Source is in the existing codex-mark4 worktree, branch codex/mark4-local.
MARK IV was already merged into local main at 003c2114 before this build.
MARK V is a separate app and service; existing collectors and MARK IV remain
the source integration. Unrelated staged changes were not included in this work.

Vercel production deployment dpl_8sw7vxvkmG8NBX75N2CLawBb3Qus was built and the
short production URL returned 200 without an SSO gate. The owned systemd
mark5.service runs on loopback 8795 with SQLite outside the app directory.
Operator access is stored in the private, gitignored
codex-mark4/.mark4-local/mark5/operator-access.txt; no passcode is in source.
Known private credentials were scanned against all 80 candidate release files:
zero matches. See ops/mark5/README.md for startup, webhook and recovery details.
