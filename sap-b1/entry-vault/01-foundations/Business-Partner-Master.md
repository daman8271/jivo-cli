---
type: foundation
sap_tables: [OCRD, OCRG, CRD1, CRD4, CRD7, OCTG, OWHT, OACT, NNM1, OBPL, PCH12]
objtype: 2
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Business partner master — finding the right party, which is step one of every entry

> Before you type a date, an amount or a GL code you have to pick **one row out of
> 8,566**. Everything downstream is decided by that pick: the creditor account, the
> due date, whether TDS comes off, whether the tax is IGST or CGST+SGST, and which
> book the entry even belongs in. Pick the wrong row and the bill still posts —
> it just posts against the wrong party, in the wrong drawer, with no TDS.
> This note is how to pick right, and how to check afterwards that you did.

## The short version

1. **The card decides the creditor account, not the group and not you.** `OPCH.CtlAccount`
   equals the vendor card's `OCRD.DebPayAcct` on **16,285 of 16,334** Oil A/P invoices,
   **4,857 of 4,864** Mart and **3,170 of 3,170** Beverages — all history. The *group*
   only predicts it, and gets it wrong on about 1 bill in 15. → [[Chart-of-Accounts]]
2. **A `CardCode` is a per-book counter, not a party identifier.** Each book runs its own
   `VENDA`/`CUSTA` sequence. Matched on GSTIN, **460 of 1,212** vendors shared between Oil
   and Beverages carry *different* codes — and worse, **884 of 2,860** codes that exist in
   both Oil and Beverages point at two *different parties*.
3. **Search by name, then confirm by GSTIN.** Every one of the 8,566 `CardName` values in
   all three books is upper-case with no stray padding, which is the only reason the
   Service Layer's case-sensitive `contains()` works at all. But 88 Oil names map to
   two-or-more cards, so the name alone is not proof.
4. **Mart's master is mostly dead.** Mart shows 2,191 partners; only **397** are live
   (173 customers, 224 vendors). 1,750 cards were frozen in one bulk action in
   September 2024 and no frozen Mart vendor has been billed since. Oil has 24 frozen
   cards, Beverages 88.
5. **You cannot create a partner.** In the last 90 days all 275 new cards across the three
   books came from three logins — JAYEESH (211), `manager` (36), MANVI (28). If the party
   is not there, the entry stops and you ask master data.

---

## 1. What is actually in the master

Row counts from `profile-OCRD.md` / `profile-OCRG.md`; live/frozen split measured
2026-08-24.

| | Oil | Mart | Bev | All |
|---|---:|---:|---:|---:|
| Partner cards (`OCRD`) | 3,411 | 2,191 | 2,964 | **8,566** |
| — customers (`CardType='C'`) | 1,176 | 943 | 1,265 | 3,384 |
| — vendors (`CardType='S'`) | 2,235 | 1,248 | 1,699 | 5,182 |
| **Live** (`validFor='Y'` and `frozenFor='N'`) | **3,387** | **397** | **2,876** | 6,660 |
| — live customers | 1,164 | 173 | 1,192 | |
| — live vendors | 2,223 | 224 | 1,684 | |
| Groups (`OCRG`) | 47 | 45 | 45 | |
| Cards carrying at least one GSTIN | 2,297 | 1,548 | 2,127 | |
| Distinct control accounts used — vendors / customers | 15 / 21 | 14 / 22 | 15 / 19 | |

`CreateDate` starts 2024-08-31 in all three books: that is the SAP go-live, so
"all history" and "the last two years" are the same window here. Related:
[[Opening-Balance-and-Cutover]].

### The four `CardCode` prefixes — and they are the only four

Measured across all three books; the prefix maps one-to-one onto `CardType` and onto a
numbering series in `NNM1` (`ObjectCode='2'`), whose `SeriesName` *is* the prefix.

| Prefix | Series | `CardType` | Means | Oil | Mart | Bev |
|---|---:|---|---|---:|---:|---:|
| `VENDA######` | 87 | `S` | ordinary **vendor** — a real outside supplier | 1,757 | 1,030 | 1,453 |
| `CUSTA######` | 85 | `C` | ordinary **customer** | 1,138 | 931 | 1,232 |
| `ORGV######` | 88 | `S` | **staff imprest vendor** — an employee's expense-claim account. 100 % of them sit in group `STAFF VENDOR` | 478 | 218 | 246 |
| `ORGC######` | 86 | `C` | **staff customer** — the employee-as-debtor side | 38 | 12 | 33 |

Series 1 and 2 are SAP's "Manual" placeholders; three Oil cards were created on them
and nothing since. **`ORG*` is not an organisation prefix — it is the staff prefix.**
More on the series machinery: [[Numbering-Series]].

---

## 2. The lookup, in the order that actually works

### a. If the paper carries a GSTIN — start there

The GSTIN is **not** on the partner header. Every header-level tax field is empty in
every row of all three books (`LicTradNum`, `VATRegNum`, `VatIdUnCmp`, `VatIDNum`:
**0 of 8,566**) — which is why `profile-OCRD.md` does not even list them, and what
**[C-0014]** is telling you. The GSTIN lives one level down, on the **address**:

| Where | Field | What it holds |
|---|---|---|
| `CRD1` (BP addresses) | `GSTRegnNo` | the **GSTIN**, exactly 15 chars where present — 9,188 of 12,908 Oil address rows |
| `CRD1` | `GSTType` | `1` = registered, on every row that has a GSTIN; blank on every row that does not. Two Oil rows carry `6`, one Mart row `5` — *meaning unverified, 1 card each* |
| `CRD1` | `AdresType` | `B` = bill-to, `S` = ship-to. They come in pairs |
| `CRD7` | `TaxId0` | the **PAN**, 10 chars on 4,050 Oil rows — never a GSTIN ([C-0014]) |

```sql
-- the vendor behind a GSTIN, in every book at once (paste the GSTIN, don't print it)
SELECT 'OIL' CO, c."CardCode", c."CardName", c."CardType", c."DebPayAcct",
       c."validFor", c."frozenFor"
FROM "JIVO_OIL_HANADB"."CRD1" a
JOIN "JIVO_OIL_HANADB"."OCRD" c ON c."CardCode" = a."CardCode"
WHERE TRIM(a."GSTRegnNo") = '<15-char GSTIN>'
UNION ALL SELECT 'MART', … FROM "JIVO_MART_HANADB"."CRD1" …
UNION ALL SELECT 'BEV',  … FROM "JIVO_BEVERAGES_HANADB"."CRD1" …
```

**A third of the master has no GSTIN, and that is correct, not missing data.** Oil: 822
of 2,235 vendors and 292 of 1,176 customers have none. Where they sit is the whole
story:

| Oil vendor group | Vendors | of which no GSTIN |
|---|---:|---:|
| STAFF VENDOR | 478 | **478** — employees, by definition |
| SERVICE | 815 | 249 |
| PURCHASE | 407 | 25 |
| TRANSPORTER | 97 | 23 |
| PURCHASE OIL | 127 | 14 |
| FIXED ASSETS | 150 | 12 |
| everything else | 161 | 21 |

