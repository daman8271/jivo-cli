---
name: jivo-bev-freight-grpo
description: Use when a transporter's consolidated freight bill / invoice book / bilty summary arrives for JIVO BEVERAGES (water, drinks) and freight GRPOs must be raised in SAP B1 — "make the GRPO for this bill", "ATS-402", "Arnav bill", a scanned bilty-summary table, or a transporter workbook mailed to logistics@jivo.in. Handles a whole bill at once, from one consolidated sheet, without the individual bilty scans. Also use to check whether a bilty is already keyed. NOT for Oil freight (use jivo-oil-freight-grpo) and NOT for a bill made out to JIVO MART (jivo-mart-freight-grpo) — all three books use different templates and not for the A/P invoice that copies these GRPOs (Transport-Bill-Playbook).
---

# Beverages freight GRPO from a transporter's consolidated bill

> 🔴 **ATTACHMENT RULE — COPY TO TARGET DOCUMENT = YES, on every file (Daman, 16 Sept 2026 · C-0090).**
> Whatever this skill attaches — to a draft, GRPO, A/P, credit memo, payment, JV, A/R, anything —
> every `Attachments2` line gets **`CopyToTargetDoc = "tYES"`** (the "Copy to Target Document"
> tick). An API upload lands **`tNO`** by default, so the scan does NOT follow the document when
> it is copied onward (GRPO → A/P, draft → posted). Set it in the SAME PATCH as the Approve stamp,
> **in all three books**, before pointing the document at the row:
> - Oil / Bev: `{"AbsoluteEntry":N,"LineNum":1,"U_CHK":<KB>,"U_CHK2":"OK","CopyToTargetDoc":"tYES"}`
> - Mart (no `U_CHK` columns): `{"AbsoluteEntry":N,"LineNum":1,"CopyToTargetDoc":"tYES"}`
>
> One object per line (line 2, 3 … too). Read back `Attachments2(N)`: every line must show
> `"CopyToTargetDoc": "tYES"` — if any shows `tNO`, the entry is not done. Proven live 16 Sept on
> Oil 177765/177767, Mart 59273, Bev 43223 (HTTP 204, stamp kept).

Internal skill. Built 2026-08-27 on ARNAV bill **ATS-402** — 44 bilties, ₹3,12,135,
drafts **15671–15714** — approved by Daman as "a fresh approach" and taught through
by him the same evening.

**The point of this skill: for Beverages you do not need the bilty scans.** The
transporter's consolidated bill gives bilty → invoice → destination → freight, and SAP
plus the emailed AR invoice supplies everything else. The classic three-paper method
([[GRPO-Playbook]] §4A) is an Oil method; Beverages collapses to one paper + SAP.

---

## 0 · Before anything: is this even Beverages?

**Read the company off the consignees, never off the bilty number.** A transporter runs
**one bilty book across all three JIVO companies**, so numbers interleave — ATS-402's
7322–7376 are Beverages while 7325/7339/7340/7351 in the same range are Oil.

```bash
# take any 3-4 invoice numbers off the bill and find which book they live in
for db in JIVO_OIL_HANADB JIVO_MART_HANADB JIVO_BEVERAGES_HANADB; do
  hana-sql/hana-sql "SELECT '$db' DB,\"DocNum\",\"CardName\" FROM \"$db\".\"OINV\" WHERE \"DocNum\" IN (…)"
done
```

Also confirm the vendor: **the same transporter has a different CardCode per book.**
ARNAV = `VENDA000948` in Bev, `VENDA000956` in Oil. Getting this wrong puts the whole
bill in the wrong company and nothing downstream will catch it.

## 1 · Get the bill as data, not as a photo

The operator will hand you a scan. **The transporter also mails the workbook** — use that.

```bash
mail-cli/jmail search --text "<any invoice no off the bill>" --since <date> --with-attachments
mail-cli/jmail pull <uid> --out ./mail --types ''     # --types '' — the default skips .xlsx
```

