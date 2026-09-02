# return-note — customer returns coming back INTO JIVO

**Section id:** `return-note`
**Files:** `pipeline/sql/return-note.sql` (summary, 23 cols) · `pipeline/sql/return-note-detail.sql` (register, 35 cols)
**As-of:** 2026-08-21 · every number below was pulled live from HANA in this session.
**Structure:** deliberately mirrors the sibling `goods-return.sql` / `goods-return-detail.sql`
(purchase returns, ORPD) so the two sections render alike — same `SCOPE`/`GRP_KEY` stacking,
same raw-INR money convention, same `PARTY_CLASS` split, same exception-flag idea.

---

## 1. Tables and columns chosen, and why

| Table | Used for | Why this one |
|---|---|---|
| `ORDN` | return note header (ObjType 16) | The register itself. 2031 docs in Oil, 1844 Mart, 184 Bev. |
| `RDN1` | return note lines | Quantity, warehouse, item, and the `BaseType`/`BaseEntry` link. |
| `ORIN` / `RIN1` | A/R credit note | The **only** reliable way to tell whether a return was credited (see trap 4). |
| `OINV` / `INV1` | A/R invoice | Two jobs: the sales denominator, and "was the base delivery ever billed?". |
| `ODLN` | delivery | Base document of a return (`BaseType`=15). Only joined in the detail file, to print `DocNum`. |
| `JDT1` | journal entry | **The size measure.** `ORDN."TransId"` → `SUM("Debit")` = stock value pushed back. |
| `OCRD` / `OCRG` | customer master + group | `PARTY_CLASS` (external vs branch vs intercompany). |

**Money unit: raw INR rupees, no suffix** — matching `goods-return.sql`. No `_L` / `_CR` columns.
**Quantity unit: PIECES** (single bottles). No tonnage conversion is applied — the lines mix UoM,
so `RET_QTY_PCS` and `RET_QTY_OTHER_UOM` are separate and **must never be added**.

### Why `RET_STOCK_COST` and not `RET_GROSS`
`DocTotal` on a return note is usually zero (trap 2), so the header value is not the size of the
return. The document's own journal entry is. Verified by account for Oil — every debit lands on
inventory, every credit on COGS:

```
AcctCode  AcctName                      LINES         DR         CR
1103001   FINISHED GOODS OIL             1606  82165397.46         0
1103002   FINISHED GOODS FOOD             261   3364918.66         0
1103004   FINISHED GOODS TRADABLE          48    636327.25         0
1103011   RAW MATERIAL FOODS                2    557736.79         0
1103005   PACKAGING MATERIALS OIL          17    221773.61         0
1103010   PACKAGING MATERIAL FOODS          1    104704.12         0
1103003   FINISHED GOODS BEVERAGES          2     15035.72         0
5100001   PRICE DIFFERENCE ACCOUNT         15      8613.16   3451.97
1103006   RAW MATERIAL OIL                  1       279.04         0
5000049   COGS OIL                        180          0    4559290.09
5000008   COGS SOYABEAN                   366          0    4901107.50
5000007   COGS GHEE                       185          0    1811029.37
```
Those debits sum to **87,074,785.81**, which is `RET_STOCK_COST` for Oil to the paisa. The only
impurity is `5100001 PRICE DIFFERENCE` (₹8,613 Dr / ₹3,452 Cr over 15 lines) — 0.01%, left in.

---

## 2. Traps found, and how each is handled

**1. `"CANCELED"` has THREE values, not two.** `'N'` live, `'Y'` the cancelled original, `'C'` the
auto-generated cancellation mirror. Filtering `<> 'Y'` double-counts. VERIFIED:

```
CO      TOTAL  LIVE_N  CANCEL_Y  MIRROR_C
OIL      2031    1817       107       107
MART     1844    1792        26        26
BEV       184     160        12        12
```
Handled: only `'N'` is counted. The detail file keeps all three but decodes them into
`CANCEL_STATUS` and computes every flag for `'N'` only.

**2. Most return notes carry NO VALUE — this is the big one.** `DocTotal` = 0 on **1104 of Oil's
1817** live returns (61%), Mart 600/1792, Bev 133/160. The note is a stock-movement document; the
money is settled on a separate credit note. And it is getting worse — Oil by month, `RET_DOCS` vs
`RET_DOCS_ZERO_VALUE`: 2026-05 = 41/42, 2026-06 = 52/52, 2026-07 = 64/65, 2026-08 = 28/28. **185 of
the last 187 Oil returns are value-blind.** Reading `RET_GROSS` as "value returned" understates the
position about 2.5x. Handled by carrying `RET_STOCK_COST` as the size measure and publishing
`RET_DOCS_ZERO_VALUE` so the reader can see how much of any row is value-blind.

**2b. The cost measure has a blind spot — but it is NOT the one this note originally claimed.
CORRECTED 2026-08-21 by adversarial review.** The earlier text said returns with no journal entry
make `RET_STOCK_COST` "a floor, not a total" and that Bev's column "must not be presented as Bev's
return cost". **That was wrong and is retracted.** Those documents *do* have inventory receipts in
`OINM`, and SAP valued every one of them at exactly zero. VERIFIED, `OINM."TransType"=16` on live
returns, split by whether `ORDN."TransId"` is null:

```
        has journal   docs   OINM TransValue      no journal   docs   OINM TransValue
OIL                   1732      87,066,172.66                    85              0.00
MART                  1640      39,938,969.34                   152              0.00
BEV                     28         259,426.65                   132              0.00
```
So `RET_STOCK_COST` reproduces SAP's inventory posting **completely**, not partially. It was
re-derived three independent ways and all three agree to the paisa:

```
                       JDT1 SUM(Debit)   OINM TransValue + PriceDiff   section output
OIL                      87,074,785.82   87,066,172.66 + 8,613.16      87,074,785.82
MART                     40,046,247.29   39,938,969.34 + 107,277.95    40,046,247.29
BEV                         259,426.66      259,426.65 +      0.01        259,426.66
```
The real caveat is about **economics, not missing data**: SAP costs those receipts at nil because
the item's moving-average cost in that warehouse is nil (VERIFIED on `OINM."CalcPrice"` = 0 and
`OITW."AvgPrice"` = 0, on ordinary inventory items, `OITM."InvntItem"` = `'Y'`). Real goods come
back and land in stock at book value zero. **Measure the blind spot in PIECES, not documents:**

