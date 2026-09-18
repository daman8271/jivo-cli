---
name: jivo-consumables-direct-indirect-expense
description: Use when an operator hands over a vendor tax invoice for CONSUMABLES or a DIRECT / INDIRECT EXPENSE that came through the gate on a PO and a GRPO — ink and make-up cartridges, cleaning and treatment chemicals, housekeeping, refreshment, staff welfare, stationery, lab and testing chemicals, thinner, labels, tape, wire seal, polythene, computer hardware, building and hardware material, RMC / concrete, tank and machine installation parts. Also covers the CAPEX bills that arrive through the same door (WIP, PEB shed, tanks, lab instruments) — the G/L account decides which. Triggers: "make the draft for this expense bill", "consumable bill entry", "R&M bill", "yeh expense entry karo", or a scan with a JIVO gate stamp whose item is not RM/PM. NOT for a bill with no GRPO behind it (jivo-ap-service-draft — fuel, courier, electricity, rent, AMC, professional fees), NOT for raw or packing material purchases (ap-rm-pm), NOT for transporter freight (jivo-*-freight-grpo), NOT for a vendor credit note (jivo-ap-credit-memo). Handles a whole BATCH of scans at once — a folder or a chat drop of many bills — by fanning out one read-only agent per bill that returns JSON; see the fan-out section.
---

# A/P draft for consumables and direct / indirect expenses (JIVO, SAP B1)

> 🔴 **ATTACHMENT RULE — every file goes up with `sapb1 attach`, never by hand (Daman, 16 Sept 2026 · C-0090).**
> Whatever this skill attaches — to a draft, GRPO, A/P, credit memo, payment, JV, A/R, anything —
> upload it with **`sapb1 attach <file> [<file>...] --company <DB>`** (`--dry-run` first, then `--yes`).
> It puts all the files on ONE `Attachments2` row, ticks **Copy to Target Document = `tYES`** on
> every line (plus the Approve stamp `U_CHK`/`U_CHK2 OK` in Oil and Bev — Mart has no such fields),
> reads the row back, and exits non-zero unless every line is `tYES` and every file downloads
> back byte-identical. An upload by any other route
> lands `tNO`, and then the scan does NOT follow the document onward (GRPO → A/P, draft → posted).
> - It prints `"AttachmentEntry": N` — point the document at row N (in the payload, or `sapb1 patch`).
> - Exit 8 = the row exists but is not finished — the message names the fix (usually
>   `sapb1 attach --row N --yes`). Exit 7 = an answer never came back: look at the row
>   (`sapb1 query Attachments2 --filter "AbsoluteEntry eq N"`) before sending any file again.
> - Never `curl -X POST …/Attachments2` or hand-PATCH the tick any more. Proven live 17 Sept 2026:
>   Oil 177963 (two files, byte-identical), Mart 59373, Bev 43331.

Internal skill. Named by Daman 2026-09-08 — "we call this = direct/indirect expenses …
this are through GRPO and PO ok! get the base document from sap through grpo and PO".
Built the same day from three live bills, all three drafted, attached and read back:
DOMINO 602627124886 → Oil **56551** · SHREE RAM RMC SRR/26-27/1003 → Oil **56552** ·
JN ENTERPRISES 210 → **Beverages 16031**.

**Core principle: this class looks like a service bill and behaves like a goods bill.**
The paper says cleaning chemical, ink, concrete, tea — but a PO was raised, the store
gated it in and made an **item-type GRPO** whose line carries a P&L or asset account
instead of a stock account. So it is a copy job, not a keying job: **find the PO, find
the GRPO, copy the GRPO.** RULE 0 in `CLAUDE.md` governs the write. `ap-rm-pm`
holds the shared rules — dates, series discipline, duplicate gate, hard stops, delete,
handwriting, attachments — **read it first, then this.** Its `bin/` scripts are shared;
this skill adds no scripts of its own.

