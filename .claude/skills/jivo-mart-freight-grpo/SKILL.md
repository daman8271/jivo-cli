---
name: jivo-mart-freight-grpo
description: Use when a transporter's freight bill / LR / bilty arrives billed to JIVO MART PVT LTD and freight GRPOs must be raised in SAP B1 — "make the GRPO for this bill", "NCR-349", a PICK & SHIP invoice, an LR summary addressed to Jivo Mart. Read the BILL-TO and the sale invoice numbers to decide the book: Mart invoice numbers run in a 7-series (707260200), Oil in 626xxxxxx. Also use to check whether an LR is already keyed. NOT for Oil freight (jivo-oil-freight-grpo) and NOT for Beverages (jivo-bev-freight-grpo) — all three books use different templates. Not for the A/P invoice that copies these GRPOs (Transport-Bill-Playbook).
---

# Mart freight GRPO from a transporter's bill

Internal skill. Built 2026-08-31 on PICK & SHIP invoice **NCR-349** (LR `NCR-3226`,
₹45,091 + IGST 18 % = ₹53,207.38 → draft **40070**), cloned from Mart's own posted
GRPO **`13733`** which the scripts here reproduce byte-for-byte.

**Mart is the third template, and it is not a variation of Oil — it is a different
document.** The tax is *on* the paper, the dimensions differ, and `PDN1` does not even
have the same columns.

| | Oil | Beverages | **Mart** |
|---|---|---|---|
| Tax | 5 % **reverse** (`RIGST@5` / `GST05R`), `VatSum` **0** | 5 % reverse | **forward charge, e.g. `IGST@18` — tax sits ON the document** |
| `DocTotal` | freight only | freight only | **freight + tax** |
| Dim3 | `Del Bkhp` | `Del Bkhp` | **`SUPPLY-C`** |
| Dim4 | empty | empty | **set** (`SC-BHKR` ex-Bhakarpur, `SC-WARH` ex-warehouse) |
| `ItemDescription` | `EDIBLE OIL` | `WATER` | **`EDIBLE OIL`** |
| `SalesPersonCode` | 115 | 3 | **36** |
| `U_Remarks` | `BILTY NO <n>` | `BILTY NO <n>` | **the literal `Y`** |
| `WtLiable` | `tNO` | `tNO` | **`tYES`** — but `WTSum` is still 0 (C-0039 holds) |
| `PDN1` UDFs | has `U_BiltyDate` | has `U_BiltyDate` | **no `U_BiltyDate` column at all** |
| Freight split | pro-rata on litres, 2 dp | pro-rata on litres | pro-rata on litres, **whole rupees** |

---

## 0 · Which book, and is it already keyed?

**Read the BILL-TO and then prove it from the invoice numbers.** `JIVO MART PVT LTD`
(GSTIN `07AAFCJ4102J1ZS`, Mayapuri Delhi) on the header is the first signal; Mart sale
invoices run in a **7-series** (`707260200`, `706260939`) against Oil's `626…`.

```bash
for db in JIVO_OIL_HANADB JIVO_MART_HANADB JIVO_BEVERAGES_HANADB; do
  hana-sql/hana-sql -env connections/hana-office-bridge.env \
    "SELECT '$db' DB,\"DocNum\",\"CardName\" FROM \"$db\".\"OINV\" WHERE \"DocNum\" IN (…)"
done
```

**Every invoice on the bill, not a sample** — one bill can span two companies (**C-0061**).
The transporter has a different CardCode per book: PICK & SHIP is `VENDA001661` Oil /
**`VENDA001018` Mart** / `VENDA001346` Bev.

**Read the handwriting before you build.** `NCR-349` carried a hand-written **"GRPO OK"**
beside the invoice number — and it was true: GRPO `13733` was already posted for that LR.
A mark like that is a fact about the document (**C-0027**: handwriting is data). Check it:

```sql
SELECT T0."DocEntry",T0."DocNum",T0."DocTotal",T1."U_BilltyNumber"
  FROM "JIVO_MART_HANADB"."OPDN" T0 JOIN "JIVO_MART_HANADB"."PDN1" T1
    ON T0."DocEntry"=T1."DocEntry" WHERE T1."U_BilltyNumber" IN (…);
-- and the same against ODRF/DRF1 for drafts
```

## 1 · Branch, Location and sub-budget come off OUR address — never from a clone

**C-0064. Read the `To,` block on the transporter's bill: the address they billed US at
decides three fields together.**