```
live returns with RET_STOCK_COST = 0    docs      pieces   % of pieces returned   their DocTotal
OIL                                       85       8,931                   2.3%      Rs 14.82 L
MART                                     152      36,805                  26.8%      Rs 79.23 L
BEV                                      132     148,870                  87.3%      Rs  2.92 L
```
Read `RET_STOCK_COST` as **"what SAP put back into inventory"** — always true, in every book — and
never as "what the returned goods were worth" in Mart or Bev. Note the last column: those zero-cost
documents are not empty documents. Mart books **₹79.23 L of gross return value on documents SAP
costed at ₹0**, which is 58% of Mart's entire `RET_GROSS`. `RET_QTY_PCS` sits beside
`RET_STOCK_COST` in every scope precisely so this divergence is visible on the page.

**3. `RDN1` mixes units of measure.** Oil's 7540 live lines: 6730 `PCS` + 424 blank (blank behaves
as PCS), leaving 386 on `SET` (359), `KGS` (10), `NOS` (8), `LTR` (4), `MTR` (4), `DRM` (1). Adding
them is meaningless. Handled by splitting into `RET_QTY_PCS` and `RET_QTY_OTHER_UOM`. Verified:
391267.21 + 3964 = **395231.21** = `RET_QTY_PCS`, and the six others sum to **33352.95** =
`RET_QTY_OTHER_UOM`. Both match the query output exactly.

**4. The ORDN↔ORIN linkage — verified empirically, and the answer is not the obvious one.**
Neither direction is a subset of the other, so the choice had to be made on evidence:

```
                       RET_SIDE_ONLY  CN_SIDE_ONLY  LIVE_RET_WITH_LIVE_CN_MISSED_BY_CN_SIDE
JIVO_OIL_HANADB                    5             3                                        0
JIVO_MART_HANADB                   0             0                                        0
JIVO_BEVERAGES_HANADB              3             0                                        0
```
Going from the credit-note side (`RIN1."BaseType"=16` → live `ORIN`) finds 1396 credited Oil
returns; from the return side (`RDN1."TargetType"=14`) finds 1398. Inspecting the 5 Oil
return-side-only cases explains everything — **all 5 are LIVE returns whose linked credit note was
CANCELLED**, and SAP left `"TrgetEntry"` pointing at the dead note:

```
DocEntry  DocNum      CANCELED  DocDate     CardCode     TrgetEntry  CN_CANCELED
1631      1625011234  N         2025-01-28  CUSTA000606        4926  Y
3781      1625116514  N         2025-11-11  CUSTA000169       10068  Y
3870      1625116535  N         2025-11-26  CUSTA000169       10459  Y
4514      1626026509  N         2026-02-06  CUSTA000606       13501  Y
4264      1626016510  N         2026-01-06  CUSTA000606       13502  Y
```
The return side would mark those five *credited* when the customer holds no live credit. The
decisive column above is the third: **the credit-note side misses zero live-return/live-CN pairs in
all three books.** So the query joins `RIN1`, never `RDN1`.

> Note for whoever reads the earlier draft of this file: its trap 4 said `RDN1."TargetType"` was a
> "strict subset — 0 rows go the other way" and quoted 1411. Both were wrong; the live numbers are
> above. The conclusion (join from the credit-note side) survives, for the opposite reason.

**5. The relationship is MANY-TO-MANY in both directions.** One Oil return (`DocEntry` 4732,
AVENUE SUPERMARTS) is credited by **82** separate credit notes; one Oil credit note can cover 3
returns. Mart is worse — 2650 credit notes point at only 423 returns, and the concentration is on
marketplace bucket-returns:

```
Mart: credit notes per credited return     Mart top returns by CN count
  1 CN      277 returns                      1607264575  2026-07-31  FLIPKART (B2C-MAY-JULY)  57
  2-5 CNs    35 returns                      1602264501  2026-02-01  FLIPKART (B2C-MAY-JULY)  41
  6-20 CNs   54 returns                      1625031101  2025-03-31  FLIPKART B2C             38
  20+ CNs    57 returns                      1625021007  2025-02-06  FLIPKART B2C             36
```
Handled: `CN_NET` is summed from `RIN1."LineTotal"` at **line** level (each line has exactly one
`BaseEntry`, so no double count), and `CN_DOCS` is a `COUNT(DISTINCT credit note)` computed at the
scope level, never a sum of per-return counts. Cross-checked for Oil: `CN_NET` = **84,567,730.63**
and `CN_DOCS` = **2517** = `COUNT(DISTINCT` live ORIN with a `BaseType`=16 line`)`. Both match.

**6. Branch/intercompany is not trade — and a group-name test alone finds NOTHING here.**
**Exactly 0** Oil returns sit in a card group whose name contains `BRANCH`. Yet:

```
CardCode     CardName                             CardGroup   RETURNS       GROSS
CUSTA000606  JIVO MART PVT LTD                    DELHI           477  31922032.51
CUSTA001105  RAVI COSMETICS                       DELHI             1    525000.00
CUSTA000496  INNOVATIVE RETAIL CONCEPTS PVT LTD   PAN INDIA        11    357148.00
CUSTA001022  JIOMART LUHARI Q1                    ANDHRA PRADESH   92    294600.00
```
`JIVO MART PVT LTD` is **477 of Oil's 1817 returns and ₹3.19 Cr of the ₹3.45 Cr header value
(92.5%)** — and it sits in card group *DELHI*. A group-only test classifies all of it as EXTERNAL
and the "external returns" number becomes fiction. Handled: `PARTY_CLASS` = group-name **then**
card-name (`%JIVO%`), never a hard-coded code list, since the same code is a different party in a
different book. BRANCH and INTERCOMPANY get their own rows — never dropped, never folded in.

**7. `"DocStatus"='O'` is not reliable at JIVO** (settled truth, re-confirmed here: Oil shows 40
open of 1817, 38 of them uncredited). `RET_DOCS_OPEN` is published as a **diagnostic only** and
measures nothing outstanding.

**8. Returns are almost never linked to the invoice they reverse.** `RDN1."BaseType"=13` (invoice)
is **ZERO rows in all three books**. Only `BaseType`=15 (delivery) exists, on just **306 of Oil's
1817** live returns (311 including cancelled). The invoice number is typed into free text instead —
**414 Oil returns** mention "INVOICE" in `"Comments"`, in at least three incompatible formats:

