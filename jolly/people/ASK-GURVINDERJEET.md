---
title: Questions for Gurvinderjeet
type: ask
to: "[[Gurvinderjeet Singh]]"
created: 2026-08-11
status: unsent
tags: [jivo/ask]
---

# Questions for Gurvinderjeet

Everything the roster is missing, in the order it blocks work. Ready to paste
into WhatsApp — trimmed to what only he can answer.

---

*Updated 11 Aug after Daman's corrections. Answered questions removed — what's
left is genuinely open, and scoped to **Oil only**.*

## Send this first — the three that block everything

> Veerji, 3 cheezan chahidiyan ne taaki main eh cheez chala sakan:
>
> 1. **Packaging kaun kharidda hai?** Shunty veerji oil lainde ne. Par cartons — jo sabse lamba lead time hai (~27 din) — unda koi banda list vich nahi hai.
> 2. **Machine di capacity kise kol hai?** Kisi vi system ch nahi hai. Gautam nu poochna painda ya tuhade kol hai?
> 3. **Tuhada apna number** — tusi sabda card bhejeya, apna nahi 😄

**English:**

> 1. **Who buys packaging?** Shunty buys oil, but cartons are the longest lead time in the chain (~27 days) and nobody in the list owns them.
> 2. **Who holds machine capacity per line?** It exists in no system — only Gautam seems to know.
> 3. **Your own number** — you sent everyone's card except your own.

---

## Then these

4. **Is the list finished?** Two contact cards got deleted from the thread — one
   at the start and one in the middle, between Gopi and Shunty. And Honey's card
   came twice, the second time with no role on it.
5. **Preshit's plan** — he does it by hand in Excel. Can we get the file each
   month automatically, and **which sheet is the real plan?** The workbook has
   three different totals (4,156 T / 4,390 T / 3,661 T).
6. **Does Oil-only include the e-com half?** The plan has 2,083 tonnes of e-com
   Oil in it — Kamal plans it, but Gagan ships it out of Mart's warehouses.
   That's half the plan by tonnage.
7. **Prince's employee code** — he doesn't exist in any system, and there are
   five other Princes. (Parked for now since he's Mart.)
8. **Gagan PU** — what does "PU" stand for?
9. **Gopi** is "Oil tracker" and marked EA — whose EA? And does he track
   consignments, or invoices?
10. **Avtar Vg** (`JWPL0014`) — Preshit's boss, and the #2 production-order
    creator in Oil. Should he be on the list?

---

## And these (fill the holes)

11. **Who owns quality / QC?**
12. **Who releases payments** to vendors?
13. **Language for each person** — Hindi, Punjabi or English, and who prefers a
    voice note over text.
14. **Working hours** — especially the plant people. When is it fair to message
    them?

---

## Already answered — don't re-ask

- ~~What is "Wellness"?~~ → JIVO Wellness Pvt Ltd = the Oil + Beverages books. Mart is the other entity.
- ~~What splits Gautam and Raju Veerji?~~ → Not a split. Gautam runs the floor; Raju Veerji is responsible above him and signs the factory's money.
- ~~Is Gagan PU the mustard-mill Gagan?~~ → No. That's Gagan International, a Ludhiana equipment maker.
- ~~Is Raju Veerji's real name Jasbir?~~ → Yes.
- ~~Does Preshit really do planning?~~ → Yes, manually in Excel.

---

## Answers received

**2026-08-27, from Daman (with Param present):**

| Question | Answer |
|---|---|
| Who buys packaging? | **Ginni veerji = [[Bhupinder Jivo]]**, +91 90237 11711 — card received 2026-08-29 ✅ |
| Who holds machine capacity? | **Gautam** — confirmed |
| Gurvinderjeet's own number | still missing |
| Which sheet is the real plan? | **ANSWERED 2026-08-29 (Daman): `FINAL (2)` = 4,156.4 T.** 4,389.9 T and 3,661.4 T are dead. |
| Chase / escalate timings | **parked** — algorithm first, messaging later |
| Reference-data asks | **we ask nobody for a template.** Lead times come from purchase history, the material-to-machine map from run history, machine speeds from ji.jivo.in. |
| LOOSE OIL GOLD (RM0000021) | **we blend it ourselves** — see gap below |
| Material cost | it is all in SAP, derive from there |
| MSL basis | **GROSS**, not net of returns |

> [!warning] New data gap from the Gold answer
> If we blend LOOSE OIL GOLD in-house, **its recipe is not in SAP.** `RM0000021`
> has no production BOM, so the engine cannot explode it into the oils it
> actually consumes — it still shows as "buy 49,903 L, no vendor". Someone in
> production needs to give us the blend ratio, or add the BOM in SAP.
> Same for `RM0000040 SO OLIVE OIL` — 24,477 L needed, no BOM, no purchase history.

## Log

- **2026-08-11** — drafted, unsent.
- **2026-08-27** — answers above recorded. Still unsent to Gurvinderjeet.
- **2026-08-29** — Daman ruled the plan of record: **`FINAL (2)`, 4,156.4 T**.
  Q5 (which sheet) is closed. Q1 (blend recipes for RM0000021 / RM0000040) is
  **withdrawn** — `engine/blend_mrp.py` closed it on 27 Aug by reading real
  components off production orders, so the question was stale when it was asked.
  **Still blocking: the workbook file itself is not in the repo.** Only the
  aggregate totals were ever saved — the 99 SKU rows behind 4,156.4 T do not
  exist on any machine we control.
