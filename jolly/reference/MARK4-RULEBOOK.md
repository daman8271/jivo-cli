# Mark 4 rulebook — what the planner takes as fact

Generated 2026-09-06 by `reference/build_mark4_rulebook.py` from the 5 Sep meeting with Gurvinder veerji, Daman's clarifications of 6 Sep, the factory app's records and the SAP BOM. **Do not edit by hand** — edit the script. Machine copy: `reference/mark4-rulebook.json`. Open questions: `out/QUESTIONS-FOR-GURVINDER-2026-09-06.md`.

## Settled rulings

| # | Rule | Source |
|---|---|---|
| R01 | Factory truth is ji.jivo.in, never SAP, for production, stock, dispatch and lines. | jolly/CLAUDE.md RULE 0 (Daman 2026-09-03) |
| R02 | A shift is 12 clock hours with lunch and tea inside it: 10 working hours per session. Day + night = 20 hours, not 22, not 24. | meeting 14:13-14:43 |
| R03 | Labour allows ONE line at night. Which one is the plant's call; the plan names its pick each day. | meeting 11:06-11:31 |
| R04 | Sunday: no production. Sunday is for dispatch — relieve the godown. | meeting 13:14-13:41 |
| R05 | Plan at 80% of capacity. If the machine gives more, good. | meeting 08:46-09:20; Daman 2026-09-06: '80% efficiency in relation to speed' |
| R06 | Keep one product running on a line all day. Every changeover lowers efficiency and output and raises labour cost. | meeting 09:28-09:59 |
| R07 | Clear Pack cannot fill 3 L or 15 L. 10 Head and 6 Head cannot fill 15 L. 15-litre tins only on the Tin Head. | meeting 03:03-03:19, 05:38-05:57, 08:05-08:20 |
| R08 | 3 L runs on the 10 Head and the 6 Head. | meeting 03:03-03:19; August: 6 Head 23,886 L |
| R09 | JP: 1-litre mustard (Kachi Ghani; the 26 g and round bottles run best). Groundnut 1 L allowed. | meeting 06:22-06:43, 12:13-12:20; Daman 2026-09-06 'majorly mustard, also groundnut' |
| R10 | Clear Pack: 1 L in the 40 g bottle (canola, sunflower); the 52 g bottles allowed. Sesame (75 g) never. | meeting 06:43-07:07, 11:42; Daman 2026-09-06 |
| R11 | 10 Head: 1 L and 2 L preferred (all ten heads usable). Every 1 L bottle Clear Pack cannot fill goes here. 5 L possible but poor. | meeting 07:07-07:49, 11:50 |
| R12 | 6 Head: 5 L first (spaced heads; labeller broken; printed 5 L tins need no label), then 3 L, then leftover 1 L / 2 L. | meeting 07:18-07:26, 08:05-08:44 |
| R13 | Pouches only on the pouch machine. No pouch requirement today. | meeting 09:20, 12:23 |
| R14 | Drums are filled by hand and are OUT of Mark 4: the three 200 L SKUs are listed as 'filled by hand, not scheduled', never as stuck. | Daman 2026-09-06 (meeting 02:45-04:07 for the manual drum line) |
| R15 | The pack of a product comes from its recipe (BOM container item), never from the plan sheet's pack-type column. Seven '15 LTR PET' rows and SO Olive 5 L are tins. | BOM check 2026-09-06; meeting 08:05 'they are 15-litre tins'; Daman 2026-09-06 yes |
| R16 | Make at least ₹2 crore of goods a day; ₹2.5 crore a day finishes the plan sheet. | meeting 13:41-14:11; Daman 2026-09-06 'it is yes' |
| R17 | Do not plan from POs alone — GT/MT orders bunch in the last weeks of the month and the buffer runs out. Production planning predicts the month's POs from past GT/MT sales (excluding e-com) and is ready for them. | meeting 10:19-11:02; Daman 2026-09-06 |
| R18 | Past GT/MT sales are read from OMS and from SAP bills. E-com stays on its POs. | Daman 2026-09-06 |
| R19 | A product with no order behind it and last-in-sales goes last (canola 5 L 4 pcs). | meeting 10:07-10:27 |
| R20 | The 1-litre pack moves from a 16-piece carton to a 20-piece carton wherever 16 was used. A recipe change; a major step. | meeting 04:26-04:43, 15:51-16:02 |
| R21 | 'Trucks that left today' is irrelevant. Show the open dispatch book in days of pendency and 'billed today, on a truck when' (2 days usual, 14 worst). | meeting 00:43-01:08 |
| R22 | The overview must read line by line, not as one total. | meeting 05:11-05:23 |
| R23 | Godown = BH-BT + BH-PF finished goods against 827,000 L working / 923,000 L peak. It is over 90% full. | STORAGE-CAPACITY.md; meeting 13:24; Daman 2026-09-06 |
| R24 | Labour cost comes from the factory app (ji.jivo.in): crew per run, hours. | meeting 12:43-13:03; Daman 2026-09-06 'JA = factory app' |
| R25 | When a material is missing, the person responsible enters WHY; when the plan says X and the plant runs Y, the system asks the relevant person and keeps the answer as a rule. Messages via WhatsApp — NOT in this build (Daman 2026-09-06: build Mark 4 first). | meeting 15:21-16:54; Daman 2026-09-06 |
| R26 | Every assumption Mark 4 makes is listed on its own page: what is taken as fact, the exact data used, and what would change it. | Daman 2026-09-06 |
| R27 | Only day 1 is observed; every later day is computed. Forecast rows stay triple-tagged. No real phone number ever. Never type a business number into the site. | jolly/CLAUDE.md |