```
GR Against Invoice No. 624121160 (Walmart India (P) Limited Zirakpur
RTV RK World 31 Box RTV Against Invoice No DL/SL/2279/24-25
Invoice Number : 624101247
```
Handled: `RET_DOCS_FROM_DELIVERY` counts the **structured** links honestly; the prose is carried
verbatim into the detail file's `REASON` column and is **deliberately not parsed**.

**9. Delivery-linked and credit-noted are mutually exclusive at JIVO.** All 306 Oil delivery-based
returns land in `NO_CREDIT_NOTE`, and the `HAS_CREDIT_NOTE` row shows `RET_DOCS_FROM_DELIVERY` = 0.
Counting all 421 uncredited Oil returns as "missing credits" overstates the exception ~2x, so
`SCOPE='NO_CN_REASON'` splits them three ways (see §4).

**10. The sales denominator excludes go-live migration.** Oil carries **11,078** invoices dated
exactly 2024-09-30 worth **₹74.74 Cr** net of migrated opening balance; Mart and Bev have none.
Leaving them in inflates `SALES_NET` ~8% and silently shrinks every ratio. The same filter is
applied to `ORDN` as a safety belt — **no return note is dated 2024-09-30 in any book**, so it is
a no-op there.

**11. `SALES_NET` is invoices net of GST, ex-cancelled, ex-migration, BEFORE credit notes** — the
ratio reads "returns per rupee invoiced". It is deliberately *not* JIVO turnover (which is already
net of credit notes); using turnover would be circular, since returns drive the credit notes being
subtracted.

**12. (found while writing this note) `ORDN` is occasionally used for RAW MATERIAL returns from
job-workers, not customer returns.** Documents whose lines are all `RM*` items: **Oil 3, Mart 0,
Bev 1**. Negligible everywhere except Bev, where that single document is the largest by cost:

```
DocEntry 653 · DocNum 1608258003 · 2025-08-08 · CUSTA001061 BHARTI MACHINERY TOOLS · DocTotal 0
  RM0000057 WHEAT GRASS CONCENTRATE   45420 GMS   LineTotal 0   Whs BH-PP
  RM0000173 LEMON LIME POWDER        151500 GMS   LineTotal 0   Whs BH-PP
  RM0000064 STEVIA (CEROVIA)          15500 GMS   LineTotal 0   Whs BH-PP
```
Its stock cost is **₹1,40,113 of Bev's ₹2,59,427 total — 54%**. Not handled by a filter (4 documents
company-wide does not justify one, and excluding it would need an item-master rule that could hide
real returns); flagged here instead. It is why Bev's top-customer row has `RET_QTY_PCS` = 0 and
`SALES_NET` = 0.

---

## 3. LIVE OUTPUT — all three companies, `{{ASOF}}` = 2026-08-21

Row counts: **Oil 72, Mart 70, Bev 72** (1 TOTAL + 3 CLASS + 2 CREDIT_NOTE + 3 NO_CN_REASON +
40 CUSTOMER + months: Oil 23, Mart 21, Bev 23). Detail file: Oil 500 (capped), Mart 500 (capped),
Bev 184 (complete). Money = raw INR.

### JIVO_OIL_HANADB
```
SCOPE         GRP_KEY                 RET_DOCS  ZERO_VAL  OPEN  FROM_DLV  QTY_PCS    RET_GROSS    STOCK_COST   NO_CN  NO_CN_BILLED  COST_NO_CN   CN_DOCS  CN_NET       SALES_NET      CN%SALES  COST%SALES
TOTAL         ALL                         1817      1104    40       306  395231.21  34518207.41  87074785.82    421           212  15217213.18     2517  84567730.63  9237973076.04    0.9154      0.9426
CLASS         BRANCH                         0         0     0         0          0            0            0      0             0            0        0            0   731950172.91         0           0
CLASS         EXTERNAL                    1340       908    24       284  240802.21   2596174.90  36895391.80    331           202   7182973.40     2132  33279271.81  5466160606.36    0.6088      0.6750
CLASS         INTERCOMPANY                 477       196    16        22  154429.00  31922032.51  50179394.02     90            10   8034239.78      385  51288458.82  3039862296.77    1.6872      1.6507
CREDIT_NOTE   HAS_CREDIT_NOTE             1396       970     2         0  236503.25  29698202.65  71857572.63      0             0            0     2517  84567730.63           NULL      NULL        NULL
CREDIT_NOTE   NO_CREDIT_NOTE               421       134    38       306  158727.96   4820004.76  15217213.18    421           212  15217213.18        0            0           NULL      NULL        NULL
NO_CN_REASON  FROM_DELIVERY_INVOICED       212        36     1       212    1474.00    310807.03    318317.73    212           212    318317.73        0            0           NULL      NULL        NULL
NO_CN_REASON  FROM_DELIVERY_UNBILLED        94        35     0        94  133472.10   1373914.23   6408391.94     94             0   6408391.94        0            0           NULL      NULL        NULL
NO_CN_REASON  STANDALONE_NO_LINK           115        63    37         0   23781.86   3135283.50   8490503.51    115             0   8490503.51        0            0           NULL      NULL        NULL
```
Top returning customers (by stock cost):
```
CUSTA000606  JIVO MART PVT LTD [INTERCOMPANY]                477  154429  31922032.51  50179394.02   90 no-CN (10 billed)
CUSTA001022  JIOMART LUHARI Q1 [EXTERNAL]                     92    9335    294600.00   5786227.96   10 no-CN ( 5 billed)
CUSTA000243  COFFRET MARKETING PVT LTD [EXTERNAL]              3    1864          0.00   2252239.48    0 no-CN
CUSTA000486  WAL MART INDIA PVT LTD [EXTERNAL]                88    8116     90207.02   1937441.90    2 no-CN
CUSTA000684  OCTAVOS ENTERPRISE SOLUTIONS PVT LTD [EXTERNAL]  24    4508          0.00   1800156.12    9 no-CN ( 7 billed)
CUSTA000574  JIOMART LUHARI [EXTERNAL]                        66    3869          0.00   1721220.04    9 no-CN
CUSTA000913  DIN DAYAL DULI CHAND [EXTERNAL]                   4    4653          5.25   1681127.40    1 no-CN
CUSTA000442  OJAS TRADERS [EXTERNAL]                          59    3979          0.00   1459325.61    1 no-CN
```
Oil by month — note `ZERO_VAL` converging on `RET_DOCS`, and `NO_CN_BILLED` collapsing after 2025-01:
```
MONTH    DOCS  ZERO_VAL  STOCK_COST  NO_CN  NO_CN_BILLED     MONTH    DOCS  ZERO_VAL  STOCK_COST  NO_CN  NO_CN_BILLED
2024-10   122        35  1643911.15     68            57     2025-10    65        35  7205791.74      2             0
2024-11   190        71  3316658.81     89            60     2025-11    50        26  1514203.77     10             2
2024-12   169       101  6285106.16     94            63     2025-12    74        44  1960587.53     15             0
2025-01   246       126  7618244.34     63            27     2026-01    76        31  3212654.87     25             0
2025-02    37        37  8644843.77      2             0     2026-02    60        33  5602929.47      8             1
2025-03    73        71  2805613.40      2             0     2026-03    73        37  3920923.92     13             0
2025-04    45        41  3423052.49      4             0     2026-04    31        19  2177823.76      4             0
2025-05    48        37  5804993.63      2             0     2026-05    42        41   685229.98      2             0
2025-06    64        34  5532404.69      2             1     2026-06    52        52  2271636.12      0             0
2025-07    58        38  3680337.59      5             0     2026-07    65        64   780904.71      1             0
2025-08    84        58  3754615.00      5             1     2026-08    28        28  1255747.11      3             0
2025-09    65        45  3976571.81      2             0
```

