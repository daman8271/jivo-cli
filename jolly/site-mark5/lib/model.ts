import { MaterialCalendar, type TimedReceipt } from "./material-calendar.ts";
import { eximOnlyStock, reconciledInbound, validateMaterialSupply } from "./material-supply.ts";
import type { ActualDay, Blocker, Day, Mark4Input, Mark4Model, Material, Order, Product, Recipe, Run, Scenario } from "./types.ts";
import { activeOrder, currentMonthOrder, evaluateInbound, comparableInboundUnit, grossDemandBook, recordedLabour, withActualValues } from "./evidence.ts";
import { DAY_TARGET, DEFAULT_SCENARIO, eligibility, LINE_IDS, rateFor, ratesForLine, PLANNING_SPEEDS, rulebook, STORAGE_LIMIT, PRODUCT_CHANGE_SETUP_HOURS, MIN_NEW_CAMPAIGN_HOURS, campaignEligible } from "./rules.ts";

import { identityConflict, orderIdentityIssue, orderLitres } from "./identity.ts";

const EPS = 1e-7;
const n = (v: unknown): number => typeof v === "number" && Number.isFinite(v) ? v : 0;
const pos = (v: unknown): number => Math.max(0, n(v));
const iso = (v: string) => v.slice(0, 10);
function addDays(date: string, count: number): string { const d = new Date(`${date}T12:00:00Z`); d.setUTCDate(d.getUTCDate() + count); return d.toISOString().slice(0, 10); }
function dateRange(start: string, end: string): string[] { const out: string[] = []; for (let d = start; d <= end && out.length < 31; d = addDays(d, 1)) out.push(d); return out; }
function sum(xs: number[]): number { return xs.reduce((a, b) => a + b, 0); }

export { validateScenario } from "./scenario.ts";
import { validateScenario } from "./scenario.ts";

export function validateInput(value: unknown): asserts value is Mark4Input {
  if (!value || typeof value !== "object") throw new Error("Input is missing.");
  const i = value as Mark4Input;
  if (i.schemaVersion !== 1 || !/^\d{4}-\d{2}-\d{2}/.test(i.meta?.as_of ?? "") || Number.isNaN(Date.parse(i.meta.as_of))) throw new Error("Input version/date is invalid.");
  if (!Array.isArray(i.plan) || i.plan.length > 500 || !i.opening?.stock || !i.opening?.fg || !i.bom || !i.items || !i.lines || !Array.isArray(i.orders) || i.orders.length > 25000 || !Array.isArray(i.sources)) throw new Error("Input is incomplete or exceeds supported size.");
  if (!i.history || !Array.isArray(i.history.days) || !Array.isArray(i.history.missing_dates)) throw new Error("History coverage is missing.");
  if (i.materialSupply) validateMaterialSupply(i.materialSupply);
  for (const row of i.plan) if (!row.code || !Number.isFinite(row.pieces) || row.pieces < 0 || !Number.isFinite(row.litres_per_piece) || row.litres_per_piece <= 0) throw new Error("Plan units are invalid.");
  for (const recipe of [...Object.values(i.bom), ...Object.values(i.blends ?? {})]) if (!Array.isArray(recipe) || recipe.length > 100 || recipe.some(r => !Array.isArray(r) || typeof r[0] !== "string" || !Number.isFinite(r[1]) || r[1] <= 0)) throw new Error("Recipe coefficients are invalid.");
}

function physicalRecipe(code: string, input: Mark4Input): { container: Product["container"]; grams: number | null; carton: number | null; containersPerPiece: number; notes: string[] } {
  const recipe = input.bom[code] ?? [];
  const primary = recipe.filter(([c, q]) => q >= .5 && !/carton|cap|top|strip|label|sleeve|seal|wad|plug|ring/i.test(input.items[c]?.name ?? "") && (!/handle/i.test(input.items[c]?.name ?? "") || /bottle|jar|tin|jerry/i.test(input.items[c]?.name ?? "")));
  const names = primary.map(([c]) => input.items[c]?.name ?? "");
  let container: Product["container"] = "unknown";
  if (names.some(s => /\bdrum\b/i.test(s))) container = "drum";
  else if (names.some(s => /\btin\b/i.test(s))) container = "tin";
  else if (names.some(s => /bottle|\bjar\b|\bcan\b|jerry|hdpe/i.test(s))) container = "bottle";
  else if (recipe.some(([c]) => /pouch|film|laminat/i.test(input.items[c]?.name ?? ""))) container = "pouch";
  const bottle = names.find(s => /bottle|hdpe/i.test(s)) ?? "";
  const grams = bottle.match(/(?:^|\D)(\d+(?:\.\d+)?)\s*(?:GM|GRAM|GMS|G)\b/i);
  const cartonRow = recipe.find(([c]) => /carton|corrugat|\bcase\b/i.test(input.items[c]?.name ?? ""));
  return { container, grams: grams ? Number(grams[1]) : null, carton: cartonRow && cartonRow[1] > 0 ? Math.round(1 / cartonRow[1]) : null, containersPerPiece: primary.find(([c]) => /bottle|tin|pouch|jar|drum|jerry/i.test(input.items[c]?.name ?? ""))?.[1] ?? 1, notes: container === "unknown" ? ["Primary container could not be identified safely from recipe components."] : [] };
}

