---
type: playbook
sap_tables: [OPCH, PCH1, PCH5, ODRF, DRF1, DRF5]
objtype: 18
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# A/P invoice — the keying sheet

> One page. Paper in hand to draft read back. Every rule here traces to a measured note;
> the links go to the evidence.

## 0 · Sort the paper first (30 seconds)

| Look for | Tells you | If missing |
|---|---|---|
| The unit / GSTIN on the bill | **Which book** — Oil, Mart, Beverages | Ask. A wrong book means re-keying, not editing |
| A gate-entry stamp | The **posting date**, and that a [[GRPO]] probably exists | No stamp → probably a service bill |
| "(BEVERAGE UNIT)" in the GRN header | The book is Beverages | |
| Goods listed with quantities, or a service | `DocType` **`I`** or **`S`** | |
| "Reverse charge" / "RCM" / "tax payable by recipient" | An `R…` tax code, and the vendor's total **excludes** tax | If the vendor charged GST it is **not** RCM, whatever the narration says |
| Handwritten marks anywhere | **Instructions, not remarks** | Every one maps to a field → the handwriting glossary |

**Read the scan in tiles, not as a page.** A page shrunk to fit is where handwriting dies —
the mark that changed a budget code on Ashok Diwan 1256 sat on top of a rubber stamp.

```bash
python3 .claude/skills/jivo-ap-draft/bin/zoom.py "<scan.pdf>" --dpi 300
```

## 1 · Is it already in SAP?

Do this **before** anything else. Neetu pre-keys drafts, so a draft may already exist.

- [ ] Search `NumAtCard` for this vendor — the vendor's own invoice number is the real
      duplicate key (15,209 distinct values in Oil, filled on 99–100%).
- [ ] Check **Document Drafts** too, not just posted documents.
- [ ] A bare 5-digit number handwritten on the paper is a **draft `DocEntry`** — someone
      already keyed it. Stop and read that draft back.

## 2 · Find the vendor

- [ ] Match on **GSTIN**, not name.
- [ ] **The `CardCode` is book-specific.** The same vendor has different codes in different
      books (Nexton is `VENDA001548` in Oil, `VENDA001235` in Beverages, same GSTIN). Never
      carry a code across. → [[Business-Partner-Master]]
- [ ] `toupper()` is unsupported here, so a name search means fetching and matching in code.
- [ ] Staff expense claim? It is an `ORGV…` **imprest** vendor, not a supplier.

## 3 · Is there a GRPO?

| | |
|---|---|
| **Yes** | Copy from it. You inherit vendor, item, quantity, rate, branch, warehouse, tax code and the scan. **48.8% of invoices** |
| **No** | You type everything. **51.1% of invoices** — this is the normal case, not the exception |
| No GRPO **and** no [[Purchase-Order]] | You cannot finish from the paper. Go back to whoever received the goods |

The GRPO's **tax code is trustworthy** — it matches the invoice on 10,617 of 10,626 lines.
The nine exceptions are place-of-supply corrections. Re-read it anyway on an inter-state
receipt: the factory gate keyed it, not Accounts.

## 4 · The header

| Field | What to put | Rule |
|---|---|---|
| `DocDate` | **The gate-in date** = the GRPO's `DocDate` | Not today. Not the vendor's date. **(C-0017)** |
| `TaxDate` | The date printed on the vendor's paper | |
| `NumAtCard` | The vendor's invoice number, **exactly as printed** | |
| `DocType` | `I` goods · `S` service | No mixed case exists |
| `BPLId` | The branch, from the paper's GSTIN | Fixes **our state**, which decides CGST+SGST vs IGST |
| `Series` | For (type, branch, month) **in this book** | **Book-local.** Aug-26 factory A/P GST = 3684 Oil, 2766 Mart, 2777 Bev → [[Numbering-Series]] |
| `DocumentSubType` | `bod_GSTTaxInvoice` | **(C-0018)** |
| `Comments` | What the bill is for, plus the gate-entry number | Genuinely used — 15,566 distinct values. `JrnlMemo` is auto-generated; don't write there |

## 5 · Each line

| Field | What to put |
|---|---|
| `AccountCode` → HANA `AcctCode` | The GL account. **Codes are not portable across books** → [[Chart-of-Accounts]] |
| `TaxCode` | From the decision table below. **Not** `VatGroup` — that is empty on 100% of non-item lines |
| `LocationCode` → `LocCode` | `2` = factory / Haryana **(C-0025)** |
| `CostingCode` → `OcrCode` | Dim 1 — profit centre |
| `CostingCode2` → `OcrCode2` | Dim 2 — **the month** (`08-2026`) |
| `CostingCode3` → `OcrCode3` | Dim 3 — **the budget.** Read the handwritten note. *Common* → `FACT_COM`, **never** the GRPO's `Factory` **(C-0027)** |
| `CostingCode4` → `OcrCode4` | Dim 4 — department. The only genuinely optional one |
| `CostingCode5` → `OcrCode5` | Dim 5 — the state |
| `WtLiable` | `tYES` if the vendor is liable — 34% of lines are |
| `U_Recvd_Qty` | The paper's quantity or litres, on a service line **(C-0025)** |
| `HsnEntry` / `SacEntry` | HSN for goods, SAC for services — **mutually exclusive (C-0013)** |

Every indirect-expense line carries dims 1, 2 and 3 at **100%** — they are mandatory in
practice, whatever the average fill rate suggests. → [[Cost-Centres-and-Dimensions]]

## 6 · The tax code

