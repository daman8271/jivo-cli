# ADVERSARIAL REFUTATION — `study-platform-reports-new.md`

Refuter run: 2026-08-22, same day as the study. READ-ONLY: every request below is a
GET. No non-GET verb was issued. No parameter value was sent that was not observed
in a live payload, in `GET /api/auth/me`, or in the app's own bundle source.

Token: live (200 on `/api/auth/me`). Bundle: `/root/.handoff-runs/rescrape-all/scratch/ecom/bundle/`.

Shell convention:
```bash
T=$(cat /root/.handoff-runs/rescrape-all/scratch/.ecom_token)   # never printed
B=/root/.handoff-runs/rescrape-all/scratch/ecom/bundle
```

## Scoreboard

| | count |
|---|---|
| claims attacked | 34 |
| CONFIRMED (tried to break, could not) | 26 |
| **REFUTED / materially wrong** | **5** |
| UPGRADED (study said NOT VERIFIED, refuter verified) | 1 |
| UNTESTABLE / not tested by policy | 6 |

---

# A. REFUTED CLAIMS

---

## R-1 — "46 metrics" is wrong. There are **40**. (REFUTED)

**Claim (study, Part A §4, three places):** *"The 46-metric health card…"*,
*"`by_fc[]` … and `by_channel[]` … carry the **exact same 46 metrics** plus a
`fc`/`channel` key"*, and Part E: *"Three output sections … sharing one 46-metric
schema"*.

**Command:**
```bash
curl -s -H "Authorization: Bearer $T" \
  'https://ecom.jivo.in/api/reports/amazon-po/sku-pendency/summary' -o sp-summary.json
python3 -c "
import json; s=json.load(open('sp-summary.json'))
print('n metrics in total:', len(s['total']))
print('by_fc keys minus total keys:', sorted(set(s['by_fc'][0])-set(s['total'])))
print('total keys minus by_fc keys:', sorted(set(s['total'])-set(s['by_fc'][0])))"
```

**Output:**
```
n metrics in total: 40
by_fc keys minus total keys: ['fc']
total keys minus by_fc keys: []
```

**Truth:** `total` has exactly **40** keys. The three-section shared-schema claim is
correct; the arity is not. A CLI table/struct sized to 46 columns is wrong.

Also, the study's field table **omits three real fields** that are in the payload:
`order_ltrs` (560895.6), `accepted_ltrs` (547332.6), `delivered_ltrs` (117445.0).
(`order_ltrs` is used later in T-9 but never introduced.)

---

## R-2 — `pending_value` is NOT "×1.05". The multiplier is **per-SKU tax rate**, and the "unexplained" residual IS explained: aerated beverages are **×1.40**. (REFUTED)

**Claim (study T-2 / Part C):** *"`overall-pendency.pending_value` is GST-inclusive
… 1.05 × the pre-tax value"*, *"The 1.05 factor matches India's 5% GST on edible
oil"*, and *"Two platforms come out marginally above 1.05 (swiggy 1.050014,
bigbasket 1.050813) — a mix effect or a per-line rounding, **not fully explained;
flagged NOT VERIFIED as to cause**"*. Carried verbatim into the shipped spec's
`overall-pendency` description: *"pending_value here is GST-INCLUSIVE and is ~1.05x
the pre-tax order_value"*.

**Command:** join `pendency-dashboard.by_sku[].order_value` to
`overall-pendency.rows[].pending_value` **per SKU**, not in aggregate:
```bash
for s in swiggy zepto blinkit bigbasket flipkart_grocery citymall zomato; do
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/$s/pendency-dashboard?scope=all" -o pd-$s.json
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/overall-pendency?platforms=$s" -o op-$s.json
done
python3 -c "
import json, collections
buckets=collections.Counter(); detail=[]
for s in 'swiggy zepto blinkit bigbasket flipkart_grocery zomato'.split():
    pd=json.load(open('pd-%s.json'%s)); op=json.load(open('op-%s.json'%s))
    opm={r['label']:r['pending_value'] for r in op['rows']}
    pdm=collections.defaultdict(float)
    for r in pd['by_sku']: pdm[r['item']] += (r.get('order_value') or 0)
    bev=0.0
    for k,v in pdm.items():
        pv=opm.get(k)
        if pv is None or not v: continue
        buckets[round(pv/v,2)]+=1
        if round(pv/v,2)!=1.05: bev += pv-1.05*v; detail.append((s,k,round(pv/v,4),round(v,2)))
    tp=sum(pdm.values()); to=op['totals']['pending_value']
    print(f'{s:18s} resid_vs_1.05={to-1.05*tp:10.2f}  explained_by_non105={bev:10.2f}  leftover={to-1.05*tp-bev:7.2f}')
print('ratio buckets:', dict(buckets)); [print('  ',d) for d in detail]"
```

**Output:**
```
swiggy             resid_vs_1.05=    961.92  explained_by_non105=    960.08  leftover=   1.84
zepto              resid_vs_1.05=     -0.00  explained_by_non105=      0.00  leftover=  -0.00
blinkit            resid_vs_1.05=     -1.57  explained_by_non105=      0.00  leftover=  -1.57
bigbasket          resid_vs_1.05=   9499.52  explained_by_non105=   9294.11  leftover= 205.41
flipkart_grocery   resid_vs_1.05=      0.00  explained_by_non105=      0.00  leftover=   0.00
zomato             resid_vs_1.05=     -0.84  explained_by_non105=      0.00  leftover=  -0.84
ratio buckets: {1.05: 91, 1.4: 4}
   ('swiggy',    'SODA LEMON 750 ML', 1.3999,  2743.92)
   ('bigbasket', 'WATER PEACH 750ML', 1.4,    11573.80)
   ('bigbasket', 'LEMON 750ML',       1.4,    11304.12)
   ('bigbasket', 'TONIC WATER 200ML', 1.4001,  3673.92)
```

