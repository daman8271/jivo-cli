import test from 'node:test';
import assert from 'node:assert/strict';
import { MACHINES, route, changeover } from '../lib/machine-policy.ts';
import { normalizeProducts } from '../lib/model.ts';
import { runEngine, verifiedPiecesPerCase, STORAGE_LIMIT } from '../lib/planning-engine.ts';
import type { FactoryNow, FactoryRun } from '../lib/shift-types.ts';
import type { Mark4Input, Product } from '../lib/types.ts';
import type { EngineRequest, EngineResult, MachineId, PlanningChange } from '../lib/planning-types.ts';

// Synthetic fixtures adapted from MARK IV acceptance fixture shape. No live totals.
const NOW = '2026-09-10T06:00:00+05:30';
function fixture(): Mark4Input {
  return { schemaVersion:1, meta:{as_of:NOW,month:'September 2026'}, plan:[],bom:{},blends:{},items:{},realise:{},
    opening:{stock:{},fg:{},fg_other_l:0,standing_l:0},orders:[],inbound_prebooked:{},inbound_provenance:{},lines:{},
    history:{status:'complete',missing_dates:[],days:Array.from({length:9},(_,n)=>({date:`2026-09-${String(n+1).padStart(2,'0')}`,made_mes_l:0,made_booked_l:0,booked_by_item:{},complete:true}))},
    sources:[{id:'factory-stock',label:'Synthetic stock',asOf:NOW,ok:true}], actual_lines:[] };
}
function add(i:Mark4Input,code:string,{fill=1,count=1,pieces=1_000_000,category='SUNFLOWER',container='bottle',grams=40,carton=20}:{fill?:number;count?:number;pieces?:number;category?:string;container?:Product['container'];grams?:number;carton?:number}={}) {
  const name=`${category} ${fill} LTR ${carton} PCS`, pm=`PM-${code}`, litres=fill*count;
  i.plan.push({code,sku:name,category,pack_type:container.toUpperCase(),litres_per_piece:litres,pieces});
  i.items[code]={name,uom:'PCS'};
  i.items[pm]={name:container==='bottle'?`PET BOTTLE ${fill} LTR ${grams} GM`:container==='tin'?`PRINTED TIN ${fill} LTR`:container==='pouch'?'POUCH FILM':'DRUM 200 LTR',uom:'PCS'};
  i.items['RM-OIL']={name:'QA OIL',uom:'LTR'}; i.items['CARTON']={name:`CORRUGATED CARTON ${carton} PCS`,uom:'PCS'};
  i.bom[code]=[['RM-OIL',litres],[pm,count],['CARTON',1/carton]];
  i.opening.stock[pm]=10_000_000; i.opening.stock['RM-OIL']=10_000_000; i.opening.stock.CARTON=10_000_000;
  i.realise[code]=100;
  return normalizeProducts(i).products.find(p=>p.code===code)!;
}
function close(actual:number,expected:number,label:string) { assert.ok(Number.isFinite(actual)&&Math.abs(actual-expected)<1e-6,`${label}: ${actual} !== ${expected}`); }

