---
name: cash-voucher
description: PARENT skill for JIVO cash vouchers — routes to the right TYPE and carries the rules every type shares. Use when a CASH SHEET of numbered cash vouchers arrives, or a pile of JIVO WELLNESS voucher slips with their bills — a "Cash sheet (<name> sir)" Zoho table with Voucher no / Date / Details / Amount / Unit columns, "cash voucher entry", "cash sheet ki entry", a DocScanner pack of voucher slips. Groups the plain vouchers onto A/P invoices against the holder's FACTORY IMPREST card - ONE ENTRY PER PO even when its vouchers fall in different months, no document over Rs 10,000, effective month per LINE. A voucher whose GRPO sits on a vendor's own card goes to that vendor plus a JV. The batch STOPS AT THE DRAFT until Daman has seen the list. Also use to check what a cash sheet was booked as, or which voucher numbers are already keyed. NOT an employee's own reimbursement claim (jivo-service-vehicle-expense), NOT a vendor's own tax invoice (ap-rm-pm / jivo-ap-service-draft).
---

# Cash vouchers → A/P drafts on the factory imprest card

**What this class is:** a factory cash holder (Arvinder) pays dozens of small
things in cash out of a ₹5-lakh float and writes a numbered voucher slip for
each. A Zoho sheet lists them all. Those vouchers become **A/P invoices against
his FACTORY IMPREST card**, reducing the float JIVO already advanced him.

It is **not** an expense claim: nobody is being reimbursed, and the sheet's rows
name the people he *paid*, not the claimant. The claimant is the sheet's title.

> ### 🔴 Every rule here was bought with a mistake
> This skill was taught by Daman line by line on **2026-09-10**, corrected on
> **09-12**, and rewritten on **2026-09-19** after a batch of ten drafts went
> wrong in nine different ways. **Each rule carries its reason.** Read the
> reason. The single biggest failure in this skill's history was an AI
> *re-deriving* a rule from first principles — "a document has one posting date,
> therefore it cannot span a month" — which was true, sensible, and wrong.
> When a case does not match an example here, reason from the **reason**, or ask.

> ### 🔴 ATTACHMENT RULE — every file goes up with `sapb1 attach`, never by hand
> (Daman, 16 Sept 2026 · C-0090.) Whatever this skill attaches — draft, GRPO,
> A/P, credit memo, payment, JV, A/R — upload it with
> **`sapb1 attach <file> [<file>...] --company <DB>`** (`--dry-run`, then `--yes`).
> It puts every file on ONE `Attachments2` row, ticks **Copy to Target Document =
> `tYES`** on each line (plus `U_CHK`/`U_CHK2 OK` in Oil and Bev — Mart has no
> such fields), reads the row back, and exits non-zero unless every line is
> `tYES` and every file downloads byte-identical. Any other route lands `tNO`,
> and then the scan does **not** follow the document onward (GRPO → A/P,
> draft → posted). Full detail: `reference/fields-and-paper.md`.

RULE 0 in `CLAUDE.md` governs the write. Shared A/P mechanics live in `ap-rm-pm`.

---

## 🗺️ The whole job, in order

Do these in this order. Most of the 2026-09-19 failures were things done in the
wrong order — a book chosen after the payload was built, a submission sent before
anyone had looked.

| # | Step | Never skip because… |
|---|---|---|
| 1 | **STEP ZERO** — book, GRPO, whose card | all three were missed once, each cost a rebuild |
| 2 | **Type** each voucher | the three types share almost no payload |
| 3 | **Shape** the documents — one per PO, ≤ ₹10,000 | grouping decided late gets re-done |
| 4 | **Build** each draft (child skill) | — |
| 5 | **Attach** the packs | a GRPO cannot post without its receiving |
| 6 | **Read back** every dimension | SAP stores silently wrong values |
| 7 | 🛑 **STOP. Show Daman the list. WAIT.** | once submitted, nothing can be undone |
| 8 | `add-draft` on his word, one at a time | — |

---

## 🚦 STEP ZERO — three questions before you build anything

All three were missed on 2026-09-19 and each one cost a rebuild. Answer them
**in this order**, for every sheet, before a single payload is written.

### 1 · Which BOOK? — the sheet's **Unit** column decides. Nothing else does.

**Daman, 2026-09-19 · C-0105.**