Per-SKU detail, bigbasket (units agree exactly, so it is a rate difference, not a
quantity difference):
```
item                       pd_units  op_units  resid_vs_1.05  implied_rate
WATER PEACH 750ML               418       418        4051.17      1.400029
LEMON 750ML                     408       408        3956.87      1.400038
TONIC WATER 200ML                96        96        1286.06      1.400052
MUSTARD 1L                    16363     16363         162.75      1.050060   <- rounding
```

**Truth:** `pending_value = order_value × (1 + the SKU's own tax rate)`. Observed
rates today: **1.05** on all 91 oil / still-juice SKU rows, **1.40** on all 4 carbonated /
aerated beverage SKU rows (28% GST + 12% compensation cess). Those four SKUs
account for 9,294 of bigbasket's 9,500 residual and 960 of swiggy's 962; the
remaining ≤0.002% is per-line rounding.

**What a CLI must say instead of "×1.05":** *"`pending_value` is tax-inclusive at
each SKU's own rate (1.05 on edible oil, 1.40 on aerated beverages); it is NOT a
flat 5% uplift on `order_value` and must never be back-converted by dividing by
1.05."* The spec description must be corrected — a user dividing a
beverage-heavy `pending_value` by 1.05 gets a number that is 33% too high.

---

## R-3 — The null-percentage gotcha is far broader than the `"-"` channel. (REFUTED as scoped)

**Claim (study Part A §4):** *"⚠ `\"-\"` channel gotcha: its `fill_rate_pct` is
`null`, not `0`. Any CLI that formats percentages must survive nulls in
`by_channel`."* Part E repeats: *"Tolerate `null` in `by_channel` (the `\"-\"`
channel)."*

**Command:**
```bash
python3 -c "
import json; s=json.load(open('sp-summary.json'))
for c in s['by_channel']: print('ch', c['channel'], 'nulls=', [k for k,v in c.items() if v is None])
for c in s['by_fc']:
    n=[k for k,v in c.items() if v is None]
    if n: print('fc', c['fc'], 'nulls=', n)"
```

**Output:**
```
ch CORE nulls= []
ch NOW nulls= []
ch FRESH nulls= []
ch - nulls= ['fill_rate_pct', 'cancel_rate_pct', 'invoiced_share_pct', 'uninvoiced_share_pct', 'short_invoice_rate_pct']
fc HBA4 nulls= ['fill_rate_pct', 'cancel_rate_pct', 'invoiced_share_pct', 'uninvoiced_share_pct', 'short_invoice_rate_pct']
fc HCC6 nulls= [... same 5 ...]
fc HMV4 nulls= [... same 5 ...]
fc HAD1 nulls= [... same 5 ...]
fc HKA2 nulls= [... same 5 ...]
```

**Truth:** **5 of the 11 `by_fc` rows** are also null-bearing, and it is **5 fields**,
not one. The nullable set is exactly
`{fill_rate_pct, cancel_rate_pct, invoiced_share_pct, uninvoiced_share_pct,
short_invoice_rate_pct}`. `acceptance_rate_pct` is the only `_pct` field that is
never null. A CLI that only null-guards `by_channel.fill_rate_pct` crashes or
prints garbage on 5 of 11 FC rows.

---

## R-4 — T-3 over-claims: today **only `group_by=category`** yields `MIXED`, not `sub_category`. (REFUTED as stated)

**Claim (T-3):** *"When `group_by` is `category` **or `sub_category`**, a group can
span heads and the row reports `item_head: \"MIXED\"`."*

**Command:**
```bash
for g in item category sub_category; do
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/overall-pendency?group_by=$g" -o x.json
  python3 -c "
import json; d=json.load(open('x.json'))
print(f\"group_by=$g groups={d['totals']['groups']} row0={d['rows'][0]['label']!r} heads={sorted(set(r['item_head'] for r in d['rows']))}\")"
done
```

**Output:**
```
group_by=item         groups=81 row0='MUSTARD 1L'             heads=['COMMODITY', 'OTHER', 'PREMIUM']
group_by=category     groups=14 row0='MUSTARD'                heads=['COMMODITY', 'MIXED', 'OTHER', 'PREMIUM']
group_by=sub_category groups=31 row0='MUSTARD KACCHI GHANI'   heads=['COMMODITY', 'OTHER', 'PREMIUM']
```

**Truth:** The mechanism claim is plausible but `sub_category` does **not** produce
`MIXED` in today's data. Only `category` does. The CLI-relevant part (renderer must
accept `MIXED`, flag enum must reject it) is unaffected and still correct.

---

## R-5 — `error` is listed as a response field of `overall-pendency`; the key is **absent**, not null. (REFUTED as documented)

**Claim (study field table):** a row `| \`error\` | inline banner | … a 200 can carry an
error string in the body |`. T-11 repeats it.

**Command:** sweep 8 param combinations:
```bash
for q in "" "?group_by=category" "?group_by=sub_category" "?item_head=PREMIUM" "?item_head=OTHER" \
         "?platforms=amazon" "?platforms=citymall" "?platforms=blinkit,zepto&group_by=category&item_head=PREMIUM"; do
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/overall-pendency$q" -o y.json
  python3 -c "
import json; d=json.load(open('y.json'))
print(f\"q='$q' max_date={d.get('max_date')!r} undated_rows={d.get('undated_rows')!r} has_error_key={'error' in d} min_po={d.get('min_po_date')} max_po={d.get('max_po_date')} nkeys={len(d)}\")"
done
```

