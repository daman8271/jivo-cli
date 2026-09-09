# Iteration 2 — original demand sources

Verified 6 September 2026, 06:32–06:34 IST. High confidence in the measured subtotals and source field arithmetic; OMS total coverage is explicitly partial because five active orders have unreadable lines/company. This report supersedes the old plan-net headline as a description of the gross order book. The sanitized evidence JSON is `site-mark4/data/iteration-2-demand-evidence.json`; raw responses stay private on the isolated VPS.

## Measured book and reconciliation

| Metric | Live result | Basis |
|---|---:|---|
| Online requested open gross | 1,139,613.29 L | All creation months; ordered/requested less delivered; expired dates excluded |
| Amazon requested open | 737,022.29 L / 113 POs | Original pending Amazon lines |
| Quick commerce requested open | 402,591.00 L | Original OPEN master_po lines |
| Amazon accepted remaining | 642,846.29 L | Accepted less received, independently reconciled against source litres |
| Total accepted eligible book | 1,045,437.29 L | Accepted Amazon plus quick commerce residual |
| Requested but not accepted | 94,176.00 L | Separate bridge, not silently treated as expiry/cancellation |
| Requested due this calendar month | 1,068,513.29 L | Delivery date else expiry; never creation date |
| Later due requested | 71,100.00 L | Remains in all-month gross; excluded this month's make |
| Expired excluded | 42,720.00 L | expiry before source business date; expiry today remains eligible |
| All-platform prior creation month | 817,103.64 L / 208 POs | Original creation date, all platforms |
| Amazon-only prior creation month | 658,257.84 L / 87 POs | This is the scope of Mark3's previous-month badge |
| Known Oil OMS open subtotal | 48,172.40 L / 14 orders | Header company=1 AND item category=OIL |
| Unknown active OMS orders | 5 | Status known; company/items/litres unknown, not zero |

Mark3's screenshot was still showing online 1,140,657 L and Amazon 738,066 L. A fresh source read is approximately 1,044 L lower, entirely in Amazon. Do not force the new feed to match a cached screenshot. Platforms unchanged: Swiggy 209,218 L/146 PO; Flipkart Grocery 59,812/20; Blinkit 51,372/120; Zepto 49,130/45; Big Basket 27,942/6; Zomato 5,117/6. Total online PO count is 456.

The old 1,059,304 L Mark4 figure described net manufacture, not this all-month gross book. These must be separate, with a bridge through accepted policy, due scope, SKU mapping, finished-stock cover and production constraints.

## Exact line truth and remaining limitations

Amazon exposes requested_qty, accepted_qty, received_qty and numeric per_liter; its remaining_ltrs matches accepted minus delivered, while Mark3 gross used requested minus delivered. The choice to schedule accepted Amazon quantities is an explicit conservative policy, not proof that the unaccepted 94,176 L was cancelled. Both amounts remain visible.

Quick commerce residual is order_qty minus delivered_qty; litres independently reconcile with total_order_liters minus total_delivered_liters. Numeric `per_liter` is the conversion; `per_ltr_unit` is a text description and cannot be multiplied. Zero quantity-to-litres mismatches were found. Ninety-eight nonzero-quantity lines have no positive litres conversion:44 are explicitly OTHER,39 BEVERAGE,15 have no classification. They are counted without invented litre conversions. The15 unclassified lines are an unresolved coverage gap; their0 source litres is not proof of zero Oil demand.

Exact SKU mapping uses Amazon sap_sku_code or a unique `(platform, original platform sku_code)` join to the product master. Names are never matching keys. 16,169.60 L of raw gross lacks a unique mapping and remains explicitly unmapped. Explicit BEVERAGE/OTHER lines retain their 899.09 L requested / 874.09 L accepted in all-platform gross, but are excluded from Oil machine demand. Separate all-month and planning-due outside-Oil fields prevent subtracting next-month amounts from this month.

Original dates and original line identity are retained. Delivery takes precedence over expiry. Without either, due is blank and the line is undated; creation is not manufactured into a delivery deadline. Overdue unexpired orders remain actionable; later-month orders remain in gross. Current-month and overdue buckets overlap, so `planningDueLitres` is the non-overlapping total due by month end.

OMS detail exposes full ordered qty/ltrs but no delivered quantity. The 48,172.40 L is therefore a gross ordered subtotal on current nonterminal orders, not a proved net remaining delivery obligation. ₹ values are not asserted as ex-GST for OMS. Online source exclusive-amount residual is ₹219,532,455.91 for the requested book, not an accepted-basis valuation.

## OMS completeness investigation

A complete numeric ID discovery read 1–3180: 2773 detail records, 402 absent, five errors. The last twelve IDs, 3169–3180, were absent. This is a literal observed frontier, not a claim that arbitrary large gaps can never exist.

All 76 current account users' `orders by-user` lists were then read fresh. Their union contains 2778 headers, highest ID3168, including every detail record and the five unreadable records. Twenty-three headers are nonterminal; eighteen details are readable. Fresh statuses expose 2444 COMPLETED, 264 REJECTED, 47 BILLING_REJECTED, and 23 active headers. The previous Mark3 cached set of 49 open orders contained 30 now COMPLETED and 10 now REJECTED. Its 406,421.5 L/49 was not the current company-scoped book. Outside Oil: known other-company open volume 24,160 L; Oil-company other-category lines 6,045 L, excluded from Oil demand.

