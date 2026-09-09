import { comparableInboundUnit, normalizedUnit, ScenarioInputError } from "./evidence.ts";
import type { EvaluatedInboundEvent, Mark4Input, MaterialSupply, Scenario } from "./types.ts";

const validDate = (v: unknown): v is string => typeof v === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v) && Number.isFinite(Date.parse(v)) && new Date(`${v}T12:00:00Z`).toISOString().slice(0, 10) === v;
const amount = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v) && v >= 0;

const sourceEtaMissed = (eta: string | null | undefined, now: string): boolean => {
  if (!eta) return false;
  // Missing arrival time means the source has the whole IST calendar day.
  const deadline = eta.length === 10 ? Date.parse(`${eta}T23:59:59.999+05:30`) : Date.parse(/(?:Z|[+-]\d{2}:\d{2})$/.test(eta) ? eta : `${eta}+05:30`);
  return Number.isFinite(deadline) && deadline < Date.parse(now);
};

export function eximOnlyStock(supply: MaterialSupply): MaterialSupply {
  if (supply.stock.oilSourcePolicy === "exim_only") return supply;
  const stock = { ...supply.stock, byItem: { ...supply.stock.byItem }, oilSourcePolicy: "exim_only" as const };
  const warehouses = supply.stock.byWarehouse;
  if (warehouses && typeof warehouses === "object" && !Array.isArray(warehouses)) {
    stock.byWarehouse = Object.fromEntries(Object.entries(warehouses).map(([warehouse, rows]) => [warehouse, Array.isArray(rows) ? rows.map(row => {
      if (!row || typeof row !== "object" || typeof row.code !== "string" || !row.code.startsWith("RM")) return row;
      if (row.included === true) {
        // Missing conversion cannot safely retain a factory contribution.
        stock.byItem[row.code] = amount(row.normalizedQuantity) ? Math.max(0, (stock.byItem[row.code] ?? 0)-row.normalizedQuantity) : 0;
      }
      return { ...row, included: false, reason: "Excluded: opening oil uses EXIM only; no factory balance fallback." };
    }) : rows]));
  }
  return { ...supply, stock };
}