## Assumptions Mark 4 makes on top

| # | Assumption | Why | What would change it |
|---|---|---|---|
| A01 | Planning speed per line and pack = min(80% x the app's rated speed, the best August run that lasted 3 hours or more) when at least 3 usable August runs exist; else 80% x rated; for a pack the app has no rating for, the typical (median) August run; else 80% x the Mark 3 carried table. A usable run logged at least 60 minutes; a logged speed above 120% of the rating is discarded as a clock error (one-hour segments carrying a whole day's pieces). | 80% of capacity is the ruling (R05). The app's rated speeds were never reached in August (JP typical 39% of rated), so 'capacity' is capped at what the machine has demonstrated. A run left open through breaks makes August speeds read slower than they were, so the cap is conservative. | Gurvinder's answer to question 1 (his own capacity number per machine). |
| A02 | Packs of 1 L or less (200 ml, 250 ml, 500 ml, 869 g / 954 ml) fill in the 1 L slot at the 1 L pieces-per-hour rate. | No August run of 250/500 ml exists; JP ran 200 ml and 954 ml in August. | A measured small-pack run in the app. |
| A03 | Bottle family decides eligibility on JP, Clear Pack and 10 Head (26 g / round / 40 g / 52 g / 75 g / small). 2 L, 3 L, 4 L, 5 L bottles are one family each. | Meeting 06:22-07:07: the lines' efficiency is bottle-specific. No ruling separates 2 L or 5 L bottles. | The machine-spec sheet Daman will give for Mark 5/6. |
| A04 | 3-litre tins fill on the Tin Head (fallback 6 Head). | Daman 2026-09-06: tins have a shape, they go on the tin machine. No August record of a 3 L tin run. | Gurvinder question 4. |
| A05 | Tin Head fills 3 L and 5 L tins at the same pieces-per-hour as 15 L tins (240/hr rated). | No rate exists for smaller tins on the Tin Head. | A measured run, or Gurvinder question 1. |
| A06 | The Tin Head is available every working day of September. | It ran 1 day in June, 1 in July, 2 in August, 1 so far in September; the plan needs about 7 full days of it. | Gurvinder question 5. |
| A07 | The night line is chosen each day as the line with the most PO-backed litres still unmade after the day session; ties go to JP (mustard). | R03 says one line, the plant's call; the meeting's example was mustard on JP. | A daily pick from Gurvinder (later: via the why-loop). |
| A08 | A changeover (oil change, cold start, or pack-size change) costs 51.3 minutes of line clearance; an oil change also flushes 400 L. A pack-size change costs no more than that. | Mark 3's measured clearance; nobody has said how long a 1 L → 5 L change takes. | Gurvinder question 7. |
| A09 | Expected GT/MT demand per SKU = the average of the last 3 months of GT/MT billing (SAP invoices, Oil book, channel GT/MT, e-com and inter-company excluded), shaped by week-of-month from the same history. The OMS open book supplies real orders on top. | R17/R18. SAP bills are the only complete 3-month record; OMS history before 2 Sep is not yet backfilled. | Gurvinder question 12 (months, per product or per oil); the OMS backfill. |
| A10 | A new FG code seen in the factory app but absent from the plan sheet is the same product as the plan row with the same name minus its carton count (16 PCS ↔ 20 PCS). Pieces targets stay; the carton item changes. | R20; Cold Press Groundnut 1 L 20 pcs (FG0000461) has run on the 10 Head since 3 Sep and is not in the 31 Aug sheet. | Gurvinder question 11. |
| A11 | Dispatch continues on Sundays at the weekday rate. | R04: Sunday is for dispatch. No measured Sunday gate rate yet. | Sunday gate-out data from ji.jivo.in after the first live Sunday. |
| A12 | ₹ of goods made = litres made x each SKU's realise rate (Mark 3's realise table). The plan sheet is worth ₹75.2 crore at those rates, i.e. ₹2.5 crore a day over 30 days. | R16 needs a rupee value per litre; realise is the only per-SKU rate we hold. | Gurvinder question 13 (₹200/kg average, 3,000 t). |
| A13 | Yellow mustard 1 L (75 g bottle) fills on the 10 Head or 6 Head, not JP. | August ran it on the 6 Head (6-7 Aug) and 10 Head (26-27 Aug), never on JP. Daman 2026-09-06: 'go with where you think it should run'. | Gurvinder question 3. |
| A14 | 40 g bottles never run on JP; 75 g and 26 g bottles never run on Clear Pack. | Not ruled, never observed in August; JP is the mustard line, Clear Pack refused sesame (75 g). | A ruling or an observed run. |
| A15 | 3 L on the 10 Head runs at the 10 Head's 5 L planning rate. | No app config and no August run for 3 L on the 10 Head; the 6 Head's 3 L record is the only 3 L data. | A measured 10 Head 3 L run. |
| A16 | Three small packs (Kachi Ghani 500 ml, Sunflower 200 ml, Sesame 500 ml) have no bottle in their recipe; they are classed SMALL by litres and fill in the 1 L slot. | SAP BOM lists only the oil for FG0000448, FG0000451, FG0000452. | A completed BOM in SAP. |
| A17 | 'GT/MT sales' means every outside channel except e-commerce: the customer's SAP channel (OCRD.U_Main_Group) in GT, MT, ROI, CORPORATE, HORECA, CSD or REFERENCE. Excluded: E-COMMERCE, BRANCH, STAFF, CASH SALE, and the 9 Oil inter-company cards (correction C-0005) — on Oil's books the whole e-commerce channel is the JIVO MART transfer (CUSTA000606). The excluded totals are published beside the included ones. | R17/R18 say GT/MT excluding e-com; Gurvinder's words at 10:37 were 'GT/MT sales, apart from e-commerce'. ROI, corporate, HORECA and CSD are outside customers the plant must also make for. | Gurvinder question 12, or Daman naming the channels. |
| A18 | Expected demand covers every SKU that sold in the last 3 months, not only the plan sheet's 84 rows: 61 sold SKUs are absent from the sheet (844,054 L in June-August, 27% of outside litres). They enter the plan as expected orders at their trailing average, ranked by sales, below PO-backed work. | A plan that ignores a quarter of what customers buy will be wrong on the lines those SKUs occupy. | Gurvinder question 12; the plan sheet being extended. |

