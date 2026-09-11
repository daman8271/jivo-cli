import type { Product } from './types.ts';
import type { Changeover, MachineId, MachineRuleView } from './planning-types.ts';

export const MACHINES: MachineId[] = ['JP Machine','Clear Pack','10 Head','6 Head','Tin Head','Hitech','Samarpan'];
export const RULES_VERSION = 'mark5-pdf-20260910-v1';
export type Route = { allowed: boolean; min: number; max: number; preference: number; conditional: boolean; reason: string };
export function route(p: Product, machine: MachineId): Route {
  const no = (reason: string): Route => ({ allowed:false,min:0,max:0,preference:0,conditional:false,reason });
  const yes = (min:number,max=min,preference=50,conditional=false,reason='Approved running rate; complete crew and packing availability remain assumed.'): Route => ({allowed:true,min,max,preference,conditional,reason});
  if (p.exclusionReason) return no(p.exclusionReason);
  if (!Number.isFinite(p.fillLitres) || p.fillLitres<=0 || !Number.isFinite(p.containersPerPiece) || p.containersPerPiece<=0) return no('Verified physical fill/count unavailable.');
  const name = `${p.name} ${p.category}`.toLowerCase(), fill=p.fillLitres;
  if (machine==='Hitech' || machine==='Samarpan') return p.container==='pouch' ? yes(machine==='Hitech'?1200:1800,machine==='Hitech'?1200:2100,60,true,'Pouch format/film compatibility and crew assumed; source does not map exact SKUs to each pouch machine.') : no('Pouch machine requires a pouch recipe.');
  if (machine==='Tin Head') return p.container==='tin' && fill===15 && !/\b\d+(?:\.\d+)?\s*k(?:g|ilo)/i.test(p.name) ? yes(600,600,100) : no('Only verified 15 L tins have a Tin Head rate; 15 kg is not 15 L.');
  if (machine==='6 Head') {
    if (!(p.container==='bottle' || (p.container==='tin'&&fill===5))) return no('No confirmed container route on 6 Head.');
    return fill===3?yes(780,780,95):fill===4?yes(720,720,80):fill===5?yes(600,600,100,p.container==='tin',p.container==='tin'?'Existing printed 5 L tin route retained conditionally; label/recipe family must match.':undefined):no('6 Head has approved rates only for 3/4/5 L; 1 L emergency rate and 2 L route are unresolved.');
  }
  if (p.container!=='bottle') return no('A supported bottle recipe is required.');
  if (machine==='10 Head') return fill===1?yes(1800,2100,70):fill===2?yes(900,900,100):no('10 Head uses 1/2 L only; larger labels do not fit.');
  if (machine==='Clear Pack') {
    if (/sesame|gingelly/.test(name)) return no('Sesame route is not established; sesame 1 L is explicitly excluded.');
    if (fill===1 && [40,52].includes(p.bottleGrams??0)) return yes(4800,4800,p.bottleGrams===40?100:70);
    if ([4,5].includes(fill)) return yes(1500,1800,fill===4?100:70);
    return no('Clear Pack requires supported 1 L 40/52 g or 4/5 L plastic bottles.');
  }
  if (fill!==1 || /yellow/.test(name)) return no('JP: supported 1 L families only; yellow mustard excluded; 200 ml speed unknown.');
  if (/mustard|kachi|pakki/.test(name)) return yes(4500,4500,100);
  if (/groundnut|peanut/.test(name)) return yes(4500,4500,75);
  if (p.bottleGrams===52 && /pomace|extra\s*light|rice\s*bran/.test(name)) return yes(4500,4500,70,true,'Approved 52 g family; exact new bottle/tooling mapping is conditional.');
  return no('No approved JP oil/bottle family match.');
}

