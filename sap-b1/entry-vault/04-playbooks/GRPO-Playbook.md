---
type: playbook
sap_tables: [OPDN, PDN1, PDN12, ODRF, DRF1, NNM1, ATC1]
objtype: 20
companies: [OIL, MART, BEV]
mined: 2026-08-27
confidence: high
---

# GRPO — the keying sheet

> The receipt, not the bill. Paper in hand to draft read back.
> **Read §0 before anything else** — a GRPO comes in two shapes that are opposite jobs,
> and everything downstream depends on which one you are holding.
>
> Sits above [[AP-Invoice-Playbook]] and [[Transport-Bill-Playbook]]: get the GRPO right
> and both of those become copy jobs. Document note: [[GRPO]].

## 0 · Which shape? The fork that decides everything

Oil, 365 days, `CANCELED='N'`, by line:

| | `DocType` `I` — **item** | `DocType` `S` — **service** |
|---|---|---|
| Lines | 8,305 | 3,319 |
| **Copied from a PO** (`BaseType` 22) | **7,594 — 91.4 %** | **10 — 0.3 %** |
| **Keyed from scratch** (`BaseType` -1) | 711 — 8.6 % | **3,309 — 99.7 %** |
| The job | **find the PO and copy it.** Seconds | **key every field.** This is where the work is |
| Posts a journal? | **Yes** — Dr stock/expense, Cr `2140001` GRNI | **No. Never.** See §8 |
| What arrives | physical goods into a warehouse | a service already performed — freight, transport |

> **[[GRPO]]'s "62.2 % from a PO, 32.5 % keyed" blends the two shapes and hides this.**
> Blended, it reads as "a third of receipts are hand-keyed". Split, the truth is:
> item receipts are almost always PO copies, and service receipts almost never are.
> *Measured 2026-08-27.*

**So:** goods on the paper → §3. **A bilty / LR / GCN → §4.** Nothing else reaches this
document — a transporter's *bill* is not a GRPO input at all, it is the A/P invoice that
copies these GRPOs later ([[Transport-Bill-Playbook]]).

## 1 · Is it already in SAP?

- [ ] Search `NumAtCard` for this vendor. **Item:** the vendor's challan / DC number.
      **Service:** the **bilty / LR number** — not the transporter's bill number.
- [ ] Check posted `OPDN` **and** `ODRF` (drafts).

**A GRPO you cannot find probably does not exist.** Unlike the A/P invoice, the GRPO is
usually *not* drafted first — **0.39 drafts per posted document, against 1.02** for an
A/P invoice. So absence here is real absence, not something sitting in Document Drafts.
That is the opposite of the A/P rule, where Neetu pre-keys drafts. → [[Document-Drafts]]

## 2 · The header — both shapes

| Field | Value | Measured |
|---|---|---|
| `DocType` | **`dDocument_Items`** or **`dDocument_Service`** | **Omit it and a copy-forward fails `[SAP -5002] Base document type and target document type do not match`** |
| `Series` | **one series per month, full stop** | Oil Aug-26 = **`2477` `GRPO0826`**. Jul `2476`, Jun `2475`, May `2474` |
| `CardCode` | look it up **in that book** | the same transporter has a different code per book — §7 of [[Transport-Bill-Playbook]] |
| `NumAtCard` | item: vendor challan · **service: the bilty number** | 603 of 604 Oil transporter GRPOs |
| `DocDate` | **the gate-in / bilty date** | where `U_BiltyDate` is recorded, `DocDate` = it on **63 of 63** |
| `TaxDate` | same as `DocDate` | **132 of 135** |
| `BPL_IDAssignedToInvoice` | Oil `2` FACTORY (90 %) · `1` DELHI · `3` PUNJAB | read it off the paper, do not default it in Mart |
| `ControlAccount` | `2110004` SUNDRY CREDITOR SERVICE | automatic on service |
| `Comments` | service: **`BILTY NO <n>`** | 197 of 198 |
| `DocumentSubType` | **leave it — `bod_None`** | the GRPO has no GST/bill-of-supply flavour |

**The series is the one place a GRPO is simpler than an A/P invoice.** The A/P side splits
by branch *and* GST flavour (`HR_G0826` vs `HR_B0826`). GRPO does not: one monthly series,
all branches, both shapes. Wrong series still returns `-10`. → [[Numbering-Series]]