test('seven physical machines have independently approved container rates',()=>{
  assert.equal(MACHINES.length,7); assert.equal(new Set(MACHINES).size,7);
  assert.ok(!MACHINES.some(x=>String(x)==='Pouch Machine'));
  const i=fixture();
  const cases:[MachineId,Parameters<typeof add>[2],number,number][]=[
    ['JP Machine',{category:'MUSTARD'},4500,4500],['Clear Pack',{fill:1},4800,4800],
    ['Clear Pack',{fill:4},1500,1800],['Clear Pack',{fill:5},1500,1800],
    ['10 Head',{fill:1},1800,2100],['10 Head',{fill:2},900,900],
    ['6 Head',{fill:3},780,780],['6 Head',{fill:4},720,720],['6 Head',{fill:5},600,600],
    ['Tin Head',{fill:15,container:'tin'},600,600],['Hitech',{fill:.75,container:'pouch'},1200,1200],['Samarpan',{fill:.75,container:'pouch'},1800,2100],
  ];
  cases.forEach(([machine,options,min,max],n)=>{const r=route(add(i,`P${n}`,options),machine);assert.equal(r.allowed,true,machine);assert.equal(r.min,min);assert.equal(r.max,max);});
});
test('physical route exclusions survive old rates and nominal pack similarities',()=>{
  const i=fixture();
  for(const fill of [3,4,5]) assert.equal(route(add(i,`TEN${fill}`,{fill}),'10 Head').allowed,false);
  for(const fill of [1,2]) assert.equal(route(add(i,`SIX${fill}`,{fill}),'6 Head').allowed,false);
  assert.equal(route(add(i,'SMALL',{fill:.2,category:'MUSTARD'}),'JP Machine').allowed,false);
  const mass=add(i,'MASS',{fill:15,container:'tin'});mass.name='OIL 15 KG TIN';assert.equal(route(mass,'Tin Head').allowed,false);
  assert.equal(route(add(i,'BOTTLE15',{fill:15}),'Tin Head').allowed,false);
  assert.equal(route(add(i,'DRUM',{fill:200,container:'drum'}),'Hitech').allowed,false);
});
test('JP changed SKU occupies six hours once, including cleaning and flushing',()=>{
  const i=fixture(), a=add(i,'A',{category:'MUSTARD'}),b=add(i,'B',{category:'GROUNDNUT'});
  const c=changeover('JP Machine',a,b);
  assert.equal(c.minutes,360);assert.deepEqual(c.sourceRange,{min:300,max:360});
  assert.equal(c.flushingLitres,1500);assert.equal(c.flushingPolicy,'reused');
  assert.equal(changeover('JP Machine',a,a).minutes,0);
  close((600-c.minutes!)/60*4500,18000,'maximum bottles after setup in ten-hour test session');
});
test('unknown opening JP reserves six hours conditionally, never a one-hour fallback',()=>{
  const p=add(fixture(),'A',{category:'MUSTARD'}),c=changeover('JP Machine',undefined,p);
  assert.equal(c.minutes,360);assert.notEqual(c.basis,'approved');assert.equal(c.requiresConfirmation,true);
});
test('heads combined setup excludes an extra parts charge and preserves open bound',()=>{
  const i=fixture(), a=add(i,'A',{category:'MUSTARD'}),b=add(i,'B',{category:'GROUNDNUT',fill:2});
  for(const machine of ['10 Head','6 Head'] as MachineId[]){const c=changeover(machine,a,b);assert.equal(c.minutes,60);assert.deepEqual(c.sourceRange,{min:60,max:null});assert.equal(c.flushingLitres,null);assert.equal(c.requiresConfirmation,true);}
});
test('Clear Pack mustard plus 1-to-5 parts occupies at least two hours',()=>{
  const i=fixture(),a=add(i,'A',{category:'MUSTARD'}),b=add(i,'B',{category:'SUNFLOWER',fill:5});
  const c=changeover('Clear Pack',a,b);assert.ok(c.minutes!>=120);assert.equal(c.sourceRange?.max,null);assert.equal(c.flushingLitres,1000);assert.equal(c.flushingPolicy,'reused');
});
test('directional cold-press-to-sunflower setup is not silently reversible',()=>{
  const i=fixture(),a=add(i,'A',{category:'COLD PRESS'}),b=add(i,'B',{category:'SUNFLOWER'}); b.bom=a.bom;
  assert.equal(changeover('10 Head',a,b).minutes,30);
  const reversed=changeover('10 Head',b,a);assert.notEqual(reversed.basis,'approved');assert.equal(reversed.requiresConfirmation,true);
});
test('combo normalization preserves physical fill and does not apply two-litre rate',()=>{
  const p=add(fixture(),'COMBO',{fill:1,count:2,category:'MUSTARD',carton:10});
  assert.equal(p.packLitres,2);assert.equal(p.fillLitres,1);assert.equal(p.containersPerPiece,2);
  assert.equal(route(p,'JP Machine').min/ p.containersPerPiece,2250);assert.equal(route(p,'10 Head').min/ p.containersPerPiece,900);
});
test('invalid physical units and explicit identity holds cannot gain a machine route',()=>{
  const p=add(fixture(),'P');
  for(const value of [0,-1,NaN,Infinity]){assert.equal(route({...p,fillLitres:value},'Clear Pack').allowed,false);assert.equal(route({...p,containersPerPiece:value},'Clear Pack').allowed,false);}
  assert.equal(route({...p,exclusionReason:'QA identity conflict'},'Clear Pack').allowed,false);
});

