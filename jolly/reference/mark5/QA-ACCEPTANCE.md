# MARK V independent acceptance QA

10 September 2026. Owner: independent Proof QA. Scope is
`site-mark5/tests/mark5-acceptance.test.ts` and this report; business code belongs
to the engine builder. Tests use deterministic synthetic Mark4Input fixtures
adapted from the existing MARK IV acceptance fixture shape, not live totals.

Authority: IMPLEMENTATION-PLAN.md, WORKING-RULES.md and all seven machine specs.
The implementation plan explicitly selects lower speed endpoints, six-hour JP
setup, ten-hour sessions and day-first allocation. Those choices resolve the
earlier machine documents' open scheduling selections without rewriting the
approved source ranges.

## Execution record

All execution on VPS, `/root/mark5-build/app`, Node v22.22.2:

```
node --experimental-strip-types --test tests/mark5-acceptance.test.ts
```

Initial policy run: **9 tests, 8 passed, 1 failed, none skipped**, process exit 1.
Duration 195.54955 ms. Actual failure: unknown opening JP setup returned 60
minutes, expected the implementation plan's conditional 360-minute reservation.
Reported to engine owner. Fixed by the builder and verified by subsequent runs.

Verified initial coverage: all seven machine rates and preserved ranges; physical
pack restrictions; JP six-hour combined change and flushing reuse; heads combined
setup without extra parts charge; Clear Pack additive mustard/1-to-5 work;
direction-sensitive head change; combo physical/sales-unit distinction; invalid
physical counts/fills and explicit identity holds.

Expanded run: **23 tests, 23 passed, zero failures/skips**, process exit 0;
350.079397 ms. Full TAP output: VPS `/tmp/mark5-acceptance.tap`.
Two initial actuals fixtures were corrected to include a zero-demand SKU so the
then-existing input validator accepted them. The timed-receipt fixture was also
completed with its required dated availability evidence before passing. Those
were fixture corrections, not hidden business-code failures.

Additional verified coverage:

- JP six-hour setup and four-hour fill fit a ten-hour window; continuation and
  two-bottle sales units preserve bottles, cases, litres and rate division.
- Every occupied session counts setup plus filling, night uses at most one
  physical line, Sunday closes and Saturday night cannot cross Sunday midnight.
- Later day machines receive scarce shared oil before night; inventory remains
  conserved across all seven forecast dates. Finite warehouse headroom is shared.
- Separate pouch rates share one finite film/container inventory; generic pouch
  actuals are counted once and not attributed to either physical machine.
- Missing source or null run litres remain unknown. Builder corrected the null
  headline path before its passing run.
- Invalid quantities, an invented rate-edit action, Manual as a machine,
  unsupported routes and stock-exceeding exact requests fail validation.
- Nonintegral carton reciprocal does not become a verified case size; source
  timestamp remains unchanged; unproven raw opening oil is withheld without EXIM.
- A receipt with verified 16:30 availability cannot support earlier filling and
  its stock is credited only once.
- Current MES reduces remaining monthly make once; live FG already covering an
  order is not credited a second time via the same current production.

Targeted TypeScript check also exited 0 on the VPS:

```
./node_modules/.bin/tsc --noEmit --allowImportingTsExtensions --module esnext --moduleResolution bundler --target es2022 --skipLibCheck tests/mark5-acceptance.test.ts
```

Test file SHA-256:
`6b75773c00b072d269d03f1770823abf912f13918f2217ca211410891d0d21e7`.
Tested engine SHA-256:
`08c9f0b1ab6f501da5c2fd1b4989dccb586de3c5b4626ca100f17f6cbede5565`.
Tested machine-policy SHA-256:
`126eb40514a71726829ef5641c930781281d7d34dab491f8234c80dfff958370`.

Final synchronized rerun: **23/23 passed**, zero failures/skips, 334.458916 ms.
VPS and local SHA-256 matched at this rerun:

- Engine: `fa692f7335d5bbc4fa7846db791458edf4293baf281ad357ea04a8e447f52676`
- Machine policy: `af784055e5ae726bf1f5458e164b9c6da735b64f33810a381574e6e309412600`
- Test file unchanged, as above.

Final TAP: VPS `/tmp/mark5-acceptance-final.tap`. Later source changes require
their own verification. This acceptance covers the stated deterministic cases,
not proof of global schedule optimality, factory-measured efficiency,
persistence/security/UI checks or release.

## Isolated positive browser fixture

`site-mark5/qa/browser_fixture.py` runs the real Service, engine, authentication,
SQLite persistence and manual AI provider path. Only input/factory source data
are synthetic. Automatic AI is disabled; no engine or AI function is mocked.

VPS service: `127.0.0.1:8876`, dedicated database
`/root/mark5-build/fixture.sqlite`, log `/root/mark5-build/fixture.log`, PID file
`/root/mark5-build/fixture.pid`. Load the existing private service environment,
then run from `/root/mark5-build/app`:

```
MARK5_QA_DB=/root/mark5-build/fixture.sqlite python3 qa/browser_fixture.py --port 8876
```

Bootstrap used a real queued refresh and succeeded. Initial tomorrow (11 Sep)
had 125,000 L: Tin Head 90,000 L / 6,000 cases at one tin per case and JP 35,000 L
/ 1,750 cases at 20 bottles per case. Sunflower 2 L is also available with six
bottles per case. These are synthetic test results, not factory claims. The source
and SKU labels explicitly identify QA data; FactoryNow has six valid aggregate
source-line slots with unknown observations and no fabricated actual production.

`python3 -m py_compile qa/browser_fixture.py` passed on VPS. Browser editing,
approval and restart flows are performed by the root reviewer; this harness
startup did not approve a plan or submit anything to a business system.
