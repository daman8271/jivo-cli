---
name: jivo-oil-freight-grpo
description: Use when a transporter's freight bill / bilty / LR arrives for JIVO OIL and freight GRPOs must be raised in SAP B1 — "make the GRPO for this bill", "ABHIMAN bill", "DEL/260349", a scanned transporter tax invoice listing bilties and invoice numbers, or a bilty scan. Also use to check whether a bilty is already keyed. NOT for Beverages freight (jivo-bev-freight-grpo) and NOT for a bill made out to JIVO MART (jivo-mart-freight-grpo) — all three books use different templates and not for the A/P invoice that copies these GRPOs (Transport-Bill-Playbook).
---

# Oil freight GRPO from a transporter's bill

> 🔴 **ATTACHMENT RULE — every file goes up with `sapb1 attach`, never by hand (Daman, 16 Sept 2026 · C-0090).**
> Whatever this skill attaches — to a draft, GRPO, A/P, credit memo, payment, JV, A/R, anything —
> upload it with **`sapb1 attach <file> [<file>...] --company <DB>`** (`--dry-run` first, then `--yes`).
> It puts all the files on ONE `Attachments2` row, ticks **Copy to Target Document = `tYES`** on
> every line (plus the Approve stamp `U_CHK`/`U_CHK2 OK` in Oil and Bev — Mart has no such fields),
> reads the row back, and exits non-zero unless every line is `tYES` and every file downloads
> back byte-identical. An upload by any other route
> lands `tNO`, and then the scan does NOT follow the document onward (GRPO → A/P, draft → posted).
> - It prints `"AttachmentEntry": N` — point the document at row N (in the payload, or `sapb1 patch`).
> - Exit 8 = the row exists but is not finished — the message names the fix (usually
>   `sapb1 attach --row N --yes`). Exit 7 = an answer never came back: look at the row
>   (`sapb1 query Attachments2 --filter "AbsoluteEntry eq N"`) before sending any file again.
> - Never `curl -X POST …/Attachments2` or hand-PATCH the tick any more. Proven live 17 Sept 2026:
>   Oil 177963 (two files, byte-identical), Mart 59373, Bev 43331.

Internal skill. Built 2026-08-31 on ABHIMAN EXPRESS bill **DEL/260349** — 5 bilties,
12 sale invoices, ₹1,68,630, drafts **55594–55598** — taught through by Daman the same
afternoon after the previous attempt got Dim1 and litres wrong.

**The Oil job is a three-paper job and the middle paper is the one people skip.**
Beverages collapses to one sheet ([[jivo-bev-freight-grpo]]); Oil does not, because
**litres and variety exist only on JIVO's own AR invoice PDF** — they cannot be
computed and cannot be queried out of SAP.

| Paper | Where it comes from | What only it can tell you |
|---|---|---|
| the transporter's **bill** | the operator, scanned | bilty no · bilty date · route · **the sale-invoice numbers** · the freight per bilty |
| the **AR invoice PDFs** | `logistics@jivo.in` | **litres** · **category** — the Product Category block |
| SAP | `OINV` / `OCRD` | the customer `CardCode` per invoice, and the destination state |

---

## 0 · Before anything: is this even Oil, and is it already keyed?

Read the company off the **consignees**, never off the bilty number — a transporter runs
one bilty book across all three JIVO companies.

```bash
for db in JIVO_OIL_HANADB JIVO_MART_HANADB JIVO_BEVERAGES_HANADB; do
  hana-sql/hana-sql -env connections/hana-office-bridge.env \
    "SELECT '$db' DB,COUNT(*) FROM \"$db\".\"OINV\" WHERE \"DocNum\" IN (…3-4 invoice nos…)"
done
```

**The same transporter has a different CardCode per book** — ABHIMAN is `VENDA001676`
in Oil, `VENDA001019` in Mart, `VENDA001362` in Bev; MAHAVIR is `VENDA001523` / `VENDA001010`
/ `VENDA001214`.

