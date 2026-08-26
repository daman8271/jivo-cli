---
name: jivo-ap-draft
description: Use when an operator hands over a vendor's tax invoice (PDF, photo, scan, or typed details) and wants it entered in SAP B1 as an A/P invoice / purchase invoice / purchase bill — "make a draft of this", "enter this bill", "data entry for this invoice", "AP invoice draft". Also use when asked to check whether a vendor invoice is already in SAP, or why an A/P draft was rejected ("define the numbering series", -10, -4002, -5002 branch).
---

# A/P invoice draft from a vendor invoice (JIVO, SAP B1)

Internal skill for the jivo-cli toolkit. Everything here was learned on live data
on 2026-08-21: Frystal NINV/26-27/0826 turned out to be Neetu's existing Draft 54906;
SSY 26-27/1450 became Drafts 54937 **and** 54938 — the same document twice, under two
logins — which is exactly the duplicate this skill now prevents.

**Core principle: at JIVO the invoice is never keyed in — it is drawn from the
GRPO that the factory already made, and it may already exist. Find before you
make; read back after you make.** RULE 0 in `CLAUDE.md` governs the write itself.

**Many bills at once?** This skill is one bill at a time. For a pile of open
GRPOs — 50 at a time, reviewed in Excel before anything is sent — use
`acc batch` (see `acc/BATCH.md`). It shares these rules; the scripts here and
the batch both call `acc/apbatch`.

**Which skill?** This one is for a vendor **tax invoice for goods that came through
the gate** — a GRPO exists and the draft is drawn from it. Two siblings share its
rules, its scripts and its attachment recipe:

- **No GRPO** — fuel / petrol-pump bills, transporter / freight / bilty bills, courier,
  electricity, rent, AMC, any service or expense bill → **`jivo-ap-service-draft`**.
  precheck exit 3 ("no GRPO") is the usual hand-off signal.
- **A credit note the vendor issued to JIVO** (rate difference, short quantity,
  return, reversal) → **`jivo-ap-credit-memo`** (`draft purchase-credit-note`).

