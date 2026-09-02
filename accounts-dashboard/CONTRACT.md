# v2 BUILD CONTRACT — binding on every agent

Every agent building JIVO Accounts Board v2 obeys this file exactly. It exists
so that ~40 agents working in parallel produce **one** application, not forty
pages that disagree about colour, currency, module names and URLs.

If this contract is silent on something, follow `site/index.html` (v1) — it is
the reference implementation for house style, tone and numeric care.

---

## 0. Hard rules

1. **No CDN. No framework. No build step. No npm.** Plain HTML + ES modules +
   hand-written SVG. The site deploys by copying `site-v2/` to Vercel.
2. **Never write to SAP.** Nothing in v2 issues any write. Read-only, per
   RULE 0. No agent runs `sapb1 draft/post/patch`. No agent runs a HANA query —
   work from `site/data.json` (already fetched, `generated_at 2026-08-22T18:50:32+05:30`).
3. **Never a confident zero.** A value that could not be computed renders as
   `not computed` with a reason. Never `₹0`, never a bare `—` where nil and
   unknown would look the same.
4. **Every number is a link.** Any rendered figure that has a derivation id gets
   `data-k="<kpi-id>"` and links to `derivation.html?k=<id>&co=<company>`.
5. **No horizontal overflow at any nesting level.** `*{box-sizing:border-box;
   min-width:0}` is already set; grid/flex children need `minmax(0,1fr)`. Wide
   tables scroll inside their own `overflow-x:auto` container, never the body.
6. **Do not touch `site/`** (that is live v1) or `pipeline/sql/*.sql` (those
   queries were adversarially reviewed; changing one silently changes the
   books). New pipeline code goes in new files.