**A single bill can span two companies, and nothing on the paper says so.** On MAHAVIR
bill `678` (2026-08-31) 14 bilties were Oil and **one — GR `3670`, ROHINI, ₹3,000 + ₹380
labour — was Beverages**: its invoice `626077983` is RM HYPERMARKET and exists only in
`JIVO_BEVERAGES_HANADB`. Run the count above over **every** invoice number on the bill,
not three of them; the odd one out is the whole finding. Key that bilty separately with
[[jivo-bev-freight-grpo]] against the Bev CardCode, and expect Σ your Oil drafts to be
**less** than the bill footer by exactly that bilty.

Then never key a bilty twice — check the posted book *and* the drafts:

```sql
SELECT T0."DocEntry",T0."DocNum",T1."U_BilltyNumber" FROM "JIVO_OIL_HANADB"."OPDN" T0
 JOIN "JIVO_OIL_HANADB"."PDN1" T1 ON T0."DocEntry"=T1."DocEntry"
 WHERE T1."U_BilltyNumber" IN (…);          -- and the same against ODRF/DRF1
```

## 1 · Clone the template, don't invent it

Pull that transporter's own last freight GRPO and copy its constants. Every field below
came out of ABHIMAN's `25645`/`25646`, and the ones that vary by vendor are marked.

```sql
SELECT T0."DocNum",T0."Series",T0."BPLId",T0."SlpCode",T1."AcctCode",T1."TaxCode",
       T1."OcrCode3",T1."LocCode",T1."U_Sub_Account"
  FROM "JIVO_OIL_HANADB"."OPDN" T0 JOIN "JIVO_OIL_HANADB"."PDN1" T1
    ON T0."DocEntry"=T1."DocEntry"
 WHERE T0."CardCode"='<vendor>' AND T0."CANCELED"='N'
 ORDER BY T0."DocDate" DESC;
```

## 2 · Get the AR invoice PDFs

The bilty hands you the invoice numbers in writing; you then open **those exact**
invoices. (This is not a contradiction of **C-0038** — never *search* SAP for an
invoice that might match a bilty, that join is 43.8 % reliable.)

```bash
mail-cli/jmail search --text "<invoice no>" --since <date> --with-attachments
mail-cli/jmail pull <uid> --out ./inv          # one mail often carries several
```

Name-check what comes back: the filenames carry the customer, and they must match
`OINV.CardName` for that invoice. That caught a misread digit on `DEL/260349` — the bill
scan reads `626070256`, the real invoice is **`626070756`** (SINGHAL FOODS, ₹18.8 L,
vs a ₹700 doc for a different party).

## 3 · Read the Product Category block — never by eye, never as plain text

```bash
.claude/skills/jivo-oil-freight-grpo/bin/parse_invoices.py ./inv -o invoices.json
```

**The block sits beside the RTGS/NEFT bank details.** A plain `pdftotext` dump
interleaves the two columns and quietly turns `IFSC` and `Bank` into categories — which
on `626070718` produced OLIVE instead of CANOLA. The script reads word coordinates and
takes only what is inside the Category/Litre column bounds.

It refuses to hand you anything that fails its three self-checks:

- printed `Total` == the sum of the category rows
- one litre value for every category row
- the resulting Dim1 is a real `OOCR` `DimCode=1` code

**Category labels can be two words.** `RICE BRAN` read as `RICE` + `BRAN` gives two labels
for one litre value and mis-pairs every row under it — that is what the pairing check
caught on bill `678`. The block's wording is not the master's code either: `SUNFLOWER`
→ **`SUNFLOWR`**, `GROUNDNUT` → **`GROUNDNT`**, `RICE BRAN` → **`RICEBRAN`**. The script
maps those and stops on anything it does not recognise rather than sending it.

If either fails, **open the PDF and read the block by eye**. Do not build from it.

### The three rules the block decides

| | Rule | |
|---|---|---|
| **`U_UNE_LTS`** | the printed **`Total` of the Litre column**. Never the Gross Wt (packaging-inclusive: 6,300 L ships as 6,257.83 kg), never computed from pack sizes (67 % accurate) | **C-0060** |
| **Dim1** | sum the Litre column **per category**, biggest **total** wins. Same category at two pack sizes is **added**. `626070718`: CANOLA 2,000+800=**2,800** beats SUNFLOWER 2,000 and OLIVE 700+800=1,500 | **C-0058** |
| **skip** | an invoice whose block is **only** TIN / CAPS / CARTON gets **no line at all**. Any oil present and it goes in, packaging rows included — they are 0 L, so they change nothing | **C-0059** |

