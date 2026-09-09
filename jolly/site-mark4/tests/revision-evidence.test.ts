import test from "node:test";
import assert from "node:assert/strict";
import { buildModel } from "../lib/model.ts";
import { activeOrder, evaluateInbound, grossDemandBook, recordedLabour, withActualValues } from "../lib/evidence.ts";
import type { InboundEvent, Mark4Input, Order } from "../lib/types.ts";

function fixture(): Mark4Input {
  return { schemaVersion: 1, meta: { as_of: "2026-09-07T07:00:00+05:30" }, plan: [{ code: "A", sku: "MUSTARD A", category: "MUSTARD", pack_type: "PET", litres_per_piece: 1, pieces: 100 }], bom: { A: [["RM-OIL", 1], ["PM-BOTTLE", 1]], B: [["RM-OIL", 1], ["PM-BOTTLE", 1]] }, blends: {}, items: { A: { name: "MUSTARD A", uom: "PCS" }, B: { name: "MUSTARD B", uom: "PCS" }, "RM-OIL": { name: "OIL", uom: "LTR" }, "PM-BOTTLE": { name: "PET BOTTLE 1 LTR 26 GM", uom: "PCS" } }, realise: { A: 100, B: 200 }, valuation: { asOf: "2026-09-06", priceBasis: "Verified per-SKU test price", litresPerPiece: { A: 1, B: 1 }, rupeesPerLitre: { A: 100, B: 200 } }, opening: { stock: { "RM-OIL": 1000, "PM-BOTTLE": 1000 }, fg: {}, fg_other_l: 0, standing_l: 0 }, orders: [], inbound_prebooked: {}, lines: { "JP Machine": { "1L": 100 } }, history: { days: [], missing_dates: [], status: "partial" }, sources: [] };
}
const order = (patch: Partial<Order> = {}): Order => ({ docnum: "PO", sourceLineId: "PO:1", date: "2026-08-01", due: "2026-08-30", code: "B", pieces: 40, packLitres: 1, channel: "OIL", _src: "OMS", expiresAt: "2026-09-30", status: "OPEN", ...patch });
const event = (patch: Partial<InboundEvent> = {}): InboundEvent => ({ id: "inbound-1", source: "factory_po", code: "PM-BOTTLE", quantity: 100, unit: "PCS", orderedAt: "2026-09-01", expectedAt: "2026-09-10", asOf: "2026-09-07", dateBasis: "supplier_due", status: "open", confidence: "confirmed", stockIncluded: false, ...patch });

test("actual daily value uses independent SKU compositions and exposes every price line", () => {
  const input = fixture();
  const [day] = withActualValues([{ date: "2026-09-06", made_booked_l: 100, made_mes_l: 40, booked_by_item: { A: 60, B: 40 }, mes_by_item_l: { B: 40 }, complete: true }], input);
  assert.equal(day.bookedValue?.value, 14000);
  assert.equal(day.mesValue?.value, 8000);
  assert.equal(day.bookedValue?.lines.find(l => l.code === "B")?.rupeesPerLitre, 200);
  assert.equal(day.bookedValue?.asOf, "2026-09-06");
  assert.match(day.mesValue!.basis, /must never be added/);
});

test("positive MES without per-SKU coverage is unvalued; observed zero stays zero", () => {
  const [missing, zero] = withActualValues([
    { date: "2026-09-05", made_booked_l: null, made_mes_l: 400, booked_by_item: null, complete: false },
    { date: "2026-09-06", made_booked_l: 0, made_mes_l: 0, booked_by_item: {}, complete: true },
  ], fixture());
  assert.equal(missing.mesValue?.value, null);
  assert.equal(missing.mesValue?.unvaluedLitres, 400);
  assert.equal(missing.mesValue?.knownValue, 0);
  assert.equal(zero.mesValue?.value, 0);
  assert.equal(zero.mesValue?.coverage, "complete");
});

test("composition mismatch cannot be passed off as a fully valued production total", () => {
  const [day] = withActualValues([{ date: "2026-09-05", made_booked_l: 100, made_mes_l: null, booked_by_item: { A: 40, UNKNOWN: 10 }, complete: true }], fixture());
  assert.equal(day.bookedValue?.value, null);
  assert.equal(day.bookedValue?.knownValue, 4000);
  assert.equal(day.bookedValue?.unvaluedLitres, 60);
  assert.equal(day.bookedValue?.reconciled, false);
});

