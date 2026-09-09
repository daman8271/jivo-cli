# MARK IV completion — 9 September 2026

Released to https://jivo-mark4-astha.vercel.app
Deployment: dpl_9ELmSSARq21K7C4zehqK32hy6YPG (final refresh-race fix; initial release dpl_9JhCTkmNCh1HrSpVt7ETYVHPx2yi). Logged-out HTTP 200 verified.

## Delivered

- Simple actual-dispatch tables inside Godown & dispatch, with date/company filters, daily history and per-trip item loads. No new 3D dispatch scene or standalone prototype.
- Overall dispatch includes Wellness and Mart; operational ownership and original source books remain separately visible. Gupta GP-FG/GP-FGM belongs to Mart. Wellness FG/storage scope remains BH-BT/BH-PF only.
- Actual gate departures come from https://ji.jivo.in/dispatch via a separately owned complete paginated collector. The source date filter is deliberately avoided because it selects docking/creation dates. No source business records are changed.
- QC availability uses timestamps; the scheduler may use remaining working hours after readiness, resume the same product after a later receipt, and reserve shared material without consuming future supply. First-day elapsed time, Sunday closure and month-end boundaries apply.
- Existing packaging PO balances receive explicitly temporary estimates only with matching supplier/material/unit evidence. Quantities are capped at outstanding balances. Fixed review/expiry: after 10 September 2026. Recorded-only mode and the packaging toggle exclude these estimates.
- EXIM supplies opening oil. Factory RM contributes zero. Packaging warehouse rules remain separate from FG warehouse rules.
- Recorded BH-only stock snapshots are archived independently. Missing physical closing reconciliation remains unknown; previous departures are not deducted again from a newer stock observation.

## Live evidence

Public feeds:
- https://mark4-astha.srv1685505.hstgr.cloud/dispatch-now.json
- https://mark4-astha.srv1685505.hstgr.cloud/storage-evidence.json
- https://mark4-astha.srv1685505.hstgr.cloud/inputs.json
- https://jivo-mark4-astha.vercel.app/api/dispatch-board

8 September actual dispatch: 125,474.6 L / 10 Wellness+Mart trips. Operational Wellness 54,076 L / 5 trips; Mart 71,398.6 L / 5 trips. Original source Oil/Mart headers are 80,449.6 / 45,025 L. Beverages 40,783.2 L is shown separately. Only 54,076 L from BH-BT/PF participates in Wellness storage comparison. Planning tonnes are litres divided by 1,000, not measured truck weight.

Material feed refreshed from 2026-09-08T21:02:48.699634Z to 21:03:52.528919Z, retaining identical estimated readiness dates: 26 hourly receipts, including 24 temporary packaging lots and two EXIM shipment estimates. No date rolling on refresh.

BH FG observations: 591,451 L at 9 September 01:27:05 IST and 02:27:06 IST. The 183,190 L legacy billed-waiting estimate is separately labelled, not an attested BH physical count.

## Verification

- Planner TypeScript suite: 160/160; typecheck clean. Additional deferred-response refresh-race regression: 1/1 passed. Automatic refresh cannot supersede an in-flight user setting; older responses cannot unlock newer requests.
- Engine/material Python tests: 105/105.
- Root storage evidence tests: 7/7; dispatch source tests: 16/16.
- Independent actual-source replay: 36 runs / 224 material reservations, no negative chronological stock, premature start, Sunday work or line/setup overlap. Evidence is qa-release.json.
- Focused automatic-night tests: 5/5, including protecting shared material; month-end midnight regression separately retained. Two legacy full-night tests run on 29 September so they do not conflict with the month boundary.
- VPS webpack production build and Vercel production build/typecheck passed.
- Default staged model including comparison: 5.21 seconds; preview API including fetch: 5.74 seconds. Public cold model API: HTTP 200 in 13.74 seconds.
- Deployed model checked: 34 runs, all 26 timing-v2 receipts present, 24 temporary PM lots, no Sunday or pre-observation starts. Counts can differ from replay as live inputs change.
- Actual rendered desktop and mobile public pages inspected; 8 September totals, trip item expansion, Wellness filter and unresolved empty state verified. No browser console errors.

## Remaining business uncertainty

08:00 IST shift start is provisional and editable; only ten effective hours per session was documented. QC medians measure elapsed arrival-to-approval, not solely laboratory work. Expected supply assumes no further Stores delay, clearly labelled; actual Stores readiness supersedes that estimate when recorded. Missing arrival times use the late edge of the source date.

Complete physical closing-stock reconciliation is unavailable without confirmed stock-deduction timing, full intervening production/transfers/returns/adjustments and a matching physical closing count. Existing future dispatch lag remains a labelled scenario; the 100-tonne aim never automatically frees 100 tonnes of Wellness storage. Partial source coverage remains visible; this release does not claim the whole forecast is confirmed production.

Runtime changes are limited to independent Mark IV material/feed scripts and its new dispatch/storage services. Mark 3 runtime and business source records were not changed. No WhatsApp messages were sent. Runtime backups: /root/mark4-completion-20260909/runtime-backup.

Final public checks: packaging switch successfully changed false then true, persisted to the saved scenario, and excluded temporary lots when off. Shift clock renders as provisional 08:00 IST. The final deployed refresh-race fix passed Vercel build and typecheck; logged-out access remains HTTP 200.
The saved packaging choice remained true at 21:12:45Z after being applied at 21:11:41Z, through the next automatic refresh. Owned preview server and browser automation were stopped after verification.
