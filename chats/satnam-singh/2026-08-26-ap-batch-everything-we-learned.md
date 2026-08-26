# 2026-08-26 — 22-scan A/P batch: everything we learned

**For Satnam, and for any Claude that opens this repo.** Daman's instruction:
"send him all the things we learned". This is the complete record — what was done,
what is left, every technical trap, every process problem, and the honest cost.

Companion files: `HANDOVER-2026-08-26-AP-BATCH.md` (the job list) ·
`.claude/skills/jivo-ap-draft/reference/matching-and-batches.md` (the rules, in the
skill where they fire) · corrections **C-0035, C-0036, C-0037**.

---

## 1. What was done

**20 Oil A/P invoice drafts, ₹51,05,435 — all submitted, all sitting with BHAWANI.**

Drafts `55311-55329` + `55302`. Series 3684 (`HR_G0826`), branch 2 FACTORY, login
USER39, `bod_GSTTaxInvoice`. Every one: drawn from its GRPO (`BaseType 20`), the bill
attached as 2 files (operator's scan + the GRPO's own copy, both `U_CHK2='OK'`),
`CostingCode2='08-2026'` on every line, read back against the paper.

Submitted with `sapb1 add-draft` → approval requests **73096-73115**, template **103
`API AP AUTO (USER39)`**, `ODRF.WddStatus='W'`. **Nothing in the ledger** — verified
0 journal rows and 0 live invoices for all 20 refs.

**Approval is not posting.** After Bhawani approves, a human presses Add a second
time. As of 08-24 Oil had 78 approved A/P drafts sitting unposted, ₹87.55 lakh.

## 2. What is left — yours

**TDS on the four TPAC drafts.** Full commands in `HANDOVER-2026-08-26-AP-BATCH.md`.

| Draft | Vendor ref | Taxable ₹ | TDS ₹ |
|---|---|---|---|
| 55313 | 2606000894 | 1,27,932 | 128 |
| 55314 | 2606000893 | 1,22,460 | 122 |
| 55324 | 2606000855 | 58,110 | 58 |
| 55329 | 2606000921 | 2,14,500 | 215 |

Set the **code only**, let SAP compute the base and amount — never write a figure
you calculated:

```bash
./sapb1 patch "Drafts(55313)" --data '{"WithholdingTaxDataCollection":[{"WTCode":"1031"}]}' --yes
```

A draft already in approval patches fine — request, attachment and base links all
survive. Proven on 7 drafts. `DocTotal` drops by the TDS; that is correct.

---

## 3. Technical learnings

### 3.1 `PurchaseDeliveryNotes.NumAtCard` holds the VENDOR'S invoice number
The exact paper→GRPO key. Use it first; gate number, amount and date are only
corroboration. `precheck.py` still matches on gate/qty/total — do this yourself:
```bash
sapb1 query PurchaseDeliveryNotes --filter "contains(NumAtCard,'<bill no>')" \
  --select "DocEntry,DocNum,CardCode,CardName,NumAtCard,DocDate,DocTotal,DocumentStatus"
```
Two hits on one ref is a **finding** (a duplicate GRPO), not an ambiguity to resolve
by picking one.

### 3.2 Never match a vendor by name — take CardCode from the GRPO
`OCRD.FederalTaxID` is **empty for all 2,235 Oil vendors**, so there is no ID to match
on. Falling back to name similarity gave **TPAC PACKAGING → GTECH PACKAGING (0.80)**
and **PIONEER PET → HOSE EXPERT (0.60)**. Five bills, ₹13.9 lakh, and every other
check — totals, tax, branch, series — would have passed clean.

### 3.3 A GRPO-drawn line inherits Dim1 only (C-0035)
`CostingCode` (Variety) and `LocationCode` come down. **`CostingCode2`, `3`, `5`
arrive null.** Effective Month = the **DocDate's** month, `MM-YYYY`. Patchable after
the fact without disturbing totals, base links or attachments — proven on 20 drafts.

### 3.4 Bottles ship with caps at ₹0
The GRPO carries the closure at `UnitPrice 0`, so open qty is ~2× the paper and
`precheck` trips (`invoice qty 3750 ≠ GRPO open qty 7500`). **The money is the
reliable test** — matched to under ₹1.50 on all five that tripped. Posted precedent
(49962) carries **both** lines; include them so the GRPO closes fully.

### 3.5 TDS: threshold, and the trap under it (C-0036, C-0037)
194Q deducts **0.1% only once that SELLER passes ₹50 lakh of FY purchases**, and
**SAP does not enforce the threshold** — it deducts whenever `WTCode 1031` is set.
The judgment is human, made before the code goes on.

**The seller is a PAN, not a CardCode.** Aggregate every card sharing `CRD7.TaxId0`.
**TPAC has two Oil cards on PAN `AAGCT4816J`** — VENDA000937 (₹28.73 L) and
VENDA000939 (₹37.26 L). Each under ₹50 L; **together ₹65,99,306, over since
2026-07-13**. That is why the four TPAC drafts need TDS.

FY26-27 position of every vendor in this batch:

| Over ₹50 L (deduct) | Under (do not) |
|---|---|
| Raj Technopack ₹1.41 Cr · SSY ₹92.3 L · Echo Plast ₹74.5 L · **TPAC ₹66.0 L (2 cards)** | Babaji ₹46.8 L · Pioneer Pet ₹41.4 L · Royal Prime ₹41.0 L · Kuber ₹37.3 L · BR Agrotech ₹26.4 L · Multilayer ₹3.9 L |

**Two are about to cross:** Pioneer Pet is **₹70,673** away, Babaji **₹1,56,733**.
Their next bill starts 194Q.