The **sheet name inside the workbook is the bill number** (`ATS:402` → sheet `402`).
On ATS-402 the OCR of the scan matched the workbook on **396 of 396 cells**, so the scan
is readable — but read the xlsx anyway and keep the scan for the operator's eyes.

Flatten it to a 10-column TSV, one row per bilty, no header:

```
srl  bilty_date(YYYY-MM-DD)  bilty  invoice_cell  weight_kg  destination  to  labour  freight  total
```

**`invoice_cell` keeps the slash notation verbatim.** `626088047/054` is **two**
invoices — the suffix replaces the last N digits of the base, so `626088047` +
`626088054`. Confirmed by Daman, and by SAP: every slash-pair on ATS-402 landed on the
same consignee as its base.

Sanity-check the transcription before going further: every row's
`labour + freight = total`, and the three column sums must hit the printed footer.

## 2 · Build the payloads

```bash
python3 .claude/skills/jivo-bev-freight-grpo/bin/build.py <bill.tsv> \
    --vendor VENDA000948 --series <month series> --out payloads
```

It reads SAP for the invoice date, consignee, ship-to state and litres, applies every
rule in §3, refuses any bilty already posted or drafted, and prints a check report.
It writes **nothing** to SAP. It fails loudly if the payload total does not tie to the
bill. `--ignore-existing` rebuilds over bilties already in SAP (only after a delete).

Then preview one, send one, read it back, and only then send the rest:

```bash
cd sap-b1/cli && eval "export $(grep -v '^#' user19-bev.env | grep -v '^$' | xargs)"
./sapb1 draft grpo --dry-run  --data-file payloads/<first>.json     # show the operator
./sapb1 draft grpo --data-file payloads/<first>.json --yes --json   # send ONE
# read it back out of ODRF/DRF1, confirm the shape, then loop the rest
```

`user19-bev.env` is GURCHARAN, the transport desk. → [[user19-gurcharan-grpo-login]]

## 3 · The Beverages template — every field, and where it comes from

Header:

| Field | Value |
|---|---|
| `CardCode` | the transporter **in the Bev book** |
| `DocType` | `dDocument_Service` |
| `Series` | the month's Bev GRPO series — Aug-26 = **`2481`** (`GRPO0826`) |
| `NumAtCard` | **the bilty number**, nothing else |
| `DocDate` = `TaxDate` = `DocDueDate` | **the bilty date** off the bill |
| `BPL_IDAssignedToInvoice` | `2` |
| `DocumentSubType` | `bod_None` |
| `Comments` | `BILTY NO <n>` |

One line per invoice on the bilty:

| Field | Value | Where from |
|---|---|---|
| `AccountCode` | `5670001` | constant |
| `ItemDescription` | **`WATER`** | **water AND drinks both take `WATER`** (Daman 2026-08-27). Oil takes `EDIBLE OIL` |
| `LineTotal` | the invoice's share of the bill's **TOTAL** (freight + labour as one figure) | §4 |
| `TaxCode` | **`RIGST@5`** for a Delhi transporter | §5 |
| `LocationCode` | `2` | C-0025 |
| `SACEntry` | **`3`** = SAC `996812` freight | **constant in Bev** — 2,406/2,406 ARNAV lines. Oil's 2-vs-40 split (C-0049) does not apply |
| `SalesPersonCode` | `3` | |
| `CostingCode` Dim1 | the invoice's **dominant Product Category** — in practice always `WATER` | 50/50 on ATS-402, 393/400 on precedent |
| `CostingCode2` Dim2 | **the month of the INVOICE date**, `MM-YYYY` | Daman: "invoice date is the factory month". Holds 2,100/2,334. **Not the bilty month** — 12 of ATS-402's 50 lines are `07-2026` under an August bilty |
| `CostingCode3` Dim3 | `Del Bkhp` | 100% |
| `CostingCode5` Dim5 | **the state of the SHIP-TO address on the AR invoice** | §6 |
| `WTLiable` | `tNO` | a GRPO never deducts TDS (C-0039) |
| `U_BilltyNumber` / `U_BiltyDate` | bilty no / bilty date | |
| `U_ARNO` | the AR invoice number | off the bill |
| `U_CardCode` | the invoice's **bill-to** CardCode | §6 |
| `U_Sub_Account` | **`SALES`** for an outside customer · **`BST`** when the invoice is billed to JIVO WELLNESS or JIVO MART — per line, off `U_ARNO` (**C-0063**). `build.py` uses the **Beverages book's** card list; CardCodes differ per book | |
| `U_Remarks` | `BILTY NO <n>` | |
| `U_UNE_LTS` | litres on that invoice | §4 |
| `U_UNE_CALI` / `U_UNE_CUNT` / `U_UNE_SCHI` | `Y` / `Y` / `N` | |