Those 249 GSTIN-less SERVICE vendors are the reverse-charge population — the bill has
no GST on it and JIVO raises both sides itself. → [[Chart-of-Accounts]] §5.

### b. If you only have a name

Measured 2026-08-24, and this is the licence for name search: **`CardName` is upper-case
on 3,411 of 3,411 Oil cards, 2,191 of 2,191 Mart and 2,964 of 2,964 Bev**, with zero
leading or trailing spaces. So the Service Layer's `contains(CardName,'…')` — which is
case-sensitive, because `toupper()`/`tolower()` are not supported on this Service Layer —
works as long as you upper-case your search fragment. That is exactly what
`.claude/skills/ap-rm-pm/bin/precheck.py` does.

Two things still bite:

- **12 Oil names contain a double space** (4 Mart, 7 Bev). A fragment that spans a word
  break can miss. Search the shortest distinctive single word.
- **A name is not unique.** Names shared by two or more cards:

| Book | Name collisions | Cards involved | customer + vendor, same name | 2+ **vendor** cards | 2+ customer cards |
|---|---:|---:|---:|---:|---:|
| Oil | 88 | 181 | 67 names / 138 cards | 9 names / 18 cards | 12 / 25 |
| Mart | 61 | 125 | 43 / 88 | 6 / 12 | 12 / 25 |
| Bev | 72 | 147 | 55 / 112 | 5 / 10 | 12 / 25 |

The customer+vendor pairs are usually the *same* real party on both ledger sides —
including every employee, who has an `ORGV` imprest card and often an `ORGC` customer
card. Say which side you are on. The dangerous ones are the **two-vendor-cards** names,
because both will accept your bill. All nine Oil cases, and the tiebreak:

| Name | Cards | Tiebreak that works |
|---|---|---|
| DELHI PUNJAB TRANSPORT CO | `VENDA000636` live, bal −₹1,12,879 · `VENDA000973` **frozen** | one is frozen |
| PALAK ENTERPRISES | `VENDA000325` **frozen** · `VENDA000931` live | one is frozen |
| VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED | `VENDA000252` **frozen** · `VENDA000930` live | one is frozen |
| BIO TECH SALES AND SERVICES | `VENDA000114` bal 0 · `VENDA001612` bal −₹14,160 | the one with movement |
| SHARMA ENTERPRISES | `VENDA000366` bal 0 · `VENDA001611` bal −₹10,500 | the one with movement |
| MAHBOOB KHAN | `VENDA000988` bal 0 · `VENDA001738` bal +₹35,000 | the one with movement |
| SIGNODE INDIA LTD | `VENDA000736` · `VENDA000952`, both live, both 0 | **ask** — check the GSTIN |
| DEEPAK KUMAR | `VENDA001008` · `VENDA001734`, both live, both 0 | **ask** — check the GSTIN |
| `<name>` IMPREST JWPL#### ×3 employees | two `ORGV` cards for one `U_Emp_Code` | see §7 |

### c. Then confirm against the vendor's own history

The card tells you what the master *says*. The last three posted bills tell you what
JIVO actually *does* — and where they disagree, the `ap-rm-pm` skill's rule is
that precedent wins (that is how a master TDS flag gets correctly overruled).

```sql
-- the vendor's last 5 posted A/P bills: what branch, series, control account, TDS
SELECT "DocNum","DocDate","TaxDate","NumAtCard","BPLId","Series",
       "CtlAccount","DocTotal","WTSum","DocDueDate"
FROM "JIVO_OIL_HANADB"."OPCH"
WHERE "CardCode" = 'VENDA######' AND "CANCELED" = 'N'
ORDER BY "DocDate" DESC LIMIT 5;
```

---

## 3. The same party, three books, three codes

Each book runs its own counter — Oil's `VENDA` series is at 1766, Mart's at 1034,
Beverages' at 1454. A vendor onboarded in Oil in 2024 and in Beverages in 2025 therefore
gets two unrelated numbers. **NEXTON SEALS is `VENDA001548` in Oil and `VENDA001235` in
Beverages** — verified: same single GSTIN on both cards, same group (105 SERVICE), same
control account `2110004`.

### How common is that? Measured on GSTIN, 2026-08-24

A party in book A is "the same party" as one in book B when they share at least one
15-character `CRD1.GSTRegnNo`.

| Pair | Parties matched | Same `CardCode` | **Different `CardCode`** |
|---|---:|---:|---:|
| Oil → Mart, customers | 689 | 647 | 42 (6 %) |
| Oil → Mart, vendors | 834 | 748 | **86 (10 %)** |
| Oil → Bev, customers | 715 | 652 | 63 (9 %) |
| Oil → Bev, **vendors** | 1,212 | 752 | **460 (38 %)** |
| Mart → Bev, customers | 664 | 647 | 17 (3 %) |
| Mart → Bev, vendors | 785 | 751 | 34 (4 %) |

**Oil ↔ Beverages vendors are the broken pair** — nearly 2 in 5 shared vendors have a
different code. Oil ↔ Mart and Mart ↔ Bev are roughly 1 in 10 and 1 in 25.

The good news: for those 502 diff-code Oil↔Bev vendor pairs, **450 (90 %) have the
character-for-character identical `CardName`**, 441 the same control account and 437 the
same group name. So an exact-name search crosses books far better than a code does.

### The other direction is worse: the same code, a different party

| Pair | `CardCode`s in both books | Same name | **Different name** | of the different-name pairs: both sides carry a GSTIN | …and the GSTINs **disagree** |
|---|---:|---:|---:|---:|---:|
| Oil vs Mart | 2,179 | 1,963 | 216 (10 %) | — | — |
| Oil vs Bev | 2,860 | 1,976 | **884 (31 %)** | 524 | **518** |
| Mart vs Bev | 2,191 | 1,972 | 219 (10 %) | — | — |

Only 6 of the 884 are the same party spelled differently. **518 are genuinely two
different companies wearing the same code.** The live example is
`CUSTA000827`: JIVO MART PRIVATE LIMITED (HARYANA) in Oil and in Beverages, but Mart's
own Haryana branch in the Mart book.

> **Never carry a `CardCode` from one book to another, and never quote one without the
> book.** [[AP-Invoice]] says the same thing from the document side.

### There *is* an official crosswalk — Oil ↔ Beverages only

Two undocumented user fields, one on each side, and neither exists in Mart:

| Book | Field | Filled | Points at |
|---|---|---:|---|
| Oil | `OCRD.U_WG_CardCode` | 2,413 / 3,411 (71 %) | a **Beverages** `CardCode` with the identical name on 2,382 (98.7 %) |
| Bev | `OCRD.U_OIL_CardCode` | 2,417 / 2,964 (82 %) | an **Oil** `CardCode` with the identical name on 2,380 (98.5 %) |
| Mart | — | — | the column does not exist. Mart is unlinked |

The two pointers agree with each other on 2,375 of 2,401 (98.9 %) where both are set,
and between them they resolve **313 of the 502** diff-code Oil↔Bev vendor pairs (153 have
the field blank). So: try the pointer first, fall back to GSTIN, then to exact name.
*Inferred:* "WG" = Wellness Group. That the fields are a deliberate crosswalk is
**measured**; who maintains them and why Mart was left out is an open question.

