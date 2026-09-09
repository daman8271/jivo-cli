#!/usr/bin/env python3
"""Independent read-only factory collector, scoped Oil. Requires Python 3.11+.
All network calls are fixed GET paths, no source-system writes or login refresh.
Private cache holds raw records. Only the allowlisted envelope goes to --output.
"""
import argparse,concurrent.futures,datetime,json,os,pathlib,ssl,time,tomllib,urllib.error,urllib.parse,urllib.request

UTC=datetime.timezone.utc
IST=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
def stamp():return datetime.datetime.now(UTC).isoformat()
def atomic(path,data):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,ensure_ascii=True));os.chmod(temp,0o600);temp.replace(path)
def load(path):return json.loads(pathlib.Path(path).read_text())

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise urllib.error.HTTPError(req.full_url,code,"Factory redirect refused",headers,fp)

class Factory:
    def __init__(self,config,cache):
        self.config=pathlib.Path(config);self.cache=pathlib.Path(cache);self.cache.mkdir(parents=True,exist_ok=True);os.chmod(self.cache,0o700)
        self.status={}
        # Immutable trust configuration is safe to reuse across concurrent GETs.
        self.ssl_context=ssl.create_default_context()
    def get(self,path,params=None):
        # Auth file is re-read so a copied refreshed token is picked up next cycle.
        c=tomllib.loads(self.config.read_text()) if self.config.suffix=='.toml' else load(self.config)
        allowed=('/barcode/items/oitm/','/po/vendors/','/po/open-pos/','/grpo/all-entries/','/planning-purchase/purchase-orders/','/production-execution/lines/','/production-execution/reports/analytics/cost-analysis/','/production-execution/reports/daily-production/','/production-execution/reports/production-movement/')
        material_paths=('/dashboards/stock/',)
        import re
        material_detail=bool(re.fullmatch(r'/(?:gate-core/raw-material-gate-entry/\d+|raw-material-gatein/gate-entries/\d+/po-receipts/view)/',path))
        if path not in allowed+material_paths and not material_detail:raise ValueError('unapproved endpoint')
        base=urllib.parse.urlsplit(c['base_url'])
        if base.scheme!='https' or base.hostname not in {'factory.jivo.in','ji.jivo.in'} or base.port not in (None,443) or base.username or base.password or base.query or base.fragment or base.path.rstrip('/')!='/api/v1':
            raise ValueError('Factory origin refused')
        url=c['base_url'].rstrip('/')+path
        if params:url+='?'+urllib.parse.urlencode(params)
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+c['access_token'],'Company-Code':'JIVO_OIL'},method='GET')
        opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=self.ssl_context))
        with opener.open(req,timeout=25) as response:
            content=response.read(16*1024*1024+1)
            if len(content)>16*1024*1024:raise ValueError('Factory response too large')
            return json.loads(content)
    def read(self,name,path,params=None,max_age=0):
        file=self.cache/(name+'.json')
        if file.exists():
            cached=load(file)
            age=time.time()-datetime.datetime.fromisoformat(cached['asOf']).timestamp()
            if age<max_age:
                self.status[name]={'ok':True,'asOf':cached['asOf'],'cached':True};return cached['data']
        data=self.get(path,params);at=stamp();atomic(file,{'asOf':at,'data':data});self.status[name]={'ok':True,'asOf':at,'cached':False};return data

