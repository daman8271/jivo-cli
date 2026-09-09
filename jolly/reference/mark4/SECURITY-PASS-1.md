# Security pass1 — feed boundary

Sentinel reviewed sanitizer/HTTP feed on6September2026. Recursive allowlist leaks fixed before exposure. Independently passed11tests (builder added a12th carry case). Public HTTPS200,740103bytes scanned with zero private-field/path/email/JWT matches. Fixed read paths, exact GET routes, no writes, loopback upstream; rate-carry scalar allowlist independently verified. Confidence high for inspected boundary.

## Final API review and public runtime closure — 6 September 2026

This supersedes the initial pending API gate. Sentinel subsequently reviewed the input loader and scenario API and reported no unresolved release blocker in the inspected code: bounded request/upstream streams, strict scenario dimensions, fixed HTTPS upstream with redirects rejected, bounded timeout, 12 new model builds/minute per instance, 30-second function limit, and generic public errors. This is scoped review evidence, not a claim that all possible security risks are eliminated.

Parent then exercised the actual public API. `HTTP-PUBLIC.json` records: valid default/scenario responses 200; invalid efficiency/line/boolean/extra sourceUrl and malformed JSON 400; oversized body 413; response private-field/path/JWT scan passed. No request can choose a private upstream URL. `HTTP-PREVIEW.json` records the preceding preview run.

The final feed test suite passes 15/15 with exit code 0, including recursive private canaries, hashed stable order identity, retained original timestamps, retained/error headers and exact read-only routes. Live `/healthz` returned 200 with `ok:true, retainedLastGood:false` at final verification. The public app serves logged-out 200. `.env*` is excluded from the app-only Vercel upload; no project credentials were deployed with the app.

Security release gate: passed for the reviewed boundary and exercised runtime cases. Confidence: high for these specific checks. Per-instance build limiting is not a global distributed denial-of-service guarantee.