export function validateMaterialSupply(supply: MaterialSupply): void {
  if (!supply || supply.version !== 1 || typeof supply.revision !== "string" || !supply.revision || !supply.stock?.byItem || !supply.coverage || !Array.isArray(supply.coverage.datasets) || !Array.isArray(supply.orders) || !Array.isArray(supply.lots) || !Array.isArray(supply.expectedReceipts) || !Array.isArray(supply.actions)) throw new Error("Material supply reconciliation is incomplete.");
  if (!Array.isArray(supply.stock.conflicts) || !Array.isArray(supply.stock.excludedWarehouses)) throw new Error("Material stock coverage is missing.");
  for (const dataset of supply.coverage.datasets) if (!dataset.id || typeof dataset.ok !== "boolean" || typeof dataset.complete !== "boolean" || !amount(dataset.expectedRefreshSeconds) || dataset.expectedRefreshSeconds <= 0) throw new Error("Material source refresh contract is invalid.");
  for (const quantity of Object.values(supply.stock.byItem)) if (!amount(quantity)) throw new Error("Reconciled stock has invalid quantities.");
  const orderIds = new Set<string>();
  for (const order of supply.orders) {
    if (!order.id || orderIds.has(order.id) || !order.code || !order.unit || [order.orderedQty, order.bookReceivedQty, order.outstandingQty, order.notYetAtGateQty, order.atGateQty].some(value => !amount(value))) throw new Error("Material purchase order identity or quantities are invalid.");
    orderIds.add(order.id);
  }
  const lotIds = new Set<string>();
  for (const lot of supply.lots) {
    if (!lot.id || lotIds.has(lot.id) || !lot.code || !amount(lot.quantity) || !lot.unit || !Array.isArray(lot.evidenceIds) || !["ordered", "loading", "in_transit", "arrived", "qc_pending", "accepted_unposted", "usable", "rejected", "cancelled", "conflict"].includes(lot.stage) || !["included", "excluded", "unresolved"].includes(lot.stockInclusion)) throw new Error("Material lot identity or quantity is invalid.");
    lotIds.add(lot.id);
  }
  for (const order of supply.orders) {
    const pendingLots = supply.lots.filter(lot => lot.orderId === order.id && lot.stockInclusion === "excluded" && !["cancelled", "rejected", "conflict"].includes(lot.stage));
    const comparableLots = pendingLots.filter(lot => normalizedUnit(lot.unit) === normalizedUnit(order.unit));
    if (comparableLots.reduce((total, lot) => total + lot.quantity, 0) > order.outstandingQty + .001) throw new Error("Incoming lots exceed their purchase order outstanding quantity.");
  }
  const receiptIds = new Set<string>();
  const receiptsPerLot = new Set<string>();
  for (const receipt of supply.expectedReceipts) {
    const lot = supply.lots.find(row => row.id === receipt.lotId);
    if (!lot || !receipt.id || receiptIds.has(receipt.id) || receiptsPerLot.has(receipt.lotId) || receipt.code !== lot.code || !amount(receipt.quantity) || !receipt.unit || !["recorded", "estimated"].includes(receipt.confidence)) throw new Error("Material receipt identity or quantity is invalid; split partial receipts into distinct lots.");
    if (normalizedUnit(receipt.unit) !== normalizedUnit(lot.unit)) throw new Error("Expected receipt and lot need the same verified normalized unit.");
    if (receipt.quantity > lot.quantity + .001) throw new Error("Expected receipt exceeds its physical lot.");
    if (!Array.isArray(receipt.evidenceIds) || !amount(receipt.sampleCount) || !["supplier_due", "shipment_eta", "supplier_item_history", "temporary_packaging_estimate", "qc_history"].includes(receipt.basis)) throw new Error("Expected receipt evidence is invalid.");
    if (receipt.confidence === "recorded" && ["supplier_item_history", "temporary_packaging_estimate", "qc_history"].includes(receipt.basis)) throw new Error("Historical availability cannot be labelled recorded.");
    for (const key of ["arrivalEarliest", "arrivalExpected", "arrivalLatest", "usableEarliest", "usableExpected", "usableLatest"] as const) if (receipt[key] !== null && !validDate(receipt[key])) throw new Error("Material receipt has an invalid date.");
    if (receipt.timingVersion === 1 || receipt.timingVersion === 2) {
      const source = receipt.sourceArrivalAt;
      const qa = receipt.qaEstimatedAt;
      const validTimestamp = (value: unknown): value is string => typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value)) && validDate(value.slice(0, 10));
      if (!amount(receipt.qaMedianHours) || !(validDate(source) || validTimestamp(source)) || !validTimestamp(qa) || typeof receipt.arrivalTimeKnown !== "boolean" || receipt.arrivalTimeKnown !== (source.length > 10) || !receipt.usableExpected) throw new Error("Hour-level QC timing metadata is incomplete or invalid.");
      const arrivalInstant = Date.parse(source.length === 10 ? `${source}T23:59:59.999+05:30` : source);
      if (Date.parse(qa) < arrivalInstant) throw new Error("Estimated QA cannot precede source arrival.");
      for (const key of ["readyAt", "storesReleaseAt"] as const) if (receipt[key] != null && (!validTimestamp(receipt[key]) || Date.parse(receipt[key]!) < (key === "storesReleaseAt" ? arrivalInstant : Date.parse(qa)))) throw new Error("Material readiness cannot precede QA clearance.");
      if (receipt.timingVersion === 1 && Date.parse(`${receipt.usableExpected}T00:00:00+05:30`) < Date.parse(qa)) throw new Error("Planning stock cannot be credited before its estimated QA timestamp.");
    }
    const order = supply.orders.find(row => row.id === lot.orderId);
    if (order?.orderedAt && receipt.usableExpected && receipt.usableExpected < order.orderedAt.slice(0, 10)) throw new Error("Material cannot be available before its purchase order.");
    if (receipt.usableExpected && receipt.arrivalExpected && receipt.usableExpected < receipt.arrivalExpected) throw new Error("Material cannot be usable before arrival.");
    for (const prefix of ["arrival", "usable"] as const) {
      const [earliest, expected, latest] = [receipt[`${prefix}Earliest`], receipt[`${prefix}Expected`], receipt[`${prefix}Latest`]];
      if (earliest && expected && earliest > expected || latest && expected && latest < expected || earliest && latest && earliest > latest) throw new Error("Material receipt window is reversed.");
    }
    receiptIds.add(receipt.id); receiptsPerLot.add(receipt.lotId);
  }
}

