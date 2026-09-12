---
name: cash-voucher-manual
description: CASH VOUCHER TYPE 3 — the voucher with NO GRPO and NO BILL, just the slip. Use when a JIVO WELLNESS voucher slip arrives on its own, or a cash-sheet row has no paper behind it — punctures, car and bike repairs, conveyance, porter and coolie charges, kitchen and refreshment, medical, staff welfare, small hardware. Books ONE A/P service draft per voucher against the holder's FACTORY IMPREST card, expense head picked from the wording, tax code Exampt, vendor ref = the bunch reference off the cash sheet. Not for a voucher with a Goods Receipt Note behind it (cash-voucher-1-grpo) and not for one with a registered vendor's GST invoice (cash-voucher-bill).
---

# Cash voucher · TYPE 3 · the MANUAL voucher — slip only

Daman named this type on **2026-09-12**: **"cash-voucher-manual"**. *"These are
basically without GRPO or any bills."*

Taught against voucher **446** of Arvinder sir's cash sheet dated 04-09-2026 —
"Cash Paid to Shyam Shukla for Car Puncture (XL6) (4618)", ₹150 → **Oil draft
56920**.

RULE 0 in `CLAUDE.md` governs the write. The rules that hold for **every** cash
voucher — the tax code and the vendor ref — live in **`cash-voucher`**; read them
first, they override anything here.

---

## How to know it is TYPE 3

**One piece of paper: the voucher slip.** No Goods Receipt Note print, no vendor
tax invoice, and no open GRPO on the imprest card at that amount (search all three
books before saying so — C-0073).

| Pack | Type | Skill |
|---|---|---|
| slip + GRPO print | 1 | `cash-voucher-1-grpo` |
| slip + a registered vendor's **GST** invoice | 2 | `cash-voucher-bill` |
| **slip alone** (or slip + a kacha/estimate slip with no GST) | **3** | **this one** |

A handwritten estimate slip with no GSTIN and no tax does **not** make it type 2 —
type 2 exists to route input credit to a vendor's GSTIN, and there is none here.

---

## 🔴 THE RULE — imprest card, service line, head from the wording

There is no vendor and nothing to copy, so **every field is chosen**, and the only
paper that can justify any of them is the slip and its row on the cash sheet.

```json
{
  "CardCode": "<the holder's FACTORY IMPREST card, this book>",
  "DocType": "dDocument_Service",
  "DocumentSubType": "bod_None",
  "Series": <HR_B for the slip's month>,
  "DocDate": "<the slip's date>",
  "TaxDate": "<the slip's date>",
  "DocDueDate": "<the slip's date>",
  "NumAtCard": "<BUNCH MON> YY/<bunch>/<this document's total>",
  "BPL_IDAssignedToInvoice": 2,
  "SalesPersonCode": <the cash holder's SlpCode>,
  "WTLiable": "tNO",
  "DocumentLines": [
    { "AccountCode": "<head from the wording>",
      "UnitPrice": <amount>,
      "TaxCode": "Exampt",
      "LocationCode": 2,
      "CostingCode":  "<the vehicle, or CANOLA / WATER>",
      "CostingCode2": "<MM-YYYY of the slip>",
      "CostingCode3": "<FACT_COM | Factory>",
      "CostingCode5": "HR",
      "U_Remarks": "<voucher number>" }
  ]
}
```

`DocType` is **`dDocument_Service`** — `AccountCode`, no `ItemCode`, and
**`UnitPrice`, never `LineTotal`**.

## 1 · Whose imprest, and whose name on the document

`CardCode` is the **FACTORY IMPREST card of the holder whose sheet this is**, in
this book — Oil `ORGV000465` ARVINDER SINGH IMPREST JWPL0115 FACTORY IMPREST
5 LAKH. `ORGV000019` (no "FACTORY IMPREST") is the decoy. Never clone a CardCode
between books. Full table: `cash-voucher` §5.

**`SalesPersonCode` is not a constant — it is whose cost this is.**

