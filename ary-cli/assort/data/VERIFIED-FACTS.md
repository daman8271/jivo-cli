# ARY — verified facts

Every figure here was pulled live from `FR8HODBNEW` on **2026-08-28** with the `ary`
CLI. Each carries the command that produced it. Nothing on this page is an estimate;
estimates live in the research corpus and are labelled there.

**Data currency:** sales, purchases and stock transfers stop at **2026-08-21** because an
internal physical stock audit is in progress. Accounting is live to 2026-08-27. Any
"12-month" window below is 2025-08-01 → 2026-08-21 and is therefore ~3 weeks short of a
full year at the tail. Sales figures are **gross of sale returns** (0.78-3.66% by year)
unless the line says net.

---

## 1. The population and the wallet ARY captures

12-month window, `ary assort wallet`:

| | |
|---|---|
| Sales | **₹7.55 Cr** |
| Bills | 365,087 |
| Average bill | **₹207** |
| Spend per resident per month | **₹1,259** |
| Bills per resident per month | **6.08** |

Denominator is the **stated** 5,000-resident headcount, not a queried one.

---

## 2. Revenue by financial year (net of returns) — `ary sales net --from … --to …`

| FY | Net sales | Bills |
|---|---|---|
| FY23-24 | ₹6.22 Cr | 322,561 |
| FY24-25 | ₹5.84 Cr | 267,576 |
| FY25-26 | ₹6.92 Cr | 329,589 |
| FY26-27 to 21-Aug | ₹3.51 Cr | 168,881 |

Lifetime: **₹22.49 Cr net** on 1,088,607 bills; 1,891 return documents worth ₹33.84 L
(1.48% of gross).

---

## 3. ⭐ The finding that carries the whole case: growth came from NEW counters, not the store

Like-for-like, the **same 143 days (1 Apr → 21 Aug) in each year**, sales ₹:

| Counter | 2023 | 2024 | 2025 | 2026 | 2026 vs 2023 |
|---|---|---|---|---|---|
| Ary Pos (the core store) | 1,73,80,378 | 1,77,32,604 | 1,69,14,531 | 1,91,74,179 | **+10.3%** |
| Ary Clothing | 41,34,261 | 48,77,759 | 56,13,206 | 52,99,903 | +28.2% |
| **Basement** (new 2025) | 0 | 0 | 34,86,102 | **50,96,951** | NEW |
| **Fruits & Vegetables** (new 2025) | 0 | 0 | 18,80,571 | **26,99,620** | NEW |
| Ary G Canteen | 12,55,967 | 12,19,974 | 16,91,089 | 23,69,215 | +88.6% |
| Ary Lite | 3,04,678 | 4,74,966 | 5,70,125 | 7,36,582 | +141.8% |
| Ary Apple A Day | 23,65,932 | 0 | 0 | 0 | **DEAD** |
| Talwandi Sabo | 11,40,975 | 9,70,453 | 0 | 0 | **DEAD** |
| Ary Warehouse | 1,07,327 | 0 | 0 | 0 | dead |
| **TOTAL** | **2,66,89,518** | **2,52,75,756** | **2,71,55,624** | **3,53,76,450** | **+32.5%** |

Decomposition of the ₹86.9 L increase:

- **New counters (Basement + Fruits & Veg): +₹78.0 L — 89.8% of all growth.**
- Same-store (Pos + Clothing + G Canteen + Lite): +₹45.0 L, +19.5%
- Counters that died (Apple A Day, Talwandi Sabo, Warehouse): −₹36.1 L

**Read:** the core store has grown ~3.3% a year for three years — flat in real terms.
Every rupee of real growth came from opening a category ARY did not previously carry.
Fruits & Vegetables went from nothing to ₹27 L a season on 133 SKUs at **172 stock
turns a year** — the fastest-turning counter ARY has. The expansion thesis is not a
hypothesis; ARY has already run the experiment twice and it worked both times.

---

## 4. The catalogue is mostly fiction — `ary assort velocity`

| | |
|---|---|
| Active SKUs | 19,481 |
| Sold at least once in 12 months | **6,197** |
| Never sold in 12 months | **13,284 (68%)** |
| Sold exactly one bill | 537 |
| Sold under ₹1,000 in the year | 1,722 |

Revenue concentration:

| Band | SKUs | Sales | Share |
|---|---|---|---|
| Top 50% of revenue | **252** | ₹3.77 Cr | 50.0% |
| To 80% | 856 (cum. 1,108) | ₹2.27 Cr | 30.0% |
| To 95% | 1,764 (cum. 2,872) | ₹1.13 Cr | 15.0% |
| Last 5% | 3,325 | ₹0.38 Cr | 5.0% |

**252 SKUs earn half the money. 1,108 earn 80%.**

Important nuance — `ary assort dead --by-group`: the 13,284 non-selling SKUs hold almost
**no stock**. The top 20 dead groups lock only ~₹4.3 lakh at cost. This is a **catalogue
hygiene** problem (dead lines still flagged active, still priced, still counted), **not**
trapped working capital. Do not report it as crores of dead inventory.

---

## 5. Shelf headroom — `ary assort headroom`

| Counter | active | SKUs stocked | sold 12m | not moving | sales 12m | turns/yr | negative rows |
|---|---|---|---|---|---|---|---|
| Ary Pos | yes | 9,867 | 5,496 | **4,371** | ₹4.29 Cr | 7.9 | 81 |
| Ary Clothing | yes | 1,970 | 1,335 | 635 | ₹1.35 Cr | 3.2 | 21 |
| Basement | yes | 192 | 98 | 94 | ₹70.8 L | — | 0 |
| Ary G Canteen | yes | 1,208 | 359 | **849** | ₹52.7 L | 6.3 | 43 |
| Fruits & Vegetables | yes | 133 | 106 | 27 | ₹50.1 L | **172.1** | 32 |
| Ary Lite | yes | 713 | 364 | 349 | ₹18.4 L | 74.3 | 34 |
| Ary Warehouse | yes | 9,094 | 0 | 9,094 | 0 | 0 | 16 |
| Ary Apple A Day | **no** | 506 | 0 | 506 | 0 | — | 0 |
| Talwandi Sabo | **no** | 621 | 0 | 621 | 0 | 0 | **607** |
| Girls Canteen Ts | **no** | 222 | 0 | 222 | 0 | — | 0 |

**Basement did ₹70.8 L on 14 bills** — ₹5.06 lakh a bill. That is institutional/bulk
supply, not retail.

---

## 6. Category coverage — the thin end. `ary assort coverage`

`per_resident_yr` = that category's annualised sales ÷ 5,000 residents.

| Category | active SKUs | sold | dead | 12m sales | **₹/resident/YEAR** |
|---|---|---|---|---|---|
| Mobile | 8 | 2 | 6 | ₹2,690 | **₹0.54** |
| Fashion Jewellery | 91 | 2 | 89 | ₹9,890 | ₹1.98 |
| Disposable | 53 | 17 | 36 | ₹30,899 | ₹6.18 |
| **Gurmat** (Sikh religious articles) | 27 | 7 | 20 | ₹34,555 | **₹6.91** |
| Kids Wear | 83 | 13 | 70 | ₹40,121 | **₹8.02** |
| Frozen | 57 | 24 | 33 | ₹49,244 | ₹9.85 |
| Toys | 220 | 18 | 202 | ₹74,369 | ₹14.87 |
| Cookware | 133 | 40 | 93 | ₹1,44,155 | ₹28.83 |
| Electricals | 120 | 31 | 89 | ₹1,50,568 | ₹30.11 |
| Sports | 136 | 41 | 95 | ₹1,71,021 | ₹34.20 |
| Appliances | 184 | 47 | 137 | ₹1,72,256 | ₹34.45 |
| Food Supplement | 205 | 56 | 149 | ₹2,99,990 | ₹60.00 |
| **Medicare** | 272 | 99 | 173 | **₹3,15,279** | **₹63.06** |
| Dairy Products | 41 | 15 | 26 | ₹9,31,461 | ₹186.29 |