Plumbing: `acc/_playbook/sap <args>` (bridge + operator login + write log), or
`sap-b1/cli/sapb1` with the operator's env sourced.

## How to recognise it

A GRPO with `DocType = dDocument_Items` whose line has **both** a generic-head
`ItemCode` **and** an `AccountCode` on the line. Most are `CG*` (consumables/expense
heads) but **`FA*` codes arrive on the same tray** — `FA0000408 WATER TAMK 5000 LTR`
(Oil, → `5680010`), `FA0000429 ADAPTATION KIT` (Bev, → `1204003 PLANT & MACHINERY-WATER`).
Do not filter on `CG` alone. `WarehouseCode` is the non-stock
warehouse (`BH-FA` at Bhakharpur). The item is a generic *expense head*; what the
vendor actually supplied is written in the line's **`U_Remarks`**, not in the item name.

```bash
acc/_playbook/sap query PurchaseDeliveryNotes --filter "DocEntry eq <n>" --json \
  | python3 -c "import json,sys;[print(l['ItemCode'],l['AccountCode'],l['WarehouseCode'],repr(l.get('U_Remarks'))) for l in json.load(sys.stdin)[0]['DocumentLines']]"
```

## The procedure

1. **Read the scan in tiles** — `.claude/skills/ap-rm-pm/bin/zoom.py "<scan>" --dpi 300`
   (`--box L,T,R,B --dpi 900` for one doubtful digit), then map **every handwritten mark
   to a field** via `ap-rm-pm/reference/handwriting.md`. On this class the marks
   carry the expense's *nature*: JN 210 said **"for machinery cleaning"** in the margin,
   which is the R&M account in words, and **"GNR"** = Ganaur. A mark you cannot map is a
   question for the operator, never a silent remark.
2. **Read the paper into facts.** Vendor + GSTIN · bill no. exactly as printed →
   `NumAtCard` · **bill date** (this is the Effective Month, step 6) · **the PO number
   the vendor printed** · gate stamp `G.No` + date · every line's qty / unit / rate /
   taxable · GST split (IGST vs CGST+SGST, or none) · round-off · grand total.
3. **The printed PO number picks the book. The buyer name and GSTIN do NOT.**
   All three companies are one legal entity (PAN `AACCJ4223F`) and the GSTIN is per
   **state**, so `06AACCJ4223F1Z0` sits on Oil branch 2 *and* Beverages branch 2 and 5.
   JN 210 was printed "Billed to JIVO WELLNESS PVT LTD, GSTIN 06AACCJ4223F1Z0" — the
   Oil signal on both counts — and belonged to **Beverages**. PO DocNum shapes differ,
   which is usually the tell: Oil `220826092` (`22`+MMYY+seq), Bev `826228027`.
   ```bash
   for CO in JIVO_OIL_HANADB JIVO_BEVERAGES_HANADB JIVO_MART_HANADB; do
     acc/_playbook/sap query PurchaseOrders --company $CO --filter "DocNum eq <printed PO>" \
       --select "DocEntry,DocNum,CardCode,CardName,DocDate,DocTotal,DocumentStatus"; done
   ```
   A vendor card existing in a book is **not** evidence the document is there — Oil had
   `VENDA000315 JN ENTERPRISES` with zero POs and zero GRPOs, ever. Search all three
   before you say anything is missing (C-0073).
4. **Find the GRPO by the vendor's own bill number — an exact key**, then take
   `CardCode` and the branch from it. Never resolve a vendor by name similarity.
   ```bash
   acc/_playbook/sap query PurchaseDeliveryNotes --company <book> \
     --filter "contains(NumAtCard,'<bill no>')" \
     --select "DocEntry,DocNum,CardCode,CardName,NumAtCard,DocDate,DocTotal,DocumentStatus,BPL_IDAssignedToInvoice,AttachmentEntry"
   ```
   A bare `contains()` over a short number (`'210'`) scans the whole table and **times
   out** — add `DocDate ge …` or `DocTotal eq …`, or use `NumAtCard eq`. A timeout is
   not "no rows"; re-run it narrowed before concluding anything.
   **No GRPO at all → this is not the skill.** Hand off to `jivo-ap-service-draft`.
