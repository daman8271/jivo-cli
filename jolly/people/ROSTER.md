---
title: JIVO people roster
type: moc
org: JIVO
source: "WhatsApp — Gurvinderjeet Singh, 2026-08-11 18:23–18:31 IST"
verified_against: [JSAP hierarchy, SAP B1 ×3 DBs, factory app, OMS, prior repo work]
last_verified: 2026-08-11
status: 9-of-10-confirmed
tags: [jivo/moc, jivo/people]
---

# JIVO people roster

> [!danger] Private — never commit
> `jivo-cli` is a **public GitHub repo**. `jolly/.gitignore` excludes `people/`
> so this folder stays on the laptop. Real names, phone numbers and reporting
> lines must never land in a public repo. Do not `git add -f` them.

**What this is.** The address book the coordination pilot dispatches against —
who to message, on which number, in what language, and who to chase when they
don't reply.

**Where it came from.** [[Gurvinderjeet Singh]] sent ten contact cards over
WhatsApp on **11 Aug 2026, 18:23–18:31 IST**, each followed by a one-line role.
Every one of those ten was then checked against **JSAP's org hierarchy**, **SAP
B1 across all three company databases**, **the factory app**, **OMS**, and
everything already written in this repo.

**Result: 9 of 10 confirmed, 1 not found, 2 role labels contradicted.**

---

## The ten

| Person | Real name | Role — his words | What the systems say | ✓ |
|---|---|---|---|---|
| [[Preshit Singh]] | Preshit Thakur | Monthly planning and billing head | **Sub-HOD, Accounts › A/R, 14 reports.** Billing in SAP; **planning by hand in Excel** | ✅ |
| [[Kamaldeep Singh\|Kamal]] | Kamaldeep Singh | Ecom monthly planning | **Sub-HOD, ECom › Supply Chain**, under Prabhu | ✅ |
| [[Prince Bathinda]] | — | Mart FG storage | **Nothing, in any system.** Also **out of scope** — Mart | ❌ |
| [[Honey Factory\|Honey]] | Honey Gupta | Wellness FG storage | Factory warehouse manager; 149 FG moves in 90d | ✅ |
| [[Gautam]] | Gautam Chanana | Production incharge | **6,003 production orders — 12× anyone else.** Runs the floor | ✅ |
| [[Raju Veerji]] | Jasbir Singh | Production incharge | **Responsible for production + HOD Dispatch + signs the factory's money** | ✅ |
| [[Ziyaul]] | Ziyaul Haque | SAP admin | **HOD over Accounts + Audit + IT; SAP superuser** | ✅ |
| [[Gurpreet Singh Gopi\|Gopi]] | Gurpreet Singh | Oil tracker | Executive, Accounts & Finance | ✅ |
| [[Shunty Veerji]] | Ravinder Singh | Oil purchaser | **HOD Accounts — and ₹28.77 Cr of oil POs in 90d** | ✅ |
| [[Gagan PU]] | Gagandeep Singh | Ecom Warehouse manager | **Sub-HOD ECom; 54% of Mart's deliveries** | ✅ |

Plus two people **not** in the ten who belong here:

- [[Gurvinderjeet Singh]] — the source of the list. **HOD, EA.** Never sent his own card.

---

> [!important] Scope: **Oil only** (Daman, 11 Aug). No Beverages.
> **[[Prince Bathinda]] and [[Gagan PU]] are both Mart — out.** The two HODs are
> parked. **[[Ravinder Jivo]]** added as PM (packaging material) Purchase incharge.
> Ten people in scope. See **[[SCOPE]]**.

## Added 11 Aug

| Person | Role | Why it matters |
|---|---|---|
| **[[Ravinder Jivo]]** | **PM Purchase incharge** — packaging material | Fills the **biggest hole in the chain**. `JWPL0695`, phone verified, contact on a **carton corrugator**, **₹2.17 Cr of packaging POs in 6 months** |

And a system nobody had mentioned: **[[../findings/2026-08-11-ji-production-mes|ji.jivo.in]]** —
a full production MES for Jivo Oil that already holds machine capacity, OEE,
downtime, waste, and a **Plan vs Production** report.

> [!important] What this vault is *for*
> Daman, 11 Aug: the system holds the whole plan so nobody else has to. Each
> person gets **the one instruction that is theirs, at the moment it matters** —
> and the system knows who to chase when something goes wrong.
>
> That makes the blank **"Owns"** field on every note the actual product. Job
> titles don't route an order; **authority does**. See **[[DISPATCH-RULES]]**.

