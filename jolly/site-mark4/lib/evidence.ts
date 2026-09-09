import type { ActualDay, ActualValue, DemandBook, EvaluatedInboundEvent, InboundEvent, Mark4Input, Order, Product, RecordedLabourSummary } from "./types.ts";

import { identityConflict } from "./identity.ts";

const finite = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);
const quantity = (v: unknown): number => finite(v) && v > 0 ? v : 0;
const sum = (values: number[]) => values.reduce((a, b) => a + b, 0);
const dateOnly = (value: string | null | undefined): string | null => value && /^\d{4}-\d{2}-\d{2}/.test(value) && Number.isFinite(Date.parse(value)) ? value.slice(0, 10) : null;

export function activeOrder(order: Order, asOf: string): boolean {
  const status = (order.status ?? "").toLowerCase().replace(/[^a-z]/g, "");
  if ((quantity(order.pieces) <= 0 && quantity(order.remainingLitres) <= 0) || ["cancelled", "canceled", "closed", "expired", "fulfilled", "fullyfulfilled", "delivered", "fullydelivered", "complete", "completed", "rejected", "billingrejected", "void"].includes(status)) return false;
  const expiry = dateOnly(order.expiresAt);
  if (expiry && expiry < asOf.slice(0, 10)) return false;
  if (order.expiresAt && order.expiresAt.includes("T") && Date.parse(order.expiresAt) < Date.parse(asOf)) return false;
  return true;
}

export function currentMonthOrder(order: Order, asOf: string): boolean {
  if (!activeOrder(order, asOf)) return false;
  const due = dateOnly(order.due);
  // Unknown due date remains in the book; it is not silently assigned a current-month deadline.
  return due !== null && due.slice(0, 7) <= asOf.slice(0, 7);
}

export function withActualValues(days: ActualDay[], input: Mark4Input): ActualDay[] {
  const planPacks = Object.fromEntries(input.plan.map(p => [p.code, p.litres_per_piece]));
  const packs = { ...planPacks, ...(input.valuation?.litresPerPiece ?? {}) };
  const prices = { ...input.realise, ...(input.valuation?.rupeesPerLitre ?? {}) };
  for (const transition of input.supplements?.cartonTransitions ?? []) {
    if (!packs[transition.to] && packs[transition.from]) packs[transition.to] = packs[transition.from];
    if (!finite(prices[transition.to]) && finite(prices[transition.from])) prices[transition.to] = prices[transition.from];
  }
  for (const code of new Set([...Object.keys(prices), ...Object.keys(packs)])) if (identityConflict(input, code)) {
    delete prices[code];
    const factoryPack = input.factoryIdentity?.items[code]?.packLitres;
    if (finite(factoryPack) && factoryPack > 0) packs[code] = factoryPack; else delete packs[code];
  }
  const priceBasis = input.valuation?.priceBasis ?? "Inherited SKU realisation table; valuation date is unavailable. This estimates goods value, not billed revenue.";
  const asOf = input.valuation?.asOf ?? null;
  const value = (day: ActualDay, kind: "booked" | "mes"): ActualValue => {
    const composition = kind === "booked" ? day.booked_by_item : day.mes_by_item_l;
    const sourceTotal = kind === "booked" ? day.made_booked_l : day.made_mes_l;
    const lines: ActualValue["lines"] = Object.entries(composition ?? {}).filter(([, v]) => finite(v) && v >= 0).map(([code, qty]) => {
      const litres = kind === "mes" ? qty : finite(packs[code]) && packs[code] > 0 ? qty * packs[code] : null;
      const price = finite(prices[code]) && prices[code] > 0 ? prices[code] : null;
      return { code, pieces: kind === "booked" ? qty : null, litres, rupeesPerLitre: price, value: litres !== null && price !== null ? litres * price : litres === 0 ? 0 : null, priceSource: price === null ? identityConflict(input, code) ? "Price withheld: factory identity conflicts with inherited planner/price identity" : "SKU price unavailable" : `${priceBasis}${code === "FG0000155" && price > 700 ? " This SKU carries a flagged high inherited realisation; verify before treating its value as reliable." : ""}`, packSource: kind === "mes" ? "Per-SKU MES litres from the factory" : input.valuation?.litresPerPiece[code] ? "Verified source pack conversion" : packs[code] ? "Dated plan or verified 16/20 family pack conversion" : "Pack conversion unavailable" };
    });
    const compositionLitres = sum(lines.map(l => l.litres ?? 0));
    const sourceLitres = finite(sourceTotal) && sourceTotal >= 0 ? sourceTotal : null;
    const zeroObservation = sourceLitres === 0 && compositionLitres === 0;
    const unknownPack = lines.some(l => l.litres === null && quantity(l.pieces) > 0);
    const reconciled = zeroObservation || (sourceLitres !== null && composition !== null && composition !== undefined && !unknownPack && Math.abs(sourceLitres - compositionLitres) <= Math.max(.05, sourceLitres * .0001));
    const knownValue = sum(lines.map(l => l.value ?? 0));
    const valuedLitres = sum(lines.filter(l => l.value !== null).map(l => l.litres ?? 0));
    const unvaluedLitres = sum(lines.filter(l => l.value === null).map(l => l.litres ?? 0)) + Math.max(0, (sourceLitres ?? compositionLitres) - compositionLitres);
    const allPriced = lines.every(l => l.value !== null);
    const complete = reconciled && (zeroObservation || allPriced);
    const coverage = complete ? "complete" : knownValue > 0 || valuedLitres > 0 ? "partial" : "unavailable";
    const basis = `${kind === "booked" ? "Booked-by-item pieces × verified pack litres" : "Per-item MES litres"} × each SKU's price. ${priceBasis} ${!reconciled ? "Composition does not fully reconcile the source total; only traced items are valued." : "Composition reconciles the source litres."} MES and booked figures overlap and must never be added.`;
    return { value: complete ? knownValue : null, knownValue, valuedLitres, unvaluedLitres, coverage, basis, asOf, reconciled, sourceLitres, compositionLitres, lines };
  };
  return days.map(day => ({ ...day, bookedValue: value(day, "booked"), mesValue: value(day, "mes") }));
}

