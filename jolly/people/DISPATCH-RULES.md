---
title: Dispatch rules — who gets told what, when
type: rules
org: JIVO
company: Oil
status: draft
last_verified: 2026-08-11
tags: [jivo/dispatch, jivo/rules]
---

# Dispatch rules

**What this is for.** The system holds the whole plan. Nobody else has to. Each
person gets the one instruction that is theirs, at the moment it matters — and
nothing else.

That is the difference between this and a dashboard: a dashboard waits to be
looked at. This goes and finds the person.

Every rule below is **event → person → message → reply we need → chase →
escalate**. Drafted from what the systems now show; the timings and limits marked
`?` need Gurvinderjeet or the person themselves.

---

## The rules, in the order the month runs

### 1. The plan hasn't arrived
| | |
|---|---|
| **Trigger** | It is the **?th** and [[Preshit Singh]]'s monthly workbook hasn't landed |
| **Who** | [[Preshit Singh]] |
| **Message** | "Veerji, August plan mil gaya? Production planning uske baad hi chalu hogi." |
| **Need back** | the file |
| **Chase** | ? hours |
| **Escalate** | [[Gurvinderjeet Singh]] |

> Everything downstream is blocked by this one. It is the highest-value alarm in
> the whole system and the cheapest to build.

### 2. The plan arrived but doesn't add up
| | |
|---|---|
| **Trigger** | The workbook's sheets disagree (they did in August: 4,156 T / 4,390 T / 3,661 T), or an e-com SKU silently resolved to 0 |
| **Who** | [[Preshit Singh]], cc [[Kamaldeep Singh]] if it's the e-com column |
| **Message** | "Plan mein FINAL aur FINAL(2) alag aa rahe hain — 4,156 vs 4,390 T. Kaunsa sahi hai?" |
| **Need back** | which sheet is the plan of record |
| **Escalate** | [[Gurvinderjeet Singh]] |

### 3. Oil will run short
| | |
|---|---|
| **Trigger** | Oil stock − (plan + 35% floor) < 0, **inside the lead time** (mustard 12–50 days) |
| **Who** | [[Shunty Veerji]] |
| **Message** | "Veerji, <oil> ki <qty> MT kami hai. Lead time <n> din — aaj order karna padega warna <date> ko line rukegi." |
| **Need back** | PO raised / already on order / can't |
| **Chase** | ? |
| **Escalate** | ? — he is an HOD |
| ⚠️ **Note** | He has **no SAP login** — Lovpreet (`exim`) keys his POs. The confirmation may have to come from Lovpreet |

### 4. Packaging will run short — the one that actually stops lines
| | |
|---|---|
| **Trigger** | Packaging stock − (exploded requirement + 35% floor) < 0, inside lead time. **Cartons ~27 days** |
| **Who** | [[Ravinder Jivo]] — **and [[Kulbir Veer Ji]] if it is cartons** |
| **Message** | "<item> ki <qty> kami hai. Lead time <n> din. Aaj order karna hoga." |
| **Need back** | PO raised / already on order / can't |
| **Escalate** | ? |
| ⚠️ **Why this one matters most** | **14 of 21 line stoppages last month were packaging** — sticker ×8, shrink ×3, bottle ×3 — against 6 machine faults. Every top-5 waste item is packaging too |

### 5. A line went down
| | |
|---|---|
| **Trigger** | Factory app run `live_status` = **BREAKDOWN** or **STOPPED** with no output |
| **Who** | [[Gautam]] |
| **Message** | "<Line> pe run #<n> <status> hai — <product>. Kya hua?" |
| **Need back** | cause + expected restart |
| **Chase** | ? minutes — a stopped line is expensive by the hour |
| **Escalate** | [[Raju Veerji]] |
| **Live example** | On 11 Aug **all six runs** read "no production yet" — two Breakdown, four Stopped — where 10 Aug completed all five. **That is exactly this alarm, and nobody got it** |

### 6. Production is behind the plan
| | |
|---|---|
| **Trigger** | Cases produced this week < plan ÷ 4, per SKU |
| **Who** | [[Gautam]] |
| **Message** | "<SKU> plan se <n> cases peeche hai. Is hafte cover ho jayega?" |
| **Need back** | yes / no + what's needed |
| **Escalate** | [[Raju Veerji]] |