## Start here

- **[[DISPATCH-RULES]]** — **the point of all this.** Event → person → message → chase → escalate. Ten rules; three are worth building first.
- **[[SCOPE]]** — **Oil only.** The chain worked step by step: what each link needs, who owns it, and where it breaks.
- **[[ORG-CHART]]** — the real reporting line, pulled live from JSAP. Who signs what, and the approval chain.
- **[[MISSING-PEOPLE]]** — **who is missing and why it matters.** 9 of JIVO's 13 HODs are not in this roster.
- **[[ASK-GURVINDERJEET]]** — the questions, ready to paste into WhatsApp.
- **[[functions/The Five Departments|The Five Departments]]** — the official org shape, and where the roster fails to cover it.

---

## Corrections from Daman, 11 Aug — read these first

| The check said | Daman's correction |
|---|---|
| Machine capacity **exists in no system** | **Wrong — there is a separate engine.** `ji.jivo.in` is a full production MES holding runs per line, OEE, downtime and waste. I searched SAP, JSAP and the factory app and concluded from three systems that a fourth didn't exist |
| Packaging procurement has **no owner** | **[[Ravinder Jivo]] — PM Purchase incharge.** Verified in SAP |
| [[Prince Bathinda]], [[Gagan PU]] | **Both Mart. Out of scope** |
| The bosses (Avtar Vg, Prabhu) | **Not part of this.** Parked |

**Method note worth keeping:** "not found in the systems I know about" is not
"does not exist". Before declaring data absent, ask which systems exist — the
roster of systems is itself a question, not something to infer from what happens
to be wired up on this laptop.

### Earlier the same evening

| The check said | Daman's correction |
|---|---|
| [[Preshit Singh]]'s "monthly planning" is uncorroborated | **He does plan — manually, in Excel.** The absence of a system trace *is* the finding, not a doubt about him |
| The OMS `prince` (Punjab manager, ₹14.9 Cr) looks like [[Prince Bathinda]] | **Completely different person.** Do not match |
| The OMS `gagan` (Beverages rate approver) might be [[Gagan PU]] | **Completely different person.** Do not match |
| [[Raju Veerji]] is not a production incharge | **He is responsible for production** — *and* dispatch, *and* the factory budget |

Both wrong guesses were **name matches**. Both were flagged as inferred rather
than confirmed, and both still wasted a look. The rule stands and is now proven
twice: **match on employee code or phone number, never on a name.**

## What the check overturned

### 1. "Wellness" — solved ✅
From SAP's own company table: **two legal entities, three sets of books.**
`JIVO_OIL_HANADB` and `JIVO_BEVERAGES_HANADB` are both **JIVO WELLNESS PVT LTD**;
`JIVO_MART_HANADB` is **JIVO MART PVT LTD**. Every employee code starts `JWPL` —
*Jivo Wellness Pvt Ltd*. So [[Honey Factory|Honey]] keeps the **main company's**
FG store, and [[Prince Bathinda|Prince]] keeps the other entity's.

### 2. [[Raju Veerji]] does much more than the label says ✅
He is responsible for production (Daman confirmed) **and** he is JSAP's **HOD of
Dispatch**, **and** he holds the largest customer book in SAP (39 customers),
**and** he is the company's busiest approver — **94 budget approvals in July**,
sole stage-1 sign-off on the *Factory*, *Factory Common* and *Delivery
Bhakharpur* budget heads.

He has no production orders of his own because he does not *operate* production —
he is answerable for it. **A method note: inferring his job from activity volume
got him wrong.** Volume finds operators, not the people they answer to.

### 3. The two production men are a hierarchy, not a split ✅
Not two incharges divided by plant or line — **two levels**. [[Gautam]] runs the
floor: factory app login, FACTORY department, 6,003 production orders, zero spend
authority, absent from the JSAP org tree. [[Raju Veerji]] sits above: responsible
for production, owns dispatch, signs the factory's money.

That is a clean escalation path, and the first one this roster has produced:
**floor → [[Gautam]] → [[Raju Veerji]] → money released.**

