import json,csv
from collections import defaultdict
B=json.load(open('built.json')); rows=B['rows']; sap_rows=B['sap_rows']
LPP=json.load(open('lpp-map.json'))

# SAP daily (independent, authoritative volume)
import subprocess
sapdaily={}
for ln in open('sap-daily.tsv').read().splitlines()[1:]:
    p=ln.split('\t')
    if len(p)>=3: sapdaily.setdefault(p[0],{})[p[1]]=float(p[2])

with open('/Users/damanpreetsingh/jivo-cli/jolly/out/august-actuals-SCORING.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['# OUTCOME DATA — WHAT ACTUALLY HAPPENED IN AUGUST 2026. FOR SCORING ONLY.',
                'NEVER feed these rows into the simulator as an input.','','','','','','','','','','','','','','',''])
    w.writerow(['section','date','line','run_id','run_number','item_code','product','status',
        'cases_app','pieces_per_case','pieces','pack_litres','litres','rated_speed_typed_by_operator',
        'rated_speed_from_line_config','rated_hours_needed','segment_running_minutes','n_segments',
        'breakdown_minutes','rejected_qty','reworked_qty','labour_count','operator','supervisor','source'])
    for r in rows:
        w.writerow(['APP_RUN',r['date'],r['line'],r['run_id'],r['run_number'],r['item'],r['product'],r['status'],
            r['cases'],r['ppc'],round(r['pieces']),r['pack_l'] or '',round(r['litres']) if r['litres'] else '',
            round(r['rated_run']),r['rated_cfg'] or '',round(r['rated_hours'],2) if r['rated_hours'] else '',
            r['seg_min'],r['nseg'],round(r['bd_min']),r['rej'],r['rew'],r['labour'],r['op'],r['sup'],
            'ji.jivo.in /production-execution/runs + run-detail (live 2026-08-31)'])
    # daily x line rollup
    agg=defaultdict(lambda: dict(runs=0,cases=0,pieces=0,litres=0,seg=0,bd=0,rh=0))
    for r in rows:
        a=agg[(r['date'],r['line'])]
        a['runs']+=1; a['cases']+=r['cases']; a['pieces']+=r['pieces']; a['litres']+=r['litres'] or 0
        a['seg']+=r['seg_min']; a['bd']+=r['bd_min']; a['rh']+=r['rated_hours'] or 0
    w.writerow([])
    w.writerow(['# ROLLUP BY DAY x LINE (app-recorded)','','','','','','','','','','','','','','','','','','','','','','',''])
    w.writerow(['section','date','line','runs','','','','','cases_app','','pieces','','litres','','',
        'rated_hours_needed','segment_running_minutes','','breakdown_minutes','','','','','','util_vs_12h_shift_pct'])
    for (d,l) in sorted(agg):
        a=agg[(d,l)]
        w.writerow(['DAY_LINE',d,l,a['runs'],'','','','',round(a['cases']),'',round(a['pieces']),'',round(a['litres']),'','',
            round(a['rh'],2),a['seg'],'',round(a['bd']),'','','','','',round(a['rh']/12*100,1)])
    # SAP daily truth
    w.writerow([])
    w.writerow(['# SAP DAILY FINISHED-GOODS RECEIPTS INTO BH-PF (the authoritative volume record; SAP has no line attribution)','','','','','','','','','','','','','','','','','','','','','','',''])
    w.writerow(['section','date','','','','item_code','','','','','pieces','pack_litres','litres','','','','','','','','','','','','source'])
    tot=0
    for d in sorted(sapdaily):
        for code,q in sorted(sapdaily[d].items()):
            L=LPP.get(code); lit=(L or 0)*q; tot+=lit
            w.writerow(['SAP_DAY',d,'','','',code,'','','','',round(q),L or '',round(lit),'','','','','','','','','','','',
                'HANA JIVO_OIL_HANADB OIGN+IGN1 WhsCode=BH-PF'])
    w.writerow(['SAP_TOTAL','2026-08 all','','','','','','','','',round(sum(sum(v.values()) for v in sapdaily.values())),'',round(tot)])
print('WROTE august-actuals-SCORING.csv  (SAP litres total in file:',round(tot),')')
