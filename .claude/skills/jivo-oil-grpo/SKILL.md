---
name: jivo-oil-grpo
description: Use when a tanker of LOOSE / BULK oil arrives and the goods receipt must be keyed in SAP B1 — the operator hands over the supplier's tax invoice (REFINED SOYABEAN / RICE BRAN / PALM / MUSTARD OIL, quantity in KG, a gate-in stamp on it) plus the JIVO purchase order it came against. Daman calls this "oil GRPO". Entered from USER21. NOT the transporter's freight bill — that is jivo-oil-freight-grpo (a service GRPO keyed off a bilty, no PO). NOT the A/P invoice that later copies this GRPO (jivo-ap-draft).
---

# Oil GRPO — a tanker of bulk oil, from the supplier's invoice + the PO

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

Internal skill. Built 2026-09-09 on **ARORA AGRI `AABV/26-27/308`** — 42,200 kg
refined soyabean against PO **220826145**, gate entry 87 — taught through by Daman
the same evening. The draft this skill produces was written blind and came out
**field-for-field identical** to the one an operator had keyed by hand in the SAP B1
client two hours earlier (56663 vs 56686): same quantity, same rate to four decimals,
same `PackageQuantity`, same comments string. That match is the reason the skill exists.

**This is a stock GRPO against an open PO.** It moves 40-odd tonnes of oil into
`BH-GJ` when a human presses Add. Everything except five numbers is cloned from the
PO — the whole job is getting those five right.

---

## The five numbers, and the only paper each one lives on