Five source detail endpoints fail: IDs1683,1684,1685,1708,1709; API error is `AttributeError: 'NoneType' object has no attribute 'category'`. Supported by-user headers prove all five are Order Created, dated 2–3 July. Headers do not expose company or items. Public output includes hashed IDs, status, creation date and `litres:null`; `unknownActiveOrderCount=5`, `isComplete=false`, global coverage partial. They cannot be guessed away.

Alternative raw Postgres access was attempted after CLI-hub discovery, through both MCP and native CLI. Both returned SQLSTATE28P01 authentication failure. No authenticated alternate SQL route was available. Recovering these five orders requires a working raw database read or repair of the OMS serializer/category relation. This is the only known active-order quantity gap from the full observed header scope.

## Sustainable independent collector

Owned new scripts: `site-mark4/scripts/demand_source.py`, `collect_demand.py`, and `test_demand_source.py`. Existing Mark3 collector, cache and service are untouched.

Every cycle: proactively renew isolated source logins when JWT has less than ten minutes left; fully paginate three ecom feeds; read all account-user headers; refresh every active/unknown detail; probe a twelve-absent new-ID frontier. A dated full numeric discovery runs every24h as a backstop. Current regular-cycle work is roughly76 header reads +23 details +12 frontier reads, not3180 detail calls every3min. Raw account-user data is reduced to IDs immediately; password hashes, names and contacts are never cached by this helper.

Initial exact recurring command (parent owns systemd installation):

```sh
cd /root/mark4-astha/app
python3 scripts/collect_demand.py \
  --raw-dir /root/mark4-astha/demand-audit \
  --out /root/mark4-astha/state/demand-supplement.json \
  --ecom-bin /root/jivo-courier/ecom-cli/jivo-ecom-pp-cli.linux \
  --ecom-config /root/mark4-astha/demand-audit/ecom.toml \
  --oms-bin /root/jivo-courier/oms-cli/oms-pp-cli.linux \
  --oms-config /root/mark4-astha/demand-audit/oms.toml \
  --oms-frontier 3168 \
  --auth-env /root/mark4-astha/demand-audit/auth.env
```

Credentials and raw files are private0600 under the isolated0700 directory. Login receives credentials through environment variables, never command arguments or logs; configs are dedicated to Mark4. Forced renewal with separate temporary configs succeeded for both ecom and the dedicated OMS account. No production credential files were modified.

Output envelope: `{asOf,attemptedAt,ok,error,data:{asOf,demandBook,orders,items}}`. A successful partial source read publishes the measured subtotal with ok:false and a specific incomplete-coverage message. Failure to refresh the source retains last-good data and its ORIGINAL source clock, with a new attemptedAt. A process lock prevents overlapping refreshes. All raw CLI output/errors stay out of public output.

## Verification

Sixteen focused normalizer tests passed, including identity-collision and planner-conflict regression cases. The initial nine cover: requested/accepted bridge, expiry, future due, undated creation, outside-Oil due quantities, null item-ID uniqueness, wrong-company exclusion, partial active headers with original source clock, and missing header identity refusal. Live full-header cycle completed in about27s before the additional frontier probe; measured totals reconciled to the prior fresh audit. Parent verifies the public merger, planner and screens separately.


## Release blocker found and corrected: SKU namespace identity

The original ecom product master uses codes that can contradict factory product identities. Multiplying source pieces by an inherited planner pack inflated mapped demand to2.786millionL. Two independently verified examples: ecom FG0000328 means Yellow Mustard1L while current factory FG0000328 means Sano Pomace200L; ecom FG0000275 is a2L mustard sales unit while current factory0275 means cold-press sunflower15L. Source quantities themselves reconcile; blindly interpreting their codes as factory codes is the error. Same-size different-oil identities also require checking, not just the litre ratio. FG0000005 current factory is Extra Light1L16PCS, so an inherited Pomace label is stale and cannot overrule the live catalog.

Factory supplied371 current OilFG identities from ten bounded prefix queries, each below the endpoint cap. The dated factory catalog and the actual planner identity snapshot are separate inputs. Every exact ecom and OMS line now carries sourceProductName, sourceSkuCode, sourcePackLitres, code_mapping_verified, mappingStatus, mappingReason and mappingIssue. Verification requires original product name and numeric unit to agree with both current factory and planner identities. Only the explicitly approved16→20 carton transition is normalized; arbitrary carton counts and product-grade words remain significant. Sales bundles are never rescaled into a different factory product. Factory COMBO/SET names do not acquire their first litre number as a manufactured piece size.

Final candidate has1849 verified original rows totalling818,041.70L across all months, plus530 held rows totalling274,693.90L. These are accepted eligible row totals including the known trade subtotal, not a new requested gross headline. Six current-factory-versus-planner identity differences are emitted as dated `identityConflicts` to hold affected forecast, finished-stock cover and valuation. The engine independently checks the live factory identity against its actual product/BOM model, so source verification cannot silently validate a stale recipe.

Factory identity refresh is owned by the separate factory collector (12h cadence via `--identity-output`), and the demand normalizer accepts it only when coverage is complete within the specified range, ok is not false, and source age is within24h. Reusing a catalog never stamps it as newly read. The parent owns installing the latest collector/service args and promoting the final candidate after integration verification.

The collector refreshes the planner identity reference every cycle from `--planner-inputs` (default `/root/jivo-courier/jolly/sim/live-inputs.json`). Plan SKU names/pack sizes override inherited generic item labels for this comparison. The reference retains the input source `state_collected_at` clock; reading the file does not make it newly fetched. CLI calls clear inherited token override variables so dedicated config scope cannot silently change.
