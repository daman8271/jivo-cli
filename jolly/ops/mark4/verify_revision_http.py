#!/usr/bin/env python3
"""Release acceptance against the real deployed model and favicon."""
import json,re,sys,urllib.request,urllib.error
base=sys.argv[1].rstrip('/')
def read(path,payload=None):
    request=urllib.request.Request(base+path,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=60) as r:return r.status,r.headers,r.read()
    except urllib.error.HTTPError as e:return e.code,e.headers,e.read()
s,h,raw=read('/api/model');assert s==200
m=json.loads(raw);book=m['demandBook'];bridge=m['planningBridge']
assert book['online']['grossOpenLitres']>0 and book['online']['priorMonthOpenLitres']>0
assert book['online']['acceptedOpenLitres']<=book['online']['grossOpenLitres']+.01
assert bridge['mappedLitres'] <= book['online']['acceptedPlanningDueLitres']+book['trade']['planningDueLitres']+.01
if book['trade'].get('unknownActiveOrderCount',0)>0:
    assert book['coverage']=='partial' and bridge['grossDueLitres'] is None
actuals=m['actuals'] if 'actuals' in m else m.get('history',{}).get('days',[])
# Locate actual days by contract; fail explicitly if this changes.
if not actuals:actuals=m.get('actualDays',[])
assert actuals,sorted(m)
assert any(d.get('mesValue',{}).get('value',0) for d in actuals)
for d in actuals:
    for k in ('bookedValue','mesValue'):
        value=d.get(k)
        if value and value['coverage']!='complete':assert value['value'] is None
lines=m['lines'];assert any((line.get('recordedLabour') or {}).get('totalCost') for line in lines)
events=m['inboundEvents'];assert any(e['source']=='exim_transit' for e in events)
assert any(e['source']=='factory_po' and e['expectedAt'] is None and not e['included'] for e in events)
eligible=next(e for e in events if e['source']=='factory_po' and e['code'].startswith('PM') and e['stockIncluded'] is False and e['quantity']>0 and e['unit'].upper() in ('PCS','PC','PIECES','NOS') and e['status']=='open')
date=m['days'][min(2,len(m['days'])-1)]['date']
payload={**m['scenario'],'arrivalDates':{eligible['id']:date}}
s,_,raw=read('/api/model',payload);assert s==200,(s,raw[:200])
changed=json.loads(raw);event=next(e for e in changed['inboundEvents'] if e['id']==eligible['id'])
assert event['included'] and event['conditional'] and event['appliedAt']==date
assert event['expectedAt']==eligible['expectedAt']
s,_,raw=read('/api/model',{'arrivalDates':{'missing-source-event':date}});assert s==400,(s,raw[:200])
s,h,raw=read('/icon.svg');assert s==200 and 'image/svg+xml' in h.get('Content-Type','') and b'<svg' in raw
s,_,raw=read('/');assert s==200 and re.search(rb'rel="icon"[^>]+icon\.svg',raw)
print(json.dumps({'base':base,'passed':True,'checks':['full/prior-month open book','mapped source-volume bound','unknown trade quantity stays unknown','historical goods worth with partial coverage','recorded labour','individual EXIM and undated factory PO visibility','arrival scenario credit and original-date preservation','invalid source ID rejected','custom SVG favicon and metadata'],'actualDays':len(actuals),'inboundEvents':len(events),'coverage':book['coverage']},indent=2))
