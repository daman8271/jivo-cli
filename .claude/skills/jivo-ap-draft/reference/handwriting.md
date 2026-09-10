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
| a bare 4-digit number in the top corner (`3502`, `3474`, `4855`), blue pen | the **gate-entry serial** — the tail of `GE-2026-<n>`, the same number FactoryApp writes into the GRPO's Comments (`Gate Entry: GE-2026-3502`) | `Comments` as `GE-2026-<n>`; confirm it against the GRPO's comments, which carry it verbatim when the GRPO came from FactoryApp | AG POLY 902/27502290 → 56484 and THE TIN 26-27/109 → 56486 (both confirmed in the GRPO); AG POLY 902/27502214 → 56485 (hand-keyed GRPO, no GE in its comments — taken from the paper) |
| `Approved by Chopra sir on mail 24/08/26` | authority to book | `Comments`, verbatim | Ashok Diwan 1256 |
| `OK` / tick in the top corner | stores checked it | nothing — do not treat as approval | Ashok Diwan 1256 |
| `Disc @ 0.50` on a fuel bill | ₹0.50 **per litre on diesel only** — decode from the arithmetic | net onto the diesel lines | Om Sai 2495 |
| `Original invoice no. & date` box on a CN | statutory reference | `OriginalRefNo` + `OriginalRefDate` (C-0024) | Royal Prime CN 56 |
| `* Recomanded by Tiwari ji` in green, with a green signature and date `1/9/26` below the table | the recommender/approver's note; the asterisk is keyed to a `★` on ONE row of the bill (here GR 13008, the only row with a party name) | `Comments`, verbatim with the date, on the draft that carries THAT row — not on every draft the bill splits into | Delhi Punjab Transport bill 119 → Bev 15837 |
| `GRPO OK` / `A/R OK` (pencil, next to the transporter's invoice number) | the transport desk has checked that the freight GRPO exists and that the sale-invoice (A/R) numbers printed on the bill match it | nothing to set — corroboration that `OPDN.NumAtCard` = the bilty will hit; find that GRPO and copy it, never hand-key. Ticks on the Package / Weight / Rate / Freight cells are the same check | PICK & SHIP NCR-358 → 55902 |
| signature with a date (`31/08/26`) at the foot of a transporter bill, beside a `For` | the approver signed the bill on that date | `Comments`: `APPROVED 31/08/26`; it is NOT the posting date (transport `DocDate` = the bill date) | PICK & SHIP NCR-358 → 55902 |
| `★` / `*` beside a single row and beside its amount | that row is the one the footnote is about | pair it with the footnote; check whether the row is a different company (it was — Beverages) | Delhi Punjab 119, GR 13008 |
| pencil `GRPO OK` / `A/R OK` (or `AIR OK`) in the top corner | the desk checked GRPO exists and A/R (sale invoice) matches | nothing — a checker's tick, not authority | Delhi Punjab 119 |
| `Rec'd 31/08/26` with a signature beside the vendor's stamp | date the bill reached JIVO | nothing on the document (the A/P `DocDate` on a transport bill is the BILL date) | Delhi Punjab 119 |
| `Kg` in the Weight column with `Point` in the Rate column and a flat amount (`1000`) | a per-delivery *point* charge, not tonnage | it is a freight line like any other — the GRPO for that bilty already carries it (13032+13033 split 15,249+1,000 on paper vs 9,876+6,373 in SAP; both sum to 16,249). Tie on the SUM per vehicle, not per row | Delhi Punjab 119, GR 13033 |
| green-ink `Debit ₹ 3600.03 Incl. GST`, initialled and dated `31/8/26`, with `Sunflower Oil 1 c/s short (Debit 3600.03)` beside the freight row | the approver's **shortage debit** on the transporter — one carton short at delivery, valued at JIVO's sale price incl. its 5 % GST (20 pcs × ₹171.43 × 1.05 = ₹3,600.03, exact, off sale invoice 626070769) | **not a field on the A/P invoice.** Book the bill at full value; carry the note verbatim in `Comments`; the debit is a separate **A/P Credit Memo drawn from the POSTED invoice** (Oil precedent ORPC NCR-240/249/307/314: `RPC1.BaseType 18`, same `NumAtCard`, dated the 1st of the next month). Name it as a follow-up — it cannot be raised until the invoice is Added | PICK & SHIP NCR-356 → 55903 |
| a second rate written under the printed one (`12.50` under `15.00`, the printed rate circled) | somebody queried the rate; the freight on the paper still uses the printed rate (1280 × 15 = 19,200) and the approver's note does not mention it | nothing on the document unless the approver's note says so — `Comments` + raise it with the operator (here ₹3,200 + GST would be at stake) | PICK & SHIP NCR-356 |
| faint pencil word top-centre near the e-mail print stamp (`Result` / `Debit`?) | unreadable at 600 dpi; it sits with the print header, not with any figure | nothing — say it is unread rather than guess | PICK & SHIP NCR-356 |
| a month name written into the gate stamp's `Item` / `Qty` line (`April month`, `May month`, `June month`) | the SERVICE PERIOD the bill covers, not the gate month | line `CostingCode2` (Effective Month) = that month, e.g. `04-2026` — it is NOT the DocDate's month on a periodic service bill; the vendor's 12 posted precedents all book the serviced month | Oxybee OSPL/UPSER26/151-153 → Bev 15932-15934 |
| a breakup under the total (`Note: 17 Days less Duty -> Deepak operator = 14168 / 1 Supervisor 35000 / GST 18% / 58018`) with a DIFFERENT total in the approver's green hand (`Debit Rs 58,516/- Incl. GST`) | the debit's arithmetic (blue, the plant) and the approved figure (green, the approver) — and they disagree | nothing on the A/P invoice: book it at full value. **Do not pick a figure** — the two hands are the operator's question to settle before the credit memo is raised | Oxybee OSPL/UPSER26/151-153 (Apr 58,018 vs 58,516; May 28,073 vs 26,259; Jun 32,450 vs 32,517) |

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

## Transporter bills — marks met on Delhi Punjab bill 118 (2026-09-02, → Oil draft 55904)

The vendor's own hand fills the grid (Date · Vehicle · Station in Devanagari · G.R. No ·
Weight · Rate · Amount); JIVO's hands sit around it. Rows that are **not bilties** are
charges folded into the bilty above them — `ONE PARTY HOLD 2000`, `DAY WALMART HOLD 2000`,
`— POINT 2000` (a second delivery point). Gurcharan keys them **inside that bilty's GRPO**
(13091's GRPO = 17,340 + 2,000 hold; 13004's = 13,000 + 2,000), and where one truck carried
two bilties (13084/13085, same HR67E1536) she re-splits the pair on litres — the two GRPOs
differ from the two paper rows but their **sum ties**. Match on the bill total, not row by row.

