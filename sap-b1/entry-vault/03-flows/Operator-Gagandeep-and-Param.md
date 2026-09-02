---
type: operator-profile
subject: "Gagandeep candidates (USER28 Mart) and Param (USER01 Oil)"
sap_tables: [ORCT, OVPM, OUSR]
companies: [OIL, MART]
mined: 2026-08-25
window: FY26-27, DocDate >= 2026-04-01
confidence: medium-high
readonly: true
---

# Who is "Gagandeep", and who is "Param"?

> **Nothing here was produced by writing to SAP.** All figures are live reads via
> `hana-sql`, 2026-08-25.

## Part 1 — Gagandeep: the name splits three ways, and none is a payments operator

| Candidate | Verdict | Confidence |
|---|---|---|
| Oil login `Gagandeep` (USERID 42) | **DEAD — ruled out conclusively** | 99% |
| Mart `USER28` "GAGAN WAREHOUSE/ VANSH" | The only operator match — a **shared route-collection login**, not accounts | 97% |
| Employee `JWPL0018` / `ORGV000003` | **A payee.** JIVO pays him; he keys nothing | 99% |
| Any other GAGAN login | **None exists** — all 3 OUSR swept | 99% |

**The Oil `Gagandeep` login is dead, exhaustively.** All 582 Oil tables carrying a
`UserSign` column were enumerated; `UserSign=42` appears in exactly one — `CUMI`, the
personal menu-bar config, 4 rows. Zero business objects. The account was created,
opened once, never used.

**No Beverages login contains GAGAN at all.**

> **Honest one-liner:** the only Gagandeep on the payments side is a *payee*, and the
> only "Gagan" who keys anything is a warehouse counter operator on a login shared
> with someone called Vansh.
>
> Residual doubt: `OUSR.U_NAME` is free text. A login named for one person can be
> operated by another. Settling this needs HR/desk confirmation, not SQL.

### What USER28's 847 documents actually are

**MEASURED: daily route-collection receipts from 7 Delhi beat salesmen, each settling
exactly one A/R invoice.** Not counter sales, not COD, not deposit slips.

The uniformity is the proof:

- All 847 are `DocType='C'`, all `BPLId=1`.
- **Only 8 distinct payers**, all named individuals: DEL DEEPAK BHARDWAJ (153),
  DEL ABHISHEK KUMAR (140), DEL KAWALJEET SINGH (125), DEL RAJU EAST (123),
  DEL SAHIL (119), DEL PINTU SINGH (112), DEL RAMANPREET (59), SANTOSH JHA (16).
  A counter-sale workflow would show hundreds of one-off names.
- **834 of 847 (98.5%) applied to an invoice — and every one settles exactly one.**
  The invoices-per-receipt histogram has a single bucket: `1 → 834`. **Zero allocation logic.**
- Two means, one per document: 368 cash (₹19.59 L) + 479 transfer (₹21.07 L) = 847.
  **Zero cheques, zero cards.**
- Two GL accounts, no exceptions: cash `1105003`, bank `1104201`.

**Correction to an earlier figure in this study:** ₹40.66 L is a **~4-month** number
(Apr 1 – Aug 6, 92 active days). Full year FY25-26 was **3,478 docs / ₹1.95 Cr**.
The fair annualised comparison is **₹1.2–1.9 Cr**, not ₹40.7 L.

### USER38 AQIB is a different workflow, not the same one

365 docs / ₹5.72 L / avg ₹1,567 — but **one payer** (SANTOSH JHA, 364 of 365),
**100% bank transfer, zero cash**, and **364 of 365 on-account with no invoice link** —
the exact inverse of USER28. One customer's near-daily standing remittance.
Accelerating hard: 92 docs in FY25-26 → 365 in four months.

### Two humans behind USER28, or one? — unresolvable from SAP

`CreateTS` verified as HHMMSS (min 100655, max 194937). The hour histogram *is* bimodal
(peaks 10:00 and 16:00, trough 14:00) — **but that is equally one person's lunch break.**

The stronger test came back negative. If Gagan and Vansh split the work they should
split *something*, and they split nothing:

- **Payers:** all 7 main payers appear in both blocks in near-equal proportion
  (Deepak 71/65, Abhishek 59/68, Kawaljeet 56/49).
