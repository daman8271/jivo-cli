---
title: Who is missing from the roster
type: gap-analysis
org: JIVO
method: "Gurvinderjeet's 10 names ⨯ JSAP hierarchy ⨯ SAP activity ⨯ the brief's five departments"
last_verified: 2026-08-11
status: open
tags: [jivo/gap, jivo/people]
---

# Who is missing from the roster

> [!important] Scope changed 11 Aug: **Oil only, no Beverages**
> This list was built before that call. For the Oil-only shortlist, read
> **[[SCOPE]]** — it is shorter and it is the one to act on.
>
> **Dropped by the scope change:** Atul Sharma (ran 100% of *Beverages*
> production) · Param Billing and Aqib (both *Mart*) · [[Prince Bathinda]] (Mart).
>
> **Still needed for Oil, in priority order:** a **packaging procurement owner**
> (there is none, and cartons are the ~27-day bottleneck) · **Avtar Vg**
> `JWPL0014` · **Pankaj** and **Shahrukh** (the Oil production bench) ·
> **Lovpreet Singh** (`exim`, keys in all of Shunty's POs) · **Prabhu**
> `JWPL2217` if the e-com half of Oil is in scope.

---

## The full cross-check (all companies)

Gurvinderjeet gave ten names. Cross-checking them against **JSAP's 223-person
hierarchy**, **SAP's actual transaction activity**, and **the five departments
named in the brief** shows what the ten do not cover.

The headline: **the roster is Accounts-heavy and plant-light.** Four of the ten
sit in Accounts & Finance. Two of the five departments the brief names have
nobody at all. And the people who do most of the physical work in SAP are, with
two exceptions, not on the list.

---

## Tier 1 — named individuals, blocking

These are real people we can name from the data, whose absence breaks something.

### 1. Avtar Vg — HOD, Accounts & Finance · `JWPL0014`
**[[Preshit Singh]] reports directly to him.** He also approved **46 budgets in
July**, is the salesperson of record on [[Shunty Veerji|Shunty]]'s SAP master, and
is the **#2 production-order creator in Oil** (203 in 90 days, 510 all-time).
Accounts, approvals and production at once — a genuine hub, and the boss of the
roster's biggest team. **Get his number.**

### 2. Prabhu — HOD, ECom · `JWPL2217`
**Both e-commerce people report to him** — [[Kamaldeep Singh]] and [[Gagan PU]].
Nothing about e-com planning or e-com dispatch can be settled without him. He
appears in SAP's order-in-hand breakdown as "PRABHU SIR". **Get his number.**

### 3. Atul Sharma — Beverages production
**He created every single one of Beverages' 209 production orders in 90 days —
100%.** Gurvinderjeet named two production incharges and neither is him. If the
pilot plans Beverages at all, this is the man it must talk to. **Not in the roster.**

### 4. Param Billing — Mart finished-goods movement
**Moves Mart's finished goods in reality** — 1,000+ transfer lines
`BH-FGM → DL-INT → DL-FG`. [[Prince Bathinda]] was named for "Mart FG storage"
but appears nowhere in Mart's stock movement; **Param does the work in the
system.** Whoever a Mart stock question should reach, the data says it is him.

### 5. Aqib — Mart dispatch, #2 behind Gagan
**268 of Mart's 673 delivery notes (40%)**, and he works the `DL-MP → DL-EC` leg
that feeds [[Gagan PU]]'s e-com warehouse. Gagan's natural deputy or counterpart.

### 6. Lovpreet Singh (`exim`) — types every one of Shunty's POs
[[Shunty Veerji|Shunty]] has **no SAP login**; all 25 of his ₹28.77 Cr of oil POs
were keyed in by Lovpreet. A message about a purchase order may need to reach
both of them.

### 7. Prabhjot — one of only three `Request Approver` accounts in JSAP
The other two are [[Ziyaul]] and [[Gurvinderjeet Singh]]. If approvals are going
to be automated, all three matter.

### 8. Shahrukh — the sole `Request Initiator`, dept FACTORY
**The only account in JSAP that can raise a request.** Also created 81 Oil
production orders. A single point of failure sitting in the plant.

### 9. Pankaj — Oil production, #3
155 Oil production orders in 90 days. Part of the real production bench behind
[[Gautam]].

### 10. Navneet Singh (`navi@2026`) — holds 60% of every customer in OMS
**515 of OMS's 854 party assignments — 60.3%**, against 32 users who hold the
rest and 23 who hold none. Whatever "who owns which customer" means at JIVO, the
answer is mostly him. Not in the roster, and not obviously in any of the ten's
reporting lines.

### 11. Chopra Sir (`audit@`) — the auditor, busiest actor in OMS
**1,069 audit-log actions** — more than four times the next person. He is the
final gate on every order: *Auditor Approval → Completed*. Nothing ships without
passing through him, and he is not in the roster.

### 12. Jaspreet Singh "Bunty" — Mart production + Gupta godown
Mart's production orders and `GP-FGM` traffic. Named in SAP's saved queries as
"ALL BUNTY VEER JII" — he has his own reporting set, which usually means seniority.

---

## Tier 2 — functions with **nobody** named

The brief says JIVO's supply chain runs on **five departments, each with its own
HOD**. Two of them have no one in the roster, and neither does anything downstream
of production.

| Function | Named in the brief? | Anyone in the roster? |
|---|---|---|
| Oil & raw-material procurement | ✅ | ✅ [[Shunty Veerji]] |
| Production | ✅ | ✅ [[Gautam]] |
| Infrastructure — storage | ✅ | ✅ [[Prince Bathinda]], [[Honey Factory]] |
| **Packaging-material procurement** | ✅ | ❌ **nobody** |
| **Finance** | ✅ | ❌ **nobody** (billing ≠ finance) |
| **Infrastructure — filling-line capacity** | ✅ | ❌ **nobody** |
| **Quality / QC** | — | ❌ **nobody** (a QC approval type and a QC line account both exist) |
| **Logistics / transport** | — | ❌ **nobody** (Transport is its own budget head) |
| **The single owning HOD the brief asks for** | ✅ §7 | ❌ **unnamed — an open management decision** |

> [!danger] Packaging is the worst gap
> Cartons were measured as the **longest packaging lead time in the chain, ~27
> days** — the thing most likely to stop a line. It is a named department in the
> brief and it has **no owner in the roster at all**.

---

## Tier 3 — the nine other HODs

JSAP has **13 active HODs. The roster contains 4.**

| Missing HOD | Code |
|---|---|
| **Avtar Vg** | JWPL0014 |
| **Prabhu** | JWPL2217 |
| Arshdeep Singh | JWPL3005 |
| Arvinder | JWPL0115 |
| Bhupinder Singh | JWPL1556 |
| Gagan Vg | JWPL0018 |
| Karanpreet Vg | JWPL1557 |
| Nirmal Didi | TEMP0001 |
| Veerji | TEMP0002 |

Ask Gurvinderjeet which of these the supply chain actually touches — nine is
too many to chase blind, but Avtar and Prabhu are not optional.

---

## Tier 4 — the two he withdrew

**Two contact cards were deleted from the thread**, one at 18:22:53 (before the
batch) and one at **18:29:13, mid-batch, between [[Gurpreet Singh Gopi]] and
[[Shunty Veerji]]**. And [[Honey Factory|Honey]]'s card was re-sent at 18:31:23
**with no role attached** — the last message before the export was taken.

Given that packaging procurement and finance are precisely the two gaps, it is
worth asking directly whether those two deleted cards were their HODs.

---

## What is still unchecked

- **OMS and the e-com platform** — the sweep for these ten people across OMS's
  55 users, its 13 tracker roles and its 656 party assignments has not come back
  yet. Prior work flagged **"Navneet"** holding ~60% of all party assignments and
  an OMS manager account `prince` with 15 parties — both worth resolving.
- **DSR** — unreachable; no credentials configured on this machine.
- **The factory live API** — its token expired on 2 Aug, so factory findings come
  from a 10 Aug local sync, not live.
- **The two voice notes** in the WhatsApp export were never transcribed.

---

## The ask, in one paragraph

> Veerji, out of the ten you sent — nine are confirmed in the systems. Missing
> and needed: **Avtar Vg** (Preshit's boss), **Prabhu** (both e-com people report
> to him), **Atul Sharma** (runs 100% of Beverages production), **Param Billing**
> and **Aqib** (who actually move Mart's stock). And nobody at all covers
> **packaging procurement**, **finance**, **quality** or **transport**. Which of
> those do you want in, and were the two cards you deleted the packaging and
> finance HODs?

## Links

[[ROSTER]] · [[ORG-CHART]] · [[ASK-GURVINDERJEET]] · [[functions/The Five Departments|The Five Departments]]
