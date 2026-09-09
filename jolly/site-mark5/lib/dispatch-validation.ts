import type { DispatchFeed, GateEntry, DispatchTotals } from "./dispatch-types.ts";
const object = (v: unknown): v is Record<string, unknown> => !!v && typeof v === "object" && !Array.isArray(v);
const text = (v: unknown) => typeof v === "string" && v.length <= 2000;
const count = (v: unknown) => typeof v === "number" && Number.isInteger(v) && v >= 0;
const quantity = (v: unknown) => v === null || typeof v === "number" && Number.isFinite(v) && v >= 0;
const date = (v: unknown) => typeof v === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v) && new Date(`${v}T00:00:00Z`).toISOString().slice(0,10) === v;
const instant = (v: unknown) => typeof v === "string" && /(?:Z|[+-]\d\d:\d\d)$/.test(v) && Number.isFinite(Date.parse(v));
const fail = () => { throw new Error("Dispatch source has an invalid or inconsistent record."); };
const operationalKeys = [["operationalWellnessLitres", "WELLNESS"], ["operationalMartLitres", "MART"], ["operationalUnclassifiedLitres", "UNKNOWN"]] as const;
function matches(actual: unknown, expected: number | null) { return expected === null ? actual === null : typeof actual === "number" && Math.abs(actual - expected) < 0.02; }
function validateOperationalTotals(total: DispatchTotals, rows: GateEntry[]) {
  const chosen = rows.filter(row => row.company !== "JIVO_BEVERAGES");
  for (const [key] of operationalKeys) {
    const expected = chosen.some(row => row[key] === null) ? null : chosen.reduce((sum,row) => sum + row[key]!, 0);
    if (!quantity(total[key]) || !matches(total[key], expected)) return fail();
  }
}
export function validateDispatchFeed(value: unknown): DispatchFeed {
  if (!object(value) || value.version !== 1 || typeof value.ok !== "boolean" || typeof value.complete !== "boolean" || !instant(value.asOf) || !instant(value.attemptedAt) || typeof value.expectedRefreshSeconds !== "number" || value.expectedRefreshSeconds < 1 || value.expectedRefreshSeconds > 3600 || !object(value.coverage) || !date(value.coverage.fromDate) || !date(value.coverage.toDate) || value.coverage.allCompanies !== true || typeof value.coverage.listComplete !== "boolean" || !count(value.coverage.listRows) || !count(value.coverage.pages) || !text(value.sourceUrl) || !text(value.unitNote) || !text(value.scopeNote) || !Array.isArray(value.days) || !Array.isArray(value.gateEntries) || !Array.isArray(value.trips) || !Array.isArray(value.issues)) return fail();
  const feed = value as unknown as DispatchFeed;
  const entries = new Map<string, typeof feed.gateEntries[number]>();
  for (const row of feed.gateEntries) {
    if (!object(row) || !text(row.id) || entries.has(row.id) || !text(row.reference) || !text(row.tripId) || !text(row.identityBasis) || !["JIVO_OIL", "JIVO_MART", "JIVO_BEVERAGES"].includes(row.company) || !date(row.date) || row.date < feed.coverage.fromDate || row.date > feed.coverage.toDate || !instant(row.departedAt) || new Date(Date.parse(row.departedAt) + 19800000).toISOString().slice(0,10) !== row.date || !quantity(row.litres) || !quantity(row.planningTonnes) || !count(row.documentCount) || !quantity(row.wellnessStorageLitres) || typeof row.detailComplete !== "boolean" || !Array.isArray(row.items) || !Array.isArray(row.warehouseLitres) || !Array.isArray(row.issues)) return fail();
    for (const item of row.items) if (!object(item) || !quantity(item.litres) || !quantity(item.quantity) || !["WELLNESS", "MART", "BEVERAGES", "UNKNOWN"].includes(item.operationalCompany) || ![item.name,item.code,item.warehouse,item.uom].every(v => v === null || text(v))) return fail();
    if (!row.issues.every(text) || row.warehouseLitres.some(v => !object(v) || !text(v.warehouse) || !quantity(v.litres) || v.litres === null)) return fail();
    if (row.litres !== null && (row.planningTonnes === null || Math.abs(row.planningTonnes - row.litres / 1000) > 0.00001)) return fail();
    if (row.detailComplete && (row.items.some(item => item.litres === null || item.warehouse === null) || row.litres === null || Math.abs(row.items.reduce((n,item) => n + item.litres!, 0) - row.litres) > 0.02)) return fail();
    for (const [key, company] of operationalKeys) {
      const expected = row.detailComplete ? row.items.filter(item => item.operationalCompany === company).reduce((sum,item) => sum + item.litres!,0) : null;
      if (!quantity(row[key]) || !matches(row[key], expected)) return fail();
    }
    if (row.detailComplete && row.company !== "JIVO_BEVERAGES" && !matches(row.litres, operationalKeys.reduce((sum,[key]) => sum + row[key]!, 0))) return fail();
    const storageExpected = row.company !== "JIVO_OIL" ? 0 : !row.detailComplete ? null : row.items.filter(item => item.operationalCompany === "WELLNESS" && ["BH-BT", "BH-PF"].includes(item.warehouse ?? "")).reduce((sum,item) => sum + item.litres!,0);
    if (!matches(row.wellnessStorageLitres, storageExpected)) return fail();
    entries.set(row.id, row);
  }
  const seen = new Set<string>();
  for (const trip of feed.trips) {
    if (!object(trip) || !text(trip.id) || !date(trip.date) || !instant(trip.departedAt) || !Array.isArray(trip.gateEntryIds) || !trip.gateEntryIds.length || !quantity(trip.combinedLitres)) return fail();
    const linked = trip.gateEntryIds.map(id => { const entry = entries.get(id); if (!entry || seen.has(id) || entry.tripId !== trip.id || entry.date !== trip.date) return fail(); seen.add(id); return entry; });
    validateOperationalTotals(trip, linked);
    const chosen = linked.filter(e => e.company !== "JIVO_BEVERAGES");
    const calculated = chosen.some(e => e.litres === null) ? null : chosen.reduce((n,e) => n + e.litres!, 0);
    if (calculated === null ? trip.combinedLitres !== null : trip.combinedLitres === null || Math.abs(calculated - trip.combinedLitres) > 0.02) return fail();
  }
  if (seen.size !== entries.size) return fail();
  const dates = new Set<string>();
  for (const day of feed.days) {
    if (!object(day) || !date(day.date) || dates.has(day.date) || day.date < feed.coverage.fromDate || day.date > feed.coverage.toDate || typeof day.complete !== "boolean" || ![day.combinedLitres,day.wellnessLitres,day.martLitres,day.beveragesLitres,day.wellnessStorageLitres].every(quantity)) return fail();
    dates.add(day.date);
    const dated = feed.gateEntries.filter(e => e.date === day.date);
    validateOperationalTotals(day, dated);
    for (const [key, company] of [["wellnessLitres", "JIVO_OIL"], ["martLitres", "JIVO_MART"], ["beveragesLitres", "JIVO_BEVERAGES"]] as const) {
      const entries = dated.filter(e => e.company === company);
      const total = entries.some(e => e.litres === null) ? null : entries.reduce((n,e) => n + e.litres!,0);
      if (total === null ? day[key] !== null : day[key] === null || Math.abs(total-day[key]!)>0.02) return fail();
    }
    const storage = dated.filter(e => e.company === "JIVO_OIL");
    const storageTotal = storage.some(e => e.wellnessStorageLitres === null) ? null : storage.reduce((n,e) => n+e.wellnessStorageLitres!,0);
    if (storageTotal === null ? day.wellnessStorageLitres !== null : day.wellnessStorageLitres === null || Math.abs(storageTotal-day.wellnessStorageLitres)>0.02) return fail();
    const rows = feed.gateEntries.filter(e => e.date === day.date && e.company !== "JIVO_BEVERAGES");
    const total = rows.some(e => e.litres === null) ? null : rows.reduce((n,e) => n + e.litres!, 0);
    if (day.tripCount !== new Set(rows.map(e => e.tripId)).size || day.gateEntryCount !== rows.length || (total === null ? day.combinedLitres !== null : day.combinedLitres === null || Math.abs(total - day.combinedLitres) > 0.02)) return fail();
  }
  for (let d = Date.parse(`${feed.coverage.fromDate}T00:00:00Z`); d <= Date.parse(`${feed.coverage.toDate}T00:00:00Z`); d += 86400000) if (!dates.has(new Date(d).toISOString().slice(0,10))) return fail();
  return feed;
}
export function validateStorageEvidence(value: unknown): import("./dispatch-types.ts").StorageEvidence | null {
  if (!object(value) || value.version !== 1 || !instant(value.asOf) || !instant(value.attemptedAt) || typeof value.ok !== "boolean" || !quantity(value.recordedFgLitres) || !quantity(value.legacyWaitingEstimateLitres) || !quantity(value.legacyPlanningPressureLitres) || !Array.isArray(value.scope) || value.scope.length !== 2 || !value.scope.includes("BH-BT") || !value.scope.includes("BH-PF") || !object(value.physicalReconciliation) || value.physicalReconciliation.complete !== false || !Array.isArray(value.physicalReconciliation.missing) || !value.physicalReconciliation.missing.every(text)) return null;
  if (value.previousObservation !== null && (!object(value.previousObservation) || !instant(value.previousObservation.observedAt) || !quantity(value.previousObservation.recordedFgLitres))) return null;
  return value as unknown as import("./dispatch-types.ts").StorageEvidence;
}