Live corrections that shaped all three (harness `harness/corrections/`): C-0017,
C-0018, **C-0024** (credit memos carry OriginalRefNo/Date), **C-0025** (service lines
carry LocationCode, U_Recvd_Qty, Budget dim), **C-0026** (attachments: approve-column
stamp; the draft carries the base document's file too).

## The procedure

1. **Read the paper into facts.** Vendor name + GSTIN · invoice no. (exactly as
   printed → `NumAtCard`) · invoice date · **buyer name** (Jivo Wellness Pvt Ltd →
   `JIVO_OIL_HANADB`, the default; Jivo Mart → `JIVO_MART_HANADB`; Jivo Beverages →
   `JIVO_BEVERAGES_HANADB`) · buyer GSTIN (→ branch) · "Buyer's order no." (= JIVO
   PO DocNum) · item lines (qty, rate, taxable) · GST split (IGST vs CGST+SGST) ·
   round-off · grand total · **JIVO's gate stamp: G.No and date (= gate-in date)** ·
   **every handwritten mark, read as data (next point)**.

   **Read the scan in tiles, not as one page** — `bin/zoom.py "<scan>" --dpi 300`
   renders it big and cuts it into 9 overlapping tiles; Read every tile (and
   `--box L,T,R,B --dpi 900` for a doubtful digit). A shrunk full page is how the
   "Common" on Ashok Diwan 1256 was missed.

   **Handwriting is data (C-0027).** List every handwritten note on the paper and
   map each to a field *before* running anything — `reference/handwriting.md` is
   the glossary: `Common` → Budget `CostingCode3 = FACT_COM` (pass it in `--note`
   or `--budget FACT_COM`; precheck applies it); `For oil plant` → Oil, branch 2;
   G.No + date → `DocDate`; `GE-2026-xxxx` → Comments; a bare 5-digit number = a
   Drafts DocEntry (stop, it exists); 10-digit `2026xxxxxx` = GRPO DocNum;
   `Approved by … on mail …` → Comments verbatim. A note you cannot map is a
   question for the operator, never a silent remark. **Add every new note you
   meet to the glossary the same day** — that is how this skill gets better at
   handwriting with each paper. A doubtful digit is settled by arithmetic and by
   the GRPO, not by squinting.
2. **Find the GRPO by the vendor's own bill number FIRST — it is an exact key.**
   `PurchaseDeliveryNotes.NumAtCard` holds the vendor's invoice number, so this is
   a lookup, not a search. Gate number, amount and date are corroboration only.
   ```bash
   sapb1 query PurchaseDeliveryNotes --filter "contains(NumAtCard,'<bill no>')" \
     --select "DocEntry,DocNum,CardCode,CardName,NumAtCard,DocDate,DocTotal,DocumentStatus"
   ```
   Take `CardCode` from that GRPO and pass it to precheck as `--vendor <CardCode>`.
   **Never let a vendor be resolved by name similarity** — `FederalTaxID` is empty
   for the whole vendor master, and name matching booked TPAC to GTECH and Pioneer
   Pet to Hose Expert (₹13.9 L, 2026-08-26). Two hits on one NumAtCard = a duplicate
   GRPO in SAP: report it, do not just pick one. Full rules:
   **`reference/matching-and-batches.md`**.
3. **Run the pre-check** (read-only; it refuses to build if anything is off):
   ```bash
   python3 .claude/skills/jivo-ap-draft/bin/precheck.py \
     --ref "<invoice no>" --vendor "<name fragment or CardCode>" \
     --gstin <buyer GSTIN> --inv-date YYYY-MM-DD --gate-date YYYY-MM-DD \
     --qty <pieces> --total <grand total> --po <buyer's order no> [--grpo <DocNum>] \
     --item "<item description as printed>" \
     --note "GE-2026-xxxx | Veh … | e-Way … | <approvals written on the paper>" \
     [--company JIVO_MART_HANADB] [--env <operator>.env] --out /tmp/ap-draft.json
   ```
   - **Exit 2 = already in SAP.** Run the `readback.py` lines it prints, one per
     existing draft, and give the operator the paper-vs-record comparison and the
     draft number(s). Do not draft again. Two drafts on one invoice → a human
     removes the extra in the client.
   - **Exit 3** = it could not identify vendor / GRPO / branch / series — fix the
     inputs; never hand-edit facts it couldn't find.
   - **Exit 4** = SAP unreachable. Not a data answer. It prints the bridge fix.
4. **Show the operator** the dry-run, from `sap-b1/cli` with the operator's env
   sourced (`set -a; source <operator>.env; set +a`):
   `./sapb1 draft purchase-invoice --dry-run --data-file /tmp/ap-draft.json`.
   Wait for their go.
5. **Send** the same command with `--yes`. Note the DocEntry SAP returns.
6. **Read it back and compare**:
   `python3 .claude/skills/jivo-ap-draft/bin/readback.py <DocEntry> --expect-total … --expect-qty …`
   Report its flags as gaps, not as success. Give the operator the draft number
   and the click-path it prints.

## Rules the scripts encode (know them anyway)

| Field | Rule | Why |
|---|---|---|
| `DocDate` | **gate-in date** (JIVO stamp / GRPO date) | Daman's rule, harness C-0017 |
| `TaxDate` | vendor's invoice date | C-0017 |
| `DocDueDate` | omit — SAP applies the vendor's terms | it computes from doc date |
| `BPL_IDAssignedToInvoice` | branch whose `FederalTaxID` = buyer GSTIN; one GSTIN sits on several Oil branches (2 FACTORY, 5 HARYANA SALES, 8 …) — **the GRPO's branch decides** | -5002 without it |
| `Series` + `DocumentSubType` | the month's GST-tax-invoice series for that branch, e.g. Oil FACTORY Aug-26 = **3684 + `bod_GSTTaxInvoice`** | without both: `-10`/`-4002 define the numbering series` (C-0018) |
| `DocumentLines` | one per **open GRPO line**: `BaseType 20, BaseEntry, BaseLine`, qty = line's open qty | stock is not received twice; a 5,870-pc invoice can be two lines because the GRPO merged two POs — say so to the operator |
| `WTLiable` | **Ask the operator — precedent beats the master flag.** precheck defaults to `tYES` when the BP is TDS-liable, but show them the vendor's last 3 posted invoices first: if those are `tNO`/TDS 0, that is how JIVO books this vendor. TPAC 2026-08-22: master said 194Q 0.1% (₹214), last 3 all `tNO` → operator chose no TDS. Always check `WTAmount` on read-back | API drafts come out TDS 0 (C-0018); and once overruled, readback's "TDS is 0 but vendor is TDS-liable" flag is a false positive |
| `Comments` | `Based On Goods Receipt PO <n> \| PO <n> \| GATE ENTRY NO <n> \| <paper notes>` ≤ 254 chars | how Accounts searches |
| `LocationCode` (lines) | inherited from the GRPO line — verify it is set (Oil factory = **2**, Bhakharpur/Haryana). An empty Location shows as an empty place-of-supply in the client | C-0025 |
| `CostingCode2` (Effective Month) | **= the DocDate's month, `MM-YYYY` (e.g. `08-2026`).** A GRPO-drawn line inherits **Dim1 only** — Dim2/3/5 come through null and must be set. Patchable after the fact without disturbing totals, base links or attachments | C-0035 |
| `WTLiable` / TDS | 194Q deducts 0.1% only once that **seller** passes **₹50 lakh FY purchases**, and the seller is a **PAN**, not a CardCode — aggregate every card sharing `CRD7.TaxId0` first (TPAC = VENDA000937 + VENDA000939). **SAP does not enforce the threshold**; it deducts whenever `WTCode 1031` is set | C-0036, C-0037 |
| `CostingCode3` (Budget) | **the bill's handwritten allocation note decides**: "Common" / "For oil plant Common" → `FACT_COM` (FACTORY COMMON); the GRPO's inherited `Factory` is the store's default, not Accounts' allocation. Ashok Diwan 1256 → 55165 was patched for this (2026-08-24) | C-0027 |
| item name ≠ paper | JIVO's item code can be named nothing like the vendor's description (paper "WASH SOLUTION 1000ML" = `CG0000018 INK CARTRIDGE WASHING`). Qty/rate/tax matching the GRPO line is the proof; **say the mismatch out loud** | operator trust |

## Pre-flight — before `--yes`, and again after read-back

Rules in a table get skipped under load; this list does not. Tick every line.

- [ ] duplicate gate passed (precheck exit 0; the ref **and** the GRPO both clean)
- [ ] every line `BaseType 20 / BaseEntry / BaseLine` set — nothing free-keyed
- [ ] `DocTotal` = the paper's grand total to the paisa; qty = paper qty
- [ ] `DocDate` = GRPO/gate date, `TaxDate` = vendor's invoice date
- [ ] `Series` is **this month's**, `DocumentSubType` set, branch = the GRPO's
- [ ] `WTLiable` = the vendor's posted precedent (not the master flag)
- [ ] `LocationCode` on every line; `Comments` has GRPO, PO, gate no., approval note
- [ ] **`CostingCode2` (Effective Month) set on EVERY line** = the DocDate month
- [ ] GRPO found by its `NumAtCard`, and `CardCode` taken from that GRPO — not name-matched
- [ ] zero-value companion lines (caps with bottles) included, and excluded from the qty check
- [ ] TDS decided on the **PAN's** FY total against ₹50 lakh, not the CardCode's
- [ ] every handwritten note mapped to a field (`reference/handwriting.md`) or raised with
      the operator — none filed silently as a remark; Budget = what the paper says
- [ ] **field diff against one posted precedent for this vendor**: every non-null
      field on its header and lines is either present in the payload or consciously
      omitted — this is what caught C-0024/25/26

After sending: read-back clean, `AttachmentEntry` set, both files listed, GRPO unchanged.

## Attachments — the draft must carry the paper (both papers)

An API-created draft comes out with `AttachmentEntry: null`. The B1 client copies the
GRPO's attachment forward on copy-to-target; the Service Layer does not — so we do it.

**Rule (Daman, 2026-08-24): the draft carries the operator's scan AND the GRPO's file**,
as two independent lines on the draft's own `Attachments2` row. Full recipe, every
command proven live: **`reference/attachments-upload.md`**. In short:

1. `POST /Attachments2` with the operator's scan (renamed `VENDOR-REF-DATE.pdf`) → row N.
2. Download the GRPO's file (`GET Attachments2(<grpoAE>)/$value`) and `PATCH Attachments2(N)`
   multipart to append it as line 2.
3. Stamp every line `U_CHK = <size KB>`, `U_CHK2 = "OK"` — JIVO guard **1120025** refuses
   the draft pointer otherwise (`[-1116] Select "OK" in Approve Column`).
4. `PATCH Drafts(<DocEntry>) {"AttachmentEntry": N}` (dry-run, then `--yes`).
5. Read back draft **and** GRPO; `TargetPath` must be the Windows UNC
   (`\\10.10.101.52\Attachments_Oil\JIVO_OIL\Attachments`) so the client can open it.

**Upload works since 2026-08-24** (hanadb CIFS mounts, `sap-b1/attachments/MOUNT-RUNBOOK.md`).
Before that, `POST /Attachments2` → `-5002 Attachments folder not defined` and `$value` →
`404 LINUX mount point`. If either error returns, a mount is down — fix per the runbook, never
retry blindly. Do **not** point the draft at the GRPO's own row (`AttachmentEntry = <grpoAE>`):
it works (proven on 54983) but the two documents then share one record — a file added later
on either shows on both.

## Hard stops

- **Exit 2 from precheck means stop.** Accounts (Neetu/USER07 and others) key
  drafts in the SAP client the same afternoon the paper arrives; handwritten
  numbers on the scan are usually that draft. It checks by vendor ref **and** by
  GRPO, so a typo'd ref does not hide a duplicate. A second draft on the same
  GRPO is a duplicate.
- **"Put it in approval / make it pending" is a client action, not a CLI one.**
  The approval request is created when a person presses **Add** on the draft.
  `POST /PurchaseInvoices` to let the approval template intercept is refused by
  the server (`-5002 Attachments folder not defined [131-102]`) and, if it ever
  weren't, would post a live invoice. Never try it; say "open the draft → WTax
  Liable → Add".
- **A draft is owned by the login that made it.** The operator's Document Drafts
  Report defaults to their own user; a draft made as `manager` is invisible to
  them until they set User = manager/All. Use their per-operator env file
  (`sap-b1/cli/<name>.env`, 0600, gitignored) so it lands in their own list.
  precheck prints the login it will use.
- **Exit 7 from `sapb1 draft`** = sent, outcome unknown → run readback / query
  Drafts by `NumAtCard`; do not re-send.
- **SAP unreachable / timeouts** (`cannot reach SAP Service Layer`): the box only
  admits the office IP. `bash connections/sap-home-bridge.sh`, then
  `export SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000 SAPB1_TIMEOUT=180 HANA_ENV=connections/hana-office-bridge.env`.
  Exported values beat `--env` files, so the operator's env still picks the login.
  `sap-office-bridge.sh` needs an office PC parked on the VPS and is often down;
  the home bridge is the durable one.

## If the draft is wrong: delete it

A draft this skill made is a draft this CLI made, so `sapb1 delete draft` will take
it without an override. Same env file as the draft (the login that owns it), and
show the operator the dry-run first — it reads the draft back, so they see the
vendor, the total and `NumAtCard` before they agree.

```bash
./sapb1 delete draft <DocEntry> --dry-run     # reads SAP, sends no DELETE
./sapb1 delete draft <DocEntry>               # then type yes at the prompt
```

- **Same day, no overrides needed.** Past 24 hours it asks for `--older-than <dur>`,
  and by then the answer is usually "leave it, Accounts will handle it in the
  client" — a day-old A/P draft may already be in someone's Document Drafts list.
- **If the draft carries attachments** (it should — see above), the delete refuses
  until `--with-attachment` — the guard cannot tell our uploads from paper somebody
  attached. Setting `AttachmentEntry` back to `null` first (PATCH, 204) is the cleaner
  route; the uploaded files stay on the share as harmless orphans (the SL has no DELETE
  for `Attachments2`). Read the GRPO back either way and confirm it still carries its bill.
- **Once it has been sent for approval, it is not yours either.** A fresh draft reads
  `AuthorizationStatus dasWithout`; the moment Accounts presses **Add** it routes via
  "USER03 AP" and the row goes `dasPending` while still reading `bost_Open`, so the
  delete refuses it (`--in-approval`) and no other guard would have. Bhawani/USER03
  is looking at it — ask, don't override.
- **A duplicate keyed by a person is not yours to remove.** Precheck exit 2 means
  Neetu (or another operator) made that draft in the client; the delete will refuse
  it, and that refusal is correct. Tell the operator which two drafts exist and let
  them remove the extra in the client — unless they explicitly say to remove that
  DocEntry, which is the only thing `--not-created-here` means.
- **Never loop it.** `--not-created-here` takes one DocEntry, needs a person at the
  prompt, and refuses `--yes`. Every delete is logged under the operator's name; the
  snapshot of what was there stays on that machine and only its sha256 goes into the
  shared log, because this repo is public.

## Reference

`reference/series-and-errors.md` — how Oil numbers A/P invoices (branch × month ×
sub-type), the Aug-26 series table, SAP error codes seen and their fixes, and the
SAP-client click-paths for drafts and approvals.

`bin/zoom.py` — render a scan big and tile it, so handwriting is read at real
resolution instead of page scale (`--box` for one region, `--dpi 900` for one digit).

`reference/matching-and-batches.md` — the exact-key GRPO lookup, vendor resolution,
the dimension block, ₹0 companion lines, running a pile (two-pass duplicate gate,
files-vs-invoices), and the 194Q threshold per PAN. Read this before any batch.

`reference/handwriting.md` — the growing glossary of what people write on JIVO's bills
and which field each mark sets (C-0027), plus the digit traps met so far.

`reference/attachments-upload.md` — the proven upload → stamp → point → verify recipe,
shared with `jivo-ap-service-draft` and `jivo-ap-credit-memo`.

Worked examples from 2026-08-24 (all three drafts live, read back, corrected by Daman):
Digicod DFM/26-27/00382 → draft 55126 (this skill) · Om Sai fuel 2495 → 55130
(`jivo-ap-service-draft`) · Royal Prime CN 56 → 55128 (`jivo-ap-credit-memo`).
