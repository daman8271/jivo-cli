# Astha live shift comparison — 8 September 2026

Public release: https://jivo-mark4-astha.vercel.app/#today
Deployment: `dpl_ACYTdCJuoMveBvP9FRdiFb6yBkhQ`.

The Shift board now compares each machine's factory-reported activity, the shared
original daily plan, and a recommendation for the next production batch. The
existing scenario remains separately labeled and cannot replace the original.

## Data and persistence

- `collect_factory_now.py` polls the factory's documented live/no-cache Oil runs
  and daily-production endpoints every 60 seconds. Status requires matching
  IN_PROGRESS identity, explicit live_status, and consistent timing segments.
  Old open headers, conflicting activity, missing lines, and source failures are
  qualified rather than represented as current production.
- Segment cases × factory pieces per case supply recorded quantity. Header
  total_production is not used. A live open segment may have unentered output.
- `/factory-now.json` and `/shift-baseline.json` are read-only, exact public
  routes in the existing independent Astha publisher.
- `mark4-astha-baseline.timer` checks each minute and atomically saves the first
  valid current-IST-day plan under `state/baselines/YYYY-MM-DD.json`. It cannot
  overwrite an existing day. This is independent of visitors and scenarios.
- Today's first saved plan is stamped 19:32:37 IST. No earlier morning snapshot
  is claimed. This initial baseline has no at-capture production counters, so
  since-save progress is unavailable. Subsequent captures store counters;
  comparisons use deltas and reject resets/disappeared rows. A complete empty
  pre-production report is a valid zero recorded-count baseline, not proof of idle.
- Factory-status checks run every 60 seconds; the comparison page checks every
  30 seconds, ages its freshness display every second, and refreshes on reconnect
  or returning to the tab. The existing scenario projection polls every 60 seconds.
- Astha materials and factory supplements target 60-second cycles; demand is
  scheduled every minute without overlapping instances. Material gate requests
  use eight workers, warehouse reads four, and reuse TLS contexts. Gates are
  still observed before warehouse stock. Empty material-less gate records remain
  tracked without irrelevant detail failures invalidating material coverage.

## Recommendation limits

Advice shares usable recorded stock, current recorded room and remaining SKU
demand across machines. It uses verified recipes/routes and eligible order rows
after FG allocation. Expected receipts and future simulated dispatch cannot
create ready-now material or space. Exact overdue uncovered orders can justify
reviewing an alternative at the next changeover; disagreement alone is not wrong.

Factory reports are operator records, not physical sensors. Tank dips remain
manual readings. The inherited FG/storage/backlog estimates and incomplete order
coverage retain their source dates and limitations; minutely polling does not
turn them into a reconciled physical inventory. Advice remains conditional where
these inputs or machine coverage need confirmation. Static recipes, historical
order discovery and other slower evidence are not relabeled as fresh observations.

## Verified release

Evidence is in `live-shift-evidence/`:

- 95 JavaScript tests, 14 Python collector/feed tests, clean TypeScript, and the
  final production build.
- Independent live replay: all six actual rows match the factory feed; a scenario
  POST and repeated refreshes preserve the baseline. Failure, future timestamps,
  counter offsets/resets, missing counters and midnight captures were exercised.
- Logged-out public HTML and the new API return 200. Two production responses
  carry different factory revisions and identical saved baseline objects.
- Desktop, mobile (390px without horizontal page overflow), light and dark
  themes inspected. A browser-only simulated outage retains all six rows while
  changing advice to recheck; automatic polling restores the fresh state.
- Production collector logs show successive successful material cycles around
  51–57 seconds, and factory observations one minute apart. Network latency can
  extend a cycle; the real timestamp and failed/stale state remain visible.

## Operations

Owned services: `mark4-astha-now`, `mark4-astha-inputs`, `mark4-astha-materials`,
`mark4-astha-factory`, `mark4-astha-demand.timer`, `mark4-astha-baseline.timer`.
Unit definitions are under `ops/mark4/`. Runtime source is `/root/mark4-astha/app`;
publisher source is `/root/mark4-astha/feed`. Private runtime data is not committed.
Pre-change service/source backups: `/root/mark4-astha/live-board-backup-20260908`.

No Mark 2/3 or other Mark 4 project's collectors, deployment, or schedule changed.
No SAP or factory business record was written. No Git commit/push was performed.