7. **Two themes, DARK BY DEFAULT.** v1 shipped a full dark theme after its README
   was written (the README's "light-only on purpose" is STALE — do not follow it).
   Both palettes are in §6 and both are mandatory. See §6.1 for the exact
   no-flash bootstrap and toggle contract.

---

## 1. Layout on disk

```
accounts-dashboard/
  specs/<section>.json        P1 output — one per section
  pipeline/
    split_data.py             data.json  ->  site-v2/data/*.json
    derive.py                 KPI registry + derivation records
    verify.py                 independent re-derivation checks
    kpis.py                   the KPI registry itself (data, not logic)
  site-v2/
    index.html  receivables.html  payables.html  open-items.html
    grpo.html   goods-return.html return-note.html provisions.html
    cash-sale.html banks.html bank-reco.html transporter.html
    party.html  document.html  bank-account.html gl-account.html
    derivation.html methodology.html health.html search.html
    assets/board.css  core.js  charts.js  ui.js
    data/            (generated — never hand-edited)
```

One agent owns one file. Do not edit a file another agent owns.

---

## 2. Data contract

### `data/manifest.json`  — ~170 KB raw, ~27 KB gzipped; polled by every page
```jsonc
{
  "generated_at": "2026-08-22T22:48:02+05:30",
  "as_of": "2026-08-22",
  "build_seconds": 41.2,
  "stale": false, "stale_reason": null,
  "history_points": 4,
  "alerts": [{"t":"...","msg":"..."}],          // raised by the refresh loop
  "companies": [{"key":"oil","label":"JIVO Wellness (Oil)","schema":"JIVO_OIL_HANADB"}, ...],
  "sections": {                                  // 13 of them, NOT 11 — see below
    "<section>": {"status":"ok"|"error"|"empty", "error":null,
                  "rows":{"oil":N,...}, "seconds":{"oil":N,...}}
  },
  "kpis": {
    "<company>": {
      "<kpi-id>": {
        "value": 226783972.18, "unit": "INR",
        "label": "JIVO owes external suppliers (credit-adjusted)",
        "section": "vendor-ageing",
        "check": {"ok": true|false|null,         // green | red | amber
                  "alt_value": 226783972.18,     // the SECOND route's figure
                  "delta_pct": 0,
                  "method": "corroborated by a second route"}
      }
    }
  },
  "audit_summary": {"rollup_disagreements":0, "cross_section_ok":true,
                    "corrections_unverified":[], "kpi_checks_failing":38,
                    "kpi_checks_total":567}
}
```

**Read `.value`, not `.v`.** An earlier build short-keyed these to save bytes and
that silently broke every consumer written against this contract; the long keys
are the contract and they are not changing again.

**`check.ok` has three states and they are not interchangeable.**
`true` = a second, independent route produced the same figure.
`false` = the two routes genuinely disagree — show the number anyway, with the red dot.
`null` = no independent route exists for that KPI, or the difference is consistent
with movement in a live book. That is a GAP, not a contradiction; never render it
as a failure and never fold it into the `false` count.

**Everything a check tooltip needs is in the manifest** (`alt_value`, `delta_pct`,
`method`). Do NOT fetch `derivations.<co>.json` just to render a dot — it is 1.6 MB.

**There are 13 sections, not 11.** `budget-heads` and `factory-indirect` arrived on
2026-08-22 and the splitter is section-agnostic, so more may appear. Sections with
no hand-built page render through `section.html?sec=<id>`; `core.hrefSection()`
already routes them there. Never hardcode a list of eleven.

### Assets that ship WITH the site — never reach outside the deploy root

`site-v2/` **is** the Vercel deploy root, so `pipeline/` is not deployed and any
`../pipeline/...` fetch 404s in production while working fine from a repo
checkout. Two pages were written that way and rendered nothing where it mattered
(the section notes and the SQL box). The build now copies both in:

| Fetch this | Never this | What it is |
|---|---|---|
| `notes/<section>.md` | `../pipeline/notes/<section>.md` | the working note, rendered inline by `ui.note()` |
| `notes/_index.json` | — | the list of notes that exist |
| `sql/<section>.sql` | `../pipeline/sql/<section>.sql` | the full query behind the page |
| `sql/_index.json` | — | the list of queries that exist |

**Check the `_index.json` before fetching.** A fetch-and-fail logs a console 404
the page cannot suppress, and `pipeline/browser-check.sh` counts console errors as
failures — benign 404s would drown a real one. `ui.note()` already does this.

A derivation record also carries `sql.text`: the exact contributing lines, already
extracted. Use that for a single KPI; fetch `sql/<section>.sql` only for the whole
query.

### `data/<section>.<company>.json`
```jsonc
{ "section":"vendor-ageing", "company":"oil", "as_of":"2026-08-22",
  "summary":[ {...} ], "detail":[ {...} ], "error":null }
```
Column names are **unchanged from SAP/the SQL** — `ADJ_OPEN`, `EFF_OPEN_INR`,
`UB_90PLUS_GROSS`. Do not rename, do not lowercase. The unit lives in the
suffix (§4).

### `data/derivations.<company>.json`
```jsonc
{ "<kpi-id>": {
    "id":"ar-trade-open", "label":"Customers owe JIVO",
    "value":73500000.0, "unit":"INR", "as_of":"2026-08-22",
    "formula":"RAW_OPEN − UNAPPLIED_CREDIT = EFF_OPEN",
    "terms":[{"label":"Raw open invoices","col":"RAW_OPEN_INR","value":...,
              "op":"+","source":"OINV","note":"..."} ],
    "excludes":[{"label":"Intercompany","amount":...,"cards":["CUSTA000606",...],
                 "why":"C-0005"}],
    "sql":{"file":"sql/customer-ageing.sql","lines":[118,173],"text":"..."},
    "caveats":["C-0019","C-0005"],
    "rows":{"section":"customer-ageing","kind":"detail","filter":"...","top":50},
    "check":{...}
  } }
```

### `data/parties.<company>.json`
`[{"card":"VENDA000483","name":"...","group":"...","kind":"TRADE|BRANCH|INTERCO|STAFF","side":"V|C","balance":-123.45}]`

### `data/history.jsonl`
One JSON object per line: `{"t":"ISO8601","kpis":{"<co>":{"<id>":value}},"rows":{...}}`

---

## 3. `assets/core.js` — the module every page imports

Exact exported API. Page agents may **use** these and must not redefine them.

```js
// ── data ──────────────────────────────────────────────────────────────
export async function manifest()                    // cached, revalidated on poll
export async function slice(section, company)       // -> {summary, detail, error}
export async function derivations(company)          // -> {id: derivation}
export async function parties(company)
export function company()                           // current, from ?co= else localStorage else 'oil'
export function setCompany(key)                     // rewrites ?co= and reloads data in place
export function onRefresh(fn)                       // fires when generated_at moves

// ── formatting (INR, Indian grouping, crores/lakhs) ───────────────────
export function money(n, opts)      // 73500000 -> "₹7.35 Cr"  |  null -> null
export function moneyFull(n)        // -> "₹7,35,00,000"
export function num(n)              // Indian-grouped integer
export function pct(n, d)
export function scale(v, col)       // honours _L / _CR / _INR column suffix -> rupees
export function ago(iso)            // "6 min ago"
export function esc(s)

// ── linking (the drill-down spine) ────────────────────────────────────
export function hrefDerivation(kpiId, co)
export function hrefParty(card, co)
export function hrefDocument(objType, docEntry, co)
export function hrefSection(sectionId, co, params)
export function hrefBank(acct, co)
export function hrefGL(acct, co)

// ── page shell ────────────────────────────────────────────────────────
export function shell({title, subtitle, section})   // masthead + company switch + nav + freshness banner
export function kpiRow(items)                       // items: [{id,label,value,sub,tone,spark}]
export function table(rows, opts)                   // sortable, filterable, csv-copy, overflow-safe
export function checkDot(kpiId, co)                 // green/amber/red -> links to derivation
export function crumb(trail)                        // [{label, href}]
export function note(id)                            // renders pipeline/notes/<id>.md inline
export function empty(msg)                          // the "never a confident zero" renderer
```

## 4. Money units — the column suffix carries the unit

| Suffix | Unit | Example column |
|---|---|---|
| `..._L` | INR **lakhs** | `BALANCE_L` |
| `..._CR` | INR **crores** | (rare) |
| `..._INR`, anything else | INR **rupees** | `EFF_OPEN_INR`, `ADJ_OPEN` |

Always convert with `scale(v, col)` before adding two columns together.
Display: `< ₹1 L` in rupees, `< ₹1 Cr` in lakhs, else crores, 2 dp, Indian
grouping. Negative = credit; show a leading `−`, never brackets.

## 5. `assets/charts.js` — exact export names

Every chart is a pure function returning an `<svg>` element, responsive via
`viewBox` + `preserveAspectRatio`, and every one accepts `{table:true}` to also
emit the equivalent `<table>` behind a disclosure.

```js
export function waterfall(steps, opts)   // [{label,value,kind:'base'|'add'|'sub'|'total'}]
export function sparkline(values, opts)
export function pareto(items, opts)      // bars + cumulative % line
export function treemap(items, opts)
export function donut(items, opts)
export function stackedBars(rows, opts)  // ageing buckets
export function lineArea(series, opts)
export function scatter(points, opts)    // {x:days, y:amount, label, href}
export function heatmap(matrix, opts)
export function meter(value, max, opts)
export function flow(nodes, links, opts) // Sankey-lite
export function hbars(items, opts)       // kept from v1
```

Rules: every mark carries a visible value label; no chart relies on colour
alone; ageing uses `--age-nd,--age1..--age6` (sequential, "not due" is brand
green as a *state*, not a ramp step); categorical uses `--c1..--c6` **in fixed
order, never cycled**; `--ok/--warn/--bad/--info/--dead` are reserved for status
and are never used as a data series.

## 6. Design tokens — already validated, copy verbatim

```css
--brand:#0A7D3F; --brand-deep:#1F3524; --ink:#22301F;
--sage:#586055;  --soft:#8B9184;
--cream:#F5F4EF; --card:#FFFFFF; --card-warm:#FAF9F4;
--line:#E4E2D6;  --line-soft:#ECEAE0;
--c1:#0A7D3F; --c2:#1D63C4; --c3:#C2610A; --c4:#8B2E9E; --c5:#0894B0; --c6:#B01253;
--age-nd:#0A7D3F;
--age1:#D99A4E; --age2:#C97F2E; --age3:#B5651B;
--age4:#9A4D12; --age5:#7D370D; --age6:#5A2108;
--ok:#0A7D3F; --warn:#935800; --bad:#B3261E; --info:#1D5F8A; --dead:#7D786C;
--radius:14px;
--shadow:0 1px 2px rgba(31,53,36,.05), 0 8px 24px -12px rgba(31,53,36,.14);
```

### 6.1 Dark theme — mandatory, and it is the DEFAULT

v1 defaults to dark and lets the office switch back to daylight. v2 must match,
or switching between the two boards will feel like two different products.

Applied from a `data-theme` attribute set **before first paint**, so there is no
white flash. This inline script goes in `<head>` of EVERY page, before the
stylesheet link — copy it verbatim:

```html
<script>(function(){var t;try{t=localStorage.getItem('jivo-theme')}catch(e){}
 document.documentElement.setAttribute('data-theme',t==='light'?'light':'dark')})();</script>
```

Note the default: anything other than the literal string `light` means dark.
Wrap the `localStorage` read in try/catch — a private window throws.

Light values in §6 sit on bare `:root`. Redefine ONLY these under
`:root[data-theme="dark"]`:

```css
:root[data-theme="dark"]{
  color-scheme:dark;
  --brand:#3FC177; --brand-deep:#EDF4EE; --ink:#E3E9E4;
  --sage:#A3ADA5;  --soft:#7F8A81;
  --cream:#0E1311; --card:#161C18; --card-warm:#1C231E;
  --line:#2B342D;  --line-soft:#222A24;
  /* same hue order as daylight, lifted into a dark-legible band */
  --c1:#35C46F; --c2:#6BA5FF; --c3:#E8913A; --c4:#C98BE6; --c5:#3DC3DC; --c6:#F5729E;
  /* ageing: one warm hue, monotonic dim -> bright (worse = hotter). On dark the
     ramp runs the OTHER WAY from daylight — do not simply reuse the light ramp. */
  --age-nd:#3FC177;
  --age1:#97704A; --age2:#B0813F; --age3:#C69138;
  --age4:#DCA333; --age5:#EEB23D; --age6:#FFC350;
  --ok:#3FC177; --warn:#E0A63A; --bad:#FF7A6B; --info:#6BB6EE; --dead:#8B948C;
  --shadow:0 1px 2px rgba(0,0,0,.45), 0 10px 26px -14px rgba(0,0,0,.6);
  --pulse:rgba(63,193,119,.45); --pulse-0:rgba(63,193,119,0);
}
```

`ui.js` `shell()` renders the toggle button (`#themeToggle`), flips
`data-theme`, and persists to `localStorage['jivo-theme']` inside try/catch.

**Charts must read their colours from CSS variables at render time, not bake
hex literals**, or every chart stays light-themed after a toggle. Re-render or
re-resolve on theme change.

Never define a colour ONLY inside the dark block. Every token gets its light
value on bare `:root` first.

Font: `system-ui,-apple-system,"Segoe UI",Roboto,sans-serif`; numerals and codes
in `ui-monospace,SFMono-Regular,Menlo,monospace`. Existing class names
(`.kpi .lab/.val/.sub`, `.card`, `.card-head`, `.seg`, `.hbar`, `.mk`, `.stamp`,
`.live`, `.navrow`, `.wrap`, `.empty`) keep their meaning — reuse, do not rename.

## 7. Page skeleton every page follows

```html
<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title><Page> · JIVO Accounts</title>
<link rel="stylesheet" href="assets/board.css">
</head><body>
<div id="shell"></div>
<main class="wrap" id="main"><div class="empty" id="boot">Loading SAP data…</div></main>
<div class="wrap"><footer id="foot"></footer></div>
<script type="module">
  import { shell, slice, company, onRefresh /* … */ } from './assets/core.js';
  async function render(){ /* … */ }
  shell({title:'…', section:'…'}); render(); onRefresh(render);
</script>
</body></html>
```

## 8. The corrections are law

`C-0001` qty is PIECES not cartons · `C-0005` 23 intercompany CardCodes, exclude
and name them · `C-0019` `DocStatus='O'` is unreliable, age from `OCRD.Balance`
· `C-0020` intercompany vendors hide outside BRANCH groups, match `CardName` too
· `C-0021` `CANCELED` is three-valued `N`/`Y`/`C`, filter `='N'` · `C-0022` A/P
`DocDate` ≠ GRPO `DocDate` in the books · `C-0023` build a party ledger from
`JDT1`, never from document extracts.

Any page that shows a figure touched by one of these links its caveat to
`methodology.html#C-00xx`.

## 9. Definition of done, per agent

- The file you own exists, is syntactically valid, and opens with no console error.
- Every figure it renders is either linked to a derivation or explicitly marked
  as a raw source column.
- No `TODO`, no placeholder text, no invented numbers. If the data does not
  support a panel, render `empty()` with the reason.
- Report back: the file path, what it renders, which KPI ids it consumes, and
  anything in the data that blocked you.
