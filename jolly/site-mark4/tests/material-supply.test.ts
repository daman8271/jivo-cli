import test from "node:test";
import assert from "node:assert/strict";
import { modelCacheKey } from "../lib/model-cache.ts";
import { buildModel, validateScenario } from "../lib/model.ts";
import type { Mark4Input, MaterialSupply } from "../lib/types.ts";

// Realistic batch quantities preserve supply timing and conservation under the campaign minimum.
function fixture(): Mark4Input {
  const supply: MaterialSupply = { version: 1, revision: "before", asOf: "2026-09-07T07:00:00+05:30", coverage: { complete: true, datasets: [{ id: "factory_po", asOf: "2026-09-07T07:00:00+05:30", attemptedAt: "2026-09-07T07:00:00+05:30", ok: true, complete: true, expectedRefreshSeconds: 180 }] }, stock: { asOf: "2026-09-07T07:00:00+05:30", byItem: { "RM-OIL": 100000, "PM-BOTTLE": 0 }, byWarehouse: {}, excludedWarehouses: [], conflicts: [] }, orders: [], lots: [], expectedReceipts: [], actions: [] };
  return { schemaVersion: 1, meta: { as_of: "2026-09-07T07:00:00+05:30" }, plan: [{ code: "A", sku: "MUSTARD A", category: "MUSTARD", pack_type: "PET", litres_per_piece: 1, pieces: 10000 }], bom: { A: [["RM-OIL", 1], ["PM-BOTTLE", 1]] }, blends: {}, items: { A: { name: "MUSTARD A", uom: "PCS" }, "RM-OIL": { name: "OIL", uom: "LTR" }, "PM-BOTTLE": { name: "PET BOTTLE 1 LTR 26 GM", uom: "PCS" } }, realise: { A: 100 }, opening: { stock: { "RM-OIL": 100000, "PM-BOTTLE": 100000 }, fg: {}, fg_other_l: 0, standing_l: 0 }, orders: [], inbound_prebooked: { "2026-09-08": { "PM-BOTTLE": 10000 } }, inbound_provenance: { "2026-09-08": { "PM-BOTTLE": "EXIM-OTW" } }, lines: { "JP Machine": { "1L": 100 } }, history: { days: [], missing_dates: [], status: "partial" }, sources: [], materialSupply: supply };
}
function addOrder(input: Mark4Input, confidence: "estimated" | "recorded" = "estimated") {
  const s = input.materialSupply!;
  s.revision = "after-new-order";
  s.orders.push({ id: "factory-po:100", code: "PM-BOTTLE", unit: "PCS", orderedAt: "2026-09-08", orderedQty: 10000, bookReceivedQty: 0, outstandingQty: 10000, notYetAtGateQty: 10000, atGateQty: 0, sourceAsOf: "2026-09-08T10:00:00+05:30" });
  s.lots.push({ id: "lot:100", code: "PM-BOTTLE", quantity: 10000, unit: "PCS", stage: "ordered", orderId: "factory-po:100", observedAt: "2026-09-08T10:00:00+05:30", stockInclusion: "excluded", evidenceIds: ["factory-po:100"], reason: "Existing factory purchase order" });
  s.expectedReceipts.push({ id: "expected:100", lotId: "lot:100", orderId: "factory-po:100", code: "PM-BOTTLE", quantity: 10000, unit: "PCS", arrivalEarliest: "2026-09-14", arrivalExpected: "2026-09-15", arrivalLatest: "2026-09-16", usableEarliest: "2026-09-15", usableExpected: "2026-09-16", usableLatest: "2026-09-17", basis: confidence === "recorded" ? "supplier_due" : "qc_history", confidence, timingVersion: 1, sourceArrivalAt: "2026-09-15T00:00:00+05:30", arrivalTimeKnown: true, qaMedianHours: 3.5, qaEstimatedAt: "2026-09-15T03:30:00+05:30", sampleCount: 4, historyFrom: "2026-08-01", historyTo: "2026-09-07", evidenceIds: ["factory-po:100", "grpo:10", "qc:10"], note: "Availability follows arrival and QC." });
}

