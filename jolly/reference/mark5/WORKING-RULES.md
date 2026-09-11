# MARK V working rules

Updated: 10 September 2026. Working source: the MARK IV worktree,
`codex/mark4-local`. This document records the ongoing requirements discussion;
it does not mean these changes have been implemented or deployed.

## Sources and status

- Current user instructions in this discussion take precedence over the supplied
  PDF and earlier planner settings.
- Supplied PDF: `Machine_Changeover_Planning_Red_Notes_Edition.pdf`, revised
  10 September 2026, at
  `/Users/damanpreetsingh/Documents/Codex/2026-09-09/make/outputs/`.
- Source SHA-256:
  `b3388f02852783347fa04f9d23e1a9260d46477f7132d65464bdbc7238636fe3`.
- All 64 pages have now been reviewed: revised answers and coverage on 1-14,
  historical summary on 15-16, complete transcript on 17-61 (00:00-59:27), and
  original checklist on 62-64. Two readers covered the original transcript in
  bounded chunks without truncation; the main reviewer checked key passages
  against the revised notes. Visually checked pages 2-4 and 12-14, including
  the struck-out space statement. See `PDF-REVIEW-2026-09-10.md`.
  The six reproduced notes are dated 9 September. Their original live Apple
  Notes were not independently re-read in this session.
- The PDF prioritizes those notes over its retained historical summary and
  transcript. Preserve that distinction when extracting its claims.
- Current MARK IV settings were checked directly in `site-mark4/lib/rules.ts`.
- Daman explicitly adopted the PDF's revised figures on 10 September: these are
  the actual operating numbers to use for MARK V. Status: **user-approved
  operating inputs**. Do not leave them classified as awaiting numeric approval.
- Confidence is high in the extraction and adoption record. Keep each quantity's
  stated meaning: running speed, changeover duration, flushing volume and full-
  shift accepted output are distinct. Adoption does not supply missing fields.

## M5-R01: Use the revised PDF operating numbers

Status: **Approved by Daman, 10 September 2026.**

Daman's instruction:
> just so you know those are the actual nukmebrs which we will be taking ok

The revised machine and changeover values below replace the corresponding older
MARK IV inputs for the MARK V design. The PDF itself puts its revised live-note
tables first; its retained historical summary, early contradictory transcript
statements and original checklist do not restore superseded numbers.

Preserve ranges such as 25-30/min, 30-35/min and 5-6 hours, and open-ended values
such as 1 hour or more. Approval of the values does not turn a range into its
midpoint or identify an unspecified oil pair. Such implementation choices must
remain visible and be resolved when designing the scheduler.

## M5-A01: Reuse flushing oil

Status: **User-approved planning assumption; physical recovery not measured.**

Daman, 10 September 2026:
> We will be assuming that they are reusing the flushing.

Consequences for MARK V:

- Assume flushing oil is reused. Do not charge the entire flushing quantity as
  fresh oil consumed or scrapped on every changeover.
- Flushing still occupies the machine for its applicable changeover time.
- Keep flushing volume separate from saleable output and actual lost oil.
- The instruction establishes reuse, not a measured 100% recovery rate. Actual
  unrecovered loss, replenishment, recovery timing and usable flushing inventory
  remain unquantified. Do not silently turn them into verified zeroes or create
  available stock from a flushing-volume entry.
- This resolves the PDF's "Reuse confirmation ??" for scenario policy. It does
  not retroactively verify factory recovery records.

Implementation status: captured here; production code has not been changed.

## Approved machine inputs for the MARK V design

Source: PDF pages 2 and 12, with the notes' qualifications retained. Rates below
are running rates. Multiplying a per-minute rate by 60 is arithmetic, not proof
of uninterrupted hourly or full-shift output. Ranges stay ranges until a planning
choice is made explicitly.

| Machine / pack | MARK IV setting (containers/hour) | MARK V approved operating rate (containers/hour) | Qualification |
|---|---:|---:|---|
| JP / 1 L | 5,400 | 4,500 | Later Speeds note: 75/min; replaces earlier note's 80/min. |
| Clear Pack / 1 L | 4,800 | 4,800 | Note omits unit; PDF uses transcript context for per hour. |
| Clear Pack / 4 L | 800 | 1,500-1,800 | 25-30/min; route explicitly included. |
| Clear Pack / 5 L | 3,000 | 1,500-1,800 | 25-30/min. |
| 10 Head / 1 L | 2,100 | 1,800-2,100 | 30-35/min. |
| 10 Head / 2 L | 1,260 | 900 | 15/min. |
| 6 Head / 3 L | 384 | 780 | 13/min. |
| 6 Head / 4 L | No supported route/rate | 720 | 12/min; used sometimes. |
| 6 Head / 5 L | 600 | 600 | 10/min. |
| Tin Head / 15 L | 600 | 600 | 10 tins/min; no inference for other tin sizes. |
| Hitech pouch | 1,800 | 1,200 | 20/min; pack weight/film not specified. |
| Samarpan pouch | Not separately scheduled | 1,800-2,100 | 30-35/min; can run together with Hitech or alone. |

