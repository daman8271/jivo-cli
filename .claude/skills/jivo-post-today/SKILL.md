---
name: jivo-post-today
description: Use when an Accounts operator wants to know which approved A/P drafts can be posted right now — "what can we post today", "kya post kar sakte hain", "which drafts are ready", "check the drafts", "Bhawani ne approve kar diye", "morning check", "anything pending to post", "which ones need JSAP approval", "why is this draft still waiting". Splits the draft pile into what is ready, what is stuck with the above office in JSAP, and what is still with Bhawani. Reads only — it never posts anything by itself.
---

# What can we post today?

**Run this once every morning.** It answers one question: *of all the A/P drafts
sitting in SAP, which ones can go into the books right now?*

## The problem it exists to solve

Every draft sits in one list, mixed together. Two kinds are in there:

* bills that need **nothing** after Bhawani approves — post them and they are done
* bills that then wait for the **above office's budget approval in JSAP**

Nobody wants to open 150 drafts one at a time to work out which is which. So
Accounts wait for the *whole batch* to clear and post everything together. The
result: a packing-material bill that was never held up sits for days behind a
transport bill stuck in JSAP.

Measured live 2026-09-04 in Oil: **₹2.08 lakh** of JSAP-stuck transport bills
was holding back **₹1.06 crore** of bills that were ready to go.

**Bhawani's approval is not the problem and this changes nothing about it.** She
still approves everything exactly as now. The only thing this removes is the
waiting *after* her.

## Run it

```bash
python3 .claude/skills/jivo-ap-draft/bin/daily_sort.py --company oil
```

`--company mart` / `--company bev` for the other books, `--all` for all three.
Add `--snapshot` to record today's calls so the accuracy keeps being checked.

It reads SAP and prints the pile as trays:

| Tray | What to do |
|---|---|
| **READY TO POST** | Bhawani approved it **and** it needs nothing else → post it |
| APPROVED BUT WAITING ON JSAP | above office; **do not hold the others for these** |
| WITH BHAWANI NOW | split into "will post straight after her" / "then waits in JSAP" |
| NOT SENT TO HER YET | use `jivo-add-and-new` — a draft nobody submits is invisible to her |
| REJECTED | her decision; fix or delete |
| CANNOT CALL THE LANE | rare — look at these by hand |

## Then what

1. **Read the READY tray out to the operator** — count, total, and the vendor
   names. That is the answer they asked for.
2. **Show the command it prints** — a `sapb1 add-draft … --dry-run` line for
   exactly those DocEntries.
3. **Run the dry-run and show them the preview.** It reads each draft, runs
   every guard, sends nothing.
4. **Only on their go-ahead**, run it without `--dry-run`.

**Never post without showing the preview first, and never post a draft they did
not agree to.** `add-draft` on an already-approved draft **puts the document
live in the books** — that is click two, and nothing here can undo it. The
operator names the drafts; you do not decide to clear the tray because it looked
ready.

5. **Say the "will post straight after her" number.** That is the planning
   figure — it tells Accounts what is coming before the batch returns.

**On a drafts-only desk** (`harness/desks.json` → `drafts_only`; Mahak's
PC-AUDIT-05 is the first) `sapb1 add-draft` is refused in the binary, exit 9.
The trays are still worth reading — she posts the documents herself — so give
her the READY list and say to Add them in the **SAP B1 client → Document
Drafts**, not through the CLI. Do not offer the `add-draft` command there.

## What decides the lane

The **GL account** on each line, nothing else:

* **RM / PM** bought against a GRPO lands on `2140001` GOODS RECEIVED BUT NOT
  INVOICED → **posts directly**. 893 of 893 Oil drafts this FY, not one went to
  JSAP.
* A **`56xxxxx` indirect-expense** line with a Budget dimension → **waits in
  JSAP** (freight outward, loading, rent, repairs, conveyance, legal…).
* Job work, inward/import freight, lab testing, plate & die, fixed assets →
  **post directly**, even though they are service bills.
* **JIVO MART never enters JSAP at all** → always posts directly.

**Two traps.** "Has a GRPO" does not mean direct — every transport bill has a
freight GRPO and they all wait in JSAP. "Is a service bill" does not mean it
waits — job work is a service bill that posts directly.

Full rule, the measured accuracy, and how to refresh it:
**`jivo-ap-draft/reference/jsap-routing.md`**

## How much to trust it

* **"READY TO POST" has never been wrong** — 1,105 of 1,105 on Oil history,
  234/234 and 273/273 on held-back months, 71/71 on Beverages. No document it
  cleared later turned up in JSAP.
* **"WAITS IN JSAP" is right about 85-88%**, and its mistakes are all the safe
  way round: it says wait on something that would have posted.
* **Still being checked forward.** All of the above is history. Live calls are
  being recorded and graded:
  `python3 .claude/skills/jivo-ap-draft/bin/daily_sort.py --score`
  If that ever shows a "said POST NOW but it went to JSAP", say so out loud and
  stop trusting the tray until it is explained.

## Things to say, and not say

* **Nothing auto-approves in JSAP.** In the 30 days to 2026-09-04 the
  auto-approver cleared **1** document and refused **586** — no FY26-27 budget
  allocation is loaded, so everything in JSAP waits for a person. Never tell an
  operator a JSAP document might clear itself.
* **`dasCancelled` drafts are hidden on purpose** — Oil carries 828 of them
  (₹42 Cr, some from 2024). They are abandoned, not work. Showing them is what
  made the list too long to read in the first place.
* If the READY tray is empty, say that plainly. It is a normal answer.
* This skill **writes nothing**. The only write is the `add-draft` the operator
  approves, and that is theirs, not yours.
