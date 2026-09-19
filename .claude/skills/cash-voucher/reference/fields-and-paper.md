# Fields, dates and the paper behind a voucher

> Header and line fields, the papers that feed them, and how to attach.

> Reference for the `cash-voucher` skill family. The rules live in
> `cash-voucher/SKILL.md`; this file holds the detail behind them.

---

## Tax code — `Exampt`, unless a bill in the pack shows GST

**Daman: "tax code would be Exempt unless there is GST on any bill provided —
for all the cash vouchers. This would be applicable for all skills."**

| The pack contains | `TaxCode` |
|---|---|
| no bill, or a kacha / estimate / handwritten slip with no GST | **`Exampt`** |
| a registered vendor's **GST tax invoice** | **the bill's own code** — `CG+SG@18`, `IGST@…` — mirrored, never computed |

The code is spelled **`Exampt`** in SAP (`OSTC`), not "Exempt". Oil also carries
`IGST@0` and `CG+SG@0` at 0% — **do not reach for those**; the recent hand-keyed
cash vouchers use `Exampt` (56884, 56910, 56911 all `Exampt`).

**This applies even when the line is a GRPO copy.** The copy arrives carrying the
GRPO's code, usually `IGST@0`; override it to `Exampt` unless a GST bill is in the
pack. Both are 0%, so no amount moves.

---

## Vendor Ref. No. — `<MON> YY/<bunch>/<this document's total>`

Daman, 2026-09-12, on voucher 446: *"vendor ref no. we need to create:
month / yy / bunch total / the total amount of entry … like in this draft it would
have been: AUG 26 39940 / 150."*

```
AUG 26/39940/150
 │      │      └─ THIS document's total, not the bunch's
 │      └─ the printed Total of the table this voucher sits in
 └─ the BUNCH's month — one value for every voucher in that bunch
```

**The month belongs to the bunch, not to the voucher.** Voucher 446 is dated
**02/09/2026** and still takes **`AUG 26`**, because it sits in the AUG bunch that
the 04-09-2026 sheet closed. Confirming evidence: draft 56884 is a **July**-dated
voucher (425) in the same bunch and also carries `AUG 26`.

⚠️ *Three drafts on bunch 39940 carry `SEP 26` (56876, 56877, 56911). Each is
independently suspect — 56877 pairs a `SEP 26` prefix with a `08-2026` Dim2, and
56911 carries voucher 446's remarks and dimensions at ₹1,050 where the sheet says
₹150. Treat them as keying slips, not as a second rule. **If a sheet's bunch month
is not obvious, ask Daman — do not derive it from the voucher's date.***

**The exception is `cash-voucher-bill`:** a registered vendor's bill has its own
reference, so that type carries **the invoice number** and no bunch at all.

---

**Search all three books before calling a GRPO missing (C-0073).** Open GRPOs on
the card carry `NumAtCard` = `<amount>/<dd-mm-yy>`; confirm the match with the
`G.No.` printed in the GRPO's `Comments` against the gate stamp on the bill.

```sql
SELECT h."DocEntry", h."DocNum", h."DocDate", h."NumAtCard", h."DocTotal",
       l."ItemCode", l."AcctCode"
FROM   <DB>.OPDN h JOIN <DB>.PDN1 l ON l."DocEntry" = h."DocEntry"
WHERE  h."CardCode" = '<imprest card>' AND h."CANCELED" = 'N'
  AND  h."DocStatus" = 'O' AND l."LineNum" = 0;
```

---

## The paper — four documents per voucher

A DocScanner pack per voucher, typically 3 pages, plus the sheet:

| Paper | What it gives you |
|---|---|
| **Supplier's bill** (Estimate Bill / handwritten yellow slip) | the **document date**, the bill ref, the line items, JIVO's gate stamp (`G.No.`) |
| **The cash voucher slip** (JIVO WELLNESS VOUCHER, No. + Dated) | the **voucher number**, the **posting date**, the **costing date**, and the handwritten **budget** mark |
| **The GRPO print** (SAP "Goods Receipt Note") | the **G/L account**, item, dims, tax, HSN, qty, price — and the `DocEntry` to copy from |
| **The cash sheet** ("front sheet") | the **bunch** total, and the `Unit` column |

---

---

## 2 · `NumAtCard` (Vendor Ref. No.) — the bunch is that table's OWN total

```
<MON> YY / <bunch> / <this document's total>
```

**The bunch is the printed Total of the table the voucher sits in — NOT the two
tables added together.** Daman: *"bunch no. is wrong — 39940 was the bunch for
ours but it is written here 49097."*