```sql
-- Oil card -> its Beverages twin, both routes, one query
SELECT o."CardCode" OIL_CODE, o."CardName", o."U_WG_CardCode" POINTER,
       b."CardCode" BEV_CODE, b."CardName" BEV_NAME
FROM "JIVO_OIL_HANADB"."OCRD" o
LEFT JOIN "JIVO_BEVERAGES_HANADB"."OCRD" b
       ON b."CardCode" = TRIM(o."U_WG_CardCode")
WHERE o."CardCode" = 'VENDA######';
```

---

## 4. The groups — and what each one implies

`OCRG` holds 47 groups in Oil, 45 in Mart, 45 in Beverages. The split runs on
`GroupType`: `C` = customer groups, `S` = vendor groups. And the two halves are
organised on completely different principles:

- **Customer groups are geography** — DELHI, PUNJAB, HARYANA, UTTAR PRADESH, … plus
  PAN INDIA, EXPORT, BRANCH CUSTOMER, STAFF CUSTOMER, DEBTORS.
- **Vendor groups are function** — SERVICE, PURCHASE, STAFF VENDOR, TRANSPORTER,
  FIXED ASSETS, PURCHASE OIL, CIVIL, PLANT & MACHINERY, IT, E-COMMERCE, FUEL,
  IMPORT & EXPORT, BRANCH VENDOR, BSU.

**The customer group tells you nothing about the sales channel** — the channel is in the
control account (`1101005` E-COM, `1101008` CALL CENTRE, …) and in `U_Main_Group`, and
those two disagree (§8). The vendor group is the useful one, because it is roughly the
kind of spend.

### Vendor groups, all three books, with the account they usually get

Counts are cards; the account column is the modal `DebPayAcct` and, in brackets, how many
*other* accounts appear inside that group.

| Vendor group | Oil cards | Mart | Bev | Usual control account | What it implies for posting |
|---|---:|---:|---:|---|---|
| SERVICE | 815 | 461 | 672 | `2110004` SUNDRY CREDITOR SERVICE (Oil: 5 accounts in use) | expenses, fees, freight — the standalone-bill population |
| STAFF VENDOR | 478 | 216 | 246 | `2110003` SUNDRY CREDITOR STAFF (1 account, no exceptions) | employee imprest, no GSTIN, no vendor invoice number |
| PURCHASE | 407 | 156 | 338 | `2110005` DOMESTIC PURCHASE (Oil 4) — but in **Mart** `2121002`, see §6 | packaging, consumables, stock |
| FIXED ASSETS | 150 | 112 | 140 | `2110004` / `2110005` — genuinely split ~50:50 in Oil and Bev | capex; the receipt parks in `2140002`, not `2140001` |
| PURCHASE OIL | 127 | 52 | 53 | `2110001` DOMESTIC OIL (Oil 4) | loose oil — small count, biggest money |
| TRANSPORTER | 97 | 95 | 96 | `2110004`, single account, all three books | freight; mostly arrives as a service GRPO |
| PLANT & MACHINERY | 46 | 46 | 46 | `2110004` | |
| CIVIL | 45 | 46 | 45 | `2110004` | |
| IT | 19 | 18 | 18 | `2110004` (+`2110006` foreign) | |
| IMPORT & EXPORT | 17 | 20 | 20 | `2110001`/`2110002` foreign oil | non-INR is possible here |
| E-COMMERCE | 13 | 16 | 14 | `2110004` — **plus `2121002` intercompany, see §6** | platform fees |
| BSU | 10 | — | — | `2110004` | Oil only |
| BRANCH VENDOR | 7 | 6 | 7 | one `212xxxx`/`2121xxx` account **per card** | never an outside party — §6 |
| FUEL | 4 | 4 | 4 | `2110004` | |
| COMPANY UNIT VENDOR | 0 | — | 0 | — | exists, never used |

### Group codes are aligned across the books — until they are not

`GroupCode` 100–142 means the same thing in all three books (105 = SERVICE everywhere).
Above 142 they diverge, and a group code carried between books is then simply wrong:

| `GroupCode` | Oil | Mart | Bev |
|---:|---|---|---|
| 143 | COMPANY UNIT CUSTOMER (`C`) | **PARENT COMPANY** (`C`) | COMPANY UNIT CUSTOMER (`C`) |
| 144 | *does not exist* | **CHHATTISGARH** (`C`) | **COMPANY UNIT VENDOR** (`S`) |
| 146 | COMPANY UNIT VENDOR (`S`) | *does not exist* | *does not exist* |
| 147 | CHHATTISGARH (`C`) | *does not exist* | *does not exist* |
| 148 | BSU (`S`) | *does not exist* | *does not exist* |

Mart's 144 is a *customer* group and Beverages' 144 is a *vendor* group. Join on
`GroupName`, never on `GroupCode`.

### The group predicts the control account. It does not decide it.

Oil A/P invoices, 365 days, `CANCELED='N'` (per **[C-0021]**):

| Oil vendor group | Control account → docs |
|---|---|
| **SERVICE** | `2110004` **1,666** · `2110008` **95** · `2110005` **32** · `2110001` 6 · `2110006` 3 |
| PURCHASE | `2110005` 1,560 · `2110004` 5 · `2110001` 1 |
| PURCHASE OIL | `2110001` 623 · `2110005` 93 · `2110002` 18 · `2110007` 11 |
| E-COMMERCE | `2110004` 635 · **`2121002` 32** · `2110005` 11 |
| TRANSPORTER | `2110004` 401 |
| BRANCH VENDOR | `2120002` 250 · `2120006` 87 · `2120001` 26 · `2121003` 4 · `2121001` 2 |
| STAFF VENDOR | `2110003` 1,324 |
| FIXED ASSETS | `2110005` 51 · `2110004` 49 |
| CIVIL 235 · IT 79+2 · FUEL 45 · P&M 31 · I&E 3 | mostly `2110004` |

So the topic's standing claim is confirmed with today's numbers: group SERVICE reaches
**five** different creditor accounts. Rolled up:

| Book | A/P docs (365 d) | On the group's modal account | **Off it** |
|---|---:|---:|---:|
| Oil | 7,380 | 6,903 | **477 (6.5 %)** |
| Mart | 3,230 | 3,031 | **199 (6.2 %)** |
| Bev | 1,447 | 1,399 | **48 (3.3 %)** |

**Read the card. `DebPayAcct` is 100 % filled on all 8,566 rows — there is never a reason
to guess.**

---

## 5. Exactly which card fields your entry depends on

Fill rates from `profile-OCRD.md` (Oil / Mart / Bev, all history) plus live checks today.
"Who types it" is from the operator's seat, not master data's.

