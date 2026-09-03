// Formatting only. Not one business number lives here — these take a figure
// that arrived from the publisher and decide how it is spelled.
// Hand-rolled Indian grouping (not toLocaleString) so the server-rendered shell
// and the browser can never disagree about a comma.

export function inr(n: number): string {
  const v = Math.round(Math.abs(n));
  const s = String(v);
  const sign = n < 0 ? "-" : "";
  if (s.length <= 3) return sign + s;
  return sign + s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + s.slice(-3);
}

export const fmt = inr;
export const cr = (rs: number) => `₹${(rs / 1e7).toFixed(2)} Cr`;
// "lakh" spelled out — on a litres-heavy site "₹x.x L" reads as litres.
export const lakh = (rs: number) => `₹${(rs / 1e5).toFixed(2)} lakh`;
export const money = (rs: number) =>
  Math.abs(rs) >= 1e7 ? cr(rs) : Math.abs(rs) >= 1e5 ? lakh(rs) : `₹${inr(rs)}`;
export const litres = (l: number) => `${inr(l)} L`;
export const pieces = (p: number) => `${inr(p)} pcs`;
/** Oil tonnes: litres × 0.91 ÷ 1000 (the density EXIM itself publishes). */
export const tonnes = (l: number) => `${((l * 0.91) / 1000).toFixed(1)} T`;
export const pct = (p: number) => `${Math.round(p)}%`;
export const pct1 = (p: number) => `${p.toFixed(1)}%`;

/** A figure that may be absent. Absent is NEVER zero — it prints as unknown. */
export function orUnknown(n: number | null | undefined, f: (v: number) => string, unknown = "not read this cycle"): string {
  return typeof n === "number" && Number.isFinite(n) ? f(n) : unknown;
}

const COUNT_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"];
export const countWord = (n: number) =>
  Number.isInteger(n) && n >= 0 && n <= 10 ? COUNT_WORDS[n] : inr(n);
export const plural = (n: number, one: string, many: string) => (n === 1 ? one : many);

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
/** "2026-09-03" → "3 Sep". Dates are not business numbers. */
export const dlabel = (iso: string | null | undefined) =>
  iso && iso.length >= 10 ? `${Number(iso.slice(8, 10))} ${MON[Number(iso.slice(5, 7)) - 1]}` : "—";

export const weekdayShort = (w: string | null | undefined) => (w ? w.slice(0, 3) : "");

/** Bands used for how full the godown is. Percentages, not litres. */
export function fullnessTone(p: number): "green" | "amber" | "red" {
  return p >= 95 ? "red" : p >= 80 ? "amber" : "green";
}
export const TONE_TEXT: Record<string, string> = {
  green: "text-emerald-300",
  amber: "text-amber-300",
  red: "text-red-300",
  zinc: "text-zinc-100",
};
export const TONE_FILL: Record<string, string> = {
  green: "bg-emerald-500",
  amber: "bg-amber-500",
  red: "bg-red-500",
};
