# Phase 5 — the Mark 3 site: a live shell over the publisher

**Decision (Fable, 2026-09-03):** Mark 3 is a **new site** — `site-live/`, Vercel
project `jivo-mark3`, public — built in `site-sep/`'s idiom (dark zinc, dense,
plain language, `SimBadge`). Mark 2 at `jivo-mark2.vercel.app` **stays up,
frozen**, as the 31-August baseline the backtest is measured against.

**The one structural change:** Mark 2 baked every number into the build from
`data/*.json`. Mark 3 bakes **nothing**. The page is a static shell that fetches
from the publisher every 180 s, client-side:

```
https://mark3-2ff07f84.srv1685505.hstgr.cloud/state.json         the NOW layer (Phase 3)
https://mark3-2ff07f84.srv1685505.hstgr.cloud/plan/<file>.json   the FORWARD layer (Phase 4:
                                                                  gen-data.py output copied by loop.sh)
```

Both carry `Cache-Control: no-store` and CORS `*`. **A Vercel deploy is a UI
change only** — data never needs one (Vercel caps at 100 deploys/day; the loop
runs 480 times/day). "Never type a business number into JSX" holds by
construction: there is no data at build time to type.

## RULE 0 still applies on screen
Every figure on the site comes from ji.jivo.in / EXIM / OMS / ecom through
`state.json`. If a panel needs a number none of them has, the panel says so.

## Layers, and what each page shows

| Route | NOW (state.json) | FORWARD (plan/*.json) |
|---|---|---|
| `/` Overview | the strip: lines running now · made today (MES view, ~⅔ of the plant — say so) · trucks inside · **invoiced-not-dispatched Oil litres and % of the 827,000 L declared limit** · tank litres (badge: manual dip reading) · arrivals today · open ecom POs · OMS open (ex-outliers Rs/L beside raw) | plan left to make, sim-expected rest of month, the block→order→run loop chain |
| `/days` + `/days/[n]` | day 1 = today, opening from live | the `-live` sim days; **only day 1 is observed** stays the rule, now re-observed every 3 min |
| `/build` | **what Gautam is running right now** (line, SKU, cases, live) — from `running_now` | beside it, what the plan would run next; differences highlighted, never hidden |
| `/storage` | the pile split (PENDING / BOOKED / DOCKED-not-gone, by company, by room when heavy data is present), measured lag note (`static: true` badge) | the sim's day-by-day godown curve against Daman's declared 827,000 L limit |
| `/materials`, `/order-by` | in QC (bulk oil pending MT, packaging), on-the-way with ETAs, open bulk POs, month-pending PO lines | zero-cover gap list and order-by dates from the sim |
| `/lines` | per-line today from MES; measured vs rated basis shown | utilisation from the sim |
| `/floor` | Floor 3D — keep; **fix the WebGL failure Daman hit**: retry once after 2 s, then draw a flat 2D floor plan instead of the "can't draw 3D" box | |
| `/whatsapp` | **dropped** — simulated drafts belong to Mark 2; the real channel is the Jolly WhatsApp agent | |

## Freshness is a first-class UI element
- Every panel: `as of HH:MM` from its source's `fetched_at` (and `server_at` on hover).
- Global badge "loop last ran N min ago" from `collected_at`: green ≤ 6 min, amber
  ≤ 15, **red beyond — the cron is dead, say so in words**.
- A source with `ok:false` renders its last-good data greyed with "no fresh data
  since <last_good_at>" — **never a zero, never blank**.
- Non-live inputs carry a persistent badge: tank levels (manual daily reading),
  ecom targets (`carried_from`), the lag note (`static`). The ceiling is NOT badged — it is Daman's declared limit (C-0079, 2026-09-04).
- All-time counters (GRPO posting backlog, QC scoreboard) are labelled all-time.

## Company scoping on screen
Oil is the planner's company. Headlines are Oil. Cross-company figures (dispatch
litres, the pile) are shown **split**, never merged: on 3 Sep, 47,182 L "dispatched
today" was 89% Beverages — a merged headline would have overstated Oil 9×.

## Split the demand, always
`orders` rows render by channel — OMS (GT/MT), ECOM-PO (dated, real), FORECAST
(the plan, net) — with the same triple-tag visual distinction Mark 2 used. On a
quiet day the "new demand" figure is 100% forecast; the site must make that obvious.

## Build
- `site-live/` from `site-sep/` (copy the components/idiom; strip `data/` imports).
- `lib/live.ts`: one fetcher (`state.json` + the plan files), 180 s interval,
  abort on unmount, exponential backoff on failure, last-good kept in memory and
  `localStorage` (try/catch — it can throw), never trusts a partial JSON.
- `lib/labels.ts`: the label rules from `honesty.json` / `label_rules` applied at
  render (e.g. FG0000155 realise never headlined unqualified).
- No phone numbers anywhere (grep test in the build).
- Deploy: `npx -y vercel deploy --prod --yes` in `site-live/`, then
  `python3 ~/.claude/scripts/vercel-public.py jivo-mark3`; verify `curl -sI` → 200.
  Cloud/iPad sessions cannot deploy (Vercel blocked) — push and say so.

## Acceptance
1. `npm run build` green from a fresh clone, zero business numbers in JSX
   (grep for digit runs ≥ 4 outside `lib/`, `data-` attributes and dates).
2. With the publisher reachable: every number on screen equals `state.json` /
   `plan/*.json` to the unit (spot-check 10 across pages).
3. With the publisher **unreachable** (block the host in the test): every panel
   shows last-good greyed + "no fresh data since", the global badge goes red, nothing
   renders as 0.
4. Freshness badges present on every panel; non-live badges on the four listed inputs.
5. Oil vs cross-company never merged in a headline (check dispatch + pile).
6. `/floor` degrades to 2D when WebGL is unavailable (force it in the test).
7. Public URL returns 200 logged-out.
