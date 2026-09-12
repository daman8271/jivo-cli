---
name: cash-voucher
description: PARENT skill for JIVO cash vouchers — routes to the right TYPE. Use when a CASH SHEET of numbered cash vouchers arrives, or a pile of JIVO WELLNESS voucher slips with their bills — a "Cash sheet (<name> sir)" Zoho table with Voucher no / Date / Details / Amount / Unit columns, "cash voucher entry", "cash sheet ki entry", a DocScanner pack of voucher slips. Routes each voucher to its type, then GROUPS the plain ones onto one A/P invoice against the holder's FACTORY IMPREST card - many vouchers, one line each, no document over Rs 10,000 and never spanning a month. A voucher with a GRPO behind it, or one made out to its own vendor, keeps its own draft. Also use to check what a cash sheet was booked as, or which voucher numbers are already keyed. NOT an employee's own reimbursement claim (jivo-service-vehicle-expense), NOT a vendor's own tax invoice (jivo-ap-draft / jivo-ap-service-draft).
---

# Cash voucher → one A/P draft per voucher, copied from its GRPO

Internal skill. Taught by Daman line by line on **2026-09-10**, against Arvinder
sir's cash sheet dated 04-09-2026. **Every rule below is a correction he made to
a draft I had already built.** Follow them; do not re-derive them — the section
"What I got wrong" at the end records what re-deriving costs.

Shared rules live in `jivo-ap-draft`; RULE 0 in `CLAUDE.md` governs the write.

**What this class is:** a factory cash holder (Arvinder) pays dozens of small
things in cash out of a ₹5-lakh float and writes a numbered voucher slip for
each. A Zoho sheet lists them all. Each voucher becomes **its own A/P invoice
against his FACTORY IMPREST card**, reducing the float JIVO already advanced him.

It is **not** an expense claim: nobody is being reimbursed, and the sheet's rows
name the people he *paid*, not the claimant. The claimant is the sheet's title.

---


---

## 🧭 FIRST — which TYPE is this voucher?

Cash vouchers split by **whether the purchase already went through a GRPO**. The
types do not share a payload, so pick one before building anything.

| Type | When | Skill |
|---|---|---|
| **1 · GRPO** | a GRPO printout is in the pack, **or** the row's amount matches an **open** GRPO on the imprest card | **`cash-voucher-1-grpo`** ← load this |
| **2 · BILL** | no GRPO, and the paper is a **registered vendor's GST tax invoice** — a GSTIN and CGST/SGST on it | **`cash-voucher-bill`** ← load this |
| **3 · MANUAL** | **no GRPO and no bill** — the slip alone. Punctures, vehicle repairs, conveyance, porter charges, kitchen, medical, small hardware | **`cash-voucher-manual`** ← load this |

**The three types share almost nothing. Do not carry a rule from one to another** —
that was the main mistake on 2026-09-12.

| | **1 · GRPO** | **2 · BILL** | **3 · MANUAL** |
|---|---|---|---|
| Books to | imprest card | **the real vendor** | imprest card |
| Doc shape | items, copied `BaseType 20` | service, `bod_GSTTaxInvoice` | service, `bod_None` |
| Posting date | the **slip** | the **gate stamp** | the **slip** |
| Document date | the **bill** | the **bill** | the **slip** (same day) |
| Series | `HR_B` | **`HR_G`** | `HR_B` |
| Tax | `Exampt` | **the bill's own GST** | `Exampt` |
| Vendor ref | `<MON> YY/<bunch>/<total>` | **the invoice number** | `<MON> YY/<bunch>/<total>` |
| G/L | **from the GRPO's item** | chosen from the head | chosen from the wording |
| Remarks | `VCH <no> - RS <amount>` | the bare number | the bare number |

---

## ⚖️ Rules that hold for EVERY cash-voucher type

Set by Daman on **2026-09-12**. These override anything type-specific below or in
a child skill.

### Document shape — GROUP the plain vouchers, ONE LINE each