### 4. [[Prince Bathinda]] exists in no system at all ❌
No phone match, no JSAP record, no factory login, no OMS account, and **no trace
in Mart's finished-goods movement** (which is run by *Param Billing*, *Aqib* and
*Jaspal Singh*). The one promising lead — an active Punjab-state OMS manager
called Prince — **Daman has ruled out as a different person.**

He is also **out of scope**: Mart FG storage, and the pilot is Oil-only. Park him.
If he comes back into scope, **ask Gurvinderjeet for his employee code first** —
name matching on "Prince" has now produced a wrong answer, and there are five
others in the data.

### 5. The Gagan question — settled ✅
**Two different Gagans.** The one who quoted ₹1.8 Cr for the 50 TPD mustard mill
is **Gagan International, a Ludhiana oil-mill equipment manufacturer** — a
company, not a person. Nothing to do with [[Gagan PU]]. (~93% confident.)

### 6. The monthly plan lives in Excel, not in any system 🔴
[[Preshit Singh]] does plan the month — **by hand, in a spreadsheet** (Daman
confirmed). That is why no system search found it, and it is the most important
thing this whole exercise turned up.

The plan is the **first link in the chain** and it has no source the pilot can
read: a workbook on a Windows account called `Jivo112`, in a `Downloads` folder,
whose e-com column is a `VLOOKUP` into another Excel file on another machine —
where a missing SKU silently becomes zero. The file also **disagrees with
itself**: 4,156 T on one sheet, 4,390 T on another, 3,661 T in its own pivot, with
no stated plan of record.

Everything downstream inherits that. See [[SCOPE]], step 1.

---

## The blanks that still block dispatch

1. **Nobody's authority is recorded.** Ten roles, zero decision rights. And what
   the approval data shows is worse than unknown: the chain is **one stage deep
   with no monetary limits** — [[Raju Veerji|Jasbir]] approved everything from
   ₹250 to ₹6,00,210 through the same single stage with no second signature.
2. **No escalation paths.** Provisionally [[Gurvinderjeet Singh]] for everyone,
   but he never said so.
3. **[[Gurvinderjeet Singh]] has no number here.** He sent everyone else's card
   and not his own. One weak candidate: `9319379079`, unverified.
4. **Three phone numbers match nothing in any system** — [[Gautam]]'s,
   [[Gurpreet Singh Gopi|Gopi]]'s and [[Prince Bathinda|Prince]]'s.
5. **One number is claimed twice.** `8146140596` is [[Gagan PU]]'s on his card
   and on the Flipkart seller account — but the factory gate log has the same
   number under *"Kamaldeep veer ji"*. **That is the number a dispatch system
   would text.**
6. **Machine capacity exists nowhere.** No system holds it; no person is attached
   to any of the six production lines. It has to come from [[Gautam]].
7. **Language, register and working hours** — unknown for all ten.

---

## Traps worth remembering

- **Match on employee code or phone, never on name.** The data holds **four
  Princes**, **six Ravinder Singhs**, **five Gurpreets**, **four Gagans** and
  **two Shuntys**.
- **Spelling drifts systemically:** ZIYAUL / ZIAUL / ZIA · JASBIR / JASVIR ·
  PRESHIT SINGH / PRESHIT THAKUR · GURVINDERJEET / GURWINDERJEET / Gurinder.
- **`BH-PS`, `DL-PS`, `PB-PS` are not [[Preshit Singh]].** *Preshit* (प्रेषित)
  means *dispatched* — these are langar/samagam free-issue warehouses. ~30 stock
  rows false-positive on any name search.
- **[[Ziyaul]] works through the shared `manager` superuser account**, so every
  action he takes in SAP is attributed to "manager" — and so is anyone else's
  with those credentials. He also runs the Audit department.
- **Two employee codes for one man, twice over:** [[Raju Veerji]] is `JWPL000C`
  in JSAP but `JWPL0147` in SAP and DSR; [[Honey Factory|Honey]] holds two
  factory logins with two codes.

---

## Log

- **2026-08-11 18:23–18:31** — [[Gurvinderjeet Singh]] sent ten contact cards
  with one-line roles over WhatsApp.
- **2026-08-11 evening** — roster built, then every name cross-checked against
  JSAP, SAP B1 (×3), the factory app, OMS and the repo's prior work. 9 of 10
  confirmed; [[Prince Bathinda]] not found; [[Raju Veerji]]'s and
  [[Preshit Singh]]'s stated roles partly contradicted. "Wellness" and the
  "two Gagans" question both resolved.
