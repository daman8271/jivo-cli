# "Add & New" — the answer, and what is left to do

**2026-08-26.** Goal: an operator drops a vendor bill PDF, the system does everything,
and the document lands in **Bhawani's approval queue** exactly as if a human had pressed
**Add & New** in the SAP B1 client. No draft for the operator to review. No live posting
that skips her.

Two workflows, 70 agents, 7.8M tokens, 2,499 tool calls, every finding adversarially
verified. Then re-verified by hand — everything below was re-run read-only before being
written down.

---

## THE ANSWER

**The submit button already exists in our CLI: `sapb1 add-draft`.**
It calls `DraftsService_SaveDraftToDocument` — literally SAP B1 → Document Drafts → Add.
It has **never been run** (0 entries in every operator's write log).

**But running it on an A/P invoice today would post the document LIVE, not submit it.**
Its own help says so:

> `dasWithout` → Add SUBMITS it for approval. Nothing enters the ledger — **unless no
> approval template matches the document, in which case SAP posts it live.**

And for an API-created A/P invoice, **no template matches**. That is the whole problem.

### Why no template matches (root cause, ~95%)

**SAP deliberately skips approval templates whose conditions are user queries when the
document comes from the Service Layer or the DI API.** SAP Support, verbatim:

> "Unfortunately, there is no workaround. It is a limitation in the DI API and Service
> Layer. The reason why it is not possible to trigger Approval Procedures based on User
> Queries via DI API and Service Layer is that it is not possible to get the correct value
> of ApprovalTemplatesID … when the Approval Procedures is based on User Queries."
> — ANKIT_CHAUHAN, Product and Topic Expert, SAP Business One Support, community.sap.com

All 8 active A/P templates across JIVO's three companies are **query-only**. `WTM4`
(predefined terms) is **empty in all three company DBs**. So none of them can ever fire
from an API. Invoice **49987** was not a fluke — it is the single unexplained escape in
888 service A/P invoices over 90 days, and its only distinguishing property is
`DataSource='S'`.

### Two of my theories were killed — good

| My theory | Verdict |
|---|---|
| Rewrite conditions to `$[TABLE.FIELD]` instead of `$[$3.1]` | **DEAD.** `$[TABLE.FIELD]` is *also* a form/FMS reference and fails identically. Proven by SAP's own syntax docs and a 2012 SAP note. |
| DI API on a Windows box (my front-runner) | **DEAD.** Same SAP limitation, word for word — "DI API **and** Service Layer". A Windows box would have hit the same wall after days of work. |

---

## THE FIX — proven on this very server

**An approval template whose Terms = "Always"** (`OWTM.Conds='N'`, no WTM5 query) **is
honoured by the Service Layer.** SAP names "Always" as the workaround, and JIVO already
runs one in production:

**Template 67 "Delivery Approval"** — `Conds='N'`, 0 queries, 0 terms:

| Evidence | Value |
|---|---|
| API-created documents it caught | **29** (`DataSource='S'`, UserSign 2 = B1i) |
| Fired at add time? | **Yes** — OWDD `CreateTime` = draft `CreateTS` to the minute (18:59/185923, 17:38/173840) |
| Result | `ODRF.WddStatus='W'`, still waiting, **none posted** |
| Negative control | same B1i login, same period, 28 A/R invoices against 21 *query-conditioned* templates → **0 caught** |

**Unconditional template: 29/29 caught. Query-conditioned: 0/28.** That is the experiment
already run, on JIVO's own data.

Someone at JIVO probed this before and never wrote it down — those drafts carry Comments
`"TEST B1I AUTH CHECK"`, `"TEST AUTH"`, `"MARKETPLACE APPROVAL PROBE"`.

---

## The full flow, once the template exists

```
PDF ─► read paper ─► precedent-diff ─► POST /Drafts ─► attach ─► sapb1 add-draft
                                                                       │
                                                            template matches → SUBMITTED
                                                                       ▼
                                                     ODRF.WddStatus='W' → BHAWANI
                                                                       │
                                                              she approves → dasApproved
                                                                       ▼
                                                        a human presses Add AGAIN → posts
```

**Approval does not post the document.** Counted live 2026-08-24: Oil had **78 open A/P
drafts sitting at `dasApproved`, ₹87.55 lakh**, and `dasGenerated` was **zero**. Nothing
auto-posts. So the operator's job ends at submission — which is exactly what was asked
for — and step 3 stays a human's.

---

## Verifier — the pass/fail test

```sql
-- submitted, in her queue, NOT in the ledger:
ODRF.WddStatus = 'W'  AND  OWDD row Status='W' approver USER03 (12)  AND  no OJDT row
```

`ODRF.WddStatus` on Oil ObjType-18 drafts: `-` never submitted (14,341) · `W` pending (73)
· `Y` approved (72) · `N` rejected (67) · `C` cancelled (818).
Cross-check on the Service Layer: `Drafts(x).AuthorizationStatus` = `dasPending`.

**A safety bug the verifiers caught in my own test design:** I was going to treat
`HTTP 204` as "submitted". SAP's own guide (`Working_with_SAP_Business_One_Service_Layer.pdf`
§3.5.5, on the SAP server) shows `Prefer: return-no-content` turns **every** successful
create into 204 — **including a live ledger post**. That test would have masked exactly the
dangerous outcome. Send **no** `Prefer` header and judge on the `Location` header plus SQL:
live → `201 Location: …/PurchaseInvoices(n)`; submitted → `Location: …/Drafts(n)`.

