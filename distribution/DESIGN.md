---
name: JIVO Distribution — The Blue Folder
description: macOS-desktop bundle composer — tick tools, watch them fill a blue folder, extract one zip
---

# Design System: JIVO Distribution — The Blue Folder

## Overview

**Creative North Star: "The Blue Folder"**

The surface is a macOS desktop, and composing a toolkit bundle is the oldest ritual on it: you drop files into a folder, then you extract the archive. A grid of tool tiles is the desktop; one large blue Finder-style folder stands beside it. Ticking a tool sends a chip of it flying into the folder's mouth, the paper stack inside rises, the counter climbs. EXTRACT closes the folder and hands back one zip. Two materials carry the world: matte tiles on a dark desk, and one glossy blue object that receives them. Nothing else is invented.

*Previous world: the Godown Load Board (chalk on blackboard) — superseded 2026-08-10, see git history.*

It is an Operate surface and behaves like one: dense selectable data, standard checkbox semantics, instant state, no load choreography. The desktop world lives in one object and one motion — the folder and the fill — never in texture over text.

**Key Characteristics:**
- Near-black neutral desk with a whisper of grain, one blue accent family, amber for notes and coral for trouble
- Flat matte tiles (no gradients, no glows); status rendered as dot + small-caps type, never pills; the only glossy things on screen are the folder and EXTRACT
- Data in mono tabular figures; prose in system sans, clamped to two lines
- The folder is the signature: it visibly fills as you tick, and that fill IS the feedback

## Colors

A dark desk with one lamp on it. The blue is the macOS folder blue family and it is reserved for the folder and for "this is selected".

