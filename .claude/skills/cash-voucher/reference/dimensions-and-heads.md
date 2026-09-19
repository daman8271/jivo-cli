# Dimensions, budgets and expense heads

> Everything about choosing a G/L head and the five costing dimensions. The spine in `SKILL.md` decides WHEN; this decides WHAT.

> Reference for the `cash-voucher` skill family. The rules live in
> `cash-voucher/SKILL.md`; this file holds the detail behind them.

---

## Dim3, the budget — where there is no precedent, decide in this order

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

---

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

---

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

---

## 6 · The `Unit` column — which book

> 🔴 **This is decided at STEP ZERO, before you open a company** — not here, not
> at field-filling time. Reading it late is how the 2026-09-19 batch was built in
> Beverages and then deleted. See **STEP ZERO · 1**.

| Unit | Book |
|---|---|
| **`Wg`** (water / beverage / "w.g plant") | **Beverages** |
| **`Canola`** | **Oil** |
| **`Common`** | **Oil** (and Dim3 `FACT_COM`, §4) |

**The Unit column beats the GRPO's book.** A voucher marked `Common` is an Oil
entry even when its PO and GRPO were raised in Beverages (C-0105, vouchers
460/461). Take the head off that GRPO, book it in Oil, and leave the stranded
GRPO for the factory.

**Dim1 and Dim5 come from the GRPO** — do not derive them. The Bev GRPOs of
29–31 Aug 2026 carry Dim1 **`DRINKS`**, not the `WATER` the posted service lines
use; both are live Bev codes. Only a voucher with no GRPO needs a Dim1 chosen,
and then it is `CANOLA` (Oil) / `WATER` (Bev), with `HR` for Dim5.

---

## Find an account by NAME, never by code prefix

The root cause of the 2026-09-12 freight error. Looking for an inward-freight
head I ran `AcctCode LIKE '567%'` because the outward one is `5670001`, got three
accounts, and picked the least-wrong of them. The right account is **`5680028`
FREIGHT INWARD-INDIRECT** — a different prefix entirely, and it never appeared.

**JIVO's chart does not group by meaning.** Freight heads alone are spread across
`5100002` (inward direct), `5300001` (outward export), `5500001` (import),
`5670001` (outward indirect) and `5680028` (inward indirect).

```sql
SELECT "AcctCode","AcctName","Postable" FROM <DB>.OACT
WHERE  UPPER("AcctName") LIKE '%FREIGHT%' OR UPPER("AcctName") LIKE '%CARTAGE%';
```

Search every word the thing could be called, across the whole chart, and read the
full list before choosing. A prefix filter silently hides the right answer and
leaves you confidently picking from the wrong shortlist.

---

## 🔴 Before you use a head you CHOSE, ask the card if it has ever used it

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

---

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
| freight / cartage / porter / courier moving goods **IN** to JIVO — a Porter (SmartShift) trip, a tempo, an auto carrying purchased goods or samples | **5680028 FREIGHT INWARD-INDIRECT** with an **RCM** tax code (`RIGST@5` inter-state, `RCGSG@5` intra-state) |
| freight on goods going **OUT** to a customer — sales dispatch | 5670001 FREIGHT AND CARTAGE OUTWARD-INDIRECT (the Delhi sales flow: Dim5 `DL`, Dim3 `Sales RE`) |
| **porter / coolie LABOUR** — men loading or unloading, no vehicle hired | 5670002 UNLOADING/LOADING CHARGES-INDIRECT |
| internet, mobile recharge | 5680003 TELEPHONE MOBILE AND INTERNET |
| printer cartridge, paper, stationery | 5680012 PRINTING AND STATIONERY |
| lab chemicals, GC/lab parts, testing | 5680013 LAB AND TESTING |
| courier, parcel | 5680023 POSTAGE & COURIER |
| legal papers, notary, stamp paper, rent/lease agreement, affidavit typing | **5680012 PRINTING AND STATIONERY** — *not* Legal & Professional (Daman, 2026-09-12, voucher 443) |
| a professional FIRM's fee — advocate, auditor, consultant, retainer, director | 5680025 LEGAL AND PROFESSIONAL |
| CETP / effluent | 5680010 CETP CHARGES |
| electricity, bank charge paid in cash | 5680011 / 5610003 |

`5680000 GENERAL EXPENSES` is not a bucket (C-0071).

---

## A staff ADVANCE row is not an expense

"cash paid advance to <name> (deduct of <month> salary)" goes to that person's own
**`<NAME> ADVANCE JWPL####`** account — precedent `11133156 SACHIN ADVANCE
JWPL2159` ₹1,000, `11133259 RIJVAN ADVANCE JWPL2764` ₹2,500.

**If no such account exists for them, HOLD that row and say so.** Do not park it
in an expense head or a generic staff debtor. Voucher 429 (₹5,000 to Mahesh
Kumar, new driver) was held for exactly this. Creating the ledger is master data,
an admin's job. State the arithmetic: *"₹34,940 entered + ₹5,000 held = ₹39,940
printed."*

---