### JIVO_MART_HANADB
```
SCOPE         GRP_KEY                 RET_DOCS  ZERO_VAL  OPEN  FROM_DLV  QTY_PCS  RET_GROSS    STOCK_COST   NO_CN  NO_CN_BILLED  COST_NO_CN   CN_DOCS  CN_NET       SALES_NET      CN%SALES  COST%SALES
TOTAL         ALL                         1792       600    30      1297   137423  13686590.14  40046247.29   1369           912  14364376.89     2650  31213325.58  3225210590.90    0.9678      1.2417
CLASS         BRANCH                         0         0     0         0        0         0.00         0.00      0             0         0.00        0         0.00    58354457.12         0           0
CLASS         EXTERNAL                    1788       599    30      1293   135985  13451049.01  39889101.76   1365           912  14207231.37     2650  31213325.58  3089123100.51    1.0104      1.2913
CLASS         INTERCOMPANY                   4         1     0         4     1438    235541.13    157145.53      4             0    157145.53        0         0.00    77733033.27         0      0.2022
CREDIT_NOTE   HAS_CREDIT_NOTE              423       376     1         0    86302   8869700.00  25681870.40      0             0         0.00     2650  31213325.58           NULL      NULL        NULL
CREDIT_NOTE   NO_CREDIT_NOTE              1369       224    29      1297    51121   4816890.15  14364376.89   1369           912  14364376.89        0         0.00           NULL      NULL        NULL
NO_CN_REASON  FROM_DELIVERY_INVOICED       912        93     0       912     5722   1501725.48   1827371.43    912           912   1827371.43        0         0.00           NULL      NULL        NULL
NO_CN_REASON  FROM_DELIVERY_UNBILLED       385        68     0       385    31652   2855175.66   9533179.78    385             0   9533179.78        0         0.00           NULL      NULL        NULL
NO_CN_REASON  STANDALONE_NO_LINK            72        63    29         0    13747    459989.00   3003825.69     72             0   3003825.69        0         0.00           NULL      NULL        NULL
```
Top returning customers (by stock cost) — Mart's returns are a marketplace story:
```
CUSTA000890  FLIPKART HARYANA FBF [EXTERNAL]                  27   2086         0.00  11244571.06    9 no-CN ( 3 billed)
CUSTA000910  FLIPKART (B2C-MAY-JULY) [EXTERNAL]              139  44668     64750.00  10279273.24   85 no-CN (52 billed)
CUSTA000885  FLIPKART B2C [EXTERNAL]                          55  21990         0.00   6352292.91   21 no-CN ( 7 billed)
CUSTA000722  KIRANAKART TECHNOLOGIES PVT LTD [EXTERNAL]       42   5664    170819.00   2282133.12    8 no-CN
CUSTA000912  AMAZON (B2C -MAY-JULY) [EXTERNAL]                53   4895         0.00   1777697.66   30 no-CN (17 billed)
CUSTA000648  SCOOTSY LOGISTICS PVT LTD [EXTERNAL]             59   6365   1224885.00   1694212.16    4 no-CN
CUSTA000586  HANDS ON TRADE PVT LTD [EXTERNAL]                36   3337    132592.00    995765.78    4 no-CN
CUSTA000879  FLIPKART INDIA PRIVATE LIMITED [EXTERNAL]        19   5584    119399.00    800694.14    4 no-CN
```

### JIVO_BEVERAGES_HANADB
```
SCOPE         GRP_KEY                 RET_DOCS  ZERO_VAL  OPEN  FROM_DLV  QTY_PCS  RET_GROSS   STOCK_COST  NO_CN  NO_CN_BILLED  COST_NO_CN  CN_DOCS  CN_NET      SALES_NET     CN%SALES  COST%SALES
TOTAL         ALL                          160       133    34        20   170452  354166.87   259426.66      59             3   189198.63      101  1179435.25  217424155.44   0.5425      0.1193
CLASS         BRANCH                         1         1     0         0     4800       0.00        0.00       1             0        0.00        0        0.00    5971053.73        0           0
CLASS         EXTERNAL                     128       101    18        19   140952  354166.87   241086.47      41             2   188475.99       87   908081.88  206736566.67   0.4392      0.1166
CLASS         INTERCOMPANY                  31        31    16         1    24700       0.00    18340.19      17             1      722.64       14   271353.37    4716535.04   5.7532      0.3888
CREDIT_NOTE   HAS_CREDIT_NOTE              101        96     0         0   146885  151919.00    70228.03       0             0        0.00      101  1179435.25          NULL     NULL        NULL
CREDIT_NOTE   NO_CREDIT_NOTE                59        37    34        20    23567  202247.87   189198.63      59             3   189198.63        0        0.00          NULL     NULL        NULL
NO_CN_REASON  FROM_DELIVERY_INVOICED         3         1     0         3       28    1213.42      207.78       3             3      207.78        0        0.00          NULL     NULL        NULL
NO_CN_REASON  FROM_DELIVERY_UNBILLED        17         1     0        17     6374  127534.45   188363.35      17             0   188363.35        0        0.00          NULL     NULL        NULL
NO_CN_REASON  STANDALONE_NO_LINK            39        35    34         0    17165   73500.00      627.50      39             0      627.50        0        0.00          NULL     NULL        NULL
```
**Bev's `STOCK_COST` is correct but tiny, and that is the point.** ₹2,59,427 is exactly what SAP
put back into inventory (verified three ways, §2 trap 2b) — but 132 of the 160 documents, carrying
**148,870 of the 170,452 pieces returned (87.3%)**, were valued at nil, and **54% of the ₹2.59 L
that *is* measured is the single raw-material document from trap 12**. So the honest Bev sentence
is "170,452 bottles came back; SAP costed ₹2.59 L of them", never "Bev's returns cost ₹2.59 L".