**Output (all 8):**
```
q=''                       max_date=None undated_rows=0 has_error_key=False min_po=27-07-2026 max_po=22-08-2026 nkeys=12
q='?group_by=category'     max_date=None undated_rows=0 has_error_key=False min_po=27-07-2026 max_po=22-08-2026 nkeys=12
q='?group_by=sub_category' max_date=None undated_rows=0 has_error_key=False min_po=27-07-2026 max_po=22-08-2026 nkeys=12
q='?item_head=PREMIUM'     max_date=None undated_rows=0 has_error_key=False min_po=28-07-2026 max_po=22-08-2026 nkeys=12
q='?item_head=OTHER'       max_date=None undated_rows=0 has_error_key=False min_po=29-07-2026 max_po=22-08-2026 nkeys=12
q='?platforms=amazon'      max_date=None undated_rows=0 has_error_key=False min_po=28-07-2026 max_po=21-08-2026 nkeys=12
q='?platforms=citymall'    max_date=None undated_rows=0 has_error_key=False min_po=None      max_po=None      nkeys=12
q='?platforms=blinkit,zepto&group_by=category&item_head=PREMIUM'
                           max_date=None undated_rows=0 has_error_key=False min_po=05-08-2026 max_po=22-08-2026 nkeys=12
```

**Truth:** The response has exactly 12 top-level keys and `error` is **not one of
them** in any observed response. The UI's `z.error` is a defensive read of a key the
happy path never emits. The study's field table presents it as a field of the
schema. A CLI's response struct must treat `error` as **optional/absent**, not as a
present-but-null field — and the study should mark this UI-inferred, not observed
(T-11 does; the field table does not).

**Bonus omission found by the same sweep:** `min_po_date` / `max_po_date` are
**nullable** (`platforms=citymall` → both `null`). The study calls them a "useful
freshness stamp for a CLI" without noting they can be null.

---

# B. UPGRADED — study said NOT VERIFIED; refuter verified it

## U-1 — T-9's full line attribution is now **exact**, not "page 0 only"

**Study status:** *"the 9-line / 9-PO coincidence is strong but only **page 0 of the
row report was inspected**, so the full line-by-line attribution is **NOT
VERIFIED**."*

**Command:** pull all 8 pages (`count`=376, `page_size`=50):
```bash
for p in 0 1 2 3 4 5 6 7; do
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/reports/amazon-po/sku-pendency?page=$p" -o rows-p$p.json
done
python3 -c "
import json,glob
res=[r for f in sorted(glob.glob('rows-p*.json')) for r in json.load(open(f))['results']]
blank=[r for r in res if r.get('has_stated_litre') is False]
print('rows collected:', len(res), 'blank-litre lines:', len(blank))
for r in blank: print('  ', r['sku_code'], r['item'], r['item_head'], 'per_liter=',r['per_liter'], 'req=',r['requested_qty'], 'ltr=',r['total_order_liters'], r['po_number'])
op=json.load(open('op-amazon.json'))
o=[r for r in op['rows'] if r['item_head']=='OTHER']
print('op amazon OTHER rows:', [(r['label'], r['open_units'], r['open_ltrs'], r['open_pos']) for r in o])
print('sum open_ltrs', sum(r['open_ltrs'] for r in o), 'sum open_units', sum(r['open_units'] for r in o))"
```

**Output:**
```
rows collected: 376  blank-litre lines: 9
   B0F9YVR47L PUNJABI JEERA 160ML  OTHER per_liter=0.16 req=10.0 ltr=0.0 2WQNS3QO
   B0F9YVR47L PUNJABI JEERA 160ML  OTHER per_liter=0.16 req=10.0 ltr=0.0 6FV15B1E
   B0DM2G4YCC WG MANGO JUICE 200ML OTHER per_liter=0.5  req=48.0 ltr=0.0 7GKHP5MS
   B0DM2G4YCC WG MANGO JUICE 200ML OTHER per_liter=0.5  req=48.0 ltr=0.0 1IFRQ3HB
   B0CSPMN88F WATER 1L             OTHER per_liter=1.0  req=1.0  ltr=0.0 2JUGXZIC
   B0C65W794Z SANO HONEY 1KG       OTHER per_liter=None req=26.0 ltr=0.0 3S1YE9KN
   B0DM2G4YCC WG MANGO JUICE 200ML OTHER per_liter=0.5  req=48.0 ltr=0.0 4YKQI86C
   B0DM2G4YCC WG MANGO JUICE 200ML OTHER per_liter=0.5  req=48.0 ltr=0.0 4VSNHQXE
   B0DM2G4YCC WG MANGO JUICE 200ML OTHER per_liter=0.5  req=96.0 ltr=0.0 4LN3LF9B
op amazon OTHER rows: [('WG MANGO JUICE 200ML',288.0,144.0,5), ('PUNJABI JEERA 160ML',20.0,3.2,2),
                       ('WATER 1L',1.0,1.0,1), ('SANO HONEY 1KG',26.0,0.0,1)]
sum open_ltrs 148.2  sum open_units 335.0
```