| SlpCode | Name |
|---|---|
| **7** | **ARVINDER SINGH** — the factory cash holder; this type's normal value |
| 38 | SUSHIL IT — an IT cost, e.g. the internet bill in `cash-voucher-bill` |

I had been treating 38 as a fixed header constant. It is not. Read `OSLP` and pick
the person the expense belongs to.

## 2 · Dates — there is only one date, so all three take it

No bill and no gate stamp exist, so the **slip's own date** is the posting date,
the document date and the due date.

| Field | Voucher 446 |
|---|---|
| `DocDate` (screen "Posting Date") | **2026-09-02** |
| `TaxDate` (screen "Document Date") | **2026-09-02** |
| `DocDueDate` | 2026-09-02 |

This is the one type where posting and document date agree. Type 1 takes the slip
for posting and the bill for document; type 2 takes the **gate stamp** for posting
and the bill for document. **Do not carry either of those here.**

## 3 · Series — `HR_B`, the imprest family

Same family as type 1, because this is the same card and there is no GST:

| Month | Oil |
|---|---|
| Aug-26 | 3324 `HR_B0826` |
| **Sep-26** | **3325 `HR_B0926`** |
| Oct-26 | 3326 |

The series follows **`DocDate`** — the slip's month — **not** the bunch month in
`NumAtCard`. Voucher 446 is `AUG 26/39940/150` and still sits in the **September**
series, because the slip is dated 02-09.

`HR_G` belongs to `cash-voucher-bill` (a GST vendor bill) and never to this type.
Probe an unknown month rather than guessing — a wrong series is refused safely
(`[SAP -10] … define the numbering series`).

## 4 · `NumAtCard` — the bunch reference, off the cash sheet

```
AUG 26/39940/150
```

Full rule, including why the month is the **bunch's** and not the voucher's:
`cash-voucher` → **Rules that hold for EVERY cash-voucher type**.

**You cannot build this without the cash sheet.** The bunch is the printed Total of
the table the voucher sits in — 39940 for the `Common`/`Canola` (Oil) table on the
04-09-2026 sheet, 9157 for the `Wg` (Beverages) one. If the operator hands you a
slip with no sheet, **ask for the sheet** rather than leaving the field blank or
inventing a reference.

## 5 · Tax — always `Exampt`

**Daman, 2026-09-12: "Tax code would be Exempt unless there is GST on any bill
provided."** There is never a bill in this type, so it is always **`Exampt`**
(spelled that way in `OSTC`). `VatSum` 0, `DocTotal` = the slip's amount.

Not `IGST@0`, not `CG+SG@0` — both exist at 0% and neither is what the hand-keyed
cash vouchers use.

## 6 · The expense head — you pick it, and you say so out loud

Nothing is inherited, so the **wording of the slip is all you have**. Use the map
in `cash-voucher` §7, and state in your report that you *chose* the head.

Voucher 446: "Car Puncture" → **`5650002` REPAIR & MAINTENANCE VEHICLE**.

**The four-wheeler / two-wheeler split is a real fork (C-0067, C-0070):**

| Slip says | Account | Dim1 |
|---|---|---|
| puncture, service, repair — **four-wheeler** | `5650002` R&M VEHICLE | **the vehicle** |
| fuel / CNG — four-wheeler | `5650015` FUEL - VEHICLES | **the vehicle** |
| Fastag, toll | `5660005` TOLL EXPENSE - VEHICLES | the vehicle |
| taxi, trip, factory→city travel, **any two-wheeler cost** | `5690002` CONVEYANCE | **`CANOLA`/`WATER`, never a vehicle** |

`5680000 GENERAL EXPENSES` is not a bucket (C-0071).

## 7 · Dim1 — the voucher usually names the vehicle, in brackets

**Daman, 2026-09-12: "this is XL6."**

The narration ends in bracketed tokens: **`(XL6) (4618)`** — the **model** and the
**last four digits of the registration**. Together they are a Dim1 code:

```
HR-4618  =  SUZUKI XL6-HR42H4618
```

```sql
SELECT "OcrCode","OcrName" FROM <DB>.OOCR
WHERE "DimCode"=1 AND "Active"='Y' AND "OcrName" LIKE '%<digits>%';
```