---

## 4. What the section actually says (the answers Accounts asked for)

**Returns as a % of sales.** Value answer, `CN_PCT_OF_SALES`: **Oil 0.92%, Mart 0.97%, Bev 0.54%**
of invoiced sales (ex-GST, ex-migration). Cost answer, `RET_COST_PCT_OF_SALES`: **Oil 0.94%,
Mart 1.24%**, Bev **0.12%** (real, but covering only 13% of Bev's returned pieces — trap 2b).
Oil's external-only rate is **0.61%** vs intercompany **1.69%** — the
Oil→Mart stock flow returns nearly 3x more per rupee than real customers do. **VERIFIED.**

**Returns by month / top customers.** In the live output above. Oil's returning "customer" is
overwhelmingly its own Mart company (477 docs, ₹5.02 Cr at cost); Mart's are marketplaces
(Flipkart FBF/B2C = 221 docs, ₹2.79 Cr at cost).

**Return notes with no credit note — the one that matters.** Headline counts:

| | live returns | no linked live CN | of which base delivery WAS invoiced | stock cost of that subset |
|---|---|---|---|---|
| Oil | 1817 | 421 (23.2%) | **212** | ₹3.18 L |
| Mart | 1792 | **1369 (76.4%)** | **912** | ₹18.27 L |
| Bev | 160 | 59 (36.9%) | 3 | ₹208 |

Split by reason (`SCOPE='NO_CN_REASON'`) so nobody reads an unbilled shipment as a missing credit:
`FROM_DELIVERY_INVOICED` = credit **is** due · `FROM_DELIVERY_UNBILLED` = no credit due ·
`STANDALONE_NO_LINK` = unanswerable from structure, check by hand.

**The Oil/Mart contrast is the finding.** Of Oil's 212 billed-uncredited returns, **207 (97.6%) are
dated 2024-10 to 2025-01** — a go-live-era backlog that stopped; Oil's current process links credit
notes properly. Of Mart's 912, only **36** are from that era; the rest run through every month to
2026-08. **Oil's is a historic cleanup. Mart's is a live, ongoing linkage gap.** VERIFIED (summed
from the MONTH rows of the live output above).

**How much of that is real money — honestly, we do not know, and the query does not claim to.**
"No credit note" means *no credit note linked in SAP*. Live credit notes with no base document on
any line: **Oil 2723 of 6147, Mart 975 of 4384, Bev 161 of 399.** A customer can have been credited
by one of those and this query cannot attribute it. A proximity probe — does the same customer have
any live credit note within ±30 days of the return? — gives:

```
                  billed & uncredited   has same-customer CN within +/-30d
JIVO_OIL_HANADB                  212                                  114
JIVO_MART_HANADB                 912                                  366
```
So roughly half of Oil's and 40% of Mart's were **plausibly credited but never linked**. That is a
**heuristic, not proof** (a nearby credit note may be for something else entirely) and it is
**INFERRED**, not verified — it is deliberately *not* a column in the SQL. Treat
`RET_DOCS_NO_CN_BILLED` as a **work list to check**, never as a proven loss.

---

## 5. Unresolved / not checked — stated plainly

1. **Whether any of the uncredited returns is a real loss is NOT established.** The ±30-day probe
   above is triage, not evidence. Settling it means opening the customer ledgers — out of scope here.
2. **Why SAP values 87% of Bev's returned pieces (and 27% of Mart's) at nil is not established.**
   It is not a missing-journal bug — `OINM` shows the receipts, priced at zero, because the item's
   warehouse moving-average cost is zero (§2 trap 2b, VERIFIED). *Why* those items carry a zero
   moving average — never costed at first receipt, a costing-method setting, or goods issued before
   they were ever valued — I did **not** investigate. It is an item-master / costing question, not
   a return-note question, and it distorts every cost figure in Bev, not just this section.
3. **The free-text invoice references in `"Comments"` are not parsed** (414 Oil returns, ≥3
   incompatible formats). A parser could recover the missing invoice link but would need a
   correction-grade rule and per-customer format handling. Not attempted.
4. **`STANDALONE_NO_LINK` (Oil 115 docs / ₹84.91 L, Mart 72 / ₹30.04 L) is genuinely unanswerable
   from document structure.** These carry the most stock cost of the three uncredited buckets in
   Oil and are the real work list, but nothing in SAP's linkage says whether credit was due.
5. **Reconciliation state was not used anywhere in this section.** The session-level warning that
   `JDT1."IntrnMatch"=0` everywhere does not affect these tables — I used `JDT1` only for the
   `SUM("Debit")` on the return's own journal, which does not depend on reconciliation. **Not
   checked** beyond that, because nothing here needs it.
6. **`ODLN` is joined only in the detail file.** The summary decides "was the base delivery
   invoiced?" straight from `RDN1."BaseEntry"` without confirming the delivery exists. I verified
   the two agree exactly — rank counts computed with and without the `ODLN` join are identical in
   all three books (Oil 212/115/94, Mart 912/72/385, Bev 3/39/17) — so there are no orphan
   `BaseEntry` values today. It could drift.
7. **No tonnage conversion.** Task allowed it with a stated factor; I left quantities in PIECES
   because the lines mix PCS/SET/KGS/NOS/LTR/MTR/DRM and the item mix is not all oil. Converting
   would need a per-item pack-size rule that does not exist in this section.

---

## 6. Adversarial review — 2026-08-21

This section was re-opened by a second agent whose brief was to assume the SQL was wrong and prove
it. Every figure below was pulled live from HANA during that review with an **independently written
query** — not by re-running the section and reading its own answer back. `VERIFIED` means the query
was run in this session and its output is quoted; `INFERRED` means it was reasoned, not run.

