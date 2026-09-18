# Matching a bill to its GRPO, resolving the vendor, and running a pile of them

Everything here was learned on 2026-08-26 entering 22 scans as Oil A/P drafts
(55311-55329 + 55302, ₹51.06 lakh). Each rule below cost a wrong turn to find.

---

## 1. The primary key is `PurchaseDeliveryNotes.NumAtCard` — it holds the VENDOR'S invoice number

The GRPO stores the vendor's own bill number. That makes paper → GRPO an exact
lookup, not a guess:

```bash
sapb1 query PurchaseDeliveryNotes --filter "contains(NumAtCard,'<the bill no>')" \
  --select "DocEntry,DocNum,CardCode,CardName,NumAtCard,DocDate,DocTotal,DocumentStatus"
```

Gate number, amount and date are **corroboration only**. Why they fail:
- the gate number is handwritten (one read as `287` was `237` at 900 dpi — the GRPO was right)
- several GRPOs share an amount (three TPAC GRPOs at ₹2,53,110)
- `precheck.py` still matches on gate/qty/total, so run this query yourself first

**Two hits on one `NumAtCard` is a FINDING, not an ambiguity to resolve by
picking one.** BR Agrotech invoice `2633100542` returned GRPO 2026086622
(`NumAtCard '.2633100542'`, created 08-17) *and* 2026086714 (clean ref, 08-22) —
both open, both ₹3,61,250, both gate 148, same UserSign. One delivery received
twice = phantom stock. Draw from the right one (its item matched the paper:
`PM0000195` "52 GMS GREEN" vs the other's `PM0000121` POMACE) and **tell the
operator the duplicate must be cancelled in the client**.

## 2. Take `CardCode` from the GRPO. Never match a vendor by name.

`OCRD.FederalTaxID` is **empty for all 2,235 Oil vendors**, so there is no ID to
match on (cf. C-0014). Name similarity produced two confident, wrong answers:

| Paper | Fuzzy match | Score | Truth |
|---|---|---|---|
| TPAC PACKAGING INDIA PRIVATE LIMITED | GTECH PACKAGING INDIA PRIVATE L | 0.80 | **VENDA000939** |
| PIONEER PET | HOSE EXPERT | 0.60 | **VENDA000942** |

Five bills, ₹13.9 lakh, would have booked to the wrong party with every other
check — totals, tax, branch, series — passing clean. The goods physically arrived
from the vendor on the GRPO; that is a fact, not an inference.

## 3. A GRPO-drawn line inherits Dim1 ONLY (C-0035)

`BaseType 20 / BaseEntry / BaseLine` brings down `CostingCode` (Variety) and
`LocationCode`. **`CostingCode2`, `3` and `5` arrive null.** Set them in the
payload, or patch after:

```bash
sapb1 patch "Drafts(<DocEntry>)" \
  --data '{"DocumentLines":[{"LineNum":0,"CostingCode2":"08-2026"}]}' --yes
```

**Effective Month (`CostingCode2`, Dim2) = the DocDate's month, `MM-YYYY`.**
Valid codes are `OOCR` where `DimCode=2`. The patch leaves DocTotal, the GRPO
base links, LocationCode and AttachmentEntry untouched — verified on 20 drafts.

## 4. Bottles ship with caps at ₹0 — the quantity check will lie

A packaging GRPO carries the closure as a companion line at `UnitPrice 0`, so
open qty is ~2× the paper. `precheck.py` trips on this every time
(`invoice qty 3750 ≠ GRPO open qty 7500`). **The money is the reliable test** —
it matched to under ₹1.50 on all five that tripped.

Posted precedent (Raj Technopack SNP-0691/26-27, DocEntry 49962) carries **both**
lines, caps at 0, each drawn from the GRPO. So include them: the invoice total
stays right and the GRPO closes fully.

## 5. Running a pile: the gate must be run TWICE

- **Broad pass, once, up front** — pull all drafts + posted invoices and match
  offline on normalised refs (strip punctuation, casefold, substring, party+total).
  Catches format variants an exact remote filter returns nothing for. Do **not**
  key on the longest digit-run: on `KPP/2026-27/1832` that is the year `2026` and
  it matches the vendor's entire history. Drop year-shaped runs, take the last.
- **Narrow pass, live, seconds before each POST.** This is not redundant. On
  2026-08-26 draft 55302 (SSY `26-27/1489`, ₹1,83,538) was created from **another
  fleet box under the same USER39 login** at 15:12 — after the broad snapshot,
  before the write. Only the narrow check caught it.

**Files are not invoices.** Of 22 scans, one was `TAX INVOICE (Page 2)` of another
(Babaji `3231/2026-27` — the second page carries only totals and looks like a
complete bill with a missing stamp) and one was already entered. 22 files = 20
invoices. Assemble multi-page bills into ONE pdf for the attachment:

```python
ims[0].save(pdf,'PDF',resolution=200.0,save_all=True,append_images=ims[1:])
```

**Re-derive each item's identity from its filename**, never from what a subagent
reports about itself — one mislabelled Pioneer Pet as another slot's number.

## 6. TDS: the threshold, and the trap under it (C-0036, C-0037)

> **2026-09-17: TDS is set by `jivo-tds` (`tds.py apply` before sending, `tds.py check`
> after).** Do not patch a WT code by hand as shown below — this section is background.

194Q deducts 0.1% only once purchases from that **seller** pass **₹50 lakh in the
financial year** — and **SAP does not enforce it**: set `WTCode 1031` and SAP
deducts regardless. The judgment is human, made before the code goes on.

**The seller is a PAN, not a CardCode.** Aggregate every card sharing
`CRD7.TaxId0` first. TPAC has two Oil cards on PAN `AAGCT4816J` — VENDA000937
(₹28.73 L) and VENDA000939 (₹37.26 L) — each under ₹50 lakh, together
**₹65,99,306**, over since 2026-07-13.

```bash
# FY-to-date by PAN, the only correct basis
hana-sql 'SELECT t."TaxId0", COUNT(DISTINCT p."CardCode") AS CARDS,
  ROUND(SUM(p."DocTotal"-p."VatSum"),0) AS TAXABLE_FYTD, ROUND(SUM(p."WTSum"),0) AS TDS
  FROM "JIVO_OIL_HANADB"."OPCH" p
  JOIN (SELECT DISTINCT "CardCode","TaxId0" FROM "JIVO_OIL_HANADB"."CRD7"
        WHERE "TaxId0" IS NOT NULL) t ON t."CardCode"=p."CardCode"
  WHERE p."DocDate">=''2026-04-01'' AND p."CANCELED"=''N'' GROUP BY t."TaxId0"'
```

Set only the code and let SAP compute the base and amount — do not write a figure
you calculated:

```bash
sapb1 patch "Drafts(<DocEntry>)" \
  --data '{"WithholdingTaxDataCollection":[{"WTCode":"1031"}]}' --yes
```

Shape on all 18 recent posted invoices of the over-threshold vendors: `WTCode
1031`, `Rate 0.1`, `Category I`, `WithholdingType V`, base = Σ `LineTotal` net of
GST, amount rounded to the rupee. **DocTotal drops by the TDS** — that is correct
and matches precedent exactly (55317 landed on ₹2,01,211, identical to SNP-0691).

**A draft already `WddStatus 'W'` can still be patched** — the approval request,
attachment and base links all survive. Verified on all 7.

**A bill dated in the previous FY but posted in this one** keeps the previous
year's threshold question. TPAC invoices `HAR2/25-26/3334` and `/2710` (TaxDate
Mar-26 and Jan-26, posted Apr/May-26) were correctly deducted because TPAC did
₹1.09 Cr in FY25-26. Which FY such a document belongs to is a question for the
CA, not for this skill.

## 7. `readback.py` cries wolf on two whole classes

`⚠ quantity X ≠ paper Y` on any bottle+cap GRPO (see §4) and `⚠ TDS is 0 but the
vendor is TDS-liable` on any vendor under the ₹50 lakh threshold (see §6). Both
are expected on correct documents. Report them as notes, never as defects — a
check that flags known-good work teaches everyone to ignore the channel.