function observed(lineName:string, litres:number|null,code:string|null=null):FactoryNow {
  const run:FactoryRun={id:'QA-RUN',code,product:code,date:'2026-09-10',sourceUpdatedAt:NOW,liveStatus:'COMPLETED',activeSegment:null,producedPieces:litres,producedLitres:litres,targetLitres:null,quantityBasis:'Synthetic verified litres'};
  return {version:1,revision:'QA-NOW',attemptedAt:NOW,asOf:NOW,ok:true,complete:true,expectedRefreshSeconds:60,date:'2026-09-10',error:null,
    lines:['JP Machine','Clear Pack','10 Head','6 Head','Tin Head','Pouch Machine'].map(line=>({line,coverage:'reported',status:'COMPLETED',runs:line===lineName?[run]:[],note:'Synthetic observation'}))};
}
function request(i:Mark4Input,changes?:PlanningChange[], factoryNow:unknown=null):EngineRequest {
  i.materialSupply={version:1,revision:'QA-MATERIAL',asOf:NOW,coverage:{complete:true,datasets:[{id:'exim',asOf:NOW,attemptedAt:NOW,ok:true,complete:true,expectedRefreshSeconds:180}]},stock:{asOf:NOW,byItem:{...i.opening.stock},oilSourcePolicy:'exim_only',byWarehouse:{},excludedWarehouses:[],conflicts:[]},orders:[],lots:[],expectedReceipts:[],actions:[]};
  return {input:i,factoryNow,now:NOW,sourceRevision:'QA-SOURCE',...(changes?{command:{date:'2026-09-10',expectedRevision:null,idempotencyKey:'qa',changes}}:{})};
}
const only=(machine:MachineId):PlanningChange[]=>[...MACHINES.filter(m=>m!==machine).map(machineId=>({type:'set_line_enabled' as const,machineId,enabled:false})),{type:'set_night_line',machineId:null}];
const days=(r:EngineResult)=>[...new Map([r.proposal,r.snapshot.tomorrow,...r.snapshot.ahead].filter(Boolean).map(d=>[d!.date,d!])).values()];