// Only the reconciled lot ledger owns arrivals when present. Older EXIM and PO
// aggregates must never be appended to it: they describe the same physical goods.
export function reconciledInbound(input: Mark4Input, end: string, scenario: Scenario): EvaluatedInboundEvent[] {
  const supply = input.materialSupply!;
  validateMaterialSupply(supply);
  const start = input.meta.as_of.slice(0, 10);
  const dates = scenario.arrivalDates ?? {};
  const events = supply.lots.map(lot => {
    const receipt = supply.expectedReceipts.find(row => row.lotId === lot.id);
    // v1 cached daily buckets are display dates, not an extra factory hold.
    // A source Stores release takes priority over the QA estimate.
    const readyAt = receipt?.storesReleaseAt ?? receipt?.readyAt ?? ((receipt?.timingVersion === 1 || receipt?.timingVersion === 2) ? receipt.qaEstimatedAt : null) ?? lot.availabilityDate ?? receipt?.usableExpected ?? null;
    const readyTime = readyAt ? Date.parse(readyAt.length === 10 ? `${readyAt}T00:00:00+05:30` : readyAt) : NaN;
    const usable = Number.isFinite(readyTime) ? new Date(readyTime + 19800000).toISOString().slice(0, 10) : null;
    const event: EvaluatedInboundEvent = {
      id: lot.id, source: lot.shipmentId ? "exim_transit" : ["arrived", "qc_pending", "accepted_unposted"].includes(lot.stage) ? "qc" : "factory_po",
      code: lot.code, quantity: receipt?.quantity ?? lot.quantity, unit: receipt?.unit ?? lot.unit,
      orderedAt: supply.orders.find(row => row.id === lot.orderId)?.orderedAt ?? null,
      expectedAt: usable, asOf: lot.observedAt, linkedOrderId: lot.orderId,
      dateBasis: receipt?.basis === "supplier_due" ? "supplier_due" : receipt?.basis === "shipment_eta" ? "transit_eta" : receipt ? "observed_lead" : "unverified",
      status: ["rejected", "cancelled", "conflict"].includes(lot.stage) ? "cancelled" : lot.stockInclusion === "included" ? "received" : ["arrived", "qc_pending", "accepted_unposted"].includes(lot.stage) ? "qc" : lot.stage === "in_transit" ? "in_transit" : "open",
      confidence: receipt?.confidence === "recorded" ? "confirmed" : receipt ? "estimated" : "unknown",
      stockIncluded: lot.stockInclusion === "included" ? true : lot.stockInclusion === "excluded" ? false : null,
      readyAt: Number.isFinite(readyTime) ? new Date(readyTime).toISOString() : null, note: `${lot.reason} ${receipt?.note ?? ""}`, included: false, appliedAt: null, conditional: receipt?.confidence !== "recorded", reason: "",
    };
    if (event.status === "cancelled") event.reason = "Rejected, cancelled or conflicting lot; no usable material credit.";
    else if (event.stockIncluded === true) event.reason = "Already included in usable stock; counted once.";
    else if (event.stockIncluded === null) event.reason = "Stock inclusion is unresolved; the store team must reconcile this lot before it can be credited.";
    else if (!comparableInboundUnit(event, input)) event.reason = "Material unit conversion is unconfirmed; quantity remains visible but is not added to usable stock.";
    else if (event.quantity <= 0) event.reason = "No positive quantity remains.";
    else if (receipt?.basis === "temporary_packaging_estimate" && (!lot.code.startsWith("PM") || !receipt.temporaryUntil || !validDate(receipt.temporaryUntil) || start > receipt.temporaryUntil || scenario.includePackagingEstimates === false)) event.reason = "Temporary packaging estimate is disabled or expired; obtain the supplier date.";
    else if (receipt?.basis === "supplier_item_history") event.reason = "Historical delivery cadence is disabled. Obtain a source delivery date for this outstanding order.";
    else if (["in_transit", "loading", "ordered"].includes(lot.stage) && sourceEtaMissed(receipt?.sourceArrivalAt ?? lot.arrivalDate ?? receipt?.arrivalExpected, input.meta.as_of)) event.reason = "Source arrival date passed without a linked gate receipt. A revised source ETA is required; QA estimates cannot move the arrival date forward.";
    else if (receipt?.confidence === "estimated" && ["shipment_eta", "qc_history"].includes(receipt.basis) && ![1, 2].includes(receipt.timingVersion ?? 0)) event.reason = "Cached QC estimate uses whole dates. Refresh hour-level receiving-to-QA timing before planning production.";
    else if (lot.stage === "qc_pending" && [1, 2].includes(receipt?.timingVersion ?? 0) && receipt?.qaEstimatedAt && lot.observedAt && Date.parse(receipt.qaEstimatedAt) < Date.parse(lot.observedAt)) event.reason = "Expected QA approval time passed, but the latest source observation still says QC pending. A QA update is needed before this lot can be planned.";
    else if (dates[lot.id]) {
      if (!validDate(dates[lot.id]) || dates[lot.id] < start || dates[lot.id] > end) throw new ScenarioInputError("Assumed availability must be inside the remaining planning month.");
      if (usable && dates[lot.id] < usable) throw new ScenarioInputError("Your assumed date cannot precede the source arrival, QA or Stores readiness already known for this lot.");
      const arrivalFloor = receipt?.sourceArrivalAt ?? lot.arrivalDate ?? receipt?.arrivalExpected;
      if (arrivalFloor && dates[lot.id] < arrivalFloor.slice(0, 10)) throw new ScenarioInputError("Your assumed date cannot precede the source arrival.");
      const arrivalFloorInstant = arrivalFloor ? Date.parse(arrivalFloor.length === 10 ? `${arrivalFloor}T23:59:59.999+05:30` : arrivalFloor) : NaN;
      event.conditional = true;
      if (scenario.supplyMode === "recorded") event.reason = "Your date assumption is excluded from the recorded-dates comparison.";
      else { event.included = true; event.appliedAt = dates[lot.id]; event.readyAt = new Date(Math.max(Date.parse(`${dates[lot.id]}T00:00:00+05:30`), Number.isFinite(readyTime) ? readyTime : 0, Number.isFinite(arrivalFloorInstant) ? arrivalFloorInstant : 0)).toISOString(); event.reason = "Your assumed usable date for this existing lot; not a source confirmation."; }
    } else if (!validDate(usable)) event.reason = "Usable date is unknown. An order or truck ETA alone does not establish QC clearance and availability.";
    else if (usable < start) event.reason = "Expected availability is overdue; a new supplier, gate or QC update is needed.";
    else if (usable > end) event.reason = "Expected usable stock is outside this month; kept visible in the incoming book.";
    else if (!receipt || receipt.evidenceIds.length === 0) event.reason = "No dated availability evidence is linked to this lot.";
    else if (receipt.confidence === "estimated" && receipt.sampleCount < 3) event.reason = "Fewer than three observations support this availability estimate; confirm the date.";
    else if (receipt.confidence === "estimated" && scenario.supplyMode === "recorded") event.reason = "Historical availability estimate is excluded in recorded-dates mode.";
    else { event.included = true; event.appliedAt = usable; event.reason = receipt.confidence === "recorded" ? "Recorded expected usable date for an existing lot; still a future commitment, not stock already received." : "Source arrival plus matching elapsed receiving-to-QA hours; the first suitable remaining shift hours can begin after estimated QA. No further stores delay is assumed, and actual stores release remains unverified."; }
    if (dates[lot.id] && !event.included && scenario.supplyMode !== "recorded") throw new ScenarioInputError(`This lot cannot take an availability assumption: ${event.reason}`);
    return event;
  });
  if (Object.keys(dates).some(id => !events.some(row => row.id === id))) throw new ScenarioInputError("An assumed incoming lot no longer exists. Clear the old dates and refresh the source book.");
  return events;
}
