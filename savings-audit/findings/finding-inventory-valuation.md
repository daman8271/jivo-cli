---
title: "₹3.37 Cr inventory valuation drift — REFUTED as money: SAP's own movement ledger says these lines are worth −₹40 L, not −₹3.35 Cr, and correcting them costs ~₹57 L in tax"
created: 2026-07-29
verdict: REFUTED
amount_verified_inr: 0
kind: control-observation
tags: [savings-audit, finding]
---

# Inventory valuation drift — arithmetic CONFIRMED, conclusion REFUTED. ₹0 bankable.

Part of [[SAVINGS-MOC]] · Evidence: [[dead-slow-stock]]

## What a CFO needs to know

The sweep found **1,250 warehouse stock lines** across the three companies showing **zero quantity but a
negative value** — headline ₹3.37 Cr of "stock worth minus something", presented as a one-time recovery.

**The counting is right. The conclusion is not.** Re-run live today the figure is **−₹3,34,63,475 on 1,250
rows**, within **0.8%** of the claim, and every warehouse subtotal quoted in the original reproduces to the
rupee (Oil GP-PM −₹53,62,936 · Oil BH-PM −₹35,94,995 · Beverages GP-PM −₹88,60,965). Nothing is wrong with
the SQL. What is wrong is what the number was taken to mean.

**The decisive test: SAP's own inventory movement ledger disagrees with the field the finding was measured
from.** `OITW."StockValue"` is a stored warehouse balance; `OINM` is the transaction journal that actually
posts to the general ledger. Across the **221,229 ordinary warehouse rows** the two agree to the rupee
**99.7% of the time** (220,548 rows) — so the comparison is sound. But across the **1,249 Oil and Beverages
rows this finding is built on**,
they diverge violently: the journal values those exact lines at **−₹39,78,495**, not −₹3.34 Cr. Only 17 of
290 Beverages orphan rows reconcile at all, and Beverages' journal total is **positive ₹1.88 lakh**. **88% of
the headline is a stale stored balance, not a posting.**

**The mechanism is visible line by line.** The single largest line, GLASS BOTTLE 200 MLS NEW in the Greater
Noida packing store, carries **−₹38,22,924** in `OITW`. Its actual movement history: **590,488 bottles in**
worth **₹48,08,217** (go-live opening plus one purchase), **590,488 bottles out** worth **₹48,08,791** — all
of it on 25 stock transfers to other godowns. Quantity balances exactly; value balances to within **₹574**.
The godown is flat. Company-wide JIVO still holds **3,58,366 of those bottles worth +₹21.92 lakh**. Nothing
left the building.

**Three more tests, all negative.** (1) Netting each item across all its warehouses collapses the ₹3.34 Cr to
**₹13.01 lakh** on 143 items — 96% is value sitting in a different godown from its quantity, exactly what
per-warehouse FIFO costing produces when transfers move quantity and value at different times (`OADM."PriceSys"='Y'`
in all three companies). (2) SAP records over-relief — the stated root cause — in a dedicated field on the
valuation layers; there are **five such layers totalling ₹1.79 lakh, all in Oil, zero in Beverages and Mart**.
If ₹3.37 Cr had been issued at more value than received, it would be there. It is not. (3) The recommended
action is already routine: **100 revaluation documents in Oil** and **46 in Beverages**, the most recent
**15-Jul-2026**. This is not a neglected backlog.

**And the subledger cannot support a ₹3.37 Cr GL conclusion, because it is out by far more elsewhere.**
Mart ties to **0.18%**. Oil is out by **₹10.67 Cr** and Beverages by **₹29.09 Cr** — 3× and 9× the finding.
The Beverages gap is now explained, and it is a **capex trap**: **₹27.9 Cr of Beverages inventory valuation
layers post to fixed-asset accounts** — PLANT & MACHINERY–COLD CHAIN ₹21.34 Cr, PLANT & MACHINERY–WHEAT GRASS
₹4.50 Cr, PIPE LINE FITTINGS ₹57 L, PLANT & MACHINERY–WATER ₹1.23 Cr. The bottling line is being tracked
through the item master. That is deliberate capital equipment, **not recoverable money**, and it means
roughly **82% of the Beverages "inventory" subledger is not inventory at all**.

**There is no money here, and the fix runs the wrong way.** Nobody owes JIVO these rupees, no spending stops,
no cash is released. Correcting understated inventory means debiting the asset and crediting cost of goods
sold — which **raises reported profit and therefore raises tax**. On the genuinely wrong ₹2.26 Cr that is
about **₹57 lakh of extra tax outflow**. **Bankable: ₹0.** What is real is a data-quality exposure worth
cleaning before statutory audit fieldwork.