| Unit column says | Book |
|---|---|
| `Common` | **Oil** — `JIVO_OIL_HANADB` |
| `Canola` | **Oil** — `JIVO_OIL_HANADB` |
| `Wg` / Wellness | **Beverages** — `JIVO_BEVERAGES_HANADB` |

🔴 **A GRPO raised in another book does NOT move the voucher.** Vouchers 460 and
461 were marked `Common`, but their PO 826228033 and GRPOs 2026088342 /
2026088343 had been raised on the **Beverages** imprest card. They were entered
in Beverages — wrong. Draft 16335 was deleted and re-keyed in Oil as 57468.

Book it in the **sheet's** book, take the expense head off that GRPO, and hand
the stranded GRPO back to the factory to close. That is a factory cleanup.

> **Why:** the Unit column is the business telling you which company's P&L the
> cost belongs to. Where the factory happened to raise a GRPO is a data-entry
> fact about the factory, not a fact about whose cost it is.
>
> **Why FIRST:** this rule already existed, buried at §6 as a field-filling note.
> It was read *after* a book had been chosen off the GRPO — so a whole batch got
> built in Beverages and deleted. A decision read late is a decision not made.

### 2 · Is there a GRPO? — search EVERY card, in ALL THREE books

**C-0102.** The search this skill used to carry filtered
`WHERE h."CardCode" = '<imprest card>'`. **That query cannot find the GRPO you
are looking for**, because a cash voucher's GRPO is often raised on the
*supplier's own* card:

| Voucher | GRPO | sat on |
|---|---|---|
| 472 / 473 / 475 | 26731, 26732, 26733 | **VENDA001090 ASHOK KITAB GHAR** |
| 467 | 26734 | **VENDA001182 BAJAJ ELECTRICAL** |

All four came back "no GRPO" and were retyped by hand on Arvinder's card,
leaving four GRPOs open in the books.

```sql
-- EVERY card, not just the imprest one. Run it in Oil, Mart AND Bev (C-0073).
SELECT h."DocEntry", h."DocNum", h."DocDate", h."CardCode", h."CardName",
       h."NumAtCard", h."DocTotal"
FROM   <DB>.OPDN h
WHERE  h."CANCELED" = 'N' AND h."DocStatus" = 'O'
  AND (h."NumAtCard" LIKE '%<bill no>%' OR h."DocTotal" = <amount>)
ORDER  BY h."DocDate";
```

**Match on the bill number in `NumAtCard` — it is exact.** Never on the
handwritten gate number off a phone scan: `634` was misread as `684`, `675` as
`678`.

> **Why the bill number:** `NumAtCard` was typed from the bill by the person who
> raised the GRPO. The gate number is handwritten on a slip and photographed at
> an angle. One is data, the other is your eyesight.

### 3 · WHOSE card is that GRPO on? — it changes the whole document

**Daman, 2026-09-19 · C-0098 — *"Enter it to the vendor and raise a JV to take it
off his float."***

| GRPO sits on | The A/P goes to | Then |
|---|---|---|
| the **imprest** card (`ORGV…`) | the imprest card, as a GRPO copy | nothing — the float comes down by itself |
| the **vendor's own** card | **that vendor**, as a GRPO copy | **a JV** — Dr the vendor / Cr FACTORY IMPREST (`cash-voucher-jv`) |

**Never retype a vendor-card GRPO as a hand-keyed line on the imprest card.**

**One JV per voucher, never combined.** 472 ₹1,716 · 473 ₹400 · 475 ₹1,716 ·
467 ₹590 are **four** journal vouchers.