test("new existing PO unlocks filling on its usable day, never on truck arrival or old legacy data", () => {
  const input = fixture();
  assert.equal(buildModel(input).summary.plannedLitres, 0);
  addOrder(input);
  const model = buildModel(input);
  assert.equal(model.days.filter(day => day.date < "2026-09-15").reduce((total, day) => total + day.productionLitres, 0), 0);
  assert.equal(model.days.find(day => day.date === "2026-09-15")?.productionLitres, 10000);
  assert.equal(model.materials.find(row => row.code === "PM-BOTTLE")?.opening, 0);
  assert.equal(model.materials.find(row => row.code === "PM-BOTTLE")?.arrivals, 10000);
  assert.equal(model.inboundEvents.length, 1);
  assert.equal(model.inboundEvents[0].conditional, true);
  assert.equal(model.summary.conditionalSupplyLitres, 10000);
  assert.equal(model.summary.conditionalLitres, 10000);
  assert.equal(model.days.find(day => day.date === "2026-09-15")?.runs[0].conditionalSupply, true);
  assert.equal(model.materialSupply?.comparison?.recorded.plannedLitres, 0);
  assert.equal(model.materialSupply?.comparison?.expected.plannedLitres, 10000);
});

test("supplier delay, short quantity and cancellation each change the future plan", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.expectedReceipts[0].usableExpected = "2026-09-17";
  input.materialSupply!.expectedReceipts[0].timingVersion = 2;
  input.materialSupply!.expectedReceipts[0].qaEstimatedAt = "2026-09-17T08:00:00+05:30";
  input.materialSupply!.expectedReceipts[0].quantity = 6000;
  const delayed = buildModel(input);
  assert.equal(delayed.days.find(day => day.date === "2026-09-16")?.productionLitres, 0);
  assert.equal(delayed.days.find(day => day.date === "2026-09-17")?.productionLitres, 6000);
  input.materialSupply!.lots[0].stage = "cancelled";
  assert.equal(buildModel(input).summary.plannedLitres, 0);
});

test("new vendor without delivery evidence stays an actionable unknown, not a promised receipt", () => {
  const input = fixture(); addOrder(input); input.materialSupply!.expectedReceipts = [];
  const result = buildModel(input);
  assert.equal(result.summary.plannedLitres, 0);
  assert.match(result.inboundEvents[0].reason, /unknown/);
  const action = result.materialSupply!.requiredActions.find(row => row.code === "PM-BOTTLE")!;
  assert.equal(action.affectedProducts[0].code, "A");
  assert.equal(action.firstNeeded, "2026-09-07");
});

test("recorded usable dates still schedule future commitments; historical estimates do not", () => {
  const input = fixture(); addOrder(input, "recorded");
  const result = buildModel(input, { supplyMode: "recorded" });
  assert.equal(result.summary.plannedLitres, 10000);
  assert.equal(result.inboundEvents[0].conditional, false);
  assert.match(result.inboundEvents[0].reason, /future commitment/);
});

test("QC accepted but inclusion unresolved cannot be added by either mode or a manual date", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.lots[0].stage = "accepted_unposted";
  input.materialSupply!.lots[0].stockInclusion = "unresolved";
  assert.equal(buildModel(input).summary.plannedLitres, 0);
  assert.equal(buildModel(input, { supplyMode: "recorded" }).summary.plannedLitres, 0);
  assert.throws(() => buildModel(input, { arrivalDates: { "lot:100": "2026-09-16" } }), /cannot take/);
});

test("received stock is counted once and duplicate physical lot identity rejects input", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.stock.byItem["PM-BOTTLE"] = 10000;
  input.materialSupply!.lots[0].stage = "usable";
  input.materialSupply!.lots[0].stockInclusion = "included";
  const result = buildModel(input);
  assert.equal(result.materials.find(row => row.code === "PM-BOTTLE")?.arrivals, 0);
  assert.equal(result.summary.plannedLitres, 10000);
  input.materialSupply!.lots.push({ ...input.materialSupply!.lots[0] });
  assert.throws(() => buildModel(input), /identity/);
});