**Verdict:** exact, no residual. 9 blank-litre lines across 9 distinct POs; their
`requested_qty` sums to 10+10+48+48+1+26+48+48+96 = **335** = amazon OTHER
`open_units`; recomputed with `per_liter` they give 288×0.5 + 20×0.16 + 1×1.0 + 26×0
= **148.2 L** = the exact `open_ltrs` gap. Also note `SANO HONEY 1KG` has
`per_liter: null` and `overall-pendency` gives it `open_ltrs: 0.0` too — so
`overall-pendency` zeroes on a null `per_liter`, it just ignores
`has_stated_litre: false` when `per_liter` IS populated. T-9 can be moved from
"mechanism VERIFIED, attribution NOT VERIFIED" to **fully VERIFIED**.

---

# C. CONFIRMED (attacked, could not break) — 26

## C-1 · T-5 — `{platform}` ignored on `blinkit-campaigns-optimization`. **CONFIRMED, and hardened.**

The study only compared two slugs. I used the app's own list
(`GET /api/auth/me` → `user.platforms` = 10 slugs) and hit all ten, plus a
refetch to rule out a stale cache producing a false md5 match.

```bash
curl -s -H "Authorization: Bearer $T" 'https://ecom.jivo.in/api/auth/me' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['user']['platforms'])"
# ['amazon','bigbasket','blinkit','citymall','flipkart','flipkart_grocery','jiomart','swiggy','zepto','zomato']

for p in amazon bigbasket blinkit citymall flipkart flipkart_grocery jiomart swiggy zepto zomato; do
  code=$(curl -s -H "Authorization: Bearer $T" \
    "https://ecom.jivo.in/api/platform/$p/blinkit-campaigns-optimization" -o bco-$p.json -w '%{http_code}')
  printf '%-18s %s %10s %s\n' "$p" "$code" "$(stat -c%s bco-$p.json)" "$(md5sum bco-$p.json|cut -c1-32)"
done
```
```
amazon             200    2747172 14c4833a54a77b03bb09e376dd4e01b9
bigbasket          200    2747172 14c4833a54a77b03bb09e376dd4e01b9
blinkit            200    2747172 14c4833a54a77b03bb09e376dd4e01b9
citymall           200    2747172 14c4833a54a77b03bb09e376dd4e01b9
flipkart           200    2747172 14c4833a54a77b03bb09e376dd4e01b9
flipkart_grocery   200    2747172 14c4833a54a77b03bb09e376dd4e01b9
jiomart            200    2747172 14c4833a54a77b03bb09e376dd4e01b9
swiggy             200    2747172 14c4833a54a77b03bb09e376dd4e01b9
zepto              200    2747172 14c4833a54a77b03bb09e376dd4e01b9
zomato             200    2747172 14c4833a54a77b03bb09e376dd4e01b9
# refetch of blinkit -> same md5, so this is not a per-request cache artefact
```
Ten for ten, byte-identical, 2,747,172 bytes. Not refutable. The study's md5 was
also reproduced exactly (`14c4833a…`), i.e. the payload is stable across ~1 hour.

## C-2 · `blinkit-sale-target` rejects non-blinkit slugs with 400. **CONFIRMED.** (The T-5/§3 "tension" the brief flagged resolves cleanly: two different endpoints, one validates, one does not.)

```bash
for p in amazon bigbasket blinkit citymall flipkart flipkart_grocery jiomart swiggy zepto zomato; do
  code=$(curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/$p/blinkit-sale-target" -o bst-$p.json -w '%{http_code}')
  printf '%-18s %s %6s %s\n' "$p" "$code" "$(stat -c%s bst-$p.json)" "$(head -c 60 bst-$p.json)"
done
```
```
amazon             400  48 ["Sale & Target is available only for Blinkit."]
bigbasket          400  48 ["Sale & Target is available only for Blinkit."]
blinkit            200 9626 {"slug":"blinkit","as_on":"2026-08-21",...
citymall           400  48 ["Sale & Target is available only for Blinkit."]
flipkart           400  48 ["Sale & Target is available only for Blinkit."]
flipkart_grocery   400  48 ["Sale & Target is available only for Blinkit."]
jiomart            400  48 ["Sale & Target is available only for Blinkit."]
swiggy             400  48 ["Sale & Target is available only for Blinkit."]
zepto              400  48 ["Sale & Target is available only for Blinkit."]
zomato             400  48 ["Sale & Target is available only for Blinkit."]
```
9 of 9 non-blinkit slugs rejected. Error body is a bare JSON **array of strings**,
not an object — a CLI error decoder must handle that shape.

## C-3 · T-1 — `open_units` = ORDERED, `pending_units` = ordered − received; identical on all q-commerce, ~26% apart on amazon. **CONFIRMED.**

```bash
for s in amazon swiggy zepto blinkit bigbasket flipkart_grocery citymall zomato; do
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/overall-pendency?platforms=$s" -o op-$s.json
done
```
```
platform             open_units pending_units   ratio open_pos   rows groups
amazon                   252536        200064  1.2623       56    496     57
swiggy                   350601        350601  1.0000      223   1270     33
zepto                     92944         92944  1.0000       68    301     14
blinkit                   25188         25188  1.0000      114    447     12
bigbasket                 53816         53816  1.0000       13    150     24
flipkart_grocery          41564         41564  1.0000       18     26      3
citymall                      0             0     n/a        0      0      0
zomato                     4174          4174  1.0000        7     26      9
```
Cross-check against the Amazon summary: `open_units` 252,536 == `requested_units`
252,536; `pending_units` 200,064 == 252,536 − 52,472 (`received_units`). Both exact.
Amazon divergence is **+26.23%**, matching the study's "~26%".

