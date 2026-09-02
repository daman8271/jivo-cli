## Targets — product, flex, segment, node, channel

*Sales-lens decoder. Live-verified 2026-08-25 against Control Panel `http://138.252.101.118:9080` (login `preshit`, admin) and SAP B1 Service Layer (`JIVO_OIL_HANADB`). Read-only throughout — no write/`save-targets` endpoint was ever called.*

### Headline: the target layer is the app's OWN data — it is NOT in SAP

This is the single most important fact for a future AI. Everything *else* the Control Panel serves is a re-dressed SAP row (invoices, orders, stock, ledgers). **The five target endpoints are the exception: they read the Django app's own database and have no SAP object behind them at all.** Verified two ways:

- **Lineage recon** (`connections/lineage-evidence/sourcemaps/control-panel.md` §2, §4): the `targets (5)` command group is the only group whose "real source behind Django" is **"Django's own DB. No SAP object."** The recon searched all three HANA company schemas — `SELECT ... FROM SYS.TABLE_COLUMNS WHERE COLUMN_NAME LIKE '%TARGET%' OR '%TGT%'` — and every hit was a stock SAP-internal column (document-flow pointers, workflow fields). SAP's `@BUDGET`/`@BUDGET1` UDT is a **cost-budget** dimension (`U_FIXED_AMOUNT`, `U_MONTH`), not the litre/realise sales target. There is no sales-target table anywhere in SAP.
- **Live behaviour**: `targets list` returns `"source":"default"` on every row (Jul & Aug 2026). The values are hard-coded app defaults, editable only through the gated `POST /realise/api/save-targets/` write path (admin PIN re-auth via `/verify-pin/`). As of 2026-08-25 **no saved override exists in any month I sampled** — every product row is `default`, and `segment` override sets come back empty `{}`.

So: **actuals (DONE) are SAP; targets (TGT) are the app.** The dashboard's whole job is to staple the two together. You cannot query a target from SAP, and you cannot audit a target against SAP — there is nothing to audit it against.

### What the sales team means by a "target"

A target at JIVO is a **monthly volume goal in LITRES**, optionally carrying a **realisation goal in ₹/litre**. It is expressed five different ways at five different grains, and — critically — **those five views are maintained by hand and do NOT foot to each other** (see Reconciliation R3). "Did we hit target?" has no single answer until you say *which* target.

The unit is always **true litres** — the app has already applied the pieces→litres conversion ([C-0001]: `INV1.Quantity` is pieces/bottles, the "20 PCS" in item names is carton config). The `liter`/`litres` fields the app returns = parsed pack-size × pieces, so target litres are directly comparable to them. You never multiply by carton config here.

### Term table