## 4 · Litres — in Beverages you CAN compute them

**This is the one place Beverages departs from C-0047.** In Oil the litre figure must be
read off the AR invoice PDF because `OITM` volume fields are NULL and packs are sold by
weight. In Beverages every SKU is a bottle with its volume printed in the item name and
quantity in PCS (C-0001), so:

> **litres = Σ (pack volume from the item name × quantity)**, and a
> `GIFT PACK 10 BOTTLES WHEAT GRASS` counts as **2.0 L** (10 × 200 ML).

Measured: reproduces the keyed `U_UNE_LTS` on **480 of 497** historical Bev ARNAV lines
(96.6%), and matched the emailed PDF on **8 of 8** checked invoices. Two of the residual
misses are a transposition on bilty 7275 where the computed figure is the correct one.

`OITM.U_Sub_Group` reproduces the PDF's Product Category exactly (`WATER` / `DRINKS` /
`GIFT PACK`), which is where Dim1 comes from.

**Split the bill's TOTAL across the invoices litre-wise, last line absorbing the
rounding** (C-0048), so the document ties to the bilty to the rupee.

### Verify against the PDF for anything that isn't plain water

The mailbox is the authority; compute is the fast path. Pull the PDF for every invoice
carrying a `DRINKS` or `GIFT PACK` line — that is where the historical misses cluster.

**Beverages AR invoices come from `beverages@jivo.in`**, not `ppc.ho@jivo.in` (that is
the Oil path).

> **⚠ Read the Product Category block by its HEADER, never by position.** Beverages prints
> it in **two different column orders** — `Category | Gross Wt | Liter` *and*
> `Category | Litre | Gross Wt` — and sometimes with no `Total` row at all. Taking the
> first number blind gives you the weight: on invoice `626088122` that is **53,898**
> instead of **2,892**, an 18× error that would go straight into `U_UNE_LTS` and drive
> the whole freight split.

## 5 · Tax — the transporter's state, never the destination

**C-0049.** The reverse-charge code follows the **transporter's own GSTIN state** against
JIVO's Haryana (`06`) branch:

- ARNAV `07ACBPY4022H1ZO` → 07 Delhi → inter-state → **`RIGST@5`**
- a Haryana (`06`) transporter → intra-state → **`GST05R`**

ATS-402 proves why the destination is irrelevant: 41 lines DL, 5 UP, 4 HR — all
`RIGST@5`. Reverse charge means header `VatSum` = **0**; the line still carries the 5%
(₹15,606.75 on ATS-402) because JIVO self-assesses and pays the government, not the
transporter. `DocTotal` stays at the freight figure.

Bev ARNAV was `IGST@5` (forward charge) until 2026-03-07 and `RIGST@5` since.

> **Gap to know:** C-0049 says disambiguate a transporter by PAN. **You cannot do that in
> Beverages** — `OCRD.LicTradNum` and `CRD7.TaxId0`/`TaxId11` are NULL on the ARNAV card.
> The tax decision rests on the GSTIN printed on the paper with nothing in SAP to check
> it against. If two same-name cards ever appear, stop and ask.

