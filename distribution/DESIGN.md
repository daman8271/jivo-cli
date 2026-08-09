---
name: JIVO Distribution — Godown Load Board
description: Chalk-on-blackboard dispatch console for composing JIVO toolkit bundles
---

# Design System: JIVO Distribution — Godown Load Board

## Overview

**Creative North Star: "The Godown Load Board"**

The surface is the blackboard that hangs in every JIVO godown: the board where the day's outgoing consignment gets chalked up line by line before the truck leaves. Composing a toolkit bundle is chalking a load list — you tick tools in chalk, and a paper dispatch slip pinned to the board's right edge writes itself as you go. Download is the slip's DISPATCH stamp. Two materials carry the whole world: chalk on board (the workspace) and typewritten paper (the output). Nothing else is invented.

It is an Operate surface and behaves like one: dense tabular data, standard checkbox semantics, instant feedback, no load choreography. The chalk world lives in material details — the board ground, hand-ruled hairlines, tick marks, the pinned slip — never in texture over text.

**Key Characteristics:**
- Near-monochrome: board green-black + chalk white, one marigold accent, red chalk reserved for warnings
- Hand-ruled flatness: 1px chalk hairlines, zero border radius, no shadows except the slip's paper lift
- Data in mono tabular figures, like column tallies on a real board
- The slip is the signature: a live paper artifact composing itself from your ticks

## Colors

Chalk dust on a dark board, with one marigold stick and a stub of red kept for trouble.

### Primary
- **Marigold Chalk** (#E8A63D): selection ticks, the active platform plate, the DISPATCH stamp, focus rings. The one warm accent — JIVO oil gold as a stick of chalk.

### Neutral
- **Board Black-Green** (#171C19): the page ground. A godown board, not pure black.
- **Board Panel** (#202622): grouped sections, hover rows — a patch of board wiped cleaner.
- **Chalk White** (#E9E7DF): primary text and drawn rules. Warm chalk, never #FFF.
- **Chalk Dust** (#9BA19A): secondary text, dimmed labels, disabled items.
- **Hairline** (rgba(233,231,223,0.22)): hand-ruled column and row rules.
- **Slip Paper** (#F4EDDC): the dispatch slip ground. **Slip Ink** (#2A2620): its typewritten text.

### Tertiary
- **Red Chalk** (#D8705F): warnings only — a tool with no binary for the chosen OS, a dead credential. Never decorative. (Lightened from the seed's #D4604F during build for ≥4.5:1 contrast at small sizes on Board Black-Green; slip-side warnings use ink-red #A3402F on paper.)

### Named Rules
**The One Stick Rule.** Marigold covers ≤10% of the screen. Ticks, one stamp, one active plate — its scarcity is what makes a tick feel like a decision.
**The Wet Rag Rule.** Errors and removals don't flash or shake; they wipe — a brief smear-out, like a rag across chalk.

## Typography

**Display Font:** shipped as 800-weight system-sans caps, +0.14em tracked, with a hand-drawn SVG chalk underline — no webfont, the site renders fully offline. (A painted/stencil woff2 remains a possible upgrade; embed it, never CDN it.)
**Body Font:** system sans stack (-apple-system, "Segoe UI", Roboto, sans-serif)
**Label/Mono Font:** system mono stack (ui-monospace, "SF Mono", Menlo, Consolas, monospace) — all data, counts, file sizes, slip text

**Character:** a painted board header over chalk-tally data. The mono does the talking; the sans fills quiet sentences; the display face appears exactly once.

### Hierarchy
- **Display** (board title only, caps, letterspaced): "JIVO — DISPATCH" board header.
- **Title** (600, 0.95rem, caps, +0.06em tracking): section/group headings, chalk-underlined.
- **Body** (400, 0.9rem, 1.5): descriptions, help lines. Max 70ch.
- **Label** (500, 0.75rem, +0.08em, caps): column heads, platform plates, counts.
- **Slip** (mono, 0.8rem, 1.6): everything printed on the dispatch slip.

### Named Rules
**The Texture Line.** Chalk texture (jitter, rough edges) may touch rules, ticks, underlines, and the display title. It never touches body or data text — legibility before theatre.

## Layout

A fixed board: left ~70% is the load board (tool groups as chalk-ruled columns/sections, one row per tool: tick box, name, OS availability, size); right ~30% is the pinned dispatch slip, sticky through scroll. Platform plates (MAC / WINDOWS) sit in the board header. Density is a virtue — rows at ~40px, tables can run wide inside their own scroll. One spacing rhythm (8px base); more space above headings than below. Below ~900px the slip drops beneath the board as a full-width sheet; the board never scrolls horizontally as a page.

## Elevation & Depth

Flat. The board is one plane; depth exists only where the world has it: the paper slip lifts off the board with a single soft `filter: drop-shadow(0 3px 10px rgba(0,0,0,0.4))` — drop-shadow, not box-shadow, so the lift follows the torn-edge silhouette — plus a pin/clip detail. Nothing else casts.

## Shapes

Zero border radius everywhere — chalk boxes are hand-ruled rectangles. Borders are 1px Hairline; a selected row's tick box fills with a drawn marigold check. The slip has straight edges with a subtly rough top edge (torn from the pad). No pills, no rounded chips.

## Do's and Don'ts

### Do:
- **Do** keep every interactive state: hover (Board Panel row wash), focus-visible (1px marigold outline, offset 2px), disabled (Chalk Dust + no tick box), selected (marigold tick + chalk-white name).
- **Do** render counts and sizes in mono tabular figures, right-aligned in their columns.
- **Do** make the slip update within 150ms of a tick — the composing slip IS the feedback.
- **Do** serve everything from the Go binary — fonts, CSS, JS embedded; the page must render identically with no network.

### Don't:
- **Don't** use chalk/handwriting fonts for data, labels, or the slip.
- **Don't** add a second accent, gradients, glass, or glow — the board has none.
- **Don't** animate page load or stagger row entrances; the board is simply there.
- **Don't** round a corner or cast a shadow off anything except the slip.
- **Don't** put credentials, env contents, or passwords anywhere in the DOM — the slip lists env *filenames* only.
