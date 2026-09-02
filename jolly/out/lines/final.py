import json,csv,statistics
from collections import defaultdict
B=json.load(open('built.json'))
rows=B['rows']; sap_rows=B['sap_rows']

# ---- production days actually worked (SAP)
sapdays=set()
for ln in open('sap-aug-oign-byitem.tsv'): pass
days_app=sorted({r['date'] for r in rows})
print('app run dates:',len(days_app),days_app[0],'->',days_app[-1])

LINES=['JP Machine','Clear Pack','10 Head','6 Head','Pouch Machine','Tin Head']
# ---- per line: rated hours needed (SAP-allocated), actual segment hours, days active
sap_h_line=defaultdict(float); sap_L_line=defaultdict(float)
for s in sap_rows:
    if s['hours']: sap_h_line[s['line']]+=s['hours']
    if s['line']: sap_L_line[s['line']]+=s['litres']
app_h_line=defaultdict(float); seg_h_line=defaultdict(float); days_line=defaultdict(set); runs_line=defaultdict(int); bd_line=defaultdict(float)
appL=defaultdict(float)
for r in rows:
    if r['rated_hours']: app_h_line[r['line']]+=r['rated_hours']
    seg_h_line[r['line']]+=r['seg_min']/60
    days_line[r['line']].add(r['date']); runs_line[r['line']]+=1
    bd_line[r['line']]+=r['bd_min']
    if r['litres']: appL[r['line']]+=r['litres']

AVAIL_12x26=12*26
print()
print('PER-LINE, AUGUST 2026 (Oil)')
hdr=f"{'line':14} {'runs':>5} {'days':>5} {'segment h':>10} {'ratedh SAP':>11} {'ratedh app':>11} {'util%12x26':>11} {'bd min':>7}"
print(hdr); print('-'*len(hdr))
tot_sap=tot_app=tot_seg=0
for l in LINES:
    u=sap_h_line[l]/AVAIL_12x26*100
    print(f"{l:14} {runs_line[l]:>5} {len(days_line[l]):>5} {seg_h_line[l]:>10.1f} {sap_h_line[l]:>11.1f} {app_h_line[l]:>11.1f} {u:>10.1f}% {bd_line[l]:>7.0f}")
    tot_sap+=sap_h_line[l]; tot_app+=app_h_line[l]; tot_seg+=seg_h_line[l]
print('-'*len(hdr))
print(f"{'TOTAL 6 lines':14} {sum(runs_line.values()):>5} {'':>5} {tot_seg:>10.1f} {tot_sap:>11.1f} {tot_app:>11.1f} {tot_sap/(AVAIL_12x26*6)*100:>10.1f}%")
print()
print(f'available hours 12h x 26d x 6 lines = {AVAIL_12x26*6} h  -> utilisation {tot_sap/(AVAIL_12x26*6)*100:.1f}%')
print(f'available hours 22h x 26d x 6 lines = {22*26*6} h (app master) -> utilisation {tot_sap/(22*26*6)*100:.1f}%')
print(f'available hours 24h x 31d x 6 lines = {24*31*6} h (ceiling)    -> utilisation {tot_sap/(24*31*6)*100:.1f}%')
print()
print(f'segment-logged running hours = {tot_seg:,.0f} h  vs rated-hours needed {tot_sap:,.0f} h')

# ================= CSV 1: MASTERS =================
CFG=[('JP Machine',2,'1 LTR',1.0,5400,'app line-config id=6'),
     ('Clear Pack',1,'1 LTR',1.0,4800,'app line-config id=4'),
     ('Clear Pack',1,'5 LTR',5.0,3000,'app line-config id=5'),
     ('10 Head',3,'1 LTR',1.0,2100,'app line-config id=7'),
     ('10 Head',3,'2 LTR',2.0,1260,'app line-config id=8'),
     ('10 Head',3,'5 LTR',5.0,900,'app line-config id=9'),
     ('6 Head',4,'1 LTR',1.0,1080,'app line-config id=10'),
     ('6 Head',4,'2 LTR',2.0,720,'app line-config id=11'),
     ('6 Head',4,'5 LTR',5.0,600,'app line-config id=12'),
     ('Pouch Machine',5,'Hitech',1.0,1800,'app line-config id=13'),
     ('Pouch Machine',5,'Samarpan',1.0,2400,'app line-config id=14'),
     ('Tin Head',6,'15 L tin',15.0,240,'DAMAN RULING 2026-08-29 - NO app line-config exists'),
     ('Manual',7,'200 L drum',200.0,None,'no config - hand filling, out of scope')]