test("legacy scenario defaults to expected supply without enabling hypothetical new purchases", () => {
  const result = validateScenario({ nightLine: null });
  assert.equal(result.supplyMode, "expected");
  assert.equal(result.allowProposedSupply, false);
});

test("overdue dates and unsupported oil units never silently become usable today", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.orders[0].orderedAt = "2026-09-01";
  input.materialSupply!.expectedReceipts[0].usableExpected = "2026-09-06";
  input.materialSupply!.expectedReceipts[0].qaEstimatedAt = "2026-09-05T03:30:00+05:30";
  input.materialSupply!.expectedReceipts[0].sourceArrivalAt = "2026-09-05T00:00:00+05:30";
  input.materialSupply!.expectedReceipts[0].usableEarliest = "2026-09-06";
  input.materialSupply!.expectedReceipts[0].arrivalExpected = "2026-09-06";
  input.materialSupply!.expectedReceipts[0].arrivalEarliest = "2026-09-06";
  assert.equal(buildModel(input).summary.plannedLitres, 0);
  input.materialSupply!.expectedReceipts[0].unit = "KGS";
  assert.throws(() => buildModel(input), /normalized unit/);
});


test("reconciled supply ignores saved hypothetical purchase switches", () => {
  const result = buildModel(fixture(), { allowProposedSupply: true });
  assert.equal(result.scenario.allowProposedSupply, false);
  assert.equal(result.summary.plannedLitres, 0);
  assert.equal(result.materialSupply?.comparison?.recorded.plannedLitres, 0);
});

test("equivalent unit spelling cannot bypass lot quantity conservation", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.expectedReceipts[0].unit = "pieces";
  input.materialSupply!.expectedReceipts[0].quantity = 10100;
  assert.throws(() => buildModel(input), /exceeds its physical lot/);
});


test("physical child lots cannot exceed the outstanding parent PO", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.lots.push({ ...input.materialSupply!.lots[0], id: "child-extra" });
  assert.throws(() => buildModel(input), /purchase order outstanding/);
});

test("availability before an order is an invalid source chronology", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.orders[0].orderedAt = "2026-09-20";
  assert.throws(() => buildModel(input), /before its purchase order/);
});


test("changed PO content invalidates API model cache even when source timestamp and revision are unchanged", () => {
  const input = fixture(); addOrder(input);
  const scenario = validateScenario(undefined);
  const before = modelCacheKey(input, "live", null, scenario);
  input.materialSupply!.expectedReceipts[0].usableExpected = "2026-09-17";
  input.materialSupply!.expectedReceipts[0].timingVersion = 2;
  input.materialSupply!.expectedReceipts[0].qaEstimatedAt = "2026-09-17T08:00:00+05:30";
  const after = modelCacheKey(input, "live", null, scenario);
  assert.notEqual(before, after);
  assert.equal(after, modelCacheKey(structuredClone(input), "live", null, scenario));
  assert.notEqual(after, modelCacheKey(input, "stale", "QC refresh failed", scenario));
});


test("historical posted receipts do not consume an open PO outstanding balance twice", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.orders[0].orderedQty = 100000;
  input.materialSupply!.orders[0].bookReceivedQty = 90000;
  input.materialSupply!.lots.push({ ...input.materialSupply!.lots[0], id: "past-posted", quantity: 90000, stage: "usable", stockInclusion: "unresolved", receiptId: "past-posted" });
  const result = buildModel(input);
  assert.equal(result.summary.plannedLitres, 10000);
  assert.equal(result.inboundEvents.find(row => row.id === "past-posted")?.included, false);
});


test("a sparse historical sample cannot promise a production restart", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.expectedReceipts[0].sampleCount = 2;
  const result = buildModel(input);
  assert.equal(result.summary.plannedLitres, 0);
  assert.match(result.inboundEvents[0].reason, /Fewer than three/);
});


