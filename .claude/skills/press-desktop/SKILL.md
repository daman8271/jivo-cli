---
name: press-desktop
description: Use when the tool that has to be driven is desktop software rather than a web API — Excel/LibreOffice workbooks, PDFs and scans, Chrome, Draw.io, image or video files — and there is no HTTP endpoint to wrap. Also use when an operator asks for something that lives in a file on their machine ("read this budget xlsx", "pull the figures out of this bill", "turn this into a PDF"), or when /printing-press stalls because the target has no API at all.
---

# press-desktop — a CLI for software that has no API

`/printing-press` wraps HTTP. This wraps everything else.

Borrowed from CLI-Anything (HKUDS), whose one real insight is worth restating,
because it is the opposite of what an agent reaches for first:

> **Never automate the GUI. Call the application's own headless backend.**

Blender renders through `blender --background`, LibreOffice converts through
`soffice --headless`, Chrome prints through `--headless --print-to-pdf`. Clicking
around a window is fragile, unobservable, and breaks the moment a dialog moves.
The backend is a documented, scriptable, testable interface that has been there
all along.

We already proved the pattern before we had a name for it: `jmail print <uid>`
drives headless Chrome to turn an approval mail thread into the PDF that goes on
a payment draft. That is a desktop harness. This skill is how to build the next one.

## Phase 0 — find the backend (never skip)

```bash
bash .claude/skills/press-desktop/probe.sh
```

Three states, and the middle one is the one that gets misread:

- **present** — on PATH, drive it directly.
- **bundle** — installed, but macOS keeps the binary inside `/Applications/…app/Contents/MacOS/`,
  off PATH. It is present. An agent that only checks `command -v` will report a
  perfectly good Chrome as missing.
- **absent** — say so and stop. Do not fall back to GUI automation, and do not
  reimplement the file format by hand.

**If the file format has a pure library, prefer it to the app.** `openpyxl` reads
a `.xlsx` with no LibreOffice, no Excel, and no launch cost. Reach for the
application only when you need what the application does — rendering, layout,
conversion fidelity, formula recalculation.

See [references/backends.md](references/backends.md) for the ladder per file type.

## Phases 1–5 — the same lean loop as printing-press

1. **Probe** — Phase 0 above. Write down the exact binary path you will call.
2. **Design** — command groups by what an operator asks for, not by what the
   backend's flags happen to be. `sheet read`, `sheet cells`, `bill text`,
   `bill tiles` — not `--convert-to`.
3. **Implement** — a thin wrapper that shells out to the backend and returns
   **structured** output (`--json`). The agent-facing value is the structure; a
   wrapper that just reprints the backend's stdout has added nothing.
4. **Test against real files** — a synthetic fixture proves nothing about a
   vendor's scanned bill or a 40-sheet budget workbook. Use a real one from
   `sap-b1/entry-vault/_data/` or an actual bill, and check the numbers by hand once.
5. **Register** — add it to `hub/registry.json` so the next agent can find it.
   A harness nobody can discover gets rebuilt from scratch in a month.

## Rules

- **Read-only unless the operator asked for a file to be written.** These
  harnesses touch the operator's own machine. Converting a file is fine; writing
  over the source is not. Emit to a new path, always.
- **Never claim the backend can do something it cannot.** If `pdftotext` returns
  nothing because the PDF is a scan, say "this is a scan, there is no text layer"
  and switch to `pdftoppm` + reading the tiles. Do not guess at the numbers.
- **A figure read off a document is `inferred`, not `measured`,** until it is
  reconciled against the system of record. Handwriting especially — see
  `.claude/skills/ap-rm-pm/reference/handwriting.md` and C-0027.
- **Never launch anything with a UI.** No `open -a`, no window, no dialog. If the
  only way to do it is with a visible app, that is a finding to report, not a
  workaround to attempt.
- Long jobs (a render, a big conversion) belong on a fleet box, not the Air.
  See the `vps-handoff` skill.

## What is worth building here at JIVO

Ranked by how often the question actually comes up:

| Target | Backend | Why it earns its place |
|---|---|---|
| **Excel / workbooks** | `openpyxl`, else `soffice --headless` | Budget files, reconciliation sheets and figure files arrive as `.xlsx` constantly. Reading one without opening it is the single most repeated desktop task here. C-0032 exists because a workbook's company scope was guessed instead of read. |
| **Vendor bills / scans** | `pdftotext -layout`, `pdftoppm` + tiles | Every A/P entry starts as a PDF or a photo. The tile-reading rule (read scans in tiles, never a whole page) is already in `ap-rm-pm`. |
| **HTML → PDF** | headless Chrome | Already live as `jmail print`. Same backend prints a dashboard or a statement. |
| **Diagrams** | `drawio -x` | Only if someone actually needs it. Do not build ahead of demand. |

Build the first one when an operator asks for it, not before. **Never write
unprompted** — the rule from `CLAUDE.md` covers desktop files as much as SAP rows.
