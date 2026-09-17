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
| Dim2 `OcrCode2` | **52.3 %** | half are blank. **Set it** = the month of the **supplier's tax invoice date** (`TaxDate`), never gate-in **(C-0093)** |
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
| `SalesPersonCode` | **not a constant** — 55 · 11 · 43 · 115 all in live use | the *Buyer* box. Clone it from that transporter's last GRPO: ARNAV is `11` GINNI VG on 309/309 lines FY26-27, PICK & SHIP is `115` |
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

### `U_UNE_LTS` — litres. **Answered 2026-08-27: read it, do not compute it.**

`U_UNE_LTS` is **litres of oil on that sale invoice**, and the operator does not work it
out. **JIVO's own AR invoice PDF prints it.** At the foot of every tax invoice, beside the
terms, there is a **Product Category** block:

```
Category      Litre     Gross Wt
OLIVE       400.0000    407.8580
OLIVE       320.0000    318.6100
CANOLA      300.0000    297.6810
SOYABEAN    600.0000    574.7800
Total        1620.00    1598.93     <- this is U_UNE_LTS
```

Invoice `626080289` prints `Total 1620.00`; GRPO `26081` line 3 carries `U_UNE_LTS =
1620`. Exact, no arithmetic. **Take the "Total" figure from the Product Category block —
never the Gross Wt column** (that is packaging-inclusive: 1,620 L shipped as 1,598.93 kg).

**Where the PDF comes from: the `logistics@jivo.in` mailbox.** PPC (`ppc.ho@jivo.in`)
mails each invoice as `<DocNum> <party>.pdf` to logistics on the dispatch day. Find it
with the invoice number the *bilty* gave you:

```bash
mail-cli/jmail search --text "626080289" --since 2026-08-01
mail-cli/jmail pull <uid> --out ./bills
```

This is **not** a contradiction of C-0038. C-0038 forbids *hunting SAP for an AR invoice
that might match a bilty* — that join is 43.8 % reliable and must never be used. Here the
bilty **hands you the invoice number in writing**; you then open that exact invoice's PDF.
The bilty stays the sole key. The invoice is looked up, never searched for.

<details><summary>If the PDF is genuinely unavailable — the fallback, and its error rate</summary>

litres = Σ (pack litres × pieces), with weight packs converted at **0.91 kg/L**
(measured: median 1.09890 L/kg over 1,068 purely weight-packed invoices = 1 ÷ 0.91 exactly;
831 of them land on 1.099 to three places). `OITM.U_UNE_TOTL`, `U_UNE_TOTB` and `SVolume`
are **NULL on every finished good** — the figure is computed by the invoice print layout,
not stored, which is why it cannot be queried out of SAP.

Reproduces the keyed `U_UNE_LTS` on **4,174 of 6,229 Oil freight lines exactly (67.0 %),
4,649 within 2 % (74.6 %)**. *Measured 2026-08-27.* A quarter wrong is why this is a
fallback and not the method.
</details>

### Dim1 (Variety) — the biggest single PRODUCT by litres **(C-0048, confirmed by the desk)**

**Gurcharan, via Daman, 2026-08-27:** *"When there is multiple products in a single invoice,
then the product with the maximum litre is selected."*

**The word that matters is *product*.** It is **not** the oil type added up across pack
sizes. Invoice `626080289` prints:

```
OLIVE      400.0000     <- 5 LTR tins
OLIVE      320.0000     <- 1 LTR
CANOLA     300.0000
SOYABEAN   600.0000     <- biggest single product  ==> Dim1 = SOYABEAN
Total     1620.00
```

Olive *totals* 720 L, but no single olive product beats soyabean's 600, so the line is
**SOYABEAN**. Reading it as "the oil type with the most litres" gives OLIVE and is wrong —
that error is what made this document look like an operator exception for half a day.

> **Still open — ask before keying, it is the only ambiguity left.** When one oil appears
> **twice at two pack sizes**, are the two rows added or kept separate? `26081` keeps them
> separate. But on **75 of the 131** past Oil lines where the two readings diverge, the
> keyed value matches the *added* total instead. It only bites on split-pack invoices —
> everywhere else both readings agree. → Open question 1a

## 4A · Worked example — bilty `7339`, the whole chain end to end