test("old accepted-unposted or QC-pending history keeps its physical stage without consuming future PO balance", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.orders[0].orderedQty = 100000;
  input.materialSupply!.orders[0].bookReceivedQty = 90000;
  input.materialSupply!.lots.push({ ...input.materialSupply!.lots[0], id: "book-overlap", quantity: 90000, stage: "accepted_unposted", stockInclusion: "unresolved", receiptId: "book-overlap" });
  const result = buildModel(input);
  assert.equal(result.summary.plannedLitres, 10000);
  assert.equal(result.materialSupply?.lots.find(row => row.id === "book-overlap")?.stage, "accepted_unposted");
  assert.equal(result.inboundEvents.find(row => row.id === "book-overlap")?.included, false);
  assert.equal(result.materials.find(row => row.code === "PM-BOTTLE")?.arrivals, 10000);
  input.materialSupply!.lots[1].stage = "qc_pending";
  assert.equal(buildModel(input).summary.plannedLitres, 10000);
  assert.throws(() => buildModel(input, { arrivalDates: { "book-overlap": "2026-09-16" } }), /cannot take/);
});

test("non-piece packaging keeps its normalized source unit for stock and future supply", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.stock.unitByItem = { "PM-BOTTLE": "MTR", "RM-OIL": "L" };
  input.materialSupply!.orders[0].unit = "MTR";
  input.materialSupply!.lots[0].unit = "MTR";
  input.materialSupply!.expectedReceipts[0].unit = "MTR";
  const result = buildModel(input);
  assert.equal(result.summary.plannedLitres, 10000);
  assert.equal(result.materials.find(row => row.code === "PM-BOTTLE")?.unit, "MTR");
});


test("purchasing withholds an exact buy quantity when an issued PO may overlap stock", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.lots[0].stockInclusion = "unresolved";
  input.materialSupply!.expectedReceipts = [];
  const result = buildModel(input);
  const material = result.materials.find(row => row.code === "PM-BOTTLE")!;
  assert.equal(material.proposedQty, null);
  assert.equal(result.summary.plannedLitres, 0);
  assert.equal(material.projectedArrival, null);
  assert.equal(material.leadDays, null);
});

test("split expected receipts are not credited again in procurement alongside their source PO", () => {
  const input = fixture(); addOrder(input);
  input.plan[0].pieces = 15000;
  const result = buildModel(input);
  assert.equal(result.materials.find(row => row.code === "PM-BOTTLE")?.proposedQty, 5000);
});

test("unlinked EXIM and contract overlap withholds a confident new purchase quantity", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.orders.push({ ...input.materialSupply!.orders[0], id: "bulk-contract", code: "RM-OIL", unit: "L", orderedQty: 50000, outstandingQty: 50000, notYetAtGateQty: 50000 });
  input.materialSupply!.lots.push({ ...input.materialSupply!.lots[0], id: "exim-unlinked", orderId: undefined, shipmentId: "shipment", code: "RM-OIL", quantity: 10000, unit: "L", stage: "in_transit" });
  const result = buildModel(input);
  assert.equal(result.materials.find(row => row.code === "RM-OIL")?.proposedQty, null);
  assert.equal(result.materialSupply?.requiredActions.find(row => row.id === "purchase-reconciliation:RM-OIL")?.quantity, null);
});


test("linked accepted-unposted stock overlap does not claim a zero new-purchase need", () => {
  const input = fixture(); addOrder(input);
  input.plan[0].pieces = 20000;
  input.materialSupply!.stock.byItem["PM-BOTTLE"] = 10000;
  input.materialSupply!.lots[0].stage = "accepted_unposted";
  input.materialSupply!.lots[0].stockInclusion = "unresolved";
  const result = buildModel(input);
  assert.equal(result.summary.plannedLitres, 10000);
  assert.equal(result.materials.find(row => row.code === "PM-BOTTLE")?.proposedQty, null);
  assert.equal(result.inboundEvents[0].included, false);
});