| # | Field | Where it comes from | The trap |
|---|---|---|---|
| 1 | `NumAtCard` | the **supplier invoice number** printed at the top of the invoice (`AABV/26-27/308`) | not the e-way bill, not the Buyer's Order No |
| 2 | line `Quantity` | invoice quantity **minus the ball-pen shortage** written on the invoice face | **this is the one people get wrong** — see below |
| 3 | `DocDate` | the **gate-in stamp** date (`Date 9/9/26` in JIVO's rubber stamp) | never today, never the invoice date |
| 4 | `TaxDate` | the **supplier's invoice date** (`4-Sep-26`) | C-0017 in reverse: DocDate is gate-in, TaxDate is the vendor's |
| 5 | line `UnitPrice` | **taxable value ÷ the GRPO quantity**, 4 dp | never the PO rate, never the invoice's printed rate |

Everything else — item, warehouse, branch, tax code, HSN, Dim1, account — comes
across from the PO by itself. Do not type any of it.

### 2 is the trap: the quantity shrinks, the money does not

The tanker is weighed at the gate and comes up short. A JIVO checker writes the
shortage on the invoice face in ball pen — `Quantity Check: Shot – 110 kg` — and
stamps the **net** figure into the gate stamp's Qty box.

- GRPO `Quantity` = **net** (invoice 42,200 kg − 110 kg = 42,090 kg = **42.09 MTS**)
- Taxable value stays the **full printed amount** — ₹62,87,800, not reduced
- so the rate rises: 6,287,800 ÷ 42.09 = **149,389.4037** per MT, against a PO rate of 149,000

JIVO pays for what the supplier billed and receives what actually landed; the
difference is settled later, not here. **Never "fix" the amount to match the quantity.**

Cross-check the two independent sources before writing: the ball-pen arithmetic
(gross − shortage) must equal the number in the gate stamp's Qty box. If they
disagree, stop and ask — one of them was misread.

### Units: the invoice is in KG, the PO is in MTS

`RM0000025` and its siblings are stocked in **MTS**. Divide by 1000, three decimals.
`UnitsOfMeasurment` on the line is **1098.9** (litres per purchase-MT, C-0050) and SAP
fills `InventoryQuantity` itself — don't touch either.

`PackageQuantity` = **ceil(Quantity)** — 42.09 → 43, 40.5 → 41. Twelve consecutive
hand-keyed GRPOs on this vendor do exactly this; it is the tanker count, not a rounding.

---

## 1 · Pre-check — reads only, and it is not optional

```bash
cd ~/jivo-cli && set -a && . sap-b1/cli/user21-oil.env && set +a
python3 .claude/skills/jivo-oil-grpo/bin/precheck.py \
  --invoice "AABV/26-27/308" --po 220826145 --bilty 8904 \
  --gross-kg 42200 --short-kg 110 --taxable 6287800
```

It prints, in order: whether the invoice or the bilty is **already** on a draft or a
posted GRPO in any book; the PO with its branch, series, warehouse, Dim1 and how much
is still open; the last three GRPOs on that vendor (the template to clone); and the
arithmetic for §2 and §5 above.

**Read the whole duplicate section. All of it.** On the build day this skill's author
piped that query through `head -40`, missed draft **56663**, and wrote a second
identical GRPO for the same tanker. Two open GRPOs for one truck is 84 tonnes of oil
that never arrived. The script exists so that check is never eyeballed again.

USER21 has an Oil password only, so the Mart and Beverages passes will fail to log in.
The script says so out loud and refuses to call it "not found" (C-0073). For a bulk-oil
tanker that is fine — **the printed PO number decides the book** (the buyer GSTIN cannot;
Oil and Bev share `06AACCJ4223F1Z0`) — but say it out loud rather than implying a clean
three-book search.

## 2 · Attach both papers first — invoice AND PO, one row, two lines

Full recipe and its traps: `.claude/skills/jivo-ap-draft/reference/attachments-upload.md`.
Upload with `sapb1 attach` — it ticks Copy to Target Document on each line (C-0090), so the
bill follows this GRPO onto the A/P invoice, and stamps `U_CHK`/`U_CHK2` or SAP refuses the
draft with 1120025 (C-0082):

```bash
sap-b1/cli/sapb1 attach "$S/AABV-26-27-308.pdf" "$S/PO-220826145.pdf" --dry-run
sap-b1/cli/sapb1 attach "$S/AABV-26-27-308.pdf" "$S/PO-220826145.pdf" --yes
# → Attachments2 row <AE> — line 1 = the invoice, line 2 = the PO, both tYES, U_CHK2 OK
#   "AttachmentEntry": <AE>   <- put this in the draft
```

Name the files after what they are (`AABV-26-27-308.pdf`, `PO-220826145.pdf`) — that
name is what the operator sees on the share.

## 3 · The draft — dry-run then `--yes`, same turn (C-0087)

```json
{
  "CardCode": "VENDA001695",
  "DocDate":  "2026-09-09",          // gate-in stamp
  "DocDueDate": "2026-09-09",
  "TaxDate":  "2026-09-04",          // supplier's invoice date
  "NumAtCard": "AABV/26-27/308",
  "Series": 2478,                     // the CURRENT month's GRPO series — copy the last GRPO
  "BPL_IDAssignedToInvoice": 2,
  "Comments": "SOYABEAN Based On Purchase Orders 220826145. GATE ENTRY NO 87",
  "SalesPersonCode": 142,
  "ContactPersonCode": 6252,
  "AttachmentEntry": <AE>,
  "U_BilltyNumber": "8904",           // invoice header: Bill of Lading / LR-RR No
  "U_BiltyDate": "2026-09-04",        // = TaxDate
  "U_TransporterName": "R.K. TANKER SERVICE",   // invoice header: "Dispatched through"
  "U_VehicleNoM": "RJ47GA7522",       // invoice header: Motor Vehicle No
  "DocumentLines": [
    { "BaseType": 22, "BaseEntry": 13509, "BaseLine": 0,
      "Quantity": 42.09, "UnitPrice": 149389.4037, "PackageQuantity": 43 }
  ]
}
```

```bash
sap-b1/cli/sapb1 draft grpo --data-file $S/grpo.json --dry-run
sap-b1/cli/sapb1 draft grpo --data-file $S/grpo.json --yes
```

- `Comments` is a fixed shape: `<VARIETY> Based On Purchase Orders <PO DocNum>. GATE ENTRY NO <n>`.
  Variety is the PO's `Comments` / Dim1 (`SOYABEAN`, `RICE BRAN REFINED OIL` …), the gate
  entry number is the `G. No.` in the stamp.
- `BaseType 22 / BaseEntry <PO DocEntry> / BaseLine 0` is what pulls the item, warehouse,
  `LocationCode 2`, `CostingCode` (Dim1), `IGST@5`, `HSNEntry` and account `1103006` across.
  Set **UnitPrice**, never `LineTotal` — SAP recomputes the total from price × quantity.
- **No Dim2.** Bulk-oil GRPOs carry Dim1 only; C-0035 (Effective Month on every line) is
  an A/P-invoice rule and does not apply here. Twelve precedents have `CostingCode2` null.
- **No TDS.** `WTLiable` stays `tNO` — a GRPO never deducts (C-0039). 194Q is decided on
  the A/P invoice that copies this GRPO (C-0085).

## 4 · Read it back — the only proof

```bash
sap-b1/cli/sapb1 query Drafts --filter "DocEntry eq <N>" --json
```

`DocTotal` **must equal the total printed on the supplier's invoice** to the rupee
(₹66,02,190.00 = 6,287,800 × 1.05). If it does not, the quantity or the rate is wrong —
go back to §2, do not adjust the total.

Also confirm: `AttachmentEntry` set · `Quantity` = the gate stamp · `UoMCode` MTS ·
`InventoryQuantity` = Quantity × 1098.9 · `CostingCode` = the variety · `Series` = this
month's · `BPLName` FACTORY.

## 5 · Then STOP. The draft is the finish line.

**Never run `sapb1 add-draft` on a GRPO.** The template that routes this desk's GRPOs is
**query-based**, and SAP skips query-conditioned templates for API/DI Adds (C-0044): the
Add would decide no approval is needed and **post 40 tonnes into stock, unapproved**,
bypassing the approver entirely. `sapb1 post PurchaseDeliveryNotes` is off for the same
reason. Both are refusals to hold even if someone asks.

Hand back the draft number and say it is sitting in **Document Drafts**. A human presses
Add in the SAP B1 client — *that* is what fires the template.

### Who sees it, and where — measured in Oil, 2026-09-09

| | |
|---|---|
| **Document Drafts** | Both. Data ownership is not in play — `ODRF.OwnerCode` is NULL on these drafts, so nothing filters them by user. The window merely *defaults* to the logged-in user; the approver changes the **User** dropdown to the creator. In practice USER27 has Added 50 of USER21's GRPO drafts in two months. |
| **Approval Status Report** | Only after someone presses Add. A draft alone raises no `OWDD` row and reaches nobody's queue. |

**Template 59 `USER06 GJ1`** (remarks "GJ IMPORT") is the route for this desk:
originator **USER21 alone**, approver **USER06**, doc types 13/15/16/20/21, terms =
**query 450 "SPECIAL KULBEER VEERJI"**, which fires when the line warehouse is
`BH-GJ`, `BH-CRUDE`, `BH-LO` or `BH-EX`. Bulk oil lands in `BH-GJ`, so it always matches.

Check the live state of any draft with the pair — the draft's own flag and the request's
process flag, never the step row, which is not updated when a request is withdrawn:

```sql
SELECT d."DocEntry", d."DocNum", d."WddStatus",          -- '-' never submitted · W pending · Y approved · N rejected · C cancelled
       w."WddCode", w."Status" AS step, w."ProcesStat"   -- ProcesStat is the authority; "Status" can read W on a cancelled request
FROM "JIVO_OIL_HANADB"."ODRF" d
LEFT JOIN "JIVO_OIL_HANADB"."OWDD" w ON w."DraftEntry" = d."DocEntry" AND w."ObjType" = '20'
WHERE d."DocEntry" = <N>;
```

`ODRF.DataSource` tells you who made it: **`I`** = keyed in the SAP B1 client,
**`S`** = written through the Service Layer by this CLI.

Then, and only then, the A/P invoice against this GRPO is a separate job — `jivo-ap-draft`.

---

## Worked example — AABV/26-27/308, 2026-09-09

| | |
|---|---|
| supplier | ARORA AGRI BUSINESS VENTURES · `VENDA001695` · GSTIN 05 (Uttarakhand) |
| PO | 220826145 · DocEntry 13509 · 400 MTS SOYABEAN @ 149,000 · 177.123 MTS still open |
| invoice | `AABV/26-27/308` · 4-Sep-26 · 42,200 KG · taxable ₹62,87,800 · IGST 5% ₹3,14,390 · **₹66,02,190** |
| ball pen | `Shot – 110 kg` |
| gate stamp | G. No. **87** · 9/9/26 · **42090 kg** · RJ47GA7522 |
| bilty | LR 8904 · R.K. TANKER SERVICE |
| → GRPO | 42.09 MTS @ 149,389.4037 · PkgQty 43 · DocDate 09-09 · TaxDate 09-04 · DocTotal ₹66,02,190 ✓ |

Keyed independently by hand as draft **56663** and by this skill as **56686** — identical.
56686 was deleted as the duplicate.
