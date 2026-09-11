"use client";

// The full order-by table: every material the September plan needs, with the
// last date each can be ordered without a run slipping. Client-side so it can
// sort and filter; every number in it arrives via props from data/materials.json
// (written only by the generator from the verified artifacts). Words only are
// mapped here — the data fields are read as they are.

import { useMemo, useState } from "react";
import type { MaterialRow } from "../lib/types";
import {
  obFmt, obDate, obUnit, obDaysBetween, obEnoughLabel, obCoverTone, obCoverBar, obMaterial,
  obStatusKey, OB_STATUS, obDays,
} from "./OrderByFmt";

type Props = {
  rows: MaterialRow[];
  freeze: string; // the day the stock was counted (31 Aug)
  today: string; // day 1 — LATE means the last date to order is today or has passed
  week1End: string; // day 1 + 6 days, computed server-side
  chaseCodes: string[]; // nothing in stock, but a PO already covers the need — chase, don't order
};

type ChipId = "all" | "late" | "week1" | "zero" | "sub1" | "chase" | "covered" | "oil";
type SortKey = "urgency" | "need" | "on_hand" | "on_order" | "cover_pct" | "short" | "order_by";

const urgencyRank = (r: MaterialRow) => (r.late ? 0 : r.order_by ? 1 : 2);