test("fully reconciled undated PO remains purchasing coverage without becoming production stock", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.expectedReceipts = [];
  const result = buildModel(input);
  assert.equal(result.summary.plannedLitres, 0);
  assert.equal(result.materials.find(row => row.code === "PM-BOTTLE")?.proposedQty, 0);
});


test("cached delivery cadence and date-rounded QA cannot enter default supply", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.expectedReceipts[0].basis = "supplier_item_history";
  assert.equal(buildModel(input).summary.plannedLitres, 0);
  input.materialSupply!.expectedReceipts[0].basis = "qc_history";
  delete input.materialSupply!.expectedReceipts[0].timingVersion;
  assert.equal(buildModel(input).summary.plannedLitres, 0);
});

test("missed source ETA blocks a future QA estimate until source date is revised", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.orders[0].orderedAt = "2026-09-01";
  input.materialSupply!.lots[0].stage = "in_transit";
  const receipt = input.materialSupply!.expectedReceipts[0];
  receipt.basis = "shipment_eta"; receipt.sourceArrivalAt = "2026-09-06"; receipt.arrivalTimeKnown = false;
  assert.equal(buildModel(input).summary.plannedLitres, 0);
  receipt.sourceArrivalAt = "2026-09-07";
  assert.equal(buildModel(input).summary.plannedLitres, 10000);
});

test("cached factory oil is removed exactly once without mutating the source", () => {
  const input = fixture(); addOrder(input);
  input.materialSupply!.stock.byItem["RM-OIL"] = 10000;
  input.materialSupply!.stock.byWarehouse = { "BH-LO": [{code:"RM-OIL", included:true, normalizedQuantity:6000}] };
  const model = buildModel(input);
  assert.equal(model.materials.find(row => row.code === "RM-OIL")?.opening, 4000);
  assert.equal(model.materialSupply?.comparison?.expected.plannedLitres, model.summary.plannedLitres);
  assert.equal(input.materialSupply!.stock.byItem["RM-OIL"], 10000);
});


test("source still QC pending after predicted approval blocks a later daily credit", () => {
  const input = fixture(); addOrder(input);
  input.meta.as_of = "2026-09-09T10:00:00+05:30";
  input.materialSupply!.lots[0].stage = "qc_pending";
  input.materialSupply!.lots[0].observedAt = "2026-09-09T09:00:00+05:30";
  input.materialSupply!.expectedReceipts[0].qaEstimatedAt = "2026-09-08T23:00:00+05:30";
  input.materialSupply!.expectedReceipts[0].sourceArrivalAt = "2026-09-08T08:00:00+05:30";
  const result = buildModel(input);
  assert.equal(result.summary.plannedLitres, 0);
  assert.match(result.inboundEvents[0].reason, /latest source observation still says QC pending/);
  input.materialSupply!.lots[0].observedAt = "2026-09-08T20:00:00+05:30";
  assert.equal(buildModel(input).summary.plannedLitres, 0); // Historical QA estimate has already passed; stale observation cannot confirm release.
});


test("hour-level contract rejects missing metadata and planning before estimated QA", () => {
  for (const patch of [{qaEstimatedAt:null}, {qaMedianHours:-1}, {sourceArrivalAt:null}, {arrivalTimeKnown:false}, {qaEstimatedAt:"2026-09-20T03:30:00+05:30"}]) {
    const input = fixture(); addOrder(input);
    Object.assign(input.materialSupply!.expectedReceipts[0],patch);
    assert.throws(() => buildModel(input), /timing metadata|before its estimated QA/);
  }
});