**Daman, 2026-09-12, superseding the one-draft-per-voucher rule below:**
*"We can write this all together in one AP — except the GRPO ones and the
vouchers which have different parties. Make sure the total of an AP invoice
does not exceed ₹10,000; if you have multiple vouchers just divide it in 2 or
3 APs."*

| Voucher | Document |
|---|---|
| type 3 · MANUAL, and any type-1 voucher whose G/L you keyed by hand | **grouped** — many vouchers on ONE A/P against the imprest card |
| **type 1 · GRPO** (a real `BaseType 20` copy) | **its own draft**, always — a copy carries one GRPO |
| **type 2 · BILL** (its own party) | **its own draft**, always — a different `CardCode` cannot share a document |

**Three limits on a group, in this order:**

1. **≤ ₹10,000 per DOCUMENT.** Over that, split into 2 or 3 A/Ps. (s.40A(3).)
2. **Never span a month.** A document has one posting date, one series and one
   period. The 04-09-2026 sheet split into **August → `HR_B0826`** (₹7,403) and
   **September → `HR_B0926`** (₹1,236). Do not push an August voucher into a
   September document to balance the cap.
3. **Never split ONE voucher across two documents.** The voucher is atomic; the
   group is what flexes.

`DocDate` = the **latest voucher date in the group**. `NumAtCard`'s third token
is **this document's own total**, not a voucher's — `AUG 26/39940/7403`.

### One voucher = ONE line, under ONE head

**Daman, 2026-09-12, on voucher 420:** *"In row 2 and 3 you divided voucher 420
into printing-and-stationery and repair-and-maintenance-office. Instead we just
book it under printing and stationery with the whole amount."*

Voucher 420 is ₹3,370 — a printer-cartridge bill of ₹2,770 and a ₹600 LED stand.
I gave it two lines on two heads. **It gets one line of ₹3,370 on `5680012`.**
The head that describes the voucher takes the whole amount; a sub-item that rode
along on the same purchase does not earn its own head. (Draft 56910, keyed by
hand, does exactly this — I had the answer in front of me and split anyway.)

**The one exception — the voucher itemises genuinely different expense types
that carry different dimensions.** Vouchers 448 and 449 are dispatch trips that
list food, CNG and toll separately; fuel and toll take the **vehicle** Dim1 and
food takes `CANOLA`, so they cannot share a line. Two lines there is right, and
56910 splits them the same way.

**The test:** would the two parts take different **dimensions**? Then split.
Only a different-sounding *name* is not enough.

Every line carries `U_Remarks` = **its own voucher's number**, so each line
traces back to one slip even inside a group of nine.

### Tax code — `Exampt`, unless a bill in the pack shows GST

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

### Dim3, the budget — decide in this order

**Daman, 2026-09-12:** *"If any voucher has an invoice attached to it then its
budget would be DEL-BHKR. Right now it is 449 and 448."*

| # | If | `CostingCode3` |
|---|---|---|
| 1 | the voucher has an **invoice** attached to it | **`Del Bkhp`** (Delivery Bhakharpur) |
| 2 | the slip is marked **Common** | **`FACT_COM`** (Factory Common) |
| 3 | neither | **`Factory`** |

**"Invoice" here means the DISPATCH invoice, not a supplier's bill.** Vouchers 448
and 449 are the `No.9959` material-dispatch trips — the driver's food, CNG and
toll for a delivery run — and each slip carries the JIVO **sale invoice** for the
consignment it served. That is what moves the cost to Delivery Bhakharpur.

A supplier's own bill does **not** trigger it, and that is measured on this same
sheet: vouchers 416 (electrician's bill), 420 (two shop bills) and 430 (clinic
slip) all have paper attached and all stay on `Factory` / `FACT_COM`.

⚠️ **Untested: a slip marked `Common` that ALSO carries a dispatch invoice.** No
voucher on the 04-09-2026 sheet is both. Ask rather than assume the order above
resolves it.