Shape on all 18 recent posted invoices of the liable vendors: `WTCode 1031`,
`Rate 0.1`, `Category I`, `WithholdingType V`, base = Σ `LineTotal` net of GST,
amount rounded to the rupee.

**A bill dated in the previous FY but posted in this one keeps the previous year's
threshold question.** TPAC `HAR2/25-26/3334` and `/2710` were correctly deducted —
TPAC did ₹1.09 Cr in FY25-26. Which FY such a document belongs to is a CA question.

### 3.6 `readback.py` cries wolf on two whole classes
`⚠ quantity X ≠ paper Y` on any bottle+cap GRPO, and `⚠ TDS is 0 but the vendor is
TDS-liable` on any vendor under the threshold. Both fire on **correct** documents.
Report them as notes. A check that flags known-good work teaches everyone to ignore
the channel — and the one real failure arrives wearing the same colour.

---

## 4. Process learnings

### 4.1 Files are not invoices
22 scans were **20 invoices**. `21-10` was literally `TAX INVOICE (Page 2)` of
`21-9` — the second page carries only totals and looks like a complete bill with a
missing stamp. One bill was already entered. Count entities, not files, and report
the difference before starting. Multi-page bills go on as **one** pdf.

### 4.2 The duplicate gate must run TWICE
- **Broad, once, up front** — bulk pull, match offline on normalised refs.
- **Narrow, live, seconds before each POST.** Not redundant: draft 55302 was created
  from **another fleet box under the same USER39 login** at 15:12, between the broad
  snapshot and the write. Only the narrow check caught it.

**One machine per pile.** Two boxes on one SAP login makes ownership indistinguishable
and duplicates near-certain.

### 4.3 Four A/P invoices were posted LIVE and unapproved from the other box today
`49987` (₹5,664), `50006`/`50007`/`50008` (₹9,734 / ₹12,548 / ₹19,620). That is
`sapb1 post` used where `draft` + `add-draft` belongs — they bypassed Bhawani and are
in the ledger. **Never `post` a document.** (C-0034.)

### 4.4 Don't trust an agent's self-report of its own identity
One reader agent labelled Pioneer Pet with another bill's slot number. Re-derive
identity from the **filename**, which is authoritative.

### 4.5 "Recorded" ≠ "delivered"
The harness said corrections were sent to every operator. But the digest injected at
session start is capped, and it **silently dropped 8 rules including C-0037**, ninety
seconds after recording — by iteration order, not severity, announced only in an HTML
comment. Default raised 6000 → 12000 (35 rules = 7.7k). **After recording anything
meant to propagate, grep the delivered file on the destination for its id.**

---

## 5. Open items for Accounts

1. **BR Agrotech `2633100542` was received into SAP twice** — GRPO 2026086622
   (`NumAtCard '.2633100542'`, 17-Aug) and 2026086714 (clean ref, 22-Aug), both open,
   both ₹3,61,250, both gate 148, same UserSign. **₹3.61 lakh of phantom stock.**
   Draft 55327 uses **2026086714** (its `PM0000195` "52 GMS GREEN" matches the paper;
   the other has `PM0000121` POMACE). **2026086622 must be cancelled in the client.**
2. **TDS under-deducted ~₹1,180** on PAN `AAGCT4816J` (TPAC): ₹1,599 due on the
   ₹15,99,306 excess, ₹419 taken.
3. **Invoice 48981 over-deducted ₹67** (Royal Prime, 31-Jul-26, PAN at ₹36.6 L).
4. **An unmapped handwritten mark.** Most bills carry a **bare 4-digit number
   top-centre** — 4548, 4183, 7901, 7529, 7481, 1653, 0821. Not a Drafts DocEntry
   (5 digits), not a GRPO DocNum (10), and **not** a bare gate-entry suffix — I queried
   `GE-2026-7901` and `GE-2026-7529`, zero hits. **Somebody in Accounts knows what it
   is in one second.** When you find out, add it to
   `.claude/skills/jivo-ap-draft/reference/handwriting.md`.

---

## 6. What it cost, and how to make it cheap

| Phase | Time | Cost |
|---|---|---|
| Setup + bulk SAP pulls | ~9 min | cheap |
| **Reading the 22 scans** (22 agents, 317 tiles) | **14m 47s** | **2,277,088 tokens — 103k/bill**, and it hit the weekly limit, killing 4 readers |
| **Matching paper → vendor + GRPO** (3 rounds) | ~10 min | 15 of 17 failed round 1 |
| **Writing the 19 drafts** | **7m 13s** | the actual job |
| Attachments (40 files) | ~5 min | 2 transient 500s |
| Effective Month fix | ~10 min | a round that shouldn't have existed |

**The writing took 7 minutes. The rest was reading paper and guessing which GRPO it
belonged to.**

The two changes that remove most of it:

1. **Write the GRN number on the bill at the gate.** Only **5 of 18** carried it;
   every one that did went through first time. The gatekeeper already writes G.No,
   Date, Qty, V.No — one more field kills the entire matching phase.
2. **Populate GSTIN on the vendor master.** Empty on all 2,235 Oil vendors, which is
   the only reason name matching was ever attempted. Needed for GST 2A/2B recon anyway.

Then: read only the stamp and margins, not 9 blind tiles per page — the GRPO already
knows the vendor, quantity, rate, tax, total, branch and POs. The paper only adds the
invoice number, the invoice date, the gate date and the handwriting.

**With those, this batch is ~10 minutes instead of ~50, and it doesn't touch quota.**

---

## 7. Still to fix in the tooling

`precheck.py` should: match the GRPO on `NumAtCard` first · take `CardCode` from that
GRPO and never name-match · write the dimension block (Dim2 from DocDate) · exclude
zero-value companion lines from the quantity test. That is the difference between one
clean pass and three. Not done — Daman's call when.
