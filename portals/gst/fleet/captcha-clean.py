#!/usr/bin/env python3
"""Clean a GST login captcha into two renders a reader can judge together.

The GST captcha is 182x50 with ~5px strokes, a grey grid overlay and a red
strike-through. Order matters and was established the hard way: upscale FIRST
(a 9x9 opening applied before upscaling erases the strokes entirely), then drop
the red, then threshold, then open.

Emits <stem>_open.png (hard, de-gridded) and <stem>_gray.png (soft, keeps
stroke shape). Two renders because the failure modes differ: the opening can eat
a thin digit, the soft one can hide a digit under the red line. Agreement across
both is the signal.
"""
import sys, numpy as np
from PIL import Image, ImageFilter

src = sys.argv[1]
stem = src.rsplit(".", 1)[0]
im = Image.open(src).convert("RGB")
big = im.resize((im.width * 6, im.height * 6), Image.LANCZOS)
a = np.array(big).astype(int)
r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
gray = a.mean(axis=2)
gray[(r - g > 50) & (r - b > 50)] = 255          # red strike-through -> background
Image.fromarray((255 - (gray < 60) * 255).astype("uint8")) \
     .filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.MinFilter(11)) \
     .save(f"{stem}_open.png")
Image.fromarray(np.clip(gray, 0, 255).astype("uint8")).save(f"{stem}_gray.png")
print(f"{stem}_open.png {stem}_gray.png")
