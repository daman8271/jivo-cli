export type SourceStamp = { id: string; label: string; asOf: string | null; ok: boolean; note?: string };
export type SourceItem = { name: string; uom: string };
export type Recipe = [string, number][];
export type PlanRow = { code: string; sku: string; category: string; head?: string; pack_type: string; litres_per_piece: number; pieces: number; litres?: number };
export type Order = { docnum: string; date: string; due: string; code: string | null; pieces: number; value?: number; channel: string; _src?: string; demand_basis?: string; is_exact_sku_due?: boolean; value_basis?: string; expiresAt?: string | null; status?: string; packLitres?: number | null; sourceLineId?: string; companyScope?: string; platform?: string; dueBasis?: string; remainingBasis?: string; requestedPieces?: number | null; requestedLitres?: number | null; remainingLitres?: number | null; sourcePackLitres?: number | null; sourceProductName?: string; sourceSkuCode?: string; mappingStatus?: string; code_mapping_verified?: boolean; mappingIssue?: string };
export type ActualDay = { date: string; made_mes_l: number | null; made_booked_l: number | null; booked_by_item: Record<string, number> | null; complete: boolean; settled?: boolean; notes?: string[]; mes_by_item_l?: Record<string, number> | null; bookedValue?: ActualValue; mesValue?: ActualValue };
export type ActualLine = { line: string; code?: string; product: string; litres: number | null; status: string; asOf: string | null; note?: string };
export type RateEvidence = { line: string; pack: string; piecesPerHour: number; basis: "rated" | "observed" | "derived" | "declared"; source: string; asOf: string | null };
export type Mark4Input = {
  schemaVersion: 1;
  meta: { as_of: string; frozen_at?: string; horizon?: number | string[]; month?: string; state_collected_at?: string; [key: string]: unknown };
  plan: PlanRow[]; bom: Record<string, Recipe>; blends: Record<string, Recipe>; items: Record<string, SourceItem>; realise: Record<string, number>;
  opening: { stock: Record<string, number>; fg: Record<string, number>; fg_other_l: number; standing_l: number; oil_l?: number; [key: string]: unknown };
  orders: Order[]; backlog?: Order[];
  inbound_prebooked: Record<string, Record<string, number>>;
  inbound_provenance?: Record<string, unknown>;
  lines: Record<string, Record<string, number>>; lines_basis?: unknown;
  history: { days: ActualDay[]; missing_dates: string[]; status: string };
  sources: SourceStamp[];
  actual_lines?: ActualLine[];
  dispatch_aging?: { pendingLitres: number | null; oldestDays: number | null; medianDays: number | null; asOf: string | null; note?: string };
  supplements?: { rates?: RateEvidence[]; cartonTransitions?: { from: string; to: string; evidence: string }[]; salesRank?: Record<string, number>; labourPerSession?: Record<string, number>; recordedLabour?: RecordedLabourInput; [key: string]: unknown };
  demandBook?: DemandBook;
  valuation?: Valuation;
  factoryIdentity?: { asOf: string | null; items: Record<string, { name: string; packLitres: number | null; uom: string }> };
  identityConflicts?: { code: string; reason: string; factoryName?: string; plannerName?: string; factoryPackLitres?: number | null; plannerPackLitres?: number | null }[];
  inboundEvents?: InboundEvent[];
  materialSupply?: MaterialSupply;
  notes?: string[];
};
export type Scenario = { shiftStartHour?: number; includePackagingEstimates?: boolean; supplyMode?: "expected" | "recorded"; nightLine: string | null; efficiency: number; allowProposedSupply: boolean; allowProvisionalRecipes: boolean; arrivalDates?: Record<string, string> };
export type Rule = { id: string; title: string; detail: string; status: "confirmed" | "assumption" | "provisional" | "unavailable"; source: string };
export type PlanningSpeed = { line: string; machine: string; pack: string; containersPerHour: number | null; status: "declared" | "unavailable" | "not separately scheduled" | "not modelled"; source: string; asOf: string };
export type Rate = RateEvidence & { effectivePiecesPerHour: number };
export type Eligibility = { allowed: boolean; preference: number; reason: string };
export type Product = {
  bottleComponentCodes?: string[];
  code: string; name: string; category: string; packLitres: number; container: "bottle" | "tin" | "pouch" | "drum" | "unknown";
  bottleGrams: number | null; fillLitres: number; containersPerPiece: number; cartonPieces: number | null; monthlyPieces: number; bookedMtdPieces: number | null; fgPieces: number;
  targetRemainingPieces: number; exactOrderPieces: number; allocatedOrderPieces: number; confirmedPieces: number; confirmedUncoveredPieces: number; forecastPieces: number; requiredPieces: number;
  plannedPieces: number; unmetPieces: number; valuePerLitre: number | null; bom: Recipe; originalCodes: string[];
  conditionalRecipe: boolean; transition: string | null; exclusionReason: string | null; notes: string[]; eligibility: Record<string, Eligibility>;
};
export type Material = { code: string; name: string; unit: string; opening: number; arrivals: number; consumed: number; remaining: number; shortage: number; firstNeeded: string | null; note: string; leadDays: number | null; orderBy: string | null; proposedQty: number | null; projectedArrival: string | null };
export type Blocker = { code: string; product: string; line: string | null; reason: string; materialCode?: string; materialName?: string; missingQuantity?: number; unit?: string };
export type Run = { startsAt?: string; endsAt?: string; idleHours?: number; conditionalSupply?: boolean; conditionalSupplyMaterials?: string[]; conditionalRecipe: boolean; line: string; code: string; product: string; pieces: number; litres: number; hours: number; dayHours: number; nightHours: number; setupHours: number; value: number | null; confirmedPieces: number; forecastPieces: number; reason: string; rate: Rate; labourCost: number | null; exactOrderPieces: number; allocatedOrderPieces: number; materials: { code: string; quantity: number; unit: string }[] };
export type Day = { date: string; sunday: boolean; runs: Run[]; blockers: Blocker[]; productionLitres: number; productionValue: number | null; knownProductionValue: number; unvaluedLitres: number; targetValue: number; targetGap: number | null; nightLine: string | null; dispatchLitres: number; storage: { openingLitres: number; madeLitres: number; dispatchedLitres: number; closingLitres: number; unbilledLitres: number; billedWaitingLitres: number; limitLitres: number; overLimitLitres: number }; arrivals: { code: string; name: string; quantity: number; unit: string; assumed: boolean }[] };
export type Line = { id: string; name: string; description: string; plannedLitres: number; hours: number; nightHours: number; availableHours: number; utilization: number; rates: Rate[]; actual: ActualLine[]; labourPerSession: number | null; recordedLabour: RecordedLabourSummary };
export type Mark4Model = {
  meta: { generatedAt: string; asOf: string; month: string; startDate: string; endDate: string; engine: string; feedStatus: "live" | "stale" | "seed"; feedError: string | null; inputAsOf: string; assumptions: string[] };
  materialSupply?: MaterialSupplyView;
  demandBook: DemandBook; planningBridge: PlanningBridge; inboundEvents: EvaluatedInboundEvent[];
  planningSpeeds: PlanningSpeed[]; sources: SourceStamp[]; scenario: Scenario; days: Day[]; lines: Line[]; products: Product[]; materials: Material[]; actuals: ActualDay[];
  summary: { plannedLitres: number; plannedValue: number | null; knownPlannedValue: number; unvaluedLitres: number; requiredLitres: number; unmetLitres: number; confirmedLitres: number; forecastLitres: number; excludedLitres: number; productionDays: number; targetValue: number; minimumDailyValue: number; desiredDailyValue: number; valueGap: number | null; storageLimitLitres: number; openingStorageLitres: number; peakStorageLitres: number; bookedMtdLitres: number | null; historyComplete: boolean; conditionalRecipeLitres?: number; conditionalSupplyLitres?: number; conditionalLitres: number; conditionalValue: number | null; strictBaseline?: { plannedLitres: number; plannedValue: number | null }; blockedProducts: number };
  dispatch: { pendingLitres: number; oldestDays: number | null; medianDays: number | null; asOf: string | null; note: string; usualDays: number; tailDays: number };
  rules: Rule[]; questions: { id: string; question: string; impact: string }[];
};