## Verdict

| | |
|---|---|
| Claimed | ₹3,37,17,000 one-time recovery |
| Re-derived on the same definition (live 2026-07-29) | **−₹3,34,63,475** (1,250 rows) — arithmetic **CONFIRMED**, −0.8% |
| Same rows valued from SAP's movement journal (`OINM`) | **−₹39,78,495** — 88% of the headline is a stale stored balance |
| Company-level effect after netting each item across warehouses | **−₹13,01,150** (143 items) — 96% evaporates |
| Genuinely impossible book states, correctly measured | **−₹2,26,23,277** |
| **Bankable amount** | **₹0** |
| Cash effect of doing the fix | **−₹57 lakh approx.** (tax on the profit uplift) |

## Component verdict

| Component | Claimed | Verified bankable | Verdict |
|---|---:|---:|---|
| ₹3.37 Cr inventory valuation drift (1,250 zero-qty negative-value warehouse rows) | ₹3,37,17,000 | **₹0** | **REFUTED** |

## Re-derivation, step by step

### 1. The claim reproduces (live, 2026-07-29)

```sql
SELECT COUNT(*), SUM("StockValue") FROM <SCHEMA>.OITW
WHERE IFNULL("OnHand",0)=0 AND IFNULL("StockValue",0)<>0;
```

| Company | Rows | Value |
|---|---:|---:|
| Oil | 959 | −₹1,85,97,513 |
| Beverages | 290 | −₹1,48,65,083 |
| Mart | 1 | −₹879 |
| **Total** | **1,250** | **−₹3,34,63,475** |

Warehouse concentration reproduces exactly as claimed. Age profile clears the go-live trap: joining the
Oil orphan rows to `OINM` for their last movement date gives **12 rows last touched in 2024, 357 in 2025,
590 in 2026** — live ongoing drift, not migration residue. (The largest Beverages line does originate in the
30-Sep-2024 opening layer, but the drift itself is current.)

### 2. Kill test (primary, new this round) — the stored balance disagrees with the posting journal

`OITW."StockValue"` is a stored warehouse balance. `OINM` is the inventory transaction journal that drives
the GL. They should be equal.

```sql
WITH n AS (SELECT "ItemCode","Warehouse" AS W, SUM(IFNULL("TransValue",0)) AS NV
           FROM <SCHEMA>.OINM GROUP BY "ItemCode","Warehouse")
SELECT CASE WHEN IFNULL(w."OnHand",0)=0 AND IFNULL(w."StockValue",0)<>0
            THEN 'ORPHAN_ROW' ELSE 'OTHER_ROW' END AS GRP,
       COUNT(*), SUM(IFNULL(w."StockValue",0)) AS OITW_VAL, SUM(IFNULL(n.NV,0)) AS OINM_VAL,
       SUM(CASE WHEN ABS(IFNULL(w."StockValue",0)-IFNULL(n.NV,0))<1 THEN 1 ELSE 0 END) AS MATCHING
FROM <SCHEMA>.OITW w LEFT JOIN n ON n."ItemCode"=w."ItemCode" AND n.W=w."WhsCode"
GROUP BY 1;
```

| | Rows | `OITW."StockValue"` | `OINM` journal | Rows reconciling |
|---|---:|---:|---:|---:|
| Oil — ordinary rows | 126,206 | ₹63.64 Cr | ₹64.26 Cr | 125,804 (99.7%) |
| Oil — **orphan rows** | 959 | **−₹1,85,97,513** | **−₹41,67,290** | 475 (49.5%) |
| Beverages — ordinary rows | 95,023 | ₹35.49 Cr | ₹37.71 Cr | 94,744 (99.7%) |
| Beverages — **orphan rows** | 290 | **−₹1,48,65,083** | **+₹1,88,795** | 17 (5.9%) |

The method is validated on 221,229 ordinary rows at 99.7% exact agreement. On the finding's own rows it
fails. Journal value of the whole population: **−₹39,78,495**, i.e. **11.9%** of the headline.

Line-level proof, the largest single row (Beverages `PM0000643` GLASS BOTTLE 200 MLS NEW, warehouse `GP-PM`,
`OITW` value −₹38,22,924):

```sql
SELECT "TransType", SUM("InQty"), SUM("OutQty"), SUM("TransValue")
FROM JIVO_BEVERAGES_HANADB.OINM
WHERE "ItemCode"='PM0000643' AND "Warehouse"='GP-PM' GROUP BY "TransType";
```