| Rate on the paper | Same state | Different state | Same state + RCM | Different state + RCM |
|---|---|---|---|---|
| Exempt / nil | `Exampt` | `Exampt` | n/a | n/a |
| 0% | `CG+SG@0` | `IGST@0` | none exists | none exists |
| 0.1% merchant export | — | `IGST@0.1` **Oil only** | — | — |
| 5% | `CG+SG@5` | `IGST@5` | `GST05R` Oil/Bev · `RCGSG@5` Mart | `RIGST@5` |
| 18% | `CG+SG@18` | `IGST@18` | `RCGSG@18` | **`RISGT@18`** ← misspelled |
| 40% | `CG+SG@40` **Mart/Bev only** | `IGST@40` **Mart/Bev only** | none | none |

- **`Exampt` and `RISGT@18` are misspelled in the master.** Matching the correct spelling
  finds nothing.
- **Never reach for 12% or 28% without asking** — nothing in any book has used one in 120
  days.
- **Road freight / GTA is almost always RCM** — `GST05R` intra-state, `RIGST@5` inter-state.
  77% of Oil's RCM lines are transporters.
- **No RCM code exists at 0%, 40% or with cess.** If the paper says reverse charge at such a
  rate, stop and ask. Do not substitute the nearest code. → [[GST-Tax-Codes]]

## 7 · TDS

- [ ] Is this vendor and this expense liable? **34% of lines are.**
- [ ] Set `WtLiable` = `tYES` on the line **and** send the code on the header:

```json
"WithholdingTaxDataCollection": [ { "WTCode": "1027" } ]
```

**SAP computes the rest.** Proven on draft 55177 — sending just the code produced rate 10%,
base ₹1,00,000, TDS ₹10,000, and `DocTotal` ₹1,08,000 (taxable + GST − TDS).

- **The line flag alone does nothing** — 67 hand-keyed Oil drafts carry `WtLiable` = `Y`
  with zero withholding rows and zero TDS.
- **TDS accounts differ per book and were renumbered on 2026-06-01.** Contractor 2% is
  `2133018` Oil, `2133021` Mart, `2133016` Bev. **Identify by name, never by number.**
  → [[TDS-Withholding]]

## 8 · The scan

- [ ] Attach the bill.
- [ ] Set `U_CHK2` = `OK` and `U_CHK` = size in KB on each line **(C-0026)**.
- [ ] Copy the base document's file onto the draft as an independent second line.
- [ ] **`400 Bad Post content` is NOT a size limit** — it is curl's `Expect: 100-continue`
      header breaking the multipart. Send `-H 'Expect:'` and a 1.4 MB file uploads fine.
      *(Draft 55177 was fixed by compressing it, which worked but for the wrong reason —
      the header was the real cause.)*
- [ ] **Compress anyway if the document total is near 10 MB** — `SUM(U_CHK) > 10240` is a
      live JIVO guard that refuses the Add. The per-line 1 MB guard exists but is
      **commented out**, so it does not fire.
- [ ] **Mart has no `U_CHK`/`U_CHK2` columns at all** — sending them returns `-1000`.
      Oil needs both, Beverages needs only the tick. → [[Attachments]]

## 9 · Read it back — the part that catches today's misses

| Check | Why |
|---|---|
| **`WTAmount`** non-zero if liable | **Not `WTApplied`** — that is 0 on every draft by design |
| `DocTotal` = taxable + GST − TDS, to the paisa | |
| `VatSum` matches the paper's GST | **On an RCM bill header `VatSum` is 0** — 1,135 of 1,135 Oil RCM invoices. The tax lives only on the line and in the journal |
| An RCM code produced **two** journal lines | Input and output, equal and opposite |
| `OcrCode3` matches the **handwritten** allocation | Not the GRPO's default |
| Journal line count is 2–6 | Anything else means it was keyed differently |
| `5680014` SHORT AND EXCESS appeared | Normal — it is SAP's rounding sink, `=\|RoundDif\|`. Not a variance. Ignore it |
| The attachment is there with its flags | |

## 10 · Then a human presses Add

Nothing posts until someone opens **Document Drafts** and adds it. Your draft is visible to
everyone and enters the approval flow immediately.

- **Exit code 7 = "unknown, go look."** The request reached SAP but the answer didn't come
  back. **Do not re-run.** Check Document Drafts.
- Count the queue on **`WddStatus`**, never `DocStatus` — 817 of 1,088 "open" Oil A/P drafts
  are cancelled in approval, not pending. → [[Document-Drafts]]

## The five things you always decide yourself

However complete the upstream documents are, these are never handed to you — and they are
where every one of today's misses lived:

1. **Series** — book-local
2. **`LocationCode`**
3. **`CostingCode3`** — the budget, off the handwritten note
4. **TDS** — the code on the header, not just the line flag
5. **`NumAtCard`** — the vendor's own number, the duplicate key

Plus the **posting date**, which belongs to a document you did not create.

## Transporter / freight bills have their own sheet

They break enough of the rules above to need one: the posting date is the **bill** date
not the gate date, the dimensions all arrive from the GRPO, `U_Recvd_Qty` stays empty,
the tax is usually **RCM** so `DocTotal` = freight − TDS, and the bilty numbers are the
key that finds the GRPOs. → **[[Transport-Bill-Playbook]]**

## Don't hand-roll it

Use the **`jivo-ap-draft`** skill. Its pre-check finds the GRPO, branch, series and any
existing draft before anything is sent; its read-back catches what SAP left blank. It was
built from live mistakes on 2026-08-21 and has been corrected four times since.

Evidence behind every rule here: [[AP-Invoice]] · [[GRPO]] · [[Purchase-to-Pay]] ·
[[Field-Name-Rosetta]] · [[Numbering-Series]] · [[Chart-of-Accounts]] ·
[[Cost-Centres-and-Dimensions]] · [[GST-Tax-Codes]] · [[TDS-Withholding]] ·
[[Business-Partner-Master]] · [[Document-Drafts]]