Confirm any code is live before sending it:
`SELECT "OcrCode","OcrName" FROM <DB>.OOCR WHERE "DimCode"=3 AND "Active"='Y';`

### Vendor Ref. No. — `<MON> YY/<bunch>/<this document's total>`

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

## The paper — four documents per voucher

A DocScanner pack per voucher, typically 3 pages, plus the sheet:

| Paper | What it gives you |
|---|---|
| **Supplier's bill** (Estimate Bill / handwritten yellow slip) | the **document date**, the bill ref, the line items, JIVO's gate stamp (`G.No.`) |
| **The cash voucher slip** (JIVO WELLNESS VOUCHER, No. + Dated) | the **voucher number**, the **posting date**, the **costing date**, and the handwritten **budget** mark |
| **The GRPO print** (SAP "Goods Receipt Note") | the **G/L account**, item, dims, tax, HSN, qty, price — and the `DocEntry` to copy from |
| **The cash sheet** ("front sheet") | the **bunch** total, and the `Unit` column |

---

## 🔴 RULE 0 — a GRPO voucher is COPIED FROM ITS GRPO, in its own draft

> ⚠️ **The "one draft per voucher" half of this rule was superseded on
> 2026-09-12** — plain (type-3) vouchers are now GROUPED onto one A/P under the
> ₹10,000 cap. See **Document shape** above. A voucher that is a real GRPO copy
> still gets its own draft, and that is what the rest of this section is about.

**Daman: "create an entry under indirect expenses, pick the GL from GRPO, make
sure separate entry pass for every voucher, attachment must be made with that of
the cash voucher, and in remarks proper voucher number along with the amount must
be mentioned."**

A cash voucher that bought **goods** was raised as a **PO → GRPO against the
imprest card** before it reached you. The A/P invoice is a **copy of that GRPO**:

```json
{"BaseType": 20, "BaseEntry": <grpoDocEntry>, "BaseLine": <n>}
```

`DocType` is **`dDocument_Items`**, not service. One line per GRPO line.

**What the copy brings, and you must not touch:** the item, the **G/L account**,
the tax code, the HSN entry, the warehouse, the quantity, the price, **Dim1** and
**Dim5**.

**What the copy gets WRONG and you must set by hand on every line:**

| Field | Set to | Why the copy is wrong |
|---|---|---|
| `CostingCode2` (Dim2, costing date) | month of the **voucher slip's** date | copy carries the GRPO's month |
| `CostingCode3` (Dim3, budget) | from the **slip's handwritten mark** | copy carries the GRPO's `Factory` |
| `U_Remarks` | `VCH <no> - RS <amount>` | copy carries nothing |

### Never pick the G/L from the wording — it is wrong about half the time

Measured on this sheet, guessing from the row's words versus reading the GRPO:

| Vch | Row wording | Guessed | GRPO's item → actual G/L |
|---|---|---|---|
| 437 | "some chemical for park maintain use" | R&M Building 5650001 ❌ | `CG0000005` HOUSEKEEPING → **5680015 HOUSE KEEPING** |
| 435 | "mcb for G.C lab use" | Lab & Testing 5680013 ❌ | `CG0000003` → **5650016 R&M PLANT & MACHINERY** |
| 436 | "tape roll for w.g plant use" | Stationery 5680012 ❌ | `CG0000021` TAPE ROLL → **5100006 PACKAGING MATERIALS** |
| 434 | "room temp machine" | R&M Plant 5650016 ❌ | `CG0000007` → **5650001 R&M OFFICE & BUILDING** |

**Four wrong out of nine.** The item on the GRPO decides the head. §7's map is a
last resort for a voucher with no GRPO at all, and nothing more.

### Find the voucher's GRPO

Open GRPOs on the imprest card carry `NumAtCard` = **`<amount>/<dd-mm-yy>`**
(`5190/31-08-26`) — the supplier's bill reference. Match the amount, confirm with
the `G.No.` printed in the GRPO's Remarks against the gate stamp on the bill.