type WorkingOrder = Omit<Order, "code"> & { code: string; remaining: number };
export function normalizeProducts(input: Mark4Input, provisionalRecipes = false): { products: Product[]; orders: WorkingOrder[]; historyComplete: boolean; actuals: ActualDay[] } {
  const start = iso(input.meta.as_of), month = start.slice(0, 7);
  const readDays = input.history.days.filter(d => d.date < start && d.date.startsWith(month));
  const actuals: ActualDay[] = dateRange(`${month}-01`, addDays(start, -1)).map(date => readDays.find(d => d.date === date) ?? { date, made_mes_l: null, made_booked_l: null, booked_by_item: null, complete: false, notes: ["Not read: this completed calendar day has no source record."] });
  const expectedDates = dateRange(`${month}-01`, addDays(start, -1));
  const historyComplete = expectedDates.every(date => actuals.some(d => d.date === date && d.complete && d.booked_by_item !== null)) && !input.history.missing_dates.some(d => d < start && d.startsWith(month));
  const booked: Record<string, number> = {};
  for (const d of actuals) for (const [code, qty] of Object.entries(d.booked_by_item ?? {})) booked[code] = (booked[code] ?? 0) + pos(qty);
  const transitions = new Map((input.supplements?.cartonTransitions ?? []).filter(t => input.bom[t.to] && input.items[t.to]).map(t => [t.from, t]));
  const canonical = (code: string) => transitions.get(code)?.to ?? code;
  const seenOrders = new Set<string>();
  const orders: WorkingOrder[] = [...input.orders, ...(input.backlog ?? [])].filter((o): o is Order & { code: string } => typeof o.code === "string" && o.code.length > 0).filter(o => {
    if (!activeOrder(o, input.meta.as_of) || !currentMonthOrder(o, input.meta.as_of)) return false;
    if (o.channel === "BEVERAGES" || o.channel === "MART" || (o._src === "OMS" && o.channel !== "OIL")) return false;
    if (o.channel === "FORECAST" || o._src === "FORECAST" || o.docnum.startsWith("FCST") || o.pieces <= 0) return false;
    if (orderIdentityIssue(input, o)) return false;
    const k = o.sourceLineId ?? `${o.docnum}:${o.code}:${o.due}:${o.pieces}`;
    if (seenOrders.has(k)) return false; seenOrders.add(k); return true;
  }).map(o => ({ ...o, code: canonical(o.code), date: o._src === "ECOM-PO" ? start : o.date, remaining: pos(o.pieces) })).sort((a, b) => Number(a._src === "ECOM-PO" || a.is_exact_sku_due === false) - Number(b._src === "ECOM-PO" || b.is_exact_sku_due === false) || a.due.localeCompare(b.due) || a.docnum.localeCompare(b.docnum));
  const grouped = new Map<string, typeof input.plan>();
  for (const row of input.plan) { const code = canonical(row.code); grouped.set(code, [...(grouped.get(code) ?? []), row]); }
  // Include real current-month demand outside the sheet when its source pack conversion is verified.
  for (const order of orders) if (!grouped.has(order.code)) {
    const pack = input.factoryIdentity?.items[order.code]?.packLitres ?? input.valuation?.litresPerPiece[order.code] ?? order.packLitres;
    if (typeof pack === "number" && Number.isFinite(pack) && pack > 0) grouped.set(order.code, [{ code: order.code, sku: input.items[order.code]?.name ?? order.code, category: input.items[order.code]?.name ?? "Unclassified", pack_type: "unknown", litres_per_piece: pack, pieces: 0 }]);
  }
  const products: Product[] = [];
  for (const [code, rows] of grouped) {
    const originals = [...new Set([...rows.map(r => r.code), code])];
    let descriptor = physicalRecipe(code, input);
    let recipe = input.bom[code] ?? [];
    let conditionalRecipe = false;
    if (provisionalRecipes && descriptor.carton === 16 && rows[0].litres_per_piece === 1 && recipe.some(([c]) => c === "PM0000121")) {
      const reference = input.bom["FG0000461"] ?? [];
      const closure = (r: Recipe) => r.filter(([c]) => /cap|closure|wad|plug/i.test(input.items[c]?.name ?? "")).map(([c,q]) => `${c}:${q}`).sort().join(",");
      const hasExtraFit = recipe.some(([c]) => /insert|sleeve/i.test(input.items[c]?.name ?? ""));
      const oldCartons = recipe.filter(([c]) => /carton|corrugat|\bcase\b/i.test(input.items[c]?.name ?? ""));
      if (reference.some(([c]) => c === "PM0000121") && reference.some(([c,q]) => c === "PM0000914" && Math.abs(q-.05)<EPS) && closure(recipe) && closure(recipe) === closure(reference) && !hasExtraFit && oldCartons.length === 1 && oldCartons[0][0] === "PM0000003") {
        recipe = recipe.filter(([c]) => c !== oldCartons[0][0]).concat([["PM0000914", .05]]); conditionalRecipe = true; descriptor = { ...descriptor, carton: 20 };
      }
    }
    const first = rows[0], packLitres = first.litres_per_piece;
    const transition = rows.map(r => transitions.get(r.code)).find(Boolean);
    const monthlyPieces = sum(rows.map(r => pos(r.pieces)));
    const knownBooked = sum(originals.map(c => booked[c] ?? 0));
    const conflict = originals.map(c => identityConflict(input, c)).find(Boolean);
    const fgPieces = conflict ? 0 : sum(originals.map(c => pos(input.opening.fg[c])));
    const confirmedPieces = sum(orders.filter(o => o.code === code && o.date <= `${month}-31`).map(o => o.remaining));
    const targetRemainingPieces = Math.max(0, monthlyPieces - knownBooked);
    const confirmedUncoveredPieces = Math.max(0, confirmedPieces - fgPieces);
    const requiredPieces = Math.max(targetRemainingPieces, confirmedUncoveredPieces);
    const notes = [...descriptor.notes];
    if (conflict) notes.push(`IDENTITY HOLD: ${conflict} Forecast production, FG cover and inherited prices are withheld pending verified recipe/price identity.`);
    for (const basis of new Set(orders.filter(o => o.code === code && o.remainingBasis).map(o => o.remainingBasis!))) notes.push(`Order quantity basis: ${basis}`);
    if (transition && pos(input.opening.fg[transition.from]) > 0) notes.push("Old 16-piece FG provisionally covers family demand by bottle count only. This does not establish 20-case-ready stock; recartoning material and labour are not modelled, pending confirmation.");
    if (conditionalRecipe) notes.push("CONDITIONAL: physical-fit hypothesis only. Same PM0000121 bottle and closures as verified groundnut, with PM0000914 at 1/20. All other recipe coefficients retained. SKU identity is not merged; brand/print acceptance is unconfirmed.");
    if (!historyComplete) notes.push("Booked month-to-date coverage is partial: remaining target subtracts known booked pieces only and may be overstated.");
    if (orders.some(o => o.code === code && o._src === "ECOM-PO")) notes.push("ECOM quantity/date here is allocated from aggregate platform demand and current open-PO SKU mix, not an exact PO line or deadline.");
    if (descriptor.container.toUpperCase() !== first.pack_type.toUpperCase()) notes.push(`Container comes from recipe (${descriptor.container}); sheet says ${first.pack_type}.`);
    const value = conflict ? undefined : input.valuation?.rupeesPerLitre[code] ?? input.valuation?.rupeesPerLitre[first.code] ?? input.realise[code] ?? input.realise[first.code];
    if (descriptor.containersPerPiece !== 1) notes.push(`${descriptor.containersPerPiece} physical containers per sales unit: fill size is ${packLitres / descriptor.containersPerPiece} L; line container/hour is divided by this count for sales units/hour.`);
    if (typeof value === "number" && value > 700) notes.push("Inherited realisation exceeds ₹700/L; it is an unverified valuation outlier, not a guaranteed price.");
    let exclusionReason: string | null = null;
    if (conflict) exclusionReason = `Identity hold: ${conflict}`;
    else if (descriptor.container === "drum" || packLitres >= 100) exclusionReason = "Drums are deferred from Mark IV; this is excluded demand, not impossible production.";
    else if (!input.bom[code]?.length) exclusionReason = "Verified recipe is unavailable.";
    else if (recipe.filter(([c,q]) => q >= .5 && /bottle|\bjar\b|jerry|hdpe|\btin\b|\bdrum\b/i.test(input.items[c]?.name ?? '') && !/cap|carton|label|preform|sleeve|seal|wad|plug/i.test(input.items[c]?.name ?? '')).length > 1) exclusionReason = "Multiple primary container components: mixed-pack route and container count are not verified.";
    else if (packLitres === 1 && descriptor.carton === 16) exclusionReason = "16-piece carton is retired for new production; exact 20-piece replacement recipe/SKU is not verified.";
    const p: Product = { code, name: input.items[code]?.name ?? first.sku, category: first.category, packLitres, container: descriptor.container, bottleGrams: descriptor.grams, fillLitres: packLitres / descriptor.containersPerPiece, containersPerPiece: descriptor.containersPerPiece, cartonPieces: descriptor.carton, monthlyPieces, bookedMtdPieces: historyComplete ? knownBooked : null, fgPieces, targetRemainingPieces, exactOrderPieces: sum(orders.filter(o => o.code === code && o._src !== "ECOM-PO" && o.is_exact_sku_due !== false).map(o => o.pieces)), allocatedOrderPieces: sum(orders.filter(o => o.code === code && (o._src === "ECOM-PO" || o.is_exact_sku_due === false)).map(o => o.pieces)), confirmedPieces, confirmedUncoveredPieces, forecastPieces: Math.max(0, targetRemainingPieces - confirmedUncoveredPieces), requiredPieces, plannedPieces: 0, unmetPieces: requiredPieces, valuePerLitre: typeof value === "number" && Number.isFinite(value) && value > 0 ? value : null, bom: recipe, conditionalRecipe, originalCodes: originals, transition: transition ? `${transition.from} → ${transition.to}: ${transition.evidence}. Piece demand is preserved; new recipe controls carton consumption.` : null, exclusionReason, notes, eligibility: {} };
    for (const line of LINE_IDS) p.eligibility[line] = eligibility({ ...p, packLitres: p.fillLitres }, line);
    products.push(p);
  }
  return { products: products.sort((a, b) => a.code.localeCompare(b.code)), orders, historyComplete, actuals };
}