## Choices this build made where the rulebook was silent

Not business facts — mechanisms the build had to pick to satisfy a ruling. Each one is the first place to look when the plan does something odd, and each can be replaced by a ruling.

| # | Choice | Why | What would change it |
|---|---|---|---|
| B01 | A product may only move to a second- or third-choice line when EVERY better line for it has less than one line-clearance of free hours left that day — i.e. the better line could not start it anyway. | The rulebook says a SKU spills to a preference-2 line only when the preference-1 lines are full. 'Full' has to mean 'cannot start another run', because the planner fills a line down to a sliver of an hour; treating a leftover 20 minutes as free hours would strand work on the wrong machine. | A ruling that a product may open on a second-choice line while its first choice still has time (for instance to keep two lines on the same oil). |
| B02 | One product change per line per session. Whatever the line was running yesterday ranks first inside its preference band; a second change is allowed only when the line would otherwise stand idle with more than one clearance of hours free, and every such lift is printed in the day's decisions. | R06: keep one product on a line all day. Ranking rather than forbidding keeps the value order intact inside the rule, and the printed lift keeps the exception visible instead of silent. | Gurvinder's answer to question 7 (what a pack-size change really costs), or a ruling that a line may change twice. |
| B03 | The night line is the line with the most order-backed litres still unmade after the day session, counting only products that line can fill; ties go to JP. With no order-backed litres left, the line with the most expected and plan-sheet litres; with nothing left at all, no night session. The reason is published every day. | R03 gives one line at night and calls the pick the plant's call; A07 fixes the rule and the JP tie. Publishing the runners-up and the reason is what lets Gurvinder overrule it. | A daily pick from Gurvinder, or his answer to question 8. |
| B04 | On Sunday nothing is made, but orders are still filled from stock and the trucks leave after the usual wait, exactly as on a weekday. | R04: Sunday is for dispatch, to relieve the godown. Mark 3 skipped dispatch on Sundays only because it sat inside the same block as production. | A measured Sunday gate rate from ji.jivo.in that differs from a weekday's (A11). |
| B05 | Expected orders are shaped by week of month in five buckets — days 1-7, 8-14, 15-21, 22-28, 29 to month end — using a product's own three-month shape when it sold in all three months, otherwise the shape of all products together. Real OMS orders for the same product in the same days are taken off the top; e-com is never netted, it keeps its own POs. | R17: orders bunch at month end, and a flat spread would leave the plant short in the last week. A product that sold in only one month has too thin a shape of its own to trust. R18 keeps e-com on its POs. | Gurvinder's answer to question 12 (how many months, per product or per oil). |
| B06 | A product that sells but is not on the plan sheet joins the plan only when SAP's recipe names its oil and its container can be classed. The rest are published as expected demand the plan cannot place, each with the reason. | A18. Without a recipe the planner cannot book the oil, the bottle or the carton, so scheduling it would quietly invent material it does not have. Publishing the rest keeps the gap visible instead of dropping it. | A completed recipe in SAP, or the plan sheet being extended to cover them. |
| B07 | For a product that sells but is not on the plan sheet, the rupees a litre are its own three-month billing average. | A12 uses the plan sheet's realise rate, and these products have none. Their own billing is the only rate that belongs to them; the default rate would flatter or punish them arbitrarily. | The plan sheet being extended (it carries a realise rate per row). |
| B08 | Products that are only expected — no order behind them yet — are ranked by their trailing monthly litres, below everything with a real order and above the rest of the plan sheet. | R19: what nobody has ordered and nobody has been buying goes last. Trailing litres is the same measure R17 uses to expect the order in the first place. | A ruling that names a different order of priority. |
| B09 | Pendency of the open dispatch book = the litres still to go out divided by the average litres that left the gate on each of the last seven recorded days — for all three books, and for Oil on its own. When no day has a record yet it is published as blank with the reason, never as zero. | Gurvinder asked how many days of pendency the open book carries (R21). Days of work at the recent gate pace is the plain reading, and both halves come from ji.jivo.in. | A ruling on the window (seven days, or the month), or a gate rate that stops being flat enough to average. |
| B10 | Rupees of goods made = the goods receipts booked in the factory app, valued at each product's realise rate; a product outside the plan sheet is valued at its own billing rate, and only a product with neither gets the default rate. Each of the three shares is published. | R16 needs a rupee figure against the ₹2 crore floor. Goods receipts are the fuller count — the machines' own reports see about two-thirds of the plant. Splitting the valuation keeps a default-rate share visible instead of hidden inside one total. | Gurvinder's answer to question 13 (₹200 a kilo over 3,000 tonnes). |
| B11 | A once-a-day input file older than eight days, or covering the wrong month, is treated as stale: the plan falls back to what it used before and says so on the page. | Both daily inputs are written by a cron job that can silently stop. A quietly stale file is worse than a named fallback, and eight days survives a long weekend plus a failed night without hiding a dead job. | A ruling on how old is too old, or the jobs becoming monitored in their own right. |
| B12 | Material is ordered against expected orders as well as against real ones. | R17 is the whole point of expecting the orders: the packaging has to be there before the order arrives. Buying only against real orders would leave every expected-only product permanently without a bottle. | A ruling that material is bought against confirmed orders only. |
| B13 | When a recipe uses more than one container per saleable piece, the line is planned in CONTAINERS, not in pieces: the slot and the bottle come from one container's litres (the piece divided by how many the recipe names), and the piece count is multiplied by the same number to get line time and material. | R15 says the recipe decides the pack, and the recipe of the four combo rows names two one-litre bottles per set. Reading the set as a two-litre pack put them on a machine no two-litre bottle needed, at half the bottle count and the wrong bottle family — so the mustard combo escaped both the mustard rule and the bottle rule at once. | A ruling that a combo set is filled some other way, or a recipe that names its containers differently. |
| B14 | A recipe child whose name only MENTIONS a container — a carton, a label, a cap, a tin strip, a sleeve — is not the container. The container is the first child left after those are set aside. | Twenty-two of the plan's recipes list something that mentions the container beside the real one, and one pouch row lists its carton first. Today the right item happens to come first almost everywhere, which is luck; the freeze will class products this sheet never saw. | An item-type field on the BOM child (SAP has one) being read instead of the name. |
| B15 | A product whose size nothing states — not the sheet, not its container's name — gets no slot at all and is published as unplaceable, never guessed into the smallest bottle. | The classifier used to read a missing size as zero litres and call it a small pack, which is a silent wrong machine. No plan row is in that state today; the freeze will meet ones that are. | The product's size reaching the sheet or its recipe. |
| B16 | A machine slot with no rating in the app and too few usable August runs to be a typical rate is published with NO planning speed, and nothing is scheduled on it until someone gives one. Two slots are in that state: Clear Pack 2 L (every one of its August two-litre runs was a combo set of one-litre bottles, so the line has no record of filling a two-litre bottle at all) and 6 Head 3 L (three runs, one of them a 71-minute clock error, one a 48-piece trial). | A speed measured on one pack is not evidence about another, and a plausible number carries further than a blank. Nothing is stranded either way: 2 L keeps the 10 Head and the 6 Head, both rated, and 3 L keeps the 10 Head and the Tin Head. | Gurvinder's answer to question 1 (his own speed per machine), or a measured run. |
| B17 | A recipe quantity is read as a COUNT of containers only when something confirms it: the container's own printed size times that quantity comes back to the piece, or — when the container prints no size — the child is counted in pieces. A container measured in kilograms, litres or metres carries an amount of that child, never a count. | The four combo rows name two 1-litre bottles per set and the arithmetic confirms it (2 x 1 L = the 2 L piece). Three pouch rows name their film in KGS. Read as a bare number, 15 kg of steel on a 200 L drum becomes fifteen drums, its litres divided by fifteen, and the row lands on a machine that fills nothing like it. | An item-type or packaging field on the BOM child being read instead of the unit and the printed size. |
| B18 | A logged run is discarded as a clock error when it beats 120% of its slot's rating — or, where the app has no rating for that slot, when its LITRES an hour beat 120% of the most litres an hour any rated slot on the same line can pour. A run under three hours never sets a median or a best. | The old guard needed a rating, so it was switched off in exactly the slots where nothing else could catch a mis-clocked segment. 6 Head 3 L was [11, 820, 4183] pieces an hour: 4,183 three-litre bottles is 12,540 L/hr on a line whose best rated slot pours 3,000, and the 71-minute segment that produced it set the median that became the planning speed — a three-litre pack filling faster in litres than the five-litre on the same heads. | Real rated speeds for the unrated slots (Gurvinder question 1), or run segments that close when the run stops. |
| B19 | A combo set and a plain bottle of the same size are separate evidence. Each line publishes a second speed table for the packs it has run as combos; a line with no combo record has no combo rate, and a SKU whose recipe holds more than one container cannot be scheduled there until someone gives one. | On Clear Pack the two clusters do not overlap at any point — plain 1 L at 1,942-2,927 bottles an hour, combo sets at 87-1,277. Pooling them published a 'typical' of 1,610 that describes neither, and planned the four combo SKUs at 2,927 bottles an hour, about 29 line-hours for work the line has never done in under 67. | Gurvinder's answer to question 1, a combo run on another line, or a ruling that a set is bundled off the line. |
| B20 | THE STORAGE CEILING IS A HARD CAP ON EVERY RUN. No run may be longer than the headroom left in the godown — the declared 827,000 L working ceiling minus what is physically in it, finished goods plus stock already billed but not yet trucked out. The headroom is worked out afresh at the start of every day and comes down litre for litre as the day's runs are made, so once it reaches zero the plant stops for the day whatever hours, material and orders are left. When the headroom is what stops a product, the day says so with a held-up row naming STORAGE as the binder, exactly as it does for a missing bottle. | Gurvinder ruled the godown limit (R09/R20) and Daman declared the figure, but neither said what the planner should DO when the plan reaches it, so this is the build's choice and not a ruling. Making it anyway would publish a month the warehouse cannot hold: goods stay in the godown until they are physically DISPATCHED, not when they are billed, so a plan that ignores the ceiling is a plan that overflows it. It is the single biggest hand on this month's sheet — bigger than hours, bigger than material — and it was applied silently in one line of the engine with its name in no rule, no assumption and no choice. A cap nobody can see is a cap nobody can argue with. | A ruling that the plant may build ahead past the ceiling (a hired warehouse, or the 923,000 L peak used as the working limit instead), a faster gate that empties the godown sooner, or Gurvinder ruling that the planner should idle the cheapest machines rather than cap every run alike. |