test('QC at noon uses remaining hours that day; no extra day and full batch waits until ready', () => {
  const input=fixture(); addOrder(input);
  const r=input.materialSupply!.expectedReceipts[0];
  Object.assign(r,{timingVersion:2,sourceArrivalAt:'2026-09-15T08:00:00+05:30',qaEstimatedAt:'2026-09-15T12:00:00+05:30',qaMedianHours:4,usableExpected:'2026-09-15'});
  const model=buildModel(input,{nightLine:null});
  const runs=model.days.find(d=>d.date==='2026-09-15')!.runs;
  assert.ok(runs.length>0);
  for(const run of runs){ assert.ok(Date.parse(run.startsAt!)>=Date.parse(r.qaEstimatedAt!)); assert.ok(Date.parse(run.endsAt!)<=Date.parse('2026-09-15T18:00:00+05:30')); }
  assert.equal(model.materials.find(r=>r.code==='PM-BOTTLE')!.arrivals,10000);
});
test('Sunday QA availability waits for Monday because Sunday is closed',()=>{
  const input=fixture();addOrder(input);const r=input.materialSupply!.expectedReceipts[0];
  Object.assign(r,{timingVersion:2,sourceArrivalAt:'2026-09-13T08:00:00+05:30',qaEstimatedAt:'2026-09-13T10:00:00+05:30',qaMedianHours:2,usableEarliest:'2026-09-13',usableExpected:'2026-09-13',arrivalEarliest:'2026-09-13',arrivalExpected:'2026-09-13'});
  const model=buildModel(input,{nightLine:null});
  assert.equal(model.days.find(d=>d.date==='2026-09-13')!.productionLitres,0);
  assert.ok(model.days.find(d=>d.date==='2026-09-14')!.productionLitres>0);
});
test('temporary packaging estimate is explicit, expires, and recorded comparison excludes it',()=>{
  const input=fixture();addOrder(input);const r=input.materialSupply!.expectedReceipts[0];
  r.basis='temporary_packaging_estimate';r.temporaryUntil='2026-09-10';
  assert.ok(buildModel(input).summary.plannedLitres>0);
  assert.equal(buildModel(input,{includePackagingEstimates:false}).summary.plannedLitres,0);
  assert.equal(buildModel(input,{supplyMode:'recorded'}).summary.plannedLitres,0);
  input.meta.as_of='2026-09-11T00:00:00+05:30';
  assert.equal(buildModel(input).summary.plannedLitres,0);
});

test('today at 16:00 has only two day hours; after 18:00 cannot backdate production',()=>{
  for(const hour of [16,19]){
    const input=fixture();input.meta.as_of=`2026-09-07T${hour}:00:00+05:30`;
    input.materialSupply!.stock.byItem['PM-BOTTLE']=10000;
    const today=buildModel(input,{nightLine:null}).days[0];
    if(hour===19) assert.equal(today.productionLitres,0);
    for(const run of today.runs){assert.ok(Date.parse(run.startsAt!)>=Date.parse(input.meta.as_of));assert.ok(run.hours<=2);assert.ok(Date.parse(run.endsAt!)<=Date.parse('2026-09-07T18:00:00+05:30'));}
  }
});
test('night can consume next calendar date readiness once, without lending it to day work',()=>{
  const input=fixture();addOrder(input);const r=input.materialSupply!.expectedReceipts[0];
  Object.assign(r,{timingVersion:2,sourceArrivalAt:'2026-09-15T20:00:00+05:30',qaEstimatedAt:'2026-09-16T00:00:00+05:30',qaMedianHours:4,usableExpected:'2026-09-16'});
  const model=buildModel(input,{nightLine:'JP Machine'});
  const before=model.days.find(d=>d.date==='2026-09-15')!;
  assert.ok(before.productionLitres>0);
  for(const run of before.runs){assert.equal(run.dayHours,0);assert.ok(Date.parse(run.startsAt!)>=Date.parse(r.qaEstimatedAt!));}
  const pm=model.materials.find(m=>m.code==='PM-BOTTLE')!;
  assert.equal(pm.arrivals,10000);assert.equal(pm.consumed,10000);assert.equal(pm.remaining,0);
});

