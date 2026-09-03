"use client";

// /order-by — the one page a planner acts on: what has to be ordered, and by
// when, for the plan to hold. Sorted by the date it has to leave, worst first.

import { useMemo, useState } from "react";
import { asMaterials, useLive } from "../lib/live";
import { maskDigits } from "../lib/labels";
import { dlabel, inr, litres, money, plural } from "../lib/fmt";
import { AsOf, Live } from "./Freshness";
import { Card, Panel, Pill } from "./Card";
import SimBadge from "./SimBadge";
import type { MaterialRow } from "../lib/types";

type Filter = "all" | "late" | "week1" | "zero";

const isLate = (r: MaterialRow) => r.late === true || r.status.toUpperCase().startsWith("LATE");
const isZero = (r: MaterialRow) => r.at_zero === "YES" || r.zero_literal === true;

export default function OrderByClient() {
  const live = useLive(["materials"]);
  const M = asMaterials(live.materials);
  const [filter, setFilter] = useState<Filter>("all");
  const [q, setQ] = useState("");

  const rows = useMemo(() => {
    const all = M?.rows ?? [];
    const week1 = new Set(
      [...all]
        .filter((r) => r.order_by)
        .sort((a, b) => String(a.order_by).localeCompare(String(b.order_by)))
        .slice(0, M?.must_order_week1 ?? 0)
        .map((r) => r.code),
    );
    let out = all;
    if (filter === "late") out = out.filter(isLate);
    if (filter === "zero") out = out.filter(isZero);
    if (filter === "week1") out = out.filter((r) => week1.has(r.code));
    const needle = q.trim().toLowerCase();
    if (needle) out = out.filter((r) => `${r.code} ${r.name} ${r.skus ?? ""}`.toLowerCase().includes(needle));
    // no order-by date sorts LAST, and never behind a made-up date
    return [...out].sort((a, b) => {
      const ao = a.order_by, bo = b.order_by;
      if (ao !== bo) {
        if (!ao) return 1;
        if (!bo) return -1;
        return ao.localeCompare(bo);
      }
      return b.value_at_risk - a.value_at_risk;
    });
  }, [M, filter, q]);

  const atRisk = rows.reduce((a, r) => a + r.value_at_risk, 0);
  const litresAtRisk = rows.reduce((a, r) => a + r.litres_at_risk, 0);

  const FILTERS: [Filter, string][] = [
    ["all", "everything"],
    ["late", "already too late"],
    ["week1", "order this week"],
    ["zero", "at zero now"],
  ];

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Order by when</h1>
        <SimBadge kind="plan" />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        Each material, the day the order has to leave, and what stops if it does not. Worked out from the plan the
        computer just rebuilt — so these dates move as the plant moves.
      </p>

      <div className="mt-6">
        <Live rec={live.materials} what="the order-by list">
          {M && (
            <>
              <div className="mb-1.5 flex justify-end">
                <AsOf rec={live.materials} />
              </div>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Card title="Materials in the plan" value={inr(M.components_in_plan)} badge={<SimBadge kind="plan" />} />
                <Card
                  title="Already too late"
                  value={inr(M.already_late)}
                  tone="text-red-400"
                  badge={<SimBadge kind="plan" />}
                  sub="ordering today still slips the run"
                />
                <Card
                  title="Shown here"
                  value={`${inr(rows.length)} ${plural(rows.length, "row", "rows")}`}
                  badge={<SimBadge kind="plan" />}
                />
                <Card
                  title="Litres behind them"
                  value={litres(litresAtRisk)}
                  tone="text-amber-300"
                  badge={<SimBadge kind="plan" />}
                  sub={`${money(atRisk)} of product waits on these`}
                />
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                {FILTERS.map(([f, label]) => (
                  <button
                    key={f}
                    type="button"
                    onClick={() => setFilter(f)}
                    className={`rounded-md px-3 py-1 text-sm ${
                      filter === f ? "bg-zinc-800 font-medium text-zinc-50" : "text-zinc-400 hover:bg-zinc-900"
                    }`}
                  >
                    {label}
                  </button>
                ))}
                <input
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="find a material or a product"
                  className="ml-auto w-64 rounded-md border border-zinc-800 bg-zinc-900 px-3 py-1 text-sm outline-none placeholder:text-zinc-600 focus:border-zinc-600"
                />
              </div>

              <div className="mt-3">
                <Panel title="What to order, and by when" badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live.materials} />}>
                  <div className="max-h-[36rem] overflow-auto">
                    <table className="w-full min-w-[60rem] text-sm">
                      <thead className="sticky top-0 z-10 bg-zinc-900">
                        <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                          <th className="py-1 font-normal">Order by</th>
                          <th className="py-1 font-normal">Material</th>
                          <th className="py-1 text-right font-normal">Need</th>
                          <th className="py-1 text-right font-normal">Have</th>
                          <th className="py-1 text-right font-normal">On order</th>
                          <th className="py-1 text-right font-normal">Covers</th>
                          <th className="py-1 text-right font-normal">Short by</th>
                          <th className="py-1 text-right font-normal">Litres at risk</th>
                          <th className="py-1 text-right font-normal">Worth</th>
                          <th className="py-1 font-normal">What it means</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((r) => {
                          const late = isLate(r);
                          return (
                            <tr
                              key={r.code}
                              className={`border-t border-zinc-800/60 ${late ? "bg-red-500/5" : ""}`}
                            >
                              <td className={`py-1 whitespace-nowrap ${late ? "text-red-300" : "text-zinc-300"}`}>
                                {r.order_by ? dlabel(r.order_by) : "—"}
                              </td>
                              <td className="py-1">
                                <span className="mr-2 font-mono text-[11px] text-zinc-500">{r.code}</span>
                                <span title={r.skus ? maskDigits(r.skus) : undefined}>{r.name}</span>
                                {isZero(r) && <Pill tone="red">at zero</Pill>}
                                <span className="ml-1 text-[10px] text-zinc-600">{r.kind.toLowerCase()}</span>
                              </td>
                              <td className="py-1 text-right tabular-nums">{inr(r.need)}</td>
                              <td className="py-1 text-right tabular-nums">{inr(r.on_hand)}</td>
                              <td className="py-1 text-right tabular-nums text-zinc-400">{inr(r.on_order)}</td>
                              <td
                                className={`py-1 text-right tabular-nums ${
                                  r.cover_pct < 50 ? "text-red-300" : r.cover_pct < 100 ? "text-amber-300" : "text-emerald-300"
                                }`}
                              >
                                {Math.round(r.cover_pct)}%
                              </td>
                              <td className="py-1 text-right tabular-nums">{r.short > 0 ? inr(r.short) : "—"}</td>
                              <td className="py-1 text-right tabular-nums">{r.litres_at_risk > 0 ? inr(r.litres_at_risk) : "—"}</td>
                              <td className="py-1 text-right tabular-nums text-amber-300">
                                {r.value_at_risk > 0 ? money(r.value_at_risk) : "—"}
                              </td>
                              <td className={`py-1 ${late ? "text-red-300" : "text-zinc-400"}`}>{maskDigits(r.status)}</td>
                            </tr>
                          );
                        })}
                        {rows.length === 0 && (
                          <tr>
                            <td colSpan={10} className="py-3 text-zinc-500">
                              Nothing matches that.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </Panel>
              </div>

              {M.zero_definitions && (
                <details className="mt-4 rounded-lg border border-zinc-800 bg-zinc-900/40 p-3 text-xs text-zinc-400">
                  <summary className="cursor-pointer text-zinc-300">
                    Two different meanings of &ldquo;at zero&rdquo; — and why both are shown
                  </summary>
                  <div className="mt-2 space-y-1">
                    {Object.entries(M.zero_definitions).map(([k, v]) => (
                      <div key={k}>
                        <span className="text-zinc-500">{k.replace(/_/g, " ")}: </span>
                        {typeof v === "string" ? maskDigits(v) : JSON.stringify(v)}
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </>
          )}
        </Live>
      </div>
    </div>
  );
}