## 3 · Item GRPO — copy the PO, then check five things

91.4 % of item lines are PO copies. Copy, then verify only what the PO cannot know:

| Field | Oil fill (365 d) | Note |
|---|---:|---|
| `WhsCode` | 100 % | `BH-PM` 2,932 · `BH-FA` 2,514 · `DL-FA` 1,554 · `BH-GJ` 449 · `PB-ST` 261 |
| `HsnEntry` | **100 %** | goods carry HSN. A blank is a defect here — unlike a service line **(C-0013)** |
| Dim1 `OcrCode` | **100 %** | the variety — `CANOLA`, `OLIVE`, `MUSTARD`, `SOYABEAN`, `BST` … |
| Dim2 `OcrCode2` | **52.3 %** | half are blank. **Set it** — the A/P invoice inherits only Dim1 **(C-0035)** |
| Dim3 `OcrCode3` | 49.8 % | `Factory` 2,341 · `BackOff` 1,315 · `FACT_COM` 214. Handwritten *Common* → `FACT_COM` **(C-0027)** |
| Dim5 `OcrCode5` | 35.2 % | |
| `WtLiable` | **2.3 %** (194 of 8,305) | goods are not TDS-bearing. Contrast service, §7 |
| Quantity | **pieces, not cartons** | **(C-0001)** |

Tax codes actually used on item lines: `CG+SG@0` 2,609 · `CG+SG@18` 2,447 · `IGST@18` 1,088
· `IGST@5` 1,078 · `IGST@0` 625 · `CG+SG@5` 403. **The single commonest code is 0 %** —
do not "correct" a zero-rated receipt to 18 % because it looks wrong. → [[GST-Tax-Codes]]

**The GRPO's tax code is trustworthy and the A/P invoice should inherit it** — same on
10,617 of 10,626 copied lines. The 9 that differ are place-of-supply corrections (IGST →
CG+SG), never a rate invention. Check it on inter-state receipts specifically. → [[GRPO]]

## 4 · Service GRPO — key it. Every field, in order

> ### The input is the bilty. Only the bilty. **(C-0038)**
>
> The transporter hands over the bilty (LR / GCN) and **that paper is the whole input**.
> One bilty → one GRPO. Every value below is read off it.
>
> **Do not go to the AR invoice for any of this.** JIVO's sale invoice is a different
> thing on a different clock: the photo of the copy the consignee signed, which comes
> back later and proves the goods were physically received. It is evidence of delivery,
> not a source for this document — and it cannot even tell you which bilty carried it:
> `OINV.U_BilltyNumber` equals the GRPO's `NumAtCard` on **only 1,434 of 3,273 Oil
> freight lines (43.8 %)**. GRPO `25886` is bilty `NCR-3627`; its invoice `626070769`
> says bilty `1126`. *Measured 2026-08-27; corrected by Daman the same day.*
>
> The invoice number lands on the GRPO because **the bilty prints it**, not because
> anyone looked it up.

**One line per sale invoice on the bilty**, not one per bilty. A bilty carrying four of
JIVO's invoices is four lines, freight apportioned; the bilty number repeats on each.
Distribution of lines per PICK & SHIP GRPO: 1 × 89 · 2 × 26 · 3 × 17 · 4 × 2 · 5 × 1.

Every value below is **205 of 205** on Oil PICK & SHIP service-GRPO lines unless noted:

| Field | Value | What it is |
|---|---|---|
| `AccountCode` | **`5670001`** | FREIGHT AND CARTAGE OUTWARD-INDIRECT |
| `ItemDescription` | `EDIBLE OIL` | free text, house wording |
| `LineTotal` | the bilty's **LR Total**, pre-tax | freight + docket charge, as one figure |
| `TaxCode` | `IGST@18` (198) · `RIGST@5` (4) · `IGST@5` (3) | §6 |
| `LocationCode` | **`2`** | **(C-0025)** |
| `SACEntry` | **`2`** = `9967` Freight | Bev uses `3`; **Mart wrongly uses `-426` freight *insurance*** |
| `SalesPersonCode` | `115` | |
| `U_BilltyNumber` | the bilty / LR number | |
| `U_BiltyDate` | the bilty date | filled on 63 of 205 — but where filled it **sets `DocDate`** |
| **`U_ARNO`** | **JIVO's own sale invoice number** | off the bilty's "Invoice No." / "Party Inv. No." |
| **`U_CardCode`** | **the consignee's `CUSTA…` code** | the customer the goods went to |
| `U_Sub_Account` | `SALES` | |
| `U_Remarks` | `BILTY NO <n>` | |
| `U_UNE_CALI` / `U_UNE_CUNT` | `Y` / `Y` | |
| **`U_UNE_LTS`** | **total litres on that sale invoice** | see below |
| `U_Recvd_Qty` | **0 — never used on transport** | C-0025's "put the qty here" is the *fuel*-bill rule |
| `Quantity` | 0 | service lines have none |