## C-4 · T-4 — `open_pos` is a distinct count, not summable across rows. **CONFIRMED exactly.**
```bash
python3 -c "
import json; d=json.load(open('op-bare.json'))
print('totals.open_pos       =', d['totals']['open_pos'])
print('sum(rows[].open_pos)  =', sum(r['open_pos'] for r in d['rows']))
print('sum(by_head[].open_pos)=', sum(h['open_pos'] for h in d['by_head']))
print('totals.rows           =', d['totals']['rows'])
print('sum(rows[].pending_units) =', sum(r['pending_units'] for r in d['rows']))
print('sum(rows[].platforms[].open_pos) =', sum(p['open_pos'] for r in d['rows'] for p in r['platforms']))"
```
```
totals.open_pos       = 499
sum(rows[].open_pos)  = 2716        <- equals totals.rows, i.e. the PO-line count
sum(by_head[].open_pos)= 866
totals.rows           = 2716
sum(rows[].pending_units) = 768351.0   <- units DO sum
sum(rows[].platforms[].open_pos) = 2716
```
The nested `platforms[].open_pos` double-counts the same way — the study did not
check that level; it behaves identically. **`open_pos` IS summable across
platform-filtered *calls*** (the 8 per-platform pulls sum to exactly 499), because a
PO belongs to one platform. Only intra-response row/head summation is wrong.

## C-5 · summary takes **zero** parameters; `fulfillment_center` / `channel` silently ignored. **CONFIRMED, and hardened** by proving the sibling row report *does* honour them.
```bash
for q in "" "?fulfillment_center=DED5" "?channel=CORE" "?fulfillment_center=DED5&channel=CORE"; do
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/reports/amazon-po/sku-pendency/summary$q" -o s.json -w "%{http_code} %{size_download} "
  echo "$(md5sum s.json|cut -c1-32)  q='$q'"; done
for q in "" "?fulfillment_center=DED5" "?channel=CORE"; do
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/reports/amazon-po/sku-pendency$q" -o r.json -w "%{http_code} %{size_download} "
  python3 -c "import json;d=json.load(open('r.json'));print('count=',d['count'],'q=\"$q\"')"; done
```
```
200 15254 7e848b7f01e717d0a822a43aae4f0b22  q=''
200 15254 7e848b7f01e717d0a822a43aae4f0b22  q='?fulfillment_center=DED5'
200 15254 7e848b7f01e717d0a822a43aae4f0b22  q='?channel=CORE'
200 15254 7e848b7f01e717d0a822a43aae4f0b22  q='?fulfillment_center=DED5&channel=CORE'   <- also ignored in combination
--- row report ---
200 42252 count= 376 q=""
200 46747 count= 133 q="?fulfillment_center=DED5"
200 44687 count= 227 q="?channel=CORE"
```
Both values are observed (`DED5` from this endpoint's own `by_fc[].fc`, `CORE` from
its own `by_channel[].channel`); both param names come from `SPDashboard`'s
`onOpen` handlers (`grep -oE '(fulfillment_center|channel):[a-zA-Z0-9_.\`]{1,30}' $B/SPDashboard-BHa8jXNE.js`
→ `channel:e`, `fulfillment_center:e`). The summary is byte-identical in all four
cases while the row report's count moves 376 → 133 / 227. **The "no flags" CLI
recommendation is correct.**

## C-6 · T-7 — summary `open_units` == row report `remaining_qty`, **not** `open_qty`. **CONFIRMED exactly.**
```
summary.open_units   170071.0 == rows.totals.remaining_qty 170071.0   True
summary.open_ltrs    373170.6 == rows.totals.remaining_ltrs 373170.6  True
rows.totals.open_qty 156234.0 -> matching summary field: []   (none)
rows.totals.open_ltrs 357851.6 -> matching summary field: []  (none)
summary.remaining_units 192812.0  summary.remaining_ltrs 429887.6
```
All six numbers in the study's T-7 table reproduce to the digit.