| TransType | In qty | Out qty | Value |
|---|---:|---:|---:|
| 59 goods receipt (go-live 30-Sep-2024) | 505,288 | — | +₹41,18,097 |
| 20 GRPO | 85,200 | — | +₹6,90,120 |
| 67 stock transfer out (25 docs) | — | 590,488 | −₹48,08,791 |
| **Net** | **590,488** | **590,488** | **−₹574** |

### 3. Kill test — net each item across all its warehouses

```sql
WITH t AS (SELECT "ItemCode", SUM(IFNULL("OnHand",0)) Q, SUM(IFNULL("StockValue",0)) V
           FROM <SCHEMA>.OITW GROUP BY "ItemCode")
SELECT CASE WHEN Q=0 AND V=0 THEN 'clean' WHEN Q=0 AND V<>0 THEN 'TRUE ORPHAN'
            WHEN Q>0 AND V<0 THEN 'qty>0 NEGATIVE value' WHEN Q>0 AND V=0 THEN 'qty>0 ZERO value'
            ELSE 'normal' END, COUNT(*), SUM(V), SUM(Q) FROM t GROUP BY 1;
```

| Bucket | Oil | Beverages | Mart |
|---|---:|---:|---:|
| Zero qty, non-zero value (**true orphan**) | 122 items, −₹9,49,117 | 21 items, −₹3,52,033 | 0 |
| Positive qty but **negative** value | 117 items, −₹65,64,974 | 92 items, −₹1,47,57,153 | 0 |
| Positive qty but **zero** value | 52 items, 3,62,645 units | 105 items, 7,37,844 units | 9 items, 203 units |
| Normal | 1,202 items, +₹62.53 Cr | 663 items, +₹35.51 Cr | 217 items, +₹9.22 Cr |

The single Mart row nets to nothing at item level. **True orphan value company-wide: −₹13,01,150** against a
headline of −₹3,34,63,475 — the other **96.1%** is value sitting in a different godown from its quantity.
Worked examples: CHAI 250 GMS shows −₹20,12,989 at Bahadurgarh packing while the company holds 63,661 units
worth **+₹39,57,192**; SANO POMACE OLIVE 1 LTR shows −₹15,87,258 at Greater Noida while the company holds
26,543 units worth **+₹39,83,998**.

### 4. Kill test — SAP's over-relief counter is empty

```sql
SELECT COUNT(*), SUM("NegInvAdjs"), SUM("OpenNegInv") FROM <SCHEMA>.OIVL
WHERE IFNULL("NegInvAdjs",0)<>0 OR IFNULL("OpenNegInv",0)<>0;
```

Oil **5 layers, −₹1,79,060**. Beverages **0 rows**. Mart **0 rows**. The stated root cause — "goods issued at
higher value than received" — is unsupported by the only table that records it. `OADM."PriceSys"='Y'`
(cost held **per warehouse**) in all three companies is the benign explanation: per-warehouse cost pools
drift against each other by design when transfers move quantity and value asynchronously.

### 5. Kill test — the subledger does not drive the GL, and is out by far more elsewhere

`OITW."BalInvntAc"` is empty on **all 270,386 rows** across the three companies — these lines carry no GL
account link. Against the real inventory accounts (`1103*`, excluding the FDR and R&D accounts misfiled in
that range in Oil):

| Company | `OITW` total | GL `1103*` inventory | Gap |
|---|---:|---:|---:|
| Mart | ₹9.22 Cr | ₹9.20 Cr | **₹1.6 L — ties, 0.18%** |
| Oil | ₹61.78 Cr | ₹51.11 Cr | ₹10.67 Cr |
| Beverages | ₹34.00 Cr | ₹4.91 Cr | ₹29.09 Cr |

The Beverages gap is explained by capex routed through the item master (`OIVL."InvntAct"` by account):

| Account | Layers | Value |
|---|---:|---:|
| 1211001 PLANT & MACHINERY – COLD CHAIN | 86 | ₹21.34 Cr |
| 1204002 PLANT & MACHINERY – WHEAT GRASS | 407 | ₹4.50 Cr |
| 1204003 PLANT & MACHINERY – WATER | 23 | ₹1.23 Cr |
| 1204005 PIPE LINE FITTINGS – WHEAT GRASS | 42 | ₹57.24 L |
| others (office equipment, lab, furniture, computers) | 180 | ₹27.8 L |
| **Total capitalised plant inside "inventory"** | | **≈ ₹27.9 Cr** |
| 1103001/2/12 genuine Beverages inventory | 35,681 | ₹4.86 Cr |

