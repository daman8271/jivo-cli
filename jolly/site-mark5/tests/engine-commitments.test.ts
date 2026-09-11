import test from 'node:test';
import assert from 'node:assert/strict';
import {runEngine} from '../lib/planning-engine.ts';
import {changeover} from '../lib/machine-policy.ts';
import {normalizeProducts} from '../lib/model.ts';
import type {EngineRequest, PlanRevision, PlannedRun} from '../lib/planning-types.ts';
import type {Mark4Input} from '../lib/types.ts';
const now='2026-09-10T06:00:00+05:30';
function request():EngineRequest {
  const stock={'RM-OIL':1000,'PM-BOTTLE':1000,CARTON:100};
  const input:Mark4Input={schemaVersion:1,meta:{as_of:now},plan:[{code:'FG-X',sku:'MUSTARD 1 L',category:'MUSTARD',pack_type:'BOTTLE',litres_per_piece:1,pieces:1000}],bom:{'FG-X':[['RM-OIL',1],['PM-BOTTLE',1],['CARTON',.05]]},blends:{},items:{'FG-X':{name:'MUSTARD 1 L',uom:'PCS'},'RM-OIL':{name:'Oil',uom:'L'},'PM-BOTTLE':{name:'PET BOTTLE 1 L 26 GM',uom:'PCS'},CARTON:{name:'CARTON',uom:'PCS'}},realise:{},opening:{stock,fg:{},fg_other_l:0,standing_l:0},orders:[],inbound_prebooked:{},lines:{},history:{status:'complete',missing_dates:[],days:Array.from({length:9},(_,n)=>({date:`2026-09-${String(n+1).padStart(2,'0')}`,made_mes_l:0,made_booked_l:0,booked_by_item:{},complete:true}))},sources:[],materialSupply:{version:1,revision:'m',asOf:now,coverage:{complete:true,datasets:[]},stock:{asOf:now,byItem:stock,oilSourcePolicy:'exim_only',byWarehouse:{},excludedWarehouses:[],conflicts:[]},orders:[],lots:[],expectedReceipts:[],actions:[]}};
  return {input,factoryNow:null,now,sourceRevision:'s'};
}
function approved(req:EngineRequest):PlanRevision {
  const original=runEngine(req).proposal!;
  const base=original.runs.find(r=>r.machineId==='JP Machine')!;
  const run:PlannedRun={...base,id:'agreed',date:'2026-09-11',pieces:100,containers:100,cases:5,litres:100,setupStartsAt:'2026-09-11T07:30:00+05:30',startsAt:'2026-09-11T13:30:00+05:30',endsAt:'2026-09-11T13:31:20+05:30',fillingMinutes:100/4500*60};
  return {id:'approval',date:run.date,revision:1,parentRevision:null,status:'approved',createdAt:now,createdBy:'operator',sourceRevision:'s',rulesVersion:'mark5-pdf-20260910-v1',changes:[],proposal:{...original,date:run.date,runs:[run],dayLitres:100,nightLitres:0,totalLitres:100}};
}
test('auto-approved future runs survive empty changes and reserve material before today',()=>{
  const req=request(),pin=approved(req);req.savedPlans=[pin];const before=JSON.stringify(pin);
  const result=runEngine(req),tomorrow=result.snapshot.tomorrow;
  assert.ok(tomorrow.runs.some(r=>r.id==='agreed'&&r.pieces===100));
  assert.ok(result.proposal!.totalLitres<=900);
  assert.equal(JSON.stringify(pin),before,'approval object remains immutable');
  assert.equal(result.snapshot.today.proposal?.date,'2026-09-10');
});
test('infeasible commitment stays recorded and emits review issue without breaking snapshot',()=>{
  const req=request(),pin=approved(req);pin.proposal.runs[0].pieces=10000;pin.proposal.runs[0].containers=10000;pin.proposal.runs[0].litres=10000;req.savedPlans=[pin];
  const result=runEngine(req);
  assert.equal(result.validation.valid,true);
  assert.ok(result.snapshot.tomorrow.blockers.some(b=>b.reason.includes('Agreed run needs review')));
  assert.ok(!result.snapshot.tomorrow.runs.some(r=>r.id==='agreed'));
  assert.equal(req.savedPlans[0].proposal.runs[0].pieces,10000);
});
test('same bottle changed labels do not become invented mechanical changes or approved zero setup',()=>{
  const req=request(),input=req.input as Mark4Input,p=normalizeProducts(input).products[0];
  const a={...p,bottleComponentCodes:['PM-BOTTLE']},b={...a,code:'FG-Y',bom:[...a.bom,['PM-LABEL',1] as [string,number]]};
  const setup=changeover('Clear Pack',a,b);
  assert.equal(setup.minutes,60);assert.equal(setup.basis,'planning_assumption');
  const rice={...a,category:'RICE BRAN',name:'RICE BRAN 1 L'},cold={...b,category:'COLD PRESS',name:'COLD PRESS 1 L'};
  assert.equal(changeover('Clear Pack',rice,cold).minutes,45);
});
test('disabling a machine suspends inherited exact work and re-enabling restores it',()=>{
  const req=request(),saved=approved(req);saved.date='2026-09-10';saved.status='draft';saved.proposal.date=saved.date;saved.changes=[{type:'set_run',machineId:'JP Machine',code:'FG-X',pieces:100,shift:'day'}];req.savedPlans=[saved];
  req.command={date:saved.date,expectedRevision:1,idempotencyKey:'disable',changes:[{type:'set_line_enabled',machineId:'JP Machine',enabled:false}]};
  const disabled=runEngine(req);assert.equal(disabled.validation.valid,true);assert.ok(!disabled.proposal!.runs.some(r=>r.machineId==='JP Machine'));assert.ok(disabled.proposal!.assumptions.some(a=>a.id==='suspended-exact-runs'));
  saved.changes.push({type:'set_line_enabled',machineId:'JP Machine',enabled:false});req.command={...req.command,idempotencyKey:'enable',changes:[{type:'set_line_enabled',machineId:'JP Machine',enabled:true}]};
  const enabled=runEngine(req);assert.equal(enabled.validation.valid,true);assert.equal(enabled.proposal!.runs.find(r=>r.machineId==='JP Machine'&&r.shift==='day')?.pieces,100);
});
test('no-night suspends inherited exact night controls without removing them',()=>{
  const req=request(),saved=approved(req);saved.date='2026-09-10';saved.status='draft';saved.proposal.date=saved.date;saved.changes=[{type:'set_run',machineId:'JP Machine',code:'FG-X',pieces:100,shift:'night'}];req.savedPlans=[saved];
  req.command={date:saved.date,expectedRevision:1,idempotencyKey:'night-off',changes:[{type:'set_night_line',machineId:null}]};
  const result=runEngine(req);assert.equal(result.validation.valid,true);assert.equal(result.proposal!.nightLitres,0);assert.ok(!result.proposal!.runs.some(r=>r.shift==='night'));assert.equal(saved.changes[0].type,'set_run');
});
test('approved exact runs are not replayed twice by cumulative newer draft controls',()=>{
  const req=request(),pin=approved(req);pin.changes=[{type:'set_run',machineId:'JP Machine',code:'FG-X',pieces:100,shift:'day'}];
  const draft:PlanRevision={...pin,id:'ai-draft',revision:2,parentRevision:1,status:'draft',changes:[...pin.changes]};req.savedPlans=[pin,draft];
  const result=runEngine(req);assert.equal(result.validation.valid,true);assert.equal(result.snapshot.tomorrow.runs.filter(r=>r.machineId==='JP Machine').length,1);assert.equal(result.snapshot.tomorrow.runs.find(r=>r.machineId==='JP Machine')?.pieces,100);
  draft.changes=[{type:'set_run',machineId:'JP Machine',code:'FG-X',pieces:200,shift:'day'}];
  const refreshed=runEngine(req);assert.equal(refreshed.validation.valid,true);assert.equal(refreshed.snapshot.tomorrow.runs.find(r=>r.machineId==='JP Machine')?.pieces,100,'unapproved draft does not replace commitment');
});
test('approved zero-setup continuation is checked after the projected preceding day',()=>{
  const req=request(),pin=approved(req),run=pin.proposal.runs[0];run.setupStartsAt='2026-09-11T07:30:00+05:30';run.startsAt=run.setupStartsAt;run.endsAt='2026-09-11T07:31:20+05:30';run.changeover={...run.changeover,minutes:0,basis:'continuation',ruleId:'same-campaign',sourceRange:{min:0,max:0},requiresConfirmation:false};req.savedPlans=[pin];
  const result=runEngine(req);
  assert.ok(result.proposal!.runs.some(r=>r.machineId==='JP Machine'&&r.code==='FG-X'));
  assert.equal(result.snapshot.tomorrow.runs.find(r=>r.id==='agreed')?.pieces,100);
  assert.ok(!result.snapshot.tomorrow.blockers.some(b=>b.reason.includes('setup interval')));
});
test('future full setup allows a different due product today',()=>{
  const req=request(),input=req.input as Mark4Input,pin=approved(req);
  input.plan[0].pieces=100;input.plan.push({...input.plan[0],code:'FG-DUE',sku:'MUSTARD DUE 1 L',pieces:500});input.items['FG-DUE']={name:'MUSTARD DUE 1 L',uom:'PCS'};input.bom['FG-DUE']=input.bom['FG-X'];
  input.orders=[{docnum:'due',date:'2026-09-10',due:'2026-09-10',code:'FG-DUE',pieces:500,channel:'OIL',_src:'OMS'}];req.savedPlans=[pin];
  req.command={date:'2026-09-10',expectedRevision:null,idempotencyKey:'jp-only',changes:[...(['Clear Pack','10 Head','6 Head','Tin Head','Hitech','Samarpan'] as const).map(machineId=>({type:'set_line_enabled' as const,machineId,enabled:false})),{type:'set_night_line',machineId:null}]};
  const result=runEngine(req);assert.equal(result.validation.valid,true);assert.equal(result.proposal!.runs.find(r=>r.machineId==='JP Machine'&&r.code==='FG-DUE')?.pieces,500);assert.equal(result.snapshot.tomorrow.runs.find(r=>r.id==='agreed')?.pieces,100);
});
