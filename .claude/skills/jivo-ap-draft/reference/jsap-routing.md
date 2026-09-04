# Which lane? POST NOW vs WAITS IN JSAP

Shared by `jivo-ap-draft`, `jivo-ap-service-draft`, `jivo-ap-credit-memo`,
`jivo-add-and-new`. Tool: `bin/jsap_route.py`.

## The problem this solves

After Bhawani approves a draft it comes back to Accounts, who make the ledger.
From there the document takes one of two lanes:

* **POST NOW** — saved and posted in SAP by the operator. Done that day.
* **WAITS IN JSAP** — it first needs the above-office **budget** approval in
  JSAP, and only then can be posted.

Nobody could tell the lanes apart at draft time, so the whole pile was held for
the slowest document. **Say the lane out loud on every draft** — then the POST
NOW ones move immediately instead of waiting behind a JSAP queue they were
never in.

## The rule

A document goes to JSAP if **any single line** is budget-controlled:

> the line carries a **Budget dimension** (SAP dim-3 = `CostingCode3` /
> `OcrCode3`) **and** its GL account is not a stock, fixed-asset or
> direct-cost account.

Everything else is posted directly.

| What the bill is | Account it lands on | Lane |
|---|---|---|
| **RM / PM** bought against a GRPO | `2140001` GOODS RECEIVED BUT NOT INVOICED | **POST NOW** |
| Service / expense bill | `56xxxxx` indirect expense + Budget dim | **WAITS IN JSAP** |
| Freight outward, transport, bilty | `5670001` | **WAITS IN JSAP** |
| Loading / unloading | `5670002` | **WAITS IN JSAP** |
| Rent, repairs, conveyance, refreshment, printing, housekeeping, legal, electricity | `56xxxxx` | **WAITS IN JSAP** |
| Casual labour, direct electricity, consumables | `5100008` / `5100020` / `5100015` | **WAITS IN JSAP** |
| Job work, refining job work | `5100009` / `5500003` | **POST NOW** |
| Inward freight, import freight | `5100002` / `5500001` | **POST NOW** |
| Lab & testing | `5100018` | **POST NOW** |
| Plate & die charges | `5100016` | **POST NOW** |
| Import agency / duties / professional | `5200003` / `5200010` | **POST NOW** |
| Fixed assets & WIP | `12xxxxx` | **POST NOW** |

**Read the account, not the words on the bill.** Unloading/loading booked
**indirect** (`5670002`) waits — 49 of 54 Oil drafts went to JSAP. The same
words booked **direct** (`5100004`) went direct all 4 times, but 4 drafts is
below the 5-draft evidence bar, so `5100004` is *not* in `NEVER_JSAP` yet and
the tool still calls it WAITS (erring toward waiting). Watch it and re-`--refit`
once a few more come through. Two bills that read identically on paper can take
different lanes purely because Accounts coded them to different heads.
| **Anything in JIVO MART** | — | **POST NOW** (Mart never entered the budget process) |

The trap: **"is it a service bill?" is not the test.** Job work and inward
freight are service bills that post directly; a freight GRPO exists behind
every transport bill yet those all go to JSAP. The account decides, not the
presence of a GRPO and not `DocType` I/S (that alone is only ~78% right).

## Accuracy — measured, not assumed

Verified 2026-09-04 against `bud.jsBudgetTable` (JSAP, `jsaplive3`) joined to
SAP `ODRF`/`DRF1`, Oil FY26-27. Held-out months rebuild the account table from
the *other* months only, so the test month is genuinely unseen. Beverages was
never used to build anything — the Oil table is applied to it unchanged.

| Population | n | Accuracy | POST NOW precision | JSAP precision |
|---|---|---|---|---|
| Oil, all resolved drafts | 2,621 | 93.1 % | **100.0 %** (1105/1105) | 88.1 % |
| Oil, July held out | 697 | 91.4 % | **100.0 %** (234/234) | 87.0 % |
| Oil, June held out | 676 | 87.1 % | **100.0 %** (273/273) | 78.4 % |
| Beverages, Oil table unchanged | 519 | 86.9 % | **100.0 %** (71/71) | 84.8 % |