export function recordedLabour(input: Mark4Input, line: string): RecordedLabourSummary {
  const source = input.supplements?.recordedLabour;
  const seen = new Set<string>();
  const runs = (source?.runs ?? []).filter(r => r.line === line).filter(r => {
    if (!r.id) return true; // Two legitimate identical rows must not disappear without a source identity.
    if (seen.has(r.id)) return false; seen.add(r.id); return true;
  }).map(r => ({ id: r.id, date: r.date, line: r.line, code: r.code, litres: finite(r.litres) && r.litres >= 0 ? r.litres : null, labourCost: finite(r.labourCost) && r.labourCost >= 0 ? r.labourCost : null }));
  const priced = runs.filter(r => r.labourCost !== null);
  const paired = priced.filter(r => r.litres !== null && r.litres > 0);
  const pairedLitres = sum(paired.map(r => r.litres ?? 0));
  return { totalCost: priced.length ? sum(priced.map(r => r.labourCost ?? 0)) : null, runCount: runs.length, litres: runs.some(r => r.litres !== null) ? sum(runs.map(r => r.litres ?? 0)) : null, costPerLitre: pairedLitres > 0 ? sum(paired.map(r => r.labourCost ?? 0)) / pairedLitres : null, windowFrom: source?.windowFrom ?? null, windowTo: source?.windowTo ?? null, asOf: source?.asOf ?? null, basis: `${source?.basis ?? "No recorded factory labour source supplied."} Cost/litre uses only runs with both cost and litres. Recorded run cost is not a verified ten-hour session price.`, costCoveredRunCount: priced.length, missingCostRunCount: runs.length - priced.length, runs };
}

export function grossDemandBook(input: Mark4Input): DemandBook {
  if (input.demandBook) return input.demandBook;
  // Old seeds never had the full source PO book. Refuse to relabel plan-filtered allocations as its total.
  return { asOf: input.meta.state_collected_at ?? input.meta.as_of, coverage: "unavailable", online: { grossOpenLitres: null, quickCommerceLitres: null, amazonLitres: null, openValueExGst: null, openPoCount: null, priorMonthOpenLitres: null, dueThisMonthLitres: null, overdueLitres: null, laterDueLitres: null, undatedLitres: null, expiredExcludedLitres: null, unmappedLitres: null, byPlatform: [], dateBasis: "The legacy seed contains plan-filtered SKU allocations, not an independently reconciled open PO book." }, trade: { grossOpenLitres: null, openOrderCount: null, openValueExGst: null, companyScope: "Oil identity only; other-company rows are quarantined", scopeVerified: false }, reconciliationNotes: ["Gross source demand is unavailable in this legacy snapshot. It must not be inferred from uncovered factory make demand or the monthly production projection."] };
}