export type ActualValue = { value: number | null; knownValue: number; valuedLitres: number; unvaluedLitres: number; coverage: "complete" | "partial" | "unavailable"; basis: string; asOf: string | null; reconciled: boolean; sourceLitres: number | null; compositionLitres: number; lines: { code: string; pieces: number | null; litres: number | null; rupeesPerLitre: number | null; value: number | null; priceSource: string; packSource: string }[] };
export type Valuation = { asOf: string | null; priceBasis: string; litresPerPiece: Record<string, number>; rupeesPerLitre: Record<string, number> };
export type RecordedLabourRun = { id?: string; date: string; line: string; code: string; litres: number | null; labourCost: number | null };
export type RecordedLabourInput = { asOf: string | null; windowFrom: string | null; windowTo: string | null; basis: string; runs: RecordedLabourRun[] };
export type RecordedLabourSummary = { totalCost: number | null; runCount: number; litres: number | null; costPerLitre: number | null; windowFrom: string | null; windowTo: string | null; asOf: string | null; basis: string; costCoveredRunCount: number; missingCostRunCount: number; runs: RecordedLabourRun[] };
export type DemandBook = {
  asOf: string | null; coverage: "complete" | "partial" | "unavailable";
  online: { grossOpenLitres: number | null; quickCommerceLitres: number | null; amazonLitres: number | null; openValueExGst: number | null; openPoCount: number | null; priorMonthOpenLitres: number | null; dueThisMonthLitres: number | null; overdueLitres: number | null; laterDueLitres: number | null; undatedLitres: number | null; expiredExcludedLitres: number | null; unmappedLitres: number | null; byPlatform: { platform: string; litres: number; poCount: number }[]; dateBasis: string; planningDueLitres?: number | null; acceptedPlanningDueLitres?: number | null; acceptedOpenLitres?: number | null; amazonAcceptedRemainingLitres?: number | null; unacceptedRequestedLitres?: number | null; outsideOilScopeLitres?: number | null; outsideOilScopeAcceptedLitres?: number | null; outsideOilScopePlanningDueLitres?: number | null; outsideOilScopeAcceptedPlanningDueLitres?: number | null };
  trade: { grossOpenLitres: number | null; openOrderCount: number | null; openValueExGst: number | null; companyScope: string; scopeVerified: boolean; isNetOutstanding?: boolean; unknownActiveOrderCount?: number; unknownActiveOrders?: { id: string; status: string; createdAt: string | null; companyScope: "unknown"; litres: null }[]; isComplete?: boolean; headerAsOf?: string | null; dueThisMonthLitres?: number | null; overdueLitres?: number | null; laterDueLitres?: number | null; undatedLitres?: number | null; planningDueLitres?: number | null };
  reconciliationNotes: string[];
};
export type QuarantinedOrder = { id: string; code: string | null; sourceProductName: string | null; litres: number | null; reason: string };
export type PlanningBridge = { quarantinedOrders: QuarantinedOrder[];  grossDueLitres: number | null; mappedLitres: number; unmappedLitres: number | null; stockCoveredLitres: number; netMakeLitres: number; unschedulableLitres: number; projectionReserveLitres: number; explicitUnacceptedLitres: number | null; outsideOilScopeLitres: number | null; knownGrossDueLitres: number | null; unknownActiveOrderCount: number; notes: string[] };
export type InboundEvent = { id: string; source: "factory_po" | "exim_transit" | "qc" | "legacy"; code: string; quantity: number; unit: string; orderedAt: string | null; expectedAt: string | null; asOf: string | null; dateBasis: "supplier_due" | "transit_eta" | "observed_lead" | "unverified"; status: "open" | "in_transit" | "qc" | "received" | "cancelled"; confidence: "confirmed" | "estimated" | "unknown"; stockIncluded: boolean | null; linkedOrderId?: string; note?: string };
export type EvaluatedInboundEvent = InboundEvent & { included: boolean; appliedAt: string | null; readyAt?: string | null; conditional: boolean; reason: string };