### 7. The plan isn't physically possible
| | |
|---|---|
| **Trigger** | Required hours (plan ÷ rated speed) > available line hours in the month |
| **Who** | [[Gautam]], then [[Preshit Singh]] |
| **Message** | "<Line> pe <n> ghante chahiye, hain sirf <m>. Plan cut karna padega ya shift badhani padegi." |
| **Need back** | a decision — cut the plan, or add capacity |
| **Escalate** | [[Raju Veerji]] + [[Gurvinderjeet Singh]] |
| **Now computable** | rated speeds exist — JP 5,400 b/hr, Clear Pack 4,800, Pouch 2,400, 10 Head 2,100, 6 Head 1,080 (1 L) |

### 8. Finished goods below floor
| | |
|---|---|
| **Trigger** | FG stock < 35% of the 3-month trend, per SKU |
| **Who** | [[Honey Factory]] |
| **Message** | "<SKU> FG floor se neeche hai — <qty> bacha hai." |
| **Need back** | confirm physical stock matches the system |
| **Escalate** | [[Raju Veerji]] |

### 9. A system feed died
| | |
|---|---|
| **Trigger** | No factory→SAP entry for N days; OMS or ecom sync stale |
| **Who** | [[Ziyaul]] |
| **Message** | "Factory se SAP mein production entry <n> din se nahi aa rahi." |
| **Need back** | acknowledged / fixed |
| **Escalate** | ? |
| ⚠️ **Live now** | The factory app's **"SAP Entry" column is blank on nearly every run.** Same shape as the GRPO feed found dead for 15 days. **Nothing monitors this today** |

### 10. E-com demand changed
| | |
|---|---|
| **Trigger** | The e-com Oil sheet moves after the plan is locked |
| **Who** | [[Kamaldeep Singh]] |
| **Message** | "Ecom plan <n> T badla hai — production plan update karun?" |
| **Escalate** | [[Gurvinderjeet Singh]] |
| ❓ **Open** | with [[Gagan PU]] out of scope, **nobody in scope ships what Kamal plans.** 2,083 T — half the plan. Needs a ruling |

---

## Before any of this can send a single message

> [!danger] Every "Owns" field in this vault is still blank
> To *give an order* you must know what the person can decide **alone**. Right
> now we know their jobs, not their authority. Not one of the ten has a recorded
> limit.
>
> The approval data makes this concrete: the chain is **one stage deep with no
> monetary limits** — [[Raju Veerji]] signed everything from ₹250 to ₹6,00,210
> through the same single stage. So "who approves this" currently has no
> data-driven answer at all.

**Three things needed before go-live:**

1. **Authority per person** — what they commit alone, and who signs above it.
2. **Chase timings** — how long is silence acceptable, per rule. A stopped line
   is minutes; a monthly plan is a day.
3. **Escalation targets** — provisionally [[Gurvinderjeet Singh]] for everything,
   which he has not confirmed.

---

## Register — this is not a detail

> [!warning] Half these people are seniors, and one is a veerji you report to
> [[Raju Veerji]], [[Shunty Veerji]] and [[Ziyaul]] are **HODs**.
> [[Kamaldeep Singh]] and [[Gagan PU]] are Sub-HODs. A machine telling an HOD what
> to do reads as an insult in a way the same message to an operator does not.
>
> **The fix is grammatical, not technical.** To a senior: *"Veerji, cartons ki
> kami aa rahi hai — order karna hoga?"* — a flag and a question. To an operator:
> a clear instruction. Same computation, different sentence.
>
> Worth deciding early whether messages go out **as Daman** or **as a system**.
> "Jivo Planning" sending an alert is very different from what looks like Daman
> texting an order at 7am. Ask Gurvinderjeet which one he wants.

**Per person, still unknown for all ten:** language (Hindi / Punjabi / English),
register, working hours, and whether they prefer a voice note.

---

## What to build first

The temptation is to build all ten rules. Don't.

**Rules 1, 4 and 5 carry almost all the value:**

- **1** — the plan is the input everything else needs, and it goes missing.
- **4** — packaging causes two-thirds of actual line stoppages, and it has the
  longest lead time.
- **5** — a stopped line costs money by the hour, and today's six stopped runs
  prove nobody is being told.

All three are computable from data we already have. None needs a new integration.

## Links

[[ROSTER]] · [[SCOPE]] · [[ORG-CHART]] · [[ASK-GURVINDERJEET]]