### Primary
- **Folder Blue** (#3B7BE8 → #71B1FB gradient on the folder; #4B90F4 as the flat accent): the folder itself, the ticked checkbox, the active target, the EXTRACT button. Nothing else may be blue. The flying chip is PAPER (white with ink text), not blue — it is a thing on its way into the folder.
- **Blue Lit** (#8ABAFF): the ticked tool's name, focus rings.

### Neutral
- **Desk** (#0B0D10): the page ground. Near-black neutral, not pure black, not tinted.
- **Desk Panel** (#101319) / **Tile** (#14181E → #1A2029): tiles, archive rows, input wells.
- **Text** (#E9EDF3): primary text. **Muted** (#9BA5B4): descriptions and notes (7.7:1 on Desk). **Dim** (#78828F): labels and metadata (4.8:1 — the floor, never used smaller than 0.66rem caps).
- **Line** (rgba(255,255,255,0.10)) / **Line 2** (0.18): tile borders and rules.
- **Paper** (#F7F9FC → #D9E2EE): the sheets stacked inside the folder. The only white in the world.

### Tertiary
- **Amber** (#F1B25A): warnings — a tool with no binary for this target, a credential known to be dead, the global burn-list banner. 10:1 on Desk.
- **Coral** (#FF8A7A): stop conditions only — unavailable component, payroll-grade contents, a failed build.
- **Mint** (#59D6A8): exactly two things — the EXTRACTED stamp and the COLLECT ZIP link.

### Named Rules
**The One Object Rule.** Blue means the folder, or a thing on its way into the folder. A blue button that does not fill the folder does not exist.
**The Honest Badge Rule.** Only `auth_mode: baked-env` may read as ready ("READY TO USE"). `auth-login`, `home-config-install` and `external-token` say what work is left; `unconfigured` reads as a gap, never as a kind of kit.

## Typography

**Display/Body Font:** Archivo (variable 400–700, vendored at `web/fonts/archivo-var.woff2`) — wordmark, section heads, descriptions, EXTRACT. Utilitarian grotesk with real character; no CDN, the woff2 ships in the repo.
**Label/Mono Font:** Fragment Mono (vendored at `web/fonts/fragment-mono-400.woff2`, system-mono fallback) — every id, count, size, badge and filename.
Offline rule unchanged: nothing is fetched at runtime except the API.

**Character:** a Finder window's restraint. Mono does the naming and the counting; sans writes the two sentences of prose per tile.

### Hierarchy
- **Section head** (mono, 0.70rem, +0.16em, caps, Dim, with a rule running off to the right): group titles.
- **Tool id** (mono, 0.86rem, 600): the tile's headline — the id, because the id is what gets POSTed.
- **Body** (sans, 0.79rem, 1.45, Muted, clamped to 2 lines): tool descriptions.
- **Note** (sans, 0.745rem, 1.5): auth notes and warnings inside the expander. Never clamped — a warning is read in full or not at all.
- **Badge / control** (mono, 0.63–0.84rem, +0.09–0.18em, caps): auth mode, tool counts, targets, EXTRACT.

### Named Rules
**The Full Reason Rule.** A reason a tile cannot be used is rendered as text in the tile. Never a `title=` tooltip, never truncated.

## Layout

Two columns: left, a responsive tile grid (`auto-fill, minmax(246px, 1fr)`) in four labelled groups — SAP & books / Ops systems / Seller portals / Desk tools — with the archive list beneath it; right, a 372px sticky panel holding the folder, its fill meter, consignee, target toggle, docs switch, global warnings and EXTRACT. Below 1080px the panel undocks to the bottom of the viewport as a sticky dock: the folder shrinks to 150px on the left, the controls reflow into two columns on the right, EXTRACT full width. 8px spacing rhythm; more space above a section head than below it. The page never scrolls horizontally.

## Elevation & Depth

The desk is flat. Depth exists in exactly one place: the folder, built as three stacked layers in a `perspective: 900px` scene — back panel (with the tab) at z0, the paper stack at z7, the front panel at z14 pivoting on `transform-origin: 50% 100%`. The whole assembly sits at a resting `rotateX(7deg)`, as if standing on the desk. Tiles lift 1px on hover and cast nothing; the ticked tile glows rather than rises (`0 10px 26px -18px` blue, plus a 1px inset ring).

## Shapes

Rounded and soft: 12px on tiles, 16px on the folder panel, 999px on badges and chips, 6–10px on controls. The folder is drawn as inline SVG paths — a back panel whose top-left rises into a tab with a slanted shoulder, and a front panel that is a rounded rectangle covering the lower 62%. Both use the same 320×210 viewBox so their coordinates line up; the paper stack sits between them in paint order, which is the whole trick.

## Motion

**The Fill.** On tick, a mono chip carrying the tool id flies from the tile into the folder mouth: FLIP (start and end `getBoundingClientRect`, animate transform only), 450ms, `cubic-bezier(0.22, 0.61, 0.36, 1)`, with a mid-keyframe lift so the path arcs. On landing, the front panel opens and bounces shut (`rotateX(0 → -17 → +4 → 0)`, 480ms) and a sheet joins the stack. Untick reverses it: the chip flies back out and fades, the stack drops. Each chip is its own animation, so rapid ticks queue naturally instead of fighting.

**The Extract.** The folder closes, the stack compresses, a single gloss sweep crosses the folder in 620ms, then the EXTRACTED stamp pops in.

### Named Rules
**The Reduced-Motion Rule.** Under `prefers-reduced-motion: reduce` there are no flights, no bounces and no sweep — the chip is never created, the sheet appears instantly, and every transition collapses to 0.001ms. The state changes; the theatre does not happen.

## Do's and Don'ts

### Do:
- **Do** keep every interactive state: hover (border lifts to Line 2), focus-visible (2px Blue Lit, 2px offset), disabled (62% opacity, flat panel, tick disabled), selected (blue border + glow + Blue Lit id).
- **Do** render counts and sizes in mono tabular figures.
- **Do** update the fill meter (`aria-live="polite"`) the instant a tick lands, before the chip finishes flying.
- **Do** show `warnings` and `skipped` from the build response above the download link, always.
- **Do** ship everything from the repo — no CDN, no webfont, no runtime fetch except the API.

### Don't:
- **Don't** add a second accent colour, or use blue for anything that is not the folder or a selection.
- **Don't** hardcode a component id, name, size, target or auth label — the grid renders from `GET /api/manifest` alone.
- **Don't** hide a reason in a tooltip, and don't truncate a warning.
- **Don't** auto-download when the build returned warnings or the selection was sensitive — render COLLECT ZIP and make it a second click.
- **Don't** put credentials, env contents or passwords anywhere in the DOM — env *filenames* only.
- **Don't** animate page load or stagger the tiles in; the desktop is simply there.