// Consume on a trial ledger: recursive recipes use on-hand blend before making the missing balance.
function consumeMaterial(code: string, qty: number, stock: Record<string, number>, blends: Record<string, Recipe>, used: Record<string, number>, path: string[] = []): { code: string; missing: number } | null {
  if (qty <= EPS) return null;
  if (path.includes(code) || path.length > 12) return { code, missing: qty };
  const direct = Math.min(pos(stock[code]), qty);
  stock[code] = pos(stock[code]) - direct;
  used[code] = (used[code] ?? 0) + direct;
  const rest = qty - direct;
  if (rest <= EPS) return null;
  if (!blends[code]?.length) return { code, missing: rest };
  for (const [child, per] of blends[code]) { const fail = consumeMaterial(child, rest * per, stock, blends, used, [...path, code]); if (fail) return fail; }
  return null;
}
export function trial(p: Product, pieces: number, stock: Record<string, number>, input: Mark4Input) {
  const next = { ...stock }, used: Record<string, number> = {};
  let failure: { code: string; missing: number } | null = null;
  for (const [code, qty] of p.bom) { const required = /carton|corrugat|\bcase\b/i.test(input.items[code]?.name ?? "") ? Math.ceil(qty * pieces - EPS) : qty * pieces; failure = consumeMaterial(code, required, next, input.blends ?? {}, used); if (failure) break; }
  return { next, used, failure };
}
export function feasible(p: Product, max: number, stock: Record<string, number>, input: Mark4Input): number {
  let low = 0, high = Math.max(0, Math.floor(max));
  while (low < high) { const mid = Math.ceil((low + high) / 2); if (trial(p, mid, stock, input).failure) high = mid - 1; else low = mid; }
  return low;
}

// Quantify the selected bottleneck for the remaining demand on an isolated
// ledger. Earlier shortages are provisionally filled only in this diagnostic;
// they must not hide a later BOM component or turn its shortage into one piece.
function bottleneckShortage(p: Product, pieces: number, code: string, stock: Record<string, number>, input: Mark4Input): number | null {
  const supplied = { ...stock };
  for (let attempt = 0; attempt < 1000; attempt++) {
    const failure = trial(p, pieces, supplied, input).failure;
    if (!failure) return 0;
    if (failure.code === code) return failure.missing;
    supplied[failure.code] = pos(supplied[failure.code]) + failure.missing;
  }
  return null;
}