**A POST NOW has never once been wrong** — across every population above, not
one document it cleared later turned up in JSAP. So POST NOW is safe to act on
immediately. WAITS IN JSAP is right ~85-88 % of the time and its errors are all
in the harmless direction (it says wait when the document would have posted).

Supporting counts: `2140001` GRNI appeared on 893 Oil drafts this FY and **not
one** reached JSAP. Drafts with no Budget dimension at all: 713, none in JSAP.

### The one case that proves the test is per-LINE

Draft **51537** (Shrichand Computers, ₹30,400) carried a `2140002` fixed-asset
line *and* a `5680022` COMPUTER AND HARDWARE line — and it went to JSAP. A
document-level test ("does it contain a never-account?") called it POST NOW and
was wrong. Testing each line and asking "is **any** line budget-controlled?"
gets it right. That is why `2140002` is deliberately **not** in `NEVER_JSAP`.

## Nothing auto-approves in JSAP right now

JSAP has an auto-approval engine (`bud.jsAutoApprovalLog`). In the 30 days to
2026-09-04 it looked at 593 documents and auto-approved **1**; the other 586
were refused with *"Monthly allocation exceeded … > Allocated=0.00"* — there is
no FY 2026-27 budget allocation loaded, so every document fails the limit check
and waits for a human. Do not tell an operator a JSAP document might clear
itself. (Same root cause as the missing allocation noted in
`accounts-dashboard/pipeline/builders/budget_heads.py`.)

## The daily sort — what this is actually for

**The problem was never posting. It was the batch moving as one lump.** Every
draft sits in one list, mixed. Nobody wants to read 143 rows to find the ones
that need nothing further, so Accounts wait for the WHOLE batch to be approved
and post it together — and a packing-material bill that needed nothing is held
for days behind a transport bill stuck in JSAP.

**Bhawani is not the bottleneck and nothing here touches her approval.** The
lumping is the bottleneck.

```bash
python3 .claude/skills/jivo-ap-draft/bin/daily_sort.py            # Oil
python3 .claude/skills/jivo-ap-draft/bin/daily_sort.py --all      # all three books
```

Read-only. It prints the pile as trays:

| Tray | Meaning |
|---|---|
| **READY TO POST** | she approved it **and** it never needed JSAP — go |
| APPROVED BUT WAITING ON JSAP | above office; **do not hold the others for these** |
| WITH BHAWANI NOW | split into "will post straight after her" / "then waits in JSAP" |
| NOT SENT TO HER YET | `jivo-add-and-new` |
| REJECTED · CANNOT CALL THE LANE | human looks |

It ends with the exact `add-draft … --dry-run` line for the ready tray, so
acting on it is one paste, not a reading exercise.

`dasCancelled` drafts are excluded — Oil carries 828 of them (₹42 Cr, some from
2024). They are abandoned, not work, and showing them is what makes a list too
long to read.

**Run it morning and evening.** Because the lane is known at draft time, the
"will post straight after her" count tells Accounts what is coming *before* the
batch returns.

## Using it

```bash
R=.claude/skills/jivo-ap-draft/bin/jsap_route.py

python3 $R 55813 55906 --company oil -v      # named drafts, with reasoning
python3 $R --pending --company oil            # the whole open pile, split in two
python3 $R --pending --company oil --since 2026-08-25
python3 $R --payload /tmp/ap-draft.json --company oil   # BEFORE sending
python3 $R --refit                            # re-derive the account table
```

`--payload` reads the same JSON the A/P skills build, so the lane can be named
in the same breath as the dry-run, before anything is sent.

## Maintaining the account table

`NEVER_JSAP` in `bin/jsap_route.py` is the list of accounts that carry a Budget
dimension but are not budget-controlled. It was derived from history, not from
a JSAP config table — **JSAP has no account→budget mapping table**; the budget
register itself is the only record. Re-derive with `--refit` (reads JSAP +
SAP, prints a paste-ready dict) whenever a new expense head appears or a lane
call is questioned. An account seen fewer than 5 times is left out
deliberately: too thin to call.