### `U_UNE_LTS` — litres, and the one thing this sheet cannot yet source

`U_UNE_LTS` is **litres of oil on that invoice's consignment**, and it is **not** the
bilty's "Actual Kgs" — that is gross weight including packaging (6,720 L shipped as
6,500 kg).

What the figure *is* arithmetically is settled: on GRPO `25886` it is `1,277` =
400 × 1 L + 800 × 1 L + 77 × 1 L, the pack maths of the consignment. Reproducing that
sum from JIVO's own invoice lines lands **2,384 of 3,267 Oil freight lines (73 %)**
exactly or within 2 % (pack size parsed from the item name — `OITM.SVolume` is 0 on
every finished good; kg packs convert at 0.91 kg/L, and 95 lines were keyed 1 : 1
without the density step). *Measured 2026-08-27.*

**Where the operator reads it off the paper is an open question — ask before keying.**
Until it is answered, take litres from the bilty or from the operator, and never
silently compute it out of SAP. → [[GRPO-Playbook#Open questions]]

**Reconcile against the bilty, not against SAP.** The bilty's printed "VALUE Rs." is
the consignment value the line is costing; on `NCR-4137` that was ₹17,47,066. Check
the paper against itself — invoice numbers, packages, value, freight — and let the
read-back in §10 confirm what SAP stored.

## 5 · The five dimensions

**A service GRPO is the origin of all five** — the A/P invoice inherits every one of them
(verified on draft 39829). **C-0035 ("lines inherit only Dim1") is the item-GRPO rule and
does not apply to freight.** So a dimension wrong here is wrong on the bill too.

| | Value | Measured |
|---|---|---|
| Dim1 `CostingCode` | **the variety shipped** — `OLIVE`, `CANOLA`, `MUSTARD` … | off the bilty's goods description. Where a consignment is mixed it is the **dominant** variety, not a split — that reproduces the keyed value on 2,759 of 3,267 lines (84.5 %) |
| Dim2 `CostingCode2` | **the DISPATCH month, `MM-YYYY`** — the month the goods went out, off the bilty date | **193 of 205 filled.** It is the dispatch month, not the GRPO's own month, and the two differ whenever a bilty is keyed after a month end |
| Dim3 `CostingCode3` | Oil `Del Bkhp` · Mart `SUPPLY-C` · Bev `Del Bkhp` | 205/205. **Never `FACT_COM`** — that is the factory-bill code |
| Dim4 `CostingCode4` | Oil: **empty**. Mart: always set | |
| Dim5 `CostingCode5` | **the destination state** | 205/205 |

### Dim5 — JIVO's state codes are not the obvious ones

Bihar is **`BH`**, not `BR`. Odisha is **`OR`**. Uttarakhand is **`UK`**. Kerala is `KE`,
Karnataka `KN`, Telangana `TE`, Chandigarh `CD`, Chhattisgarh `CH`.
**Look it up, never spell it out:**

```sql
SELECT "OcrCode","OcrName" FROM "JIVO_OIL_HANADB"."OOCR"
WHERE "DimCode"=5 AND "Active"='Y' ORDER BY "OcrCode";
```

→ [[Cost-Centres-and-Dimensions]], **C-0033**

## 6 · Tax on a freight GRPO — read the paper, not the vendor type

| The bill says | Code | Header `VatSum` |
|---|---|---|
| GST charged at 18 % (forward charge) | `IGST@18` / `CGST@9`+`SGST@9` | **equals** the line GST |
| "GST payable by recipient" / no GST — GTA, inter-state | `RIGST@5` | **0** |
| same, intra-state | `RCGS@2.5` + `RSGS@2.5` | **0** |

**The same transporter does both.** PICK & SHIP has forward-charge and RCM GRPOs in Oil.
Never infer the shape from the vendor — read this bill. → [[GST-Tax-Codes]]

## 7 · TDS — there is none on a GRPO. Ever.

**`WTSum` is 0 on all 3,923 Oil service GRPOs.** Not "usually", not "below threshold" —
a GRPO has never deducted TDS at JIVO in any of the three books.

The only TDS-shaped field is the line flag `WtLiable`, which **deducts nothing here**:

- Service lines: `Y` on 186 of 205 — and this is what makes the **A/P invoice** inherit
  the liability. Set it.
- Item lines: `Y` on 194 of 8,305 (2.3 %). Goods are not TDS-bearing.

The actual deduction happens on the A/P invoice, where it must be sent explicitly —
a draft built from GRPO lines comes out `WTSum = 0` **(C-0018)**. → [[TDS-Withholding]],
§5 of [[Transport-Bill-Playbook]]

## 8 · What it does to the books — and the correction

| | Journal? |
|---|---|
| Item GRPO | **Yes** — 4,762 of 6,858 carry a `TransId`. Dr stock/expense, Cr `2140001` GRNI |
| **Service GRPO** | **No — 0 of 3,923.** `TransId` is NULL on every one |

**A service GRPO has no accounting effect whatsoever.** No expense, no GRNI, no accrual,
no vendor liability, at any point in its life. It is a priced, fully-coded claim record
that sits open until the bill copies it. Nothing posts until the A/P invoice.

> **[[GRPO]] gets this wrong** — its "The journal it posts" section gives Dr expense /
> Cr `2140001` as *the* GRPO entry. That is the **item** receipt only. The ₹354.76 Cr
> credited to `2140001` under TransType 20 over 365 days is item receipts *(derived — by
> elimination, since no service GRPO has a journal at all)*.
>
> Why it matters: it invites a confident wrong answer about GRNI. The "open GRPOs waiting
> for a bill" pile (Oil 138 · ₹21.49 L) is a **commitment** figure, not a ledger balance —
> for freight there is nothing in the ledger to be a balance of.

## 9 · The attachment — the bilty, not the bill

**135 of 135** PICK & SHIP GRPOs carry one, and the filenames are the **bilty numbers**:
`3864.pdf`, `3627.pdf`, `3221.pdf`, `3159.pdf`.

So on a two-part scan the split is:

| Page | Document | Goes on |
|---|---|---|
| the transporter's tax invoice (`NCR-368`) | the **bill** | the **A/P invoice** |
| the bilty / LR (`NCR-4137`) | the **receipt** | **this GRPO**, saved as `4137.pdf` |

Do not put the vendor's bill on the GRPO. → [[Attachments]], **C-0026**

## 10 · Read it back

```bash
sapb1 query Drafts --filter "DocEntry eq <n>" --json
```

- [ ] `DocTotal` = base + tax, reconciled to the paper to the rupee
- [ ] every line's Dim1 / Dim2 / Dim3 / Dim5, `LocationCode`, `SACEntry`
- [ ] `U_ARNO` reads back exactly as the invoice number **printed on the bilty**
- [ ] `U_UNE_LTS` = the litres you were given, unchanged
- [ ] `NumAtCard` is the **bilty**, not the bill

## 11 · Then a human presses Add

Oil, `CANCELED='N'`, joined to the approval request log `OWDD`:

| Shape | `WddStatus` | Documents | Real approval requests |
|---|---|---:|---:|
| Item | `P` | 4,048 | **4,815** |
| Item | `A` | 125 | 139 |
| Item | `-` | 2,687 | **0** |
| **Service** | `-` | **3,923** | **0** |

**Item GRPOs go through approval 61 % of the time. A service GRPO never has — not one of
3,923, in the whole history of the book.**

### But a GRPO from *this CLI* bypasses approval either way — and that is a gap, not a rule

38 templates cover TransType 20 in Oil. **20 are Active — and all 20 are query-conditioned
(`Conds='Y'`), which SAP skips for Service Layer documents.** The only two *Always*
templates for GRPO (`29` USER26 DELIVERY GR, `88` BH-GR) are **both switched off**.

Across the whole Oil book only two document types have an Active Always template:

| TransType | Template | |
|---|---|---|
| 15 Delivery | `67` Delivery Approval | |
| **18 A/P invoice** | **`103` API AP AUTO (USER39)** | built for exactly this problem during the A/P batch |
| **20 GRPO** | **— none —** | nobody built the equivalent |

So a GRPO drafted here lands at `WddStatus '-'` and reaches no approver. For an item GRPO
that is a **real difference from keying it in the client**, where it would usually enter
approval. Say so out loud to whoever is expecting to approve it.

**`sapb1 add-draft` is therefore not part of this sheet** — there is nothing for it to
submit to. That mandate belongs to the A/P invoice ([[jivo-add-and-new]], **C-0034**),
whose Always template `103` exists precisely so an API document cannot slip past Bhawani.
The GRPO's only control today is a human at the factory confirming the goods or the trip
actually happened, in *Purchasing – A/P → Purchasing Reports → Document Drafts Report*,
and pressing **Add**.

> **Open item for Accounts:** should GRPO get an Always template like `103`? Until it does,
> every GRPO this CLI creates is invisible to the approval flow that covers 61 % of the
> item receipts keyed by hand. *Measured 2026-08-27; the decision is not ours.*

## Pre-flight — tick before `--yes`

- [ ] shape decided: item (§3, copy the PO) or service (§4, key it)
- [ ] `NumAtCard` clean in `OPDN` **and** `ODRF` for this vendor
- [ ] right book, right `CardCode` **for that book**, right `BPLId`
- [ ] this month's series (Oil Aug-26 = `2477`)
- [ ] `DocType` explicit
- [ ] `DocDate` = gate-in / bilty date; `TaxDate` = same
- [ ] service: **the bilty is the only input** (C-0038) — one line per invoice number
      printed on it, `U_ARNO` transcribed from the paper
- [ ] `U_UNE_LTS` = litres, **not** the bilty's "Actual Kgs" gross weight
- [ ] Dim5 looked up in `OOCR`, not spelled from the state name
- [ ] tax shape read off **this** bill, not from the vendor
- [ ] `WtLiable` set on service lines; **no TDS figure anywhere**
- [ ] bilty page attached — **not** the bill
- [ ] read back §10

## What we have actually done

| | |
|---|---|
| GRPOs posted through this CLI | **none, ever** |
| GRPOs drafted through this CLI | **one** — Oil **`55415`** / DocNum `2026086808`, 2026-08-27 |
| That draft | PICK & SHIP LOGISTICS `VENDA001661`, bilty `NCR-4137`, service, ₹63,100 + IGST 11,358 = **₹74,458** |
| Its state | draft, `WddStatus '-'`, never added |
| Read-back | clean — all 5 dimensions, all 8 UDFs, tax and total survived byte-for-byte |
| What it cost to learn | Dim5 `BH` (a `BR` guess would have failed), Dim2 = the dispatch month, `U_UNE_LTS` ≠ gross kg, attachment = bilty not bill, service GRPOs post no journal |
| What we got wrong | **built the whole method around SAP's AR invoice.** Daman corrected it 2026-08-27: the bilty is the input, the signed AR-invoice photo is later proof of delivery. **C-0038** |

## Open questions

| # | Question | Why it is open | Who answers |
|---|---|---|---|
| 1 | **Where does the operator read `U_UNE_LTS` off the bilty?** | It is not the "Actual Kgs" column (gross weight, packaging included). The arithmetic matches the consignment's pack maths on 73 % of lines, but the *paper source* has never been confirmed — and after C-0038 it cannot be quietly computed out of SAP | Daman / Gurcharan |
| 2 | Should GRPO get an Active *Always* approval template like A/P's `103`? | §11 — every GRPO from this CLI lands at `WddStatus '-'` and reaches no approver | Accounts |

---

Evidence: this sheet's numbers come from `hana-sql` against `OPDN`/`PDN1` in
`JIVO_OIL_HANADB`, 365-day windows, `CANCELED='N'`, mined 2026-08-27.
Related: [[GRPO]] · [[AP-Invoice-Playbook]] · [[Transport-Bill-Playbook]] ·
[[Numbering-Series]] · [[GST-Tax-Codes]] · [[TDS-Withholding]] ·
[[Cost-Centres-and-Dimensions]] · [[Attachments]] · [[Purchase-to-Pay]]
