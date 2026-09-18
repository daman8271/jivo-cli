# Backend ladder, by file type

Pick the highest rung that is available. Higher = fewer moving parts, no app
launch, no window, and a much better failure message when it does not work.

## Spreadsheets (.xlsx / .xls / .ods / .csv)

1. **`openpyxl`** (present on this Mac, and on the fleet) — reads cells, formulas,
   sheet names, merged ranges, and cell fills. Pure Python, no app.
   ```python
   import openpyxl
   wb = openpyxl.load_workbook(path, data_only=True)   # data_only → cached values, not "=SUM(...)"
   for ws in wb.worksheets:
       print(ws.title, ws.max_row, ws.max_column)
   ```
   **Trap:** `data_only=True` returns the value Excel *last cached*. A workbook
   built by a script and never opened in Excel has no cached values — every
   formula cell reads `None`. If a column comes back all-`None`, that is why;
   fall back to LibreOffice, which recalculates.
2. **`soffice --headless --convert-to csv`** — recalculates, and handles `.xls`
   and `.ods`. Converts **one sheet only** (the first) unless you loop with a
   filter option. Slow to start. Not installed on this Mac as of 2026-08-25.
3. **Never** parse the zip/XML by hand.

## PDF

1. **`pdftotext -layout f.pdf -`** — a text PDF. `-layout` preserves columns,
   which is what makes a tax invoice readable. Empty output = there is no text
   layer, i.e. it is a scan. That is information, not an error.
2. **`pdftoppm -r 200 -png f.pdf out`** — rasterise, then read the tiles. Follow
   `ap-rm-pm`'s rule: read a scan in tiles, not whole pages, and compare
   digits only within one hand.
3. **`qpdf`** for splitting and merging without re-rendering (absent here).

## HTML → PDF / rendered DOM

`"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new
--disable-gpu --print-to-pdf=out.pdf --no-pdf-header-footer file.html`

Working precedent: `mail-cli`'s `jmail print`. Read that before writing another.
Chrome is a **bundle** on this Mac — not on PATH, still present.

## Images

`magick in.png -crop 800x600+0+0 out.png` — cropping a bill into tiles.
`magick identify -format '%w %h' f.png` — dimensions before deciding a tile grid.

## Video / audio

`ffmpeg`. Present. Long jobs go to a fleet box.

## Probing the machine you are actually on

`bash .claude/skills/press-desktop/probe.sh`. Run it on the box that will do the
work, not on the Mac if the job is going to the VPS — the answer differs per box,
and an operator's Windows machine differs most of all.
