// Order-by lane helpers — pure functions, safe for BOTH server and client
// components (lib/data.ts reads fs and must stay server-only, so the client
// table imports formatters from here instead).
// No business numbers live in this file — only formatting, date math and the
// plain-word labels this lane renders (see PLAIN-LANGUAGE.md). Raw values from
// data/*.json (kind "PACK", status "covered", the August-rule definition string)
// are mapped to floor words HERE, at render time — the data keys never change.

import { lakhCrore, materialWord, packWords } from "../lib/types";

export const obFmt = (n: number) => Math.round(n).toLocaleString("en-IN");

// Money: on a litres-heavy page the lib's "₹x.x L" reads as litres — spell out "lakh".
export const obMoney = (rs: number) =>
  Math.abs(rs) >= 1e7
    ? `₹${(rs / 1e7).toFixed(2)} crore`
    : Math.abs(rs) >= 1e5
      ? `₹${(rs / 1e5).toFixed(2)} lakh`
      : `₹${obFmt(rs)}`;

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
export const obDate = (iso: string) =>
  iso ? `${Number(iso.slice(8, 10))} ${MON[Number(iso.slice(5, 7)) - 1]}` : "";

// Short unit for table cells.
export const obUnit = (u: string) =>
  u === "LTR" ? "L" : u === "PCS" ? "pcs" : u === "KGS" ? "kg" : u === "MTR" ? "m" : u.toLowerCase();

// Spoken unit for sentences ("13.78 lakh litres", "4,000 pieces").
export const obUnitWord = (u: string) =>
  u === "LTR" ? "litres" : u === "PCS" ? "pieces" : u === "KGS" ? "kg" : u === "MTR" ? "metres" : u.toLowerCase();

// Indian words in sentences (rule 4): "13.78 lakh litres", "66,000 litres" — lib's lakhCrore, plus the unit.
export const obLakh = (n: number, unitWord: string) => `${lakhCrore(n)} ${unitWord}`;

// Whole days from a to b (b - a), ISO date strings.
export const obDaysBetween = (a: string, b: string) =>
  Math.round((Date.parse(b) - Date.parse(a)) / 86400000);

export const obDays = (n: number) => (n === 1 ? "1 day" : `${obFmt(n)} days`);

// cover_pct arrives capped at 999.9 by the artifact — render the cap honestly.
export const obCoverLabel = (pct: number) =>
  pct >= 999.9 ? "≥1,000%" : `${pct % 1 === 0 ? pct.toFixed(0) : pct.toFixed(1)}%`;

// "Enough for" — what the floor reads instead of "cover". The figure is the
// artifact's cover_pct (stock + on order, as a share of the month's need).
export const obEnoughLabel = (pct: number) => (pct >= 999.9 ? "10 months+" : `${obCoverLabel(pct)} of month`);

export const obCoverTone = (pct: number) =>
  pct < 1 ? "text-red-400" : pct < 50 ? "text-amber-300" : pct < 100 ? "text-zinc-200" : "text-emerald-400/80";

export const obCoverBar = (pct: number) =>
  pct < 1 ? "bg-red-500" : pct < 50 ? "bg-amber-400" : pct < 100 ? "bg-zinc-400" : "bg-emerald-500";

// Pull the threshold out of the August rule's own definition string in
// data/materials.json ("cover < 1% …") so the page never types it.
export const obPctFromText = (s: string): string | null => {
  const m = /(\d+(?:\.\d+)?)\s*%/.exec(s || "");
  return m ? m[1] : null;
};

// "component" → the material's own name: oil, label, cap, bottle, carton, tin,
// pouch… worked out from the item name at render time (lib's materialWord —
// the same words the day pages use).
export const obMaterial = (name: string, kind: string) => materialWord(name, kind);

// A product no machine can fill — "200-litre drum", "3-litre bottle" — from the
// artifact's own pack_type and litres_per_piece (lib's packWords, singular).
export const obPackDesc = (u: { pack_type: string; litres_per_piece: number }) => packWords(u, false);

// Status words — one set, used by every block on the page.
export type ObStatusKey = "late" | "chase" | "week" | "later" | "ok";

export const obStatusKey = (
  r: { late: boolean; order_by: string },
  isChase: boolean,
  week1End: string,
): ObStatusKey => (r.late ? "late" : isChase ? "chase" : r.order_by ? (r.order_by <= week1End ? "week" : "later") : "ok");

export const OB_STATUS: Record<ObStatusKey, { label: string; cls: string; title: string }> = {
  late: {
    label: "ALREADY LATE",
    cls: "bg-red-500/15 text-red-300 font-medium",
    title: "The last date to order has passed. Order today — the run still slips.",
  },
  chase: {
    label: "PO coming — chase it",
    cls: "bg-sky-500/15 text-sky-300 font-medium",
    title: "Nothing in stock today, but a PO is already placed for the full need. Chase the truck. Do not order again.",
  },
  week: {
    label: "this week",
    cls: "bg-amber-500/15 text-amber-300",
    title: "Must be on a PO this week.",
  },
  later: {
    label: "later",
    cls: "bg-zinc-800 text-zinc-300",
    title: "Has a last date to order, after this week.",
  },
  ok: {
    label: "enough for planned runs",
    cls: "bg-zinc-800 text-zinc-500",
    title:
      "The runs booked never run out of it. It can still be short of the full month's target — see the note under the table.",
  },
};