If the A/P is **already posted** on the vendor, you owe only the JV. (Voucher
463: OPCH 51358 H M PLASTICS ₹2,596 already existed; JV 6881 closed it. Daman:
*"There is already an entry in H M Plastic, u just have to pass JV in Arvinder
sir. For future reference, book the invoice and pass JV."*)

> **Why:** an A/P copied from the GRPO is the only thing that **closes** that
> GRPO. Retyping the expense somewhere else books the cost but leaves the GRPO
> open for ever — four of them are open right now because of this. And the JV is
> needed because when the A/P lands on the vendor, nothing has reduced Arvinder's
> float, even though his cash is what paid for it.

---

## 🧭 Which TYPE is each voucher?

Cash vouchers split by **whether the purchase already went through a GRPO**. The
types do not share a payload, so pick one before building anything.

| Type | When | Skill |
|---|---|---|
| **1 · GRPO** | a GRPO printout is in the pack, **or** STEP ZERO found an open GRPO matching it | **`cash-voucher-1-grpo`** |
| **2 · BILL** | no GRPO, and the paper is a **registered vendor's GST tax invoice** — GSTIN and CGST/SGST on it | **`cash-voucher-bill`** |
| **3 · MANUAL** | **no GRPO and no bill** — the slip alone. Punctures, vehicle repairs, conveyance, porter, kitchen, medical, small hardware | **`cash-voucher-manual`** |

**The three types share almost nothing. Do not carry a rule from one to
another** — that was the main mistake of 2026-09-12.

| | **1 · GRPO** | **2 · BILL** | **3 · MANUAL** |
|---|---|---|---|
| Books to | imprest card¹ | **the real vendor** | imprest card |
| Doc shape | items, copied `BaseType 20` | service, `bod_GSTTaxInvoice` | service, `bod_None` |
| Series | `HR_B` | **`HR_G`** | `HR_B` |
| Tax | `Exampt` | **the bill's own GST** | `Exampt` |
| Vendor ref | `<MON> YY/<bunch>/<total>` | **the invoice number** | `<MON> YY/<bunch>/<total>` |
| G/L | **from the GRPO's item** | chosen from the head | chosen from the wording |
| Remarks | `VCH <no> - RS <amount>` | the bare number | the bare number |
| Needs a JV | only if ¹ | **yes** | no |

¹ unless its GRPO sits on the vendor's card — then the vendor, plus a JV
(STEP ZERO · 3).

---

## ⚖️ How the vouchers become documents

### Rule 1 · ONE ENTRY PER PO — even across months

Vouchers that share a PO share a document. **A cash-voucher A/P may span
months.** (Daman, 2026-09-19 · C-0097.)

🔴 **The old "never span a month" rule is DEAD.** It is what wrongly split PO
220826165 (voucher 468, 31-08) away from voucher 466 (09-09), and PO 220826164
the same way. **Do not re-derive it** from the fact that a document has one
posting date and one series. It does, and it still spans months.

Draft **57456** is the proof it works: ₹5,700, vouchers 468 and 466 on one PO,
carrying an `08-2026` line and `09-2026` lines together. That is correct.

> **Why:** the PO is the real-world unit of purchase. Splitting one PO across two
> documents makes the two halves untraceable to each other and leaves a GRPO
> matched against a document it only half belongs to. The calendar is a reporting
> convenience; the PO is the transaction.

### Rule 2 · ≤ ₹10,000 per DOCUMENT — the only thing that splits a PO

**Daman, 2026-09-10: "10k is the hard limit."** Over ₹10,000, split the PO into
2 or 3 A/Ps — **at voucher boundaries**. That is why PO 220926034 is two entries.

> **Why:** s.40A(3) disallows cash expenditure over ₹10,000 to one person in one
> day. This is law, not a house preference.

### Rule 3 · NEVER split one voucher across two documents

The voucher is atomic; the group is what flexes. A single voucher over ₹10,000 is
rare — **if one appears, stop and tell the operator.** Do not split it to fit and
do not merge vouchers to pack a document.

---

## 📅 Dates — three of them, and they mean different things

**This is where the most corrections landed**, and it is the one place worth
understanding rather than memorising.

| SAP B1 screen | OData field | Takes its value from |
|---|---|---|
| **Posting Date** | **`DocDate`** | the **LATEST voucher slip in the entry** |
| **Document Date** | **`TaxDate`** | the supplier's bill where the document has ONE; otherwise the latest slip |
| Costing date = Dim2 | **`CostingCode2`** | **PER LINE** — each voucher's OWN slip date |
| — | `Series` | the month **`DocDate`** lands in |
| — | `DocDueDate` | follows `DocDate` |

### 🧠 Why they differ — read this before touching a date

**The effective month (`CostingCode2`) is when the cash left the float.** That is
the event being recorded. Arvinder writes a date on the slip; that date is when
the money went out and when the factory incurred the cost. It is **per line**
because each voucher is its own cash event.

**The posting date is a batching artefact.** We put several vouchers on one A/P
because of the PO rule and the ₹10,000 cap. The document then needs *one* date,
so it takes the latest slip. That is filing convenience — **it must never drag an
August voucher's cost into September's numbers.** Different fields, different
questions.

**A period printed on a bill is about consumption, not cash.** Voucher 478's DTC
pass runs 08-09-26 → 07-10-26. Accrual logic says split it ₹1,303 September /
₹237 October. **That is wrong here.** Daman, 2026-09-19: *"only the effective
month is changed as on the voucher."* A cash voucher records ₹1,540 leaving a
float on one day in September — splitting it invents an expense in a month where
no cash moved, and breaks the float reconciliation. It is also uncheckable: any
person can look at the slip and see its date; nobody can eyeball ₹236.83.

⚠️ **Day-splitting a period survives only for a type-2 vendor bill** (Daman's
voucher 421 internet ruling, 2026-09-12 — see `reference/fields-and-paper.md`).
**Never for a plain cash voucher.** That boundary is not yet confirmed with him —
if a type-2 bill straddles a month end, **ask.**

⚠️ **Patching `Series` silently resets `TaxDate` to `DocDate`.** Send `TaxDate`
again in a second PATCH and read it back. (Measured on 56767.)

Series numbers, period checks and the `HR_B` family: `reference/fields-and-paper.md`.

---

## ❓ The ASK list — five things you never decide alone

Every one of these was decided alone once, and every one became a correction.
**Asking costs one message. Being wrong costs a rebuild, or an approval cycle.**

| # | When | What you do |
|---|---|---|
| 1 | one voucher's bills span **two expense heads** | **ASK.** Never split, never merge, on your own reading |
| 2 | the last SAP entry **contradicts the slip's own handwritten mark** | **ASK** — two papers against one precedent is not yours to settle |
| 3 | a precedent budget makes **no sense** for what the voucher is | **ASK.** 467 → `Del Bkhp` is a *delivery* budget on a factory STP repair |
| 4 | a **single voucher** exceeds ₹10,000 | **ASK.** Do not split it to fit |
| 5 | a **type-2 bill** covers a period crossing a month end | **ASK** before day-splitting it |

### The shape of a good ask

**Daman, 2026-09-19 · C-0100 — *"Do not split it yourself ask from me first."***

> Voucher 453 · ₹2,083 · sheet says `5650015` FUEL - VEHICLES
>   • CNG — ₹983 (XL6)
>   • reversing camera — ₹1,100 · RD 1 Stop Drive Tech, 01-09-26
>
> Two heads on one voucher. One line or two?

Name the voucher, the amount, what the sheet says, what the **bills** say, and
the actual question. Then key exactly what he answers — nothing else.

**Read the bills behind the voucher, not just its narration** — that is how you
notice there is a question to ask at all. Voucher 420's narration is one
sentence; its two bills belong in two heads.

> **Why not just decide:** on 2026-09-12 Daman split voucher 420 himself. That
> was **his call, made when asked** — it is not a licence to split the next one.
> Precedent does not settle a split either. Only he does.

---

## 🔴 The sheet's GL and Budget columns are a WORKING NOTE, not the authority

**Daman, 2026-09-19 · C-0099 — asked which wins for voucher 464: *"last SAP entry
wins."***

Before keying a G/L account **or** a budget the sheet has named, look up **the
last entry booked on that card for that account** and compare.

```sql
SELECT TOP 5 i."DocNum", i."DocDate", l."AcctCode", l."LineTotal",
       l."OcrCode3", l."OcrCode2"
FROM   <DB>.PCH1 l JOIN <DB>.OPCH i ON i."DocEntry" = l."DocEntry"
WHERE  i."CardCode" = '<the imprest card>' AND l."AcctCode" = '<account>'
ORDER  BY i."DocDate" DESC;
```

| Sheet vs last SAP entry | What you key |
|---|---|
| **agree** | that value |
| **disagree** | **the LAST SAP ENTRY** |
| disagree, and the **slip's handwritten mark** backs the sheet | **ASK** (ASK list #2) |
| disagree, and the precedent is **absurd** for this voucher | **ASK** (ASK list #3) |
| **no precedent** on that card for that account | fall through to `reference/dimensions-and-heads.md` |

Measured: voucher 464, bank charges ₹708. Sheet said `Factory`; OPCH 50620 dt
2026-08-04, same card `ORGV000465`, AcctCode `5610003`, ₹708.00, carried
**`FACT_COM`**. `FACT_COM` is right.

> **Why:** the sheet is transcribed by a person from a slip, once, at speed. The
> last SAP entry is what the business actually did with that account on that
> card, and it is what next month's comparison will be drawn against.
> Consistency beats a fresh guess.

---

## 🛑 STOP AT THE DRAFT — a cash sheet does NOT go to Bhawani on your own word

**Daman, 2026-09-19 · C-0101 — *"Hold the batch at draft, wait for my
approval."***

This is the **one documented exception** to `CLAUDE.md`'s rule that a bill is not
finished until the approver has it. It applies to **cash vouchers only** — every
other bill still goes draft → attach → `add-draft` the same day.

**The sequence, and it is not negotiable:**

1. Build **every** draft in the batch.
2. Attach every pack (`sapb1 attach`).
3. **Read back every dimension** — SAP stores silently wrong values.
4. **Print the list** — Draft No., vouchers, PO, total, book — and **stop.**
5. **Wait for Daman's word on THIS list.** Not a guess, not silence, not "he said
   do the sheet."
6. Only then `sapb1 add-draft`, one at a time, reading back `WddStatus='W'`.

### What it costs to skip it — measured, 2026-09-19

Ten drafts were submitted in **nine seconds** (13:10:30 → 13:10:39). Problems
surfaced at 13:43. By then:

| Attempted | SAP said |
|---|---|
| `DELETE Drafts(57462)` | **-10** *"Cannot remove drafts as Draft No. N is in approval processes"* |
| `DELETE Drafts(57455)` | **-10** same |
| `PATCH` the `CardCode` | **-2028** party cannot change |
| `PATCH` a shorter line array | line stayed, money duplicated |

**Once a draft is in the queue you cannot delete it, cannot change its party,
cannot remove a line.** 57455 still sits there labelled "DO NOT ADD" waiting to
be rejected. Held at the draft, all of it was one clean delete-and-rebuild.

> **The rule costs one round trip. Skipping it cost a day.**

While `WddStatus` is `-` the draft reaches **nobody**. Once `add-draft` runs it
becomes `W` and the door closes behind it.

> `add-draft` also needs a login an Always-terms template names. Oil 103 lists
> **USER08, USER39 and USER07** (C-0104 — check `WTM1`, the list changes). From a
> login no template names it posts **LIVE** — `jivo-add-and-new`.

---

## ✅ Pre-flight — tick before `--yes`

- [ ] **book** taken from the sheet's `Unit` column, before anything was built
- [ ] every voucher searched for an open GRPO on **every card, all three books**,
      matched on `NumAtCard` — never on a handwritten gate number
- [ ] any GRPO on a **vendor's** card → A/P to that vendor + **one JV per voucher**
- [ ] **ONE ENTRY PER PO**, spanning months where it must; only the ₹10,000 cap
      splits a PO; no voucher split across documents
- [ ] `DocDate` = the **latest voucher date in the entry**
- [ ] `CostingCode2` = **each LINE's own voucher month** — 08-2026 and 09-2026 on
      one document is correct
- [ ] `Series` = `HR_B<MMYY>` for **`DocDate`**'s month, period open; if `Series`
      was patched, **`TaxDate` re-sent and read back**
- [ ] every G/L and budget checked against the **last SAP entry** on that card
- [ ] nothing on the **ASK list** was decided alone
- [ ] any head you CHOSE run through the **zero-history check**
- [ ] `U_Remarks` = `VCH <no> - RS <amount>`, on every line
- [ ] `NumAtCard` = `<MON> YY/<bunch>/<this document's own total>`
- [ ] `VatSum` 0 and `WTLiable` tNO (types 1 and 3); `Comments` ≤ 254 chars
- [ ] attachment row complete, `U_CHK2='OK'`, read back byte-identical
- [ ] **every dimension read back after the write**
- [ ] **Draft No. (`DocEntry`) reported, never `DocNum`** — every open draft in a
      series shares one `DocNum`; it identifies nothing
- [ ] 🛑 **list shown to Daman, and his word received, before any `add-draft`**

---

## 📚 Reference

| File | What is in it |
|---|---|
| `reference/dimensions-and-heads.md` | Dim1–Dim5, the expense-head map, finding an account by name, the zero-history check, imprest cards per book, advance rows |
| `reference/fields-and-paper.md` | `NumAtCard`, `U_Remarks`, tax codes, the four papers per voucher, fuel quantities, period bills, attaching, series numbers |
| `reference/grpo-and-sap-traps.md` | building a GRPO copy, editing a draft after the fact, why `DocNum` is useless, PATCH cannot shrink a line collection |
| `reference/failures-and-examples.md` | the measured failure record, and voucher 437 end to end |

**Child skills:** `cash-voucher-1-grpo` · `cash-voucher-bill` ·
`cash-voucher-manual` · `cash-voucher-jv`