This is **[[finding-hs-filling-advance]] territory — deliberate capital equipment, not recoverable money**.
It is flagged, not claimed.

### 6. Kill test — the action is already standard practice

`OMRV` revaluation documents: **Oil 100** (30-Sep-2024 → 15-Jul-2026), **Beverages 46** (30-Sep-2024 →
18-Mar-2026), Mart 0. Costing already runs this monthly.

## What is actually real

A genuine data-integrity exposure, correctly measured at company level:

- **143 items** carry value with zero stock anywhere — **−₹13,01,150**
- **209 items** show positive stock at a **negative** total value, which is impossible — **−₹2,13,22,127**
  (Oil −₹65,64,974, Beverages −₹1,47,57,153)
- **166 items** hold real stock — 3,62,645 units in Oil, 7,37,844 in Beverages — carried at **zero value**

**Total clearly-wrong negative book value: ₹2,26,23,277** — real, but 33% smaller than claimed, differently
shaped, and worth ₹0 in cash. Beverages carries two-thirds of it inside a company whose genuine inventory
ledger is only ₹4.86 Cr.

**Trap caught while sizing this:** extending the 166 zero-value items at `OITM."LastPurPrc"` returns ₹5.25 Cr
— but **₹5.08 Cr of that is one line**, `PM0000566 LABEL 250 MLS BOPP`, 95,700 labels at a recorded last
purchase price of **₹531 each**. A BOPP label costs paise; the price field is corrupt (almost certainly a
roll/box price entered per piece). Excluding it, the realistic value of stock carried at zero is
**≈ ₹17 lakh**, not ₹5 Cr. Do not quote the extended figure. `LastPurPrc` is unreliable on this item master.

## Action

**Owner: Head of Costing, with Financial Controller sign-off — target before statutory audit fieldwork.**

1. **Rebuild `OITW` warehouse balances from `OINM`** — this is the real fix and it dissolves 88% of the
   symptom. 757 warehouse rows carry a stored balance that SAP's own journal contradicts. Raise with the SAP
   partner as a balance-recalculation / stock posting-integrity job, not as a revaluation.
2. Clear the **143 zero-stock-with-value items** (₹13.01 L) by inventory revaluation — small, clean, closes
   the literal version of this finding.
3. Investigate the **209 items showing positive stock at negative value** (₹2.13 Cr), Beverages first — the
   one state that cannot be explained away, and it distorts gross margin by item.
4. Value the **166 items carried at zero** (≈₹17 L) at a verified cost, and fix `LastPurPrc` on
   `PM0000566` before anyone extends it into a report.
5. Fix the **process**, not just the balances: per-warehouse FIFO plus stock transfers that move quantity and
   value at different times regenerates this every month. Either sequence transfers correctly or reconsider
   per-warehouse costing.
6. **Escalate separately, do not bundle here:** the **₹27.9 Cr of capitalised plant sitting inside the
   Beverages inventory subledger** and the residual **₹10.67 Cr Oil** subledger-to-ledger gap. Each is
   materially larger than this finding and neither belongs in a savings number.

**Do not book any of this as a saving.** If Finance wants a number for the audit file, it is a ₹2.26 Cr
misstatement to correct, carrying roughly **₹57 lakh of tax payable** on the resulting profit uplift.

## Overlaps and double-count guard

Single-component bundle, so there is no internal double count. External:

- **[[finding-off-spec-olive-oil]]** — same table, same ₹0 outcome. RM0000052 sits in Oil warehouse `BH-OT`
  at **+294,992 units / +₹8,21,15,664**, a *positive*-value line. It is inside the ₹61.78 Cr Oil `OITW` total
  quoted above but appears in **none** of the negative buckets here. **No rupee overlap.**
- **[[finding-hs-filling-advance]]** — the ₹27.9 Cr of capitalised plant inside the Beverages inventory
  subledger is the same theme (capex routed through non-capex documents). Referenced for context; **₹0
  claimed here**.
- **[[finding-cc-interest-conversion-rate]]** — the 8.25% working-capital multiplier is **deliberately not
  applied**. This is not a working-capital release: correcting it *raises* book inventory rather than freeing
  cash. Any argument that understated stock reduces bank drawing power is an unverified overlay, **not
  additive**, and **₹0 is claimed for it**.
- No overlap with [[finding-blessing-advertising-overdue]], [[finding-trade-spend-as-credit-notes]],
  [[finding-no-invoice-vendors]], [[finding-advances-vs-open-bills]] or [[finding-dormant-vendor-advances]] —
  different subledgers entirely.

**Contribution to the audit's bankable total: ₹0.**