**Verdict: the arithmetic survived. Ten attacks, zero wrong numbers.** Two claims *about* the
numbers were wrong and are corrected above (§2 trap 2b, and the Bev caption in §3); four new
limitations were found and are recorded below; three rendering bugs were found on the page itself and
fixed in `site/index.html`. **No executable SQL changed** — `build_data.py` strips the comment
header before execution, so `pipeline/sql/return-note.sql` produces byte-identical SQL to before
the review, and the published numbers are unchanged.

### 6.1 What was attacked, and how it was checked

| # | Attack | Method | Result |
|---|---|---|---|
| 1 | Double counting / join fan-out | Re-derived every TOTAL measure from single-table aggregates, and summed each facet | **CLEAN** |
| 2 | Cancelled documents | `"CANCELED"` distribution on every table touched | **CLEAN** |
| 3 | Branch + intercompany | Classified all 23 group CardCodes in all 3 books, both directions | **CLEAN** |
| 4 | Unapplied money | Grepped the SQL: no `ORCT` / `OVPM` / `"OpenBal"` / `"IntrnMatch"` anywhere | **N/A by construction** |
| 5 | Migrated openings 2024-09-30 | Counted them on both `ORDN` and `OINV` | **CLEAN** |
| 6 | Three-schema portability | Ran the statement on all 3 schemas at 3 different as-of dates | **CLEAN** |
| 7 | Empty and null | Ran at `{{ASOF}}` = 2024-10-01, before any return exists | **CLEAN, returns a row** |
| 8 | Money units | Every column name checked against its actual scale | **CLEAN in SQL, 3 render bugs** |
| 9 | Re-derive the headline another way | `RET_STOCK_COST` reached 3 independent ways | **AGREES to the paisa** |
| 10 | Performance | Timed on all 3 books | **1.4–2.0 s summary, 1.3–2.1 s detail** |

**1 — double counting. VERIFIED clean.** Each headline was rebuilt from scratch and matched exactly:

```
                              section says       independent query says   route
Oil RET_DOCS                          1817                         1817   COUNT(*) on ORDN
Oil RET_GROSS                  34518207.41                  34518207.41   SUM(DocTotal) on ORDN
Oil RET_QTY_PCS                   395231.21    391267.21 + 3964 = 395231.21   RDN1 grouped by "unitMsr"
Oil RET_STOCK_COST             87074785.82                  87074785.82   JDT1 debit summed BY ACCOUNT
Oil RET_DOCS_NO_CN                     421                          421   NOT EXISTS on RIN1/ORIN
Oil RET_STOCK_COST_NO_CN       15217213.18                  15217213.18   correlated subqueries, no joins
Oil CN_DOCS / CN_NET       2517 / 84567730.63       2517 / 84567730.63    RIN1 grouped by "BaseType"
Oil SALES_NET                9237973076.04   9985334384.71 - 747361308.68 = 9237973076.03
Mart RET_STOCK_COST            40046247.29                  40046247.29
Mart NO_CN_REASON        912 / 385 / 72               912 / 385 / 72      EXISTS-based rewrite
Bev  RET_STOCK_COST              259426.66                    259426.66
Bev  NO_CN_REASON             3 / 17 / 39                  3 / 17 / 39
```
Fan-out was ruled out at the source: `ORDN."TransId"` is **unique** on live returns (Oil 1732 rows /
1732 distinct, Mart 1640 / 1640, Bev 28 / 28), so the `JDT1` join cannot multiply; every `RIN1`
line carries exactly one `"BaseEntry"`, so `CN_NET` cannot; and `QTY` / `DLVBASE` / `RDLV` are each
grouped to one row per return before they are joined. Facet sums were checked too — `MONTH` and
`CLASS` each sum to `TOTAL` exactly for `RET_DOCS`, `RET_STOCK_COST` and `CN_NET` in all three books.

**2 — cancelled documents. VERIFIED clean.** `"CANCELED" = 'N'` is applied on all four document
tables the section reads (`ORDN`, `OINV`, `ORIN`, and `OINV` again inside `DLVINV`). The three-value
trap is real and correctly handled:

```
        ORDN total   'N' live   'Y' cancelled   'C' cancellation mirror
OIL           2031       1817             107                      107
MART          1844       1792              26                       26
BEV            184        160              12                       12
```

**3 — branch and intercompany. VERIFIED clean, both directions.** Every one of the 23 known group
CardCodes was classified in every book. **No group card falls through to EXTERNAL**, and **no
third-party customer is falsely caught** — the only cards matching either test are JIVO entities:

```
OIL   BRANCH: CUSTA000001/2/3/4, CUSTA001099 (group 'BRANCH CUSTOMER')
      INTERCOMPANY: CUSTA000606 JIVO MART PVT LTD (group 'DELHI' — 477 returns, 92.5% of header value),
                    CUSTA000827, CUSTA000906, CUSTA001113
MART  BRANCH: CUSTA000827/874/875/876/877/878/926   INTERCOMPANY: CUSTA000001 (4 returns)
BEV   BRANCH: CUSTA000001/2/3/4 (CUSTA000002 has the 1 branch return)
      INTERCOMPANY: CUSTA000606 (31 returns), CUSTA000827
```
The same codes are *different, unrelated* parties in other books — Oil's `CUSTA000874` is RAKESH
BROTHER, Mart's is JIVO MART PVT LTD - DL — which is exactly why the section classifies by
group-name-then-card-name and not by a hard-coded code list. Both classes get their own row; neither
is dropped or folded into EXTERNAL. (Mart's `VENDA000001` trap does not reach this section: `ORDN`
and `OINV` are customer documents, `"CardType"` = `'C'` throughout.)

**4 — unapplied money. N/A, and proven so rather than assumed.** The section is document-shaped, not
balance-shaped. It reads no `ORCT`, no `OVPM`, no `"OpenBal"`, and touches `"DocStatus"` only to
publish `RET_DOCS_OPEN` as a labelled diagnostic. There is nothing here to double-subtract.

**5 — migrated openings. VERIFIED clean.** `ORDN` has **zero** documents dated 2024-09-30 in any
book, so the filter on the return side is a genuine no-op (kept as a safety belt). On the sales
side it matters: Oil carries **11,078** invoices dated exactly 2024-09-30 worth **₹74.74 Cr**;
including them would inflate `SALES_NET` by **8.09%** and shrink every ratio. Mart and Bev: none.

