# mcp-benchmark — accuracy harness for the JIVO MCP layer

A **blind** 30-question benchmark that measures whether the remote MCP layer gives
the same answers as the CLI/HANA ground truth. Built 2026-07-30 (goal #101).

## Why it exists
A phone answer via the MCP looked authoritative but contained a real error: it
reported "40 journal entries" when the true figure was ~130. Cause was not the
model — the MCP returned a field named `count` holding *rows in this page* (hard
capped at 20 by the Service Layer), with no pagination and no server-side total.

## Files
| File | What |
|---|---|
| `questions.json` | the 30 questions + angle + `truth_plan` (how to compute truth) |
| `truth-key.json` | ground truth per question, with the exact commands + raw evidence |
| `baseline-mcp-answers.json` | what the MCP answered, blind, BEFORE any fix |
| `baseline-scored.json` | per-question verdict + root-caused defect + required fix |

## Method (the anti-cheat matters)
1. **Blind phase** — agents answer using ONLY `POST <gateway>/jivo/mcp`. Run with
   **no SSH tunnel open**, so the CLI physically cannot reach SAP (the box
   IP-whitelists) — cheating is impossible, not merely forbidden. Every answer
   ships the exact tool calls + raw evidence for audit.
2. **Truth phase** — only after the blind phase, computed independently ON THE VPS
   (which holds permanent tunnels), two ways where possible:
   - `ssh vps-pub 'cd /opt/jivo-mcp/env/sapb1 && SAPB1_HOST=127.0.0.1 SAPB1_PORT=47500 /opt/jivo-mcp/bin/sapb1 query <E> --count --company <DB>'`
   - `ssh vps-pub '/opt/jivo-truth/hana-sql -env /opt/jivo-truth/hana.env "SELECT ..."'`
   Both agreed exactly on the control figure (3,390 business partners in Oil).
   Do NOT open per-agent tunnels from the Mac — that path collapses under
   concurrency (two agents died at 6m18s before this was switched).
3. **Score** — CORRECT / WRONG / PARTIAL / REFUSED / TRUTH_UNRESOLVED, each
   mismatch tagged to a named MCP defect.

## Baseline (2026-07-30, before fixes)
**75.86%** — 22 CORRECT, 0 WRONG, 6 REFUSED, 1 TRUTH_UNRESOLVED (q06, an
intraday-moving count that could not be pinned).

⚠️ **Read the 0-WRONG carefully.** The blind agent was *instructed* to admit
limitations, so missing capability surfaced as refusal. A normal phone session has
no such instruction — there the same defects produce confidently wrong answers,
which is exactly what happened in the real ledger query. Treat 75.9% as the
optimistic bound.

All 6 refusals were the same defect: **no `company` parameter**, so Mart and
Beverages are unreachable. Latent defects the model had to work around: page cap
(13 questions), no server-side count (9), no aggregation (9 — q22 needed **462**
paged calls), weak/wrong field naming in descriptions (5).

---

## Result after the fixes (2026-07-30)

| Tier | Baseline | After | Movement |
|---|---|---|---|
| Easy (30) | 75.9% (22 correct) | **100%** of gradable (29/30, 1 stale) | +7 |
| Hard (20) | 80.0% (16 correct) | **95%** (19/20) | +3 |
| **Overall** | **38/49** | **48/49 = 97.96%** | **+10** |

Across all 50: **0 wrong, 0 hallucinated, 0 refused.**

### ⚠️ Read the 98% with its caveat

The headline **depends on a live-drift tolerance**. Against the *literal* frozen
tolerances, roughly 14 questions breach — q08 by 1.28%, q18's JIVO MART balance by
3.0%, h15's July by 6%, h16's weighted average by 4.7 days against a ±3 band.

They were accepted because every one of those deltas reconciles arithmetically to a
single event: ~30-31 Oil invoices worth ~₹1.88 Cr net booked between key-freeze and
the run (~6 h), of which ~6 went to JIVO MART. That event appears independently in
eight separate answers, and in h16 it is near-provable — the >90-day numerator matches
the key to the paisa, and replaying the key's own 435.4659-day average with the new
paper predicts 430.774 against the tool's 430.77.

**The strongest evidence that the arithmetic is right is the pattern, not the score:**
every CLOSED-period figure matched the frozen key exactly (June 2026 sales, Q1 FY26-27
for all three companies and the group, FY2025-26 including the year-end boundary, the
June product ranking, the Blessing reconciliation to the rupee, all 12 FX figures, both
aging buckets, the nil-return and non-existent-customer probes). Every deviation sits on
a still-open window or a live running balance.

### What the fixes actually bought
- All 8 previously-REFUSED questions now answer; 7 of 8 exact to the paisa.
- h12 clears SILENT_PARAM_DISCARD — baseline's most dangerous defect.
- h19 went from structurally underivable to matching ₹21,77,83,981.25 to the paisa.

### Still broken — do not quote these
1. **h10 customer-credit population** — 263 accounts vs the key's 222; the frozen keys
   also contradict each other on the sibling figure (h10 says 312 suppliers in credit,
   q09 says 346), so the instability may be on the key's side. Unresolved either way.
2. **OVPM `DocType='S'` scoping under-reports payments** — costs ₹72.06 lakh on q30 and
   ₹1.75 Cr on h17. Disclosed in the answers, but a reader taking the headline gets the
   smaller number.
3. **No as-of / snapshot read.** A month-end close cannot be reproduced later, and two
   runs an hour apart disagree. Every "right now" figure is a reading with a clock on it.
4. **q05 vs h19 read as contradictory** — "no fixed-asset items" (AssetItem flag) vs
   "354 items in the FIXED ASSETS group". Both true on their own field.

### Anti-cheat audit (run on the retest, not just asserted)
8 blind agents, **180 commands and file-reads inspected, 0 violations**. Only one host
was ever contacted: the gateway. No `ssh`, no CLI binary, no `/opt/jivo-truth`, no read
of anything under `mcp-benchmark/`.
