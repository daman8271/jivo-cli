---
name: jivo-add-and-new
description: USE AUTOMATICALLY whenever an Accounts operator hands over one or more vendor bills — a PDF, photo, scan or folder of them — even with no instruction at all, or only "enter this", "make this", "do these", "yeh karo". Entering a bill is not finished until the approver has it, so this runs after every A/P draft by default. Explicit triggers: "add and new", "add & new", "send it to Bhawani", "send for approval", "submit it", "don't show me the draft", "just add it". Also use when asked why a draft is not in the Approval Status Report, why an invoice posted without approval, or what AuthorizationStatus / ODRF.WddStatus means.
---

# Add & New — enter the bill AND send it to the approver

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
`UseTerms='tNO'` (Terms = Always, no query), document type **A/P Invoice only**, approver
**USER03 BHAWANI**. On **2026-09-10** Daman asked for Divjot to get Add & New too, so
**USER08 (DIVJOT) was added as a second originator** on all three:

| Company | Template | Stage | Originators (read back 2026-09-10) |
|---|---|---|---|
| `JIVO_OIL_HANADB` | **103** | 13 | `USER39` (USERID 53) + `USER08` (17) |
| `JIVO_MART_HANADB` | **48** | 4 | `USER39` (53) + `USER08` (17) |
| `JIVO_BEVERAGES_HANADB` | **68** | 12 | `USER39` (**50**) + `USER08` (17) |

**So this flow works for A/P invoices created by USER39 (MUQEEM) or USER08 (DIVJOT), in
ALL THREE books** — measured 2026-09-10, superseding the Oil-only reading of 2026-09-02.

**Both halves had to be true, and now both are.** The company switch that lets an API
submit reach *any* template — *Enable Approval Procedures in DI* (`OADM.EnbApprDI`) — was
`Y` in Oil and `N` in Mart and Beverages on 2026-09-02, which is why Mart draft 40128
(DPTC bill 122, ₹88,951) posted LIVE as A/P invoice 12210 / JE 85639. An admin has since
turned it on: **`Y` in all three books, read 2026-09-10.** Verified end to end rather than
from the flag alone — `add-draft --dry-run` as USER39 on Mart draft 39829 and Bev draft
16056 both raised zero DI-approval problems and printed *"would be submitted for
approval"*.

**You do not have to check this by hand — guard 5b reads the flag live on every run** and
refuses the submit itself if a company is ever switched back off. If you want to see it:

```sql
SELECT "EnbApprDI" FROM "<COMPANY>".OADM;   -- 'Y' in all three as of 2026-09-10
```

**🔴 What has NOT changed: any other login still posts LIVE.** Mart 48 and Bev 68 name
USER39 and USER08 and nobody else. **Oil 103 also names USER07 (HARSH) since 2026-09-16**
(Daman: "do it for Harsh also"). USER19 is on **no** Always-terms template in any book, and
USER07 is on none in Mart or Beverages. The Shahrukh and Vishal desks (both USER07) stay
**drafts-only by desk policy** (`harness/desks.json`) — the template reason for that policy is
gone in Oil, and Daman kept the policy anyway on 2026-09-16: "let him make only drafts pls".
Do not lift it because a template now names USER07. Guard 5c refuses the rest
before anything is sent (exit 9) — leave the draft attached and let a person press Add in
the SAP B1 client, which does consult the query templates.

**It does NOT cover anything else** — an outgoing payment, any other document type, or
any other login. (Oil 103 also lists A/P Credit Memo since 2026-09-15, but that only
matters for an Add in the SAP client — `add-draft` itself still takes A/P invoice drafts
only.) Those have **no matching template**, so `add-draft`
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

**And say which lane it lands in after her.** Once Bhawani approves and Accounts
make the ledger, the document either gets posted that day or waits again for the
above-office **budget** approval in JSAP. Operators cannot tell the two apart, so
they hold the whole pile for the slowest bill. Name it:

```bash
python3 .claude/skills/jivo-ap-draft/bin/jsap_route.py <DocEntry> --company oil -v
python3 .claude/skills/jivo-ap-draft/bin/daily_sort.py --company oil   # the whole pile, in trays
```

**`daily_sort.py` is the one to run when an operator asks "what can we post?"**
It separates *approved and needs nothing else* from *approved but still waiting
on JSAP* — the split Accounts could not see, which is why they waited for the
whole batch instead of releasing the bills that were never held up.