| Term | Meaning | SAP lineage | Differs from the accounts view | Gotchas / corrections |
|---|---|---|---|---|
| **TGT** | The monthly target — litres and/or ₹-value goal, per channel/segment/node/product | **None (Django DB).** No SAP object | Accounts has no concept of a sales target; "turnover" is a backward-looking actual | Five independent grains that don't reconcile (R3). All `source:default` right now |
| **DONE / DONE L** | Achieved value (₹) / achieved volume (litres) month-to-date against TGT | SAP `OINV`/`INV1` net of returns (`ORIN`/`RIN1`), via `sales-data` | DONE L is **litres** — accounts never measures volume | `liter` already = pack-size × pieces ([C-0001]); can go **negative** (Jul PREMIUM\|GHEE = −1,468 L, returns > sales) |
| **BAL / BAL W/O OIH** | Gap left to target: `TGT − DONE`; and `TGT − DONE − OIH` | Derived (TGT from Django, DONE/OIH from SAP) | n/a — a planning measure, not a ledger figure | OIH = open sales-order book (`ORDR`/`RDR1.OpenQty`) |
| **REALISE (₹/L)** | Net avg selling price per litre actually earned, after schemes/CN | `sales-data`: net sales ₹ ÷ litres, from `OINV`/`INV1`/`ORIN` | Accounts turnover = `DocTotal − VatSum − CreditNotes` in **rupees**; realise is **₹ per litre**, a rate not a total | The whole API is named for it (`/realise/api/…`) |
| **`tgt_ltrs` / `target_sale`** | Product-target **litres** for a `U_TYPE\|SUB_GROUP` key | Django DB | — | `target_sale` in the Slide-1 feed is a **misnomer — it is litres, not rupees**. Equals `tgt_ltrs` exactly |
| **`tgt_rate` / `target_realise`** | Product-target **realisation** (₹/L goal) for that key | Django DB | — | Equals `tgt_rate`. In `nodes` it was **0 in July** (litre-only), **populated in August** — the ₹/L target is a recent addition |
| **Product target** (`targets list`) | Litres + ₹/L keyed by `U_TYPE\|U_Sub_Group` (16 keys) | Django DB; key vocab derived from SAP `OITM.U_TYPE`+`U_Sub_Group`(+`U_Variety`) | — | Key taxonomy is the app's **Slide-1 derived** taxonomy, not raw OITM (R1): OLIVE is split into `OLIVE`+`EXTRA VIRGIN OLIVE` by `U_Variety`; premium MUSTARD is relabelled `YELLOW MUSTARD` |
| **FLEX target** (`targets flex`) | Flat litre goal per **salesperson** for the month | Django DB | — | Key format `¦person=<NAME>` (broken-bar `¦` = U+00A6, generic flex-dimension prefix). `¦person=—` (em-dash) = unassigned bucket. **Empty `{}` when not yet set** (Aug 2026 was empty; July had 10 people) |
| **SEGMENT override** (`targets segment`) | Saved target overrides scoped to one segment (OILS/BEVERAGES/PREMIUM/COMMODITY) | Django DB | — | Holds **only explicitly-saved overrides**, never the defaults. **Empty `{}` is normal** and is what I observed for every segment |
| **NODE target** (`targets nodes`) | Litres (+ ₹/L) by **main_group × state × sales_person × segment** | Django DB | — | Two "segment" senses collide: the row's `segment` field = PREMIUM/COMMODITY (= SAP `U_TYPE`); the `seg` **query param** = OILS/BEVERAGES and **is ignored** — OILS and BEVERAGES returned byte-identical rows (R-note). Blank string = "all/unscoped" |
| **CHANNEL target** (`targets channel`) | One litre figure per **main group / channel** | Django DB; channel = SAP `OCRD.U_Main_Group` on the actual side | — | Channel **codes differ from the actuals**: target uses `ECOM`, SAP `U_Main_Group` says `E-COMMERCE`; 7 target channels vs 12 actual main-groups (R4) |
| **Channels: GT / MT / ROI / ECOM / HORECA / CSD / REST** | General Trade / Modern Trade / Rest-of-India / E-Commerce / Hotels-Restaurants-Catering / Canteen Stores Dept / residual | `OCRD.U_Main_Group` (party's governing main group) | Accounts groups by BP/GL, never by go-to-market channel | **ROI = Rest of India, not return-on-investment.** `main_group` values differ across company books ([C-0015]) — do not segment across companies on it |
| **Segment: OILS vs BEVERAGES** | Two reporting tracks (edible oils vs juices/wellness) | `OITM.U_TYPE`/`U_Sub_Group` taxonomy ([never name-match]) | — | The target layer sampled is **OILS/oil-company only**; BEVERAGES has its own feeds and the node `seg=BEVERAGES` filter did not actually scope (open question) |
| **Segment: PREMIUM vs COMMODITY** | Margin tier within OILS | SAP `OITM.U_TYPE` (values `PREMIUM`, `COMMODITY`; SAP also has `OTHERS` + blank which targets ignore) | — | This is the finer `segment` inside a node row, distinct from OILS/BEVERAGES |

### The five endpoints ↔ CLI methods (all GET, read-only)

| CLI | Endpoint | Shape | Live Aug-2026 sample |
|---|---|---|---|
| `targets list` | `GET /realise/api/targets/` | `{key → {tgt_ltrs, tgt_rate, source}}`, key = `U_TYPE\|SUB_GROUP` | 16 keys, all `source:default`; e.g. `COMMODITY\|MUSTARD` 625,000 L @ ₹145 |
| `targets flex` | `GET /realise/api/flex-targets/` | `{¦person=NAME → litres}` | `{}` (not yet set for Aug; Jul had 10 people, 1,295,000 L) |
| `targets segment` | `GET /realise/api/segment-targets/` | `{key → {tgt_ltrs, tgt_rate}}`, only saved overrides | `{}` for OILS and PREMIUM |
| `targets nodes` | `GET /realise/api/target-nodes/` | `[{main_group, state, sales_person, segment, target_ltrs, target_realise}]` | 21 rows; `target_realise` now populated (was 0 in July) |
| `targets channel` | `GET /realise/api/channel-targets/` | `{channel → litres}` | `{GT:400000, ECOM:1285000, MT:170000, ROI:115000, CSD:30809, HORECA:5000, REST:20000}` |

Write counterpart (documented, **never called**): `POST /realise/api/save-targets/` — persists product-target edits; gated behind an admin PIN modal (`/realise/api/verify-pin/`).

### Reconciliation results (live CP vs live SAP)

**R1 — Product-target taxonomy vs SAP OITM (Oil). RECONCILES, with a derivation caveat.**
The 16 Aug-2026 product keys vs distinct `U_TYPE|U_Sub_Group` in `JIVO_OIL_HANADB.OITM` (2,277 items swept live): **13 keys match a real OITM sub-group exactly**. The other 3 are **app-derived Slide-1 labels, not raw OITM values**:
- `PREMIUM|EXTRA VIRGIN OLIVE` — OITM has `PREMIUM|OLIVE` (105 items) and one `PREMIUM|EXTRA VIRGIN`; the app splits OLIVE by `U_Variety='EXTRA VIRGIN'` into a separate bucket. Proof: July line rows carry `PREMIUM|OLIVE` (289 rows) and **never** `EXTRA VIRGIN OLIVE`, yet the Slide-1 rollup shows both (OLIVE 236,716 L + EXTRA VIRGIN OLIVE 27,028 L).
- `PREMIUM|YELLOW MUSTARD` — OITM has no such sub-group; line rows carry `PREMIUM|MUSTARD` (32 rows), which the rollup relabels `YELLOW MUSTARD` (26,655 L).
- `PREMIUM|SLICED OLIVE` (target 0/0) — OITM files SLICED OLIVE under `OTHERS`, not `PREMIUM`; a placeholder key with a zero target.

Ruling: **target keys use the app's derived product taxonomy** (OITM `U_TYPE`+`U_Sub_Group` refined by `U_Variety`), never the raw OITM column. Never name-match a target key straight onto `OITM.U_Sub_Group`.

**R2 — TGT vs DONE, July 2026 OILS product total. RECONCILES.**
Product-target total **2,005,000 L** vs actual DONE **2,189,879 L** = **109.2 % of target**. The Slide-1 realise feed (`sales data`) embeds `target_sale`/`target_realise` per product row, and these equal the `targets` endpoint values field-for-field (e.g. `COMMODITY|MUSTARD` target_sale 625,000 @ target_realise 145; `PREMIUM|CANOLA` 350,000 @ 205). This is the app literally stapling its Django target onto the SAP-derived actual. Actual DONE lineage: `OINV`/`INV1` net of `ORIN`/`RIN1`, litres = pack-size × pieces.

**R3 — Do the four target layers foot to each other? THEY DO NOT. (The headline gotcha.)**
July 2026 totals, same month, same OILS business:

| Layer | July total | Aug total |
|---|---|---|
| Product (`targets list`) | 2,005,000 L | 2,005,000 L |
| Channel (`targets channel`) | 2,541,000 L | 2,025,809 L |
| Nodes (`targets nodes`) | 2,541,000 L | 2,805,809 L |
| Flex (`targets flex`) | 1,295,000 L | (empty) |

- **Product ≠ Channel** by **536,000 L** in July — two independent target-setting exercises over the same goal.
- **Nodes == Channel exactly (2,541,000)** in July — nodes were a clean decomposition of channel targets — **but in Aug they diverge by 780,000 L** (nodes 2,805,809 vs channel 2,025,809), because Aug added premium per-person node rows on top of the commodity figure that the channel target still reflects. Hand-maintained layers drift.
- **Flex (1,295,000)** is lower than all — it covers only the 10 named salespeople and omits the large unassigned house channels (ECOM, MT commodity, etc.).

For a future AI: **never quote "the July target" as one number.** It is 2.0 M (product), 2.5 M (channel/node) or 1.3 M (flex) depending on the lens.

**R4 — Channel target vs actual channel litres, July 2026. Vocab does NOT line up cleanly.**
Target (app) vs actual litres (`sales data`, `OCRD.U_Main_Group`):

| Channel | Target L | Actual L | % |
|---|---|---|---|
| ECOM / E-COMMERCE | 1,300,000 | 1,019,267 | 78 % |
| GT | 685,000 | 617,699 | 90 % |
| MT | 215,000 | 257,621 | 120 % |
| ROI | 256,000 | 214,928 | 84 % |

Caveats: target code `ECOM` ≠ actual `U_Main_Group` value `E-COMMERCE` (the app maps them); **7 target channels but 12 actual main-groups** — `CORPORATE`, `CASH SALE`, `STAFF`, `BRANCH`, `REFERENCE`, `PURCHASE OIL` carry real litres yet have no channel target.

### Open questions

- **Beverages / Mart target scope.** `targets nodes --seg BEVERAGES` returned **byte-identical rows to `--seg OILS`** (21 rows each, Aug), so the `seg` query param appears to be **ignored** by the nodes endpoint — I could not confirm a separate BEVERAGES node set exists, nor any Mart target layer. Needs a login/segment that actually scopes, or reading the server code.
- **Where the Django target table physically lives** is still unidentified (recon could not reach the app's DB host; it is confirmed *not* in SAP and *not* in the 15-DB Postgres cluster). So targets cannot be cross-checked at the row level against any datastore I can reach — only against the API's own output.
- **`target_realise` went from 0 (July nodes) to populated (Aug nodes).** Confirm this is a deliberate rollout of ₹/L node targets, not a data-entry artefact.
- **`preshit` money-gating.** Sales **volume + `line_total`** are visible to this login (used above), so TGT-vs-DONE in litres and ₹ is computable. Only the dedicated money panels (COGS, salaries, expense aggregates) are blank for this login — not relevant to the litre-based target layer.
- Whether the **`save-targets` flow ever writes back to SAP**: recon rules it Django-only (confidence ~85 %, code/doc evidence, write path not executed). No SAP UDT could receive it.
