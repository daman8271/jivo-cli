#!/usr/bin/env python3
"""Render a bilty scan to readable page images.

Transporter scans arrive sideways and the handwriting is small, so a full-page
read at thumbnail size loses digits. This renders each page big, and can rotate.

    python3 render.py "<scan.pdf>" [--dpi 200] [--rotate 270] [--out DIR]

Read-only: writes image files under --out and touches no business system.
"""
import argparse, os, shutil, subprocess, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270],
                    help="clockwise; page 1 of a Mahavir-style bill usually needs 270")
    ap.add_argument("--out", default="bilty-pages")
    a = ap.parse_args()

    if not shutil.which("pdftoppm"):
        sys.exit("pdftoppm not found - brew install poppler")
    os.makedirs(a.out, exist_ok=True)

    subprocess.run(["pdftoppm", "-r", str(a.dpi), "-png", a.pdf,
                    os.path.join(a.out, "pg")], check=True)

    pages = sorted(f for f in os.listdir(a.out) if f.startswith("pg") and f.endswith(".png"))
    for f in pages:
        p = os.path.join(a.out, f)
        if a.rotate:
            subprocess.run(["sips", "-r", str(a.rotate), p],
                           check=True, capture_output=True)
        print(p)
    print(f"\n{len(pages)} page(s). Open EVERY one with the Read tool.", file=sys.stderr)
    print("Zoom any clipped/unclear digit before trusting it:", file=sys.stderr)
    print("  python3 .claude/skills/jivo-ap-draft/bin/zoom.py <page.png> --box L,T,R,B",
          file=sys.stderr)

if __name__ == "__main__":
    main()