```sql
SELECT h."DocEntry", h."DocNum", h."DocDate", h."NumAtCard", h."DocTotal",
       l."ItemCode", l."Dscription", l."AcctCode", l."OcrCode", l."OcrCode3"
FROM   <DB>.OPDN h JOIN <DB>.PDN1 l ON l."DocEntry" = h."DocEntry"
WHERE  h."CardCode" = '<imprest card>' AND h."CANCELED" = 'N'
  AND  h."DocStatus" = 'O' AND l."LineNum" = 0
ORDER  BY h."DocDate";
```

`DocStatus 'O'` + line `TargetType = -1` = not yet copied. A **closed** GRPO
already has its A/P — never copy it twice.

---

## 1 · Dates — THREE papers, THREE different dates

**This is where the most corrections landed.** SAP's screen labels do not match
the OData field names, and I got them backwards:

| SAP B1 screen | OData field | Reads from | Voucher 437 |
|---|---|---|---|
| **Posting Date** | **`DocDate`** | the **cash voucher slip** | slip 01/09/26 → **2026-09-01** |
| **Document Date** | **`TaxDate`** | the **supplier's bill** | bill 31-08-26 → **2026-08-31** |
| — | `DocDueDate` | follows `DocDate` | 2026-09-01 |
| Costing date = Dim2 | `CostingCode2` | the **voucher slip** | 01/09/26 → **`09-2026`** |
| — | `Series` | the month **`DocDate`** lands in | **3325** (Sep) |

So a voucher routinely **posts in one month against a bill from the previous
one**, and costs to the posting month. That is correct, not a mismatch to fix.
Precedent confirms it: posted doc 50035 has posting date 06-08-2026 against
document date 31-07-2026.

**There is no "Costing Date" column.** Checked every column and UDF of `ODRF` and
`DRF1` — none is it. The costing date **is** Dimension 2, written as the
`MM-YYYY` code. Confirm the code is active in `OOCR` `DimCode = 2` first.

**Series (BPL 2, A/P invoice, `NNM1 ObjectCode 18`)** — the `HR_B` family, not
`HR_D`:

| Month | Oil | Bev |
|---|---|---|
| Jul-26 | 3323 | 2677 |
| Aug-26 | 3324 | 2678 |
| Sep-26 | **3325** | **2679** |
| Oct-26 | 3326 | 2680 |

Probe an unknown month rather than guessing — a wrong number is refused safely
with `[SAP -10] 10000521 … define the numbering series`. Check the period is open
(`OFPR.PeriodStat = 'N'`).

⚠️ **Patching `Series` silently resets `TaxDate` to `DocDate`.** It happened on
56767: one PATCH set `DocDate` 01-09 + `Series` 3325 + `TaxDate` 31-08, and the
read-back showed `TaxDate` had become 01-09. **Send `TaxDate` again in a second
PATCH and read it back.**

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

## 3 · `U_Remarks` = voucher number **AND** amount

**`VCH 437 - RS 5190`**, on **every** line of the draft. `NVARCHAR(100)`.

Older posted lines carry the bare number (230, 226, 205 …). Daman changed this on
2026-09-10 — **the amount goes in too**, on every line.

## 4 · Dim3, the budget — read the paper, never the GRPO (C-0027)

The **voucher slip** carries a handwritten allocation mark, and the cash sheet
repeats it in the `Unit` column. `Common` → **`FACT_COM`** (FACTORY COMMON).
The GRPO says `Factory`; **the paper overrides it, every time.**

Daman: *"Budget is wrong on all. It should be common."* — draft 56767 had been
built as a clean GRPO copy and carried `Factory` on all four lines, even though
the slip had `Common` underlined in the CREDIT block **and** the sheet's `Unit`
column said `Common`. Two independent tellings, both ignored because the copy
looked complete.

`Canola` → **ASK.** Not yet confirmed; do not assume `Factory`.

## 5 · Whose imprest — the card differs per book