**Read the model token before dismissing it as a number.** In this hand `XL6`
looks exactly like `2L6` or `226`, and I logged it as an unexplained number until
Daman pointed at it. Oil has 89 active Dim1 codes — search on the **registration
digits**, which are unambiguous, and use the model only to confirm the hit.

The cash sheet's own wording can name a different model from the registration
(the 4618 row reads "Eeco car pancher" on the sheet and is an XL6 in SAP).
**The registration digits win.**

Where the voucher names no vehicle and no variety: **`CANOLA`** for Oil,
**`WATER`** for Beverages.

## 8 · Dim2, Dim3, Dim5

| Dim | Field | Value |
|---|---|---|
| 2 | `CostingCode2` | `MM-YYYY` of the **slip's** date — `09-2026` for voucher 446 |
| 3 | `CostingCode3` | **`FACT_COM`** when the slip is marked **Common**, else `Factory` |
| 5 | `CostingCode5` | `HR` |

**🔴 Dim2 and the `NumAtCard` month legitimately disagree.** Voucher 446 is
`CostingCode2` **`09-2026`** and `NumAtCard` **`AUG 26`**/…. Dim2 follows the
**voucher**; the vendor-ref month follows the **bunch**. That is not a mistake to
reconcile.

Dim3's mark is handwritten, in a different pen, and often crossed by the Manager's
signature — **tile-zoom the slip** (`jivo-ap-draft/bin/zoom.py --dpi 600 --box …`)
before deciding. On voucher 446 the green "Common" is clean and unmistakable.
Confirm any code is active: `SELECT "OcrCode" FROM <DB>.OOCR WHERE "DimCode"=3 AND "Active"='Y';`

## 9 · Remarks, description, Comments

- `U_Remarks` = **the bare voucher number** — `446`. Not `VCH 446 - RS 150`.
  The hand-keyed history is inconsistent (`VCH 437 - RS 5190`, `VOUCHER NO.425`,
  `430`, `446`); the recent ones are the bare number.
- line description: **empty**.
- header `Comments`: **blank**.

## 10 · A staff ADVANCE row is not an expense

"cash paid advance to <name> (deduct of <month> salary)" goes to that person's own
**`<NAME> ADVANCE JWPL####`** account. **If no such account exists, HOLD the row
and say so** — creating the ledger is master data, an admin's job. State the
arithmetic: *"₹34,940 entered + ₹5,000 held = ₹39,940 printed."* (`cash-voucher` §7.)

## 11 · ₹10,000 cap

No cash-voucher document may exceed **₹10,000**. One document, one voucher. If one
is over, **stop and tell the operator** — never split a voucher, never merge two.

## 12 · Attach — the slip, one line

The pack is the slip alone; there is no bill and no GRPO file to add. Name it
`CASH-VCH-<no>-<dd-mm-yyyy>.pdf`, one line on the draft's own `Attachments2` row.
Follow `jivo-ap-draft/reference/attachments-upload.md` — `-H "Expect:"` is
load-bearing, stamp `U_CHK`/`U_CHK2` (Oil only) **before** pointing the draft at
the row, each file under 1 MB, and `cmp` the `$value` read-back.

Daman's standing rule for the sheet-batch (`cash-voucher` §8) is that the **front
sheet** rides on every voucher's draft too. On a single loose voucher there is no
sheet to attach — but you needed it for `NumAtCard` anyway, so attach it when you
have it.

## 13 · Stop at the draft

`WddStatus` stays `-`. **Daman, 2026-09-12: "make draft only pls."**

Report the **`DocEntry`**, never the `DocNum` — every draft in one series shares
the same provisional `DocNum`. And hand over the retrieval path, because the
posting date is often a previous month and the report's default range hides it:

```
Purchasing - A/P → Purchasing Reports → Document Drafts Report
  ☑ A/P Invoice   ☑ Open Only
  User          = the login that created it
  Posting date  = a range covering the SLIP's month
```

---

## Worked example — voucher 446, end to end

