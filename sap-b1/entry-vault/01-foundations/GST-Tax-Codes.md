---
type: foundation
sap_tables: [OSTC, STC1, OSTA, OTCD, TCD1, TCD2, TCD3, OCHP, OSAC, PCH1, INV1, OITM]
objtype: all
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# GST tax codes — the one field that decides the tax, and the four ways it goes wrong

> You are keying a bill or an invoice. Every line needs a tax code. This note says
> which code exists, what each one actually posts, which ones SAP will fill in for
> you, which ones you must type by hand, and the five names that are spelled wrong
> in JIVO's own master data.

## The short version

1. **`TaxCode` is the field. `VatGroup` is not.** `TaxCode` is filled on **100%** of
   purchase and sales lines in all three books. `VatGroup` is filled on 18% of Oil
   purchase lines — and on **zero** non-item lines, which is exactly where every
   RCM and expense line lives. Never key a report on `VatGroup`.
2. **The code is a container, not a rate.** `OSTC` (the code) → `STC1` (its
   components) → `OSTA` (each component's rate *and* its GL accounts). The rate you
   see posted comes from `OSTA`, never from the code's name.
3. **Same state → `CG+SG@<rate>`. Different state → `IGST@<rate>`.** That is the
   whole decision, and SAP fills it in automatically from a determination table
   keyed on (our state, their state, the item's rate UDF) — **but only for sales of
   an item**. On purchases the code is typed by hand 99.5% of the time.
4. **Reverse charge is always hand-typed, always a `R…`/`GST05R` code, and always
   posts twice** — input RCM debited, output RCM credited, equal and opposite. The
   vendor is paid the base only, and **`OPCH.VatSum` reads 0** on every one of the
   1,840 RCM bills across the three books.
5. **Five names are misspelled in the master.** `Exampt` (not Exempt), `RISGT@18`
   (S and G transposed), `RCGSG@5` / `RCGSG@…` (no trailing `T`), and `GST05R`
   which does not follow the naming scheme at all. A filter on the correct spelling
   returns nothing.

Related: [[Chart-of-Accounts]] (the `2131…`/`2132…`/`2137…` families), [[AP-Invoice]],
[[AR-Invoice]], [[AP-Credit-Memo]], [[GRPO]], [[Numbering-Series]].

---

## 1. Where the tax lives on a line — three fields that look the same

Measured on `PCH1` / `INV1`, all history, all three books.

| Field | Oil purch. | Mart purch. | Bev purch. | Oil sales | What it really is |
|---|---:|---:|---:|---:|---|
| `TaxCode` | **100%** | **100%** | **100%** | **100%** | **The real field.** The `OSTC` code. |
| `VatGroup` | 18% | 54% | 13% | 68% | A legacy mirror. See below. |
| `VatPrcnt` | 62% | 94% | 64% | 89% | The headline rate SAP computed. 0 on exempt/nil, so "62% filled" means 38% of lines are zero-rated. |
| `VatSum` | 60% | 93% | 64% | 71% | The tax on the line. Filled on RCM lines even though the header is 0. |
| `VatGrpSrc` | 100% | 100% | 100% | 100% | **Where the code came from** — `M` typed, `N` inherited, `D` from the determination table. |

### `VatGroup` is empty on every non-item line — that is the real defect

```
Oil   PCH1: item lines 17,286 (VatGroup filled 7,164 = 41%) · non-item lines 22,961 (VatGroup filled 0)
Mart  PCH1: item lines 14,683 (VatGroup filled 11,870 = 81%) · non-item lines  7,171 (VatGroup filled 0)
Bev   PCH1: item lines  2,938 (VatGroup filled  1,426 = 49%) · non-item lines  7,825 (VatGroup filled 0)
```

Zero out of 37,957 non-item lines carry a `VatGroup`. Non-item lines are the
freight, commission, rent, professional-fee and staff-claim lines — i.e. **all of the
reverse charge and all of the exempt spend**. A GST report keyed on `VatGroup`
does not "drop four fifths of the lines"; it drops **the entire service side of the
business**, which is where the compliance risk is.

---

## 2. The master data, decoded

Three tables, in this order. Everything else is derived.

| Table | Rows (Oil / Mart / Bev) | What it holds |
|---|---|---|
| `OSTC` | 23 / 24 / 24 | The **tax code** an operator picks. Carries only a headline `Rate` and the AR/AP validity flags. |
| `STC1` | 36 / 38 / 38 | The code's **component rows** — one per tax head (CGST, SGST, IGST, CESS). |
| `OSTA` | 40 / 41 / 41 | Each **component's** rate, its **input GL** (`PurchTax`), its **output GL** (`SalesTax`) and its **reverse-charge percentage** (`RvsCrgPrc`). |

`OSTC.Rate` is a display field. The number that posts is the sum of the
`OSTA.Rate` of the components. That is why `CG+SG@18` shows 18 but posts 9 + 9.

### 2.1 The complete code list, decoded from the master (not from the name)

Rates and GL accounts read from `OSTA`; components from `STC1`. `Lines` = purchase
lines (`PCH1`) + sales lines (`INV1`), all history, that book.

| Code | Master name | Components (rate → GL) | Oil | Mart | Bev | Reverse charge? |
|---|---|---|---:|---:|---:|---|
| `Exampt` | EXEMPT (Mart: "Exampt") | Exampt 0% → `2131017` in / `2132017` out | 21,013 | 1,365 | 3,472 | no |
| `CG+SG@0` | CGST+SGST@0% | CGST@0 0% `2131006`, SGST@0 0% `2131005` | 4,044 | 5 | 107 | no |
| `IGST@0` | IGST@0% | IGST@0 0% → `2131001` / `2132001` | 1,150 | 26 | 252 | no |
| `IGST@0.1` | IGST@0.1% | IGST@0.1 0.1% → `2131022` / `2132021` | **2** | — | — | no |
| `CG+SG@5` | CGST+SGST@5% | CGST@2.5 `2131008`, SGST@2.5 `2131007` | 32,441 | 37,868 | 750 | no |
| `IGST@5` | IGST@5% | IGST@5 5% → `2131002` / `2132002` | 53,218 | 160,240 | 5,221 | no |
| `CG+SG@12` | CGST+SGST@12% | CGST@6 `2131010`, SGST@6 `2131009` | 2,397 | 3,758 | 1,226 | no |
| `IGST@12` | IGST@12% | IGST@12 → `2131003` / `2132003` | 3,102 | 1,963 | 2,424 | no |
| `CG+SG@18` | CGST+SGST@18% | CGST@9 `2131012`, SGST@9 `2131011` | 9,138 | 3,226 | 1,347 | no |
| `IGST@18` | IGST@18% | IGST@18 → `2131004` / `2132004` | 5,743 | 2,256 | 4,444 | no |
| `CG+SG@28` | CGST+SGST@28% | CGST@14 `2131016`, SGST@14 `2131015` | 8 | **never** | 1 | no |
| `IGST@28` | IGST@28% | IGST@28 → `2131014` / `2132014` | 4 | 2 | **never** | no |
| `CS28+C12` | CGST14+SGST14+CESS12 | CGST@14 + SGST@14 + CESS12 `2131013` | **never** | 30 | 93 | no |
| `IG28+C12` | IGST28%+Cess12% | IGST@28 + CESS12 | **never** | 73 | 468 | no |
| `CG+SG@40` | CGST + SGST @40% | CGST@20 + SGST@20 | **not in Oil** | 54 | 85 | no |
| `IGST@40` | IGST@40% (Bev: "OUTPUT IGST @40%") | IGST@40 40% | **not in Oil** | 60 | 233 | no |
| `GST05R` | SGST @ 2.5 % + CGST @ 2.5 % RCM | RCGS@2.5 `2137102`/`2137502`, RSGS@2.5 `2137101`/`2137501` | 2,900 | 218 | 653 | **yes, 100%** |
| `RCGSG@5` | RCM CGST+SGST@5 | *identical to `GST05R`* | 50 | 907 | 23 | **yes, 100%** |
| `RCGSG@12` | RCM CGST+SGST@12% | RCGST@6 `2137104`/`2137504`, RSGST@6 `2137103`/`2137503` | 0 † | **never** | **never** | **yes, 100%** |
| `RCGSG@18` | RCM CGST+SGST@18% | RCGST@9 `2137106`/`2137506`, RSGST@9 `2137105`/`2137505` | 72 | 28 | 8 | **yes, 100%** |
| `RCGSG@28` | RCM CGST+SGST@28% | RCGST@14 `2137108`/`2137508`, RSGST@14 `2137107`/`2137507` | **never** | 0 † | **never** | yes (Mart SGST leg **not** flagged — see traps) |
| `RIGST@5` | RCM IGST @5% | RIGST@5 → in `2137109` / out `2137509` | 3,000 | 576 | 3,108 | **yes, 100%** |
| `RIGST@12` | RCM IGST @12% | RIGST@12 → `2137110` / `2137510` | 0 † | 1 | **never** | **yes** (Mart/Bev) · **unwired in Oil** |
| `RISGT@18` | RCM IGST @18% | RIGST@18 → `2137111` / `2137511` | 135 | 38 | 8 | **yes, 100%** |
| `RIGST@28` | RCM IGST @28% | RIGST@28 → `2137112` / `2137512` | **never** | **never** | **never** | **yes** (Mart/Bev) · **unwired in Oil** |

† `0` = never on an invoice, but touched exactly once elsewhere — Oil's `RCGSG@12`
and `RIGST@12` on a [[GRPO]] line (`PDN1`), Mart's `RCGSG@28` on a
[[Document-Drafts|draft]] line (`DRF1`). "never" = zero lines across `PCH1`, `INV1`,
`RIN1`, `RPC1`, `PDN1`, `POR1`, `DLN1`, `RDR1` and `DRF1` in that book.

The input/output account names are in [[Chart-of-Accounts]] §5. Note the pattern:
`2131xxx` = input (claimable), `2132xxx` = output (payable), `2137 1xx` / `2137 5xx`
= the RCM pair.

---

## 3. What is in one book and not another

Same three tables, side by side. **The classic error is reading Oil's list and
keying it in Beverages.**

| Difference | Oil | Mart | Bev |
|---|---|---|---|
| Codes in `OSTC` | 23 | 24 | 24 |
| The 40% slab (`CG+SG@40`, `IGST@40`) | **absent** | present, in use | present, in use |
| `CGST@20` / `SGST@20` authorities | **absent** | present | present |
| `IGST@40` authority | present but **no code uses it** | present | present |
| Merchant-export `IGST@0.1` | **only here** | absent | absent |
| `Exampt` usable on a freight / landed-cost row (`OSTC.Freight`) | **Y** | **N** | **N** |
| `RIGST@12` / `RIGST@28` GL accounts | **NULL — unwired** | wired | wired |
| `RSGST@14` reverse-charge % | 100 | **0 — broken** | 100 |
| Registration states in the determination table | DL HR PB HP (4) | DL HR PB RJ KT UP (6) | DL HR PB HP (4) |
| Branches (`OBPL`) | 8 | 20 (base + BSU + TPT) | 6 |

**Oil cannot bill the 40% slab at all.** There is no `CG+SG@40`/`IGST@40` code in
Oil's `OSTC`, and no CGST@20/SGST@20 authority. An Oil item whose revised rate is 40
falls through to nothing. Mart and Beverages are already using it (Bev sold ₹2.66 Cr
on `CG+SG@40` and ₹43.01 L on `IGST@40`).

**The same account number means different taxes in different books.** Already noted
in [[Chart-of-Accounts]] §5 and it bites here too:

| Account | Oil | Mart | Bev |
|---|---|---|---|
| `2131020` | Inter-branch ITC Clearing | INTER BRANCH ITC CLEARING | **INPUT IGST @40%** |
| `2131021` | INPUT IGST @40 % | **TDS ON CONTRACTOR @ 0.25% 194C** | INPUT CGST @20% |
| `2131022` | INPUT IGST @0.1 % | INPUT IGST@40% | INPUT SGST @20% |
| `2132018` | OUTPUT CGST @20% | **OUTPUT IGST @ 40 %** | OUTPUT CGST @20% |
| `2132020` | OUTPUT IGST @40% | **OUTPUT CGST@20%** | OUTPUT IGST @40% |

A three-company GST summary that groups by account number silently adds Mart's
40% output tax to Oil's 20% CGST. Group by the **authority** (`OSTA.Code`), never by
the account number.

---

## 4. The misspellings — read this before you write a filter

Five names in the master do not say what they mean. All five are **measured from
`OSTC`/`OSTA`, in all three books**; they are not typos in this note.

| What is on the screen | What it means | The correct spelling, which finds **nothing** |
|---|---|---|
| `Exampt` | Exempt / nil-rated / no GST on the paper | `Exempt`, `EXEMPT` |
| `RISGT@18` | RCM **IGST** @18% — S and G transposed | `RIGST@18` |
| `RCGSG@5` `RCGSG@12` `RCGSG@18` `RCGSG@28` | RCM **CGST+SGST** — no `T` after the second `G` | `RCGST@…`, `RCGSG@5%` |
| `GST05R` | RCM CGST 2.5% + SGST 2.5% — a fifth naming scheme for the one situation | `RCGSG@5`, `GST5R`, `GST@5R` |
| `CG+SG@…` | CGST + SGST | `CGST+SGST@…` (that is the *name*, not the code) |

And the ones that are only *nearly* wrong:

- `RISGT@18` is the **code**; the authority underneath it is spelled correctly
  (`RIGST@18`). So a join on the code works and a join on the authority works, but
  eyeballing the two side by side looks like a mismatch.
- Beverages' `Exampt` code is named `EXEMPT`; Mart's is named `Exampt`. Same code,
  different label.
- **In Beverages the authorities `CGST@9` and `SGST@9` are *named* "CGST@2.5%" and
  "SGST@2.5%".** The rate stored is 9%, so the arithmetic is right — but any report
  that prints the authority *name* shows 2.5% against an 18% invoice.

Rule: match on `OSTC.Code` / `OSTA.Code`, never on `Name`, and never on a rate
parsed out of a name.

---

## 5. How a code gets onto a line

### 5.1 There is a determination table, and it is the reason sales invoices are easy

`OTCD` / `TCD1` / `TCD2` / `TCD3` — SAP's Tax Code Determination. All three books
have it configured, in the same shape:

| Priority | Keys | Reads | Live from | Live to |
|---:|---|---|---|---|
| 1 | our state × their state × item rate | `OITM.U_Rev_tax_Rate` | 2025-09-22 | — |
| 2 | state × branch × item rate | `OITM.U_Rev_tax_Rate` | 2025-09-22 | — |
| 3 | (exports: `AE` × branch 2) | `OITM.U_Rev_tax_Rate` | 2025-09-22 | — |
| 4 | our state × their state × item rate | `OITM.U_Tax_Rate` | 2024-04-01 | **2025-09-21** |
| 5 | state × branch × item rate | `OITM.U_Tax_Rate` | 2024-04-01 | **2025-09-21** |
| 6 | (exports) | `OITM.U_Tax_Rate` | 2024-10-01 | **2025-09-21** |

**The GST 2.0 cutover is in the data.** Rules 4–6 expired on **2025-09-21**; rules
1–3 start **2025-09-22**. From that date SAP reads a *different field on the item* —
`U_Rev_tax_Rate` ("revised tax rate"), not `U_Tax_Rate`. Anyone who maintains an
item's tax rate in the old field is maintaining a dead field.

The live matrix, measured (all three books agree on the logic):

| Item's revised rate | Same state | Different state | Oil has it? | Mart | Bev |
|---:|---|---|---|---|---|
| 0 | `CG+SG@0` | `IGST@0` | yes | yes | yes |
| 5 | `CG+SG@5` | `IGST@5` | yes | yes | yes |
| 18 | `CG+SG@18` | `IGST@18` | yes | yes | yes |
| 40 | `CG+SG@40` | `IGST@40` | **no rows** | yes | yes |
| 12 · 28 | — | — | **gone** | **gone** | **gone** |

**12% and 28% are no longer in any book's live determination.** Matches the
documents: Oil booked **zero** lines at 12% or 28% in the last 120 days, on either
side. The old (expired) rules did map 40 → `CS28+C12` / `IG28+C12`, the 28+12-cess
pair; the live rules use the real 40% codes.

### 5.2 It fires on sales, and almost never on purchases

`VatGrpSrc` on the line says where the code came from — `D` determination,
`N` inherited (copied from the base document or the item), `M` typed.

| Book | Sales lines `D` | Purchase lines `D` |
|---|---:|---:|
| Oil | 40,873 of 98,170 (42%) | 179 of 40,247 (**0.4%**) |

On a vendor bill you are choosing the code yourself. Nothing defaults it.

### 5.3 What does **not** pick the code

- **The item master's own tax-code fields are empty.** `OITM.TaxCodeAP`,
  `TaxCodeAR`, `VatGroupPu`, `VatGourpSa` — filled on **1 item out of 2,274** in
  Oil and **0 of 1,356** in Mart, **0 of 2,193** in Bev. They look like the answer
  and they are blank.
- **`OTCD` itself carries no default.** Four stub rows (`MI`, `SI`, `SD`, `WT`),
  `DftArCode` and `DftApCode` both NULL in all three books. There is no fallback
  code; if determination misses, the field is yours.
- **HSN and SAC do not pick the code** — next section.

### 5.4 The determination has holes, and they are exactly where you would not look

Live rows that exist but carry **no tax code**:

| Book | Our state → their state | Item rate | Result |
|---|---|---:|---|
| Oil | DL → DL | 18 | no code |
| Oil | HP → HP | 0 | no code |
| Bev | DL → DL | 0 | no code |

And the item side: **`U_Rev_tax_Rate` is empty on 652 of 2,274 Oil items (29%),
463 of 1,356 Mart items (34%) and 1,124 of 2,193 Bev items (51%).** For those items
determination cannot fire at all, on any document. Half the Beverages catalogue is
in that state.

---

## 6. HSN vs SAC — reporting, not tax

Correction **C-0013** already settles the rule: goods carry HSN, services carry SAC,
mutually exclusive; a blank `HsnEntry` is only a defect if `SacEntry` is also empty.
Confirmed here and extended:

| | Table it points at | Rows | Carries a rate? | Carries a tax code? |
|---|---|---:|---|---|
| `HsnEntry` | `OCHP` (chapter / heading / sub-heading) | 519 Oil | **no** | **no** |
| `SacEntry` | `OSAC` (`ServCode`, `ServName`) | 614 Oil | **no** | **no** |

Neither master table has a rate or a tax-code column — measured from
`SYS.TABLE_COLUMNS`. So **HSN/SAC cannot select a tax code, and never has.** It is
printed on the invoice and reported in GSTR-1; it is not an input to the tax.

What HSN *is* wired to: `OITM.ChapterID` (filled on 2,261 of 2,274 Oil items,
1,334/1,356 Mart, 1,914/2,193 Bev) — so the HSN comes off the item automatically on
an item line, and must be typed on a service line.

Measured fill (`PCH1` all-history / last 120 days):

| | Oil | Mart | Bev |
|---|---|---|---|
| `HsnEntry` | 43% / 49% | 67% / 54% | 27% / 16% |
| `SacEntry` | 33% / 33% | 27% / 34% | 41% / 59% |
| Together | 76% | 94% | 68% |

The gap is not "missing HSN"; it is the lines that are neither goods nor a catalogued
service — staff claims and GL-only expense rows.

`OITM.GstTaxCtg` is the item's GST category: `R` regular (2,254 of 2,274 Oil),
`E` exempt (5), `N` nil (3). `PCH1.ItmTaxType` (`GR` / `NN`) is filled on item lines
only — its NULL count is exactly the non-item line count, 22,961 in Oil.

---

## 7. Reverse charge — why you see the tax twice

### The mechanism, from the master

An RCM authority is an ordinary authority with **`OSTA.RvsCrgPrc = 100`** — reverse
charge 100%. That one flag does three things:

1. the tax is **not** added to what the vendor is owed,
2. `PurchTax` (the input RCM account, `2137 1xx`) is **debited** — JIVO's credit,
3. `SalesTax` (the output RCM account, `2137 5xx`) is **credited** — JIVO's liability
   to the government.

So it posts as a matched pair, equal and opposite, on the same journal. Measured on
[[AP-Invoice]] journals (`TransType` 18):

| Pair | Oil, 365 d | Oil, 120 d | Mart, 365 d | Bev, 365 d |
|---|---:|---:|---:|---:|
| `2137109` in / `2137509` out — IGST 5% RCM | 302 / 302 lines, ₹33.89 L each side | 95 / 95 lines, ₹9.53 L | 113 / 113 | 106 / 106 |
| `2137101`+`2137102` in / `2137501`+`2137502` out — CGST+SGST 2.5% RCM | 133 each, ₹2.59 L | 31 each | 103 each | 80 each |
| `2137111` / `2137511` — IGST 18% RCM | — | 16 each | 23 each | — |

A real 4-line journal (Oil, freight bill, `RIGST@5`, base ₹6,420):

| Account | Name | Dr | Cr |
|---|---|---:|---:|
| `2110004` | SUNDRY CREDITOR SERVICE | | 6,420 |
| `5670001` | FREIGHT AND CARTAGE OUTWARD | 6,420 | |
| `2137109` | INPUT IGST @ 5 % RCM | 321 | |
| `2137509` | OUTPUT IGST @ 5 % RCM | | 321 |

The vendor is credited **6,420, not 6,741**. The intra-state version (`GST05R`)
produces six tax lines instead of two — CGST and SGST, in and out.

### The trap that breaks every GST report

**`OPCH.VatSum` (header) is 0 on every single RCM bill.**

| Book | A/P docs carrying an RCM code | of which header `VatSum` = 0 |
|---|---:|---:|
| Oil | 1,135 | **1,135** |
| Mart | 339 | **339** |
| Bev | 366 | **366** |

The tax exists only on the **line** (`PCH1.VatSum`) and in the journal. No header
field carries it — there is no populated reverse-charge column on `OPCH`. Any input-
credit or GST-payable figure built from `OPCH.VatSum` is missing the whole of RCM
(₹33.89 L + ₹5.18 L on the Oil pairs alone in the last year).

### Which codes trigger it, and who they belong to

All six RCM codes are `RvsCrgPrc = 100` in Mart and Bev. In Oil, `RIGST@12` and
`RIGST@28` have **NULL GL accounts and `RvsCrgPrc = 0`** — they are in the code list
but not wired to anything.

**Every RCM line at JIVO is hand-typed.** `VatGrpSrc` = `M` on 6,156 of the 6,157
Oil RCM purchase lines. Determination never returns an RCM code — not even the
priority-1 rule, despite its key field being called `Rev_tax_Rate` (which means
*revised*, not *reverse*).

Who they belong to, Oil, all history:

| Vendor group | `GST05R` | `RIGST@5` | `RISGT@18` | `RCGSG@18` | `RCGSG@5` |
|---|---:|---:|---:|---:|---:|
| TRANSPORTER | 2,834 | 1,889 | — | — | 44 |
| PURCHASE OIL | — | 790 | — | — | — |
| SERVICE | 66 | 317 | 125 | 72 | 6 |
| IT | — | — | 10 | — | — |

**77% of all RCM lines are road freight (GTA).** The transporter does not charge GST;
JIVO self-invoices. Intra-state carriers get `GST05R`, inter-state get `RIGST@5`.
See [[AP-Invoice]] and the transporter block there.

### `GST05R` and `RCGSG@5` are the same code twice

Both decompose to exactly `RCGS@2.5` + `RSGS@2.5` — identical components, identical
accounts, identical rate. There is no functional difference. Which one the office
uses is pure habit, and **the habit differs per book**:

| Book | `GST05R` lines | `RCGSG@5` lines | House habit |
|---|---:|---:|---|
| Oil | 2,900 | 50 | `GST05R` |
| Mart | 218 | **907** | `RCGSG@5` |
| Bev | 653 | 23 | `GST05R` |

Pick either — but pick the one the rest of that book uses, or the intra-state RCM
total splits across two codes and nobody's reconciliation ties.

---

## 8. Purchase side vs sales side

`OSTC.ValidForAR` and `ValidForAP` are **`Y` on every code in every book** — SAP will
not stop you putting a reverse-charge code on a customer invoice. Practice, measured:

| Family | On purchases | On sales |
|---|---|---|
| `CG+SG@…` / `IGST@…` (normal) | yes, all books | yes, all books |
| `Exampt` | yes, heavily | **almost never** (see trap) |
| `IGST@0.1` (merchant export) | never | **Oil only, 2 lines** |
| `CS28+C12` / `IG28+C12` (28+cess) | Mart, Bev | Mart, Bev — never Oil |
| `CG+SG@40` / `IGST@40` | Mart, Bev | Mart, Bev — **not available in Oil** |
| All six `R…` / `GST05R` | yes — this is where RCM lives | **zero lines, all books, all history** |

Live vocabulary, **last 120 days** — this is the shortlist an operator actually needs:

| Book | Purchases | Sales |
|---|---|---|
| Oil | `CG+SG@18` 1,015 · `Exampt` 950 · `CG+SG@0` 787 · `IGST@18` 713 · `RIGST@5` 567 · `GST05R` 430 · `IGST@5` 267 · `IGST@0` 197 · `CG+SG@5` 117 · `RISGT@18` 17 · `RCGSG@18` 10 · `RCGSG@5` 3 | `IGST@5` 3,877 · `CG+SG@5` 1,527 · `IGST@18` 140 · `CG+SG@18` 102 · `CG+SG@0` 2 · `IGST@0.1` 2 |
| Mart | `CG+SG@5` 704 · `IGST@5` 471 · `IGST@18` 356 · `Exampt` 295 · `RIGST@5` 267 · `RCGSG@5` 122 · `CG+SG@18` 84 · `RISGT@18` 18 · `GST05R` 10 · `IGST@0` 4 · `CG+SG@40` 1 · `CG+SG@0` 1 | `IGST@5` 27,827 · `CG+SG@5` 4,935 · `IGST@18` 16 · `CG+SG@18` 11 · `IGST@40` 1 |
| Bev | `RIGST@5` 1,028 · `Exampt` 440 · `IGST@18` 234 · `IGST@5` 87 · `GST05R` 57 · `CG+SG@18` 56 · `IGST@0` 36 · `IGST@40` 7 · `CG+SG@0` 5 · `CG+SG@5` 3 · `RCGSG@5` 1 | `IGST@5` 2,508 · `CG+SG@5` 286 · `IGST@40` 90 · `CG+SG@40` 13 · `IGST@18` 11 · `CG+SG@18` 1 |

Nothing at 12%, 28% or `CS28+C12` in the last 120 days in any book.

### The three codes for "no GST", and the money behind them

Oil purchases, all history, by vendor group — the same situation is being coded three
different ways:

| Code | Biggest by line count | Biggest by value |
|---|---|---|
| `Exampt` (₹160.88 Cr) | STAFF VENDOR 6,295 · SERVICE 2,285 · FUEL 718 | PURCHASE OIL ₹95.46 Cr · FIXED ASSETS ₹46.88 Cr |
| `IGST@0` (₹157.59 Cr) | STAFF VENDOR 703 · PURCHASE OIL 192 | PURCHASE OIL ₹153.81 Cr |
| `CG+SG@0` (₹2.29 Cr) | STAFF VENDOR 1,554 · SERVICE 990 · CIVIL 797 | CIVIL ₹0.72 Cr · SERVICE ₹0.68 Cr |

**8,552 staff expense-claim lines are split across all three.** Exempt, nil-rated
and zero-rated are three different rows of GSTR-3B. Which one is right for a staff
claim with no GST on it is a question for the GST consultant, not for the keyboard —
see Open questions.

---

## 9. The decision table

**Given** the paper in your hand, answer four things: goods or service (it does not
change the code — it changes HSN vs SAC), **our GSTIN state vs the other party's
place of supply**, whether **reverse charge** applies, and **the rate**.

| Rate on the paper | Same state (intra) | Different state (inter) | Same state + **RCM** | Different state + **RCM** |
|---|---|---|---|---|
| No GST / exempt / nil | `Exampt` | `Exampt` | n/a | n/a |
| 0% | `CG+SG@0` | `IGST@0` | none exists | none exists |
| 0.1% (merchant export) | — | `IGST@0.1` — **Oil only** | — | — |
| 5% | `CG+SG@5` | `IGST@5` | **`GST05R`** in Oil/Bev · **`RCGSG@5`** in Mart | `RIGST@5` |
| 12% | `CG+SG@12` | `IGST@12` | `RCGSG@12` — never used anywhere | `RIGST@12` — **unwired in Oil** |
| 18% | `CG+SG@18` | `IGST@18` | `RCGSG@18` | **`RISGT@18`** ← the misspelled one |
| 28% | `CG+SG@28` | `IGST@28` | `RCGSG@28` — Mart's SGST leg is broken | `RIGST@28` — **unwired in Oil** |
| 28% + 12% cess | `CS28+C12` | `IG28+C12` | none exists | none exists |
| 40% | `CG+SG@40` — **Mart/Bev only** | `IGST@40` — **Mart/Bev only** | none exists | none exists |

Reading the table:

- **There is no reverse-charge code at 0% or 40%, and none for cess.** If the paper
  says reverse charge at a rate that has no `R…` code, stop and ask — do not
  substitute the nearest one.
- **"Same state" means our GSTIN's state, not our warehouse.** JIVO bills from four
  states in Oil and Beverages (DL, HR, PB, HP) and six in Mart (DL, HR, PB, RJ, KT,
  UP). The branch (`BPLId`) on the document is what fixes our side — 8 branches in
  Oil, 20 in Mart, 6 in Bev. See [[Numbering-Series]] for the branch↔series link.
- **The 40% row is the one that will bite this year.** Live in Mart and Beverages,
  absent from Oil.

---

## 10. Pre-flight — before you type a tax code

- [ ] **Which book am I in?** The code list is not the same in all three. `Exampt`,
      `CG+SG@…`, `IGST@…` up to 28% are safe everywhere. `CG+SG@40` / `IGST@40` are
      Mart/Bev only. `IGST@0.1` is Oil only.
- [ ] **What does the paper actually say?** Take the rate and the head (CGST+SGST vs
      IGST) off the invoice. Do not derive it from the vendor's address — a vendor in
      another state can still bill CGST+SGST if the place of supply is here.
- [ ] **Does the paper say "reverse charge" / "RCM" / "tax payable by recipient"?**
      If yes, the code starts with `R` (or is `GST05R`) and the vendor's total will
      *exclude* the tax. If the vendor charged the GST, it is **not** RCM, whatever
      the narration says.
- [ ] **Is it a GTA / road-freight bill?** Then it is almost certainly RCM —
      `GST05R` intra-state, `RIGST@5` inter-state.
- [ ] **Is my branch (`BPLId`) right before I pick the code?** The branch fixes our
      state, which is what decides CG+SG vs IGST.
- [ ] **On an item line**, check the item's `U_Rev_tax_Rate` is set. If it is blank
      (29% of Oil items, 51% of Bev items) SAP will not fill the code and will not
      warn you.
- [ ] **On a service line**, expect to type both the code **and** the SAC — nothing
      defaults on a non-item line, and `VatGroup` will stay empty by design.
- [ ] **Copying from a GRPO or a PO?** The code comes across as `VatGrpSrc = N`
      (inherited). Re-read it against the paper: the receipt was keyed by the factory
      gate, not by Accounts.
- [ ] **Never reach for a 12% or 28% code without asking.** Nothing in any book has
      used one in 120 days; the live determination no longer offers them.

---

## 11. After you save — the read-back

Three checks. The first two are the ones that catch a wrong code.

**1. Did the tax land in the right account family?**

```sql
-- swap the schema and the DocEntry
SELECT j."Account", a."AcctName", j."Debit", j."Credit"
FROM   JIVO_OIL_HANADB.OPCH h
JOIN   JIVO_OIL_HANADB.JDT1 j ON j."TransId" = h."TransId"
LEFT JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode" = j."Account"
WHERE  h."DocEntry" = <DocEntry>
ORDER BY j."Line_ID";
```

- input GST must be `2131xxx` **debited**;
- an RCM code must produce **two lines per head** — `2137 1xx` Dr and `2137 5xx` Cr,
  **equal**. One leg alone means the code is wrong.
- `2132xxx` (output) on a purchase, or `2131xxx` (input) on a sale, is always wrong.

**2. Is the header total the base, or the base plus tax?**

```sql
SELECT h."DocTotal", h."VatSum" AS HEADER_VAT,
       SUM(l."LineTotal") AS BASE, SUM(l."VatSum") AS LINE_VAT,
       STRING_AGG(DISTINCT l."TaxCode", ',') AS CODES
FROM   JIVO_OIL_HANADB.OPCH h
JOIN   JIVO_OIL_HANADB.PCH1 l ON l."DocEntry" = h."DocEntry"
WHERE  h."DocEntry" = <DocEntry>
GROUP BY h."DocTotal", h."VatSum";
```

On a normal bill `DocTotal ≈ BASE + LINE_VAT − TDS`. On an **RCM** bill
`HEADER_VAT = 0` and `DocTotal ≈ BASE − TDS` — that is correct, not a bug.

**3. Did the code come from where you think?**

```sql
SELECT "LineNum", "TaxCode", "VatGrpSrc", "VatPrcnt", "VatSum",
       "HsnEntry", "SacEntry"
FROM   JIVO_OIL_HANADB.PCH1 WHERE "DocEntry" = <DocEntry>;
```

`VatGrpSrc = M` on a line you did not type is worth a second look.

---

## Which documents it touches

Every tax-bearing line in every book. `TaxCode` is 100% filled on all of them.

| Note | Table | Where the code comes from |
|---|---|---|
| [[AP-Invoice]] | `PCH1` | **typed** (99.6% `M`/`N`) — the note this matters most for |
| [[AP-Credit-Memo]] | `RPC1` | inherited from the invoice being reversed; re-read it |
| [[GRPO]] | `PDN1` | keyed at the factory gate, then inherited by the A/P bill |
| [[Purchase-Order]] | `POR1` | keyed by purchase; carries forward |
| [[AR-Invoice]] | `INV1` | **determination** (42% `D` in Oil) |
| [[AR-Credit-Memo]] | `RIN1` | inherited from the invoice |
| [[Delivery]] · [[Sales-Order]] · [[AR-Return]] | `DLN1` · `RDR1` · `RDN1` | determination, then inherited |
| [[Document-Drafts]] | `DRF1` | whatever the draft was built from — **the last chance to fix it** |

Foundations it sits next to: [[Chart-of-Accounts]] (the accounts the code posts to),
[[Numbering-Series]] (the branch, which fixes our state),
[[Cost-Centres-and-Dimensions]] (tax lines carry **no** dimensions, by design).
Flow: [[Purchase-to-Pay]].

---

## Traps

1. **`VatGroup` is blank on every non-item line — 37,957 of them.** All the RCM and
   all the exempt service spend is invisible to a `VatGroup` report. Use `TaxCode`.
2. **`OPCH.VatSum` = 0 on all 1,840 RCM bills across the three books.** The tax is
   line-level only. Header-based input-credit reports understate GST.
3. **`Exampt`, `RISGT@18`, `RCGSG@…`, `GST05R` are misspelled or off-scheme.** A
   filter on the correct spelling silently returns zero rows and reads as "we don't
   do that".
4. **Beverages' `CGST@9` / `SGST@9` authorities are *named* "CGST@2.5%" /
   "SGST@2.5%".** Rates are right, labels are wrong. Never print the name.
5. **Oil's `RIGST@12` and `RIGST@28` have no GL accounts and `RvsCrgPrc = 0`.**
   They appear in the picklist. Mart and Beverages have them wired.
6. **Mart's `RSGST@14` has `RvsCrgPrc = 0` while `RCGST@14` has 100.** `RCGSG@28`
   in Mart would reverse-charge the CGST leg and charge the SGST leg to the vendor.
   Never used yet — do not be the first without checking with Accounts.
7. **Oil has no 40% code at all.** Mart and Beverages are already billing it. An
   Oil item on the 40% slab has nowhere to go.
8. **The same account number is a different tax in a different book**
   (`2131020`, `2131021`, `2131022`, `2132018`, `2132020`). Group by authority code,
   never by account number, in any cross-company GST report.
9. **All 11,078 Oil `Exampt` *sales* lines are dated 2024-09-30 and read
   "OPENING BALANCE ACCOUNT"** — ₹74.74 Cr of data migration, not sales. Mart's
   6 biggest `Exampt` sales lines are the same thing on 2024-12-31 (₹6.57 Cr).
   Any "exempt turnover" figure that includes them is wrong.
10. **`GST05R` and `RCGSG@5` are the identical code twice**, and the three books
    prefer different ones. Intra-state RCM totals split unless you sum both.
11. **`OSTC.ValidForAR` = `Y` on every reverse-charge code.** SAP will let you put
    `RIGST@5` on a customer invoice. It has never happened; nothing stops it.
12. **Determination reads `U_Rev_tax_Rate` from 2025-09-22, not `U_Tax_Rate`.**
    Maintaining the old field changes nothing on a document dated today.
13. **Three determination cells return no code** (Oil DL→DL @18, Oil HP→HP @0,
    Bev DL→DL @0). They fail quietly — the field is just left for you.
14. **`Exampt` cannot be used on a freight / landed-cost row in Mart or Beverages**
    (`OSTC.Freight = N`); in Oil it can. Same code, different availability.
15. **HSN/SAC never picks the code.** `OCHP` and `OSAC` have no rate and no
    tax-code column. Fixing an HSN does not fix a tax.

---

## Open questions

1. **Which of `Exampt` / `IGST@0` / `CG+SG@0` is correct for a staff expense claim
   with no GST on it?** 8,552 Oil lines are split across all three, and exempt vs
   nil-rated vs zero-rated are different GSTR-3B rows. Needs the GST consultant, not
   a query.
2. **Oil sold ₹15.89 Cr of "CANOLA COLD PRESS LOOSE OIL OLD" on `IGST@0`** (9 lines,
   Jan–Jun 2025). Is loose oil genuinely nil-rated inter-state, or should those have
   been `IGST@5`? Not something this note can settle.
3. **Would SAP actually refuse `RIGST@12` / `RIGST@28` in Oil**, given the authority
   has NULL accounts, or would it post to nothing? Cannot be tested read-only.
   `RIGST@12` has been touched exactly once in Oil, on a GRPO line; `RIGST@28`
   never.
4. **Why does Oil have an `IGST@40` *authority* (`2131021`/`2132020`) but no `IGST@40`
   code?** Half-finished GST 2.0 setup is the obvious guess; unverified.
5. **`U_Rev_tax_Rate` is blank on 51% of Beverages items and 29% of Oil items.** Is
   that a maintenance backlog, or are those items genuinely non-sellable (raw
   material, packaging)? Would need a join to sales history to say.
6. **`VatGrpSrc` letter meanings are inferred**, not documented here: `D` matches the
   determination output, `M` matches hand-typed RCM (6,156 of 6,157 lines), `N`
   matches copied/inherited lines. Confident on `D` and `M`; `N` is the weakest.
7. **Priority-2 determination in Oil covers branches 1–5 only** — nothing for
   `DELHI ISD` (6), `DELHI INFO` (7), `HARYANA INFO` (8). Priority 1 is state-based
   so it should still fire; not proven on a live document.
8. **Nobody has used `CS28+C12` / `IG28+C12` in 120 days.** With the 40% codes live,
   are the 28+cess codes retired or still needed for old-rate credit notes?

---

## Queries used

```sql
-- 1. Which tax tables exist and carry rows
SELECT TABLE_NAME, RECORD_COUNT FROM SYS.M_TABLES
WHERE SCHEMA_NAME='JIVO_OIL_HANADB'
  AND (TABLE_NAME LIKE '%TAX%' OR TABLE_NAME LIKE '%VAT%' OR TABLE_NAME LIKE 'OST%');
-- OSTC 23 · STC1 36 · OSTT 18 · OSTA 40 · OTAX 55,447 · TAX1 217,647; OSTB/OSTE/OSTG/OSTQ/OSTS/OSTX all 0

-- 2. The code master, per book
SELECT "Code","Name","Rate","ValidForAR","ValidForAP","Lock","IsSystem","Freight"
FROM   JIVO_OIL_HANADB.OSTC ORDER BY "Code";

-- 3. Components + the authority behind each (rate, accounts, reverse-charge %)
SELECT s."STCCode", s."Line_ID", s."STACode", s."EfctivRate",
       a."Name", a."Rate", a."PurchTax", a."SalesTax", a."RvsCrgPrc"
FROM   JIVO_OIL_HANADB.STC1 s
LEFT JOIN JIVO_OIL_HANADB.OSTA a ON a."Code"=s."STACode" AND a."Type"=s."STAType"
ORDER BY s."STCCode", s."Line_ID";

-- 4. Tax-code determination: the rules, what they read, and when they are live
SELECT r."AbsId", r."Priority", r."KeyFld_1", r."KeyFld_2", r."UDFAlias_3",
       COUNT(v."AbsId") AS ROWS_, MIN(t."EfctFrom"), MAX(t."EfctTo")
FROM   JIVO_OIL_HANADB.TCD1 r
LEFT JOIN JIVO_OIL_HANADB.TCD2 v ON v."Tcd1Id"=r."AbsId"
LEFT JOIN JIVO_OIL_HANADB.TCD3 t ON t."Tcd2Id"=v."AbsId"
GROUP BY r."AbsId", r."Priority", r."KeyFld_1", r."KeyFld_2", r."UDFAlias_3"
ORDER BY r."Priority";

-- 5. The live matrix: (our state = their state?) x item rate -> code
SELECT CASE WHEN v."KeyFld_1_V"=v."KeyFld_2_V" THEN 'SAME state' ELSE 'OTHER state' END,
       v."KeyFld_3_V", t."TaxCode", COUNT(*)
FROM   JIVO_OIL_HANADB.TCD1 r
JOIN   JIVO_OIL_HANADB.TCD2 v ON v."Tcd1Id"=r."AbsId"
LEFT JOIN JIVO_OIL_HANADB.TCD3 t ON t."Tcd2Id"=v."AbsId"
WHERE  r."Priority"=1
GROUP BY 1,2,3 ORDER BY 2,1;

-- 6. Code usage, purchases and sales, all history + last 120 days (repeat for INV1/OINV)
SELECT l."TaxCode", COUNT(*) AS LINES_ALL,
       SUM(CASE WHEN h."DocDate" >= ADD_DAYS(CURRENT_DATE,-120) THEN 1 ELSE 0 END) AS LINES_120D,
       COUNT(DISTINCT l."DocEntry") AS DOCS,
       ROUND(SUM(l."LineTotal")) AS BASE_INR, ROUND(SUM(l."VatSum")) AS TAX_INR
FROM   JIVO_OIL_HANADB.PCH1 l JOIN JIVO_OIL_HANADB.OPCH h ON h."DocEntry"=l."DocEntry"
GROUP BY l."TaxCode" ORDER BY LINES_ALL DESC;

-- 7. VatGroup is empty on every non-item line
SELECT CASE WHEN "ItemCode" IS NULL OR "ItemCode"='' THEN 'no item' ELSE 'item' END,
       CASE WHEN "VatGroup" IS NULL OR "VatGroup"='' THEN 'VatGroup EMPTY' ELSE 'filled' END,
       COUNT(*)
FROM   JIVO_OIL_HANADB.PCH1 GROUP BY 1,2;

-- 8. Where the code came from, per code
SELECT "TaxCode","VatGrpSrc",COUNT(*),
       SUM(CASE WHEN "VatGroup" IS NULL OR "VatGroup"='' THEN 0 ELSE 1 END),
       SUM(CASE WHEN "ItemCode" IS NULL OR "ItemCode"='' THEN 0 ELSE 1 END)
FROM   JIVO_OIL_HANADB.PCH1 GROUP BY "TaxCode","VatGrpSrc" ORDER BY 3 DESC;

-- 9. Every RCM bill has a zero header VatSum
SELECT COUNT(*) AS RCM_DOCS, SUM(CASE WHEN "VatSum"=0 THEN 1 ELSE 0 END) AS HEADER_ZERO
FROM   JIVO_OIL_HANADB.OPCH
WHERE  "DocEntry" IN (SELECT DISTINCT "DocEntry" FROM JIVO_OIL_HANADB.PCH1
                      WHERE "TaxCode" LIKE 'R%' OR "TaxCode"='GST05R');

-- 10. The RCM pair on one journal
SELECT j."Line_ID", j."Account", a."AcctName", j."Debit", j."Credit"
FROM   JIVO_OIL_HANADB.JDT1 j LEFT JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE  j."TransId"=225549 ORDER BY j."Line_ID";

-- 11. Codes in the master that no document has ever used
SELECT c."Code", c."Rate", CASE WHEN u."TaxCode" IS NULL THEN 'NEVER USED' ELSE 'used' END
FROM   JIVO_OIL_HANADB.OSTC c
LEFT JOIN (SELECT DISTINCT "TaxCode" FROM JIVO_OIL_HANADB.PCH1
           UNION SELECT DISTINCT "TaxCode" FROM JIVO_OIL_HANADB.INV1
           UNION SELECT DISTINCT "TaxCode" FROM JIVO_OIL_HANADB.RIN1
           UNION SELECT DISTINCT "TaxCode" FROM JIVO_OIL_HANADB.RPC1
           UNION SELECT DISTINCT "TaxCode" FROM JIVO_OIL_HANADB.PDN1
           UNION SELECT DISTINCT "TaxCode" FROM JIVO_OIL_HANADB.POR1
           UNION SELECT DISTINCT "TaxCode" FROM JIVO_OIL_HANADB.DLN1
           UNION SELECT DISTINCT "TaxCode" FROM JIVO_OIL_HANADB.RDR1
           UNION SELECT DISTINCT "TaxCode" FROM JIVO_OIL_HANADB.DRF1) u
       ON u."TaxCode"=c."Code"
ORDER BY 3 DESC, 1;

-- 12. The item master defaults nothing
SELECT COUNT(*) AS ITEMS,
       SUM(CASE WHEN "TaxCodeAP"<>'' THEN 1 ELSE 0 END) AS TAXCODEAP,
       SUM(CASE WHEN "TaxCodeAR"<>'' THEN 1 ELSE 0 END) AS TAXCODEAR,
       SUM(CASE WHEN "VatGroupPu"<>'' THEN 1 ELSE 0 END) AS VATGRPPU,
       SUM(CASE WHEN "VatGourpSa"<>'' THEN 1 ELSE 0 END) AS VATGRPSA,
       SUM(CASE WHEN "ChapterID" > 0 THEN 1 ELSE 0 END) AS CHAPTERID,
       SUM(CASE WHEN "U_Rev_tax_Rate" IS NOT NULL THEN 1 ELSE 0 END) AS REV_RATE
FROM   JIVO_OIL_HANADB.OITM;

-- 13. HSN and SAC masters carry no rate and no tax code
SELECT COLUMN_NAME FROM SYS.TABLE_COLUMNS
WHERE SCHEMA_NAME='JIVO_OIL_HANADB' AND TABLE_NAME IN ('OCHP','OSAC');
-- OCHP: AbsEntry, Chapter, Heading, SubHeading, Dscription, ChapterID
-- OSAC: AbsEntry, ServName, ServCode

-- 14. The exempt "sales" that are really the migration
SELECT h."DocDate", COUNT(*) AS LINES_, MIN(l."Dscription")
FROM   JIVO_OIL_HANADB.INV1 l JOIN JIVO_OIL_HANADB.OINV h ON h."DocEntry"=l."DocEntry"
WHERE  l."TaxCode"='Exampt' GROUP BY h."DocDate";
-- 2024-09-30 · 11,078 lines · "OPENING BALANCE ACCOUNT"

-- 15. Who the RCM codes belong to
SELECT g."GroupName", l."TaxCode", COUNT(*)
FROM   JIVO_OIL_HANADB.PCH1 l
JOIN   JIVO_OIL_HANADB.OPCH h ON h."DocEntry"=l."DocEntry"
JOIN   JIVO_OIL_HANADB.OCRD c ON c."CardCode"=h."CardCode"
LEFT JOIN JIVO_OIL_HANADB.OCRG g ON g."GroupCode"=c."GroupCode"
WHERE  l."TaxCode" LIKE 'R%' OR l."TaxCode"='GST05R'
GROUP BY g."GroupName", l."TaxCode" ORDER BY 3 DESC;
```

Run any of these with:

```bash
./hana-sql/hana-sql -env connections/hana-office-bridge.env "<one SELECT>"
```

Swap `JIVO_OIL_HANADB` for `JIVO_MART_HANADB` or `JIVO_BEVERAGES_HANADB`. Every
figure in this note was pulled on **2026-08-24**; the fill rates and the "last 120
days" columns move, the master-data structure does not.