| Book | CardCode | Name |
|---|---|---|
| Oil (`JIVO_OIL_HANADB`) | **`ORGV000465`** | ARVINDER SINGH IMPREST JWPL0115 FACTORY IMPREST 5 LAKH |
| Beverages (`JIVO_BEVERAGES_HANADB`) | **`ORGV000245`** | same name |
| Mart (`JIVO_MART_HANADB`) | `ORGV000217` | same name |

`ORGV000019` (plain, no "FACTORY IMPREST") is the decoy — never use it. **Never
clone a CardCode across books** ([[sap-named-connections]]). Match names in code,
not by OData filter (`toupper` unsupported; C-0036).

Other holders carry this class historically: `ORGV000041` BHUPINDER SINGH GINNI,
`ORGV000207` LOVPREET SINGH.

## 6 · The `Unit` column — which book

| Unit | Book |
|---|---|
| **`Wg`** (water / beverage / "w.g plant") | **Beverages** |
| **`Canola`** | **Oil** |
| **`Common`** | **Oil** (and Dim3 `FACT_COM`, §4) |

**Dim1 and Dim5 come from the GRPO** — do not derive them. The Bev GRPOs of
29–31 Aug 2026 carry Dim1 **`DRINKS`**, not the `WATER` the posted service lines
use; both are live Bev codes. Only a voucher with no GRPO needs a Dim1 chosen,
and then it is `CANOLA` (Oil) / `WATER` (Bev), with `HR` for Dim5.

### 🔴 Before you use a head you CHOSE, ask the card if it has ever used it

One query, and it is not optional. It caught the only wrong head in a batch of
nine on 2026-09-12, with no false alarms:

```sql
SELECT l."AcctCode", a."AcctName", COUNT(*) AS TIMES_USED, MAX(h."DocDate") AS LAST_USED
FROM   <DB>.OPCH h JOIN <DB>.PCH1 l ON l."DocEntry" = h."DocEntry"
JOIN   <DB>.OACT a ON a."AcctCode" = l."AcctCode"
WHERE  h."CardCode" = '<the card you are booking to>'
  AND  l."AcctCode" IN ('<every head you chose>')
GROUP  BY l."AcctCode", a."AcctName";
```

**A head with `TIMES_USED` = 0 on that card is wrong until proven otherwise.**
Stop and re-read the slip, or ask. Measured on Arvinder's imprest card, the eight
correct heads had 13–81 uses each; the wrong one had **zero**.

Run it against **the card the document is made out to** — a head with no history
on the imprest card can be perfectly normal on a vendor's card (`5670001` FREIGHT
AND CARTAGE is zero on the imprest card and routine on SmartShift's).

## 7 · Expense-head map — ONLY for a voucher with no GRPO

**Read RULE 0 first.** If the voucher has a GRPO this table is wrong by
construction. Use it only when no open GRPO matches, **say out loud** that you
picked the head rather than inherited it, and **run the zero-history check
above on every head you take from this table** — the table is a starting guess,
the card's own history is the evidence.

⚠️ **This table is worded in the operator's language, and the operator's words do
not name JIVO's accounts.** "Some legal documents" meant stamp paper and a notary
stamp, which is **stationery**; JIVO's LEGAL AND PROFESSIONAL head carries
advocates' and auditors' fees. Matching the narration's vocabulary to an account
name is the single most reliable way to get this wrong.