| `OCRD` field | Reads as | Filled | Decides | Who types it |
|---|---|---|---|---|
| `CardCode` | the party | 100 % | everything below. **Per book** | you pick it |
| `CardName` | the party's name | 100 %, always upper case | the printed name; `OPCH.CardName` is copied and *can* be edited on the document | copied |
| `CardType` | `S` vendor / `C` customer | 100 % | which ledger side. `S` 2,235 / `C` 1,176 in Oil | fixed at creation |
| **`DebPayAcct`** | **the control account** | **100 %** | the credit (vendor) or debit (customer) line of the journal — `OPCH.CtlAccount` on 99.7–100 % | **master data. Never overridden on the document — fix the card instead** |
| `GroupCode` | vendor function / customer state | 100 % | reporting, and the *default* for `DebPayAcct` | master data |
| `GroupNum` | payment terms → `OCTG` | 100 % (`-1` = the real term "ADVANCE/CASH/0 DAYS", 2,831 of 3,411 Oil) | `DocDueDate`. See below | master data |
| `WTLiable` | subject to TDS | 93 / 98 / 94 % (`Y` on 548 Oil vendors) | whether SAP *offers* TDS | master data; you confirm against precedent |
| `CRD4` rows | the vendor's actual TDS codes → `OWHT` | 389 of 548 Oil `Y` vendors | whether TDS is actually computed | master data |
| `Currency` | `INR`, or `##` = any | 100 % | the document currency. Oil: 27 vendors + 4 customers `##`, rest INR. Mart/Bev instead hard-set 9 vendors to `USD` and 3 to `EUR` | master data |
| `validFor` / `frozenFor` | active / frozen | 100 % | whether SAP will post at all | master data |
| `Balance` | ledger balance, **positive = DEBIT** | 26 / 6 / 17 % non-zero | your sanity check before posting | SAP |
| `SlpCode` | sales employee | set on 312 of 1,176 Oil customers, 1,390 of 2,235 vendors | defaults onto A/R documents | master data |
| `BillToDef` / `ShipToDef` | which `CRD1` address is default | 99–100 % | **the GSTIN on the document** | master data; you may change the address on the document |
| `U_Main_Group` | channel / spend tag | 99–100 %, 63 values | reporting only, and it disagrees across books — §8 | master data |
| `U_Emp_Code` | `JWPL####` employee code | 100 % of `ORGV` cards | which employee an imprest account belongs to | master data |
| `U_MSME` / `U_MSME_Type` | MSME registration | 279 of 2,235 Oil vendors (12 %); Mart 44; Bev 222 | nothing automatic. 698 Oil bills / ₹65.23 Cr in a year went to flagged vendors | master data |
| `U_Fssai` | FSSAI licence | 29 Oil vendors | nothing automatic | master data |
| `DflAccount` / `DflBankKey` / `DflSwift` | the party's bank details | 56 / 40 / 46 % | outgoing payments. **Never print these** | master data |
| `U_BranchHomeBpl` | a default branch | **10 of 3,411 in Oil; the column does not exist in Mart or Bev** | nothing. **The card carries no branch** | — |

### Payment terms set the due date — and get overridden a lot

`GroupNum` → `OCTG.PymntGroup`. The terms in use: ADVANCE/CASH/0 DAYS, COD, NET-01 …
NET-45, LC 60, and five percentage-advance terms. Oil A/P over 365 days, checking whether
`DocDueDate − DocDate` equals the term's `ExtraDays`:

| Vendor's term | A/P docs | Due date matches the term |
|---|---:|---:|
| ADVANCE/CASH/0 DAYS (`-1`) | 4,343 | 3,574 (82 %) |
| NET-30 | 2,327 | **1,310 (56 %)** |
| NET-25 | 371 | 249 (67 %) |
| NET-35 | 114 | 58 (51 %) |
| NET-15 | 102 | 80 (78 %) |

So the due date is a *suggestion* from the card that Accounts edits on roughly 4 bills in
10 on credit terms. Do not treat a due date that disagrees with the master as an error.

### TDS: the flag is not enough, and this is why drafts come out zero

Two things have to be true before SAP deducts anything — `WTLiable='Y'` **and** at least
one `CRD4` row pointing at an `OWHT` code. Measured:

| Book | Vendors `WTLiable='Y'` | …with a TDS code attached | **flagged but no code** |
|---|---:|---:|---:|
| Oil | 548 | 389 (71 %) | **159** |
| Mart | 338 | 87 (26 %) | **251** |
| Bev | 376 | 148 (39 %) | **228** |

And what that does to real bills — Oil, 365 days:

| Vendor state | A/P docs | Docs with TDS | TDS deducted |
|---|---:|---:|---:|
| `WTLiable='Y'` **with** a code | 3,668 | 3,164 (86 %) | ₹76.74 lakh |
| `WTLiable='Y'` **without** a code | 86 | **0** | **₹0** |
| `WTLiable='N'` | 3,626 | 0 | ₹0 |

That silent third row is the master-data half of **[C-0018]**. The codes themselves are
not portable either: "Contractors (Ind/HUF) 1 %" is `WTCode` **1023** in Oil and Mart but
**1230** in Beverages.

```sql
-- does this vendor actually have TDS wired up?
SELECT c."CardCode", c."WTLiable", w."WTCode", w."WTName", w."Rate"
FROM "JIVO_OIL_HANADB"."OCRD" c
LEFT JOIN "JIVO_OIL_HANADB"."CRD4" x ON x."CardCode" = c."CardCode"
LEFT JOIN "JIVO_OIL_HANADB"."OWHT" w ON w."WTCode"  = x."WTCode"
WHERE c."CardCode" = 'VENDA######';
```

### The branch is not on the card — but the vendor predicts it

There is no usable default business place on `OCRD`. The branch comes from the buyer
GSTIN (`OBPL.TaxIdNum` / `FederalTaxID`) and, for a GRPO-based bill, from the GRPO.
Still, the vendor's own history is a good check: of 689 Oil vendors billed in the last
365 days, **643 used exactly one `BPLId`** (5,792 of 7,380 documents); 42 used two, 2
used three, one four and one five. A branch that does not match the vendor's usual one is
worth a second look. → [[Numbering-Series]], [[AP-Invoice]]

### The address you pick sets the GSTIN, which sets IGST vs CGST+SGST

`PCH12.BpGSTN` (the vendor GSTIN stamped on the A/P invoice, filled on 70 % of Oil bills,
91 % Mart, 53 % Bev) equals one of the GSTINs on that vendor's `CRD1` addresses on
**11,273 of 11,404** Oil bills — 98.9 %. `PCH12.BPStatGSTN` is its state code and
`PCH12.IsIGSTAct` is the resulting flag (`Y` on 11,670 Oil bills, `N` on 4,492).

Most cards make this easy: 3,184 of 3,388 Oil cards have exactly **one** bill-to address.
But **101 Oil cards carry more than one distinct GSTIN on their bill-to addresses**
(60 have two, 12 have four, one has 33). On those the address is a real decision, and
picking the wrong one flips the tax split. Prior measurement on the A/R side agrees:
`INV12.BpGSTN = CRD1.GSTRegnNo` (bill-to) on 2,262 of 2,263 B2B invoices
(`portals/gst/docs/comparison-spec.md`).