## Speeds the plan uses (containers per hour)

**Planning** already has the 80% and the August cap inside it. The engine's own `lines` table holds RATED speeds and derates them at run time — moving a planning speed into that table without turning that derate off runs the plant at half.

**Aug range** is the whole kept spread, min to max. A median sitting in the middle of a 380x spread is not a measurement, and the column is there so it cannot look like one.

| Line | Pack | App rated | Aug range | Aug typical (3 h+) | Aug best | Aug runs (3 h+) | **Planning** | Basis |
|---|---|---:|---:|---:|---:|---:|---:|---|
| JP Machine | 1L | 5,400 | 120–6,008 | 2,132 | 2,910 | 20 (16) | **2,910** | min(80% x rated, best sustained August run of 3 h+) over 20 runs; 1 run(s) discarded as clock errors — above 120% of rating |
| Clear Pack | 1L | 4,800 | 1,942–2,927 | 2,653 | 2,927 | 6 (6) | **2,927** | min(80% x rated, best sustained August run of 3 h+) over 6 runs |
| Clear Pack | 2L | — | — | — | — | 0 (0) | **—** | NO RATE — needs a ruling |
| Clear Pack | 4L | — | — | — | — | 0 (0) | **800** | 80% x Mark 3 carried table; no app config, no August run |
| Clear Pack | 5L | 3,000 | 187–1,068 | 819 | 1,068 | 6 (6) | **1,068** | min(80% x rated, best sustained August run of 3 h+) over 6 runs; 1 run(s) discarded as clock errors — above 120% of rating |
| 10 Head | 1L | 2,100 | 48–2,213 | 1,390 | 1,957 | 19 (16) | **1,680** | min(80% x rated, best sustained August run of 3 h+) over 19 runs; 3 run(s) discarded as clock errors — above 120% of rating |
| 10 Head | 2L | 1,260 | — | — | — | 0 (0) | **1,008** | 80% x rated (no August run) |
| 10 Head | 3L | — | — | — | — | 0 (0) | **720** | DERIVED: 3 L assumed to run at the 10 Head's 5 L planning rate (A15) |
| 10 Head | 5L | 900 | — | — | — | 0 (0) | **720** | 80% x rated (no August run) |
| 6 Head | 5L | 600 | 24–529 | 285 | 529 | 15 (13) | **480** | min(80% x rated, best sustained August run of 3 h+) over 15 runs; 2 run(s) discarded as clock errors — above 120% of rating |
| 6 Head | 3L | — | 11–820 | 415 | 820 | 2 (2) | **—** | NO RATE — needs a ruling (the 2 usable August run(s) are too few to be a typical rate); 1 run(s) discarded as clock errors — above 120% of this line's best rated litres/hour |
| 6 Head | 2L | 720 | 53–678 | 625 | 678 | 5 (3) | **576** | min(80% x rated, best sustained August run of 3 h+) over 5 runs |
| 6 Head | 1L | 1,080 | 373–810 | 424 | 810 | 4 (3) | **810** | min(80% x rated, best sustained August run of 3 h+) over 4 runs; 2 run(s) discarded as clock errors — above 120% of rating |
| Tin Head | 15L | 240 | 56–215 | 130 | 215 | 3 (3) | **192** | min(80% x rated, best sustained August run of 3 h+) over 3 runs |
| Tin Head | 3L | — | — | — | — | 0 (0) | **192** | DERIVED: same tins-per-hour as 15 L (A05) |
| Tin Head | 5L | — | — | — | — | 0 (0) | **192** | DERIVED: same tins-per-hour as 15 L (A05) |
| Pouch Machine | POUCH | 4,200 | 243–1,982 | 1,346 | 1,982 | 6 (6) | **1,982** | min(80% x rated, best sustained August run of 3 h+) over 6 runs |

