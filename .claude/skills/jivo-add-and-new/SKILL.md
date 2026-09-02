---
name: jivo-add-and-new
description: USE AUTOMATICALLY whenever an Accounts operator hands over one or more vendor bills — a PDF, photo, scan or folder of them — even with no instruction at all, or only "enter this", "make this", "do these", "yeh karo". Entering a bill is not finished until the approver has it, so this runs after every A/P draft by default. Explicit triggers: "add and new", "add & new", "send it to Bhawani", "send for approval", "submit it", "don't show me the draft", "just add it". Also use when asked why a draft is not in the Approval Status Report, why an invoice posted without approval, or what AuthorizationStatus / ODRF.WddStatus means.
---

# Add & New — enter the bill AND send it to the approver

**The operator does not want to see the draft.** They want the bill entered and sitting
in **BHAWANI's** Approval Status Report (SAP user `USER03`, USERID 12). She is the
checker. Their job ends when she has it.

Proven end to end on 2026-08-26: draft 55331 (Royal Prime RPL/1217/2026-27, ₹5,664)
reached her as request **73093** with **zero** ledger impact, no human in the SAP client.

## Three doors, and only one is right

| Command | What it really does |
|---|---|
| `sapb1 draft <doctype>` | saves a draft the approver **NEVER sees** (`ODRF.WddStatus='-'`) |
| `sapb1 post <EntitySet>` | **LIVE, unapproved** (`dasWithout`) — straight into the ledger. **Never for a document.** |
| **`sapb1 add-draft <DocEntry>`** | the client's **Add** button. **This is the one.** |

`add-draft` **submits** a `dasWithout` draft — *but only if an approval template matches*.
If none matches, **SAP posts it live instead**. That is the whole trap (C-0034).

## Why a template might not match — and the fix that is already in place

SAP **deliberately skips** approval templates whose terms are **user queries** when the
document comes from the Service Layer or the DI API. All of JIVO's original A/P templates
(40, 41, 83, 96) are query-only, so none of them ever fires for a document this CLI makes.

**`API AP AUTO (USER39)` was created 2026-08-26 in all three companies** to close this —
`UseTerms='tNO'` (Terms = Always, no query), originator **USER39 only**, document type
**A/P Invoice only**, approver **USER03 BHAWANI**:

| Company | Template | Stage | USER39 is USERID |
|---|---|---|---|
| `JIVO_OIL_HANADB` | **103** | 13 | 53 |
| `JIVO_MART_HANADB` | **48** | 4 | 53 |
| `JIVO_BEVERAGES_HANADB` | **68** | 12 | **50** |

**So this flow works for A/P invoices created by USER39 — in Oil ONLY (measured 2026-09-02).**

**🔴 In Mart and Beverages `add-draft` POSTS LIVE.** The template exists in all three
books, but the company switch that lets an API submit reach *any* template —
*Enable Approval Procedures in DI* (`OADM.EnbApprDI`) — is **`Y` in Oil and `N` in Mart
and Beverages**. With it off, `DraftsService_SaveDraftToDocument` skips template 48 / 68
exactly as it skips the query templates, and the invoice lands in the ledger unapproved.
Caught on Mart draft 40127 (ARNAV ATS:395, ₹22,000) before the Add was sent: the draft was
left at `WddStatus '-'`, attached, and a person presses Add in the client — client-side
approvals in Mart are alive (136 A/P requests in the 30 days to 2026-09-02). Template 48
has raised **zero** requests, ever; that silence was the tell. **Check before every
add-draft outside Oil:**

```sql
SELECT "EnbApprDI" FROM "<COMPANY>".OADM;   -- must be 'Y', or add-draft posts live
```

The fix is a person ticking *Enable Approval Procedures in DI* in that company's General
Settings (Administration → System Initialization → General Settings, BP tab — verify the
tab on the first pass) and then re-measuring with the query. Until then, in Mart and
Beverages the CLI's job ends at the attached draft, and say so plainly.

**It does NOT cover anything else** — a credit memo, an outgoing payment, any other
document type, or any other login. Those have **no matching template**, so `add-draft`
would **post them live**. Stop and say so rather than trying. Check first:

```sql
SELECT t."WtmCode", t."Name" FROM "<COMPANY>".OWTM t
  JOIN "<COMPANY>".WTM3 d ON d."WtmCode"=t."WtmCode"
 WHERE t."Conds"='N' AND t."Active"='Y' AND d."TransType"=<ObjType>;
```

## The procedure

1. **Build the document exactly as its own skill says.** Do not hand-roll the payload.
   - vendor tax invoice for goods through the gate → **`jivo-ap-draft`**
   - fuel / transport / service / expense, no GRPO → **`jivo-ap-service-draft`**
   - vendor's credit note → **`jivo-ap-credit-memo`**
   Those skills own the paper-reading, the duplicate gate, the precedent field-diff, the
   series and the branch. This skill only adds the last step.