Categories with **no group at all**: baby care (3 SKUs sit in an "Accessories →
Baby Accessories" subgroup), pet care, optical/eyewear, hardware/tools/DIY.
"Academy Books" holds 288 SKUs, **all deactivated**. "Raw Material" holds 149 active
SKUs with zero sales.

The thick end, for contrast: Confectionery ₹1,969/resident/yr, Personal Care ₹1,013,
Academy Dress ₹931, Winter Wear ₹865, Fruits ₹717, Vegetable ₹538.

### Medicare is not a pharmacy

Top 12 Medicare sellers, 12 months — every one is a general-store home remedy:

| Product | Sub-group | 12m sales |
|---|---|---|
| Dettol Antiseptic Liquid 210 ml | Antisept Lotion | ₹20,214 |
| **Jivo Pain Relief Oil 250 ml** | Pain Relief | ₹18,040 |
| GSK Eno 5 g Lemon Fresh | Eno | ₹17,931 |
| Dabur Honitus Cough Remedy 100 ml | Cough Syrup | ₹17,202 |
| Dettol Antisept Lotion 60 ml | Antisept Lotion | ₹11,105 |
| Vicks VapoRub 10 ml | Vaporub | ₹10,833 |
| Dabur Chyawanprash 450+50 g | Chyawanprash | ₹10,800 |
| Vicks Inhaler 0.5 ml | Medicare | ₹10,344 |
| Boroline Antiseptic Cream 20 g | Medicare | ₹9,945 |
| Dwarkesh Anar Dana Goli 100 g | Pachak Churan | ₹8,350 |
| Dabur Glucose D 125 g | Glucose | ₹8,089 |
| Johnson's Benadryl 150 ml | Banadryl | ₹8,055 |

No paracetamol. No antibiotic. No antacid tablet. No ORS sachet. No BP, diabetes,
thyroid or asthma medicine. No prescription anything. **A township of 5,000 — including
several thousand boarding children — has ₹63 per head per year of Dettol and churan and
no pharmacy.** JIVO's own Pain Relief Oil is the second-best seller in the category.

---

## 7. Seasonality — January empties the township

Bills by month, `SaleHeader` × `SaleDetail`:

| | 2024 | 2025 | 2026 |
|---|---|---|---|
| **January** | **15,957** | **10,038** | **15,078** |
| February | 23,340 | 16,006 | 22,776 |
| March | 26,017 | 24,547 | 31,040 |
| April | 29,210 | 29,125 | 37,085 |
| May | 27,945 | 25,847 | **41,388** |
| June | 28,990 | 29,199 | 38,563 |
| July | 20,086 | 22,208 | 29,576 |

January falls 35-65% below the surrounding months, every single year — the residential
school empties for the winter break and Rajgarh sits at ~1,700 m. July dips too.
**March-June is peak.** Any range plan has to hold this shape: a January-heavy stock
build is money parked for two months.

---

## 8. The books — `ary ledger trial`, `ary accounts list --group <id>`

| Group | Balance (debit-positive) |
|---|---|
| Sales A/C | ₹21.22 Cr Cr |
| Sales Return | ₹0.32 Cr Dr |
| Purchase | ₹16.54 Cr Dr |
| Purchase Return | ₹0.44 Cr Cr |
| Profit & Loss A/C | **₹2.70 Cr DEBIT** |
| Salary Expenses (6 accounts) | ₹1.51 Cr |
| Indirect Expenses (56 accounts) | ₹0.82 Cr |
| Direct Expenses (12) | ₹0.20 Cr |
| Vehicle Expenses (5) | ₹0.02 Cr |
| Deposits (Asset, 10) | ₹1.93 Cr |
| Fixed Assets (64) | ₹0.88 Cr |
| Bank Accounts (7) | ₹0.55 Cr |
| Reserves & Surplus | ₹0.51 Cr Cr |
| Secured Loans (3) | ₹0.47 Cr Cr |
| Sundry Creditors (648) | ₹0.71 Cr Cr |
| **Akal Academy Cs (3,604 accounts)** | ₹0.22 Cr Dr |
| Local Debtors - Baru Sahib (15) | ₹0.37 Cr Cr |
| Employee Customer Account (112) | ₹0.11 Cr Dr |
| Branch / Divisions (4) | ₹0.94 Cr Dr |

Crude trading margin: ₹21.22 Cr − ₹16.54 Cr ≈ **₹4.68 Cr on ₹21.22 Cr ≈ 22%** before
stock movement. **The ₹2.70 Cr debit on Profit & Loss A/C is not yet interpreted** — under
Indian convention a debit P&L balance is an accumulated loss, but this CLI presents all
balances debit-positive, so the sign has to be proved from the ledger before anyone
repeats it. Flagged, not concluded.

---

## 9. Stock variance — `ary audit variance`

Lifetime physical counts, at cost:

| Warehouse | shortage | excess | net |
|---|---|---|---|
| Basement | ₹58.58 L | ₹67.05 L | +₹8.47 L |
| Ary G Canteen | ₹54.31 L | ₹14.11 L | **−₹40.19 L** |
| Ary Pos | ₹46.34 L | ₹37.27 L | −₹9.07 L |
| Ary Clothing | ₹37.24 L | ₹37.35 L | +₹0.11 L |
| Ary Apple A Day | ₹25.21 L | ₹1.85 L | **−₹23.36 L** |
| Ary Warehouse | ₹17.68 L | ₹6.27 L | −₹11.43 L |
| Talwandi Sabo | ₹12.44 L | ₹0.68 L | −₹11.76 L |
| Fruits & Vegetables | ₹6.81 L | ₹0.43 L | −₹6.38 L |
| Ary Lite | ₹0.31 L | ₹2.56 L | +₹2.25 L |
| **TOTAL** | **₹2.59 Cr** | **₹1.67 Cr** | **−₹91.5 L** |

−₹91.5 L is **4.1% of lifetime net sales**. Indian retail shrink normally runs 1-2%.
Both halves being enormous points at book-keeping failure as much as loss — the largest
single shortage line is "Packing Material Exp." at ₹11.01 L, and "Jivo Canola Refined
Edible Oil 15 Ltr" shows ₹6.62 L short in G Canteen and ₹2.43 L in Basement. G Canteen's
−₹40.19 L is consistent with recipe consumption never being posted.

Negative book stock, `ary stock value`: **Ary Clothing −408,439 qty on 21 rows**,
**Talwandi Sabo −145,519 on 607 rows**, Ary G Canteen −9,642 on 43, Ary Pos −7,222 on 81.

---

## 10. Data quality limits — what cannot be answered from this database today

| Limit | Evidence |
|---|---|
| **97% of bills have no identified buyer.** Customer 00001, ledger account "Cash", carries 1,054,205 of 1,088,607 lifetime bills and ₹17.13 Cr at ₹162.53 average | `ary sales by-customer`, `ary customers get 00001` |
| **99.7% of bills have no salesperson.** SalesPersonID [NONE] on 1,085,051 bills | `ary sales by-staff` |
| **No cost price in the master.** `StandardCostPrice` set on **41 of 19,481** active SKUs; `StandardSalePrice` on 562; `MaxRetailPrice` on **zero** | `SELECT COUNT(*), SUM(CASE WHEN … )` on ProductMaster |
| Real cost/price/margin exists only per-location on `ProductChildMaster` (purchase_cost, mrp, selling_price, margin_pct) | `ary products children` |
| **No ARY↔SAP item map.** `ProductCodeSAP` present on all 21,466 SKUs, empty in every one | `ary products sap-gap` |
| `ProductMaster.QuantityOnHand` is dead — non-zero on one SKU. On-hand is `Stock.Quantity` | `study/specs/schema-notes.md` |
| The payment-mode table's Cash amount reads ₹10,023 Cr against ₹22.49 Cr of net sales — **that column is unusable**, do not quote `ary sales payment-mix` amounts | `ary sales payment-mix` |
| SAP login is `sa` (sysadmin). The read-only guarantee comes from the CLI's guard, not from the grant | `ary doctor` |

## 11. JIVO inside ARY

126 SKUs carry "JIVO" in the name. Two intercompany customer accounts are active:
**Jivo Wellness Pvt Ltd - Delhi** (39 bills, ₹12.96 L, last 2026-03-02) and
**Jivo Mart Pvt Ltd - Punjab** (2 bills, ₹6.17 L, last 2024-06-05). JIVO Pain Relief Oil
is the #2 Medicare seller; "Jivo Canola Refined Edible Oil 15 Ltr" is simultaneously the
third-largest shortage line and a dead-stock line (₹2.12 L on hand, last sold
2024-07-11).

---

## 12. ⭐ The two successful launches — ARY's own playbook

### Fruits & Vegetables: nothing → ₹68 L a year on ~70 SKUs

Monthly, warehouse 18, from first bill:

| Month | SKUs sold | Bills | Sales |
|---|---|---|---|
| 2024-08 (launch) | 12 | 1 | ₹3,855 |
| 2024-09 | 55 | 651 | **₹3.39 L** |
| 2025-03 | 51 | 3,527 | ₹4.15 L |
| 2025-08 | 66 | 1,803 | ₹5.34 L |
| 2026-03 | 63 | 4,566 | ₹4.14 L |
| 2026-05 | 79 | 6,322 | **₹6.37 L** |
| 2026-06 | 77 | 5,658 | **₹6.83 L** |

Three things to copy:

1. **It reached run-rate in ONE month** — ₹3,855 in the launch month, ₹3.39 L the next.
   There was no slow ramp to wait out.
2. **The range never grew.** 55 SKUs at launch, 77 today. Sales doubled while the
   assortment stayed flat.
3. **The growth came from FREQUENCY, not range.** Bills went 651 → 6,322 — nearly 10×
   in 21 months. Residents came back more often once fresh produce simply existed.

### Basement: one customer, ₹77.5 L a year

All of Basement's 12-month revenue is **customer 002CM, "Hunger Heroes"** — a
mass-feeding/langar kitchen buying a standing ~59-line provisions basket roughly monthly at
₹5.4-6.7 lakh a bill. Its top lines: Rice 1 Kg ₹7.57 L, Loose Milk ₹7.57 L, Atta 1 Kg
₹5.84 L, Rice_L ₹4.49 L, Milk_Z ₹3.82 L, Atta_L ₹3.39 L, Fortune Soya 1 L ₹2.82 L,
Dahi_Z ₹2.45 L, Paneer_Z ₹2.43 L, Frozen Peas ₹1.78 L.

### Sales per moving SKU per year — where productivity actually lives

| Counter | SKUs sold 12m | Sales 12m | **₹ per SKU per year** |
|---|---|---|---|
| Basement | 105 | ₹77.5 L | **₹73,826** |
| Fruits & Vegetables | 111 | ₹54.9 L | **₹49,482** |
| Ary G Canteen | 368 | ₹56.8 L | ₹15,429 |
| Ary Clothing | 1,345 | ₹1.40 Cr | ₹10,432 |
| **Ary Pos (core store)** | 5,671 | ₹4.68 Cr | **₹8,255** |
| Ary Lite | 373 | ₹19.8 L | ₹5,296 |

Basement is **9×** and Fruits & Veg **6×** more productive per SKU than the core store.

**Read:** the answer to "carry everything people need" is not ten thousand more SKUs. Both
things that have worked at ARY were narrow, high-turn ranges — one fresh, one
institutional. The core store's 5,671 moving SKUs already earn only ₹8,255 each.

---

## 13. ⭐ JIVO owns the shop and holds half the shelf in its own core category

Edible Oil & Ghee (groups 122 + 140), 12 months:

| | SKUs | 12m sales |
|---|---|---|
| **JIVO own brand** | 22 | **₹7.79 L** |
| **Competitor brands** | 20 | **₹7.78 L** |
| Unbranded ghee / til | 7 | ₹16.62 L |

ARY is a unit of **Jivo Wellness Pvt Ltd — an edible oil company** — and inside its own
captive store, competitors sell as much branded oil as JIVO does.

Competitor lines, 12 months: Fortune Soya 1 L ₹3.09 L, Soyabean Fortune_L ₹1.77 L,
Mashal Mustard 500 ml ₹0.65 L, Fortune Soya 750 ml ₹0.64 L, Pcs Mustard 200 ml ₹0.45 L,
Gagan Soyabean ₹0.29 L, Pansari Til ₹0.42 L, Mashal 1 L ₹0.23 L, Gagan Vanaspati ₹0.19 L,
Kings Soya ₹0.12 L, Minchy's, Mahakosh, Figaro.

**Fortune (Adani Wilmar) totals ₹5.52 L, and ₹4.59 L of it — 83% — is the single
Hunger Heroes langar account.** One institutional buyer, one standing monthly order, is
buying a competitor's soya oil inside a JIVO-owned shop. That is one conversation, not a
project.

Meanwhile **"Jivo Canola Refined Edible Oil 15 Ltr"** is simultaneously ARY's third-largest
stock shortage (₹6.62 L in G Canteen, ₹2.43 L in Basement) and a dead-stock line
(₹2.12 L on hand, last sold 2024-07-11), and **JIVO Pain Relief Oil is the second-best
seller in the whole Medicare category** (₹18,040). The own-brand signal is there; nobody is
managing it.

---

## 14. Flagged for Accounts — a probable duplicate bill

Customer 002CM (Hunger Heroes), 11 May 2026, four bills keyed between 17:49 and 18:57:

| Serial | Bill | Voucher time | Entered | Lines | Value |
|---|---|---|---|---|---|
| 2002747.0001 | Hp1 | 17:49 | 17:50 | 59 | ₹5,45,332.29 |
| 2002751.0001 | Hp2 | 18:54 | 18:55 | 59 | **₹5,91,370.12** |
| 2002752.0001 | Hp3 | 18:56 | 18:56 | 59 | **₹5,91,370.12** |
| 2002753.0001 | Hp4 | 18:57 | 18:57 | 59 | ₹5,50,114.12 |

**Hp2 and Hp3 are identical to the paisa on the same 59 lines, entered one minute apart.**
That looks like a double-keyed bill worth **₹5.91 lakh**. ARY has no bill-cancellation
document, so a duplicate can only be reversed by a sale return — and no matching return
exists. Reported, not acted on: this CLI cannot write, and nobody asked for a correction.

---

## 15. ⭐⭐ The largest single gap: the campus mess does not buy from ARY

Named institutional buyers, 12 months (customer 00001 = anonymous walk-in, excluded):

| Customer | Bills | 12m sales | Avg bill | What it looks like |
|---|---|---|---|---|
| **Hunger Heroes** | 13 | **₹76.6 L** | ₹5,88,870 | mass-feeding kitchen, standing monthly provisions order |
| Akal Academy | 2,055 | ₹26.7 L | ₹1,299 | departmental petty purchasing, not provisions |
| Jivo Wellness Pvt Ltd - Delhi | 16 | ₹11.4 L | ₹71,358 | intercompany |
| Enquiry The Kalgidhar Trust Baru Sahib | 1,045 | ₹10.1 L | ₹969 | departmental petty purchasing |
| Katebaa Rural Services Foundation-06 | 4 | ₹8.0 L | ₹2,00,017 | second bulk buyer |
| Cash Sale (0000D) | 102 | ₹7.1 L | ₹6,998 | |
| University Students | 295 | ₹6.5 L | ₹2,220 | |
| **Akal Catering Services (Mess)** | 150 | **₹4.3 L** | ₹2,875 | **the campus mess** |
| Camp Commandant NCC Solan | 23 | ₹2.6 L | ₹11,142 | outside body |
| Akal De-Adiction Ward | 661 | ₹2.4 L | ₹368 | |
| Gurmat Camp Baru Sahib | 35 | ₹1.1 L | ₹3,259 | |
| **Akal Hospital Baru Sahib** | 64 | **₹0.8 L** | ₹1,240 | **a hospital exists on campus** |
| Akal Nursing College Baru Sahib | 42 | ₹0.8 L | ₹1,831 | |
| Eternal University | 50 | ₹1.3 L | ₹2,647 | |

Three conclusions, all from this one table:

**1. The mess bypasses ARY almost entirely.** "Akal Catering Services (Mess)" buys
**₹4.3 lakh a year** at ₹2,875 a bill. A kitchen feeding several thousand boarders consumes
provisions in crores. Whatever it buys, it buys somewhere else.

**2. One feeding programme is the whole institutional business, and it is small relative to
the campus.** Cross-checking Hunger Heroes' own consumption against mess norms: it took
40,780 kg of grain (17,800 kg rice + 22,980 kg atta) and 24,232 L of milk over 12 months.
At ~375 g grain and ~200 ml milk per person per day that feeds **≈300-330 people
year-round** — against a boarding population in the thousands. ARY supplies under a tenth
of the campus's institutional food.

**3. There is a hospital on campus** (Akal Hospital Baru Sahib) and it buys ₹79,000 a year
from ARY. That cuts both ways for the pharmacy question: the hospital presumably dispenses
to inpatients, so it takes a slice of retail pharmacy demand — and it is itself an
unserved institutional customer for surgicals and consumables.

**4. Trust departments buy petty, not consolidated.** Akal Academy on 2,055 bills at ₹1,299,
the Kalgidhar Trust on 1,045 bills at ₹969. Thousands of small bills instead of a
procurement contract.

**The independent research lane put the institutional mess wallet at ~₹5.5 Cr a year with
ARY at ₹1.31 Cr annualised — 24% captured, ~₹4.2 Cr of headroom. This table is consistent
with that and arrived at it a different way.** For comparison, the entire retail store is
₹4.29 Cr a year. The mess is the single largest number on the table and it is not a new
category — it is a customer ARY already bills.

That lane also concluded the **retail** store is ~77% saturated against a ~₹10.1 Cr
addressable retail wallet (HP rural MPCE ₹5,825/person/month, HCES 2023-24, VERIFIED;
escalated to ~₹6,850 for Aug-2026, ESTIMATED), leaving ~₹2.3 Cr of retail headroom. It rated
its own confidence **medium**, because only ~4,433 of the ~5,000 residents are externally
corroborated and the cohort split is unverified. Treat ₹4.2 Cr and ₹2.3 Cr as well-founded
estimates, not measurements.

---

## 16. ⭐⭐⭐ Eternal University spends ₹2.51 Cr a year on food and buys ₹2.78 lakh from ARY

**This is the single largest verified finding of the whole exercise**, and it comes from
EU's own audited accounts, not an estimate.

Eternal University 17th Annual Report 2024-25, Income & Expenditure statement:
- line 9 "Mess meal charges" — **₹196.00 lakh**
- line 11 "Boarding & lodging expenditure for EU faculty/staff" — **₹55.00 lakh**
- **Total food/boarding spend: ₹251 lakh a year**

What EU's group buys from ARY in 12 months (`ary sales by-customer`):
Eternal University ₹1.32 L + Apple A Day ₹0.69 L + Akal Nursing College ₹0.77 L
= **₹2.78 lakh. ARY has 1.1% of it.**

The buyer is on the same 450-acre campus. No new location, no new population, no new
licence, no new category is required to sell to it.

### The whole campus institutional wallet

| Institution | Est. annual food budget | Bought from ARY (12m) | ARY share |
|---|---|---|---|
| Eternal University (mess + staff boarding) | **₹251 L (VERIFIED)** | ₹2.78 L | **1.1%** |
| Akal Academy Baru Sahib (mess) | ₹222 L (ESTIMATED at EU's verified per-student rate) | ₹26.65 L | 12.0% |
| School of Spiritual Sciences | ₹54 L (ESTIMATED, same rate) | ~in Gurmat Camp | ~2% |
| Kalgidhar Trust Baru Sahib | not separable | ₹10.07 L | — |
| Akal Catering Services (Mess) | not separable | ₹4.31 L | — |
| De-Addiction Ward / Hospital | not separable | ₹5.53 L | — |
| **CAMPUS TOTAL** | **₹528-614 L (ESTIMATED)** | **₹49.47 L (VERIFIED)** | **8-9%** |

Two independent methods now agree the institutional gap is **₹4-5 Cr a year**: this
budget-vs-billed build-up, and the wallet lane's ₹5.5 Cr wallet at 24% capture. ARY's
entire retail store is ₹4.29 Cr a year. **The institutional gap is larger than the shop.**

---

## 17. The population is FLAT TO SHRINKING — growth is not coming from more people

| Claim | Status | Figure |
|---|---|---|
| Eternal University enrolment | **VERIFIED** (EU 17th Annual Report, as on 31-Jul-2025) | **1,102** — not the 2,500 on Wikipedia, nor the 1,300 on barusahib.org |
| EU enrolment a decade ago | **VERIFIED** (NAAC SSR 2015-16) | 1,108 → **no growth in 10 years** |
| EU seat fill | **VERIFIED** | 503 admitted against 974 sanctioned = **51.6%** |
| EU hostel spare capacity | VERIFIED | ~400 beds empty of ~1,500 |
| Akal Academy Grade X registrations | **VERIFIED** (CBSE disclosure, school code 43022) | 125 (2019-20) → 98 (2024-25), **−22%** |
| Akal Academy Grade XII registrations | **VERIFIED** (same) | 113 (2018-19) → 57 (2025-26), **−50%** |
| Akal Academy total enrolment | ESTIMATED from board cohorts | ~1,250 (range 1,100-1,450), not the "over 1,550" directories quote |
| School of Spiritual Sciences | VERIFIED | 305 students |
| AIRWE rural women | VERIFIED count | 487 |
| EU faculty + staff | VERIFIED (EU report) | 116 + 29 = 145 — not Wikipedia's 170+200 |
| Resident staff families | VERIFIED partial ("more than 200 families") | ~700-1,300 family members |
| **Term-time township total** | ESTIMATED | **~4,550-4,800** — the ~5,000 brief is sound |

Plus footfall nobody counted: **Akal Charitable Hospital, 100 beds, 11 doctors, ~120-131
outside OPD patients a day** (43,706-47,848 free OPD a year) with attendants; gurdwara
pilgrims and visiting parents; and the Trust's **4,409 network teachers** rotating through
Baru Sahib for training (the Trust runs 130 schools / 75,000 students).

**Implication:** ARY's +29% cannot be explained by population. It is wallet share. And a
range plan that assumes a growing customer base is planning against a shrinking one.

### The winter shutdown, measured three times on ARY's own till

| Winter | Term benchmark | Vacation floor | Bills ratio | Revenue ratio | Window |
|---|---|---|---|---|---|
| 2023-24 | 988.0 bills/day (Nov) | 465.9 | 47.2% | 39.0% | 27 Dec – 25 Jan |
| 2024-25 | 727.8 (1-20 Dec) | 356.4 | 49.0% | 47.9% | 28 Dec – 8 Feb |
| **2025-26 (cleanest)** | **1,066.7 (1-23 Dec)** | **376.3** | **35.3%** | **39.2%** | **29 Dec – 20 Jan, 23 days** |

The floor is flat and hard (a 306-438 band for 23 days) and it **steps back up on a single
day** — 376 bills on 20 Jan, 638 on 21 Jan. That is a measurement, not a trend: the
permanent resident base is **~1,700-2,300 people**, and the buyer should stop buying
~29 Dec and restart ~20 Jan.

---

## 18. ⚠️ Correction to my own earlier framing — two hypotheses are now dead

**(a) The per-resident metric was overstated, because a Delhi NGO is inside it.**

`ary customers get 002CM`: **Hunger Heroes is at "Green Park Main, New Delhi, Delhi
110016"** — an outside food-charity organisation, not a resident. In FY26-27 to date it is
**₹50.97 lakh on NINE bills = 14.41% of all revenue** (verified independently: my query
returns 14.41%, the research lane 14.53%).

So the honest resident figure is **~₹1,290 per resident per month, not ₹1,493** — the
earlier number divided institutional charity sales by the residential population. The
₹1,259 figure in §1 above carries the same defect. **Corrected: strip 002CM and the other
institutional accounts before quoting any per-resident number.**

**(b) Baby care is NOT the opportunity I flagged in §6. There are almost no babies.**

Verified: **425 diaper packs in 12 months** (Pampers L-7 81, M-8 80, Happy Skin S 62,
L-5 23, plus tail). At ~7 pants a pack that is ~3,000 pants a year — **8 pants a day,
i.e. one to two children in nappies on the entire campus.** Infant formula: 13 packs.
Combined baby-specific spend ₹38,002 a year.

Baby *toiletries* do sell — Himalaya and Johnson's baby soap, shampoo, talc, oil and
lotion total ~₹1.5 lakh a year — but in India those are bought by adults as gentle
toiletries, so they are not evidence of an infant base.

**The residential cohort is boarding children aged 5-18 and students aged 18-25, not
families with infants.** My "no diapers or formula on a campus with married staff
families" line in the original PLAN.md was a plausible inference that the data refutes.
Recorded so nobody acts on it.

---

## 19. ARY has switched off three counters with live populations behind them

| Counter | Lifetime bills | Lifetime sales | Last sale | Dark for | Population still behind it |
|---|---|---|---|---|---|
| **Talwandi Sabo** (WH 14) | 91,229 | ₹51.24 L | 11-Jul-2024 | **13.5 months** | **Akal University, 2,703 students — grew from 2,172 (+24.4%) while the counter sat dark** |
| Girls Canteen Ts (WH 17) | 10,867 | ₹5.13 L | 22-Mar-2024 | 17 months | same campus, girls' hostel |
| **Ary Apple A Day** (WH 13) | 27,178 | ₹38.43 L | 30-Nov-2023 | **33 months** | **Eternal University's cafeteria — EU's 2024-25 annual report STILL names "Apple a-day" as its campus cafeteria** |

Talwandi Sabo's prior run-rate was ₹3.35 lakh a month. **ARY closed a counter serving a
captive campus whose student population then grew 24%.** And it closed EU's cafeteria while
EU kept ₹2.51 Cr of food spend and still lists the outlet as its own.

Talwandi Sabo also carries the worst data damage in the database: **607 rows of negative
book stock** and ₹1.24 Cr of lifetime shortage. Whatever happened there was not an orderly
closure.

---

## 20. Public sources about this campus are wrong — use these instead

| Widely published claim | Where it comes from | Correct figure | Authority |
|---|---|---|---|
| Eternal University has 2,500 students | Wikipedia + most aggregators | **1,102** (31-Jul-2025) | EU 17th Annual Report 2024-25 |
| Eternal University has 1,300 students | barusahib.org | **1,102** | same |
| EU has 170 faculty + 200 staff | Wikipedia | **116 faculty + 29 staff** | same |
| Akal University has 3,100 students | barusahib.org | **2,703** current session | barusahib.org year-end report |
| Akal Academy Baru Sahib has "over 1,550" | schoolmykids.com (quotes 2017-18 fees) | ~1,250 est.; board cohorts down 22-50% | school's own CBSE disclosure |

Anyone sizing ARY off the public web over-forecasts the university cohort by **127%**.

---

## 21. ⭐⭐ The mess basket needs ZERO new SKUs — ARY already stocks all of it

The full 59-line basket Hunger Heroes buys is a **mess provisions basket**, and every line
is already in ARY's catalogue and already being supplied. 12 months:

| Line | Qty | Sales | Line | Qty | Sales |
|---|---|---|---|---|---|
| Rice 1 Kg | 11,200 pcs | ₹7.57 L | Sugar 1 Kg | 3,200 pcs | ₹1.23 L |
| Loose Milk | 16,105 L | ₹7.57 L | Tomato_Z | 4,260 kg | ₹1.21 L |
| Atta 1 Kg | 15,000 pcs | ₹5.84 L | Potato_Z | 5,265 kg | ₹1.20 L |
| Rice_L | 6,600 kg | ₹4.49 L | Tea 1 Kg | 480 pcs | ₹1.00 L |
| Milk_Z | 8,127 L | ₹3.82 L | Green Chilli_Z | 1,850 kg | ₹0.94 L |
| Atta_L | 7,980 kg | ₹3.39 L | Desi Ghee 1 L | 200 pcs | ₹0.82 L |
| Fortune Soya 1 L | 2,160 pcs | ₹2.82 L | Kabuli Chana | 720 pcs | ₹0.81 L |
| Dahi_Z | 3,514 kg | ₹2.45 L | Rajma 1 Kg | 640 pcs | ₹0.74 L |
| Paneer_Z | 1,038 kg | ₹2.43 L | Mung Sabat | 760 pcs | ₹0.67 L |
| Frozen Peas_Z | 1,575 kg | ₹1.78 L | Urad Dhuli | 600 pcs | ₹0.67 L |
| Soyabean Fortune_L | 1,280 L | ₹1.77 L | Chana Black | 770 pcs | ₹0.62 L |
| Rajdhani Daliya | 4,050 pcs | ₹1.41 L | Tea_L | 300 kg | ₹0.65 L |
| Onion_Z | 4,475 kg | ₹1.37 L | + 33 more pulse, spice, veg and fruit lines |

**This is the most actionable conclusion in the whole exercise.** Supplying Eternal
University's ₹2.51 Cr mess requires **no new category, no new SKU, no licence, no cold
chain and no new supplier** — only rice, atta, milk, dal, oil, ghee, tea, sugar, spices and
vegetables that ARY buys and sells today, at volumes it already handles for another
customer. It is a purchase-order conversation, not a retail project.

Note also the pricing tier already exists: **65 SKUs carry `_Z` / `_L` suffixes** — bulk
twins of retail lines, priced and unitised differently (Rice 1 Kg in Pcs at ₹67.60 vs
Rice_L in Kgs at ₹68.00). They carry **₹39.9 lakh** of 12-month sales on 63 moving SKUs.
The institutional channel is already built; it serves one customer.

---

## 22. ⚠️⚠️ CAVEAT ON §6 — ARY's category tree is unreliable, so group-based coverage understates

Testing the tree against reality:

| Product | Filed under |
|---|---|
| Loose Milk | **Mini Meals** |
| Dahi_Z (curd) | **Others** |
| Khoya_Z | **Confectionery** |
| Loose Desi Ghee | Oil & Ghee |
| Peas (Fresh Matar)_Z | **Fruits** |
| Kala Chana_L | **Atta & Other Flours** |
| Lobia_L | **Veg Delight** |
| Mixed Daal 1 Kg | **Rice & Other Grains** |
| Nutri 1 Kg (soya chunks) | General Items |

Name-searching every dairy word (milk, dahi, paneer, curd, butter, cheese, khoya, ghee)
across all groups, 12-month sales, shows where dairy actually sits:

| Filed under | SKUs | 12m sales |
|---|---|---|
| Confectionery | 128 | ₹19.39 L |
| Oil & Ghee | 4 | ₹16.16 L |
| Mini Meals | 2 | ₹11.39 L |
| **Dairy Products** | **10** | **₹9.54 L** |
| Others | 1 | ₹2.45 L |
| Chinese Items | 1 | ₹1.88 L |
| Drinks | 19 | ₹1.45 L |
| + 7 more groups | 47 | ₹2.55 L |

**"Dairy Products" holds under 15% of the dairy-word sales.** (The name search
over-captures in the other direction — much of that Confectionery figure is milk chocolate
and milk sweets, not chiller dairy — so neither number alone is the truth.)

**Consequence:** `ary assort coverage`, which groups by `ProductGroupID`, is a reliable
measure of **what the operator's own tree says**, but it is NOT a reliable measure of
whether ARY carries a category. My §6 statements "Dairy 41 SKUs / ₹186 per resident" and
"Frozen 57 SKUs" understate real coverage by an unknown amount.

The `ary assort probe` command (§ below) was added to answer the question the group tag
cannot. **Every "missing category" conclusion in the research corpus must be re-tested with
`probe` before anyone buys stock against it.** This is the same trap as JIVO correction
C-0016: a blank usually means the value lives somewhere else.

---

## 23. ⭐⭐⭐ The honest gap table — `ary assort probe`, name-searched across ALL 21,466 SKUs

This is the trustworthy version of §6. It ignores ARY's category tree entirely and searches
product names across the whole catalogue, so a category filed in the wrong group still
counts. 12-month window, 5,000 residents.

| Probe | SKUs in catalogue | active | sold 12m | groups | 12m sales | ₹/resident/YEAR |
|---|---|---|---|---|---|---|
| **paracetamol / crocin / dolo / calpol / combiflam** | **3** | 3 | **1** | 1 | **₹502** | **₹0.10** |
| **antacid** (digene, gelusil, pantop, omez, rantac) | **0** | 0 | 0 | — | **₹0** | **₹0.00** |
| **antibiotic** (azithro, amoxy, cipro, augmentin) | **0** | 0 | 0 | — | **₹0** | **₹0.00** |
| **diabetes / BP / thyroid** (metformin, telma, amlodipine, thyronorm) | **0** | 0 | 0 | — | **₹0** | **₹0.00** |
| **pet food** (pedigree, whiskas, dog/cat food) | **0** | 0 | 0 | — | **₹0** | **₹0.00** |
| **eyewear** (spectacles, reading glasses, goggles) | **0** | 0 | 0 | — | **₹0** | **₹0.00** |
| medical devices (thermometer, oximeter, glucometer, nebuliser) | 3 | 3 | **0** | 1 | ₹0 | ₹0.00 |
| hand tools (screwdriver, plier, hammer, spanner, wrench) | 18 | **8** | **0** | 1 | ₹0 | ₹0.00 |
| ORS / rehydration (ORS, Electral, Enerzal) | 13 | 13 | 7 | 4 | ₹7,453 | ₹1.49 |
| LED bulb / battery / torch | 47 | 47 | **5** | 5 | ₹8,575 | ₹1.72 |
| protein / malted drinks (whey, Horlicks, Bournvita) | 40 | 39 | 15 | 7 | ₹60,443 | ₹12.09 |
| sunscreen / SPF | 48 | 48 | 23 | 1 | ₹88,414 | ₹17.68 |
| mobile charger / cable / earphone / power bank | 14 | 14 | 5 | 3 | ₹99,713 | ₹19.94 |
| sanitary pads / napkins | 81 | 81 | 21 | 3 | ₹4,16,962 | **₹83.39** |

### What this proves

**1. There is no pharmacy, and this is now measured, not inferred.** Across 21,466 SKUs,
ARY holds **three** paracetamol SKUs. **One** sold: Crocin 500 mg, 26 strips, **₹502.06 in
twelve months, last sold 14-Feb-2026.** Antacid, antibiotic, and every chronic-disease
medicine return a **hard zero** — not "filed elsewhere", not "thin": absent from the
catalogue. A township of 5,000 people, several thousand of them boarding children, bought
26 strips of paracetamol in a year. This is the clearest gap in the business.

**2. Three categories are listed but literally never sell.** Medical devices (3 SKUs),
hand tools (18 SKUs, 8 active) and LED/battery (47 SKUs, only 5 moving) are on the
catalogue and produced **₹0 and ₹8,575** respectively. That is not assortment; it is
paperwork.

**3. Two categories do not exist at all** — pet food and eyewear, zero SKUs. Reading
glasses for an ageing staff and teaching population, on a campus 30-50 km from an optician,
is worth a look.

**4. Sanitary pads are the one hygiene category working** — ₹83/resident/year on 81 SKUs
with 21 moving. Given ~2,000+ women and girls on campus that is roughly ₹200 each a year,
which is a plausible real number. It shows the model works when the range exists.

**5. Mobile accessories: 14 SKUs, ₹99,713.** My §6 figure of "8 SKUs, ₹2,690" came from the
"Mobile" **group tag** — the real answer, found by name, is 14 SKUs across 3 groups doing
₹1 lakh. Still tiny for 5,000 phone owners, but the group-tag number was wrong by 37×.
**This is exactly why `probe` exists.**

---

## 24. ⭐⭐ Pharmacy: a live compliance exposure, and a hard technical blocker

### ARY already sells drugs, without a drug licence

Verified at SKU level (`ary query` on SaleDetail × ProductMaster, 12-month window):

| Product | Bills | Qty | 12m sales |
|---|---|---|---|
| Vicks VapoRub 10 ml | 228 | 232 | ₹10,833 |
| Vicks Inhaler 0.5 ml | 146 | 156 | ₹10,344 |
| **Johnson's Benadryl 150 ml** | 47 | 49 | **₹8,055** |
| Strepsils 8 Tab | 208 | 246 | ₹7,101 |
| **Omnigel (Cipla) 30 g** | 37 | 37 | **₹5,486** |
| Moov Pain Relief 20 g | 44 | 45 | ₹5,445 |
| Moov Pain Relief 50 g | 22 | 22 | ₹5,035 |
| **Johnson's Benadryl 60 ml** | 43 | 47 | **₹3,760** |
| **Volini Gel 30 g** | 20 | 20 | **₹3,270** |
| + Vicks 50/25/5 ml, Moov spray/10 g, Volini spray/20 g, Vicks BabyRub | | | ₹14,400 |
| **Disprin Tablet** | 107 | 122 | ₹925 |
| **Crocin 500 mg** | 26 | 26 | ₹502 |
| **TOTAL (19 SKUs)** | **~1,100** | | **≈₹75,000** |

The research lane put the "unambiguously allopathic" slice at **₹41,023 across 613 bills**
and called ~76% (₹31,200) Schedule H.

**My correction to that lane, and it matters:** the largest lines by value — **Vicks VapoRub,
Inhaler and BabyRub, ₹28,100 combined — are licensed in India as Ayurvedic proprietary
medicines**, not Schedule H allopathic drugs. Moov is largely a counter-irritant. The
genuinely prescription-schedule molecules here are **Benadryl (diphenhydramine, ₹11,815),
Volini and Omnigel (diclofenac, ₹12,908), Crocin (paracetamol) and Disprin (aspirin)** —
roughly **₹25,000-26,000 a year**, not ₹31,200 of a ₹41,023 base.

**But the lane's underlying legal point is correct and important:** **India has no statutory
OTC category.** There is no schedule of drugs a shop may sell without a licence, so the
common idea of a compliant "OTC-only corner" does not exist in Indian law. Selling Crocin
or Benadryl over a general-store counter without a Form 20/21 licence is technically
unlicensed sale of a drug.

**Calibration, explicitly:** this is real but it is **₹25,000 a year of exposure in a
₹9 Cr business**, and it is what essentially every kirana in India does. It is a
housekeeping item to fold into the pharmacy decision — **not a scandal, and not a reason to
stop trading.** The lane's own adversarial verifier was killed by the quota reset, so
**this lane has not been independently challenged.** Treat the legal detail as
well-sourced-but-unverified until a second pass runs.

### The licensing path (HP-specific, from the lane, VERIFIED against HP sources)

| Requirement | Detail |
|---|---|
| Application | **Form 19** under Rule 59(2), for **Form 20 + Form 21** (retail) |
| Government fee | **₹3,000** challan |
| Pharmacist | A registered pharmacist with **HP Pharmacy Council (Shimla)** registration, who must swear an affidavit they are **"not engaged anywhere else in any kind of service or business"** — so a **dedicated FTE**, not a shared name |
| Premises (rural) | Site map **stamped and signed by the Panchayat Pradhan** — 2 original copies. Rural sites do not use municipal approval |
| Company papers | Board resolution authorising the applicant, plus MOA and AOA (Jivo Wellness Pvt Ltd) |
| Standing duties | **3 months' written notice before closing**; fresh licence on any change of premises or constitution |
| Schedule H1 | Separate register at time of supply: prescriber name and address, patient, drug, quantity — retained **3 years** |
| Margin | **DPCO 2013 caps scheduled-formulation retailer margin at 16%** of price-to-retailer, unchanged as at 30-Jun-2026 |
| Authority to ask | Sirmaur Drug Inspector / DHSR Shimla, **0177-2621383** |

### ⛔ The hard blocker nobody would have guessed — the ERP cannot hold an expiry date

`ary query` on `ProductChildMaster`: **111,021 rows. `ExpDate` populated on ZERO.
`MfgDate` populated on ZERO.**

FusionERP8 as configured **cannot track a pharmaceutical batch or expiry date at all.** A
pharmacy legally cannot operate without batch and expiry tracking — it is required for
recall, for Schedule H1 records and for expiry returns to the supplier. **This must be
solved before a licence is worth applying for**, and the answer depends on whether the
FusionERP8 vendor has a pharmacy module. It is a software question, not a retail one.

### The one internal question to ask first

**Akal Charitable Hospital is on the same campus** — 100 beds, 11 doctors, ~120-131 free
OPD patients a day. It almost certainly already holds a drug licence and runs a dispensary.
Two consequences: (a) it may be able to host or sponsor the licence, and (b) whatever it
already dispenses free to residents is demand a retail pharmacy will **not** get. That is
one conversation inside the same Trust, and it should happen before any money is spent.

---

## 25. ⭐⭐⭐ Margin inverts the priority: institutional is bigger in revenue, retail is bigger in PROFIT

Cost comes from `ProductChildMaster.PurchaseCost` (the only place ARY holds cost — the
product master has it on 41 of 19,481 SKUs), averaged per SKU across its location children,
applied to 12-month sold quantity.

| Channel | SKUs priced | 12m sales | Est. COGS | **Gross margin** |
|---|---|---|---|---|
| **Institutional** (Hunger Heroes' mess basket) | 103 | ₹76.55 L | ₹71.02 L | **7.2%** |
| **Retail walk-in** (customer 00001) | 6,037 | ₹5.99 Cr | ₹4.13 Cr | **31.0%** |

**Retail earns 4.3× the margin rate of institutional supply.** Which means the two
opportunities have to be sized in gross profit, not revenue:

| Opportunity | Revenue gap | × margin | **Gross profit** | Investment needed |
|---|---|---|---|---|
| Institutional / mess (₹4-5 Cr gap) | ₹4.0-5.0 Cr | 7.2% | **₹29-36 L** | **≈ nil** — no new SKU, licence, cold chain or supplier |
| Retail headroom (₹2.3 Cr, from the wallet lane) | ₹2.3 Cr | 31.0% | **₹71 L** | capital, licences, cold chain, new categories |

**Both are worth doing and they barely compete for resources.** But the ranking by
*return on effort* is unambiguous: **institutional first** — ₹29-36 lakh of gross profit
for a purchase-order conversation is the highest-ROI move available to ARY. Retail
expansion is the larger profit prize and the slower, costlier one.

A useful side conclusion: **at 7.2% ARY is not profiteering on the langar/feeding
programme.** If the fairness of a Trust-owned shop pricing to a captive population is ever
raised, this is the number that answers it.

### Real margin by category, weighted by 12-month sales

| Low margin — the institutional commodities | | High margin — where retail profit lives | |
|---|---|---|---|
| **Pulses** | **8.5%** | Academy Dress | 45.2% |
| **Vegetable** | **10.1%** | Oil & Ghee | 42.0% |
| Salt & Sugar | 13.0% | Thermals | 41.7% |
| Fabrics | 13.4% | Accessories | 41.0% |
| Tea & Coffee | 14.3% | Soft Drinks | 39.7% |
| Womens Wear | 14.6% | House Hold | 38.2% |
| **Dairy Products** | **14.8%** | Bag & Purses | 37.9% |
| Winter Wear | 15.4% | **Stationary** | **37.7%** |
| Home Furnishing | 15.8% | Footwear | 35.8% |
| **Fruits** | **16.0%** | **Personal Care** | **33.0%** |
| **Rice & Other Grains** | **16.4%** | Drinks | 33.9% |
| Edible Oil & Ghee | 17.6% | Toiletories | 31.9% |
| Mens Wear | 18.5% | Under Garment | 32.7% |
| **Atta & Other Flours** | **20.0%** | Mini Meals | 31.0% |
| Dry Fruits | 21.0% | Confectionery | 25.0% |

Every commodity the mess buys — rice, atta, pulses, dairy, vegetables, sugar, tea, oil —
sits in the **8-20%** band. Every category with retail margin — stationery, personal care,
household, accessories, footwear — sits at **32-45%**.

**Two figures in that table are artefacts, not findings:**
- **Spices −64.1%** — a unit mismatch (bought in Kg, sold in Pcs, or the averaged child
  cost is wrong). It is not a loss-making category.
- **Chinese Items 88.2%, Sandwiches 96.7%, Chatpati Items 65.9%** — canteen prepared food,
  where the "cost" on the finished dish is not its recipe. These are inflated because
  **recipe consumption is never posted** — the same defect that produces G Canteen's
  −₹40.19 lakh stock variance (§9).

**Confidence: medium-high on the 7.2% vs 31.0% split** (two large, independent populations,
6,037 SKUs on one side), **medium on individual category rates** — averaging `PurchaseCost`
across location children is a rough method, and the Spices row proves it can fail. Anyone
acting on a single category's rate should re-derive it from that category's own children.

---

## 26. Talwandi Sabo — a counter that worked, switched off, at a campus that then grew 24%

Monthly sales before it went dark (warehouses 14 + 17):

| Month | Bills | Sales | | Month | Bills | Sales |
|---|---|---|---|---|---|---|
| 2023-08 | 6,481 | ₹4.71 L | | 2024-02 | **10,460** | **₹5.47 L** |
| 2023-09 | 9,371 | **₹5.57 L** | | 2024-03 | 9,440 | ₹4.71 L |
| 2023-10 | 9,534 | ₹4.90 L | | 2024-04 | 8,958 | ₹4.17 L |
| 2023-11 | 9,422 | ₹4.62 L | | 2024-05 | 6,017 | ₹3.05 L |
| 2023-12 | 8,460 | ₹4.26 L | | 2024-06 | 3,401 | ₹1.62 L |
| 2024-01 | 7,777 | ₹3.84 L | | **2024-07** | **665** | **₹0.86 L** — last month |

At its plateau (Sep-2023 → Mar-2024) it ran **~9,500 bills and ~₹4.8 lakh a month** —
about **₹55-58 lakh a year**. It then decayed over four months and stopped on 11-Jul-2024.

Meanwhile **Akal University, Talwandi Sabo grew from 2,172 to 2,703 students (+24.4%)**
(barusahib.org year-end report). The captive population behind that counter is a quarter
larger than when the counter was working.

At the retail margin measured in §25 (31.0%), reinstating the prior run-rate is worth
**₹17-18 lakh of gross profit a year** — from a shop that has already proved it works, on a
campus in the same Trust network.

Two cautions before anyone reopens it:
- The Punjab GST registration **03AACCJ4223F1Z6** is still live, so returns are presumably
  still being filed on a dormant business — worth confirming.
- Talwandi Sabo carries the worst data damage in the database: **607 rows of negative book
  stock** and **₹1.24 Cr of lifetime shortage**. Whatever happened in mid-2024 was not an
  orderly closure, and it should be understood before stock is put back in.

The parallel case is **Ary Apple A Day** — Eternal University's cafeteria, ₹38.43 lakh and
27,178 bills lifetime, dark since 30-Nov-2023 (**33 months**), while EU's 2024-25 annual
report **still names "Apple a-day" as its campus cafeteria.**

---

## 27. ⭐ The supply base for the institutional play already exists

12 months to 21-Aug-2026, `ary purchases summary` / `by-supplier`:

**Total purchases ₹6.36 Cr on 2,966 bills.**

| Supplier | GSTIN | Bills | 12m purchases | Read |
|---|---|---|---|---|
| M/S Shashi Bhushan Manoj Kumar Aeron | — | 261 | **₹70.97 L** | largest supplier, deep relationship |
| Dharam Pal & Sons | 04AAKFD3082F1ZP (Chandigarh) | 13 | ₹45.92 L | bulk, ₹3.5 L a bill |
| **Himachal Wholesale Syndicate** | 02AABFH6020J1ZX | 36 | ₹39.82 L | HP local wholesale |
| **Raja Ram Jai Prakash & Co.** | 02AAEFR2111D1Z5 | 55 | ₹39.39 L | HP local wholesale |
| **Hygienic Milk** | — | **880** | ₹25.72 L | daily milk — a working perishable route |
| Mangla Sales Corporation | 02BDQPR7603L1Z5 | 27 | ₹24.36 L | HP |
| Sahni Trading Co. | 02ABZPS8831R1ZG | 28 | ₹22.67 L | HP |
| Katebaa Rural Ser & Sol Foundation | 06AAKCK3871G1ZD (Haryana) | 8 | ₹20.14 L | also a *customer* (₹8.0 L) |
| Solan Agencies | 02AERPS9622K1ZX | 25 | ₹18.95 L | HP, Solan |
| Lakhmi Chand Tejoo Mal | 07AAAFL3353P2Z1 (Delhi) | 33 | ₹16.91 L | fabrics |
| Gian Chand Faquir Chand | 02AABFG7465L1ZB | 23 | ₹16.65 L | HP |
| Leela Associates | 02BHSPB6268F2ZC | 126 | ₹16.29 L | HP, frequent |
| **Jivo Wellness Pvt Ltd - Haryana** | 06AACCJ4223F1Z0 | 35 | **₹13.34 L** | **intercompany — ARY buys JIVO oil** |
| Sunil Trading Co. | 02ABZPK6081F1ZF | 57 | ₹13.61 L | HP |
| Parhlad Chand Batra & Sons | 02ABMPB2280L1ZV | 22 | ₹13.15 L | HP |

**Why this matters for recommendation 1:** at least ten of the top fifteen suppliers carry
**02 (Himachal Pradesh) GSTINs** and already run 22-126-bill relationships with ARY, plus a
Chandigarh bulk source at ₹3.5 lakh a bill and **a daily milk route running 880 deliveries a
year**. Quadrupling staples volume for a mess contract is a **price negotiation with
existing suppliers**, not a new supply chain to build. That is the single biggest
execution risk on the institutional play, and it is already largely retired.

Also worth noting: **Katebaa Rural Services & Solutions Foundation is both a supplier
(₹20.14 L) and a customer (₹8.00 L)**, and JIVO's own Haryana branch is a ₹13.34 L supplier.

### A cross-check that does not fully reconcile — flagged, not concluded

Sales ₹7.55 Cr against purchases ₹6.36 Cr implies a crude **15.8%** gross spread. But the
measured channel margins in §25 (retail 31.0% on ₹5.99 Cr, institutional 7.2% on ₹0.77 Cr)
imply roughly **₹1.91 Cr of gross profit ≈ 28%**.

The two differ by around **₹0.7 Cr**. Purchases are not COGS — stock build, timing and the
in-progress physical audit all sit in that gap — but the size of the discrepancy is
suggestively close to ARY's own measured stock variance (§9: −₹91.5 L net, 4.1% of sales).
**This is an observation worth a proper investigation, not a finding.** It needs an opening
and closing stock figure to settle, which the audit will produce.

---

## 28. ⭐ The year turns on one 27-day window, and it must be paid for at the cash floor

Uniform and boarder-kit groups (Academy Dress, Unstiched Suits, Winter Wear, Footwear,
Fabrics, Thermals), monthly:

| Month | Sales | | Month | Sales |
|---|---|---|---|---|
| 2025-08 | ₹9.86 L | | 2026-02 | **₹6.18 L** ← trough |
| 2025-09 | ₹11.19 L | | **2026-03** | **₹30.31 L** ← **5× the month before** |
| 2025-10 | ₹21.64 L | | 2026-04 | ₹17.30 L |
| 2025-11 | ₹13.74 L | | 2026-05 | ₹12.63 L |
| 2025-12 | ₹11.17 L | | 2026-06 | ₹8.31 L |
| 2026-01 | ₹10.71 L | | 2026-07 | ₹8.86 L |

**Verified independently: the 27 days from 22-Feb-2026 to 20-Mar-2026 carried ₹25.74 lakh
across 966 bills** — about 15% of the annual uniform business in 7% of the year.
(The research lane said ₹27.8 L on a slightly wider group set; same conclusion.)

**The working-capital problem this creates:** that stock has to be ordered and paid for in
**December**, which is exactly when ARY's cash is at its annual floor — January retail runs
at roughly half a normal month because the campus is empty. **The single biggest sales
window of the year is financed from the weakest cash position of the year.** It needs to be
a named seasonal facility, ordered by 30 November, not funded out of working cash.

### The operating calendar — climate × academic year × festivals

Rajgarh (1,551 m) monthly normals, from the seasonality lane:

| Month | High / Low °C | Rain mm | Wet days | What it means for the shelf |
|---|---|---|---|---|
| Jan | 14.4 / 2.8 | 23 | 2.8 | Coldest, frost. **Campus empty.** Buy nothing. |
| Feb | 16.7 / 3.3 | 36 | 3.5 | Cool ends ~Feb. Uniform trough before the spike |
| Mar | 21.7 / 7.2 | 28 | 3.6 | **Peak month.** Uniform + kit. Warm days, cold nights |
| Apr | 27.2 / 12.2 | 25 | 2.9 | Hot season begins |
| May | 31.7 / 16.7 | 36 | 4.1 | Hottest. Highest bill count on record (41,388) |
| Jun | 32.2 / 19.4 | 114 | 9.6 | **Monsoon arrives ~mid-June** |
| Jul | 27.8 / 19.4 | **249** | **18.0** | Wettest. Rainwear, gumboots, umbrellas, damp-proofing |
| Aug | 25.6 / 18.3 | **244** | **18.3** | Near-equal wettest, 20.6 muggy days |
| Sep | 25.0 / 15.6 | 132 | 10.2 | Monsoon withdraws |
| Oct | 22.8 / 10.6 | 23 | 2.1 | Driest and clearest. **Winter wear peaks** |
| Nov | 20.0 / 7.2 | **5** | 0.7 | Driest of all. **Order the March uniform stock now** |
| Dec | 16.1 / 4.4 | 10 | 1.5 | Cool season starts. Cash floor begins |

Operational moves this implies, all verifiable against the data above:

1. **Order the uniform/kit block by 30 November**, financed as a named facility.
2. **Move the annual physical stock count from August to the January trough.** ARY currently
   counts in August — which is why sales, purchases and transfers in this database stop at
   21-Aug-2026. Counting in January, when footfall is at 35-49%, costs far less disruption
   and does not blind the business during a trading month.
3. **Buy woollens twice** — Oct-Dec and again for March, because nights stay cold into spring
   while days warm fast.
4. **Buy rainwear for July-August**, not for the calendar monsoon: 18 wet days a month in
   both, on a hill campus.
5. **Reverse the stationery calendar** — it indexes highest in August, not at session start.

---

## 29. ⭐⭐⭐ ARY is already JIVO's captive consumer test market — and nobody is reading it

The oil finding in §13 was only half the story. Pulling everything JIVO-branded through
ARY, 12 months:

**74 JIVO SKUs sold · 12,552 bills · 45,420 units · ₹18.03 lakh.**

And it is not oil. It is JIVO's entire diversification portfolio, being consumed at scale by
5,000 people:

| JIVO SKU | Units sold | 12m sales | Bills | Buy cost → sell price |
|---|---|---|---|---|
| **Natural Mineral Water 1 L** | **12,982** | **₹2,59,640** | **4,685** | ₹6.34 → ₹20.00 |
| Wheatgrass Pet 160 ml Punjabi Jeera | 8,534 | ₹85,340 | 1,853 | ₹6.20 → ₹10.00 |
| Wheatgrass Pet 250 ml Punjabi Jeera | 5,117 | ₹76,755 | 154 | ₹14.29 → ₹15.00 |
| Natural Mineral Water 500 ml | 4,216 | ₹42,558 | 809 | |
| Natural Mineral Water 250 ml | 2,138 | ₹12,828 | 183 | ₹3.00 → ₹6.00 |
| Wheatgrass Juice 200 ml — Blueberry | 1,291 | ₹45,185 | 297 | ₹28.13 → ₹35.00 |
| Wheatgrass Juice 200 ml — Apple | 1,263 | ₹43,805 | 334 | ₹27.86 → ₹35.00 |
| Wheatgrass Juice 200 ml — Mojito | 1,233 | ₹43,155 | 403 | |
| Wheatgrass Mango 500 ml | 546 | ₹18,300 | 53 | |
| Wheatgrass Juice 200 ml — Mango | 708 | ₹20,795 | 205 | ₹27.68 → ₹35.00 |
| Wheatgrass Juice 200 ml — Rose | 615 | ₹21,525 | 338 | |
| Wheatgrass 200 ml — Ginger Ale | 390 | ₹13,650 | 148 | |
| Pista 250 g Salted | 185 | ₹64,750 | 167 | ₹289.29 → ₹350.00 |
| Koffie 100 g | 95 | ₹19,950 | 71 | ₹161.90 → ₹210.00 |
| Pain Relief Oil 250 ml | 94 | ₹18,040 | 61 | ₹142.86 → ₹200.00 |
| Green Cardamom 100 g | 31 | ₹15,469 | 30 | ₹414.29 → ₹499.00 |

**What this actually is:** a 5,000-person closed consumer panel, running a full
flavour-and-format matrix on JIVO's newest categories, with real money changing hands and
every transaction already in a database. Companies pay market-research firms for exactly
this and get a fraction of the sample.

### The panel is already answering questions

**Sugar-free is failing, decisively:**

| Wheatgrass | SKUs | Units | 12m sales |
|---|---|---|---|
| Regular | 10 | **20,112** | ₹3,72,660 |
| **Sugar-free** | 4 | **1,485** | ₹51,975 |

Sugar-free variants are **7% of wheatgrass units** despite carrying a quarter of the SKU
count. Four SKUs earning 12% of the category's revenue is a delisting decision, made with
real purchase data rather than a focus group.

**Format beats flavour:** Punjabi Jeera in the small 160 ml PET pack outsells every
fruit-flavoured 200 ml variant **combined** (8,534 units vs ~5,500). The winning
configuration is the cheap, small, savoury one — ₹10 retail.

**Mineral water is the real hit:** 12,982 units of 1 L across **4,685 separate bills** — that
is repeat consumer behaviour, not a bulk order, at a **68% retail margin** (₹6.34 → ₹20).

### The blocker, and why it links to the identity problem

**JIVO gets the volume signal but not the buyer.** With 97% of bills booked to one anonymous
walk-in account (§10), nobody can tell whether the wheatgrass is bought by 18-25 university
students or by staff families, whether the sugar-free variants failed with everyone or only
with the young, or whether mineral water is a hostel habit or a visitor purchase.

Fixing identity capture at the till — a student ID scan, a phone number, a campus wallet —
converts ARY from a shop that happens to sell JIVO products into **a segmented product-test
instrument for the parent company.** That is a strategic argument for the identity fix that
has nothing to do with retail analytics, and it is probably worth more to JIVO than ARY's
entire ₹18 lakh of own-brand sales.

---

## 30. ⭐ Tailoring: ARY pays 18 tailors ₹17.03 lakh a year and bills ₹5.92 lakh for it

`ary ledger trial` on the **"Stiching Charges Payable"** group — 18 accounts:

| | |
|---|---|
| Debits (paid to tailors, 12m book movement) | **₹17,06,317** |
| Credits (charges accrued) | ₹17,02,929 |
| Net movement | ₹3,388 |

The 18 tailor accounts: Amita Kumari, Anita-Tailor, Balwinder Singh Tailor, Inderpreet
Kaur, Joginder Singh, Kawaljeet Kaur, Kuldeep Kaur, Madhu Chanda Talior, Manjeet Kaur
(inactive), Pooja, Rahul, Rahul Talior, Sharma Ji, Shubham Tailor, Subham, Sukhdeep Kaur,
Suman Kaur, Virender Singh Tailor.

Against that, the revenue side (`SaleDetail`, 12 months):

| | |
|---|---|
| "Stiching Charges From Customer" | **₹5,92,043** across **1,457 bills** |

**Correction to the services research lane:** it reported "18 tailors, ₹5.77 lakh a year"
and framed this as *a service ARY never bills*. Both halves need fixing. ARY **does** bill
it — ₹5.92 lakh on 1,457 bills, and it is the **second-largest single SKU in the whole
catalogue** by transaction count. And the tailor cost is not ₹5.77 lakh: the ledger shows
**₹17.06 lakh** of payments through that group.

**What the corrected numbers actually say:** ₹5.92 lakh billed against ₹17.06 lakh paid.
Either

- roughly **₹11 lakh of tailoring labour is being absorbed into garment cost** rather than
  charged as a service (plausible — ARY sells unstitched suits: Tejoo, Pranav and K Mark
  lines total well over ₹15 lakh a year, and stitching them is part of that sale), or
- the service is genuinely under-recovered by ₹11 lakh a year.

**Which of those it is cannot be settled from this data**, and it matters — one is normal
accounting, the other is an ₹11 lakh leak. It needs the ARY accountant to say whether
stitching labour sits inside the unstitched-suit margin. Flagged as the single highest-value
question this exercise cannot answer itself.

Either way the lane's underlying recommendation survives in stronger form: **stitching is
already a real, high-frequency service business at ARY** — 1,457 transactions a year, more
than most product SKUs — and nobody is managing it as one.

---

## 31. ⭐⭐ The dominant pattern across every category: procurement failure, not market gap

Three independent execution lanes reached the same conclusion by different routes, and it
is the most important structural finding in the exercise.

### Baby care — my §18 correction needs its own correction

The babycare lane challenged my conclusion, and it is **partly right**. Verified:

| Diaper SKUs by pack class | SKUs listed | **Ever purchased** | 12m sales |
|---|---|---|---|
| Small pack (2-9 pieces) | 37 | **14** | ₹28,358 |
| **Monthly / bulk pack** (42s, 50s, Baby Dry) | **2** | **0** | **₹0** |
| Other / unspecified | 27 | 6 | ₹5,766 |
| **Total Pampers + Huggies + MamyPoko** | **66** | **20** | **₹34,124** |

And the whole baby probe (diaper, wipes, baby, Cerelac, Lactogen, formula):
**247 SKUs listed across 11 groups, 80 sold, ₹2.07 lakh, ₹41/resident/year.**

**Every single Huggies code has zero purchases and zero sales. Both monthly-pack codes have
never been bought once.** ARY only ever procures 2-9 piece emergency packs.

**Where both readings stand:**
- **My §18 finding holds on volume.** 425 diaper packs a year is genuinely tiny — nobody
  should build a baby aisle expecting a large infant base.
- **The lane is right on cause.** A parent who needs a month of nappies cannot buy them at
  ARY at any price, because the monthly pack has never been ordered. The 425 packs are
  emergency top-ups, not a household's supply.
- **Which effect dominates is not resolvable from this data.** Small campus infant base
  and unstocked bulk packs produce the same 425-pack signal. **The cheap test is to order
  the two existing monthly-pack codes once** and see whether they move — ₹5,000 of stock
  answers a question no amount of analysis can.

### Mobile accessories — a real business hidden in four codes

The lane found ARY already sells **₹2.16 lakh a year of cables, chargers, earphones and
TWS at a verified 41-43% gross margin**, through **four generic catch-all product codes**.
My own probe found ₹99,713 on 14 named SKUs; the lane found more by including the generic
codes. Either way the "₹2,690 Mobile group" figure that started this investigation was
never the business — it was a mis-classification. **An unmanaged, growing, high-margin
category exists and nobody can see it because it has no SKUs.**

### The q-commerce benchmark puts it beyond doubt

> ARY already carries the SKU breadth of an entire Blinkit city network outside India's top
> eight metros — **19,481 active lines against Blinkit's ~20,000 for a whole tier-3 city** —
> on 6.7% of one DMart store's revenue.

### ⭐ What this means for the brief

The user asked for **every product people need that ARY doesn't have.** The honest answer,
now supported by five independent lines of evidence:

**ARY does not have an assortment problem. It has an availability problem.**

- 19,481 active SKUs, matching a whole city's q-commerce network — but **only 6,197 sold**
- 252 SKUs earn half the revenue; 1,108 earn 80%
- Every Huggies code, both monthly diaper packs, all 3 medical devices, all 8 active hand
  tools, 42 of 47 LED/battery SKUs: **listed, never ordered, never sold**
- The two things that did work (Fruits & Veg, Basement) were **narrow ranges kept in stock**,
  not broad ones
- The categories that look "missing" by group tag (mobile, dairy) are mostly **mis-filed
  or unordered**, not absent

**Adding thousands more SKUs to a catalogue where 68% of the existing ones never sell would
make the problem worse, not better.** The work is: order what is already listed, delete what
will never sell, and add *narrow* new ranges one at a time — which is exactly what ARY's own
two successes did.

---

## 32. ⭐⭐⭐ The benchmark table — the definitive answer to "what should ARY carry?"

`ary assort benchmark` — ARY's live range against an external SKU-line benchmark
(BigBasket BB Now metro category counts, pro-rated to a 5,000-person population by the
q-commerce lane; metro counts VERIFIED live, the pro-rata ESTIMATED).

| Category | Benchmark lines | ARY active | ARY **selling** | selling vs benchmark | listed vs benchmark | Verdict |
|---|---|---|---|---|---|---|
| **Baby care** | 323 | **0** | **0** | **0.0%** | 0.00× | **NO ARY GROUP EXISTS** |
| **Bakery, cakes & dairy** | 864 | 225 | **92** | **10.6%** | 0.26× | **severe range gap** |
| Gourmet & world food | 210 | 235 | 45 | 21.4% | 1.12× | severe range gap |
| **Foodgrains, oil & masala** | 1,913 | 1,274 | **451** | **23.6%** | 0.67× | **severe range gap** |
| **Fruits & vegetables** | 271 | 167 | 132 | 48.7% | 0.62× | range gap |
| Beverages | 438 | 934 | 271 | 61.9% | 2.13× | adequate |
| Snacks & branded foods | 1,992 | 4,095 | 1,371 | 68.8% | 2.06× | adequate |
| Kitchen, garden & pets | 308 | 901 | 243 | 78.9% | **2.93×** | over-listed, under-stocked |
| Cleaning & household | 795 | 2,766 | 866 | 108.9% | **3.48×** | over-listed, under-stocked |
| Beauty & hygiene | 886 | 3,747 | 1,236 | 139.5% | **4.23×** | over-listed, under-stocked |
| Eggs, meat & fish | 0 | 0 | 0 | — | — | **structural zero, excluded** (vegetarian institution) |
| **TOTAL** | **8,000** | **14,344** | **4,707** | **58.8%** | **1.79×** | |

### The answer, in one line

**ARY lists 1.79× the benchmark range and sells 0.59× of it.** Both halves of that sentence
are true simultaneously, and they are the whole problem.

### Two different jobs, and confusing them is why this looked like one question

**Job 1 — ADD range, in three categories only.** These are genuinely short of lines, and
the shortfall is not a listing artefact:

- **Baby care: 323 benchmark lines, no ARY product group at all.** The 247 baby SKUs that
  exist are scattered across 11 other groups with 80 selling. Worst relative gap in the
  business.
- **Bakery, cakes & dairy: 92 selling lines against 864.** ARY lists only 225 — it has not
  even *listed* the range, so this is a real buying gap, not an availability one. Dairy's
  sub-benchmark alone is 294 lines against ARY's 41. This is the largest verified depth gap.
- **Foodgrains, oil & masala: 451 selling against 1,913** on 1,274 listed. The core township
  basket, and the single biggest absolute shortfall — 1,462 lines. Masalas & spices alone
  benchmarks 649 lines.
- **Fruits & vegetables: 132 selling against 271** — and this is ARY's *best* counter, at 172
  stock turns a year. The benchmark says it could carry twice the lines and ARY is the only
  fresh source for 5,000 people. Strong candidate: proven demand, proven operation.

**Job 2 — DELETE range, in three categories.** These carry 2.9× to 4.2× the benchmark in
listings while selling a fraction:

- **Beauty & hygiene: 3,747 listed against an 886 benchmark — 4.23×** — with 1,236 selling.
- **Cleaning & household: 2,766 listed against 795 — 3.48×.**
- **Kitchen, garden & pets: 901 against 308 — 2.93×.**

Those three hold **7,414 listed SKUs where the benchmark says 1,989.** That is ~5,400 lines
of catalogue an operator must price, count and shelve for no return — and it is precisely
the shelf and attention that Job 1's missing dairy, staples and baby lines need.

**So the two jobs pay for each other.** Delete ~5,400 dead lines from over-listed
categories, add ~1,500 real lines to dairy, staples and baby care. Net catalogue shrinks,
net revenue grows. That is the opposite of "carry every product", and it is what the data
says.

**One methodological caution:** the benchmark's pro-rata from metro SKU counts is an
ESTIMATE, and category boundaries between BigBasket's tree and ARY's do not map cleanly
(§22 — ARY's tree is unreliable, so `ary_active_skus` here inherits that noise). Treat the
*direction and magnitude* as sound — 4× over-listed in beauty, 10× under-sold in dairy are
too large to be mapping error — and re-derive any single category before acting on its
exact number.

---

## 33. ⚠️⚠️ METHODOLOGY FAILURE CAUGHT — the first coverage diff produced false "missing" verdicts

**Do not use any coverage figure produced before this section was written.**

The first run of `assort/bin/diff.py` reported **81 "must-have" SKU lines ARY has nothing
for**, including these:

| Reported "missing" | What `ary assort probe` actually finds |
|---|---|
| Toor / arhar dal — economy grade | **12 SKUs, 6 selling, ₹71,949** in 12 months |
| Almonds — everyday grade | **151 SKUs** (almond+badam), 48 selling, **₹7,97,032** |
| Cashew — whole grade W240/W320 | present |
| Raw peanuts / moongphali | present |
| Chikki — peanut, til, dry-fruit | present |

**Cause:** the diff matched each researched line by AND-ing the distinctive words in its
description. "Toor / arhar dal — economy grade, sold loose" became
`name LIKE '%toor%' AND '%arhar%' AND '%dal%'` — which matches nothing, because ARY's SKU
is called plainly **"Arhar Daal 1 Kg"**. The AND was added to stop the opposite failure
(a single generic word like `milk` matches 389 SKUs and marked all 52 dairy lines covered),
and it overcorrected.

**Fix applied:** a two-tier verdict. Specific AND-groups are tried first; before any line is
declared missing, single distinctive words are tried as a **broad commodity fallback**. Each
result now carries `matchQuality`:

- **`specific`** — the line's own qualifiers all appear in one product name. Strong.
- **`broad`** — only the commodity word matched. **ARY is in this line, but this exact pack,
  grade or brand is unproven.**
- **`missing`** — nothing matches, specific or broad. This is now a real finding.

**Why this is recorded rather than quietly fixed:** the false list was plausible,
well-formatted, and would have sent a buyer to source arhar dal and almonds that ARY already
sells ₹8.7 lakh of. It is the same trap as JIVO correction **C-0016** (a blank usually means
the value lives elsewhere) and the same trap as §22 (ARY's category tree). **In this database
the default assumption must be that ARY probably has it under a different name** — the burden
of proof is on "missing", not on "covered".

**Standing rule for anyone using this toolkit:** before acting on any `missing` verdict,
re-check it with `ary assort probe <commodity words>`. That command queries the live
catalogue directly and has been right every time the diff was wrong.

---

## 34. ⭐⭐ Mobile accessories: a real ₹1.5 lakh business at 40% margin, hidden in three SKU codes

Verified at SKU level, 12 months:

| Code | Product name | Units | 12m sales | Bills | Avg rate | Cost | Price | **Margin** |
|---|---|---|---|---|---|---|---|---|
| **07P1** | Mobile Adapter | 126 | **₹52,568** | 123 | ₹418 | ₹221.00 | ₹362.33 | **39.1%** |
| **07P0** | Mobile Datacable | 600 | **₹50,927** | 580 | ₹85 | ₹65.08 | ₹115.91 | **44.3%** |
| **0AWR** | Bluetooth Buds | 77 | **₹50,790** | 75 | ₹660 | ₹441.63 | ₹730.41 | **40.2%** |
| 01F4/01F5 | Charger 38 / 41 | 5 | ₹2,690 | 5 | ₹538 | | | |
| 02SD | Mobile Earphone 02 | 8 | ₹1,320 | 8 | ₹165 | | | |
| **Tech total** | | **816** | **₹1,58,295** | **791** | | | | **~40%** |

(Cotton Buds and Tulip Ear Buds, ₹24,208, are toiletries caught by the same name search —
excluded above.)

**What the numbers actually say:**

- **This is a real, repeat business: 791 separate bills a year.** Not a one-off. Students
  and staff are buying cables and adapters roughly **twice a week**, every week.
- **The margin is 39-44%**, verified from `ProductChildMaster` cost and price — well above
  ARY's 31% retail average and 5× the institutional channel's 7.2%.
- **It runs on THREE generic product codes.** "Mobile Datacable" sold 600 units at an
  average ₹85 — meaning every cable type, length and connector in the store is booked to one
  SKU. Nobody can tell whether the demand is USB-C or Lightning, 1 m or 2 m, or which price
  point sells.
- **The ₹2,690 "Mobile group" figure that opened this investigation was never the business.**
  It is the two "Charger 38/41" SKUs — the only ones filed under the Mobile group tag. The
  real business is ~59× larger and sits under **Accessories**. This is §22's taxonomy problem
  producing a two-orders-of-magnitude error on a live category.

**The cheapest high-return action in this whole exercise:** split those three codes into real
SKUs. It costs nothing, needs no stock, no licence and no supplier — it is data entry — and
it converts an invisible ₹1.58 lakh line into a category that can be bought, priced and grown
deliberately. Until it is done, no one can answer "which cable should we stock more of?"

The research lane costed a full 130-SKU tech bay at ₹3.10 lakh one-off for ~₹59,000/month of
incremental revenue, plus fitted tempered glass and covers (₹25,000 one-off, ~₹28,750/month).
Those are **ESTIMATES from that lane and were not independently verified here.** The
₹1.58 lakh, the 791 bills and the 39-44% margins are VERIFIED.

---

## 35. ⭐⭐ RESOLVED: the ₹2.70 Cr P&L debit is an OPENING BALANCE, not a loss — and ARY trades profitably

§8 flagged this as unresolved and warned nobody should repeat it. It is now settled.

### The ₹2.70 Cr is a migration opening entry

`TransactionChild` where `AccountID = 15` (Profit & Loss A/C) returns **exactly one line**:
a debit of **₹2,70,44,148**, and its voucher is **serial 1638345.0001 dated 2023-04-01** —
the first day of the books. That voucher's other legs are the whole opening balance sheet:
Cash ₹70,881 Dr, Credit Card Receivable ₹17,068 Dr, Cess @12% ₹8,280 Dr, Advance Against
Order ₹2,84,763 Cr, and a long list of creditors — Raja Ram Jai Prakash ₹2,76,950 Cr,
Himachal Wholesale Syndicate ₹3,34,070 Cr, Parhlad Chand Batra ₹2,07,815 Cr, Sunil Trading
₹1,16,222 Cr, Mangla Sales ₹1,41,719 Cr, CM Trading ₹1,12,100 Cr and others.

**It is the balancing figure of a data migration on day one, not three years of trading.**
An accumulated loss would be thousands of postings; this is one.

### ARY's actual trading result, computed from the ledger

`TransactionChild` × `AccountMaster` × `GroupMaster`, all-time (2023-04-01 → 2026-08-27):

| Group | Accounts | Debit | Credit | Net |
|---|---|---|---|---|
| Sales Accounts | 2 | ₹33,09,643 | ₹21,22,93,067 | **−₹20,89,83,423** (income) |
| Indirect Incomes | 5 | ₹1,22,557 | ₹6,08,000 | −₹4,85,443 |
| Direct Incomes | 1 | ₹5,580 | ₹2,69,421 | −₹2,63,841 |
| Purchase Accounts | 2 | ₹16,54,02,193 | ₹44,66,085 | **₹16,09,36,108** |
| Salary Expenses | 6 | ₹15,12,07,15 | ₹31,582 | ₹1,50,89,133 |
| Indirect Expenses | 38 | ₹82,74,869 | ₹63,539 | ₹82,11,331 |
| Direct Expenses | 7 | ₹19,71,016 | 0 | ₹19,71,016 |
| Vehicle Expenses | 5 | ₹2,03,041 | 0 | ₹2,03,041 |

| | |
|---|---|
| Total income | **₹20.97 Cr** |
| Total purchases + expenses | **₹18.64 Cr** |
| **Trading surplus before stock** | **+₹2.33 Cr** |
| Closing stock at cost (`ary stock value`) | +₹1.18 Cr |
| Physical-count variance (§9) | −₹0.91 Cr |
| **Cumulative surplus, 3.4 years** | **≈ +₹2.60 Cr** |
| **Annualised** | **≈ ₹0.76 Cr/yr on ~₹6.6 Cr revenue ≈ 11.6%** |

**ARY is profitable — roughly ₹76 lakh a year at an 11-12% net margin.** For a single-store
captive retailer that is a healthy result, and it is consistent with the measured 31% retail
gross margin (§25) less ~19 points of salary, indirect and direct expense.

**Two honest caveats.** (a) There is no opening-stock figure in the books (the "Opening Stock"
account sits at zero), so the closing-stock addition assumes purchases were expensed as
incurred — the standard reading, but an accountant should confirm it. (b) The physical audit
in progress will move the −₹0.91 Cr variance figure. **Confidence: high that ARY is
profitable and the ₹2.70 Cr is not a loss; medium on the exact ₹0.76 Cr/year.**

It is a coincidence worth noting rather than a finding: the cumulative surplus (₹2.60 Cr)
and the migration opening balance (₹2.70 Cr) are close in size. They are unrelated numbers.

---

## 36. ⭐⭐ Verified true zeros — the honest, probe-checked gap list

Every row below was checked with `ary assort probe` against all 21,466 SKUs (not the
category tree, not the diff), so a zero here means the words appear in **no product name in
the catalogue**. 12-month window, ₹/resident/year on 5,000 residents.

### Women's health — a hard zero, on a campus with 2,000+ women and girls

| Probe | SKUs | Sold | 12m sales |
|---|---|---|---|
| **menstrual cup** (incl. Sirona, Pee Safe) | **0** | 0 | **₹0** |
| **intimate wash** (incl. Everteen, VWash) | **0** | 0 | **₹0** |
| **pregnancy test kit** (incl. Prega News) | **0** | 0 | **₹0** |
| **tampons** | **0** | 0 | **₹0** |
| *(for contrast)* sanitary pads | 81 | 21 | ₹4,16,962 |

ARY does pads well — ₹83/resident/year, roughly ₹200 a year per woman on campus, which is a
plausible real figure. But **the entire rest of women's intimate health does not exist in
the catalogue.** The cohort is ~1,102 university students (487 of them AIRWE rural women),
several hundred senior schoolgirls, and resident staff women. This is the clearest
underserved cohort in the business, and pads prove the demand converts when the product is
on the shelf.

Menstrual cups deserve their own note: 2026 adoption in India is rising fast (the
demand-side research flagged it as a live trend), a cup is a **₹300-500 one-off replacing
years of pads**, and a residential campus with limited disposal infrastructure is close to
the ideal use case. Zero SKUs.

### Elderly and chronic care — also a hard zero

| Probe | SKUs | Sold | 12m sales |
|---|---|---|---|
| **walking stick / crutch / walker** | **0** | 0 | **₹0** |
| **adult diaper / pull-ups** | **0** | 0 | **₹0** |
| reading glasses / spectacles | 4 | **0** | **₹0** |

Against a resident population that includes elderly people, ~690 staff, a 100-bed hospital
with ~120 OPD patients a day, and students who break limbs playing sport. Reading glasses
are *listed* (4 SKUs) and have never sold once — the §31 procurement pattern again.

### Skin care — the one category the hill climate already drives

| Probe | SKUs | Sold | 12m sales | ₹/resident/yr |
|---|---|---|---|---|
| moisturiser / cold cream (Nivea, Vaseline) | 200 | 83 | **₹5,48,581** | ₹109.72 |
| petroleum jelly | 86 | 27 | ₹3,30,420 | ₹66.08 |
| sunscreen / SPF | 48 | 23 | ₹88,414 | ₹17.68 |
| **lip balm** | **6** | 6 | ₹9,655 | ₹1.93 |

Cold cream at ₹110/resident/year is one of ARY's better-performing lines — the January
average low is 2.8 °C and it is dry from October to December, so the demand is structural.

Two gaps stand out against that: **sunscreen at ₹17.68** on a campus at 1,551 m where UV is
materially higher than the plains and students are outdoors daily; and **lip balm at 6 SKUs
/ ₹9,655**, where every one of the 6 sold — a fully sold-through range that is simply too
small. Chapped lips at altitude in a Himachal winter are near-universal.

**Ranked by conviction:** lip balm (100% sell-through, trivially cheap, obvious climate
demand) > menstrual cups and intimate wash (large cohort, zero supply, proven category
adjacency in pads) > sunscreen depth > walking sticks and reading glasses (real but small).

---

## 37. 🔴 ARY SELLS LOOSE MILK BELOW COST — a live, quantified cash loss

This is the most immediately actionable finding in the entire exercise, and it is verified
on both sides of the ledger.

### The numbers

12 months to 21-Aug-2026, from `PurchaseDetail` and `SaleDetail`:

| | Loose Milk | Milk_Z (bulk twin) |
|---|---|---|
| Litres **bought** | 20,311 | 8,127 |
| **Average purchase cost** | **₹54.78/L** | ₹46.02/L |
| Litres **sold** | 16,105 | 8,127 |
| **Sale rate charged** | **₹47.00/L flat** — min ₹47, max ₹47 | ₹47.00 flat |
| Revenue | ₹7,56,944 | ₹3,81,969 |
| Purchase cost | ₹10,39,029 | ₹3,74,037 |
| **Result** | **−₹7.78/L · ≈ −₹1.25 lakh a year** | +₹0.98/L, essentially break-even |

The selling price has **zero variance across every single transaction** — 16,105 litres all
at exactly ₹47.00. It is a hard-coded price that nobody has revisited.

### The cause: the purchase cost rose 22% and the price never moved

Monthly average purchase cost for loose milk:

| Month | ₹/L | Month | ₹/L |
|---|---|---|---|
| 2025-04 | 46.00 | 2025-11 | 54.84 |
| 2025-05 | 45.00 | 2025-12 | 55.00 |
| 2025-06 | 45.00 | 2026-01 | 55.00 |
| 2025-07 | 55.00 | 2026-02 | 55.00 |
| 2025-08 | 51.67 | 2026-03 | 55.00 |
| 2025-09 | 45.00 | 2026-05 | 54.71 |
| 2025-10 | 50.00 | **2026-08** | **55.00** |

Cost went from **₹45 to a settled ₹55** — a 22% rise, held steady since December 2025.
**The retail price has been ₹47.00 throughout.** ARY has been selling milk at ₹8 below cost
for at least nine months.

### Why it was invisible

- `ProductChildMaster` still carries the **old** figures — cost ₹38.83, price ₹52.41 — so
  every margin report built from the price master shows loose milk at a healthy **+35%**.
  The real cost only appears on the purchase documents. **This is exactly why §25's
  category margins carry a medium-confidence caveat.**
- The loss is buried inside "Mini Meals", which is where Loose Milk is filed (§22).
- At ₹1.25 lakh a year it is 0.17% of revenue — invisible in a P&L, and precisely the kind
  of thing only a per-SKU cost-versus-price check finds.

### What to do, and the one judgement call

Mechanically the fix is a price revision to about ₹58-60/L. **But the decision is not purely
commercial**: milk at a subsidised price to a captive population of boarding children, at a
charitable trust's shop, may well be deliberate. Nobody in the data can say.

**So this is reported, not recommended.** Someone at ARY should confirm whether the ₹47 is
policy or neglect. If it is policy, it should be recorded as a subsidy — currently it is
absorbed silently and shows up as a healthy margin in every report. If it is neglect, it has
cost about ₹1.25 lakh and is still running.

**One methodological point worth carrying forward:** `ProductChildMaster` prices can be
badly stale. Any margin figure in this document derived from it (§25 category margins,
§34 tech margins) should be re-checked against `PurchaseDetail` before being acted on. The
purchase ledger is the truth; the price master is a hope.

### The below-cost problem is systematic, not one SKU

Sweeping **every** SKU where the 12-month weighted-average sale rate is below the 12-month
weighted-average purchase cost (units sold > 20):

| Product | Units sold | Purchase cost | Sale rate | Per unit | **12m loss** |
|---|---|---|---|---|---|
| **Am Lower** | 1,512 | ₹197.41 | ₹106.52 | **−₹90.89** | **−₹1,37,432** |
| **Loose Milk** | 16,105 | ₹51.16 | ₹47.00 | −₹4.16 | **−₹66,951** |
| Led Light | 33 | ₹580.50 | ₹105.30 | −₹475.20 | −₹15,682 |
| Red Label Tea 22 g | 75 | ₹206.44 | ₹17.33 | −₹189.10 | −₹14,183 |
| Girlish Woolen Pajami | 46 | ₹414.29 | ₹138.43 | −₹275.86 | −₹12,690 |
| **Dahi_Z** | 3,515 | ₹72.67 | ₹69.82 | −₹2.85 | −₹10,025 |
| **Desi Ghee 1 Ltr** | 200 | ₹458.08 | ₹411.61 | −₹46.47 | −₹9,294 |
| **Rajdhani Daliya 1 Kg** | 4,050 | ₹36.86 | ₹34.87 | −₹1.99 | −₹8,049 |
| Steel Fork | 36 | ₹161.03 | ₹10.00 | −₹151.03 | −₹5,437 |
| **Pumpkin_Z** | 2,600 | ₹13.19 | ₹11.23 | −₹1.96 | −₹5,088 |
| Abro Lower | 394 | ₹279.64 | ₹268.23 | −₹11.41 | −₹4,496 |
| Sauce Pan With Lid | 23 | ₹552.46 | ₹420.00 | −₹132.46 | −₹3,047 |
| **Mausambi_Z** | 974 | ₹65.68 | ₹63.10 | −₹2.58 | −₹2,511 |
| Shubh Diwali Diya | 72 | ₹61.15 | ₹29.17 | −₹31.99 | −₹2,303 |
| + 11 more (Ginger_Z, Paneer_Z, containers, candles, kadai, Jivo Olive Oil…) | | | | | −₹8,600 |

**Total: 27 SKUs, ≈ −₹3.06 lakh a year.** Split by plausibility:

| | SKUs | 12m |
|---|---|---|
| Plausible real below-cost selling | 22 | **−₹2.56 lakh** |
| Sale rate below *half* the cost — likely a pricing or pack error | 5 | −₹0.50 lakh |

**Not a unit-conversion artefact.** `ProductMaster` shows all eight of the worst offenders
at `ConversionFactor 1.000` with matching primary and alternate units (Loose Milk Ltr/Kgs,
the rest Pcs/Pcs). So the extremes — Steel Fork bought at ₹161 and sold at ₹10, Red Label
Tea at ₹206 vs ₹17 — are genuine pricing errors or single-versus-case confusion at the till,
not measurement noise.

**The pattern to notice:** the institutional bulk twins are *all* here — Dahi_Z, Pumpkin_Z,
Mausambi_Z, Ginger_Z, Paneer_Z, Golden Apple_Z, plus Loose Milk and Rajdhani Daliya. Each
loses ₹1-4 per unit on large volume. That is consistent with §25's finding that the
institutional channel runs at 7.2% gross margin: **parts of it are below zero.** Before ARY
chases the ₹4-5 crore mess opportunity (§16), it needs a costed price list — winning more
volume at negative margin makes the business worse.

**Highest-value single action here:** "Am Lower" — 1,512 units at −₹90.89 each,
**−₹1.37 lakh, the largest single leak found anywhere in this exercise.** One SKU, one price
correction.

### ⭐ Why no report at ARY could ever have caught this

`ary assort leak` puts the price master's cost next to the real purchase cost. Every single
leaking SKU shows the same defect:

| Product | Real purchase cost | Sale rate | **Price master says cost is** |
|---|---|---|---|
| Am Lower | ₹197.41 | ₹106.62 | **₹340.00** |
| Loose Milk | ₹51.98 | ₹47.00 | **₹65.00** |
| Red Label Tea 22 g | ₹206.44 | ₹17.33 | **₹454.92** |
| Desi Ghee 1 Ltr | ₹471.18 | ₹414.80 | **₹553.57** |
| Dahi_Z | ₹73.12 | ₹69.98 | **₹90.00** |
| Rajdhani Daliya 1 Kg | ₹37.33 | ₹35.14 | **₹39.00** |
| Pumpkin_Z | ₹13.56 | ₹11.33 | **₹19.00** |
| Shubh Diwali Diya | ₹61.15 | ₹29.17 | **₹600.00** |
| At Fabric Kurta Pajama | ₹144.55 | ₹112.02 | **₹300.00** |

**The master cost is HIGHER than reality on every row.** A margin report built from
`ProductChildMaster` therefore compares the selling price against an inflated cost — and
still shows these as loss-making, or shows a *different* loss than the real one. Either way
the figures are unusable, which is why nobody has acted on them.

**Two conclusions:**
1. **Cost data at ARY is unreliable in both directions.** `StandardCostPrice` is populated
   on 41 of 19,481 SKUs; `ProductChildMaster` is populated but wrong. **The purchase ledger
   is the only trustworthy cost source**, which is what `ary assort leak` uses.
2. **Any margin figure in this document derived from the price master carries this risk** —
   §25's category margins and §34's tech margins included. Re-derive from `PurchaseDetail`
   before acting on a single category.

`ary assort leak` is now a standing command, so this check can be run any week rather than
rediscovered. On the tighter default (min 20 units, weighted properly) it reports **21 SKUs
and −₹2.75 lakh** — the earlier −₹3.06 lakh figure used a slightly looser cost average.
Either way the ranking is the same and **"Am Lower" at −₹1.35 lakh is the single biggest
leak in the business.**

---

## 38. Basket and footfall — what the campus day actually looks like

### Hourly footfall (Apr → 21 Aug 2026), and it is not a shop's normal day

| Hour | Bills | Avg bill | | Hour | Bills | Avg bill |
|---|---|---|---|---|---|---|
| 08 | 89 | ₹147 | | 16 | 10,930 | ₹177 |
| **09** | **15,590** | ₹197 | | **17** | **22,268** | ₹211 |
| 10 | 8,099 | ₹205 | | **18** | **20,670** | ₹255 |
| 11 | 8,435 | **₹369** | | **19** | **26,269** | ₹147 |
| 12 | 7,574 | ₹236 | | **20** | **22,641** | ₹191 |
| **13** | 10,643 | ₹196 | | 21 | 6,872 | ₹240 |
| 14 | 3,865 | ₹179 | | 22 | 1,741 | ₹143 |
| 15 | 2,979 | **₹315** | | 23 | 216 | ₹199 |

**The day has two sharp peaks and a dead middle.** 09:00 (15,590 bills — before class),
then a collapse to 2,979 at 15:00, then a much larger evening surge **17:00-20:00 carrying
91,848 bills — 55% of the day's traffic in four hours.**

Two things follow:
- **Staffing must match the shape, not the clock.** Four evening hours carry more than the
  whole morning and afternoon combined.
- **Basket size inverts against traffic.** The 11:00 and 15:00 troughs carry the *highest*
  average bills (₹369 and ₹315) — that is staff and family shopping, not students. The
  19:00 peak has the *lowest* (₹147) — high-frequency student snacking. Two different
  customers, two different ranges, and the range should be laid out for whoever is in the
  store at that hour.

### What residents buy together (Jun → 21 Aug 2026, same-bill pairs)

| Pair | Together | Read |
|---|---|---|
| **Lmk Pts + Foodcoast Tomato Ketchup 8 g** | **1,303** | canteen pizza slice + sachet |
| **Tomato + Onion** | **977** | the fresh staple pair |
| Onion + Potato | 772 | |
| Tomato + Potato | 474 | |
| Tomato + Cucumber | 382 | |
| Tomato + Banana Kg | 372 | |
| Ketchup 8 g + Over Loaded Pizza | 341 | |
| Tomato + Lemon | 341 | |
| **Spring Rolls + Steam Momos** | **327** | the canteen combo |
| Ketchup 8 g + Pizza 99/- | 315 | |
| **Wai Wai Noodle + Yippee Noodles** | **303** | students buy two brands at once |
| Lays Kurkure + Lays Magic Masala | 301 | same — two flavours per trip |
| Noodles Half + Spring Rolls | 275 | |
| Noodles Half + Steam Momos | 260 | |

**Three actionable readings:**

1. **The fresh basket is a fixed set** — tomato, onion, potato, cucumber, lemon, ginger,
   banana appear in every top pair. Those seven lines have to be in stock *together*; one
   out-of-stock breaks a basket rather than losing a single line. It also explains Fruits &
   Veg turning stock 172 times a year.
2. **Students buy two brands of the same thing in one trip** (Wai Wai *and* Yippee, Kurkure
   *and* Magic Masala). That is variety-seeking, not brand loyalty — so in student
   categories, breadth of flavour beats depth of any one brand, and it argues against the
   instinct to rationalise to one supplier.
3. **The canteen and the shop are one basket.** Pizza plus a ketchup sachet is the single
   most common pair in the business (1,303), and momos-plus-spring-rolls is close behind.
   The canteen menu and the grocery shelf should be planned together, not as separate
   counters — which is also where G Canteen's −₹40.19 lakh recipe-posting problem (§9) does
   real damage, because that unbilled consumption is the same basket.

### The fresh basket's availability is already good — with one exception

Days each core fresh line actually sold, out of **142 trading days** (1 Apr → 21 Aug 2026):

| Line | Days sold | Availability | Qty | 12m-window sales |
|---|---|---|---|---|
| Onion | 140 | **98.6%** | 4,598 | ₹1,27,479 |
| Potato | 140 | **98.6%** | 4,933 | ₹58,112 |
| Tomato | 138 | **97.2%** | 3,186 | ₹94,604 |
| Banana Kg | 134 | 94.4% | 3,908 | ₹1,84,063 |
| Ginger | 130 | 91.5% | 239 | ₹38,456 |
| Lemon | 129 | 90.8% | 11,164 | ₹58,703 |
| **Cucumber** | **81** | **57.0%** | 1,484 | ₹42,638 |

**This is a genuinely good result and worth saying so** — 91-99% availability on six of seven
fresh lines, on a hill site 30-50 km from a mandi, is competent operational work. It is the
counterpoint to §31: where ARY *does* manage a range actively, it manages it well. Fruits &
Veg turning 172 times a year is not luck.

**Cucumber is the exception at 57%** — absent on 61 of 142 days, while appearing in 382 of the
top same-bill pairs. Given the basket logic above, a missing cucumber does not cost one line;
it breaks a fresh basket that was otherwise complete. It may be pure seasonality (cucumber is
a summer line and the window spans April to August, so a genuine season is plausible) — worth
one check with the buyer rather than an assumption either way.

---

## 39. ⚠️⭐ MAJOR QUALIFICATION to §16 — the campus runs its OWN food units, and ARY buys FROM them

This is the most important caveat in the document, and it changes how the institutional
opportunity should be pitched.

The ledger holds these accounts, and their group placement is the finding:

| Account | Ledger group | Side |
|---|---|---|
| **Akal Dairy - Baru Sahib** | Local **Creditors** - Baru Sahib | ARY owes them |
| **Akal Modi Khana - Baru Sahib** | Local **Creditors** - Baru Sahib | ARY owes them |
| **Akal Bakery - Baru Sahib** | Local **Creditors** - Baru Sahib | ARY owes them |
| **Akal Catering Mess** | Local **Creditors** - Baru Sahib | ARY owes them |
| Akal Academy · Akal Hospital · Eternal University · Akal Nursing College · Akal De-Adiction Ward · Akal Mahila Mandal | Local **Debtors** - Baru Sahib | they owe ARY |

("Modi Khana" is the gurdwara/institutional provision store — the langar stores.)

### What ARY buys from them, and when it started

| Unit | Vouchers | ARY purchases (credit) | First txn | Last txn |
|---|---|---|---|---|
| **Akal Modi Khana** | 7 | **₹2,42,640** | 2026-06-08 | 2026-08-14 |
| **Akal Dairy** | 73 | ₹77,726 | 2026-06-03 | 2026-08-17 |
| **Akal Bakery** | 115 | ₹54,706 | 2026-06-03 | 2026-08-21 |
| **Akal Catering Mess** | 56 | ₹31,641 | 2026-06-03 | 2026-08-21 |
| **Total** | 251 | **₹4,06,713** | — | current |

**All four relationships began in June 2026 — under three months ago — and all four are
live to the last day of data.** In one quarter ARY has bought ₹4.07 lakh from the campus's
own dairy, bakery, langar stores and catering mess.

### Why this matters, in both directions

**Against the §16 thesis:** the campus is not an unserved buyer waiting for a supplier. It
already operates its own dairy, bakery, provision store and catering mess. Eternal
University's ₹2.51 Cr of mess spend is very likely flowing largely to **those in-house
units**, not leaking to an outside market ARY could win. **"₹4-5 crore of unserved
institutional wallet" is too strong a claim** and should not be presented as a clean
addressable gap.

**For it, and this is the more interesting reading:** ARY has just spent one quarter
becoming a *customer* of those units. That is a working commercial relationship, opened
recently, on 251 vouchers. The realistic prize is therefore **not "displace the mess"** —
it is:

1. **Two-way trade.** ARY buys their dairy and bread for retail; they buy ARY's staples,
   spices, oil and vegetables for the mess. ARY already runs the purchasing muscle (§27:
   ₹6.36 Cr of purchases, ten HP suppliers, a daily milk route) that four small in-house
   units cannot each replicate.
2. **Consolidated procurement for the campus.** The gap is not that the mess buys nothing —
   it is that Akal Academy places **2,055 petty bills at ₹1,299** and the Trust **1,045 at
   ₹969** (§15). Those are thousands of small purchases that a single supply contract could
   absorb at better prices for the Trust and better margin for ARY.

**Revised, defensible version of §16:** the institutional opportunity is real but it is a
**procurement-consolidation and two-way-trade opportunity**, not a virgin market. The
₹2.51 Cr figure is a VERIFIED measure of *what the campus spends on food*, not of what ARY
can capture. **Anyone quoting ₹4-5 crore should stop and read this section first.**

**What would settle it:** ask the Trust what Akal Dairy, Akal Bakery and Akal Modi Khana
actually supply and at what scale, and whether Eternal University's ₹1.96 Cr of mess meal
charges is paid to those units or to outside vendors. One conversation; it is the single
highest-value unanswered question in this exercise.

---

## 40. ⭐⭐ Dastar and Patka — ARY's genuinely distinctive category, ₹9.94 lakh a year

The single largest category nobody in a generic retail benchmark would ever look for, and it
is specific to what ARY is:

| Product | Qty | 12m sales | Bills | Rate |
|---|---|---|---|---|
| **Dastar Fabric White** | 6,010.7 m | **₹3,90,698** | **813** | ₹65.00/m |
| **Dastar Fabric Navy Blue** | 4,962.8 m | **₹3,22,580** | **811** | ₹65.00/m |
| Patka Big Blue | 1,189 | ₹77,285 | 535 | ₹65.00 |
| Patka Big White | 1,118 | ₹72,670 | 554 | ₹65.00 |
| Js Dastar Keshri | 1,036 | ₹67,340 | 28 | ₹65.00 |
| Patka Small Blue | 445 | ₹22,250 | 220 | ₹50.00 |
| Patka Small White | 424 | ₹21,200 | 207 | ₹50.00 |
| Patka Big New | 252 | ₹16,380 | 137 | ₹65.00 |
| + 6 more (Stc, Pink, Js White, 3.5 m Keshri, 2.5 m Kesari) | | ₹32,469 | | |
| **Total** | | **₹9,93,521** | **~3,400** | **₹198.70/resident/yr** |

**₹198.70 per resident per year — larger than dairy (₹186), larger than every medicine
combined (₹63), and on ~3,400 separate transactions.** Nearly 11 km of turban fabric a year.

**Why this is worth its own section:**

1. **It is a captive, non-discretionary, repeat category with an unmistakable demand base.**
   Every Sikh boy and man on campus needs dastar or patka fabric, replaced regularly, and
   there is no alternative supplier within 30-50 km. It cannot be disrupted by Blinkit,
   Amazon or a trip to town.
2. **No generic benchmark contains it.** BigBasket has no dastar line; the q-commerce
   benchmark (§32) has no category it maps to. A pure "what do modern retailers carry"
   exercise would have missed ARY's fourth-largest per-resident category entirely — which is
   the strongest argument in this document for reading the *institution*, not just the retail
   playbook.
3. **The depth is thin against the volume.** Two colours (white, navy) carry ₹7.13 lakh of
   the ₹9.94 lakh. Keshri exists but sells 28 bills. There is no premium tier — everything
   is ₹65/m, and the only higher-priced lines (₹150-210) sold 3 units between them. F-74
   voile, malmal, full-voile and starch-and-dye services are the obvious adjacencies, none
   of which ARY stocks. Gurmat articles as a group sit at just ₹6.91/resident/year (§23).

**Corollary for the whole exercise:** the demand-side research was told to look at Indian
modern trade and q-commerce, so it produced 1,619 SKU lines of national assortment — good
work, and it found real gaps. But the biggest *proven* per-resident categories at ARY are
**uniform fabric, dastar, academy dress and confectionery** — three of which are artefacts
of this being a Sikh residential school, not a town. **The institution-specific range is
where ARY's defensible business already is**, and it deserves the same depth analysis the
national categories got.

### Correction to my own probe method

My multi-word probe `"washing bar" "washing soap"` returned zero and I nearly recorded
laundry bars as a gap. Probing the single words `washing bar soap` returns **528 SKUs,
168 selling, ₹10,69,323 — ₹213.86 per resident per year.** A quoted multi-word phrase is an
exact substring match and fails on any word-order or spelling difference.

**Rule for using `ary assort probe`: pass single words, not phrases.** The tool ORs them, and
ARY's product names are too irregular for phrase matching. This is the third time in this
exercise that a name-matching assumption produced a false gap (see §22, §33) — in this
database the burden of proof always sits on "missing".

---

## 41. ⭐ The Five Ks and Academy Dress — the institution-specific range, mapped

### Academy Dress subgroup depth (groups 161 + 163), 12 months

| Subgroup | SKUs | Sold | 12m sales |
|---|---|---|---|
| **White Suit** | 64 | 33 | **₹22,35,015** |
| **Blue Suit** | 73 | 28 | **₹15,68,203** |
| EU Uniforms | 22 | 14 | ₹4,84,300 |
| **Kachhera** | 20 | **3** | ₹3,33,860 |
| Patka White | 6 | 4 | ₹1,16,300 |
| Patka Blue | 5 | 2 | ₹99,535 |
| Maroon Suits | 12 | 12 | ₹75,100 |
| Dastar Keshri | 1 | 1 | ₹67,340 |
| **Kirpan** | 3 | 3 | ₹31,387 |
| **Kara** | 1 | 1 | ₹7,560 |
| **Kangha** | 2 | 2 | ₹4,940 |
| Dastar White | 5 | **1** | ₹813 |
| Dastar Blue | 12 | **2** | ₹570 |
| **Total** | **226** | **106** | **₹50,24,923** |

Uniform and dress is a **₹50.25 lakh a year** business — ARY's largest non-grocery category
after the core store's food, and its second counter (Ary Clothing) exists for it.

### The Five Ks, at SKU level

| Article | Product | Units | 12m sales | Rate | Bills |
|---|---|---|---|---|---|
| **Kachhera** | Medium 30×13 | **1,607** | **₹2,08,910** | ₹130 | 644 |
| | Large 35×15 | 541 | ₹86,560 | ₹160 | 234 |
| | Small 26×11 | 349 | ₹38,390 | ₹110 | 126 |
| | Than Kachhera Ved (fabric) | 45 | ₹2,893 | ₹65 | 7 |
| **Kirpan** | Angel Kirpan | 116 | ₹23,200 | ₹200 | 88 |
| | Kirpan 7 Taksali | 13 | ₹5,187 | ₹399 | **1** |
| | Kirpan 5 Taksali | 12 | ₹3,000 | ₹250 | **1** |
| **Kara** | Kara | 378 | ₹7,560 | ₹26.91 | 106 |
| | Kara Simran | 86 | ₹4,090 | ₹47.73 | 71 |
| **Kangha** | Kangha | 307 | ₹4,740 | ₹15.50 | 199 |
| **Gatra** | Adjustable 1" / 1.5" | 178 | ₹7,860 | ₹40-50 | 133 |
| **Total** | | **3,632** | **₹3,92,390** | | **~1,610** |

**What the numbers show:**

1. **Kachhera is the volume driver — 2,497 garments a year on 1,004 bills** at ₹110-160.
   Three sizes carry it, and only **3 of the 20 Kachhera SKUs sold at all**: the range is
   already effectively narrow, and it works.
2. **Kirpan has a real premium tier that is not being sold.** Angel Kirpan (₹200) does
   116 units on 88 bills. The Taksali kirpans at ₹250 and ₹399 sold **on one bill each** —
   25 units to one buyer, twice. That is not retail demand, it is an institutional order.
   A displayed premium range at a Sikh institution is an obvious untested opportunity.
3. **Kara and Kangha are priced as commodities and sell as commodities** — ₹26.91 and ₹15.50,
   378 and 307 units. There is no sarbloh, no engraved, no gift-boxed tier. On a campus where
   these are worn daily and given as gifts at Amrit ceremonies and Gurpurabs, one SKU each is
   thin.
4. **Dastar White (5 SKUs, 1 sold, ₹813) and Dastar Blue (12 SKUs, 2 sold, ₹570) look dead
   here** — but §40 shows "Dastar Fabric White" doing ₹3.90 lakh under a *different* group.
   Same §22 taxonomy problem: the Academy Dress subgroups hold near-empty duplicates of lines
   that sell elsewhere.

**The pattern across §40 and §41:** ARY's institution-specific range is its most defensible
business — captive, repeat, non-discretionary, undisruptable by any e-commerce competitor —
and it is being run at **exactly one price point per article** with no premium tier and no
gifting range. That is the opposite of the national-brand categories, where ARY carries 4×
the benchmark listings (§32).

---

## 42. The coverage corpus, read honestly

`ary assort research`, after the §33 fix split solid line-level matches from broad commodity
matches. 12 categories diffed so far, worst line-coverage first:

| Category | Lines | **Line match** | Commodity only | Dormant | **Missing** | Line coverage |
|---|---|---|---|---|---|---|
| **medical-devices** | 58 | **6** | 43 | 7 | 2 | **11.5%** |
| **oralcare** | 54 | 14 | 37 | 2 | 1 | **21.4%** |
| **frozen** | 51 | 11 | 39 | 1 | 0 | **27.0%** |
| dryfruits | 57 | 18 | 38 | 1 | 0 | 33.3% |
| **dairy** | 52 | 19 | 32 | 1 | 0 | 34.9% |
| beverages-hot | 54 | 21 | 32 | 1 | 0 | 36.6% |
| bakery | 52 | 21 | 31 | 0 | 0 | 44.2% |
| femcare | 48 | 20 | 22 | 6 | 0 | 46.9% |
| oils | 46 | 24 | 22 | 0 | 0 | 51.5% |
| beverages-cold | 48 | 25 | 21 | 2 | 0 | 54.3% |
| fruits | 52 | 28 | 20 | 3 | 1 | 60.6% |
| confectionery | 46 | 29 | 17 | 0 | 0 | 65.8% |

**How to read this.** "Missing" is now almost always **zero** — because ARY genuinely has
something under nearly every commodity heading. The signal has moved into the middle column:
**"commodity only" means ARY sells *something* in that line but not the pack, grade or brand
the research says it should carry.** Medical devices at 6 line-matches out of 58, and frozen
at 11 of 51, are the real depth gaps — consistent with §23 (medical devices: 3 SKUs, zero
sales) and §32 (bakery/dairy 92 selling lines against a benchmark of 864).

**Genuinely missing, with no match at all** — the four the corpus can defend:

| Category | Line | Essentiality |
|---|---|---|
| **oralcare** | **Denture cleansing tablets / soak powder** | **must-have** |
| fruits | Chikoo / Sapota | should-have |
| medical-devices | Instant single-use cold pack | should-have |
| medical-devices | Compression / varicose vein stockings | nice-to-have |

Denture care is the notable one: a must-have line with no match anywhere in 21,466 SKUs, on
a campus with resident elderly staff and a 100-bed hospital. Cold packs and compression
stockings fit the same cohort, and the sports injuries of 2,600 students.

**The tool now shows its own uncertainty**, which is the point. `ary assort gaps --state
commodity` lists every weak match with the term that produced it, so a buyer can see that
"Period-pain OTC tablet" matched only on the word `tablet`, and that "Pregnancy test kit"
matched only on `basic` — neither of which proves anything. Those are exactly the lines
§36 confirmed as true zeros by direct probe.

---

## 43. ⭐ Pricing fairness: ARY does NOT exploit its captive market

The single most serious reputational risk in this whole exercise is that a charitable
trust's shop, the only one for 5,000 people who cannot shop elsewhere, might be
over-charging them. It was tested directly.

### On packaged branded goods — where MRP is legally binding — there is essentially nothing

Every SKU whose 12-month weighted-average sale rate exceeds the MRP recorded on its own sale
lines, restricted to **branded packaged goods** (excluding canteen dishes, own-brand "Ary"
items and the loose `_L`/`_Z` bulk lines, none of which carry a legal MRP):

| Product | Brand | Units | MRP | Sale rate | % over | 12m overcharge |
|---|---|---|---|---|---|---|
| Curtain Ring | Tulsi | 400 | ₹1.50 | ₹2.00 | 33.3% | **₹200** |
| Masoor Malka 1 Kg | Raja | 240 | ₹76.50 | ₹76.88 | 0.5% | **₹90** |
| Button | Mahajan | 100 | ₹0.90 | ₹1.00 | 11.1% | **₹10** |
| **Total** | | | | | | **₹300** |

**Three SKUs, ₹300 a year, on a ₹7.55 crore business.** Curtain rings and buttons rounded to
the nearest rupee. That is rounding, not exploitation. **On the metric that carries actual
Legal Metrology exposure, ARY is clean.**

### The apparent breaches are all canteen food and loose goods, where MRP does not apply

The unfiltered query returns 20 lines, and the top ones are:

| Product | Units | "MRP" | Sale rate | What it actually is |
|---|---|---|---|---|
| Softy Ice Cream | 6,647 | ₹20.00 | ₹29.13 | **canteen-made** — no MRP exists |
| Grilled Sandwich Gc | 1,849 | ₹60.00 | ₹66.71 | canteen dish |
| Masala Fries Gc | 2,298 | ₹40.00 | ₹43.69 | canteen dish |
| Sugar Cane Juice | 1,685 | ₹15.00 | ₹19.13 | canteen |
| Special Thali 99/- | 519 | ₹99.00 | ₹109.45 | canteen meal |
| Soyabean Fortune_L, Sugar_L, Tea_L, Besan, Rajma, Mung | | | | **loose/bulk** — sold by weight |

A prepared dish has no MRP, and a loose commodity sold by weight has none either. The "MRP"
field on those lines is a stale menu or reference price. **This is a data-hygiene point, not
a pricing one** — though it does mean the MRP field cannot be used for margin work
(consistent with §37's finding that the price master is unreliable).

### Read together with the margin evidence, the fairness picture is clear

| Evidence | Finding |
|---|---|
| Above-MRP on packaged goods | **₹300/year on 3 rounding-level SKUs** |
| Institutional / mess margin (§25) | **7.2%** — barely above cost |
| 27 SKUs (§37) | sold **below** purchase cost, −₹2.75 lakh/yr |
| Loose milk | **₹47.00/L against a ₹55 cost** for nine months |
| Retail margin (§25) | 31.0% — normal Indian retail, not captive-market pricing |

**ARY is if anything under-pricing.** It loses money on milk, sells the campus's feeding
programme goods at 7.2%, and its retail margin is ordinary. If the fairness question is ever
raised — by the Trust, by residents, or by anyone examining a charitable institution running
a monopoly shop — **these are the numbers that answer it**, and they answer it well.

The corollary matters for §37's judgement call: since ARY is not profiteering anywhere else,
the ₹47 milk price is much more likely to be **deliberate subsidy** than neglect. It should
still be recorded as a subsidy rather than absorbed silently as a phantom +35% margin.

---

## 44. ⚠️ Payment-mode data: the COUNTS are usable, every AMOUNT column is not

The digital lane claimed "UPI is 56.3% of tenders and 42.9% of collections value". The first
half is right; the second cannot be supported by this database, and it is worth pinning down
because a payments strategy would be built on it.

### What is trustworthy: tender counts

`SalePayment` × `SaleHeader`, 12 months:

| MOPID | Mode | **Tenders** | **% of tenders** |
|---|---|---|---|
| **503** | UPI (booked as "Paytm") | **222,237** | **55.7%** |
| 1 | Cash | 166,072 | 41.6% |
| 2 | Credit Sale | 11,019 | 2.8% |

**VERIFIED and important: UPI is now the majority payment method at ARY by transaction
count** — 55.7% against cash's 41.6%. On a rural Himachal campus that is a genuinely
notable fact, and it is the strongest single argument for the digital-layer work: residents
have already changed behaviour without ARY building anything.

### What is broken: all three amount columns

| Column | 12-month total | Should be |
|---|---|---|
| `SUM(Amount)` | **₹900.35 crore** | ₹7.55 crore |
| `SUM(TenderAmount)` | **₹894.43 crore** | ₹7.55 crore |
| `SUM(TenderAmount − ReturnAmount)` | ₹2.26 crore | ₹7.55 crore |

The first two are **~119× actual sales.** The third is 30% of it. And the per-mode split is
nonsense in both directions: by `Amount`, cash is 99.3% of value while UPI is 0.4%; by
net tender, cash is 100.0% and UPI and credit are both exactly ₹0.

**Diagnosis:** MOPID 1 (Cash) carries a scaling or units defect — ₹8,944 crore of
"TenderAmount" on 166,072 tenders is ₹53,858 per cash transaction on a shop with a ₹207
average bill. And UPI/credit tenders record their value in `Amount` only, leaving
`TenderAmount` and `ReturnAmount` at zero, so any net-tender calculation attributes 100% to
cash by construction.

**This supersedes §10's note** that `ary sales payment-mix` amounts are unusable — now the
mechanism is known:

> **Payment-mode COUNTS are reliable. Payment-mode VALUES are not, in any column.**
> Quote "55.7% of transactions are UPI". Never quote a rupee split by payment mode.

The 42.9%-of-value figure the lane reported is therefore **unverifiable, not wrong** — there
is no column in this database that can produce a trustworthy value split. Anyone sizing a
payments or wallet project must get that from the acquirer's settlement reports (Paytm's own
statements), not from FusionERP8.

### The rest of the digital lane's findings stand, and two are strong

| Claim | Status |
|---|---|
| 96.2% of FY26-27 bills (162,434 of 168,881) booked to one anonymous account | **VERIFIED** — matches my own §18 count of 14.41% institutional / 71.1% walk-in |
| A campus wallet spendable only at ARY is a **closed-system PPI** — no RBI authorisation, no escrow | **VERIFIED**, and it removes the regulatory objection to the wallet idea entirely |
| **FusionERP8 already ships a configured, never-used wallet data model** | **VERIFIED** — consistent with `CustomerMaster` carrying unused `loyalty_points`, `visits` and `crm_limit` fields |
| WhatsApp order-to-pickup needs no app build; a customer-initiated conversation opens a free 24-hour window | VERIFIED against Meta's published pricing |
| Identified-customer basket ₹1,586 vs walk-in ₹155 | **VERIFIED but correctly flagged by the lane as NOT causal** — the identified accounts are institutions and credit households, so the 10× is a selection effect, not a benefit of identification. Good discipline from that lane. |

---

## 45. ⭐ The student credit book is small, current, and well-run

The "Akal Academy Cs" group holds 3,604 individual student and staff accounts — the only
identified customers ARY has. Ageing them by last transaction date (`TransactionChild` ×
`TransactionMaster`, one row per account):

| Age of last transaction | Accounts | Net balance | Owed to ARY |
|---|---|---|---|
| **Active (last 90 days)** | **640** | ₹16,52,476 | ₹16,72,607 |
| 90-365 days | 369 | ₹4,33,982 | ₹4,92,350 |
| 1-2 years | 306 | ₹1,41,287 | ₹1,58,466 |
| **Over 2 years** | **1,774** | **−₹5,990** | ₹26,500 |
| **Total** | **3,089 with activity** | **₹22,21,755** | **₹23,49,923** |

Credit sales themselves, 12 months: **1,057 customers, 11,019 tenders, ₹2.09 crore**
(2.8% of tenders).

**This is a genuinely well-managed book, and it is worth saying so plainly:**

- **75% of the outstanding is under 90 days old** — ₹16.5 lakh of ₹22.2 lakh.
- **1,774 accounts dormant over two years carry a NET CREDIT of −₹5,990** — meaning students
  who left are, in aggregate, in credit rather than owing. Only ₹26,500 of debit sits
  anywhere in that tail. For a student credit book at a boarding school with constant
  turnover, that is close to ideal.
- **Total exposure is ₹22.2 lakh on ₹7.55 crore of sales — 2.9%**, entirely to a captive,
  Trust-employed or Trust-enrolled population.

**Why it matters for the identity work (§29, §44):** the objection to a campus wallet is
usually credit risk and collection. ARY has been running exactly that model for three years
on 3,089 accounts with a clean ageing profile and near-zero bad debt in the dormant tail.
**The credit infrastructure, the collection discipline and the household relationships
already exist** — a wallet would formalise something that already works, not introduce a new
risk. Combined with the closed-system PPI finding (no RBI authorisation needed) and the
unused wallet model already in FusionERP8, the barriers to that project are lower than
anyone would assume.

**One caveat:** 3,089 accounts have ledger activity out of 3,604 in the group, and only
1,315 have transacted in the last year. The book is small relative to the ~5,000 population
— roughly a quarter of residents have an account — which is consistent with 96% of bills
being anonymous walk-ins. The model works; it just has not been extended.

---

## 46. ⚠️⚠️ The research fleet's own numbers do not add up — and that is the point of this section

Aggregating every recommendation from all 10 completed intelligence and execution lanes:

| | |
|---|---|
| Recommendations produced | **101** |
| Sum of claimed monthly impact | **₹1.11 crore/month** |
| **Annualised** | **₹13.33 crore/year** |
| ARY's actual annual revenue | **₹7.55 crore** |

**The lanes collectively recommend adding 177% of ARY's entire current revenue.** That is not
credible, and no one should present these figures in aggregate.

### Why it happens, and it is not the agents being careless

Each lane sized *its own* opportunity honestly and in isolation, exactly as instructed. But:

1. **They double-count the same prize.** The `wallet` lane claims **₹35 lakh/month** for the
   mess-procurement contract; the `population` lane claims **₹4.18 lakh/month** for the same
   Eternal University contract; `dairy-fresh-build` claims ₹75,000/month for a dairy supply
   line that would largely serve it. Three lanes, one contract.
2. **The largest single figure is the least verified.** ₹35 lakh/month = ₹4.2 crore/year is
   the wallet lane's institutional headroom — and **§39 shows the campus already runs its own
   dairy, bakery, langar store and catering mess, which ARY buys *from*.** That number is
   the one most likely to be wrong.
3. **Revenue is not profit.** At the institutional channel's measured 7.2% margin (§25),
   ₹4.2 crore of mess revenue is ₹30 lakh of gross profit — not ₹4.2 crore of value.
4. **Several lanes size the same shelf twice** — the qcommerce lane's ₹1.07 lakh/month for
   cutting the dead tail and the retail-range lanes' additions compete for the same space.

### What this document does instead

Every figure in this file is either **VERIFIED against the live database with its query
recorded**, or **explicitly labelled ESTIMATED with its assumption stated**. The verified
findings are deliberately smaller and duller than the fleet's headline numbers:

| Verified, actionable, with a query behind it | Annual value |
|---|---|
| Stop selling 27 SKUs below purchase cost (§37) | **+₹2.75 lakh** (cash, immediate) |
| "Am Lower" price correction alone | **+₹1.35 lakh** |
| Reinstate Talwandi Sabo's prior run-rate at 31% margin (§26) | **+₹17-18 lakh gross profit** |
| Split the 3 tech catch-all codes and manage the category (§34) | ₹1.58 lakh base at 40% margin |
| Institutional / mess opportunity (§16, §39) | **₹29-36 lakh gross profit IF winnable** — and §39 says test that first |
| Retail range headroom (§25) | ₹71 lakh gross profit, needs capital and licences |

**The honest summary:** ARY has roughly **₹20 lakh of gross profit available from fixing
things that are already broken**, and a larger but genuinely uncertain prize in
institutional supply and retail depth. It does not have ₹13 crore of upside.

**Why this section exists:** the user asked for maximum-depth multi-agent research and got
it — 1,619 researched SKU lines across 36 categories and 101 recommendations, which surfaced
real findings this analysis would not have reached alone (the pharmacy licensing path, the
IMS Act, HP supplier names, the closed-system PPI point, the below-cost dairy line).
**But a fleet of independent agents each sizing an opportunity in isolation produces a total
that is worse than useless.** The value is in the individual verified findings, not the sum.