### The same lines when the piece is a COMBO SET (B19)

A set of two bottles is not a two-litre pack and it is not a plain one-litre run either. These blocks are the line's own record of filling combos, in bottles per hour; a line absent from this table has no combo rate, so a combo cannot be scheduled on it.

| Line | Pack | App rated | Aug range | Aug typical (3 h+) | Aug best | Aug runs (3 h+) | **Planning** | Basis |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Clear Pack | 1L combo | 4,800 | 87–1,277 | 1,132 | 1,277 | 6 (6) | **1,277** | min(80% x rated, best sustained August run of 3 h+) over 6 runs |

## Which pack and bottle goes on which line (1 = first choice, 2 = when 1 is full, 3 = last resort)

| Line | Pack | Bottle family → preference | August litres | of which combo |
|---|---|---|---:|---:|
| JP Machine | 1L | 26G → 1, ROUND-23.8G → 1, SMALL → 1, 52G → 3 | 324,956 | 0 |
| Clear Pack | 1L | 40G → 1, 52G → 2 | 131,263 | 54,136 |
| Clear Pack | 2L | ANY → 2 | 0 | 0 |
| Clear Pack | 4L | ANY → 2 | 0 | 0 |
| Clear Pack | 5L | HDPE → 1 | 284,060 | 0 |
| 10 Head | 1L | 52G → 1, 75G → 1, SMALL → 2, 40G → 2, 26G → 3, ROUND-23.8G → 3 | 284,115 | 0 |
| 10 Head | 2L | ANY → 1 | 0 | 0 |
| 10 Head | 3L | HDPE → 2 | 0 | 0 |
| 10 Head | 5L | HDPE → 3 | 0 | 0 |
| 6 Head | 5L | HDPE → 1, TIN → 1 | 200,120 | 0 |
| 6 Head | 3L | HDPE → 1, TIN → 2 | 23,886 | 0 |
| 6 Head | 2L | ANY → 2 | 38,086 | 0 |
| 6 Head | 1L | ANY → 3 | 53,936 | 0 |
| Tin Head | 15L | TIN → 1 | 35,955 | 0 |
| Tin Head | 3L | TIN → 1 | 0 | 0 |
| Tin Head | 5L | TIN → 2 | 0 | 0 |
| Pouch Machine | POUCH | ANY → 1 | 52,288 | 0 |