The 04-09-2026 sheet has **two** bunches:

| Table | Bunch | Example |
|---|---|---|
| `Common` / `Canola` → **Oil** | **39940** | `AUG 26/39940/5190` (vch 437) |
| `Wg` → **Beverages** | **9157** | `<MON> 26/9157/<amount>` |

**Month prefix follows the DOCUMENT date (the bill), not the posting date.**
Voucher 437 posts 01-09-2026 but its bill is 31-08-26, so the prefix is
**`AUG 26`**. Precedent 50035 proves it: posted 06-08-2026, document date
31-07-2026, `NumAtCard` `JUL 26/32820/3800`. Three letters — `AUG 26`, never
`AUGUST 26` or `SEPT`.

*A trap for whoever reads the history: grouping posted docs on the middle token
does show some complete batches summing to it across two books (`64544` = Oil
48,934 + Bev 15,610, exact). That is not the rule. Take the bunch off the sheet.*

---

## 3 · `U_Remarks` = voucher number **AND** amount

**`VCH 437 - RS 5190`**, on **every** line of the draft. `NVARCHAR(100)`.

Older posted lines carry the bare number (230, 226, 205 …). Daman changed this on
2026-09-10 — **the amount goes in too**, on every line.

---

## A bill for a PERIOD that crosses a month — split it by days

**⚠️ TYPE-2 VENDOR BILLS ONLY. Never a plain cash voucher — see the box below.**