test('JP initial shift fits six-hour setup plus four-hour filling and correct case units',()=>{
  const i=fixture();add(i,'JP',{category:'MUSTARD'});
  const r=runEngine(request(i,only('JP Machine')));assert.equal(r.validation.valid,true);
  const runs=r.proposal!.runs;assert.equal(runs.length,1);const a=runs[0];
  assert.equal(a.changeover.minutes,360);assert.equal(a.fillingMinutes,240);assert.equal(a.pieces,18000);
  assert.equal(a.containers,18000);assert.equal(a.litres,18000);assert.equal(a.cases,900);
  close((Date.parse(a.endsAt)-Date.parse(a.setupStartsAt))/60000,600,'entire occupied session');
});
test('a continuing JP combo uses its physical one-litre speed divided once',()=>{
  const i=fixture();add(i,'COMBO',{fill:1,count:2,category:'MUSTARD',carton:10});
  const r=runEngine(request(i,only('JP Machine'),observed('JP Machine',0,'COMBO')));
  const a=r.proposal!.runs[0];assert.ok(a);assert.equal(a.changeover.minutes,0);
  assert.equal(a.pieces,22500);assert.equal(a.containers,45000);assert.equal(a.litres,45000);assert.equal(a.cases,2250);assert.equal(a.fillingMinutes,600);
});
test('each occupied session includes setup within ten hours and night has one physical line',()=>{
  const i=fixture();add(i,'JP',{category:'MUSTARD'});add(i,'FOUR',{fill:4});add(i,'POUCH',{fill:.75,container:'pouch'});
  const r=runEngine(request(i));assert.ok(r.proposal!.runs.length>1);
  for(const d of days(r)){
    assert.ok(new Set(d.runs.filter(x=>x.shift==='night').map(x=>x.machineId)).size<=1);
    const groups=new Map<string,typeof d.runs>();for(const run of d.runs){const key=`${run.machineId}:${run.shift}`;groups.set(key,[...(groups.get(key)??[]),run]);assert.ok(Date.parse(run.startsAt)>=Date.parse(run.setupStartsAt));close((Date.parse(run.endsAt)-Date.parse(run.startsAt))/60000,run.fillingMinutes,'filling clock');}
    for(const rs of groups.values()){rs.sort((a,b)=>a.setupStartsAt.localeCompare(b.setupStartsAt));assert.ok(rs.reduce((n,x)=>n+x.fillingMinutes+(x.changeover.minutes??0),0)<=600+1e-6);for(let n=1;n<rs.length;n++)assert.ok(Date.parse(rs[n].setupStartsAt)>=Date.parse(rs[n-1].endsAt));}
    if(d.date==='2026-09-13')assert.equal(d.runs.length,0);
    for(const run of d.runs.filter(x=>x.date==='2026-09-12'&&x.shift==='night'))assert.ok(Date.parse(run.endsAt)<=Date.parse('2026-09-13T00:00:00+05:30'));
  }
});
test('all day lines reserve shared oil before night can take the remainder',()=>{
  const i=fixture();add(i,'JP',{category:'MUSTARD'});add(i,'FOUR',{fill:4});i.opening.stock['RM-OIL']=60000;
  const r=runEngine(request(i));const d=r.proposal!;
  assert.ok(d.runs.some(x=>x.machineId==='Clear Pack'&&x.shift==='day'),'later day line receives stock');
  close(d.dayLitres,60000,'all shared stock belongs to feasible day work');assert.equal(d.nightLitres,0);
  const total=days(r).flatMap(x=>x.runs).reduce((n,x)=>n+x.litres,0);close(total,60000,'forward stock conservation');
});
test('warehouse headroom limits all forward runs without fabricated dispatch clearance',()=>{
  const i=fixture();add(i,'TIN',{fill:15,container:'tin'});i.opening.fg_other_l=STORAGE_LIMIT-1500;
  const r=runEngine(request(i));const total=days(r).flatMap(d=>d.runs).reduce((n,x)=>n+x.litres,0);
  assert.ok(total>0);assert.ok(total<=1500);assert.ok(days(r).some(d=>d.blockers.some(b=>b.kind==='storage')));
});
test('Hitech and Samarpan are separate capacities sharing finite pouch inventory',()=>{
  const i=fixture();add(i,'POUCH',{container:'pouch',fill:.75});i.opening.stock['PM-POUCH']=20000;
  const r=runEngine(request(i));const d=r.proposal!;
  assert.ok(d.runs.some(x=>x.machineId==='Hitech'));assert.ok(d.runs.some(x=>x.machineId==='Samarpan'));
  for(const run of d.runs){assert.equal(run.speedPerHour,run.machineId==='Hitech'?1200:1800);close(run.litres,run.containers*.75,'verified pouch fill');}
  assert.equal(days(r).flatMap(d=>d.runs).reduce((n,x)=>n+x.containers,0),20000);
});
test('generic pouch actuals count once and never imply either physical machine is running',()=>{
  const i=fixture();add(i,'P',{pieces:0,container:'pouch',fill:.75});
  const r=runEngine(request(i,undefined,observed('Pouch Machine',321)));
  assert.equal(r.snapshot.today.recordedLitres,321);assert.match(r.snapshot.today.aggregatePouchNote??'',/321/);
  for(const m of r.snapshot.today.machines.filter(x=>['Hitech','Samarpan'].includes(x.machineId))){assert.equal(m.recordedLitres,null);assert.equal(m.status,'unknown');}
});
test('missing source and unreadable run litres remain unknown rather than recorded zero',()=>{
  const i=fixture();add(i,'P',{pieces:0});
  const missing=runEngine(request(i));assert.equal(missing.snapshot.today.recordedLitres,null);
  assert.ok(missing.snapshot.today.machines.every(m=>m.recordedLitres===null&&m.status==='unknown'));
  const unreadable=runEngine(request(i,undefined,observed('JP Machine',null)));
  assert.equal(unreadable.snapshot.today.recordedLitres,null);
  assert.equal(unreadable.snapshot.today.machines.find(m=>m.machineId==='JP Machine')!.recordedLitres,null);
});
test('exact operator requests cannot exceed stock or unsupported machine routes',()=>{
  const i=fixture();add(i,'JP',{category:'MUSTARD'});i.opening.stock['RM-OIL']=10;
  const stock=runEngine(request(i,[{type:'set_run',machineId:'JP Machine',code:'JP',pieces:100,shift:'day'}]));assert.equal(stock.validation.valid,false);
  const other=fixture();add(other,'FIVE',{fill:5});
  const invalid=runEngine(request(other,[{type:'set_run',machineId:'10 Head',code:'FIVE',pieces:100,shift:'day'}]));assert.equal(invalid.validation.valid,false);
  const manual=runEngine(request(other,[{type:'set_run',machineId:'Manual' as MachineId,code:'FIVE',pieces:100,shift:'day'}]));assert.equal(manual.validation.valid,false);
});
test('exact operator requests reject invalid quantities and invented rate-change actions',()=>{
  for(const pieces of [0,-1,.5,NaN,Infinity]){const i=fixture();add(i,'P');const r=runEngine(request(i,[{type:'set_run',machineId:'Clear Pack',code:'P',pieces,shift:'day'}]));assert.equal(r.validation.valid,false,String(pieces));}
  const i=fixture();add(i,'P');const r=runEngine(request(i,[{type:'set_rate',machineId:'Clear Pack',speed:999999} as unknown as PlanningChange]));assert.equal(r.validation.valid,false);
});
test('case conversion does not round unexplained BOM coefficients into a verified box size',()=>{
  const i=fixture(),p=add(i,'P');assert.equal(verifiedPiecesPerCase(p,i),20);
  const bad={...p,bom:p.bom.map(([c,q])=>[c,c==='CARTON'?.07:q] as [string,number])};assert.equal(verifiedPiecesPerCase(bad,i),null);
});
test('planning carries source timestamp unchanged and rejects stock from missing EXIM reconciliation',()=>{
  const i=fixture();add(i,'P');const before=JSON.stringify(i);const req=request(i);const sourceStamp=i.meta.as_of;
  const r=runEngine(req);assert.equal(r.snapshot.sourceAsOf,sourceStamp);assert.equal(i.meta.as_of,sourceStamp);
  assert.ok(JSON.parse(before).meta.as_of===sourceStamp);
  delete i.materialSupply;const withheld=runEngine({...req,input:i});assert.equal(days(withheld).flatMap(d=>d.runs).length,0);assert.match(withheld.validation.warnings.join(' '),/EXIM/);
});
test('QC material enters the shared ledger only at its recorded afternoon release',()=>{
  const i=fixture();add(i,'P',{pieces:5000});i.opening.stock['RM-OIL']=0;
  const req=request(i,only('Clear Pack'));const supply=i.materialSupply!;
  supply.lots.push({id:'QC',code:'RM-OIL',quantity:5000,unit:'LTR',stage:'qc_pending',observedAt:NOW,stockInclusion:'excluded',availabilityDate:'2026-09-10T16:30:00+05:30',evidenceIds:['QA-RELEASE'],reason:'Synthetic recorded release time'});
  supply.expectedReceipts.push({id:'QC-RELEASE',lotId:'QC',code:'RM-OIL',quantity:5000,unit:'LTR',arrivalEarliest:'2026-09-10',arrivalExpected:'2026-09-10',arrivalLatest:'2026-09-10',usableEarliest:'2026-09-10',usableExpected:'2026-09-10',usableLatest:'2026-09-10',readyAt:'2026-09-10T16:30:00+05:30',basis:'supplier_due',confidence:'recorded',sampleCount:0,historyFrom:null,historyTo:null,evidenceIds:['QA-RELEASE'],note:'Synthetic dated usable-stock commitment, not a live receipt'});
  const r=runEngine(req);assert.ok(r.proposal!.runs.length>0);
  for(const run of r.proposal!.runs)assert.ok(Date.parse(run.startsAt)>=Date.parse('2026-09-10T16:30:00+05:30'));
  assert.ok(r.proposal!.runs.reduce((n,x)=>n+x.containers,0)<=4800);
  close(days(r).flatMap(d=>d.runs).reduce((n,x)=>n+x.litres,0),5000,'released oil counted once');
});
test('live FG already covering orders is not credited again through current MES output',()=>{
  const i=fixture();add(i,'P',{category:'MUSTARD',pieces:1000});i.opening.fg.P=400;
  i.orders=[{docnum:'QA-PO',date:'2026-09-10',due:'2026-09-10',code:'P',pieces:1000,channel:'GT'}];
  const r=runEngine(request(i,only('JP Machine'),observed('JP Machine',400,'P')));
  const runs=days(r).flatMap(d=>d.runs);
  close(runs.reduce((n,x)=>n+x.pieces,0),600,'monthly target less current made once');
  close(runs.reduce((n,x)=>n+x.confirmedLitres,0),600,'PO less current FG once, not less MES again');
});