Paper: **JIVO WELLNESS voucher 446**, dated 02/09/26, "Cash Paid to Shyam Shukla
for Car Puncture. (XL6) (4618)", ₹150, marked **Common** in green · and its row on
the **04-09-2026 cash sheet**: `446 | 02/09/2026 | … (4618) | 150 | Common`, table
Total **39940**.

```json
{ "CardCode": "ORGV000465",
  "DocType": "dDocument_Service", "DocumentSubType": "bod_None",
  "Series": 3325,
  "DocDate": "2026-09-02", "TaxDate": "2026-09-02", "DocDueDate": "2026-09-02",
  "NumAtCard": "AUG 26/39940/150",
  "BPL_IDAssignedToInvoice": 2, "SalesPersonCode": 7, "WTLiable": "tNO",
  "DocumentLines": [
    { "AccountCode": "5650002", "UnitPrice": 150, "TaxCode": "Exampt",
      "LocationCode": 2,
      "CostingCode": "HR-4618", "CostingCode2": "09-2026",
      "CostingCode3": "FACT_COM", "CostingCode5": "HR",
      "U_Remarks": "446" } ] }
```

→ Oil draft **56920** (`DocNum` 626093102), ₹150, VatSum 0, attachment row 177011
read back byte-identical, `WddStatus '-'`.

---

## What I got wrong, so nobody repeats it

| # | Field | I had | Correct | Root cause |
|---|---|---|---|---|
| 1 | `TaxCode` | `IGST@0` | **`Exampt`** | picked the zero-rate code type 1's **GRPO copy** happened to carry, instead of asking what a cash voucher uses. Three zero-rate codes exist; the hand-keyed vouchers all use `Exampt` |
| 2 | `NumAtCard` | **left blank** | **`AUG 26/39940/150`** | decided "no bill and no sheet in the pack" meant no reference existed. The reference was never on the slip — it is on the **cash sheet**, which I should have asked for |
| 3 | `(XL6)` | logged as an unexplained number `(226)` | the **model name** | read a handwritten token as digits because the field next to it was digits, then reported it as a mystery instead of testing it as a word |

**The pattern: when a field had no source in the pack, I left it empty or copied a
neighbouring document — instead of asking which piece of paper carries it.** For
this type the answer is usually **the cash sheet**.

---

## Pre-flight — tick before `--yes`

- [ ] **no GRPO** (all three books, C-0073) and **no GST bill** — otherwise wrong skill
- [ ] the **cash sheet** is in hand, and the voucher's row found on it
- [ ] `CardCode` = the holder's **FACTORY IMPREST** card for **this** book
- [ ] `DocType` `dDocument_Service`, `DocumentSubType` `bod_None`
- [ ] `DocDate` = `TaxDate` = `DocDueDate` = **the slip's date**
- [ ] `Series` = `HR_B<MMYY>` for the **slip's** month, period open (`OFPR.PeriodStat='N'`)
- [ ] `NumAtCard` = `<BUNCH MON> YY/<bunch>/<this doc's total>`, bunch = that
      table's **own printed Total**
- [ ] `TaxCode` **`Exampt`**, `VatSum` 0
- [ ] head chosen from the wording, four-wheeler vs two-wheeler fork checked, and
      **said out loud** that it was chosen
- [ ] Dim1 = the **vehicle** if the slip brackets one (match on the registration
      digits), else `CANOLA`/`WATER`
- [ ] Dim2 = the **slip's** month (may differ from the `NumAtCard` month — fine)
- [ ] Dim3 from the **tile-zoomed** slip; Dim5 `HR`
- [ ] `U_Remarks` = the **bare voucher number**; description empty; `Comments` blank
- [ ] `UnitPrice` set, not `LineTotal`
- [ ] document **≤ ₹10,000**
- [ ] advance rows on a named `ADVANCE` ledger or **held**, arithmetic stated
- [ ] slip attached, < 1 MB, `U_CHK2='OK'`, `$value` `cmp`'d
- [ ] **`DocEntry`** reported with the Document Drafts Report filters
- [ ] **not submitted** — draft only