| Our bill-to address | Branch `BPL_IDAssignedToInvoice` | **Location** = place of supply | Dim4 sub-budget |
|---|---|---|---|
| **Delhi** — `07AAFCJ4102J1ZS`, Mayapuri | **1** DELHI | **1** DELHI | **`SC-WARH`** |
| **Haryana** — `06AAFCJ4102J1ZU`, Bhakarpur Sonipat | **2** HARYANA | **2** HARYANA | **`SC-BHKR`** |

`LocationCode` **is** the place of supply — `OLCT` carries the GSTIN, so the location is
what puts JIVO's own GSTIN on the document. Verify both tables rather than trusting this
table, because the branch list is long (20 rows, incl. BSU/TPT sets):

```sql
SELECT "BPLId","BPLName","State","TaxIdNum" FROM "JIVO_MART_HANADB"."OBPL";
SELECT "Code","Location","State","GSTRegnNo" FROM "JIVO_MART_HANADB"."OLCT";
```

> **This is exactly where cloning bites.** 8 of 9 posted PICK & SHIP Mart GRPOs are
> BPL 1 / Location 1 / `SC-WARH`. The single outlier, `13733`, is BPL 2 / 2 / `SC-BHKR` —
> and it is the most recent, so "copy the vendor's last GRPO" reproduces the one wrong
> document. It did, on the first pass at `NCR-349` (draft `40070`, deleted and rebuilt as
> `40072`). **These three fields are read off the paper; only the rest are cloned.**

**MART ONLY.** Oil sits on BPL 2 with Dim4 empty; Beverages on BPL 2. Nothing here
transfers to the other two books.

## 1A · The tax code is DERIVED, never cloned (C-0049 + C-0065)

**Two independent reads decide it, and neither is the destination.**

1. **Inter or intra** — the **transporter's own GSTIN state**, printed on their bill,
   against the **branch state you just chose in §1**. In Mart that is Delhi `07` or
   Haryana `06`, not the fixed `06` C-0049 assumes for Oil.
   **SAP cannot help you here: `OCRD.LicTradNum` is NULL on every Mart transporter card.**
   Read the GSTIN off the paper.
2. **Forward or reverse** — off the paper too. A GTA bill saying *"GST payable by
   consignee"* / *"RCM"* is reverse charge at 5 %; a logistics bill that prints its own
   GST line and adds it to the total is forward charge, usually 18 %.

| | Forward charge | Reverse charge |
|---|---|---|
| **Inter**-state | **`IGST@18`** (or `IGST@5`) | **`RIGST@5`** · `RISGT@18` at 18 |
| **Intra**-state | **`CG+SG@18`** | **`GST05R`** · `RCGSG@18` at 18 |

Forward charge puts the tax **on** the document — `VatSum` is the bill's tax and
`DocTotal` its Net Amount. Reverse charge leaves `VatSum` 0 and `DocTotal` at the freight.

`NCR-349`: PICK & SHIP `09AAQCP4145A1ZF` = **UP (09)** vs branch **Delhi (07)** →
inter-state, and the bill prints *IGST @ 18.00 %* → **`IGST@18`**.

> The same transporter bills from different state offices, so **do not assume last
> month's code still holds** — PICK & SHIP is `09` (Lucknow) on this bill.

### The rest you do clone

Salesperson and account come from that transporter's last Mart GRPO.

```sql
SELECT T0."DocNum",T0."Series",T0."BPLId",T0."SlpCode",T1."AcctCode",T1."TaxCode",
       T1."OcrCode3",T1."OcrCode4",T1."LocCode",T1."U_Sub_Account",T1."U_Remarks"
  FROM "JIVO_MART_HANADB"."OPDN" T0 JOIN "JIVO_MART_HANADB"."PDN1" T1
    ON T0."DocEntry"=T1."DocEntry"
 WHERE T0."CardCode"='<vendor>' AND T0."CANCELED"='N' ORDER BY T0."DocDate" DESC;
```

(`BPLId`, `LocCode` and Dim4 are **not** in that list — see the table above.)

## 2 · Litres and Dim1 — computed, not read

**This is where Mart departs from Oil.** C-0060 says read the printed `Total` off the AR
invoice PDF — but Mart's invoice PDFs are not reliably in any mailbox we can reach. So:

```bash
.claude/skills/jivo-mart-freight-grpo/bin/litres_from_sap.py 707260200 706260939 -o litres.json
```

> **litres = Σ (pack volume from the item name × Quantity)**, Quantity in PIECES (C-0001);
> category = `OITM.U_Sub_Group`, which is what the invoice's Product Category block prints.