5. **Run `ap-rm-pm`'s precheck** as the duplicate gate and the series finder.
   Exit 2 = already in SAP → stop and report, unless the operator says draft it anyway.
6. **Build the payload — copy the GRPO, decide only these.**

   | Field | Rule on this class |
   |---|---|
   | `DocDate` | the **gate-in** date = the GRPO's `DocDate` (C-0017) |
   | `TaxDate` | the vendor's **invoice date** |
   | `NumAtCard` | the bill number exactly as printed |
   | `BPL_IDAssignedToInvoice` | **from the GRPO**, never from the GSTIN. A `[SAP -3000] … does not have permission` on `BusinessPlaces` does not block anything — USER07 cannot read the branch list and does not need to |
   | `Series` + `DocumentSubType` | **this month's** GST-tax-invoice series for that branch. Sep-2026: Oil branch 2 = **3685**, Bev branch 2 = **2778**, both `bod_GSTTaxInvoice`. Find it, never assume last month's (C-0018) |
   | `DocumentLines` | one per **open** GRPO line: `BaseType 20`, `BaseEntry` = GRPO DocEntry, `BaseLine` = its `LineNum`, plus `ItemCode`, `Quantity` = `RemainingOpenQuantity`, `UnitPrice`, `TaxCode`, `WarehouseCode` — all copied from the GRPO line |
   | `CostingCode` (Dim1) | inherits from the GRPO; copy it anyway (`CANOLA`, `DRINKS`, …) |
   | **`CostingCode2` (Effective Month)** | **`MM-YYYY` of the vendor's INVOICE DATE** — Daman 2026-09-08. **Not** the DocDate/gate-in month, which is what C-0035 says, and **not** the GRPO's inherited value. It only bites when a bill crosses a month end, and then it bites hard: JN 210 is dated 26-Aug, gated in 2-Sep → **`08-2026`** |
   | `CostingCode3` (Budget) | the GRPO's value (`Factory`) unless the paper's handwriting reallocates it — "Common" → `FACT_COM` (C-0027) |
   | `CostingCode5` | the GRPO's value (`HR`) |
   | `LocationCode` | the GRPO's value (Bhakharpur factory = `2`); empty here is an empty place-of-supply on screen (C-0025) |
   | `WTLiable` / TDS | **set by `jivo-tds`** (step 7) — goods: 0.1% only on the part above ₹50 lakh for the year, Oil + Bev together. Never copied from old bills |
   | `Comments` | `Based On Goods Receipt PO <DocNum> \| PO <DocNum> \| GATE ENTRY NO <n> \| <what it is> \| <paper notes>`, ≤254 chars |

   **Dim2/3/5 come through null on a GRPO-drawn line and must be set explicitly**
   (C-0035); only Dim1 inherits.
7. **TDS, then dry-run, show the operator, then send.**
   ```bash
   python3 .claude/skills/jivo-tds/bin/tds.py apply /tmp/ap-<vendor>.json --company OIL   # repo root; exit 2 = STOP, say why
   ./sapb1 draft purchase-invoice --dry-run --data-file /tmp/ap-<vendor>.json
   ./sapb1 draft purchase-invoice --data-file /tmp/ap-<vendor>.json --yes
   ```
8. **Read it back and compare** — totals to the paisa, qty, both dates, every
   `BaseType 20` link, all four dimensions and `LocationCode` populated.
   Report the flags as gaps, not as success. Then
   `python3 .claude/skills/jivo-tds/bin/tds.py check <DocEntry> --company OIL` — **exit 3 = TDS wrong in SAP, do not
   send to Bhawani**; tell the operator its message.
9. **Attach both papers, then name the lane.** See below. A goods bill drawn from a
   GRPO is **POST NOW**, not a JSAP wait — say so unprompted
   (`ap-rm-pm/bin/jsap_route.py <DocEntry> --company oil -v`).

