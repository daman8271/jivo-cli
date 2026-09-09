#!/usr/bin/env python3
import json,sys,time,urllib.request,urllib.error,re
base=sys.argv[1].rstrip('/')

def request(payload=None,raw=None):
    body=raw if raw is not None else json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(base+'/api/model',data=body,headers={'Content-Type':'application/json'})
    started=time.monotonic()
    try:
        with urllib.request.urlopen(req,timeout=55) as r: status=r.status;data=r.read()
    except urllib.error.HTTPError as e:status=e.code;data=e.read()
    return status,json.loads(data),round(time.monotonic()-started,2)

results=[]
s,m,t=request();assert s==200 and m['days'] and m['products'];assert any(d['runs'] for d in m['days']);results.append({'check':'nonempty default model','status':s,'seconds':t,'engine':m['meta']['engine'],'source':m['meta']['inputAsOf']})
private=re.compile(r'password|access_token|refresh_token|authorization|cookie|customer_name|driver_phone|mobile_number',re.I)
def scan(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():assert not private.search(k),k;scan(v)
    elif isinstance(obj,list):
        for v in obj:scan(v)
    elif isinstance(obj,str):assert not re.search(r'/Users/|/root/|eyJ[A-Za-z0-9_-]{20,}\.',obj),obj[:40]
scan(m);results.append({'check':'model private field/path/JWT scan','passed':True})
for payload in [{'efficiency':1.2},{'nightLine':'UNKNOWN'},{'sourceUrl':'http://127.0.0.1/'},{'efficiency':0.805},{'allowProposedSupply':'yes'}]:
    s,d,t=request(payload);assert s==400,(payload,s,d);results.append({'check':'invalid '+next(iter(payload)),'status':s})
for label,raw in [('malformed JSON',b'{'),('oversize body',b'{"padding":"'+b'x'*3000+b'"}')]:
    s,d,t=request(raw=raw);assert s in (400,413),(label,s,d);results.append({'check':label,'status':s})
for setting in [{'nightLine':None,'efficiency':.8,'allowProposedSupply':False,'allowProvisionalRecipes':False},{'nightLine':'JP Machine','efficiency':.8,'allowProposedSupply':True,'allowProvisionalRecipes':False},{'nightLine':'auto','efficiency':.8,'allowProposedSupply':False,'allowProvisionalRecipes':True}]:
    s,d,t=request(setting);assert s==200,(setting,s,d)
    assert {k:v for k,v in d['scenario'].items() if k!='arrivalDates'}==setting,(setting,d['scenario'])
    assert not d['scenario'].get('arrivalDates'),d['scenario']
    assert all(not day['runs'] for day in d['days'] if day['sunday'])
    for day in d['days']:
        night={r['line'] for r in day['runs'] if r['nightHours']>0};assert len(night)<=1
        if setting['nightLine'] is None:assert not night
    results.append({'check':'scenario','settings':setting,'status':s,'seconds':t,'plannedLitres':d['summary']['plannedLitres']})
print(json.dumps({'base':base,'checks':results,'passed':True},indent=2))