The block spells it `SUNFLOWER`; the Dim1 master spells it **`SUNFLOWR`**. The script
maps it. Check any new category against `OOCR` `DimCode=1` before trusting it.

## 4 · Build the drafts

**One draft per BILTY. One line per SALE INVOICE. Freight pro-rata on litres, last line
absorbs the rounding.** Proved exact on the template: `25645` split 64,000 over
4,500/3,000 L → 38,400/25,600; `25646` split 63,902 over 9,000/325 L → 61,675/2,227.

```bash
.claude/skills/jivo-oil-freight-grpo/bin/build_drafts.py bill.json invoices.json customers.json
```

`customers.json` is `{invoice: CardCode}` straight out of `OINV` — it feeds
`U_CardCode`, decides `SALES` vs `BST`, and the customer's ship-to `State` in `CRD1` is
your second, independent read on Dim5.

> **⚠ CardCodes are PER BOOK.** `CUSTA000877` is **JIVO MART - RJ** in the Mart book and
> **M/S FOOD MONDE** in Oil. A JIVO-card list borrowed from another company silently
> marks an outside customer as intercompany — it did exactly that here before the set was
> split per company. `BST_CARDS_BY_COMPANY` in `build_drafts.py` is keyed by company for
> that reason; regenerate it per book with:
> ```sql
> SELECT "CardCode","CardName" FROM "<db>"."OCRD"
>  WHERE UPPER("CardName") LIKE '%JIVO WELLNESS%' OR UPPER("CardName") LIKE '%JIVO MART%';
> ```

### Every field, and where it comes from

| Field | Value | Source |
|---|---|---|
| `DocType` | `dDocument_Service` | a freight GRPO is a service; it posts **no journal** |
| `CardCode` | the transporter, **in this book** | §0 |
| `DocDate` / `TaxDate` / `DocDueDate` | **the bilty date**, not the bill date | |
| `NumAtCard` · `Comments` | the **bilty** no · `BILTY NO <bilty>` | the bill's `NumAtCard` is the transporter's invoice — that goes on the A/P invoice, not here |
| `Series` | the `NNM1` series for the **bilty's month** (`2477` = GRPO0826) | series is monthly; a July bilty keyed in August still uses July |
| `BPL_IDAssignedToInvoice` | `2` FACTORY | |
| `SalesPersonCode` | **not a constant** — clone it (ABHIMAN & PICK & SHIP `115`, ARNAV `11`) | |
| `ItemDescription` · `AccountCode` | `EDIBLE OIL` · `5670001` | |
| `TaxCode` | **depends on the transporter's own state — clone it.** Interstate (vendor GSTIN `07` Delhi → Oil `06`): `RIGST@5`. Intrastate (vendor GSTIN `06` Haryana): **`GST05R`**. Set `tax_code` in `bill.json` | both are reverse charge; header `VatSum` stays 0 either way |
| `LocationCode` | `2` | C-0025 |
| Dim1 `CostingCode` | §3 | **C-0058** |
| Dim2 `CostingCode2` | the **dispatch** month `MM-YYYY`, off the bilty date | not the GRPO's own month |
| Dim3 `CostingCode3` | `Del Bkhp`. **Never `FACT_COM`** | |
| Dim4 | Oil: **empty** | |
| Dim5 `CostingCode5` | the **destination state** — look it up, never spell it | Bihar `BH`, Odisha `OR`, Uttarakhand `UK`, Karnataka `KN` |
| `U_BilltyNumber` · `U_BiltyDate` · `U_ARNO` | bilty · bilty date · **the sale invoice number** | |
| `U_UNE_LTS` | §3 | **C-0060** |
| **`U_Sub_Account`** | **`SALES`** for an outside customer · **`BST`** when that line's sale invoice is billed to **JIVO WELLNESS or JIVO MART** | **SAP refuses the document without it.** Decided **per line** off `U_ARNO` — one bilty can carry both (**C-0063**) |
| **`U_CardCode`** | the **customer** on that sale invoice | not the vendor |
| `U_Remarks` | `BILTY NO <bilty>` | |
| `Quantity` | omit — service lines have none | |