## The traps — every one of these was met live

**1 · The same `CG` code is a DIFFERENT item in every book.** Verified 2026-09-08 from
`OITM` in all three. Oil and Bev have `CG0000003`/`CG0000004` **swapped**, and
`CG0000011`/`CG0000012` **swapped** as well:

| Code | Oil | Beverages | Mart |
|---|---|---|---|
| `CG0000003` | R&M PLANT AND MACHINERY | STAFF WELFARE | STATIONARY OTHER THAN PAPER RIM |
| `CG0000004` | STAFF WELFARE | R&M PLANT AND MACHINERY | PAPER RIM A4 |
| `CG0000005` | HOUSEKEEPING | HOUSEKEEPING | PAPER LABEL |
| `CG0000011` | INK CARTRIDGE | MAKEUP CARTRIDGE | — |
| `CG0000012` | MAKEUP CARTRIDGE | INK CARTRIDGE WASHING | — |

**So never carry an item code across books, and never take one from a remembered
table — including the table below.** Copying the GRPO's own `ItemCode` is what keeps
this safe, which is another reason not to free-key a line. Read the code out of the
GRPO you found in step 4, in the book you found it in.

**2 · The account is chosen per line, not fixed by the item.** Bev `CG0000004` normally
posts to `5650016` R&M PLANT & MACHINERY but one 2026 GRPO line sent it to `5680010`
CETP CHARGES. Read `AccountCode` off the line; do not infer it from the item.

**3 · Capex arrives through the same door — say which one it is.** `OACT.GroupMask`
separates them: **5 = expenditure, 1 = asset**. SHREE RAM RMC's concrete landed on
`1212016 PEB SHED NEW LAND 2 ACRE`, an asset, not an expense. Name it out loud; a
fixed-asset line is not a direct expense even though it came in on the same tray.

**4 · A capex GRPO may carry `TaxCode CG+SG@0` with the GST folded into `UnitPrice`.**
SHREE RAM's paper charges CGST+SGST ₹2,578.50; the GRPO booked 3 × 5,634.50 = 16,903.50
+ 0.50 round = the paper's ₹16,904 with `VatSum 0`. **All 9 of this vendor's A/P
invoices since 2026-08-01 read `VatSum 0`** — that is the current PEB-shed run's
practice, and correct: ITC on civil works is blocked under s.17(5), so the tax is
capitalised. It is **not** a universal rule for the vendor — of 125 posted invoices, 7
do carry GST (counted live 2026-09-08). So check the recent run, not a `--top 5` sample:
an unordered `--top 5` is what produced an earlier wrong "all five" claim here. **Copy the GRPO. Do not "fix" the tax** — and
do not read `VatSum 0` as an error to report.