---

## What is left — one decision, then it is mostly wiring

### Decision needed: create ONE approval template

| | |
|---|---|
| **Shape** | Terms = **Always** (`Conds='N'`, no query), Documents = **A/P Invoice (18)** only, Stage = **13** (existing → BHAWANI), Originators = **USER39 only** |
| **How** | `ApprovalTemplates` accepts POST from our CLI — or a human does it in Administration → Approval Procedures (safer, and it is shared config) |
| **Blast radius** | It also catches every A/P invoice **USER39 keys in the client by hand** — 15 in August. Nobody else is affected. Existing templates 40/41 are untouched, so the other ~35 originators and ~25–45 daily requests carry on unchanged. |
| **Test first** | `TEST_JIVO_OIL_HANADB` exists — 94 templates, 16,194 A/P invoices, newest dated 2026-08-25. A near-live sandbox. **Blocked: its passwords differ per company (C-0031) and we do not have one.** |

### Then (mechanical)

| # | Phase | Status |
|---|---|---|
| 2 | Create the Always template (sandbox → live), verify with the SQL above | **needs the decision** |
| 3 | One supervised end-to-end run: draft → attach → `add-draft` → confirm `WddStatus='W'` | queued |
| 4 | Auto-intake pipeline: PDF → tiles → classify (GRPO? goods vs service) → precedent-diff → payload → attach → `add-draft` → verify → one-line report | queued |
| 5 | Fix `readback.py`'s two false positives on service lines (no-GRPO, TDS-0) | queued |
| 6 | Record the correction; package as a skill | queued |
| 7 | Ship to operators | queued |

---

## What we must never do

- **`sapb1 post PurchaseInvoices`** — bypasses approval, `dasWithout`, straight to the
  ledger. This is what put 49987 in the books.
- **Run `add-draft` on an A/P invoice before the Always template exists** — same outcome,
  because no template matches.
- **Edit templates 40 or 41** — 966 and 960 requests in 90 days. Touching them touches
  every A/P operator in the company.
- **INSERT into OWDD/WDD1 to fabricate a request** — assessed and rejected as unsupportable.

## SAP state to clean up

- **49987** — posted live A/P invoice, ₹5,664, unapproved. Cancel it in the client
  (Purchasing → A/P Invoice → DocNum 626084197 → Cancel). No CLI can do this.
- **55296** — draft `WddStatus='C'`, but **request 73069 is still `W` in Bhawani's queue**
  pointing at it. She should clear it, or say the word and it can be deleted (`--in-approval`).
- **55297** — ✅ deleted, verified gone.