export function buildModel(input: Mark4Input, settings?: unknown, feedStatus: Mark4Model["meta"]["feedStatus"] = "seed", feedError: string | null = null, compareSupply = true): Mark4Model {
  input = { ...input, bom: { ...input.bom, ...((input.supplements?.verifiedBom ?? {}) as Record<string, Recipe>) }, items: { ...input.items, ...((input.supplements?.verifiedItems ?? {}) as Mark4Input["items"]) } };
  validateInput(input);
  if (input.materialSupply) {
    const materialSupply = eximOnlyStock(input.materialSupply);
    input = { ...input, materialSupply, opening: { ...input.opening, stock: materialSupply.stock.byItem } };
  }
  const scenario = validateScenario(settings);
  if (input.materialSupply) scenario.allowProposedSupply = false;
  const start = iso(input.meta.as_of), month = start.slice(0, 7), end = new Date(Date.UTC(Number(start.slice(0, 4)), Number(start.slice(5, 7)), 0)).toISOString().slice(0, 10);
  const dates = dateRange(start, end);
  const { products, orders, historyComplete, actuals } = normalizeProducts(input, scenario.allowProvisionalRecipes);
  const productByCode = new Map(products.map(p => [p.code, p]));
  let stock = Object.fromEntries(Object.entries(input.opening.stock).map(([c, q]) => [c, pos(q)]));
  const consumed: Record<string, number> = {}, arrived: Record<string, number> = {}, shortages: Record<string, number> = {}, firstNeeded: Record<string, string> = {};
  const unit = (code: string) => input.materialSupply?.stock.unitByItem?.[code] ?? (code.startsWith("RM") ? "L" : (input.items[code]?.uom || "pieces"));
  const shipments = new Map<string, number>();
  const queueShipment = (date: string, litres: number) => shipments.set(date, (shipments.get(date) ?? 0) + litres);
  const originalPlanCodes = new Set(input.plan.map(p => p.code));
  const reclassifiedFg = sum(Object.entries(input.opening.fg).filter(([code]) => !originalPlanCodes.has(code)).map(([code, qty]) => { const p = products.find(x => x.originalCodes.includes(code)); return p ? pos(qty) * p.packLitres : 0; }));
  let unbilled = sum(Object.entries(input.opening.fg).map(([code, qty]) => {
    const p = products.find(x => x.originalCodes.includes(code));
    return p ? pos(qty) * p.packLitres : 0;
  })) + Math.max(0, pos(input.opening.fg_other_l) - reclassifiedFg);
  if (typeof input.opening.fg_litres === "number" && Number.isFinite(input.opening.fg_litres)) unbilled = pos(input.opening.fg_litres);
  let waiting = pos(input.opening.standing_l);
  const openingStorage = unbilled + waiting;
  // The old billed backlog is an estimate, so its two-day clearance is explicitly a scenario.
  queueShipment(start, waiting / 2); queueShipment(addDays(start, 1), waiting / 2);
  const existing = Object.fromEntries(products.map(p => [p.code, p.fgPieces]));
  const earmarks = new Map<string, { code: string; pieces: number; litres: number }[]>();
  const earmark = (ready: string, due: string, code: string, pieces: number, litres: number) => {
    const billingDate = ready > due ? ready : due;
    earmarks.set(billingDate, [...(earmarks.get(billingDate) ?? []), { code, pieces, litres }]);
    queueShipment(addDays(billingDate, 2), litres);
  };
  for (const o of orders) {
    if (!currentMonthOrder(o, input.meta.as_of)) continue;
    const p = productByCode.get(o.code); if (!p) continue;
    const take = Math.min(existing[o.code] ?? 0, o.remaining);
    existing[o.code] = (existing[o.code] ?? 0) - take; o.remaining -= take;
    if (take) earmark(start > o.date ? start : o.date, o.due, o.code, take, take * p.packLitres);
  }
  const arrivalsByDate: Record<string, Day["arrivals"]> = {};
  const inboundEvents = input.materialSupply ? reconciledInbound(input, end, scenario) : evaluateInbound(input, end, scenario.arrivalDates);
  for (const event of inboundEvents.filter(event => event.included && event.appliedAt)) {
    const at = event.appliedAt!;
    arrivalsByDate[at] = [...(arrivalsByDate[at] ?? []), { code: event.code, name: input.items[event.code]?.name ?? event.code, quantity: event.quantity, unit: event.unit, assumed: event.conditional }];
  }
  // Procurement is a separate gross-demand scenario: stock and accepted inbound are credited once.
  const procurement: Record<string, number> = {};
  const procurementStock = { ...stock };
  const procurementUnresolved = new Set<string>();
  if (input.materialSupply) {
    // Purchasing nets the source PO balance, not its split physical/history lots.
    // This ledger never supplies production and never credits an order twice.
    const sourceOrders = new Map(input.materialSupply.orders.map(order => [order.id, order]));
    for (const order of sourceOrders.values()) {
      if (comparableInboundUnit({ code: order.code, unit: order.unit } as import("./types.ts").InboundEvent, input)) procurementStock[order.code] = (procurementStock[order.code] ?? 0) + order.outstandingQty;
      else procurementUnresolved.add(order.code);
    }
    for (const lot of input.materialSupply.lots) {
      if (lot.quantity <= 0 || ["usable", "cancelled", "rejected"].includes(lot.stage) || lot.stockInclusion === "included") continue;
      if (lot.orderId && sourceOrders.has(lot.orderId)) {
        if (lot.stockInclusion === "unresolved" && sourceOrders.get(lot.orderId)!.outstandingQty > 0) procurementUnresolved.add(lot.code);
        continue;
      }
      const overlappingOrder = [...sourceOrders.values()].some(order => order.code === lot.code && order.outstandingQty > 0);
      if (lot.stockInclusion !== "excluded" || overlappingOrder || !comparableInboundUnit({ code: lot.code, unit: lot.unit } as import("./types.ts").InboundEvent, input)) {
        procurementUnresolved.add(lot.code);
        continue;
      }
      procurementStock[lot.code] = (procurementStock[lot.code] ?? 0) + lot.quantity;
    }
  } else {
    for (const rows of Object.values(arrivalsByDate)) for (const a of rows) procurementStock[a.code] = (procurementStock[a.code] ?? 0) + a.quantity;
    const creditedCommitments = new Set<string>();
    for (const event of inboundEvents) {
      if (creditedCommitments.has(event.id)) continue; creditedCommitments.add(event.id);
      if (!event.included && event.stockIncluded === false && !["received", "cancelled"].includes(event.status) && comparableInboundUnit(event, input) && event.quantity > 0) procurementStock[event.code] = (procurementStock[event.code] ?? 0) + event.quantity;
    }
  }
  function need(code: string, quantity: number, path: string[] = []) {
    if (path.includes(code) || path.length > 12) return;
    const take = Math.min(pos(procurementStock[code]), quantity); procurementStock[code] = pos(procurementStock[code]) - take;
    const rest = quantity - take; if (rest <= EPS) return;
    if (input.blends[code]?.length) for (const [child, per] of input.blends[code]) need(child, rest * per, [...path, code]);
    else procurement[code] = (procurement[code] ?? 0) + rest;
  }
  for (const p of products.filter(p => !p.exclusionReason && Object.values(p.eligibility).some(e => e.allowed))) for (const [code, per] of p.bom) need(code, /carton|corrugat|\bcase\b/i.test(input.items[code]?.name ?? "") ? Math.ceil(per * p.requiredPieces-EPS) : per * p.requiredPieces);
  const leadDays = (code: string) => code.startsWith("RM") ? 14 : 7;
  const firstProductionDate = new Date(`${start}T12:00:00Z`).getUTCDay() === 0 ? addDays(start,1) : start;
  if (scenario.allowProposedSupply) for (const [code, quantity] of Object.entries(procurement)) {
    const date = addDays(start, leadDays(code));
    if (date <= end) arrivalsByDate[date] = [...(arrivalsByDate[date] ?? []), { code, name: input.items[code]?.name ?? code, quantity, unit: unit(code), assumed: true }];
  }
  const timedReceipts: TimedReceipt[] = inboundEvents.filter(event => event.included && event.appliedAt).map(event => ({ at: Date.parse(event.readyAt ?? `${event.appliedAt}T00:00:00+05:30`), code: event.code, quantity: event.quantity, conditional: event.conditional }));
  if (scenario.allowProposedSupply) for (const [date, rows] of Object.entries(arrivalsByDate)) for (const row of rows.filter(row => row.assumed)) if (!inboundEvents.some(event => event.included && event.appliedAt === date && event.code === row.code)) timedReceipts.push({ at: Date.parse(`${date}T00:00:00+05:30`), code: row.code, quantity: row.quantity, conditional: true });
  const calendar = new MaterialCalendar(stock, timedReceipts);
  const HOUR = 3600000;
  const days: Day[] = [];
  const lastProductByLine: Record<string, string | undefined> = {};
  const lineDescriptions: Record<string, string> = { "JP Machine": "Mustard first · groundnut when useful", "Clear Pack": "40 g litre bottles · supported 4/5 L", "10 Head": "1/2 L bottles · supported 3 L", "6 Head": "5 L first · printed tins avoid labeller", "Tin Head": "15 L tins · declared planning speed", "Pouch Machine": "Hitech only · reserve after priority work" };
  for (const date of dates) {
    const sunday = new Date(`${date}T12:00:00Z`).getUTCDay() === 0;
    const openingLitres = unbilled + waiting;
    for (const o of orders.filter(o => o.date <= date && o.remaining > 0)) { const p = productByCode.get(o.code); if (!p) continue; const take = Math.min(existing[o.code] ?? 0, o.remaining); existing[o.code] = (existing[o.code] ?? 0) - take; o.remaining -= take; if (take) earmark(date, o.due, o.code, take, take * p.packLitres); }
    for (const a of arrivalsByDate[date] ?? []) arrived[a.code] = (arrived[a.code] ?? 0) + a.quantity;
    const shiftStart = Date.parse(`${date}T${String(scenario.shiftStartHour ?? 8).padStart(2, "0")}:00:00+05:30`);
    const calendarClose = date === end || new Date(`${date}T12:00:00Z`).getUTCDay() === 6 ? Date.parse(`${addDays(date, 1)}T00:00:00+05:30`) : Infinity;
    const sessionEnd = (hours: number) => Math.min(shiftStart + hours * HOUR, calendarClose);
    stock = calendar.available(shiftStart);
    // Only a simulated physical departure releases space. This happens on Sunday too.
    const dispatchLitres = Math.min(waiting, shipments.get(date) ?? 0); waiting -= dispatchLitres;
    for (const entry of earmarks.get(date) ?? []) { const moved = Math.min(unbilled, entry.litres); unbilled -= moved; waiting += moved; }
    const runs: Run[] = [], blockers: Blocker[] = [];
    const sessions = Object.fromEntries(LINE_IDS.map(line => [line, 10]));
    const usedHours = Object.fromEntries(LINE_IDS.map(line => [line, 0]));
    const currentCursor = date === start ? Math.max(shiftStart, Date.parse(input.meta.as_of)) : shiftStart;
    const cursor = Object.fromEntries(LINE_IDS.map(line => [line, currentCursor]));
    const paidSessions = Object.fromEntries(LINE_IDS.map(line => [line, new Set<number>()]));
    const campaignCount = Object.fromEntries(LINE_IDS.map(line => [line, 0]));
    let nightLine: string | null = null;
    const deferredCampaigns = new Map<string, { blocker: Blocker; hours: number }>();
    const viableCampaigns = new Set<string>();
    const score = (p: Product, line: string): number => {
      const urgent = orders.filter(o => o.code === p.code && o.remaining > EPS && o.date <= date).sort((a, b) => Number(a._src === "ECOM-PO" || a.is_exact_sku_due === false) - Number(b._src === "ECOM-PO" || b.is_exact_sku_due === false) || a.due.localeCompare(b.due))[0];
      const dueBoost = urgent ? (urgent._src === "ECOM-PO" || urgent.is_exact_sku_due === false ? 50000 : 100000) + (urgent.due <= date ? 20000 : 10000 - Math.min(9000, Math.max(0, (Date.parse(urgent.due) - Date.parse(date)) / 86400000) * 100)) : 0;
      const preference = p.eligibility[line].preference * 100;
      const sales = pos(input.supplements?.salesRank?.[p.code]);
      return dueBoost + preference + Math.min(100, p.unmetPieces * p.packLitres / 1000) + Math.min(99, sales) - (p.container === "pouch" && !urgent ? 5000 : 0);
    };
    const candidates = (line: string) => products.filter(p => p.unmetPieces >= 1 && p.eligibility[line].allowed && rateFor(input, p, line, scenario.efficiency)).sort((a, b) => score(b, line) - score(a, line) || a.code.localeCompare(b.code));
    const allocation = (p: Product, line: string, from: number, until: number, setup: number, ledger: MaterialCalendar, headroom: number, previous?: string) => {
      const rate = rateFor(input, p, line, scenario.efficiency)!;
      for (const at of ledger.times(from + setup * HOUR, until)) {
        const availableHours = (until - at) / HOUR;
        const availableStock = ledger.available(at);
        const bound = Math.min(p.unmetPieces, rate.effectivePiecesPerHour * availableHours, Math.floor(headroom / p.packLitres));
        const qty = feasible(p, bound, availableStock, input);
        const hours = qty / rate.effectivePiecesPerHour;
        if (campaignEligible(hours, previous === p.code)) return { at, qty, hours, availableStock, bound };
      }
      return null;
    };
    if (!sunday) {
      if (scenario.nightLine && scenario.nightLine !== "auto") nightLine = scenario.nightLine;
      else if (scenario.nightLine === "auto") {
        // Preview the same bounded two-campaign policy on independent ledgers.
        // This estimates useful extra filling, not a globally optimal schedule.
        const preview = (line: string, hoursAvailable: number, eligible: Product[], priorities: Map<string, number>) => {
          const previewCalendar = calendar.clone();
          let headroom = Math.max(0, STORAGE_LIMIT - unbilled - waiting);
          let occupied = (currentCursor - shiftStart) / HOUR, litres = 0, nightHours = 0, priority = -Infinity;
          let previous = lastProductByLine[line];
          let campaigns = 0;
          const remaining = Object.fromEntries(eligible.map(p => [p.code, p.unmetPieces]));
          for (let pass = 0; pass < 2 + timedReceipts.length; pass++) {
            let choice: { p: Product; qty: number; hours: number; setup: number; score: number; at: number } | null = null;
            for (const p of eligible) {
              if (remaining[p.code] < 1 || campaigns >= 2 && previous !== p.code) continue;
              const setup = previous && previous !== p.code ? PRODUCT_CHANGE_SETUP_HOURS : 0;
              const picked = allocation({ ...p, unmetPieces: remaining[p.code] }, line, shiftStart + occupied * HOUR, sessionEnd(hoursAvailable), setup, previewCalendar, headroom, previous);
              if (!picked) continue;
              const { qty, hours, at } = picked;
              const candidateScore = priorities.get(p.code)! + Math.min(99, hours) - (setup ? 15000 : 0);
              if (!choice || candidateScore > choice.score || (candidateScore === choice.score && p.code < choice.p.code)) choice = { p, qty, hours, setup, at, score: candidateScore };
            }
            if (!choice) break;
            const { p, qty, hours, setup, at } = choice;
            const attempt = trial(p, qty, previewCalendar.available(at), input);
            if (attempt.failure) throw new Error("Night preview material allocation invariant failed.");
            previewCalendar.reserve(at, attempt.used);
            occupied = (at - shiftStart) / HOUR - setup;
            const dayHours = Math.max(0, Math.min(10, occupied + setup + hours) - Math.min(10, occupied + setup));
            nightHours += Math.max(0, hours - dayHours);
            occupied += setup + hours;
            litres += qty * p.packLitres; headroom = Math.max(0, headroom - qty * p.packLitres);
            priority = Math.max(priority, priorities.get(p.code)!);
            if (campaigns === 0 || previous !== p.code) campaigns++;
            remaining[p.code] -= qty; previous = p.code;
          }
          return { litres, nightHours, priority };
        };
        let best = -Infinity;
        for (const line of LINE_IDS) {
          const eligible = candidates(line);
          const priorities = new Map(eligible.map(p => [p.code, score(p, line)]));
          const day = preview(line, 10, eligible, priorities), extended = preview(line, 20, eligible, priorities);
          if (extended.nightHours <= EPS || extended.litres <= day.litres + EPS) continue;
          const s = extended.priority + Math.min(1000, extended.litres / 100);
          if (s > best) { best = s; nightLine = line; }
        }
      }
      if (nightLine) sessions[nightLine] = 20;
      // Globally choose the strongest currently feasible line-product pair, then reconsider shared stock.
      for (let pass = 0; pass < LINE_IDS.length * (2 + timedReceipts.length); pass++) {
        const deferredThisPass = new Map<string, { blocker: Blocker; hours: number }>();
        let choice: { p: Product; line: string; qty: number; hours: number; setup: number; score: number; at: number } | null = null;
        for (const line of LINE_IDS) {
          if (sessionEnd(sessions[line]) - cursor[line] <= EPS) continue;
          for (const p of candidates(line)) {
            if (campaignCount[line] >= 2 && lastProductByLine[line] !== p.code) continue;
            const setup = lastProductByLine[line] && lastProductByLine[line] !== p.code ? PRODUCT_CHANGE_SETUP_HOURS : 0;
            const rate = rateFor(input, p, line, scenario.efficiency)!;
            const picked = allocation(p, line, cursor[line], sessionEnd(sessions[line]), setup, calendar, Math.max(0, STORAGE_LIMIT - unbilled - waiting), lastProductByLine[line]);
            if (!picked) {
              const available = calendar.available(cursor[line] + setup * HOUR);
              const storagePieces = Math.floor(Math.max(0, STORAGE_LIMIT-unbilled-waiting)/p.packLitres);
              const bound = Math.min(p.unmetPieces, rate.effectivePiecesPerHour * Math.max(0, (sessionEnd(sessions[line]) - cursor[line])/HOUR - setup), storagePieces);
              const qty = feasible(p, bound, available, input);
              const hours = qty/rate.effectivePiecesPerHour;
              if (qty > 0 && !campaignEligible(hours, lastProductByLine[line] === p.code)) {
                const material = qty < Math.floor(bound) ? trial(p, qty + 1, available, input).failure : null;
                const cap = material ? `${input.items[material.code]?.name ?? material.code} limits the available material` : p.unmetPieces <= bound + EPS ? "remaining demand limits the quantity" : storagePieces <= bound + EPS ? "available godown space limits the quantity" : "remaining session time limits the quantity";
                const blocker: Blocker = { code: p.code, product: p.name, line, reason: `Deferred small campaign: ${qty.toLocaleString("en-IN")} pieces allow ${Math.max(1, Math.round(hours*3600)).toLocaleString("en-IN")} seconds of filling; ${cap}. A new campaign needs at least ${MIN_NEW_CAMPAIGN_HOURS} productive hour under the provisional planning guard. No materials or setup time are consumed.`, ...(material ? {materialCode:material.code, materialName:input.items[material.code]?.name ?? material.code, unit:unit(material.code)} : {}) };
                if (!deferredThisPass.has(p.code) || hours > deferredThisPass.get(p.code)!.hours) deferredThisPass.set(p.code, {hours, blocker});
              }
              continue;
            }
            const { qty, hours, at } = picked;
            viableCampaigns.add(p.code);
            const s = score(p, line) + Math.min(99, qty / rate.effectivePiecesPerHour) - (setup ? 15000 : 0);
            if (!choice || s > choice.score || (s === choice.score && `${line}:${p.code}` < `${choice.line}:${choice.p.code}`)) choice = { p, line, qty, hours: qty / rate.effectivePiecesPerHour, setup, at, score: s };
          }
        }
        for (const [code, deferred] of deferredThisPass) deferredCampaigns.set(code, deferred);
        if (!choice) break;
        const { p, line, qty, hours, setup, at } = choice;
        deferredCampaigns.delete(p.code);
        const attempt = trial(p, qty, calendar.available(at), input); if (attempt.failure) throw new Error("Material allocation invariant failed.");
        const conditionalSupplyMaterials = calendar.reserve(at, attempt.used);
        const conditionalSupply = conditionalSupplyMaterials.length > 0;
        stock = calendar.available(at);
        for (const [code, q] of Object.entries(attempt.used)) consumed[code] = (consumed[code] ?? 0) + q;
        const previousProduct = lastProductByLine[line];
        const before = (at - shiftStart) / HOUR - setup;
        const idleHours = Math.max(0, (at - cursor[line])/HOUR - setup);
        cursor[line] = at + hours * HOUR; usedHours[line] += hours + setup; if (campaignCount[line] === 0 || previousProduct !== p.code) campaignCount[line]++; lastProductByLine[line] = p.code;
        const dayHours = Math.max(0, Math.min(10, before + setup + hours) - Math.min(10, before + setup));
        const rawNightHours = hours - dayHours;
        const nightHours = rawNightHours < EPS ? 0 : rawNightHours;
        let remaining = qty, confirmed = 0, justBilled = 0, exactOrderPieces = 0, allocatedOrderPieces = 0;
        for (const o of orders.filter(o => o.code === p.code && o.date <= date && o.remaining > 0)) {
          const take = Math.min(o.remaining, remaining); o.remaining -= take; remaining -= take; confirmed += take; if (o._src === "ECOM-PO" || o.is_exact_sku_due === false) allocatedOrderPieces += take; else exactOrderPieces += take;
          if (take) { earmark(date, o.due, p.code, take, take * p.packLitres); if (o.due <= date) justBilled += take * p.packLitres; }
          if (!remaining) break;
        }
        const litres = qty * p.packLitres;
        unbilled += litres;
        // Same-day fulfilled orders move into the billed-waiting pile, not out of the godown.
        existing[p.code] = (existing[p.code] ?? 0) + remaining;
        if (justBilled > 0) { unbilled -= justBilled; waiting += justBilled; }
        p.plannedPieces += qty; p.unmetPieces = Math.max(0, p.requiredPieces - p.plannedPieces);
        const rate = rateFor(input, p, line, scenario.efficiency)!;
        const preferred = LINE_IDS.filter(l => p.eligibility[l].allowed && p.eligibility[l].preference > p.eligibility[line].preference);
        const alternativeNote = preferred.length ? ` Higher-preference ${preferred.join(" / ")} ${preferred.some(l => usedHours[l] > 0) ? "already has an allocated campaign; this eligible fallback uses another line." : "remains an alternative; this allocation balances competing campaign priorities."}` : "";
        const labour = input.supplements?.labourPerSession?.[line];
        let newlyPaidSessions = 0;
        for (const session of [0, 1]) if (at + hours*HOUR > shiftStart + session*10*HOUR && at - setup*HOUR < shiftStart + (session+1)*10*HOUR && !paidSessions[line].has(session)) { paidSessions[line].add(session); newlyPaidSessions++; }
        runs.push({ startsAt: new Date(at).toISOString(), endsAt: new Date(at + hours * HOUR).toISOString(), idleHours, conditionalSupply, conditionalSupplyMaterials, conditionalRecipe: p.conditionalRecipe, line, code: p.code, product: p.name, pieces: qty, litres, hours, dayHours, nightHours, setupHours: setup, value: p.valuePerLitre === null ? null : litres * p.valuePerLitre, confirmedPieces: confirmed, forecastPieces: qty - confirmed, reason: `${conditionalSupply ? "This run uses supply whose usable date is estimated; confirm the displayed delivery/QC window. " : ""}${p.eligibility[line].reason}${alternativeNote} ${confirmed ? `${confirmed.toLocaleString("en-IN")} pieces cover open orders${allocatedOrderPieces ? " (includes legacy inferred ECOM mix)" : " (exact source line basis)"}; ` : "Monthly reserve prepares for later orders; "}${setup ? `product change from ${previousProduct}; ${PRODUCT_CHANGE_SETUP_HOURS} h provisional setup charged, including across dates.` : previousProduct === p.code ? "same-product continuation; no additional setup charged." : "first horizon campaign; opening setup is unknown and provisionally zero."}${p.transition ? " Verified 20-piece replacement recipe applied." : ""}`, rate, exactOrderPieces, allocatedOrderPieces, labourCost: typeof labour === "number" && labour > 0 ? labour * newlyPaidSessions : null, materials: Object.entries(attempt.used).filter(([, q]) => q > EPS).map(([code, quantity]) => ({ code, quantity, unit: unit(code) })) });
      }
    }
    stock = calendar.available(sessionEnd(Math.max(...Object.values(sessions))));
    for (const p of products.filter(p => p.unmetPieces >= 1)) {
      if (p.exclusionReason) { blockers.push({ code: p.code, product: p.name, line: null, reason: p.exclusionReason }); continue; }
      const compatible = LINE_IDS.filter(l => p.eligibility[l].allowed && rateFor(input, p, l, scenario.efficiency));
      if (!compatible.length) {
        const routed = LINE_IDS.filter(line => p.eligibility[line].allowed);
        blockers.push({ code: p.code, product: p.name, line: null, reason: routed.length ? `Approved planning speed is unavailable for ${routed.join(" / ")}; no production is scheduled.` : "No confirmed eligible line with a usable capacity: " + [...new Set(Object.values(p.eligibility).map(e => e.reason))].join(" ") }); continue;
      }
      const one = trial(p, 1, stock, input);
      if (one.failure) {
        // Preserve the component that prevents even one more piece. A full
        // unmet-demand trial may encounter an unrelated earlier BOM shortage.
        const code = one.failure.code;
        const missing = bottleneckShortage(p, Math.ceil(p.unmetPieces), code, stock, input);
        if (!firstNeeded[code]) firstNeeded[code] = date;
        if (missing !== null) shortages[code] = Math.max(shortages[code] ?? 0, missing);
        blockers.push({ code: p.code, product: p.name, line: compatible[0], reason: `Waiting for ${input.items[code]?.name ?? code}; no usable material remains within the selected shift hours. Check the incoming QA readiness time; a later release waits for the next open session.`, materialCode: code, materialName: input.items[code]?.name ?? code, ...(missing === null ? {} : { missingQuantity: missing }), unit: unit(code) });
      } else if (unbilled + waiting + p.packLitres > STORAGE_LIMIT + EPS) blockers.push({ code: p.code, product: p.name, line: compatible[0], reason: "Physical godown space is full. Billing alone cannot unblock production; a truck must leave." });
      else if (sunday) blockers.push({ code: p.code, product: p.name, line: compatible[0], reason: "Sunday is closed for production; dispatch relief continues." });
      else if (deferredCampaigns.has(p.code) && !viableCampaigns.has(p.code) && !runs.some(run => run.code === p.code)) blockers.push(deferredCampaigns.get(p.code)!.blocker);
      else blockers.push({ code: p.code, product: p.name, line: compatible[0], reason: "No feasible filling window remains after material/QA readiness, setup and other allocated campaigns. Review the next open session; a late release does not create extra working hours." });
    }
    const productionLitres = sum(runs.map(r => r.litres));
    const unvaluedLitres = sum(runs.filter(r => r.value === null).map(r => r.litres));
    const productionValue = unvaluedLitres ? null : sum(runs.map(r => r.value ?? 0));
    const targetValue = sunday ? 0 : DAY_TARGET;
    days.push({ date, sunday, runs, blockers, productionLitres, productionValue, knownProductionValue: sum(runs.map(r => r.value ?? 0)), unvaluedLitres, targetValue, targetGap: productionValue === null ? null : Math.max(0, targetValue - productionValue), nightLine: runs.some(r => r.nightHours > EPS) ? nightLine : null, dispatchLitres, storage: { openingLitres, madeLitres: productionLitres, dispatchedLitres: dispatchLitres, closingLitres: unbilled + waiting, unbilledLitres: unbilled, billedWaitingLitres: waiting, limitLitres: STORAGE_LIMIT, overLimitLitres: Math.max(0, unbilled + waiting - STORAGE_LIMIT) }, arrivals: arrivalsByDate[date] ?? [] });
  }
  stock = calendar.balance(Infinity);
  const allRuns = days.flatMap(d => d.runs);
  const codes = new Set([...Object.keys(input.opening.stock), ...Object.keys(arrived), ...Object.keys(consumed), ...Object.keys(shortages), ...Object.keys(procurement), ...procurementUnresolved]);
  const materials: Material[] = [...codes].filter(c => pos(input.opening.stock[c]) || arrived[c] || consumed[c] || shortages[c] || procurement[c] || procurementUnresolved.has(c)).map(code => ({ code, name: input.items[code]?.name ?? code, unit: unit(code), opening: pos(input.opening.stock[code]), arrivals: arrived[code] ?? 0, consumed: consumed[code] ?? 0, remaining: pos(stock[code]), shortage: shortages[code] ?? 0, firstNeeded: firstNeeded[code] ?? null, leadDays: !input.materialSupply && procurement[code] ? leadDays(code) : null, orderBy: !input.materialSupply && procurement[code] ? addDays(firstNeeded[code] ?? firstProductionDate, -leadDays(code)) : null, proposedQty: procurementUnresolved.has(code) ? null : procurement[code] ?? 0, projectedArrival: !input.materialSupply && procurement[code] ? addDays(start, leadDays(code)) : null, note: input.materialSupply ? procurementUnresolved.has(code) ? "Purchase quantity is unresolved because an incoming load may overlap an existing order or its usable stock/unit is unconfirmed. Reconcile before placing another order." : "Purchase need nets usable opening stock and each issued PO line outstanding balance once against the gross eligible target. Physical lots from those POs are not added again. Undated orders remain purchasing commitments, not production-ready stock. Confirm supplier timing; no new purchase is assumed placed." : shortages[code] ? "Shortage shows the first exhausted component. Proposed quantity nets shared stock and comparable already-issued outstanding commitments, including undated POs, against the gross eligible production target. Those undated commitments do not become production stock; provisional lead is 7 days for packaging and 14 days for oil. Neither an issued PO nor supplier commitment; line/storage limits may mean not all proposed stock is used." : "Shared stock ledger; future arrivals are included only under the selected scenario." })).sort((a, b) => b.shortage - a.shortage || a.code.localeCompare(b.code));
  const productionDays = days.filter(d => !d.sunday).length;
  const plannedLitres = sum(allRuns.map(r => r.litres));
  const unvaluedLitres = sum(allRuns.filter(r => r.value === null).map(r => r.litres));
  const plannedValue = unvaluedLitres ? null : sum(allRuns.map(r => r.value ?? 0));
  const excluded = (p: Product) => p.container === "drum" || p.packLitres >= 100;
  const demandBook = grossDemandBook(input);
  const mappedLitres = sum(products.map(p => p.confirmedPieces * p.packLitres));
  const stockCoveredLitres = sum(products.map(p => Math.min(p.fgPieces, p.confirmedPieces) * p.packLitres));
  const monthOrders = input.orders.filter(o => currentMonthOrder(o, input.meta.as_of));
  const quarantinedOrders = monthOrders.flatMap(o => { const reason = orderIdentityIssue(input, o); return reason ? [{ id: o.sourceLineId ?? o.docnum, code: o.code, sourceProductName: o.sourceProductName ?? null, litres: orderLitres(o), reason }] : []; });
  const unmappedOrders = monthOrders.filter(o => orderIdentityIssue(input, o) || !products.some(p => p.originalCodes.includes(o.code!)));
  const unmappedKnownLitres = sum(unmappedOrders.map(o => orderLitres(o) ?? 0));
  const missingUnits = unmappedOrders.some(o => orderLitres(o) === null);
  const knownGrossDue = typeof demandBook.online.planningDueLitres === "number" && typeof demandBook.trade.planningDueLitres === "number" ? demandBook.online.planningDueLitres + demandBook.trade.planningDueLitres : null;
  const knownAcceptedDue = typeof demandBook.online.acceptedPlanningDueLitres === "number" && typeof demandBook.trade.planningDueLitres === "number" ? demandBook.online.acceptedPlanningDueLitres + demandBook.trade.planningDueLitres : null;
  const unknownActiveOrderCount = demandBook.trade.unknownActiveOrderCount ?? 0;
  const tradeComplete = demandBook.trade.isComplete !== false && unknownActiveOrderCount === 0;
  const outsideAcceptedDue = typeof demandBook.online.outsideOilScopeAcceptedPlanningDueLitres === "number" ? demandBook.online.outsideOilScopeAcceptedPlanningDueLitres : (demandBook.online.outsideOilScopeAcceptedLitres ?? 0) === 0 ? 0 : null;
  if (knownAcceptedDue !== null && outsideAcceptedDue !== null && mappedLitres > knownAcceptedDue - outsideAcceptedDue + Math.max(.11, knownAcceptedDue * .0001)) throw new Error("Mapped production demand exceeds the independently reconciled accepted Oil order book.");
  const model: Mark4Model = {
    demandBook, inboundEvents, planningSpeeds: PLANNING_SPEEDS.map(row => ({ ...row })),
    planningBridge: { quarantinedOrders, grossDueLitres: input.demandBook ? (tradeComplete ? knownGrossDue : null) : (missingUnits ? null : mappedLitres + unmappedKnownLitres), knownGrossDueLitres: knownGrossDue, unknownActiveOrderCount, outsideOilScopeLitres: outsideAcceptedDue, mappedLitres, unmappedLitres: knownAcceptedDue !== null ? outsideAcceptedDue === null ? null : Math.max(0, knownAcceptedDue - outsideAcceptedDue - mappedLitres) : missingUnits ? null : unmappedKnownLitres, explicitUnacceptedLitres: knownGrossDue !== null && knownAcceptedDue !== null ? Math.max(0, knownGrossDue - knownAcceptedDue) : null, stockCoveredLitres, netMakeLitres: sum(products.map(p => p.confirmedUncoveredPieces * p.packLitres)), unschedulableLitres: sum(products.filter(p => !LINE_IDS.some(line => p.eligibility[line].allowed && rateFor(input, p, line))).map(p => p.confirmedUncoveredPieces * p.packLitres)), projectionReserveLitres: sum(products.map(p => p.forecastPieces * p.packLitres)), notes: [`${quarantinedOrders.length} current-due source lines are held for unresolved product identity; their original litres remain in the gross book and unmapped demand.`, "Gross open PO book is independent of this production bridge and includes later-due and unmapped demand.", unknownActiveOrderCount > 0 ? `${unknownActiveOrderCount} active trade headers have unreadable detail. Their company, due date and litres are unresolved; the known subtotal is not a complete trade or current-month demand total.` : "No unreadable active trade headers are reported in this input.", "Outside-Oil accepted demand is displayed separately from unmapped Oil demand. Requested-minus-accepted is a quantity-policy difference, not missing SKU mapping.", "Bridge uses eligible unexpired current-month/overdue line quantities; Amazon accepted remaining can differ from requested-minus-received gross demand.", "Stock reduces current PO make demand only. Monthly production projection and PO demand are combined with max(), not added.", "Unverified cross-company identity is quarantined. Undated demand stays in the book until its requirement date is resolved."] },
    meta: { generatedAt: new Date().toISOString(), asOf: input.meta.state_collected_at ?? input.meta.as_of, month, startDate: start, endDate: end, engine: "Mark IV independent deterministic planner · v1", feedStatus, feedError, inputAsOf: input.meta.frozen_at ?? input.meta.as_of, assumptions: ["Conditional planning from the stamped input snapshot; displayed compute time does not refresh source data.", "OMS Beverages/Mart rows are excluded because cross-company FG codes do not prove Oil SKU identity.", input.orders.some(o => o._src === "ECOM-EXACT") ? "Exact e-commerce source lines supply accepted remaining demand; the gross requested residual book is shown separately, including its unaccepted portion." : "Legacy ECOM source PO totals are real, but per-SKU/day allocations are inferred from platform mix; they are not exact original PO lines.", ...(input.notes ?? [])] },
    sources: input.sources.map(s => ({ id: s.id, label: s.label, asOf: s.asOf, ok: s.ok, note: s.note })), scenario, days,
    lines: LINE_IDS.map(line => { const runs = allRuns.filter(r => r.line === line); const hours = sum(runs.map(r => r.hours + r.setupHours)); const nightHours = sum(runs.map(r => r.nightHours)); const availableHours = sum(days.filter(d => !d.sunday).map(d => {
      const begin = Date.parse(`${d.date}T${String(scenario.shiftStartHour ?? 8).padStart(2, "0")}:00:00+05:30`);
      const close = d.date === end || new Date(`${d.date}T12:00:00Z`).getUTCDay() === 6 ? Date.parse(`${addDays(d.date, 1)}T00:00:00+05:30`) : Infinity;
      return Math.max(0, (Math.min(begin + (d.nightLine === line ? 20 : 10)*HOUR, close) - Math.max(begin, d.date === start ? Date.parse(input.meta.as_of) : begin))/HOUR);
    })); return { id: line, name: line, description: lineDescriptions[line], plannedLitres: sum(runs.map(r => r.litres)), hours, nightHours, availableHours, utilization: availableHours ? hours / availableHours : 0, rates: ratesForLine(line), actual: (input.actual_lines ?? []).filter(a => a.line === line), labourPerSession: input.supplements?.labourPerSession?.[line] ?? null, recordedLabour: recordedLabour(input, line) }; }),
    products, materials, actuals: withActualValues([...actuals, ...input.history.days.filter(d => d.date === start)], input),
    summary: { plannedLitres, plannedValue, knownPlannedValue: sum(allRuns.map(r => r.value ?? 0)), unvaluedLitres, requiredLitres: sum(products.filter(p => !excluded(p)).map(p => p.requiredPieces * p.packLitres)), unmetLitres: sum(products.filter(p => !excluded(p)).map(p => p.unmetPieces * p.packLitres)), confirmedLitres: sum(products.filter(p => !excluded(p)).map(p => p.confirmedUncoveredPieces * p.packLitres)), forecastLitres: sum(products.filter(p => !excluded(p)).map(p => p.forecastPieces * p.packLitres)), excludedLitres: sum(products.filter(excluded).map(p => p.requiredPieces * p.packLitres)), productionDays, targetValue: DAY_TARGET * productionDays, minimumDailyValue: 20000000, desiredDailyValue: DAY_TARGET, valueGap: plannedValue === null ? null : Math.max(0, DAY_TARGET * productionDays - plannedValue), storageLimitLitres: STORAGE_LIMIT, openingStorageLitres: openingStorage, peakStorageLitres: Math.max(openingStorage, ...days.map(d => d.storage.closingLitres)), bookedMtdLitres: historyComplete ? sum(actuals.map(d => pos(d.made_booked_l))) : null, historyComplete, conditionalRecipeLitres: sum(allRuns.filter(r => r.conditionalRecipe).map(r => r.litres)), conditionalSupplyLitres: sum(allRuns.filter(r => r.conditionalSupply).map(r => r.litres)), conditionalLitres: sum(allRuns.filter(r => r.conditionalRecipe || r.conditionalSupply).map(r => r.litres)), conditionalValue: allRuns.some(r => (r.conditionalRecipe || r.conditionalSupply) && r.value === null) ? null : sum(allRuns.filter(r => r.conditionalRecipe || r.conditionalSupply).map(r => r.value ?? 0)), blockedProducts: products.filter(p => p.unmetPieces >= 1 && !excluded(p)).length },
    dispatch: { pendingLitres: input.dispatch_aging?.pendingLitres ?? pos(input.opening.standing_l), oldestDays: input.dispatch_aging?.oldestDays ?? null, medianDays: input.dispatch_aging?.medianDays ?? null, asOf: input.dispatch_aging?.asOf ?? null, note: input.dispatch_aging?.note ?? "Oil billed-waiting volume is an apportioned estimate. Detailed oldest pending age is unavailable. Future departures are scenario assumptions, not truck appointments.", usualDays: 2, tailDays: 14 },
    rules: rulebook(scenario, input),
    questions: [
      { id: "tin3", question: "Which machine and speed should we use for each 3 L tin?", impact: "These tin recipes stay blocked; 3 L plastic has a separate supported route." },
      { id: "labels", question: "How do labelled products finish while the 6 Head labeller is broken?", impact: "Non-printed packs on 6 Head are provisional; extra labour/setup is not yet measured." },
      { id: "yellow", question: "Which bottle and line should normally run yellow mustard?", impact: "JP remains excluded. Supported 10 Head/6 Head routes are the interim choice; confirm the normal bottle/line pairing." },
      { id: "cartons", question: "Which exact 20-piece SKU/carton replaces each old family, and can existing 16-piece FG ship as-is or must it be repacked?", impact: "Only verified transitions run by default. Old FG provisionally covers bottle demand without recartoning costs; whether it is 20-case-ready remains unanswered." },
      { id: "target", question: "Does the monthly sheet mean goods made this month, or available stock including opening goods?", impact: "This plan provisionally nets booked MTD from a production target and does not subtract current FG twice." },
      { id: "rates", question: "What is the typical changeover time?", impact: "The machine speeds are declared; the 1-hour campaign setup is still provisional and affects feasibility." },
      { id: "cost", question: "What is the labour cost of one 10-hour session on each line?", impact: "Recorded-run cost cannot establish session cost; unavailable is not zero." },
      { id: "value", question: "Is ₹2.5 crore required per calendar day or per production day?", impact: "Sunday currently has no production target; weekdays show the full desired value." },
      { id: "sales", question: "Which months should form the GT/MT trailing-sales average?", impact: "The approved monthly projection is retained; a new historical sales model is not claimed." },
    ],
  };
  if (input.materialSupply) {
    const supply = input.materialSupply;
    const actions: Omit<NonNullable<Mark4Model["materialSupply"]>["requiredActions"][number], "firstNeeded" | "affectedProducts">[] = [...supply.actions];
    for (const code of procurementUnresolved) actions.push({ id: `purchase-reconciliation:${code}`, code, quantity: null, unit: unit(code), reason: "New purchase quantity is unresolved; reconcile existing commitments before buying more.", ownerRole: "Purchase / stores", requiredConfirmation: "Link incoming loads to the existing PO and reconcile usable stock before placing another order.", evidenceIds: supply.lots.filter(lot => lot.code === code).flatMap(lot => lot.evidenceIds) });
    for (const material of materials.filter(row => row.shortage > 0)) if (!actions.some(row => row.code === material.code)) actions.push({ id: `schedule:${material.code}`, code: material.code, quantity: material.shortage, unit: material.unit, reason: "Scheduled production needs more usable material.", ownerRole: "Purchase / stores", requiredConfirmation: "Confirm the outstanding quantity and usable date, or arrange the remaining supply.", evidenceIds: [] });
    model.materialSupply = { ...supply, requiredActions: actions.map(action => {
      const affected = products.filter(product => days.some(day => day.blockers.some(blocker => blocker.materialCode === action.code && blocker.code === product.code)));
      return { ...action, firstNeeded: firstNeeded[action.code] ?? null, affectedProducts: affected.map(product => ({ code: product.code, name: product.name, dates: days.filter(day => day.blockers.some(blocker => blocker.materialCode === action.code && blocker.code === product.code)).map(day => day.date) })) };
    }) };
    if (compareSupply) {
      const other = buildModel(input, { ...scenario, supplyMode: scenario.supplyMode === "recorded" ? "expected" : "recorded" }, feedStatus, feedError, false);
      const totals = (result: Mark4Model) => ({ plannedLitres: result.summary.plannedLitres, knownPlannedValue: result.summary.knownPlannedValue, unvaluedLitres: result.summary.unvaluedLitres });
      model.materialSupply.comparison = scenario.supplyMode === "recorded" ? { recorded: totals(model), expected: totals(other) } : { expected: totals(model), recorded: totals(other) };
    }
  }
  if (scenario.allowProvisionalRecipes) { const baseline = buildModel(input, { ...scenario, allowProvisionalRecipes: false }, feedStatus, feedError, false); model.summary.strictBaseline = { plannedLitres: baseline.summary.plannedLitres, plannedValue: baseline.summary.plannedValue }; }
  assertInvariants(model);
  return model;
}

