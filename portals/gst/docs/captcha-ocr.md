# GST captcha OCR feasibility — findings

Nothing was written to the repo; all working files are in the scratchpad (`captcha_ocr.py`, `*-clean.png`). No credentials touched or printed.

## (a) Tooling on this Mac

```
$ which tesseract; tesseract --version
/opt/homebrew/bin/tesseract
tesseract 5.5.2  (leptonica-1.87.0)
$ brew list tesseract        # Homebrew present at /opt/homebrew/bin/brew
/opt/homebrew/Cellar/tesseract/5.5.2/...
$ tesseract --list-langs
eng, osd, snum
$ python3 --version          # /opt/homebrew/bin/python3 -> 3.14.7
pytesseract  MISSING
PIL          OK 12.2.0
cv2          MISSING
numpy        OK 2.4.5
scipy        OK 1.17.1       (used for morphology instead of cv2)
```

`snum` is a serial-number model that Homebrew's tesseract formula bundles by default (`brew cat tesseract` → resource from `USCDataScience/counterfeit-electronics-tesseract`). It turned out to be the only model that works at all on these captchas. It exists on any `brew install tesseract` Mac; a Linux box (VPS) would need that one file fetched.

## (b) OCR results

The captcha is harder than "digits on a grid": the grid lines are **black like the digits** (37% of pixels are black), there is a fisheye warp in the middle, digits overlap, and the background is a dark-to-light gradient. Raw tesseract reads nothing:

```
$ tesseract captcha1.png - --psm 7 -c tessedit_char_whitelist=0123456789   → ""
(psm 8: "1" / "" / "")
```

**Pipeline** (`/private/tmp/claude-501/-Users-damanpreetsingh-jivo-cli/84155c82-d76d-4f82-b84d-67109c30f276/scratchpad/captcha_ocr.py`, Pillow+numpy+scipy, tesseract via subprocess):
1. red mask `R − max(G,B) > 40`, dilated 2 px (catches the dark-red anti-aliased fringe)
2. inpaint red pixels from nearest non-red pixel, biased vertically (`distance_transform_edt(sampling=(1,3))`)
3. grey threshold `L < 40` → digits + grid
4. **binary opening with 9x9** — kills the 2-6 px grid lines, keeps 14-30 px digit strokes
5. drop blobs < 150 px, invert to black-on-white, 24 px border
6. `tesseract --psm 7|8 -l snum -c tessedit_char_whitelist=0123456789`

Cleaned images saved next to the originals: `captcha1-clean.png`, `captcha02-clean.png`, `captcha03-clean.png`, `captcha04-clean.png`. Visually the glyphs are clean — grid and red line fully gone, only a frame stub left at the edges.

Grid search (144 combos: thr 30/40 × open 9/11/13 × close 0/5 × scale 1/0.5 × psm 7/8/13 × eng/snum), `python3 captcha_ocr.py grid`:

| model | best config | 357108 | 167706 | 493355 | exact |
|---|---|---|---|---|---|
| snum | thr40 open9 close0 psm7/8 | 357108 | **167705** | 493355 | 2/3 |
| eng | thr30 open9 psm8 | 357108 | 1677006 | 35 | 1/3 |

Added the unlabelled `captcha04.png` (I read it visually as **486062**, unverified): snum → 466362, eng → 80062. Both wrong.

Honest tally for the best single config over 4 samples: **exact 2/4 (50%), per-digit ~83-88%** (edit distance 4/24). With a border-stub-removal tweak captcha1 flipped to 557108 — the reads are fragile to small perturbations. A vote ensemble over 8 snum reads (thr×kernel×psm) gave 2/4. Simulating the CLI's real input (downscale to 182x50, re-upscale 4x) dropped to 0-1/4 depending on the resampling method, so the pipeline is also sensitive to how the original is upscaled.

Cost per attempt: clean 20 ms + tesseract 55 ms.

Failure modes seen: a "6" whose top is cut by the red line comes back as "5"; digits in the fisheye zone (the 8/0 in captcha04) merge with neighbours; overlapping 7s/3s survive only sometimes.

Confidence that tesseract tops out around 30-50% exact per attempt on this captcha family: ~80%. What stops certainty: n=4, and the grid search on 3 labelled samples is overfit — the true rate needs ≥100 fresh labelled captchas.

## (c) n/a — tesseract present; pipeline above is Pillow/numpy/scipy only (no cv2/pytesseract needed)

## (d) Recommendation

**Do not ship auto-OCR as the default path yet.** Ship the operator-typed path first, with OCR as an opt-in experiment:

1. **Default: operator types it.** CLI fetches `/services/captcha?rnd=…`, saves the PNG, opens it (`/usr/bin/open` on macOS; Ghostty supports inline Kitty-protocol images but no `imgcat`/`viu`/`chafa` installed — printing the path + `open` is the portable choice), prompts for exactly 6 digits, validates `^\d{6}$`, offers `r` to refresh.
2. **Every manual answer is a free training label.** Save `(captcha.png, typed digits, login succeeded?)` to a gitignored local dir. ~1-2k labelled samples is enough to train a small fixed-length digit CNN for this one captcha generator, which is the realistic route to >95%; tesseract will not get there.
3. **Opt-in `--captcha auto`**: run the pipeline, accept only a 6-digit result, retry with a fresh captcha (refresh is free) up to N=3, then fall back to (1).
4. **Threshold to make auto worth shipping as default:** ≥80% exact per attempt measured on ≥100 fresh labelled captchas (3 retries → 99% unattended logins, 0.25 wasted auth POSTs per login). Below ~70% the operator-typed path is both faster and safer; at today's ~50% you'd burn 1 failed authenticate POST per login on average and still drop to manual 12% of the time.
5. **Blocking pre-condition for any auto-retry:** confirm that a wrong captcha on `POST /services/authenticate` does **not** count toward the GST account-lock counter (RECON.md has nothing on lockout; the POST body/error codes are still discovery item D1). I did not check this and it decides whether retries are safe. Submit one deliberately wrong captcha with correct credentials, record the error code and whether an attempt counter is mentioned.
6. **Audio captcha button:** exists on the login form — noted only; do not use it.

Files: pipeline `/private/tmp/claude-501/-Users-damanpreetsingh-jivo-cli/84155c82-d76d-4f82-b84d-67109c30f276/scratchpad/captcha_ocr.py` (`grid` and `save <thr> <open> <close> <scale>` modes); cleaned PNGs `captcha{1,02,03,04}-clean.png` in the same directory.