Excluded: **Manual** — app line_id 7 — one DRAFT run ever, never a drum. Out of Mark 4 (Daman 2026-09-06).

## Products whose plan-sheet pack type disagrees with the recipe (recipe wins, R15)

- FG0000191 SOYABEAN OIL 15 LTR — sheet says PET, recipe uses TIN 15 LTR
- FG0000015 REFINED OIL 15 LTR — sheet says PET, recipe uses TIN 15 LTR
- FG0000275 COLD PRESS SUNFLOWER OIL 15 LTR — sheet says PET, recipe uses TIN 15 LTR
- FG0000232 SO OLIVE OIL 5 LTR 4 PCS — sheet says PET, recipe uses TIN 5 LTR SO OLIVE PRINTED
- FG0000132 RICE BRAN OIL 15 LTR — sheet says PET, recipe uses TIN 15 LTR
- FG0000158 REFINED COTTON SEED OIL 15 LTR — sheet says PET, recipe uses TIN 15 LTR
- FG0000367 SANO POMACE OLIVE OIL 15 L — sheet says PET, recipe uses TIN 15 LTR
- FG0000026 MUSTARD KACCHI GHANI 15 LTR — sheet says PET, recipe uses TIN 15 LTR

## Products Mark 4 moves to a different machine than Mark 3 does