test("recorded labour is a covered run subtotal, never manufactured into a session rate", () => {
  const input = fixture();
  input.supplements = { recordedLabour: { asOf: "2026-09-07", windowFrom: "2026-09-01", windowTo: "2026-09-06", basis: "Factory recorded run cost", runs: [{ id: "1", date: "2026-09-01", line: "JP Machine", code: "A", litres: 100, labourCost: 200 }, { id: "2", date: "2026-09-02", line: "JP Machine", code: "A", litres: 50, labourCost: null }] } };
  const result = recordedLabour(input, "JP Machine");
  assert.equal(result.totalCost, 200);
  assert.equal(result.costPerLitre, 2);
  assert.equal(result.missingCostRunCount, 1);
  assert.equal(result.litres, 150);
  assert.equal(buildModel(input, { nightLine: null }).lines[0].labourPerSession, null);
});

test("overdue unexpired non-plan demand is scheduled; later-due and expired demand is not forced into this month", () => {
  const input = fixture(); input.plan[0].pieces = 10000; input.opening.stock["RM-OIL"] = 100000; input.opening.stock["PM-BOTTLE"] = 100000;
  input.orders = [order({ pieces: 4000 }), order({ docnum: "FUTURE", sourceLineId: "2", code: "A", due: "2026-10-03", expiresAt: "2026-10-10", pieces: 999 }), order({ docnum: "EXPIRED", sourceLineId: "3", pieces: 999, expiresAt: "2026-09-06" })];
  const model = buildModel(input, { nightLine: null });
  assert.equal(model.products.find(p => p.code === "B")?.requiredPieces, 4000);
  assert.equal(model.products.find(p => p.code === "B")?.plannedPieces, 4000);
  assert.equal(model.products.find(p => p.code === "A")?.requiredPieces, 10000);
  assert.equal(activeOrder(input.orders[0], input.meta.as_of), true);
  assert.equal(activeOrder(input.orders[2], input.meta.as_of), false);
});

test("terminal order states stay out while partial fulfilment remains active", () => {
  for (const status of ["COMPLETED", "REJECTED", "BILLING_REJECTED", "CANCELLED", "FULLY_DELIVERED"]) assert.equal(activeOrder(order({ status }), "2026-09-07"), false);
  assert.equal(activeOrder(order({ status: "PARTIALLY_FULFILLED" }), "2026-09-07"), true);
});

test("gross source book stays independent of plan, stock netting and accepted-versus-requested quantities", () => {
  const input = fixture();
  input.opening.fg = { A: 20 };
  input.orders = [order({ code: "A", pieces: 100 }), order({ docnum: "B", sourceLineId: "B:1" })];
  input.demandBook = grossDemandBook(input);
  input.demandBook.coverage = "complete";
  Object.assign(input.demandBook.online, { grossOpenLitres: 10000, acceptedOpenLitres: 9000, planningDueLitres: 6000, acceptedPlanningDueLitres: 5000 });
  Object.assign(input.demandBook.trade, { grossOpenLitres: 1000, planningDueLitres: 200 });
  const model = buildModel(input, { nightLine: null });
  assert.equal(model.demandBook.online.grossOpenLitres, 10000);
  assert.equal(model.demandBook.trade.grossOpenLitres, 1000);
  assert.equal(model.planningBridge.grossDueLitres, 6200);
  assert.equal(model.planningBridge.explicitUnacceptedLitres, 1000);
  assert.equal(model.planningBridge.mappedLitres, 140);
  assert.equal(model.planningBridge.stockCoveredLitres, 20);
  assert.equal(model.planningBridge.netMakeLitres, 120);
  assert.equal(model.products.find(p => p.code === "A")?.requiredPieces, 100, "Monthly projection still covers the overlapping PO, not projection+PO.");
});

