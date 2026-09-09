# MARK IV actual production review

Published just after midnight IST on 9 September 2026 to the existing `jivo-mark4-astha` project.

User's September 8 review: https://jivo-mark4-astha.vercel.app/?reviewDate=2026-09-08#today-review

The new navigation entry is **Today's review**. It shows dated factory segment output by machine, the original saved plan and its reasons, exact product/machine overlap, explicitly unconfirmed possible explanations, source coverage, and why a better/worse conclusion is not established. It excludes not-started drafts and distinguishes unentered quantities from zero production. Historical recommendations remain unchanged.

September 8 evidence: 34,020 L entered across six started run records; two not-started drafts excluded; two of six exact SKU/machine pairs also appear in the saved plan. The baseline was captured at 19:32 IST after production had begun, without output counters at capture. This is descriptive overlap, not attainment or proof of advance prediction. Overlapping machine segments and unresolved warehouse policy are disclosed.

Verification:

- 131 JavaScript tests, 23 Python checks and typecheck passed; production build passed.
- Independent code review found no remaining material findings after temporal, archive and privacy fixes.
- Rendered preview checked on desktop (1280 px) and mobile (390 px); no horizontal document overflow.
- Production root returned HTTP 200 without login or redirects. Public-project check: already public, zero failures.
- After midnight, September 8's dated API returned the correct factory date, baseline date, 34,020 L and capture timestamp with no source errors.
- September 9's API returned September 9 factory data and an explicit unavailable baseline, rather than borrowing the earlier plan.
- Production browser deep link showed Historical factory review, Today is 9 September 2026, 34,020 L, six line cards, the late-capture explanation and Not established verdict; mobile width and document width both 390 px.

Deployment: `6XXFzuoa822UsMphC9zRV9s3H6Ex`, aliased to the existing short production domain. Stage: `/root/mark4-today-review-20260908`. Runtime backup: `/root/mark4-today-review-backup-20260908`.

Thirteen owned files synced to `/root/mark4-astha/app`. The isolated feed's three script dependencies were updated. Only `mark4-astha-inputs.service` and `mark4-astha-now.service` were restarted; feed health returned true. The September 8 sanitized factory and baseline archives were preserved under `/root/mark4-astha/state/reviews/2026-09-08/`.

No monthly target, warehouse policy, factory business record, Mark 3 application or main checkout was changed by this page release. The separate Plan 44 comparison documents the remaining input discrepancies.