| Row says | Account |
|---|---|
| kitchen — vegetables, wood, tissue paper, canteen | 5630004 REFRESHMENT |
| medicine, hospital, safety shoes | 5630003 STAFF WELFARE |
| plant/machine repair, motor rewind, lathe work, welding repair | 5650016 R&M PLANT & MACHINERY |
| building fittings, park/grounds upkeep, hardware | 5650001 R&M OFFICE & BUILDING |
| housekeeping, cleaning/treatment chemicals | 5680015 HOUSE KEEPING |
| packing tape, wrap | 5100006 PACKAGING MATERIALS EXPENSES |
| puncture, service, repair — **four-wheelers** | 5650002 R&M VEHICLE *(vehicle Dim1)* |
| fuel/CNG — four-wheelers | 5650015 FUEL - VEHICLES *(vehicle Dim1)* |
| Fastag, toll | 5660005 TOLL EXPENSE - VEHICLES |
| taxi, trip, factory→city travel, **every two-wheeler cost** (C-0067) | 5690002 CONVEYANCE *(Dim1 `CANOLA`/`WATER`, never a vehicle — C-0070)* |
| porter/coolie charge, unloading, loading | 5670002 UNLOADING/LOADING CHARGES-INDIRECT |
| internet, mobile recharge | 5680003 TELEPHONE MOBILE AND INTERNET |
| printer cartridge, paper, stationery | 5680012 PRINTING AND STATIONERY |
| lab chemicals, GC/lab parts, testing | 5680013 LAB AND TESTING |
| courier, parcel | 5680023 POSTAGE & COURIER |
| legal papers, notary, stamp paper, rent/lease agreement, affidavit typing | **5680012 PRINTING AND STATIONERY** — *not* Legal & Professional (Daman, 2026-09-12, voucher 443) |
| a professional FIRM's fee — advocate, auditor, consultant, retainer, director | 5680025 LEGAL AND PROFESSIONAL |
| CETP / effluent | 5680010 CETP CHARGES |
| electricity, bank charge paid in cash | 5680011 / 5610003 |

`5680000 GENERAL EXPENSES` is not a bucket (C-0071).

### A staff ADVANCE row is not an expense

"cash paid advance to <name> (deduct of <month> salary)" goes to that person's own
**`<NAME> ADVANCE JWPL####`** account — precedent `11133156 SACHIN ADVANCE
JWPL2159` ₹1,000, `11133259 RIJVAN ADVANCE JWPL2764` ₹2,500.

**If no such account exists for them, HOLD that row and say so.** Do not park it
in an expense head or a generic staff debtor. Voucher 429 (₹5,000 to Mahesh
Kumar, new driver) was held for exactly this. Creating the ledger is master data,
an admin's job. State the arithmetic: *"₹34,940 entered + ₹5,000 held = ₹39,940
printed."*

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

Follow `jivo-ap-draft/reference/attachments-upload.md`; `-H "Expect:"` is
load-bearing. Class-specific traps:

- **`[SAP -1116] (1120026) Attachment Size Should be Less Than 1 MB`** — the cap
  is **per FILE, not per row** (761 + 115 + 463 KB on one row was accepted).
  Re-render a fat photographed pack:
  `pdftoppm -r 100 -jpeg -jpegopt quality=45 pack.pdf out/pg` then
  `magick out/pg-*.jpg -quality 45 pack-small.pdf` (13 pages, 4.1 MB → 738 KB).
  **Spot-check a page** — the voucher number and amount must stay readable — and
  say in the report that the attached copy is a re-render.
- Stamp `U_CHK = <size KB>`, `U_CHK2 = 'OK'` on **every** line *before* patching
  `AttachmentEntry`, or SAP refuses with `-1116 (1120025)` (C-0082). Every book's
  `ATC1` has both UDFs.
- SAP **auto-renames** a filename already on the share (name + ddmmyyyy + time).
  Harmless; the file is correct.
- A refused `AttachmentEntry` patch leaves an **orphan `Attachments2` row**. It is
  harmless and cannot be deleted from this CLI — report it, don't hide it.
- Prove it: pull `$value` back and `cmp`. For any line but the first the filename
  selector must be **quoted**: `$value?filename='NAME.pdf'`.

## 9 · Editing a draft after the fact

- **Field-only PATCH is safe** — dims, remarks, dates, `NumAtCard`. Send the
  **complete** `DocumentLines` array with every `LineNum` (a partial collection
  rewrites what you omit), then read the whole line back. Verified on 56767:
  G/L, Dim1/5, tax, HSN, prices, remarks, `AttachmentEntry`, `DocTotal` all
  survived.