export default function OrderByTable({ rows, freeze, today, week1End, chaseCodes }: Props) {
  const chase = useMemo(() => new Set(chaseCodes), [chaseCodes]);
  const [q, setQ] = useState("");
  const [chip, setChip] = useState<ChipId>("all");
  const [sortKey, setSortKey] = useState<SortKey>("urgency");
  const [asc, setAsc] = useState(false);

  const chips: { id: ChipId; label: string; test: (r: MaterialRow) => boolean; tone: string }[] = useMemo(
    () => [
      { id: "all", label: "All", test: () => true, tone: "text-zinc-300" },
      { id: "late", label: "Already late", test: (r) => r.late, tone: "text-red-300" },
      {
        id: "week1",
        label: "This week",
        test: (r) => !!r.order_by && r.order_by <= week1End && r.cover_pct < 100,
        tone: "text-amber-300",
      },
      { id: "zero", label: "Nothing in stock", test: (r) => r.zero_literal, tone: "text-red-300" },
      { id: "sub1", label: "Almost nothing (August rule)", test: (r) => r.zero_august_rule, tone: "text-amber-300" },
      { id: "chase", label: "PO coming — chase", test: (r) => chase.has(r.code), tone: "text-sky-300" },
      { id: "covered", label: "Enough for planned runs", test: (r) => r.status === "covered", tone: "text-zinc-400" },
      { id: "oil", label: "Oils", test: (r) => r.kind === "OIL", tone: "text-emerald-300" },
    ],
    [week1End, chase],
  );

  const shown = useMemo(() => {
    const test = chips.find((c) => c.id === chip)?.test ?? (() => true);
    const needle = q.trim().toLowerCase();
    const filtered = rows.filter(
      (r) =>
        test(r) &&
        (!needle ||
          r.code.toLowerCase().includes(needle) ||
          r.name.toLowerCase().includes(needle) ||
          r.skus.toLowerCase().includes(needle)),
    );
    const sorted = [...filtered];
    if (sortKey === "urgency") {
      sorted.sort(
        (a, b) =>
          urgencyRank(a) - urgencyRank(b) ||
          (a.order_by || "9999").localeCompare(b.order_by || "9999") ||
          a.cover_pct - b.cover_pct ||
          b.short - a.short,
      );
    } else if (sortKey === "order_by") {
      sorted.sort((a, b) => {
        if (!a.order_by && !b.order_by) return 0;
        if (!a.order_by) return 1; // dateless rows sink, either direction
        if (!b.order_by) return -1;
        const cmp = a.order_by.localeCompare(b.order_by);
        return asc ? cmp : -cmp;
      });
    } else {
      sorted.sort((a, b) => (asc ? a[sortKey] - b[sortKey] : b[sortKey] - a[sortKey]));
    }
    return sorted;
  }, [rows, chips, chip, q, sortKey, asc]);

  const clickSort = (k: SortKey) => {
    if (sortKey === k) setAsc(!asc);
    else {
      setSortKey(k);
      // dates and "enough for" read naturally ascending (soonest / thinnest first)
      setAsc(k === "order_by" || k === "cover_pct");
    }
  };

  const arrow = (k: SortKey) => (sortKey === k ? (asc ? " ▲" : " ▼") : "");

  const Th = ({ k, children, right = true }: { k?: SortKey; children: React.ReactNode; right?: boolean }) => (
    <th className={`px-3 py-2 font-medium whitespace-nowrap ${right ? "text-right" : "text-left"}`}>
      {k ? (
        <button onClick={() => clickSort(k)} className="hover:text-zinc-200">
          {children}
          {arrow(k)}
        </button>
      ) : (
        children
      )}
    </th>
  );

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-3">
        {chips.map((c) => {
          const n = rows.filter(c.test).length;
          return (
            <button
              key={c.id}
              onClick={() => setChip(c.id)}
              className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                chip === c.id
                  ? "border-zinc-500 bg-zinc-800 text-zinc-100"
                  : "border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800/80 " + c.tone
              }`}
            >
              {c.label} <span className="tabular-nums opacity-70">{obFmt(n)}</span>
            </button>
          );
        })}
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="search item, code or product…"
          className="ml-auto text-sm bg-zinc-900 border border-zinc-800 rounded-md px-3 py-1.5 w-56 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600"
        />
        {sortKey !== "urgency" && (
          <button
            onClick={() => {
              setSortKey("urgency");
              setAsc(false);
            }}
            className="text-xs px-2.5 py-1 rounded-full border border-zinc-700 text-zinc-400 hover:bg-zinc-800"
          >
            ↺ most urgent first
          </button>
        )}
      </div>

      <div className="rounded-xl border border-zinc-800 overflow-auto max-h-[640px]">
        <table className="w-full text-sm min-w-[1040px]">
          <thead className="bg-zinc-900 text-zinc-400 text-left sticky top-0 z-10">
            <tr>
              <Th right={false}>Item</Th>
              <Th right={false}>What it is for</Th>
              <Th k="need">Need this month</Th>
              <Th k="on_hand">In stock</Th>
              <Th k="on_order">Coming (on order)</Th>
              <Th k="cover_pct">Enough for</Th>
              <Th k="order_by">Last date to order</Th>
              <Th right={false}>Status</Th>
            </tr>
          </thead>
          <tbody>
            {shown.map((r) => {
              const isChase = chase.has(r.code);
              const st = OB_STATUS[obStatusKey(r, isChase, week1End)];
              const past = r.late && r.order_by ? obDaysBetween(r.order_by, today) : 0;
              const products = r.skus.split(";").filter(Boolean);
              return (
                <tr key={r.code} className={`border-t border-zinc-900 ${r.late ? "bg-red-950/15" : ""}`}>
                  <td className="px-3 py-1.5 min-w-[220px]">
                    <div className="text-zinc-100">{r.name}</div>
                    <div className="text-xs text-zinc-600">
                      <span className="font-mono">{r.code}</span>
                      <span className={`ml-2 ${r.kind === "OIL" ? "text-emerald-500/80" : "text-zinc-500"}`}>
                        {obMaterial(r.name, r.kind)}
                      </span>
                    </div>
                  </td>
                  <td className="px-3 py-1.5 text-xs text-zinc-500 max-w-[220px]" title={products.join(" · ")}>
                    <span className="line-clamp-2">
                      {products.slice(0, 2).join(" · ")}
                      {products.length > 2 ? ` +${products.length - 2} more` : ""}
                    </span>
                  </td>
                  <td className="px-3 py-1.5 text-right tabular-nums whitespace-nowrap">
                    {obFmt(r.need)} <span className="text-zinc-600">{obUnit(r.uom)}</span>
                  </td>
                  <td className={`px-3 py-1.5 text-right tabular-nums ${r.on_hand === 0 ? "text-red-400" : "text-zinc-300"}`}>
                    {r.on_hand === 0 ? "nothing" : obFmt(r.on_hand)}
                  </td>
                  <td className={`px-3 py-1.5 text-right tabular-nums ${r.on_order > 0 ? "text-sky-300" : "text-zinc-600"}`}>
                    {r.on_order > 0 ? obFmt(r.on_order) : "—"}
                  </td>
                  <td className="px-3 py-1.5 text-right whitespace-nowrap">
                    <span className={`tabular-nums ${obCoverTone(r.cover_pct)}`}>{obEnoughLabel(r.cover_pct)}</span>
                    <span className="inline-block w-10 h-1 rounded-full bg-zinc-800 ml-2 align-middle overflow-hidden">
                      <span
                        className={`block h-full ${obCoverBar(r.cover_pct)}`}
                        style={{ width: `${Math.min(100, r.cover_pct)}%` }}
                      />
                    </span>
                  </td>
                  <td className="px-3 py-1.5 text-right whitespace-nowrap">
                    {r.order_by ? (
                      <>
                        <span className={r.late ? "text-red-300 font-medium" : "text-zinc-200"}>{obDate(r.order_by)}</span>
                        <div className="text-[11px] text-zinc-600">
                          {r.first_short_day ? `runs out ${obDate(r.first_short_day)} · ` : ""}
                          {r.lead_days} days to arrive
                          {r.order_basis === "unscheduled" ? " · no run booked" : ""}
                        </div>
                      </>
                    ) : (
                      <span className="text-zinc-600">—</span>
                    )}
                  </td>
                  <td className="px-3 py-1.5 whitespace-nowrap">
                    <span className={`text-[11px] px-2 py-0.5 rounded-full ${st.cls}`} title={st.title}>
                      {st.label}
                    </span>
                    {r.late && (
                      <span className="text-[11px] text-red-400/80 ml-1.5">
                        {past > 0 ? `by ${obDays(past)}` : "order today"}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
            {shown.length === 0 && (
              <tr>
                <td colSpan={8} className="px-3 py-6 text-center text-zinc-600">
                  no items match
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="mt-1.5 text-xs text-zinc-600">
        {obFmt(shown.length)} of {obFmt(rows.length)} items shown · stock counted {obDate(freeze)} · each item in its
        own unit (litres, pieces, kg, metres) · tap a column heading to sort
      </div>
    </div>
  );
}