## 6 · Reading the AR invoice — what the paper gives you (Daman, 2026-08-27)

| On the invoice | Field |
|---|---|
| barcode label, e.g. `CUSTA001220 - GT - PAN INDIA` | the customer code → `U_CardCode` |
| header block, e.g. `(Only For Beverages)` | which company book (C-0030) |
| `Invoice Date: 10/08/2026` | **the factory month** → Dim2 `08-2026` |
| **Ship to** → state in the address | **Dim5** |
| page 2 Product Category → **Liter** | `U_UNE_LTS` |
| the rubber stamp | the receiving party's — **not keyed**, varies |

**Dim5 is the SHIP-TO state, not the transporter's Destination column and not the
bill-to state.** On ATS-402 the two agreed on all 50 lines, so a Destination-based
answer looked right — it was right by luck. `build.py` takes the ship-to and flags any
row where the transporter's column disagrees.

**A ship-to name that isn't the customer is normal.** ATS-402 bilty 7368 says
`THE KALGIDHAR` on the paper; invoice `626088100` is billed to `ILAHI CO.`
(`CUSTA000844`) with `ShipToCode` = `THE KALGIDHAR SOCIETY RAJOURI GARDEN F3`. The
transporter writes the delivery point. **`U_CardCode` is the bill-to.**

## 7 · Checks that actually catch things

- **The three column sums must hit the printed footer**, and every row's
  `labour + freight = total`.
- **Payload total must tie to the bill total** to the rupee. `build.py` exits non-zero if not.
- **kg/L from the transporter's own weight column against the computed litres** —
  bottled water lands **1.00–1.15**. On ATS-402, 43 of 44 did. This is an independent
  check the build never used, and it substitutes for [[GRPO-Playbook]]'s box-count test
  when you have no bilty scans.
- **Every slash-pair should land on the same consignee** as its base invoice.
- **Never key a bilty twice** — `build.py` checks `OPDN` and `ODRF` first.

## 8 · Read it back, then stop

```bash
hana-sql/hana-sql 'SELECT D."NumAtCard",D."DocEntry",D."DocTotal",D."VatSum",D."WTSum",
  D."Series",D."BPLId",D."DocType",COUNT(L."LineNum"),SUM(L."U_UNE_LTS")
  FROM "JIVO_BEVERAGES_HANADB"."ODRF" D JOIN "JIVO_BEVERAGES_HANADB"."DRF1" L
   ON L."DocEntry"=D."DocEntry" WHERE D."ObjType"=''20'' AND D."DocEntry">=<first>
  GROUP BY …'
```

- [ ] count of drafts = rows on the bill
- [ ] Σ `DocTotal` = the bill footer
- [ ] `VatSum` 0 and `WTSum` 0 on every header
- [ ] Series / BPL / DocType right on every one
- [ ] Σ `U_UNE_LTS` = the litres you computed

**Then hand over the DocEntry list and stop.** A human presses Add in the SAP client —
and on a GRPO that **Add posts it live**; there is no approver step (**C-0044**, unlike
an A/P invoice). Never run `sapb1 add-draft` on these.

**The drafts carry no attachment.** [[GRPO-Playbook]] §9 wants the bilty page on each
one, filenamed by bilty number. Say so explicitly when you hand over.

## 9 · What comes next

The A/P invoice against the transporter's bill copies these GRPOs — that is
[[Transport-Bill-Playbook]], and it is a copy job once the GRPOs are right.

---

Related: [[GRPO-Playbook]], [[Transport-Bill-Playbook]], [[jivo-add-and-new]],
corrections C-0025, C-0030, C-0033, C-0035, C-0038, C-0039, C-0044, C-0045, C-0047,
C-0048, C-0049.