export function assertInvariants(model: Mark4Model): void {
  for (const day of model.days) {
    if (day.sunday && day.runs.length) throw new Error("Sunday production invariant failed.");
    const nightLines = new Set(day.runs.filter(r => r.nightHours > EPS).map(r => r.line));
    if (nightLines.size > 1) throw new Error("Night capacity invariant failed.");
    for (const line of LINE_IDS) {
      const runs = day.runs.filter(r => r.line === line);
      if (sum(runs.map(r => r.hours + r.setupHours)) > (day.nightLine === line ? 20 : 10) + EPS) throw new Error("Line capacity invariant failed.");
      for (const run of runs) { const p = model.products.find(p => p.code === run.code)!; if (!p.eligibility[line].allowed) throw new Error("Machine eligibility invariant failed."); }
    }
    const expected = day.storage.openingLitres + day.productionLitres - day.dispatchLitres;
    if (Math.abs(expected - day.storage.closingLitres) > .01) throw new Error("Physical storage conservation failed.");
    if (day.storage.unbilledLitres < -.01 || day.storage.billedWaitingLitres < -.01) throw new Error("Negative finished stock invariant failed.");
  }
  for (const m of model.materials) if (Math.abs(m.opening + m.arrivals - m.consumed - m.remaining) > .01 || m.remaining < -EPS) throw new Error("Material conservation failed.");
  for (const p of model.products) if (p.plannedPieces > p.requiredPieces + EPS || p.unmetPieces < -EPS) throw new Error("Demand conservation failed.");
}
