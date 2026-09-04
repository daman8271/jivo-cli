# site-live — JIVO Mark 3, the plant right now

Mark 2 (`../site-sep`, live at `jivo-mark2.vercel.app`) is **frozen**: the
31-August baseline the backtest is measured against. Do not touch it.

Mark 3 is a **live shell**. Mark 2 baked every number into the build. Mark 3
bakes **nothing** — the page is static, and every figure on it is fetched in the
reader's browser, every 180 seconds, from the publisher:

```
https://mark3-2ff07f84.srv1685505.hstgr.cloud/state.json       the NOW layer   (live/collect.py)
https://mark3-2ff07f84.srv1685505.hstgr.cloud/plan/<f>.json    the FORWARD layer (live/gen_live.py)
```

Both are served `Cache-Control: no-store` with CORS `*`. **A Vercel deploy is a
UI change only.** Data never needs one — which matters, because Vercel caps at
100 deploys a day and the ingest loop runs 480 times a day.

## The two rules, and how Mark 3 keeps them

**Only today is observed.** Day 1 is read off the plant; every later day is
computed from the day before plus what the planner decided. The difference from
Mark 2 is that "today" is now re-observed every three minutes, so the whole
28-day ladder is rebuilt on a fresh opening each cycle.

**Never type a business number.** Mark 2 enforced this by discipline. Mark 3
enforces it by construction: there is no data at build time to type. `npm run
check:numbers` scans `app/` and `components/` for any digit run of four or more
and any phone-shaped run, and comes back clean — the three.js hex palette lives
in `lib/webgl.ts` for exactly this reason.

## What is where

```
lib/live.ts      the ONE fetcher — polling, backoff, last-good, freshness
lib/labels.ts    plan/honesty.json's own label rules, applied at render
lib/types.ts     the publisher's field names, as it actually emits them
lib/fmt.ts       formatting only (Indian grouping, litres, tonnes, dates)
lib/webgl.ts     the WebGL probe + retry, and the 3D palette
components/      the dark-zinc idiom, carried over from Mark 2
fixtures/        one saved cycle from the publisher — the offline copy
scripts/         sync-fixtures.mjs, check-no-numbers.mjs
```

## `lib/live.ts` — the fetch design

One module-level store, shared by every mounted component. A page declares what
it needs (`useLive(["state", "overview"])`) and only those sources are polled.

| Requirement | How |
|---|---|
| 180 s interval | one 5 s scheduler ticks; each source has its own `nextAt` |
| abort on unmount | last subscriber gone → every in-flight `AbortController` aborted, ticker cleared |
| exponential backoff | 30 s → 60 → 2 m → 4 m → 8 m → 16 m → 30 m cap, ±15% jitter so sources never sync up |
| last-good in memory | a failure never overwrites `data`; it flips `stale` and records the error verbatim |
| last-good in `localStorage` | key `mark3:live:v1:<id>`; **every** read and write in `try/catch` — it throws in a private window, with site data blocked, and inside a thumbnailer |
| never trust a partial JSON | `res.ok` → `.json()` (throws on a truncated body) → a per-source shape guard. A body that parses but is the wrong shape is a **failure**, and the last-good stays on screen labelled stale |
| freshness exposed | per source `ok / fetched_at / server_at / last_good_at / stale / error / from`, and a global age off `collected_at` |

`localStorage` is hydrated inside `subscribe` (an effect), never during render,
so the first client render matches the server HTML and hydration stays clean.

An abort caused by unmounting leaves the record untouched; a request that times
out (20 s) counts as a real failure. That distinction is deliberate.

## Freshness on screen

- Every panel: **"as of HH:MM"** from its own source, with the publisher's
  `server_at`, our `fetched_at` and any error on hover. A row of stat tiles fed
  by one source carries one stamp above the row rather than four identical ones.
- Global badge off `collected_at`: green ≤ 6 min, amber ≤ 15, **red beyond —
  and red says in words that the loop is not running.** It is **also red when
  this browser cannot reach the publisher at all**, whatever stamp the last body
  happens to carry: "the loop last ran a minute ago" is true and useless while
  every panel underneath says *no fresh data*, and a green badge over that
  contradiction is the one thing this page must never do.
- A source whose last attempt failed renders its last-good body **greyed** with
  "no fresh data since HH:MM" and a *try again* button. **Never a zero, never
  blank.** A source that has never answered says so and names the error.
- **Two different things make a panel stale, and both show.** `LiveSource` greys
  a panel when a single adapter inside `state.json` failed *and* when this
  browser could not refresh `state.json` at all — in the second case every
  adapter inside the body still reports `ok`, because it was fine, minutes ago,
  in a body nobody can replace. Reading `env.ok` alone printed a plain "as of
  16:36" and a green LIVE badge over numbers the publisher had stopped serving.
- **A saved copy is not a failure.** On the first render of a session
  `localStorage`'s copy is on screen before the first fetch lands. That is
  `stale` but not failed, and it says so quietly — "this browser's saved copy
  from HH:MM — reading the plant now…" — instead of raising the amber
  no-fresh-data alarm on every single page load.

## The five persistent (non-live) badges

