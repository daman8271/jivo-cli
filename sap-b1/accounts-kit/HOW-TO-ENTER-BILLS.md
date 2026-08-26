# How to enter bills — Satnam

**You do not need to remember anything. Give Claude the bills and it does the rest.**

## What to do

1. Open Claude Code on the `jivo-cli` folder.
2. Drag the bill PDFs in. One, or twenty.
3. Say what you want in your own words — or say nothing at all:

   > *"enter these"* · *"make these bills"* · *"yeh karo"* · or just drop the files

That's it. Claude will read each bill, find the matching GRPO, make the entry,
attach the bill, and **send it to Bhawani for approval**.

**You do not have to say "add and new".** It happens by itself.

## What you should see at the end

For every bill, a line like this:

```
Draft 55331 · ROYAL PRIME LABELS · RPL/1217/2026-27 · ₹5,664
  → sent to BHAWANI (request 73093)
  → nothing in the ledger
```

Two things must be true. If either is missing, **something went wrong — say so**:

- **sent to BHAWANI** — she has it
- **nothing in the ledger** — it has not been posted

## What happens next

Bhawani checks it and approves. **Her approval does not post the bill** — after she
approves, someone opens it in SAP and presses **Add** one more time. That is normal.
Your part is finished when she has it.

## Which company

The bill itself decides. Claude reads the buyer's name and GSTIN off the paper:

| The paper says | Company |
|---|---|
| Jivo Wellness Pvt Ltd (nothing else named) | **Oil** |
| Jivo Mart | **Mart** |
| "(Beverage Unit)" or "ONLY FOR BEVERAGES" | **Beverages** |

All three work from your machine. If you want to switch by hand in a cmd window:
`use oil` · `use mart` · `use bev`

## If something looks wrong

**Just say so in plain words.** Examples that all work:

- *"this one didn't go to Bhawani"*
- *"why is this showing posted?"*
- *"the amount is wrong"*
- *"I gave you 20 bills, only 18 came back"*

Claude will check SAP and tell you what actually happened. **Do not re-run a bill that
already went** — if it is already with Bhawani, sending it again creates a second
request and takes the first one away from her. Claude refuses this on purpose.

## The one thing to never let happen

A bill must **never** go straight into the books without Bhawani seeing it. If Claude
ever tells you a bill was "posted" instead of "sent for approval", **stop and tell
Daman**. That happened once (invoice 626084197 on 26 Aug) and it had to be cancelled
in SAP by hand.

## If Claude says it cannot

Two real limits, both fine to hear:

- **Credit notes and payments** cannot be auto-sent yet — only A/P invoices. Claude
  will make the draft and tell you to press Add yourself in SAP.
- **A bill with no GRPO** (fuel, transport, service bills) is handled differently but
  still works — Claude picks the right method from the paper.

Anything else it refuses, ask why. It should give you a reason from SAP, not a rule.

---
*Set up 26 Aug 2026. Background, if you ever want it: `acc/ADD-AND-NEW-PLAN.md`.*