Adopted routes and their source qualifications:

- JP: mostly mustard 1 L; occasional 200 ml; pomace, extra light and rice bran
  in the 52 g family. Exact SKU/container mappings remain to be established.
  Do not apply the 1 L speed automatically to 200 ml or every bottle family.
- 10 Head: operational use is 1 L and 2 L; larger packs are not used because
  of the labelling restriction. Distinguish operational suitability from the
  filler's physical capability. MARK IV currently permits 3 L and 5 L.
- 6 Head: mainly 3/4/5 L, with 1 L only for emergencies; manual labels. The
  "4 + labour people" note does not establish total line staffing or measured
  packing throughput. A 2 L working route is not settled by these notes.
- Both pouch machines can run together or singly. Their relation to the one
  night-line limit, complete crews and shared equipment remains unspecified.
- The same cap size does not establish approved item-code interchangeability.

## Approved changeover inputs

Source: PDF pages 3, 13 and 14. MARK IV currently applies a provisional one-hour
product-change allowance; the new evidence requires machine- and change-specific
rules. A direction-specific entry must not become a symmetric rule silently.

| Machine / change | Approved source value | Scope and overlap |
|---|---|---|
| JP / SKU change | About 5-6 hours | PDF says cleaning/flushing is included. Exact SKU/oil/bottle transitions still need classification. |
| Clear Pack / parts, 1 L to 5 L | 1 hour | Mechanical change; keep distinct from flushing. |
| Clear Pack / base flushing entry | 30 minutes | Oil pair unspecified. |
| Clear Pack / mustard to cold press or other oil | 1 hour or more | Flushing, direction-specific; no measured upper bound. |
| Clear Pack / rice bran to cold press | 45 minutes | Flushing. |
| Clear Pack / generic daytime SKU change | About 1 hour | Parts/flushing inclusion unresolved; does not override specific longer cases. |
| 10 Head / parts only | About 30 minutes | Mechanical component. |
| 10 Head / mustard, groundnut, EV | 1 hour or more | Parts and flushing combined; do not add another 30 minutes. Exact from/to pairs unspecified. |
| 10 Head / cold press to sunflower | About 30 minutes | Prefer specific note over the transcript's later 45-minute suggestion. |
| 6 Head | Same as 10 Head | Reported inheritance, not separate measurement. |

Approved flushing quantities: Clear Pack mustard 1,000 L, other oils 550 L;
JP 1,500 L. These are the source's operating estimates, adopted for MARK V,
and are subject to M5-A01 reuse.
They are not established losses or ready-to-use opening inventory.

## Boundaries still requiring decisions

- Effective output: breaks, ordinary stoppages and rejects are not resolved by
  running speeds. Do not silently reapply the earlier 80% rule or assume 100%
  full-shift availability when converting the new figures into planning capacity.
- Speed ranges, the 5-6-hour JP range and open-ended "1 hour or more" need
  explicit planning choices; do not silently use an average or lower bound.
- Clear Pack's start is reported as 07:30 +/-30 minutes. A full day/night clock,
  net hours, breaks, setup scheduling and Sunday crossover remain incomplete.
- The space-bottleneck sentence is struck out in the source note. This removes
  that statement as a settled finding; it does not establish unlimited storage,
  remove an existing declared warehouse capacity or prove congestion cannot occur.
- Full crews, minimum batches, shared-resource restrictions, pouch/tin changeover
  times and good-output shift evidence remain incomplete.
- The PDF's unanswered checklist categories are active heads, combo packing,
  substitutions/carton transition and running costs. Treat that as this PDF's
  coverage, not proof that earlier project evidence does not exist. In particular,
  MARK IV already has a specifically verified groundnut carton transition.

Next step: incorporate Daman's remaining corrections, then produce the MARK V
implementation plan before modifying the scheduling engine.