The one fully-traced real GRPO. Oil, **DocEntry `26081`** / DocNum `2026086780`, keyed by
**GURCHARAN (USER19)** on 2026-08-26 for a bilty dated 2026-08-13. Everything below was
read back out of `OPDN`/`PDN1`.

**Three papers, three different jobs — and none of them is optional:**

| Paper | Where it comes from | What only it can tell you |
|---|---|---|
| **The bilty** (`7339.pdf`) | the transporter, scanned | bilty no · bilty date · vehicle · **the sale-invoice numbers** · consignee · total boxes |
| **The AR invoice PDFs** | `logistics@jivo.in`, mailed by `ppc.ho@jivo.in` | **litres** (Product Category → Total) · **category/variety** · box count · destination state |
| **The transporter's invoice book** (`.xlsx`) | mailed by the transporter from his own address | **the freight amount**, split Freight + Labour · the weight |

> **The freight figure is not on the bilty.** `7339`'s bilty has an empty "Total Freight"
> box. The number came from ARNAV's own mailed workbook, sheet `401` (bill ATS:401,
> 2026-08-24), row: `7339 | 626080290/289 | 3200 kg | DELHI | LEBOUR 820 | Freight 4500 |
> **TOTAL 5320**`. `DocTotal` = 5,320. **Freight + Labour go in as one figure** — there is
> no separate labour line.
>
> ```bash
> mail-cli/jmail search --sender <transporter> --since 2026-08-01 --with-attachments
> ```

**The bilty under-reports the invoices — cross-check on box count.** `7339` writes
`Bill No. 626080290, 289`, but the GRPO has **three** lines. The bilty's description says
**"205 Box Edible Oil"**, and the invoices print their box counts: `626080296` = 50 Box,
`626080290` = 50 Box, `626080289` = 105 Box → **205**. Two invoices only add to 155.
**Always add the invoices' "Total … Box" up to the bilty's package count before keying** —
that is what catches a missing invoice, and there is nothing in SAP that will.

**The keyed document:**

| Header | |
|---|---|
| `CardCode` | `VENDA000956` ARNAV TRANSPORT SERVICE |
| `NumAtCard` | `7339` — the G.R. No, and nothing else |
| `DocDate` = `TaxDate` = `DocDueDate` | `2026-08-13` — **the bilty date**, not the keying date |
| `Series` `2477` (`GRPO0826`) · `BPLId` `2` FACTORY · `DocType` `S` | service, Aug-26, factory branch |
| `DocTotal` | `5,320` · `VatSum 0` (reverse charge) · `WTSum 0` |

| # | `U_ARNO` | `OcrCode` Dim1 | `U_UNE_LTS` | `Price` |
|---|---|---|---|---|
| 1 | `626080296` | SUNFLOWR | 1,000 | 1,652 |
| 2 | `626080290` | CANOLA | 600 | 991 |
| 3 | `626080289` | SOYABEAN | 1,620 | **2,677** |
| | | | **3,220** | **5,320** |

Common to all three lines: `AcctCode 5670001` · `Dscription EDIBLE OIL` · `TaxCode
RIGST@5` · `LocCode 2` · `SacEntry 2` (9967) · `OcrCode2 08-2026` · `OcrCode3 Del Bkhp` ·
`OcrCode5 DL` · `U_Remarks BILTY NO 7339` · `U_BilltyNumber 7339` · `U_BiltyDate
2026-08-13` · `U_CardCode CUSTA000178` · `U_Sub_Account SALES` · `U_UNE_CALI/CUNT Y`.

### How the freight splits — pro-rata on litres, last line absorbs the rounding

₹5,320 ÷ 3,220 L = **₹1.65217/L**, applied to each invoice's litres:

| | litres | exact | keyed |
|---|---|---|---|
| 1 | 1,000 | 1,652.17 | 1,652 |
| 2 | 600 | 991.30 | 991 |
| 3 | 1,620 | 2,676.52 | **2,677** |
| | | 5,319.99 | **5,320** |

Round each line to whole rupees, then **set the last line to `total − Σ(the others)`** so
the document ties to the bilty exactly. Never leave a 1-rupee gap and never adjust the
total. **Confirmed by the desk (C-0048): "divide the total amount litre-wise provided in each
invoice no."** Holds on **1,120 of 1,253 multi-line Oil freight GRPOs (89.4 %)** with every
line inside the rounding tolerance. Where it does not, check the transporter's own workbook
first — if that sheet apportions per invoice itself, its figures win.

