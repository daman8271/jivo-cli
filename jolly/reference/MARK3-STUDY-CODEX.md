# Mark 3 product study for the local Mark 4 experiment

Studied 6 September 2026, around 02:00 IST. This is a dated observation, not a live status report.

## What we are building

A factory planning workspace for the monthly planner, production in-charge, purchase desk and godown team. It joins recorded past days, the current plant position, and a computed plan through month-end. The intended operating loop is: identify demand, find a feasible machine and available ingredients/packaging, identify a blocking material, work out when to order it, run something else while waiting, then resume after it arrives. Warehouse capacity and physical dispatch constrain production throughout.

The current product presents plans and purchase suggestions. This review found no operator workflow on the visited pages that submits purchase orders or tells the factory to execute a run. Simulated purchases are events in the model, not confirmed business transactions.

## Pages visited live

- https://jivo-mark3.vercel.app/ — current plant tiles; forward month outcome; confirmed versus expected demand; products with no compatible machine; blocker chains; source/assumption disclosures.
- https://jivo-mark3.vercel.app/build — actual machine activity alongside today's proposed runs; goods receipts distinguished from machine production; recent runs and warehouse movements.
- https://jivo-mark3.vercel.app/days — earlier factory records next to the future plan. Booked production and machine-log production stay separate; missing records are not zeros.
- https://jivo-mark3.vercel.app/days/2 — a future day's machine/product quantities, changeovers, shortages, material arrivals and demand. The route number is relative to the rolling opening, not the calendar date.
- https://jivo-mark3.vercel.app/lines — per-machine totals, hours and pack-size speeds, with rated/observed/derived origins.
- https://jivo-mark3.vercel.app/storage — unsold finished goods plus billed goods awaiting trucks, the owner's capacity limit, dispatch lag and future occupancy.
- https://jivo-mark3.vercel.app/materials — tanks, incoming oil, QC-held supplies, packing stock and shortages.
- https://jivo-mark3.vercel.app/order-by — material requirements and last ordering dates, lateness/zero-stock filters and search.
- https://jivo-mark3.vercel.app/floor — interactive day selector and machine/warehouse view; the initial 3D render failed in this headless browser. This does not establish failure on the owner's iPad.

The top-level routes and one future-day route returned HTTP 200. The site showed recent collection and plan rebuild stamps during inspection. This establishes what the public UI displayed, not independent verification of factory quantities.

## Data flow checked in code

Factory adapters, EXIM, OMS and ecom -> live/collect.py -> state.json -> live/freeze_live.py -> sim/live-inputs.json -> engine/august_sim.py -> live/gen_live.py -> plan JSON -> site-live/lib/live.ts -> client pages.

live/loop.sh orchestrates collection and replanning independently: a good data collection can coexist with a failed plan rebuild. The frontend shows both clocks and retains last-good data with stale labels. A deploy changes the shell; the data publisher changes the numbers.

Factory truth comes from ji.jivo.in. EXIM owns tank readings/monthly targets, OMS supplies distributor/shop orders, and ecom supplies platform POs. Reads have different real cadences; refreshing a panel does not make a manual tank dip newly measured.

## Material findings to consider before defining Mark 4

1. VERIFIED: past-day production is now available and shown, but is not netted off the monthly plan. live/freeze_live.py explicitly leaves pieces_made_mtd null and says history is not used by the engine on this run. Agree the target definition before implementing subtraction; do not blindly subtract overlapping stock/production quantities.
2. VERIFIED: the UI's billed-but-waiting Oil figure is labelled REAL, while the disclosed calculation apportions an all-company backlog using a company share from a slower read. That is an estimate based on live inputs, not an individually reconciled physical inventory count.
3. VERIFIED: future oil arrivals include assumptions about undrawn blanket contracts and lead times; machine rates include derived rates and additional derating; non-moving packaging availability remains explicitly unresolved. These qualifications affect what a proposed schedule means.
4. OBSERVED: the interface is dense and repeats long technical source notes. A clearer list of decisions, owners, deadlines and expected effects is a possible Mark 4 direction, not an agreed specification.
5. LIMIT: aggregate August agreement is the site's calibration claim. This study did not rerun that backtest or establish day/product/machine prediction accuracy.

## Local experiment setup

Worktree: /Users/damanpreetsingh/jivo-cli/.claude/worktrees/codex-mark4
Branch: codex/mark4-local, initial base b1c6facf.
Original main checkout and its uncommitted application changes were not copied over or edited. Mark 3 code was clean there when the worktree was created.

Current project credential files were copied with owner-only permissions. Factory/ecom/OMS auth configs were separately copied; source ../.mark4-local/activate.sh from jolly before CLI work. Ecom has a private wrapper and renewal helpers. Credential paths are ignored and removed from this worktree index, while remaining on disk. Earlier Git history still contains the credentials that were already tracked. Remote login validity has not been refreshed or verified.

Dependencies were independently copied using APFS clone copy. Baseline checks passed: 87 existing Python tests, frontend number scan, TypeScript no-emit check and launcher/helper shell syntax.

Local launcher: ../.mark4-local/start-local.sh from jolly. It binds 127.0.0.1:3404. No server is running yet. No deploy or production collection job was started.

The Mark 4 feature scope remains for Daman to define.
