/** Reservation ledger: a later allocation cannot consume stock needed by an
 * already-reserved earlier run, or lend a future receipt to an earlier run. */
export type TimedReceipt = { at: number; code: string; quantity: number; conditional: boolean };
export class MaterialCalendar {
  opening: Record<string, number>;
  receipts: TimedReceipt[];
  private balances = new Map<string, Record<string, number>>();
  private capacities = new Map<string, Record<string, number>>();
  reservations: { at: number; used: Record<string, number> }[] = [];
  constructor(opening: Record<string, number>, receipts: TimedReceipt[]) {
    this.opening = { ...opening }; this.receipts = receipts.map(row => ({ ...row }));
  }
  clone(): MaterialCalendar { const copy = new MaterialCalendar(this.opening, this.receipts); copy.reservations = this.reservations.map(row => ({ at: row.at, used: { ...row.used } })); return copy; }
  balance(at: number, recordedOnly = false): Record<string, number> {
    const key = `${at}:${recordedOnly}`;
    const cached = this.balances.get(key); if (cached) return cached;
    const result = { ...this.opening };
    for (const row of this.receipts) if (row.at <= at && !(recordedOnly && row.conditional)) result[row.code] = (result[row.code] ?? 0) + row.quantity;
    for (const row of this.reservations) if (row.at <= at) for (const [code, quantity] of Object.entries(row.used)) result[code] = (result[code] ?? 0) - quantity;
    this.balances.set(key, result); return result;
  }
  available(at: number, recordedOnly = false): Record<string, number> {
    const key = `${at}:${recordedOnly}`;
    const cached = this.capacities.get(key); if (cached) return cached;
    const result = { ...this.balance(at, recordedOnly) };
    // Future reservations are commitments: protect their stock even when the
    // global priority allocator revisits a line with an earlier free clock.
    for (const later of this.reservations.filter(row => row.at > at)) {
      const balance = this.balance(later.at, recordedOnly);
      for (const code of new Set([...Object.keys(result), ...Object.keys(balance)])) result[code] = Math.min(result[code] ?? 0, balance[code] ?? 0);
    }
    const capacity = Object.fromEntries(Object.entries(result).map(([code, value]) => [code, Math.max(0, value)]));
    this.capacities.set(key, capacity); return capacity;
  }
  reserve(at: number, used: Record<string, number>): string[] {
    const available = this.available(at), known = this.available(at, true);
    for (const [code, quantity] of Object.entries(used)) if (quantity > (available[code] ?? 0) + 1e-7) throw new Error(`Timed material reservation exceeded ${code} stock.`);
    this.reservations.push({ at, used: { ...used } });
    this.balances.clear(); this.capacities.clear();
    return Object.entries(used).filter(([code, quantity]) => quantity > (known[code] ?? 0) + 1e-7).map(([code]) => code);
  }
  times(from: number, until: number): number[] { return [...new Set([from, ...this.receipts.map(row => row.at).filter(at => at > from && at < until)])].sort((a,b) => a-b); }
}