Two things that decide the answer:

- **A `+` combo is one piece of the summed volume.** `COLD PRESS 1 LTR +1 LTR COMBO 10
  SETS PLAIN` at qty 40 is **80 L**, not 40. Without that, `706260939` computes 2,096
  instead of 2,176 and the whole freight split shifts.
- **Dim1 is the biggest category TOTAL** (**C-0058**), summed across pack sizes:
  `706260939` = MUSTARD 1,484 · OLIVE 436 · CANOLA 160 · RICE BRAN 96 → **MUSTARD**.

**⚠ Validated on ONE document.** Always check against the transporter's weight column —
2,780 kg ÷ 2,776 L = **1.0014 kg/L**, and bottled oil should land ≈ 0.90–1.05. A miss
there means the parse is wrong. If a line has no parseable pack size the script stops.

## 3 · Build, preview, send

```bash
.claude/skills/jivo-mart-freight-grpo/bin/build_drafts.py bill.json litres.json customers.json
cd sap-b1/cli
./sapb1 draft grpo --company JIVO_MART_HANADB --dry-run --data "$(cat draft.json)"
./sapb1 draft grpo --company JIVO_MART_HANADB --yes     --data "$(cat draft.json)"
```

`customers.json` is `{invoice: CardCode}` out of `OINV`; it also decides `SALES` vs
**`BST`** (**C-0063** — JIVO WELLNESS or JIVO MART as the customer). **CardCodes are per
book**: `CUSTA000877` is JIVO MART - RJ here but M/S FOOD MONDE in Oil, so the builder
carries Mart's own list.

**The tax is on the document.** The bill's *Sub Total* is what the lines must add to; the
*Net Amount* is what `DocTotal` becomes. On `NCR-349`: lines 9,746 + 35,345 = **45,091**
(Sub Total ✓), IGST 18 % = **8,116.38** ✓, `DocTotal` **53,207** ✓. All the accessorial
columns — Hamali/loading, Other, Docket, FOV, FSC — are already inside that Sub Total;
they are not separate lines (and cf. **C-0062**: labour rides with the freight).

## 4 · Read it back, then STOP

```sql
SELECT T0."DocEntry",T0."NumAtCard",T0."DocTotal",T0."VatSum",T0."WTSum",T0."Series",
       T1."U_ARNO",T1."U_UNE_LTS",T1."LineTotal",T1."VatSum",T1."TaxCode",T1."OcrCode",
       T1."OcrCode2",T1."OcrCode3",T1."OcrCode4",T1."OcrCode5",T1."U_Sub_Account"
  FROM "JIVO_MART_HANADB"."ODRF" T0 JOIN "JIVO_MART_HANADB"."DRF1" T1
    ON T0."DocEntry"=T1."DocEntry" WHERE T0."DocEntry"=<n>;
```

- [ ] Σ line totals = the bill's **Sub Total**; `DocTotal` = its **Net Amount**
- [ ] header `VatSum` = the bill's tax; `WTSum` **0**
- [ ] Branch + Location match **our** bill-to address, and Dim4 matches them (C-0064)
- [ ] Tax code derived from the transporter's GSTIN vs that branch (C-0049/C-0065), not cloned
- [ ] Dim3 `SUPPLY-C`, Dim5 = destination state
- [ ] `U_Sub_Account` right per line, `U_Remarks` = `Y`

**Never run `sapb1 add-draft` on a freight GRPO** — no Always approval template exists for
TransType 20, so Add posts it live with no approver (**C-0044**). A human presses Add.

**No attachment.** The GRPO wants the **LR/bilty** page, not the transporter's bill
(**C-0026**) — say so when handing over.

Note the login: from this Mac drafts are made by **`manager`** and land in *its* Document
Drafts list. Mart's own freight GRPOs are keyed by **`USER19` GURCHARAN/RAJENDER**.

---

Related: [[jivo-oil-freight-grpo]], [[jivo-bev-freight-grpo]], [[GRPO-Playbook]],
[[Transport-Bill-Playbook]]. Corrections **C-0058** (Dim1 = biggest category total),
**C-0059** (packaging-only), **C-0061** (a bill can span two companies), **C-0062**
(freight + labour), **C-0063** (BST), **C-0064** (branch/location/sub-budget off our
address), **C-0049 + C-0065** (tax from the transporter's GSTIN vs that branch),
C-0001, C-0025, C-0026, C-0027, C-0039, C-0044.