**If you miss `U_Sub_Account`, `U_BilltyNumber` or `U_ARNO`, SAP refuses the whole
document** with `[SAP -1116] (1120020) For Freight Booking, Please Fill Bilty No,
Invoice No and Sub Account`. That refusal is clean — nothing is created.

### Two shapes the ABHIMAN bill did not have

**A LABOUR column.** MAHAVIR bills freight and labour separately and foots them to a
`G. TOTAL`. **Both go on the GRPO** — the bilty's line is freight + labour — because the
A/P invoice that copies these must tie to the vendor's G. Total. Evidence: every past
MAHAVIR A/P is exactly **99 %** of the GRPO total it was built from (4,000→3,960;
22,500→22,275; 63,894→63,255) — that 1 % is 194C transporter TDS at the invoice, so the
GRPO carries the gross. **Confirmed by Daman, 2026-08-31 (C-0062).**

**One freight amount covering TWO bilties** (a merged cell). On bill `678`, GR `3692`+`3693`
share ₹4,000 and GR `3807`+`3808` share ₹11,000. Keep **one draft per bilty** and split the
shared amount across them **pro-rata on litres**, the same rule used inside a bilty. Check
the column foots to the printed TOTAL before you trust your reading of a merged cell —
that arithmetic is what proves the merge covers two rows and not one.

## 5 · Send, one at a time

```bash
sapb1 draft grpo --company JIVO_OIL_HANADB --dry-run --data "$(…)"    # show the first
sapb1 draft grpo --company JIVO_OIL_HANADB --yes     --data "$(…)"    # then the rest
```

## 6 · Read it back, then STOP

```sql
SELECT T0."DocEntry",T0."NumAtCard",T0."DocTotal",T0."Series",T0."WddStatus",
       T1."U_ARNO",T1."U_UNE_LTS",T1."LineTotal",T1."TaxCode",T1."OcrCode",
       T1."OcrCode2",T1."OcrCode3",T1."OcrCode5",T1."U_Sub_Account",T1."U_CardCode"
  FROM "JIVO_OIL_HANADB"."ODRF" T0 JOIN "JIVO_OIL_HANADB"."DRF1" T1
    ON T0."DocEntry"=T1."DocEntry" WHERE T0."DocEntry" BETWEEN <a> AND <b>;
```

- [ ] one draft per bilty on the bill
- [ ] Σ `DocTotal` == the bill footer, to the rupee
- [ ] header `VatSum` 0 (reverse charge)
- [ ] Series / BPL / DocType right on every one
- [ ] all five dimensions filled on every line, Dim4 empty
- [ ] `U_Sub_Account` = `SALES` on every outside-customer line, `BST` on every JIVO-to-JIVO one

**Then hand over the DocEntry list and stop.**

> **Never run `sapb1 add-draft` on a freight GRPO.** There is no Always approval template
> for TransType 20, so **Add posts it live** — there is no approver step to submit it to
> (**C-0044**; unlike an A/P invoice, whose template `103` exists precisely for that).
> A human confirms the trip happened and presses Add in the SAP client.
> Daman, 2026-08-31: *"do not add it — I wanna see only the draft."*

**The drafts carry no attachment.** [[GRPO-Playbook]] §9 wants the **bilty** page on each
one, filenamed by bilty number — **not** the transporter's bill, which belongs on the A/P
invoice (**C-0026**). Say so explicitly when you hand over, and ask for the bilty scans.

Note whose SAP login made them: they land in **that user's** Document Drafts list. From
this Mac that is `manager`, not an operator's desk.

## 7 · What comes next

The A/P invoice against the transporter's bill copies these GRPOs — that is
[[Transport-Bill-Playbook]], and it is a copy job once the GRPOs are right.

---

Related: [[GRPO-Playbook]] §4/§4A, [[jivo-bev-freight-grpo]], [[Transport-Bill-Playbook]],
[[jivo-add-and-new]]. Corrections **C-0058** (Dim1 = biggest category total, supersedes
C-0048), **C-0059** (packaging-only invoice gets no line), **C-0060** (`U_UNE_LTS` is the
printed Total), **C-0061** (a bill can span two companies), **C-0062** (freight + labour),
**C-0063** (BST when JIVO-to-JIVO), C-0025, C-0026, C-0033, C-0038, C-0044.