test("outside-Oil demand is separate from unmapped demand and unreadable active headers prevent a complete total", () => {
  const input = fixture(); input.orders = [order()];
  input.demandBook = grossDemandBook(input);
  Object.assign(input.demandBook.online, { planningDueLitres: 1000, acceptedPlanningDueLitres: 900, outsideOilScopeLitres: 200, outsideOilScopeAcceptedLitres: 180, outsideOilScopePlanningDueLitres: 120, outsideOilScopeAcceptedPlanningDueLitres: 100 });
  Object.assign(input.demandBook.trade, { planningDueLitres: 100, unknownActiveOrderCount: 5, isComplete: false, unknownActiveOrders: [{ id: "unknown-header", status: "OPEN", createdAt: "2026-09-01", companyScope: "unknown", litres: null }] });
  const model = buildModel(input, { nightLine: null });
  assert.equal(model.planningBridge.knownGrossDueLitres, 1100);
  assert.equal(model.planningBridge.grossDueLitres, null);
  assert.equal(model.planningBridge.unknownActiveOrderCount, 5);
  assert.equal(model.planningBridge.outsideOilScopeLitres, 100, "Use due-scoped outside-Oil accepted quantity, not its all-month volume.");
  assert.equal(model.planningBridge.unmappedLitres, 860);
  assert.equal(model.planningBridge.explicitUnacceptedLitres, 100);
  assert.equal(model.demandBook.trade.unknownActiveOrders?.[0].litres, null);
});

test("real dated commitments unlock production while QC/received/undated/overdue entries remain explicit", () => {
  const input = fixture(); input.plan[0].pieces = 10000; input.opening.stock["RM-OIL"] = 100000; input.opening.stock["PM-BOTTLE"] = 100000; input.opening.stock["PM-BOTTLE"] = 0;
  input.inboundEvents = [event({ quantity: 10000 }), event({ id: "qc", source: "qc", status: "qc", stockIncluded: true }), event({ id: "no-date", expectedAt: null, dateBasis: "unverified" }), event({ id: "past", expectedAt: "2026-09-04" }), event({ id: "done", status: "received" })];
  const model = buildModel(input, { nightLine: null });
  assert.equal(model.days.filter(d => d.date < "2026-09-10").flatMap(d => d.runs).length, 0);
  assert.equal(model.days.find(d => d.date === "2026-09-10")?.productionLitres, 10000);
  assert.equal(model.materials.find(m => m.code === "PM-BOTTLE")?.arrivals, 10000);
  assert.equal(model.inboundEvents.filter(e => e.included).length, 1);
  assert.match(model.inboundEvents.find(e => e.id === "past")!.reason, /not assumed today/);
});

test("estimated issued PO dates are conditional commitments, not new purchase toggles", () => {
  const input = fixture(); input.inboundEvents = [event({ confidence: "estimated", dateBasis: "observed_lead" })];
  const [result] = evaluateInbound(input, "2026-09-30");
  assert.equal(result.included, true);
  assert.equal(result.conditional, true);
});

test("assumed delivery dates unlock existing undated commitments only from the selected day", () => {
  const input = fixture(); input.plan[0].pieces = 10000; input.opening.stock["RM-OIL"] = 100000; input.opening.stock["PM-BOTTLE"] = 100000; input.opening.stock["PM-BOTTLE"] = 0;
  input.inboundEvents = [event({ quantity: 10000, expectedAt: null, dateBasis: "unverified", confidence: "unknown" })];
  const strict = buildModel(input, { nightLine: null });
  assert.equal(strict.summary.plannedLitres, 0);
  assert.equal(strict.materials.find(m => m.code === "PM-BOTTLE")?.proposedQty, 0, "Do not buy a duplicate quantity already outstanding on a PO.");
  const assumed = buildModel(input, { nightLine: null, arrivalDates: { "inbound-1": "2026-09-16" } });
  assert.equal(assumed.days.filter(d => d.date < "2026-09-16").flatMap(d => d.runs).length, 0);
  assert.equal(assumed.days.find(d => d.date === "2026-09-16")?.productionLitres, 10000);
  assert.equal(assumed.inboundEvents[0].expectedAt, null);
  assert.equal(assumed.inboundEvents[0].appliedAt, "2026-09-16");
  assert.equal(assumed.inboundEvents[0].conditional, true);
});