The first two columns are the engine's own buckets, where every tin is one 'TIN'. The last two are what the recipe says the line actually fills. Every row here is a Mark 3 misplacement.

| Code | Product | Engine bucket, before | after | Mark 4 pack | Bottle | Fills per piece |
|---|---|---|---|---|---|---:|
| FG0000015 | REFINED OIL 15 LTR | 15L | TIN | 15L | TIN | 1 |
| FG0000026 | MUSTARD KACCHI GHANI 15 LTR | 15L | TIN | 15L | TIN | 1 |
| FG0000033 | COLD PRESS 1 LTR + 1 LTR COMBO 10 SET | 2L | 1L | 1L | 40G | 2 |
| FG0000088 | COLD PRESS 1 LTR +1 LTR COMBO 10 SET PLAIN | 2L | 1L | 1L | 40G | 2 |
| FG0000091 | COLD PRESS SUNFLOWER 1 LTR +1 LTR COMBO 10 SET PLAIN | 2L | 1L | 1L | 40G | 2 |
| FG0000132 | RICE BRAN OIL 15 LTR | 15L | TIN | 15L | TIN | 1 |
| FG0000158 | REFINED COTTON SEED OIL 15 LTR | 15L | TIN | 15L | TIN | 1 |
| FG0000191 | SOYABEAN OIL 15 LTR | 15L | TIN | 15L | TIN | 1 |
| FG0000232 | SO OLIVE OIL 5 LTR 4 PCS | 5L | TIN | 5L | TIN | 1 |
| FG0000275 | COLD PRESS SUNFLOWER OIL 15 LTR | 15L | TIN | 15L | TIN | 1 |
| FG0000367 | SANO POMACE OLIVE OIL 15 L | 15L | TIN | 15L | TIN | 1 |
| FG0000429 | MUSTARD KACHI GHANI 1 LTR + 1 LTR COMBO 10 SET PLAIN | 2L | 1L | 1L | 40G | 2 |