**6 — three-schema portability. VERIFIED clean.** The statement uses no UDF (`U_*` column), no
hard-coded account code, and no hard-coded card code — the only literals are SAP object types
(13/14/15/16), `"CANCELED"` values and the go-live date. Run on all three schemas at
`{{ASOF}}` = 2026-08-21, 2025-12-31 and 2024-10-01: **9 runs, 9 exit-0**, sensible movement in
between. Row counts are stable and bounded (72 / 70 / 72 at today's date, `LIMIT 200` never near).

**7 — empty and null. VERIFIED clean.** At `{{ASOF}}` = 2024-10-01 (before any book has a return)
the query returns the `TOTAL` row with `RET_DOCS` = 0 and `NULL` in every `SUM`-derived column,
plus whatever `CLASS`/`MONTH` rows the sales side produces. Nothing throws, nothing divides by
zero (`CASE WHEN s.NET > 0` guards both ratios). The dashboard renders `NULL` as an em dash, so an
empty book reads "no returns" rather than "₹0".

**8 — money units. The SQL is honest; the page was not.** Every money column carries raw INR and no
`_L` / `_CR` suffix, which is what the renderer's convention means by "anything else = rupees", and
the magnitudes check out (Oil `SALES_NET` 9,237,973,076 = ₹923.80 Cr across 23 months ≈ ₹40 Cr a
month — right for Oil). **No column name lies about its scale.** Two *rendering* bugs were found in
`site/index.html` and fixed:

* `isMoneyCol()` had no `_cost` suffix, so `RET_STOCK_COST` and `RET_STOCK_COST_NO_CN` — the two
  columns this whole section is built on — rendered as bare integers ("8,70,74,786") beside
  ₹-formatted columns in the same table. Fixed by adding `_cost` to the suffix list. Checked every
  `raw/*.tsv` header first: **`return-note` is the only section with a `_COST` column**, so the
  change cannot disturb anyone else's numbers.
* `RET_COST_PCT_OF_SALES` is a percentage (Oil 0.9426) but appeared in the CLASS table with no
  formatter, so it went through `num()` and was **rounded to a whole number** — Oil and Mart showed
  `1`, Bev showed `0`, on a table people read as "returns as a share of sales". Fixed by forwarding
  `cell` through `renderFaceted()` (additive; blocks that do not define one are unaffected) and
  giving the column a `0.00%` formatter. The KPI tile was already correct — it formats explicitly.
  **Still open elsewhere:** the same rounding hits `LR_PCT` / `VEH_PCT` in `transporter`,
  `RET_PCT_OF_GRPO` in `goods-return`, `MANUAL_JE_PCT*`, `RECONCILED_LINES_PCT`, `CARD_REAL_PCT`
  and `INV_SAMEDAY_PCT`. Those are other sections' calls to make; flagged, not touched.
* `isMoneyCol()` also read two **document counts** as money, because of how they end:
  `RET_DOCS_ZERO_VALUE` (matched on `value$`) and `RET_DOCS_OPEN` (matched on `open$`, and shared
  with `goods-return`). Neither appears in a rendered table today, so nothing was visibly wrong —
  but the next person to add one to a `cols:` list would have got "₹1,104 documents". Fixed by
  excluding any column containing `_DOCS_`. Verified safe by scanning **all 411 distinct columns in
  every `raw/*.tsv`**: every `_DOCS_` column in the whole dashboard is a count, none is money, and
  after the change **zero** count columns are misdetected anywhere.

**Latent, deliberately left alone:** `RET_STOCK_COST_NO_CN` **is** money and `isMoneyCol()` does
**not** detect it (it ends `_NO_CN`, not a money suffix). It is currently rendered only by the
"Returned, never credited" KPI, which calls `money()` explicitly and is correct. Do not add it to a
table block without a `cell` formatter. Teaching the shared regex to strip trailing qualifier
suffixes would be too clever for the blast radius, so this is documented rather than fixed.

**9 — the headline, reached three ways. VERIFIED, agrees to the paisa.** `RET_STOCK_COST` is the
biggest thing the section asserts, so it was rebuilt from `JDT1` **by account** (which also tests
the claim that every debit is inventory) and from `OINM`, SAP's own inventory audit trail, which
shares no table with the section's cost path:

```
OIL   JDT1 debits: 1103001 82,165,397.46 . 1103002 3,364,918.66 . 1103004 636,327.25
                 . 1103011 557,736.79 . 1103005 221,773.61 . 1103010 104,704.12
                 . 1103003 15,035.72 . 1103006 279.04 . 5100001 8,613.16  = 87,074,785.81
      OINM "TransValue" 87,066,172.66 + "PriceDiff" 8,613.16 (Dr) = 87,074,785.82
      section                                                      87,074,785.82
MART  JDT1 1103001 39,598,272.13 . 1103004 193,528.11 . 5100001 107,277.95
           . 1103002 84,678.56 . 1103003 62,490.54                = 40,046,247.29
      OINM 39,938,969.34 + 107,277.95 = 40,046,247.29 . section     40,046,247.29
BEV   JDT1 1103012 140,113.03 . 1103001 119,200.62 . 1103002 113.00 . 5100001 0.01 = 259,426.66
      OINM 259,426.65 + 0.01 = 259,426.66 . section                                  259,426.66
```
The account test holds in **all three books, not just Oil**: every debit lands on `1103xxx`
inventory (plus the `5100001` price-difference impurity) and every credit on `5000xxx` COGS or
`1102007` SALES BRANCH TRANSFER. `OJDT."TransType"` is **16 on all 1732 / 1640 / 28 journals**, so
no foreign entry leaks in. No `JDT1` line carries a negative debit or credit, and
`"IntrnMatch"` = 0 / `"Closed"` = `'N'` on **100%** of them — SAP's internal reconciliation is
unused here, as it is everywhere else at JIVO. The price-difference impurity is bigger in Mart than
the header suggested: **₹107,278, or 0.268% of Mart's total** (Oil 0.0099%, Bev negligible). Still
immaterial, still left in, now stated correctly.

`SALES_NET` was re-derived the same way: Oil `9,985,334,384.71 − 747,361,308.68 = 9,237,973,076.03`
against the section's `9,237,973,076.04`; Mart `3,225,210,590.90` and Bev `217,424,155.44` exact.

**10 — performance. VERIFIED.** Summary 1.5 / 1.4 / 1.4 s, detail 1.9 / 2.0 / 1.3 s (Oil / Mart /
Bev), 9.5 s for the whole section through `build_data.py` including connect. Nowhere near the 60 s
daily-refresh budget.

### 6.2 New limitations found by the review

These are recorded in the SQL header as traps 12–15 so they travel with the query.

**12. `CN_DOCS` is not additive across rows — by design.** It is a `COUNT(DISTINCT` credit note`)`
computed inside each group, which is right for that group and wrong to add up. Oil's 23 `MONTH`
rows sum to **2518** against a `TOTAL` of **2517**, because one credit note credits returns dated in
two different months and is correctly counted in both. Every *other* measure is additive and was
checked. **Never sum `CN_DOCS` across rows.** VERIFIED.

**13. "No credit note" has a measured false-positive rate, and it is small.** Following the full
structural chain — return → base delivery → the invoice that consumed that delivery → a credit note
raised against **that invoice** (`RIN1."BaseType"=13`) — finds returns already credited by the other
route:

```
                    billed & uncredited   of those, credited via the invoice chain
OIL                                 212                                          4  (1.9%)
MART                                912                                          3  (0.3%)
BEV                                   3                                          0
```
They are deliberately still counted as uncredited: a credit note against the invoice does not prove
the **returned line** was the line credited, so the structural test the section uses is the honest
one. Budget ~2% noise on Oil's work list, ~0.3% on Mart's. VERIFIED. (This is a *separate*, much
smaller leak than the standalone-credit-note route in §4, which stays unmeasurable.)

**14. `RET_DOCS_NO_CN_BILLED` rounds 3 Mart documents the generous way.** A return can cite more
than one base delivery (Oil 2 do, Mart 8, Bev 0). When those deliveries disagree about whether they
were invoiced, `DLV_INVOICED` takes `MAX`, so the return counts as BILLED. **Exactly 3 Mart returns
are affected; Oil and Bev none.** Immaterial, but a choice rather than an accident. VERIFIED.

**15. The "was the base delivery invoiced?" test was cross-checked and is exact.** `DLVINV` reads
`INV1."BaseType"=15` on a live invoice. The mirror-image route, `DLN1."TargetType"=13`, was run
against it: **zero disagreement in either direction** in all three books (Oil 202 of 289 base
deliveries invoiced, Mart 898 of 1258, Bev 3 of 20). `ODLN."DocStatus"` is useless for this — **all**
base deliveries are `'C'` closed, including the never-invoiced ones, because the return itself
closed them. Another instance of the house rule that `"DocStatus"` means nothing at JIVO. VERIFIED.

### 6.3 Earlier claims re-tested and confirmed

Every quantitative claim in the SQL header was re-run rather than taken on trust. All held:

* `"CANCELED"` three-value distribution (2031/1817/107/107 · 1844/1792/26/26 · 184/160/12/12).
* `DocTotal` = 0 on **1104 / 600 / 133** live returns; zero returns have `DocTotal` = 0 with a
  non-zero `VatSum`, and none has a negative `DocTotal`.
* UoM split, to the third decimal, in all three books.
* The link-direction evidence: return-side-only **5 Oil / 0 Mart / 3 Bev**, credit-note-side-only
  **3 / 0 / 0**, and **all** return-side-only cases point at a `"CANCELED" = 'Y'` credit note (the
  eleven rows were printed and read). Live returns with a live credit note missed by the
  credit-note-side join: **0 in all three books.** The direction chosen is the right one.
* `RDN1."BaseType"=13` (invoice) is **0 rows** everywhere; `BaseType`=15 on 306 / 1297 / 20 live
  returns, matching `RET_DOCS_FROM_DELIVERY` exactly.
* Credit notes with no base document on any line: **2723 of 6147 · 975 of 4384 · 161 of 399**.
* **414** Oil returns mention "INVOICE" in `"Comments"` (Mart 55, Bev 64).
* `CN_NET` completeness: credit notes carrying a `BaseType`=16 line carry **no other lines at all**
  in any book, and their `BaseType`=16 line totals match the header net to within ₹131 on ₹8.46 Cr
  (Oil), ₹27 (Mart), ₹14 (Bev). `CN_NET` is not clipping anything.
* Every return's `"CardCode"` resolves in `OCRD`; no live return has a blank `"CardName"`; so the
  `IFNULL` fallbacks in `RET` never fire today.
* The ±30-day proximity probe in §4 reproduces exactly: **Oil 212 → 114, Mart 912 → 366** (Bev
  3 → 1). Still a heuristic, still deliberately not a column.
* Oil's billed-uncredited backlog really is historic — **207 of 212 fall in 2024-10 … 2025-01** —
  while Mart's runs through **every month to 2026-08** (2025-01: 36, then 49/47/45/85/85/89/57/51/
  48/36/44/61/15/37/45/39/21/13/9). The Oil-is-a-cleanup / Mart-is-live contrast holds.