test('same product resumes after noon QA without a new campaign or second setup',()=>{
  const input=fixture();addOrder(input);input.materialSupply!.stock.byItem['PM-BOTTLE']=5000;
  input.plan[0].sku='SUNFLOWER POUCH';input.plan[0].category='SUNFLOWER';input.plan[0].pack_type='POUCH';input.items['PM-BOTTLE'].name='POUCH FILM';
  input.meta.as_of='2026-09-15T07:00:00+05:30';const r=input.materialSupply!.expectedReceipts[0];
  Object.assign(r,{quantity:5000,timingVersion:2,sourceArrivalAt:'2026-09-15T08:00:00+05:30',qaEstimatedAt:'2026-09-15T12:00:00+05:30',qaMedianHours:4,usableExpected:'2026-09-15'});
  const model=buildModel(input,{nightLine:null});const runs=model.days[0].runs;
  assert.equal(model.days[0].productionLitres,10000);
  assert.equal(runs.length,2);assert.equal(runs[0].code,runs[1].code);
  assert.equal(runs[1].setupHours,0);
  assert.ok(Date.parse(runs[1].startsAt!)>=Date.parse(r.qaEstimatedAt!));
  assert.equal(runs.reduce((s,r)=>s+r.materials.find(m=>m.code==='PM-BOTTLE')!.quantity,0),10000);
});
test('manual day cannot move arrival earlier; same day preserves QA hour',()=>{
  const input=fixture();addOrder(input);const r=input.materialSupply!.expectedReceipts[0];
  Object.assign(r,{timingVersion:2,sourceArrivalAt:'2026-09-15T08:00:00+05:30',qaEstimatedAt:'2026-09-17T12:00:00+05:30',qaMedianHours:52,usableExpected:'2026-09-17'});
  assert.throws(()=>buildModel(input,{arrivalDates:{'lot:100':'2026-09-14'}}),/cannot precede/);
  const model=buildModel(input,{nightLine:null,arrivalDates:{'lot:100':'2026-09-17'}});
  for(const run of model.days.find(d=>d.date==='2026-09-17')!.runs) assert.ok(Date.parse(run.startsAt!)>=Date.parse(r.qaEstimatedAt!));
});

test('Saturday night and month-end stop at midnight even if material is ready later',()=>{
  for(const [date,next] of [['2026-09-12','2026-09-13'],['2026-09-30','2026-10-01']]){
    const input=fixture();input.meta.as_of=`${date}T07:00:00+05:30`;
    input.plan[0].pieces=200000;input.materialSupply!.stock.byItem['PM-BOTTLE']=200000;input.materialSupply!.stock.byItem['RM-OIL']=200000;
    const model=buildModel(input,{nightLine:'JP Machine'});
    for(const run of model.days[0].runs) assert.ok(Date.parse(run.endsAt!)<=Date.parse(`${next}T00:00:00+05:30`));
    if(date==='2026-09-12')assert.equal(model.days[1].productionLitres,0);
  }
});

test('manual usable day for undated QC cannot precede its recorded evening arrival',()=>{
  const input=fixture();addOrder(input);input.materialSupply!.expectedReceipts=[];
  const lot=input.materialSupply!.lots[0];lot.stage='qc_pending';lot.arrivalDate='2026-09-15T18:00:00+05:30';
  const model=buildModel(input,{arrivalDates:{'lot:100':'2026-09-15'},nightLine:null});
  assert.equal(model.days.find(d=>d.date==='2026-09-15')!.productionLitres,0);
  assert.ok(Date.parse(model.inboundEvents[0].readyAt!)>=Date.parse(lot.arrivalDate));
});
test('waiting until noon does not avoid paying the started day session',()=>{
  const input=fixture();addOrder(input);input.supplements={labourPerSession:{'JP Machine':500}};
  const r=input.materialSupply!.expectedReceipts[0];Object.assign(r,{timingVersion:2,sourceArrivalAt:'2026-09-15T08:00:00+05:30',qaEstimatedAt:'2026-09-15T12:00:00+05:30',qaMedianHours:4,usableExpected:'2026-09-15'});
  const run=buildModel(input,{nightLine:null}).days.find(d=>d.date==='2026-09-15')!.runs[0];
  assert.equal(run.labourCost,500);
});