**One card is not a party at all.** `CUSTA000873` AMAZON holds **1,696 distinct GSTINs**
across 1,718 bill-to addresses — every Amazon fulfilment centre. Next largest: the CSD
area-manager card (33), the two JIVO MART cards (30 each), METRO (11). If you count
distinct GSTINs to size a customer base you will be counting Amazon warehouses.

---

## 6. Intercompany and inter-branch — the cards that are not outside parties

`2120001`–`2120006` and `2121001`–`2121003` are not creditors. They are the other side of
JIVO. And **the same account number means a different entity in each book**, so this table
is the one to read before touching any of them.

| Account | Oil book | Mart book | Bev book |
|---|---|---|---|
| `2120001` | JIVO WELLNESS PVT. LTD **DELHI** (Oil's own branch) | JIVO WELLNESS DELHI (**zero balance**) | JIVO **BEVERAGES** DELHI (Bev's own branch) |
| `2120002` | JIVO WELLNESS HARYANA — **−₹70.29 Cr**, Oil's largest | JIVO WELLNESS HARYANA (zero) | JIVO BEVERAGES HARYANA (−₹58.53 L) |
| `2120006` | JIVO WELLNESS PUNJAB (−₹1.86 Cr) | JIVO WELLNESS PUNJAB (zero) | JIVO BEVERAGES PUNJAB (−₹4.81 L) |
| `2120007` | JIVO BEVERAGES (a sibling) | JIVO **MART** HARYANA (Mart's own branch, −₹2.59 Cr) | JIVO **OIL** (a sibling) |
| `2120008`–`2120013` | *do not exist* | JIVO MART DELHI / PUNJAB / UP / RAJASTHAN / KARNATAKA — Mart's own branches | *do not exist* |
| `2121001` | SUNDRY CREDITORS JIVO AGRI | same | same |
| **`2121002`** | SUNDRY CREDITORS **JIVO MART** (−₹2.25 Cr) | SUNDRY CREDITORS **JIVO WELLNESS** (**−₹24.84 Cr**) | SUNDRY CREDITORS JIVO MART (zero) |
| `2121003` | SUNDRY CREDITORS ARY | same | same |

The debtor side mirrors it exactly: `1102001`–`1102006` are own-branch in Oil and Bev,
`1102008`–`1102013` are Mart's own branches, and `1102008` is the sibling company in Oil
(JIVO BEVERAGES) and in Bev (JIVO OIL).

**So the rule is not "2120xxx = inter-branch".** It is: read the account *name* in *that
book*. `2121002` is Mart in two books and Oil in the third.

### These parties do not stay inside the BRANCH groups — [C-0005] and [C-0020] confirmed

Re-measured 2026-08-24; both corrections hold, and here is the evidence:

| Book | Card | Name | Group | Control account |
|---|---|---|---|---|
| Oil | `VENDA000483` | JIVO MART PVT LTD | **E-COMMERCE** | `2121002` — 32 A/P docs in 365 d |
| Mart | `VENDA000001` | JIVO WELLNESS PVT LTD | **PURCHASE** | `2121002` — **1,874 A/P docs, 58 % of all Mart A/P**, −₹24.83 Cr |
| Mart | `VENDA000004` | JIVO WELLNESS PVT LTD - DL | **PURCHASE** | `2121002` |
| Oil | `CUSTA000606` | JIVO MART PVT LTD | **DELHI** | `1101005` SUNDRY DEBTORS E-COM |
| Oil | `CUSTA001113` | JIVO MART PVT LTD - SERVICE | **DELHI** | `1101005` |
| Oil | `CUSTA000827` | JIVO MART PRIVATE LIMITED (HARYANA) | **HARYANA** | `1101001` SUNDRY DEBTORS GT — indistinguishable from a general-trade shop |
| Bev | `CUSTA000606` / `CUSTA000827` | as above | DELHI / HARYANA | `1101005` / `1101001` |

Mart's single biggest A/P counterparty is its own parent, filed under PURCHASE. **Match
on `CardName` as well as the group**, exactly as [C-0020] says, and exclude the full
[C-0005] list of 23 codes from any external-party report.

In the Beverages book the branch cards are *named* `JIVO WELLNESS PVT LTD - DL/HR/PB/HP`
because Beverages is a unit of the same legal entity — but their accounts are
`JIVO BEVERAGES <state>`. The name is not the tell; the account is.

**One defect found:** Mart `VENDA000977` FONIO FOODS PVT LTD sits in group E-COMMERCE
with control account `2120008` JIVO MART PVT. LTD. DELHI — an outside vendor pointed at
Mart's own branch account. Balance is zero, so nothing has posted through it yet. Bill
that card and the cost lands in inter-branch. Worth a master-data fix.

---

## 7. Staff imprest vendors — the pattern, decoded

`ORGV000187 PUNEET KAUR IMPREST JWPL0031` is the shape. Measured across all three books,
the rules are exact:

| Rule | Oil | Mart | Bev |
|---|---|---|---|
| Every `STAFF VENDOR` card has the `ORGV` prefix | 478 / 478 | 216 / 216 | 246 / 246 |
| Every one has `IMPREST` in the `CardName` | 478 / 478 | 216 / 216 | 246 / 246 |
| Every one has `U_Emp_Code` filled | 478 / 478 | 216 / 216 | 246 / 246 |
| Every one has control account `2110003` SUNDRY CREDITOR STAFF | 478 / 478 | 216 / 216 | 246 / 246 |
| Every one has **no GSTIN** | 478 / 478 | — | — |

**The convention is `<PERSON NAME> IMPREST JWPL####`** — the employee's name, the word
IMPREST, then their JWPL employee code. It holds on 441 of 478 Oil names cleanly; the
other 37 are keying variants: `(JWPL####)`, a trailing amount (`… JWPL#### 2 LAKH`), a
site (`… (HO) JWPL####`), two codes on one card, and one misspelling `JWLP####`.

**So parse `U_Emp_Code`, not the name.** It is `JWPL####` on 477 of 478 Oil cards
(the 478th literally holds a first name). The `ORGC` staff-*customer* cards are the same
employees on the debtor side — 38 in Oil, and only 13 of those carry IMPREST in the name.

### Most of them are dormant, which is why name search hurts

| Book | Imprest cards | Billed at least once in 365 d | Non-zero balance |
|---|---:|---:|---:|
| Oil | 478 | **83** | 75 |
| Mart | 218 | 19 | 21 |
| Bev | 246 | 24 | 19 |

Volume, last 90 days, group `STAFF VENDOR`: Oil 200 bills / ₹13.82 L across **36**
accounts; Mart 55 / ₹6.61 L across 12; Bev 52 / ₹2.94 L across 8. `acc/INVENTORY.md`
counts 357 standalone service bills against this group in its own 90-day window — the
same order, a slightly different cut. Either way: 942 imprest cards exist and about 126
are alive.

**Across books, match on `U_Emp_Code`.** 209 employees have an imprest card in both Oil
and Beverages; 191 share the code and **18 do not**. Oil↔Mart: 198 shared, 8 differ.

Imprest bills also have no vendor invoice number — `NumAtCard` is blank, so the normal
duplicate check does not apply. → [[AP-Invoice]], [[Chart-of-Accounts]]

---

## 8. [C-0015] re-measured — the channel tag still disagrees

The correction says `U_Main_Group` differs across books for 129 customers. Re-measured
today on customer cards that share a `CardCode` **and** an identical `CardName` (so they
really are the same party):

| Pair | Customers whose `U_Main_Group` disagrees | of which the CALL CENTER / CALL CENTRE spelling |
|---|---:|---:|
| Oil ↔ Mart | **116** | 107 |
| Oil ↔ Bev | **125** | 116 |
| Mart ↔ Bev | 11 | — |

Matching on `CardCode` alone (the looser test, which also catches the code collisions in
§3) gives 171 / 253 / 72. Either way the correction stands: the tag is unusable for
cross-book segmentation, the cause is 92 % one missing letter, and **it is not only an
Oil-vs-Mart problem — Oil vs Beverages is worse.** Mart carries both spellings at once
(109 CENTRE, 19 CENTER).

The residue is small but real: ROI↔GT (3), WEBSITE↔E-COMMERCE (2), HORECA↔ROI,
HORECA↔GT, CORPORATE↔GT, GT↔E-COMMERCE (1 each). Those are genuine disagreements about
what the customer *is*, not spelling.

**For channel, use the control account** (`1101005` E-COM, `1101008` CALL CENTRE,
`1101004` MT, `1101007` HORECA …). It is 100 % filled and it is what the ledger actually
uses. → [[Chart-of-Accounts]] §2

---

## 9. Pre-flight — before you key anything against a party

- [ ] **Which book.** Oil, Mart or Beverages. Decided by the buyer GSTIN / the entity on
      the paper, never by the code. A `CardCode` from another book is worse than no code.
- [ ] **Found the card by GSTIN or exact name**, not by a remembered number.
- [ ] **Exactly one hit.** If the name returns two vendor cards, resolve it — frozen
      first, then non-zero balance, then GSTIN. If both survive, ask.
- [ ] **`validFor='Y'` and `frozenFor='N'`.** In Mart this eliminates 82 % of the master.
- [ ] **The card is an outside party.** If `DebPayAcct` starts `212` or `2121`, or the
      name contains JIVO / AKAL ROZGAR / ARY, stop — it is intercompany or inter-branch
      ([C-0005], [C-0020]) and belongs in a different conversation.
- [ ] **Read `DebPayAcct` off the card.** Do not infer it from the group; the group is
      wrong on ~6.5 % of Oil bills.
- [ ] **TDS: `WTLiable` *and* a `CRD4` code.** Flag without code = zero TDS, silently.
      Then check the vendor's last three posted bills — precedent beats the flag
      ([C-0018], and the `ap-rm-pm` skill).
- [ ] **Currency.** If the card is `##` or hard-set to USD/EUR, the document is not INR.
- [ ] **The right address.** If the card has more than one bill-to GSTIN, pick the one on
      the paper — it decides IGST vs CGST+SGST.
- [ ] **Branch.** Not on the card. Compare against the vendor's usual `BPLId` anyway.
- [ ] **Already keyed?** Check `NumAtCard` for this vendor before anything
      ([[AP-Invoice]]). Imprest cards have no `NumAtCard`, so check date + amount there.
- [ ] **The card does not exist?** Stop. Only three logins create partners; ask master
      data. Do not create a near-duplicate — 88 Oil names already collide.

## 10. After you save — the read-back

```sql
-- everything the card decided, on the document it decided it for
SELECT p."DocNum", p."CardCode", p."CardName",
       p."CtlAccount", c."DebPayAcct"      AS card_says,
       p."DocCur", c."Currency"            AS card_cur,
       p."DocDate", p."DocDueDate", t."PymntGroup", t."ExtraDays",
       p."WTSum", c."WTLiable",
       p."BPLId", x."BpGSTN" IS NOT NULL   AS vendor_gstin_stamped, x."IsIGSTAct"
FROM "JIVO_OIL_HANADB"."OPCH"  p
JOIN "JIVO_OIL_HANADB"."OCRD"  c ON c."CardCode" = p."CardCode"
LEFT JOIN "JIVO_OIL_HANADB"."OCTG" t ON t."GroupNum" = c."GroupNum"
LEFT JOIN "JIVO_OIL_HANADB"."PCH12" x ON x."DocEntry" = p."DocEntry"
WHERE p."DocEntry" = <DocEntry>;
```

Four things to confirm: `CtlAccount` = `card_says`; `WTSum` non-zero if the vendor is
TDS-wired; `IsIGSTAct` matches the tax on the paper; `BPLId` is the vendor's usual branch.

## 11. Traps

| Trap | What actually happens |
|---|---|
| **Carrying a `CardCode` between books** | 884 of 2,860 Oil/Bev shared codes are *different parties* (518 proven by disagreeing GSTINs). `CUSTA000827` is JIVO MART in Oil and Bev, and Mart's own Haryana branch in Mart |
| **Inferring the control account from the group** | wrong on 477 of 7,380 Oil A/P bills; group SERVICE alone reaches five different creditor accounts |
| **Looking for the GSTIN on the partner header** | `LicTradNum` / `VATRegNum` are empty on all 8,566 cards. It is `CRD1.GSTRegnNo`; `CRD7.TaxId0` is the PAN ([C-0014]) |
| **Trusting `WTLiable='Y'`** | 159 Oil, 251 Mart and 228 Bev vendors are flagged with no `CRD4` code. SAP deducts nothing and says nothing |
| **Searching Mart's master** | 1,794 of 2,191 cards are frozen — 1,750 of them in one September-2024 action. Nearly every hit is dead |
| **Reading `2121002` as one entity** | JIVO MART in Oil and Bev, JIVO WELLNESS in Mart. Same for the whole `2120xxx` block |
| **Reading a Beverages branch card's name** | Bev's own branches are *named* JIVO WELLNESS PVT LTD - DL/HR/PB. The account name is the tell, not the card name |
| **Counting distinct GSTINs to size a customer** | one card (AMAZON) holds 1,696 of them |
| **Segmenting on `U_Main_Group` across books** | 116–125 customers disagree, 92 % of it CALL CENTER vs CALL CENTRE ([C-0015]) |
| **Assuming a due date that differs from the term is an error** | it differs on 44 % of NET-30 Oil bills. Accounts edits it |
| **Parsing the imprest employee out of `CardName`** | 37 of 478 Oil names deviate, including a misspelled `JWLP`. Use `U_Emp_Code` |
| **Expecting a `NumAtCard` duplicate check on an imprest bill** | there is no vendor invoice number on those |
| **Creating a partner to unblock yourself** | you cannot, and shouldn't — 88 Oil names already collide. Three logins own this |
| **Trusting `profile-OCRD.md` for a field's absence** | see below |

### A caveat about the mined corpus itself

`_data/profile-OCRD.md` lists **234 of `OCRD`'s 437 columns**. Two reasons, both worth
knowing before you conclude "SAP does not have that field":

1. The profiler drops any column that is empty in *every* book. That is a feature — but
   it means `LicTradNum`, `VATRegNum`, `PymCode`, `Territory`, `frozenFrom/To` and ~200
   others are simply absent from the file rather than shown as dashes.
2. The field table is built from **Oil's** column list. So for Mart and Beverages a dash
   can mean "the column does not exist in that book". `U_WG_CardCode` reads
   `71 % / — / —` — but Mart and Bev do not *have* that column, and Beverages has
   `U_OIL_CardCode`, which the profile never mentions at all. Same for `U_TDS_RECOV`.

When a field matters, check `SYS.TABLE_COLUMNS` per schema before trusting a dash.

## 12. Open questions

- **Who maintains `U_WG_CardCode` / `U_OIL_CardCode`, and why is Mart excluded?** The
  crosswalk is real and 98.7 % accurate, but 998 Oil cards and 547 Bev cards have it
  blank and nothing links Mart at all. Is it an add-on, a one-off migration script, or
  hand-keyed? Closing query: `SELECT "UpdateDate", COUNT(*) FROM OCRD WHERE
  "U_WG_CardCode" <> '' GROUP BY "UpdateDate"` — I did not run it.
- **Why do 460 Oil↔Bev vendors have different codes when Oil↔Mart manages 10 %?** Two
  onboarding waves, or a different master-data owner per book. Unknown.
- **`CRD1.GSTType` values `5` and `6`** — one card each. SAP's India localisation uses
  this for composition / SEZ / overseas, but I did not confirm which is which. Do not
  build a rule on them.
- **Is "not MSME-flagged" the same as "not MSME"?** 279 of 2,235 Oil vendors carry a
  registration number. Whether the other 1,956 are genuinely non-MSME or just unrecorded
  I cannot tell from SAP, and the 45-day payment consequence is a legal inference, not a
  measurement.
- **What are the 5 same-name Oil/Bev pairs whose GSTINs disagree?** Either two genuinely
  different companies with the same trading name, or a keying error on one side. 5 cards
  — worth someone eyeballing.
- **Service Layer field names** for `DebPayAcct`, `GroupNum` and `CRD1` are quoted from
  `ap-rm-pm/bin/precheck.py`, which runs in production. I could not verify them live
  from this session — the Service Layer on `138.252.101.222:50000` is unreachable from
  here; only the HANA bridge is up. Treat the exact OData spellings as **unverified today**.
- **`CRD8` (27,194 Oil rows) and `CRD12` (6,829)** are populated and I did not open them.
  If a partner field seems missing, they are the next place to look.

## Which documents it touches

Every one of them, but especially: [[AP-Invoice]] · [[AP-Credit-Memo]] · [[GRPO]] ·
[[AR-Invoice]] · [[AR-Credit-Memo]] · [[Incoming-Payment]] · [[Outgoing-Payment]] ·
[[Journal-Entry]] · [[Purchase-to-Pay]]. Foundations it leans on:
[[Chart-of-Accounts]] · [[Numbering-Series]] · [[Cost-Centres-and-Dimensions]] ·
[[Document-Drafts]]. Still to write: [[Business-Places-and-Branches]] ·
[[Intercompany-and-Inter-branch]] · [[Staff-Imprest-Accounts]] · [[Add-on-Tables-and-UDFs]].

## Queries used

All read-only, all run 2026-08-24 through
`./hana-sql/hana-sql -env connections/hana-office-bridge.env`. Schemas
`JIVO_OIL_HANADB`, `JIVO_MART_HANADB`, `JIVO_BEVERAGES_HANADB`.

```sql
-- 1. master size, live vs frozen, control-account spread
SELECT "CardType", COUNT(*) total,
       SUM(CASE WHEN "frozenFor"='N' AND "validFor"='Y' THEN 1 ELSE 0 END) live,
       COUNT(DISTINCT "DebPayAcct") accts
FROM "JIVO_OIL_HANADB"."OCRD" GROUP BY "CardType";

-- 2. the four prefixes (digits collapsed to #)
SELECT REPLACE_REGEXPR('[0-9]+' IN "CardCode" WITH '#' OCCURRENCE ALL) shape,
       "CardType", COUNT(*) FROM "JIVO_OIL_HANADB"."OCRD"
GROUP BY REPLACE_REGEXPR('[0-9]+' IN "CardCode" WITH '#' OCCURRENCE ALL), "CardType";

-- 3. the BP numbering series
SELECT "Series","SeriesName","BeginStr","NextNumber","Locked"
FROM "JIVO_OIL_HANADB"."NNM1" WHERE "ObjectCode"='2';

-- 4. header tax fields are empty everywhere (0/0/0)
SELECT COUNT(*) n,
  SUM(CASE WHEN LENGTH(TRIM(IFNULL("LicTradNum",'')))>0 THEN 1 ELSE 0 END) lic,
  SUM(CASE WHEN LENGTH(TRIM(IFNULL("VATRegNum",'')))>0 THEN 1 ELSE 0 END) vatreg
FROM "JIVO_OIL_HANADB"."OCRD";

-- 5. where the GSTIN lives, and how many cards have one
SELECT COUNT(*) addr_rows, COUNT(DISTINCT "CardCode") cards,
  SUM(CASE WHEN LENGTH(TRIM(IFNULL("GSTRegnNo",'')))=15 THEN 1 ELSE 0 END) gst15,
  COUNT(DISTINCT CASE WHEN LENGTH(TRIM(IFNULL("GSTRegnNo",'')))=15
                      THEN "CardCode" END) cards_with_gst
FROM "JIVO_OIL_HANADB"."CRD1";

-- 6. cross-book party match on GSTIN: same code or not (repeat per pair)
WITH O AS (SELECT DISTINCT a."CardCode" C, TRIM(a."GSTRegnNo") G, d."CardType" T
           FROM "JIVO_OIL_HANADB"."CRD1" a
           JOIN "JIVO_OIL_HANADB"."OCRD" d ON d."CardCode"=a."CardCode"
           WHERE LENGTH(TRIM(IFNULL(a."GSTRegnNo",'')))=15),
     B AS (SELECT DISTINCT "CardCode" C, TRIM("GSTRegnNo") G
           FROM "JIVO_BEVERAGES_HANADB"."CRD1"
           WHERE LENGTH(TRIM(IFNULL("GSTRegnNo",'')))=15),
     P AS (SELECT O.C oc, O.T ot, B.C bc FROM O JOIN B ON O.G=B.G
           GROUP BY O.C, O.T, B.C),
     A AS (SELECT oc, ot, MAX(CASE WHEN oc=bc THEN 1 ELSE 0 END) same
           FROM P GROUP BY oc, ot)
SELECT ot, COUNT(*) matched, SUM(same) same_code,
       SUM(CASE WHEN same=0 THEN 1 ELSE 0 END) diff_code FROM A GROUP BY ot;

-- 7. same code, different party (and whether the GSTINs disagree)
--    full form in §3; the shape is OCRD JOIN OCRD on CardCode, then EXISTS over CRD1.

-- 8. the Oil<->Bev crosswalk fields
SELECT COUNT(*) filled,
  SUM(CASE WHEN EXISTS(SELECT 1 FROM "JIVO_BEVERAGES_HANADB"."OCRD" z
      WHERE z."CardCode"=TRIM(o."U_WG_CardCode")
        AND UPPER(TRIM(z."CardName"))=UPPER(TRIM(o."CardName"))) THEN 1 ELSE 0 END) hits
FROM "JIVO_OIL_HANADB"."OCRD" o
WHERE LENGTH(TRIM(IFNULL(o."U_WG_CardCode",'')))>0;

-- 9. groups, cards, and how many control accounts each group actually uses
SELECT g."GroupCode", g."GroupName", g."GroupType", COUNT(c."CardCode") bps,
       COUNT(DISTINCT c."DebPayAcct") naccts
FROM "JIVO_OIL_HANADB"."OCRG" g
LEFT JOIN "JIVO_OIL_HANADB"."OCRD" c ON c."GroupCode"=g."GroupCode"
GROUP BY g."GroupCode", g."GroupName", g."GroupType";

-- 10. group vs control account on real A/P, 365 days
SELECT g."GroupName", p."CtlAccount", COUNT(*) docs
FROM "JIVO_OIL_HANADB"."OPCH" p
JOIN "JIVO_OIL_HANADB"."OCRD" c ON c."CardCode"=p."CardCode"
JOIN "JIVO_OIL_HANADB"."OCRG" g ON g."GroupCode"=c."GroupCode"
WHERE p."DocDate">=ADD_DAYS(CURRENT_DATE,-365) AND p."CANCELED"='N'
GROUP BY g."GroupName", p."CtlAccount";

-- 11. the control account IS the card (all history, both ledgers)
SELECT COUNT(*) docs, SUM(CASE WHEN p."CtlAccount"=c."DebPayAcct" THEN 1 ELSE 0 END) m
FROM "JIVO_OIL_HANADB"."OPCH" p
JOIN "JIVO_OIL_HANADB"."OCRD" c ON c."CardCode"=p."CardCode";

-- 12. payment terms vs the due date SAP actually put on the bill
SELECT c."GroupNum", t."PymntGroup", COUNT(*) docs,
  SUM(CASE WHEN DAYS_BETWEEN(p."DocDate",p."DocDueDate")=t."ExtraDays"
           THEN 1 ELSE 0 END) matches_term
FROM "JIVO_OIL_HANADB"."OPCH" p
JOIN "JIVO_OIL_HANADB"."OCRD" c ON c."CardCode"=p."CardCode"
LEFT JOIN "JIVO_OIL_HANADB"."OCTG" t ON t."GroupNum"=c."GroupNum"
WHERE p."DocDate">=ADD_DAYS(CURRENT_DATE,-365) AND p."CANCELED"='N'
GROUP BY c."GroupNum", t."PymntGroup";

-- 13. TDS: flag vs code vs money (365 d)
WITH V AS (SELECT c."CardCode" cc, c."WTLiable" wl,
             CASE WHEN EXISTS(SELECT 1 FROM "JIVO_OIL_HANADB"."CRD4" x
                              WHERE x."CardCode"=c."CardCode")
                  THEN 'code' ELSE 'no code' END hc
           FROM "JIVO_OIL_HANADB"."OCRD" c)
SELECT V.wl, V.hc, COUNT(*) docs,
       SUM(CASE WHEN IFNULL(p."WTSum",0)<>0 THEN 1 ELSE 0 END) with_tds,
       ROUND(SUM(IFNULL(p."WTSum",0))/100000,2) tds_lakh
FROM "JIVO_OIL_HANADB"."OPCH" p JOIN V ON V.cc=p."CardCode"
WHERE p."DocDate">=ADD_DAYS(CURRENT_DATE,-365) AND p."CANCELED"='N'
GROUP BY V.wl, V.hc;

-- 14. the document GSTIN comes from the card's address
WITH A AS (SELECT DISTINCT "CardCode" C, TRIM("GSTRegnNo") G
           FROM "JIVO_OIL_HANADB"."CRD1"
           WHERE LENGTH(TRIM(IFNULL("GSTRegnNo",'')))=15)
SELECT COUNT(*) docs,
  SUM(CASE WHEN EXISTS(SELECT 1 FROM A
      WHERE A.C=p."CardCode" AND A.G=TRIM(x."BpGSTN")) THEN 1 ELSE 0 END) matched
FROM "JIVO_OIL_HANADB"."OPCH" p
JOIN "JIVO_OIL_HANADB"."PCH12" x ON x."DocEntry"=p."DocEntry"
WHERE LENGTH(TRIM(IFNULL(x."BpGSTN",'')))=15;

-- 15. inter-branch / intercompany account map, per book
SELECT "AcctCode","AcctName","CurrTotal" FROM "JIVO_OIL_HANADB"."OACT"
WHERE "AcctCode" LIKE '212%' AND LENGTH("AcctCode")=7;

-- 16. the imprest pattern
SELECT g."GroupName", COUNT(*) n,
  SUM(CASE WHEN c."CardCode" LIKE 'ORGV%' THEN 1 ELSE 0 END) orgv,
  SUM(CASE WHEN UPPER(c."CardName") LIKE '%IMPREST%' THEN 1 ELSE 0 END) has_imprest,
  SUM(CASE WHEN LENGTH(TRIM(IFNULL(c."U_Emp_Code",'')))>0 THEN 1 ELSE 0 END) has_empcode
FROM "JIVO_OIL_HANADB"."OCRD" c
JOIN "JIVO_OIL_HANADB"."OCRG" g ON g."GroupCode"=c."GroupCode"
WHERE g."GroupName" LIKE 'STAFF%' GROUP BY g."GroupName";

-- 17. C-0015 re-measured (same code AND same name = same party)
SELECT o."U_Main_Group" oil_tag, m."U_Main_Group" mart_tag, COUNT(*) n
FROM "JIVO_OIL_HANADB"."OCRD" o
JOIN "JIVO_MART_HANADB"."OCRD" m ON m."CardCode"=o."CardCode"
WHERE o."CardType"='C' AND m."CardType"='C'
  AND UPPER(TRIM(o."CardName"))=UPPER(TRIM(m."CardName"))
  AND IFNULL(o."U_Main_Group",'')<>IFNULL(m."U_Main_Group",'')
GROUP BY o."U_Main_Group", m."U_Main_Group";

-- 18. who creates partners
SELECT u."USER_CODE", u."U_NAME", COUNT(*) bps_90d
FROM "JIVO_OIL_HANADB"."OCRD" c
LEFT JOIN "JIVO_OIL_HANADB"."OUSR" u ON u."USERID"=c."UserSign"
WHERE c."CreateDate">=ADD_DAYS(CURRENT_DATE,-90)
GROUP BY u."USER_CODE", u."U_NAME";

-- 19. the corpus gap: 437 columns in OCRD, 234 in the profile
SELECT COUNT(*) FROM SYS.TABLE_COLUMNS
WHERE SCHEMA_NAME='JIVO_OIL_HANADB' AND TABLE_NAME='OCRD';
```