### What the handwriting on the bilty is — and is not

`7339` carries a Gurmukhi note across the description box, next to the consignee's stamp
and the printed *"We are not responsible for Leakage & Breakage"* clause. Best reading
(**low confidence — verify with the operator, the hand is poor**):

> `3 — ਪੇਟੀ ਸੋਇਆ ਪਾਊਚ …` — 3 boxes soya pouch
> `1 — " ਸਨਫਲਾਵਰ …` — 1 box sunflower ("`"`" = ditto)

It reads as a **delivery-side damage/shortage note written by the consignee**, not an
entry instruction: the counts (3, 1) match no invoice, box or litre figure on the
document. **Nothing from it was keyed** — `U_Remarks` is `BILTY NO 7339` and nothing more.
The two numbers written in the printed boxes *are* keyed-relevant, and both are easy to
misread: the **"Rate" box holds `3200/KG`, which is the weight**, and the vehicle number
`DL1LAK7060` is written *above* a struck-out one.

**Standing rule from this document: a handwritten mark on a bilty is either a damage note
(ignore, but tell the operator) or a correction to a printed box (use the correction).
If you cannot tell which, ask — do not key it into `U_Remarks`.**

## 5 · The five dimensions

**A service GRPO is the origin of all five** — the A/P invoice inherits every one of them
(verified on draft 39829). **C-0035 ("lines inherit only Dim1") is the item-GRPO rule and
does not apply to freight.** So a dimension wrong here is wrong on the bill too.

| | Value | Measured |
|---|---|---|
| Dim1 `CostingCode` | **the variety shipped** — `OLIVE`, `CANOLA`, `MUSTARD` … | off the bilty's goods description. Where a consignment is mixed it is the **dominant** variety, not a split — that reproduces the keyed value on 2,759 of 3,267 lines (84.5 %) |
| Dim2 `CostingCode2` | **the month of THAT LINE's sale (tax) invoice date, `MM-YYYY`** — never the bilty date | **C-0093.** Where the two months differ, 223 of 242 hand-keyed lines (Jun–Aug 2026) took the invoice month. One bilty can carry two months |
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
| What it cost to learn | Dim5 `BH` (a `BR` guess would have failed), Dim2 = each line's sale invoice month (C-0093; first written here as "dispatch month", which was wrong), `U_UNE_LTS` ≠ gross kg, attachment = bilty not bill, service GRPOs post no journal |
| What we got wrong | **built the whole method around SAP's AR invoice.** Daman corrected it 2026-08-27: the bilty is the input, the signed AR-invoice photo is later proof of delivery. **C-0038** |

## Open questions

| # | Question | Why it is open | Who answers |
|---|---|---|---|
| 1 | ~~Where does the operator read `U_UNE_LTS` off the bilty?~~ | **ANSWERED 2026-08-27 — he does not read it off the bilty.** It is printed on JIVO's own AR invoice PDF, in the Product Category block, as `Total … Litre`; the PDFs sit in `logistics@jivo.in`. §4 | closed |
| 1a | **On a mixed-category invoice, which category becomes Dim1?** | No rule reproduces the operator: best is top-by-litres at 84.5 % over 2,164 mixed lines, and the one fully-traced document is an exception to it | Gurcharan |
| 1b | **When the freight does not split pro-rata on litres (17 % of multi-line GRPOs), what is the basis?** | Weight and box count both fail to explain them; the transporter's own workbook may already apportion | Gurcharan |
| 2 | Should GRPO get an Active *Always* approval template like A/P's `103`? | §11 — every GRPO from this CLI lands at `WddStatus '-'` and reaches no approver | Accounts |

---

Evidence: this sheet's numbers come from `hana-sql` against `OPDN`/`PDN1` in
`JIVO_OIL_HANADB`, 365-day windows, `CANCELED='N'`, mined 2026-08-27.
Related: [[GRPO]] · [[AP-Invoice-Playbook]] · [[Transport-Bill-Playbook]] ·
[[Numbering-Series]] · [[GST-Tax-Codes]] · [[TDS-Withholding]] ·
[[Cost-Centres-and-Dimensions]] · [[Attachments]] · [[Purchase-to-Pay]]