| Mark (hand) | Means | Field |
|---|---|---|
| `Debit ₹2000/- Bilty no 13091` (green, the approver's hand, beside `Recd OK 29/8/26`) | JIVO will not pay that charge — a **debit note** is owed | **Not a line edit.** Precedent CN 5744/5170/5345/5346: an A/P credit memo drawn from the *posted* invoice (`BaseType 18`, acct 5670001, GST05R). So: draft the invoice at the full GRPO value, note it in `Comments`, raise the credit memo after posting |
| `one party hold` / `Delivery-2000/` (pencil, circled with the green) | the checker's identification of which paper row the debit is | corroboration only |
| `GRPO OK` / `A/R OK` (pencil, top right) | the transport desk has verified the GRPOs and the AR invoices behind them | none — a checker's tick |
| `Debit` (pencil, underlined, top corner) | routing note: this bill carries a debit | `Comments` |
| `Recd OK <date>` + signature (green) / signature + `20/08/26` (blue) | received at HO / approved for entry | none; the dates are NOT `DocDate` — `DocDate` = the bill date for this class (Transport-Bill-Playbook §2) |

Digit traps on this vendor: `13081` vs `13082` — the GRPO's `NumAtCard` said 13081 while
its Comments said 13082; the paper's row and the amount (6,577) settle it.
