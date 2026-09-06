# Demand baseline — where "expected GT/MT orders" come from (Mark 4, 2026-09-06)

**Ruling (R17, R18, meeting 10:19-11:02; Daman 2026-09-06):** never plan from POs alone. GT/MT
bunches its orders in the last weeks of the month (wholesalers stock up to distribute from the
1st), so a PO-only plan is empty at month-end and the buffer runs out. Production planning
predicts the month's POs from **past GT/MT sales, excluding e-commerce**, and is ready for them.

**Source:** SAP billing, Oil book, read through `hana-sql` (read-only) — **the one allowed SAP use
in the live planner**; everything about the factory still comes from ji.jivo.in (RULE 0).
Script: `live/demand_baseline_sap.py` → `live/state/demand_baseline.json`. Run it **daily on the
VPS** (it reaches HANA directly via `connections/hana-vps-direct.env`); never in the 3-minute loop.
The freeze only reads the file; if the file is missing it falls back to the plan sheet's forecast
and says so in honesty.

## The channel field, verified live 2026-09-06 (HANA, JIVO_OIL_HANADB, June-August 2026, FG items)

`OCRD.U_Main_Group` is the customer's channel and every sale line inherits it (Control Panel
decoder, `control-panel/vault/SALES-LENS-DECODER.md`). Customer *groups* (OCRG) are geography, not channel.

| U_Main_Group | Customers | Jun-Aug net ₹ Cr (all items) | Included? |
|---|---:|---:|---|
| E-COMMERCE | 3 | 73.99 | **no** — ₹73.78 Cr of it is CUSTA000606 JIVO MART PVT LTD, the inter-company transfer; e-com stays on ecom.jivo.in POs |
| GT | 71 | 30.26 | yes |
| MT | 10 | 12.59 | yes |
| ROI (Rest of India) | 24 | 12.56 | yes (A17) |
| CORPORATE | 7 | 2.53 | yes (A17) |
| HORECA | 12 | 2.34 | yes (A17) |
| CSD | 2 | 1.72 | yes (A17) |
| BRANCH | 4 | 1.10 | no — JIVO WELLNESS branch cards, inter-company |
| REFERENCE | 2 | 0.99 | yes (A17; 12 L of FG in the window) |
| STAFF / CASH SALE | 23 | 0.08 | no |

Inter-company cards excluded (C-0005, Oil): CUSTA000001/2/3/4/606/827/906/1099/1113.

## Definitions
- ₹ = `INV1.LineTotal` (net of GST), never the header `DocTotal − VatSum` (tax-only invoices exist).
- Credit notes (`ORIN`/`RIN1`) are subtracted, same grouping.
- `INV1.Quantity` is **pieces** (C-0001). Litres = pieces × `engine/plan_units.pack_litres(OITM.U_SKU)`; KGS packs = weight ÷ 0.91.
- Week-of-month buckets: 1 = days 1-7, 2 = 8-14, 3 = 15-21, 4 = 22-28, 5 = 29-31. The freeze shapes the expected stream with `litres_per_day` per bucket.

## What the first pull said (window 2026-06-01 → 2026-08-31, written to live/state/demand_baseline.json)
- Outside FG demand: **3,176,798 L, ₹59.83 Cr** over 3 months → **1,058,933 L / ₹19.9 Cr a month**.
- By channel (L): GT 1,662,456 · MT 737,147 · ROI 566,910 · HORECA 102,969 · CORPORATE 95,574 · CSD 11,731.
- Excluded: CUSTA000606 ₹64.42 Cr (FG only, CN netted), branches ₹0.93 Cr, e-com others ₹0.17 Cr.
- **Month-end bunching is real:** L/day by bucket = 20,317 · 25,624 · 20,129 · 33,893 · **134,695** (days 29-31).
- **125 SKUs sold; 64 are on the plan sheet, 61 are not (844,054 L = 27% of outside litres)** → assumption A18.
