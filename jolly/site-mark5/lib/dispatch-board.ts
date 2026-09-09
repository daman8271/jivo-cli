import type { DispatchFeed, DispatchStatus, GateEntry, DispatchItem } from "./dispatch-types.ts";
export type CompanyFilter = "all" | "wellness" | "mart" | "beverages" | "unknown";
export const planningTonnes = (litres: number | null) => litres === null ? null : litres / 1000;
export function dispatchStatus(feed: DispatchFeed, now = Date.now()): DispatchStatus {
  const age = now - Date.parse(feed.asOf);
  if (!feed.ok || !Number.isFinite(age) || age < -300000 || age > Math.max(300, feed.expectedRefreshSeconds * 3) * 1000) return "stale";
  return feed.complete && feed.coverage.listComplete ? "fresh" : "incomplete";
}
export function operationalCompany(entry: GateEntry, item: DispatchItem): Exclude<CompanyFilter, "all"> {
  return ({ WELLNESS: "wellness", MART: "mart", BEVERAGES: "beverages", UNKNOWN: "unknown" } as const)[item.operationalCompany];
}
function sum(values: (number | null)[]) { return values.some(v => v === null) ? null : values.reduce<number>((a, b) => a + b!, 0); }
export function entryQuantity(entry: GateEntry, filter: CompanyFilter): number | null {
  if (filter === "all") return entry.company === "JIVO_BEVERAGES" ? 0 : entry.litres;
  if (filter === "beverages") return entry.company === "JIVO_BEVERAGES" ? entry.litres : 0;
  if (entry.company === "JIVO_BEVERAGES") return 0;
  if (!entry.detailComplete || !entry.items.length) return null;
  return sum(entry.items.filter(item => operationalCompany(entry, item) === filter).map(item => item.litres));
}
export function selectDispatch(feed: DispatchFeed, date: string, filter: CompanyFilter = "all") {
  const day = feed.days.find(row => row.date === date);
  const all = feed.gateEntries.filter(row => row.date === date);
  const relevant = all.filter(row => filter === "beverages" ? row.company === "JIVO_BEVERAGES" : row.company !== "JIVO_BEVERAGES");
  const rows = relevant.filter(row => filter === "all" || filter === "beverages" || entryQuantity(row, filter) !== 0);
  const trips = [...new Set(rows.map(row => row.tripId))].map(id => {
    const entries = rows.filter(row => row.tripId === id);
    const quantity = sum(entries.map(row => entryQuantity(row, filter)));
    return { id, entries, litres: quantity, departedAt: entries.map(row => row.departedAt).sort().at(-1)!, identityBasis: entries[0].identityBasis };
  }).sort((a, b) => Date.parse(b.departedAt) - Date.parse(a.departedAt));
  return { day, rows, trips, litres: day ? sum(rows.map(row => entryQuantity(row, filter))) : null,
    wellnessLitres: day ? sum(relevant.filter(row => row.company !== "JIVO_BEVERAGES").map(row => entryQuantity(row, "wellness"))) : null,
    martLitres: day ? sum(relevant.filter(row => row.company !== "JIVO_BEVERAGES").map(row => entryQuantity(row, "mart"))) : null,
    unclassifiedLitres: day ? sum(relevant.filter(row => row.company !== "JIVO_BEVERAGES").map(row => entryQuantity(row, "unknown"))) : null,
    storageLitres: day?.wellnessStorageLitres ?? null };
}