- **Changing the line COUNT by PATCH corrupts the price fields** — rebuild
  instead (`jivo-service-vehicle-expense` §8): detach
  (`{"AttachmentEntry": null}`) → `sapb1 delete draft` → create fresh. Detaching
  first means the `--with-attachment` override is not needed and all six delete
  guards pass on a same-day draft of your own.
- **All drafts in one series share the same provisional `DocNum`.** Four drafts in
  series 3325 all read `626093102`. **Report `DocEntry`, never `DocNum`.**

## 10 · ₹10,000 cap

**Daman, 2026-09-10: "10k is the hard limit."** No cash-voucher document may
exceed **₹10,000**.

Since 2026-09-12 vouchers are **grouped**, so this is now the live constraint on
every document, not a theoretical one — it is what decides how many A/Ps a sheet
becomes. A single voucher is
rarely over ₹10,000. **If one is, stop and tell the operator.** Do not split the
voucher and do not merge vouchers to pack documents. Context, not a lecture:
s.40A(3) disallows cash expenditure over ₹10,000 to one person in one day.

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

## 12 · Stop at the draft

`WddStatus` stays `-`. The draft reaches nobody until a human presses **Add** in
*Purchasing – A/P → Purchasing Reports → Document Drafts Report* (tick **A/P
Invoice**, **Open Only**, **User = the creating login**, and a **posting-date
range that covers the posting date** — a September filter will not show an
August-posted draft). `ODRF.OwnerCode` is NULL, so anyone can Add it once the
User dropdown is changed.

`sapb1 add-draft` is **only** for a login an Always-terms template names (Oil 103
/ Mart 48 / Bev 68 → USER39, USER08). From USER07 or any other login it refuses,
and that refusal is correct — `jivo-add-and-new`, C-0078.

---

## Worked example — voucher 437, end to end

Paper: **Estimate Bill** from NEW SWAMI KHAD & BEEJ BHANDAR (Ganaur) ₹5,190 dated
31-08-26, gate stamp `G.No.639` · **voucher slip 437** dated 01/09/26 "Cash Paid
to Jasmeet ji for Purchase Some Chemical for Park Maintain use ₹5190/-", marked
`Common`, ₹100 revenue stamp · **GRPO print** 2026086899 (DocEntry 26374, PO
220826156) · the cash sheet.

```json
{ "CardCode": "ORGV000465", "DocType": "dDocument_Items",
  "DocumentSubType": "bod_None",
  "DocDate": "2026-09-01", "TaxDate": "2026-08-31", "DocDueDate": "2026-09-01",
  "NumAtCard": "AUG 26/39940/5190", "Series": 3325,
  "BPL_IDAssignedToInvoice": 2, "SalesPersonCode": 7, "WTLiable": "tNO",
  "Comments": "BEING EXPENSE BOOKED AGAINST HOUSE KEEPING 5190/-, CASH VCH 437 DT 01-09-26, BILL 5190/31-08-26 NEW SWAMI KHAD & BEEJ BHANDAR, G.NO.639",
  "DocumentLines": [
    {"BaseType":20,"BaseEntry":26374,"BaseLine":0,"U_Remarks":"VCH 437 - RS 5190","CostingCode2":"09-2026","CostingCode3":"FACT_COM"},
    {"BaseType":20,"BaseEntry":26374,"BaseLine":1,"U_Remarks":"VCH 437 - RS 5190","CostingCode2":"09-2026","CostingCode3":"FACT_COM"},
    {"BaseType":20,"BaseEntry":26374,"BaseLine":2,"U_Remarks":"VCH 437 - RS 5190","CostingCode2":"09-2026","CostingCode3":"FACT_COM"},
    {"BaseType":20,"BaseEntry":26374,"BaseLine":3,"U_Remarks":"VCH 437 - RS 5190","CostingCode2":"09-2026","CostingCode3":"FACT_COM"}
  ] }
```

