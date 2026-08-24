# Handwriting on a vendor bill — what it means and which field it sets

Shared by `jivo-ap-draft`, `jivo-ap-service-draft`, `jivo-ap-credit-memo`.

**Rule (Daman, 2026-08-24, C-0027): a handwritten mark on a bill is an instruction,
not a remark.** Before anything else, list every handwritten note on the paper and map
each one to a field using this glossary. A note you cannot map is a question for the
operator — never file it silently into `Comments`.

**This file grows.** Every paper that carries a note not listed here gets a new row
the same day, with the paper it came from. That is how the skill gets better at
handwriting with each trial: the vocabulary is small, the spellings are few, and
the same people write the same things on every bill.

## Glossary — seen live, verified

| Written on the paper | Reads as | Sets | Seen on |
|---|---|---|---|
| `Common`, `Comman`, `Comon` (next to "For oil plant") | Factory **Common** | line `CostingCode3 = FACT_COM` (dim 3, name FACTORY COMMON) — overrides the GRPO's `Factory` | Ashok Diwan 1256 → 55165 (patched after Daman's correction) |
| `For oil plant`, `For oil` | the Oil company, factory | company `JIVO_OIL_HANADB`, branch 2 FACTORY | Ashok Diwan 1256 |
| `(BEVERAGE UNIT)` in the GRN stamp header | the Beverages company | company `JIVO_BEVERAGES_HANADB` (vendor CardCodes differ per company) | Nexton Seals, 08-24 |
| Stamp `G.No 136 · Date 13/8/26 · V.No HR67F9911 · Qty 600 kg` | gate-in stamp | **`DocDate` = the stamp date** (C-0017); `Comments` `GATE ENTRY NO 136 dt 13-08-26`; vehicle and qty into `Comments` (service bills: qty → `U_Recvd_Qty`, C-0025) | every factory bill |
| `GE-2026-9529` | gate-entry register number | `Comments` | SSY 26-27/1450 |
| a bare 5-digit number (`54906`) | a `Drafts` DocEntry — Accounts already keyed it | **stop: precheck exit 2**, read that draft back | Frystal NINV/26-27/0826 |
| a 10-digit `2026086644` | a GRPO DocNum | `--grpo` | many |
| `Approved by Chopra sir on mail 24/08/26` | authority to book | `Comments`, verbatim | Ashok Diwan 1256 |
| `OK` / tick in the top corner | stores checked it | nothing — do not treat as approval | Ashok Diwan 1256 |
| `Disc @ 0.50` on a fuel bill | ₹0.50 **per litre on diesel only** — decode from the arithmetic | net onto the diesel lines | Om Sai 2495 |
| `Original invoice no. & date` box on a CN | statutory reference | `OriginalRefNo` + `OriginalRefDate` (C-0024) | Royal Prime CN 56 |

## How to actually read it — tiles, not a full page

A whole scanned page shrunk to fit is where handwriting goes to die: the mark that
changed the Budget on Ashok Diwan 1256 was a small word sitting on top of a rubber
stamp, and it read as scribble at page scale. **Render big, then read in pieces:**

```bash
# every part of the page, 3x3 overlapping tiles at 300 dpi — Read all nine
python3 .claude/skills/jivo-ap-draft/bin/zoom.py "<scan.pdf>" --dpi 300

# one region you already care about (fractions of the page: L,T,R,B)
python3 .claude/skills/jivo-ap-draft/bin/zoom.py "<scan.pdf>" --box 0,0.45,0.55,0.72 --dpi 600
```

Where things live on a JIVO-stamped bill (starting points, verify per paper):
invoice no. + date `0.45,0.13,1.0,0.20` · gate stamp `0.28,0.44,0.52,0.53` ·
allocation / signatures under the stamp `0.35,0.50,1.0,0.60` ·
tax + total column `0.70,0.70,1.0,0.85` · approval line at the foot `0,0.94,0.85,0.99`.

Read **every** tile in grid mode. The mark that changes a field is usually the one in
a corner nobody thought to look at. 900 dpi on a single doubtful digit is cheap.

## Reading digits — settle by evidence, not by squinting

- **Compare glyphs only within the same hand.** A bill carries three or four
  different hands — the vendor's (invoice no., date, amounts), the gatekeeper's
  (the G.No/Date/V.No stamp), the storekeeper's, the approver's. The gatekeeper's
  "3" in `G.No 136` says nothing about the vendor's "3": on Ashok Diwan 1256 the
  vendor writes 3 as a top-loop ∂ (see the two ₹300 GST figures) while the
  gatekeeper writes it flat-topped with a bowl. **Find the same digit elsewhere in
  the SAME hand and compare against that** — a cross-hand comparison is how a 3
  becomes a 7.
- A doubtful digit is settled by **arithmetic** (qty × rate must equal the amount; taxable
  + GST must equal the gross) and by **SAP** (the GRPO's `NumAtCard`, qty and total) — never
  by picking the likelier-looking shape.
- Indian handwriting traps met so far: `1` with a long flag reads as `7`; `6` can look like
  `b` (HSN `63b` on the Ashok Diwan bill = **6310**, old cloth/rags); `9` and `4` in GSTINs
  (a GSTIN is 2 digits + 10-char PAN `AAAAA9999A` + `1Z` + check char — if the read does
  not fit, it is wrong); `0`/`O`, `5`/`S` in vehicle numbers (HR67**F**9911 on the stamp vs
  HR67**E**9911 on the printed line — the stamp was the registration).
- Dates are DD-MM-YY. `13-8-26` is 2026-08-13; never "normalise" to a different day.
- **Cross-check dates for internal consistency**: a vendor bill cannot be dated
  *after* the gate stamp that let it through the gate (the bill travels with the
  truck). If your two readings imply that, at least one is wrong — and SAP's GRPO,
  keyed by a person holding the physical paper, is better evidence than any scan.
- When two readings survive, say both to the operator with the field they would
  change, and give each a confidence. Never pick one silently.

## Words we expect to meet next (unverified — confirm on the first paper, then move up)

`Bev`, `Beverage` next to an allocation → likely a Beverages budget centre, not Oil ·
`Sales`, `HO`, `Delhi` → a non-factory branch / cost centre — check `ProfitCenters`
dim 3 and the vendor's precedent before setting anything ·
`Urgent`, `Pay`, `Cash` → payment instructions, not accounting fields — `Comments` only.