export type MaterialSupply = {
  version: 1; revision: string; asOf: string;
  unmappedShipments?: { name: string; quantity: number | null; unit: string; eta: string | null; stage: string }[];
  coverage: { complete: boolean; datasets: { id: string; asOf: string | null; attemptedAt: string | null; ok: boolean; complete: boolean; expectedRefreshSeconds: number; note?: string }[] };
  stock: { asOf: string | null; byItem: Record<string, number>; unitByItem?: Record<string, string>; oilSourcePolicy?: "exim_only"; unmappedOils?: { name: string; quantity: number; unit: string }[]; byWarehouse: unknown; excludedWarehouses: unknown[]; conflicts: unknown[] };
  orders: { id: string; code: string; unit: string; orderedAt: string | null; orderedQty: number; bookReceivedQty: number; outstandingQty: number; notYetAtGateQty: number; reconciliationComplete?: boolean; notYetAtGateBasis?: "lifetime_receipts_net_book" | "unreconciled_upper_bound"; atGateQty: number; sourceAsOf: string | null }[];
  lots: { id: string; code: string; quantity: number; unit: string; stage: "ordered" | "loading" | "in_transit" | "arrived" | "qc_pending" | "accepted_unposted" | "usable" | "rejected" | "cancelled" | "conflict"; orderId?: string; shipmentId?: string; receiptId?: string; observedAt: string | null; stockInclusion: "included" | "excluded" | "unresolved"; arrivalDate?: string | null; availabilityDate?: string | null; evidenceIds: string[]; reason: string }[];
  expectedReceipts: { id: string; lotId: string; orderId?: string; code: string; quantity: number; unit: string; arrivalEarliest: string | null; arrivalExpected: string | null; arrivalLatest: string | null; usableEarliest: string | null; usableExpected: string | null; usableLatest: string | null; basis: "supplier_due" | "shipment_eta" | "supplier_item_history" | "temporary_packaging_estimate" | "qc_history"; readyAt?: string | null; temporaryUntil?: string | null; confidence: "recorded" | "estimated"; timingVersion?: 1 | 2; sourceArrivalAt?: string | null; arrivalTimeKnown?: boolean; qaMedianHours?: number | null; qaEstimatedAt?: string | null; storesReleaseAt?: string | null; sampleCount: number; historyFrom: string | null; historyTo: string | null; evidenceIds: string[]; note: string }[];
  actions: { id: string; code: string; quantity: number; unit: string; orderId?: string; reason: string; ownerRole: string; requiredConfirmation: string; evidenceIds: string[] }[];
};
export type MaterialSupplyView = MaterialSupply & {
  comparison?: { expected: { plannedLitres: number; knownPlannedValue: number; unvaluedLitres: number }; recorded: { plannedLitres: number; knownPlannedValue: number; unvaluedLitres: number } };
  requiredActions: (Omit<MaterialSupply["actions"][number], "quantity"> & { quantity: number | null; firstNeeded: string | null; affectedProducts: { code: string; name: string; dates: string[] }[] })[];
};