def refresh_identity(client,path):
    """Refresh the qualified Oil catalog twice daily, retaining original freshness on failure."""
    target=pathlib.Path(path)
    previous=load(target) if target.exists() else None
    if previous and previous.get('ok',True) and time.time()-datetime.datetime.fromisoformat(previous['asOf']).timestamp()<43200:
        return
    try:
        items={};counts={};timestamps=[]
        for digit in range(10):
            prefix='FG0000'+str(digit);name='identity-'+prefix
            rows=client.read(name,'/barcode/items/oitm/',{'search':prefix,'limit':200})
            if not isinstance(rows,list) or len(rows)>=200:raise ValueError('Factory identity prefix incomplete')
            counts[prefix]=len(rows);timestamps.append(client.status[name]['asOf'])
            for row in rows:
                code=row.get('item_code','')
                if not code.startswith(prefix):continue
                items[code]={'name':row['item_name'],'uom':row.get('inventory_uom'),'groupCode':row.get('item_group_code'),'piecesPerBox':row.get('pieces_per_box'),'piecesPerBoxSource':row.get('pieces_per_box_source'),'validFor':row.get('valid_for'),'frozenFor':row.get('frozen_for'),'company':'JIVO_OIL'}
        if not items:raise ValueError('Factory identity catalog empty')
        atomic(target,{'ok':True,'asOf':min(timestamps),'source':'factory barcode items-oitm','company':'JIVO_OIL','coverage':{'prefixes':counts,'range':'FG0000000-FG0000999','completeWithinRange':True,'errors':[]},'items':items})
    except Exception:
        atomic(target,{**(previous or {'asOf':None,'items':{}}),'ok':False,'error':'Factory identity refresh failed; previous evidence retained.','attemptedAt':stamp()})
        client.status['identity']={'ok':False,'asOf':(previous or {}).get('asOf')}

