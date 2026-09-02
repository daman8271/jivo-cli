"use client";

import Link from "next/link";
import { useState } from "react";

export type LnRun = { sku: string; oil: string | null; litres: number; hours: number; flush_min: number };
export type LnCell = {
  day: number;
  label: string;
  working: boolean;
  hours: number;
  oil: string | null;
  litres: number;
  value: number;
  flushMin: number;
  runs: LnRun[];
};
export type LnRow = { line: string; cells: LnCell[] };
export type LnDayHead = { day: number; label: string; wd: string; working: boolean; util: number };

type Hover = { line: string; cell: LnCell; x: number; y: number; below: boolean };

const inr = (n: number) => Math.round(n).toLocaleString("en-IN");
const money = (rs: number) => (rs >= 1e7 ? `₹${(rs / 1e7).toFixed(2)} Cr` : `₹${(rs / 1e5).toFixed(1)} L`);
const IDLE = "#3f3f46";
const HATCH = "repeating-linear-gradient(45deg, rgba(255,255,255,0.05) 0 3px, rgba(255,255,255,0) 3px 7px)";

export default function LnGantt({
  rows,
  days,
  colours,
  shift,
}: {
  rows: LnRow[];
  days: LnDayHead[];
  colours: Record<string, string>;
  shift: number;
}) {
  const [hover, setHover] = useState<Hover | null>(null);
  const cols = `104px repeat(${days.length}, minmax(26px, 1fr))`;
  const hoverDay = hover ? hover.cell.day : null;

  function enter(e: { currentTarget: HTMLElement }, line: string, cell: LnCell) {
    const r = e.currentTarget.getBoundingClientRect();
    const w = typeof window === "undefined" ? 1280 : window.innerWidth;
    const x = Math.min(Math.max(r.left + r.width / 2, 176), w - 176);
    const below = r.top < 260;
    setHover({ line, cell, x, y: below ? r.bottom : r.top, below });
  }

  return (
    <div className="relative">
      <div className="overflow-x-auto pb-1">
        <div className="min-w-[880px]">
          {/* day numbers */}
          <div className="grid items-end gap-x-[2px]" style={{ gridTemplateColumns: cols }}>
            <div />
            {days.map((d) => (
              <div key={d.day} className="text-center leading-tight">
                <div className={`text-[9px] ${d.working ? "text-zinc-600" : "text-zinc-700"}`}>{d.wd}</div>
                <div
                  className={`text-[11px] tabular-nums ${
                    hoverDay === d.day ? "text-amber-300" : d.working ? "text-zinc-400" : "text-zinc-600"
                  }`}
                >
                  {d.day}
                </div>
              </div>
            ))}
          </div>

          {/* one row per line */}
          {rows.map((row) => (
            <div key={row.line} className="grid items-center gap-x-[2px] mt-[3px]" style={{ gridTemplateColumns: cols }}>
              <div className="text-[11px] text-zinc-400 pr-2 truncate">{row.line}</div>
              {row.cells.map((c) => {
                // a run of six minutes is 0.8% of the day: give every real run a visible sliver
                const raw = Math.max(0, Math.min(1, c.hours / shift)) * 100;
                const pct = c.hours > 0 ? Math.max(6, raw) : 0;
                const colour = c.oil ? colours[c.oil] || IDLE : IDLE;
                return (
                  <Link
                    key={c.day}
                    href={`/day/${c.day}`}
                    aria-label={`${row.line}, ${c.label}, ${c.hours.toFixed(1)} hours`}
                    onMouseEnter={(e) => enter(e, row.line, c)}
                    onFocus={(e) => enter(e, row.line, c)}
                    onMouseLeave={() => setHover(null)}
                    onBlur={() => setHover(null)}
                    className={`relative block h-10 rounded-[3px] border transition-colors ${
                      hoverDay === c.day ? "border-zinc-600" : "border-zinc-800/70"
                    } ${c.working ? "bg-zinc-900/70" : "bg-zinc-900/30"}`}
                    style={c.working ? undefined : { backgroundImage: HATCH }}
                  >
                    {c.hours > 0 ? (
                      <span
                        className="absolute inset-x-0 bottom-0 rounded-b-[2px]"
                        style={{ height: `${pct}%`, background: colour, opacity: 0.92 }}
                      />
                    ) : c.working ? (
                      <span className="absolute inset-x-1 bottom-0 h-[2px] bg-zinc-700 rounded" />
                    ) : null}
                  </Link>
                );
              })}
            </div>
          ))}

          {/* all-lines utilisation */}
          <div className="grid items-center gap-x-[2px] mt-2 pt-2 border-t border-zinc-900" style={{ gridTemplateColumns: cols }}>
            <div className="text-[10px] uppercase tracking-wider text-zinc-600 pr-2">All lines</div>
            {days.map((d) => (
              <div
                key={d.day}
                className={`text-center text-[10px] tabular-nums ${
                  d.util >= 100 ? "text-amber-300 font-semibold" : d.util > 0 ? "text-zinc-400" : "text-zinc-700"
                }`}
              >
                {d.util > 0 ? d.util : "·"}
              </div>
            ))}
          </div>
        </div>
      </div>

      {hover && (
        <div
          className="fixed z-[60] pointer-events-none"
          style={{
            left: hover.x,
            top: hover.y,
            transform: hover.below ? "translate(-50%, 10px)" : "translate(-50%, calc(-100% - 10px))",
          }}
        >
          <div className="w-[336px] rounded-lg border border-zinc-700 bg-zinc-950 shadow-2xl p-3">
            <div className="flex items-baseline justify-between">
              <div className="text-sm font-semibold">{hover.line}</div>
              <div className="text-[11px] text-zinc-500">{hover.cell.label}</div>
            </div>
            {hover.cell.hours > 0 ? (
              <>
                <div className="mt-1 text-[11px] text-zinc-400 tabular-nums">
                  {hover.cell.hours.toFixed(1)} h of {shift} h · {inr(hover.cell.litres)} L · {money(hover.cell.value)}
                  {hover.cell.flushMin > 0 ? ` · ${hover.cell.flushMin} min oil change` : ""}
                </div>
                <ul className="mt-2 space-y-1">
                  {hover.cell.runs.map((r, i) => (
                    <li key={i} className="flex gap-2 items-start">
                      <span
                        className="mt-[5px] h-2 w-2 rounded-[2px] shrink-0"
                        style={{ background: r.oil ? colours[r.oil] || IDLE : IDLE }}
                      />
                      <span className="text-[11px] leading-snug text-zinc-300">
                        {r.sku}
                        <span className="text-zinc-500 tabular-nums">
                          {" — "}
                          {inr(r.litres)} L · {r.hours.toFixed(1)} h
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <div className="mt-1 text-[11px] text-zinc-500">
                {hover.cell.working ? "Nothing ran on this line." : "Sunday — the plant is off."}
              </div>
            )}
            <div className="mt-2 pt-2 border-t border-zinc-800 text-[10px] text-zinc-600">Click to open the day</div>
          </div>
        </div>
      )}
    </div>
  );
}