### 6.4 Still unresolved after the review

1. **Why SAP values 87% of Bev's and 27% of Mart's returned pieces at nil** (see §5.2). Not a bug in
   this section; an item-master / costing question that distorts every cost figure in those books.
2. **Whether any uncredited return is a real loss** — unchanged from §5.1. The review narrowed the
   *structural* false positives (finding 13: 4 Oil, 3 Mart) but the standalone-credit-note route
   stays unattributable, and that is the big one.
3. **`ORDN` used for raw-material returns** (trap 12 in §2, Oil 3 / Mart 0 / Bev 1 documents) is
   still unfiltered. Confirmed materially significant only in Bev, where one document is 54% of
   the measured cost.
4. **The detail file had never been run before this review.** `return-note-detail.sql` was written
   after the last build, so `data.json` carried no `detail` for this section and no
   `raw/return-note-detail.*.tsv` existed. It has now been run through the pipeline: **Oil 500
   (capped inside rank 4), Mart 500 (capped inside rank 1 — take Mart's counts from the summary),
   Bev 184 (complete)**, 35 columns, and its rank/flag distribution agrees with the summary exactly
   (Oil 212/115/94 + 79 filler, `FLAG_NO_CREDIT_NOTE` = Y on 421; Bev 3/39/17 + 125, Y on 59).
5. **The detail rows are shipped but not rendered.** `RENDERERS['return-note']` consumes `summary`
   only, so ~1,184 detail rows sit in `data.json` unused. That is the house pattern for every
   section here (`goods-return`, `grpo`, `transporter` do the same) — noted, not changed.