export class ScenarioInputError extends Error {}
export const normalizedUnit = (unit: string) => /^(l|ltr|litre|litres|liter|liters)$/i.test(unit) ? "L" : /^(pc|pcs|piece|pieces|nos|each|ea)$/i.test(unit) ? "PCS" : /^(kg|kgs|kilogram|kilograms)$/i.test(unit) ? "KG" : unit.toUpperCase();
export function comparableInboundUnit(event: InboundEvent, input: Mark4Input): boolean {
  const expected = input.materialSupply?.stock.unitByItem?.[event.code] ?? (event.code.startsWith("RM") ? "L" : input.items[event.code]?.uom);
  return !!expected && normalizedUnit(event.unit) === normalizedUnit(expected);
}
export function evaluateInbound(input: Mark4Input, end: string, arrivalDates: Record<string, string> = {}): EvaluatedInboundEvent[] {
  const start = input.meta.as_of.slice(0, 10);
  let events: InboundEvent[];
  if (input.inboundEvents !== undefined) events = input.inboundEvents;
  else events = Object.entries(input.inbound_prebooked ?? {}).flatMap(([date, entries]) => Object.entries(entries).map(([code, amount]) => {
    const provenance = String((input.inbound_provenance?.[date] as Record<string, unknown> | undefined)?.[code] ?? "unverified");
    const exactTransit = /^EXIM-OTW$/.test(provenance);
    return { id: `legacy:${date}:${code}`, source: "legacy" as const, code, quantity: amount, unit: code.startsWith("RM") ? "L" : input.items[code]?.uom ?? "pieces", orderedAt: null, expectedAt: date, asOf: input.meta.state_collected_at ?? input.meta.as_of, dateBasis: exactTransit ? "transit_eta" as const : "unverified" as const, status: exactTransit ? "in_transit" as const : "open" as const, confidence: exactTransit ? "confirmed" as const : "unknown" as const, stockIncluded: exactTransit ? false : null, note: `Legacy merged provenance: ${provenance}. ${exactTransit ? "" : "Needs per-event source reconciliation; aggregate quantity is not credited as certain material."}` };
  }));
  const uniqueEvents = new Map<string, InboundEvent>();
  for (const event of events) {
    const previous = uniqueEvents.get(event.id);
    if (previous) {
      const identity = (entry: InboundEvent) => JSON.stringify([entry.source, entry.code, entry.quantity, normalizedUnit(entry.unit), entry.expectedAt, entry.dateBasis, entry.status, entry.confidence, entry.stockIncluded, entry.linkedOrderId]);
      if (identity(previous) !== identity(event)) throw new Error("Conflicting incoming source event identities require reconciliation.");
    } else uniqueEvents.set(event.id, event);
  }
  events = [...uniqueEvents.values()];
  for (const [id, date] of Object.entries(arrivalDates)) {
    const event = events.find(event => event.id === id);
    if (!event) throw new ScenarioInputError("An incoming material selection no longer exists. Refresh the source book and select it again.");
    if (date < start || date > end) throw new ScenarioInputError("Assumed incoming dates must be inside the displayed planning month and cannot precede its start.");
    if (event.quantity <= 0 || ["cancelled", "received"].includes(event.status) || event.stockIncluded !== false || !comparableInboundUnit(event, input)) throw new ScenarioInputError("This incoming entry is not eligible for a date assumption: it is received, cancelled, already in stock, or unresolved in quantity/unit.");
  }
  const seen = new Set<string>();
  return events.map(event => {
    const row: EvaluatedInboundEvent = { ...event, included: false, appliedAt: null, conditional: event.confidence !== "confirmed", reason: "" };
    if (seen.has(event.id)) { row.reason = "Duplicate source event identity; credited once only."; return row; } seen.add(event.id);
    if (!comparableInboundUnit(event, input)) row.reason = "Incoming unit does not match the normalized material ledger; a verified conversion is required.";
    else if (!finite(event.quantity) || event.quantity <= 0) row.reason = "No positive outstanding quantity.";
    else if (event.status === "cancelled") row.reason = "Cancelled commitment; no material credit.";
    else if (event.status === "received" || event.stockIncluded === true) row.reason = "Received/already included in opening stock; adding again would double-count material.";
    else if (event.stockIncluded !== false) row.reason = "Whether opening stock already includes this quantity is unresolved; awaiting reconciliation.";
    else if (arrivalDates[event.id]) { row.included = true; row.appliedAt = arrivalDates[event.id]; row.conditional = true; row.reason = "Your assumed availability date for an existing commitment. This is a what-if, not a supplier promise, receipt, or confirmed QC release."; }
    else if (!dateOnly(event.expectedAt)) row.reason = "No supported material availability date; supplier or QC must confirm it.";
    else if (dateOnly(event.expectedAt)! < start) row.reason = "Expected date is overdue. Arrival is not assumed today; obtain a revised commitment or receipt.";
    else if (dateOnly(event.expectedAt)! > end) row.reason = "Commitment remains in the incoming book, outside this month's schedule.";
    else if (event.dateBasis === "unverified" || event.confidence === "unknown") row.reason = "Date/availability basis is unverified; not credited to the main schedule.";
    else if (event.status === "qc" && event.confidence !== "confirmed") row.reason = "QC has not provided a confirmed release; stock is not production-ready.";
    else if (event.source === "legacy" && event.dateBasis !== "transit_eta") row.reason = "Legacy aggregate is not a reconciled supplier commitment.";
    else { row.included = true; row.appliedAt = dateOnly(event.expectedAt); row.reason = event.confidence === "confirmed" ? "Dated existing commitment credited as expected material; not a recorded receipt." : "Existing issued commitment uses an evidence-based estimated date. Included conditionally; not a new hypothetical purchase."; }
    return row;
  });
}