RM/PM drawn from a GRPO is **POST NOW** and must not be held behind the service
bills; a `56xxxxx` expense line with a Budget dimension **WAITS IN JSAP**. Nothing
auto-approves in JSAP right now (no FY26-27 allocation loaded — 586 of 587
documents refused in the 30 days to 2026-09-04), so a JSAP document waits for a
person. Rule, accuracy and traps: **`jivo-ap-draft/reference/jsap-routing.md`**.

## Hard stops

- **🔴 Never run `add-draft` in a company whose `EnableApprovalProcedureInDI` is `tNO`.**
  As of **2026-09-10 all three are `tYES`**, so this no longer blocks Mart or Beverages
  (C-0088, superseding C-0074) — but the rule stands because the flag is a checkbox a
  person can untick. Guard 5b reads it live and refuses, so trust the guard, not this
  paragraph. History, for why the guard exists: Oil `tYES`, Mart `tNO`, Beverages `tNO`
  (CompanyService_GetAdminInfo, 2026-09-02). Template 48 / 68 existed there and were never
  consulted: Mart draft 40128
  (DPTC bill 122, ₹88,951) posted LIVE as A/P invoice 12210 / JE 85639 with the preview
  saying "will be submitted for approval". `sapb1` built after 2026-09-02 refuses this
  itself (guard 5b, exit 9); older binaries on operator boxes do not. In Mart/Bev stop at
  the draft and tell the operator a person presses Add in the client — or an admin turns
  the flag on and the flow works as in Oil.

- **Never `sapb1 post` a document** to "just get it in". That is the 49987 mistake:
  ₹5,664 in the Oil ledger, unapproved, and no CLI can undo it — only SAP can Cancel it.
- **Never run `add-draft` on a document type with no Always template** — credit memos,
  outgoing payments, anything but an A/P invoice. It would post live. Use the query above.
- **Never run `add-draft` from a login the template does not name.** Only USER39 (MUQEEM)
  and USER08 (DIVJOT) are originators. Guard 5c enforces it and there is no flag; the
  `SAPB1_APPROVAL_TEMPLATE` env override is an assertion that an **admin has widened the
  template**, not a way past the refusal — set it wrongly and the Add posts live.
- **Never re-run `add-draft` on a `dasPending` draft.** It is already in somebody's queue;
  adding it again raises a SECOND request and takes the first out from under them. The
  command refuses this, and there is no override.
- **Never test on HTTP 204.** `Prefer: return-no-content` makes *every* create return 204,
  including a live post. Judge on the `Location` header and the SQL above.
- **`add-draft` cannot be undone from this CLI**, and it never approves on anyone's behalf.
- **Never write unprompted** (RULE 0). Asked = do it. Not asked = don't touch it.

## The double-request side effect — FIXED in Oil 2026-09-15

Until 2026-09-15 an A/P invoice Added **from the SAP client** by USER39 or USER08 matched
template 103 (Always) AND the condition-based "USER03 AP" templates (Oil 40 / 41) — all
three route to stage 13 = USER03 — so Bhawani got **two requests for one draft**, and the
draft posted only when she approved both. Measured live 2026-09-15: 23 Oil A/P drafts
carrying two open requests (15 × 41+103, 8 × 40+103). The CLI's own submit was never
the cause: a Service Layer Add consults only the Always template.

Fix applied 2026-09-15 (Daman, write log `queries/daman/sap-writes.jsonl`): Oil 103 now
lists **A/P Credit Memo** as well as A/P Invoice, and **USER08 and USER39 were removed as
originators from Oil 40 and 41** — so their A/P invoices and credit memos reach Bhawani
through 103 alone, from either route. Read back: 40 = 32 originators, 41 = 37, neither
names 17 or 53. Requests that already existed stay: Bhawani approves both on those.

Mart (template 17 "USER03 AP" + 48) and Beverages (1 "USER03 AP" / 2 "USER03 INVOICE"
+ 68) had the same overlap — 20 and 2 doubled drafts on 2026-09-15 — and still do until
the same change is made there. Check `ApprovalTemplates` before assuming.

Full background: `acc/ADD-AND-NEW-PLAN.md`. Correction: **C-0034**.