test("unknown, received, stock-included and out-of-horizon dates cannot create material", () => {
  const input = fixture(); input.inboundEvents = [event()];
  assert.throws(() => buildModel(input, { arrivalDates: { missing: "2026-09-10" } }), /no longer exists/);
  assert.throws(() => buildModel(input, { arrivalDates: { "inbound-1": "2026-10-01" } }), /displayed planning month/);
  for (const patch of [{ stockIncluded: true }, { stockIncluded: null }, { status: "received" as const }, { status: "cancelled" as const }]) {
    input.inboundEvents = [event(patch)];
    assert.throws(() => buildModel(input, { arrivalDates: { "inbound-1": "2026-09-10" } }), /not eligible/);
  }
});

test("incoming identities deduplicate once and conflicting quantities fail validation", () => {
  const input = fixture(); input.inboundEvents = [event(), event()];
  assert.equal(evaluateInbound(input, "2026-09-30").length, 1);
  input.inboundEvents = [event(), event({ quantity: 200 })];
  assert.throws(() => evaluateInbound(input, "2026-09-30"), /Conflicting incoming/);
});

test("source 1L demand cannot inflate into inherited FG0000328 200L drums", () => {
  const input = fixture();
  input.plan.push({ code: "FG0000328", sku: "SANO POMACE 200 L", category: "POMACE", pack_type: "DRUM", litres_per_piece: 200, pieces: 0 });
  input.orders = [order({ code: "FG0000328", pieces: 7231, packLitres: 1, remainingLitres: 7231, code_mapping_verified: true })];
  const model = buildModel(input, { nightLine: null });
  assert.equal(model.planningBridge.mappedLitres, 0);
  assert.equal(model.planningBridge.unmappedLitres, 7231);
  assert.equal(model.planningBridge.quarantinedOrders[0].litres, 7231);
  assert.match(model.planningBridge.quarantinedOrders[0].reason, /200 L/);
});

test("same-pack unverified oil identity cannot consume FG or become a real order", () => {
  const input = fixture();
  input.opening.fg.A = 100;
  input.orders = [order({ code: "A", code_mapping_verified: false, mappingIssue: "Source EXTRA LIGHT maps to planner POMACE", pieces: 40, remainingLitres: 40 })];
  const model = buildModel(input, { nightLine: null });
  assert.equal(model.planningBridge.mappedLitres, 0);
  assert.equal(model.planningBridge.stockCoveredLitres, 0);
  assert.equal(model.planningBridge.unmappedLitres, 40);
});

test("current factory conflicts also hold forecast recipes and inherited actual prices", () => {
  const input = fixture();
  input.plan[0].sku = "POMACE 1 L";
  input.factoryIdentity = { asOf: "2026-09-07", items: { A: { name: "EXTRA LIGHT OLIVE 1 L", packLitres: 1, uom: "PCS" } } };
  input.opening.fg.A = 100;
  input.orders = [order({ code: "A", code_mapping_verified: true, remainingLitres: 40 })];
  const model = buildModel(input, { nightLine: null });
  const product = model.products.find(p => p.code === "A")!;
  assert.equal(product.plannedPieces, 0);
  assert.equal(product.fgPieces, 0);
  assert.equal(product.valuePerLitre, null);
  assert.match(product.exclusionReason!, /Identity hold/);
  const [day] = withActualValues([{ date: "2026-09-06", made_booked_l: 40, made_mes_l: 40, booked_by_item: { A: 40 }, mes_by_item_l: { A: 40 }, complete: true }], input);
  assert.equal(day.bookedValue?.value, null);
  assert.equal(day.mesValue?.unvaluedLitres, 40);
});

test("mapped Oil demand cannot exceed the independent accepted due book", () => {
  const input = fixture();
  input.orders = [order({ pieces: 40, remainingLitres: 40 })];
  input.demandBook = grossDemandBook(input);
  input.demandBook.online.acceptedPlanningDueLitres = 10;
  input.demandBook.trade.planningDueLitres = 0;
  assert.throws(() => buildModel(input, { nightLine: null }), /exceeds the independently reconciled/);
});