> 🔴 **NOT for a plain cash voucher. Daman, 2026-09-19:** *"No, while entering
> cash vouchers only the effective month is changed as on the voucher, the
> document date is the recent date from all of the vouchers."*
>
> Asked directly about **voucher 478** — a bus pass running 08-09 to 07-10, which
> had been split ₹1,303.17 on `09-2026` + ₹236.83 on `10-2026` — he said **no.**
> A cash voucher stays **whole, in the month of its own slip**, however long the
> period on the paper behind it.
>
> | Voucher | Period on the paper | Lines |
> |---|---|---|
> | **478** bus pass, slip dated Sep | 08-09 → 07-10 | **ONE**, ₹1,540, `CostingCode2` = `09-2026` |
>
> ⚠️ **SCOPE — ask if you are not sure.** The day-split below was Daman's own
> ruling on **voucher 421**, a registered vendor's GST tax invoice (`type 2 ·
> BILL`) with a printed service period and its own draft. The 2026-09-19 ruling
> was about a plain imprest voucher (`type 3`). Read as: **day-split a type-2
> vendor bill; never day-split a plain cash voucher.** That boundary has **not**
> been confirmed with him — if a type-2 bill straddles a month end, **ask before
> splitting it.**

Any bill that buys a stretch of time — internet, AMC, subscription, rent, an
insurance or service contract — prints its period. When that period straddles a
month end, the cost does **not** all belong to the month you post it in.

**Recipe**

1. Read the period off the bill (`12 AUG 2026 TO 12 SEP 2026`).
2. Count the days that fall in each calendar month, **inclusive of both end
   dates**: Aug 12→31 = **20**, Sep 1→12 = **12**, total **32**.
3. Prorate the **taxable** value (not the GST-inclusive total) by those days, and
   **put any rounding remainder on the last line** so the lines sum exactly.
4. One line per month, each with `CostingCode2` = **that month's** `MM-YYYY`.
   Everything else — account, tax code, Dim1, Dim3, Dim5, `U_Remarks` — is
   identical on every line.
5. GST follows each line on its own. Check `VatSum` and `DocTotal` are unchanged.

Voucher 421, ₹1,000 + 18%:

| Line | Days | Taxable | GST | `CostingCode2` |
|---|---|---|---|---|
| 0 | Aug 20 | **625.00** | 112.50 | `08-2026` |
| 1 | Sep 12 | **375.00** | 67.50 | `09-2026` |
| | 32 | 1,000.00 | **180.00** | DocTotal **1,180** ✓ |

⚠️ **`DocDate`, `TaxDate`, `Series` and `NumAtCard` do NOT change** — the document
is still one bill posted once. Only the **costing month** differs per line.

⚠️ On an existing draft this **changes the line count, so it is a rebuild, not a
PATCH** (a patched line count corrupts the price fields). Detach, delete,
recreate, then point the new draft back at the **same** `Attachments2` row.

---

## A FUEL line carries the quantity off the pump slip — `U_Recvd_Qty`

**Daman, 2026-09-12:** *"In the voucher consisting fuel we need to update its
received quantity — you can see the amount from the attachment."*

A `5650015 FUEL - VEHICLES` line is not finished at the rupees. The pump / CNG
cash memo prints **rate × quantity = amount**, and the **quantity** goes on the
line in **`U_Recvd_Qty`** (the line UDF; `Quantity` itself stays 0 on a service
line and cannot hold it).

Voucher 449, BPCL KMP CNG memo: rate **97.80**, quantity **5.04**, amount
**492.91** → line `5650015` ₹493 with **`U_Recvd_Qty` = 5.04**.

- **Indian pump slips are often in Devanagari numerals** — `९७.८०` is 97.80,
  `५.०४` is 5.04, `९९५९` is the truck number 9959. Read them as digits.
- **Prove the reading: rate × quantity must equal the printed amount.** 97.80 ×
  5.04 = 492.91. If it does not tie, you have misread a digit — do not send it.
- The rupees on the voucher may be the memo's amount **rounded** (492.91 → 493).
  The voucher's figure is what the line totals; the memo's is what proves the
  quantity.
- Same idea for any metered purchase on a cash voucher (diesel, petrol, CNG).
  A toll or Fastag line has no quantity — leave it 0.

---

## 8 · Attach — the voucher, the GRPO's file, and the front sheet

**Three lines on the draft's OWN `Attachments2` row.** Never point two documents
at one row.

| Line | File |
|---|---|
| 1 | the **cash voucher pack** — slip + supplier's bill (+ GRPO print), named `CASH-VCH-<no>-<dd-mm-yyyy>.pdf` |
| 2 | the **GRPO's own file** — download `Attachments2(<grpo AtcEntry>)/$value` and re-upload |
| 3 | the **cash sheet / front sheet** — `CASH-SHEET-FRONT-<HOLDER>-<date>.pdf` |

Daman, 2026-09-10: *"this front sheet — this also normally goes through it."*
The cash sheet goes on **every** voucher's draft, in both books.

Upload all three with ONE `sapb1 attach <pack> <grpo-file> <front-sheet> --yes`
(recipe: `ap-rm-pm/reference/attachments-upload.md`). Class-specific traps:

- **`[SAP -1116] (1120026) Attachment Size Should be Less Than 1 MB`** — the cap
  is **per FILE, not per row** (761 + 115 + 463 KB on one row was accepted).
  Re-render a fat photographed pack:
  `pdftoppm -r 100 -jpeg -jpegopt quality=45 pack.pdf out/pg` then
  `magick out/pg-*.jpg -quality 45 pack-small.pdf` (13 pages, 4.1 MB → 738 KB).
  **Spot-check a page** — the voucher number and amount must stay readable — and
  say in the report that the attached copy is a re-render.
- `sapb1 attach` stamps `U_CHK = <size KB>`, `U_CHK2 = 'OK'` on **every** line before
  you patch `AttachmentEntry` — without it SAP refuses with `-1116 (1120025)` (C-0082) —
  and ticks **`CopyToTargetDoc = 'tYES'` on every line, every book** (C-0090). Exit
  non-zero = not done; never hand-PATCH around it.
- SAP **auto-renames** a filename already on the share (name + ddmmyyyy + time).
  Harmless; the file is correct.
- A refused `AttachmentEntry` patch leaves an **orphan `Attachments2` row**. It is
  harmless and cannot be deleted from this CLI — report it, don't hide it.
- Prove it: pull `$value` back and `cmp`. For any line but the first the filename
  selector must be **quoted**: `$value?filename='NAME.pdf'`.

---

## 11 · Read the sheet — and prove the reading

**The sheet prints its own Total per table. Sum your transcription and match it
before building anything.** Phone scans are skewed, so voucher numbers sit
visually a line above their data and an off-by-one looks plausible. The printed
total is the checksum — on the 04-09-2026 sheet both tables tied to the rupee
(9,157 and 39,940), and that, not careful reading, is what proved the alignment.

- Render at 500 dpi and crop into bands; `-r 200` is not enough for the Amount
  column.
- Cross-check any voucher whose slip you have against its own bills
  (405 = 705 + 150 + 400 + 532 = 1,787 ✓).
- **A repeated pencil mark on every row is a tick-off, not a dimension.** Only a
  mark that *varies* between rows carries information (contrast
  `jivo-service-vehicle-expense` §2, where TR/BO/F genuinely set Dim3).
- If a table prints no total, say so — do not proceed as if it had.

---