→ draft **56767**, ₹5,190, VatSum 0. Read back: `CG0000005` / **5680015 HOUSE
KEEPING** / `CANOLA` / `HR` / `IGST@0` / HSN 237 / LocCode 2 all inherited from
the GRPO; Dim2 and Dim3 set by hand. Attachment row 176525 carries the voucher
pack (761 KB), the GRPO's bill photo (115 KB) and the front sheet (463 KB), all
`U_CHK2='OK'` and all read back byte-identical.

`Comments` shape, **≤ 254 characters** (`[SAP -8112] … Value too long` above it):

```
BEING EXPENSE BOOKED AGAINST <HEAD> <total>/-, CASH VCH <no> DT <dd-mm-yy>,
BILL <ref> <SUPPLIER>, G.NO.<n>
```

---

## What I got wrong, so nobody repeats it

Every one of these was a correction Daman made to draft 56767 **after** I had
built it and reported it as finished.

| # | Field | I had | Correct | Root cause |
|---|---|---|---|---|
| 1 | Document shape | one draft per book, grouped to fill the ₹10k cap | **one draft per voucher** | invented a grouping rule from posted history instead of asking |
| 2 | G/L | hand-picked from the row's wording | **from the GRPO's item** | never looked for a GRPO; assumed the class was service-only |
| 3 | Dim3 budget | inherited the GRPO's `Factory` | **`FACT_COM`** from the slip's "Common" | treated a GRPO copy as authoritative for *everything* (C-0027 was in context and ignored) |
| 4 | Dim2 costing | inherited the GRPO's `08-2026` | **`09-2026`** from the slip's date | same |
| 5 | Vendor ref bunch | `49097` (both tables added) | **`39940`** (that table's own Total) | trusted an inference from history over the sheet in hand |
| 6 | Posting date | 31-08-2026 | **01-09-2026** (slip's date) | mapped SAP's screen label "Document Date" to `DocDate` instead of `TaxDate` |

**The pattern in all six: a derived rule beat the paper in front of me.** The
paper wins. When a GRPO and a slip disagree, the slip wins for Dim2/Dim3 and the
GRPO wins for the G/L — and when neither is clear, ask instead of inferring.

---

## Pre-flight — tick before `--yes`

- [ ] transcription **summed and matched to that table's printed Total**
- [ ] **every voucher searched for an open GRPO** (amount + `G.No.`); where one
      exists the draft is a **copy** and no G/L, item, tax, HSN, Dim1 or Dim5 is
      set by hand
- [ ] plain vouchers **grouped** ≤ ₹10,000, never spanning a month, no single
      voucher split across documents; GRPO copies and own-party vouchers alone
- [ ] **one line per voucher**, whole amount on one head — split only when the
      parts take different dimensions
- [ ] every CHOSEN head run through the **zero-history check** against the card
      the document is made out to; nothing with `TIMES_USED` = 0 sent
- [ ] FACTORY IMPREST `ORGV…` for **this book** — not the plain twin, not another
      book's code
- [ ] `DocDate` (posting) = the **voucher slip's** date
- [ ] `TaxDate` (document) = the **supplier's bill** date
- [ ] `Series` = `HR_B<MMYY>` for **`DocDate`**'s month, period open; if `Series`
      was patched, **`TaxDate` re-sent and read back**
- [ ] `CostingCode2` = month of the **slip's** date, on every line
- [ ] `CostingCode3` = the **slip's** mark (`Common` → `FACT_COM`), on every line
- [ ] `U_Remarks` = `VCH <no> - RS <amount>`, on every line
- [ ] `NumAtCard` = `<bill's MON> YY/<that table's Total>/<this doc's total>`
- [ ] `VatSum` 0; `WTLiable` tNO
- [ ] `Comments` ≤ 254 chars
- [ ] attachment row carries **voucher pack + GRPO's file + front sheet**, every
      file < 1 MB, `U_CHK2='OK'` on each, `$value` read back and `cmp`'d
- [ ] advance rows on a named `ADVANCE` ledger or **held**, with the arithmetic
      stated
- [ ] `DocEntry` reported, never `DocNum`