**5 · A paper "case of 4 cartridges" is 4 pieces on the GRPO.** Domino's 1-case lines
are qty **4** @ 4,001 (= the printed 16,004). The handwritten **"16 P.S"** on that scan
is 16 cartridges, and it reconciles 4+4+4+2+2. Qty and rate matching the GRPO line is
the proof the line is right — the item name will not match the paper, and **say the
mismatch out loud** (Domino's ₹800 freight line is booked as `INK CARTRIDGE`).

**6 · SAP's rounding can leave the draft short of the paper.** Domino's bill is
₹1,09,230.**24**; the GRPO and therefore the draft are ₹1,09,230.00, with
`RoundingDiffAmount -0.24`. Copying keeps the two documents matched — report the paise,
do not chase them.

**7 · Beverages refuses an attachment line over 1 MB.** Guard **1120026** (`U_CHK` >
1024) fires on the `PATCH Drafts{AttachmentEntry}`, not on the upload, so the file goes
up and only then is refused. Oil does not have this guard; Bev also has 1120025 (`U_CHK2`
null) and 1120027 (row `SUM(U_CHK)` > 5120). Compress a phone scan first — 2200 px wide,
JPEG q65 took JN's 1,575 KB to 500 KB and every figure, the gate stamp and the
handwriting stayed readable:
```bash
pdftoppm -r 200 -jpeg -jpegopt quality=72 "<scan>.pdf" pg && magick pg-1.jpg -resize 2200x -quality 65 "<small>.pdf"
```
An `Attachments2` row can never be deleted, so a refused upload leaves a permanent
orphan. Harmless — but compress *before* the first POST and there is none.

**8 · The series follows the DocDate's MONTH, and DocDate is the gate-in date.** A bill
gated in during August but keyed in September needs **August's** series, not this
month's. Gupta 1386 (gate 26-Aug) went on Oil branch 2 series **3684**, while the same
day's September bills went on **3685**. August was still open — proven by draft 56553,
created 2026-09-08 on series 3684. Check, don't assume the current month.

**9 · Freight may be an ADDITIONAL EXPENSE, not a line — copy it as one.** Sidel
18S0008475's ₹8,439 packing-and-freight sits on the GRPO as
`DocumentAdditionalExpenses`, `ExpenseCode 6`, `DistributeExpense tYES`,
`DistributionMethod aedm_Quantity`, `Stock tYES` — so it is distributed into the asset
value and never touches its own freight account. Hand-rolling it as a second item line
misstates both the asset and the tax base. Carry it across the same way, referencing the
GRPO:
```json
"DocumentAdditionalExpenses": [
  {"ExpenseCode": 6, "LineTotal": 8439, "TaxCode": "IGST@18",
   "BaseDocType": 20, "BaseDocEntry": <grpoEntry>, "BaseDocLine": 0,
   "DistributionMethod": "aedm_Quantity"}
]
```
Proven live on draft 16040 (total came back at the paper's ₹3,41,892 exactly). The
posted precedent 625033168 carries the same shape. Other Sidel bills put the freight on
its *own* line instead (18S0008488) — so **read the GRPO, do not assume either shape**.

**10 · GRPO `LineNum` is NOT contiguous — `BaseLine` must be the real number.** Sidel
18S0008488's two GRPO lines are `LineNum` **6** and **14** (the GRPO drew from scattered
PO lines). `BaseLine: 0,1` would point at lines that do not exist. Read `LineNum` off
each line; never enumerate.

**11 · A vendor-name search can miss the vendor entirely.** The real Beverages card for
AK Engineering is spelled **`AK ENIGNEERING`** (VENDA001452) — a name sweep for
`%A%K%ENG%` returns nothing, because "ENIGNEERING" contains no "ENG". Oil holds a
correctly-spelled twin (`VENDA001764 AK ENGINEERING`) with **zero documents**, created
the same day. Name-matching would have booked the bill in the wrong book against an
empty card. The printed PO number found it. This is C-0073 in one bill.

## The item catalogue — a starting map, never an answer

Oil GRPO lines since Apr-2026, most-used first. **Codes are per book (trap 1); accounts
are per line (trap 2). Use this to recognise a bill, never to build one.**

| Oil code | Item | Account | |
|---|---|---|---|
| `CG0000015` | REFRESHMENT | `5630004` REFRESHMENT | exp |
| `CG0000007` | R&M BUILDING AND OFFICE | `5650001` R&M OFFICE & BUILDING | exp |
| `CG0000003` | R&M PLANT AND MACHINERY | `5650016` R&M PLANT & MACHINERY | exp |
| `CG0000005` | HOUSEKEEPING | `5680015` HOUSE KEEPING | exp |
| `CG0000013` `CG0000006` `CG0000014` | STATIONERY / PAPER RIM A4 | `5680012` PRINTING AND STATIONERY | exp |
| `CG0000004` | STAFF WELFARE | `5630003` STAFF WELFARE | exp |
| `CG0000008` | COMPUTER AND HARDWARE | `5680022` COMPUTER AND HARDWARE | exp |
| `CG0000011` `CG0000012` `CG0000010` `CG0000056` | INK / MAKEUP CARTRIDGE, WIRE SEAL, POLYTHENE BAGS | `5100015` **CONSUMABLE/DIRECT EXPENSE** | exp |
| `CG0000031` `CG0000019` `CG0000035` `CG0000018` `CG0000016` | BARCODE LABELS, THINNER, WAX RIBBON, INK CARTRIDGE WASHING, BUBBLE WRAP | `5100006` PACKAGING MATERIALS EXPENSES | exp |
| `CG0000048` | OIL TESTING CHEMICALS | `5100018` LAB & TESTING DIRECT EXPENSE | exp |
| `CG0000068` | BUILDING/HARDWARE FOR PEB SHED NEW LAND | `1212016` PEB SHED NEW LAND 2 ACRE | **capex** |
| `CG0000052` `CG0000049` | BUILDING MATERIAL / TIN SHED - NEW LAND WIP | `1212013` BUILDINGS WIP - NEW BUILDING | **capex** |
| `CG0000067` | TILES FOR DOCK AND 1ST FLOOR EXTENSION | `1212010` WIP- DOCK & 1ST FLOOR EXTENSION | **capex** |
| `CG0000034` | INSTALLATION PARTS 50 KL TANK | `1213006` TANK 50 KL - NEW | **capex** |
| `CG0000069` `CG0000070` `CG0000071` | GC MACHINE GASES / CHEMICAL / GLASSWARE | `1205009` AGILENT 8860 GC SYSTEM | **capex** |

Beverages runs a much wider `5100015` **CONSUMABLES DIRECT EXPENSE** — caustic soda,
alum powder, eco power hypo, DPD tablets, PH booster, D.A.P/urea, lab consumables, ink
and make-up — plus `1109005` PREPAID R&M (SIDEL) as its capex/prepaid head.
Regenerate rather than trust this table:
```bash
hana-sql/hana-sql 'SELECT T1."ItemCode", MAX(T2."ItemName"), T1."AcctCode", MAX(T3."AcctName"), MAX(T3."GroupMask"), COUNT(*)
FROM "<BOOK>"."PDN1" T1 LEFT JOIN "<BOOK>"."OITM" T2 ON T2."ItemCode"=T1."ItemCode"
LEFT JOIN "<BOOK>"."OACT" T3 ON T3."AcctCode"=T1."AcctCode"
WHERE T1."ItemCode" LIKE '"'"'CG%'"'"' AND T1."DocDate">='"'"'2026-04-01'"'"'
GROUP BY T1."ItemCode", T1."AcctCode" ORDER BY COUNT(*) DESC'
```

## Attachments — the draft carries both papers

Same recipe as `ap-rm-pm/reference/attachments-upload.md`, and it applies here in
all three books: download the GRPO's own copy of the bill → `sapb1 attach "VENDOR-REF-DATE.pdf"
"<grpo-file>.pdf" --yes` (scan = line 1, GRPO's copy = line 2 of the **same new row**; it stamps
`U_CHK = <size KB>`, `U_CHK2 = "OK"` and ticks **`CopyToTargetDoc = "tYES"`** on every line,
C-0090; Mart: the tick only) → `PATCH Drafts(<DocEntry>) {"AttachmentEntry": N}`
→ read back the draft **and** the GRPO (the GRPO must still carry its own row).
**Beverages has `U_CHK`/`U_CHK2` on `ATC1` exactly like Oil** — verified 2026-09-08,
`sapb1 attach` stamps there too — and enforces the
1 MB cap of trap 7. Bev files land on `\\10.10.101.52\Attachments_Bev\JIVO_BEVERAGES\Attachments`.

## Hard stops

- **Never `sapb1 post` this, or anything else document-shaped** — `post` refuses
  documents outright, and it would bypass the approver.
- **`add-draft` reaches the approver from a login the template names, and nowhere else.**
  The only Always-terms A/P templates are Oil **103**, Mart **48**, Bev **68**, and each
  names **USER39 (MUQEEM) and USER08 (DIVJOT)** — read back 2026-09-10, and all three
  books now route an API Add to approval (`OADM.EnbApprDI='Y'` everywhere, C-0088
  superseding C-0074). From those two logins, submit it. From **USER07/HARSH** the submit
  is still refused (guard 5c) and the honest finish on this class is: draft it, attach both
  papers, tell the operator the draft number, and a person presses **Add** in the SAP B1
  client. Say that plainly — and say that Bhawani's approval still does not post it.
- **A drafts-only desk finishes at the draft** — `harness/desks.json` → `drafts_only`.
- **Exit 7** = sent, outcome unknown → query `Drafts` by `NumAtCard`; do not re-send.
- If the draft is wrong: `sapb1 delete draft <DocEntry> --dry-run` first. With an
  attachment pointer set it needs `--with-attachment`; `PATCH`ing `AttachmentEntry` back
  to `null` is the cleaner route.

## Worked examples — 2026-09-08, eleven bills, all live, attached and read back

Every one drafted under **USER07 (HARSH)**, every one verified: total to the paisa,
`BaseType 20` links, all four dimensions, and the PDF downloading back off the share.

| Draft | Book | Vendor | Ref | Total | GRPO ← PO | What it taught |
|---|---|---|---|---|---|---|
| **56551** | Oil | DOMINO PRINTECH | 602627124886 | 1,09,230 | 2026096546 ← 220926000 | `5100015` direct expense; case→4 pcs; 24p rounding |
| **56552** | Oil | SHREE RAM RMC | SRR/26-27/1003 | 16,904 | 2026096547 ← 220926023 | capex `1212016`; `CG+SG@0`, GST in price |
| **56556** | Oil | GUPTA CEMENT STORE | 1386 | 35,400 | 2026086950 ← 220826163 | **August gate-in → August series 3684**; `FA*` item; `5680010` CETP |
| **56557** | Oil | SHREE RAM RMC | SRR/26-27/1009 | 28,173 | 2026096548 ← 220926023 | same PO as 1003, drew the remaining 5 cubic |
| **56558** | Oil | RAM BHAJ SURESH KUMAR | 270 | 956 | 2026096549 ← 220926022 | cartage inside the R&M line; gate counted 4 of 5 pieces |
| **56560** | Oil | RAM BHAJ SURESH KUMAR | 269 | 2,938 | 2026096550 ← 220926021 | handwritten **"Common" → `FACT_COM`** (C-0027), overriding the GRPO's `Factory` |
| **16031** | Bev | JN ENTERPRISES | 210 | 8,054 | 2026098045 ← **826228027** | the printed PO picked the book; Dim2 `08-2026`; 1 MB cap |
| **16037** | Bev | GUPTA CEMENT STORE | 1445 | 7,682 | 2026098051 ← 926228007 | "cement" bill with no cement; 15 lines; `for Pasteuriser (Beverage) Plant` |
| **16038** | Bev | AK ENIGNEERING | 1102 | 11,800 | 2026098046 ← 826228024 | the misspelled vendor card; name search fails, PO wins |
| **16039** | Bev | SIDEL INDIA | 18S0008488 | 2,412 | 2026098050 ← 126228016 | **`BaseLine` 6 and 14**, not 0 and 1 |
| **16040** | Bev | SIDEL INDIA | 18S0008475 | 3,41,892 | 2026098049 ← 626228001 | freight as an **additional expense**; capex `1204003` |

All eleven stopped at the draft for a human to press Add.

## A batch of scans — fan out to parallel agents, JSON back

Proven on 2026-09-08 with 11 files in one Telegram drop. One bill at a time is the
default; past three or four, the reading is the bottleneck and it parallelises cleanly.

**Split it this way, and do not move the line:** the agents do the *discovery* — read
the scan, find the PO and GRPO, duplicate-check. **The main loop does every write.**
A subagent has already created a real draft at JIVO despite read-only instructions,
so the instruction is not the control; not giving it the job is.

1. **Inventory first, then say what is missing.** List the files against what the
   operator sent and name the gaps in one line — they will send the rest. Watch for the
   browser's duplicate download (`Ram bhaj suresh kumar 269.pdf` *and* `269 (1).pdf`,
   identical bytes) and drop one, and check whether a file is already drafted before
   spending an agent on it.
   ```bash
   for f in "<name1>" "<name2>" …; do [ -f "$HOME/Downloads/$f.pdf" ] \
     && printf "  HAVE     %-34s %7s KB  %s pg\n" "$f" $(( $(stat -f%z "$HOME/Downloads/$f.pdf")/1024 )) \
        "$(pdfinfo "$HOME/Downloads/$f.pdf" | awk '/^Pages/{print $2}')" \
     || printf "  MISSING  %s\n" "$f"; done
   ```
2. **One agent per bill, launched in a single message** so they run concurrently.
   Every prompt carries: the scan path · the `zoom.py` tile discipline (**read every
   tile, settle digits by arithmetic**) · the three env files · "the printed PO number
   picks the book, the GSTIN cannot" · the `contains()` **timeout is not "no rows"**
   warning · the duplicate queries · the reconciliation checks · the JSON schema.
   Two things earn their place in every prompt:
   - **`YOU ARE READ-ONLY — absolute.` Only `sapb1 query` and `hana-sql`. Never
     `draft`/`post`/`patch`/`delete`/`add-draft`. If a write seems needed → `flags`.**
   - **Name the sibling refs in the same batch.** A drop like this one carries
     `SRR/26-27/1003` next to `1009`, `18S0008488` next to `18S0008475`, `269` next to
     `270` — tell each agent which number is *not* its own, or a short-ref search
     cross-reports and the wrong GRPO gets drafted.
   Model floor: omit `model` so the agent inherits the session's, or set `opus`.
   **Never Sonnet or Haiku on JIVO money work.**
3. **JSON back, one object per bill** — `vendor{name,gstin,pan}`, `invoice_no`,
   `invoice_date`, `buyer{}`, `printed_po_no`, `gate_stamp{}`, `paper_lines[]`,
   `tax{}`, `round_off`, `grand_total`, `handwritten_marks[]`,
   `sap{book,how_book_decided,books_searched[],all_numatcard_hits[],grpo{},grpo_lines[],po{},duplicate_posted_ap,existing_draft}`,
   `reconciliation{}`, `flags[]`. Real numbers, never placeholders; a genuinely absent
   field is `null` **plus a line in `flags`**. `"book":"NOT_FOUND"` with the search list
   is a good answer — an invented GRPO is not.
4. **Verify before you draft — every agent's GRPO claim, with your own query.** One
   `--filter "DocEntry eq N" --json` per bill confirms vendor, ref, total, branch and
   the open quantities. A wrong `BaseEntry` books somebody else's document, and that
   is not a risk to take on a report. This is cheap; skipping it is not.
5. **Second-pass duplicate gate across the batch itself.** Two files can be the same
   bill under different names, and two GRPOs can share one `NumAtCard`. Group the
   returned JSON by `(book, CardCode, invoice_no)` before building anything.
6. **Then draft serially** — payload, dry-run, send, read back, attach, one at a time,
   under the operator's own login. Hold anything whose reconciliation is `DIFF`, whose
   `flags` are non-empty, or whose book came back `NOT_FOUND`, and report those
   separately rather than guessing. Finish with one table: draft number, book, vendor,
   ref, total, GRPO ← PO, and what was held and why.

## Reference

`ap-rm-pm/SKILL.md` — the shared rules; read it first.
`ap-rm-pm/reference/attachments-upload.md` · `handwriting.md` ·
`series-and-errors.md` · `matching-and-batches.md` · `jsap-routing.md`.
`jivo-ap-service-draft` — the same bill shape with **no** GRPO behind it.