- **Means:** cash 169/158, transfer 207/220. Identical mix.

**Attribution for all 847 documents is unresolvable from SAP alone.** Needs shift records.

### Is it worth automating? Yes — and the blocker named earlier does not exist

**MEASURED keying speed:** median gap between consecutive receipts within a burst
(n=671, gaps ≤10 min) = **66 seconds**; mean 101 s.
→ ~**65 operator-hours/year ≈ 8 working days** at FY25-26 volume. AQIB adds ~7 h.

**Structurally this is the most mechanisable shape in the book**: 8 known payers,
1:1 invoice match with *zero* allocation logic, 2 GL accounts, 1 branch, no cheques.
USER28 is the **#2 receipt operator in Mart by count** (847, behind Shoaib's 884)
while moving 0.07% of Shoaib's value.

> ⚠️ **CORRECTION — a mid-study finding was wrong.** It was reported that
> `IncomingPayments` has no write path because it is absent from `sapb1 draft`'s 14
> doctypes. That is true of `sapb1 draft <doctype>` but **misses the separate command
> that does exactly this job**:
>
> ```
> sapb1 draft payment incoming   → bopot_IncomingPayments
> sapb1 draft payment outgoing   → bopot_OutgoingPayments
> ```
>
> Both directions exist, are wired, and are tested (`draftpayment.go:41-53`).
> **There is no missing write path.** This makes USER28's stream the ideal *pilot*:
> the 1:1 matching means an automation cannot get allocation wrong.

**Sequence:** build the bank-transfer half first (479 docs, auto-matchable against
statements); leave cash to the human.

*Confidence 90%.* What stops certainty: time spent *outside* SAP — counting cash,
reconciling the salesman's book — was not measured and is plausibly larger than the
66 s of keying.

---

## Part 2 — Param: a second hand is visible on Avtar's login, from 2026-08-12

`USER01` = AVTAR SINGH, `USERID` 10 in Oil. This toolkit's own records say Param works
on a machine configured with Avtar's credentials, so his writes are attributed to Avtar.
The data supports that, without proving it.

### USER01's Oil outgoing payments, FY26-27: 638 docs, ₹62.77 Cr

100% bank transfer. **626 of 638 (98%) on-account** — against Taran's 46%.
Same `Ref1` register as Taran (826466xxx, interleaved ranges), so both hands draw from
one shared numbered queue.

### The night block

| Block | Docs | % on-account | Avg value | Distinct accounts | Distinct parties |
|---|---:|---:|---:|---:|---:|
| Day | 601 | 98.0% | ₹10,37,398 | 15 | 88 |
| **Night (21:00–06:00)** | **37** | **100%** | **₹1,15,045** | **3** | **11** |

The night block is **9× smaller per document**, uses a **much narrower set of accounts
and parties**, and — decisively — **did not exist before 2026-08-12**:

| Date | Docs | First | Last |
|---|---:|---|---|
| 2026-08-12 | 5 | 22:47:03 | 23:56:15 |
| 2026-08-13 | 2 | 22:20:01 | 22:23:02 |
| 2026-08-19 | 5 | 22:54:39 | 23:10:12 |
| 2026-08-21 | 16 | 23:09:46 | 23:45:56 |
| 2026-08-24 | 4 | 23:41:02 | 23:59:15 |
| 2026-08-25 | 5 | 00:06:08 | 00:15:10 |

Compare Taran, who never keys later than 20:42.

**Read, stated honestly:** activity on `USER01` between 22:00 and 00:15 began on
2026-08-12 and is materially different in shape from the daytime work on the same login.
That is **consistent with** a second operator being added to this login in mid-August,
and Param is the known candidate. It is **not proof** — one person working late on a
narrower task would look similar.

**Confidence ~65%.** What would settle it: ask Param which nights he worked, or check
the box's own write log — every write from this CLI is stamped with the registered
operator name, so `queries/param/sap-writes.jsonl` would separate the two hands
immediately for anything keyed through the CLI rather than the SAP client.

> **Governance note, not an accusation:** ₹62.77 Cr moved this FY under a login whose
> operator cannot be determined from the books. That is worth fixing with a second
> named login regardless of any automation.