## Acceptance checks (Proof runs these)

- AC01 No run of a TIN item on any line except Tin Head, and 5 L / 3 L tins on the 6 Head.
- AC02 No 15L slot on Clear Pack, 10 Head or 6 Head. No 3L on Clear Pack. No POUCH outside Pouch Machine. No DRUM scheduled anywhere.
- AC03 The three drum SKUs appear in the plan output as manual/not-scheduled and never in a 'stuck: no machine' list.
- AC04 Every line ≤ 10 h on any day; at most ONE line per day up to 20 h; Sundays 0 production hours; the night line is named per day.
- AC05 lines.json publishes per line-slot: rated, aug_median, aug_best, planning, basis; planning equals the A01 rule.
- AC06 Pack class of every plan SKU equals the BOM container (R15): the 7 '15 LTR' rows + FG0000232 are TIN.
- AC07 Bottle-family eligibility holds in every run: no 75G/26G on Clear Pack; no 40G/75G on JP; JP 1 L runs are 26G/ROUND/SMALL or 52G.
- AC08 Forecast rows triple-tagged; demand baseline published with months, source, channel filter, exclusions; its totals reconcile to the source within 0.5%.
- AC09 overview.json carries ₹ made today, target, floor, per-line strip, dispatch pendency and lag median/p90 with basis; 'trucks left today' is not a headline.
- AC10 assumptions.json lists every R* and A* id from this rulebook and every open question; the site's /assumptions renders them; check:numbers and the phone-mask scan pass.
- AC11 gen_live.py cross-checks pass (all existing + new); `next build` passes; fixtures synced; every existing Mark 3 route still renders.
- AC12 The offline chain (freeze_live → august_sim → gen_live) runs on the committed fixtures with rc=0 and the plan shows the rulebook in effect (spot-check: Soyabean 15 L on Tin Head; Cold Press 3 L on 6 Head or 10 Head; Kachi Ghani 1 L on JP).