2. **Attach the bill** — `.claude/skills/jivo-ap-draft/reference/attachments-upload.md`.
   Do it **before** the Add. A live A/P invoice with no attachment is refused by JIVO
   guard **180021** `Please Attach its Receiving`.
3. **Preview the Add** (reads SAP, sends nothing):
   ```bash
   # Mac:      ACC_ENV=user39-oil.env acc/_playbook/sap add-draft <DocEntry> --dry-run
   # Windows:  cd sap-b1\accounts-kit  &  use.cmd oil  &  sapb1.exe add-draft <DocEntry> --dry-run
   ```
   Read the `WILL` lines. Show the operator the money and what it says.
4. **Send it:**
   ```bash
   # Mac:      ACC_ENV=user39-oil.env acc/_playbook/sap add-draft <DocEntry> --yes
   # Windows:  sapb1.exe add-draft <DocEntry> --yes
   ```
   **Many bills at once?** `add-draft` takes several DocEntries in one command — they are
   previewed together, confirmed once, then sent one at a time, stopping at the first
   problem. 21 bills worth ₹51.12 lakh went through this way on 2026-08-26 with zero
   posting live.
5. **Verify independently — the tool's word is not proof:**
   ```sql
   SELECT d."DocEntry", d."WddStatus", w."WddCode", w."WtmCode", u."USER_CODE"
   FROM "JIVO_OIL_HANADB".ODRF d
   JOIN "JIVO_OIL_HANADB".OWDD w ON w."DraftEntry"=d."DocEntry"
   JOIN "JIVO_OIL_HANADB".WDD1 s ON s."WddCode"=w."WddCode"
   JOIN "JIVO_OIL_HANADB".OUSR u ON u."USERID"=s."UserID"
   WHERE d."DocEntry"=<DocEntry>;
   -- want: WddStatus 'W', approver USER03
   SELECT COUNT(*) FROM "JIVO_OIL_HANADB".OJDT WHERE "TransType"=18 AND "BaseRef"='<DocNum>';
   -- want: 0 — nothing in the ledger
   ```
   Run via `hana-sql/hana-sql "<sql>"`. Report the draft number **and** the request number.

## What `ODRF.WddStatus` means

`-` never submitted (the approver cannot see it) · `W` **waiting — in her queue** ·
`Y` approved · `N` rejected · `C` cancelled.
Service-Layer equivalent: `Drafts(x).AuthorizationStatus` = `dasPending`.

## After she approves — say this out loud

**Approval does not post the document.** It becomes `dasApproved` and is *still a draft*;
a human presses Add a second time. Measured 2026-08-24: Oil had **78 approved A/P drafts
sitting unposted, ₹87.55 lakh**, `dasGenerated` zero. Never tell an operator the bill is
"done" at submission — it is *with the approver*, which is what they asked for.

## Hard stops

- **🔴 Never run `add-draft` in a company whose `EnableApprovalProcedureInDI` is `tNO`
  — Mart and Beverages as of 2026-09-02 (C-0074).** SAP consults approval templates for a
  DI-API / Service Layer Add only when General Settings → BP → *Enable Approval Procedures
  in DI* is on. Oil `tYES`, Mart `tNO`, Beverages `tNO` (CompanyService_GetAdminInfo,
  2026-09-02). Template 48 / 68 exist there and are never consulted: Mart draft 40128
  (DPTC bill 122, ₹88,951) posted LIVE as A/P invoice 12210 / JE 85639 with the preview
  saying "will be submitted for approval". `sapb1` built after 2026-09-02 refuses this
  itself (guard 5b, exit 9); older binaries on operator boxes do not. In Mart/Bev stop at
  the draft and tell the operator a person presses Add in the client — or an admin turns
  the flag on and the flow works as in Oil.

- **Never `sapb1 post` a document** to "just get it in". That is the 49987 mistake:
  ₹5,664 in the Oil ledger, unapproved, and no CLI can undo it — only SAP can Cancel it.
- **Never run `add-draft` on a document type with no Always template** — credit memos,
  outgoing payments, anything but an A/P invoice. It would post live. Use the query above.
- **Never re-run `add-draft` on a `dasPending` draft.** It is already in somebody's queue;
  adding it again raises a SECOND request and takes the first out from under them. The
  command refuses this, and there is no override.
- **Never test on HTTP 204.** `Prefer: return-no-content` makes *every* create return 204,
  including a live post. Judge on the `Location` header and the SQL above.
- **`add-draft` cannot be undone from this CLI**, and it never approves on anyone's behalf.
- **Never write unprompted** (RULE 0). Asked = do it. Not asked = don't touch it.

## Known side effect

Template 103 also catches the ~20 A/P invoices a month USER39 keys **by hand** in the
client, which already match template 41 — so Bhawani sees **two requests** for those.
Harmless, and the fix when it matters is a dedicated robot login. Mention it if she asks.

Full background: `acc/ADD-AND-NEW-PLAN.md`. Correction: **C-0034**.
