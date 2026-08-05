# Design — JIVO Godown Board

<!-- world: "JIVO daylight" — the brand's own light language (jivo.in), applied
     to an ops board. Supersedes the split-flap concourse world on the user's
     explicit steer 2026-08-01 ("make this like our brand colours" + "not so
     robotic style"). The two-boards structure and all data semantics carried
     over unchanged. -->

One surface: a public, daily-refreshed stock board (`site/index.html`,
Operate mode).

## Palette (from jivo.in, verified live 2026-08-01)

| Token | Value | Use |
|---|---|---|
| `--brand` | `#0A7D3F` | JIVO green: wordmark, key figures, active states, links |
| `--brand-deep` | `#1F3524` | section headings |
| `--ink` | `#22301F` | body text |
| `--sage` / `--soft` | `#586055` / `#8B9184` | secondary / tertiary text |
| `--cream` | `#F5F4EF` | page ground |
| `--card` / `--card-warm` | `#FFFFFF` / `#FAF9F4` | cards / hover & sub-rows |
| `--line` / `--line-soft` | `#E4E2D6` / `#ECEAE0` | borders, hairlines |
| status | OUT `#B3261E`, LOW `#935800`, HIGH `#1D5F8A`, DEAD `#7D786C`, OK `#0A7D3F` | soft-tinted pills, word always shown |

Light-only, deliberately: it mirrors the brand site and reads in daylight on a
phone. Color is never the sole signal.

## Type & voice

- **System stack** (`system-ui`) for everything except the **Oswald** accents
  (embedded data-URI, OFL): the `JIVO` wordmark and the big card values.
- Sentence case throughout; no tracking games, no mono-as-costume
  (tabular-nums via `font-variant-numeric`). SAP item names stay as stored
  (caps) — data truth, not styling.
- Warm plain copy: "Goods in godowns ₹52.42 Cr", "All clear — nothing short".

## Components

- White cards, 14px radius, 1px warm border, soft two-layer shadow.
- Status pills (999px radius, tinted bg + dark accessible text).
- Filters: pill toggles; active = solid brand green with white text.
- Boards keep their colored dot markers (amber = less, blue = more).
- Tables: sticky white header inside `.tscroll.tall`; rows
  `content-visibility:auto`; every table scrolls in its own container.
- **Glass dock** (`assets/dock.js`): fixed bottom-centre navigation pill on
  all 7 pages — the design system's **single glassmorphism element**, added
  on user request 2026-08-02 (Apple-style dock reference). True glass
  (`rgba(255,255,255,.55)` + `backdrop-filter: blur(18px) saturate(1.4)`,
  solid cream fallback), lucide stroke icons, macOS magnification physics
  under a fine pointer (44→76px, rAF + lerp), tooltip chips, brand-green
  active dot. Touch: fixed 44px, no magnify. Nothing else on the surface
  may go glassy.

## Motion

One subtle moment: the masthead card rises 6px on load (500ms). Everything
else is 150ms state feedback. `prefers-reduced-motion` respected.

## History

v1 (superseded): split-flap concourse board — dark flap cells, steel bezel,
amber dot-matrix ticker. Archived reference: `.impeccable/baseline-index.html`
(pre-design workflow baseline) and git history once committed.
