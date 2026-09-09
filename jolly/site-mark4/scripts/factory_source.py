"""Sanitized independent factory supplement. No business writes; original collectors untouched.
Raw inputs use factory CLI envelopes. This module emits only allowlisted business fields.
"""
import json, pathlib, datetime, collections, hashlib, statistics, sys, os
sys.path.insert(0, os.environ.get('MARK4_FACTORY_REFERENCE_ROOT',str(pathlib.Path(__file__).resolve().parents[2])))
from live.adapters.factory_production import _day_rows, _booked

def normalize(raw):
    now=raw.get('asOf') or datetime.datetime.now(datetime.timezone.utc).isoformat()
    read=lambda name:raw[name]
    ident=lambda *s:hashlib.sha256('|'.join(map(str,s)).encode()).hexdigest()[:16]
    g=read('grpo-september')['results'];pos=read('open-pos');cost=read('cost-analysis')['results'];receipts=[];unposted=collections.defaultdict(float);qc=[]
    for entry in g['results']:
     if entry['phase'] in ['GATE','CANCELLED']:continue
     for po in entry['po_receipts']:
      for line in po['items']:
       if not str(line.get('item_code','')).startswith(('PM','RM')): continue
       key=(str(po['po_number']),line['item_code']);qty=float(line['received_qty']);rej=float(line['rejected_qty']);accepted=line['qc_status']=='ACCEPTED';usable=max(qty-rej,0) if accepted else 0
       if not po['is_posted']:unposted[key]+=qty
       row={'id':ident('receipt',line['po_item_receipt_id']),'code':line['item_code'],'name':line['item_name'],'receivedAt':entry['entry_time'],'receivedQuantity':qty,'acceptedReported':float(line['accepted_qty']),'rejectedQuantity':rej,'usableQuantity':usable,'unit':line['uom'],'qcStatus':line['qc_status'],'posted':po['is_posted'],'linkedOrderId':ident('po',po['po_number'])}
       receipts.append(row)
       if not accepted:qc.append({'id':row['id'],'source':'qc','code':row['code'],'quantity':max(qty-rej,0),'unit':row['unit'],'orderedAt':None,'expectedAt':None,'asOf':now,'dateBasis':'unverified','status':'qc','confidence':'unknown','stockIncluded':False,'linkedOrderId':row['linkedOrderId'],'receivedAt':row['receivedAt']})
    orders=[];events=[];agg=collections.defaultdict(lambda:{'remainingQuantity':0,'notYetAtGateQuantity':0,'unpostedAtGateQuantity':0,'lineCount':0})
    remaining_at_gate=dict(unposted)
    for po in pos['orders']:
     for line in po['items']:
      if not str(line.get('po_item_code','')).startswith(('PM','RM')): continue
      code=line['po_item_code'];unit=line['uom'];remain=float(line['remaining_qty']);key=(str(po['po_number']),code);atgate=min(remain,remaining_at_gate.get(key,0));remaining_at_gate[key]=max(0,remaining_at_gate.get(key,0)-atgate);adjusted=max(0,remain-atgate)
      row={'id':ident('po-line',po['po_number'],line['line_num']),'orderId':ident('po',po['po_number']),'code':code,'name':line['item_name'],'unit':unit,'orderedAt':po['doc_date'],'expectedAt':None,'orderedQuantity':float(line['ordered_qty']),'receivedQuantity':float(line['received_qty']),'remainingQuantity':remain,'unpostedAtGateQuantity':atgate,'notYetAtGateQuantity':adjusted,'unitPrice':float(line['rate']),'branchId':po['branch_id']}
      orders.append(row)
      # Unknown receipt date means these CANNOT be automatically released into stock.
      events.append({'id':row['id'],'source':'factory_po','code':code,'quantity':adjusted,'unit':unit,'orderedAt':po['doc_date'],'expectedAt':None,'asOf':pos['asOf'],'dateBasis':'unverified','status':'open','confidence':'unknown','stockIncluded':False,'linkedOrderId':row['orderId']})
      a=agg[(code,unit)];a['name']=line['item_name'];a['remainingQuantity']+=remain;a['notYetAtGateQuantity']+=adjusted;a['unpostedAtGateQuantity']+=atgate;a['lineCount']+=1
    runs=[{'date':r['date'],'line':r['line'],'code':r['item_code'],'litres':r['litres'],'labourCost':r['labour_cost']} for r in cost['per_run']]
    lab=[]
    for machine in read('lines')['results']:
     rs=[r for r in runs if r['line']==machine['name']];amounts=[r['labourCost'] for r in rs]
     lab.append({'line':machine['name'],'runCount':len(rs),'totalRecordedCost':round(sum(amounts),2) if rs else None,'meanPerRun':round(statistics.mean(amounts),2) if rs else None,'medianPerRun':round(statistics.median(amounts),2) if rs else None,'minPerRun':min(amounts) if rs else None,'maxPerRun':max(amounts) if rs else None,'sessionRate':None})
    b=read('booked-september');history=[]
    for date, payload in sorted(raw.get('mes',{}).items()):
     rows=_day_rows(payload,{});mes=collections.defaultdict(float)
     for r in rows:mes[r['sku_code']]+=r['litres']
     daily={'results':{**b['results'],'data':[r for r in b['results']['data'] if r['date'][:10]==date]}}
     booked,_=_booked(daily)
     history.append({'booked_recorded_value':{'value':booked['value_inr'],'coveredLitres':booked['litres'],'asOf':now,'basis':'Factory BH-PF goods-receipt transaction value (INR), by receipt date','rows':booked['receipts']},'date':date,'read_at':now,'mes_by_item_l':dict(mes),'mes_litres':round(sum(mes.values()),3),'mes_run_count':len(rows),'booked_by_item':{c:r['pcs'] for c,r in booked['by_item'].items()},'booked_by_item_value_inr':{c:r['value_inr'] for c,r in booked['by_item'].items()},'booked_value_inr':booked['value_inr'],'booked_litres':booked['litres'],'booked_receipts':booked['receipts'],'booked_truncated':len(b['results']['data'])>=int(b['results'].get('meta',{}).get('limit',1000))})
    fixture={'asOf':now,'source':'ji.jivo.in','company':'JIVO_OIL','confidence':'high for returned records; incomplete all-supplier coverage; no supplier delivery date verified','coverage':{'supplierCount':pos['supplierCount'],'supplierSelection':pos.get('supplierSelection','suppliers present on September Oil raw-material gate board'),'allSuppliers':bool(pos.get('allSuppliers',False)),'openOrderCount':len(pos['orders']),'openOrderLines':len(orders),'poDateFrom':min((r['orderedAt'] for r in orders),default=None),'poDateTo':max((r['orderedAt'] for r in orders),default=None),'gateEntries':g['count'],'gatePagesRead':g.get('pages_read',1),'gatePagesTotal':g['total_pages'],'gateMonth':raw.get('month','2026-09'),'errors':len(pos['errors'])},'notes':['PO date is contract creation, not an arrival date. Blanket order age cannot estimate supplier lead.','Subtract unposted gate receipts before considering an open PO balance as still to arrive; gate receipts are a month-window reconciliation, not all-time.','QC ACCEPTED uses received minus rejected; accepted_qty can be zero on accepted rows.','Posted and already-accepted receipts are audit evidence, never added again to current stock.','PCS preforms require a blowing conversion; they are not ready bottles. MTS oil must retain original unit until approved oil-density conversion.','Book value is factory movement transaction_value on receipt date, not revenue and not exact production-date value.','MES covers recorded runs only. Preserve actual zero from returned empty/zero report, distinct from unread.','Cost analytics lacks Sep5 costs despite Sep5 MES runs. Recorded labour per run is not an approved ten-hour shift wage.'],'openOrderLines':orders,'outstandingByItem':[{'code':k[0],'unit':k[1],**v} for k,v in sorted(agg.items())],'inboundEvents':events+qc,'gateReceipts':receipts,'recordedLabour':{'asOf':now,'windowFrom':raw.get('from_date','2026-09-01'),'windowTo':raw.get('to_date','2026-09-06'),'actualRunDates':sorted({r['date'] for r in runs}),'basis':'Factory recorded labour cost per MES run; no verified ten-hour session wage','runs':runs,'byLine':lab},'history':{'read_at':now,'days':history},'planningPurchase':{'orderCount':len(raw.get('planning-orders',{}).get('data',[])),'cancelledCount':sum(r.get('status')=='CANCELLED' for r in raw.get('planning-orders',{}).get('data',[]))},'commitmentsMeaning':'Outbound reservations against stock; not supplier delivery promises'}
    fixture['sourceStatus']=raw.get('sourceStatus',{})
    fixture['coverage']['allSuppliers']=bool(pos.get('allSuppliers')) and not pos.get('errors')
    fixture['coverage']['gateComplete']=g.get('pages_read',1)==g.get('total_pages',1)
    fixture['coverage']['supplierCountRead']=pos.get('supplierCountRead',pos['supplierCount'])
    fixture['coverage']['supplierCatalogCount']=pos.get('supplierCatalogCount')
    fixture['coverage']['allOrderLineCount']=sum(len(o.get('items',[])) for o in pos['orders'])
    fixture['coverage']['materialOrderCount']=len({r['orderId'] for r in orders})
    fixture['coverage']['materialLineCount']=len(orders)
    fixture['history']['quantityBasis']='MES segment produced_cases times factory case litres; separate from header total_production used in cost analytics'
    fixture['history']['sourceDisagreements']=[]
    for date,payload in sorted(raw.get('mes',{}).items()):
        runs=payload.get('results',payload) if isinstance(payload,dict) else payload
        mismatches=sum(abs(float(r.get('total_production') or 0)-sum(float(s.get('produced_cases') or 0) for s in r.get('segments',[])))>0.001 for r in runs)
        if mismatches: fixture['history']['sourceDisagreements'].append({'date':date,'runCount':len(runs),'headerVersusSegmentsMismatchCount':mismatches})
    return fixture