export function oilFamily(p: Product): string {
  const s=`${p.category} ${p.name}`.toLowerCase();
  if (/mustard|kachi|pakki/.test(s)) return 'mustard';
  if (/rice\s*bran/.test(s)) return 'rice-bran';
  if (/groundnut|peanut/.test(s)) return 'groundnut';
  if (/extra\s*virgin/.test(s)) return 'extra-virgin';
  if (/sunflower/.test(s)) return 'sunflower';
  if (/pomace/.test(s)) return 'pomace';
  if (/extra\s*light/.test(s)) return 'extra-light';
  if (/cold\s*press|canola|rapeseed/.test(s)) return 'cold-press';
  return `unmapped:${p.category}`;
}
function bottleKey(p:Product): string|null { return p.bottleComponentCodes?.length?`${p.fillLitres}:${[...p.bottleComponentCodes].sort().join('|')}`:null; }
export function changeover(machine:MachineId, previous:Product|undefined, next:Product):Changeover {
  const make=(minutes:number|null,basis:Changeover['basis'],ruleId:string,activities:string[],min:number|null=minutes,max:number|null=minutes,flushingLitres:number|null=null):Changeover=>({minutes,sourceRange:min===null?null:{min,max},basis,ruleId,includedActivities:activities,flushingLitres,flushingPolicy:'reused',requiresConfirmation:basis==='unknown'||basis==='planning_assumption'||max===null});
  if (previous?.code===next.code) return make(0,'continuation','same-campaign',[]);
  if (!previous) return make(machine==='JP Machine'?360:60,'planning_assumption','unknown-opening-setup',['Opening setup unknown; conditional reservation (JP 6 hours, others 1 hour)'],null,null);
  if (machine==='JP Machine') return make(360,'approved','JP-total-5-6h',['parts','cleaning','flushing'],300,360,1500);
  if (['Tin Head','Hitech','Samarpan'].includes(machine)) return make(60,'planning_assumption',`${machine}-unknown-setup-60m`,['Setup unmeasured; conditional 60-minute reservation'],null,null);
  const from=oilFamily(previous),to=oilFamily(next),sameBottle=bottleKey(previous)!==null&&bottleKey(previous)===bottleKey(next),sameOil=from===to&&!from.startsWith('unmapped:');
  if (machine==='Clear Pack') {
    const parts=sameBottle?0:previous.fillLitres===1&&next.fillLitres===5?60:null;
    if (sameOil) return sameBottle?make(60,'planning_assumption','CP-same-bottle-label-change',['Same bottle/oil; label or SKU clearance unmeasured; conditional 60 minutes'],null,null):parts===null?make(60,'planning_assumption','CP-unlisted-parts',['Unlisted bottle change; conditional 60 minutes'],null,null):make(parts,'approved','CP-parts-1-to-5',['parts']);
    const flush=from==='mustard'?60:from==='rice-bran'&&to==='cold-press'?45:30;
    const bounded=from==='rice-bran'&&to==='cold-press';
    const unknownPair=from!=='mustard'&&!bounded;
    return make((parts??60)+flush,parts===null||unknownPair?'planning_assumption':from==='mustard'?'planning_assumption':'approved',from==='mustard'?'CP-leaving-mustard':bounded?'CP-rice-bran-to-cold-press':'CP-unlisted-flush-30m',[...(sameBottle?[]:['parts']), 'flushing',...(parts===null?['Unlisted parts duration assumed 60 minutes']:[]),...(unknownPair?['Unlisted oil pair uses conditional base flushing']:[])],parts===null||unknownPair?null:(parts+flush),from==='mustard'||parts===null||unknownPair?null:parts+flush,from==='mustard'?1000:550);
  }
  if (sameOil) return make(30,'approved','HEAD-parts-only',['parts']);
  if (from==='cold-press'&&to==='sunflower') return make(30,sameBottle?'approved':'planning_assumption','HEAD-cold-press-to-sunflower',['combined change',...(sameBottle?[]:['Concurrent bottle change coverage unresolved'])],30,sameBottle?30:null);
  if (['mustard','groundnut','extra-virgin'].includes(from)||['mustard','groundnut','extra-virgin'].includes(to)) return make(60,'planning_assumption','HEAD-combined-open-bound',['parts and flushing combined','Oil-category direction mapping assumed'],60,null);
  return make(60,'planning_assumption','HEAD-unlisted-change-60m',['Unlisted oil transition; conditional 60 minutes'],null,null);
}

export const MACHINE_RULES:MachineRuleView[]=MACHINES.map(machineId=>({machineId,packs:machineId==='JP Machine'?'1 L; 200 ml unrated':machineId==='Clear Pack'?'1 / 4 / 5 L':machineId==='10 Head'?'1 / 2 L':machineId==='6 Head'?'3 / 4 / 5 L':machineId==='Tin Head'?'15 L tins':'Pouches; format conditional',speed:machineId==='JP Machine'?'4,500/hour':machineId==='Clear Pack'?'1 L 4,800; 4/5 L 1,500–1,800/hour':machineId==='10 Head'?'1 L 1,800–2,100; 2 L 900/hour':machineId==='6 Head'?'3 L 780; 4 L 720; 5 L 600/hour':machineId==='Tin Head'?'600 tins/hour':machineId==='Hitech'?'1,200/hour':'1,800–2,100/hour',changeover:machineId==='JP Machine'?'5–6 hours total; plan uses 6':machineId==='Clear Pack'?'Parts and directional flush separately':machineId==='10 Head'||machineId==='6 Head'?'30 minutes parts; named-oil combined 1 hour+':'Unmeasured; conditional 60 minutes',note:'Revised PDF adopted 10 Sep. Running speeds; lower speed endpoints selected explicitly. Flushing oil reused; losses unmeasured.',sourcePages:'PDF 2–3, 12–14'}));
