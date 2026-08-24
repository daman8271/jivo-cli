#!/usr/bin/env python3
"""zoom — render a scanned bill big, then cut it into overlapping tiles.

Why this exists: on 2026-08-24 an A/P draft went out with the wrong Budget
dimension because the paper's handwritten "Common" was a small mark sitting on
top of a rubber stamp. Read as one shrunk full page it looked like scribble; at
300 dpi in its own tile it is unmistakable. **A full-page read is for the
printed grid; handwriting is read from tiles.**

    python3 zoom.py "<scan.pdf>" [--page 1] [--dpi 300] [--grid 3x3]
                    [--overlap 0.18] [--out DIR] [--box L,T,R,B]

It prints the files it wrote, in reading order. Open each one with the Read
tool — every tile, not a sample: the mark that changes a field is usually the
one in the corner nobody looked at.

`--box` (fractions of the page, 0-1) crops one region instead of tiling, for
when you already know where to look: --box 0,0.55,0.5,0.8 is the bottom-left
quadrant where JIVO's gate stamp and approvals live.

Read-only: touches no business system, writes only image files under --out.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile

try:
    from PIL import Image
except ImportError:                                          # pragma: no cover
    sys.exit("zoom: needs Pillow (python3 -m pip install pillow)")

Image.MAX_IMAGE_PIXELS = None          # scans at 600 dpi trip the decompression guard


def render(pdf: pathlib.Path, page: int, dpi: int, workdir: pathlib.Path) -> pathlib.Path:
    """One page of a PDF → a PNG at `dpi`, via pdftoppm (poppler)."""
    if not shutil.which("pdftoppm"):
        sys.exit("zoom: pdftoppm not found (brew install poppler)")
    stem = workdir / "page"
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi),
                    "-f", str(page), "-l", str(page), str(pdf), str(stem)],
                   check=True, capture_output=True)
    made = sorted(workdir.glob("page*.png"))
    if not made:
        sys.exit(f"zoom: pdftoppm produced nothing for page {page} of {pdf.name}")
    return made[0]


def grid_tiles(w: int, h: int, cols: int, rows: int, overlap: float):
    """Overlapping tile boxes. Overlap matters: a word split down the middle by a
    hard grid is exactly the word that gets misread."""
    tw, th = w / cols, h / rows
    ox, oy = tw * overlap, th * overlap
    for r in range(rows):
        for c in range(cols):
            yield (r, c,
                   (max(0, int(c * tw - ox)), max(0, int(r * th - oy)),
                    min(w, int((c + 1) * tw + ox)), min(h, int((r + 1) * th + oy))))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", help="the scan (PDF, or an image — PNG/JPG pass straight through)")
    ap.add_argument("--page", type=int, default=1, help="1-based page number (default 1)")
    ap.add_argument("--dpi", type=int, default=300, help="render resolution (default 300; 400-600 for faint pen)")
    ap.add_argument("--grid", default="3x3", help="COLSxROWS, e.g. 3x3 (default) or 2x4")
    ap.add_argument("--overlap", type=float, default=0.18, help="tile overlap as a fraction (default 0.18)")
    ap.add_argument("--box", help="crop ONE region instead of tiling: L,T,R,B as page fractions 0-1")
    ap.add_argument("--out", help="output directory (default: alongside in a <stem>-zoom folder)")
    a = ap.parse_args()

    pdf = pathlib.Path(a.pdf).expanduser()
    if not pdf.exists():
        sys.exit(f"zoom: no such file: {pdf}")
    out = pathlib.Path(a.out).expanduser() if a.out else pdf.with_name(pdf.stem + "-zoom")
    out.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        if pdf.suffix.lower() == ".pdf":
            src = render(pdf, a.page, a.dpi, pathlib.Path(tmp))
        else:
            src = pdf
        with Image.open(src) as im:
            im = im.convert("RGB")
            w, h = im.size
            print(f"page {a.page} of {pdf.name} at {a.dpi} dpi → {w}×{h} px")

            if a.box:
                try:
                    l, t, r, b = (float(x) for x in a.box.split(","))
                except ValueError:
                    sys.exit("zoom: --box wants four fractions, e.g. 0,0.55,0.5,0.8")
                box = (int(l * w), int(t * h), int(r * w), int(b * h))
                if box[2] <= box[0] or box[3] <= box[1]:
                    sys.exit(f"zoom: --box is empty after scaling: {box}")
                p = out / f"{pdf.stem}-p{a.page}-box.png"
                im.crop(box).save(p)
                print(f"  {p}")
                return

            try:
                cols, rows = (int(x) for x in a.grid.lower().split("x"))
            except ValueError:
                sys.exit("zoom: --grid wants COLSxROWS, e.g. 3x3")
            if cols < 1 or rows < 1:
                sys.exit("zoom: --grid must be at least 1x1")
            written = []
            for r, c, box in grid_tiles(w, h, cols, rows, a.overlap):
                p = out / f"{pdf.stem}-p{a.page}-r{r + 1}c{c + 1}.png"
                im.crop(box).save(p)
                written.append(p)
            print(f"{len(written)} tiles ({cols}×{rows}, {int(a.overlap * 100)}% overlap) — "
                  "Read every one, in this order:")
            for p in written:
                print(f"  {p}")


if __name__ == "__main__":
    main()