# observed speeds (>=3 segment runs)
obs=defaultdict(list)
for r in rows:
    if r['status']!='COMPLETED' or r['nseg']<3 or r['seg_min']<=0 or r['pieces']<=0: continue
    obs[(r['line'],round(r['pack_l'],2) if r['pack_l'] else None)].append(r['pieces']/(r['seg_min']/60))
with open('/Users/damanpreetsingh/jivo-cli/jolly/out/aug01-lines-TRUTH.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['line','line_id','config_name','pack_litres','rated_pieces_per_hour','rated_litres_per_hour',
        'capacity_pieces_per_12h_shift','capacity_litres_per_12h_shift','capacity_litres_per_22h_day_app_master',
        'observed_median_pcs_per_hour_aug','observed_best_pcs_per_hour_aug','observed_n_runs','observed_median_pct_of_rated',
        'verdict_vs_ruling','master_source','master_created_at','as_at','confidence','note'])
    for line,lid,cfg,L,sp,src in CFG:
        k=(line,round(L,2) if L else None); o=sorted(obs.get(k,[]),reverse=True)
        med=statistics.median(o) if o else None; best=max(o) if o else None
        pct=(med/sp*100) if (o and sp) else None
        if sp is None: verdict='OUT OF SCOPE'
        elif not o: verdict='NO WELL-LOGGED AUG RUN - unverified'
        elif pct>=90: verdict='CONFIRMED by Aug runs'
        elif pct>=60: verdict='rated not reached in Aug (median %.0f%%)'%pct
        else: verdict='REFUTED in practice - median only %.0f%% of rated'%pct
        w.writerow([line,lid,cfg,L,sp,(sp*L if sp and L else ''),
            (sp*12 if sp else ''),(sp*12*L if sp and L else ''),(sp*22*L if sp and L else ''),
            (round(med) if med else ''),(round(best) if best else ''),len(o),(round(pct,1) if pct else ''),
            verdict,src,'2026-08-05 (created AFTER the 1 Aug study date)','2026-08-01',
            'VERIFIED - read live from ji.jivo.in' if 'app line-config' in src else 'INFERRED - operator word only',
            ''])
    w.writerow([])
    w.writerow(['# NON-SPEED MASTERS','','','','','','','','','','','','','','','','','',''])
    for k,v,c,n in [
      ('standard_hours_per_day (all 7 lines)','22.00','VERIFIED - app /production-execution/lines/','IDENTICAL on all 7 lines = template default; contradicts the app OEE engine which benchmarks a 12 h shift'),
      ('OEE benchmark shift used by the app','12.00 h','VERIFIED - reverse-engineered, 118/119 runs exact','perf = min(100, pieces / (rated x (12h - breakdown)))'),
      ('electricity_units_per_hour','NULL on all 7 lines','VERIFIED - app','GAP: no per-line electricity rate exists, so the shift-length/electricity trade-off Daman asked for cannot be costed from the app'),
      ('line clearance: raise -> QA sign-off','22.7 min median','DERIVED from 133 Aug clearances','p90 99 min; per line: 6 Head 10, JP 23, 10 Head 29, Clear Pack 31, Pouch 36'),
      ('line clearance: QA sign-off -> production','4.0 min median','DERIVED from 134 Aug clearances','p90 47 min'),
      ('LINE CLEARANCE TOTAL (raise -> first output)','51.3 min median','DERIVED from 133 Aug clearances','p90 130 min. ONE CLEARANCE PER RUN (135 clearances / 136 runs)'),
      ('manpower per run (labour_count)','18 median','VERIFIED - app run records','17-18 on the 4 main lines; Pouch 12; Tin Head 15; one junk value 1000; rate_per_hour is 0.00 so labour COST is unusable'),
      ('supervisor','Ravi on 128 of 136 runs','VERIFIED - app run records','Hardeep 3'),
      ('machines registered on lines','0','VERIFIED - app /production-execution/machines/ returns []','GAP: no filler/capper/labeler breakdown exists'),
      ('maintenance assets registered (Oil)','1 (a deactivated smoke-test record)','VERIFIED - app maintenance/assets','GAP'),
      ('PM plans / PM executions (Oil)','0 / 0','VERIFIED - app maintenance','GAP: planned maintenance is NOT recorded anywhere'),
      ('machine availability on 2026-08-01','NOT RECORDED','GAP','13 maintenance work orders exist, none dated 1 Aug, none linked to a line, none with real downtime'),
      ('flush per oil change','400 L of the incoming oil','Daman ruling 2026-08-29','reused ~1 month, so MATERIAL ~400 L per oil per month; TIME per changeover'),
    ]:
        w.writerow([k,'','','','','','','','','','','','',v,c,'','2026-08-01','',n])
print()
print('WROTE /Users/damanpreetsingh/jivo-cli/jolly/out/aug01-lines-TRUTH.csv')
