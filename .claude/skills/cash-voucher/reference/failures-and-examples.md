# What went wrong, and one voucher end to end

> The measured failure record. Read this before deciding a rule here is optional.

> Reference for the `cash-voucher` skill family. The rules live in
> `cash-voucher/SKILL.md`; this file holds the detail behind them.

---

## Why this rule exists — measured, 2026-09-19

Ten drafts were submitted in **nine seconds** (13:10:30 → 13:10:39), before
anyone had seen them. Problems surfaced at 13:43. By then:

| Attempted | SAP said |
|---|---|
| `DELETE Drafts(57462)` | **-10** · *"Cannot remove drafts as Draft No. N is in approval processes"* |
| `DELETE Drafts(57455)` | **-10** · same |
| `PATCH` the `CardCode` | **-2028** · party cannot change |
| `PATCH` a shorter line array | line stayed, money duplicated (see below) |

**Once a draft is in the queue you cannot delete it, cannot change its party,
cannot remove a line.** Every fix after that point becomes a workaround, and
57455 is still sitting there labelled "DO NOT ADD" waiting to be rejected.

Held at the draft, all of it would have been one clean delete-and-rebuild. The
rule costs one round trip. Skipping it cost a day.

> `add-draft` also needs a login an Always-terms template names. Oil 103 now
> lists **USER08, USER39 and USER07** (C-0104 — verify in `WTM1`, the list
> changes). From a login no template names it posts **LIVE** — `jivo-add-and-new`.

---

---

## What I got wrong, so nobody repeats it

Every one of these was a correction Daman made to draft 56767 **after** I had
built it and reported it as finished.

| # | Field | I had | Correct | Root cause |
|---|---|---|---|---|
| 1 | Document shape | one draft per book, grouped to fill the ₹10k cap | one draft per voucher ⚠️ **SUPERSEDED 2026-09-19 → ONE ENTRY PER PO (C-0097)** | invented a grouping rule from posted history instead of asking |
| 2 | G/L | hand-picked from the row's wording | **from the GRPO's item** | never looked for a GRPO; assumed the class was service-only |
| 3 | Dim3 budget | inherited the GRPO's `Factory` | **`FACT_COM`** from the slip's "Common" | treated a GRPO copy as authoritative for *everything* (C-0027 was in context and ignored) |
| 4 | Dim2 costing | inherited the GRPO's `08-2026` | **`09-2026`** from the slip's date | same |
| 5 | Vendor ref bunch | `49097` (both tables added) | **`39940`** (that table's own Total) | trusted an inference from history over the sheet in hand |
| 6 | Posting date | 31-08-2026 | **01-09-2026** (slip's date) | mapped SAP's screen label "Document Date" to `DocDate` instead of `TaxDate` |

**The pattern in all six: a derived rule beat the paper in front of me.** The
paper wins. When a GRPO and a slip disagree, the slip wins for Dim2/Dim3 and the
GRPO wins for the G/L — and when neither is clear, ask instead of inferring.

---

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

---