Each follows its input everywhere it appears, and every sentence is read from
the data rather than typed here:

| Badge | Input | Sentence comes from |
|---|---|---|
| HAND-READ DAILY | tank litres | `exim.tanks.reading_note` |
| CARRIED FORWARD | ecom targets | `ecom.targets.carried_from` |
| MEASURED ONCE | the invoice→truck lag | `factory_dispatch.lag_note.caveat` (`static: true`) |
| YOUR LIMIT | the godown ceiling | `storage.ceiling.source` (`declared: true`, `declared_by`) — Daman's own capacity sheet, ruled a fact 2026-09-04, so this one is a declared limit rather than a guess |
| ALL-TIME | the QC scoreboard, the posting backlog | `factory_inbound.notes.qc_counts_scope` |
| NOT MOVING | packaging in non-moving rooms | `overview.opening.packaging_in_non_moving_rooms_pcs`, **when the publisher ships it** — absent today, and the badge simply does not appear |

## Company scoping

Oil is the planner's company, so Oil is the headline. Cross-company figures are
shown **split and never summed into one number**: the gate table lists Oil,
Beverages and Mart as separate rows (on 3 Sep a merged "dispatched today" would
have been mostly Beverages and read as Oil), and the all-books dispatch backlog
sits in its own panel that says out loud it is all three books.

`invoiced_not_dispatched.by_company` is `{}` on a cheap cycle. The page says
"the company split only comes back on the slower read" rather than showing the
all-books figure under an Oil heading.

## Demand is always split

Three channels, three colours, everywhere: **OMS** (a real order from a shop or
distributor), **ECOM-PO** (a real dated platform order) and **FORECAST** (the
month's target spread into the month, which nobody has ordered). A row is only
treated as real when the channel, the docnum prefix and the customer string all
agree — Mark 2's triple tag, kept.

## Phone numbers

`plan/honesty.json`'s `numbers-masked` rule holds for the plan files. It does
**not** hold for `state.json`: the live gate feed carries driver names with
mobiles in them. So the site never renders `driver_name` at all, and
`maskDigits()` runs over every free-text note that reaches the DOM.

Two traps that bit this on the way in, both fixed and both worth knowing:

1. An ISO timestamp is also a long run of digits and dashes. A naive phone regex
   turned `2026-09-03T16:08` into `…T16:08`. Dates are now excluded explicitly.
2. Masking must run over **free text only**. PO numbers, GRPO numbers, bill
   numbers and lorry plates are digit runs a regex cannot tell from a mobile, so
   identifier fields are rendered raw and never passed through the mask.

## Running it

```bash
npm run dev                                  # against the live publisher
NEXT_PUBLIC_MARK3_FIXTURES=1 npm run dev     # against fixtures/ — no network at all
npm run build                                # must stay green
npm run check:numbers                        # zero business numbers in JSX
```

`fixtures/` holds one consistent cycle saved from the publisher (all ten files
share a `collected_at`). `predev`/`prebuild` copy it to `public/fixtures/`,
which is gitignored so the JSON lives in the repo exactly once.

**Turbopack caches aggressively: `rm -rf .next` after changing a
`NEXT_PUBLIC_*` value**, or the old value stays inlined in the bundle.

| Env | What it does |
|---|---|
| `NEXT_PUBLIC_MARK3_FIXTURES=1` | serve the saved copies from this origin; the nav shows a SAVED COPIES badge |
| `NEXT_PUBLIC_MARK3_BASE=<url>` | point every fetch somewhere else — how you test publisher-down |
| `NEXT_PUBLIC_MARK3_FORCE_2D=1` | skip the WebGL probe and draw the flat floor plan |

## `/floor` never shows a dead box

Probe WebGL → if it fails, wait **2 s and probe once more** → if it still fails,
draw a flat 2D floor plan carrying the same information (pad height by hours,
colour by oil, a live dot per running machine, the godown against its limit, the
gate split into ordered and expected). Daman hit the "can't draw 3D" dead box on
Mark 2; there is no state that produces one here.

## Deploying

Vercel project `jivo-mark3`, public, **not** linked to GitHub — a push does not
redeploy.

```bash
npx -y vercel deploy --prod --yes            # in site-live/
python3 ~/.claude/scripts/vercel-public.py jivo-mark3
curl -sI https://jivo-mark3.vercel.app       # must be 200, not a 302 to sso-api
```

A cloud/iPad session **cannot** do this — Vercel is blocked by the sandbox
network policy. Push the change and say it needs deploying from a machine that
can reach Vercel.

## What is deliberately not here

`/whatsapp` is gone. Mark 2's simulated drafts belong to Mark 2; the real
channel is the Jolly WhatsApp agent.

The publisher also serves `plan/build.json`, `plan/whatsapp.json`,
`plan/scenarios.json` and `plan/questions.json`. **This site never reads them.**
They are byte-identical to Mark 2's frozen 31-August `data/` — leftovers of
`loop.sh`'s `publish_plan` copying everything it finds — and `honesty.json`
`not_here` says the run list, the what-ifs and the messages are not worked out
on this run. Reading them would put August numbers under a live timestamp.