## C-7 · T-7b — "Remaining Qty" / "Remaining QTY" label collision. **CONFIRMED.**
```bash
grep -oE '\{key:`(remaining_qty|remaining_ltrs|invoiced_short_qty|invoiced_short_ltrs|open_qty|open_ltrs)`,label:`[^`]+`' $B/SkuPoPendency-mBzq5vij.js
```
```
{key:`remaining_qty`,label:`Remaining Qty`
{key:`remaining_ltrs`,label:`Remaining LTR`
{key:`invoiced_short_qty`,label:`Remaining QTY`
{key:`open_qty`,label:`Open QTY`
{key:`invoiced_short_ltrs`,label:`Remaining LTR`
{key:`open_ltrs`,label:`Open LTR`
```
`remaining_ltrs` and `invoiced_short_ltrs` collide **exactly** ("Remaining LTR");
`remaining_qty` / `invoiced_short_qty` differ only by case.

## C-8 · T-6 — `growth_pct` is caller-chosen, `= projection_ltr / closes[newest selected] − 1`. **CONFIRMED, and extended.**
```bash
for cm in 2026-07 2026-02 none 2026-02,2026-07 2025-08 2026-07,2026-06; do
  curl -s -H "Authorization: Bearer $T" \
    "https://ecom.jivo.in/api/platform/blinkit/blinkit-sale-target?close_months=$cm" -o t.json
  python3 -c "
import json; d=json.load(open('t.json'))['targets']; g=d['grand_total']
print(f\"cm='$cm' selected={[c['key'] for c in d['close_months']]} prev={d['prev_month_label']!r} closes={g['closes']} growth={g['growth_pct']} proj={round(g['projection_ltr'],4)}\")"
done
```
```
cm='2026-07'         selected=['2026-07'] prev='Jul' closes={'2026-07':115000.0} growth=0.03690186335403722 proj=119243.7143
cm='2026-02'         selected=['2026-02'] prev='Feb' closes={'2026-02': 61828.0} growth=0.928636124178597  proj=119243.7143
cm='none'            selected=[]          prev=None  closes={}                   growth=None               proj=119243.7143
cm='2026-02,2026-07' selected=['2026-07','2026-02'] prev='Jul' closes={'2026-07':115000.0,'2026-02':61828.0} growth=0.03690186335403722 proj=119243.7143
cm='2025-08'         selected=['2025-08'] prev='Aug' closes={'2025-08': 54484.0} growth=1.1886005852307888 proj=119243.7143
cm='2026-07,2026-06' selected=['2026-07','2026-06'] prev='Jul' closes={'2026-07':115000.0,'2026-06':81536.0} growth=0.03690186335403722 proj=119243.7143
```
Arithmetic: 119243.7143/115000−1 = 0.0369019 ✓; /61828−1 = 0.9286361 ✓;
/54484−1 = 1.1886006 ✓. `projection_ltr` is invariant to `close_months` ✓.
**New (not in the study):** the server **sorts** the CSV and picks the max key —
`2026-02,2026-07` yields prev=Jul, not Feb. So "newest selected" means newest by
date, not first in the caller's list.

## C-9 · `blinkit-sale-target` `date` / `compare_date` / `nocache`. **CONFIRMED.**
```bash
for q in "?date=2026-08-15&compare_date=2026-08-14" "?date=2026-07-31" "?nocache=1" "?date=2026-08-21"; do
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/blinkit/blinkit-sale-target$q" -o t.json -w "%{http_code} %{size_download} "; ...; done
```
```
?date=2026-08-15&compare_date=2026-08-14  as_on=2026-08-15 cmp=2026-08-14 max=2026-08-21 Aug-26 elapsed=15 dim=31 editable=True  target=180000 done=58671  ach=0.32595 proj=121253.400
?date=2026-07-31                          as_on=2026-07-31 cmp=2026-07-30 max=2026-08-21 Jul-26 elapsed=31 dim=31 editable=False target=None   done=115000 ach=None    proj=115000.000  cm=[2026-06..2026-01] prev='Jun'
?nocache=1                                as_on=2026-08-21 ... 9626 bytes, md5 identical to bare
?date=2026-08-21                          identical to bare
md5: c4d4b05164db3e368bf2380f71ce54cc  {nocache=1, bare, bare-refetch}   <- all three
```
Projection formula holds at a second data point: 58671/15×31 = **121253.4** ✓ (study
only checked 80778/21×31). `date=2026-07-31` reproduces the closed-month behaviour
exactly: `editable=false`, `target_ltr=null`, `achieved_pct=null`, `close_months`
shifts back one month, `prev_month_label` → "Jun". `compare_date` server-defaults
to `date − 1 day` even when `date` is supplied alone. `achieved_pct` = 80778/180000
= 0.4487667 ✓ (fraction).

## C-10 · `blinkit-campaigns-optimization` `from`/`to` narrow server-side; no page/limit; no section selector. **CONFIRMED.**
```bash
for r in "from=2026-08-01&to=2026-08-05" "from=2026-08-01" "to=2026-08-31" "from=2026-03-01&to=2026-08-31"; do ... ; done
```
```
200  742811  cov={'from':'2026-08-01','to':'2026-08-05',...} pb=3526  bf=1591  ra=295  sku=13 mom=0 mtd=0
200 2747172  cov={'from':'2026-08-01','to':'2026-08-31',...} pb=12800 bf=6782  ra=1058 sku=13 mom=0 mtd=0
200 2747172  cov={'from':'2026-08-01','to':'2026-08-31',...} pb=12800 bf=6782  ra=1058 sku=13 mom=0 mtd=0
200 9955787  cov={'from':'2026-03-01','to':'2026-08-31',...} pb=35511 bf=46711 ra=2250 sku=13 mom=0 mtd=0
```
Byte counts reproduce the study's exactly. **New:** `from` and `to` default
**independently** — `?from=2026-08-01` alone still returns `to: 2026-08-31`, and
`?to=2026-08-31` alone still returns `from: 2026-08-01`. `skuMaster` is not narrowed.

## C-11 · bare-call default window = the calendar month, and the UI sends it explicitly anyway. **CONFIRMED.**
```bash
grep -oE '.{200}\.get\(be,\{from:.{300}' $B/PlatformBlinkitCampaignsOptimization-B32l52Wb.js
```
```
getMonth()-(Se-1),1)),max:t(new Date(e.getFullYear(),e.getMonth()+1,0)),firstOfMonth:t(new Date(...,e.getMonth(),1))}
 ... m.get(be,{from:u.firstOfMonth,to:u.max}) ...        <- initial load
 ... m.get(be,{from:N,to:u.max}) ...                     <- widening load
```
`u.max = new Date(y, m+1, 0)` = **last day of the current month** (not the latest
data date), `u.min = new Date(y, m-5, 1)`, `Se=6`. The study's characterisation is
right, and the app never relies on the server default — but the bare call
independently echoes `2026-08-01 → 2026-08-31`, so the documented default is correct.

## C-12 · T-12 dead fields: `momHistory`, `mtdSpend`, `max_date`, `undated_rows`. **CONFIRMED as far as testable.**
`momHistory` and `mtdSpend` are `[]` even over the **full 6-month** window
(`from=2026-03-01&to=2026-08-31`, 9.96 MB) — the study only tested the default
month, so this is a strictly stronger test. Source confirms both are plumbed and
neither is rendered:
```bash
grep -oc 'momHistory' $B/PlatformBlinkitCampaignsOptimization-B32l52Wb.js   # 2
grep -oE '.{80}momHistory.{120}' $B/PlatformBlinkitCampaignsOptimization-B32l52Wb.js
# ...keywordSnap:re,dailyTotals:x,momHistory:e?.momHistory??[],mtdSpend:e?.mtdSpend??[]}}
```
`max_date: null` and `undated_rows: 0` in all 8 param combinations swept above
(plus the 8 per-platform pulls = ~16 responses today).

## C-13 · Part C — volumes agree EXACTLY on all 7 `pendency-dashboard` platforms. **CONFIRMED to the digit.**
```
plat                op(pend_u,pend_l,open_pos,rows)          pd.totals(same 4)                      match
swiggy              (350601.0, 380218.0, 223, 1270)          (350601.0, 380218.0, 223, 1270)        True
zepto               (92944.0, 88930.4, 68, 301)              (92944.0, 88930.4, 68, 301)            True
blinkit             (25188.0, 33728.0, 114, 447)             (25188.0, 33728.0, 114, 447)           True
bigbasket           (53816.0, 63600.0, 13, 150)              (53816.0, 63600.0, 13, 150)            True
flipkart_grocery    (41564.0, 41564.0, 18, 26)               (41564.0, 41564.0, 18, 26)             True
citymall            (0.0, 0.0, 0, 0)                         (0.0, 0.0, 0, 0)                       True
zomato              (4174.0, 8470.0, 7, 26)                  (4174.0, 8470.0, 7, 26)                True
```
And the 8 per-platform `overall-pendency` pulls sum exactly to the bare call:
`pending_units 768351 ✓  open_units 820823 ✓  open_pos 499 ✓  rows 2716 ✓`;
`groups` does not sum (152 vs 81) ✓. `amazon` 400s on `pendency-dashboard`
(`["Pendency dashboard is not yet enabled for platform 'amazon'."]`) ✓.

## C-14 · Side finding — shipped spec's `platform pendency` enum is stale (4, should be 7). **CONFIRMED, and still unfixed.**
```bash
grep -oE 'new Set\(\[[^]]{0,220}\]\)' $B/PlatformPendencyDashboard-WE4i01HO.js
# new Set([`zepto`,`swiggy`,`blinkit`,`bigbasket`,`flipkart_grocery`,`citymall`,`zomato`])
```
Live: those 7 return 200; `amazon`, `flipkart`, `jiomart` return 400. The shipped
`/root/jivo-cli/ecom-cli/spec.yaml` still declares
`enum: [blinkit, zepto, swiggy, bigbasket]` — **the fix the study recommends has
not been applied**. 7 is the right number.

## C-15 through C-26 — smaller claims, all confirmed
- `overall-pendency` bare call: 200, 47,945 bytes, no params required ✓
- `item_head` enum server-stated: `ALL|PREMIUM|COMMODITY|OTHER` all 200, `MIXED` → **400 `["`item_head` must be PREMIUM, COMMODITY, OTHER or ALL."]`** ✓; 41+24+16 = 81 ✓
- `group_by` enum: 81 / 14 / 31 groups, `rows` invariant at 2716 ✓
- `totals.groups == len(rows)` = 81 ✓; `totals.rows` = PO-line count 2716 ✓
- `by_head[]` pending_units sums to totals ✓ (only `open_pos` does not)
- Export column spec: `open_ltrs`/`pending_ltrs`/`pending_value` all `format:\`money\``, `open_units`/`pending_units`/`open_pos` `format:\`number\`` — the litres-as-money UI bug is real ✓
- UI reads exactly 5 keys off the payload (`z.available_platforms, z.by_head, z.error, z.rows, z.totals`, plus `B.pending_ltrs` where `B = z.totals`) ✓
- `bco` key inventory, row counts and byte shares reproduce exactly (skuMaster 13 / brandFund 6782 / productBooster 12800 / recommendationAds 1058; PB = 80.4%) ✓
- `sales` overwrite: `o=e=>{let t=i(e.campaign);return{...e,sku:t,salesReported:S(e.sales),sales:se(a.get(t),e.qty)}}` ✓ — the API's `sales` really is discarded
- `skuMaster` pre-GST `basicPrice`: Extra Light 1L = **497.1428571** ✓
- T-8: `overall-pendency` amazon MUSTARD 1L `open_units` 42,720 / `open_ltrs` 52,720 ✓; row report shows `per_liter` ∈ {1.0, 2.0} on that item ✓ — litres are per-ASIN, never inferable from the label
- T-10: `_pct` scale split confirmed — summary `{fill_rate_pct:21.39, cancel_rate_pct:0.0, acceptance_rate_pct:97.13, invoiced_share_pct:39.26, uninvoiced_share_pct:60.74, short_invoice_rate_pct:7.58}` (0–100) vs sale-target `growth_pct 0.0369 / achieved_pct 0.4488` (0–1) ✓
- summary `by_fc` = 11 FCs (DED5 DED3 HHS1 HNR4 HHR7 HDL2 HBA4 HCC6 HMV4 HAD1 HKA2), `by_channel` = 4 (CORE NOW FRESH "-") ✓
- summary reachable on 200 despite the UI's `PERMS.shipmentPlanning` gate ✓
- `available_platforms[]` = the 8 slugs, and it is the authoritative enum (see M-1) ✓

---

# D. UNTESTABLE / NOT TESTED

| # | claim | why not tested |
|---|---|---|
| N-1 | `mtdSpend` row shape `{campaign, campaignId, impressions, budget, claimables, consumed}` | array is `[]` in every call, including the full 6-month window. Shape remains UI-column-spec-only. Study already flags NOT VERIFIED — correct. |
| N-2 | `momHistory` purpose | `[]` over 6 months, rendered nowhere. Cannot determine intent. |
| N-3 | `max_date` "never populated" | proving a negative. `null` in ~16 responses across every param combination today. |
| N-4 | T-11 — a 200 carrying a non-empty `error` string | never reproduced; the key is absent entirely (see R-5). Cannot be provoked without sending unobserved values. |
| N-5 | enum case-sensitivity (`item_head=premium`, `group_by=Item`) | **not tested by policy** — a lower-cased variant is not an observed value. A CLI should upper-case `item_head` and lower-case `group_by` defensively. |
| N-6 | `date` beyond `max_date` (e.g. today, 2026-08-22) on `blinkit-sale-target` | **not tested by policy** — outside the app's own picker bound (`max = response.max_date`). Behaviour unknown; a CLI should clamp to `max_date`. |

---

# E. WHAT THE STUDY MISSED — must reach the CLI

### M-1 · `overall-pendency` rejects two of the account's own platform slugs (400)
`GET /api/auth/me` reports **10** platforms; `overall-pendency` accepts only the
**8** in `available_platforms[]`.
```bash
for p in flipkart jiomart; do
  curl -s -H "Authorization: Bearer $T" "https://ecom.jivo.in/api/platform/overall-pendency?platforms=$p" -o x.json -w "%{http_code} "
  cat x.json; echo; done
```
```
400 ["Unknown platform(s): flipkart."]
400 ["Unknown platform(s): jiomart."]
```
The CLI's `--platforms` enum must be the **8**, and must NOT reuse the shared
10-slug platform enum. Error body is a JSON array of strings.

### M-2 · `min_po_date` / `max_po_date` are nullable
`?platforms=citymall` → both `null`. The study recommends them as a freshness
stamp without noting this. Also note the format is `DD-MM-YYYY`, not ISO — a CLI
must not parse them as `YYYY-MM-DD`.

### M-3 · `close_months` is order-insensitive; the server picks the max key
`close_months=2026-02,2026-07` → `prev_month_label: "Jul"`, growth measured off
2026-07. A CLI must not promise "the first one you list".

### M-4 · `prev_month_label` has **no year** — printing it beside `growth_pct` is not enough
`close_months=2025-08` → `prev_month_label: "Aug"`, indistinguishable from a
2026-08 close. The study's rule *"A CLI must print `prev_month_label` next to
`growth_pct`"* is insufficient: print the **close-month key** (`2025-08`), or at
minimum `closes` itself.

### M-5 · Three summary fields the study's table never introduces
`order_ltrs`, `accepted_ltrs`, `delivered_ltrs`. Also `delivery_shortfall_ltrs`
(429887.6) is an **exact duplicate** of `remaining_ltrs` (429887.6) — a CLI
rendering both as separate tiles is showing the same number twice.

### M-6 · The row report's `totals` block is **filter-scoped**, and its bare `count` is 376, not 496
`count` 376 → 133 with `?fulfillment_center=DED5`, → 227 with `?channel=CORE`, and
`totals` moves with it. The summary's `total` is unfilterable (C-5). So the two
`totals` blocks are only comparable on the **bare** row-report call. This is the
mechanism behind T-7 and the study does not state it: `summary.total.lines` = 496
(all lines) but `summary.total.outstanding_lines` = 376 = the row report's default
`count`.

### M-7 · Shipped spec gaps for these four endpoints
- `blinkit-sale-target` params **omit `nocache`**, which the study documents and I
  verified 200 (md5-identical body).
- `overall-pendency` description carries the wrong GST claim — see **R-2**; it must
  not say "~1.05x".
- `platform pendency` enum is still the stale 4 — see **C-14**.
- `blinkit-campaigns-optimization` description advertises "MTD spend" as content;
  `mtdSpend` is always `[]` (C-12). Reword or drop.
- No spec entry records that `blinkit-sale-target` / `overall-pendency` error bodies
  are bare JSON **arrays of strings**, not `{detail: …}` objects.

### M-8 · `sub_category` does not currently produce `MIXED` (R-4) — do not document it as if it does.

---

## Read-only compliance

Every request in this refutation is a GET. Parameter names used:
`platforms`, `item_head`, `group_by` (from the `overall-pendency` params memo `L`
and arrays `S`/`C`), `from`, `to` (from `m.get(be,{from:…,to:…})`), `date`,
`compare_date`, `close_months`, `nocache` (from the sale-target params memo `L`),
`page`, `fulfillment_center`, `channel` (from the shipped spec + `SPDashboard`'s
`onOpen` handlers). Parameter values used: platform slugs from
`GET /api/auth/me → user.platforms` and from `available_platforms[].slug`;
item heads from array `S` plus `MIXED` observed in live `rows[].item_head`;
group_by from array `C`; dates from the app's own computed picker bounds
(`firstOfMonth`, `min`, `max`, `max_date`) and from
`available_close_months[].key`; `DED5` / `CORE` from the summary's own
`by_fc[].fc` / `by_channel[].channel`; `page` 0–7 bounded by the response's own
`count`/`page_size`. No unobserved value was sent. No `set-target` POST, no
mutation of any kind.
