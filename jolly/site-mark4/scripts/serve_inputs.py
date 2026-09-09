#!/usr/bin/env python3
"""Read-only, field-allowlisted adapter for Mark 3 source inputs, not its plan output."""
import argparse
import hashlib
import json
import math
import re
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CODE = re.compile(r'^(?:FG|RM|PM)[A-Z0-9]{5,20}$')
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
LINE_NAMES = {'JP Machine', 'Clear Pack', '10 Head', '6 Head', 'Tin Head', 'Pouch Machine'}

def number(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None

def stamp(value):
    if not isinstance(value, str): return None
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value
    except ValueError: return None

def text(value, limit=180):
    # Only call for explicitly public operational names; never arbitrary source notes.
    if not isinstance(value, str): return ''
    value=re.sub(r'https?://\S+|[\w.+-]+@[\w.-]+\.\w+|(?:/Users/|/root/|/home/)\S*|\+?\d[\d ()-]{8,}\d', '[redacted]', value)
    return value[:limit]

def numeric_map(value):
    return {k: number(v) for k, v in (value or {}).items() if CODE.fullmatch(k) and number(v) is not None}

def pairs(value):
    return [[r[0], number(r[1])] for r in (value or []) if isinstance(r, list) and len(r) == 2 and isinstance(r[0], str) and CODE.fullmatch(r[0]) and number(r[1]) is not None]

def date_maps(value, provenance=False):
    allowed = {'EXIM-OTW','EXIM-OTW-OVERDUE','PO-LEAD','PO-LEAD-OVERDUE','QC-ACCEPTED','FACTORY-QC','GATE-QC','QC-PM','QC-OIL'}
    return {d: {k: v for k, v in rows.items() if CODE.fullmatch(k) and isinstance(v, str) and all(token in allowed for token in v.split('+'))} if provenance else numeric_map(rows)
            for d, rows in (value or {}).items() if DATE.fullmatch(d) and isinstance(rows, dict)}

def source_stamp(row):
    mode = row.get('mode', '')
    if isinstance(mode,str):
        for prefix in ('carried ','last-good '):
            if mode.startswith(prefix):return stamp(mode[len(prefix):])
    return stamp(row.get('server_at')) or stamp(row.get('fetched_at'))

def sanitize_supplements(raw):
    out={'rates':[], 'verifiedBom':{}, 'verifiedItems':{}, 'cartonTransitions':[]}
    for r in raw.get('rates',[]):
        if r.get('line') not in LINE_NAMES or number(r.get('piecesPerHour')) is None or r.get('basis') not in {'rated','observed','derived'}:continue
        out['rates'].append({'line':r['line'],'pack':text(r.get('pack'),30),'piecesPerHour':number(r['piecesPerHour']),'basis':r['basis'],'source':'ji.jivo.in machine capacity evidence','asOf':stamp(r.get('asOf'))})
    out['verifiedBom']={k:pairs(v) for k,v in raw.get('verifiedBom',{}).items() if CODE.fullmatch(k)}
    out['verifiedItems']={k:{'name':text(v.get('name')),'uom':text(v.get('uom'),20)} for k,v in raw.get('verifiedItems',{}).items() if CODE.fullmatch(k) and isinstance(v,dict)}
    for r in raw.get('cartonTransitions',[]):
        if CODE.fullmatch(str(r.get('from',''))) and CODE.fullmatch(str(r.get('to',''))):
            out['cartonTransitions'].append({'from':r['from'],'to':r['to'],'evidence':'Factory recipes independently verified: identical per-piece oil, bottle, cap and labels. The carton and tape quantities differ.'})
    labor=raw.get('recordedLabour',{})
    out['recordedLabour']={'asOf':stamp(labor.get('asOf')),'windowFrom':stamp(labor.get('windowFrom')),'windowTo':stamp(labor.get('windowTo')),'basis':'Recorded run cost, not a verified ten-hour session rate. Cost-rate endpoint unavailable.','runs':[]}
    for r in labor.get('runs',[]):
        if r.get('line') not in LINE_NAMES or not CODE.fullmatch(str(r.get('code',''))):continue
        out['recordedLabour']['runs'].append({'date':stamp(r.get('date')),'line':r['line'],'code':r['code'],'litres':number(r.get('litres')),'labourCost':number(r.get('labourCost'))})
    aging=raw.get('dispatchAging',{})
    out['dispatchAging']={k:number(aging.get(k)) for k in ('pendingLitres','oldestDays','medianDays','bills')}
    out['dispatchAging'].update({k:stamp(aging.get(k)) for k in ('asOf','windowFrom','windowTo')})
    out['dispatchAging']['note']='Windowed open invoice records for BH-BT/BH-PF. Request scoped Oil; company is not independently attested. Not reconciled physical storage. Older open bills may be missing.'
    out['dispatchAging']['buckets']=[{'label':text(r.get('label'),30),'bills':number(r.get('bills')),'litres':number(r.get('litres'))} for r in aging.get('buckets',[])]
    return out

def sanitize(raw, state, supplements=None, carry=None):
    if not isinstance(raw, dict) or not isinstance(raw.get('plan'), list) or not raw['plan'] or not isinstance(raw.get('opening', {}).get('stock'), dict):
        raise ValueError('Planning source missing required plan or stock')
    meta = raw.get('meta', {})
    if not stamp(meta.get('as_of')) or not isinstance(meta.get('horizon'), list) or len(meta['horizon']) != 2 or not all(DATE.fullmatch(str(d)) for d in meta['horizon']):
        raise ValueError('Planning source missing dated horizon')
    out = {'schemaVersion': 1, 'meta': {'frozen':stamp(meta.get('frozen')),'as_of':stamp(meta['as_of']),'horizon':list(meta['horizon']),'month':text(meta.get('month'),40),'rolling':meta.get('rolling') is True,'state_collected_at':stamp(meta.get('state_collected_at'))}}
    out['plan'] = [{**{k:text(row.get(k)) for k in ('code','sku','head','category','pack_type')}, **{k:number(row.get(k)) for k in ('litres_per_piece','pieces','litres')}}
                   for row in raw['plan'] if isinstance(row, dict) and CODE.fullmatch(str(row.get('code', '')))]
    if not out['plan']: raise ValueError('No valid plan rows')
    for row in out['plan']:
        if any(number(row.get(k)) is None or row[k] < 0 for k in ('litres_per_piece', 'pieces', 'litres')): raise ValueError('Invalid plan quantities')
        if row['litres_per_piece'] <= 0: raise ValueError('Invalid pack volume')
    out['bom'] = {k: pairs(v) for k,v in raw.get('bom', {}).items() if CODE.fullmatch(k)}
    out['blends'] = {k: pairs(v) for k,v in raw.get('blends', {}).items() if CODE.fullmatch(k)}
    # Keep only material/FG master names: omit expense, personnel and asset records.
    out['items'] = {k: {'name': text(v.get('name')), 'uom': text(v.get('uom'), 20)} for k,v in raw.get('items', {}).items() if CODE.fullmatch(k) and isinstance(v,dict)}
    out['realise'] = numeric_map(raw.get('realise'))
    opening = raw['opening']
    out['opening'] = {k: numeric_map(opening.get(k)) for k in ('stock','fg')}
    out['opening'].update({k: number(opening.get(k)) for k in ('fg_litres','fg_plan_l','fg_other_l','standing_l','oil_l','oil_tank_l','oil_drum_l','packaging_pieces')})
    out['opening']['standing_basis'] = 'Estimated: all-company open dispatch backlog multiplied by Oil share; not a reconciled physical count.'
    out['opening']['packaging_non_moving_pcs'] = number(opening.get('packaging_non_moving_pcs'))
    def orders(rows):
        result=[]
        occurrences={}
        for row in rows or []:
            if not CODE.fullmatch(str(row.get('code',''))) or number(row.get('pieces')) is None: continue
            # The source repeats the same order in backlog with an unclamped creation date.
            # Exclude that date and array position; retain multiplicity of identical lines.
            signature=json.dumps([row.get(k) for k in ('docnum','code','due','pieces','value','channel','_src')],separators=(',',':'),sort_keys=True)
            ordinal=occurrences.get(signature,0);occurrences[signature]=ordinal+1
            identity=signature+':'+str(ordinal)
            channel = str(row.get('channel','')).upper()
            src = str(row.get('_src','')).upper()
            result.append({'docnum': hashlib.sha256(identity.encode()).hexdigest()[:16], 'date': stamp(row.get('date')), 'due': stamp(row.get('due')), 'code': row['code'], 'pieces': number(row['pieces']), 'value': number(row.get('value')), 'channel': channel if channel in {'GT','MT','FORECAST','OIL','MART','BEVERAGES','ECOM','QCOM','AMAZON','FLIPKART','B2B','B2C','ONLINE','QUICK_COMMERCE'} else 'OTHER', '_src': src if src in {'OMS','ECOM-PO','FORECAST','PLAN'} else 'unknown', 'demand_basis':'allocated_ecom_mix' if src=='ECOM-PO' else 'monthly_forecast' if src=='FORECAST' else 'source_order_line', 'is_exact_sku_due':src=='OMS', 'value_basis':'derived_realisation' if src=='ECOM-PO' else 'source_order_value', 'planning_scope':'oil' if channel=='OIL' else 'ecom_allocated' if src=='ECOM-PO' else 'forecast' if src=='FORECAST' else 'non_oil_or_unverified'})
        return result
    out['orders'] = orders(raw.get('orders'))
    out['backlog'] = orders(raw.get('backlog'))
    out['inbound_prebooked'] = date_maps(raw.get('inbound_prebooked'))
    out['inbound_provenance'] = date_maps(raw.get('inbound_provenance'), True)
    out['lines'] = {k: {slot: number(v) for slot,v in slots.items() if re.fullmatch(r'(?:\d+(?:\.\d+)?L|TIN|POUCH)',slot) and number(v) is not None} for k,slots in raw.get('lines',{}).items() if k in LINE_NAMES}
    out['lines_basis'] = {k: {slot:v for slot,v in slots.items() if re.fullmatch(r'(?:\d+(?:\.\d+)?L|TIN|POUCH)',slot) and v in {'rated','measured','derived','assumed'}} for k,slots in raw.get('lines_basis',{}).items() if k in LINE_NAMES}
    h = raw.get('history',{}).get('data') or {}
    out['history'] = {'status': h.get('status') if h.get('status') in {'complete','partial','unavailable'} else 'unavailable', 'read_at':stamp(h.get('read_at')), 'missing_dates':[d for d in h.get('missing_dates',[]) if isinstance(d,str) and DATE.fullmatch(d)], 'days':[]}
    for row in h.get('days',[]):
        if not DATE.fullmatch(str(row.get('date',''))):continue
        day={'date':row['date'],'read_at':stamp(row.get('read_at')), 'booked_by_item':numeric_map(row.get('booked_by_item')) if isinstance(row.get('booked_by_item'),dict) else None, 'complete':row.get('complete') is True,'settled':row.get('settled') is True,'booked_truncated':row.get('booked_truncated') is True}
        for key in ('made_mes_l','made_booked_l','made_booked_pcs','dispatched_oil_l','runs','open_segments'):day[key]=number(row.get(key))
        day['notes'] = [] if day['complete'] else ['Some records were not read. Missing values are not zero.']
        out['history']['days'].append(day)
    out['sources']=[]
    labels={'opening_fg':'Finished goods','opening_pm':'Packaging stock','opening_oil':'Manual tank dip','opening_oil_drums':'Drum stock','standing':'Dispatch pile estimate','orders':'OMS orders','orders_ecom':'E-commerce orders','inbound':'Inbound materials','lines':'Machine capacity','history':'Factory history'}
    for key,label in labels.items():
        p=raw.get('provenance',{}).get(key,{})
        effective=source_stamp(p)
        source_id=p.get('source')
        source_status=state.get('sources',{}).get(source_id,{}) if isinstance(source_id,str) else {}
        observed_ok=p.get('ok',source_status.get('ok',True))
        out['sources'].append({'id':key,'label':label,'asOf':effective,'ok':effective is not None and observed_ok is True,'note':'E-commerce litres by date are allocated to SKUs using the open-PO mix; exact SKU due dates are not known and values are derived.' if key=='orders_ecom' else 'Carried source reading' if str(p.get('mode','')).startswith('carried ') else 'Original source timestamp; collection does not refresh the underlying observation.'})
    production=state.get('factory_production') or {}
    actualstamp=source_stamp(state.get('sources',{}).get('factory_production',{}))
    out['actual_lines']=[]
    seen=set()
    for row in (production.get('running_now') or []) + (production.get('recent_runs') or []):
        ident=row.get('run_id')
        if ident in seen or row.get('line') not in LINE_NAMES:continue
        seen.add(ident)
        live_status=str(row.get('live_status','')).upper()
        out['actual_lines'].append({'run_id':number(ident),'date':stamp(row.get('date')),'line':row['line'],'code':row.get('sku_code') if CODE.fullmatch(str(row.get('sku_code',''))) else None,'product':text(row.get('sku')),'litres':None,'asOf':actualstamp,'status':live_status if live_status in {'RUNNING','STOPPED','PAUSED','COMPLETED','IDLE','BREAKDOWN'} else 'UNKNOWN','running_minutes':number(row.get('running_minutes')),'breakdown_minutes':number(row.get('breakdown_minutes'))})
    actualstamp=source_stamp(state.get('sources',{}).get('factory_production',{}))
    out['sources'].append({'id':'actual_lines','label':'Machine observations','asOf':actualstamp,'ok':state.get('sources',{}).get('factory_production',{}).get('ok') is True,'note':'MES has partial plant coverage. Recent stopped runs are historical observations.'})
    out['actual_booked_today']={'date':stamp(production.get('date')), 'by_item':numeric_map((production.get('booked_today') or {}).get('by_item')), 'litres':number((production.get('booked_today') or {}).get('litres')), 'asOf':actualstamp}
    supplements=sanitize_supplements(supplements or {})
    configs=production.get('line_configs')
    config_stamp=actualstamp
    if not isinstance(configs,list) or not configs:
        block=(carry or {}).get('line_configs') or {}
        configs=block.get('data');config_stamp=stamp(block.get('at'))
    live_rates=[]
    for r in configs if isinstance(configs,list) else []:
        if r.get('line_name') not in LINE_NAMES or r.get('is_active') is False:continue
        pack=str(r.get('config_name','')).replace(' LTR','L')
        if pack in {'Hitech','Samarpan'}:pack='POUCH-'+pack
        if not re.fullmatch(r'(?:\d+(?:\.\d+)?L|POUCH-(?:Hitech|Samarpan))',pack):continue
        try:rate=float(r.get('rated_speed'))
        except (ValueError,TypeError):continue
        if not math.isfinite(rate) or rate<=0:continue
        live_rates.append({'line':r['line_name'],'pack':pack,'piecesPerHour':rate,'basis':'rated','source':'ji.jivo.in hourly machine config','asOf':config_stamp})
    if live_rates:supplements['rates']=live_rates
    out['supplements']=supplements
    for code,bom in (supplements or {}).get('verifiedBom',{}).items(): out['bom'][code]=pairs(bom)
    for code,item in (supplements or {}).get('verifiedItems',{}).items(): out['items'][code]={'name':text(item.get('name')),'uom':text(item.get('uom'),20)}
    # Only publish master data used by plan, stocks, orders or recipe dependencies.
    used={r['code'] for r in out['plan']} | set(out['opening']['fg']) | set(out['opening']['stock']) | {r['code'] for r in out['orders']}
    for day in out['history']['days']: used.update((day.get('booked_by_item') or {}).keys())
    for recipe in list(out['bom'].values())+list(out['blends'].values()):used.update(r[0] for r in recipe)
    out['items']={k:v for k,v in out['items'].items() if k in used}
    out['dispatch_aging']=(supplements or {}).get('dispatchAging', {'available':False,'note':'Invoice-age evidence not read.'})
    return out

class Feed:
    def __init__(self, root, supplements, ttl=15, supplemental_root=None):
        self.root=Path(root); self.supplements=supplements; self.ttl=ttl; self.cached=None; self.checked=0; self.lock=threading.Lock(); self.error=False
        self.supplemental_root=Path(supplemental_root) if supplemental_root else None
    def get(self):
        with self.lock:
            if self.cached is not None and time.monotonic()-self.checked < self.ttl:return self.cached
            self.checked=time.monotonic()
            try:
                raw=json.loads((self.root/'sim/live-inputs.json').read_text())
                state=json.loads((self.root/'live/state/state.json').read_text())
                try:carry=json.loads((self.root/'sim/live-carry.json').read_text())
                except (OSError,ValueError):carry={}
                value=sanitize(raw,state,self.supplements,carry)
                if self.supplemental_root:
                    from revision_input import merge, add_exim_transit, merge_material_supply
                    for kind in ('demand','factory'):
                        try:
                            p=self.supplemental_root/f'{kind}-supplement.json'
                            if p.stat().st_size > 5000000: raise ValueError('Supplement exceeds size limit')
                            envelope=json.loads(p.read_text())
                        except (OSError,ValueError): envelope={}
                        merge(value,envelope,kind)
                    try:
                        material_path=self.supplemental_root/'material-supply.json'
                        if material_path.stat().st_size > 15000000: raise ValueError('Material supply exceeds size limit')
                        material_envelope=json.loads(material_path.read_text())
                        if not isinstance(material_envelope.get('data'),dict) or material_envelope['data'].get('version') != 1:
                            raise ValueError('Invalid reconciled material envelope')
                        self.last_material_envelope=material_envelope
                    except (OSError,ValueError):
                        prior=getattr(self,'last_material_envelope',{})
                        material_envelope={**prior,'ok':False,'error':'Material feed read failed; original ledger retained.'} if prior else {}
                    merge_material_supply(value,material_envelope)
                    add_exim_transit(value,state,self.root)
                    # Reuse the project's one pack parser for historical SKUs,
                    # including kg tins and combination sales units.
                    import importlib.util
                    parser_path=self.root/'engine/plan_units.py'
                    packs={r['code']:r['litres_per_piece'] for r in value['plan']}
                    if parser_path.is_file():
                        spec=importlib.util.spec_from_file_location('mark4_pack_units',parser_path)
                        parser_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser_module)
                        history_codes={c for d in value['history']['days'] for c in list((d.get('booked_by_item') or {}))+list((d.get('mes_by_item_l') or {}))}
                        for code in history_codes:
                            source_item=raw.get('items',{}).get(code,{})
                            if code not in value['items'] and CODE.fullmatch(code): value['items'][code]={'name':text(source_item.get('name')),'uom':text(source_item.get('uom'),20)}
                            name=source_item.get('name','')
                            parsed,_=parser_module.pack_litres(name)
                            # The shared kg-to-litre parser assumes oil density;
                            # dry goods cannot acquire litres through that path.
                            oil_name=bool(re.search(r'OIL|MUSTARD|SOYABEAN|SUNFLOWER|GROUNDNUT|CANOLA|OLIVE|POMACE|COCONUT|SESAME|RICE BRAN|PEANUT',name,re.I))
                            if re.search(r'\b(?:KG|KGS|KILOGRAM)',name,re.I) and not oil_name:
                                packs.pop(code,None)
                            elif parsed is not None and parsed>0:packs[code]=parsed
                    valuation=value.get('valuation') or {}
                    value['valuation']={'asOf':valuation.get('asOf'), 'priceBasis':valuation.get('priceBasis') or 'Same inherited SKU realisation table as the forward plan; original price date is not attested. Estimated selling worth, not billing or booked transaction cost.', 'litresPerPiece':{**packs,**valuation.get('litresPerPiece',{})}, 'rupeesPerLitre':{**value['realise'],**valuation.get('rupeesPerLitre',{})}}
                self.cached=json.dumps(value, separators=(',',':'),allow_nan=False).encode(); self.error=False
                self.material_complete=(value.get('materialSupply') or {}).get('coverage',{}).get('complete') is True
            except (OSError,ValueError,TypeError,KeyError):
                self.error=True
                if self.cached is None: raise ValueError('Source unavailable or invalid')
            return self.cached

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/factory-now.json','/shift-baseline.json','/dispatch-now.json','/storage-evidence.json') or self.path.startswith('/review/'):
            from live_board_feed import read_board
            try: body=read_board(self.server.feed.supplemental_root,self.path)
            except ValueError:
                self.send_response(503);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b'{"error":"Factory board unavailable"}');return
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Access-Control-Allow-Origin','*');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
        if self.path not in ('/inputs.json','/healthz'):
            self.send_error(404);return
        try: body=self.server.feed.get()
        except ValueError:
            self.send_response(503);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"ok":false,"error":"Source unavailable or invalid"}');return
        if self.path=='/healthz':body=json.dumps({'ok':not self.server.feed.error,'retainedLastGood':self.server.feed.error,'materialCoverageComplete':getattr(self.server.feed,'material_complete',False)}).encode()
        self.send_response(200);self.send_header('X-Mark4-Retained-Last-Good','true' if self.server.feed.error else 'false');self.send_header('X-Mark4-Source-Status','error' if self.server.feed.error else 'ok');self.send_header('Access-Control-Expose-Headers','X-Mark4-Retained-Last-Good, X-Mark4-Source-Status');self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Access-Control-Allow-Origin','*');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*args):pass

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',required=True);parser.add_argument('--port',type=int,default=8794);parser.add_argument('--supplements',default=str(Path(__file__).with_name('supplements.json')));parser.add_argument('--supplement-root')
    args=parser.parse_args()
    supplements=json.loads(Path(args.supplements).read_text()) if Path(args.supplements).exists() else {}
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.feed=Feed(args.source_root,supplements,supplemental_root=args.supplement_root);server.serve_forever()
if __name__=='__main__':main()
