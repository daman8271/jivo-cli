# GRPO copies, and the SAP behaviours that bite

> How a GRPO copy is built, and the API traps that cost real money on 2026-09-19.

> Reference for the `cash-voucher` skill family. The rules live in
> `cash-voucher/SKILL.md`; this file holds the detail behind them.

---

## 🔴 RULE 0 — a GRPO voucher is COPIED FROM ITS GRPO

> ⚠️ **The "one draft per voucher" half of this rule is DEAD.** Superseded on
> 2026-09-12 (grouping) and again on **2026-09-19** by **ONE ENTRY PER PO**
> (C-0097) — which applies to GRPO vouchers too. Live proof: drafts **57454**,
> **57456** and **57457** each carry two or more GRPO-copy vouchers on one
> document. What survives below is the **copy** half: the lines come from the
> GRPO, so the G/L never comes from the voucher's wording. Document shape is
> decided in `SKILL.md` → **How the vouchers become documents**.

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

---

## Never pick the G/L from the wording — it is wrong about half the time

Measured on this sheet, guessing from the row's words versus reading the GRPO:

| Vch | Row wording | Guessed | GRPO's item → actual G/L |
|---|---|---|---|
| 437 | "some chemical for park maintain use" | R&M Building 5650001 ❌ | `CG0000005` HOUSEKEEPING → **5680015 HOUSE KEEPING** |
| 435 | "mcb for G.C lab use" | Lab & Testing 5680013 ❌ | `CG0000003` → **5650016 R&M PLANT & MACHINERY** |
| 436 | "tape roll for w.g plant use" | Stationery 5680012 ❌ | `CG0000021` TAPE ROLL → **5100006 PACKAGING MATERIALS** |
| 434 | "room temp machine" | R&M Plant 5650016 ❌ | `CG0000007` → **5650001 R&M OFFICE & BUILDING** |

**Four wrong out of nine.** The item on the GRPO decides the head. §7's map is a
last resort for a voucher with no GRPO at all, and nothing more.

---

## Find the voucher's GRPO

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

---

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

---

## 🔎 Telling an operator WHERE the draft is — never give them the `DocNum`

**Measured 2026-09-19 and it cost Daman a search:** a draft's `DocNum` is **not
its number.** It is the *next* number the series will hand out when the draft is
finally Added, so **every open draft in the series carries the same one.** Ten
drafts in Oil series 3325 all read `DocNum 626093112` — nine of Arvinder's plus
another desk's ₹2,87,710 document. Searching by it can never find one draft.

**Give them the `DocEntry`.** That is what the client calls the **Draft No.**, and
what SAP itself quotes back: *"Cannot remove drafts as Draft No. N is in approval
processes."*

Hand over **all** of this, not just a number:

| | |
|---|---|
| **Draft No.** | `DocEntry` — e.g. **57461** |
| Vendor | the card's full name |
| Posting date | `DocDate` |
| Total | `DocTotal` |
| Vendor Ref. No. | `NumAtCard` — `SEP 26/45939/7130` |

**Where to look:** `Purchasing – A/P` → `Purchasing Reports` → **Document Drafts
Report** — tick **A/P Invoice**, **Open Only**, **User = the creating login**, and
a posting-date range that covers the posting date. ⚠️ The User filter is the one
people miss; and a batch spanning months has drafts **outside** a single month's
range — 57455 is posted 31-08 while the rest are September.

Once `add-draft` has run the document is `AuthorizationStatus = dasPending` and
the approver sees it under **Approvals → Approval Status Report**, not in her
drafts list.

---

## ⛔ PATCHing a draft — you can ADD a line, you can NEVER remove one

**C-0103.** SAP merges `DocumentLines` **by `LineNum`**. Sending a shorter array
does **not** shorten the document: the extra line stays and the money shifts onto
it. Draft 57460 went **₹9,351 → ₹10,051** this way, and the same PATCH was sent
**13 times** before anyone noticed.

| Want to | Can you |
|---|---|
| **add** a line (incl. a GRPO copy — `BaseType`/`BaseEntry`/`BaseLine` do link) | **yes** — send the same PATCH **twice**, the second one populates the amounts |
| **change** a field on an existing line | yes |
| **remove** a line | **NO.** Delete the draft and rebuild it |

🔴 **Never send `UnitPrice` on a service line.** It makes SAP recompute
`LineTotal` — a ₹983 line was driven to ₹463.88. Send `LineTotal` only.

**If a PATCH does not do what you expected, stop after the second try** and read
the document back. Thirteen attempts is not persistence, it is a loop.

---

---
