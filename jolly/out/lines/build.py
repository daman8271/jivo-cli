import json,glob,re,statistics,csv
from collections import defaultdict,Counter
from datetime import datetime

R=[json.load(open(f))['results'] for f in glob.glob('detail/*.json')]
LPP=json.load(open('lpp-map.json'))
rec=json.load(open('recon-prod-aug.json'))['results']
sapitems={x['item_code']:x for x in rec['sap_by_item']}

# ---- rated speed table (line, pack litres) -> pieces/hr  [from app line-configs + Daman ruling for Tin Head]
def rated(line,L):
    if L is None: return None,'no pack size'
    if line=='JP Machine':      return (5400,'config 1L') if L<=1.05 else (None,'JP has no config >1L')
    if line=='Clear Pack':      return (4800,'config 1L') if L<=1.05 else ((3000,'config 5L') if L<=5.05 else (None,'no config'))
    if line=='10 Head':         return (2100,'config 1L') if L<=1.05 else ((1260,'config 2L') if L<=2.05 else ((900,'config 5L') if L<=5.05 else (None,'no config')))
    if line=='6 Head':          return (1080,'config 1L') if L<=1.05 else ((720,'config 2L') if L<=3.05 else ((600,'config 5L') if L<=5.05 else (None,'no config')))
    if line=='Pouch Machine':   return (2400,'config Samarpan') if L<=1.05 else (None,'no config')
    if line=='Tin Head':        return (240,'Daman ruling - NOT in app') if L>=12 else (None,'no config')
    return None,'Manual - out of scope'

# ---- ACTUALS by day+line from app runs
rows=[]
for r in R:
    ppc=r['pieces_per_case'] or 1
    cases=float(r['total_production'] or 0)
    pcs=cases*ppc
    L=r['litres_per_piece']; L=float(L) if L else LPP.get(r['item_code'])
    mins=sum(int(s['duration_minutes'] or 0) for s in r['segments'])
    rt,src=rated(r['line_name'],L)
    rh=pcs/rt if rt else None
    rows.append(dict(date=r['date'],line=r['line_name'],run_id=r['id'],run_number=r['run_number'],
        item=r['item_code'],product=r['product'],status=r['status'],
        cases=cases,ppc=ppc,pieces=pcs,litres=(pcs*L if L else None),pack_l=L,
        rated_run=float(r['rated_speed'] or 0),rated_cfg=rt,rated_src=src,
        seg_min=mins,nseg=len(r['segments']),bd_min=float(r['total_breakdown_time'] or 0),
        rej=float(r['rejected_qty'] or 0),rew=float(r['reworked_qty'] or 0),
        labour=r.get('labour_count'),op=r.get('operators'),sup=r.get('supervisor'),
        rated_hours=rh))
rows.sort(key=lambda x:(x['date'],x['line'],x['run_number'] or 0))

# ---- coverage of SAP litres by items that appear in app runs
runitems={r['item'] for r in rows}
covL=sum((LPP.get(k) or 0)*v['sap_qty'] for k,v in sapitems.items() if k in runitems)
totL=sum((LPP.get(k) or 0)*v['sap_qty'] for k,v in sapitems.items())
print(f'SAP litres total = {totL:,.0f}; of which items also seen in app runs = {covL:,.0f} ({covL/totL*100:.1f}%)')

# ---- item -> dominant line, from app runs (by pieces)
il=defaultdict(Counter)
for r in rows: 
    if r['pieces']>0: il[r['item']][r['line']]+=r['pieces']
# pack-size -> dominant line fallback
pl=defaultdict(Counter)
for r in rows:
    if r['pieces']>0 and r['pack_l']: pl[round(r['pack_l'],3)][r['line']]+=r['pieces']
def pick_line(code,L):
    if code in il: return il[code].most_common(1)[0][0],'from app runs'
    if L is None: return None,'no pack size'
    if L>=100: return 'Manual','200L drum - hand filled, out of scope'
    if L>=12:  return 'Tin Head','tin pack'
    key=round(L,3)
    if key in pl: return pl[key].most_common(1)[0][0],'pack-size default'
    cand=[k for k in pl if abs(k-L)<0.3]
    if cand: return pl[min(cand,key=lambda k:abs(k-L))].most_common(1)[0][0],'nearest pack default'
    return 'Clear Pack','fallback'

# ---- SAP-based rated hours
sap_rows=[];sap_h=0.0;unassigned=0.0
for code,v in sapitems.items():
    if code.startswith('PM'): continue
    L=LPP.get(code); pcs=v['sap_qty']
    line,how=pick_line(code,L)
    rt,src=rated(line,L) if line else (None,'')
    h=pcs/rt if rt else None
    if h: sap_h+=h
    else: unassigned+=(L or 0)*pcs
    sap_rows.append(dict(code=code,name=v['item_name'],pieces=pcs,pack_l=L,litres=(L or 0)*pcs,line=line,how=how,rated=rt,hours=h))
app_h=sum(r['rated_hours'] for r in rows if r['rated_hours'])
print(f'RATED HOURS needed: app-recorded runs = {app_h:,.0f} h ; ALL SAP output = {sap_h:,.0f} h ; litres unassignable = {unassigned:,.0f}')
json.dump(dict(rows=rows,sap_rows=sap_rows,app_h=app_h,sap_h=sap_h,totL=totL),open('built.json','w'))