def collect(client,args):
    from factory_source import normalize
    if args.identity_output:refresh_identity(client,args.identity_output)
    today=datetime.datetime.now(IST).date();start=today.replace(day=1);last=today-datetime.timedelta(days=1)
    month=start.strftime('%Y-%m');gate=[];page=1;pages=1;total=0
    while page<=pages:
        data=client.read('gate-'+month+'-'+str(page),'/grpo/all-entries/',{'month':today.month,'year':today.year,'page_size':100,'page':page})
        if not isinstance(data,dict) or not isinstance(data.get('results'),list):raise ValueError('gate shape')
        gate.extend(data['results']);pages=int(data['total_pages']);total=int(data['count']);page+=1
        if pages>50:raise ValueError('gate page limit')
    if len(gate)!=total:raise ValueError('gate pagination incomplete')
    po_file=client.cache/'open-pos-merged.json'
    if po_file.exists() and time.time()-datetime.datetime.fromisoformat(load(po_file)['asOf']).timestamp()<args.po_max_age:
        pos=load(po_file);client.status['purchaseOrders']={'ok':not pos['errors'],'asOf':pos['asOf'],'cached':True}
    else:
        vendors=client.read('vendor-catalog','/po/vendors/',max_age=21600)
        if not isinstance(vendors,list):raise ValueError('vendor catalog shape')
        catalog=sorted({r['vendor_code'] for r in vendors if isinstance(r,dict) and r.get('vendor_code')})
        selected=catalog[:args.max_suppliers] if args.max_suppliers else catalog
        result=[];errors=[]
        def fetch(v):
            try:
                data=client.get('/po/open-pos/',{'supplier_code':v})
                if not isinstance(data,list):raise ValueError('open PO shape')
                return data,None
            except Exception:return [],'supplier read failed'
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for rows,error in pool.map(fetch,selected):
                result.extend(rows)
                if error:errors.append(error)
        # IDs deduplicate records; no vendor identity is carried to public output.
        unique={str(r['po_number']):r for r in result}
        pos={'asOf':stamp(),'supplierCount':len(selected),'supplierCatalogCount':len(catalog),'supplierCountRead':len(selected)-len(errors),'supplierSelection':'all factory Oil vendor catalog entries' if len(selected)==len(catalog) else 'bounded factory Oil vendor catalog scan','allSuppliers':len(selected)==len(catalog) and not errors,'orders':list(unique.values()),'errors':errors}
        if errors:raise RuntimeError('purchase-order coverage incomplete')
        atomic(po_file,pos);client.status['purchaseOrders']={'ok':True,'asOf':pos['asOf'],'cached':False}
    costs=client.read('cost-'+month,'/production-execution/reports/analytics/cost-analysis/',{'date_from':str(start),'date_to':str(today)})
    lines=client.read('lines','/production-execution/lines/',max_age=21600)
    planning=client.read('planning-orders','/planning-purchase/purchase-orders/',max_age=1800)
    mes={};day=start
    while day<=last:
        date=str(day);payload=client.read('mes-'+date,'/production-execution/reports/daily-production/',{'date':date},max_age=3600 if day<last-datetime.timedelta(days=1) else 0)
        if not isinstance(payload,list):raise ValueError('MES shape')
        mes[date]={'results':payload};day+=datetime.timedelta(days=1)
    booked=client.read('booked-'+month,'/production-execution/reports/production-movement/',{'date_from':str(start),'date_to':str(last),'warehouse':'BH-PF','transaction_type':'59','limit':1000}) if last>=start else {'data':[],'meta':{'limit':1000}}
    if not isinstance(booked,dict) or not isinstance(booked.get('data'),list):raise ValueError('booked movement shape')
    if len(booked['data'])>=int(booked.get('meta',{}).get('limit',1000)):raise ValueError('booked movement cap reached')
    raw={'asOf':stamp(),'month':month,'from_date':str(start),'to_date':str(today),'mes':mes,'grpo-september':{'results':{'results':gate,'count':total,'total_pages':pages,'pages_read':pages}},'open-pos':pos,'cost-analysis':{'results':costs},'lines':{'results':lines},'booked-september':{'results':booked},'planning-orders':planning,'sourceStatus':client.status}
    fixture=normalize(raw)
    fixture['history']['days']=[{**r,'read_at':client.status['mes-'+r['date']]['asOf'],'mes_as_of':client.status['mes-'+r['date']]['asOf']} for r in fixture['history']['days']]
    data={k:fixture[k] for k in ['inboundEvents','recordedLabour','coverage','openOrderLines','outstandingByItem','gateReceipts','sourceStatus']}
    data['historyDays']=fixture['history']['days'];data['sourceDisagreements']=fixture['history']['sourceDisagreements'];data['recordedLabour']['asOf']=client.status['cost-'+month]['asOf']
    data['coverage']['poAsOf']=pos['asOf'];data['coverage']['bookedAsOf']=client.status.get('booked-'+month,{}).get('asOf')
    data['coverage']['note']='Open PO delivery dates are not exposed; undated outstanding orders do not become stock. Raw-material POs may duplicate EXIM contracts; only packaging PO events are additive.'
    # Oil PO balances can be EXIM blanket contracts already accounted for; expose the
    # raw-material order ledger, but do not double-credit as another arrival event.
    data['inboundEvents']=[{**e,'stockIncluded':None,'note':'May overlap EXIM blanket contracts; reconciliation required before treating as additional supply.'} if e['source']=='factory_po' and e['code'].startswith('RM') else e for e in data['inboundEvents']]
    return {'asOf':fixture['asOf'],'ok':True,'data':data}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True);p.add_argument('--cache-dir',required=True);p.add_argument('--output',required=True);p.add_argument('--identity-output');p.add_argument('--interval',type=int,default=0);p.add_argument('--po-max-age',type=int,default=1800);p.add_argument('--max-suppliers',type=int,default=0);p.add_argument('--workers',type=int,default=4);args=p.parse_args()
    if args.workers<1 or args.workers>4:p.error('workers must be 1 to 4')
    while True:
        began=time.monotonic()
        try:
            result=collect(Factory(args.config,args.cache_dir),args);atomic(args.output,result)
            print(json.dumps({'ok':True,'asOf':result['asOf'],'orders':result['data']['coverage']['openOrderCount'],'suppliers':result['data']['coverage']['supplierCountRead'],'seconds':round(time.monotonic()-began,1)}),flush=True)
        except Exception as exc:
            previous=load(args.output) if pathlib.Path(args.output).exists() else {'asOf':None,'data':{}}
            failed={**previous,'ok':False,'error':'Factory supplement refresh failed; last successful evidence retained.','attemptedAt':stamp()}
            atomic(args.output,failed);print(json.dumps({'ok':False,'errorType':type(exc).__name__,'statusCode':getattr(exc,'code',None)}),flush=True)
            if not args.interval:raise SystemExit(1)
        if not args.interval:break
        time.sleep(max(1,args.interval-(time.monotonic()-began)))
if __name__=='__main__':main()
