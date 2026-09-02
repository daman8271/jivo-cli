// Order-by lane helpers — pure functions, safe for BOTH server and client
// components (lib/data.ts reads fs and must stay server-only, so the client
// table imports formatters from here instead).
// No business numbers live in this file — only formatting and date math.

export const obFmt = (n: number) => Math.round(n).toLocaleString("en-IN");

// Money: on a litres-heavy page the lib's "₹x.x L" reads as litres — spell out "lakh".
export const obMoney = (rs: number) =>
  Math.abs(rs) >= 1e7
    ? `₹${(rs / 1e7).toFixed(2)} Cr`
    : Math.abs(rs) >= 1e5
      ? `₹${(rs / 1e5).toFixed(2)} lakh`
      : `₹${obFmt(rs)}`;

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
export const obDate = (iso: string) =>
  iso ? `${Number(iso.slice(8, 10))} ${MON[Number(iso.slice(5, 7)) - 1]}` : "";

export const obUnit = (u: string) =>
  u === "LTR" ? "L" : u === "PCS" ? "pcs" : u === "KGS" ? "kg" : u.toLowerCase();

// Whole days from a to b (b - a), ISO date strings.
export const obDaysBetween = (a: string, b: string) =>
  Math.round((Date.parse(b) - Date.parse(a)) / 86400000);

// cover_pct arrives capped at 999.9 by the artifact — render the cap honestly.
export const obCoverLabel = (pct: number) =>
  pct >= 999.9 ? "≥1,000%" : `${pct % 1 === 0 ? pct.toFixed(0) : pct.toFixed(1)}%`;

export const obCoverTone = (pct: number) =>
  pct < 1 ? "text-red-400" : pct < 50 ? "text-amber-300" : pct < 100 ? "text-zinc-200" : "text-emerald-400/80";

export const obCoverBar = (pct: number) =>
  pct < 1 ? "bg-red-500" : pct < 50 ? "bg-amber-400" : pct < 100 ? "bg-zinc-400" : "bg-emerald-500";
